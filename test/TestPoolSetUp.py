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
    import TestPool
except Exception:
    from . import TestPool


# test fixture
class TestPoolSetUp(object):

    # constructor
    # \brief defines server parameters

    def __init__(self, device="pooltestp09/testts/t1r228",
                 instance="POOLTESTS1"):
        # information about tango writer
        self.new_device_info_writer = PyTango.DbDevInfo()
        # information about tango writer class
        self.new_device_info_writer._class = "Pool"
        # information about tango writer server
        self.new_device_info_writer.server = "Pool/%s" % instance
        # information about tango writer name
        self.new_device_info_writer.name = device

        # server instance
        self.instance = instance
        self._psub = None
        # device proxy
        self.dp = None
        # device properties

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

    # starts server
    def start(self):
        path = os.path.dirname(TestPool.__file__)
        if not path:
            path = '.'

        if sys.version_info > (3,):
            self._psub = subprocess.call(
                "cd %s;  python3 ./TestPool.py %s &" %
                (path, self.instance),
                stdout=None,
                stderr=None, shell=True)
        else:
            self._psub = subprocess.call(
                "cd %s;  python ./TestPool.py %s &" %
                (path, self.instance),
                stdout=None,
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
        if sys.version_info > (3,):
            with subprocess.Popen(
                    "ps -ef | grep 'TestPool.py %s' | grep -v grep" %
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
                "ps -ef | grep 'TestPool.py %s' | grep -v grep" %
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
    simps = TestPoolSetUp()
    simps.setUp()
    print(simps.dp.status())
    simps.tearDown()
