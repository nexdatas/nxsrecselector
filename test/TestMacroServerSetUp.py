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
import TestMacroServer


## test fixture
class TestMacroServerSetUp(object):

    ## constructor
    # \brief defines server parameters
    def __init__(self, instance="MSTESTS1", msdevices=None, doordevices=None):
        if not isinstance(msdevices, list):
            msdevices = ["mstestp09/testts/t1r228"]
        if not isinstance(doordevices, list):
            doordevices = ["doortestp09/testts/t1r228"]
        ## information about tango writer
        self.server = "MacroServer/%s" % instance
        self.door = {}
        self.ms = {}
        ## device proxy
        self.dps = {}
        for dv in msdevices:
            self.ms[dv] = PyTango.DbDevInfo()
            self.ms[dv]._class = "MacroServer"
            self.ms[dv].server = self.server
            self.ms[dv].name = dv

        for dv in doordevices:
            self.door[dv] = PyTango.DbDevInfo()
            self.door[dv]._class = "Door"
            self.door[dv].server = self.server
            self.door[dv].name = dv

        ## server instance
        self.instance = instance
        self._psub = None

    ## test starter
    # \brief Common set up of Tango Server
    def setUp(self):
        print "\nsetting up..."
        self.add()
        self.start()

    def add(self):
        db = PyTango.Database()
#        db.add_device(self.new_device_info_writer)
        devices = self.ms.values()
        devices.extend(self.door.values())
        for dv in devices:
            db.add_device(dv)
            print dv.name
        if devices:
            db.add_server(self.server, devices)

    ## starts server
    def start(self):
        path = os.path.dirname(TestMacroServer.__file__)
        if not path:
            path = '.'

        self._psub = subprocess.call(
            "cd %s;  python ./TestMacroServer.py %s &" % (path, self.instance),
            stdout=None, stderr=None, shell=True)
        print "waiting for simple server",

        found = False
        cnt = 0
        devices = self.ms.values()
        devices.extend(self.door.values())
        while not found and cnt < 1000:
            try:
                print "\b.",
                dpcnt = 0
                for dv in devices:
                    self.dps[dv.name] = PyTango.DeviceProxy(dv.name)
                    time.sleep(0.01)
                    if self.dps[dv.name].state() == PyTango.DevState.ON:
                        dpcnt += 1
                if dpcnt == len(devices):
                    found = True
            except Exception as e:
                found = False
            cnt += 1
        print ""

    ## test closer
    # \brief Common tear down of Tango Server
    def tearDown(self):
        print "tearing down ..."
        self.delete()
        self.stop()

    def delete(self):
        db = PyTango.Database()
        db.delete_server(self.server)

    ## stops server
    def stop(self):
        output = ""
        pipe = subprocess.Popen(
            "ps -ef | grep 'TestMacroServer.py %s'" % self.instance,
            stdout=subprocess.PIPE, shell=True).stdout

        res = pipe.read().split("\n")
        for r in res:
            sr = r.split()
            if len(sr) > 2:
                subprocess.call(
                    "kill -9 %s" % sr[1], stderr=subprocess.PIPE, shell=True)


if __name__ == "__main__":
    simps = TestMacroServerSetUp()
    simps.setUp()
#    import time
#    time.sleep(30)
    simps.tearDown()