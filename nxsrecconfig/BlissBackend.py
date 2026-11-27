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

""" ``bliss`` scan backend

The selector exchanges data with BLISS sessions through Redis, so it does
not need BLISS itself.  A BLISS session publishes its channels, motors and
measurement groups with :class:`nxsrecconfig.BlissSession.NXSBlissSession`
and applies the channels selected by the selector to its measurement groups.

The target (``Door``) of the selector is the BLISS session name.
The Redis database is given by the ``NXSBLISS_REDIS_URL`` environment
variable or provided by Beacon, i.e. by the ``BEACON_HOST`` variable.

Redis keys of a session:

* ``nxsselector:<session>:elements``: published elements, i.e. JSON lists
  of ``AcqChannelList``, ``ExpChannelList``, ``MotorList`` and
  ``MeasurementGroupList`` in the format of Sardana pools
* ``nxsselector:<session>:env``: scan environment variables in JSON
* ``nxsselector:<session>:mntgrps``: BLISS full names of channels
  selected for measurement groups, in JSON
* ``nxsselector:<session>:datasources``: descriptions of STEP
  datasources without BLISS counters selected for measurement groups,
  i.e. their XML definitions, NeXus types and ranks, in JSON,
  see :mod:`nxsrecconfig.BlissDataSources`
"""

import json
import os
import re

from .Utils import Utils
from .ScanBackend import ScanBackend


#: (:obj:`str`) Redis key prefix
PREFIX = "nxsselector"

#: (:obj:`list` <:obj:`str`>) element lists of the sessions
ELEMENTLISTS = ["AcqChannelList", "ExpChannelList", "MotorList",
                "MeasurementGroupList"]


def sessionKey(session, kind):
    """ provides a Redis key of a session

    :param session: session name
    :type session: :obj:`str`
    :param kind: key kind, i.e. ``elements``, ``env`` or ``mntgrps``
    :type kind: :obj:`str`
    :returns: Redis key
    :rtype: :obj:`str`
    """
    return "%s:%s:%s" % (PREFIX, session, kind)


def channelName(fullname):
    """ provides a selector channel name of a BLISS channel

    NeXus names and datasource names cannot contain ``:`` or ``.``

    :param fullname: BLISS full name, e.g. ``diode:diode``
    :type fullname: :obj:`str`
    :returns: channel name, e.g. ``diode_diode``
    :rtype: :obj:`str`
    """
    return re.sub(r"[^0-9a-zA-Z_]+", "_", str(fullname))


def redisConnection(url=None):
    """ opens the Redis connection of BLISS

    :param url: Redis URL, from ``NXSBLISS_REDIS_URL`` or Beacon if None
    :type url: :obj:`str`
    :returns: Redis connection
    :rtype: :class:`redis.Redis`
    """
    import redis
    url = url or os.environ.get("NXSBLISS_REDIS_URL")
    if not url:
        from blissdata.beacon.data import BeaconData
        url = BeaconData().get_redis_db()
    return redis.Redis.from_url(url, decode_responses=True)


def _decode(value, default=None):
    """ decodes a JSON value

    :param value: JSON string or None
    :type value: :obj:`str`
    :param default: default value
    :type default: `any`
    :returns: decoded value
    :rtype: `any`
    """
    if value is None:
        return default
    try:
        return json.loads(value)
    except Exception:
        return default


class BlissPool(object):

    """ elements of a BLISS session in the format of Sardana pools,
        used by :class:`nxsrecconfig.Utils.PoolUtils`
    """

    def __init__(self, session, elements):
        """ constructor

        :param session: session name
        :type session: :obj:`str`
        :param elements: element lists, i.e. lists of dictionaries
        :type elements: :obj:`dict` <:obj:`str`, :obj:`list`>
        """
        #: (:obj:`str`) session name
        self.session = session
        for listattr in ELEMENTLISTS:
            setattr(self, listattr, [
                json.dumps(elm) for elm in elements.get(listattr) or []])

    def name(self):
        """ provides the pool name

        :returns: session name
        :rtype: :obj:`str`
        """
        return self.session


class BlissBackend(ScanBackend):

    """ scan backend of BLISS sessions
    """

    #: (:obj:`str`) backend name
    name = "bliss"

    #: (:obj:`bool`) the backend provides measurement group devices
    supportsMntGrps = False

    #: (:obj:`bool`) the backend selects channels of its measurement groups
    selectsChannels = True

    #: (:obj:`list` <:obj:`str`>) types of STEP datasources without
    #:   BLISS counters which are read by BLISS sessions
    dataSourceTypes = ["TANGO", "DB", "PYEVAL", "CLIENT"]

    def __init__(self, numberOfThreads=None, redis=None):
        """ constructor

        :param numberOfThreads: number of threads
        :type numberOfThreads: :obj:`str`
        :param redis: Redis connection, see :func:`redisConnection`
        :type redis: :class:`redis.Redis`
        """
        ScanBackend.__init__(self, numberOfThreads)
        self.__redis = redis

    @property
    def redis(self):
        """ Redis connection

        :returns: Redis connection
        :rtype: :class:`redis.Redis`
        """
        if self.__redis is None:
            self.__redis = redisConnection()
        return self.__redis

    def sessions(self):
        """ provides names of the published sessions

        :returns: session names
        :rtype: :obj:`list` <:obj:`str`>
        """
        pattern = re.compile(
            r"^%s:(.+):elements$" % re.escape(PREFIX))
        names = []
        for key in self.redis.scan_iter(sessionKey("*", "elements")):
            found = pattern.match(Utils.tostr(key))
            if found:
                names.append(found.group(1))
        return sorted(names)

    def elements(self, session):
        """ provides the published elements of a session

        :param session: session name
        :type session: :obj:`str`
        :returns: element lists
        :rtype: :obj:`dict` <:obj:`str`, :obj:`list` <:obj:`dict`>>
        """
        if not session:
            return {}
        data = self.redis.hgetall(sessionKey(session, "elements")) or {}
        return {Utils.tostr(key): _decode(value, [])
                for key, value in data.items()}

    def defaultDoor(self, db):
        """ provides the default target, i.e. the first published session

        :param db: tango database
        :type db: :class:`tango.Database`
        :returns: session name
        :rtype: :obj:`str`
        """
        sessions = self.sessions()
        return sessions[0] if sessions else ""

    def isDoorValid(self, door):
        """ checks if the session is published

        :param door: session name
        :type door: :obj:`str`
        :returns: True if the session is published
        :rtype: :obj:`bool`
        """
        return bool(door) and bool(
            self.redis.exists(sessionKey(door, "elements")))

    def updateMacroServer(self, door):
        """ updates the scan server, i.e. the session

        :param door: session name
        :type door: :obj:`str`
        :returns: session name
        :rtype: :obj:`str`
        """
        return door or ""

    def getMacroServer(self, door):
        """ provides the scan server, i.e. the session

        :param door: session name
        :type door: :obj:`str`
        :returns: session name
        :rtype: :obj:`str`
        """
        return door or ""

    def getPools(self, door):
        """ provides the elements of the session as a pool

        :param door: session name
        :type door: :obj:`str`
        :returns: list with the session pool
        :rtype: :obj:`list` <:class:`BlissPool`>
        """
        elements = self.elements(door)
        if not elements:
            return []
        return [BlissPool(door, elements)]

    def isDoorRunning(self, ms):
        """ checks if a scan is running

        :param ms: session name
        :type ms: :obj:`str`
        :returns: True if the session publishes a running scan
        :rtype: :obj:`bool`
        """
        return bool(self.getEnv("ScanRunning", ms))

    def __channels(self, session, listattrs=None):
        """ provides the published channels and motors of a session

        :param session: session name
        :type session: :obj:`str`
        :param listattrs: element lists, channels and motors if None
        :type listattrs: :obj:`list` <:obj:`str`>
        :returns: channels and motors by names
        :rtype: :obj:`dict` <:obj:`str`, :obj:`dict`>
        """
        elements = self.elements(session)
        channels = {}
        for listattr in listattrs or ["AcqChannelList", "MotorList"]:
            for elm in elements.get(listattr) or []:
                channels[elm["name"]] = elm
        return channels

    def nonExistingChannels(self, door, channels):
        """ provides the channels which are not published by the session

        :param door: session name
        :type door: :obj:`str`
        :param channels: channel names
        :type channels: :obj:`list` <:obj:`str`>
        :returns: channels which do not exist
        :rtype: :obj:`list` <:obj:`str`>
        """
        existing = self.__channels(door)
        return [ch for ch in channels if ch not in existing]

    def channelSource(self, name):
        """ provides the tango source of a channel

        BLISS channels are written from scan data, i.e. by CLIENT
        datasources

        :param name: channel name
        :type name: :obj:`str`
        :returns: None
        :rtype: :obj:`str`
        """
        return None

    def getEnv(self, var, ms):
        """ provides a scan environment variable

        :param var: variable name
        :type var: :obj:`str`
        :param ms: session name
        :type ms: :obj:`str`
        :returns: variable value or None
        :rtype: `any`
        """
        if not ms:
            return None
        return _decode(self.redis.hget(sessionKey(ms, "env"), var))

    def setEnv(self, var, value, ms):
        """ sets a scan environment variable

        :param var: variable name
        :type var: :obj:`str`
        :param value: variable value
        :type value: `any`
        :param ms: session name
        :type ms: :obj:`str`
        """
        self.setEnvs({var: value}, ms)

    def setEnvs(self, varvalues, ms):
        """ sets scan environment variables

        :param varvalues: variable names and values
        :type varvalues: :obj:`dict` <:obj:`str`, `any`>
        :param ms: session name
        :type ms: :obj:`str`
        """
        if not ms or not varvalues:
            return
        self.redis.hset(sessionKey(ms, "env"), mapping={
            var: json.dumps(value, default=str)
            for var, value in varvalues.items()})

    def usetEnv(self, var, ms):
        """ unsets a scan environment variable

        :param var: variable name
        :type var: :obj:`str`
        :param ms: session name
        :type ms: :obj:`str`
        """
        if ms:
            self.redis.hdel(sessionKey(ms, "env"), var)

    def __env(self, ms):
        """ provides the scan environment

        :param ms: session name
        :type ms: :obj:`str`
        :returns: scan environment
        :rtype: :obj:`dict` <:obj:`str`, `any`>
        """
        if not ms:
            return {}
        data = self.redis.hgetall(sessionKey(ms, "env")) or {}
        return {Utils.tostr(key): _decode(value)
                for key, value in data.items()}

    def getSelectorEnv(self, door, names, data):
        """ provides selector variables from the scan environment

        :param door: session name
        :type door: :obj:`str`
        :param names: names of variables
        :type names: :obj:`list` <:obj:`str`>
        :param data: dictionary to be filled with the variables
        :type data: :obj:`dict` <:obj:`str`, `any`>
        """
        self._readSelectorEnv(self.__env(door), names, data)

    def setSelectorEnv(self, door, data, cmddata=None):
        """ stores selector variables in the scan environment

        :param door: session name
        :type door: :obj:`str`
        :param data: variables
        :type data: :obj:`dict` <:obj:`str`, `any`>
        :param cmddata: command variables
        :type cmddata: :obj:`dict` <:obj:`str`, `any`>
        """
        self.setEnvs(self._selectorEnvUpdate(data, cmddata), door)

    def getScanEnv(self, door):
        """ provides scan file variables of the scan environment

        :param door: session name
        :type door: :obj:`str`
        :returns: JSON string with the variables
        :rtype: :obj:`str`
        """
        return json.dumps(self._readScanEnv(self.__env(door)))

    def setScanEnv(self, door, jdata):
        """ sets scan file variables of the scan environment

        :param door: session name
        :type door: :obj:`str`
        :param jdata: JSON string with the variables
        :type jdata: :obj:`str`
        :returns: scan id or -1
        :rtype: :obj:`int`
        """
        data = json.loads(Utils.stringToDictJson(jdata))
        scanID = -1
        env = self.__env(door)
        if 'ScanID' in env.keys():
            scanID = int(env["ScanID"])
        new = self._scanEnvUpdate(data)
        if 'ScanID' in new.keys():
            scanID = int(new["ScanID"])
        self.setEnvs(new, door)
        return scanID

    def selectChannels(self, ms, mntgrp, channels):
        """ requests channels of a measurement group of the session

        Motors and unknown channels are skipped.
        The session applies the request,
        see :meth:`nxsrecconfig.BlissSession.NXSBlissSession.apply`

        :param ms: session name
        :type ms: :obj:`str`
        :param mntgrp: measurement group name
        :type mntgrp: :obj:`str`
        :param channels: ordered channel names
        :type channels: :obj:`list` <:obj:`str`>
        """
        if not ms or not mntgrp:
            return
        # measurement groups of BLISS contain only counters
        existing = self.__channels(ms, ["AcqChannelList"])
        fullnames = [existing[ch]["full_name"] for ch in channels
                     if ch in existing]
        self.redis.hset(sessionKey(ms, "mntgrps"), mntgrp,
                        json.dumps(fullnames))

    def selectDataSources(self, ms, mntgrp, datasources):
        """ requests STEP datasources without BLISS counters
            to be read in scans of a measurement group of the session

        The session creates BLISS counters of the datasources,
        see :meth:`nxsrecconfig.BlissSession.NXSBlissSession.apply`

        :param ms: session name
        :type ms: :obj:`str`
        :param mntgrp: measurement group name
        :type mntgrp: :obj:`str`
        :param datasources: datasource descriptions by datasource names,
                            i.e. dictionaries with ``xml`` definitions,
                            ``nxtype`` NeXus types and ``rank``
        :type datasources: :obj:`dict` <:obj:`str`, :obj:`dict`>
        """
        if not ms or not mntgrp:
            return
        self.redis.hset(sessionKey(ms, "datasources"), mntgrp,
                        json.dumps(datasources or {}))

    def __nomntgrps(self, *args, **kwargs):
        """ measurement group devices are not supported

        :raises: :exc:`NotImplementedError`
        """
        raise NotImplementedError(
            "Measurement group devices are not supported by the '%s' backend"
            % self.name)

    createMntGrp = __nomntgrps
    deleteMntGrp = __nomntgrps
    mntGrpConfiguration = __nomntgrps
    setMntGrpConfiguration = __nomntgrps
    testMntGrpConfiguration = __nomntgrps
