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
# \file DSItemTest.py
# unittests for field Tags running Tango Server
#
import unittest
# import os
import sys
# import subprocess
# import random
import struct

from nxsrecconfig.Describer import DSItem


# if 64-bit machione
IS64BIT = (struct.calcsize("P") == 8)


# test fixture
class DSItemTest(unittest.TestCase):

    # constructor
    # \param methodName name of the test method

    def __init__(self, methodName):
        unittest.TestCase.__init__(self, methodName)

        self._tfname = "field"
        self._tfname = "group"
        self._fattrs = {"short_name": "test", "units": "m"}

        self._bint = "int64" if IS64BIT else "int32"
        self._buint = "uint64" if IS64BIT else "uint32"
        self._bfloat = "float64" if IS64BIT else "float32"

    # test starter
    # \brief Common set up
    def setUp(self):
        print("\nsetting up...")

    # test closer
    # \brief Common tear down
    def tearDown(self):
        print("tearing down ...")

    # constructor test
    # \brief It tests default settings
    def test_constructor(self):
        fun = sys._getframe().f_code.co_name
        print("Run: %s.%s() " % (self.__class__.__name__, fun))
        el = DSItem()
        self.assertEqual(el.name, None)
        self.assertEqual(el.dstype, None)
        self.assertEqual(el.record, None)
        self.assertEqual(el.parentobj, None)

        el = DSItem("myname")
        self.assertEqual(el.name, "myname")
        self.assertEqual(el.dstype, None)
        self.assertEqual(el.record, None)
        self.assertEqual(el.parentobj, None)

        el = DSItem(dstype="mytype")
        self.assertEqual(el.name, None)
        self.assertEqual(el.dstype, "mytype")
        self.assertEqual(el.record, None)
        self.assertEqual(el.parentobj, None)

        el = DSItem(record="myrecord")
        self.assertEqual(el.name, None)
        self.assertEqual(el.dstype, None)
        self.assertEqual(el.record, "myrecord")
        self.assertEqual(el.parentobj, None)

        el = DSItem("myname2", "mytype2")
        self.assertEqual(el.name, "myname2")
        self.assertEqual(el.dstype, "mytype2")
        self.assertEqual(el.record, None)

        el = DSItem(None, "mytype2", "myrecord2")
        self.assertEqual(el.name, None)
        self.assertEqual(el.dstype, "mytype2")
        self.assertEqual(el.record, "myrecord2")
        self.assertEqual(el.parentobj, None)

        el = DSItem("myname2", None, "myrecord2")
        self.assertEqual(el.name, "myname2")
        self.assertEqual(el.dstype, None)
        self.assertEqual(el.record, "myrecord2")

        el = DSItem("myname3", "mytype3", "myrecord3", parentobj="datasource")
        self.assertEqual(el.name, "myname3")
        self.assertEqual(el.dstype, "mytype3")
        self.assertEqual(el.record, "myrecord3")
        self.assertEqual(el.parentobj, "datasource")

        el = DSItem(True, 1, 1.234, parentobj="field")
        self.assertEqual(el.name, "True")
        self.assertEqual(el.dstype, "1")
        self.assertEqual(el.parentobj, "field")
        self.assertEqual(el.record, "1.234")

    # constructor test
    # \brief It tests default settings
    def test_constructor_dsitem(self):
        fun = sys._getframe().f_code.co_name
        print("Run: %s.%s() " % (self.__class__.__name__, fun))
        el = DSItem("myname3", "mytype3", "myrecord3", parentobj="field")
        self.assertEqual(el.name, "myname3")
        self.assertEqual(el.dstype, "mytype3")
        self.assertEqual(el.record, "myrecord3")
        self.assertEqual(el.parentobj, "field")

        el2 = DSItem(dsitem=el)
        self.assertEqual(el2.name, "myname3")
        self.assertEqual(el2.dstype, "mytype3")
        self.assertEqual(el2.record, "myrecord3")
        self.assertEqual(el.parentobj, "field")

        el2 = DSItem("name", "type", "record", dsitem=el)
        self.assertEqual(el2.name, "myname3")
        self.assertEqual(el2.dstype, "mytype3")
        self.assertEqual(el2.record, "myrecord3")
        self.assertEqual(el2.parentobj, "field")

        el = None
        self.assertEqual(el2.name, "myname3")
        self.assertEqual(el2.dstype, "mytype3")
        self.assertEqual(el2.record, "myrecord3")
        self.assertEqual(el2.parentobj, "field")


if __name__ == '__main__':
    unittest.main()
