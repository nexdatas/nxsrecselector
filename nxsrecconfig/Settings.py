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
from .Utils import Utils
import pickle

## NeXus Sardana Recorder settings
class Settings(object):
    

    ## ccontructor
    # \param server NXSRecSelector server
    def __init__(self, server = None):
        ## Tango server
        self.__server = server

        ##  dictionary with Settings 
        self.state = {}


        ## timer
        self.state["Timer"] = '[]'

        ## group of electable components
        self.state["ComponentGroup"] = '{}'

        ## group of automatic components describing instrument state
        self.state["AutomaticComponentGroup"] = '{}'

        ## automatic datasources
        self.state["AutomaticDataSources"] = '[]'

        ## selected datasources
        self.state["DataSourceGroup"] = '{}'

        ## group of optional components available for automatic selection
        self.state["OptionalComponents"] = '{}'

        
        ## appending new entries to existing file
        self.state["AppendEntry"] = False
        
        ## select components from the active measurement group
        self.state["ComponentsFromMntGrp"] = False
        
        ## Configuration Server variables
        self.state["ConfigVariables"] = '{}'

        ## JSON with Client Data Record
        self.state["DataRecord"] = '{}'

        ## JSON with Element Labels
        self.state["Labels"] = '{}'

        ## JSON with NeXus paths for Label Paths
        self.state["LabelPaths"] = '{}'

        ## JSON with NeXus paths for Label Links
        self.state["LabelLinks"] = '{}'

        ## JSON with NeXus paths for Label Displays
        self.state["HiddenElements"] = '[]'

        ## JSON with NeXus paths for Label Types
        self.state["LabelTypes"] = '{}'

        ## JSON with NeXus paths for Label Shapes
        self.state["LabelShapes"] = '{}'

        ## create dynamic components
        self.state["DynamicComponents"] = True

        ## create links for dynamic components
        self.state["DynamicLinks"] = True

        ## path for dynamic components
        self.state["DynamicPath"] = \
            '/entry$var.serialno:NXentry/NXinstrument/NXcollection'

        ## timezone
        self.state["TimeZone"] = 'Europe/Berlin'

        ## configuration file
        self.configFile = '/tmp/nxsrecconfig.cfg'

        ## tango database
        self.__db = PyTango.Database()


        ## Configuration Server device name
        self.state["ConfigDevice"] = ''

        ## Door device name
        self.state["Door"] = ''

        ## MntGrp
        self.state["MntGrp"] = ''


        ## config server proxy
        self.__configProxy = None

        ## NeXus Data Writer device
        self.state["WriterDevice"] = ''

        ## config writer proxy
        self.__writerProxy = None

        ## default mntgrp
        self.__defaultmntgrp = 'nxsmntgrp'

        ## black list of pools
        self.poolBlacklist = []

        self.__macroserver = ""


        self.__pools = []

        ## Record names set by sardana
        self.recorder_names = ['serialno', 'end_time', 'start_time', 
                               'point_nb', 'timestamps']


    ## provides selected components
    # \returns list of available selected components
    def components(self):
        cps = json.loads(self.state["ComponentGroup"])
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

    ## provides automatic components
    # \returns list of available automatic components
    def automaticComponents(self):
        self.updateControllers()
        cps = json.loads(self.state["AutomaticComponentGroup"])
        if isinstance(cps, dict):
            return [cp for cp in cps.keys() if cps[cp]]
        else:
            return []
        

    ## provides selected datasources
    # \returns list of available selected datasources
    def dataSources(self):
        dds = self.disableDataSources()
        if not isinstance(dds, list):
            dds = []
        dss = json.loads(self.state["DataSourceGroup"])
        if isinstance(dss, dict):
            return [ds for ds in dss.keys() if dss[ds] and ds not in dds]
        else:
            return []




    ## get method for configDevice attribute
    # \returns name of configDevice           
    def __getConfigDevice(self):
        if "ConfigDevice" not in self.state or not self.state["ConfigDevice"]:
            self.state["ConfigDevice"] = Utils.getDeviceName(
                self.__db, "NXSConfigServer")
        return self.state["ConfigDevice"]

    ## set method for configDevice attribute
    # \param name of configDevice           
    def __setConfigDevice(self, name):
        if name:
            self.state["ConfigDevice"] = name
        else:
            self.state["ConfigDevice"] = Utils.getDeviceName(
                self.__db, "NXSConfigServer")


    ## del method for configDevice attribute
    def __delConfigDevice(self):
        self.state.pop("ConfigDevice")

    ## the json data string
    configDevice = property(__getConfigDevice, __setConfigDevice, 
                            __delConfigDevice, 
                            doc = 'configuration server device name')


    ## get method for automaticDataSources attribute
    # \returns name of automaticDataSources           
    def __getAutomaticDataSources(self):
#        return self.state["AutomaticDataSources"]
        adsg = json.loads(self.state["AutomaticDataSources"])
        pmots = self.poolMotors()

        adsg = list(set(adsg) | set(pmots))
        return json.dumps(adsg)


    ## set method for automaticDataSources attribute
    # \param name of automaticDataSources           
    def __setAutomaticDataSources(self, name):
        jname = self.__stringToListJson(name)
        if self.state["AutomaticDataSources"] != jname:
            self.state["AutomaticDataSources"] = jname
            self.updateControllers()

    ## del method for automaticDataSources attribute
    def __delAutomaticDataSources(self):
        self.state.pop("AutomaticDataSources")

    ## the json data string
    automaticDataSources = property(
        __getAutomaticDataSources, 
        __setAutomaticDataSources, 
        __delAutomaticDataSources, 
        doc = 'automatic components group')



    ## set method for configuration attribute
    # \param name of configuration           
    def __setConfiguration(self, jconf):
        self.state = json.loads(jconf)


    ## get method for configuration attribute
    # \param name of configuration           
    def __getConfiguration(self):
        return json.dumps(self.state)

    ## del method for configuration attribute
    def __delConfiguration(self):
        self.state.pop("Configuration")

    ## the json data string
    configuration = property(
        __getConfiguration, 
        __setConfiguration, 
        __delConfiguration, 
        doc = 'automatic components group')



    ## get method for timer attribute
    # \returns name of timer           
    def __getTimer(self):
        return self.state["Timer"]


    ## set method for timer attribute
    # \param name of timer           
    def __setTimer(self, name):
        jname = self.__stringToListJson(name)
        if self.state["Timer"] != jname:
            self.state["Timer"] = jname

    ## del method for timer attribute
    def __delTimer(self):
        self.state.pop("Timer")

    ## the json data string
    timer = property(
        __getTimer, 
        __setTimer, 
        __delTimer, 
        doc = 'automatic components group')





    ## get method for optionalComponents attribute
    # \returns name of optionalComponents           
    def __getOptionalComponents(self):
        return self.state["OptionalComponents"]

    ## set method for optionalComponents attribute
    # \param name of optionalComponents           
    def __setOptionalComponents(self, name):
        jname = self.__stringToListJson(name)
        if self.state["OptionalComponents"] != jname:
            self.state["OptionalComponents"] = jname

    ## del method for optionalComponents attribute
    def __delOptionalComponents(self):
        self.state.pop("OptionalComponents")

    ## the json data string
    optionalComponents = property(
        __getOptionalComponents, 
        __setOptionalComponents, 
        __delOptionalComponents, 
        doc = 'automatic components group')




    @classmethod
    def __stringToDictJson(cls, string, toBool = False):
        try:
            acps = json.loads(string)
            assert isinstance(acps, dict) 
            jstring = string
        except:
            lst = re.sub("[^\w]", "  ", string).split()
            if len(lst) % 2:
                lst.append("")
            dct = dict(zip(*[iter(lst)]*2))
            if toBool:
                for k in dct.keys():
                    dct[k] = False \
                        if dct[k].lower() == 'false' else True
            jstring = json.dumps(dct)
        return jstring


    @classmethod
    def __stringToListJson(cls, string):
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
        return self.state["AutomaticComponentGroup"]


    ## set method for automaticComponentGroup attribute
    # \param name of automaticComponentGroup           
    def __setAutomaticComponentGroup(self, name):
        jname = self.__stringToDictJson(name, True)
        if self.state["AutomaticComponentGroup"] != jname:
            self.state["AutomaticComponentGroup"] = jname
            self.updateControllers()

    ## del method for automaticComponentGroup attribute
    def __delAutomaticComponentGroup(self):
        self.state.pop("AutomaticComponentGroup")

    ## the json data string
    automaticComponentGroup = property(
        __getAutomaticComponentGroup, 
        __setAutomaticComponentGroup, 
        __delAutomaticComponentGroup, 
        doc = 'automatic components group')


    ## get method for componentGroup attribute
    # \returns name of componentGroup           
    def __getComponentGroup(self):
        cpg = json.loads(self.state["ComponentGroup"])
        dss = json.loads(self.state["DataSourceGroup"]).keys()
        for cp in set(cpg.keys()):
            if cp in dss:
                cpg.pop(cp)

        return json.dumps(cpg)


    ## set method for componentGroup attribute
    # \param name of componentGroup           
    def __setComponentGroup(self, name):
        jname = self.__stringToDictJson(name, True)
        if self.state["ComponentGroup"] != jname:
            self.state["ComponentGroup"] = jname

    ## del method for componentGroup attribute
    def __delComponentGroup(self):
        self.state.pop("ComponentGroup")

    ## the json data string
    componentGroup = property(
        __getComponentGroup, 
        __setComponentGroup, 
        __delComponentGroup, 
        doc = 'components group')


    ## get method for dataSourceGroup attribute
    # \returns name of dataSourceGroup           
    def __getDataSourceGroup(self):
        dsg = json.loads(self.state["DataSourceGroup"])
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
        if self.state["DataSourceGroup"] != jname:
            self.state["DataSourceGroup"] = jname

    ## del method for dataSourceGroup attribute
    def __delDataSourceGroup(self):
        self.state.pop("DataSourceGroup")

    ## the json data string
    dataSourceGroup = property(
        __getDataSourceGroup, 
        __setDataSourceGroup, 
        __delDataSourceGroup, 
        doc = 'datasource  group')





    ## get method for labels attribute
    # \returns name of labels           
    def __getLabels(self):
        return self.state["Labels"]


    ## set method for labels attribute
    # \param name of labels           
    def __setLabels(self, name):
        jname = self.__stringToDictJson(name)
        if self.state["Labels"] != jname:
            self.state["Labels"] = jname

    ## del method for labels attribute
    def __delLabels(self):
        self.state.pop("Labels")

    ## the json data string
    labels = property(
        __getLabels, 
        __setLabels, 
        __delLabels, 
        doc = 'datasource  labels')




    ## get method for labelLinks attribute
    # \returns name of labelLinks           
    def __getLabelLinks(self):
        return self.state["LabelLinks"]


    ## set method for labelLinks attribute
    # \param name of labelLinks           
    def __setLabelLinks(self, name):
        jname = self.__stringToDictJson(name)
        if self.state["LabelLinks"] != jname:
            self.state["LabelLinks"] = jname

    ## del method for labelLinks attribute
    def __delLabelLinks(self):
        self.state.pop("LabelLinks")

    ## the json data string
    labelLinks = property(
        __getLabelLinks, 
        __setLabelLinks, 
        __delLabelLinks, 
        doc = 'label links')



    ## get method for hiddenElements attribute
    # \returns name of hiddenElements           
    def __getHiddenElements(self):
        return self.state["HiddenElements"]


    ## set method for hiddenElements attribute
    # \param name of hiddenElements           
    def __setHiddenElements(self, name):
        jname = self.__stringToListJson(name)
        if self.state["HiddenElements"] != jname:
            self.state["HiddenElements"] = jname

    ## del method for hiddenElements attribute
    def __delHiddenElements(self):
        self.state.pop("HiddenElements")

    ## the json data string
    hiddenElements = property(
        __getHiddenElements, 
        __setHiddenElements, 
        __delHiddenElements, 
        doc = 'label displays')




    ## get method for labelPaths attribute
    # \returns name of labelPaths           
    def __getLabelPaths(self):
        return self.state["LabelPaths"]


    ## set method for labelPaths attribute
    # \param name of labelPaths           
    def __setLabelPaths(self, name):
        jname = self.__stringToDictJson(name)
        if self.state["LabelPaths"] != jname:
            self.state["LabelPaths"] = jname

    ## del method for labelPaths attribute
    def __delLabelPaths(self):
        self.state.pop("LabelPaths")

    ## the json data string
    labelPaths = property(
        __getLabelPaths, 
        __setLabelPaths, 
        __delLabelPaths, 
        doc = 'label paths')


    ## get method for labelShapes attribute
    # \returns name of labelShapes           
    def __getLabelShapes(self):
        return self.state["LabelShapes"]


    ## set method for labelShapes attribute
    # \param name of labelShapes           
    def __setLabelShapes(self, name):
        jname = self.__stringToDictJson(name)
        if self.state["LabelShapes"] != jname:
            self.state["LabelShapes"] = jname

    ## del method for labelShapes attribute
    def __delLabelShapes(self):
        self.state.pop("LabelShapes")

    ## the json data string
    labelShapes = property(
        __getLabelShapes, 
        __setLabelShapes, 
        __delLabelShapes, 
        doc = 'label shapes')



    ## get method for labelTypes attribute
    # \returns name of labelTypes           
    def __getLabelTypes(self):
        return self.state["LabelTypes"]


    ## set method for labelTypes attribute
    # \param name of labelTypes           
    def __setLabelTypes(self, name):
        jname = self.__stringToDictJson(name)
        if self.state["LabelTypes"] != jname:
            self.state["LabelTypes"] = jname

    ## del method for labelTypes attribute
    def __delLabelTypes(self):
        self.state.pop("LabelTypes")

    ## the json data string
    labelTypes = property(
        __getLabelTypes, 
        __setLabelTypes, 
        __delLabelTypes, 
        doc = 'label types')



    ## get method for mntGrp attribute
    # \returns name of mntGrp           
    def __getMntGrp(self):
        if "MntGrp" not in self.state or not self.state["MntGrp"]:
            self.state["MntGrp"] = self.__defaultmntgrp
        return self.state["MntGrp"]


    ## set method for mntGrp attribute
    # \param name of mntGrp           
    def __setMntGrp(self, name):
        if name:
            self.state["MntGrp"] = name
        else:
            self.state["MntGrp"] = self.__defaultmntgrp



    ## del method for mntGrp attribute
    def __delMntGrp(self):
        self.state.pop("MntGrp")

    ## the json data string
    mntGrp = property(__getMntGrp, __setMntGrp, 
                           __delMntGrp, 
                           doc = 'measurement group')





    ## get method for door attribute
    # \returns name of door           
    def __getDoor(self):
        try:
            dp = PyTango.DeviceProxy(self.state["Door"])
            dp.ping()
        except:
            self.state["Door"] = ''
        if "Door" not in self.state or not self.state["Door"]:
            self.state["Door"] = Utils.getDeviceName(
                self.__db, "Door")
            self.__updateMacroServer(self.state["Door"])
        return self.state["Door"]


    ## set method for door attribute
    # \param name of door           
    def __setDoor(self, name):
        if name:
            self.state["Door"] = name
        else:
            self.state["Door"] = Utils.getDeviceName(
                self.__db,"Door")
        self.__updateMacroServer(self.state["Door"])



    ## del method for door attribute
    def __delDoor(self):
        self.state.pop("Door")

    ## the json data string
    door = property(__getDoor, __setDoor, 
                           __delDoor, 
                           doc = 'door server device name')


    def __getMacroServer(self):
        if not self.__macroserver:
            door = self.__getDoor()
            self.__updateMacroServer(door)
        return self.__macroserver

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
        poolNames = list(
            set(msp.get_property("PoolNames")["PoolNames"])
            - set(self.poolBlacklist))
        self.__pools = Utils.getProxies(poolNames)
        


    ## the json data string
    macroServer = property(__getMacroServer,
                           doc = 'macroServer device name')

    
        



    ## get method for writerDevice attribute
    # \returns name of writerDevice           
    def __getWriterDevice(self):
        if "WriterDevice" not in self.state or not self.state["WriterDevice"]:
            self.state["WriterDevice"] = Utils.getDeviceName(
                self.__db, "NXSDataWriter")
        return self.state["WriterDevice"]

    ## set method for writerDevice attribute
    # \param name of writerDevice           
    def __setWriterDevice(self, name): 
        if name:
            self.state["WriterDevice"] = name
        else:
            self.state["WriterDevice"] = Utils.getDeviceName(
                self.__db,"NXSDataWriter")


    ## del method for writerDevice attribute
    def __delWriterDevice(self):
        self.state.pop("WriterDevice")


    ## the json data string
    writerDevice = property(__getWriterDevice, __setWriterDevice, 
                            __delWriterDevice, doc = 'Writer device name')










    ## get method for ScanDir attribute
    # \returns name of ScanDir
    def __getScanDir(self):
        ms =  self.__getMacroServer()
        return str(Utils.getEnv('ScanDir', ms))

    ## set method for ScanDir attribute
    # \param name of ScanDir           
    def __setScanDir(self, name):
        ms =  self.__getMacroServer()
        Utils.setEnv('ScanDir', name, ms)

    ## the json data string
    scanDir = property(__getScanDir, __setScanDir,
                       doc = 'scan directory')



    ## get method for ScanID attribute
    # \returns name of ScanID
    def __getScanID(self):
        ms =  self.__getMacroServer()
        sid = Utils.getEnv('ScanID', ms)
        if sid:
            return int(sid)
        else:
            Utils.setEnv('ScanID', 0, ms)
            return 0

    ## set method for ScanID attribute
    # \param name of ScanID           
    def __setScanID(self, name):
        ms =  self.__getMacroServer()
        Utils.setEnv('ScanID', name, ms)

    ## the json data string
    scanID = property(__getScanID, __setScanID,
                       doc = 'scan id')


    ## get method for ScanFile attribute
    # \returns name of ScanFile
    def __getScanFile(self):
        ms =  self.__getMacroServer()
        return Utils.getEnv('ScanFile', ms)

    ## set method for ScanFile attribute
    # \param name of ScanFile           
    def __setScanFile(self, name):
        ms =  self.__getMacroServer()
        Utils.setEnv('ScanFile', name, ms)

    ## the json data string
    scanFile = property(__getScanFile, __setScanFile,
                       doc = 'scan file(s)')



    ## executes command on configuration server    
    # \returns command result
    def __configCommand(self, command, var = None):
        if "configDevice" not in self.state or not self.state["ConfigDevice"]:
            self.__getConfigDevice()
        self.__configProxy = Utils.openProxy(self.state["ConfigDevice"])
        self.__configProxy.Open()
        if var is None:
            res = getattr(self.__configProxy, command)()
        else:
            res = self.__configProxy.command_inout(command, var)
        return res


    ## read configuration server attribute
    # \returns attribute value
    def __configAttr(self, attr):
        if "configDevice" not in self.state or not self.state["ConfigDevice"]:
            self.__getConfigDevice()
        self.__configProxy = Utils.openProxy(self.state["ConfigDevice"])
        self.__configProxy.Open()
        res = getattr(self.__configProxy, attr)
        return res
        

    ## mandatory components
    # \returns list of mandatory components
    def mandatoryComponents(self):
        return self.__configCommand("MandatoryComponents")

    ## available components
    # \returns list of available components
    def availableComponents(self):
        return self.__configCommand("AvailableComponents")

    ## available components
    # \returns list of component Variables
    def componentVariables(self, name):
        return self.__configCommand("ComponentVariables", name)

    ## available datasources
    # \returns list of available datasources
    def availableDataSources(self):
        return self.__configCommand("AvailableDataSources")



    ## available pool channels
    # \returns pool channels of the macroserver pools
    def poolChannels(self):
        res = []
        ms =  self.__getMacroServer()
        msp = Utils.openProxy(ms)
        pn = msp.get_property("PoolNames")["PoolNames"]
        if len(pn)>0:
            pool = Utils.openProxy(pn[0])
            exps = pool.ExpChannelList
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
        ms =  self.__getMacroServer()
        msp = Utils.openProxy(ms)
        pn = msp.get_property("PoolNames")["PoolNames"]
        if len(pn)>0:
            pool = Utils.openProxy(pn[0])
            exps = pool.MotorList
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
        labels = json.loads(self.state["Labels"])
        label = labels.get(name, "")
        paths = json.loads(self.state["LabelPaths"])
        return paths.get(label, "")
        

    ## saves configuration
    def saveConfiguration(self):
        fl = open(self.configFile, "w+")
        json.dump(self.state, fl)


    ## loads configuration
    def loadConfiguration(self):
        fl = open(self.configFile, "r")
        self.state = json.load(fl)


    ## provides components for all variables
    # \returns dictionary with components for all variables 
    def variableComponents(self):
        acp = self.availableComponents()
        vrs = {}
        for c in acp:
            vr =  self.componentVariables(c)
            if vr:
                for v in vr:
                    if v not in vrs:
                        vrs[v] = []
                    vrs[v].append(c)

        
        jdc = json.dumps(vrs)
        return jdc


    ## provides description of all components        
    # \returns JSON string with description of all components
    def description(self):
        dc = self.__description(full = True)
        jdc = json.dumps(dc)
        return jdc


    ## provides description of components        
    # \param dstype list datasets only with given datasource type.
    #        If '' all available ones are taken
    # \param full if True describes all available ones are taken
    #        otherwise selectect, automatic and mandatory
    # \returns description of required components
    def __description(self, dstype = '', full = False):
        describer = Describer(self.state["ConfigDevice"])
        cp = None
        if not full:
            cp = list(set(self.components()) | 
            set(self.automaticComponents()) | 
            set(self.mandatoryComponents()))
            res = describer.components(cp, 'STEP', dstype)
        else:
            res = describer.components(cp, '', dstype)
        return res



    ## provides full names of pool devices
    # \returns JSON string with full names of pool devices
    def fullDeviceNames(self):
        pools = self.__getPools()
        return  json.dumps(Utils.getFullDeviceNames(pools))
        

    ## checks client records
    def __checkClientRecords(self, datasources, pools):

        describer = Describer(self.state["ConfigDevice"])

        frecords = Utils.getFullDeviceNames(pools)

        dsres = describer.dataSources(
            set(datasources) - set(frecords.keys()), 'CLIENT')
        records = [str(dsr[2]) for dsr in dsres.values()]
        
        cp = list(set(self.components()) | 
                  set(self.automaticComponents()) | 
                  set(self.mandatoryComponents()))
        cpres = describer.components(cp, '', 'CLIENT')
        for grp in cpres:
            for dss in grp.values():
                for dsrs in dss.values():
                    for dsr in dsrs: 
                        records.append(str(dsr[2]))
        if self.__server:                
            print >> self.__server.log_debug, "Records:", records

        urecords = json.loads(self.state["DataRecord"]).keys()
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

        

    ## set active measurement group from components
    def createConfiguration(self):
        pools = self.__getPools()
#        timerable = self.availableTimers()
        cnf = {}
        cnf['controllers'] = {} 
        cnf['description'] = "Measurement Group" 
        cnf['label'] = "" 

        timers = json.loads(self.state["Timer"])
        timer =  timers[0] if timers else ''

        datasources = self.dataSources()
        hidden = json.loads(self.state["HiddenElements"])
        dontdisplay = set(hidden)

        self.__checkClientRecords(datasources, pools)

        aliases = []
        if isinstance(datasources, list):
            aliases = datasources
        if timer:
            aliases.append(timer)
        else:
            raise Exception(
                "Timer or Monitor not defined")

        res = self.__description('CLIENT')
        
        for grp in res:
            for cp, dss in grp.items():
                ndcp = cp in dontdisplay
                for ds in dss.keys():
                    aliases.append(str(ds))
                    if not ndcp and str(ds) in dontdisplay:
                        dontdisplay.remove(str(ds))
        aliases = list(set(aliases))

        if not self.state["MntGrp"]:
            self.state["MntGrp"] = self.__defaultmntgrp
        mntGrpName = self.state["MntGrp"]
        mfullname = str(Utils.getMntGrpName(pools, mntGrpName))
        ms =  self.__getMacroServer()
        if not mfullname:
            msp = Utils.openProxy(ms)
            pn = msp.get_property("PoolNames")["PoolNames"]
            if len(pn)>0:
                pool = Utils.openProxy(pn[0])
            if not pool and len(pools)> 0 :
                pool = pools[0]
            if pool:
                pool.CreateMeasurementGroup([mntGrpName, timer])
                mfullname = str(Utils.getMntGrpName(pools, mntGrpName))

        Utils.setEnv('ActiveMntGrp', mntGrpName, ms)
        cnf['label'] = mntGrpName
        index = 0
        fullname = Utils.getFullDeviceNames(pools, [timer])[timer]
        if not fullname:
            raise Exception(
                "Timer or Monitor cannot be found amount the servers")
        cnf['monitor'] = fullname
        cnf['timer'] = fullname
                        
        if len(timers) > 1:
            ltimers = set(timers[1:])
            if timer in ltimers:
                ltimers.remove(timer)
            aliases = sorted(set(aliases)- ltimers)
        else:
            ltimers = set()
            aliases = sorted(set(aliases))
        index = Utils.addDevices(aliases, dontdisplay, pools, 
                                 cnf, fullname, index)
        for ltimer in ltimers:
            index = Utils.addDevice(ltimer, dontdisplay, pools, 
                                    cnf, ltimer, index)
        conf = json.dumps(cnf)
        return conf, mfullname

    ## set active measurement group from components
    # \returns string with mntgrp configuration
    def updateMntGrp(self):
        conf, mntgrp  = self.createConfiguration()
        dpmg = Utils.openProxy(mntgrp)
        dpmg.Configuration = conf
        return str(dpmg.Configuration)


    ## import setting from active measurement
    def importMntGrp(self):
        conf = json.loads(self.mntGrpConfiguration())
        
        pools = self.__getPools()
        dsg = json.loads(self.dataSourceGroup)
        hel = json.loads(self.hiddenElements)
        channels = Utils.getFullDeviceNames(pools)
        for ch in channels.keys():
            if ch in dsg.keys():
                dsg[ch] = False
            if ch in hel:
                hel.remove(ch)
        timers = {}
        timers[conf["timer"]] = ''
        for ctrl in conf["controllers"].values():
            
            timers[ctrl['units']['0']['timer']] = ''
            for ch in ctrl['units']['0']['channels'].values():
                dsg[ch['name']] = True
                if not bool(ch['plot_type']):
                    hel.append(ch['name'])

        dtimers = Utils.getAliases(pools, timers)
        otimers = list(dtimers.values())
        otimers.remove(dtimers[conf["timer"]])
        otimers.insert(0,dtimers[conf["timer"]])

        jdsg = json.dumps(dsg)
        if self.state["DataSourceGroup"] != jdsg:
            self.state["DataSourceGroup"] = jdsg
            if self.__server:
                dp = PyTango.DeviceProxy(str(self.__server.get_name()))
                dp.write_attribute(str("DataSourceGroup"), 
                                   self.state["DataSourceGroup"])
        jhel = json.dumps(hel)
        if self.state["HiddenElements"] != jhel:
            self.state["HiddenElements"] =jhel
            if self.__server:
                dp = PyTango.DeviceProxy(str(self.__server.get_name()))
                dp.write_attribute(str("HiddenElements"), 
                                   self.state["HiddenElements"])

        jtimers = json.dumps(otimers)
        if self.state["Timer"] != jtimers:
            self.state["Timer"] =jtimers
            if self.__server:
                dp = PyTango.DeviceProxy(str(self.__server.get_name()))
                dp.write_attribute(str("Timer"), 
                                   self.state["Timer"])


    ## provides configuration of mntgrp
    # \param proxy DeviceProxy of mntgrp 
    # \returns string with mntgrp configuration
    def mntGrpConfiguration(self, proxy=None):
        if not proxy:
            pools = self.__getPools()
            if not self.state["MntGrp"]:
                self.state["MntGrp"] = self.__defaultmntgrp
            mntGrpName = self.state["MntGrp"]
            fullname = str(Utils.getMntGrpName(pools, mntGrpName))
            dpmg = Utils.openProxy(fullname)
        else:
            dpmg = proxy
        return str(dpmg.Configuration)


    ## check if active measurement group was changed
    # \returns True if it is different to the current setting
    def isMntGrpChanged(self):
        mgconf = json.loads(self.mntGrpConfiguration())
        llconf, _ = self.createConfiguration()
        lsconf = json.loads(llconf)
        return not Utils.compareDict(mgconf, lsconf)
        


    ## checks existing controllers of pools for 
    #      AutomaticDataSources
    def updateControllers(self):
        ads = set(json.loads(self.automaticDataSources))
        pools = self.__getPools()
        nonexisting = []
        fnames = Utils.getFullDeviceNames(pools, ads)
        for dev in ads:
            if dev not in fnames.keys():
                nonexisting.append(dev)
        
        describer = Describer(self.state["ConfigDevice"])
        acps = json.loads(self.state["AutomaticComponentGroup"])
        
        rcp = set()
        for acp in acps.keys():
            res = describer.components([acp], '', '')
            for cp, dss in res[1].items():
                if isinstance(dss, dict):
                    for ds in dss.keys():
                        if ds in nonexisting:
                            rcp.add(cp)
                            break
        for acp in acps.keys():
            if acp in rcp:
                acps[acp] = False
            else:
                acps[acp] = True
                
        jacps = json.dumps(acps)
        if self.state["AutomaticComponentGroup"] != jacps:
            self.state["AutomaticComponentGroup"] = jacps
            if self.__server:
                dp = PyTango.DeviceProxy(str(self.__server.get_name()))
                dp.write_attribute(str("AutomaticComponentGroup"), 
                                   self.state["AutomaticComponentGroup"])

    ## provides available Timers from MacroServer pools            
    # \returns  available Timers from MacroServer pools            
    def availableTimers(self):
        pools = self.__getPools()
        return Utils.getTimers(pools)

    ## provides full name of Measurement group
    # \param name alias
    # \returns full name of Measurement group
    def findMntGrp(self, name):
        pools = self.__getPools()
        return Utils.getMntGrpName(pools, name)
        

    ## update a list of Disable DataSources
    # \returns list of disable datasources
    def disableDataSources(self):
        if "configDevice" not in self.state \
                or not self.state["ConfigDevice"]:
            self.__getConfigDevice()
        res = self.__description()    
        dds = set()

        for dss in res[1].values():
            if isinstance(dss, dict):
                for ds in dss.keys():
                    dds.add(ds)
        return list(dds)

            

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
            if 'new' in dc.keys() :
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
        ms =  self.__getMacroServer()
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
