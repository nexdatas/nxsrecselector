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
import re
import PyTango
from .Describer import Describer
from .DynamicComponent import DynamicComponent
from .Utils import Utils
import pickle
import Queue
import getpass
import threading


ATTRIBUTESTOCHECK = ["Value", "Position", "Counts", "Data",
                     "Voltage", "Energy", "SampleTime"]

## NeXus Sardana Recorder settings
class Settings(object):

    ## ccontructor
    # \param server NXSRecSelector server
    def __init__(self, server=None):
        ## Tango server
        self.__server = server

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

        ##  dictionary with Settings
        self.__state = {}
        ## timer
        self.__state["Timer"] = '[]'
        ## ordered channels
        self.__state["OrderedChannels"] = '[]'
        ## group of electable components
        self.__state["ComponentGroup"] = '{}'
        ## group of automatic components describing instrument state
        self.__state["AutomaticComponentGroup"] = '{}'
        ## automatic datasources
        self.__state["AutomaticDataSources"] = '[]'
        ## selected datasources
        self.__state["DataSourceGroup"] = '{}'
        ## group of optional components available for automatic selqection
        self.__state["OptionalComponents"] = '[]'
        ## appending new entries to existing file
        self.__state["AppendEntry"] = False
        ## select components from the active measurement group
        self.__state["ComponentsFromMntGrp"] = False
        ## Configuration Server variables
        self.__state["ConfigVariables"] = '{}'
        ## JSON with Client Data Record
        self.__state["DataRecord"] = '{}'
        ## JSON with Element Labels
        self.__state["Labels"] = '{}'
        ## JSON with NeXus paths for Label Paths
        self.__state["LabelPaths"] = '{}'
        ## JSON with NeXus paths for Label Links
        self.__state["LabelLinks"] = '{}'
        ## JSON with NeXus paths for Label Displays
        self.__state["HiddenElements"] = '[]'
        ## JSON with NeXus paths for Label Types
        self.__state["LabelTypes"] = '{}'
        ## JSON with NeXus paths for Label Shapes
        self.__state["LabelShapes"] = '{}'
        ## create dynamic components
        self.__state["DynamicComponents"] = True
        ## create links for dynamic components
        self.__state["DynamicLinks"] = True
        ## path for dynamic components
        self.__state["DynamicPath"] = \
            '/entry$var.serialno:NXentry/NXinstrument/collection'
        ## timezone
        self.__state["TimeZone"] = self.__defaultzone
        ## Configuration Server device name
        self.__state["ConfigDevice"] = ''
        ## NeXus Data Writer device
        self.__state["WriterDevice"] = ''
        ## Door device name
        self.__state["Door"] = ''
        ## MntGrp
        self.__state["MntGrp"] = ''

        ## configuration file
        self.configFile = '/tmp/nxsrecconfig.cfg'

        ## tango database
        self.__db = PyTango.Database()

        ## config server proxy
        self.__configProxy = None
        ## config server module
        self.__configModule = None
        ## config writer proxy
        self.__writerProxy = None
        ## module label
        self.__moduleLabel = 'module'

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


    ## provides names of variables
    def names(self):
        return self.__state.keys()

    ## provides values of the required variable
    # \param name name of the required variable
    # \returns  values of the required variable
    def value(self, name):
        vl = ''
        if name in self.__state.keys():
            if isinstance(self.__state[name], unicode):
                vl = str(self.__state[name])
            else:
                vl = self.__state[name]
        return vl

    ## provides selected components
    # \returns list of available selected components
    def __components(self):
        cps = json.loads(self.__state["ComponentGroup"])
        ads = json.loads(self.dataSourceGroup)
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
        cps = json.loads(self.__state["AutomaticComponentGroup"])
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
        dss = json.loads(self.__state["DataSourceGroup"])
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
        if "ConfigDevice" not in self.__state \
                or not self.__state["ConfigDevice"]:
            self.__state["ConfigDevice"] = Utils.getDeviceName(
                self.__db, "NXSConfigServer")
        name = self.__state["ConfigDevice"]
        if name:
            if name != self.__moduleLabel:
                try:
                    dp = Utils.getProxies([name])
                    if not dp:
                        self.__state["ConfigDevice"] = ''
                        name = ''
                except:
                    self.__state["ConfigDevice"] = ''
                    name = ''
        return name

    ## set method for configDevice attribute
    # \param name of configDevice
    def __setConfigDevice(self, name):
        if name:
            self.__state["ConfigDevice"] = name
        else:
            self.__state["ConfigDevice"] = Utils.getDeviceName(
                self.__db, "NXSConfigServer")

    ## the json data string
    configDevice = property(__getConfigDevice, __setConfigDevice,
                            doc='configuration server device name')

    ## get method for automaticDataSources attribute
    # \returns name of automaticDataSources
    def __getAutomaticDataSources(self):
#        return self.__state["AutomaticDataSources"]
        adsg = json.loads(self.__state["AutomaticDataSources"])
        pmots = self.poolMotors()

        adsg = list(set(adsg if adsg else []) | set(pmots if pmots else []))
        return json.dumps(adsg)

    ## set method for automaticDataSources attribute
    # \param name of automaticDataSources
    def __setAutomaticDataSources(self, name):
        jname = self.__stringToListJson(name)
        if self.__state["AutomaticDataSources"] != jname:
            self.__state["AutomaticDataSources"] = jname

    ## the json data string
    automaticDataSources = property(
        __getAutomaticDataSources,
        __setAutomaticDataSources,
        doc='automatic components group')

    ## set method for configuration attribute
    # \param name of configuration
    def __setConfiguration(self, jconf):
        self.__state = json.loads(jconf)

    ## get method for configuration attribute
    # \returns configuration
    def __getConfiguration(self):
        return json.dumps(self.__state)

    ## the json data string
    configuration = property(
        __getConfiguration,
        __setConfiguration,
        doc='automatic components group')

    ## set method for appendEntry attribute
    # \param name of appendEntry
    def __setAppendEntry(self, ae):
        self.__state["AppendEntry"] = bool(ae)

    ## get method for appendEntry attribute
    # \returns flag of appendEntry
    def __getAppendEntry(self):
        return bool(self.__state["AppendEntry"])

    ## the json data string
    appendEntry = property(
        __getAppendEntry,
        __setAppendEntry,
        doc='flag for append entry')

    ## set method for componentsFromMntGrp attribute
    # \param flag  componentsFromMntGrp
    def __setComponentsFromMntGrp(self, flag):
        self.__state["ComponentsFromMntGrp"] = bool(flag)

    ## get method for componentsFromMntGrp attribute
    # \returns flag of componentsFromMntGrp
    def __getComponentsFromMntGrp(self):
        return bool(self.__state["ComponentsFromMntGrp"])

    ## the json data string
    componentsFromMntGrp = property(
        __getComponentsFromMntGrp,
        __setComponentsFromMntGrp,
        doc='flag for components from measurement group')

    ## set method for dynamicComponents attribute
    # \param flag  dynamic Components
    def __setDynamicComponents(self, flag):
        self.__state["DynamicComponents"] = bool(flag)

    ## get method for dynamicComponents attribute
    # \returns flag of dynamicComponents
    def __getDynamicComponents(self):
        return bool(self.__state["DynamicComponents"])

    ## the json data string
    dynamicComponents = property(
        __getDynamicComponents,
        __setDynamicComponents,
        doc='flag for dynamic components')

    ## set method for dynamicLinks attribute
    # \param flag dynamic Links
    def __setDynamicLinks(self, flag):
        self.__state["DynamicLinks"] = bool(flag)

    ## get method for dynamicLinks attribute
    # \returns flag of dynamicLinks
    def __getDynamicLinks(self):
        return bool(self.__state["DynamicLinks"])

    ## the json data string
    dynamicLinks = property(
        __getDynamicLinks,
        __setDynamicLinks,
        doc='flag for dynamic component links')

    ## set method for dynamicPath attribute
    # \param path dynamic path
    def __setDynamicPath(self, path):
        self.__state["DynamicPath"] = str(path)

    ## get method for dynamicPath attribute
    # \returns dynamicPath
    def __getDynamicPath(self):
        return str(self.__state["DynamicPath"])

    ## the json data string
    dynamicPath = property(
        __getDynamicPath,
        __setDynamicPath,
        doc='dynamic path')

    ## get method for timer attribute
    # \returns name of timer
    def __getTimer(self):
        return self.__state["Timer"]

    ## set method for timer attribute
    # \param name of timer
    def __setTimer(self, name):
        jname = self.__stringToListJson(name)
        if self.__state["Timer"] != jname:
            self.__state["Timer"] = jname

    ## the json data string
    timer = property(
        __getTimer,
        __setTimer,
        doc='timers')

    ## get method for orderedChannels attribute
    # \returns name of orderedChannels
    def __getOrderedChannels(self):
        pch = self.poolChannels()
        och = json.loads(self.__state["OrderedChannels"])

        ordchannels = [ch for ch in och if ch in pch]    
        uordchannels = list(set(pch) - set(och))
        ordchannels.extend(sorted(uordchannels))
        return json.dumps(ordchannels)

    ## set method for orderedChannels attribute
    # \param name of orderedChannels
    def __setOrderedChannels(self, name):
        jname = self.__stringToListJson(name)
        if self.__state["OrderedChannels"] != jname:
            self.__state["OrderedChannels"] = jname

    ## the json data string
    orderedChannels = property(
        __getOrderedChannels,
        __setOrderedChannels,
        doc='ordered channels')

    ## get method for optionalComponents attribute
    # \returns name of optionalComponents
    def __getOptionalComponents(self):
        return self.__state["OptionalComponents"]

    ## set method for optionalComponents attribute
    # \param name of optionalComponents
    def __setOptionalComponents(self, name):
        jname = self.__stringToListJson(name)
        if self.__state["OptionalComponents"] != jname:
            self.__state["OptionalComponents"] = jname

    ## the json data string
    optionalComponents = property(
        __getOptionalComponents,
        __setOptionalComponents,
        doc='automatic components group')

    ## get method for dataRecord attribute
    # \returns name of dataRecord
    def __getDataRecord(self):
        return self.__state["DataRecord"]

    ## set method for dataRecord attribute
    # \param name of dataRecord
    def __setDataRecord(self, name):
        jname = self.__stringToDictJson(name)
        if self.__state["DataRecord"] != jname:
            self.__state["DataRecord"] = jname

    ## the json data string
    dataRecord = property(
        __getDataRecord,
        __setDataRecord,
        doc='client data record')

    ## get method for configVariables attribute
    # \returns name of configVariables
    def __getConfigVariables(self):
        return self.__state["ConfigVariables"]

    ## set method for configVariables attribute
    # \param name of configVariables
    def __setConfigVariables(self, name):
        jname = self.__stringToDictJson(name)
        if self.__state["ConfigVariables"] != jname:
            self.__state["ConfigVariables"] = jname

    ## the json variables string
    configVariables = property(
        __getConfigVariables,
        __setConfigVariables,
        doc='configuration variables')

    @classmethod
    def __stringToDictJson(cls, string, toBool=False):
        try:
            if not string or string == "Not initialised":
                return {}
            acps = json.loads(string)
            assert isinstance(acps, dict)
            jstring = string
        except:
            lst = re.sub("[^\w]", "  ", string).split()
            if len(lst) % 2:
                lst.append("")
            dct = dict(zip(*[iter(lst)] * 2))
            if toBool:
                for k in dct.keys():
                    dct[k] = False \
                        if dct[k].lower() == 'false' else True
            jstring = json.dumps(dct)
        return jstring

    @classmethod
    def __stringToListJson(cls, string):
        if not string or string == "Not initialised":
            return []
        try:
            acps = json.loads(string)
            assert isinstance(acps, (list, tuple))
            jstring = string
        except:
            lst = re.sub("[^\w]", "  ", string).split()
            jstring = json.dumps(lst)
        return jstring

    ## get method for automaticComponentGroup attribute
    # \returns name of automaticComponentGroup
    def __getAutomaticComponentGroup(self):
        return self.__state["AutomaticComponentGroup"]

    ## set method for automaticComponentGroup attribute
    # \param name of automaticComponentGroup
    def __setAutomaticComponentGroup(self, name):
        jname = self.__stringToDictJson(name, True)
        if self.__state["AutomaticComponentGroup"] != jname:
            self.__state["AutomaticComponentGroup"] = jname

    ## the json data string
    automaticComponentGroup = property(
        __getAutomaticComponentGroup,
        __setAutomaticComponentGroup,
        doc='automatic components group')

    ## get method for componentGroup attribute
    # \returns name of componentGroup
    def __getComponentGroup(self):
        cpg = json.loads(self.__state["ComponentGroup"])
        dss = json.loads(self.__state["DataSourceGroup"]).keys()
        for cp in set(cpg.keys()):
            if cp in dss:
                cpg.pop(cp)

        return json.dumps(cpg)

    ## set method for componentGroup attribute
    # \param name of componentGroup
    def __setComponentGroup(self, name):
        jname = self.__stringToDictJson(name, True)
        if self.__state["ComponentGroup"] != jname:
            self.__state["ComponentGroup"] = jname

    ## the json data string
    componentGroup = property(
        __getComponentGroup,
        __setComponentGroup,
        doc='components group')

    ## get method for dataSourceGroup attribute
    # \returns name of dataSourceGroup
    def __getDataSourceGroup(self):
        dsg = json.loads(self.__state["DataSourceGroup"])
        ads = self.availableDataSources()
        pchs = self.poolChannels()
        for ds in tuple(dsg.keys()):
            if ds not in pchs and ds not in ads:
                dsg.pop(ds)
        for pc in pchs:
            if pc not in dsg.keys():
                dsg[pc] = False
        return json.dumps(dsg)

    ## set method for dataSourceGroup attribute
    # \param name of dataSourceGroup
    def __setDataSourceGroup(self, name):
        jname = self.__stringToDictJson(name, True)
        if self.__state["DataSourceGroup"] != jname:
            self.__state["DataSourceGroup"] = jname

    ## the json data string
    dataSourceGroup = property(
        __getDataSourceGroup,
        __setDataSourceGroup,
        doc='datasource  group')


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

    ## get method for labels attribute
    # \returns name of labels
    def __getLabels(self):
        return self.__state["Labels"]

    ## set method for labels attribute
    # \param name of labels
    def __setLabels(self, name):
        jname = self.__stringToDictJson(name)
        if self.__state["Labels"] != jname:
            self.__state["Labels"] = jname

    ## the json data string
    labels = property(
        __getLabels,
        __setLabels,
        doc='datasource  labels')

    ## get method for labelLinks attribute
    # \returns name of labelLinks
    def __getLabelLinks(self):
        return self.__state["LabelLinks"]

    ## set method for labelLinks attribute
    # \param name of labelLinks
    def __setLabelLinks(self, name):
        jname = self.__stringToDictJson(name)
        if self.__state["LabelLinks"] != jname:
            self.__state["LabelLinks"] = jname

    ## the json data string
    labelLinks = property(
        __getLabelLinks,
        __setLabelLinks,
        doc='label links')

    ## get method for hiddenElements attribute
    # \returns name of hiddenElements
    def __getHiddenElements(self):
        return self.__state["HiddenElements"]

    ## set method for hiddenElements attribute
    # \param name of hiddenElements
    def __setHiddenElements(self, name):
        jname = self.__stringToListJson(name)
        if self.__state["HiddenElements"] != jname:
            self.__state["HiddenElements"] = jname

    ## the json data string
    hiddenElements = property(
        __getHiddenElements,
        __setHiddenElements,
        doc='label displays')

    ## get method for labelPaths attribute
    # \returns name of labelPaths
    def __getLabelPaths(self):
        return self.__state["LabelPaths"]

    ## set method for labelPaths attribute
    # \param name of labelPaths
    def __setLabelPaths(self, name):
        jname = self.__stringToDictJson(name)
        if self.__state["LabelPaths"] != jname:
            self.__state["LabelPaths"] = jname

    ## the json data string
    labelPaths = property(
        __getLabelPaths,
        __setLabelPaths,
        doc='label paths')

    ## get method for labelShapes attribute
    # \returns name of labelShapes
    def __getLabelShapes(self):
        return self.__state["LabelShapes"]

    ## set method for labelShapes attribute
    # \param name of labelShapes
    def __setLabelShapes(self, name):
        jname = self.__stringToDictJson(name)
        if self.__state["LabelShapes"] != jname:
            self.__state["LabelShapes"] = jname

    ## the json data string
    labelShapes = property(
        __getLabelShapes,
        __setLabelShapes,
        doc='label shapes')

    ## get method for labelTypes attribute
    # \returns name of labelTypes
    def __getLabelTypes(self):
        return self.__state["LabelTypes"]

    ## set method for labelTypes attribute
    # \param name of labelTypes
    def __setLabelTypes(self, name):
        jname = self.__stringToDictJson(name)
        if self.__state["LabelTypes"] != jname:
            self.__state["LabelTypes"] = jname

    ## the json data string
    labelTypes = property(
        __getLabelTypes,
        __setLabelTypes,
        doc='label types')

    ## get method for mntGrp attribute
    # \returns name of mntGrp
    def __getMntGrp(self):
        if "MntGrp" not in self.__state or not self.__state["MntGrp"]:
            self.__state["MntGrp"] = self.__defaultmntgrp
        return self.__state["MntGrp"]

    ## set method for mntGrp attribute
    # \param name of mntGrp
    def __setMntGrp(self, name):
        if name:
            self.__state["MntGrp"] = name
        else:
            self.__state["MntGrp"] = self.__defaultmntgrp

    ## the json data string
    mntGrp = property(__getMntGrp, __setMntGrp,
                           doc='measurement group')

    ## get method for timeZone attribute
    # \returns name of timeZone
    def __getTimeZone(self):
        if "TimeZone" not in self.__state or not self.__state["TimeZone"]:
            self.__state["TimeZone"] = self.__defaultzone
        return self.__state["TimeZone"]

    ## set method for timeZone attribute
    # \param name of timeZone
    def __setTimeZone(self, name):
        if name:
            self.__state["TimeZone"] = name
        else:
            self.__state["TimeZone"] = self.__defaultzone

    ## th time zone
    timeZone = property(__getTimeZone, __setTimeZone,
                           doc='time zone')

    ## get method for door attribute
    # \returns name of door
    def __getDoor(self):
        try:
            dp = PyTango.DeviceProxy(str(self.__state["Door"]))
            dp.ping()
        except:
            self.__state["Door"] = ''
        if "Door" not in self.__state or not self.__state["Door"]:
            self.__state["Door"] = Utils.getDeviceName(
                self.__db, "Door")
            self.__updateMacroServer(self.__state["Door"])
        return self.__state["Door"]

    ## set method for door attribute
    # \param name of door
    def __setDoor(self, name):
        if name:
            self.__state["Door"] = name
        else:
            self.__state["Door"] = Utils.getDeviceName(
                self.__db, "Door")
        self.__updateMacroServer(self.__state["Door"])

    ## the json data string
    door = property(__getDoor, __setDoor,
                           doc='door server device name')

    def __getPools(self):
        if not self.__pools:
            door = self.__getDoor()
            self.__updateMacroServer(door)
        return self.__pools

    def __updateMacroServer(self, door):
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
            self.__updateMacroServer(door)
        return self.__macroserver

    ## the json data string
    macroServer = property(__getMacroServer,
                           doc='macroServer device name')

    ## get method for writerDevice attribute
    # \returns name of writerDevice
    def __getWriterDevice(self):
        if "WriterDevice" not in self.__state \
                or not self.__state["WriterDevice"]:
            self.__state["WriterDevice"] = Utils.getDeviceName(
                self.__db, "NXSDataWriter")
        res = self.__state["WriterDevice"]
        return res

    ## set method for writerDevice attribute
    # \param name of writerDevice
    def __setWriterDevice(self, name):
        if name:
            self.__state["WriterDevice"] = name
        else:
            self.__state["WriterDevice"] = Utils.getDeviceName(
                self.__db, "NXSDataWriter")

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
        if "ConfigDevice" not in self.__state \
                or not self.__state["ConfigDevice"]:
            self.__getConfigDevice()
        if self.__state["ConfigDevice"] and \
                self.__state["ConfigDevice"].lower() != self.__moduleLabel:
            self.__configProxy = Utils.openProxy(self.__state["ConfigDevice"])
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
                dbp = '{"host":"localhost","db":"nxsconfig","use_unicode":true,' \
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

    ## read configuration server attribute
    # \returns attribute value
    def __configAttr(self, attr):
        inst = self.__setConfigInstance()
        res = getattr(inst, attr)
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

    ## provides datasource path for the given label
    # \param name given datasource
    # \returns  datasource path for the given label
    def dataSourcePath(self, name):
        labels = json.loads(self.__state["Labels"])
        label = labels.get(name, "")
        paths = json.loads(self.__state["LabelPaths"])
        return paths.get(label, "")

    ## saves configuration
    def saveConfiguration(self):
        fl = open(self.configFile, "w+")
        json.dump(self.__state, fl)

    ## loads configuration
    def loadConfiguration(self):
        fl = open(self.configFile, "r")
        self.__state = json.load(fl)

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

    ## provides full names of pool devices
    # \returns JSON string with full names of pool devices
    def __fullDeviceNames(self):
        pools = self.__getPools()
        return json.dumps(Utils.getFullDeviceNames(pools))

    ## provides full names of pool devices
    fullDeviceNames = property(
        __fullDeviceNames,
        doc=' provides full names of pool devices')

    ## checks client records
    def __checkClientRecords(self, datasources, pools):

        nexusconfig_device = self.__setConfigInstance()
        describer = Describer(nexusconfig_device)

        frecords = Utils.getFullDeviceNames(pools)

        dsres = describer.dataSources(
            set(datasources) - set(frecords.keys()), 'CLIENT')
        records = [str(dsr[2]) for dsr in dsres.values()]

        cp = list(set(self.components) |
                  set(self.automaticComponents) |
                  set(self.mandatoryComponents()))
        cpres = describer.components(cp, '', 'CLIENT')
        for grp in cpres:
            for dss in grp.values():
                for dsrs in dss.values():
                    for dsr in dsrs:
                        records.append(str(dsr[2]))
        if self.__server:
            print >> self.__server.log_debug, "Records:", records

        urecords = json.loads(self.__state["DataRecord"]).keys()
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

    def __createMntGrp(self, ms, mntGrpName, timer, pools):
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

    ## set active measurement group from components
    def createMntGrpConfiguration(self):
        pools = self.__getPools()
        cnf = {}
        cnf['controllers'] = {}
        cnf['description'] = "Measurement Group"
        cnf['label'] = ""

        timers = json.loads(self.__state["Timer"])
        timer = timers[0] if timers else ''
        if not timer:
            raise Exception(
                "Timer or Monitor not defined")

        datasources = self.dataSources
        disabledatasources = self.disableDataSources
        hidden = json.loads(self.__state["HiddenElements"])
        dontdisplay = set(hidden)

        self.__checkClientRecords(datasources, pools)

        aliases = []
        if isinstance(datasources, list):
            aliases = datasources
        pchs = json.loads(self.orderedChannels)
        pdd = list(set(pchs) & set(disabledatasources))
        aliases.extend(pdd)

        for tm in timers:
            if tm not in aliases:
                aliases.append(tm)
                dontdisplay.add(tm)

        res = self.__cpdescription('CLIENT')

        for grp in res:
            for cp, dss in grp.items():
                ndcp = cp in dontdisplay
                for ds in dss.keys():
                    aliases.append(str(ds))
                    if not ndcp and str(ds) in dontdisplay:
                        dontdisplay.remove(str(ds))

        self.__state["HiddenElements"] = json.dumps(list(dontdisplay))
        aliases = list(set(aliases))

        if not self.__state["MntGrp"]:
            self.__state["MntGrp"] = self.__defaultmntgrp
        mntGrpName = self.__state["MntGrp"]
        mfullname = str(Utils.getMntGrpName(pools, mntGrpName))
        ms = self.__getMacroServer()

        if not mfullname:
            mfullname = self.__createMntGrp(ms, mntGrpName, timer, pools)

        Utils.setEnv('ActiveMntGrp', mntGrpName, ms)
        cnf['label'] = mntGrpName
        index = 0
        fullname = Utils.getFullDeviceNames(pools, [timer])[timer]
        if not fullname:
            raise Exception(
                "Timer or Monitor cannot be found amount the servers")
        cnf['monitor'] = fullname
        cnf['timer'] = fullname

        ltimers = set()
        if len(timers) > 1:
            ltimers = set(timers[1:])
            if timer in ltimers:
                ltimers.remove(timer)

        ordchannels = [ch for ch in pchs if ch in aliases]    
        uordchannels = list(set(aliases) - set(ordchannels))
    

        fullnames = Utils.getFullDeviceNames(pools, aliases)
        for al in ordchannels:
            index = Utils.addDevice(
                al, dontdisplay, pools, cnf,
                al if al in ltimers else timer, index, fullnames)
        for al in uordchannels:
            index = Utils.addDevice(
                al, dontdisplay, pools, cnf,
                al if al in ltimers else timer, index, fullnames)

        conf = json.dumps(cnf)
        return conf, mfullname

    ## set active measurement group from components
    # \returns string with mntgrp configuration
    def updateMntGrp(self):
        conf, mntgrp = self.createMntGrpConfiguration()
        dpmg = Utils.openProxy(mntgrp)
        dpmg.Configuration = conf
        return str(dpmg.Configuration)

    ## import setting from active measurement
    def importMntGrp(self):
        conf = json.loads(self.mntGrpConfiguration())

        pools = self.__getPools()
        dsg = json.loads(self.dataSourceGroup)
        hel = json.loads(self.hiddenElements)
        channels = Utils.getExperimentalChannels(pools)
        for ch in channels:
            if ch in dsg.keys():
                dsg[ch] = False
            if ch in hel:
                hel.remove(ch)

        otimers = None        
        timers = {}
        if "timer" in conf.keys() and "controllers" in conf.keys():
            timers[conf["timer"]] = ''
            for ctrl in conf["controllers"].values():
                if 'units' in ctrl.keys() and \
                        '0' in ctrl['units'].keys() and \
                        'timer' in ctrl['units']['0'].keys():
                    timers[ctrl['units']['0']['timer']] = ''
                    if 'channels' in ctrl['units']['0'].keys():
                        for ch in ctrl['units']['0']['channels'].values():
                            dsg[ch['name']] = True
                            if not bool(ch['plot_type']):
                                hel.append(ch['name'])

            dtimers = Utils.getAliases(pools, timers)
            otimers = list(dtimers.values())
            otimers.remove(dtimers[conf["timer"]])
            otimers.insert(0, dtimers[conf["timer"]])
            
            tms = json.loads(self.__state["Timer"])
            tms.extend(otimers)

            hel2 = json.loads(self.hiddenElements)
            for tm in tms:
                if tm in hel2:
                    if tm in dsg.keys():
                        dsg[tm] = False
                    if tm in hel:
                        hel.remove(tm)

        jdsg = json.dumps(dsg)
        if self.__state["DataSourceGroup"] != jdsg:
            self.__state["DataSourceGroup"] = jdsg
            if self.__server:
                dp = PyTango.DeviceProxy(str(self.__server.get_name()))
                dp.write_attribute(str("DataSourceGroup"),
                                   self.__state["DataSourceGroup"])
        jhel = json.dumps(hel)
        if self.__state["HiddenElements"] != jhel:
            self.__state["HiddenElements"] = jhel
            if self.__server:
                dp = PyTango.DeviceProxy(str(self.__server.get_name()))
                dp.write_attribute(str("HiddenElements"),
                                   self.__state["HiddenElements"])

        if otimers is not None:        
            jtimers = json.dumps(otimers)
            if self.__state["Timer"] != jtimers:
                self.__state["Timer"] = jtimers
                if self.__server:
                    dp = PyTango.DeviceProxy(str(self.__server.get_name()))
                    dp.write_attribute(str("Timer"),
                                       self.__state["Timer"])

    ## provides configuration of mntgrp
    # \param proxy DeviceProxy of mntgrp
    # \returns string with mntgrp configuration
    def mntGrpConfiguration(self, proxy=None):
        if not proxy:
            pools = self.__getPools()
            if not self.__state["MntGrp"]:
                self.__state["MntGrp"] = self.__defaultmntgrp
            mntGrpName = self.__state["MntGrp"]
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
        ads = set(json.loads(self.automaticDataSources))
        pools = self.__getPools()
        nonexisting = []
        fnames = Utils.getFullDeviceNames(pools, ads)
        nexusconfig_device = self.__setConfigInstance()
        describer = Describer(nexusconfig_device)

        for dev in ads:
            if dev not in fnames.keys():
                nonexisting.append(dev)

        acps = json.loads(self.__state["AutomaticComponentGroup"])

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
            thd = threading.Thread(target=_checker, args=(cqueue,))
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
        if self.__state["AutomaticComponentGroup"] != jacps:
            self.__state["AutomaticComponentGroup"] = jacps
            if self.__server:
                dp = PyTango.DeviceProxy(str(self.__server.get_name()))
                dp.write_attribute(str("AutomaticComponentGroup"),
                                   self.__state["AutomaticComponentGroup"])

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
        dp = Utils.openProxy(self.macroServer)
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
        jdata = self.__stringToDictJson(jdata)
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
        self.__importEnv(self.names(), self.__state)

    ## imports Enviroutment Data
    # \param names names of required variables
    # \param data dictionary with resulting data
    def __importEnv(self, names, data):
        params = ["ScanDir",
                  "ScanFile"]

        dp = Utils.openProxy(self.macroServer)
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
        self.__exportEnv(self.__state)

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
            self.labels, self.labelPaths, self.labelLinks,
            self.labelTypes, self.labelShapes)
        dcpcreator.setLinkParams(self.dynamicLinks, self.dynamicPath)

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

## checkers if Tango devices are alive
# \params cqueue queue with task of the form ['comp','alias','alias', ...]
def _checker(cqueue):
    while True:
        lds = cqueue.get()
        ok = True
        for ds in lds[1:]:
            if isinstance(ds, tuple) and len(ds) > 2:
                dname = str(ds[1])
                attr = str(ds[2])
            else:
                dname = str(ds)
                attr = None
                
            try:
                dp = PyTango.DeviceProxy(dname)
                if dp.state() in [
                    PyTango.DevState.FAULT, 
                    PyTango.DevState.ALARM]:
                    raise Exception("FAULT or ALARM STATE")
                dp.ping()
                if not attr:
                    for gattr in ATTRIBUTESTOCHECK:
                        if hasattr(dp, gattr):
                            _ = getattr(dp, gattr)
                else:
                    _ = getattr(dp, attr)
            except:
                ok = False
                break
        if ok:
            lds[:] = []
        cqueue.task_done()
