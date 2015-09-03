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
## \file TangoDSItemTest.py
# unittests for TangoDsItemTest running Tango Server
#
import unittest
import os
import sys
import subprocess
import random
import struct

from nxsrecconfig.CheckerThread import TangoDSItem


## if 64-bit machione
IS64BIT = (struct.calcsize("P") == 8)


## test fixture
class TangoDSItemTest(unittest.TestCase):

    ## constructor
    # \param methodName name of the test method
    def __init__(self, methodName):
        unittest.TestCase.__init__(self, methodName)

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
        el = TangoDSItem()
        self.assertEqual(el.name, None)
        self.assertEqual(el.device, None)
        self.assertEqual(el.attr, None)

        el = TangoDSItem("myname")
        self.assertEqual(el.name, "myname")
        self.assertEqual(el.device, None)
        self.assertEqual(el.attr, None)

        el = TangoDSItem(device="mytype")
        self.assertEqual(el.name, None)
        self.assertEqual(el.device, "mytype")
        self.assertEqual(el.attr, None)

        el = TangoDSItem(attr="myattr")
        self.assertEqual(el.name, None)
        self.assertEqual(el.device, None)
        self.assertEqual(el.attr, "myattr")

        el = TangoDSItem("myname2", "mytype2")
        self.assertEqual(el.name, "myname2")
        self.assertEqual(el.device, "mytype2")
        self.assertEqual(el.attr, None)

        el = TangoDSItem(None, "mytype2", "myattr2")
        self.assertEqual(el.name, None)
        self.assertEqual(el.device, "mytype2")
        self.assertEqual(el.attr, "myattr2")

        el = TangoDSItem("myname2", None, "myattr2")
        self.assertEqual(el.name, "myname2")
        self.assertEqual(el.device, None)
        self.assertEqual(el.attr, "myattr2")

        el = TangoDSItem("myname3", "mytype3", "myattr3")
        self.assertEqual(el.name, "myname3")
        self.assertEqual(el.device, "mytype3")
        self.assertEqual(el.attr, "myattr3")

        el = TangoDSItem(True, 1, 1.234)
        self.assertEqual(el.name, "True")
        self.assertEqual(el.device, "1")
        self.assertEqual(el.attr, "1.234")


if __name__ == '__main__':
    unittest.main()
