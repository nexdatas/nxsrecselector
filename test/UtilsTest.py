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
import json

import logging
logger = logging.getLogger()


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
            "TestServer":['ttestp09/testts/t1r228'],
            }
        pass

    def get_device_exported_for_class(self, class_name, filter= '*'):
        dd = Datum('device')
        if class_name in self.classdevices:
            dd.value_string = self.classdevices[class_name]
        else:
            dd.value_string = []
        return dd
    
class Pool(object):

    def __init__(self):
        self.AcqChannelList = []
        self.MeasurementGroupList = []
        self.ExpChannelList = []
      

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
        self._simps3 = TestServerSetUp.TestServerSetUp( "ttestp09/testts/t3r228", "S3") 
        self._simps4 = TestServerSetUp.TestServerSetUp( "ttestp09/testts/t4r228", "S4")

        self.cnt = '{"units": {"0":{"channels":{},' \
            + ' "trigger_type":0, "id":0, "timer":"%s", "monitor":"%s"}}}'
        self.chnl = '{"ndim":0, "index":%s, "name":"%s", "data_type":"%s", "plot_type":%s, "enabled": true, "label": "%s", "instrument":null, "shape": [%s], "_controller_name": "%s", "conditioning": "", "full_name": "%s", "_unit_id": "0", "normalization": 0, "output":true, "plot_axes":[%s], "nexus_path": "", "data_units": "No unit", "source": "%s"}'


    ## test starter
    # \brief Common set up
    def setUp(self):       
        self._simps.setUp()
        self._simps2.setUp()
        self._simps3.setUp()
        self._simps4.setUp()

    ## test closer
    # \brief Common tear down
    def tearDown(self):       
        self._simps4.tearDown()
        self._simps3.tearDown()
        self._simps2.tearDown()
        self._simps.tearDown()

    ## Exception tester
    # \param exception expected exception
    # \param method called method      
    # \param args list with method arguments
    # \param kwargs dictionary with method arguments
    def myAssertRaise(self, exception, method, *args, **kwargs):
        err = None
        try:
            error =  False
            method(*args, **kwargs)
        except exception, e:
            error = True
            err = e
        self.assertEqual(error, True)
        return err


    def myAssertDict(self, dct, dct2):
        logger.debug('dict %s' % type(dct))
        logger.debug("\n%s\n%s" % ( dct, dct2))
        self.assertTrue(isinstance(dct, dict))
        self.assertTrue(isinstance(dct2, dict))
        logger.debug("%s %s" %(len(dct.keys()), len(dct2.keys())))
        self.assertEqual(len(dct.keys()), len(dct2.keys()))
        for k,v in dct.items():
            logger.debug("%s  in %s" %(str(k), str(dct2.keys())))
            self.assertTrue(k in dct2.keys())
            if isinstance(v, dict):
                self.myAssertDict(v, dct2[k])
            else:
                logger.debug("%s , %s" %(str(v), str(dct2[k])))
                self.assertEqual(v, dct2[k])


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
            self.assertEqual(dd, '')


    ## getDeviceName test   
    def test_getDeviceName_OK(self):
        fun = sys._getframe().f_code.co_name
        print "Run: %s.%s() " % (self.__class__.__name__, fun)
        
        arr = ["TestServer"]

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
            dv = ''
            for server in src:
                try:
                    dp = PyTango.DeviceProxy(server)
                    dp.ping()
                    dv = server
                    break
                except:
                    pass
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


    ## getDeviceName test   
    def test_getFullDeviceNames_empty(self):
        fun = sys._getframe().f_code.co_name
        print "Run: %s.%s() " % (self.__class__.__name__, fun)
        

        arr = [
            {"name":"test/ct/01", "full_name":"counter_01/Value"} ,
            {"name":"test/ct/02", "full_name":"counter_02/att"} ,
            {"name":"test/ct/03", "full_name":"counter_03/value"} ,
            {"name":"test/ct/04", "full_name":"counter_04/13"} ,
            {"name":"null", "full_name":"counter_04"} ,
            ]



        pool = Pool()
        pool.AcqChannelList = [json.dumps(a) for a in arr]
    
        import nxsrecconfig 
        dd = Utils.getFullDeviceNames([])
        self.assertEqual(dd, {})

        dd = Utils.getFullDeviceNames([], [arr[0]["name"]])
        self.assertEqual(dd, {})
        dd = Utils.getFullDeviceNames([pool], [arr[4]["name"]])
        self.assertEqual(dd, {"null":""})
        


    ## getDeviceName test   


    ## getDeviceName test   
    def test_getFullDeviceNames_pool1(self):
        fun = sys._getframe().f_code.co_name
        print "Run: %s.%s() " % (self.__class__.__name__, fun)
        

        arr = [
            ["test/ct/01", "counter_01", "Value"],
            ["test/ct/02", "counter_02", "att"],
            ["test/ct/03", "counter_03", "value"],
            ["test/ct/04", "counter_04", "13"],
            ["null", "counter_04",""],
            ]

        pool = Pool()
        pool.AcqChannelList = [json.dumps(
                {"name":a[0], "full_name":"%s/%s" % (a[1], a[2])}) for a in arr]
    
        
        for ar in arr:
            dd = Utils.getFullDeviceNames([pool], [ar[0]])
            self.assertEqual(dd, {ar[0]:ar[1]})
        

        dd = Utils.getFullDeviceNames([pool], [ar[0] for ar in arr])
        self.assertEqual(dd, dict((ar[0],ar[1]) for ar in arr))

        dd = Utils.getFullDeviceNames([pool])
        self.assertEqual(dd, dict((ar[0],ar[1]) for ar in arr))
            


    def test_getFullDeviceNames_pool2(self):
        fun = sys._getframe().f_code.co_name
        print "Run: %s.%s() " % (self.__class__.__name__, fun)
        

        arr = [
            ["test/ct/01", "counter_01", "Value"],
            ["test/ct/02", "counter_02", "att"],
            ["test/ct/03", "counter_03", "value"],
            ["test/ct/04", "counter_04", "13"],
            ["null", "counter_04",""],
            ]


        arr2 = [
            ["test/mca/01", "mca_01", "1"],
            ["test/mca/02", "mca_02", "a"],
            ["test/sca/03", "my_sca_03", "1"],
            ["test/sca/04", "mysca_04", "123"],
            ]

        pool = Pool()
        pool2 = Pool()
        pool.AcqChannelList = [json.dumps(
                {"name":a[0], "full_name":"%s/%s" % (a[1], a[2])}) for a in arr]
        pool2.AcqChannelList = [json.dumps(
                {"name":a[0], "full_name":"%s/%s" % (a[1], a[2])}) for a in arr2]
    
        
        for ar in arr:
            dd = Utils.getFullDeviceNames([pool, pool2], [ar[0]])
            self.assertEqual(dd, {ar[0]:ar[1]})

        for ar in arr2:
            dd = Utils.getFullDeviceNames([pool, pool2], [ar[0]])
            self.assertEqual(dd, {ar[0]:ar[1]})
        

        res = dict((ar[0],ar[1]) for ar in arr)
        res.update(dict((ar[0],ar[1]) for ar in arr2))

        lst = [ar[0] for ar in arr]
        lst.extend([ar[0] for ar in arr2])

        dd = Utils.getFullDeviceNames([pool, pool2], lst)
        self.assertEqual(dd, res)

        dd = Utils.getFullDeviceNames([pool, pool2])
        self.assertEqual(dd, res)

        lst.extend(["sfdsdf","sdfsfd"])
        dd = Utils.getFullDeviceNames([pool, pool2], lst)
        self.assertEqual(dd, res)
            
        


    ## getDeviceName test   
    def test_getMntGrpName_empty(self):
        fun = sys._getframe().f_code.co_name
        print "Run: %s.%s() " % (self.__class__.__name__, fun)
        

        arr = [
            {"name":"test/ct/01", "full_name":"mntgrp_01e"} ,
            {"name":"test/ct/02", "full_name":"mntgrp_02att"} ,
            {"name":"test/ct/03", "full_name":"mntgrp_03value"} ,
            {"name":"test/ct/04", "full_name":"mntgrp_04/13"} ,
            {"name":"null", "full_name":"mntgrp_04"} ,
            ]



        pool = Pool()
        pool.MeasurementGroupList = [json.dumps(a) for a in arr]
    
        import nxsrecconfig 
        dd = Utils.getFullDeviceNames([])
        self.assertEqual(dd, {})

        dd = Utils.getMntGrpName([], arr[0]["name"])
        self.assertEqual(dd, '')
        dd = Utils.getMntGrpName([pool], arr[4]["name"])
        self.assertEqual(dd, arr[4]["full_name"])


    def test_getMntGrpName_pool1(self):
        fun = sys._getframe().f_code.co_name
        print "Run: %s.%s() " % (self.__class__.__name__, fun)
        

        arr = [
            ["test/ct/01", "mntgrp_01Value"],
            ["test/ct/02", "mntgrp_02att"],
            ["test/ct/03", "mntgrp_03value"],
            ["test/ct/04", "mntgrp_0413"],
            ["null", "mntgrp_04"],
            ]



        pool = Pool()
        pool.MeasurementGroupList = [json.dumps(
                {"name":a[0], "full_name":a[1]}) for a in arr]
    
        
        for ar in arr:
            dd = Utils.getMntGrpName([pool], ar[0])
            self.assertEqual(dd, ar[1])

        

        dd = Utils.getMntGrpName([pool], "adsasd")
        self.assertEqual(dd, '')


    def test_getMntGrpName_pool2(self):
        fun = sys._getframe().f_code.co_name
        print "Run: %s.%s() " % (self.__class__.__name__, fun)
        

        arr = [
            ["test/ct/01", "mntgrp_01Value"],
            ["test/ct/02", "mntgrp_02att"],
            ["test/ct/03", "mntgrp_03value"],
            ["test/ct/04", "mntgrp_0413"],
            ["null", "mntgrp_04"],
            ]


        arr2 = [
            ["test/mca/01", "mgca_011"],
            ["test/mca/02", "mgca_02a"],
            ["test/sca/03", "mgy_sca_031"],
            ["test/sca/04", "mntysca_04123"],
            ]

        pool = Pool()
        pool2 = Pool()
        pool.MeasurementGroupList = [json.dumps(
                {"name":a[0], "full_name":a[1]}) for a in arr]
        pool2.MeasurementGroupList = [json.dumps(
                {"name":a[0], "full_name":a[1]}) for a in arr2]
    
        
        for ar in arr:
            dd = Utils.getMntGrpName([pool, pool2], ar[0])
            self.assertEqual(dd, ar[1])

        for ar in arr2:
            dd = Utils.getMntGrpName([pool, pool2], ar[0])
            self.assertEqual(dd, ar[1])
        

        dd = Utils.getMntGrpName([pool, pool2], "adsasd")
        self.assertEqual(dd, '')
            





    ## getDeviceControllers test   
    def test_getDeviceControllers_empty(self):
        fun = sys._getframe().f_code.co_name
        print "Run: %s.%s() " % (self.__class__.__name__, fun)
        

        arr = [
            {"name":"test/ct/01", "controller":"counter_01/Value"} ,
            {"name":"test/ct/02", "controller":"counter_02/att"} ,
            {"name":"test/ct/03", "controller":"counter_03/value"} ,
            {"name":"test/ct/04", "controller":"counter_04/13"} ,
            {"name":"null", "controller":"counter_04"} ,
            ]



        pool = Pool()
        pool.ExpChannelList = [json.dumps(a) for a in arr]
    
        import nxsrecconfig 
        dd = Utils.getDeviceControllers([], "test/ct/01")
        self.assertEqual(dd, {})

        dd = Utils.getDeviceControllers([], arr[0]["name"])
        self.assertEqual(dd, {})
        dd = Utils.getDeviceControllers([pool], arr[4]["name"])
        self.assertEqual(dd, {arr[4]["name"]:arr[4]["controller"]})
        
        dd = Utils.getDeviceControllers([pool], "sdfds")
        self.assertEqual(dd, {})




    ## getDeviceControllers test   
    def test_getDeviceControllers_pool1(self):
        fun = sys._getframe().f_code.co_name
        print "Run: %s.%s() " % (self.__class__.__name__, fun)
        

        arr = [
            ["test/ct/01", "counter_01"],
            ["test/ct/02", "counter_02att"],
            ["test/ct/03", "counter_03value"],
            ["test/ct/04", "counter_0413"],
            ["null", "counter_04"],
            ]

        pool = Pool()
        pool.ExpChannelList = [json.dumps(
                {"name":a[0], "controller":a[1]}) for a in arr]
    
        
        for ar in arr:
            dd = Utils.getDeviceControllers([pool], [ar[0]])
            self.assertEqual(dd, {ar[0]:ar[1]})
        

        dd = Utils.getDeviceControllers([pool], [ar[0] for ar in arr])
        self.assertEqual(dd, dict((ar[0],ar[1]) for ar in arr))

            


    def test_getDeviceControllers_pool2(self):
        fun = sys._getframe().f_code.co_name
        print "Run: %s.%s() " % (self.__class__.__name__, fun)
        

        arr = [
            ["test/ct/01", "counter_01Value"],
            ["test/ct/02", "counter_02att"],
            ["test/ct/03", "counter_03alue"],
            ["test/ct/04", "counter_0413"],
            ["null", "counter_04"],
            ]


        arr2 = [
            ["test/mca/01", "mca_01"],
            ["test/mca/02", "mca_02"],
            ["test/sca/03", "my_sca1"],
            ["test/sca/04", "mysca_123"],
            ]

        pool = Pool()
        pool2 = Pool()
        pool.ExpChannelList = [json.dumps(
                {"name":a[0], "controller":a[1]}) for a in arr]
        pool2.ExpChannelList = [json.dumps(
                {"name":a[0], "controller":a[1]}) for a in arr2]
    
        
        for ar in arr:
            dd = Utils.getDeviceControllers([pool, pool2], [ar[0]])
            self.assertEqual(dd, {ar[0]:ar[1]})

        for ar in arr2:
            dd = Utils.getDeviceControllers([pool, pool2], [ar[0]])
            self.assertEqual(dd, {ar[0]:ar[1]})
        

        res = dict((ar[0],ar[1]) for ar in arr)
        res.update(dict((ar[0],ar[1]) for ar in arr2))

        lst = [ar[0] for ar in arr]
        lst.extend([ar[0] for ar in arr2])

        dd = Utils.getDeviceControllers([pool, pool2], lst)
        self.assertEqual(dd, res)


        lst.extend(["sfdsdf","sdfsfd"])
        dd = Utils.getDeviceControllers([pool, pool2], lst)
        self.assertEqual(dd, res)
            
        

    def test_getTimers(self):
        fun = sys._getframe().f_code.co_name
        print "Run: %s.%s() " % (self.__class__.__name__, fun)
        

        arr = [
            ["test/ct/01", ["CTExpChannel"]],
            ["test/ct/02", ["conem", "CTExpChannel"]],
            ["test/ct/03", ["CTExpChannel", "ZeroDChannel"]],
            ["test/ct/04", ["oneD","CTExpChannel"]],
            ["null", ["counter_04"]],
            ]


        arr2 = [
            ["test/mca/01", ["CTExpChannel"]],
            ["test/mca/02", ["CTExpChannel2","CTExpChannel1"]],
            ["test/sca/03", ["CTExpChannel3","CTExpChannel123"]],
            ["test/sca/04", ["CTExpChannel","CTExpChannel2","CTExpChannel3"]],
            ]

        pool = Pool()
        pool2 = Pool()
        pool.ExpChannelList = [json.dumps(
                {"name":a[0], "interfaces":a[1]}) for a in arr]
        pool2.ExpChannelList = [json.dumps(
                {"name":a[0], "interfaces":a[1]}) for a in arr2]

        dd = Utils.getTimers([])
        self.assertEqual(dd, [])

        lst = [ar[0] for ar in arr if  "CTExpChannel" in ar[1]]

        dd = Utils.getTimers([pool])
        self.assertEqual(dd, lst)


        lst.extend([ar[0] for ar in arr2 if  "CTExpChannel" in ar[1]])
    
        
        dd = Utils.getTimers([pool, pool2])
        self.assertEqual(dd, lst)
            



    def test_addDevice_empty(self):
        fun = sys._getframe().f_code.co_name
        print "Run: %s.%s() " % (self.__class__.__name__, fun)
        

        arr = [
            ["test/ct/01", "counter_01Value"],
            ["test/ct/02", "counter_02att"],
            ["test/ct/03", "counter_03alue"],
            ["test/ct/04", "counter_0413"],
            ["null", "counter_04"],
            ]


        arr2 = [
            ["test/mca/01", "mca_01"],
            ["test/mca/02", "mca_02"],
            ["test/sca/03", "my_sca1"],
            ["test/sca/04", "mysca_123"],
            ]

        pool = Pool()
        pool2 = Pool()
        pool.ExpChannelList = [json.dumps(
                {"name":a[0], "controller":a[1]}) for a in arr]
        pool2.ExpChannelList = [json.dumps(
                {"name":a[0], "controller":a[1]}) for a in arr2]
    


        hsh = {}
        res =  Utils.addDevice("", [],[], hsh,"", 0)
        self.assertEqual(res, 0)
        self.assertEqual(hsh, {})

        hsh = {}
        res =  Utils.addDevice("", [], [pool, pool2], hsh, "", 0)
        self.assertEqual(res, 0)
        self.assertEqual(hsh, {})

        hsh = {}
        res =  Utils.addDevice("test/ct/012134", [], [pool, pool2], hsh, "", 0)
        self.assertEqual(res, 0)
        self.assertEqual(hsh, {})





    def test_addDevice_controller(self):
        fun = sys._getframe().f_code.co_name
        print "Run: %s.%s() " % (self.__class__.__name__, fun)
        


        aarr = [
            ["test/ct/01", self._simps.new_device_info_writer.name, "Value"],
            ["test/ct/02", self._simps.new_device_info_writer.name, "att"],
            ["test/ct/03", self._simps2.new_device_info_writer.name, "value"],
            ["test/ct/04", self._simps2.new_device_info_writer.name, "13"],
            ["null", self._simps2.new_device_info_writer.name,""],
            ]


        aarr2 = [
            ["test/mca/01", "mca_01", "1"],
            ["test/mca/02", "mca_02", "a"],
            ["test/sca/03", "my_sca_03", "1"],
            ["test/sca/04", "mysca_04", "123"],
            ]

        arr = [
            ["test/ct/01", "cntl_01Value", ["CTExpChannel"]],
            ["test/ct/02", "cntl_02att", ["conem", "CTExpChannel"]],
            ["test/ct/03", "cntl_03alue", ["CTExpChannel", "ZeroDChannel"]],
            ["test/ct/04", "cntl_0413", ["oneD","CTExpChannel"]],
            ["null", "cntl_04", ["counter_04"]],
            ]


        arr2 = [
            ["test/mca/01", "mca_01", ["CTExpChannel"]],
            ["test/mca/02", "mca_02", ["conem", "CTExpChannel"]],
            ["test/sca/03", "my_sca1", ["CTExpChannel2", "ZeroDChannel"]],
            ["test/sca/04", "mysca_123", ["CTExpChannel","CTExpChannel2","CTExpChannel3"]],
            ]

        pool = Pool()
        pool2 = Pool()
        pool.ExpChannelList = [json.dumps(
                {"name":a[0], "controller":a[1], "interfaces":a[2]}) for a in arr]
        pool2.ExpChannelList = [json.dumps(
                {"name":a[0], "controller":a[1], "interfaces":a[2]}) for a in arr2]
    



        hsh = {}
        self.myAssertRaise(PyTango.DevFailed, Utils.addDevice,
                           arr[0][0], [], [pool, pool2], hsh, "", 0)
        res = json.loads(self.cnt % ("",""))
        fr = {}
        fr['controllers'] = {}
        fr['controllers'][arr[0][1]]= res
        self.assertEqual(hsh, fr)

        pool.AcqChannelList = [json.dumps(
                {"name":a[0], "full_name":"%s/%s" % (a[1], a[2])}) for a in aarr]
        pool2.AcqChannelList = [json.dumps(
                {"name":a[0], "full_name":"%s/%s" % (a[1], a[2])}) for a in aarr2]

        hsh = {}
        res = Utils.addDevice(arr[0][0], [], [pool, pool2], hsh, "", 0)
        self.assertEqual(res, 1)
        jres = json.loads(self.cnt % ("",""))
        fr = {}
        fr['controllers'] = {}
        fr['controllers'][arr[0][1]]= jres
        ch = json.loads(self.chnl % (0,arr[0][0], "float64",
                                     "1",arr[0][0],"",arr[0][1],aarr[0][1],'"<mov>"',
                                "%s/%s" %(aarr[0][1], 'value')))
        fr['controllers'][arr[0][1]]['units']['0']['channels'][aarr[0][1]] = ch
        self.myAssertDict(hsh, fr)

        ch = json.loads(self.chnl % (0,arr[0][0], "float64","1",
                                     arr[0][0],"",arr[0][1],aarr[0][1],'"<mov>"',
                                "%s/%s" %(aarr[0][1], 'value')))
        fr['controllers'][arr[0][1]]['units']['0']['channels'][aarr[0][1]] = ch
        self.myAssertDict(hsh, fr)


        hsh = {}
        res = Utils.addDevice(arr[0][0], [], [pool, pool2], hsh, aarr[0][0], 0)
        self.assertEqual(res, 1)

        jres = json.loads(self.cnt % (aarr[0][1],aarr[0][1]))
        fr = {}
        fr['controllers'] = {}
        fr['controllers'][arr[0][1]]= jres
        ch = json.loads(self.chnl % (0, arr[0][0], "float64","1",
                                     arr[0][0],"",arr[0][1],aarr[0][1],'"<mov>"',
                                "%s/%s" %(aarr[0][1], 'value')))
        fr['controllers'][arr[0][1]]['units']['0']['channels'][aarr[0][1]] = ch
        self.myAssertDict(hsh, fr)



    def test_addDevice_controller_separate_ctrls(self):
        fun = sys._getframe().f_code.co_name
        print "Run: %s.%s() " % (self.__class__.__name__, fun)
        
        aarr = [
            ["test/ct/01", self._simps.new_device_info_writer.name, "Value"],
            ["test/ct/02", self._simps.new_device_info_writer.name, "att"],
            ["test/ct/03", self._simps2.new_device_info_writer.name, "value"],
            ["test/ct/04", self._simps2.new_device_info_writer.name, "13"],
            ["null", self._simps2.new_device_info_writer.name,""],
            ]

        arr = [
            ["test/ct/01", "cntl_01Value", ["CTExpChannel"]],
            ["test/ct/02", "cntl_02att", ["conem", "CTExpChannel"]],
            ["test/ct/03", "cntl_03alue", ["CTExpChannel", "ZeroDChannel"]],
            ["test/ct/04", "cntl_01Value413", ["oneD","CTExpChannel"]],
            ["null", "cntl_04", ["counter_04"]],
            ]


        aarr2 = [
            ["test/mca/01", self._simps.new_device_info_writer.name, "1"],
            ["test/mca/02", self._simps.new_device_info_writer.name, "a"],
            ["test/sca/03", self._simps2.new_device_info_writer.name, "1"],
            ["test/sca/04", self._simps2.new_device_info_writer.name, "123"],
            ]

        arr2 = [
            ["test/mca/01", "mca_01", ["CTExpChannel"]],
            ["test/mca/02", "mca_02", ["conem", "CTExpChannel"]],
            ["test/sca/03", "my_sca1", ["CTExpChannel2", "ZeroDChannel"]],
            ["test/sca/04", "mysca_123", ["CTExpChannel","CTExpChannel2","CTExpChannel3"]],
            ]

        pool = Pool()
        pool2 = Pool()
        pool.ExpChannelList = [json.dumps(
                {"name":a[0], "controller":a[1], "interfaces":a[2]}) for a in arr]
        pool2.ExpChannelList = [json.dumps(
                {"name":a[0], "controller":a[1], "interfaces":a[2]}) for a in arr2]
    
        pool.AcqChannelList = [json.dumps(
                {"name":a[0], "full_name":"%s/%s" % (a[1], a[2])}) for a in aarr]
        pool2.AcqChannelList = [json.dumps(
                {"name":a[0], "full_name":"%s/%s" % (a[1], a[2])}) for a in aarr2]

        hsh = {}
        iindex = 123
        index = iindex
        for i, a in enumerate(aarr):
            logger.debug("i = %s"% i)
            index = Utils.addDevice(a[0], [], [pool, pool2], hsh, a[0], index)
            self.assertEqual(index, iindex+1+i)
        fr = {}
        fr['controllers'] = {}

        for i, a in enumerate(aarr):
            jres = json.loads(self.cnt % (a[1],a[1]))
            fr['controllers'][arr[i][1]]= jres
            ch = json.loads(self.chnl % (iindex+i, a[0], "float64","1",
                                         a[0],"",arr[i][1],a[1],'"<mov>"',
                                    "%s/%s" %(a[1], 'value')))
            fr['controllers'][arr[i][1]]['units']['0']['channels'][a[1]] = ch
        self.myAssertDict(hsh, fr)


    def test_addDevice_controller_separate_ctrls_2pools(self):
        fun = sys._getframe().f_code.co_name
        print "Run: %s.%s() " % (self.__class__.__name__, fun)
        
        aarr = [
            ["test/ct/01", self._simps.new_device_info_writer.name, "Value"],
            ["test/ct/02", self._simps.new_device_info_writer.name, "att"],
            ["test/ct/03", self._simps2.new_device_info_writer.name, "value"],
            ["test/ct/04", self._simps2.new_device_info_writer.name, "13"],
            ["null", self._simps2.new_device_info_writer.name,""],
            ]

        arr = [
            ["test/ct/01", "cntl_01Value", ["CTExpChannel"]],
            ["test/ct/02", "cntl_02att", ["conem", "CTExpChannel"]],
            ["test/ct/03", "cntl_03alue", ["CTExpChannel", "ZeroDChannel"]],
            ["test/ct/04", "cntl_01Value413", ["oneD","CTExpChannel"]],
            ["null", "cntl_04", ["counter_04"]],
            ]

        aarr2 = [
            ["test/mca/01", self._simps.new_device_info_writer.name, "1"],
            ["test/mca/02", self._simps.new_device_info_writer.name, "a"],
            ["test/sca/03", self._simps2.new_device_info_writer.name, "1"],
            ["test/sca/04", self._simps2.new_device_info_writer.name, "123"],
            ]

        arr2 = [
            ["test/mca/01", "mca_01", ["CTExpChannel"]],
            ["test/mca/02", "mca_02", ["conem", "CTExpChannel"]],
            ["test/sca/03", "my_sca1", ["CTExpChannel2", "ZeroDChannel"]],
            ["test/sca/04", "mysca_123", ["CTExpChannel","CTExpChannel2","CTExpChannel3"]],
            ]

        pool = Pool()
        pool2 = Pool()
        pool.ExpChannelList = [json.dumps(
                {"name":a[0], "controller":a[1], "interfaces":a[2]}) for a in arr]
        pool2.ExpChannelList = [json.dumps(
                {"name":a[0], "controller":a[1], "interfaces":a[2]}) for a in arr2]
    
        pool.AcqChannelList = [json.dumps(
                {"name":a[0], "full_name":"%s/%s" % (a[1], a[2])}) for a in aarr]
        pool2.AcqChannelList = [json.dumps(
                {"name":a[0], "full_name":"%s/%s" % (a[1], a[2])}) for a in aarr2]

        hsh = {}
        iindex = 123
        index = iindex
        for i, a in enumerate(aarr):
            logger.debug("i = %s"% i)
            index = Utils.addDevice(a[0], [], [pool, pool2], hsh, a[0], index)
            self.assertEqual(index, iindex+1+i)

        for i, a in enumerate(aarr2):
            logger.debug("i = %s"% i)
            index = Utils.addDevice(a[0], [], [pool, pool2], hsh, a[0], index)
            self.assertEqual(index, iindex+1+i+len(aarr))

        fr = {}
        fr['controllers'] = {}
        for i, a in enumerate(aarr):
            jres = json.loads(self.cnt % (a[1],a[1]))
            fr['controllers'][arr[i][1]]= jres
            ch = json.loads(self.chnl % (iindex+i, a[0], "float64", 
                                         "1",a[0],"",arr[i][1],a[1],'"<mov>"',
                                         "%s/%s" %(a[1], 'value')))
            fr['controllers'][arr[i][1]]['units']['0']['channels'][a[1]] = ch
        for i, a in enumerate(aarr2):
            jres = json.loads(self.cnt % (a[1],a[1]))
            fr['controllers'][arr2[i][1]]= jres
            ch = json.loads(self.chnl % (iindex+i+len(aarr), a[0], "float64",
                                         "1",a[0],"",arr2[i][1],a[1],'"<mov>"',
                                         "%s/%s" %(a[1], 'value')))
            fr['controllers'][arr2[i][1]]['units']['0']['channels'][a[1]] = ch
        self.myAssertDict(hsh, fr)
            
            


    def test_addDevice_controller_ctrls(self):
        fun = sys._getframe().f_code.co_name
        print "Run: %s.%s() " % (self.__class__.__name__, fun)

        
        aarr = [
            ["test/ct/01", self._simps.new_device_info_writer.name, "Value"],
            ["test/ct/02", self._simps2.new_device_info_writer.name, "att"],
            ["test/ct/03", self._simps3.new_device_info_writer.name, "value"],
            ["test/ct/04", self._simps4.new_device_info_writer.name, "13"],
            ]

        arr = [
            ["test/ct/01", "cntl_01", ["CTExpChannel"]],
            ["test/ct/02", "cntl_01", ["conem", "CTExpChannel"]],
            ["test/ct/03", "cntl_01", ["CTExpChannel", "ZeroDChannel"]],
            ["test/ct/04", "cntl_01", ["oneD","CTExpChannel"]],
            ]


        aarr2 = [
            ["test/mca/01", self._simps.new_device_info_writer.name, "1"],
            ["test/mca/02", self._simps.new_device_info_writer.name, "a"],
            ["test/sca/03", self._simps2.new_device_info_writer.name, "1"],
            ["test/sca/04", self._simps2.new_device_info_writer.name, "123"],
            ]

        arr2 = [
            ["test/mca/01", "mca_01", ["CTExpChannel"]],
            ["test/mca/02", "mca_02", ["conem", "CTExpChannel"]],
            ["test/sca/03", "my_sca1", ["CTExpChannel2", "ZeroDChannel"]],
            ["test/sca/04", "mysca_123", ["CTExpChannel","CTExpChannel2","CTExpChannel3"]],
            ]

        pool = Pool()
        pool2 = Pool()
        pool.ExpChannelList = [json.dumps(
                {"name":a[0], "controller":a[1], "interfaces":a[2]}) for a in arr]
        pool2.ExpChannelList = [json.dumps(
                {"name":a[0], "controller":a[1], "interfaces":a[2]}) for a in arr2]
    
        pool.AcqChannelList = [json.dumps(
                {"name":a[0], "full_name":"%s/%s" % (a[1], a[2])}) for a in aarr]
        pool2.AcqChannelList = [json.dumps(
                {"name":a[0], "full_name":"%s/%s" % (a[1], a[2])}) for a in aarr2]

        hsh = {}
        iindex = 123
        index = iindex
        for i, a in enumerate(aarr):
            logger.debug("i = %s"% i)
            index = Utils.addDevice(a[0], [], [pool, pool2], hsh, aarr[0][0], index)
            self.assertEqual(index, iindex+1 + i)
        fr = {}
        fr['controllers'] = {}
        jres = json.loads(self.cnt % (aarr[0][1],aarr[0][1]))
        fr['controllers'][arr[0][1]]= jres

        for i, a in enumerate(aarr):
            ch = json.loads(self.chnl % (iindex+i, a[0], "float64",
                                         "1",a[0],"",arr[i][1],a[1],'"<mov>"',
                                         "%s/%s" %(a[1], 'value')))
            fr['controllers'][arr[i][1]]['units']['0']['channels'][a[1]] = ch
        self.myAssertDict(hsh, fr)


    def test_addDevice_controller_ctrls_2pools(self):
        fun = sys._getframe().f_code.co_name
        print "Run: %s.%s() " % (self.__class__.__name__, fun)

        
        aarr = [
            ["test/ct/01", self._simps.new_device_info_writer.name, "Value"],
            ["test/ct/02", self._simps2.new_device_info_writer.name, "att"],
            ["test/ct/03", self._simps3.new_device_info_writer.name, "value"],
            ["test/ct/04", self._simps4.new_device_info_writer.name, "13"],
            ]

        arr = [
            ["test/ct/01", "cntl_01", ["CTExpChannel"]],
            ["test/ct/02", "cntl_01", ["conem", "CTExpChannel"]],
            ["test/ct/03", "cntl_01", ["CTExpChannel", "ZeroDChannel"]],
            ["test/ct/04", "cntl_01", ["oneD","CTExpChannel"]],
            ]

        pool = Pool()
        pool2 = Pool()
        pool.ExpChannelList = [json.dumps(
                {"name":a[0], "controller":a[1], "interfaces":a[2]}) for a in arr[:2]]
        pool2.ExpChannelList = [json.dumps(
                {"name":a[0], "controller":a[1], "interfaces":a[2]}) for a in arr[2:]]
    
        pool.AcqChannelList = [json.dumps(
                {"name":a[0], "full_name":"%s/%s" % (a[1], a[2])}) for a in aarr[:2]]
        pool2.AcqChannelList = [json.dumps(
                {"name":a[0], "full_name":"%s/%s" % (a[1], a[2])}) for a in aarr[2:]]

        hsh = {}
        iindex = 123
        index = iindex
        for i, a in enumerate(aarr):
            logger.debug("i = %s"% i)
            index = Utils.addDevice(a[0], [], [pool, pool2], hsh, aarr[0][0], index)
            self.assertEqual(index, iindex+1 + i)
        fr = {}
        fr['controllers'] = {}
        jres = json.loads(self.cnt % (aarr[0][1],aarr[0][1]))
        fr['controllers'][arr[0][1]]= jres

        for i, a in enumerate(aarr):
            ch = json.loads(self.chnl % (iindex+i, a[0], "float64","1",
                                         a[0],"",arr[i][1],a[1],'"<mov>"',
                                         "%s/%s" %(a[1], 'value')))
            fr['controllers'][arr[i][1]]['units']['0']['channels'][a[1]] = ch
        self.myAssertDict(hsh, fr)

            

if __name__ == '__main__':
    unittest.main()

