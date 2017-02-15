#!/usr/bin/env python
#   This file is part of nexdatas - Tango Server for NeXus data writer
#
#    Copyright (C) 2012-2017 DESY, Jan Kotanski <jkotan@mail.desy.de>
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
## \file ConverterTest.py
# unittests for field Tags running Tango Server
#
import unittest
import os
import sys
import subprocess
import random
import struct
import binascii
import string

from nxsrecconfig.Converter import (
    Converter, Converter1to2, Converter2to1,
    Converter2to3, Converter3to2)

## if 64-bit machione
IS64BIT = (struct.calcsize("P") == 8)


class MyConverter(object):

    def __init__(self, log_list):
        self.log_list = log_list
        self.names = {}

    def convert(self, selection):
        self.log_list.append("%s" % self.__class__.__name__)


class MyConverter1(MyConverter):
    pass


class MyConverter2(MyConverter):
    pass


class MyConverter3(MyConverter):
    pass


class MyConverter4(MyConverter):
    pass


## test fixture
class ConverterTest(unittest.TestCase):

    ## constructor
    # \param methodName name of the test method
    def __init__(self, methodName):
        unittest.TestCase.__init__(self, methodName)
        try:
            self.__seed = long(binascii.hexlify(os.urandom(16)), 16)
        except NotImplementedError:
            self.__seed = long(time.time() * 256)

        self.__rnd = random.Random(self.__seed)

    ## Exception tester
    # \param exception expected exception
    # \param method called method
    # \param args list with method arguments
    # \param kwargs dictionary with method arguments
    def myAssertRaise(self, exception, method, *args, **kwargs):
        err = None
        try:
            error = False
            method(*args, **kwargs)
        except exception, e:
            error = True
            err = e
        self.assertEqual(error, True)
        return err

    def myAssertDict(self, dct, dct2):
        logger.debug('dict %s' % type(dct))
        logger.debug("\n%s\n%s" % (dct, dct2))
        self.assertTrue(isinstance(dct, dict))
        if not isinstance(dct2, dict):
            print "NOT DICT", type(dct2), dct2
            print "DICT", type(dct), dct
        self.assertTrue(isinstance(dct2, dict))
        logger.debug("%s %s" % (len(dct.keys()), len(dct2.keys())))
        if set(dct.keys()) ^ set(dct2.keys()):
            print 'DCT', dct.keys()
            print 'DCT2', dct2.keys()
            print "DIFF", set(dct.keys()) ^ set(dct2.keys())
        self.assertEqual(len(dct.keys()), len(dct2.keys()))
        for k, v in dct.items():
            logger.debug("%s  in %s" % (str(k), str(dct2.keys())))
            self.assertTrue(k in dct2.keys())
            if isinstance(v, dict):
                self.myAssertDict(v, dct2[k])
            else:
                logger.debug("%s , %s" % (str(v), str(dct2[k])))
                if v != dct2[k]:
                    print 'VALUES', k, v, dct2[k]
                self.assertEqual(v, dct2[k])

    def getRandomString(self, maxsize):
        letters = [chr(i) for i in range(256)]
        size = self.__rnd.randint(1, maxsize)
        return ''.join(self.__rnd.choice(letters) for _ in range(size))

    ## test starter
    # \brief Common set up
    def setUp(self):
        print "SEED =", self.__seed
        print "\nsetting up..."

    ## test closer
    # \brief Common tear down
    def tearDown(self):
        print "tearing down ..."

    def test_constructor(self):
        fun = sys._getframe().f_code.co_name
        print "Run: %s.%s() " % (self.__class__.__name__, fun)

        arr = {
            "1.2.3": [1, 2, 3],
            "2.22.1": [2, 22, 1],
            "3.23.5": [3, 23, 5],
            "1.81.6": [1, 81, 6],
            "1.1.7": [1, 1, 7],
            "1.0.9": [1, 0, 9],
        }

        self.myAssertRaise(Exception, Converter, None)
        self.myAssertRaise(Exception, Converter, "")
        self.myAssertRaise(Exception, Converter, "3.4")
        self.myAssertRaise(Exception, Converter, "2")
        for k, ar in arr.items():
            cv = Converter(k)
            self.assertEqual(cv.majorversion, ar[0])
            self.assertEqual(cv.minorversion, ar[1])
            self.assertEqual(cv.patchversion, ar[2])
            self.assertEqual(len(cv.down), 2)
            self.assertEqual(len(cv.up), 2)
            self.assertTrue(isinstance(cv.up[0], Converter1to2))
            self.assertTrue(isinstance(cv.up[1], Converter2to3))
            self.assertTrue(isinstance(cv.down[1], Converter3to2))
            self.assertTrue(isinstance(cv.down[0], Converter2to1))

    def test_version(self):
        fun = sys._getframe().f_code.co_name
        print "Run: %s.%s() " % (self.__class__.__name__, fun)

        arr = {
            "1.2.3": [1, 2, 3],
            "2.22.1": [2, 22, 1],
            "3.23.5": [3, 23, 5],
            "1.81.6": [1, 81, 6],
            "1.1.7": [1, 1, 7],
            "1.0.9": [1, 0, 9],
        }

        self.myAssertRaise(Exception, Converter, None)
        self.myAssertRaise(Exception, Converter, "")
        self.myAssertRaise(Exception, Converter, "3.4")
        self.myAssertRaise(Exception, Converter, "2")
        ma, mi, pa = Converter.version({})
        self.assertEqual(ma, 1)
        self.assertEqual(mi, 0)
        self.assertEqual(pa, 0)
        for k, ar in arr.items():
            ma, mi, pa = Converter.version({"Version": k})

    def test_convert(self):
        fun = sys._getframe().f_code.co_name
        print "Run: %s.%s() " % (self.__class__.__name__, fun)
        histlog = []
        myver = "1.2.3"
        cv = Converter(myver)
        cv.up = []
        cv.down = []
        self.myAssertRaise(Exception, cv.convert, {"Version": "11.2.3"})
        mysel = {"Version": "1.0.1"}
        cv.convert(mysel)
        self.assertEqual(mysel["Version"], "1.0.1")
        cv.down = [MyConverter1(histlog), MyConverter2(histlog),
                   MyConverter3(histlog), MyConverter4(histlog)]

        histlog[:] = []
        mysel = {"Version": "3.23.3"}
        cv.convert(mysel)
        self.assertEqual(mysel["Version"], myver)
        self.assertEqual(histlog, ["MyConverter2", "MyConverter1"])

        histlog[:] = []
        mysel = {"Version": "1.23.3"}
        cv.convert(mysel)
        self.assertEqual(mysel["Version"], "1.23.3")
        self.assertEqual(histlog, [])

        histlog[:] = []
        mysel = {"Version": "2.13.3"}
        cv.convert(mysel)
        self.assertEqual(mysel["Version"], myver)
        self.assertEqual(histlog, ["MyConverter1"])

        histlog[:] = []
        mysel = {"Version": "4.03.3"}
        cv.convert(mysel)
        self.assertEqual(mysel["Version"], myver)
        self.assertEqual(histlog,
                         ["MyConverter3", "MyConverter2", "MyConverter1"])

        histlog[:] = []
        cv.down = []
        myver = "3.2.3"
        cv = Converter(myver)
        self.myAssertRaise(Exception, cv.convert, {"Version": "11.2.3"})
        cv.up = [
            MyConverter1(histlog), MyConverter2(histlog),
            MyConverter3(histlog), MyConverter4(histlog)
        ]

        mysel = {"Version": "1.03.3"}
        cv.convert(mysel)
        self.assertEqual(mysel["Version"], myver)
        self.assertEqual(histlog, ["MyConverter1", "MyConverter2"])
        histlog[:] = []
        mysel = {"Version": "3.90.3"}
        cv.convert(mysel)
        self.assertEqual(mysel["Version"], "3.90.3")
        self.assertEqual(histlog, [])
        histlog[:] = []
        mysel = {"Version": "2.0.3"}
        cv.convert(mysel)
        self.assertEqual(mysel["Version"], myver)
        self.assertEqual(histlog, ["MyConverter2"])
        histlog[:] = []

    def test_allkeys(self):
        fun = sys._getframe().f_code.co_name
        print "Run: %s.%s() " % (self.__class__.__name__, fun)
        histlog = []
        myver = "1.2.3"
        cv = Converter(myver)
        self.assertEqual(cv.allkeys({}), set([
            'UserData',
            'UnplottedComponents',
            'DataSourceSelection',
            'DefaultDynamicLinks',
            'DataSourcePreselection',
            'PreselectingDataSources',
            'ComponentPreselection',
            'ComponentSelection',
            'DefaultDynamicPath',
            'DynamicPath',
            'AutomaticComponentGroup',
            'DynamicLinks',
            'ComponentGroup',
            'HiddenElements',
            'DataSourceGroup',
            'AutomaticDataSources',
            'DataRecord',
            'PreselectedDataSources',
            'InitDataSources'
        ]))

        cv.up = []
        cv.down = []
        self.assertEqual(cv.allkeys({}), set())
        for i in range(20):
            lk = []
            kk = self.__rnd.randint(0, 20)
            for k in range(kk):
                lk.append(MyConverter1(histlog))
                lk[-1].names = dict(
                    (self.getRandomString(20), self.getRandomString(20))
                    for _ in range(self.__rnd.randint(0, 20)))
            cv.up[:] = lk
            names = dict(
                (self.getRandomString(20), self.getRandomString(20))
                for _ in range(self.__rnd.randint(0, 20)))
            for k in names.keys():
                if k in names.values():
                    names.pop(k)
            res = set(names.keys())
            for ll in lk:
                res.update(ll.names.keys())
                res.update(ll.names.values())
            self.assertEqual(cv.allkeys(names), res)


if __name__ == '__main__':
    unittest.main()
