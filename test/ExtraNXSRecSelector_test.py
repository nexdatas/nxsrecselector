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
# \file NXSRecSelector_test.py
# unittests for field Tags running Tango Server
#
import unittest
import sys
import time
import json

try:
    import tango
except Exception:
    import PyTango as tango

try:
    import ServerSetUp
except Exception:
    from . import ServerSetUp
try:
    import ExtraSettings_test
except Exception:
    from . import ExtraSettings_test

from nxsrecconfig.MacroServerPools import MacroServerPools
from nxsrecconfig.Selector import Selector
from nxsrecconfig.ProfileManager import ProfileManager
from nxsrecconfig.Utils import MSUtils


# test fixture
class ExtraNXSRecSelectorTest(ExtraSettings_test.ExtraSettingsTest):

    # constructor
    # \param methodName name of the test method

    def __init__(self, methodName):
        ExtraSettings_test.ExtraSettingsTest.__init__(self, methodName)

        self._sv = ServerSetUp.ServerSetUp()
        self._sv2 = ServerSetUp.ServerSetUp(
            device="testp09/testnrs2/testr228",
            instance="NRS2TEST")

    # test starter
    # \brief Common set up of Tango Server
    def setUp(self):
        ExtraSettings_test.ExtraSettingsTest.setUp(self)
        self._sv.setUp()

    # test starter
    # \brief Common set up of Tango Server
    def mySetUp(self):
        self._sv2.setUp()

    # test closer
    # \brief Common tear down oif Tango Server
    def tearDown(self):
        self._sv.tearDown()
        ExtraSettings_test.ExtraSettingsTest.tearDown(self)

    # test closer
    # \brief Common tear down oif Tango Server
    def myTearDown(self):
        self._sv2.tearDown()

    def value(self, rs, name):
        return json.loads(rs.profileConfiguration)[name]

    def names(self, rs):
        return list(json.loads(rs.profileConfiguration).keys())

    def setProp(self, rc, name, value):
        db = tango.Database()
        name = "" + name[0].upper() + name[1:]
        db.put_device_property(
            self._sv.new_device_info_writer.name,
            {name: value})
        rc.Init()

    # opens config server
    # \param args connection arguments
    # \returns NXSConfigServer instance
    def openRecSelector(self):

        found = False
        cnt = 0
        while not found and cnt < 1000:
            try:
                sys.stdout.write(".")
                xmlc = tango.DeviceProxy(
                    self._sv.new_device_info_writer.name)
                time.sleep(0.01)
                xmlc.set_timeout_millis(25000)
                if xmlc.state() == tango.DevState.ON:
                    found = True
                found = True
            except Exception as e:
                print("%s%s" % (self._sv.new_device_info_writer.name, e))
                found = False
            except Exception:
                found = False

            cnt += 1

        if not found:
            raise Exception(
                "Cannot connect to %s" %
                self._sv.new_device_info_writer.name)

        self.assertEqual(xmlc.state(), tango.DevState.ON)
        return xmlc

    # opens config server
    # \param args connection arguments
    # \returns NXSConfigServer instance
    def openRecSelector2(self):

        found = False
        cnt = 0
        while not found and cnt < 1000:
            try:
                sys.stdout.write(".")
                xmlc = tango.DeviceProxy(
                    self._sv2.new_device_info_writer.name)
                time.sleep(0.01)
                xmlc.set_timeout_millis(25000)
                if xmlc.state() == tango.DevState.ON:
                    found = True
                found = True
            except Exception as e:
                print("%s%s" % (self._sv2.new_device_info_writer.name, e))
                found = False
            except Exception:
                found = False

            cnt += 1

        if not found:
            raise Exception(
                "Cannot connect to %s" %
                self._sv2.new_device_info_writer.name)

        self.assertEqual(xmlc.state(), tango.DevState.ON)
        return xmlc

    def subtest_constructor(self):
        rs = self.openRecSelector()
        msp = MacroServerPools(10)
        se = Selector(msp, self.version)
        se["Door"] = rs.door
        se["ConfigDevice"] = rs.configDevice
        pm = ProfileManager(se)
        amgs = pm.availableMntGrps()
        # print "AMGs", amgs
        cf = tango.DeviceProxy(rs.configDevice)
        # print "AvSels", cf.availableSelections()
        # print "AMGs", amgs
        amntgrp = MSUtils.getEnv('ActiveMntGrp', msp.getMacroServer(rs.door))
        if amntgrp in pm.availableMntGrps():
            self.assertEqual(rs.mntGrp, amntgrp)
        elif cf.availableSelections():
            self.assertEqual(rs.mntGrp, cf.availableSelections()[0])
        elif amgs:
            self.assertEqual('', amntgrp)
        else:
            self.assertEqual('nxsmntgrp', amntgrp)

        # print "MntGrp", rs.mntGrp
        # memorize attirbutes
        # print "ConfigDevice", rs.configDevice
        # print "Door", rs.door
        # print "DeviceGroups", rs.deviceGroups

    def switchProfile(self, rs, flag):
        if flag:
            rs.switchProfile()
        else:
            mg = rs.mntGrp
            MSUtils.setEnv('ActiveMntGrp', mg, list(self._ms.ms.keys())[0])
            rs.switchProfile()

    def subtest_switchProfile_importMntGrp(self):
        pass


if __name__ == '__main__':
    unittest.main()
