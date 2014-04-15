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
from .Utils import Utils
import time
## NeXus Sardana Recorder settings
class Settings(object):
    

    def __init__(self, server = None):
        ## Tango server
        self.__server = server

        ## server configuration dictionary
        self.state = {}


        ## timer
        self.state["Timer"] = ''

        ## group of electable components
        self.state["ComponentGroup"] = '{}'

        ## group of automatic components describing instrument state
        self.state["AutomaticComponentGroup"] = '{}'

        ## automatic datasources
        self.state["AutomaticDataSources"] = '[]'

        ## selected datasources
        self.state["DataSourceGroup"] = '{}'

        ## group of optional components available for automatic selection
        self.state["OptionalComponents"] = ''

        
        ## appending new entries to existing file
        self.state["AppendEntry"] = False
        
        ## select components from the active measurement group
        self.state["ComponentsFromMntGrp"] = False
        
        ## Configuration Server variables
        self.state["ConfigVariables"] = '{}'

        ## JSON with Client Data Record
        self.state["DataRecord"] = '{}'

        ## JSON with DataSource Labels
        self.state["DataSourceLabels"] = '{}'

        ## JSON with NeXus paths for DataSource Labels
        self.state["LabelPaths"] = '{}'

        ## JSON with NeXus paths for DataSource Labels
        self.state["LabelLinks"] = '{}'

        ## JSON with NeXus paths for DataSource Labels
        self.state["LabelTypes"] = '{}'

        ## JSON with NeXus paths for DataSource Labels
        self.state["LabelShapes"] = '{}'

        ## create dynamic components
        self.state["DynamicComponents"] = True

        ## create links for dynamic components
        self.state["DynamicLinks"] = True

        ## path for dynamic components
        self.state["DynamicPath"] = '/entry$var.serialno:NXentry/NXinstrument/NXcollection'

        ## timezone
        self.state["TimeZone"] = 'Europe/Berlin'

        ## configuration file
        self.configFile = '/tmp/nxsrecconfig.cfg'

        ## tango database
        self.__db = PyTango.Database()


        ## Configuration Server device name
        self.state["ConfigDevice"] = ''

        ## MacroServer device name
        self.state["MacroServer"] = ''

        ## config server proxy
        self.__configProxy = None

        ## NeXus Data Writer device
        self.state["WriterDevice"] = ''

        ## config writer proxy
        self.__writerProxy = None

        ## default mntgrp
        self.__defaultmntgrp = 'mntgrp'

    def components(self):
        cps = json.loads(self.state["ComponentGroup"])
        if isinstance(cps, dict):
            return [cp for cp in cps.keys() if cps[cp]]
        else:
            return []

    def automaticComponents(self):
        cps = json.loads(self.state["AutomaticComponentGroup"])
        if isinstance(cps, dict):
            return [cp for cp in cps.keys() if cps[cp]]
        else:
            return []
        

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
            self.state["ConfigDevice"] = Utils.findDevice(self.__db, "NXSConfigServer")
        return self.state["ConfigDevice"]

    ## set method for configDevice attribute
    # \param name of configDevice           
    def __setConfigDevice(self, name):
        if name:
            self.state["ConfigDevice"] = name
        else:
            self.state["ConfigDevice"] = Utils.findDevice(self.__db, "NXSConfigServer")


    ## del method for configDevice attribute
    def __delConfigDevice(self):
        self.state.pop("ConfigDevice")

    ## the json data string
    configDevice = property(__getConfigDevice, __setConfigDevice, __delConfigDevice, 
                            doc = 'configuration server device name')






    ## get method for macroServer attribute
    # \returns name of macroServer           
    def __getMacroServer(self):
        if "MacroServer" not in self.state or not self.state["MacroServer"]:
            self.state["MacroServer"] = Utils.findDevice(self.__db,"MacroServer")
        return self.state["MacroServer"]

    ## set method for macroServer attribute
    # \param name of macroServer           
    def __setMacroServer(self, name):
        if name:
            self.state["MacroServer"] = name
        else:
            self.state["MacroServer"] = Utils.findDevice(self.__db,"MacroServer")


    ## del method for macroServer attribute
    def __delMacroServer(self):
        self.state.pop("MacroServer")

    ## the json data string
    macroServer = property(__getMacroServer, __setMacroServer, __delMacroServer, 
                            doc = 'door server device name')



    ## get method for writerDevice attribute
    # \returns name of writerDevice           
    def __getWriterDevice(self):
        if "writerDevice" not in self.state or not self.state["WriterDevice"]:
            self.state["WriterDevice"] = Utils.findDevice(self.__db, "NXSDataWriter")
        return self.state["WriterDevice"]

    ## set method for writerDevice attribute
    # \param name of writerDevice           
    def __setWriterDevice(self, name): 
        if name:
            self.state["WriterDevice"] = name
        else:
            self.state["WriterDevice"] = Utils.findDevice(
                self.__db,"NXSDataWriter")


    ## del method for writerDevice attribute
    def __delWriterDevice(self):
        self.state.pop("WriterDevice")


    ## the json data string
    writerDevice = property(__getWriterDevice, __setWriterDevice, 
                            __delWriterDevice, doc = 'Writer device name')







    ## get method for ActiveMntGrp attribute
    # \returns name of ActiveMntGrp
    def __getActiveMntGrp(self):
        ms =  self.__getMacroServer()
        return Utils.getEnv('ActiveMntGrp', ms)



    ## set method for ActiveMntGrp attribute
    # \param name of ActiveMntGrp           
    def __setActiveMntGrp(self, name):
        if not name:
            name =  self.__defaultmntgrp
        ms =  self.__getMacroServer()
        pools = Utils.pools(self.__db)
        pool = None
        full = Utils.findMntGrpName(name, pools)
        if not full:
            msp = Utils.openProxy(ms)
            pn = msp.get_property("PoolNames")["PoolNames"]
            if len(pn)>0:
                pool = Utils.openProxy(pn[0])
            if not pool and len(pools)> 0 :
                pool = pools[0]
            if pool:
                pool.CreateMeasurementGroup([name, self.state["Timer"]])
        if full or pool:        
            Utils.setEnv('ActiveMntGrp', name, ms)

    ## the json data string
    activeMntGrp = property(__getActiveMntGrp, __setActiveMntGrp,
                       doc = 'active measurement group')




    ## get method for ScanDir attribute
    # \returns name of ScanDir
    def __getScanDir(self):
        ms =  self.__getMacroServer()
        return str(Utils.getEnv('ScanDir', ms))

    ## set method for ScanDir attribute
    # \param name of ScanDir           
    def __setScanDir(self, name):
        s1 = time.time()
        ms =  self.__getMacroServer()
        s2 = time.time()
        Utils.setEnv('ScanDir', name, ms)
        s3 = time.time()
#        print "SCanDIR", s2-s1,s3-s2

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
    def __configCommand(self, command):
        if "configDevice" not in self.state or not self.state["ConfigDevice"]:
            self.__getConfigDevice()
        self.__configProxy = Utils.openProxy(self.state["ConfigDevice"])
        self.__configProxy.Open()
        res = getattr(self.__configProxy, command)()
        return res


    ## read configuration server attribute
    def __configAttr(self, attr):
        if "configDevice" not in self.state or not self.state["ConfigDevice"]:
            self.__getConfigDevice()
        self.__configProxy = Utils.openProxy(self.state["ConfigDevice"])
        self.__configProxy.Open()
        res = getattr(self.__configProxy, attr)
        return res
        

    ## mandatory components
    def mandatoryComponents(self):
        return self.__configCommand("MandatoryComponents")

    ## available components
    def availableComponents(self):
        return self.__configCommand("AvailableComponents")

    ## available datasources
    def availableDataSources(self):
        return self.__configCommand("AvailableDataSources")

    ## save configuration
    def dataSourcePath(self, name):
        labels = json.loads(self.state["DataSourceLabels"])
        label = labels.get(name, "")
        paths = json.loads(self.state["LabelPaths"])
        return paths.get(label, "")
        

    ## save configuration
    def saveConfiguration(self):
        fl = open(self.configFile, "w+")
        json.dump(self.state, fl)

    ## load configuration
    def loadConfiguration(self):
        fl = open(self.configFile, "r")
        self.state = json.load(fl)

        
    def description(self):
        dc = self.__description(full = True)
        jdc = json.dumps(dc)
        return jdc

    def __description(self, dstype = '', full = False):
        describer = Describer(self.state["ConfigDevice"])
        cp = None
        if not full:
            cp = list(set(self.components()) | 
            set(self.automaticComponents()) | 
            set(self.mandatoryComponents()))
        res = describer.run(cp, 'STEP')
        return res

    ## set active measurement group from components
    def updateMntGrp(self):
        s0 = time.time()
        pools = Utils.pools(self.__db)
        s1 = time.time()
        hsh = {}
        hsh['controllers'] = {} 
        hsh['description'] = "Measurement Group" 
        hsh['label'] = "" 
        timer = self.state["Timer"]
        datasources = self.dataSources()

        s2 = time.time()

        aliases = []
        if isinstance(datasources, list):
            aliases = datasources
        if timer:
            aliases.append(timer)

        s3 = time.time()

        res = self.__description('CLIENT')    
        for grp in res:
            for dss in grp.values():
                for ds in dss.keys():
                    aliases.append(str(ds))
        aliases = list(set(aliases))

        s4 = time.time()

        mntGrpName = self.__getActiveMntGrp()
        s5 = time.time()

        fullname = str(Utils.findMntGrpName(mntGrpName, pools))
        s6 = time.time()
        dpmg = Utils.openProxy(fullname)
        hsh['label'] = mntGrpName
        index = 0
        s7 = time.time()
        fullname = Utils.findFullDeviceName(timer, pools)
        s8 = time.time()
        if not fullname:
            raise Exception("Timer or Monitor cannot be found amount the servers")
        hsh['monitor'] = fullname
        hsh['timer'] = fullname
                        
        s9 = time.time()
#        for alias in aliases:
#            index = Utils.addDevice(alias, pools, hsh, timer, index)
        index = Utils.addDevices(aliases, pools, hsh, fullname, index)
        s10 = time.time()
        dpmg.Configuration = json.dumps(hsh)
        s11 = time.time()
#        print "update", s1-s0, s2-s1,s3-s2,s4-s3,s5-s4,s6-s5,s7-s6,s8-s7,s9-s8,s10-s9,s11-s10


    ## checks existing controllers of pools for 
    #      AutomaticDataSources
    def updateControllers(self):
        ads = set(json.loads(self.state["AutomaticDataSources"]))
        pools = Utils.pools(self.__db)
        nonexisting = []
        fnames = Utils.findFullDeviceNames(ads, pools)
        for dev in ads:
            if dev not in fnames.keys():
                nonexisting.append(dev)
        
        describer = Describer(self.state["ConfigDevice"])
        acps = json.loads(self.state["AutomaticComponentGroup"])
        
        rcp = set()
        for acp in acps.keys():
            res = describer.run([acp], '', '')
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
                
        self.state["AutomaticComponentGroup"] = json.dumps(acps)
        if self.__server:
            dp = PyTango.DeviceProxy(str(self.__server.get_name()))
            dp.write_attribute(str("AutomaticComponentGroup"), 
                               self.state["AutomaticComponentGroup"])

    def availableTimers(self):
        pools = Utils.pools(self.__db)
        return Utils.findTimers(pools)
        

    ## update a list of Disable DataSources
    def disableDataSources(self):
        if "configDevice" not in self.state or not self.state["ConfigDevice"]:
            self.__getConfigDevice()
        res = self.__description()    
        dds = set()

        for dss in res[1].values():
            if isinstance(dss, dict):
                for ds in dss.keys():
                    dds.add(ds)
        return list(dds)

            

        
