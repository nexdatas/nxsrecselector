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
## \file CheckerItemTest.py
# unittests for TangoDsItemTest running Tango Server
#
import unittest
#import os
import sys
#import subprocess
#import random
import struct

from nxsrecconfig.CheckerThread import CheckerItem

## if 64-bit machione
IS64BIT = (struct.calcsize("P") == 8)


## test fixture
class CheckerItemTest(unittest.TestCase):

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
        el = CheckerItem(None)
        self.assertTrue(isinstance(el, list))
        self.assertEqual(el.name, None)
        self.assertEqual(el.errords, None)
        self.assertEqual(el.message, None)
        self.assertEqual(el.active, True)

        el = CheckerItem("myname")
        self.assertEqual(el.name, "myname")
        self.assertEqual(el.errords, None)
        self.assertEqual(el.message, None)
        self.assertEqual(el.active, True)

        el = CheckerItem(None)
        el.errords = "mytype"
        self.assertEqual(el.name, None)
        self.assertEqual(el.errords, "mytype")
        self.assertEqual(el.message, None)
        self.assertEqual(el.active, True)

        el = CheckerItem(None)
        el.message = "mymessage"
        self.assertEqual(el.name, None)
        self.assertEqual(el.errords, None)
        self.assertEqual(el.message, "mymessage")
        self.assertEqual(el.active, True)

        el = CheckerItem("myname2")
        el.errords = "mytype2"
        self.assertEqual(el.name, "myname2")
        self.assertEqual(el.errords, "mytype2")
        self.assertEqual(el.message, None)
        self.assertEqual(el.active, True)

        el = CheckerItem(None)
        el.errords = "mytype2"
        el.message = "mymessage2"
        self.assertEqual(el.name, None)
        self.assertEqual(el.errords, "mytype2")
        self.assertEqual(el.message, "mymessage2")
        self.assertEqual(el.active, True)

        el = CheckerItem("myname2")
        el.message = "mymessage2"
        self.assertEqual(el.name, "myname2")
        self.assertEqual(el.errords, None)
        self.assertEqual(el.message, "mymessage2")
        self.assertEqual(el.active, True)

        el = CheckerItem("myname3")
        el.errords = "mytype3"
        el.message = "mymessage3"
        self.assertEqual(el.name, "myname3")
        self.assertEqual(el.errords, "mytype3")
        self.assertEqual(el.message, "mymessage3")
        self.assertEqual(el.active, True)
        el.active = False
        self.assertEqual(el.active, False)


if __name__ == '__main__':
    unittest.main()
