
#!/usr/bin/env python
#   This file is part of nxsrecconfig - NeXus Sardana Recorder Settings
#
#    Copyright (C) 2014-2016 DESY, Jan Kotanski <jkotan@mail.desy.de>
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
from .Converter import Converter


## Access class to Selection dictionary and Config Device
class Selector(object):
    """ selection state """

    ## constructor
    # \param macroserverpools MacroServerPools object
    def __init__(self, macroserverpools, version):

        ## macro server and pools
        self.__msp = macroserverpools

        ##  selection dictionary with Settings
        self.__selection = Selection(Version=version)
        ##  selection dictionary with Settings
        self.__converter = Converter(version)

        ##  selection dictionary with Settings
        self.__version = version

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
        state = dict(state)
        self.__converter.convert(state)
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

    ## get method for preselectedDataSources attribute
    def __preGetPreselectingDataSources(self):
        self.__selection.updatePreselectingDataSources(
            self.poolElementNames('MotorList'))

    ## update method for orderedChannels attribute
    def __preGetOrderedChannels(self):
        self.__selection.updateOrderedChannels(
            self.poolElementNames('ExpChannelList'))

    ## update method for mntGrp attribute
    def __preGetMntGrp(self):
        self.__selection.resetMntGrp()

    ## set method for mntGrp attribute
    def __postSetMntGrp(self, _=True):
        self.__selection.resetMntGrp()

    ## update method for componentGroup attribute
    def __preGetComponentSelection(self):
        self.__selection.updateComponentSelection()

    ## update method for dataSourceGroup attribute
    def __preGetDataSourceSelection(self):
        self.__selection.updateDataSourceSelection(
            PoolUtils.getElementNames(self.getPools(), 'ExpChannelList'),
            self.configCommand("availableDataSources"))

    ## update method for timeZone attribute
    def __preGetTimeZone(self):
        self.__selection.resetTimeZone()

    ## set method for timeZone attribute
    # \param name of timeZone
    def __postSetTimeZone(self, _=True):
        self.__selection.resetTimeZone()

    ## resets preselected components to set of given components
    # \param components new selection preselected components
    def resetPreselectedComponents(self, components):
        self.__selection.resetPreselectedComponents(components)

    ## updates active state of preselected components
    # \returns new group of preselected components
    def preselect(self):
        datasources = set(json.loads(self["PreselectingDataSources"]))
        acpgroup = json.loads(self["ComponentPreselection"])
        adsgroup = json.loads(self["DataSourcePreselection"])
        configdevice = self.setConfigInstance()
        print "DS adsgroup", adsgroup
        jacps, jadss = self.__msp.checkChannels(
            self["Door"], configdevice, datasources,
            acpgroup, adsgroup, self.descErrors)
        changed = False
        if self["ComponentPreselection"] != jacps:
            self["ComponentPreselection"] = jacps
            changed = True
        if self["DataSourcePreselection"] != jadss:
            self["DataSourcePreselection"] = jadss
            changed = True
        if changed:
            self.storeSelection()

    ## provides pool proxies
    # \returns list of pool proxies
    def getPools(self):
        return self.__msp.getPools(self["Door"])

    ## provides MacroServer name
    # \returns MacroServer name
    def getMacroServer(self):
        return self.__msp.getMacroServer(self["Door"])

    ## provides names from given pool listattr
    # \param listattr pool attribute with list
    # \returns names from given pool listattr
    def poolElementNames(self, listattr):
        return PoolUtils.getElementNames(self.getPools(), listattr)

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
        cnfmajor = int(str(configDevice.version).split(".")[0])
        if cnfmajor < 2:
            raise Exception("NXSConfigServer (%s) version below 2.0.0" %
                            self.__selection["ConfigDevice"])
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
        update = False
        if names is None:
            names = self.__converter.allkeys(self)
        if data is None:
            data = {}
            update = True
        self.__msp.getSelectorEnv(self["Door"], names, data)
        if update:
            self.set(data)

    ## exports Selector Environment Data
    def exportEnv(self, data=None, cmddata=None):
        if data is None:
            data = self
        self.__msp.setSelectorEnv(self["Door"], data, cmddata)

    ## gets Scan Environment Data
    # \returns JSON String with important variables
    def getScanEnvVariables(self):
        return self.__msp.getScanEnv(self["Door"])

    ## sets Scan Environment Data
    # \param jdata JSON String with important variables
    def setScanEnvVariables(self, jdata):
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
        cnfdv = self["ConfigDevice"]
        avsl = inst.availableSelections()
        confs = None
        if self["MntGrp"] in avsl:
            confs = inst.selections([self["MntGrp"]])
        if confs is not None:
            self.set(json.loads(str(confs[0])))
            self["ConfigDevice"] = cnfdv
            return True
        return False
