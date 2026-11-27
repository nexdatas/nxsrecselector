#!/usr/bin/env python
#   This file is part of nxsrecconfig - NeXus Sardana Recorder Settings
#
#    Copyright (C) 2014-2026 DESY, Jan Kotanski <jkotan@mail.desy.de>
#
#    nexdatas is free software: you can redistribute it and/or modify
#    it under the terms of the GNU General Public License as published by
#    the Free Software Foundation, either version 3 of the License, or
#    (at your option) any later version.
#
#    nexdatas is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU General Public License for more details.
#
#    You should have received a copy of the GNU General Public License
#    along with nexdatas.  If not, see <http://www.gnu.org/licenses/>.
#

""" BLISS session side of the ``bliss`` scan backend

It publishes channels, motors and measurement groups of a BLISS session
for the selector and applies the channels selected by the selector to
the BLISS measurement groups.  In a BLISS session::

    from nxsrecconfig.BlissSession import NXSBlissSession
    nxsbliss = NXSBlissSession()
    nxsbliss.sync()      # after changes in the selector or the session

The selector has to use the ``bliss`` backend with the session name
as its ``Door``.

Selected STEP datasources which are not BLISS counters, i.e. TANGO, DB,
PYEVAL or CLIENT datasources, are read by counters of
:class:`nxsrecconfig.BlissDataSources.NXSDataSourceController`
which are added to the measurement groups.  CLIENT datasources are
read from ``userdata``, e.g.::

    nxsbliss = NXSBlissSession(userdata=lambda: {"energy": mono.energy})

:func:`setup_nexdatas` sets up everything in the session setup, i.e. the
session, the BLISS scan metadata of the selector profiles and a watcher
which applies changes of the selector automatically::

    from nxsrecconfig.BlissSession import setup_nexdatas
    nexdatas = setup_nexdatas("p09/nxsrecselector/1", links=True)

The scan directory and file of the selector, i.e. ``ScanDir`` and
``ScanFile``, follow ``SCAN_SAVING`` of BLISS.  They can be changed by
the selector unless the session uses the ESRF data policy.
"""

import datetime
import hashlib
import json
import logging
import os

from .BlissBackend import (
    BlissBackend, channelName, redisConnection, sessionKey)
from .BlissDataSources import CONTROLLER


class BlissAPI(object):

    """ access to the current BLISS session
    """

    def __init__(self, controller=CONTROLLER, userdata=None, canfail=True):
        """ constructor

        :param controller: name of the datasource counter controller
        :type controller: :obj:`str`
        :param userdata: user data of CLIENT datasources
                         or a function returning them
        :type userdata: :obj:`dict` <:obj:`str`, `any`> or callable
        :param canfail: fill values of datasources which cannot be read,
                        stop the scan otherwise
        :type canfail: :obj:`bool`
        """
        #: (:obj:`str`) name of the datasource counter controller
        self.controller = controller
        #: (:obj:`dict` or callable) user data
        self.userdata = userdata
        #: (:obj:`bool`) fill values of datasources which cannot be read
        self.canfail = canfail
        #: (:class:`nxsrecconfig.BlissDataSources.NXSDataSourceController`)
        #:     datasource counter controller
        self.__controller = None

    def setDataSources(self, datasources):
        """ sets the datasources read by the datasource counters

        :param datasources: datasource descriptions by datasource names
        :type datasources: :obj:`dict` <:obj:`str`, :obj:`dict`>
        :returns: full names of the datasource counters by datasource names
        :rtype: :obj:`dict` <:obj:`str`, :obj:`str`>
        """
        if self.__controller is None:
            if not datasources:
                return {}
            from .BlissDataSources import (
                DataSourceReader, NXSDataSourceController)
            self.__controller = NXSDataSourceController(
                self.controller, DataSourceReader(self.userdata),
                self.canfail)
        self.__controller.canfail = self.canfail
        self.__controller.setDataSources(datasources)
        return {cnt.name: cnt.fullname
                for cnt in self.__controller.counters}

    def session(self):
        """ provides the session name

        :returns: session name
        :rtype: :obj:`str`
        """
        from bliss import current_session
        return current_session.name

    def counters(self):
        """ provides the counters of the session

        :returns: counters, i.e. dictionaries with ``fullname``,
                  ``controller``, ``shape`` and ``dtype``
        :rtype: :obj:`list` <:obj:`dict` <:obj:`str`, `any`>>
        """
        import numpy
        from bliss import global_map
        counters = []
        for cnt in global_map.get_counters_iter():
            try:
                dtype = numpy.dtype(cnt.dtype).name
            except Exception:
                dtype = "float64"
            ctrl = getattr(cnt, "_counter_controller", None)
            counters.append({
                "fullname": cnt.fullname,
                "controller": getattr(ctrl, "name", "") or "",
                "shape": list(getattr(cnt, "shape", None) or []),
                "dtype": dtype,
            })
        return counters

    def axes(self):
        """ provides the axis names of the session

        :returns: axis names
        :rtype: :obj:`list` <:obj:`str`>
        """
        from bliss import global_map
        return [axis.name for axis in global_map.get_axes_iter()]

    def mntgrps(self):
        """ provides the measurement groups of the session

        :returns: ``{name: {"available": [...], "enabled": [...]}}``
        :rtype: :obj:`dict` <:obj:`str`, :obj:`dict`>
        """
        from bliss.common import measurementgroup
        return {mg.name: {"available": list(mg.available),
                          "enabled": list(mg.enabled)}
                for mg in measurementgroup.get_all()}

    def activeMntGrp(self):
        """ provides the active measurement group name

        :returns: measurement group name
        :rtype: :obj:`str`
        """
        from bliss.common import measurementgroup
        return measurementgroup.get_active_name()

    def selectChannels(self, name, fullnames):
        """ enables only the given counters of a measurement group,
            the group is created if it does not exist

        :param name: measurement group name
        :type name: :obj:`str`
        :param fullnames: counter full names
        :type fullnames: :obj:`list` <:obj:`str`>
        """
        from bliss.common import measurementgroup
        mgs = {mg.name: mg for mg in measurementgroup.get_all()}
        if name not in mgs:
            measurementgroup.MeasurementGroup(
                name, {"counters": list(fullnames)})
            return
        mg = mgs[name]
        missing = [fn for fn in fullnames if fn not in mg.available]
        if missing:
            from bliss import global_map
            counters = [cnt for cnt in global_map.get_counters_iter()
                        if cnt.fullname in missing]
            if counters:
                mg.add(*counters)
        mg.disable_all()
        names = [fn for fn in fullnames if fn in mg.available]
        if names:
            mg.enable(*names)

    def scanSaving(self):
        """ provides the scan directory and file of SCAN_SAVING

        :returns: dictionary with ``ScanDir``, ``ScanFile`` and
                  ``data_policy``
        :rtype: :obj:`dict` <:obj:`str`, `any`>
        """
        from bliss import current_session
        ss = current_session.scan_saving
        filename = None
        try:
            filename = ss.filename
        except Exception:
            pass
        if not filename:
            filename = ss.data_fullpath
        return {"ScanDir": ss.get_path(),
                "ScanFile": [os.path.basename(filename)] if filename else [],
                "data_policy": str(ss.data_policy)}

    def setScanSaving(self, scandir=None, scanfile=None):
        """ sets the scan directory and file of SCAN_SAVING

        :param scandir: scan directory
        :type scandir: :obj:`str`
        :param scanfile: scan file name, its extension is skipped
        :type scanfile: :obj:`str`
        :raises: :exc:`PermissionError` for the ESRF data policy
        """
        from bliss import current_session
        ss = current_session.scan_saving
        if str(ss.data_policy).upper() == "ESRF":
            raise PermissionError(
                "SCAN_SAVING paths are defined by the ESRF data policy")
        if scandir and scandir != ss.get_path():
            ss.base_path = scandir
            ss.template = ""
        if scanfile:
            name = os.path.splitext(os.path.basename(scanfile))[0]
            if name:
                ss.data_filename = name

    def setActiveMntGrp(self, name):
        """ activates a measurement group

        :param name: measurement group name
        :type name: :obj:`str`
        """
        from bliss.common import measurementgroup
        measurementgroup.set_active_name(name)


class NXSBlissSession(object):

    """ publishes a BLISS session for the selector
        and applies the selected channels
    """

    def __init__(self, session=None, redis=None, api=None, userdata=None,
                 canfail=True, log=None):
        """ constructor

        :param session: session name, the current session if None
        :type session: :obj:`str`
        :param redis: Redis connection, see
                      :func:`nxsrecconfig.BlissBackend.redisConnection`
        :type redis: :class:`redis.Redis`
        :param api: BLISS session access
        :type api: :class:`BlissAPI`
        :param userdata: user data of CLIENT datasources read by
                         datasource counters or a function returning them
        :type userdata: :obj:`dict` <:obj:`str`, `any`> or callable
        :param canfail: fill values of datasources which cannot be read,
                        stop the scan otherwise
        :type canfail: :obj:`bool`
        :param log: logger
        :type log: :class:`logging.Logger`
        """
        #: (:class:`logging.Logger`) logger
        self.log = log or logging.getLogger("nxsrecconfig")
        #: (:class:`BlissAPI`) BLISS session access
        self.api = api or BlissAPI(userdata=userdata, canfail=canfail)
        #: (:obj:`str`) session name
        self.session = session or self.api.session()
        #: (:class:`redis.Redis`) Redis connection
        self.redis = redis if redis is not None else redisConnection()
        #: (:obj:`dict` <:obj:`str`, :obj:`str`>) datasource counters
        self.__dscounters = {}
        #: (:obj:`dict` <:obj:`str`, `any`>) published scan paths
        self.__paths = {}
        #: (:class:`nxsrecconfig.BlissBackend.BlissBackend`) environment
        #:     of the session, without notifications of the session
        self.backend = BlissBackend(redis=self.redis, notify=False)

    def elements(self):
        """ provides the session elements in the format of Sardana pools

        :returns: element lists
        :rtype: :obj:`dict` <:obj:`str`, :obj:`list` <:obj:`dict`>>
        """
        channels = []
        controller = getattr(self.api, "controller", None)
        for cnt in self.api.counters():
            # datasource counters are selected as datasources
            if controller and cnt.get("controller") == controller:
                continue
            channels.append({
                "name": channelName(cnt["fullname"]),
                "full_name": cnt["fullname"],
                "source": cnt["fullname"],
                "controller": cnt.get("controller", ""),
                "type": "CounterTimer",
                "interfaces": ["Counter", "ExpChannel"],
                "shape": cnt.get("shape", []),
                "dtype": cnt.get("dtype", "float64"),
            })
        motors = [{
            "name": channelName(axis),
            "full_name": axis,
            "source": axis,
            "controller": "",
            "type": "Motor",
            "interfaces": ["Motor", "Moveable"],
        } for axis in self.api.axes()]
        mntgrps = [{
            "name": name,
            "full_name": name,
            "type": "MeasurementGroup",
            "channels": mg["enabled"],
        } for name, mg in self.api.mntgrps().items()]
        return {
            "AcqChannelList": channels,
            "ExpChannelList": channels,
            "MotorList": motors,
            "MeasurementGroupList": mntgrps,
        }

    def publish(self):
        """ publishes the session elements and its active measurement group
        """
        elements = self.elements()
        key = sessionKey(self.session, "elements")
        self.redis.delete(key)
        self.redis.hset(key, mapping={
            name: json.dumps(value) for name, value in elements.items()})
        active = self.api.activeMntGrp()
        if active:
            if self.backend.getEnv("ActiveMntGrp", self.session) is None:
                self.backend.setEnv("ActiveMntGrp", active, self.session)
        self.publishPaths()

    def signature(self):
        """ provides a signature of the session elements

        :returns: signature changed by changes of counters, axes and
                  measurement groups
        :rtype: :obj:`str`
        """
        return hashlib.sha1(json.dumps(
            self.elements(), sort_keys=True, default=str).encode()
        ).hexdigest()

    def publishPaths(self):
        """ publishes the scan directory and file of SCAN_SAVING
        """
        try:
            paths = self.api.scanSaving()
        except Exception as e:
            self.log.debug("nxsrecconfig: SCAN_SAVING: %s" % e)
            return
        values = {"ScanDir": paths.get("ScanDir"),
                  "ScanFile": paths.get("ScanFile")}
        self.backend.setEnvs(values, self.session)
        self.__paths = values

    def applyPaths(self):
        """ applies the scan directory and file changed by the selector
            to SCAN_SAVING

        :returns: True if SCAN_SAVING was changed
        :rtype: :obj:`bool`
        """
        if not self.__paths:
            return False
        scandir = self.backend.getEnv("ScanDir", self.session)
        scanfile = self.backend.getEnv("ScanFile", self.session)
        if isinstance(scanfile, (list, tuple)):
            scanfile = scanfile[0] if scanfile else None
        published = self.__paths.get("ScanFile") or [None]
        newdir = scandir if scandir != self.__paths.get("ScanDir") \
            else None
        newfile = scanfile if scanfile != published[0] else None
        if not newdir and not newfile:
            return False
        try:
            self.api.setScanSaving(newdir, newfile)
        except Exception as e:
            self.log.warning(
                "nxsrecconfig: scan paths of the selector are not "
                "applied: %s" % e)
            return False
        return True

    @property
    def scanRunning(self):
        """ the session runs a scan

        :returns: True if a scan is running
        :rtype: :obj:`bool`
        """
        return bool(self.backend.getEnv("ScanRunning", self.session))

    def pending(self):
        """ provides measurement groups with selections not applied

        :returns: measurement group names
        :rtype: :obj:`list` <:obj:`str`>
        """
        return sorted(self.redis.hgetall(
            sessionKey(self.session, "mntgrps")) or {})

    def scanStarted(self, scan_info):
        """ publishes a started scan

        :param scan_info: scan info
        :type scan_info: :obj:`dict` <:obj:`str`, `any`>
        """
        values = {"ScanRunning": {
            "session": self.session,
            "number": scan_info.get("scan_nb"),
            "since": datetime.datetime.now().astimezone().isoformat()}}
        if scan_info.get("scan_nb") is not None:
            values["ScanID"] = scan_info.get("scan_nb")
        self.backend.setEnvs(values, self.session)
        pending = self.pending()
        if pending:
            self.log.warning(
                "nxsrecconfig: the selection of %s was changed after "
                "the scan was created, it is applied after the scan"
                % ", ".join(pending))

    def scanEnded(self, scan_info=None):
        """ publishes the end of a scan

        :param scan_info: scan info
        :type scan_info: :obj:`dict` <:obj:`str`, `any`>
        """
        self.backend.usetEnv("ScanRunning", self.session)

    def apply(self):
        """ applies the selected channels and datasources to
            the measurement groups and activates the measurement group
            of the selector

        :returns: names of updated measurement groups
        :rtype: :obj:`list` <:obj:`str`>
        """
        self.applyPaths()
        key = sessionKey(self.session, "mntgrps")
        requests = self.redis.hgetall(key) or {}
        dsrequests = {
            name: json.loads(value) for name, value in
            (self.redis.hgetall(
                sessionKey(self.session, "datasources")) or {}).items()}
        datasources = {}
        for dss in dsrequests.values():
            datasources.update(dss or {})
        if datasources or self.__dscounters:
            self.__dscounters = self.api.setDataSources(datasources)
        dscounters = self.__dscounters
        updated = []
        for name, value in requests.items():
            fullnames = list(json.loads(value))
            fullnames.extend(
                dscounters[ds] for ds in sorted(dsrequests.get(name) or {})
                if ds in dscounters and dscounters[ds] not in fullnames)
            self.api.selectChannels(name, fullnames)
            updated.append(name)
        if requests:
            self.redis.hdel(key, *requests.keys())
        active = self.backend.getEnv("ActiveMntGrp", self.session)
        if active and active != self.api.activeMntGrp() and \
           active in self.api.mntgrps():
            self.api.setActiveMntGrp(active)
        return sorted(updated)

    def sync(self):
        """ applies the selection and publishes the session

        :returns: names of updated measurement groups
        :rtype: :obj:`list` <:obj:`str`>
        """
        updated = self.apply()
        self.publish()
        return updated


class NXSBlissWatcher(object):

    """ applies changes of the selector to a BLISS session

    The selector notifies the session by the Redis channel
    ``nxsselector:<session>:changed``.  Changes are applied when no scan
    is running.  Changes of the session elements, i.e. counters, axes
    and measurement groups, are published.
    """

    def __init__(self, session, interval=2.0, log=None):
        """ constructor

        :param session: BLISS session of the selector
        :type session: :class:`NXSBlissSession`
        :param interval: interval of checks in seconds
        :type interval: :obj:`float`
        :param log: logger
        :type log: :class:`logging.Logger`
        """
        #: (:class:`NXSBlissSession`) session
        self.session = session
        #: (:obj:`float`) interval of checks in seconds
        self.interval = interval
        #: (:class:`logging.Logger`) logger
        self.log = log or session.log
        #: (:obj:`bool`) changes of the selector to be applied
        self.changed = False
        #: (:obj:`str`) signature of the published elements
        self.signature = None
        #: (:class:`redis.client.PubSub`) subscription
        self.__pubsub = None
        #: (`any`) greenlet or thread of the watcher
        self.__task = None
        #: (:obj:`bool`) stop flag
        self.__stop = False

    def subscribe(self):
        """ subscribes the notifications of the selector
        """
        if self.__pubsub is None:
            self.__pubsub = self.session.redis.pubsub(
                ignore_subscribe_messages=True)
            self.__pubsub.subscribe(
                sessionKey(self.session.session, "changed"))

    def unsubscribe(self):
        """ unsubscribes the notifications of the selector
        """
        if self.__pubsub is not None:
            try:
                self.__pubsub.unsubscribe()
                self.__pubsub.close()
            except Exception:
                pass
            self.__pubsub = None

    def poll(self, timeout=0.0):
        """ checks notifications and session changes once

        :param timeout: time to wait for notifications in seconds
        :type timeout: :obj:`float`
        :returns: True if the session was synchronized
        :rtype: :obj:`bool`
        """
        self.subscribe()
        message = self.__pubsub.get_message(timeout=timeout)
        while message is not None:
            if message.get("type") == "message":
                self.changed = True
            message = self.__pubsub.get_message(timeout=0)
        if self.session.scanRunning:
            return False
        if self.changed:
            self.changed = False
            self.session.sync()
            self.signature = self.session.signature()
            return True
        signature = self.session.signature()
        if signature != self.signature:
            self.session.publish()
            self.signature = signature
        return False

    def run(self):
        """ checks notifications and session changes until stopped
        """
        while not self.__stop:
            try:
                self.poll(self.interval)
            except Exception as e:
                self.log.warning("nxsrecconfig: watcher: %s" % e)
                self.__sleep(self.interval)

    @classmethod
    def __sleep(cls, seconds):
        """ sleeps cooperatively

        :param seconds: time in seconds
        :type seconds: :obj:`float`
        """
        try:
            import gevent
            gevent.sleep(seconds)
        except ImportError:
            import time
            time.sleep(seconds)

    def start(self):
        """ starts the watcher in a greenlet, or a thread without gevent
        """
        if self.__task is not None:
            return
        self.__stop = False
        self.subscribe()
        try:
            import gevent
            self.__task = gevent.spawn(self.run)
        except ImportError:
            import threading
            self.__task = threading.Thread(target=self.run, daemon=True)
            self.__task.start()

    def stop(self):
        """ stops the watcher
        """
        self.__stop = True
        task = self.__task
        self.__task = None
        if task is not None:
            if hasattr(task, "kill"):
                task.kill()
            else:
                task.join(self.interval + 1)
        self.unsubscribe()


class NXSNexDatas(object):

    """ NeXus profiles of the selector in a BLISS session,
        see :func:`setup_nexdatas`
    """

    def __init__(self, session, meta=None, watcher=None):
        """ constructor

        :param session: BLISS session of the selector
        :type session: :class:`NXSBlissSession`
        :param meta: scan metadata of the profiles
        :type meta: :class:`nxsrecconfig.BlissScanMeta.NXSScanMeta`
        :param watcher: watcher of the selector
        :type watcher: :class:`NXSBlissWatcher`
        """
        #: (:class:`NXSBlissSession`) session
        self.session = session
        #: (:class:`nxsrecconfig.BlissScanMeta.NXSScanMeta`) scan metadata
        self.meta = meta
        #: (:class:`NXSBlissWatcher`) watcher
        self.watcher = watcher

    def sync(self):
        """ applies the selection and publishes the session

        :returns: names of updated measurement groups
        :rtype: :obj:`list` <:obj:`str`>
        """
        return self.session.sync()

    def stop(self):
        """ stops the watcher and unregisters the scan metadata
        """
        if self.watcher is not None:
            self.watcher.stop()
        if self.meta is not None:
            self.meta.unregister()


def setup_nexdatas(selector=None, links=False, userdata=None, canfail=True,
                   profile=None, session=None, watch=True, interval=2.0,
                   scanmeta=True, redis=None, api=None, log=None):
    """ sets up NeXus profiles of the selector in a BLISS session

    It synchronizes the session with the selector, registers the scan
    metadata of the profiles and starts a watcher of the selector.

    :param selector: NXSRecSelector device name or proxy
    :type selector: :obj:`str` or `any`
    :param links: add STEP fields of the profiles as links to scan data
    :type links: :obj:`bool`
    :param userdata: user data of CLIENT datasources
                     or a function without arguments returning them
    :type userdata: :obj:`dict` <:obj:`str`, `any`> or callable
    :param canfail: fill values of datasources which cannot be read,
                    stop the scan otherwise
    :type canfail: :obj:`bool`
    :param profile: profile name or a function of a scan returning it,
                    the active measurement group if None
    :type profile: :obj:`str` or callable
    :param session: session name, the current session if None
    :type session: :obj:`str`
    :param watch: start the watcher of the selector
    :type watch: :obj:`bool`
    :param interval: interval of the watcher checks in seconds
    :type interval: :obj:`float`
    :param scanmeta: register the scan metadata of the profiles
    :type scanmeta: :obj:`bool`
    :param redis: Redis connection
    :type redis: :class:`redis.Redis`
    :param api: BLISS session access
    :type api: :class:`BlissAPI`
    :param log: logger
    :type log: :class:`logging.Logger`
    :returns: NeXus profiles in the session
    :rtype: :class:`NXSNexDatas`
    """
    nxsbliss = NXSBlissSession(session=session, redis=redis, api=api,
                               userdata=userdata, canfail=canfail, log=log)
    nxsbliss.sync()
    meta = None
    if scanmeta:
        from .BlissScanMeta import NXSScanMeta
        mdata = (lambda scan: userdata()) if callable(userdata) \
            else userdata
        meta = NXSScanMeta(selector, profile=profile, userdata=mdata,
                           log=log, session=nxsbliss)
        meta.register(links=links)
    watcher = None
    if watch:
        watcher = NXSBlissWatcher(nxsbliss, interval, log)
        watcher.signature = nxsbliss.signature()
        watcher.start()
    return NXSNexDatas(nxsbliss, meta, watcher)
