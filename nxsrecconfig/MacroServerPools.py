#!/usr/bin/env python
#   This file is part of nxsrecconfig - NeXus Sardana Recorder Settings
#
#    Copyright (C) 2014-2017 DESY, Jan Kotanski <jkotan@mail.desy.de>
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


""" sardana scan backend, i.e. macroserver and pools """

import json

try:
    import tango
except Exception:
    import PyTango as tango


from .Utils import (
    Utils, TangoUtils, MSUtils, PoolUtils, OldTangoError, PYTG_BUG_213)
from .ScanBackend import ScanBackend


class MacroServerPools(ScanBackend):

    """ sardana macro server and pools """

    #: (:obj:`str`) backend name
    name = "sardana"

    #: (:obj:`bool`) the backend provides measurement group devices
    supportsMntGrps = True

    def __init__(self, numberOfThreads):
        """ constructor

        :param numberOfThreads: number of threads
        :type numberOfThreads: :obj:`str`
        """
        ScanBackend.__init__(self, numberOfThreads)

        #: (:class:`tango.Database`) tango database
        self.__db = tango.Database()

        #: (:obj:`str`) macro server device name
        self.__macroserver = ""
        #: (:obj:`list` <:obj:`tango.DeviceProxy`>) pool instances
        self.__pools = []

    def defaultDoor(self, db):
        """ provides the default door

        :param db: tango database
        :type db: :class:`tango.Database`
        :returns: door device name
        :rtype: :obj:`str`
        """
        return TangoUtils.getDeviceName(db, "Door")

    def isDoorValid(self, door):
        """ checks if the door has a macro server

        :param door: door device name
        :type door: :obj:`str`
        :returns: True if valid
        :rtype: :obj:`bool`
        """
        if door:
            if ':' in door.split('/')[0] and len(door.split('/')) > 1:
                host, port = door.split('/')[0].split(':')
                db = tango.Database(host, int(port))
                macroserver = MSUtils.getMacroServer(db, door, False)
            else:
                macroserver = MSUtils.getMacroServer(self.__db, door, False)
            if not macroserver:
                door = ''
        return bool(door)

    def updateMacroServer(self, door):
        """ updates MacroServer and sardana pools for given door

        :param door: door device name
        :type door: :obj:`str`
        :returns: macroserver device name
        :rtype: :obj:`str`
        """
        self.__macroserver = ""
        self.__pools = []
        host = None
        port = None
        if not door:
            raise Exception("Door '%s' cannot be found" % door)
        if ":" in door.split("/")[0] and len(door.split("/")) > 1:
            host, port = door.split("/")[0].split(":")
            db = tango.Database(host, int(port))
            macroserver = MSUtils.getMacroServer(db, door)
        else:
            macroserver = MSUtils.getMacroServer(self.__db, door)
        msp = TangoUtils.openProxy(macroserver)
        pnames = msp.get_property("PoolNames")["PoolNames"]
        if not pnames:
            pnames = []
        poolNames = list(
            set(pnames) - set(self.poolBlacklist))
        poolNames = ["%s/%s" % (door.split("/")[0], pn)
                     if (host and ":" not in pn)
                     else pn
                     for pn in poolNames]
        self.__pools = TangoUtils.getProxies(poolNames)
        self.__macroserver = macroserver
        return self.__macroserver

    def getMacroServer(self, door):
        """ door macro server device name

        :param door: door device name
        :type door: :obj:`str`
        :returns: macroserver device name
        :rtype: :obj:`str`
        """
        if not self.__macroserver:
            self.updateMacroServer(door)
        return self.__macroserver

    def getPools(self, door):
        """ door pool device proxies

        :param door: door device name
        :type door: :obj:`str`
        :returns: pool device proxies
        :rtype: :obj:`list` <:obj:`tango.DeviceProxy`>
        """
        if not self.__pools:
            self.updateMacroServer(door)
        return self.__pools

    def nonExistingChannels(self, door, channels):
        """ provides the channels which are not found in the pools

        :param door: door device name
        :type door: :obj:`str`
        :param channels: channel names
        :type channels: :obj:`list` <:obj:`str`>
        :returns: channels not found in the pools
        :rtype: :obj:`list` <:obj:`str`>
        """
        pools = self.getPools(door)
        fnames = PoolUtils.getFullDeviceNames(pools, channels)
        return [dev for dev in channels if dev not in fnames.keys()]

    def channelSource(self, name):
        """ provides the tango source of a pool channel

        :param name: channel name
        :type name: :obj:`str`
        :returns: tango attribute name or None
        :rtype: :obj:`str`
        """
        return PoolUtils.getSource(name)

    def isDoorRunning(self, ms):
        """ check if any door server is running

        :param ms: macroserver device name
        :type ms: :obj:`str`
        :returns: if any door running
        :rtype: :obj:`bool`
        """
        status = False
        error = None
        if ms:
            msp = TangoUtils.openProxy(ms)
            doors = msp.doorList
            for door in doors:
                try:
                    dp = tango.DeviceProxy(door)
                    if dp.state() == tango.DevState.RUNNING:
                        status = True
                        break
                except Exception as e:
                    error = str(e)
                if error:
                    raise Exception(
                        "Cannot connect to the door: %s" % error)
        return status

    def getSelectorEnv(self, door, names, data):
        """ imports Environment Data

        :param door: door device
        :type door: :obj:`str`
        :param names: names of required variables
        :type names: :obj:`list` <:obj:`str`>
        :param data: dictionary with resulting data
        :type data: :obj:`dict` <:obj:`str` , `any`>
        """
        msp = TangoUtils.openProxy(self.getMacroServer(door))
        if PYTG_BUG_213:
            raise OldTangoError(
                "Reading Encoded Attributes not supported in tango < 9.2.5")
        rec = msp.Environment
        if rec[0] == 'pickle':
            dc = Utils.pickleloads(rec[1])
            if 'new' in dc.keys():
                self._readSelectorEnv(dc['new'], names, data)

    def setSelectorEnv(self, door, data, cmddata=None):
        """ exports all Environment Data

        :param door: door device
        :type door: :obj:`str`
        :param data: data dictionary
        :type data: :obj:`dict` <:obj:`str` , `any`>
        :param cmddata: command data dictionary
        :type cmddata: :obj:`dict` <:obj:`str` , `any`>
        """
        msp = TangoUtils.openProxy(self.getMacroServer(door))
        if PYTG_BUG_213:
            raise OldTangoError(
                "Reading Encoded Attributes not supported in tango < 9.2.5")
        rec = msp.Environment
        if rec[0] == 'pickle':
            dc = Utils.pickleloads(rec[1])
            if 'new' in dc.keys():
                MSUtils.writeEnvAttr(
                    {'new': self._selectorEnvUpdate(data, cmddata)}, msp)

    def getScanEnv(self, door):
        """ fetches Scan Environment Data

        :param door: door device
        :type door: :obj:`str`
        :returns: JSON String with important variables
        :rtype: :obj:`str`
        """
        res = {}
        msp = TangoUtils.openProxy(self.getMacroServer(door))
        if PYTG_BUG_213:
            raise OldTangoError(
                "Reading Encoded Attributes not supported in tango < 9.2.5")
        rec = msp.Environment
        if rec[0] == 'pickle':
            dc = Utils.pickleloads(rec[1])
            if 'new' in dc.keys():
                res = self._readScanEnv(dc['new'])
        return json.dumps(res)

    def setScanEnv(self, door, jdata):
        """ stores Scan Environment Data

        :param door: door device
        :type door: :obj:`str`
        :param jdata: JSON String with important variables
        :type jdata: :obj:`str`
        """
        jdata = Utils.stringToDictJson(jdata)
        data = json.loads(jdata)
        scanID = -1
        msp = TangoUtils.openProxy(self.getMacroServer(door))
        if PYTG_BUG_213:
            raise OldTangoError(
                "Reading Encoded Attributes not supported in tango < 9.2.5")
        rec = msp.Environment
        if rec[0] == 'pickle':
            dc = Utils.pickleloads(rec[1])
            if 'new' in dc.keys():
                if 'ScanID' in dc['new'].keys():
                    scanID = int(dc['new']["ScanID"])
            new = self._scanEnvUpdate(data)
            if 'ScanID' in new.keys():
                scanID = int(new["ScanID"])
            MSUtils.writeEnvAttr({'new': new}, msp)
        return scanID

    def getEnv(self, var, ms):
        """ provides a macroserver environment variable

        :param var: variable name
        :type var: :obj:`str`
        :param ms: macroserver device name
        :type ms: :obj:`str`
        :returns: variable value
        :rtype: `any`
        """
        return MSUtils.getEnv(var, ms)

    def setEnv(self, var, value, ms):
        """ sets a macroserver environment variable

        :param var: variable name
        :type var: :obj:`str`
        :param value: variable value
        :type value: `any`
        :param ms: macroserver device name
        :type ms: :obj:`str`
        """
        MSUtils.setEnv(var, value, ms)

    def setEnvs(self, varvalues, ms):
        """ sets macroserver environment variables

        :param varvalues: variable names and values
        :type varvalues: :obj:`dict` <:obj:`str`, `any`>
        :param ms: macroserver device name
        :type ms: :obj:`str`
        """
        MSUtils.setEnvs(varvalues, ms)

    def usetEnv(self, var, ms):
        """ unsets a macroserver environment variable

        :param var: variable name
        :type var: :obj:`str`
        :param ms: macroserver device name
        :type ms: :obj:`str`
        """
        MSUtils.usetEnv(var, ms)

    def createMntGrp(self, pool, name, timer):
        """ creates a measurement group in the pool

        :param pool: pool proxy
        :type pool: :class:`tango.DeviceProxy`
        :param name: measurement group name
        :type name: :obj:`str`
        :param timer: timer name
        :type timer: :obj:`str`
        """
        try:
            TangoUtils.command(
                pool, "CreateMeasurementGroup", [name, timer])
        except tango.CommunicationFailed as cf:
            if len(cf.args) >= 2 and \
               cf.args[1].reason == "API_DeviceTimedOut":
                TangoUtils.wait(pool)
            else:
                raise

    def deleteMntGrp(self, pool, name):
        """ deletes a measurement group from the pool

        :param pool: pool proxy
        :type pool: :class:`tango.DeviceProxy`
        :param name: measurement group name
        :type name: :obj:`str`
        """
        TangoUtils.command(pool, "DeleteElement", Utils.tostr(name))

    def mntGrpConfiguration(self, device):
        """ provides the measurement group configuration

        :param device: measurement group device name
        :type device: :obj:`str`
        :returns: JSON configuration
        :rtype: :obj:`str`
        """
        dpmg = TangoUtils.openProxy(Utils.tostr(device))
        return Utils.tostr(dpmg.Configuration)

    def setMntGrpConfiguration(self, device, conf):
        """ sets the measurement group configuration

        :param device: measurement group device name
        :type device: :obj:`str`
        :param conf: JSON configuration
        :type conf: :obj:`str`
        :returns: the configuration read back from the device
        :rtype: :obj:`str`
        """
        dpmg = TangoUtils.openProxy(Utils.tostr(device))
        dpmg.Configuration = conf
        return Utils.tostr(dpmg.configuration)

    def testMntGrpConfiguration(self, device, conf):
        """ provides the configuration the measurement group makes of conf
            and restores its current configuration

        :param device: measurement group device name
        :type device: :obj:`str`
        :param conf: JSON configuration
        :type conf: :obj:`str`
        :returns: the configuration read back from the device
        :rtype: :obj:`str`
        """
        dpmg = TangoUtils.openProxy(Utils.tostr(device))
        oldconf = Utils.tostr(dpmg.configuration)
        dpmg.Configuration = conf
        conf = Utils.tostr(dpmg.configuration)
        dpmg.Configuration = oldconf
        return conf
