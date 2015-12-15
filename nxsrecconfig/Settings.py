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
## \file Settings.py
# nxswriter runner

"""  NeXus Sardana Recorder Settings implementation """

import json
import gc
import PyTango
import nxsrecconfig
from .Describer import Describer
from .DynamicComponent import DynamicComponent
from .Utils import Utils, TangoUtils, MSUtils, PoolUtils
from .ProfileManager import ProfileManager
from .Selector import Selector
from .MacroServerPools import MacroServerPools
from . import Streams


## NeXus Sardana Recorder settings
class Settings(object):

    ## ccontructor
    # \param server NXSRecSelector server
    def __init__(self, server=None, numberofthreads=None):
        ## Tango server
        self.__server = server
        ## number of threads
        self.numberOfThreads = numberofthreads or 20

        ## configuration selection
        self.__msp = MacroServerPools(self.numberOfThreads)

        ## configuration selection
        self.__selector = Selector(self.__msp, nxsrecconfig.__version__)

        ## profile
        self.__profileManager = ProfileManager(self.__selector)

        ## configuration file
        self.profileFile = '/tmp/nxsrecconfig.cfg'

        ## tango database
        self.__db = PyTango.Database()

        ## timer filter list
        self.timerFilterList = ["*dgg*", "*/ctctrl0*"]
        ## default device groups
        self.__defaultDeviceGroups = \
            '{"timer": ["*exp_t*"], "dac": ["*exp_dac*"], ' \
            + '"counter": ["*exp_c*"], "mca": ["*exp_mca*"], '\
            + '"adc": ["*exp_adc*"], "motor": ["*exp_mot*"]}'

        ## device groups
        self.__deviceGroups = str(self.__defaultDeviceGroups)
        ## administator data
        self.__adminDataNames = '[]'

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
        self.fetchProfile()

    ## provides values of the required variable
    # \param name name of the required variable
    # \returns  values of the required variable
    def value(self, name):
        vl = ''
        if name in self.__selector.keys():
            vl = self.__selector[name]
            if isinstance(vl, unicode):
                vl = str(vl)
        return vl

    ## provides names of variables
    def names(self):
        return self.__selector.keys()

## read-only variables

    ## provides user selected components
    # \returns list of available selected components
    def selectedComponents(self):
        return self.__profileManager.components()

    ## provides all configuration components
    # \returns list of available selected components
    def __components(self):
        return list(set(self.selectedComponents()) |
                    set(self.preselectedComponents()) |
                    set(self.mandatoryComponents()))

    ##  provides selected components
    components = property(
        __components,
        doc='provides selected components')

    ## provides preselected components
    # \returns list of available preselected components
    def preselectedComponents(self):
        return self.__profileManager.preselectedComponents()

    ## provides description component errors
    # \returns list of available description component errors
    def __getDescriptionErrors(self):
        return self.__selector.descErrors

    ## provides preselected components
    descriptionErrors = property(__getDescriptionErrors,
                                 doc='provides description component errors')

    ## provides selected datasources
    # \returns list of available selected datasources
    def selectedDataSources(self):
        return self.__profileManager.dataSources()

    def __dataSources(self):
        return list(
            set(self.selectedDataSources()) |
            set(self.componentDataSources())
        )

    ##  provides selected data sources
    dataSources = property(
        __dataSources,
        doc=' provides selected data sources')

    ## provides a list of profile component DataSources
    # \returns list of profile component datasources
    def componentDataSources(self):
        return self.__profileManager.componentDataSources()

## read-write variables

    ## get method for defaultPreselectedComponents attribute
    # \returns list of components
    def __getDefaultPreselectedComponents(self):
        return self.__profileManager.defaultPreselectedComponents

    ## set method for defaultPreselectedComponents attribute
    # \param components list of components
    def __setDefaultPreselectedComponents(self, components):
        self.__profileManager.defaultPreselectedComponents = components

    ## default PreselectedComponents
    defaultPreselectedComponents = property(
        __getDefaultPreselectedComponents,
        __setDefaultPreselectedComponents,
        doc='default Preselected components')

    ## get method for configDevice attribute
    # \returns name of configDevice
    def __getConfigDevice(self):
        return self.__selector["ConfigDevice"]

    ## set method for configDevice attribute
    # \param name of configDevice
    def __setConfigDevice(self, name):
        if name != self.__selector["ConfigDevice"]:
            self.__selector["ConfigDevice"] = name
            self.switchProfile(toActive=False)

    ## the json data string
    configDevice = property(__getConfigDevice, __setConfigDevice,
                            doc='configuration server device name')

    ## get method for poolBlacklist attribute
    # \returns name of poolBlacklist
    def __getPoolBlacklist(self):
        return self.__msp.poolBlacklist

    ## set method for poolBlacklist attribute
    # \param name of poolBlacklist
    def __setPoolBlacklist(self, name):
        self.__msp.poolBlacklist = name

    ## black list of pools
    poolBlacklist = property(__getPoolBlacklist, __setPoolBlacklist,
                             doc='pool black list')

    ## set method for configuration attribute
    # \param name of configuration
    def __setProfileConfiguration(self, jconf):
        self.__selector.set(json.loads(jconf))
        self.storeProfile()

    ## get method for configuration attribute
    # \returns configuration
    def __getProfileConfiguration(self):
        return json.dumps(self.__selector.get())

    ## the json data string
    profileConfiguration = property(
        __getProfileConfiguration,
        __setProfileConfiguration,
        doc='preselected components group')

    ## set method for appendEntry attribute
    # \param name of appendEntry
    def __setAppendEntry(self, ae):
        self.__selector["AppendEntry"] = bool(ae)
        self.storeProfile()

    ## get method for appendEntry attribute
    # \returns flag of appendEntry
    def __getAppendEntry(self):
        return bool(self.__selector["AppendEntry"])

    ## the json data string
    appendEntry = property(
        __getAppendEntry,
        __setAppendEntry,
        doc='flag for append entry')

    ## get method for userData attribute
    # \returns name of userData
    def __getUserData(self):
        return self.__selector["UserData"]

    ## set method for userData attribute
    # \param name of userData
    def __setUserData(self, name):
        jname = Utils.stringToDictJson(name)
        if self.__selector["UserData"] != jname:
            self.__selector["UserData"] = jname
            self.storeProfile()

    ## the json data string
    userData = property(
        __getUserData,
        __setUserData,
        doc='client data record')

    ## get method for deviceGroups attribute
    # \returns name of deviceGroups
    def __getDeviceGroups(self):
        try:
            ldct = json.loads(self.__deviceGroups)
            assert isinstance(ldct, dict)
            for vl in ldct.values():
                assert isinstance(vl, list)
            return self.__deviceGroups
        except Exception:
            return self.__defaultDeviceGroups

    ## sets method for deviceGroups attribute
    # \param name of deviceGroups
    def __setDeviceGroups(self, name):
        jname = Utils.stringToDictJson(name)
        ## device groups
        self.__deviceGroups = jname

    ## the json data string
    deviceGroups = property(
        __getDeviceGroups,
        __setDeviceGroups,
        doc='device groups')

    # \returns name of adminDataNames
    def __getAdminDataNames(self):
        try:
            lad = json.loads(self.__adminDataNames)
            assert isinstance(lad, list)
            return self.__adminDataNames
        except Exception:
            return '[]'

    ## set method for adminDataNames attribute
    # \param name of adminDataNames
    def __setAdminDataNames(self, name):
        jname = Utils.stringToListJson(name)
        ## administator data
        self.__adminDataNames = jname

    ## the json data string
    adminDataNames = property(
        __getAdminDataNames,
        __setAdminDataNames,
        doc='administrator data')

    ## get method for configVariables attribute
    # \returns name of configVariables
    def __getConfigVariables(self):
        return self.__selector["ConfigVariables"]

    ## set method for configVariables attribute
    # \param name of configVariables
    def __setConfigVariables(self, name):
        jname = Utils.stringToDictJson(name)
        if self.__selector["ConfigVariables"] != jname:
            self.__selector["ConfigVariables"] = jname
            self.storeProfile()

    ## the json variables string
    configVariables = property(
        __getConfigVariables,
        __setConfigVariables,
        doc='configuration variables')

    ## get method for dataSourceGroup attribute
    # \returns names of STEP dataSources
    def __getStepDatSources(self):
        inst = self.__selector.setConfigInstance()
        if inst.stepdatasources:
            return inst.stepdatasources
        else:
            return "[]"

    ## set method for dataSourceGroup attribute
    # \param names of STEP dataSources
    def __setStepDatSources(self, names):
        inst = self.__selector.setConfigInstance()
        inst.stepdatasources = names

    ## the json data string
    stepdatasources = property(
        __getStepDatSources,
        __setStepDatSources,
        doc='step datasource list')

    def channelProperties(self, ptype):
        props = json.loads(self.__selector["ChannelProperties"])
        return json.dumps(props[ptype])

    def setChannelProperties(self, typeandvariables):
        ptype, variables = typeandvariables
        jvar = Utils.stringToDictJson(variables)
        props = json.loads(self.__selector["ChannelProperties"])
        lvar = json.dumps(props[ptype])
        if lvar != jvar:
            props[ptype] = json.loads(jvar)
            self.__selector["ChannelProperties"] = json.dumps(props)
            self.storeProfile()

    ## get method for mntGrp attribute
    # \returns name of mntGrp
    def __getMntGrp(self):
        return self.__selector["MntGrp"]

    ## set method for mntGrp attribute
    # \param name of mntGrp
    def __setMntGrp(self, name):
        self.__selector["MntGrp"] = name

    ## the json data string
    mntGrp = property(__getMntGrp, __setMntGrp,
                      doc='measurement group')

    ## get method for door attribute
    # \returns name of door
    def __getDoor(self):
        return self.__selector["Door"]

    ## set method for door attribute
    # \param name of door
    def __setDoor(self, name):
        self.__selector["Door"] = name
        self.__msp.updateMacroServer(self.__selector["Door"])

    ## the json data string
    door = property(__getDoor, __setDoor,
                    doc='door server device name')

    ## get method for writerDevice attribute
    # \returns name of writerDevice
    def __getWriterDevice(self):
        return self.__selector["WriterDevice"]

    ## set method for writerDevice attribute
    # \param name of writerDevice
    def __setWriterDevice(self, name):
        self.__selector["WriterDevice"] = name
        self.storeProfile()

    ## the json data string
    writerDevice = property(__getWriterDevice, __setWriterDevice,
                            doc='Writer device name')

    ## get method for ScanDir attribute
    # \returns name of ScanDir
    def __getScanDir(self):
        ms = self.__selector.getMacroServer()
        return str(MSUtils.getEnv('ScanDir', ms))

    ## set method for ScanDir attribute
    # \param name of ScanDir
    def __setScanDir(self, name):
        ms = self.__selector.getMacroServer()
        MSUtils.setEnv('ScanDir', str(name), ms)

    ## the json data string
    scanDir = property(__getScanDir, __setScanDir,
                       doc='scan directory')

    ## get method for ScanID attribute
    # \returns name of ScanID
    def __getScanID(self):
        ms = self.__selector.getMacroServer()
        sid = MSUtils.getEnv('ScanID', ms)
        if sid:
            return int(sid)
        else:
            MSUtils.setEnv('ScanID', 0, ms)
            return 0

    ## set method for ScanID attribute
    # \param name of ScanID
    def __setScanID(self, name):
        ms = self.__selector.getMacroServer()
        MSUtils.setEnv('ScanID', name, ms)

    ## the json data string
    scanID = property(__getScanID, __setScanID,
                      doc='scan id')

    ## get method for ScanFile attribute
    # \returns name of ScanFile
    def __getScanFile(self):
        ms = self.__selector.getMacroServer()
        val = MSUtils.getEnv('ScanFile', ms)
        ret = [val] if isinstance(val, (str, unicode)) else val
        return json.dumps(ret)

    ## set method for ScanFile attribute
    # \param name of ScanFile
    def __setScanFile(self, name):
        jname = json.loads(Utils.stringToListJson(name))

        ms = self.__selector.getMacroServer()
        if isinstance(jname, (list, tuple)) and len(jname) == 1:
            jname = jname[0]
        MSUtils.setEnv('ScanFile', jname, ms)

    ## the json data string
    scanFile = property(__getScanFile, __setScanFile,
                        doc='scan file(s)')

    ## provides components for all variables
    # \returns dictionary with components for all variables
    def variableComponents(self):
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

    ## provides description of all components
    # \returns JSON string with description of all components
    def componentDescription(self):
        dc = self.__profileManager.cpdescription(full=True)
        jdc = json.dumps(dc)
        return jdc

    ## provides full names of pool devices
    # \returns JSON string with full names of pool devices
    def fullDeviceNames(self):
        pools = self.__selector.getPools()
        return json.dumps(PoolUtils.getFullDeviceNames(pools))

    ## provides available Timers from MacroServer pools
    # \returns  available Timers from MacroServer pools
    def availableTimers(self):
        pools = self.__selector.getPools()
        return PoolUtils.getTimers(pools, self.timerFilterList)

##  commands

    ## executes command on configuration server
    # \returns command result
    def __configCommand(self, command, *var):
        return self.__selector.configCommand(command, *var)

    ## mandatory components
    # \returns list of mandatory components
    def mandatoryComponents(self):
        mc = self.__configCommand("mandatoryComponents") or []
        return mc

    ## available components
    # \returns list of available components
    def availableComponents(self):
        ac = self.__configCommand("availableComponents") or []
        return ac

    ## available selections
    # \returns list of available selections
    def availableProfiles(self):
        ac = self.__configCommand("availableSelections") or []
        return ac

    ## available datasources
    # \returns list of available datasources
    def availableDataSources(self):
        ad = self.__configCommand("availableDataSources") or []
        return ad

    ## available pool channels
    # \returns pool channels of the macroserver pools
    def poolChannels(self):
        return self.__selector.poolChannels()

    ## available pool motors
    # \returns pool motors of the macroserver pools
    def poolMotors(self):
        return self.__selector.poolMotors()

    ## saves configuration
    def saveProfile(self):
        fl = open(self.profileFile, "w+")
        json.dump(self.__selector.get(), fl)

    ## saves configuration
    def storeProfile(self):
        self.__selector.storeSelection()

    ## fetch configuration
    def fetchProfile(self):
        self.__profileManager.fetchProfile()

    ## loads configuration
    def loadProfile(self):
        fl = open(self.profileFile, "r")
        self.__selector.set(json.load(fl))

    ## provides description of client datasources
    # \param cps component names
    # \returns JSON string with description of client datasources
    def componentClientSources(self, cps):
        nexusconfig_device = self.__selector.setConfigInstance()
        describer = Describer(nexusconfig_device)
        if cps:
            cp = cps
        else:
            cp = self.components
        dc = describer.components(cp, '', 'CLIENT', self.configVariables)
        jdc = json.dumps(dc)
        return jdc

    ## create configuration
    # \param cps component names
    # \returns JSON string with description of client datasources
    def createWriterConfiguration(self, cps):
        nexusconfig_device = self.__selector.setConfigInstance()
        if cps:
            cp = cps
        else:
            cp = self.components
        TangoUtils.command(nexusconfig_device,
                           "createConfiguration",
                           cp)
        return str(nexusconfig_device.xmlstring)

    ##  sends ConfigVariables into ConfigServer
    #        and updates serialno if appendEntry selected
    def updateConfigVariables(self):
        confvars = self.configVariables
        nexusconfig_device = self.__selector.setConfigInstance()
        jvars = json.loads(confvars)
        cvars = json.loads(nexusconfig_device.variables)
        ## appending scans to one file?
        if self.appendEntry and 'serialno' not in jvars.keys():
            ## an entry name should contain $var.serialno
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

    ## checks existing controllers of pools for
    #      PreselectedDataSources
    def preselectComponents(self):
        self.__selector.updatePreselectedComponents()
        gc.collect()

    ## reset preselected Components to defaultPreselectedComponents
    def resetPreselectedComponents(self):
        self.__selector.resetPreselectedComponents(
            self.defaultPreselectedComponents)
        self.preselectComponents()
        self.storeProfile()

    ## clear all selections
    def deleteAllProfiles(self):
        avsel = self.availableProfiles()
        if avsel:
            inst = self.__selector.setConfigInstance()
            for name in avsel:
                inst.deleteSelection(name)

    ## describe datasources
    # \param datasources list for datasource names
    # \returns list of dictionary with description of datasources
    def dataSourceDescription(self, datasources):
        nexusconfig_device = self.__selector.setConfigInstance()
        describer = Describer(nexusconfig_device)
        return describer.dataSources(datasources)

# MntGrp methods

    ## deletes mntgrp
    # \param name mntgrp name
    def deleteProfile(self, name):
        self.__profileManager.deleteProfile(name)

    ## provides configuration of mntgrp
    # \returns string with mntgrp configuration
    def mntGrpConfiguration(self):
        return self.__profileManager.mntGrpConfiguration()

    ## check if active measurement group was changed
    # \returns True if it is different to the current setting
    def isMntGrpUpdated(self):
        return self.__profileManager.isMntGrpUpdated()

    ## set active measurement group from components
    # \returns string with mntgrp configuration
    def updateMntGrp(self):
        return self.__profileManager.updateProfile()

    ## switch to active measurement
    def switchProfile(self, toActive=True):
        self.__profileManager.switchProfile(toActive)

    ## import setting from active measurement
    def importMntGrp(self):
        self.__profileManager.importMntGrp()

    ## available mntgrps
    # \returns list of available measurement groups
    def availableMntGrps(self):
        return self.__profileManager.availableMntGrps()

# Dynamic component methods

    ## creates dynamic component
    # \param params datasource parameters
    # \returns dynamic component name
    def createDynamicComponent(self, params):
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
                dcpcreator.setInitDSources(json.loads(
                    self.__selector["InitDataSources"]))

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

    ## removes dynamic component
    # \param name dynamic component name
    def removeDynamicComponent(self, name):
        nexusconfig_device = self.__selector.setConfigInstance()
        dcpcreator = DynamicComponent(nexusconfig_device)
        dcpcreator.remove(name)

# Environment methods:

    ## gets Scan Environment Data
    # \returns JSON String with important variables
    def __getScanEnvVariables(self):
        return self.__selector.getScanEnvVariables()

    ## sets Scan Environment Data
    # \param jdata JSON String with important variables
    def __setScanEnvVariables(self, jdata):
        return self.__selector.setScanEnvVariables(jdata)

    ## the json data string
    scanEnvVariables = property(
        __getScanEnvVariables,
        __setScanEnvVariables,
        doc='scan environment data'
    )

    ## imports all Enviroutment Data
    def importEnvProfile(self):
        self.__selector.importEnv()

    ## exports all Enviroutment Data
    def exportEnvProfile(self):
        nenv = {}
        commands = {
            "components": "Components",
            "preselectedComponents": "PreselectedComponents",
            "dataSources": "DataSources"
        }
        for attr, name in commands.items():
            vl = getattr(self, attr)
            nenv[str(name)] = vl
        self.__selector.exportEnv(cmddata=nenv)
