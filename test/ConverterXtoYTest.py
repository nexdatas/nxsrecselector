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
# \package test nexdatas
# \file ConverterXtoYTest.py
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

from nxsrecconfig.Converter import ConverterXtoY

# if 64-bit machione
IS64BIT = (struct.calcsize("P") == 8)


# test fixture
class ConverterXtoYTest(unittest.TestCase):

    # constructor
    # \param methodName name of the test method

    def __init__(self, methodName):
        unittest.TestCase.__init__(self, methodName)
        try:
            self.__seed = long(binascii.hexlify(os.urandom(16)), 16)
        except NotImplementedError:
            self.__seed = long(time.time() * 256)

        self.__rnd = random.Random(self.__seed)

    # Exception tester
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
        self.assertTrue(isinstance(dct, dict))
        if not isinstance(dct2, dict):
            print "NOT DICT", type(dct2), dct2
            print "DICT", type(dct), dct
        self.assertTrue(isinstance(dct2, dict))
        if set(dct.keys()) ^ set(dct2.keys()):
            print 'DCT', dct.keys()
            print 'DCT2', dct2.keys()
            print "DIFF", set(dct.keys()) ^ set(dct2.keys())
        self.assertEqual(len(dct.keys()), len(dct2.keys()))
        for k, v in dct.items():
            self.assertTrue(k in dct2.keys())
            if isinstance(v, dict):
                self.myAssertDict(v, dct2[k])
            else:
                if v != dct2[k]:
                    print 'VALUES', k, v, dct2[k]
                self.assertEqual(v, dct2[k])

    def getRandomName(self, maxsize):
        letters = string.lowercase + string.uppercase + string.digits
        size = self.__rnd.randint(1, maxsize)
        return ''.join(self.__rnd.choice(letters) for _ in range(size))

    # test starter
    # \brief Common set up
    def setUp(self):
        print "SEED =", self.__seed
        print "\nsetting up..."

    # test closer
    # \brief Common tear down
    def tearDown(self):
        print "tearing down ..."

    def test_convert(self):
        fun = sys._getframe().f_code.co_name
        print "Run: %s.%s() " % (self.__class__.__name__, fun)

        mysel = {}
        cv = ConverterXtoY()
        self.assertEqual(cv.names, {})
        cv.convert(mysel)
        self.assertEqual(mysel, {})

        for i in range(2000):
            mysel = {}
            tnames = dict(
                (self.getRandomName(20), self.getRandomName(20))
                for _ in range(self.__rnd.randint(1, 20)))
            for k in tnames.keys():
                if k in tnames.values():
                    tnames.pop(k)
            names = {}
            for k, vl in tnames.items():
                names[vl] = k
            cv.names = dict(names)
            keys1 = self.__rnd.sample(names.keys(), self.__rnd.randint(
                0, len(names.keys())))
            keys2 = set([self.getRandomName(20) for _ in range(5)])
            keys2.update(keys1)
            for k in keys2:
                mysel[k] = self.getRandomName(20)
            for k in mysel.keys():
                if k in names.values():
                    mysel.pop(k)
                    keys2.remove(k)
            osel = dict(mysel)
            cv.convert(mysel)
            res = {}
            for k, vl in osel.items():
                if k in names:
                    res[names[k]] = vl
                else:
                    res[k] = vl

            self.myAssertDict(mysel, res)


if __name__ == '__main__':
    unittest.main()
