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
#

"""  NeXus Sardana Recorder Settings implementation """

import json
import gc
import PyTango
import xml.dom.minidom

from .Describer import Describer
from .DynamicComponent import DynamicComponent
from .Utils import Utils, TangoUtils, MSUtils, PoolUtils
from .ProfileManager import ProfileManager
from .Selector import Selector
from .Release import __version__
from .MacroServerPools import MacroServerPools
from . import Streams


class Settings(object):
    """ NeXus Sardana Recorder settings
    """

    def __init__(self, server=None, numberofthreads=None):
        """ contructor

        :param server: NXSRecSelector server
        :param numberofthreads: number of threads used to check device state
        """
        #: Tango server
        self.__server = server
        #: number of threads
        self.numberOfThreads = numberofthreads or 20

        #: configuration selection
        self.__msp = MacroServerPools(self.numberOfThreads)

        #: configuration selection
        self.__selector = Selector(self.__msp, self.version)

        #: profile
        self.__profileManager = ProfileManager(self.__selector)

        #: configuration file
        self.profileFile = '/tmp/nxsrecconfig.cfg'

        #: tango database
        self.__db = PyTango.Database()

        #: timer filters
        self.timerFilters = ["*dgg*", "*/ctctrl0*"]
        #: timer filters
        self.mutedChannelFilters = ["*tip551*"]
        #: default device groups
        self.__defaultDeviceGroups = \
            '{"timer": ["*exp_t*"], "dac": ["*exp_dac*"], ' \
            + '"counter": ["*exp_c*"], "mca": ["*exp_mca*"], ' \
            + '"adc": ["*exp_adc*"], "motor": ["*exp_mot*"]}'

        #: device groups
        self.__deviceGroups = str(self.__defaultDeviceGroups)
        #: administator data
        self.adminDataNames = []

        if server:
            if hasattr(self.__server, "log_fatal"):
                Streams.log_fatal = server.log_fatal
            if hasattr(self.__server, "log_error"):
                Streams.log_error = server.log_error
            if hasattr(self.__server, "log_warn"):
                Streams.log_warn = server.log_warn
            if hasattr(self.__server, "log_info"):
                Streams.log_info = server.log_info
            if hasattr(self.__server, "log_debug"):
                Streams.log_debug = server.log_debug

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
            message = str(info[1].__str__()) + "\n " + (" ").join(
                traceback.format_tb(sys.exc_info()[2]))
            Streams.error("Error in fetching profile: %s"
                          % self.__selector["MntGrp"])
            Streams.error(str(message))

    def value(self, name):
        """ provides values of the required variable

        :param name: name of the required variable
        :returns: values of the required variable
        """
        vl = ''
        if name in self.__selector.keys():
            vl = self.__selector[name]
            if isinstance(vl, unicode):
                vl = str(vl)
        return vl

    def names(self):
        """ provides names of variables

        :returns:  all names of variables
        """
        return self.__selector.keys()

    def __version(self):
        """ provides server version

        :returns: server version
        """
        return __version__

    #: server version
    version = property(
        __version,
        doc='server version')

# read-only variables

    def administratorDataNames(self):
        """ provides administrator data names

        :returns: list of provides administrator data names
        """
        return list(self.adminDataNames)

    def selectedComponents(self):
        """ provides user selected components

        :returns: list of available selected components
        """
        return self.__profileManager.components()

    def __components(self):
        """ provides all configuration components

        :returns: list of available selected components
        """
        return list(set(self.selectedComponents()) |
                    set(self.preselectedComponents()) |
                    set(self.mandatoryComponents()))

    #: provides selected components
    components = property(
        __components,
        doc='provides selected components')

    def preselectedComponents(self):
        """ provides preselected components

        :returns: list of available preselected components
        """
        return self.__profileManager.preselectedComponents()

    def __getDescriptionErrors(self):
        """ provides description component errors

        :returns: list of available description component errors
        """
        return self.__selector.descErrors

    #: provides preselected components
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
        """
        return self.__profileManager.preselectedDataSources()

    def __dataSources(self):
        """ provides all selected data sources

        :returns: all selected data sources
        """
        return list(
            set(self.selectedDataSources()) |
            set(self.componentDataSources())
        )

    #: provides all selected data sources
    dataSources = property(
        __dataSources,
        doc=' provides selected data sources')

    def componentDataSources(self):
        """ provides a list of profile component DataSources

        :returns: list of profile component datasources
        """
        return self.__profileManager.componentDataSources()

# read-write variables

    def __getDefaultPreselectedComponents(self):
        """ get method for defaultPreselectedComponents attribute

        :returns: list of components
        """
        return self.__profileManager.defaultPreselectedComponents

    def __setDefaultPreselectedComponents(self, components):
        """ set method for defaultPreselectedComponents attribute

        :param components: list of components
        """
        self.__profileManager.defaultPreselectedComponents = components

    #: default PreselectedComponents
    defaultPreselectedComponents = property(
        __getDefaultPreselectedComponents,
        __setDefaultPreselectedComponents,
        doc='default Preselected components')

    def __getConfigDevice(self):
        """ get method for configDevice attribute

        :returns: name of configDevice
        """
        return self.__selector["ConfigDevice"]

    def __setConfigDevice(self, name):
        """ set method for configDevice attribute

        :param name: name of configDevice
        """
        if name != self.__selector["ConfigDevice"]:
            self.__selector["ConfigDevice"] = name
            self.switchProfile(toActive=False)

    #: the json data string
    configDevice = property(__getConfigDevice, __setConfigDevice,
                            doc='configuration server device name')

    def __getPoolBlacklist(self):
        """ get method for poolBlacklist attribute

        :returns: name of poolBlacklist
        """
        return self.__msp.poolBlacklist

    def __setPoolBlacklist(self, name):
        """ set method for poolBlacklist attribute

        :param name: name of poolBlacklist
        """
        self.__msp.poolBlacklist = name

    #: black list of pools
    poolBlacklist = property(__getPoolBlacklist, __setPoolBlacklist,
                             doc='pool black list')

    def __setProfileConfiguration(self, jconf):
        """ set method for configuration attribute
        :param name: name of configuration
        """
        self.__selector.set(json.loads(jconf))
        self.storeProfile()

    def __getProfileConfiguration(self):
        """ get method for configuration attribute

        :returns: configuration
        """
        return json.dumps(self.__selector.get())

    #: the json data string
    profileConfiguration = property(
        __getProfileConfiguration,
        __setProfileConfiguration,
        doc='preselected components group')

    def __setAppendEntry(self, ae):
        """ set method for appendEntry attribute
        :param name: name of appendEntry
        """
        self.__selector["AppendEntry"] = bool(ae)
        self.storeProfile()

    ##
    def __getAppendEntry(self):
        """ get method for appendEntry attribute

        :returns: flag of appendEntry
        """
        return bool(self.__selector["AppendEntry"])

    #: the json data string
    appendEntry = property(
        __getAppendEntry,
        __setAppendEntry,
        doc='flag for append entry')

    ##
    def __getUserData(self):
        """ get method for userData attribute

        :returns: name of userData
        """
        return self.__selector["UserData"]

    ##
    def __setUserData(self, name):
        """
        set method for userData attribute

        :param name: name of userData
        """
        jname = Utils.stringToDictJson(name)
        if self.__selector["UserData"] != jname:
            self.__selector["UserData"] = jname
            self.storeProfile()

    #: the json data string
    userData = property(
        __getUserData,
        __setUserData,
        doc='client data record')

    def __getDeviceGroups(self):
        """ get method for deviceGroups attribute

        :returns: name of deviceGroups
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

    def __setDeviceGroups(self, name):
        """ sets method for deviceGroups attribute

        :param name: name of deviceGroups
        """
        jname = Utils.stringToDictJson(name)
        #: device groups
        self.__deviceGroups = jname

    #: the json data string
    deviceGroups = property(
        __getDeviceGroups,
        __setDeviceGroups,
        doc='device groups')

    def __getConfigVariables(self):
        """ get method for configVariables attribute

        :returns: name of configVariables
        """
        return self.__selector["ConfigVariables"]

    def __setConfigVariables(self, name):
        """ set method for configVariables attribute

        :param name: name of configVariables
        """
        jname = Utils.stringToDictJson(name)
        if self.__selector["ConfigVariables"] != jname:
            self.__selector["ConfigVariables"] = jname
            self.storeProfile()

    #: the json variables string
    configVariables = property(
        __getConfigVariables,
        __setConfigVariables,
        doc='configuration variables')

    def __getStepDatSources(self):
        """ get method for dataSourceGroup attribute

        :returns: names of STEP dataSources
        """
        inst = self.__selector.setConfigInstance()
        if inst.stepdatasources:
            return inst.stepdatasources
        else:
            return "[]"

    def __setStepDatSources(self, names):
        """ set method for dataSourceGroup attribute
        :param names: names of STEP dataSources
        """
        inst = self.__selector.setConfigInstance()
        inst.stepdatasources = names

    #: the json data string
    stepdatasources = property(
        __getStepDatSources,
        __setStepDatSources,
        doc='step datasource list')

    def channelProperties(self, ptype):
        """ provides channel properties of the given type

        :param ptype: property type
        :returns:  json dictionary with channel properties
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
        """
        return self.__selector["MntGrp"]

    def __setMntGrp(self, name):
        """ set method for mntGrp attribute

        :param name: name of mntGrp
        """
        self.__selector["MntGrp"] = name

    #: the json data string
    mntGrp = property(__getMntGrp, __setMntGrp,
                      doc='measurement group')

    def __getDoor(self):
        """ get method for door attribute

        :returns: name of door
        """
        return self.__selector["Door"]

    def __setDoor(self, name):
        """ set method for door attribute

        :param name: name of door
        """
        self.__selector["Door"] = name
        self.__msp.updateMacroServer(self.__selector["Door"])

    #: the json data string
    door = property(__getDoor, __setDoor,
                    doc='door server device name')

    def __getMacroServer(self):
        """ get method for macro server attribute

        :returns: name of macro server
        """
        return self.__msp.getMacroServer(self.__selector["Door"])

    #: the json data string
    macroServer = property(__getMacroServer,
                           doc='macroserver device name')

    def __getWriterDevice(self):
        """ get method for writerDevice attribute

        :returns: name of writerDevice
        """
        return self.__selector["WriterDevice"]

    def __setWriterDevice(self, name):
        """ set method for writerDevice attribute

        :param name: name of writerDevice
        """
        self.__selector["WriterDevice"] = name
        self.storeProfile()

    #: the json data string
    writerDevice = property(__getWriterDevice, __setWriterDevice,
                            doc='Writer device name')

    def __getScanDir(self):
        """ get method for ScanDir attribute

        :returns: name of ScanDir
        """
        ms = self.__selector.getMacroServer()
        return str(MSUtils.getEnv('ScanDir', ms))

    def __setScanDir(self, name):
        """ set method for ScanDir attribute

        :param name: name of ScanDir
        """
        ms = self.__selector.getMacroServer()
        MSUtils.setEnv('ScanDir', str(name), ms)

    #: the json data string
    scanDir = property(__getScanDir, __setScanDir,
                       doc='scan directory')

    def __getScanID(self):
        """ get method for ScanID attribute

        :returns: name of ScanID
        """
        ms = self.__selector.getMacroServer()
        sid = MSUtils.getEnv('ScanID', ms)
        if sid:
            return int(sid)
        else:
            MSUtils.setEnv('ScanID', 0, ms)
            return 0

    def __setScanID(self, name):
        """ set method for ScanID attribute

        :param name: name of ScanID
        """
        ms = self.__selector.getMacroServer()
        MSUtils.setEnv('ScanID', name, ms)

    #: the json data string
    scanID = property(__getScanID, __setScanID,
                      doc='scan id')

    def __getScanFile(self):
        """ get method for ScanFile attribute

        :returns: name of ScanFile
        """
        ms = self.__selector.getMacroServer()
        val = MSUtils.getEnv('ScanFile', ms)
        ret = [val] if isinstance(val, (str, unicode)) else val
        return json.dumps(ret)

    def __setScanFile(self, name):
        """ set method for ScanFile attribute

        :param name: name of ScanFile
        """
        jname = json.loads(Utils.stringToListJson(name))

        ms = self.__selector.getMacroServer()
        if isinstance(jname, (list, tuple)) and len(jname) == 1:
            jname = jname[0]
        MSUtils.setEnv('ScanFile', jname, ms)

    #: the json data string
    scanFile = property(__getScanFile, __setScanFile,
                        doc='scan file(s)')

    def variableComponents(self):
        """ provides components for all variables

        :returns: dictionary with components for all variables
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
        """
        dc = self.__profileManager.cpdescription(full=True)
        jdc = json.dumps(dc)
        return jdc

    def fullDeviceNames(self):
        """ provides full names of pool devices

        :returns: JSON string with full names of pool devices
        """
        pools = self.__selector.getPools()
        return json.dumps(PoolUtils.getFullDeviceNames(pools))

    def availableTimers(self):
        """ provides available Timers from MacroServer pools

        :returns:  available Timers from MacroServer pools
        """
        pools = self.__selector.getPools()
        return PoolUtils.getTimers(pools, self.timerFilters)

    def mutedChannels(self):
        """ provides muted channels from pool

        :returns: muted channels from pool
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
        except:
            dsxmls = {}
            for ds in avds:
                try:
                    dsxmls[str(ds)] = TangoUtils.command(
                        nexusconfig_device, "dataSources",
                        [str(ds)])[0]
                except:
                    pass
        lst = []
        for ds, dsxml in dsxmls.items():
            indom = xml.dom.minidom.parseString(dsxml)
            nodes = indom.getElementsByTagName("datasource")
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
        :param var: command parameter list
        :returns: command result
        """
        return self.__selector.configCommand(command, *var)

    def mandatoryComponents(self):
        """ mandatory components

        :returns: list of mandatory components
        """
        mc = self.__configCommand("mandatoryComponents") or []
        return mc

    def availableComponents(self):
        """ available components

        :returns: list of available components
        """
        ac = self.__configCommand("availableComponents") or []
        return ac

    def availableProfiles(self):
        """ available selections

        :returns: list of available selections
        """
        ac = self.__configCommand("availableSelections") or []
        return ac

    def availableDataSources(self):
        """ available datasources

        :returns: list of available datasources
        """
        ad = self.__configCommand("availableDataSources") or []
        return ad

    def poolElementNames(self, listattr):
        """ provides names from given pool listattr

        :param listattr: name of pool attribute with a element list
        :returns: names from given pool listattr
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
        :returns: JSON string with description of client datasources
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

    def createWriterConfiguration(self, cps):
        """ create configuration

        :param cps: component names
        :returns: JSON string with description of client datasources
        """
        nexusconfig_device = self.__selector.setConfigInstance()
        if cps:
            cp = cps
        else:
            cp = self.components
        TangoUtils.command(nexusconfig_device,
                           "createConfiguration",
                           cp)
        return str(nexusconfig_device.xmlstring)

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
                    cvars["serialno"] = str(sn)
                except ValueError:
                    pass
            else:
                cvars["serialno"] = str(1)
            jvars["serialno"] = cvars["serialno"]
            confvars = json.dumps(jvars)
        nexusconfig_device.variables = str(confvars)

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
        :returns: list of dictionary with description of datasources
        """
        nexusconfig_device = self.__selector.setConfigInstance()
        describer = Describer(nexusconfig_device)
        return describer.dataSources(datasources)

# MntGrp methods

    def deleteProfile(self, name):
        """ deletes mntgrp

        :param name: mntgrp name
        """
        self.__profileManager.deleteProfile(name)

    def mntGrpConfiguration(self):
        """ provides configuration of mntgrp

        :returns: string with mntgrp configuration
        """
        return self.__profileManager.mntGrpConfiguration()

    def isMntGrpUpdated(self):
        """ check if active measurement group was changed

        :returns: True if it is different to the current setting
        """
        return self.__profileManager.isMntGrpUpdated()

    def updateMntGrp(self):
        """ set active measurement group from components

        :returns: string with mntgrp configuration
        """
        return self.__profileManager.updateProfile(False)

    def switchProfile(self, toActive=True):
        """ switch to active measurement

        :param toActive: if False update the current profile
        """
        self.__profileManager.switchProfile(toActive)

    def updateProfile(self):
        """ update profile and measurement group

        :param setenv: set ActiveMntGrp and PreScanSnapshot variables
        :returns: string with mntgrp configuration
        """
        return self.__profileManager.updateProfile(True)

    def importMntGrp(self):
        """ import setting from active measurement
        """
        self.__profileManager.importMntGrp()

    def availableMntGrps(self):
        """ available mntgrps

        :returns: list of available measurement groups
        """
        return self.__profileManager.availableMntGrps()

# Dynamic component methods

    def createDynamicComponent(self, params):
        """ creates dynamic component

        :param params: datasource parameters
        :returns: dynamic component name
        """
        nexusconfig_device = self.__selector.setConfigInstance()
        dcpcreator = DynamicComponent(nexusconfig_device)
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
            str(self.__selector["DefaultDynamicPath"]))

        return dcpcreator.create()

    def removeDynamicComponent(self, name):
        """ removes dynamic component

        :param name: dynamic component name
        """
        nexusconfig_device = self.__selector.setConfigInstance()
        dcpcreator = DynamicComponent(nexusconfig_device)
        dcpcreator.remove(name)

# Environment methods:

    def scanEnvVariables(self):
        """ gets Scan Environment Data

        :returns: JSON String with important variables
        """
        return self.__selector.getScanEnvVariables()

    def setScanEnvVariables(self, jdata):
        """ sets Scan Environment Data
        :param jdata: JSON String with important variables
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
            nenv[str(name)] = vl
        self.__selector.exportEnv(cmddata=nenv)
