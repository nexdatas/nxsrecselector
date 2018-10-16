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

"""  Selection state """

import json
import PyTango
# import getpass
from os.path import expanduser
from .Utils import TangoUtils, PoolUtils, Utils
from .Selection import Selection
from .Converter import Converter


class Selector(object):

    """ access class to Selection dictionary and Config Device """

    #

    def __init__(self, macroserverpools, version,
                 defaultpath="/$var.entryname#'scan'$var.serialno:NXentry/"
                 "NXinstrument/collection",
                 defaulttimezone="Europe/Berlin",
                 defaultmntgrp="nxsmntgrp"):
        """ constructor

        :param macroserverpools: MacroServerPools object
        :type macroserverpools: \
            :class:`nxsrecconfig.MacroServerPools.MacroServerPools`
        :param version: selector version
        :type version: :obj:`str`
        :param defaultpath:  default dynamic component path
        :type defaultpath: :obj:`str`
        :param defaultpath:  default dynamic component path
        :type defaultpath: :obj:`str`
        :param defaulttimezone:  default time zone
        :type defaulttimezone: :obj:`str`
        :param defaultmntgrp:  default measurement group name
        :type defaultmntgrp: :obj:`str`
        """

        #: (:class:`nxsrecconfig.MacroServerPools.MacroServerPools`) \
        #:  macro server and pools
        self.__msp = macroserverpools

        #: (:class:`nxsrecconfig.Selection.Selection`) \
        #:  selection dictionary with Settings
        self.__selection = Selection(
            Version=version,
            MntGrp=defaultmntgrp,
            TimeZone=defaulttimezone,
            DefaultDynamicPath=defaultpath
        )
        #: (:class:`nxsrecconfig.Converter.Converter`) \
        #:  selection dictionary with Settings
        self.__converter = Converter(version)

        #: (:obj:`str`) selection dictionary with Settings
        self.__version = version

        #: (:class:`PyTango.Database`) tango database
        self.__db = PyTango.Database()

        #: (:obj:`str`) module label
        self.moduleLabel = 'module'
        #: (:obj:`list` <:obj:`str`>) error descriptions
        self.descErrors = []

    def reset(self):
        """ resets seleciton except Door and ConfigDevice
        """
        door = self["Door"]
        cf = self["ConfigDevice"]
        self.__selection.reset()
        self["Door"] = door
        self["ConfigDevice"] = cf

    def deselect(self):
        """ deselects all seleciton elements
        """
        self.__selection.deselect()

    def set(self, state):
        """ sets selection from state data

        :param state: state data
        :type state: :obj:`dict` <:obj:`str`, `any`>
        """
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

    def keys(self):
        """ provides all names of variables

        :returns: selection keys
        :rtype: :obj:`list` <:obj:`str`>
        """
        return list(self.__selection.keys())

    def get(self):
        """ provides selection data

        :returns: selection data
        :rtype: :obj:`dict` <:obj:`str`, `any`>
        """
        for key in self.keys():
            if hasattr(self, "_Selector__preGet" + key):
                getattr(self, "_Selector__preGet" + key)()
        return dict(self.__selection)

    #
    def __getitem__(self, key):
        """ provides value of selection item

        :param key: selection item name
        :type key: :obj:`str`
        :returns: selection item value
        :rtype: `any`
        """
        if key in self.keys():
            if key and key[0].upper() != key[0]:
                key = key[0].upper() + key[1:]
            if hasattr(self, "_Selector__preGet" + key):
                getattr(self, "_Selector__preGet" + key)()
            return self.__selection[key]
        else:
            return None

    def __setitem__(self, key, value):
        """ sets value of selection item

        :param key: selection item name
        :type key: :obj:`str`
        :param value: selection item value
        :type value: `any`
        """
        changed = False
        if self.__selection[key] != value:
            self.__selection[key] = value
            changed = True
        if hasattr(self, "_Selector__postSet" + key):
            getattr(self, "_Selector__postSet" + key)(changed)

    def __preGetConfigDevice(self):
        """ updates method for configDevice attribute

        :brief: if configdevice is not defined in the selection
                it finds first running NXSConfigServer
        """
        if "ConfigDevice" not in self.__selection.keys() \
                or not self.__selection["ConfigDevice"]:
            self.__selection["ConfigDevice"] = TangoUtils.getDeviceName(
                self.__db, "NXSConfigServer")

    def __postSetConfigDevice(self, _=True):
        """ reset method for configDevice attribute
        """
        if not self.__selection["ConfigDevice"]:
            self.__selection["ConfigDevice"] = TangoUtils.getDeviceName(
                self.__db, "NXSConfigServer")

    def __preGetWriterDevice(self):
        """ update method for writerDevice attribute
        """
        if "WriterDevice" not in self.__selection.keys() \
                or not self.__selection["WriterDevice"]:
            self.__selection["WriterDevice"] = TangoUtils.getDeviceName(
                self.__db, "NXSDataWriter")

    def __postSetWriterDevice(self, _=True):
        """ set method for writerDevice attribute
        """
        if not self.__selection["WriterDevice"]:
            self.__selection["WriterDevice"] = TangoUtils.getDeviceName(
                self.__db, "NXSDataWriter")

    def __preGetDoor(self):
        """ update method for door attribute
        """
        if "Door" not in self.__selection.keys() \
                or not self.__selection["Door"]:
            self.__selection["Door"] = TangoUtils.getDeviceName(
                self.__db, "Door")
            self.__msp.updateMacroServer(self.__selection["Door"])

    def __postSetDoor(self, changed=True):
        """ set method for door attribute

        :param changed: True if selection element has been changed
        :type changed: :obj:`bool`
        """
        if not self.__selection["Door"]:
            self.__selection["Door"] = TangoUtils.getDeviceName(
                self.__db, "Door")
            changed = True
        if changed:
            self.__msp.updateMacroServer(self.__selection["Door"])

    def __preGetPreselectingDataSources(self):
        """ get method for preselectedDataSources attribute
        """
        self.__selection.updatePreselectingDataSources(
            self.poolElementNames('MotorList'))

    def __preGetOrderedChannels(self):
        """ update method for orderedChannels attribute
        """
        self.__selection.updateOrderedChannels(
            self.poolElementNames('ExpChannelList'))

    def __preGetChannelProperties(self):
        """ update method for orderedChannels attribute
        """
        pools = self.getPools()
        try:
            triggergate = PoolUtils.getElementNames(
                pools, 'TriggerGateList')
        except Exception:
            triggergate = []
        self.__selection.updateChannelProperties(
            PoolUtils.getDeviceControllers(pools), triggergate)

    def __preGetMntGrp(self):
        """ update method for mntGrp attribute
        """
        self.__selection.resetMntGrp()

    def __postSetMntGrp(self, _=True):
        """ set method for mntGrp attribute
        """
        self.__selection.resetMntGrp()

    def __preGetComponentSelection(self):
        """ update method for componentGroup attribute
        """
        self.__selection.updateComponentSelection()

    def __preGetDataSourceSelection(self):
        """ update method for dataSourceGroup attribute
        """
        self.__selection.updateDataSourceSelection(
            PoolUtils.getElementNames(self.getPools(), 'ExpChannelList'),
            self.configCommand("availableDataSources"))

    def __preGetTimeZone(self):
        """ update method for timeZone attribute
        """
        self.__selection.resetTimeZone()

    def __postSetTimeZone(self, _=True):
        """ set method for timeZone attribute
        """
        self.__selection.resetTimeZone()

    def resetPreselectedComponents(self, components):
        """ resets preselected components to set of given components

        :param components: new selection preselected components
        :type components: :obj:`list` <:obj:`str`>
        """
        self.__selection.resetPreselectedComponents(components)

    def preselect(self):
        """ updates active state of preselected components

        :brief: It provides new group of preselected components
        """
        datasources = set(json.loads(self["PreselectingDataSources"]))
        acpgroup = json.loads(self["ComponentPreselection"])
        adsgroup = json.loads(self["DataSourcePreselection"])
        configdevice = self.setConfigInstance()
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

    def getPools(self):
        """ provides pool proxies

        :returns: list of pool proxies
        :rtype: :obj:`list` <:obj:`PyTango.DeviceProxy`>
        """
        return self.__msp.getPools(self["Door"])

    def getMacroServer(self):
        """ provides MacroServer name

        :returns: MacroServer name
        :rtype: :obj:`str`
        """
        return self.__msp.getMacroServer(self["Door"])

    def poolElementNames(self, listattr):
        """ provides names from the given pool listattr

        :param listattr: pool attribute with list
        :type listattr: :obj:`str`
        :returns: names from given pool listattr
        :rtype: :obj:`list` <:obj:`str`>
        """
        return PoolUtils.getElementNames(self.getPools(), listattr)

    def setConfigInstance(self):
        """ sets config instances

        :returns: set config instance
        :rtype: :class:`PyTango.DeviceProxy` \
             or :class:`nxsconfigserver.XMLConfigurator.XMLConfigurator`
        """
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
                home = expanduser("~")
                # user = getpass.getuser()
                dbp = '{"host":"localhost","db":"nxsconfig",' \
                    + '"use_unicode":true,' \
                    + '"read_default_file":"%s/.my.cnf"}' % home
                configDevice.jsonsettings = dbp
                configDevice.open()
                configDevice.availableComponents()
        cnfmajor = int(Utils.tostr(configDevice.version).split(".")[0])
        if cnfmajor < 2:
            raise Exception("NXSConfigServer (%s) version below 2.0.0" %
                            self.__selection["ConfigDevice"])
        return configDevice

    def configCommand(self, command, *var):
        """ executes command on configuration server

        :param command: command name
        :type command: :obj:`str`
        :param var: parameter list
        :type var: [ `any` ]
        :returns: command result
        :rtype: `any`
        """
        configdevice = self.setConfigInstance()
        return TangoUtils.command(configdevice, command, *var)

    def importEnv(self, names=None, data=None):
        """ imports Selector Environment Data

        :param names: names of required variables
        :type names: :obj:`list` <:obj:`str`>
        :param data: dictionary with resulting data
        :type data: :obj:`dict` <:obj:`str` , `any`>
        """
        update = False
        if names is None:
            names = self.__converter.allkeys(self)
        if data is None:
            data = {}
            update = True
        self.__msp.getSelectorEnv(self["Door"], names, data)
        if update:
            self.set(data)

    def exportEnv(self, data=None, cmddata=None):
        """ exports Selector Environment Data

        :param data: dictionary with input data
        :type data: :obj:`dict` <:obj:`str` , `any`>
        :param cmddata: dictionary with command input data
        :type cmddata: :obj:`dict` <:obj:`str` , `any`>
        """
        if data is None:
            data = self
        self.__msp.setSelectorEnv(self["Door"], data, cmddata)

    def getScanEnvVariables(self):
        """ gets Scan Environment Data

        :returns: JSON String with important variables
        :rtype: :obj:`str`
        """
        return self.__msp.getScanEnv(self["Door"])

    def setScanEnvVariables(self, jdata):
        """ sets Scan Environment Data

        :param jdata: JSON String with important variables
        :type jdata: :obj:`str`
        """
        return self.__msp.setScanEnv(self["Door"], jdata)

    def storeSelection(self):
        """ saves configuration
        """
        inst = self.setConfigInstance()
        conf = Utils.tostr(json.dumps(self.get()))
        inst.selection = conf
        inst.storeSelection(self["MntGrp"])

    def fetchSelection(self):
        """ fetch configuration

        :returns: if configuration was fetched
        :rtype: :obj:`bool`
        """
        inst = self.setConfigInstance()
        cnfdv = self["ConfigDevice"]
        avsl = inst.availableSelections()
        confs = None
        if self["MntGrp"] in avsl:
            confs = inst.selections([self["MntGrp"]])
        if confs is not None:
            self.set(json.loads(Utils.tostr(confs[0])))
            self["ConfigDevice"] = cnfdv
            return True
        return False
