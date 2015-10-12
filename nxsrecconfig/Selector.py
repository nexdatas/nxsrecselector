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
## \file Selector.py
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
    # \param macroserverpools MacroServerPools object
    def __init__(self, macroserverpools):

        ## macro server and pools
        self.__msp = macroserverpools

        ##  dictionary with Settings
        self.__selection = Selection()

        ## tango database
        self.__db = PyTango.Database()

        ## module label
        self.moduleLabel = 'module'
        ## error descriptions
        self.descErrors = []

    ## resets seleciton except Door and ConfigDevice
    def reset(self):
        door = self["Door"]
        cf = self["ConfigDevice"]
        self.__selection.reset()
        self["Door"] = door
        self["ConfigDevice"] = cf

    ## deselect seleciton elements
    def deselect(self):
        self.__selection.deselect()

    ## sets selection from state data
    # \param state state data
    def set(self, state):
        self.reset()
        for key in state.keys():
            if key and key[0].upper() != key[0]:
                key = key[0].upper() + key[1:]
            changed = False
            if self.__selection[key] != state[key]:
                self.__selection[key] = state[key]
                changed = True
            if hasattr(self, "_Selector__postSet" + key):
                getattr(self, "_Selector__postSet" + key)(changed)

    ## provides names of variables
    def keys(self):
        return self.__selection.keys()

    ## provides selection data
    # \returns selection data
    def get(self):
        for key in self.keys():
            if hasattr(self, "_Selector__preGet" + key):
                getattr(self, "_Selector__preGet" + key)()
        return dict(self.__selection)

    ## provides value of selection item
    # \param key selection item name
    # \return selection item value
    def __getitem__(self, key):
        if key in self.keys():
            if key and key[0].upper() != key[0]:
                key = key[0].upper() + key[1:]
            if hasattr(self, "_Selector__preGet" + key):
                getattr(self, "_Selector__preGet" + key)()
            return self.__selection[key]
        else:
            return None

    ## sets value of selection item
    # \param key selection item name
    # \param value selection item value
    def __setitem__(self, key, value):
        changed = False
        if self.__selection[key] != value:
            self.__selection[key] = value
            changed = True
        if hasattr(self, "_Selector__postSet" + key):
            getattr(self, "_Selector__postSet" + key)(changed)

    ## updates method for configDevice attribute
    # \brief if configdevice is not defined in the selection
    #        it finds first running NXSConfigServer
    def __preGetConfigDevice(self):
        if "ConfigDevice" not in self.__selection.keys() \
                or not self.__selection["ConfigDevice"]:
            self.__selection["ConfigDevice"] = TangoUtils.getDeviceName(
                self.__db, "NXSConfigServer")

    ## reset method for configDevice attribute
    def __postSetConfigDevice(self, _=True):
        if not self.__selection["ConfigDevice"]:
            self.__selection["ConfigDevice"] = TangoUtils.getDeviceName(
                self.__db, "NXSConfigServer")

    ## update method for writerDevice attribute
    # \returns name of writerDevice
    def __preGetWriterDevice(self):
        if "WriterDevice" not in self.__selection.keys() \
                or not self.__selection["WriterDevice"]:
            self.__selection["WriterDevice"] = TangoUtils.getDeviceName(
                self.__db, "NXSDataWriter")

    ## set method for writerDevice attribute
    def __postSetWriterDevice(self, _=True):
        if not self.__selection["WriterDevice"]:
            self.__selection["WriterDevice"] = TangoUtils.getDeviceName(
                self.__db, "NXSDataWriter")

    ## update method for door attribute
    def __preGetDoor(self):
        if "Door" not in self.__selection.keys() \
                or not self.__selection["Door"]:
            self.__selection["Door"] = TangoUtils.getDeviceName(
                self.__db, "Door")
            self.__msp.updateMacroServer(self.__selection["Door"])

    ## set method for door attribute
    def __postSetDoor(self, changed=True):
        if not self.__selection["Door"]:
            self.__selection["Door"] = TangoUtils.getDeviceName(
                self.__db, "Door")
            changed = True
        if changed:
            self.__msp.updateMacroServer(self.__selection["Door"])

    ## get method for automaticDataSources attribute
    def __preGetAutomaticDataSources(self):
        self.__selection.updateAutomaticDataSources(self.poolMotors())

    ## update method for orderedChannels attribute
    def __preGetOrderedChannels(self):
        self.__selection.updateOrderedChannels(self.poolChannels())

    ## update method for mntGrp attribute
    def __preGetMntGrp(self):
        self.__selection.resetMntGrp()

    ## set method for mntGrp attribute
    def __postSetMntGrp(self, _=True):
        self.__selection.resetMntGrp()

    ## update method for componentGroup attribute
    def __preGetComponentGroup(self):
        self.__selection.updateComponentGroup()

    ## update method for dataSourceGroup attribute
    def __preGetDataSourceGroup(self):
        self.__selection.updateDataSourceGroup(
            self.poolChannels(),
            self.configCommand("availableDataSources"))

    ## update method for timeZone attribute
    def __preGetTimeZone(self):
        self.__selection.resetTimeZone()

    ## set method for timeZone attribute
    # \param name of timeZone
    def __postSetTimeZone(self, _=True):
        self.__selection.resetTimeZone()

    ## resets automatic components to set of given components
    # \param components new selection automatic components
    def resetAutomaticComponents(self, components):
        self.__selection.resetAutomaticComponents(components)

    ## updates active state of automatic components
    # \returns new group of automatic components
    def updateAutomaticComponents(self):
        datasources = set(json.loads(self["AutomaticDataSources"]))
        acpgroup = json.loads(self["AutomaticComponentGroup"])
        configdevice = self.setConfigInstance()
        jacps =  self.__msp.checkComponentChannels(
            self["Door"], configdevice, datasources, acpgroup, self.descErrors)
        if self["AutomaticComponentGroup"] != jacps:
            self["AutomaticComponentGroup"] = jacps
            self.storeSelection()

    ## provides pool proxies
    # \returns list of pool proxies
    def getPools(self):
        return self.__msp.getPools(self["Door"])

    ## provides MacroServer name
    # \returns MacroServer name
    def getMacroServer(self):
        return self.__msp.getMacroServer(self["Door"])

    ## available pool channels
    # \returns pool channels of the macroserver pools
    def poolChannels(self):
        return PoolUtils.getExperimentalChannels(self.getPools())

    ## available pool motors
    # \returns pool motors of the macroserver pools
    def poolMotors(self):
        return PoolUtils.getMotorNames(self.getPools())

    ## sets config instances
    # \returns set config instance
    def setConfigInstance(self):
        configDevice = None
        self.__preGetConfigDevice()

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

    ## saves configuration
    def storeSelection(self):
        inst = self.setConfigInstance()
        conf = str(json.dumps(self.get()))
        inst.selection = conf
        inst.storeSelection(self["MntGrp"])

    ## fetch configuration
    # \returns if configuration was fetched    
    def fetchSelection(self):
        inst = self.setConfigInstance()
        avsl = inst.availableSelections()
        confs = None
        if self["MntGrp"] in avsl:
            confs = inst.selections([self["MntGrp"]])
        if confs:
            self.set(json.loads(str(confs[0])))
            return True
        return False

