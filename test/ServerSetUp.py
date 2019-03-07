#!/usr/bin/env python
#   This file is part of nexdatas - Tango Server for NeXus data writer
#
#    Copyright (C) 2012-2017 DESY, Jan Kotanski <jkotan@mail.desy.de>
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


# test fixture
class ServerSetUp(object):

    # constructor
    # \brief defines server parameters

    def __init__(self, device="testp09/testnrs/testr228", instance="NRSTEST"):
        # information about tango writer
        self.new_device_info_writer = PyTango.DbDevInfo()
        self.new_device_info_writer._class = "NXSRecSelector"
        self.new_device_info_writer.server = "NXSRecSelector/%s" % instance
        self.new_device_info_writer.name = device
        # server instance
        self.instance = instance

        self._psub = None

    # test starter
    # \brief Common set up of Tango Server
    def setUp(self):
        print("tearing down ...")
        db = PyTango.Database()
        db.add_device(self.new_device_info_writer)
        db.add_server(self.new_device_info_writer.server,
                      self.new_device_info_writer)

        if sys.version_info > (3,):
            if os.path.isfile("../NXSRecSelector"):
                self._psub = subprocess.call(
                    "cd ..; python3 ./NXSRecSelector %s &" % self.instance,
                    stdout=None,
                    stderr=None, shell=True)
            else:
                self._psub = subprocess.call(
                    "python3 NXSRecSelector %s &" % self.instance, stdout=None,
                    stderr=None, shell=True)
        else:
            if os.path.isfile("../NXSRecSelector"):
                self._psub = subprocess.call(
                    "cd ..; ./NXSRecSelector %s &" % self.instance,
                    stdout=None,
                    stderr=None, shell=True)
            else:
                self._psub = subprocess.call(
                    "NXSRecSelector %s &" % self.instance, stdout=None,
                    stderr=None, shell=True)
        sys.stdout.write("waiting for server ")

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
                dp = PyTango.DeviceProxy(dvname)
                time.sleep(0.01)
                if dp.state() == PyTango.DevState.ON:
                    found = True
                found = True
            except Exception:
                found = False
            cnt += 1
        print("")

    # test closer
    # \brief Common tear down oif Tango Server
    def tearDown(self):
        print("tearing down ...")
        db = PyTango.Database()
        db.delete_server(self.new_device_info_writer.server)

        if sys.version_info > (3,):
            with subprocess.Popen(
                    "ps -ef | grep 'NXSRecSelector %s' | grep -v grep" %
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
                "ps -ef | grep 'NXSRecSelector %s' | grep -v grep" %
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
