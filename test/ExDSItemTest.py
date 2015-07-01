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
## \file ExDSItemTest.py
# unittests for field Tags running Tango Server
#
import unittest
import os
import sys
import subprocess
import random
import struct

from nxsrecconfig.Describer import DSItem, ExDSItem



## if 64-bit machione
IS64BIT = (struct.calcsize("P") == 8)




## test fixture
class ExDSItemTest(unittest.TestCase):

    ## constructor
    # \param methodName name of the test method
    def __init__(self, methodName):
        unittest.TestCase.__init__(self, methodName)


        self._tfname = "field"
        self._tfname = "group"
        self._fattrs = {"short_name":"test","units":"m" }


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
        el = ExDSItem()
        self.assertEqual(el.name, None)
        self.assertEqual(el.dstype, None)
        self.assertEqual(el.record, None)
        self.assertEqual(el.mode, None)
        self.assertEqual(el.nxtype, None)
        self.assertEqual(el.shape, None)


        el = ExDSItem(None, "mymode", "mynxtype", [23,4,5])
        self.assertEqual(el.name, None)
        self.assertEqual(el.dstype, None)
        self.assertEqual(el.record, None)
        self.assertEqual(el.mode, "mymode")
        self.assertEqual(el.nxtype, "mynxtype")
        self.assertEqual(el.shape, [23,4,5])


        el = DSItem("myname3", "mytype3", "myrecord3")
        self.assertEqual(el.name, "myname3")
        self.assertEqual(el.dstype, "mytype3")
        self.assertEqual(el.record, "myrecord3")


        el2 = ExDSItem(el, "mymode2", "mynxtype2", [4,5])
        self.assertEqual(el2.name, "myname3")
        self.assertEqual(el2.dstype, "mytype3")
        self.assertEqual(el2.record, "myrecord3")
        self.assertEqual(el2.mode, "mymode2")
        self.assertEqual(el2.nxtype, "mynxtype2")
        self.assertEqual(el2.shape, [4,5])

if __name__ == '__main__':
    unittest.main()
