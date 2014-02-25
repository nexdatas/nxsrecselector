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

## NeXus Sardana Recorder settings
class Settings(object):
    

    def __init__(self, server = None):
        ## Tango server
        self.__server = server

        ## selected components
        self.components = ''

        ## selected datasources
        self.dataSources = ''
        
        ## active measurement group
        self.activeMntGrp = ''

        ## appending new entries to existing file
        self.appendEntry = False
        
        ## select components from the active measurement group
        self.componentsFromMntGrp = False
        
        ## Configuration Server variables
        self.configVariables = ''

        ## JSON with Client Data Record
        self.dataRecord = ''

        ## create dynamic components
        self.dynamicComponents = True

        ## create links for dynamic components
        self.dynamicLinks = True

        ## path for dynamic components
        self.dynamicPath = '/entry$var.serialno:NXentry/NXinstrument/NXcollection'
        

        ## scan directory
        self.scanDir = '/tmp/'
        
        ## scan file
        self.scanFile = 'test.nxs'

        ## scan file
        self.scanID = 1

        ## timezone
        self.timeZone = 'Europe/Berlin'


        ## tango database
        self.__db = PyTango.Database()


        ## Configuration Server device name
        self.__configDevice = ''

        ## config server proxy
        self.__configProxy = None

        ## NeXus Data Writer device
        self.__writerDevice = ''

        ## config writer proxy
        self.__writerProxy = None


    ## get method for configDevice attribute
    # \returns name of configDevice           
    def __getConfigDevice(self):
        if not self.__configDevice:
            self.__configDevice = self.__findDevice("NXSConfigServer")
        return self.__configDevice

    ## set method for configDevice attribute
    # \param name of configDevice           
    def __setConfigDevice(self, name):
        if name:
            self.__configDevice = name
        else:
            self.__configDevice = self.__findDevice("NXSConfigServer")


    ## del method for configDevice attribute
    def __delConfigDevice(self):
        del self.__configDevice 


    ## the json data string
    configDevice = property(__getConfigDevice, __setConfigDevice, __delConfigDevice, 
                       doc = 'configuration server device name')






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
        if not self.__configDevice:
            self.__getConfigDevice()
        self.__configProxy = PyTango.DeviceProxy(self.__configDevice)
        self.__configProxy.Open()
        res = getattr(self.__configProxy, command)()
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
