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
        
        ## Configuration Server device name
        self.configDevice = None

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

        ## NeXus Data Writer device
        self.writerDevice = None

    ## mandatory components
    def mandatoryComponents(self):
        return []
        

    ## available components
    def availableComponents(self):
        return []

    ## available datasources
    def availableDataSources(self):
        return []
