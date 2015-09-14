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

import gc
import json
import PyTango
from .Describer import Describer
from .DynamicComponent import DynamicComponent
from .Utils import Utils, TangoUtils, MSUtils, PoolUtils
from .MntGrpTools import MntGrpTools
from .Selector import Selector
from .MacroServerPools import MacroServerPools


## NeXus Sardana Recorder settings
class Settings(object):

    ## ccontructor
    # \param server NXSRecSelector server
    def __init__(self, server=None):
        ## Tango server
        self.__server = server
        ## number of threads
        self.numberOfThreads = 20

        ## configuration selection
        self.__msp = MacroServerPools(self.numberOfThreads)

        ## configuration selection
        self.__selector = Selector(self.__msp)

        self.__mntgrptools = MntGrpTools(self.__selector)

        ## configuration file
        self.configFile = '/tmp/nxsrecconfig.cfg'

        ## tango database
        self.__db = PyTango.Database()

        ## timer filter list
        self.timerFilterList = ["*dgg*", "*/ctctrl0*"]
        ## default automaticComponents
        self.defaultAutomaticComponents = []
        ## default device groups
        self.__defaultDeviceGroups = \
            '{"timer": ["*exp_t*"], "dac": ["*exp_dac*"], ' \
            + '"counter": ["*exp_c*"], "mca": ["*exp_mca*"], '\
            + '"adc": ["*exp_adc*"], "motor": ["*exp_mot*"]}'

        ## device groups
        self.__deviceGroups = str(self.__defaultDeviceGroups)
        ## administator data
        self.__adminData = '[]'
        ## error descriptions
        self.__descErrors = []

        self.__setupSelection()

    def __setupSelection(self):
        if not self.__server:
            self.fetchConfiguration()
        ms = self.getMacroServer()
        amntgrp = MSUtils.getEnv('ActiveMntGrp', ms)
        if amntgrp:
            self.__selector["MntGrp"] = amntgrp
        else:
            avsel = self.availableSelections()
            if avsel and avsel[0]:
                self.__selector["MntGrp"] = avsel[0]
        self.fetchConfiguration()

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

    ## provides selected components
    # \returns list of available selected components
    def __components(self):
        cps = json.loads(self.__selector["ComponentGroup"])
        ads = json.loads(self.__selector["DataSourceGroup"])
        dss = [ds for ds in ads if ads[ds]]
        acp = self.availableComponents()
        res = []
        if isinstance(cps, dict):
            res = [cp for cp in cps.keys() if cps[cp]]
            for ds in dss:
                if ds in acp:
                    res.append(ds)
        return res

    ##  provides selected components
    components = property(
        __components,
        doc='provides selected components')

    ## provides automatic components
    # \returns list of available automatic components
    def __automaticComponents(self):
        cps = json.loads(self.__selector["AutomaticComponentGroup"])
        if isinstance(cps, dict):
            return [cp for cp in cps.keys() if cps[cp]]
        else:
            return []

    ## provides automatic components
    automaticComponents = property(__automaticComponents,
                            doc=' provides automatic components')

    ## provides description component errors
    # \returns list of available description component errors
    def __getDescriptionErrors(self):
        return self.__descErrors

    ## provides automatic components
    descriptionErrors = property(__getDescriptionErrors,
                                 doc='provides description component errors')

    ## provides selected datasources
    # \returns list of available selected datasources
    def __dataSources(self):
        dds = self.disableDataSources
        if not isinstance(dds, list):
            dds = []
        dss = json.loads(self.__selector["DataSourceGroup"])
        if isinstance(dss, dict):
            return [ds for ds in dss.keys() if dss[ds] and ds not in dds]
        else:
            return []

    ##  provides selected data sources
    dataSources = property(
        __dataSources,
        doc=' provides selected data sources')

    ## provides a list of Disable DataSources
    # \returns list of disable datasources
    def __disableDataSources(self):
        res = self.cpdescription()
        dds = set()

        for dss in res[0].values():
            if isinstance(dss, dict):
                for ds in dss.keys():
                    dds.add(ds)
        return list(dds)

    ##  provides a list of Disable DataSources
    disableDataSources = property(
        __disableDataSources,
        doc='provides a list of Disable DataSources')

## read-write variables

    ## get method for configDevice attribute
    # \returns name of configDevice
    def __getConfigDevice(self):
        return self.__selector["ConfigDevice"]

    ## set method for configDevice attribute
    # \param name of configDevice
    def __setConfigDevice(self, name):
        if name != self.__selector["ConfigDevice"]:
            self.__selector["ConfigDevice"] = name
            self.switchMntGrp(toActive=False)

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
    def __setConfiguration(self, jconf):
        self.__selector.set(json.loads(jconf))
        self.storeConfiguration()

    ## get method for configuration attribute
    # \returns configuration
    def __getConfiguration(self):
        return json.dumps(self.__selector.get())

    ## the json data string
    configuration = property(
        __getConfiguration,
        __setConfiguration,
        doc='automatic components group')

    ## set method for appendEntry attribute
    # \param name of appendEntry
    def __setAppendEntry(self, ae):
        self.__selector["AppendEntry"] = bool(ae)
        self.storeConfiguration()

    ## get method for appendEntry attribute
    # \returns flag of appendEntry
    def __getAppendEntry(self):
        return bool(self.__selector["AppendEntry"])

    ## the json data string
    appendEntry = property(
        __getAppendEntry,
        __setAppendEntry,
        doc='flag for append entry')

    ## get method for dataRecord attribute
    # \returns name of dataRecord
    def __getDataRecord(self):
        return self.__selector["DataRecord"]

    ## set method for dataRecord attribute
    # \param name of dataRecord
    def __setDataRecord(self, name):
        jname = Utils.stringToDictJson(name)
        if self.__selector["DataRecord"] != jname:
            self.__selector["DataRecord"] = jname
            self.storeConfiguration()

    ## the json data string
    dataRecord = property(
        __getDataRecord,
        __setDataRecord,
        doc='client data record')

    ## get method for dataRecord attribute
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

    # \returns name of adminData
    def __getAdminData(self):
        try:
            lad = json.loads(self.__adminData)
            assert isinstance(lad, list)
            return self.__adminData
        except Exception:
            return '[]'

    ## set method for adminData attribute
    # \param name of adminData
    def __setAdminData(self, name):
        jname = Utils.stringToListJson(name)
        ## administator data
        self.__adminData = jname

    ## the json data string
    adminData = property(
        __getAdminData,
        __setAdminData,
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
            self.storeConfiguration()

    ## the json variables string
    configVariables = property(
        __getConfigVariables,
        __setConfigVariables,
        doc='configuration variables')

    ## get method for dataSourceGroup attribute
    # \returns names of STEP dataSources
    def __getSTEPDataSources(self):
        inst = self.setConfigInstance()
        if inst.stepdatasources:
            return list(inst.stepdatasources)
        else:
            return list()

    ## set method for dataSourceGroup attribute
    # \param names of STEP dataSources
    def __setSTEPDataSources(self, names):
        inst = self.setConfigInstance()
        inst.stepdatasources = [str(nm) for nm in names]

    ## the json data string
    stepdatasources = property(
        __getSTEPDataSources,
        __setSTEPDataSources,
        doc='datasource  group')

    ## get method for labelShapes attribute
    # \returns name of labelShapes
    def __getLabelShapes(self):
        return self.__selector["LabelShapes"]

    ## set method for labelShapes attribute
    # \param name of labelShapes
    def __setLabelShapes(self, name):
        jname = Utils.stringToDictJson(name)
        if self.__selector["LabelShapes"] != jname:
            self.__selector["LabelShapes"] = jname
            self.storeConfiguration()

    ## the json data string
    labelShapes = property(
        __getLabelShapes,
        __setLabelShapes,
        doc='label shapes')

    ## get method for labelTypes attribute
    # \returns name of labelTypes
    def __getLabelTypes(self):
        return self.__selector["LabelTypes"]

    ## set method for labelTypes attribute
    # \param name of labelTypes
    def __setLabelTypes(self, name):
        jname = Utils.stringToDictJson(name)
        if self.__selector["LabelTypes"] != jname:
            self.__selector["LabelTypes"] = jname
            self.storeConfiguration()

    ## the json data string
    labelTypes = property(
        __getLabelTypes,
        __setLabelTypes,
        doc='label types')

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
        self.storeConfiguration()

    ## the json data string
    writerDevice = property(__getWriterDevice, __setWriterDevice,
                            doc='Writer device name')

    ## get method for ScanDir attribute
    # \returns name of ScanDir
    def __getScanDir(self):
        ms = self.getMacroServer()
        return str(MSUtils.getEnv('ScanDir', ms))

    ## set method for ScanDir attribute
    # \param name of ScanDir
    def __setScanDir(self, name):
        ms = self.getMacroServer()
        MSUtils.setEnv('ScanDir', str(name), ms)

    ## the json data string
    scanDir = property(__getScanDir, __setScanDir,
                       doc='scan directory')

    ## get method for ScanID attribute
    # \returns name of ScanID
    def __getScanID(self):
        ms = self.getMacroServer()
        sid = MSUtils.getEnv('ScanID', ms)
        if sid:
            return int(sid)
        else:
            MSUtils.setEnv('ScanID', 0, ms)
            return 0

    ## set method for ScanID attribute
    # \param name of ScanID
    def __setScanID(self, name):
        ms = self.getMacroServer()
        MSUtils.setEnv('ScanID', name, ms)

    ## the json data string
    scanID = property(__getScanID, __setScanID,
                       doc='scan id')

    ## get method for ScanFile attribute
    # \returns name of ScanFile
    def __getScanFile(self):
        ms = self.getMacroServer()
        val = MSUtils.getEnv('ScanFile', ms)
        return [val] if isinstance(val, (str, unicode)) else val

    ## set method for ScanFile attribute
    # \param name of ScanFile
    def __setScanFile(self, name):
        ms = self.getMacroServer()
        if isinstance(name, (list, tuple)) and len(name) == 1:
            name = name[0]
        MSUtils.setEnv('ScanFile', name, ms)

    ## the json data string
    scanFile = property(__getScanFile, __setScanFile,
                       doc='scan file(s)')

##  commands

    def __getPools(self):
        return self.__selector.getPools()

    ## updates MacroServer for the given door server
    # \param door current door server
    def updateMacroServer(self, door):
        return self.__msp.updateMacroServer(door)

    ## provides the current macroserver name
    # \returns macroserver name
    def getMacroServer(self):
        return self.__selector.getMacroServer()

    ## sets config instances
    # \returns set config instance
    def setConfigInstance(self):
        return self.__selector.setConfigInstance()

    ## executes command on configuration server
    # \returns command result
    def __configCommand(self, command, *var):
        return self.__selector.configCommand(command, *var)

    ## mandatory components
    # \returns list of mandatory components
    def mandatoryComponents(self):
        mc = self.__configCommand("mandatoryComponents")
        mc = mc if mc else []
        return mc

    ## available components
    # \returns list of available components
    def availableComponents(self):
        ac = self.__configCommand("availableComponents")
        ac = ac if ac else []
        return ac

    ## available selections
    # \returns list of available selections
    def availableSelections(self):
        ac = self.__configCommand("availableSelections")
        ac = ac if ac else []
        return ac

    ## available components
    # \returns list of component Variables
    def componentVariables(self, name):
        av = self.__configCommand("componentVariables", name)
        av = av if av else []
        return av

    ## available datasources
    # \returns list of available datasources
    def availableDataSources(self):
        ad = self.__configCommand("availableDataSources")
        ad = ad if ad else []
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
    def saveConfiguration(self):
        fl = open(self.configFile, "w+")
        json.dump(self.__selector.get(), fl)

    ## saves configuration
    def storeConfiguration(self):
        inst = self.setConfigInstance()
        conf = str(json.dumps(self.__selector.get()))
        inst.selection = conf
        inst.storeSelection(self.mntGrp)

    ## fetch configuration
    def fetchConfiguration(self):
        inst = self.setConfigInstance()
        avsl = inst.availableSelections()
        confs = None
        if self.mntGrp in avsl:
            confs = inst.selections([self.mntGrp])
        if confs:
            self.__selector.set(json.loads(str(confs[0])))
        else:
            avmg = self.availableMeasurementGroups()
            if self.mntGrp in avmg:
                self.__selector.deselect()
                self.__selector.resetAutomaticComponents(
                    self.defaultAutomaticComponents)
                self.updateControllers()

    ## loads configuration
    def loadConfiguration(self):
        fl = open(self.configFile, "r")
        self.__selector.set(json.load(fl))

    ## provides components for all variables
    # \returns dictionary with components for all variables
    def __variableComponents(self):
        acp = self.availableComponents()
        vrs = {}
        for c in acp:
            vr = self.componentVariables(c)
            if vr:
                for v in vr:
                    if v not in vrs:
                        vrs[v] = []
                    vrs[v].append(c)

        jdc = json.dumps(vrs)
        return jdc

    ##  provides components for all variables
    variableComponents = property(
        __variableComponents,
        doc='provides components for all variables')

    ## provides description of all components
    # \returns JSON string with description of all components
    def __description(self):
        dc = self.cpdescription(full=True)
        jdc = json.dumps(dc)
        return jdc

    ##  provides description of all components
    description = property(__description,
                            doc='provides description of all components')

    ## provides description of client datasources
    # \param cps component names
    # \returns JSON string with description of client datasources
    def clientSources(self, cps):
        nexusconfig_device = self.setConfigInstance()
        describer = Describer(nexusconfig_device)
        if cps:
            cp = cps
        else:
            cp = None
            cp = list(set(self.components) |
                      set(self.automaticComponents) |
                      set(self.mandatoryComponents()))
        dc = describer.components(cp, '', 'CLIENT', self.configVariables)
        jdc = json.dumps(dc)
        return jdc

    ## create configuration
    # \param cps component names
    # \returns JSON string with description of client datasources
    def createConfiguration(self, cps):
        nexusconfig_device = self.setConfigInstance()
        if cps:
            cp = cps
        else:
            cp = None
            cp = list(set(self.components) |
                      set(self.automaticComponents) |
                      set(self.mandatoryComponents()))
        TangoUtils.command(nexusconfig_device,
                           "createConfiguration",
                           cp)
        return str(nexusconfig_device.xmlstring)

    ## provides full names of pool devices
    # \returns JSON string with full names of pool devices
    def __fullDeviceNames(self):
        pools = self.__getPools()
        return json.dumps(PoolUtils.getFullDeviceNames(pools))

    ## provides full names of pool devices
    fullDeviceNames = property(
        __fullDeviceNames,
        doc=' provides full names of pool devices')

    ##  sends ConfigVariables into ConfigServer
    #        and updates serialno if appendEntry selected
    def updateConfigVariables(self):

        confvars = self.configVariables
        nexusconfig_device = self.setConfigInstance()
        jvars = json.loads(confvars)
        cvars = json.loads(nexusconfig_device.variables)
        ## appending scans to one file?
        if self.appendEntry and not 'serialno' in jvars.keys():
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
    #      AutomaticDataSources
    def updateControllers(self):
        jacps = self.__selector.updateAutomaticComponents(self.__descErrors)
        if self.__selector["AutomaticComponentGroup"] != jacps:
            self.__selector["AutomaticComponentGroup"] = jacps
            self.storeConfiguration()
        gc.collect()

    ## reset automaticComponentGroup to defaultAutomaticComponents
    def resetAutomaticComponents(self):
        self.__selector.resetAutomaticComponents(
            self.defaultAutomaticComponents)
        self.updateControllers()
        self.storeConfiguration()

    ## clear all selections
    def clearAllSelections(self):
        avsel = self.availableSelections()
        if avsel:
            inst = self.setConfigInstance()
            for name in avsel:
                inst.deleteSelection(name)

    ## provides available Timers from MacroServer pools
    # \returns  available Timers from MacroServer pools
    def __availableTimers(self):
        pools = self.__getPools()
        return PoolUtils.getTimers(pools, self.timerFilterList)

    ##  provides description of all components
    availableTimers = property(
        __availableTimers,
        doc='provides available Timers from MacroServer pools')

# MntGrp methods

    ## provides full name of Measurement group
    # \param name alias
    # \returns full name of Measurement group
    def findMntGrp(self, name):
        pools = self.__getPools()
        return PoolUtils.getMntGrpName(pools, name)

    ## deletes mntgrp
    # \param name mntgrp name
    def deleteMntGrp(self, name):
        self.__mntgrptools.macroServer = self.getMacroServer()
        self.__mntgrptools.deleteMntGrp(name)
        inst = self.setConfigInstance()
        inst.deleteSelection(name)

    ## describe datasources
    # \param datasources list for datasource names
    # \returns list of dictionary with description of datasources
    def getSourceDescription(self, datasources):
        self.__mntgrptools.configServer = self.setConfigInstance()
        return self.__mntgrptools.getSourceDescription(datasources)

    ## provides description of components
    # \param full if True describes all available ones are taken
    #        otherwise selectect, automatic and mandatory
    # \returns description of required components
    def cpdescription(self, full=False):
        nexusconfig_device = self.setConfigInstance()
        describer = Describer(nexusconfig_device)
        cp = None
        if not full:
            cp = list(
                set(self.components) | set(self.automaticComponents) |
                set(self.mandatoryComponents()))
            res = describer.components(cp, 'STEP', '')
        else:
            res = describer.components(cp, '', '')
        return res

    ## provides configuration of mntgrp
     # \returns string with mntgrp configuration
    def mntGrpConfiguration(self):
        pools = self.__getPools()
        self.__mntgrptools.macroServer = self.getMacroServer()
        if not self.__selector["MntGrp"]:
            self.switchMntGrp(toActive=False)
        dpmg = self.__mntgrptools.getMntGrpProxy(pools)
        if not dpmg:
            return "{}"
        return str(dpmg.Configuration)

    ## check if active measurement group was changed
    # \returns True if it is different to the current setting
    def isMntGrpChanged(self):
        pools = self.__getPools()
        mgconf = json.loads(self.mntGrpConfiguration())
        self.__mntgrptools.macroServer = self.getMacroServer()
        self.__mntgrptools.configServer = self.setConfigInstance()
        self.__mntgrptools.dataSources = self.dataSources
        self.__mntgrptools.disableDataSources = self.disableDataSources
        self.__mntgrptools.components = list(
            set(self.components) | set(self.automaticComponents) |
            set(self.mandatoryComponents()))
        llconf, _ = self.__mntgrptools.createMntGrpConfiguration(pools)
        self.storeConfiguration()
        lsconf = json.loads(llconf)
        return not Utils.compareDict(mgconf, lsconf)

    ## set active measurement group from components
    # \returns string with mntgrp configuration
    def updateMntGrp(self):
        pools = self.__getPools()
        self.__mntgrptools.macroServer = self.getMacroServer()
        self.__mntgrptools.configServer = self.setConfigInstance()
        self.__mntgrptools.dataSources = self.dataSources
        self.__mntgrptools.disableDataSources = self.disableDataSources
        self.__mntgrptools.components = list(
            set(self.components) | set(self.automaticComponents) |
            set(self.mandatoryComponents()))
        conf, mntgrp = self.__mntgrptools.createMntGrpConfiguration(pools)
        self.storeConfiguration()
        dpmg = TangoUtils.openProxy(mntgrp)
        dpmg.Configuration = conf
        return str(dpmg.Configuration)

    ## switch to active measurement
    def switchMntGrp(self, toActive=True):
        pools = self.__getPools()
        if not self.__selector["MntGrp"] or toActive:
            ms = self.getMacroServer()
            amntgrp = MSUtils.getEnv('ActiveMntGrp', ms)
            if not toActive or amntgrp:
                self.__selector["MntGrp"] = amntgrp
        self.fetchConfiguration()
        jconf = self.mntGrpConfiguration()
        self.__mntgrptools.configServer = self.setConfigInstance()
        if self.__mntgrptools.importMntGrp(jconf, pools):
            self.storeConfiguration()

    ## import setting from active measurement
    def importMntGrp(self):
        pools = self.__getPools()
        self.__mntgrptools.macroServer = self.getMacroServer()
        self.__mntgrptools.configServer = self.setConfigInstance()
        jconf = self.mntGrpConfiguration()
        if self.__mntgrptools.importMntGrp(jconf, pools):
            self.storeConfiguration()

    ## available mntgrps
    # \returns list of available measurement groups
    def availableMeasurementGroups(self):
        self.__mntgrptools.macroServer = self.getMacroServer()
        return self.__mntgrptools.availableMeasurementGroups()

# Dynamic component methods

    ## creates dynamic component
    # \param params datasource parameters
    # \returns dynamic component name
    def createDynamicComponent(self, params):
        nexusconfig_device = self.setConfigInstance()
        dcpcreator = DynamicComponent(nexusconfig_device)
        if isinstance(params, (list, tuple)):
            if len(params) > 0 and params[0]:
                dcpcreator.setStepDSources(
                    json.loads(params[0]))
            else:
                dcpcreator.setStepDSources(self.dataSources)
            if len(params) > 1 and params[1]:
                dcpcreator.setStepDictDSources(json.loads(params[1]))
            if len(params) > 2 and params[2]:
                dcpcreator.setInitDSources(json.loads(params[2]))
            else:
                dcpcreator.setInitDSources(json.loads(
                        self.__selector["InitDataSources"]))

        withoutLinks = list(set(self.components) |
                            set(self.automaticComponents) |
                            set(self.mandatoryComponents()))

        links = json.loads(self.__selector["LabelLinks"])
        for ds in withoutLinks:
            links[ds] = False

        dcpcreator.setLabelParams(
            self.__selector["Labels"],
            self.__selector["LabelPaths"],
            json.dumps(links),
            self.__selector["LabelTypes"],
            self.__selector["LabelShapes"])
        dcpcreator.setDefaultLinkPath(
            bool(self.__selector["DynamicLinks"]),
            str(self.__selector["DynamicPath"]))

        return dcpcreator.create()

    ## removes dynamic component
    # \param name dynamic component name
    def removeDynamicComponent(self, name):
        nexusconfig_device = self.setConfigInstance()
        dcpcreator = DynamicComponent(nexusconfig_device)
        dcpcreator.remove(name)

# Environment methods:

    ## fetches Enviroutment Data
    # \returns JSON String with important variables
    def fetchEnvData(self):
        return self.__selector.fetchEnvData()

    ## stores Enviroutment Data
    # \param jdata JSON String with important variables
    def storeEnvData(self, jdata):
        return self.__selector.storeEnvData(jdata)

    ## imports all Enviroutment Data
    def importAllEnv(self):
        self.__selector.importEnv()

    ## exports all Enviroutment Data
    def exportAllEnv(self):
        nenv = {}
        commands = {
            "components": "Components",
            "automaticComponents": "AutomaticComponents",
            "dataSources": "DataSources"
            }
        for attr, name in commands.items():
            vl = getattr(self, attr)
            nenv[str(name)] = vl
        self.__selector.exportEnv(cmddata=nenv)
