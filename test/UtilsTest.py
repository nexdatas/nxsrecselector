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
import pickle

import TestServerSetUp

from nxsrecconfig.Utils import Utils




## if 64-bit machione
IS64BIT = (struct.calcsize("P") == 8)

class Datum(object):
    def __init__(self, device, value_string = None):
        self.device = device
        self.value_string = value_string if value_string else []

class DB(object):
    def __init__(self):
        self.classdevices = {
            "NXSDataWriter":['test/nxsdatawriter/01','test/nxsdatawriter/02'],
            "NXSConfigServer":['test/nxsconfigserver/01','test/nxsconfigserver/02'],
            "Door":['test/door/01','test/door/02','test/door/03'],
            "MacroServer":['test/ms/01'],
            }
        pass

    def get_device_name(self, serv_name, class_name):
        
        print "-> DbDatum"

    def get_server_list(self, filter= '*'):
        
        print "-> DbDatum"

    def get_server_class_list(self, server, filter= '*'):
        
        print "-> DbDatum"

    def get_device_exported_for_class(self, class_name, filter= '*'):
        dd = Datum('device')
        if class_name in self.classdevices:
            dd.value_string = self.classdevices[class_name]
        else:
            dd.value_string = []
        return dd
    
      

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

    ## getEnv test   
    def test_getsetEnv(self):
        fun = sys._getframe().f_code.co_name
        print "Run: %s.%s() " % (self.__class__.__name__, fun)
        
        arr = {
            "ScanDir": [u'/tmp/',  "/tmp/sardana/" ],
            "ScanFile": [[u'sar4r.nxs'], [u'sar4r.nxs', u'sar5r.nxs']],
            "ScanID": [192, 123],
            "ScanNone": ["", "Something new"],
            "_ViewOptions": [{'ShowDial': True}, {'ShowDial': False}],
            }

        for k, vl in arr.items():
            self.assertEqual(
                vl[0], Utils.getEnv(
                    k, self._simps.new_device_info_writer.name))

        for k, vl in arr.items():
            Utils.setEnv(k, vl[1], 
                         self._simps.new_device_info_writer.name)
            self.assertEqual(vl[1], Utils.getEnv(
                    k, self._simps.new_device_info_writer.name))


    ## getEnv test   
    def test_getEnv(self):
        fun = sys._getframe().f_code.co_name
        print "Run: %s.%s() " % (self.__class__.__name__, fun)
        
        arr = {
            "ScanDir": [u'/tmp/',  "/tmp/sardana/" ],
            "ScanFile": [[u'sar4r.nxs'], [u'sar4r.nxs', u'sar5r.nxs']],
            "ScanID": [192, 123],
            "blebleble": ["", "Something new"],
            "_ViewOptions": [{'ShowDial': True}, {'ShowDial': False}],
            }

        
        for k, vl in arr.items():
            self.assertEqual(
                vl[0], Utils.getEnv(
                    k, self._simps.new_device_info_writer.name))

        self.assertEqual(self._simps.dp.Environment[0],'pickle')
        en = pickle.loads(self._simps.dp.Environment[1])['new']
        
        for k, vl in arr.items():
            en[k] = vl[1]
            self._simps.dp.Environment =  (
                'pickle',
                pickle.dumps( {'new': en}))
            self.assertEqual(vl[1], Utils.getEnv(
                    k, self._simps.new_device_info_writer.name))

            

 

    ## setEnv test   
    def test_setEnv(self):
        fun = sys._getframe().f_code.co_name
        print "Run: %s.%s() " % (self.__class__.__name__, fun)
        
        arr = {
            "ScanDir": [u'/tmp/',  "/tmp/sardana/" ],
            "ScanFile": [[u'sar4r.nxs'], [u'sar4r.nxs', u'sar5r.nxs']],
            "ScanID": [192, 123],
            "ScanNone": ["", "Something new"],
            "_ViewOptions": [{'ShowDial': True}, {'ShowDial': False}],
            }

        for k, vl in arr.items():
            self.assertEqual(
                vl[0], Utils.getEnv(
                    k, self._simps.new_device_info_writer.name))

        for k, vl in arr.items():
            Utils.setEnv(k, vl[1], 
                         self._simps.new_device_info_writer.name)

            self.assertEqual(self._simps.dp.Environment[0],'pickle')
            en = pickle.loads(self._simps.dp.Environment[1])['new']
            self.assertEqual(en[k], Utils.getEnv(
                    k, self._simps.new_device_info_writer.name))


    ## getProxies test   
    def test_getProxies(self):
        fun = sys._getframe().f_code.co_name
        print "Run: %s.%s() " % (self.__class__.__name__, fun)
        self.assertEqual(Utils.getProxies([]), [])
        self.myAssertRaise(PyTango.DevFailed, Utils.getProxies, ["bleble"])
        dpl = Utils.getProxies([self._simps.new_device_info_writer.name])
        self.assertEqual(len(dpl), 1)
        self.assertEqual(type(dpl[0]), PyTango.DeviceProxy)
        self.assertEqual(dpl[0].name(), 
                         self._simps.new_device_info_writer.name)


        dpl = Utils.getProxies([
                self._simps.new_device_info_writer.name,
                self._simps2.new_device_info_writer.name])
        self.assertEqual(len(dpl), 2)
        self.assertEqual(type(dpl[0]), PyTango.DeviceProxy)
        self.assertEqual(type(dpl[1]), PyTango.DeviceProxy)
        self.assertEqual(dpl[0].name(), 
                         self._simps.new_device_info_writer.name)
        self.assertEqual(dpl[1].name(), 
                         self._simps2.new_device_info_writer.name)



    ## getDeviceName test   
    def test_getDeviceName(self):
        fun = sys._getframe().f_code.co_name
        print "Run: %s.%s() " % (self.__class__.__name__, fun)
        
        arr = [ "NXSDataWriter" , "" , "NXSConfigServer", "Door", 
                "MacroServer" , "bleble"]

        db = DB()
    
        for ar in arr:
            dd = Utils.getDeviceName(db, ar)
            src = db.get_device_exported_for_class(ar).value_string
            dv = src[0] if len(src) else ''
            self.assertEqual(dd, dv)


    ## getDeviceName test   
    def test_getDeviceName_db(self):
        fun = sys._getframe().f_code.co_name
        print "Run: %s.%s() " % (self.__class__.__name__, fun)
        
        arr = [ "NXSDataWriter" , "" , "NXSConfigServer", "Door", 
                "MacroServer" , "bleble"]

        db = PyTango.Database()
    
        for ar in arr:
            dd = Utils.getDeviceName(db, ar)
            src = db.get_device_exported_for_class(ar).value_string
            dv = src[0] if len(src) else ''
            self.assertEqual(dd, dv)
                
            
    ## getDeviceName test   
    def test_getMacroServer(self):
        fun = sys._getframe().f_code.co_name
        print "Run: %s.%s() " % (self.__class__.__name__, fun)
        
        arr = [
            [self._simps.new_device_info_writer.name, 'test/door/1'],
            [self._simps.new_device_info_writer.name, 'test/door/2'],
            [self._simps2.new_device_info_writer.name, 'test/door/3'],
            ["", 'test/door/4'],
            ]

        self._simps2.dp.DoorList = [
            'test/door/2','test/door/3'
            ]
        db = DB()
        db.classdevices['MacroServer'] = [ 
            self._simps.new_device_info_writer.name,
            self._simps2.new_device_info_writer.name]

        for ar in arr:
            ms = Utils.getMacroServer(db, ar[1])
            self.assertEqual(ms, ar[0])


    ## getDeviceName test   
    def test_getMacroServer_db(self):
        fun = sys._getframe().f_code.co_name
        print "Run: %s.%s() " % (self.__class__.__name__, fun)
        
        arr = [
            [self._simps.new_device_info_writer.name, 'test/door/1'],
            [self._simps.new_device_info_writer.name, 'test/door/2'],
            [self._simps2.new_device_info_writer.name, 'test/door/3'],
            ["", 'test/door/4'],
            ]

        self._simps2.dp.DoorList = [
            'test/door/2','test/door/3'
            ]
        db = DB()
        servers =  db.get_device_exported_for_class(
            "MacroServer").value_string

        alldoors = set()
        for sr in servers:
            try:
                dp = PyTango.DeviceProxy(sr)
            except:
                dp = None
            if dp:
                doors = dp.DoorList
                sdoors = set(doors) - alldoors
                for dr in sdoors:
                    ms = Utils.getMacroServer(db, dr)
                    self.assertEqual(ms, sr)
                alldoors.extends(sdoors)


if __name__ == '__main__':
    unittest.main()
