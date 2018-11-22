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
try:
    import TestMacroServer
except Exception:
    from . import TestMacroServer


# test fixture
class TestMacroServerSetUp(object):

    # constructor
    # \brief defines server parameters

    def __init__(self, instance="MSTESTS1", msdevices=None, doordevices=None,
                 python=None):
        if not isinstance(msdevices, list):
            msdevices = ["mstestp09/testts/t1r228"]
        if not isinstance(doordevices, list):
            doordevices = ["doortestp09/testts/t1r228"]
        # information about tango writer
        self.server = "MacroServer/%s" % instance
        self.python = python
        self.door = {}
        self.ms = {}
        # device proxy
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

        # server instance
        self.instance = instance
        self._psub = None

    # test starter
    # \brief Common set up of Tango Server
    def setUp(self):
        print("\nsetting up...")
        self.add()
        self.start()

    def add(self):
        db = PyTango.Database()
#        db.add_device(self.new_device_info_writer)
        devices = list(self.ms.values())
        devices.extend(list(self.door.values()))
        for dv in devices:
            db.add_device(dv)
            print(dv.name)
        if devices:
            db.add_server(self.server, devices)

    # starts server
    def start(self):
        path = os.path.dirname(TestMacroServer.__file__)
        if not path:
            path = '.'

        if (sys.version_info > (3,) and self.python is None) or \
           self.python == 3:
            self._psub = subprocess.call(
                "cd %s;  python3 ./TestMacroServer.py %s &" %
                (path, self.instance),
                stdout=None, stderr=None, shell=True)
        else:
            self._psub = subprocess.call(
                "cd %s;  python2 ./TestMacroServer.py %s &" %
                (path, self.instance),
                stdout=None, stderr=None, shell=True)
        sys.stdout.write("waiting for simple server")

        found = False
        cnt = 0
        devices = list(self.ms.values())
        devices.extend(list(self.door.values()))
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
        if sys.version_info > (3,):
            with subprocess.Popen(
                    "ps -ef | grep 'TestMacroServer.py %s' | grep -v grep" %
                    self.instance,
                    stdout=subprocess.PIPE, shell=True) as proc:
                pipe = proc.stdout
                res = str(pipe.read(), "utf8").split("\n")
                for r in res:
                    sr = r.split()
                    if len(sr) > 2:
                        subprocess.call(
                            "kill -9 %s" % sr[1], stderr=subprocess.PIPE,
                            shell=True)
                pipe.close()
        else:
            pipe = subprocess.Popen(
                "ps -ef | grep 'TestMacroServer.py %s' | grep -v grep" %
                self.instance,
                stdout=subprocess.PIPE, shell=True).stdout
            res = str(pipe.read()).split("\n")
            for r in res:
                sr = r.split()
                if len(sr) > 2:
                    subprocess.call(
                        "kill -9 %s" % sr[1], stderr=subprocess.PIPE,
                        shell=True)
            pipe.close()


if __name__ == "__main__":
    simps = TestMacroServerSetUp()
    simps.setUp()
#    import time
#    time.sleep(30)
    simps.tearDown()
