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
"""

import json

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
                 canfail=True):
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
        """
        #: (:class:`BlissAPI`) BLISS session access
        self.api = api or BlissAPI(userdata=userdata, canfail=canfail)
        #: (:obj:`str`) session name
        self.session = session or self.api.session()
        #: (:class:`redis.Redis`) Redis connection
        self.redis = redis if redis is not None else redisConnection()
        #: (:obj:`dict` <:obj:`str`, :obj:`str`>) datasource counters
        self.__dscounters = {}

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
            backend = BlissBackend(redis=self.redis)
            if backend.getEnv("ActiveMntGrp", self.session) is None:
                backend.setEnv("ActiveMntGrp", active, self.session)

    def apply(self):
        """ applies the selected channels and datasources to
            the measurement groups and activates the measurement group
            of the selector

        :returns: names of updated measurement groups
        :rtype: :obj:`list` <:obj:`str`>
        """
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
        backend = BlissBackend(redis=self.redis)
        active = backend.getEnv("ActiveMntGrp", self.session)
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
