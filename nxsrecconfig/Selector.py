#!/usr/bin/env python
#   This file is part of nxsrecconfig - NeXus Sardana Recorder Settings
#
#    Copyright (C) 2014-2015 DESY, Jan Kotanski <jkotan@mail.desy.de>
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
## \file state.py
# component describer

"""  Selection state """

import json
import PyTango
import getpass
from .Utils import TangoUtils, PoolUtils
from .Selection import Selection


## NeXus Sardana Recorder settings
class Selector(object):
    """ selection state """

    ## constructor
    # \param configserver configuration server name
    def __init__(self, macroserverpools):

        ## macro server and pools
        self.__msp = macroserverpools
#        self.__numberOfThreads = numberOfThreads

        ##  dictionary with Settings
        self.__selection = Selection()

        ## tango database
        self.__db = PyTango.Database()

        ## module label
        self.moduleLabel = 'module'

        self.__selection.reset()

    def reset(self):
        self.__selection.reset()

    def deselect(self):
        self.__selection.deselect()

    def set(self, state):
        self.reset()
        for key in state.keys():
            if key and key[0].upper() != key[0]:
                key = key[0].upper() + key[1:]
            self.__selection[key] = state[key]
            if hasattr(self, "_Selector__reset" + key):
                getattr(self, "_Selector__reset" + key)()

    ## provides names of variables
    def keys(self):
        return self.__selection.keys()

    def get(self):
        for key in self.keys():
            if hasattr(self, "_Selector__update" + key):
                getattr(self, "_Selector__update" + key)()
        return dict(self.__selection)

    def __getitem__(self, key):
        if key in self.keys():
            if key and key[0].upper() != key[0]:
                key = key[0].upper() + key[1:]
            if hasattr(self, "_Selector__update" + key):
                getattr(self, "_Selector__update" + key)()
            return self.__selection[key]
        else:
            return None

    def __setitem__(self, key, value):
        self.__selection[key] = value
        if hasattr(self, "_Selector__reset" + key):
            getattr(self, "_Selector__reset" + key)()

    ## updates method for configDevice attribute
    def __updateConfigDevice(self):
        if "ConfigDevice" not in self.__selection.keys() \
                or not self.__selection["ConfigDevice"]:
            self.__selection["ConfigDevice"] = TangoUtils.getDeviceName(
                self.__db, "NXSConfigServer")
        name = self.__selection["ConfigDevice"]
        if name:
            if name != self.moduleLabel:
                try:
                    dp = TangoUtils.getProxies([name])
                    if not dp:
                        self.__selection["ConfigDevice"] = ''
                except (PyTango.DevFailed, PyTango.Except, PyTango.DevError):
                    self.__selection["ConfigDevice"] = ''

    ## get method for automaticDataSources attribute
    def __updateAutomaticDataSources(self):
        self.__selection.updateAutomaticDataSources(self.poolMotors())

    ## update method for orderedChannels attribute
    def __updateOrderedChannels(self):
        self.__selection.updateOrderedChannels(self.poolChannels())

    ## update method for mntGrp attribute
    def __updateMntGrp(self):
        self.__selection.updateMntGrp()

    ## update method for componentGroup attribute
    def __updateComponentGroup(self):
        self.__selection.updateComponentGroup()

    ## update method for dataSourceGroup attribute
    def __updateDataSourceGroup(self):
        self.__selection.updateDataSourceGroup(
            self.poolChannels(),
            self.configCommand("availableDataSources"))

    ## update method for door attribute
    def __updateDoor(self):
        try:
            if str(self.__selection["Door"]):
                dp = PyTango.DeviceProxy(str(self.__selection["Door"]))
                dp.ping()
        except (PyTango.DevFailed, PyTango.Except, PyTango.DevError):
            self.__selection["Door"] = ''
        if "Door" not in self.__selection.keys() \
                or not self.__selection["Door"]:
            self.__selection["Door"] = TangoUtils.getDeviceName(
                self.__db, "Door")
            self.__msp.updateMacroServer(self.__selection["Door"])

    ## update method for timeZone attribute
    def __updateTimeZone(self):
        self.__selection.updateTimeZone()

    ## update method for writerDevice attribute
    # \returns name of writerDevice
    def __updateWriterDevice(self):
        if "WriterDevice" not in self.__selection.keys() \
                or not self.__selection["WriterDevice"]:
            self.__selection["WriterDevice"] = TangoUtils.getDeviceName(
                self.__db, "NXSDataWriter")

    ## reset method for configDevice attribute
    def __resetConfigDevice(self):
        if not self.__selection["ConfigDevice"]:
            self.__selection["ConfigDevice"] = TangoUtils.getDeviceName(
                self.__db, "NXSConfigServer")

    ## set method for mntGrp attribute
    def __resetMntGrp(self):
        self.__selection.resetMntGrp()

    ## set method for timeZone attribute
    # \param name of timeZone
    def __resetTimeZone(self):
        self.__selection.resetTimeZone()

    ## set method for door attribute
    def __resetDoor(self):
        if not self.__selection["Door"]:
            self.__selection["Door"] = TangoUtils.getDeviceName(
                self.__db, "Door")

    ## set method for writerDevice attribute
    def __resetWriterDevice(self):
        if not self.__selection["WriterDevice"]:
            self.__selection["WriterDevice"] = TangoUtils.getDeviceName(
                self.__db, "NXSDataWriter")

    def resetAutomaticComponents(self, components):
        self.__selection.resetAutomaticComponents(components)

    def updateAutomaticComponents(self, channelerrors):
        datasources = set(json.loads(self["AutomaticDataSources"]))
        acpgroup = json.loads(self["AutomaticComponentGroup"])
        configdevice = self.setConfigInstance()
        return self.__msp.checkComponentChannels(
            self["Door"], configdevice, datasources, acpgroup, channelerrors)

    def getPools(self):
        return self.__msp.getPools(self["Door"])

    ## available pool channels
    # \returns pool channels of the macroserver pools
    def poolChannels(self):
        return PoolUtils.getExperimentalChannels(self.getPools())        

    ## available pool motors
    # \returns pool motors of the macroserver pools
    def poolMotors(self):
        return PoolUtils.getMotorNames(self.getPools())        

    def getMacroServer(self):
        return self.__msp.getMacroServer(self["Door"])

    ## sets config instances
    # \returns set config instance
    def setConfigInstance(self):
        configDevice = None
        if "ConfigDevice" not in self.__selection.keys() \
                or not self.__selection["ConfigDevice"]:
            self.__updateConfigDevice()

        if self.__selection["ConfigDevice"] and \
                self.__selection["ConfigDevice"].lower() != self.moduleLabel:
            configDevice = TangoUtils.openProxy(
                self.__selection["ConfigDevice"])
            configDevice.command_inout("Open")
        else:
            from nxsconfigserver import XMLConfigurator
            from MySQLdb.connections import DatabaseError
            configDevice = XMLConfigurator.XMLConfigurator()
            self.getMacroServer()

            data = {}
            self.importEnv(['DBParams'], data)
            if 'DBParams' in data.keys():
                dbp = data['DBParams']
            else:
                dbp = '{}'

            try:
                configDevice.jsonsettings = dbp
                configDevice.open()
                configDevice.availableComponents()
            except DatabaseError:
                user = getpass.getuser()
                dbp = '{"host":"localhost","db":"nxsconfig",' \
                    + '"use_unicode":true,' \
                    + '"read_default_file":"/home/%s/.my.cnf"}' % user
                configDevice.jsonsettings = dbp
                configDevice.open()
                configDevice.availableComponents()
        return configDevice

    ## executes command on configuration server
    # \returns command result
    def configCommand(self, command, *var):
        configdevice = self.setConfigInstance()
        return TangoUtils.command(configdevice, command, *var)

    ## imports Selector Environment Data
    # \param names names of required variables
    # \param data dictionary with resulting data
    def importEnv(self, names=None, data=None):
        if names is None:
            names = self.keys()
        if data is None:
            data = self
        self.__msp.getSelectorEnv(self["Door"], names, data)

    ## exports Selector Environment Data
    def exportEnv(self, data=None, cmddata=None):
        if data is None:
            data = self
        self.__msp.setSelectorEnv(self["Door"], data, cmddata)

    ## fetches Environment Data
    # \returns JSON String with important variables
    def fetchEnvData(self):
        return self.__msp.getScanEnv(self["Door"])

    ## stores Environment Data
    # \param jdata JSON String with important variables
    def storeEnvData(self, jdata):
        return self.__msp.setScanEnv(self["Door"], jdata)
