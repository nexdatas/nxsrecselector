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
## \file MacroServerPoolTest.py
# unittests for TangoDsItemTest running Tango Server
#
import unittest
import os
import sys
import subprocess
import random
import struct
import threading
import binascii
import Queue
import PyTango

import TestMacroServerSetUp
import TestPoolSetUp
import TestServerSetUp

from nxsrecconfig.MacroServerPools import MacroServerPools


## if 64-bit machione
IS64BIT = (struct.calcsize("P") == 8)




## test fixture
class MacroServerPoolTest(unittest.TestCase):

    ## constructor
    # \param methodName name of the test method
    def __init__(self, methodName):
        unittest.TestCase.__init__(self, methodName)


        self._bint = "int64" if IS64BIT else "int32"
        self._buint = "uint64" if IS64BIT else "uint32"
        self._bfloat = "float64" if IS64BIT else "float32"

        self._ms = TestMacroServerSetUp.TestMacroServerSetUp()
        self._pool = TestPoolSetUp.TestPoolSetUp()
#        self._ms2 = TestMacroServerSetUp.TestMacroServerSetUp("mstestp09/testts/t2r228", "MSTESTS2")
        self._simps = TestServerSetUp.TestServerSetUp()
#        self._simps2 = TestServerSetUp.TestServerSetUp( "ttestp09/testts/t2r228", "S2")
 #       self._simps3 = TestServerSetUp.TestServerSetUp( "ttestp09/testts/t3r228", "S3") 
 #       self._simps4 = TestServerSetUp.TestServerSetUp( "ttestp09/testts/t4r228", "S4")
 #       self._simpsoff = TestServerSetUp.TestServerSetUp( "ttestp09/testts/t5r228", "OFF")


        try:
            self.__seed  = long(binascii.hexlify(os.urandom(16)), 16)
        except NotImplementedError:
            self.__seed  = long(time.time() * 256) 
         
        self.__rnd = random.Random(self.__seed)


    ## test starter
    # \brief Common set up
    def setUp(self):
        print "SEED =", self.__seed 
        self._ms.setUp()
        self._pool.setUp()
#        self._ms2.setUp()
        self._simps.setUp()
#        self._simps2.setUp()
#        self._simps3.setUp()
#        self._simps4.setUp()
#        self._simpsoff.add()
        print "\nsetting up..."        

    ## test closer
    # \brief Common tear down
    def tearDown(self):
        print "tearing down ..."
#        self._simpsoff.delete()
#        self._simps4.tearDown()
#        self._simps3.tearDown()
#        self._simps2.tearDown()
        self._simps.tearDown()
#        self._ms2.tearDown()
        self._pool.tearDown()
        self._ms.tearDown()
 
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
        msp = MacroServerPools(0)
        msp = MacroServerPools(10)

    ## constructor test
    # \brief It tests default settings
    def test_getMacroServer(self):
        fun = sys._getframe().f_code.co_name
        print "Run: %s.%s() " % (self.__class__.__name__, fun)
        msp = MacroServerPools(0)
        msp = MacroServerPools(10)
        self.myAssertRaise(Exception, msp.updateMacroServer, "sfdsTESTdfdf/sdfsdf/sdffsf")
        self.myAssertRaise(Exception, msp.updateMacroServer, "")
        self.myAssertRaise(Exception, msp.getMacroServer, "")
        self.myAssertRaise(Exception, msp.getPools, "")

        msp.updateMacroServer(self._ms.door.keys()[0])
        self.assertEqual(msp.getMacroServer(""),self._ms.ms.keys()[0])
        self.assertEqual(msp.getMacroServer(self._ms.door.keys()[0]),self._ms.ms.keys()[0])
        self.assertEqual(msp.getPools(self._ms.door.keys()[0]), [])
        self.myAssertRaise(Exception, msp.getPools, "")

        self.myAssertRaise(Exception, msp.updateMacroServer, "sfdsTESTdfdf/sdfsdf/sdffsf")
        self.myAssertRaise(Exception, msp.updateMacroServer, "")
        self.myAssertRaise(Exception, msp.getMacroServer, "")
        self.myAssertRaise(Exception, msp.getPools, "")

        self.assertEqual(msp.getPools(self._ms.door.keys()[0]), [])

        self._ms.dps[self._ms.ms.keys()[0]].DoorList = []
        self.myAssertRaise(Exception, msp.updateMacroServer, self._ms.door.keys()[0])
        self.myAssertRaise(Exception, msp.getMacroServer, "")
        self.myAssertRaise(Exception, msp.getPools, self._ms.door.keys()[0])


    ## constructor test
    # \brief It tests default settings
    def test_getPool(self):
        fun = sys._getframe().f_code.co_name
        print "Run: %s.%s() " % (self.__class__.__name__, fun)
        msp = MacroServerPools(10)
        db = PyTango.Database()
        db.put_device_property(self._ms.ms.keys()[0], {'PoolNames':self._pool.dp.name()})
        self._ms.dps[self._ms.ms.keys()[0]].Init()

        self.myAssertRaise(Exception, msp.updateMacroServer, "sfdsTESTdfdf/sdfsdf/sdffsf")
        self.myAssertRaise(Exception, msp.updateMacroServer, "")
        self.myAssertRaise(Exception, msp.getMacroServer, "")
        self.myAssertRaise(Exception, msp.getPools, "")

        msp.updateMacroServer(self._ms.door.keys()[0])
        self.assertEqual(msp.getMacroServer(""), self._ms.ms.keys()[0])
        self.assertEqual(msp.getMacroServer(self._ms.door.keys()[0]),self._ms.ms.keys()[0])
        pools = msp.getPools(self._ms.door.keys()[0])
        self.assertEqual(len(pools), 1)
        self.assertTrue(isinstance(pools[0], PyTango.DeviceProxy))
        self.assertEqual(pools[0].name(), self._pool.dp.name())
        
        pools = msp.getPools("sdfs")
        self.assertEqual(len(pools), 1)
        self.assertTrue(isinstance(pools[0], PyTango.DeviceProxy))
        self.assertEqual(pools[0].name(), self._pool.dp.name())

        self.myAssertRaise(Exception, msp.updateMacroServer, "sfdsTESTdfdf/sdfsdf/sdffsf")
        self.myAssertRaise(Exception, msp.updateMacroServer, "")
        self.myAssertRaise(Exception, msp.getMacroServer, "")

        pools = msp.getPools(self._ms.door.keys()[0])
        self.assertEqual(len(pools), 1)
        self.assertTrue(isinstance(pools[0], PyTango.DeviceProxy))
        self.assertEqual(pools[0].name(), self._pool.dp.name())

        pools = msp.getPools("sdfs")
        self.assertEqual(len(pools), 1)
        self.assertTrue(isinstance(pools[0], PyTango.DeviceProxy))
        self.assertEqual(pools[0].name(), self._pool.dp.name())

        self._ms.dps[self._ms.ms.keys()[0]].DoorList = []
        self.myAssertRaise(Exception, msp.updateMacroServer, self._ms.door.keys()[0])
        self.myAssertRaise(Exception, msp.getMacroServer, "")
        self.myAssertRaise(Exception, msp.getPools, "")
        
        self.myAssertRaise(Exception, msp.getPools, self._ms.door.keys()[0])



    ## constructor test
    # \brief It tests default settings
    def test_getPool_1to3(self):
        fun = sys._getframe().f_code.co_name
        print "Run: %s.%s() " % (self.__class__.__name__, fun)
        doors = ["door2testp09/testts/t1r228","door2testp09/testts/t2r228","door2testp09/testts/t3r228"]
        msname = "ms2testp09/testts/t1r228"
        try:
            
            ms2 = TestMacroServerSetUp.TestMacroServerSetUp("MSTESTS1TO3", [msname], doors)
            ms2.setUp()

            msp = MacroServerPools(10)
            db = PyTango.Database()
            db.put_device_property(ms2.ms.keys()[0], {'PoolNames':self._pool.dp.name()})
            ms2.dps[ms2.ms.keys()[0]].Init()

            
            for i in range(3):
                ms2.dps[ms2.ms.keys()[0]].DoorList = doors
                print "doors", doors[i]
                self.myAssertRaise(Exception, msp.updateMacroServer, "sfdsTESTdfdf/sdfsdf/sdffsf")
                self.myAssertRaise(Exception, msp.updateMacroServer, "")
                self.myAssertRaise(Exception, msp.getMacroServer, "")
                self.myAssertRaise(Exception, msp.getPools, "")
                print doors[i]
                msp.updateMacroServer(doors[i])
                self.assertEqual(msp.getMacroServer(""), ms2.ms.keys()[0])
                self.assertEqual(msp.getMacroServer(doors[i]),ms2.ms.keys()[0])
                pools = msp.getPools(doors[i])
                self.assertEqual(len(pools), 1)
                self.assertTrue(isinstance(pools[0], PyTango.DeviceProxy))
                self.assertEqual(pools[0].name(), self._pool.dp.name())

                pools = msp.getPools("sdfs")
                self.assertEqual(len(pools), 1)
                self.assertTrue(isinstance(pools[0], PyTango.DeviceProxy))
                self.assertEqual(pools[0].name(), self._pool.dp.name())

                self.myAssertRaise(Exception, msp.updateMacroServer, "sfdsTESTdfdf/sdfsdf/sdffsf")
                self.myAssertRaise(Exception, msp.updateMacroServer, "")
                self.myAssertRaise(Exception, msp.getMacroServer, "")

                pools = msp.getPools(doors[i])
                self.assertEqual(len(pools), 1)
                self.assertTrue(isinstance(pools[0], PyTango.DeviceProxy))
                self.assertEqual(pools[0].name(), self._pool.dp.name())

                pools = msp.getPools("sdfs")
                self.assertEqual(len(pools), 1)
                self.assertTrue(isinstance(pools[0], PyTango.DeviceProxy))
                self.assertEqual(pools[0].name(), self._pool.dp.name())

                ms2.dps[ms2.ms.keys()[0]].DoorList = []
                self.myAssertRaise(Exception, msp.updateMacroServer, doors[i])
                self.myAssertRaise(Exception, msp.getMacroServer, "")
                self.myAssertRaise(Exception, msp.getPools, "")

                self.myAssertRaise(Exception, msp.getPools, doors[i])
        finally:
            ms2.tearDown()


    ## constructor test
    # \brief It tests default settings
    def test_getPool_3to3(self):
        fun = sys._getframe().f_code.co_name
        print "Run: %s.%s() " % (self.__class__.__name__, fun)
        doors = ["door3testp09/testts/t1r228","door3testp09/testts/t2r228","door3testp09/testts/t3r228"]
        mss =  ["ms3testp09/testts/t1r228", "ms3testp09/testts/t2r228", "ms3testp09/testts/t3r228"]
        try:
            
            ms3 = TestMacroServerSetUp.TestMacroServerSetUp("MSTESTS3TO3", mss, doors)
            ms3.setUp()

            msp = MacroServerPools(10)
            db = PyTango.Database()
            for j, ms in enumerate(mss):
                db.put_device_property(ms, {'PoolNames':self._pool.dp.name()})
                ms3.dps[ms].Init()
            

            for i, ms in enumerate(mss):
                ms3.dps[ms].DoorList = [doors[i]]
                print "ms", ms, "doors", doors[i]
                self.myAssertRaise(Exception, msp.updateMacroServer, "sfdsTESTdfdf/sdfsdf/sdffsf")
                self.myAssertRaise(Exception, msp.updateMacroServer, "")
                self.myAssertRaise(Exception, msp.getMacroServer, "")
                self.myAssertRaise(Exception, msp.getPools, "")
                print doors[i]
                msp.updateMacroServer(doors[i])
                self.assertEqual(msp.getMacroServer(""), ms)
                self.assertEqual(msp.getMacroServer(doors[i]),ms)
                pools = msp.getPools(doors[i])
                self.assertEqual(len(pools), 1)
                self.assertTrue(isinstance(pools[0], PyTango.DeviceProxy))
                self.assertEqual(pools[0].name(), self._pool.dp.name())

                pools = msp.getPools("sdfs")
                self.assertEqual(len(pools), 1)
                self.assertTrue(isinstance(pools[0], PyTango.DeviceProxy))
                self.assertEqual(pools[0].name(), self._pool.dp.name())

                self.myAssertRaise(Exception, msp.updateMacroServer, "sfdsTESTdfdf/sdfsdf/sdffsf")
                self.myAssertRaise(Exception, msp.updateMacroServer, "")
                self.myAssertRaise(Exception, msp.getMacroServer, "")

                pools = msp.getPools(doors[i])
                self.assertEqual(len(pools), 1)
                self.assertTrue(isinstance(pools[0], PyTango.DeviceProxy))
                self.assertEqual(pools[0].name(), self._pool.dp.name())

                pools = msp.getPools("sdfs")
                self.assertEqual(len(pools), 1)
                self.assertTrue(isinstance(pools[0], PyTango.DeviceProxy))
                self.assertEqual(pools[0].name(), self._pool.dp.name())

                ms3.dps[ms].DoorList = []
                self.myAssertRaise(Exception, msp.updateMacroServer, doors[i])
                self.myAssertRaise(Exception, msp.getMacroServer, "")
                self.myAssertRaise(Exception, msp.getPools, "")

                self.myAssertRaise(Exception, msp.getPools, doors[i])
        finally:
            ms3.tearDown()
                        

if __name__ == '__main__':
    unittest.main()
