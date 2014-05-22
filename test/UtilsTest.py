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
## \file UtilsTest.py
# unittests for field Tags running Tango Server
#
import unittest
import os
import sys
import subprocess
import random
import struct
import PyTango

import TestServerSetUp

from nxsrecconfig.Utils import Utils



## if 64-bit machione
IS64BIT = (struct.calcsize("P") == 8)




## test fixture
class UtilsTest(unittest.TestCase):

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

        self._simps = TestServerSetUp.TestServerSetUp()
        self._simps2 = TestServerSetUp.TestServerSetUp( "ttestp09/testts/t2r228", "S2")

    ## test starter
    # \brief Common set up
    def setUp(self):       
        self._simps.setUp()
        self._simps2.setUp()

    ## test closer
    # \brief Common tear down
    def tearDown(self):       
        self._simps2.tearDown()
        self._simps.tearDown()

    ## Exception tester
    # \param exception expected exception
    # \param method called method      
    # \param args list with method arguments
    # \param kwargs dictionary with method arguments
    def myAssertRaise(self, exception, method, *args, **kwargs):
        try:
            error =  False
            method(*args, **kwargs)
        except exception, e:
            error = True
        self.assertEqual(error, True)

    ## constructor test
    # \brief It tests default settings
    def test_constructor(self):
        fun = sys._getframe().f_code.co_name
        print "Run: %s.%s() " % (self.__class__.__name__, fun)
        el = Utils()

#        self.assertEqual(el.tagName, self._tfname)
#        self.assertEqual(el._tagAttrs, self._fattrs)
#        self.assertEqual(el.content, [])
#        self.assertEqual(el.doc, "")
#        self.assertEqual(el.last, None)

    ## openProxy test
    # \brief It tests default settings
    def test_openProxy(self):
        fun = sys._getframe().f_code.co_name
        print "Run: %s.%s() " % (self.__class__.__name__, fun)
        self.myAssertRaise(PyTango.DevFailed, Utils.openProxy, "sdf/testtestsf/d")

        dp = Utils.openProxy(self._simps.new_device_info_writer.name)
        self.assertTrue(isinstance(dp, PyTango.DeviceProxy))
        self.assertEqual(dp.name(), self._simps.new_device_info_writer.name)
        dp.setState("RUNNING")
        dp = Utils.openProxy(self._simps.new_device_info_writer.name)
        self._simps.stop()
        
        self.myAssertRaise(PyTango.DevFailed, Utils.openProxy, 
                           self._simps.new_device_info_writer.name)

    ## getEnv text   
    def test_getsetEnv(self):
        fun = sys._getframe().f_code.co_name
        print "Run: %s.%s() " % (self.__class__.__name__, fun)
        self.assertEqual(u'/tmp/', 
                         Utils.getEnv("ScanDir", 
                                      self._simps.new_device_info_writer.name))
        self.assertEqual([u'sar4r.nxs'], 
                         Utils.getEnv("ScanFile", 
                                      self._simps.new_device_info_writer.name))
        self.assertEqual(192, 
                         Utils.getEnv("ScanID", 
                                      self._simps.new_device_info_writer.name))
        self.assertEqual("", 
                         Utils.getEnv("ScanNone", 
                                      self._simps.new_device_info_writer.name))
 
        Utils.setEnv("ScanDir", "/tmp/sardana/", 
                     self._simps.new_device_info_writer.name)
        self.assertEqual(u'/tmp/sardana/', 
                         Utils.getEnv("ScanDir", 
                                      self._simps.new_device_info_writer.name))

        Utils.setEnv("ScanFile", [u'sar4r.nxs', u'sar5r.nxs'],  
                     self._simps.new_device_info_writer.name)
        self.assertEqual([u'sar4r.nxs', u'sar5r.nxs'], 
                         Utils.getEnv("ScanFile", 
                                      self._simps.new_device_info_writer.name))

        Utils.setEnv("ScanID", 123,  
                     self._simps.new_device_info_writer.name)
        self.assertEqual(123, 
                         Utils.getEnv("ScanID", 
                                      self._simps.new_device_info_writer.name))
        Utils.setEnv("ScanNone", "Somethin new",  
                     self._simps.new_device_info_writer.name)
        self.assertEqual("Somethin new", 
                         Utils.getEnv("ScanNone", 
                                      self._simps.new_device_info_writer.name))

if __name__ == '__main__':
    unittest.main()
