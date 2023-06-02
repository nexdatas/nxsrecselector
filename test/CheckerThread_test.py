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
# \file CheckerThreadTest.py
# unittests for TangoDsItemTest running Tango Server
#
import unittest
import os
import sys
import time
import random
import struct
import threading
import binascii

try:
    import tango
except Exception:
    import PyTango as tango

try:
    import TestServerSetUp
except Exception:
    from . import TestServerSetUp

from nxsrecconfig.CheckerThread import (
    CheckerThread, CheckerItem, TangoDSItem, ATTRIBUTESTOCHECK)

if sys.version_info > (3,):
    import queue as Queue
else:
    import Queue


# if 64-bit machione
IS64BIT = (struct.calcsize("P") == 8)

if sys.version_info > (3,):
    long = int


# test fixture
class CheckerItemTest(unittest.TestCase):

    # constructor
    # \param methodName name of the test method

    def __init__(self, methodName):
        unittest.TestCase.__init__(self, methodName)

        self._bint = "int64" if IS64BIT else "int32"
        self._buint = "uint64" if IS64BIT else "uint32"
        self._bfloat = "float64" if IS64BIT else "float32"

        self._simps = TestServerSetUp.TestServerSetUp()
        self._simps2 = TestServerSetUp.TestServerSetUp(
            "ttestp09/testts/t2r228", "S2")
        self._simps3 = TestServerSetUp.TestServerSetUp(
            "ttestp09/testts/t3r228", "S3")
        self._simps4 = TestServerSetUp.TestServerSetUp(
            "ttestp09/testts/t4r228", "S4")
        self._simpsoff = TestServerSetUp.TestServerSetUp(
            "ttestp09/testts/t5r228", "OFF")

        try:
            self.__seed = long(binascii.hexlify(os.urandom(16)), 16)
        except NotImplementedError:
            self.__seed = long(time.time() * 256)

        self.__rnd = random.Random(self.__seed)

    # test starter
    # \brief Common set up
    def setUp(self):
        print("SEED = %s" % self.__seed)
        self._simps.setUp()
        self._simps2.setUp()
        self._simps3.setUp()
        self._simps4.setUp()
        self._simpsoff.add()
        print("\nsetting up...")

    # test closer
    # \brief Common tear down
    def tearDown(self):
        print("tearing down ...")
        self._simpsoff.delete()
        self._simps4.tearDown()
        self._simps3.tearDown()
        self._simps2.tearDown()
        self._simps.tearDown()

    # constructor test
    # \brief It tests default settings
    def test_constructor(self):
        fun = sys._getframe().f_code.co_name
        print("Run: %s.%s() " % (self.__class__.__name__, fun))
        el = CheckerThread(None, None)
        self.assertTrue(isinstance(el, threading.Thread))
        self.assertEqual(el.index, None)
        el = CheckerThread(45, None)
        self.assertTrue(isinstance(el, threading.Thread))
        self.assertEqual(el.index, 45)
        idn = self.__rnd.randint(1, 1231233)

        cqueue = Queue.Queue()
        el = CheckerThread(idn, cqueue)
        self.assertTrue(isinstance(el, threading.Thread))
        self.assertEqual(el.index, idn)

    # constructor test
    # \brief It tests default settings
    def test_run(self):
        fun = sys._getframe().f_code.co_name
        print("Run: %s.%s() " % (self.__class__.__name__, fun))
        idn = self.__rnd.randint(1, 1231233)
        cqueue = Queue.Queue()
        self.assertTrue(cqueue.empty())
        el = CheckerThread(idn, cqueue)
        self.assertEqual(el.index, idn)
        el.run()
        self.assertTrue(cqueue.empty())

        ci0 = CheckerItem("cp0")
        ci0.append(TangoDSItem("ds0", None, None))
        cqueue.put(ci0)

        ci1 = CheckerItem("cp1")
        ci1.append(TangoDSItem("ds1", "wrongsdfgdfg", None))
        cqueue.put(ci1)

        ci2 = CheckerItem("cp2")
        ci2.append(TangoDSItem("ds2", self._simps3.new_device_info_writer.name,
                               None))
        cqueue.put(ci2)

        ci3 = CheckerItem("cp3")
        ci3.append(TangoDSItem("ds3", self._simps3.new_device_info_writer.name,
                               'ScalarDouble'))
        ci3.append(TangoDSItem("ds4", self._simps3.new_device_info_writer.name,
                               'ScalarLong'))
        ci3.append(TangoDSItem("ds5", self._simps3.new_device_info_writer.name,
                               'ScalarShort'))
        ci3.append(TangoDSItem("ds6", self._simps3.new_device_info_writer.name,
                               'ScalarBoolean'))
        cqueue.put(ci3)

        ci4 = CheckerItem("cp4")
        ci4.append(TangoDSItem("ds3", self._simps3.new_device_info_writer.name,
                               'ScalarDouble'))
        ci4.append(TangoDSItem("ds4", self._simps3.new_device_info_writer.name,
                               'ScalarDoubleddd'))
        cqueue.put(ci4)

        ci5 = CheckerItem("cp5")
        dp = tango.DeviceProxy(self._simps4.new_device_info_writer.name)
        dp.SetState("ALARM")
        ci5.append(TangoDSItem("ds3", self._simps4.new_device_info_writer.name,
                               'ScalarDouble'))
        ci5.append(TangoDSItem("ds4", self._simps4.new_device_info_writer.name,
                               'ScalarShort'))
        cqueue.put(ci5)

        ci6 = CheckerItem("cp6")
        dp = tango.DeviceProxy(self._simps4.new_device_info_writer.name)
        dp.CreateAttribute("Position")
        ci6.append(TangoDSItem("ds3", self._simps4.new_device_info_writer.name,
                               None))
        ci6.append(TangoDSItem("ds4", self._simps4.new_device_info_writer.name,
                               'ScalarShort'))
        cqueue.put(ci6)

        ci7 = CheckerItem("cp6")
        dp = tango.DeviceProxy(self._simps.new_device_info_writer.name)
        dp.CreateAttribute("Position")
        ci7.append(TangoDSItem("ds3", self._simps.new_device_info_writer.name,
                               None))
        ci7.append(TangoDSItem("ds4", self._simps.new_device_info_writer.name,
                               'ScalarShort'))
        cqueue.put(ci7)

        ci8 = CheckerItem("cp8")
        dp = tango.DeviceProxy(self._simps2.new_device_info_writer.name)
        dp.SetState("FAULT")
        ci8.append(TangoDSItem("ds3", self._simps2.new_device_info_writer.name,
                               'ScalarDouble'))
        ci8.append(TangoDSItem("ds4", self._simps2.new_device_info_writer.name,
                               'ScalarShort'))
        cqueue.put(ci8)

        ci9 = CheckerItem("cp9")
        ci9.append(TangoDSItem(
            "ds3", self._simpsoff.new_device_info_writer.name,
            'ScalarDouble'))
        ci9.append(TangoDSItem(
            "ds4", self._simpsoff.new_device_info_writer.name,
            'ScalarShort'))
        cqueue.put(ci9)

        el.run()

        self.assertTrue(ci0.message is not None)
        self.assertEqual(ci0.errords.split(" ")[0], 'ds0')
        self.assertTrue(not ci0.active)
        self.assertTrue(ci1.message is not None)
        self.assertEqual(ci1.errords.split(" ")[0], 'ds1')
        self.assertTrue(not ci1.active)
        self.assertEqual(ci2.errords, None)
        self.assertEqual(ci2.message, None)
        self.assertTrue(ci2.active)
        self.assertEqual(ci3.errords, None)
        self.assertEqual(ci3.message, None)
        self.assertTrue(ci3.active)
        self.assertEqual(ci4.errords.split(" ")[0], "ds4")
        self.assertEqual(ci4.message, 'Empty Attribute')
        self.assertTrue(not ci4.active)
        self.assertEqual(ci5.errords.split(" ")[0], "ds4")
        self.assertEqual(ci5.message, 'ALARM STATE')
        self.assertTrue(ci5.active)
        self.assertEqual(ci6.errords.split(" ")[0], "ds4")
        self.assertEqual(ci6.message, 'ALARM STATE')
        self.assertTrue(ci6.active)
        self.assertEqual(ci7.errords, None)
        self.assertEqual(ci7.message, None)
        self.assertTrue(ci7.active, None)
        self.assertEqual(ci8.errords.split(" ")[0], "ds3")
        self.assertEqual(ci8.message, 'FAULT STATE')
        self.assertTrue(not ci8.active)
        self.assertEqual(ci9.errords.split(" ")[0], "ds3")
        self.assertTrue(ci9.message is not None)
        self.assertTrue(not ci9.active)

    # constructor test
    # \brief It tests default settings
    def test_run_off(self):
        fun = sys._getframe().f_code.co_name
        print("Run: %s.%s() " % (self.__class__.__name__, fun))
        idn = self.__rnd.randint(1, 1231233)
        cqueue = Queue.Queue()
        self.assertTrue(cqueue.empty())
        el = CheckerThread(idn, cqueue)
        self.assertEqual(el.index, idn)
        el.run()
        self.assertTrue(cqueue.empty())

        ci0 = CheckerItem("cp0")
        ci0.append(TangoDSItem("ds0", None, None))
        cqueue.put(ci0)

        ci1 = CheckerItem("cp1")
        ci1.append(TangoDSItem("ds1", "wrongsdfgdfg", None))
        cqueue.put(ci1)

        ci2 = CheckerItem("cp2")
        ci2.append(TangoDSItem("ds2", self._simps3.new_device_info_writer.name,
                               None))
        cqueue.put(ci2)

        ci3 = CheckerItem("cp3")
        ci3.append(TangoDSItem("ds3", self._simps3.new_device_info_writer.name,
                               'ScalarDouble'))
        ci3.append(TangoDSItem("ds4", self._simps3.new_device_info_writer.name,
                               'ScalarLong'))
        ci3.append(TangoDSItem("ds5", self._simps3.new_device_info_writer.name,
                               'ScalarShort'))
        ci3.append(TangoDSItem("ds6", self._simps3.new_device_info_writer.name,
                               'ScalarBoolean'))
        cqueue.put(ci3)

        ci4 = CheckerItem("cp4")
        ci4.append(TangoDSItem("ds3", self._simps3.new_device_info_writer.name,
                               'ScalarDouble'))
        ci4.append(TangoDSItem("ds4", self._simps3.new_device_info_writer.name,
                               'ScalarDoubleddd'))
        cqueue.put(ci4)

        ci5 = CheckerItem("cp5")
        dp = tango.DeviceProxy(self._simps4.new_device_info_writer.name)
        dp.SetState("ALARM")
        ci5.append(TangoDSItem("ds3", self._simps4.new_device_info_writer.name,
                               'ScalarDouble'))
        ci5.append(TangoDSItem("ds4", self._simps4.new_device_info_writer.name,
                               'ScalarShort'))
        cqueue.put(ci5)

        ci6 = CheckerItem("cp6")
        dp = tango.DeviceProxy(self._simps4.new_device_info_writer.name)
        dp.CreateAttribute("Position")
        ci6.append(TangoDSItem("ds3", self._simps4.new_device_info_writer.name,
                               None))
        ci6.append(TangoDSItem("ds4", self._simps4.new_device_info_writer.name,
                               'ScalarShort'))
        cqueue.put(ci6)

        ci7 = CheckerItem("cp6")
        dp = tango.DeviceProxy(self._simps.new_device_info_writer.name)
        dp.CreateAttribute("Position")
        ci7.append(TangoDSItem("ds3", self._simps.new_device_info_writer.name,
                               None))
        ci7.append(TangoDSItem("ds4", self._simps.new_device_info_writer.name,
                               'ScalarShort'))
        cqueue.put(ci7)

        ci8 = CheckerItem("cp8")
        dp = tango.DeviceProxy(self._simps2.new_device_info_writer.name)
        dp.SetState("OFF")
        ci8.append(TangoDSItem("ds3", self._simps2.new_device_info_writer.name,
                               'ScalarDouble'))
        ci8.append(TangoDSItem("ds4", self._simps2.new_device_info_writer.name,
                               'ScalarShort'))
        cqueue.put(ci8)

        ci9 = CheckerItem("cp9")
        ci9.append(TangoDSItem(
            "ds3", self._simpsoff.new_device_info_writer.name,
            'ScalarDouble'))
        ci9.append(TangoDSItem(
            "ds4", self._simpsoff.new_device_info_writer.name,
            'ScalarShort'))
        cqueue.put(ci9)

        el.run()

        self.assertTrue(ci0.message is not None)
        self.assertEqual(ci0.errords.split(" ")[0], 'ds0')
        self.assertTrue(not ci0.active)
        self.assertTrue(ci1.message is not None)
        self.assertEqual(ci1.errords.split(" ")[0], 'ds1')
        self.assertTrue(not ci1.active)
        self.assertEqual(ci2.errords, None)
        self.assertEqual(ci2.message, None)
        self.assertTrue(ci2.active)
        self.assertEqual(ci3.errords, None)
        self.assertEqual(ci3.message, None)
        self.assertTrue(ci3.active)
        self.assertEqual(ci4.errords.split(" ")[0], "ds4")
        self.assertEqual(ci4.message, 'Empty Attribute')
        self.assertTrue(not ci4.active)
        self.assertEqual(ci5.errords.split(" ")[0], "ds4")
        self.assertEqual(ci5.message, 'ALARM STATE')
        self.assertTrue(ci5.active)
        self.assertEqual(ci6.errords.split(" ")[0], "ds4")
        self.assertEqual(ci6.message, 'ALARM STATE')
        self.assertTrue(ci6.active)
        self.assertEqual(ci7.errords, None)
        self.assertEqual(ci7.message, None)
        self.assertTrue(ci7.active, None)
        self.assertEqual(ci8.errords.split(" ")[0], "ds3")
        self.assertEqual(ci8.message, 'OFF STATE')
        self.assertTrue(not ci8.active)
        self.assertEqual(ci9.errords.split(" ")[0], "ds3")
        self.assertTrue(ci9.message is not None)
        self.assertTrue(not ci9.active)

    # constructor test
    # \brief It tests default settings
    def test_run_user_change(self):
        fun = sys._getframe().f_code.co_name
        print("Run: %s.%s() " % (self.__class__.__name__, fun))
        idn = self.__rnd.randint(1, 1231233)
        cqueue = Queue.Queue()
        self.assertTrue(cqueue.empty())
        el = CheckerThread(idn, cqueue)
        el.tangoSourceOffStates = ["ALARM"]
        el.tangoSourceAlarmStates = ["FAULT"]
        el.tangoSourceFaultStates = ["OFF"]
        self.assertEqual(el.index, idn)
        el.run()
        self.assertTrue(cqueue.empty())

        ci0 = CheckerItem("cp0")
        ci0.append(TangoDSItem("ds0", None, None))
        cqueue.put(ci0)

        ci1 = CheckerItem("cp1")
        ci1.append(TangoDSItem("ds1", "wrongsdfgdfg", None))
        cqueue.put(ci1)

        dp = tango.DeviceProxy(self._simps3.new_device_info_writer.name)
        ci2 = CheckerItem("cp2")
        ci2.append(TangoDSItem("ds2", self._simps3.new_device_info_writer.name,
                               None))
        cqueue.put(ci2)

        ci3 = CheckerItem("cp3")
        dp.SetState("FAULT")
        ci3.append(TangoDSItem("ds3", self._simps3.new_device_info_writer.name,
                               'ScalarDouble'))
        ci3.append(TangoDSItem("ds4", self._simps3.new_device_info_writer.name,
                               'ScalarLong'))
        ci3.append(TangoDSItem("ds5", self._simps3.new_device_info_writer.name,
                               'ScalarShort'))
        ci3.append(TangoDSItem("ds6", self._simps3.new_device_info_writer.name,
                               'ScalarBoolean'))
        cqueue.put(ci3)

        ci4 = CheckerItem("cp4")
        ci4.append(TangoDSItem("ds3", self._simps3.new_device_info_writer.name,
                               'ScalarDouble'))
        ci4.append(TangoDSItem("ds4", self._simps3.new_device_info_writer.name,
                               'ScalarDoubleddd'))
        cqueue.put(ci4)

        ci5 = CheckerItem("cp5")
        dp = tango.DeviceProxy(self._simps4.new_device_info_writer.name)
        dp.SetState("ALARM")
        ci5.append(TangoDSItem("ds3", self._simps4.new_device_info_writer.name,
                               'ScalarDouble'))
        ci5.append(TangoDSItem("ds4", self._simps4.new_device_info_writer.name,
                               'ScalarShort'))
        cqueue.put(ci5)

        ci6 = CheckerItem("cp6")
        dp.CreateAttribute("Position")
        ci6.append(TangoDSItem("ds3", self._simps4.new_device_info_writer.name,
                               None))
        ci6.append(TangoDSItem("ds4", self._simps4.new_device_info_writer.name,
                               'ScalarShort'))
        cqueue.put(ci6)

        ci7 = CheckerItem("cp6")
        dp = tango.DeviceProxy(self._simps.new_device_info_writer.name)
        dp.CreateAttribute("Position")
        ci7.append(TangoDSItem("ds3", self._simps.new_device_info_writer.name,
                               None))
        ci7.append(TangoDSItem("ds4", self._simps.new_device_info_writer.name,
                               'ScalarShort'))
        cqueue.put(ci7)

        ci8 = CheckerItem("cp8")
        dp = tango.DeviceProxy(self._simps2.new_device_info_writer.name)
        dp.SetState("OFF")
        ci8.append(TangoDSItem("ds3", self._simps2.new_device_info_writer.name,
                               'ScalarDouble'))
        ci8.append(TangoDSItem("ds4", self._simps2.new_device_info_writer.name,
                               'ScalarShort'))
        cqueue.put(ci8)

        ci9 = CheckerItem("cp9")
        ci9.append(TangoDSItem(
            "ds3", self._simpsoff.new_device_info_writer.name,
            'ScalarDouble'))
        ci9.append(TangoDSItem(
            "ds4", self._simpsoff.new_device_info_writer.name,
            'ScalarShort'))
        cqueue.put(ci9)

        el.run()

        self.assertTrue(ci0.message is not None)
        self.assertEqual(ci0.errords.split(" ")[0], 'ds0')
        self.assertTrue(not ci0.active)
        self.assertTrue(ci1.message is not None)
        self.assertEqual(ci1.errords.split(" ")[0], 'ds1')
        self.assertTrue(not ci1.active)
        self.assertEqual(ci2.errords.split(" ")[0], 'ds2')
        self.assertEqual(ci2.message, "FAULT STATE")
        self.assertTrue(ci2.active)
        self.assertEqual(ci3.errords.split(" ")[0], 'ds6')
        self.assertEqual(ci3.message, "FAULT STATE")
        self.assertTrue(ci3.active)
        self.assertEqual(ci4.errords.split(" ")[0], "ds4")
        self.assertEqual(ci4.message, 'Empty Attribute')
        self.assertTrue(not ci4.active)
        self.assertEqual(ci5.errords.split(" ")[0], "ds3")
        self.assertEqual(ci5.message, 'ALARM STATE')
        self.assertTrue(not ci5.active)
        self.assertEqual(ci6.errords.split(" ")[0], "ds3")
        self.assertEqual(ci6.message, 'ALARM STATE')
        self.assertTrue(not ci6.active)
        self.assertEqual(ci7.errords, None)
        self.assertEqual(ci7.message, None)
        self.assertTrue(ci7.active, None)
        self.assertEqual(ci8.errords.split(" ")[0], "ds3")
        self.assertEqual(ci8.message, 'OFF STATE')
        self.assertTrue(not ci8.active)
        self.assertEqual(ci9.errords.split(" ")[0], "ds3")
        self.assertTrue(ci9.message is not None)
        self.assertTrue(not ci9.active)

    # constructor test
    # \brief It tests default settings
    def test_run_user_no(self):
        fun = sys._getframe().f_code.co_name
        print("Run: %s.%s() " % (self.__class__.__name__, fun))
        idn = self.__rnd.randint(1, 1231233)
        cqueue = Queue.Queue()
        self.assertTrue(cqueue.empty())
        el = CheckerThread(idn, cqueue)
        el.tangoSourceOffStates = []
        el.tangoSourceAlarmStates = []
        el.tangoSourceFaultStates = []
        self.assertEqual(el.index, idn)
        el.run()
        self.assertTrue(cqueue.empty())

        ci0 = CheckerItem("cp0")
        ci0.append(TangoDSItem("ds0", None, None))
        cqueue.put(ci0)

        ci1 = CheckerItem("cp1")
        ci1.append(TangoDSItem("ds1", "wrongsdfgdfg", None))
        cqueue.put(ci1)

        ci2 = CheckerItem("cp2")
        ci2.append(TangoDSItem("ds2", self._simps3.new_device_info_writer.name,
                               None))
        cqueue.put(ci2)

        dp = tango.DeviceProxy(self._simps4.new_device_info_writer.name)
        ci3 = CheckerItem("cp3")
        dp.SetState("FAULT")
        ci3.append(TangoDSItem("ds3", self._simps3.new_device_info_writer.name,
                               'ScalarDouble'))
        ci3.append(TangoDSItem("ds4", self._simps3.new_device_info_writer.name,
                               'ScalarLong'))
        ci3.append(TangoDSItem("ds5", self._simps3.new_device_info_writer.name,
                               'ScalarShort'))
        ci3.append(TangoDSItem("ds6", self._simps3.new_device_info_writer.name,
                               'ScalarBoolean'))
        cqueue.put(ci3)

        ci4 = CheckerItem("cp4")
        ci4.append(TangoDSItem("ds3", self._simps3.new_device_info_writer.name,
                               'ScalarDouble'))
        ci4.append(TangoDSItem("ds4", self._simps3.new_device_info_writer.name,
                               'ScalarDoubleddd'))
        cqueue.put(ci4)

        ci5 = CheckerItem("cp5")
        dp.SetState("ALARM")
        ci5.append(TangoDSItem("ds3", self._simps4.new_device_info_writer.name,
                               'ScalarDouble'))
        ci5.append(TangoDSItem("ds4", self._simps4.new_device_info_writer.name,
                               'ScalarShort'))
        cqueue.put(ci5)

        ci6 = CheckerItem("cp6")
        dp = tango.DeviceProxy(self._simps4.new_device_info_writer.name)
        dp.CreateAttribute("Position")
        ci6.append(TangoDSItem("ds3", self._simps4.new_device_info_writer.name,
                               None))
        ci6.append(TangoDSItem("ds4", self._simps4.new_device_info_writer.name,
                               'ScalarShort'))
        cqueue.put(ci6)

        ci7 = CheckerItem("cp6")
        dp = tango.DeviceProxy(self._simps.new_device_info_writer.name)
        dp.CreateAttribute("Position")
        ci7.append(TangoDSItem("ds3", self._simps.new_device_info_writer.name,
                               None))
        ci7.append(TangoDSItem("ds4", self._simps.new_device_info_writer.name,
                               'ScalarShort'))
        cqueue.put(ci7)

        ci8 = CheckerItem("cp8")
        dp = tango.DeviceProxy(self._simps2.new_device_info_writer.name)
        dp.SetState("OFF")
        ci8.append(TangoDSItem("ds3", self._simps2.new_device_info_writer.name,
                               'ScalarDouble'))
        ci8.append(TangoDSItem("ds4", self._simps2.new_device_info_writer.name,
                               'ScalarShort'))
        cqueue.put(ci8)

        ci9 = CheckerItem("cp9")
        ci9.append(TangoDSItem(
            "ds3", self._simpsoff.new_device_info_writer.name,
            'ScalarDouble'))
        ci9.append(TangoDSItem(
            "ds4", self._simpsoff.new_device_info_writer.name,
            'ScalarShort'))
        cqueue.put(ci9)

        el.run()

        self.assertTrue(ci0.message is not None)
        self.assertEqual(ci0.errords.split(" ")[0], 'ds0')
        self.assertTrue(not ci0.active)
        self.assertTrue(ci1.message is not None)
        self.assertEqual(ci1.errords.split(" ")[0], 'ds1')
        self.assertTrue(not ci1.active)
        self.assertEqual(ci2.errords, None)
        self.assertEqual(ci2.message, None)
        self.assertTrue(ci2.active)
        self.assertEqual(ci3.errords, None)
        self.assertEqual(ci3.message, None)
        self.assertTrue(ci3.active)
        self.assertEqual(ci4.errords.split(" ")[0], "ds4")
        self.assertEqual(ci4.message, 'Empty Attribute')
        self.assertTrue(not ci4.active)
        self.assertEqual(ci5.errords, None)
        self.assertEqual(ci5.message, None)
        self.assertTrue(ci5.active)
        self.assertEqual(ci6.errords, None)
        self.assertEqual(ci6.message, None)
        self.assertTrue(ci6.active)
        self.assertEqual(ci7.errords, None)
        self.assertEqual(ci7.message, None)
        self.assertTrue(ci7.active, None)
        self.assertEqual(ci8.errords, None)
        self.assertEqual(ci8.message, None)
        self.assertTrue(ci8.active)
        self.assertEqual(ci9.errords.split(" ")[0], "ds3")
        self.assertTrue(ci9.message is not None)
        self.assertTrue(not ci9.active)

    # constructor test
    # \brief It tests default settings
    def test_run_property(self):
        fun = sys._getframe().f_code.co_name
        print("Run: %s.%s() " % (self.__class__.__name__, fun))
        idn = self.__rnd.randint(1, 1231233)
        cqueue = Queue.Queue()
        self.assertTrue(cqueue.empty())
        el = CheckerThread(idn, cqueue)
        self.assertEqual(el.index, idn)
        el.run()
        self.assertTrue(cqueue.empty())

        ci0 = CheckerItem("cp0")
        ci0.append(TangoDSItem("ds0", None, None))
        cqueue.put(ci0)

        ci1 = CheckerItem("cp1")
        ci1.append(TangoDSItem("ds1", "wrongsdfgdfg", None))
        cqueue.put(ci1)

        ci2 = CheckerItem("cp2")
        ci2.append(TangoDSItem("ds2", self._simps3.new_device_info_writer.name,
                               None))
        cqueue.put(ci2)

        ci3 = CheckerItem("cp3")
        ci3.append(TangoDSItem("ds3", self._simps3.new_device_info_writer.name,
                               '@ScalarDouble'))
        ci3.append(TangoDSItem("ds4", self._simps3.new_device_info_writer.name,
                               '@ScalarLong'))
        ci3.append(TangoDSItem("ds5", self._simps3.new_device_info_writer.name,
                               '@ScalarShort'))
        ci3.append(TangoDSItem("ds6", self._simps3.new_device_info_writer.name,
                               '@ScalarBoolean'))
        cqueue.put(ci3)

        ci4 = CheckerItem("cp4")
        ci4.append(TangoDSItem("ds3", self._simps3.new_device_info_writer.name,
                               '@ScalarDouble'))
        ci4.append(TangoDSItem("ds4", self._simps3.new_device_info_writer.name,
                               '@ScalarDoubleddd'))
        cqueue.put(ci4)

        ci5 = CheckerItem("cp5")
        dp = tango.DeviceProxy(self._simps4.new_device_info_writer.name)
        dp.SetState("ALARM")
        ci5.append(TangoDSItem("ds3", self._simps4.new_device_info_writer.name,
                               '@ScalarDouble'))
        ci5.append(TangoDSItem("ds4", self._simps4.new_device_info_writer.name,
                               '@ScalarShort'))
        cqueue.put(ci5)

        ci6 = CheckerItem("cp6")
        dp = tango.DeviceProxy(self._simps4.new_device_info_writer.name)
        dp.CreateAttribute("Position")
        ci6.append(TangoDSItem("ds3", self._simps4.new_device_info_writer.name,
                               None))
        ci6.append(TangoDSItem("ds4", self._simps4.new_device_info_writer.name,
                               '@ScalarShort'))
        cqueue.put(ci6)

        ci7 = CheckerItem("cp6")
        dp = tango.DeviceProxy(self._simps.new_device_info_writer.name)
        dp.CreateAttribute("Position")
        ci7.append(TangoDSItem("ds3", self._simps.new_device_info_writer.name,
                               None))
        ci7.append(TangoDSItem("ds4", self._simps.new_device_info_writer.name,
                               '@ScalarShort'))
        cqueue.put(ci7)

        ci8 = CheckerItem("cp8")
        dp = tango.DeviceProxy(self._simps2.new_device_info_writer.name)
        dp.SetState("FAULT")
        ci8.append(TangoDSItem("ds3", self._simps2.new_device_info_writer.name,
                               '@ScalarDouble'))
        ci8.append(TangoDSItem("ds4", self._simps2.new_device_info_writer.name,
                               '@ScalarShort'))
        cqueue.put(ci8)

        ci9 = CheckerItem("cp9")
        ci9.append(TangoDSItem(
            "ds3", self._simpsoff.new_device_info_writer.name,
            '@ScalarDouble'))
        ci9.append(TangoDSItem(
            "ds4", self._simpsoff.new_device_info_writer.name,
            '@ScalarShort'))
        cqueue.put(ci9)

        el.run()

        self.assertTrue(ci0.message is not None)
        self.assertEqual(ci0.errords.split(" ")[0], 'ds0')
        self.assertTrue(not ci0.active)
        self.assertTrue(ci1.message is not None)
        self.assertEqual(ci1.errords.split(" ")[0], 'ds1')
        self.assertTrue(not ci1.active)
        self.assertEqual(ci2.errords, None)
        self.assertEqual(ci2.message, None)
        self.assertTrue(ci2.active)
        self.assertEqual(ci3.errords, None)
        self.assertEqual(ci3.message, None)
        self.assertTrue(ci3.active)
        self.assertEqual(ci4.errords, None)
        self.assertEqual(ci4.message, None)
        self.assertTrue(ci4.active)
        self.assertEqual(ci5.errords.split(" ")[0], 'ds4')
        self.assertEqual(ci5.message, 'ALARM STATE')
        self.assertTrue(ci5.active)
        self.assertEqual(ci6.errords.split(" ")[0], "ds4")
        self.assertEqual(ci6.message, 'ALARM STATE')
        self.assertTrue(ci6.active)
        self.assertEqual(ci7.errords, None)
        self.assertEqual(ci7.message, None)
        self.assertTrue(ci7.active, None)
        self.assertEqual(ci8.errords.split(" ")[0], "ds3")
        self.assertEqual(ci8.message, 'FAULT STATE')
        self.assertTrue(not ci8.active)
        self.assertEqual(ci9.errords.split(" ")[0], "ds3")
        self.assertTrue(ci9.message is not None)
        self.assertTrue(not ci9.active)

    # constructor test
    # \brief It tests default settings
    def test_run_command(self):
        fun = sys._getframe().f_code.co_name
        print("Run: %s.%s() " % (self.__class__.__name__, fun))
        idn = self.__rnd.randint(1, 1231233)
        cqueue = Queue.Queue()
        self.assertTrue(cqueue.empty())
        el = CheckerThread(idn, cqueue)
        self.assertEqual(el.index, idn)
        el.run()
        self.assertTrue(cqueue.empty())

        ci0 = CheckerItem("cp0")
        ci0.append(TangoDSItem("ds0", None, None))
        cqueue.put(ci0)

        ci1 = CheckerItem("cp1")
        ci1.append(TangoDSItem("ds1", "wrongsdfgdfg", None))
        cqueue.put(ci1)

        ci2 = CheckerItem("cp2")
        ci2.append(TangoDSItem("ds2", self._simps3.new_device_info_writer.name,
                               None))
        cqueue.put(ci2)

        ci3 = CheckerItem("cp3")
        ci3.append(TangoDSItem("ds3", self._simps3.new_device_info_writer.name,
                               'GetDouble()'))
        ci3.append(TangoDSItem("ds4", self._simps3.new_device_info_writer.name,
                               'GetLong()'))
        ci3.append(TangoDSItem("ds5", self._simps3.new_device_info_writer.name,
                               'GetShort()'))
        ci3.append(TangoDSItem("ds6", self._simps3.new_device_info_writer.name,
                               'GetBoolean()'))
        cqueue.put(ci3)

        ci4 = CheckerItem("cp4")
        ci4.append(TangoDSItem("ds3", self._simps3.new_device_info_writer.name,
                               'GetDouble()'))
        ci4.append(TangoDSItem("ds4", self._simps3.new_device_info_writer.name,
                               'GetDoubleddd()'))
        cqueue.put(ci4)

        ci5 = CheckerItem("cp5")
        dp = tango.DeviceProxy(self._simps4.new_device_info_writer.name)
        dp.SetState("ALARM")
        ci5.append(TangoDSItem("ds3", self._simps4.new_device_info_writer.name,
                               'GetDouble()'))
        ci5.append(TangoDSItem("ds4", self._simps4.new_device_info_writer.name,
                               'GetShort()'))
        cqueue.put(ci5)

        ci6 = CheckerItem("cp6")
        dp = tango.DeviceProxy(self._simps4.new_device_info_writer.name)
        dp.CreateAttribute("Position")
        ci6.append(TangoDSItem("ds3", self._simps4.new_device_info_writer.name,
                               None))
        ci6.append(TangoDSItem("ds4", self._simps4.new_device_info_writer.name,
                               'GetShort()'))
        cqueue.put(ci6)

        ci7 = CheckerItem("cp6")
        dp = tango.DeviceProxy(self._simps.new_device_info_writer.name)
        dp.CreateAttribute("Position")
        ci7.append(TangoDSItem("ds3", self._simps.new_device_info_writer.name,
                               None))
        ci7.append(TangoDSItem("ds4", self._simps.new_device_info_writer.name,
                               'GetShort()'))
        cqueue.put(ci7)

        ci8 = CheckerItem("cp8")
        dp = tango.DeviceProxy(self._simps2.new_device_info_writer.name)
        dp.SetState("FAULT")
        ci8.append(TangoDSItem("ds3", self._simps2.new_device_info_writer.name,
                               'GetDouble()'))
        ci8.append(TangoDSItem("ds4", self._simps2.new_device_info_writer.name,
                               'GetShort()'))
        cqueue.put(ci8)

        ci9 = CheckerItem("cp9")
        ci9.append(TangoDSItem(
            "ds3", self._simpsoff.new_device_info_writer.name,
            'GetDouble()'))
        ci9.append(TangoDSItem(
            "ds4", self._simpsoff.new_device_info_writer.name,
            'GetShort()'))
        cqueue.put(ci9)

        el.run()

        self.assertTrue(ci0.message is not None)
        self.assertEqual(ci0.errords.split(" ")[0], 'ds0')
        self.assertTrue(not ci0.active)
        self.assertTrue(ci1.message is not None)
        self.assertEqual(ci1.errords.split(" ")[0], 'ds1')
        self.assertTrue(not ci1.active)
        self.assertEqual(ci2.errords, None)
        self.assertEqual(ci2.message, None)
        self.assertTrue(ci2.active)
        self.assertEqual(ci3.errords, None)
        self.assertEqual(ci3.message, None)
        self.assertTrue(ci3.active)
        self.assertEqual(ci4.errords.split(" ")[0], 'ds4')
        self.assertEqual(ci4.message, 'GetDoubleddd')
        self.assertTrue(not ci4.active)
        self.assertEqual(ci5.errords.split(" ")[0], 'ds4')
        self.assertEqual(ci5.message, 'ALARM STATE')
        self.assertTrue(ci5.active)
        self.assertEqual(ci6.errords.split(" ")[0], "ds4")
        self.assertEqual(ci6.message, 'ALARM STATE')
        self.assertTrue(ci6.active)
        self.assertEqual(ci7.errords, None)
        self.assertEqual(ci7.message, None)
        self.assertTrue(ci7.active, None)
        self.assertEqual(ci8.errords.split(" ")[0], "ds3")
        self.assertEqual(ci8.message, 'FAULT STATE')
        self.assertTrue(not ci8.active)
        self.assertEqual(ci9.errords.split(" ")[0], "ds3")
        self.assertTrue(ci9.message is not None)
        self.assertTrue(not ci9.active)

    # constructor test
    # \brief It tests default settings
    def test_run_attr(self):
        fun = sys._getframe().f_code.co_name
        print("Run: %s.%s() " % (self.__class__.__name__, fun))
        idn = self.__rnd.randint(1, 1231233)
        cqueue = Queue.Queue()
        self.assertTrue(cqueue.empty())
        el = CheckerThread(idn, cqueue)
        self.assertEqual(el.index, idn)

        matt = list(ATTRIBUTESTOCHECK)
        self.assertEqual(matt, ["Value", "Position", "Counts", "Data",
                                "Voltage", "Energy", "SampleTime"])
        ATTRIBUTESTOCHECK[:] = []
        el.run()
        self.assertTrue(cqueue.empty())

        ci0 = CheckerItem("cp0")
        ci0.append(TangoDSItem("ds0", None, None))
        cqueue.put(ci0)

        ci1 = CheckerItem("cp1")
        ci1.append(TangoDSItem("ds1", "wrongsdfgdfg", None))
        cqueue.put(ci1)

        ci2 = CheckerItem("cp2")
        ci2.append(TangoDSItem(
            "ds2", self._simps3.new_device_info_writer.name, None))
        cqueue.put(ci2)

        ci3 = CheckerItem("cp3")
        ci3.append(TangoDSItem(
            "ds3", self._simps3.new_device_info_writer.name,
            'ScalarDouble'))
        ci3.append(TangoDSItem(
            "ds4", self._simps3.new_device_info_writer.name,
            'ScalarLong'))
        ci3.append(TangoDSItem(
            "ds5", self._simps3.new_device_info_writer.name,
            'ScalarShort'))
        ci3.append(TangoDSItem(
            "ds6", self._simps3.new_device_info_writer.name,
            'ScalarBoolean'))
        cqueue.put(ci3)

        ci4 = CheckerItem("cp4")
        ci4.append(TangoDSItem(
            "ds3", self._simps3.new_device_info_writer.name,
            'ScalarDouble'))
        ci4.append(TangoDSItem(
            "ds4", self._simps3.new_device_info_writer.name,
            'EmptyAttribute'))
        cqueue.put(ci4)

        ci5 = CheckerItem("cp5")
        dp = tango.DeviceProxy(
            self._simps4.new_device_info_writer.name)
        dp.SetState("ALARM")
        ci5.append(TangoDSItem(
            "ds3", self._simps4.new_device_info_writer.name,
            'ScalarDouble'))
        ci5.append(TangoDSItem(
            "ds4", self._simps4.new_device_info_writer.name,
            'ScalarShort'))
        cqueue.put(ci5)

        ci6 = CheckerItem("cp6")
        dp = tango.DeviceProxy(
            self._simps4.new_device_info_writer.name)
        dp.CreateAttribute("Position")
        ci6.append(TangoDSItem(
            "ds3", self._simps4.new_device_info_writer.name, None))
        ci6.append(TangoDSItem(
            "ds4", self._simps4.new_device_info_writer.name,
            'ScalarShort'))
        cqueue.put(ci6)

        ci7 = CheckerItem("cp6")
        dp = tango.DeviceProxy(self._simps.new_device_info_writer.name)
        dp.CreateAttribute("Position")
        ci7.append(TangoDSItem(
            "ds3", self._simps.new_device_info_writer.name, None))
        ci7.append(TangoDSItem(
            "ds4", self._simps.new_device_info_writer.name, 'ScalarShort'))
        cqueue.put(ci7)

        ci8 = CheckerItem("cp8")
        dp = tango.DeviceProxy(self._simps2.new_device_info_writer.name)
        dp.SetState("FAULT")
        ci8.append(TangoDSItem("ds3", self._simps2.new_device_info_writer.name,
                               'ScalarDouble'))
        ci8.append(TangoDSItem("ds4", self._simps2.new_device_info_writer.name,
                               'ScalarShort'))
        cqueue.put(ci8)

        ci9 = CheckerItem("cp9")
        ci9.append(TangoDSItem(
            "ds3", self._simpsoff.new_device_info_writer.name,
            'ScalarDouble'))
        ci9.append(TangoDSItem(
            "ds4", self._simpsoff.new_device_info_writer.name,
            'ScalarShort'))
        cqueue.put(ci9)

        el.run()

        self.assertTrue(ci0.message is not None)
        self.assertEqual(ci0.errords.split(" ")[0], 'ds0')
        self.assertTrue(not ci0.active)
        self.assertTrue(ci1.message is not None)
        self.assertEqual(ci1.errords.split(" ")[0], 'ds1')
        self.assertTrue(not ci1.active)
        self.assertEqual(ci2.errords, None)
        self.assertEqual(ci2.message, None)
        self.assertTrue(ci2.active)
        self.assertEqual(ci3.errords, None)
        self.assertEqual(ci3.message, None)
        self.assertTrue(ci3.active)
        self.assertEqual(ci4.errords.split(" ")[0], "ds4")
        self.assertEqual(ci4.message, 'Empty Attribute')
        self.assertTrue(not ci4.active)
        self.assertEqual(ci5.errords.split(" ")[0], "ds4")
        self.assertEqual(ci5.message, 'ALARM STATE')
        self.assertTrue(ci5.active)
        self.assertEqual(ci6.errords.split(" ")[0], "ds4")
        self.assertEqual(ci6.message, 'ALARM STATE')
        self.assertTrue(ci6.active)
        self.assertEqual(ci7.errords, None)
        self.assertEqual(ci7.message, None)
        self.assertTrue(ci7.active, None)
        self.assertEqual(ci8.errords.split(" ")[0], "ds3")
        self.assertEqual(ci8.message, 'FAULT STATE')
        self.assertTrue(not ci8.active)
        self.assertEqual(ci9.errords.split(" ")[0], "ds3")
        self.assertTrue(ci9.message is not None)
        self.assertTrue(not ci9.active)

        ATTRIBUTESTOCHECK[:] = matt

    def test_start(self):
        fun = sys._getframe().f_code.co_name
        print("Run: %s.%s() " % (self.__class__.__name__, fun))
        idn = self.__rnd.randint(1, 1231233)
        cqueue = Queue.Queue()
        self.assertTrue(cqueue.empty())
        el = CheckerThread(idn, cqueue)
        self.assertEqual(el.index, idn)
        self.assertTrue(cqueue.empty())

        ci0 = CheckerItem("cp0")
        ci0.append(TangoDSItem("ds0", None, None))
        cqueue.put(ci0)

        ci1 = CheckerItem("cp1")
        ci1.append(TangoDSItem("ds1", "wrongsdfgdfg", None))
        cqueue.put(ci1)

        ci2 = CheckerItem("cp2")
        ci2.append(TangoDSItem("ds2", self._simps3.new_device_info_writer.name,
                               None))
        cqueue.put(ci2)

        ci3 = CheckerItem("cp3")
        ci3.append(TangoDSItem("ds3", self._simps3.new_device_info_writer.name,
                               'ScalarDouble'))
        ci3.append(TangoDSItem("ds4", self._simps3.new_device_info_writer.name,
                               'ScalarLong'))
        ci3.append(TangoDSItem("ds5", self._simps3.new_device_info_writer.name,
                               'ScalarShort'))
        ci3.append(TangoDSItem("ds6", self._simps3.new_device_info_writer.name,
                               'ScalarBoolean'))
        cqueue.put(ci3)

        ci4 = CheckerItem("cp4")
        ci4.append(TangoDSItem("ds3", self._simps3.new_device_info_writer.name,
                               'ScalarDouble'))
        ci4.append(TangoDSItem("ds4", self._simps3.new_device_info_writer.name,
                               'ScalarDoubleddd'))
        cqueue.put(ci4)

        ci5 = CheckerItem("cp5")
        dp = tango.DeviceProxy(self._simps4.new_device_info_writer.name)
        dp.SetState("ALARM")
        ci5.append(TangoDSItem("ds3", self._simps4.new_device_info_writer.name,
                               'ScalarDouble'))
        ci5.append(TangoDSItem("ds4", self._simps4.new_device_info_writer.name,
                               'ScalarShort'))
        cqueue.put(ci5)

        ci6 = CheckerItem("cp6")
        dp = tango.DeviceProxy(self._simps4.new_device_info_writer.name)
        dp.CreateAttribute("Position")
        ci6.append(TangoDSItem("ds3", self._simps4.new_device_info_writer.name,
                               None))
        ci6.append(TangoDSItem("ds4", self._simps4.new_device_info_writer.name,
                               'ScalarShort'))
        cqueue.put(ci6)

        ci7 = CheckerItem("cp6")
        dp = tango.DeviceProxy(self._simps.new_device_info_writer.name)
        dp.CreateAttribute("Position")
        ci7.append(TangoDSItem("ds3", self._simps.new_device_info_writer.name,
                               None))
        ci7.append(TangoDSItem("ds4", self._simps.new_device_info_writer.name,
                               'ScalarShort'))
        cqueue.put(ci7)

        ci8 = CheckerItem("cp8")
        dp = tango.DeviceProxy(self._simps2.new_device_info_writer.name)
        dp.SetState("FAULT")
        ci8.append(TangoDSItem("ds3", self._simps2.new_device_info_writer.name,
                               'ScalarDouble'))
        ci8.append(TangoDSItem("ds4", self._simps2.new_device_info_writer.name,
                               'ScalarShort'))
        cqueue.put(ci8)

        ci9 = CheckerItem("cp9")
        ci9.append(TangoDSItem(
            "ds3", self._simpsoff.new_device_info_writer.name,
            'ScalarDouble'))
        ci9.append(TangoDSItem(
            "ds4", self._simpsoff.new_device_info_writer.name,
            'ScalarShort'))
        cqueue.put(ci9)

        el.start()
        el.join()

        self.assertTrue(ci0.message is not None)
        self.assertEqual(ci0.errords.split(" ")[0], 'ds0')
        self.assertTrue(not ci0.active)
        self.assertTrue(ci1.message is not None)
        self.assertEqual(ci1.errords.split(" ")[0], 'ds1')
        self.assertTrue(not ci1.active)
        self.assertEqual(ci2.errords, None)
        self.assertEqual(ci2.message, None)
        self.assertTrue(ci2.active)
        self.assertEqual(ci3.errords, None)
        self.assertEqual(ci3.message, None)
        self.assertTrue(ci3.active)
        self.assertEqual(ci4.errords.split(" ")[0], "ds4")
        self.assertEqual(ci4.message, 'Empty Attribute')
        self.assertTrue(not ci4.active)
        self.assertEqual(ci5.errords.split(" ")[0], "ds4")
        self.assertEqual(ci5.message, 'ALARM STATE')
        self.assertTrue(ci5.active)
        self.assertEqual(ci6.errords.split(" ")[0], "ds4")
        self.assertEqual(ci6.message, 'ALARM STATE')
        self.assertTrue(ci6.active)
        self.assertEqual(ci7.errords, None)
        self.assertEqual(ci7.message, None)
        self.assertTrue(ci7.active, None)
        self.assertEqual(ci8.errords.split(" ")[0], "ds3")
        self.assertEqual(ci8.message, 'FAULT STATE')
        self.assertTrue(not ci8.active)
        self.assertEqual(ci9.errords.split(" ")[0], "ds3")
        self.assertTrue(ci9.message is not None)
        self.assertTrue(not ci9.active)

    def test_start_five(self):
        fun = sys._getframe().f_code.co_name
        print("Run: %s.%s() " % (self.__class__.__name__, fun))
        # idn = self.__rnd.randint(1, 1231233)
        cqueue = Queue.Queue()
        self.assertTrue(cqueue.empty())
        ths = []
        for i in range(5):
            ths.append(CheckerThread(i, cqueue))

        ci0 = CheckerItem("cp0")
        ci0.append(TangoDSItem("ds0", None, None))
        cqueue.put(ci0)

        ci1 = CheckerItem("cp1")
        ci1.append(TangoDSItem("ds1", "wrongsdfgdfg", None))
        cqueue.put(ci1)

        ci2 = CheckerItem("cp2")
        ci2.append(TangoDSItem("ds2", self._simps3.new_device_info_writer.name,
                               None))
        cqueue.put(ci2)

        ci3 = CheckerItem("cp3")
        ci3.append(TangoDSItem("ds3", self._simps3.new_device_info_writer.name,
                               'ScalarDouble'))
        ci3.append(TangoDSItem("ds4", self._simps3.new_device_info_writer.name,
                               'ScalarLong'))
        ci3.append(TangoDSItem("ds5", self._simps3.new_device_info_writer.name,
                               'ScalarShort'))
        ci3.append(TangoDSItem("ds6", self._simps3.new_device_info_writer.name,
                               'ScalarBoolean'))
        cqueue.put(ci3)

        ci4 = CheckerItem("cp4")
        ci4.append(TangoDSItem("ds3", self._simps3.new_device_info_writer.name,
                               'ScalarDouble'))
        ci4.append(TangoDSItem("ds4", self._simps3.new_device_info_writer.name,
                               'ScalarDoubleddd'))
        cqueue.put(ci4)

        ci5 = CheckerItem("cp5")
        dp = tango.DeviceProxy(self._simps4.new_device_info_writer.name)
        dp.SetState("ALARM")
        ci5.append(TangoDSItem("ds3", self._simps4.new_device_info_writer.name,
                               'ScalarDouble'))
        ci5.append(TangoDSItem("ds4", self._simps4.new_device_info_writer.name,
                               'ScalarShort'))
        cqueue.put(ci5)

        ci6 = CheckerItem("cp6")
        dp = tango.DeviceProxy(self._simps4.new_device_info_writer.name)
        dp.CreateAttribute("Position")
        ci6.append(TangoDSItem("ds3", self._simps4.new_device_info_writer.name,
                               None))
        ci6.append(TangoDSItem("ds4", self._simps4.new_device_info_writer.name,
                               'ScalarShort'))
        cqueue.put(ci6)

        ci7 = CheckerItem("cp6")
        dp = tango.DeviceProxy(self._simps.new_device_info_writer.name)
        dp.CreateAttribute("Position")
        ci7.append(TangoDSItem("ds3", self._simps.new_device_info_writer.name,
                               None))
        ci7.append(TangoDSItem("ds4", self._simps.new_device_info_writer.name,
                               'ScalarShort'))
        cqueue.put(ci7)

        ci8 = CheckerItem("cp8")
        dp = tango.DeviceProxy(self._simps2.new_device_info_writer.name)
        dp.SetState("FAULT")
        ci8.append(TangoDSItem("ds3", self._simps2.new_device_info_writer.name,
                               'ScalarDouble'))
        ci8.append(TangoDSItem("ds4", self._simps2.new_device_info_writer.name,
                               'ScalarShort'))
        cqueue.put(ci8)

        ci9 = CheckerItem("cp9")
        ci9.append(TangoDSItem(
            "ds3", self._simpsoff.new_device_info_writer.name,
            'ScalarDouble'))
        ci9.append(TangoDSItem(
            "ds4", self._simpsoff.new_device_info_writer.name,
            'ScalarShort'))
        cqueue.put(ci9)

        for el in ths:
            el.start()
        for el in ths:
            el.join()

        self.assertTrue(ci0.message is not None)
        self.assertEqual(ci0.errords.split(" ")[0], 'ds0')
        self.assertTrue(not ci0.active)
        self.assertTrue(ci1.message is not None)
        self.assertEqual(ci1.errords.split(" ")[0], 'ds1')
        self.assertTrue(not ci1.active)
        self.assertEqual(ci2.errords, None)
        self.assertEqual(ci2.message, None)
        self.assertTrue(ci2.active)
        self.assertEqual(ci3.errords, None)
        self.assertEqual(ci3.message, None)
        self.assertTrue(ci3.active)
        self.assertEqual(ci4.errords.split(" ")[0], "ds4")
        self.assertEqual(ci4.message, 'Empty Attribute')
        self.assertTrue(not ci4.active)
        self.assertEqual(ci5.errords.split(" ")[0], "ds4")
        self.assertEqual(ci5.message, 'ALARM STATE')
        self.assertTrue(ci5.active)
        self.assertEqual(ci6.errords.split(" ")[0], "ds4")
        self.assertEqual(ci6.message, 'ALARM STATE')
        self.assertTrue(ci6.active)
        self.assertEqual(ci7.errords, None)
        self.assertEqual(ci7.message, None)
        self.assertTrue(ci7.active, None)
        self.assertEqual(ci8.errords.split(" ")[0], "ds3")
        self.assertEqual(ci8.message, 'FAULT STATE')
        self.assertTrue(not ci8.active)
        self.assertEqual(ci9.errords.split(" ")[0], "ds3")
        self.assertTrue(ci9.message is not None)
        self.assertTrue(not ci9.active)


if __name__ == '__main__':
    unittest.main()
