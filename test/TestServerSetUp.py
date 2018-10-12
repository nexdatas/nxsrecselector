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
# \package test nexdatas
# \file ServerSetUp.py
# class with server settings
#
import os
import sys
import subprocess

import PyTango
import time
import TestServer


# test fixture
class TestServerSetUp(object):

    # constructor
    # \brief defines server parameters

    def __init__(self, device="ttestp09/testts/t1r228", instance="S1"):
        # information about tango writer
        self.new_device_info_writer = PyTango.DbDevInfo()
        # information about tango writer class
        self.new_device_info_writer._class = "TestServer"
        # information about tango writer server
        self.new_device_info_writer.server = "TestServer/%s" % instance
        # information about tango writer name
        self.new_device_info_writer.name = device

        # server instance
        self.instance = instance
        self._psub = None
        # device proxy
        self.dp = None
        # device properties
        self.device_prop = {
            'DeviceBoolean': False,
            'DeviceShort': 12,
            'DeviceLong': 1234566,
            'DeviceFloat': 12.4345,
            'DeviceDouble': 3.453456,
            'DeviceUShort': 1,
            'DeviceULong': 23234,
            'DeviceString': "My Sting"
        }

        # class properties
        self.class_prop = {
            'ClassBoolean': True,
            'ClassShort': 1,
            'ClassLong': -123555,
            'ClassFloat': 12.345,
            'ClassDouble': 1.23445,
            'ClassUShort': 1,
            'ClassULong': 12343,
            'ClassString': "My ClassString",
        }

    # test starter
    # \brief Common set up of Tango Server
    def setUp(self):
        print("\nsetting up...")
        self.add()
        self.start()

    def add(self):
        db = PyTango.Database()
        db.add_device(self.new_device_info_writer)
        db.add_server(self.new_device_info_writer.server,
                      self.new_device_info_writer)
        db.put_device_property(self.new_device_info_writer.name,
                               self.device_prop)
        db.put_class_property(self.new_device_info_writer._class,
                              self.class_prop)

    # starts server
    def start(self):
        path = os.path.dirname(TestServer.__file__)
        if not path:
            path = '.'

        if os.path.isfile("%s/ST" % path):
            if sys.version_info > (3,):
                self._psub = subprocess.call(
                    "cd %s; python3 ./TestServer.py %s &" %
                    (path, self.instance), stdout=None,
                    stderr=None, shell=True)
            else:
                self._psub = subprocess.call(
                    "cd %s; python ./TestServer.py %s &" %
                    (path, self.instance), stdout=None,
                    stderr=None, shell=True)

        sys.stdout.write("waiting for simple server")

        found = False
        cnt = 0
        while not found and cnt < 1000:
            try:
                sys.stdout.write(".")
                self.dp = PyTango.DeviceProxy(self.new_device_info_writer.name)
                time.sleep(0.01)
                if self.dp.state() == PyTango.DevState.ON:
                    found = True
            except Exception:
                found = False
            cnt += 1
        print("")

    # test closer
    # \brief Common tear down of Tango Server
    def tearDown(self):
        print("tearing down ...")
        self.delete()
        self.stop()

    def delete(self):
        db = PyTango.Database()
        db.delete_server(self.new_device_info_writer.server)

    # stops server
    def stop(self):
        pipe = subprocess.Popen(
            "ps -ef | grep 'TestServer.py %s'" % self.instance,
            stdout=subprocess.PIPE, shell=True).stdout

        res = str(pipe.read()).split("\n")
        for r in res:
            sr = r.split()
            if len(sr) > 2:
                subprocess.call(
                    "kill -9 %s" % sr[1], stderr=subprocess.PIPE, shell=True)
        pipe.close()


# test fixture
class MultiTestServerSetUp(object):

    # constructor
    # \brief defines server parameters

    def __init__(self, instance="MTS01", devices=None):
        if not isinstance(devices, list):
            devices = ["ttestp09/testts/mt1r228"]

        # information about tango writer
        self.server = "TestServer/%s" % instance
        self.ts = {}
        # device proxy
        self.dps = {}
        for dv in devices:
            self.ts[dv] = PyTango.DbDevInfo()
            self.ts[dv]._class = "TestServer"
            self.ts[dv].server = self.server
            self.ts[dv].name = dv

        # server instance
        self.instance = instance
        self._psub = None

        # device properties
        self.device_prop = {
            'DeviceBoolean': False,
            'DeviceShort': 12,
            'DeviceLong': 1234566,
            'DeviceFloat': 12.4345,
            'DeviceDouble': 3.453456,
            'DeviceUShort': 1,
            'DeviceULong': 23234,
            'DeviceString': "My Sting"
        }

        # class properties
        self.class_prop = {
            'ClassBoolean': True,
            'ClassShort': 1,
            'ClassLong': -123555,
            'ClassFloat': 12.345,
            'ClassDouble': 1.23445,
            'ClassUShort': 1,
            'ClassULong': 12343,
            'ClassString': "My ClassString",
        }

    # test starter
    # \brief Common set up of Tango Server
    def setUp(self):
        print("\nsetting up...")
        self.add()
        self.start()

    def add(self):
        db = PyTango.Database()

        devices = list(self.ts.values())
        for dv in devices:
            db.add_device(dv)
            # print dv.name
            db.put_device_property(dv.name, self.device_prop)
            db.put_class_property(dv._class, self.class_prop)

        if devices:
            db.add_server(self.server, devices)

    # starts server
    def start(self):
        path = os.path.dirname(TestServer.__file__)
        if not path:
            path = '.'

        if sys.version_info > (3,):
            self._psub = subprocess.call(
                "cd %s;  python3 ./TestServer.py %s &" % (path, self.instance),
                stdout=None, stderr=None, shell=True)
        else:
            self._psub = subprocess.call(
                "cd %s;  python ./TestServer.py %s &" % (path, self.instance),
                stdout=None, stderr=None, shell=True)
        sys.stdout.write("waiting for simple server")

        found = False
        cnt = 0
        devices = list(self.ts.values())
        while not found and cnt < 1000:
            try:
                sys.stdout.write(".")
                dpcnt = 0
                for dv in devices:
                    self.dps[dv.name] = PyTango.DeviceProxy(dv.name)
                    time.sleep(0.01)
                    if self.dps[dv.name].state() == PyTango.DevState.ON:
                        dpcnt += 1
                if dpcnt == len(devices):
                    found = True
            except Exception:
                found = False
            cnt += 1
        print("")

    # test closer
    # \brief Common tear down of Tango Server
    def tearDown(self):
        print("tearing down ...")
        self.delete()
        self.stop()

    def delete(self):
        db = PyTango.Database()
        db.delete_server(self.server)

    # stops server
    def stop(self):
        pipe = subprocess.Popen(
            "ps -ef | grep 'TestServer.py %s'" % self.instance,
            stdout=subprocess.PIPE, shell=True).stdout

        res = str(pipe.read()).split("\n")
        for r in res:
            sr = r.split()
            if len(sr) > 2:
                subprocess.call(
                    "kill -9 %s" % sr[1], stderr=subprocess.PIPE, shell=True)
        pipe.close()


if __name__ == "__main__":
    simps = TestServerSetUp()
    simps.setUp()
    print(simps.dp.status())
    simps.tearDown()
    simps = MultiTestServerSetUp()
    simps.setUp()
    for dp in simps.dps.values():
        print(dp.status())
    simps.tearDown()
    simps = MultiTestServerSetUp(devices=[
        "tm2/dd/sr", "dsf/44/fgg", "sdffd/sdfsd/sfd"])
    simps.setUp()
    for dp in simps.dps.values():
        print(dp.status())
    simps.tearDown()
