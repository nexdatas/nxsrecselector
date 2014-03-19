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

## NeXus Sardana Recorder settings
class Settings(object):
    

    def __init__(self, server = None):
        ## Tango server
        self.__server = server

        ## server configuration dictionary
        self.state = {}

        ## configuration version
        self.state["ConfigVersion"] = ''

        ## configuration version
        self.state["ComponentInfo"] = ''

        ## group of electable components
        self.state["ComponentGroup"] = '{}'

        ## group of automatic components describing instrument state
        self.state["AutomaticComponentGroup"] = '{}'

        ## automatic datasources
        self.state["AutomaticDataSources"] = '[]'

        ## disable datasources
        self.state["DisableDataSources"] = '[]'


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

        ## config server proxy
        self.__configProxy = None

        ## NeXus Data Writer device
        self.state["WriterDevice"] = ''

        ## config writer proxy
        self.__writerProxy = None

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
        dds = json.loads(self.state["DisableDataSources"])
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
            self.state["ConfigDevice"] = self.__findDevice("NXSConfigServer")
        return self.state["ConfigDevice"]

    ## set method for configDevice attribute
    # \param name of configDevice           
    def __setConfigDevice(self, name):
        if name:
            self.state["ConfigDevice"] = name
        else:
            self.state["ConfigDevice"] = self.__findDevice("NXSConfigServer")


    ## del method for configDevice attribute
    def __delConfigDevice(self):
        self.state.pop("ConfigDevice")


    ## the json data string
    configDevice = property(__getConfigDevice, __setConfigDevice, __delConfigDevice, 
                            doc = 'configuration server device name')



    ## get method for writerDevice attribute
    # \returns name of writerDevice           
    def __getWriterDevice(self):
        if "writerDevice" not in self.state or not self.state["WriterDevice"]:
            self.state["WriterDevice"] = self.__findDevice("NXSDataWriter")
        return self.state["WriterDevice"]

    ## set method for writerDevice attribute
    # \param name of writerDevice           
    def __setWriterDevice(self, name):
        if name:
            self.state["WriterDevice"] = name
        else:
            self.state["WriterDevice"] = self.__findDevice("NXSDataWriter")


    ## del method for writerDevice attribute
    def __delWriterDevice(self):
        self.state.pop("WriterDevice")


    ## the json data string
    writerDevice = property(__getWriterDevice, __setWriterDevice, 
                            __delWriterDevice, doc = 'Writer device name')






    ## get method for writerDevice attribute
    # \returns name of writerDevice           
    def __getWriterDevice(self):
        if not self.__writerDevice:
            self.__writerDevice = self.__findDevice("NXSDataWriter")
        return self.__writerDevice

    ## set method for writerDevice attribute
    # \param name of writerDevice           
    def __setWriterDevice(self, name):
        if name:
            self.__writerDevice = name
        else:
            self.__writerDevice = self.__findDevice("NXSDataWriter")


    ## del method for writerDevice attribute
    def __delWriterDevice(self):
        del self.__writerDevice 


    ## the json data string
    writerDevice = property(__getWriterDevice, __setWriterDevice, __delWriterDevice, 
                       doc = 'writeruration server device name')


    ## find device
    # \param name device class name
    def __findDevice(self, name):        
        servers = self.__db.get_device_exported_for_class(
            name).value_string
        if len(servers):
            return servers[0]                


    ## executes command on configuration server    
    def __configCommand(self, command):
        if "configDevice" not in self.state or not self.state["ConfigDevice"]:
            self.__getConfigDevice()
        self.__configProxy = PyTango.DeviceProxy(self.state["ConfigDevice"])
        self.__configProxy.Open()
        res = getattr(self.__configProxy, command)()
        return res


    ## read configuration server attribute
    def __configAttr(self, attr):
        if "configDevice" not in self.state or not self.state["ConfigDevice"]:
            self.__getConfigDevice()
        self.__configProxy = PyTango.DeviceProxy(self.state["ConfigDevice"])
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
        self.state["ConfigVersion"] = ''

    ## checks existing controllers of pools for 
    #      AutomaticDataSources
    def updateControllers(self):
        pass

    def __reloadDeps(self):
        pass

    def __getDS(self, strategy='', dstype=''):
        if "configDevice" not in self.state or not self.state["ConfigDevice"]:
            self.__getConfigDevice()
        describer = Describer(self.state["ConfigDevice"])
        res = describer.run(self.components(), strategy, dstype)
        dds = set()
        for dss in res[1].values():
            if isinstance(dss, dict):
                for ds in dss.keys():
                    dds.add(ds)
        return list(dds)

    ## update a list of Disable DataSources
    def updateDataSources(self):
        ver = self.state["ConfigVersion"]
        csver = self.__configAttr("Version")
        if not ver or csver != ver:
            self.__reloadDeps()
        
        dss = self.__getDS('STEP','CLIENT')
        print "DSS = ", dss
        self.state["DisableDataSources"] = str(json.dumps(dss))
        if self.__server:
            dp = PyTango.DeviceProxy(str(self.__server.get_name()))
            dp.write_attribute(str("DisableDataSources"), 
                               self.state["DisableDataSources"])

            

        
