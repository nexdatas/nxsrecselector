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

""" scan backends: ``sardana``, ``bliss`` and ``null``

The ``sardana`` backend uses the Sardana MacroServer and its pools.
The ``null`` backend runs without any scan control system, e.g. to
select components for scans of other systems: it has no channels and
no measurement groups, and keeps its scan environment in memory.
The ``bliss`` backend uses BLISS sessions published in Redis,
see :mod:`nxsrecconfig.BlissBackend`.
"""

import copy
import json

from .Utils import Utils
from .ScanBackend import ScanBackend
from .MacroServerPools import MacroServerPools
from .BlissBackend import BlissBackend


class SardanaBackend(MacroServerPools):

    """ sardana scan backend, i.e. macroserver and pools """


class NullBackend(ScanBackend):

    """ scan backend without scan control system """

    #: (:obj:`str`) backend name
    name = "null"

    #: (:obj:`bool`) the backend provides measurement group devices
    supportsMntGrps = False

    def __init__(self, numberOfThreads=None):
        """ constructor

        :param numberOfThreads: number of threads
        :type numberOfThreads: :obj:`str`
        """
        ScanBackend.__init__(self, numberOfThreads)
        #: (:obj:`dict` <:obj:`str`, `any`>) scan environment
        self.__env = {}

    @property
    def environment(self):
        """ scan environment variables

        :returns: a copy of the scan environment variables
        :rtype: :obj:`dict` <:obj:`str`, `any`>
        """
        return copy.deepcopy(self.__env)

    def defaultDoor(self, db):
        """ provides the default target

        :param db: tango database
        :type db: :class:`tango.Database`
        :returns: empty string, there are no doors
        :rtype: :obj:`str`
        """
        return ""

    def isDoorValid(self, door):
        """ checks if the target is valid

        :param door: target name
        :type door: :obj:`str`
        :returns: True, any target is valid
        :rtype: :obj:`bool`
        """
        return True

    def updateMacroServer(self, door):
        """ updates the scan server for given target

        :param door: target name
        :type door: :obj:`str`
        :returns: empty string, there is no scan server
        :rtype: :obj:`str`
        """
        return ""

    def getMacroServer(self, door):
        """ provides the scan server name

        :param door: target name
        :type door: :obj:`str`
        :returns: empty string, there is no scan server
        :rtype: :obj:`str`
        """
        return ""

    def getPools(self, door):
        """ provides channel sources

        :param door: target name
        :type door: :obj:`str`
        :returns: an empty list, there are no pools
        :rtype: :obj:`list`
        """
        return []

    def isDoorRunning(self, ms):
        """ checks if a scan is running

        :param ms: scan server name
        :type ms: :obj:`str`
        :returns: False, scans are not known
        :rtype: :obj:`bool`
        """
        return False

    def nonExistingChannels(self, door, channels):
        """ provides the channels which are not known to the backend

        Channels cannot be checked without a control system,
        so all of them are taken as existing.

        :param door: target name
        :type door: :obj:`str`
        :param channels: channel names
        :type channels: :obj:`list` <:obj:`str`>
        :returns: an empty list
        :rtype: :obj:`list` <:obj:`str`>
        """
        return []

    def channelSource(self, name):
        """ provides the tango source of a channel

        :param name: channel name
        :type name: :obj:`str`
        :returns: None, sources are not known
        :rtype: :obj:`str`
        """
        return None

    def getEnv(self, var, ms=None):
        """ provides a scan environment variable

        :param var: variable name
        :type var: :obj:`str`
        :param ms: scan server name (not used)
        :type ms: :obj:`str`
        :returns: variable value or None
        :rtype: `any`
        """
        return copy.deepcopy(self.__env.get(var))

    def setEnv(self, var, value, ms=None):
        """ sets a scan environment variable

        :param var: variable name
        :type var: :obj:`str`
        :param value: variable value
        :type value: `any`
        :param ms: scan server name (not used)
        :type ms: :obj:`str`
        """
        self.__env[var] = copy.deepcopy(value)

    def setEnvs(self, varvalues, ms=None):
        """ sets scan environment variables

        :param varvalues: variable names and values
        :type varvalues: :obj:`dict` <:obj:`str`, `any`>
        :param ms: scan server name (not used)
        :type ms: :obj:`str`
        """
        for var, value in varvalues.items():
            self.setEnv(var, value)

    def usetEnv(self, var, ms=None):
        """ unsets a scan environment variable

        :param var: variable name
        :type var: :obj:`str`
        :param ms: scan server name (not used)
        :type ms: :obj:`str`
        """
        self.__env.pop(var, None)

    def getSelectorEnv(self, door, names, data):
        """ provides selector variables from the scan environment

        :param door: target name (not used)
        :type door: :obj:`str`
        :param names: names of variables
        :type names: :obj:`list` <:obj:`str`>
        :param data: dictionary to be filled with the variables
        :type data: :obj:`dict` <:obj:`str`, `any`>
        """
        self._readSelectorEnv(self.__env, names, data)

    def setSelectorEnv(self, door, data, cmddata=None):
        """ stores selector variables in the scan environment

        :param door: target name (not used)
        :type door: :obj:`str`
        :param data: variables
        :type data: :obj:`dict` <:obj:`str`, `any`>
        :param cmddata: command variables
        :type cmddata: :obj:`dict` <:obj:`str`, `any`>
        """
        self.setEnvs(self._selectorEnvUpdate(data, cmddata))

    def getScanEnv(self, door):
        """ provides scan file variables of the scan environment

        :param door: target name (not used)
        :type door: :obj:`str`
        :returns: JSON string with the variables
        :rtype: :obj:`str`
        """
        return json.dumps(self._readScanEnv(self.__env))

    def setScanEnv(self, door, jdata):
        """ sets scan file variables of the scan environment

        :param door: target name (not used)
        :type door: :obj:`str`
        :param jdata: JSON string with the variables
        :type jdata: :obj:`str`
        :returns: scan id or -1
        :rtype: :obj:`int`
        """
        data = json.loads(Utils.stringToDictJson(jdata))
        scanID = -1
        if 'ScanID' in self.__env.keys():
            scanID = int(self.__env["ScanID"])
        new = self._scanEnvUpdate(data)
        if 'ScanID' in new.keys():
            scanID = int(new["ScanID"])
        self.setEnvs(new)
        return scanID

    def __nomntgrps(self, *args, **kwargs):
        """ measurement groups are not supported

        :raises: :exc:`NotImplementedError`
        """
        raise NotImplementedError(
            "Measurement groups are not supported by the '%s' backend"
            % self.name)

    createMntGrp = __nomntgrps
    deleteMntGrp = __nomntgrps
    mntGrpConfiguration = __nomntgrps
    setMntGrpConfiguration = __nomntgrps
    testMntGrpConfiguration = __nomntgrps


#: (:obj:`dict` <:obj:`str`, :class:`ScanBackend`>) scan backends by name
BACKENDS = {
    "sardana": SardanaBackend,
    "null": NullBackend,
    "bliss": BlissBackend,
}

#: (:obj:`str`) default scan backend
DEFAULTBACKEND = "sardana"


def createBackend(name=None, numberOfThreads=None):
    """ creates a scan backend

    :param name: backend name, the default backend if None or empty
    :type name: :obj:`str`
    :param numberOfThreads: number of threads
    :type numberOfThreads: :obj:`str`
    :returns: scan backend
    :rtype: :class:`ScanBackend`
    """
    name = (name or DEFAULTBACKEND).lower()
    if name not in BACKENDS:
        raise ValueError(
            "Scan backend '%s' is not available (available: %s)"
            % (name, ", ".join(sorted(BACKENDS))))
    return BACKENDS[name](numberOfThreads)
