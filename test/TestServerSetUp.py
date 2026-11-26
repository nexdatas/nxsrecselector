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
import time

try:
    from TangoDbUtils import (
        add_device, add_server, database, delete_server)
except ImportError:
    from .TangoDbUtils import (
        add_device, add_server, database, delete_server)

try:
    import tango
except Exception:
    import PyTango as tango

try:
    import TestServer
except Exception:
    from . import TestServer


# test fixture
class TestServerSetUp(object):

    # constructor
    # \brief defines server parameters

    def __init__(self, device="ttestp09/testts/t1r228", instance="S1"):
        # information about tango writer
        self.new_device_info_writer = tango.DbDevInfo()
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
        db = database()
        add_device(self.new_device_info_writer, db)
        add_server(self.new_device_info_writer.server,
                   self.new_device_info_writer, db)
        db.put_device_property(self.new_device_info_writer.name,
                               self.device_prop)
        db.put_class_property(self.new_device_info_writer._class,
                              self.class_prop)

    # starts server
    def start(self):
        db = database()
        path = os.path.dirname(TestServer.__file__)
        if not path:
            path = '.'

        # force the python fault handler on in the server subprocess so a
        # fatal signal (e.g. segfault) prints a C-level traceback to stderr
        env = dict(os.environ, PYTHONFAULTHANDLER="1")
        self._psub = subprocess.Popen(
            "cd %s; %s ./TestServer.py %s" %
            (path, sys.executable, self.instance),
            stdout=subprocess.PIPE, stderr=subprocess.PIPE, shell=True,
            env=env)

        sys.stdout.write("waiting for simple server")

        found = False
        cnt = 0
        dvname = self.new_device_info_writer.name
        while not found and cnt < 1000:
            try:
                sys.stdout.write(".")
                sys.stdout.flush()
                exl = db.get_device_exported(dvname)
                if dvname not in exl.value_string:
                    time.sleep(0.01)
                    cnt += 1
                    continue
                self.dp = tango.DeviceProxy(dvname)
                time.sleep(0.01)
                if self.dp.state() == tango.DevState.ON:
                    found = True
            except Exception:
                found = False
            cnt += 1
        print("")
        if self._psub.poll() is not None:
            out, err = self._psub.communicate()
            print("TestServer stdout:\n%s"
                  % out.decode('utf8', errors='replace'))
            print("TestServer stderr:\n%s"
                  % err.decode('utf8', errors='replace'))
            self.dumpps()

    # dumps the TestServer processes still running, for crash diagnostics
    def dumpps(self):
        with subprocess.Popen(
                "ps -ef | grep 'TestServer.py %s' | grep -v grep" %
                self.instance,
                stdout=subprocess.PIPE, shell=True) as proc:
            out = proc.stdout.read().decode('utf8', errors='replace')
            print("TestServer ps:\n%s" % out)

    # test closer
    # \brief Common tear down of Tango Server
    def tearDown(self):
        print("tearing down ...")
        self.delete()
        self.stop()

    def delete(self):
        delete_server(self.new_device_info_writer.server)

    # stops server
    def stop(self):
        with subprocess.Popen(
                "ps -ef | grep 'TestServer.py %s' | grep -v grep" %
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
        if self._psub is not None:
            self._psub.kill()
            try:
                out, err = self._psub.communicate(timeout=5)
            except subprocess.TimeoutExpired:
                self._psub.kill()
                out, err = self._psub.communicate()
            if out:
                print("TestServer stdout:\n%s"
                      % out.decode('utf8', errors='replace'))
            if err:
                print("TestServer stderr:\n%s"
                      % err.decode('utf8', errors='replace'))


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
            self.ts[dv] = tango.DbDevInfo()
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
        db = database()

        devices = list(self.ts.values())
        for dv in devices:
            add_device(dv, db)
            # print dv.name
            db.put_device_property(dv.name, self.device_prop)
            db.put_class_property(dv._class, self.class_prop)

        if devices:
            add_server(self.server, devices, db)

    # starts server
    def start(self):
        db = database()
        path = os.path.dirname(TestServer.__file__)
        if not path:
            path = '.'

        # force the python fault handler on in the server subprocess so a
        # fatal signal (e.g. segfault) prints a C-level traceback to stderr
        env = dict(os.environ, PYTHONFAULTHANDLER="1")
        self._psub = subprocess.Popen(
            "cd %s;  %s ./TestServer.py %s" % (path, sys.executable,
                                               self.instance),
            stdout=subprocess.PIPE, stderr=subprocess.PIPE, shell=True,
            env=env)
        sys.stdout.write("waiting for simple server")

        found = False
        cnt = 0
        devices = list(self.ts.values())
        while not found and cnt < 1000:
            try:
                sys.stdout.write(".")
                sys.stdout.flush()
                dpcnt = 0
                for dv in devices:
                    exl = db.get_device_exported(dv.name)
                    if dv.name not in exl.value_string:
                        time.sleep(0.01)
                        cnt += 1
                        continue
                    self.dps[dv.name] = tango.DeviceProxy(dv.name)
                    time.sleep(0.01)
                    if self.dps[dv.name].state() == tango.DevState.ON:
                        dpcnt += 1
                if dpcnt == len(devices):
                    found = True
            except Exception:
                found = False
            cnt += 1
        print("")
        if self._psub.poll() is not None:
            out, err = self._psub.communicate()
            print("TestServer stdout:\n%s"
                  % out.decode('utf8', errors='replace'))
            print("TestServer stderr:\n%s"
                  % err.decode('utf8', errors='replace'))
            self.dumpps()

    # dumps the TestServer processes still running, for crash diagnostics
    def dumpps(self):
        with subprocess.Popen(
                "ps -ef | grep 'TestServer.py %s' | grep -v grep" %
                self.instance,
                stdout=subprocess.PIPE, shell=True) as proc:
            out = proc.stdout.read().decode('utf8', errors='replace')
            print("TestServer ps:\n%s" % out)

    # test closer
    # \brief Common tear down of Tango Server
    def tearDown(self):
        print("tearing down ...")
        self.delete()
        self.stop()

    def delete(self):
        delete_server(self.server)

    # stops server
    def stop(self):
        with subprocess.Popen(
                "ps -ef | grep 'TestServer.py %s' | grep -v grep" %
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
        if self._psub is not None:
            self._psub.kill()
            try:
                out, err = self._psub.communicate(timeout=5)
            except subprocess.TimeoutExpired:
                self._psub.kill()
                out, err = self._psub.communicate()
            if out:
                print("TestServer stdout:\n%s"
                      % out.decode('utf8', errors='replace'))
            if err:
                print("TestServer stderr:\n%s"
                      % err.decode('utf8', errors='replace'))


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
