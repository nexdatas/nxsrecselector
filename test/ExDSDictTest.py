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
## \file ExDSDictTest.py
# unittests for field Tags running Tango Server
#
import unittest
#import os
import sys
#import subprocess
#import random
import struct

from nxsrecconfig.Describer import (
    DSItem,
    ExDSDict)


## if 64-bit machione
IS64BIT = (struct.calcsize("P") == 8)


## test fixture
class ExDSDictTest(unittest.TestCase):

    ## constructor
    # \param methodName name of the test method
    def __init__(self, methodName):
        unittest.TestCase.__init__(self, methodName)

        self._tfname = "field"
        self._tfname = "group"
        self._fattrs = {"short_name": "test", "units": "m"}

        self._bint = "int64" if IS64BIT else "int32"
        self._buint = "uint64" if IS64BIT else "uint32"
        self._bfloat = "float64" if IS64BIT else "float32"

    ## test starter
    # \brief Common set up
    def setUp(self):
        print "\nsetting up..."

    ## test closer
    # \brief Common tear down
    def tearDown(self):
        print "tearing down ..."

    ## constructor test
    # \brief It tests default settings
    def test_constructor(self):
        fun = sys._getframe().f_code.co_name
        print "Run: %s.%s() " % (self.__class__.__name__, fun)
        el = ExDSDict()
        self.assertTrue(isinstance(el, dict))

    def test_appendDSList(self):
        fun = sys._getframe().f_code.co_name
        print "Run: %s.%s() " % (self.__class__.__name__, fun)
        dl = ExDSDict()
        self.assertEqual(len(dl.keys()), 0)

        el = DSItem("myname3", "mytype3", "myrecord3")
        el4 = DSItem("myname4", "mytype4", "myrecord4")
        el5 = DSItem(None, "mytype5", "myrecord5")

        dl.appendDSList([el], "mymode2")
        self.assertEqual(len(dl.keys()), 1)
        self.assertEqual(len(dl["myname3"]), 1)
        self.assertEqual(dl["myname3"][0].name, "myname3")
        self.assertEqual(dl["myname3"][0].name, "myname3")
        self.assertEqual(dl["myname3"][0].dstype, "mytype3")
        self.assertEqual(dl["myname3"][0].record, "myrecord3")
        self.assertEqual(dl["myname3"][0].mode, "mymode2")
        self.assertEqual(dl["myname3"][0].nxtype, None)
        self.assertEqual(dl["myname3"][0].shape, None)

        dl.appendDSList([el], "mymode3", "mynxtype3", [4, 5])
        self.assertEqual(len(dl.keys()), 1)
        self.assertEqual(len(dl["myname3"]), 2)
        self.assertEqual(dl["myname3"][0].name, "myname3")
        self.assertEqual(dl["myname3"][0].dstype, "mytype3")
        self.assertEqual(dl["myname3"][0].record, "myrecord3")
        self.assertEqual(dl["myname3"][0].mode, "mymode2")
        self.assertEqual(dl["myname3"][0].nxtype, None)
        self.assertEqual(dl["myname3"][0].shape, None)
        self.assertEqual(dl["myname3"][1].name, "myname3")
        self.assertEqual(dl["myname3"][1].dstype, "mytype3")
        self.assertEqual(dl["myname3"][1].record, "myrecord3")
        self.assertEqual(dl["myname3"][1].mode, "mymode3")
        self.assertEqual(dl["myname3"][1].nxtype, "mynxtype3")
        self.assertEqual(dl["myname3"][1].shape, [4, 5])

        dl.appendDSList([el4], "mymode4", "mynxtype4", [14, 15])
        self.assertEqual(len(dl.keys()), 2)
        self.assertEqual(len(dl["myname3"]), 2)
        self.assertEqual(dl["myname3"][0].name, "myname3")
        self.assertEqual(dl["myname3"][0].dstype, "mytype3")
        self.assertEqual(dl["myname3"][0].record, "myrecord3")
        self.assertEqual(dl["myname3"][0].mode, "mymode2")
        self.assertEqual(dl["myname3"][0].nxtype, None)
        self.assertEqual(dl["myname3"][0].shape, None)
        self.assertEqual(dl["myname3"][1].name, "myname3")
        self.assertEqual(dl["myname3"][1].dstype, "mytype3")
        self.assertEqual(dl["myname3"][1].record, "myrecord3")
        self.assertEqual(dl["myname3"][1].mode, "mymode3")
        self.assertEqual(dl["myname3"][1].nxtype, "mynxtype3")
        self.assertEqual(dl["myname3"][1].shape, [4, 5])
        self.assertEqual(len(dl["myname4"]), 1)
        self.assertEqual(dl["myname4"][0].name, "myname4")
        self.assertEqual(dl["myname4"][0].dstype, "mytype4")
        self.assertEqual(dl["myname4"][0].record, "myrecord4")
        self.assertEqual(dl["myname4"][0].mode, "mymode4")
        self.assertEqual(dl["myname4"][0].nxtype, "mynxtype4")
        self.assertEqual(dl["myname4"][0].shape, [14, 15])

        dl.appendDSList([el5], "mymode5", "mynxtype5", [12, 2])
        self.assertEqual(len(dl.keys()), 3)
        self.assertEqual(len(dl["myname3"]), 2)
        self.assertEqual(dl["myname3"][0].name, "myname3")
        self.assertEqual(dl["myname3"][0].dstype, "mytype3")
        self.assertEqual(dl["myname3"][0].record, "myrecord3")
        self.assertEqual(dl["myname3"][0].mode, "mymode2")
        self.assertEqual(dl["myname3"][0].nxtype, None)
        self.assertEqual(dl["myname3"][0].shape, None)
        self.assertEqual(dl["myname3"][1].name, "myname3")
        self.assertEqual(dl["myname3"][1].dstype, "mytype3")
        self.assertEqual(dl["myname3"][1].record, "myrecord3")
        self.assertEqual(dl["myname3"][1].mode, "mymode3")
        self.assertEqual(dl["myname3"][1].nxtype, "mynxtype3")
        self.assertEqual(dl["myname3"][1].shape, [4, 5])
        self.assertEqual(len(dl["myname4"]), 1)
        self.assertEqual(dl["myname4"][0].name, "myname4")
        self.assertEqual(dl["myname4"][0].dstype, "mytype4")
        self.assertEqual(dl["myname4"][0].record, "myrecord4")
        self.assertEqual(dl["myname4"][0].mode, "mymode4")
        self.assertEqual(dl["myname4"][0].nxtype, "mynxtype4")
        self.assertEqual(dl["myname4"][0].shape, [14, 15])
        self.assertEqual(len(dl["__unnamed__1"]), 1)
        self.assertEqual(dl["__unnamed__1"][0].name, None)
        self.assertEqual(dl["__unnamed__1"][0].dstype, "mytype5")
        self.assertEqual(dl["__unnamed__1"][0].record, "myrecord5")
        self.assertEqual(dl["__unnamed__1"][0].mode, "mymode5")
        self.assertEqual(dl["__unnamed__1"][0].nxtype, "mynxtype5")
        self.assertEqual(dl["__unnamed__1"][0].shape, [12, 2])

        dl.appendDSList([el5], "mymode5a", "mynxtype5a", [2, 23])
        dl.appendDSList([el5], "mymode5b", "mynxtype5b", [123, 2])
        self.assertEqual(len(dl.keys()), 5)
        self.assertEqual(len(dl["__unnamed__2"]), 1)
        self.assertEqual(dl["__unnamed__2"][0].name, None)
        self.assertEqual(dl["__unnamed__2"][0].dstype, "mytype5")
        self.assertEqual(dl["__unnamed__2"][0].record, "myrecord5")
        self.assertEqual(dl["__unnamed__2"][0].mode, "mymode5a")
        self.assertEqual(dl["__unnamed__2"][0].nxtype, "mynxtype5a")
        self.assertEqual(dl["__unnamed__2"][0].shape, [2, 23])
        self.assertEqual(len(dl["__unnamed__3"]), 1)
        self.assertEqual(dl["__unnamed__3"][0].name, None)
        self.assertEqual(dl["__unnamed__3"][0].dstype, "mytype5")
        self.assertEqual(dl["__unnamed__3"][0].record, "myrecord5")
        self.assertEqual(dl["__unnamed__3"][0].mode, "mymode5b")
        self.assertEqual(dl["__unnamed__3"][0].nxtype, "mynxtype5b")
        self.assertEqual(dl["__unnamed__3"][0].shape, [123, 2])


if __name__ == '__main__':
    unittest.main()
