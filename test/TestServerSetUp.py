#!/usr/bin/env python
#   This file is part of nexdatas - Tango Server for NeXus data writer
#
#    Copyright (C) 2012-2014 DESY, Jan Kotanski <jkotan@mail.desy.de>
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
## \file ServerSetUp.py
# class with server settings
#
import unittest
import os
import sys
import subprocess

import PyTango
import time
import TestServer


## test fixture
class TestServerSetUp(object):

    ## constructor
    # \brief defines server parameters
    def __init__(self, device = "ttestp09/testts/t1r228", instance = "S1"):
        ## information about tango writer
        self.new_device_info_writer = PyTango.DbDevInfo()
        ## information about tango writer class
        self.new_device_info_writer._class = "TestServer"
        ## information about tango writer server
        self.new_device_info_writer.server = "TestServer/%s" % instance
        ## information about tango writer name
        self.new_device_info_writer.name = device

        ## server instance
        self.instance = instance
        self._psub = None
        ## device proxy
        self.dp = None
        ## device properties
        self.device_prop = {
            'DeviceBoolean':False,
            'DeviceShort':12,
            'DeviceLong':1234566,
            'DeviceFloat':12.4345,
            'DeviceDouble':3.453456,
            'DeviceUShort':1,
            'DeviceULong':23234,
            'DeviceString':"My Sting"
            }

        ##  class properties
	self.class_prop = {
            'ClassBoolean':True,
            'ClassShort':1,
            'ClassLong':-123555,
            'ClassFloat':12.345,
            'ClassDouble':1.23445,
            'ClassUShort':1,
            'ClassULong':12343,
            'ClassString':"My ClassString",
            }
        

    ## test starter
    # \brief Common set up of Tango Server
    def setUp(self):
        print "\nsetting up..."
        db = PyTango.Database()
        db.add_device(self.new_device_info_writer)
        db.add_server(self.new_device_info_writer.server, self.new_device_info_writer)
        db.put_device_property(self.new_device_info_writer.name, self.device_prop)
        db.put_class_property(self.new_device_info_writer._class, self.class_prop)


        path = os.path.dirname(TestServer.__file__)
        
        if os.path.isfile("%s/ST" % path):
            self._psub = subprocess.call(
                "cd %s; ./ST %s &" % (path, self.instance ) ,stdout =  None, 
                stderr =  None,  shell= True)
        print "waiting for simple server",
        
        found = False
        cnt = 0
        while not found and cnt < 1000:
            try:
                print "\b.",
                self.dp = PyTango.DeviceProxy(self.new_device_info_writer.name)
                time.sleep(0.01)
                if self.dp.state() == PyTango.DevState.ON:
                    found = True
            except:    
                found = False
            cnt +=1
        print ""

    ## test closer
    # \brief Common tear down oif Tango Server
    def tearDown(self): 
        print "tearing down ..."
        db = PyTango.Database()
        db.delete_server(self.new_device_info_writer.server)
        
        output = ""
        pipe = subprocess.Popen(
            "ps -ef | grep 'TestServer.py %s'" % self.instance, stdout=subprocess.PIPE , shell= True).stdout

        res = pipe.read().split("\n")
        for r in res:
            sr = r.split()
            if len(sr)>2:
                 subprocess.call("kill -9 %s" % sr[1],stderr=subprocess.PIPE , shell= True)

        

if __name__ == "__main__":
    simps = TestServerSetUp()
    simps.setUp()
    print simps.dp.status()
    simps.tearDown()
