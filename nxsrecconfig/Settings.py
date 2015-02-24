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
from .Utils import checker
from .Selection import Selection
import pickle
import Queue
import getpass
import threading

try:
    from nxstools.nxsxml import (XMLFile, NDSource)
    NXSTOOLS = True
except:
    NXSTOOLS = False


## NeXus Sardana Recorder settings
class Settings(object):

    ## ccontructor
    # \param server NXSRecSelector server
    def __init__(self, server=None):
        ## Tango server
        self.__server = server
        ## configuration selection
        self.__selection = Selection(self)

        ## number of threads
        self.numberOfThreads = 8
        ## default zone
        self.__defaultzone = 'Europe/Berlin'
        ## default mntgrp
        self.__defaultmntgrp = 'nxsmntgrp'

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

        ## Record names set by sardana
        self.recorder_names = ['serialno', 'end_time', 'start_time',
                               'point_nb', 'timestamps', 'scan_title']

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
        inst = self.__setConfigInstance()
        if inst.stepdatasources:
            return list(inst.stepdatasources)
        else:
            return list()

    ## set method for dataSourceGroup attribute
    # \param names of STEP dataSources
    def __setSTEPDataSources(self, names):
        inst = self.__setConfigInstance()
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

    ## get method for timeZone attribute
    # \returns name of timeZone
    def __getTimeZone(self):
        return self.__selection["TimeZone"]

    ## set method for timeZone attribute
    # \param name of timeZone
    def __setTimeZone(self, name):
        self.__selection["TimeZone"] = name
        self.storeConfiguration()

    ## th time zone
    timeZone = property(__getTimeZone, __setTimeZone,
                           doc='time zone')

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

    def __getMacroServer(self):
        if not self.__macroserver:
            door = self.__getDoor()
            self.updateMacroServer(door)
        return self.__macroserver

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
        ms = self.__getMacroServer()
        return str(Utils.getEnv('ScanDir', ms))

    ## set method for ScanDir attribute
    # \param name of ScanDir
    def __setScanDir(self, name):
        ms = self.__getMacroServer()
        Utils.setEnv('ScanDir', name, ms)

    ## the json data string
    scanDir = property(__getScanDir, __setScanDir,
                       doc='scan directory')

    ## get method for ScanID attribute
    # \returns name of ScanID
    def __getScanID(self):
        ms = self.__getMacroServer()
        sid = Utils.getEnv('ScanID', ms)
        if sid:
            return int(sid)
        else:
            Utils.setEnv('ScanID', 0, ms)
            return 0

    ## set method for ScanID attribute
    # \param name of ScanID
    def __setScanID(self, name):
        ms = self.__getMacroServer()
        Utils.setEnv('ScanID', name, ms)

    ## the json data string
    scanID = property(__getScanID, __setScanID,
                       doc='scan id')

    ## get method for ScanFile attribute
    # \returns name of ScanFile
    def __getScanFile(self):
        ms = self.__getMacroServer()
        return Utils.getEnv('ScanFile', ms)

    ## set method for ScanFile attribute
    # \param name of ScanFile
    def __setScanFile(self, name):
        ms = self.__getMacroServer()
        Utils.setEnv('ScanFile', name, ms)

    ## the json data string
    scanFile = property(__getScanFile, __setScanFile,
                       doc='scan file(s)')

    ## sets config instances
    # \returns set config instance
    def __setConfigInstance(self):
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
            self.__getMacroServer()

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
        inst = self.__setConfigInstance()
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
        ms = self.__getMacroServer()
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
        ms = self.__getMacroServer()
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
        inst = self.__setConfigInstance()
        conf = str(json.dumps(self.__selection.get()))
        inst.selection = conf
        inst.storeSelection(self.mntGrp)

    ## fetch configuration
    def fetchConfiguration(self):
        inst = self.__setConfigInstance()
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
    def __cpdescription(self, dstype='', full=False):

        nexusconfig_device = self.__setConfigInstance()
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
        dc = self.__cpdescription(full=True)
        jdc = json.dumps(dc)
        return jdc

    ##  provides description of all components
    description = property(__description,
                            doc='provides description of all components')

    ## provides description of client datasources
    # \params cps component names
    # \returns JSON string with description of client datasources
    def clientSources(self, cps):
        nexusconfig_device = self.__setConfigInstance()
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
        nexusconfig_device = self.__setConfigInstance()
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
        nexusconfig_device = self.__setConfigInstance()
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

    ## checks client records
    def __checkClientRecords(self, datasources, pools):

        describer = Describer(self.__setConfigInstance())

        frecords = Utils.getFullDeviceNames(pools)
        dsres = describer.dataSources(
            set(datasources) - set(frecords.keys()), 'CLIENT')
        records = [str(dsr[2]) for dsr in dsres.values()]

        cpres = describer.components(
            list(set(self.components) |
                 set(self.automaticComponents) |
                 set(self.mandatoryComponents())),
            '', 'CLIENT')
        for grp in cpres:
            for dss in grp.values():
                for dsrs in dss.values():
                    for dsr in dsrs:
                        records.append(str(dsr[2]))
        if self.__server:
            print >> self.__server.log_debug, "Records:", records

        urecords = json.loads(self.__selection["DataRecord"]).keys()
        precords = frecords.values()
        missing = sorted(set(records)
                         - set(self.recorder_names)
                         - set(urecords)
                         - set(precords))
        if self.__server:
            print >> self.__server.log_debug, "URecords:", urecords
        if self.__server:
            print >> self.__server.log_debug, "PRecords:", precords
        if missing:
            raise Exception(
                "User Data not defined %s" % str(missing))

    @classmethod
    def __createMntGrp(cls, ms, mntGrpName, timer, pools):
        pool = None
        amntgrp = Utils.getEnv('ActiveMntGrp', ms)
        msp = Utils.openProxy(ms)
        pn = msp.get_property("PoolNames")["PoolNames"]
        apool = None
        lpool = [None, 0]
        fpool = None
        for pl in pn:
            pool = Utils.openProxy(pl)
            if not fpool:
                fpool = pool
            mntgrps = Utils.getMntGrps(pool)
            if amntgrp in mntgrps:
                apool = pool
            if lpool[1] < len(mntgrps):
                lpool = [pool, len(mntgrps)]

        if not apool:
            apool = lpool[0]
        lpool = None
        if not apool and fpool:
            apool = fpool
        fpool = None
        if not apool and len(pools) > 0:
            apool = pools[0]
        if apool:
            apool.CreateMeasurementGroup([mntGrpName, timer])
            mfullname = str(Utils.getMntGrpName(pools, mntGrpName))
        return mfullname

    ## prepares timers
    def __prepareTimers(self, cnf, ltimers, pools):
        mtimers = json.loads(self.__selection["Timer"])
        timer = mtimers[0] if mtimers else ''
        if not timer:
            raise Exception(
                "Timer or Monitor not defined")
        fullname = Utils.getFullDeviceNames(pools, [timer])[timer]
        if not fullname:
            raise Exception(
                "Timer or Monitor cannot be found amount the servers")
        cnf['monitor'] = fullname
        cnf['timer'] = fullname
        if len(mtimers) > 1:
            ltimers = set(mtimers[1:])
            if timer in ltimers:
                ltimers.remove(timer)
        return timer

    def __fetchChannels(self, dontdisplay, timers, pools):
        aliases = []
        datasources = self.dataSources

        self.__checkClientRecords(datasources, pools)
        if isinstance(datasources, list):
            aliases = list(datasources)
        pchs = json.loads(self.__selection["OrderedChannels"])
        aliases.extend(list(set(pchs) & set(self.disableDataSources)))

        res = self.__cpdescription('CLIENT')

        for grp in res:
            for cp, dss in grp.items():
                ndcp = cp in dontdisplay
                for ds in dss.keys():
                    aliases.append(str(ds))
                    if not ndcp and str(ds) in dontdisplay:
                        dontdisplay.remove(str(ds))

        self.__selection["HiddenElements"] = json.dumps(list(dontdisplay))
        aliases = list(set(aliases))

        for tm in timers:
            if tm not in aliases:
                aliases.append(tm)
                dontdisplay.add(tm)

        ordchannels = [ch for ch in pchs if ch in aliases]
        aliases = list(set(aliases) - set(ordchannels))
        ordchannels.extend(aliases)
        return ordchannels

    ## sets mntgrp
    def __prepareMntGrp(self, cnf, timer, pools):
        if not self.__selection["MntGrp"]:
            self.__selection["MntGrp"] = self.__defaultmntgrp
        mntGrpName = self.__selection["MntGrp"]
        mfullname = str(Utils.getMntGrpName(pools, mntGrpName))
        ms = self.__getMacroServer()

        if not mfullname:
            mfullname = self.__createMntGrp(ms, mntGrpName, timer, pools)

        Utils.setEnv('ActiveMntGrp', mntGrpName, ms)
        cnf['label'] = mntGrpName
        return mfullname

    ## set active measurement group from components
    def createMntGrpConfiguration(self):
        pools = self.__getPools()
        cnf = {}
        cnf['controllers'] = {}
        cnf['description'] = "Measurement Group"
        cnf['label'] = ""

        dontdisplay = set(json.loads(self.__selection["HiddenElements"]))

        ltimers = set()
        timer = self.__prepareTimers(cnf, ltimers, pools)

        aliases = self.__fetchChannels(
            dontdisplay, set(ltimers) | set([timer]), pools)

        mfullname = self.__prepareMntGrp(cnf, timer, pools)

        index = 0
        fullnames = Utils.getFullDeviceNames(pools, aliases)
        for al in aliases:
            index = Utils.addDevice(
                al, dontdisplay, pools, cnf,
                al if al in ltimers else timer, index, fullnames)

        conf = json.dumps(cnf)
        self.storeConfiguration()
        return conf, mfullname

    ## set active measurement group from components
    # \returns string with mntgrp configuration
    def updateMntGrp(self):
        conf, mntgrp = self.createMntGrpConfiguration()
        dpmg = Utils.openProxy(mntgrp)
        dpmg.Configuration = conf
        return str(dpmg.Configuration)

    def __createDataSources(self, tangods):
        ads = self.availableDataSources()
        sds = self.getSourceDescription(ads)

        extangods = []
        exsource = {}
        for name, label, initsource in tangods:
            source = initsource if initsource[:8] != 'tango://' \
                else initsource[8:]
            msource = None
            csource = None
            spsource = source.split("/")
            if len(spsource) > 3 and ":" in spsource[0]:
                host, port = spsource[0].split(":")
                mhost = host.split(".")[0]
                csource = "/".join(spsource[1:])
                if mhost != host:
                    msource = "%s:%s/%s" % (mhost, port, csource)
                device = "/".join(spsource[1:-1])
                attribute = spsource[-1]
                exsource[source] = [host, port, device, attribute]
            extangods.append(
                [name, label, initsource, source, msource, csource])

        jds = {}
        for ds in sds:
            js = json.loads(ds)
            for name, label, initsource, source, msource, csource in extangods:
                if source == js["record"]:
                    jds[initsource] = js["dsname"]
                    break
                elif msource == js["record"]:
                    jds[initsource] = js["dsname"]
                    break

        for name, label, initsource, source, msource, csource in extangods:
            if initsource not in jds:
                jds[initsource] = None
                i = 0
                nname = name
                while nname in ads:
                    i += 1
                    nname = "%s_%s" % (name, i)
                name = nname

                if source in exsource:
                    host, port, device, attribute = exsource[source]
                    df = XMLFile("ds.xml")
                    sr = NDSource(df)
                    sr.initTango(
                        name, device, "attribute", attribute, host, port)

                    inst = self.__setConfigInstance()
                    xml = df.prettyPrint()
                    inst.xmlstring = str(xml)
                    inst.storeDataSource(str(name))
                    jds[initsource] = name
        return jds

    ## swithc to active measurement
    def switchMntGrp(self):
        ms = self.__getMacroServer()
        amntgrp = Utils.getEnv('ActiveMntGrp', ms)
        self.__selection["MntGrp"] = amntgrp
        self.fetchConfiguration()
        self.importMntGrp()

    ## import setting from active measurement
    def importMntGrp(self):
        conf = json.loads(self.mntGrpConfiguration())

        pools = self.__getPools()
        dsg = json.loads(self.__selection["DataSourceGroup"])
        hel = json.loads(self.__selection["HiddenElements"])
        channels = Utils.getExperimentalChannels(pools)
        for ch in channels:
            if ch in dsg.keys():
                dsg[ch] = False
            if ch in hel:
                hel.remove(ch)

        otimers = None
        timers = {}
        tangods = []
        if "timer" in conf.keys() and "controllers" in conf.keys():
            timers[conf["timer"]] = ''
            for ctrl in conf["controllers"].values():
                if 'units' in ctrl.keys() and \
                        '0' in ctrl['units'].keys():
                    if 'timer' in ctrl['units']['0'].keys():
                        timers[ctrl['units']['0']['timer']] = ''
                        if 'channels' in ctrl['units']['0'].keys():
                            for ch in ctrl['units']['0']['channels'].values():
                                dsg[ch['name']] = True

                                if not bool(ch['plot_type']):
                                    hel.append(ch['name'])
                    if 'channels' in ctrl['units']['0'].keys():
                        for ch in ctrl['units']['0']['channels'].values():
                            if '_controller_name' in ch.keys() and \
                                    ch['_controller_name'] == '__tango__':
                                tangods.append(
                                    [ch['name'], ch['label'], ch["source"]])

            if tangods and NXSTOOLS:
                jds = self.__createDataSources(tangods)
                for ctrl in conf["controllers"].values():
                    if 'units' in ctrl.keys() and \
                            '0' in ctrl['units'].keys():
                        if 'channels' in ctrl['units']['0'].keys():
                            for ch in ctrl['units']['0']['channels'].values():
                                if '_controller_name' in ch.keys() and \
                                        ch['_controller_name'] == '__tango__':
                                    if ch["source"] in jds.keys():
                                        name = jds[ch["source"]]
                                        dsg[name] = True
                                        if not bool(ch['plot_type']):
                                            hel.append(ch['name'])

            dtimers = Utils.getAliases(pools, timers)
            otimers = list(dtimers.values())
            otimers.remove(dtimers[conf["timer"]])
            otimers.insert(0, dtimers[conf["timer"]])

            tms = json.loads(self.__selection["Timer"])
            tms.extend(otimers)

            hel2 = json.loads(self.__selection["HiddenElements"])
            for tm in tms:
                if tm in hel2:
                    if tm in dsg.keys():
                        dsg[tm] = False
                    if tm in hel:
                        hel.remove(tm)

        changed = False
        jdsg = json.dumps(dsg)
        if self.__selection["DataSourceGroup"] != jdsg:
            self.__selection["DataSourceGroup"] = jdsg
            changed = True

        jhel = json.dumps(hel)
        if self.__selection["HiddenElements"] != jhel:
            self.__selection["HiddenElements"] = jhel
            changed = True

        if otimers is not None:
            jtimers = json.dumps(otimers)
            if self.__selection["Timer"] != jtimers:
                self.__selection["Timer"] = jtimers
                changed = True
        if changed:
            self.storeConfiguration()

    ## available mntgrps
    # \returns list of available measurement groups
    def availableMeasurementGroups(self):
        mntgrps = None
        pool = None
        ms = self.__getMacroServer()
        msp = Utils.openProxy(ms)
        pn = msp.get_property("PoolNames")["PoolNames"]
        fpool = None
        for pl in pn:
            pool = Utils.openProxy(pl)
            if not fpool:
                fpool = pool
        if fpool:
            mntgrps = Utils.getMntGrps(fpool)
        mntgrps = mntgrps if mntgrps else []
        amntgrp = Utils.getEnv('ActiveMntGrp', ms)

        try:
            if mntgrps:
                ind = mntgrps.index(amntgrp)
                mntgrps[0], mntgrps[ind] = mntgrps[ind], mntgrps[0]
        except ValueError:
            pass
        return mntgrps

    ## provides configuration of mntgrp
    # \param proxy DeviceProxy of mntgrp
    # \returns string with mntgrp configuration
    def mntGrpConfiguration(self, proxy=None):
        if not proxy:
            pools = self.__getPools()
            if not self.__selection["MntGrp"]:
                self.switchMntGrp()
            mntGrpName = self.__selection["MntGrp"]
            fullname = str(Utils.getMntGrpName(pools, mntGrpName))
            if not fullname:
                return "{}"
            dpmg = Utils.openProxy(fullname)
        else:
            dpmg = proxy
        return str(dpmg.Configuration)

    ## check if active measurement group was changed
    # \returns True if it is different to the current setting
    def isMntGrpChanged(self):
        mgconf = json.loads(self.mntGrpConfiguration())
        llconf, _ = self.createMntGrpConfiguration()
        lsconf = json.loads(llconf)
        return not Utils.compareDict(mgconf, lsconf)

    ##  sends ConfigVariables into ConfigServer
    #        and updates serialno if appendEntry selected
    def updateConfigVariables(self):

        confvars = self.configVariables
        nexusconfig_device = self.__setConfigInstance()
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
        ads = set(json.loads(self.__selection["AutomaticDataSources"]))
        pools = self.__getPools()
        nonexisting = []
        fnames = Utils.getFullDeviceNames(pools, ads)
        nexusconfig_device = self.__setConfigInstance()
        describer = Describer(nexusconfig_device)

        for dev in ads:
            if dev not in fnames.keys():
                nonexisting.append(dev)

        acps = json.loads(self.__selection["AutomaticComponentGroup"])

        rcp = set()
        toCheck = {}
        for acp in acps.keys():
            res = describer.components([acp], '', '')
            for cp, dss in res[1].items():
                if isinstance(dss, dict):
                    tgds = describer.dataSources(dss.keys(), 'TANGO')
                    for ds in dss.keys():
                        if ds in tgds.keys():
                            if cp not in toCheck.keys():
                                toCheck[cp] = [cp]
                            srec = tgds[ds][2].split("/")
                            rds = "/".join(srec[:-1])
                            attr = srec[-1]
                            toCheck[cp].append((str(ds), str(rds), str(attr)))
                        elif ds in nonexisting:
                            rcp.add(cp)
                            if cp in toCheck.keys():
                                toCheck.pop(cp)
                            break
                        elif ds in ads:
                            if cp not in toCheck.keys():
                                toCheck[cp] = [cp]
                            toCheck[cp].append(str(ds))

        cqueue = Queue.Queue()
        for lds in toCheck.values():
            if self.__server:
                print >> self.__server.log_debug, "To Check:", lds
            cqueue.put(lds)
        for _ in range(self.numberOfThreads):
            thd = threading.Thread(target=checker, args=(cqueue,))
            thd.daemon = True
            thd.start()
        cqueue.join()

        for lds in toCheck.values():
            if lds and len(lds) > 0:
                if self.__server:
                    print >> self.__server.log_debug, "Problem with:", lds
                rcp.add(lds[0])

        for acp in acps.keys():
            if acp in rcp:
                acps[acp] = False
            else:
                acps[acp] = True

        jacps = json.dumps(acps)
        if self.__selection["AutomaticComponentGroup"] != jacps:
            self.__selection["AutomaticComponentGroup"] = jacps
            self.storeConfiguration()

    ## provides available Timers from MacroServer pools
    # \returns  available Timers from MacroServer pools
    def __availableTimers(self):
        pools = self.__getPools()
        return Utils.getTimers(pools, self.timerFilterList)

    ##  provides description of all components
    availableTimers = property(
        __availableTimers,
        doc='provides available Timers from MacroServer pools')

    ## provides full name of Measurement group
    # \param name alias
    # \returns full name of Measurement group
    def findMntGrp(self, name):
        pools = self.__getPools()
        return Utils.getMntGrpName(pools, name)

    ## provides a list of Disable DataSources
    # \returns list of disable datasources
    def __disableDataSources(self):
        res = self.__cpdescription()
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

    ## fetches Enviroutment Data
    # \returns JSON String with important variables
    def fetchEnvData(self):
        params = ["ScanDir",
                  "ScanFile",
                  "ScanID",
#                  "ActiveMntGrp",
                  "NeXusSelectorDevice"]
        res = {}
        dp = Utils.openProxy(self.__getMacroServer())
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
        ms = self.__getMacroServer()
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

        dp = Utils.openProxy(self.__getMacroServer())
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

        ms = self.__getMacroServer()
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

    ## creates dynamic component
    # \param params datasource parameters
    # \returns dynamic component name
    def createDynamicComponent(self, params):
        nexusconfig_device = self.__setConfigInstance()
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
        nexusconfig_device = self.__setConfigInstance()
        dcpcreator = DynamicComponent(nexusconfig_device)
        dcpcreator.removeDynamicComponent(name)

    ## deletes mntgrp
    # \param name mntgrp name
    def deleteMntGrp(self, name):
        pool = None
        ms = self.__getMacroServer()
        msp = Utils.openProxy(ms)
        pn = msp.get_property("PoolNames")["PoolNames"]
        fpool = None
        for pl in pn:
            pool = Utils.openProxy(pl)
            if not fpool:
                fpool = pool
        if fpool:
            fpool.DeleteElement(str(name))
