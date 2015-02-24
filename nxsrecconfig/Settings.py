#!/usr/bin/env python
#   This file is part of nxsrecconfig - NeXus Sardana Recorder Settings
#
#    Copyright (C) 2014 DESY, Jan Kotanski <jkotan@mail.desy.de>
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
import PyTango
from .Describer import Describer
from .DynamicComponent import DynamicComponent
from .Utils import Utils
from .MntGrpTools import MntGrpTools
from .Selection import Selection
import pickle
import getpass


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
        self.__selection = Selection(self, self.numberOfThreads)

        ## default zone
        self.__defaultzone = 'Europe/Berlin'

        self.__pureVar = [
            "AppendEntry",
            "ComponentsFromMntGrp",
            "DynamicComponents",
            "DynamicLinks",
            "DynamicPath",
            "TimeZone",
            "ConfigDevice",
            "WriterDevice",
            "Door",
            "MntGrp",
            "ScanDir"
            ]

        self.__mntgrptools = MntGrpTools(self.__selection, self)

        ## configuration file
        self.configFile = '/tmp/nxsrecconfig.cfg'

        ## tango database
        self.__db = PyTango.Database()
        self.__selection.db = self

        ## config server proxy
        self.__configProxy = None
        ## config server module
        self.__configModule = None
        ## config writer proxy
        self.__writerProxy = None
        ## module label
        self.__moduleLabel = 'module'
        self.__selection.moduleLabel = self.__moduleLabel

        ## macro server instance
        self.__macroserver = ""
        ## pool instances
        self.__pools = []
        ## black list of pools
        self.poolBlacklist = []
        ## timer filter list
        self.timerFilterList = ["*dgg*", "*ctctrl*"]

        self.__nxsenv = "NeXusConfiguration"

    ## provides values of the required variable
    # \param name name of the required variable
    # \returns  values of the required variable
    def value(self, name):
        vl = ''
        if name in self.__selection.keys():
            vl = self.__selection[name]
            if isinstance(vl, unicode):
                vl = str(vl)
        return vl

    ## provides names of variables
    def names(self):
        return self.__selection.keys()

## read-only variables

    ## provides selected components
    # \returns list of available selected components
    def __components(self):
        cps = json.loads(self.__selection["ComponentGroup"])
        ads = json.loads(self.__selection["DataSourceGroup"])
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
        cps = json.loads(self.__selection["AutomaticComponentGroup"])
        if isinstance(cps, dict):
            return [cp for cp in cps.keys() if cps[cp]]
        else:
            return []

    ## provides automatic components
    automaticComponents = property(__automaticComponents,
                            doc=' provides automatic components')

    ## provides selected datasources
    # \returns list of available selected datasources
    def __dataSources(self):
        dds = self.disableDataSources
        if not isinstance(dds, list):
            dds = []
        dss = json.loads(self.__selection["DataSourceGroup"])
        if isinstance(dss, dict):
            return [ds for ds in dss.keys() if dss[ds] and ds not in dds]
        else:
            return []

    ##  provides selected data sources
    dataSources = property(
        __dataSources,
        doc=' provides selected data sources')

## read-write variables

    ## get method for configDevice attribute
    # \returns name of configDevice
    def __getConfigDevice(self):
        return self.__selection["ConfigDevice"]

    ## set method for configDevice attribute
    # \param name of configDevice
    def __setConfigDevice(self, name):
        if name != self.__selection["ConfigDevice"]:
            self.__selection["ConfigDevice"] = name
            self.switchMntGrp()

    ## the json data string
    configDevice = property(__getConfigDevice, __setConfigDevice,
                            doc='configuration server device name')

    ## set method for configuration attribute
    # \param name of configuration
    def __setConfiguration(self, jconf):
        self.__selection.set(json.loads(jconf))
        self.storeConfiguration()

    ## get method for configuration attribute
    # \returns configuration
    def __getConfiguration(self):
        return json.dumps(self.__selection.get())

    ## the json data string
    configuration = property(
        __getConfiguration,
        __setConfiguration,
        doc='automatic components group')

    ## set method for appendEntry attribute
    # \param name of appendEntry
    def __setAppendEntry(self, ae):
        self.__selection["AppendEntry"] = bool(ae)
        self.storeConfiguration()

    ## get method for appendEntry attribute
    # \returns flag of appendEntry
    def __getAppendEntry(self):
        return bool(self.__selection["AppendEntry"])

    ## the json data string
    appendEntry = property(
        __getAppendEntry,
        __setAppendEntry,
        doc='flag for append entry')

    ## get method for dataRecord attribute
    # \returns name of dataRecord
    def __getDataRecord(self):
        return self.__selection["DataRecord"]

    ## set method for dataRecord attribute
    # \param name of dataRecord
    def __setDataRecord(self, name):
        jname = Utils.stringToDictJson(name)
        if self.__selection["DataRecord"] != jname:
            self.__selection["DataRecord"] = jname
            self.storeConfiguration()

    ## the json data string
    dataRecord = property(
        __getDataRecord,
        __setDataRecord,
        doc='client data record')

    ## get method for configVariables attribute
    # \returns name of configVariables
    def __getConfigVariables(self):
        return self.__selection["ConfigVariables"]

    ## set method for configVariables attribute
    # \param name of configVariables
    def __setConfigVariables(self, name):
        jname = Utils.stringToDictJson(name)
        if self.__selection["ConfigVariables"] != jname:
            self.__selection["ConfigVariables"] = jname
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
        return self.__selection["LabelShapes"]

    ## set method for labelShapes attribute
    # \param name of labelShapes
    def __setLabelShapes(self, name):
        jname = Utils.stringToDictJson(name)
        if self.__selection["LabelShapes"] != jname:
            self.__selection["LabelShapes"] = jname
            self.storeConfiguration()

    ## the json data string
    labelShapes = property(
        __getLabelShapes,
        __setLabelShapes,
        doc='label shapes')

    ## get method for labelTypes attribute
    # \returns name of labelTypes
    def __getLabelTypes(self):
        return self.__selection["LabelTypes"]

    ## set method for labelTypes attribute
    # \param name of labelTypes
    def __setLabelTypes(self, name):
        jname = Utils.stringToDictJson(name)
        if self.__selection["LabelTypes"] != jname:
            self.__selection["LabelTypes"] = jname
            self.storeConfiguration()

    ## the json data string
    labelTypes = property(
        __getLabelTypes,
        __setLabelTypes,
        doc='label types')

    ## get method for mntGrp attribute
    # \returns name of mntGrp
    def __getMntGrp(self):
        return self.__selection["MntGrp"]

    ## set method for mntGrp attribute
    # \param name of mntGrp
    def __setMntGrp(self, name):
        self.__selection["MntGrp"] = name

    ## the json data string
    mntGrp = property(__getMntGrp, __setMntGrp,
                           doc='measurement group')

    ## get method for door attribute
    # \returns name of door
    def __getDoor(self):
        return self.__selection["Door"]

    ## set method for door attribute
    # \param name of door
    def __setDoor(self, name):
        self.__selection["Door"] = name
        self.updateMacroServer(self.__selection["Door"])
        if self.__selection["ConfigDevice"]:
            self.storeConfiguration()

    ## the json data string
    door = property(__getDoor, __setDoor,
                           doc='door server device name')

    ## get method for writerDevice attribute
    # \returns name of writerDevice
    def __getWriterDevice(self):
        return self.__selection["WriterDevice"]

    ## set method for writerDevice attribute
    # \param name of writerDevice
    def __setWriterDevice(self, name):
        self.__selection["WriterDevice"] = name
        self.storeConfiguration()

    ## the json data string
    writerDevice = property(__getWriterDevice, __setWriterDevice,
                            doc='Writer device name')

    ## get method for ScanDir attribute
    # \returns name of ScanDir
    def __getScanDir(self):
        ms = self.getMacroServer()
        return str(Utils.getEnv('ScanDir', ms))

    ## set method for ScanDir attribute
    # \param name of ScanDir
    def __setScanDir(self, name):
        ms = self.getMacroServer()
        Utils.setEnv('ScanDir', name, ms)

    ## the json data string
    scanDir = property(__getScanDir, __setScanDir,
                       doc='scan directory')

    ## get method for ScanID attribute
    # \returns name of ScanID
    def __getScanID(self):
        ms = self.getMacroServer()
        sid = Utils.getEnv('ScanID', ms)
        if sid:
            return int(sid)
        else:
            Utils.setEnv('ScanID', 0, ms)
            return 0

    ## set method for ScanID attribute
    # \param name of ScanID
    def __setScanID(self, name):
        ms = self.getMacroServer()
        Utils.setEnv('ScanID', name, ms)

    ## the json data string
    scanID = property(__getScanID, __setScanID,
                       doc='scan id')

    ## get method for ScanFile attribute
    # \returns name of ScanFile
    def __getScanFile(self):
        ms = self.getMacroServer()
        return Utils.getEnv('ScanFile', ms)

    ## set method for ScanFile attribute
    # \param name of ScanFile
    def __setScanFile(self, name):
        ms = self.getMacroServer()
        Utils.setEnv('ScanFile', name, ms)

    ## the json data string
    scanFile = property(__getScanFile, __setScanFile,
                       doc='scan file(s)')

##  commands

    def __getPools(self):
        if not self.__pools:
            door = self.__getDoor()
            self.updateMacroServer(door)
        return self.__pools

    def updateMacroServer(self, door):
        if not door:
            raise Exception("Door '%s' cannot be found" % door)
        self.__macroserver = Utils.getMacroServer(self.__db, door)
        msp = Utils.openProxy(self.__macroserver)
        pnames = msp.get_property("PoolNames")["PoolNames"]
        if not pnames:
            pnames = []
        poolNames = list(
            set(pnames) - set(self.poolBlacklist))
        self.__pools = Utils.getProxies(poolNames)

    def getMacroServer(self):
        if not self.__macroserver:
            door = self.__getDoor()
            self.updateMacroServer(door)
        return self.__macroserver

    ## sets config instances
    # \returns set config instance
    def setConfigInstance(self):
        if "ConfigDevice" not in self.__selection.keys() \
                or not self.__selection["ConfigDevice"]:
            self.__getConfigDevice()

        if self.__selection["ConfigDevice"] and \
                self.__selection["ConfigDevice"].lower() != self.__moduleLabel:
            self.__configProxy = Utils.openProxy(
                self.__selection["ConfigDevice"])
            self.__configProxy.open()
            self.__configModule = None
        else:
            from nxsconfigserver import XMLConfigurator
            self.__configModule = XMLConfigurator.XMLConfigurator()
            self.getMacroServer()

            data = {}
            self.__importEnv(['DBParams'], data)
            if 'DBParams' in data.keys():
                dbp = data['DBParams']
            else:
                dbp = '{}'

            try:
                self.__configModule.jsonsettings = dbp
                self.__configModule.open()
                self.__configModule.availableComponents()
            except:
                user = getpass.getuser()
                dbp = '{"host":"localhost","db":"nxsconfig",' \
                    + '"use_unicode":true,' \
                    + '"read_default_file":"/home/%s/.my.cnf"}' % user
                self.__configModule.jsonsettings = dbp
                self.__configModule.open()
                self.__configModule.availableComponents()
            self.__configProxy = None
        return self.__configProxy \
            if self.__configProxy else self.__configModule

    ## executes command on configuration server
    # \returns command result
    def __configCommand(self, command, var=None):
        inst = self.setConfigInstance()
        if var is None:
            res = getattr(inst, command)()
        else:
            if self.__configProxy:
                res = inst.command_inout(command, var)
            else:
                res = getattr(inst, command)(var)
        return res

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
        res = []
        ms = self.getMacroServer()
        msp = Utils.openProxy(ms)
        pn = msp.get_property("PoolNames")["PoolNames"]
        if pn:
            for pl in pn:
                pool = Utils.openProxy(pl)
                exps = pool.ExpChannelList
                if exps:
                    for jexp in exps:
                        if jexp:
                            exp = json.loads(jexp)
                            if exp and isinstance(exp, dict):
                                res.append(exp['name'])
        return res

    ## available pool motors
    # \returns pool motors of the macroserver pools
    def poolMotors(self):
        res = []
        ms = self.getMacroServer()
        msp = Utils.openProxy(ms)
        pn = msp.get_property("PoolNames")["PoolNames"]
        if pn:
            for pl in pn:
                pool = Utils.openProxy(pl)
                exps = pool.MotorList
                if exps:
                    for jexp in exps:
                        if jexp:
                            exp = json.loads(jexp)
                            if exp and isinstance(exp, dict):
                                res.append(exp['name'])
        return res

    ## saves configuration
    def saveConfiguration(self):
        fl = open(self.configFile, "w+")
        json.dump(self.__selection, fl)

    ## saves configuration
    def storeConfiguration(self):
        inst = self.setConfigInstance()
        conf = str(json.dumps(self.__selection.get()))
        inst.selection = conf
        inst.storeSelection(self.mntGrp)

    ## fetch configuration
    def fetchConfiguration(self):
        inst = self.setConfigInstance()
        avsl = inst.availableSelections()
        if self.mntGrp in avsl:
            confs = inst.selections([self.mntGrp])
            if confs:
                self.__selection.set(json.loads(str(confs[0])))

    ## loads configuration
    def loadConfiguration(self):
        fl = open(self.configFile, "r")
        self.__selection.set(json.load(fl))

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

    ## provides description of components
    # \param dstype list datasets only with given datasource type.
    #        If '' all available ones are taken
    # \param full if True describes all available ones are taken
    #        otherwise selectect, automatic and mandatory
    # \returns description of required components
    def cpdescription(self, dstype='', full=False):

        nexusconfig_device = self.setConfigInstance()
        describer = Describer(nexusconfig_device)
        cp = None
        if not full:
            cp = list(set(self.components) |
            set(self.automaticComponents) |
            set(self.mandatoryComponents()))
            res = describer.components(cp, 'STEP', dstype)
        else:
            res = describer.components(cp, '', dstype)
        return res

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
    # \params cps component names
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
        dc = describer.final(cp, '', 'CLIENT', self.configVariables)
        jdc = json.dumps(dc)
        return jdc

    ## create configuration
    # \params cps component names
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
        nexusconfig_device.createConfiguration(cp)
        return str(nexusconfig_device.xmlstring)

    ## provides full names of pool devices
    # \returns JSON string with full names of pool devices
    def __fullDeviceNames(self):
        pools = self.__getPools()
        return json.dumps(Utils.getFullDeviceNames(pools))

    ## provides full names of pool devices
    fullDeviceNames = property(
        __fullDeviceNames,
        doc=' provides full names of pool devices')

    ## describe datasources
    # \param datasources list for datasource names
    # \returns list of dictionary with description of datasources
    def getSourceDescription(self, datasources):
        nexusconfig_device = self.setConfigInstance()
        describer = Describer(nexusconfig_device)
        dsres = describer.dataSources(set(datasources))
        dslist = []
        if isinstance(dsres, dict):
            for ds in dsres.values():
                elem = {}
                elem["dsname"] = ds[0]
                elem["dstype"] = ds[1]
                elem["record"] = ds[2]
                dslist.append(str(json.dumps(elem)))
        return dslist

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
                except Exception:
                    pass
            else:
                cvars["serialno"] = str(1)
            jvars["serialno"] = cvars["serialno"]
            confvars = json.dumps(jvars)
        nexusconfig_device.variables = confvars

    ## checks existing controllers of pools for
    #      AutomaticDataSources
    def updateControllers(self):
        pools = self.__getPools()
        self.__selection.updateControllers(pools)

    ## provides available Timers from MacroServer pools
    # \returns  available Timers from MacroServer pools
    def __availableTimers(self):
        pools = self.__getPools()
        return Utils.getTimers(pools, self.timerFilterList)

    ##  provides description of all components
    availableTimers = property(
        __availableTimers,
        doc='provides available Timers from MacroServer pools')

    ## provides a list of Disable DataSources
    # \returns list of disable datasources
    def __disableDataSources(self):
        res = self.cpdescription()
        dds = set()

        for dss in res[1].values():
            if isinstance(dss, dict):
                for ds in dss.keys():
                    dds.add(ds)
        return list(dds)

    ##  provides a list of Disable DataSources
    disableDataSources = property(
        __disableDataSources,
        doc='provides a list of Disable DataSources')

# MntGrp methods

    ## provides full name of Measurement group
    # \param name alias
    # \returns full name of Measurement group
    def findMntGrp(self, name):
        pools = self.__getPools()
        return Utils.getMntGrpName(pools, name)

    ## deletes mntgrp
    # \param name mntgrp name
    def deleteMntGrp(self, name):
        self.__mntgrptools.deleteMntGrp(name)
        inst = self.setConfigInstance()
        inst.deleteSelection(name)

    ## provides configuration of mntgrp
    # \param proxy DeviceProxy of mntgrp
    # \returns string with mntgrp configuration
    def mntGrpConfiguration(self, proxy=None):
        pools = self.__getPools()
        return self.__mntgrptools.mntGrpConfiguration(pools, proxy)

    ## check if active measurement group was changed
    # \returns True if it is different to the current setting
    def isMntGrpChanged(self):
        pools = self.__getPools()
        mgconf = json.loads(self.__mntgrptools.mntGrpConfiguration(pools))
        llconf, _ = self.__mntgrptools.createMntGrpConfiguration(pools)
        lsconf = json.loads(llconf)
        return not Utils.compareDict(mgconf, lsconf)

    ## set active measurement group from components
    # \returns string with mntgrp configuration
    def updateMntGrp(self):
        pools = self.__getPools()
        conf, mntgrp = self.__mntgrptools.createMntGrpConfiguration(pools)
        dpmg = Utils.openProxy(mntgrp)
        dpmg.Configuration = conf
        return str(dpmg.Configuration)

    ## switch to active measurement
    def switchMntGrp(self):
        pools = self.__getPools()
        return self.__mntgrptools.switchMntGrp(pools)

    ## import setting from active measurement
    def importMntGrp(self):
        pools = self.__getPools()
        return self.__mntgrptools.importMntGrp(pools)

    ## available mntgrps
    # \returns list of available measurement groups
    def availableMeasurementGroups(self):
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
                dcpcreator.setDataSources(
                    json.loads(params[0]))
            else:
                dcpcreator.setDataSources(self.dataSources)
            if len(params) > 1 and params[1]:
                dcpcreator.setDictDSources(params[1])
            if len(params) > 2 and params[2]:
                dcpcreator.setInitDSources(json.loads(params[2]))
        dcpcreator.setLabelParams(
            self.__selection["Labels"],
            self.__selection["LabelPaths"],
            self.__selection["LabelLinks"],
            self.__selection["LabelTypes"],
            self.__selection["LabelShapes"])
        dcpcreator.setLinkParams(
            bool(self.__selection["DynamicLinks"]),
            str(self.__selection["DynamicPath"]))

        dcpcreator.setComponents(
            list(set(self.components) |
                 set(self.automaticComponents) |
                 set(self.mandatoryComponents())))

        return dcpcreator.create()

    ## removes dynamic component
    # \param name dynamic component name
    def removeDynamicComponent(self, name):
        nexusconfig_device = self.setConfigInstance()
        dcpcreator = DynamicComponent(nexusconfig_device)
        dcpcreator.removeDynamicComponent(name)

# Environment methods:

    ## fetches Enviroutment Data
    # \returns JSON String with important variables
    def fetchEnvData(self):
        params = ["ScanDir",
                  "ScanFile",
                  "ScanID",
#                  "ActiveMntGrp",
                  "NeXusSelectorDevice"]
        res = {}
        dp = Utils.openProxy(self.getMacroServer())
        rec = dp.Environment
        if rec[0] == 'pickle':
            dc = pickle.loads(rec[1])
            if 'new' in dc.keys():
                for var in params:
                    if var in dc['new'].keys():
                        res[var] = dc['new'][var]
        return json.dumps(res)

    ## stores Enviroutment Data
    # \param jdata JSON String with important variables
    def storeEnvData(self, jdata):
        jdata = Utils.stringToDictJson(jdata)
        data = json.loads(jdata)
        scanID = -1
        ms = self.getMacroServer()
        msp = Utils.openProxy(ms)

        rec = msp.Environment
        if rec[0] == 'pickle':
            dc = pickle.loads(rec[1])
            if 'new' in dc.keys():
                for var in data.keys():
                    dc['new'][str(var)] = data[var]
                pk = pickle.dumps(dc)
                if 'ScanID' in dc['new'].keys():
                    scanID = int(dc['new']["ScanID"])
                msp.Environment = ['pickle', pk]
        return scanID

    ## imports all Enviroutment Data
    def importAllEnv(self):
        self.__importEnv(self.__selection.keys(), self.__selection)

    ## imports Enviroutment Data
    # \param names names of required variables
    # \param data dictionary with resulting data
    def __importEnv(self, names, data):
        params = ["ScanDir",
                  "ScanFile"]

        dp = Utils.openProxy(self.getMacroServer())
        rec = dp.Environment
        nenv = {}
        if rec[0] == 'pickle':
            dc = pickle.loads(rec[1])
            if 'new' in dc.keys():
                if self.__nxsenv in dc['new'].keys():
                    nenv = dc['new'][self.__nxsenv]
                for var in names:
                    name = var if var in params else ("NeXus%s" % var)
                    if name in dc['new'].keys():
                        vl = dc['new'][name]
                        if type(vl) not in [str, bool, int]:
                            vl = json.dumps(vl)
                        data[var] = vl
                    elif var in nenv.keys():
                        vl = nenv[var]
                        if type(vl) not in [str, bool, int]:
                            vl = json.dumps(vl)
                        data[var] = vl

    ## exports all Enviroutment Data
    def exportAllEnv(self):
        self.__exportEnv(self.__selection)

    ## exports all Enviroutment Data
    def __exportEnv(self, data):
        params = ["ScanDir",
                  "ScanFile"]

        commands = {
            "components": "Components",
            "automaticComponents": "AutomaticComponents",
            "dataSources": "DataSources"
            }

        ms = self.getMacroServer()
        msp = Utils.openProxy(ms)

        rec = msp.Environment
        if rec[0] == 'pickle':
            dc = pickle.loads(rec[1])
            if 'new' in dc.keys():
                if self.__nxsenv not in dc['new'].keys() \
                        or not isinstance(dc['new'][self.__nxsenv], dict):
                    dc['new'][self.__nxsenv] = {}
                nenv = dc['new'][self.__nxsenv]
                for var in data.keys():
                    if var in self.__pureVar:
                        vl = data[var]
                    else:
                        try:
                            vl = json.loads(data[var])
                        except ValueError:
                            vl = data[var]
                    if var in params:
                        dc['new'][str(var)] = vl
                    else:
                        nenv[("%s" % var)] = vl

                for attr, name in commands.items():
                    vl = getattr(self, attr)
                    nenv[str(name)] = vl
                pk = pickle.dumps(dc)
                msp.Environment = ['pickle', pk]
