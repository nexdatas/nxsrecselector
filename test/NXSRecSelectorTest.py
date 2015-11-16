#!/usr/bin/env python
#   This file is part of nexdatas - Tango Server for NeXus data writer
#
#    Copyright (C) 2012-2015 DESY, Jan Kotanski <jkotan@mail.desy.de>
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
## \package test nexdatas
## \file NXSRecSelectorTest.py
# unittests for field Tags running Tango Server
#
import unittest
import os
import sys
import subprocess
import random
import time
import PyTango

import ServerSetUp
import SettingsTest
from nxsrecconfig import Settings
import nxsrecconfig
## test fixture
class NXSRecSelectorTest(SettingsTest.SettingsTest):

    ## constructor
    # \param methodName name of the test method
    def __init__(self, methodName):
        SettingsTest.SettingsTest.__init__(self, methodName)

        self._sv = ServerSetUp.ServerSetUp()



    ## test starter
    # \brief Common set up of Tango Server
    def setUp(self):
        SettingsTest.SettingsTest.setUp(self)
        self._sv.setUp()

    ## test closer
    # \brief Common tear down oif Tango Server
    def tearDown(self): 
        self._sv.tearDown()
        SettingsTest.SettingsTest.tearDown(self)
        
    ## opens config server
    # \param args connection arguments
    # \returns NXSConfigServer instance   
    def openRecSelector(self):
        
        found = False
        cnt = 0
        while not found and cnt < 1000:
            try:
                print "\b.",
                xmlc = PyTango.DeviceProxy(self._sv.new_device_info_writer.name)
                time.sleep(0.01)
                if xmlc.state() == PyTango.DevState.ON:
                    found = True
                found = True
            except Exception,e:    
                print self._sv.new_device_info_writer.name,e
                found = False
            except:
                found = False
                
            cnt +=1

        if not found:
            raise Exception, "Cannot connect to %s" % self._sv.new_device_info_writer.name


        self.assertEqual(xmlc.state(), PyTango.DevState.ON)
        
        return xmlc
        



if __name__ == '__main__':
    unittest.main()

