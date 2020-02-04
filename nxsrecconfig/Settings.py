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

"""  NeXus Sardana Recorder Settings implementation """

import json
import gc
import PyTango
import xml.etree.ElementTree as et
from lxml.etree import XMLParser
# from lxml import etree
import sys
import weakref

from .Describer import Describer
from .DynamicComponent import DynamicComponent
from .Utils import (
    Utils, TangoUtils, MSUtils, PoolUtils, PYTG_BUG_213)
from .ProfileManager import ProfileManager
from .Selector import Selector
from .Release import __version__
from .MacroServerPools import MacroServerPools
from .StreamSet import StreamSet

if sys.version_info > (3,):
    unicode = str


class Settings(object):

    """ NeXus Sardana Recorder settings
    """

    def __init__(self, server=None, numberofthreads=None,
                 defaultnexuspath=None,
                 defaulttimezone=None, defaultmntgrp=None,
                 syncsnapshot=False):
        """ contructor

        :param server: NXSRecSelector server
        :type server: :class:`nxsrecconfig.NXSConfig.NXSRecSelector`
        :param numberofthreads: number of threads used to check device state
        :type numberofthreads: :obj:`str`
        :param defaultnexuspath:  default dynamic component path
        :type defaultnexuspath: :obj:`str`
        :param syncsnapshot: preselection merges current ScanSnapshot
        :type syncsnapshot: :obj:`bool`
        """
        #: (:class:`nxsrecconfig.NXSConfig.NXSRecSelector`) Tango server
        self.__server = server
        #: (:obj:`int`) number of threads
        self.numberOfThreads = numberofthreads or 20

        #: (:class:`StreamSet` or :class:`PyTango.Device_4Impl`) stream set
        self._streams = StreamSet(weakref.ref(server) if server else None)

        #: (:obj:`str`) default NeXus path
        self.defaultNeXusPath = defaultnexuspath or \
            "/$var.entryname#'scan'$var.serialno:NXentry/" \
            "NXinstrument/collection"

        #: (:obj:`str`) default CanFail DataSources
        self.defaultCanFailDataSources = []

        #: (:obj:`str`) default time zone
        self.defaultTimeZone = defaulttimezone or "Europe/Berlin"

        #: (:obj:`str`) default measurement group
        self.defaultMntGrp = defaultmntgrp or "nxsmntgrp"

        #: (:obj:`bool`) preselection merges current ScanSnapshot
        self.syncSnapshot = syncsnapshot
        if PYTG_BUG_213:
            self._streams.error(
                "Settings::Settings() - "
                "Reading/Writinh Encoded Attributes for python3 and "
                "PyTango < 9.2.5"
                " is not supported ")

        #: (:class:`nxsrecconfg.MacroServerPools.MacroServerPools`) \
        #:     configuration selection
        self.__msp = MacroServerPools(self.numberOfThreads)

        #: (:class:`nxsrecconfg.Selector.Selector`) \
        #:   configuration selector
        self.__selector = Selector(
            self.__msp, self.version, self.defaultNeXusPath,
            self.defaultTimeZone, self.defaultMntGrp)

        #: (:class:`nxsrecconfg.ProfileManager.ProfileManager) \
        #: profile
        self.__profileManager = ProfileManager(
            self.__selector,
            syncsnapshot=syncsnapshot
        )

        #: (:obj:`str`) configuration file
        self.profileFile = '/tmp/nxsrecconfig.cfg'

        #: (:class:`PyTango.Database`) tango database
        self.__db = PyTango.Database()

        #:  (:obj:`list` <:obj:`str`>) timer filters
        self.mutedChannelFilters = ["*tip551*"]
        #: (:obj:`str`) default device groups
        self.__defaultDeviceGroups = \
            '{"timer": ["*exp_t*"], "dac": ["*exp_dac*"], ' \
            + '"counter": ["*exp_c*"], "mca": ["*exp_mca*"], ' \
            + '"adc": ["*exp_adc*"], "motor": ["*exp_mot*"]}'

        #: (:obj:`str`) device groups
        self.__deviceGroups = Utils.tostr(self.__defaultDeviceGroups)
        #: (:obj:`list` <:obj:`str`>) administator data
        self.adminDataNames = []

        self.__setupSelection()

    def __setupSelection(self):
        """ sets up the current selection from ActiveMntGrp
        """
        if not self.__server:
            self.fetchProfile()
        ms = self.__selector.getMacroServer()
        amntgrp = MSUtils.getEnv('ActiveMntGrp', ms)
        if amntgrp:
            self.__selector["MntGrp"] = amntgrp
        else:
            avsel = self.availableProfiles()
            if avsel and avsel[0]:
                self.__selector["MntGrp"] = avsel[0]
        try:
            self.fetchProfile()
        except Exception:
            import sys
            import traceback
            info = sys.exc_info()
            message = Utils.tostr(info[1].__str__()) + "\n " + (" ").join(
                traceback.format_tb(sys.exc_info()[2]))
            self._streams.error("Error in fetching profile: %s"
                                % self.__selector["MntGrp"])
            self._streams.error(Utils.tostr(message))

    def value(self, name):
        """ provides values of the required variable

        :param name: name of the required variable
        :type name: :obj:`str`
        :returns: values of the required variable
        :rtype: `any`
        """
        vl = ''
        if name in self.__selector.keys():
            vl = self.__selector[name]
            if isinstance(vl, unicode):
                vl = Utils.tostr(vl)
        return vl

    def names(self):
        """ provides names of variables

        :returns:  all names of variables
        :rtypes: :obj:`list` <:obj:`str`>
        """
        return list(self.__selector.keys())

    def __version(self):
        """ provides server version

        :returns: server version
        :rtype: :obj:`str`
        """
        return __version__

    #: (:obj:`str`) server version
    version = property(
        __version,
        doc='server version')

# read-only variables

    def administratorDataNames(self):
        """ provides administrator data names

        :returns: list of provides administrator data names
        :rtype: :obj:`list` <:obj:`str`>
        """
        return list(self.adminDataNames)

    def selectedComponents(self):
        """ provides user selected components

        :returns: list of available selected components
        :rtype: :obj:`list` <:obj:`str`>
        """
        return self.__profileManager.components()

    def __components(self):
        """ provides all configuration components

        :returns: list of available selected components
        :rtype: :obj:`list` <:obj:`str`>
        """
        return list(set(self.selectedComponents()) |
                    set(self.preselectedComponents()) |
                    set(self.mandatoryComponents()))

    #: (:obj:`list` <:obj:`str`>) provides selected components
    components = property(
        __components,
        doc='provides selected components')

    def preselectedComponents(self):
        """ provides preselected components

        :returns: list of available preselected components
        :rtype: :obj:`list` <:obj:`str`>
        """
        return self.__profileManager.preselectedComponents()

    def __getDescriptionErrors(self):
        """ provides description component errors

        :returns: list of available description component errors
        :rtype: :obj:`list` <:obj:`str`>
        """
        return self.__selector.descErrors

    #: (:obj:`list` <:obj:`str`>) provides preselected components
    descriptionErrors = property(__getDescriptionErrors,
                                 doc='provides description component errors')

    def selectedDataSources(self):
        """ provides selected datasources

        :returns: list of available selected datasources
        """
        return self.__profileManager.dataSources()

    def preselectedDataSources(self):
        """ provides preselected datasources

        :returns: list of available preselected datasources
        :rtype: :obj:`list` <:obj:`str`>
        """
        return self.__profileManager.preselectedDataSources()

    def __dataSources(self):
        """ provides all selected data sources

        :returns: all selected data sources
        :rtype: :obj:`list` <:obj:`str`>
        """
        return list(
            set(self.selectedDataSources()) |
            set(self.componentDataSources())
        )

    #: (:obj:`list` <:obj:`str`>) provides all selected data sources
    dataSources = property(
        __dataSources,
        doc=' provides selected data sources')

    def componentDataSources(self):
        """ provides a list of profile component DataSources

        :returns: list of profile component datasources
        :rtype: :obj:`list` <:obj:`str`>
        """
        return self.__profileManager.componentDataSources()

# read-write variables

    def __getDefaultPreselectedComponents(self):
        """ get method for defaultPreselectedComponents attribute

        :returns: list of components
        :rtype: :obj:`list` <:obj:`str`>
        """
        return self.__profileManager.defaultPreselectedComponents

    def __setDefaultPreselectedComponents(self, components):
        """ set method for defaultPreselectedComponents attribute

        :param components: list of components
        :type components: :obj:`list` <:obj:`str`>
        """
        self.__profileManager.defaultPreselectedComponents = components

    #: (:obj:`list` <:obj:`str`>) default PreselectedComponents
    defaultPreselectedComponents = property(
        __getDefaultPreselectedComponents,
        __setDefaultPreselectedComponents,
        doc='default Preselected components')

    def __getClientRecordKeys(self):
        """ get method for clientRecordKeys attribute

        :returns: list of components
        :rtype: :obj:`list` <:obj:`str`>
        """
        return self.__profileManager.clientRecordKeys

    def __setClientRecordKeys(self, components):
        """ set method for clientRecordKeys attribute

        :param components: list of components
        :type components: :obj:`list` <:obj:`str`>
        """
        self.__profileManager.clientRecordKeys = components

    #: (:obj:`list` <:obj:`str`>) client record keys
    clientRecordKeys = property(
        __getClientRecordKeys,
        __setClientRecordKeys,
        doc='clientRecordKeys')

    def __getTimerFilters(self):
        """ get method for clientRecordKeys attribute

        :returns: list of timer filters
        :rtype: :obj:`list` <:obj:`str`>
        """
        return self.__profileManager.timerFilters

    def __setTimerFilters(self, filters):
        """ set method for clientRecordKeys attribute

        :param components: list of filters
        :type components: :obj:`list` <:obj:`str`>
        """
        self.__profileManager.timerFilters = filters

    #: (:obj:`list` <:obj:`str`>) timer filters
    timerFilters = property(
        __getTimerFilters,
        __setTimerFilters,
        doc='timerFilters')

    def __getConfigDevice(self):
        """ get method for configDevice attribute

        :returns: name of configDevice
        :rtype: :obj:`str`
        """
        return self.__selector["ConfigDevice"]

    def __setConfigDevice(self, name):
        """ set method for configDevice attribute

        :param name: name of configDevice
        :type name: :obj:`str`
        """
        if name != self.__selector["ConfigDevice"]:
            self.__selector["ConfigDevice"] = name
            self.switchProfile(toActive=False)

    #: (:obj:`str`) the json data string
    configDevice = property(__getConfigDevice, __setConfigDevice,
                            doc='configuration server device name')

    def __getPoolBlacklist(self):
        """ get method for poolBlacklist attribute

        :returns: name of poolBlacklist
        :rtype: :obj:`list` <:obj:`str`>
        """
        return self.__msp.poolBlacklist

    def __setPoolBlacklist(self, names):
        """ set method for poolBlacklist attribute

        :param names: names of poolBlacklist
        :type names: :obj:`list` <:obj:`str`>
        """
        self.__msp.poolBlacklist = names

    #: (:obj:`list` <:obj:`str`>) black list of pools
    poolBlacklist = property(__getPoolBlacklist, __setPoolBlacklist,
                             doc='pool black list')

    def __setProfileConfiguration(self, jconf):
        """ set method for configuration attribute

        :param name: name of configuration
        :type name: :obj:`str`
        """
        self.__selector.set(json.loads(jconf))
        self.storeProfile()

    def __getProfileConfiguration(self):
        """ get method for configuration attribute

        :returns: configuration
        :rtype: :obj:`str`
        """
        return json.dumps(self.__selector.get())

    #: (:obj:`str`) the json data string
    profileConfiguration = property(
        __getProfileConfiguration,
        __setProfileConfiguration,
        doc='preselected components group')

    def __setAppendEntry(self, ae):
        """ set method for appendEntry attribute

        :param ae: appendEntry flag
        :type ae: :obj:`bool`
        """
        self.__selector["AppendEntry"] = bool(ae)
        self.storeProfile()

    def __getAppendEntry(self):
        """ get method for appendEntry attribute

        :returns: flag of appendEntry
        :rtype: :obj:`bool`
        """
        return bool(self.__selector["AppendEntry"])

    #: (:obj:`bool`) the json data string
    appendEntry = property(
        __getAppendEntry,
        __setAppendEntry,
        doc='flag for append entry')

    def __getUserData(self):
        """ get method for userData attribute

        :returns: userData json dictionary
        :rtype: :obj:`str`
        """
        return self.__selector["UserData"]

    def __setUserData(self, udata):
        """
        set method for userData attribute

        :param udata: userData json dictionary
        :type udata: :obj:`str`
        """
        jname = Utils.stringToDictJson(udata)
        if self.__selector["UserData"] != jname:
            self.__selector["UserData"] = jname
            self.storeProfile()

    #: (:obj:`str`) the json data string
    userData = property(
        __getUserData,
        __setUserData,
        doc='client data record')

    def __getDeviceGroups(self):
        """ get method for deviceGroups attribute

        :returns: deviceGroups json dictionary
        :rtype: :obj:`str`
        """
        try:
            ldct = json.loads(self.__deviceGroups)
            if not isinstance(ldct, dict):
                raise Exception("DeviceGroups is not a JSON dictionary")
            for vl in ldct.values():
                if not isinstance(vl, list):
                    raise Exception(
                        "DeviceGroups is not a JSON dictionary of lists")
            return self.__deviceGroups
        except Exception:
            return self.__defaultDeviceGroups

    def __setDeviceGroups(self, groups):
        """ sets method for deviceGroups attribute

        :param groups: name of deviceGroups
        :type groups: :obj:`str`
        """
        jname = Utils.stringToDictJson(groups)
        #: device groups
        self.__deviceGroups = jname

    #: (:obj:`str`) the json data string
    deviceGroups = property(
        __getDeviceGroups,
        __setDeviceGroups,
        doc='device groups')

    def __getConfigVariables(self):
        """ get method for configVariables attribute

        :returns: name of configVariables
        :rtype: :obj:`str`
        """
        return self.__selector["ConfigVariables"]

    def __setConfigVariables(self, name):
        """ set method for configVariables attribute

        :param name: name of configVariables
        :type name: :obj:`str`
        """
        jname = Utils.stringToDictJson(name)
        if self.__selector["ConfigVariables"] != jname:
            self.__selector["ConfigVariables"] = jname
            self.storeProfile()

    #: (:obj:`str`) the json variables string
    configVariables = property(
        __getConfigVariables,
        __setConfigVariables,
        doc='configuration variables')

    def __getStepDatSources(self):
        """ get method for dataSourceGroup attribute

        :returns: names of STEP dataSources
        :rtype: :obj:`str`
        """
        inst = self.__selector.setConfigInstance()
        if inst.stepdatasources:
            return inst.stepdatasources
        else:
            return "[]"

    def __setStepDatSources(self, names):
        """ set method for dataSourceGroup attribute
        :param names: names of STEP dataSources
        :type names: :obj:`str`
        """
        inst = self.__selector.setConfigInstance()
        inst.stepdatasources = names

    #: (:obj:`str`) the json data string
    stepdatasources = property(
        __getStepDatSources,
        __setStepDatSources,
        doc='step datasource list')

    def __getLinkDatSources(self):
        """ get method for dataSourceGroup attribute

        :returns: names of link dataSources
        :rtype: :obj:`str`
        """
        inst = self.__selector.setConfigInstance()
        if inst.linkdatasources:
            return inst.linkdatasources
        else:
            return "[]"

    def __setLinkDatSources(self, names):
        """ set method for dataSourceGroup attribute
        :param names: names of link dataSources
        :type names: :obj:`str`
        """
        inst = self.__selector.setConfigInstance()
        inst.linkdatasources = names

    #: (:obj:`str`) the json data string
    linkdatasources = property(
        __getLinkDatSources,
        __setLinkDatSources,
        doc='link datasource list')

    def __getCanFailDatSources(self):
        """ get method for dataSourceGroup attribute

        :returns: names of canfail dataSources
        :rtype: :obj:`str`
        """
        inst = self.__selector.setConfigInstance()
        if inst.canfaildatasources:
            return inst.canfaildatasources
        else:
            return "[]"

    def __setCanFailDatSources(self, names):
        """ set method for dataSourceGroup attribute
        :param names: names of canfail dataSources
        :type names: :obj:`str`
        """
        inst = self.__selector.setConfigInstance()
        inst.canfaildatasources = json.dumps(list(
            set(self.defaultCanFailDataSources) |
            set(json.loads(names))))

    #: (:obj:`str`) the json data string
    canfaildatasources = property(
        __getCanFailDatSources,
        __setCanFailDatSources,
        doc='canfail datasource list')

    def channelProperties(self, ptype):
        """ provides channel properties of the given type

        :param ptype: property type
        :type ptype: :obj:`str`
        :returns:  json dictionary with channel properties
        :rtype: :obj:`str`
        """
        props = json.loads(self.__selector["ChannelProperties"])
        if ptype in props.keys():
            return json.dumps(props[ptype])
        else:
            return '{}'

    def setChannelProperties(self, typeandvariables):
        """ sets channel properties of the given type

        :param typeandvariables:
               (property type, json dictionary of channel propertie values)
        :type typeandvariables: (:obj:`str`, :obj:`str`)
        """
        ptype, variables = typeandvariables
        jvar = Utils.stringToDictJson(variables)
        props = json.loads(self.__selector["ChannelProperties"])
        if ptype in props.keys():
            lvar = json.dumps(props[ptype])
        else:
            lvar = '{}'
        if lvar != jvar:
            props[ptype] = json.loads(jvar)
            self.__selector["ChannelProperties"] = json.dumps(props)
            self.storeProfile()

    def __getMntGrp(self):
        """ get method for mntGrp attribute

        :returns: name of mntGrp
        :rtype: :obj:`str`
        """
        return self.__selector["MntGrp"]

    def __setMntGrp(self, name):
        """ set method for mntGrp attribute

        :param name: name of mntGrp
        :type name: :obj:`str`
        """
        self.__selector["MntGrp"] = name

    #: (:obj:`str`) the json data string
    mntGrp = property(__getMntGrp, __setMntGrp,
                      doc='measurement group')

    def __getDoor(self):
        """ get method for door attribute

        :rtype: :obj:`str`
        :returns: name of door
        """
        return self.__selector["Door"]

    def __setDoor(self, name):
        """ set method for door attribute

        :type name: :obj:`str`
        :param name: name of door
        """
        self.__selector["Door"] = name
        self.__msp.updateMacroServer(self.__selector["Door"])

    #: (:obj:`str`) the json data string
    door = property(__getDoor, __setDoor,
                    doc='door server device name')

    def __getMacroServer(self):
        """ get method for macro server attribute

        :returns: name of macro server
        :rtype :obj:`str`
        """
        return self.__msp.getMacroServer(self.__selector["Door"])

    #: (:obj:`str`) the json data string
    macroServer = property(__getMacroServer,
                           doc='macroserver device name')

    def __getWriterDevice(self):
        """ get method for writerDevice attribute

        :returns: name of writerDevice
        :rtype: :obj:`str`
        """
        return self.__selector["WriterDevice"]

    def __setWriterDevice(self, name):
        """ set method for writerDevice attribute

        :param name: name of writerDevice
        :type name: :obj:`str`
        """
        self.__selector["WriterDevice"] = name
        self.storeProfile()

    #: (:obj:`str`) the json data string
    writerDevice = property(__getWriterDevice, __setWriterDevice,
                            doc='Writer device name')

    def __getScanDir(self):
        """ get method for ScanDir attribute

        :returns: name of ScanDir
        :rtype: :obj:`str`
        """
        ms = self.__selector.getMacroServer()
        return Utils.tostr(MSUtils.getEnv('ScanDir', ms))

    def __setScanDir(self, name):
        """ set method for ScanDir attribute

        :param name: name of ScanDir
        :type name: :obj:`str`
        """
        ms = self.__selector.getMacroServer()
        MSUtils.setEnv('ScanDir', Utils.tostr(name), ms)

    #: the json data string
    scanDir = property(__getScanDir, __setScanDir,
                       doc='scan directory')

    def __getScanID(self):
        """ get method for ScanID attribute

        :returns: name of ScanID
        :rtype: :obj:`int`
        """
        ms = self.__selector.getMacroServer()
        sid = MSUtils.getEnv('ScanID', ms)
        try:
            return int(sid)
        except Exception:
            self._streams.error(
                "Settings::Settings() - "
                "ScanID wrongly defined (%s)" % sid)
            return -1
            # print(str(e))

    def __setScanID(self, name):
        """ set method for ScanID attribute

        :param name: name of ScanID
        :type name: :obj:`int`
        """
        ms = self.__selector.getMacroServer()
        MSUtils.setEnv('ScanID', name, ms)

    #: (:obj:`int`) the json data string
    scanID = property(__getScanID, __setScanID,
                      doc='scan id')

    def __getScanFile(self):
        """ get method for ScanFile attribute

        :returns: name of ScanFile
        :rtype: :obj:`str`
        """
        ms = self.__selector.getMacroServer()
        val = MSUtils.getEnv('ScanFile', ms)
        ret = [val] if isinstance(val, (str, unicode)) else val
        return json.dumps(ret)

    def __setScanFile(self, name):
        """ set method for ScanFile attribute

        :param name: name of ScanFile
        :type name: :obj:`str`
        """
        jname = json.loads(Utils.stringToListJson(name))

        ms = self.__selector.getMacroServer()
        if isinstance(jname, (list, tuple)) and len(jname) == 1:
            jname = jname[0]
        MSUtils.setEnv('ScanFile', jname, ms)

    #: (:obj:`str`) the json data string
    scanFile = property(__getScanFile, __setScanFile,
                        doc='scan file(s)')

    def variableComponents(self):
        """ provides components for all variables

        :returns: json dictionary with components for all variables
        :rtype: :obj:`str`
        """
        acps = self.availableComponents()
        vrs = {}
        for cp in acps:
            vr = self.__configCommand("componentVariables", cp) or []
            if vr:
                for v in vr:
                    if v not in vrs:
                        vrs[v] = []
                    vrs[v].append(cp)

        jdc = json.dumps(vrs)
        return jdc

    def componentDescription(self):
        """ provides description of all components

        :returns: JSON string with description of all components
        :rtype: :obj:`str`
        """
        dc = self.__profileManager.cpdescription(full=True)
        jdc = json.dumps(dc)
        return jdc

    def fullDeviceNames(self):
        """ provides full names of pool devices

        :returns: JSON string with full names of pool devices
        :rtype: :obj:`str`
        """
        pools = self.__selector.getPools()
        return json.dumps(PoolUtils.getFullDeviceNames(pools))

    def availableTimers(self):
        """ provides available Timers from MacroServer pools

        :returns:  available Timers from MacroServer pools
        :rtype: :obj:`list` <:obj:`str`>
        """
        pools = self.__selector.getPools()
        return PoolUtils.getTimers(pools, self.timerFilters)

    def mutedChannels(self):
        """ provides muted channels from pool

        :returns: muted channels from pool
        :rtype: :obj:`list` <:obj:`str`>
        """
        pools = self.__selector.getPools()
        nexusconfig_device = self.__selector.setConfigInstance()
        res = set(PoolUtils.filterNames(pools, self.mutedChannelFilters))
        avds = TangoUtils.command(nexusconfig_device,
                                  "availableDataSources")
        try:
            xmls = TangoUtils.command(
                nexusconfig_device, "dataSources")
            dsxmls = dict(zip(avds, xmls))
        except Exception:
            dsxmls = {}
            for ds in avds:
                try:
                    dsxmls[Utils.tostr(ds)] = TangoUtils.command(
                        nexusconfig_device, "dataSources",
                        [Utils.tostr(ds)])[0]
                except Exception:
                    pass
        lst = []
        for ds, dsxml in dsxmls.items():
            if sys.version_info > (3,):
                root = et.fromstring(bytes(dsxml, "UTF-8"),
                                     parser=XMLParser(collect_ids=False))
            else:
                root = et.fromstring(dsxml,
                                     parser=XMLParser(collect_ids=False))
            nodes = root.findall(".//datasource")
            if nodes:
                record = Utils.getRecord(nodes[0])
                lst.append(json.dumps({"name": ds, "full_name": record}))
        res.update(set(PoolUtils.filterNames(
            None, self.mutedChannelFilters, lst)))
        return list(res)

#  commands

    def __configCommand(self, command, *var):
        """ executes command on configuration server

        :param command: command name
        :type command: :obj:`str`
        :param var: command parameter list
        :type var: [ `any` ]
        :returns: command result
        :rtype: `any`
        """
        return self.__selector.configCommand(command, *var)

    def mandatoryComponents(self):
        """ mandatory components

        :returns: list of mandatory components
        :rtype: :obj:`list` <:obj:`str`>
        """
        mc = self.__configCommand("mandatoryComponents") or []
        return mc

    def availableComponents(self):
        """ available components

        :returns: list of available components
        :rtype: :obj:`list` <:obj:`str`>
        """
        ac = self.__configCommand("availableComponents") or []
        return ac

    def availableProfiles(self):
        """ available selections

        :returns: list of available selections
        :rtype: :obj:`list` <:obj:`str`>
        """
        ac = self.__configCommand("availableSelections") or []
        return ac

    def availableDataSources(self):
        """ available datasources

        :returns: list of available datasources
        :rtype: :obj:`list` <:obj:`str`>
        """
        ad = self.__configCommand("availableDataSources") or []
        return ad

    def poolElementNames(self, listattr):
        """ provides names from given pool listattr

        :param listattr: name of pool attribute with a element list
        :type listattr: :obj:`str`
        :returns: names from given pool listattr
        :rtype: :obj:`list` <:obj:`str`>
        """
        return self.__selector.poolElementNames(listattr)

    def saveProfile(self):
        """ saves configuration
        """
        fl = open(self.profileFile, "w+")
        json.dump(self.__selector.get(), fl)

    def storeProfile(self):
        """ saves configuration
        """
        self.__selector.storeSelection()

    def fetchProfile(self):
        """ fetch configuration
        """
        self.__profileManager.fetchProfile()

    def loadProfile(self):
        """ loads configuration
        """
        fl = open(self.profileFile, "r")
        self.__selector.set(json.load(fl))

    def componentClientSources(self, cps):
        """ provides description of client datasources

        :param cps: component names
        :type cps: :obj:`list` <:obj:`str`>
        :returns: JSON string with description of client datasources
        :rtype: :obj:`str`
        """
        nexusconfig_device = self.__selector.setConfigInstance()
        describer = Describer(nexusconfig_device)
        if cps:
            cp = cps
        else:
            cp = self.components
        dc = describer.components(cp, '', 'CLIENT', self.configVariables)
        jdc = json.dumps(dc)
        return jdc

    def componentSources(self, cps):
        """ provides description of datasources

        :param cps: component names
        :type cps: :obj:`list` <:obj:`str`>
        :returns: JSON string with description of client datasources
        :rtype: :obj:`str`
        """
        nexusconfig_device = self.__selector.setConfigInstance()
        describer = Describer(nexusconfig_device)
        if cps:
            cp = cps
        else:
            cp = self.components
        dc = describer.components(cp, '', '', self.configVariables)
        jdc = json.dumps(dc)
        return jdc

    def createWriterConfiguration(self, cps):
        """ create configuration and clean stepdatasources and linkdatasources

        :param cps: component names
        :type cps: :obj:`list` <:obj:`str`>
        :returns: JSON string with description of client datasources
        :rtype: :obj:`str`
        """
        nexusconfig_device = self.__selector.setConfigInstance()
        if cps:
            cp = cps
        else:
            cp = self.components
        try:
            TangoUtils.command(
                nexusconfig_device, "createConfiguration", cp)
        except PyTango.CommunicationFailed as cf:
            if len(cf.args) >= 2 and \
               cf.args[1].reason == "API_DeviceTimedOut":
                TangoUtils.wait(nexusconfig_device)
            else:
                raise
        nexusconfig_device.stepdatasources = "[]"
        nexusconfig_device.linkdatasources = "[]"

        return Utils.tostr(nexusconfig_device.xmlstring)

    def updateConfigVariables(self):
        """  sends ConfigVariables into ConfigServer
        and updates serialno if appendEntry selected
        """
        confvars = self.configVariables
        nexusconfig_device = self.__selector.setConfigInstance()
        jvars = json.loads(confvars)
        cvars = json.loads(nexusconfig_device.variables)
        # appending scans to one file?
        if self.appendEntry and 'serialno' not in jvars.keys():
            # an entry name should contain $var.serialno
            if 'serialno' in cvars.keys():
                try:
                    sn = int(cvars["serialno"])
                    sn += 1
                    cvars["serialno"] = Utils.tostr(sn)
                except ValueError:
                    pass
            else:
                cvars["serialno"] = Utils.tostr(1)
            jvars["serialno"] = cvars["serialno"]
            confvars = json.dumps(jvars)
        nexusconfig_device.variables = Utils.tostr(confvars)
        props = json.loads(self.channelProperties("canfail"))
        sprops = set([ky for ky, vl in props.items() if vl])
        nexusconfig_device.canfaildatasources = json.dumps(
            list(sprops | set(self.defaultCanFailDataSources)))

    def preselectComponents(self):
        """ checks existing controllers of pools
        """
        self.__selector.preselect()
        gc.collect()

    def resetPreselectedComponents(self):
        """ reset preselected Components to defaultPreselectedComponents
        """
        self.__selector.resetPreselectedComponents(
            self.defaultPreselectedComponents)
        self.__selector["DataSourcePreselection"] = '{}'
        self.preselectComponents()
        self.storeProfile()

    def deleteAllProfiles(self):
        """ clear all selections
        """
        avsel = self.availableProfiles()
        if avsel:
            inst = self.__selector.setConfigInstance()
            for name in avsel:
                inst.deleteSelection(name)

    def dataSourceDescription(self, datasources):
        """ describe datasources

        :param datasources: list for datasource names
        :type datasources: :obj:`list` <:obj:`str`>
        :returns: list of dictionary with description of datasources
        :rtype: [{"dsname": :obj:`str`, "dstype": :obj:`str`, \
                  "record": :obj:`str`}, ...]
        """
        nexusconfig_device = self.__selector.setConfigInstance()
        describer = Describer(nexusconfig_device)
        return describer.dataSources(datasources)

    def createDataSources(self, datasources):
        """ describe datasources

        :param datasources:  JSON dictionary with
                             {``dsname``: ``tangosource``, ...}
        :type datasources: :obj:`str`
        """
        jvar = Utils.stringToDictJson(datasources)
        jdss = json.loads(jvar)
        tangods = [[name, name, source] for name, source in jdss.items()]
        self.__profileManager.createDataSources(tangods)

    def addStepDataSources(self, datasources):
        """ describe datasources

        :param datasources: list for datasource names
        :type datasources: :obj:`list` <:obj:`str`>
        :returns: list of datasources not found in components
        :rtype: :obj:`list` <:obj:`str`>
        """
        inst = self.__selector.setConfigInstance()
        describer = Describer(inst)
        cp = self.components
        cpdss = describer.components(cp, '', '', self.configVariables)
        dss = [ds["dsname"]
               for ds in cpdss if ds["strategy"] in ['INIT', 'FINAL']]

        dsources = set(datasources or [])
        found = json.dumps(list(dsources & set(dss)))
        notfound = list(dsources - set(dss))
        inst.stepdatasources = found
        inst.linkdatasources = found
        return notfound

# MntGrp methods

    def deleteProfile(self, name):
        """ deletes mntgrp

        :param name: mntgrp name
        :type name: :obj:`str`
        """
        self.__profileManager.deleteProfile(name)

    def mntGrpConfiguration(self):
        """ provides configuration of mntgrp

        :returns: string with mntgrp configuration
        :rtype: :obj:`str`
        """
        return self.__profileManager.mntGrpConfiguration()

    def isMntGrpUpdated(self):
        """ check if active measurement group was changed

        :returns: True if it is different to the current setting
        :rtype: :obj:`bool`
        """
        return self.__profileManager.isMntGrpUpdated()

    def updateMntGrp(self):
        """ set active measurement group from components

        :returns: string with mntgrp configuration
        :rtype: :obj:`str`
        """
        return self.__profileManager.updateProfile(False)

    def switchProfile(self, toActive=True):
        """ switch to active measurement

        :param toActive: if False update the current profile
        :type toActive: :obj:`bool`
        """
        self.__profileManager.switchProfile(toActive)

    def updateProfile(self):
        """ update profile and measurement group

        :returns: string with mntgrp configuration
        :rtype: :obj:`str`
        """
        return self.__profileManager.updateProfile(True)

    def importMntGrp(self):
        """ import setting from active measurement
        """
        self.__profileManager.importMntGrp()

    def availableMntGrps(self):
        """ available mntgrps

        :returns: list of available measurement groups
        :rtype: :obj:`list` <:obj:`str`>
        """
        return self.__profileManager.availableMntGrps()

# Dynamic component methods

    def createDynamicComponent(self, params):
        """ creates dynamic component

        :param params: datasource parameters
        :type params: :obj:`list` <:obj:`str`>
        :returns: dynamic component name
        :rtype: :obj:`str`
        """
        nexusconfig_device = self.__selector.setConfigInstance()
        dcpcreator = DynamicComponent(
            nexusconfig_device, self.defaultNeXusPath)
        if isinstance(params, (list, tuple)):
            if len(params) > 0 and params[0]:
                dcpcreator.setStepDSources(
                    json.loads(params[0]))
            else:
                dcpcreator.setStepDSources(self.selectedDataSources())
            if len(params) > 1 and params[1]:
                dcpcreator.setStepDictDSources(json.loads(params[1]))
            if len(params) > 2 and params[2]:
                dcpcreator.setInitDSources(json.loads(params[2]))
            else:
                dcpcreator.setInitDSources(self.preselectedDataSources())

        # pools = self.__selector.getPools()
        # channelsources = PoolUtils.getChannelSources(self.__pools, aliases)

        withoutLinks = self.components
        links = json.loads(self.channelProperties("link"))
        for ds in withoutLinks:
            links[ds] = False

        dcpcreator.setLabelParams(
            self.channelProperties("label"),
            self.channelProperties("nexus_path"),
            json.dumps(links),
            self.channelProperties("data_type"),
            self.channelProperties("shape"))
        dcpcreator.setDefaultLinkPath(
            bool(self.__selector["DefaultDynamicLinks"]),
            Utils.tostr(self.__selector["DefaultDynamicPath"]))

        return dcpcreator.create()

    def removeDynamicComponent(self, name):
        """ removes dynamic component

        :param name: dynamic component name
        :type name: :obj:`str`
        """
        nexusconfig_device = self.__selector.setConfigInstance()
        dcpcreator = DynamicComponent(nexusconfig_device)
        dcpcreator.remove(name)

# Environment methods:

    def scanEnvVariables(self):
        """ gets Scan Environment Data

        :returns: JSON String with important variables
        :rtype: :obj:`str`
        """
        return self.__selector.getScanEnvVariables()

    def setScanEnvVariables(self, jdata):
        """ sets Scan Environment Data

        :param jdata: JSON String with important variables
        :type jdata: :obj:`str`
        """
        return self.__selector.setScanEnvVariables(jdata)

    def importEnvProfile(self):
        """ imports all Enviroutment Data
        """
        self.__selector.importEnv()

    def exportEnvProfile(self):
        """ exports all Enviroutment Data
        """
        nenv = {}
        commands = {
            "components": "Components",
            "dataSources": "DataSources"
        }
        for attr, name in commands.items():
            vl = getattr(self, attr)
            nenv[Utils.tostr(name)] = vl
        self.__selector.exportEnv(cmddata=nenv)
