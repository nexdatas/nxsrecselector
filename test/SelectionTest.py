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
## \file SelectionTest.py
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
import json

from nxsrecconfig.Selection import Selection


## if 64-bit machione
IS64BIT = (struct.calcsize("P") == 8)


## test fixture
class SelectionTest(unittest.TestCase):

    ## constructor
    # \param methodName name of the test method
    def __init__(self, methodName):
        unittest.TestCase.__init__(self, methodName)

        self._tfname = "field"
        self._tfname = "group"
        self._fattrs = {"short_name": "test", "units": "m"}

        ## default zone
        self.__defaultzone = 'Europe/Berlin'
        ## default mntgrp
        self.__defaultmntgrp = 'nxsmntgrp'

        self._bint = "int64" if IS64BIT else "int32"
        self._buint = "uint64" if IS64BIT else "uint32"
        self._bfloat = "float64" if IS64BIT else "float32"

        self._keys = [
            ("Timer", '[]'),
            ("OrderedChannels", '[]'),
            ("ComponentGroup", '{}'),
            ("AutomaticComponentGroup", '{}'),
            ("AutomaticDataSources", '[]'),
            ("DataSourceGroup", '{}'),
            ("InitDataSources", '[]'),
            ("OptionalComponents", '[]'),
            ("AppendEntry", False),
            ("ComponentsFromMntGrp", False),
            ("ConfigVariables", '{}'),
            ("DataRecord", '{}'),
            ("Labels", '{}'),
            ("LabelPaths", '{}'),
            ("LabelLinks", '{}'),
            ("HiddenElements", '[]'),
            ("LabelTypes", '{}'),
            ("LabelShapes", '{}'),
            ("DynamicComponents", True),
            ("DynamicLinks", True),
            ("DynamicPath",
             '/entry$var.serialno:NXentry/NXinstrument/collection'),
            ("TimeZone", self.__defaultzone),
            ("ConfigDevice", ''),
            ("WriterDevice", ''),
            ("Door", ''),
            ("MntGrp", '')
        ]

        self.__dump = {}

        try:
            self.__seed = long(binascii.hexlify(os.urandom(16)), 16)
        except NotImplementedError:
            self.__seed = long(time.time() * 256)

        self.__rnd = random.Random(self.__seed)

    ## test starter
    # \brief Common set up
    def setUp(self):
        print "SEED =", self.__seed
        print "\nsetting up..."

    ## test closer
    # \brief Common tear down
    def tearDown(self):
        print "tearing down ..."

    def dump(self, el):
        self.__dump = {}
        for key, vl in el.items():
            self.__dump[key] = vl

    def compareToDump(self, el, excluded=None):
        exc = set(excluded or [])
        dks = set(self.__dump.keys()) - exc
        eks = set(el.keys()) - exc
        self.assertEqual(dks, eks)
        for key in dks:
            self.assertEqual(self.__dump[key], el[key])

    ## constructor test
    # \brief It tests default settings
    def test_constructor(self):
        fun = sys._getframe().f_code.co_name
        print "Run: %s.%s() " % (self.__class__.__name__, fun)
        el = Selection()
        self.assertTrue(isinstance(el, dict))
        self.assertEqual(len(el.keys()), len(self._keys))
        for key, vl in self._keys:
            self.assertTrue(key in el.keys())
            self.assertEqual(el[key], vl)

    ## constructor test
    # \brief It tests default settings
    def test_reset(self):
        fun = sys._getframe().f_code.co_name
        print "Run: %s.%s() " % (self.__class__.__name__, fun)
        el = Selection()
        el.clear()
        self.assertEqual(len(el.keys()), 0)
        el.reset()
        self.assertTrue(isinstance(el, dict))
        self.assertEqual(len(el.keys()), len(self._keys))
        for key, vl in self._keys:
            self.assertTrue(key in el.keys())
            self.assertEqual(el[key], vl)

    def getRandomName(self, maxsize):
        letters = string.lowercase + string.uppercase + string.digits
        size = self.__rnd.randint(1, maxsize)
        return ''.join(self.__rnd.choice(letters) for _ in range(size))

    ## deselect test
    def test_deselect(self):
        fun = sys._getframe().f_code.co_name
        print "Run: %s.%s() " % (self.__class__.__name__, fun)
        for i in range(20):
            el = Selection()
            el.deselect()
            self.assertEqual(len(el.keys()), len(self._keys))
            for key, vl in self._keys:
                self.assertTrue(key in el.keys())
                self.assertEqual(el[key], vl)

            cps = {}
            dss = {}
            lcp = self.__rnd.randint(1, 40)
            lds = self.__rnd.randint(1, 40)
            for i in range(lcp):
                cps[self.getRandomName(10)] = bool(self.__rnd.randint(0, 1))
            for i in range(lds):
                dss[self.getRandomName(10)] = bool(self.__rnd.randint(0, 1))
            el["ComponentGroup"] = json.dumps(cps)
            el["DataSourceGroup"] = json.dumps(dss)
            el["InitDataSources"] = json.dumps(
                self.__rnd.sample(dss, self.__rnd.randint(1, lds)))
            self.dump(el)

            el.deselect()

            ncps = json.loads(el["ComponentGroup"])
            ndss = json.loads(el["DataSourceGroup"])

            self.assertEqual(el["InitDataSources"], '[]')
            self.assertEqual(len(cps), len(ncps))
            self.assertEqual(len(dss), len(ndss))
            for key in cps.keys():
                self.assertTrue(key in ncps.keys())
                self.assertEqual(ncps[key], False)
            for key in dss.keys():
                self.assertTrue(key in ndss.keys())
                self.assertEqual(ndss[key], False)

            self.compareToDump(el, ["ComponentGroup", "DataSourceGroup",
                                    "InitDataSources"])

    ## updateAutomaticDataSources test
    def test_updateAutomaticDataSources(self):
        fun = sys._getframe().f_code.co_name
        print "Run: %s.%s() " % (self.__class__.__name__, fun)
        for i in range(20):
            el = Selection()
            el.updateAutomaticDataSources(None)
            self.assertEqual(len(el.keys()), len(self._keys))
            for key, vl in self._keys:
                self.assertTrue(key in el.keys())
                self.assertEqual(el[key], vl)

            lds1 = self.__rnd.randint(1, 40)
            lds2 = self.__rnd.randint(1, 40)
            lds3 = self.__rnd.randint(1, 40)
            dss1 = [self.getRandomName(10) for _ in range(lds1)]
            dss2 = [self.getRandomName(10) for _ in range(lds2)]
            dss3 = [self.getRandomName(10) for _ in range(lds3)]

            el["AutomaticDataSources"] = json.dumps(
                list(set(dss1) | set(dss2)))
            self.dump(el)
            el.updateAutomaticDataSources(None)

            self.compareToDump(el, ["AutomaticDataSources"])
            self.assertEqual(set(list(set(dss2) | set(dss1))),
                             set(json.loads(el["AutomaticDataSources"])))

            el.updateAutomaticDataSources(list(set(dss3) | set(dss2)))

            self.assertEqual(set(list(set(dss3) | set(dss2) | set(dss1))),
                             set(json.loads(el["AutomaticDataSources"])))

            self.compareToDump(el, ["AutomaticDataSources"])

    ## updateOrderedChannels test
    def test_updateOrderedChannels(self):
        fun = sys._getframe().f_code.co_name
        print "Run: %s.%s() " % (self.__class__.__name__, fun)
        for i in range(20):
            el = Selection()
            el.updateOrderedChannels([])
            self.assertEqual(len(el.keys()), len(self._keys))
            for key, vl in self._keys:
                self.assertTrue(key in el.keys())
                self.assertEqual(el[key], vl)

            lds1 = self.__rnd.randint(1, 40)
            lds2 = self.__rnd.randint(1, 40)
            lds3 = self.__rnd.randint(1, 40)
            dss1 = [self.getRandomName(10) for _ in range(lds1)]
            dss2 = [self.getRandomName(10) for _ in range(lds2)]
            dss3 = [self.getRandomName(10) for _ in range(lds3)]

            dss = []
            dss.extend(dss2)
            for ds in dss1:
                if ds not in dss:
                    dss.append(ds)
            pchs = []
            pchs.extend(dss2)
            for ds in dss3:
                if ds not in pchs:
                    pchs.append(ds)
            pchs = sorted(pchs)
            el["OrderedChannels"] = json.dumps(dss)
            self.dump(el)

            el.updateOrderedChannels(pchs)

            self.compareToDump(el, ["OrderedChannels"])

            ndss = json.loads(el["OrderedChannels"])
            odss = []
            odss.extend(dss2)
            for ds in dss3:
                if ds not in odss:
                    odss.append(ds)

            self.assertEqual(ndss[:len(dss2)], odss[:len(dss2)])
            self.assertEqual(set(ndss), set(odss))

    ## deselect test
    def test_updateComponentGroup(self):
        fun = sys._getframe().f_code.co_name
        print "Run: %s.%s() " % (self.__class__.__name__, fun)
        for i in range(20):
            el = Selection()
            el.deselect()
            self.assertEqual(len(el.keys()), len(self._keys))
            for key, vl in self._keys:
                self.assertTrue(key in el.keys())
                self.assertEqual(el[key], vl)

            cps = {}
            dss = {}
            lcp = self.__rnd.randint(1, 40)
            lds = self.__rnd.randint(1, 40)
            for i in range(lcp):
                cps[self.getRandomName(10)] = bool(self.__rnd.randint(0, 1))
            for i in range(lds):
                dss[self.getRandomName(10)] = bool(self.__rnd.randint(0, 1))
            ccps = self.__rnd.sample(cps, self.__rnd.randint(1, lcp))
            for cp in ccps:
                dss[cp] = bool(self.__rnd.randint(0, 1))
            el["ComponentGroup"] = json.dumps(cps)
            el["DataSourceGroup"] = json.dumps(dss)
            common = set(cps) & set(dss)
            self.dump(el)

            el.updateComponentGroup()

            ncps = json.loads(el["ComponentGroup"])
            ndss = json.loads(el["DataSourceGroup"])

            self.assertEqual(len(cps), len(ncps) + len(common))
            for key in cps.keys():
                if key not in common:
                    self.assertTrue(key in ncps.keys())
                    self.assertEqual(ncps[key], cps[key])
            self.compareToDump(el, ["ComponentGroup"])

    ## deselect test
    def test_updateComponentGroup(self):
        fun = sys._getframe().f_code.co_name
        print "Run: %s.%s() " % (self.__class__.__name__, fun)
        for i in range(20):
            el = Selection()
            el.deselect()
            self.assertEqual(len(el.keys()), len(self._keys))
            for key, vl in self._keys:
                self.assertTrue(key in el.keys())
                self.assertEqual(el[key], vl)

            dss = {}
            lall = self.__rnd.randint(1, 40)
            adss = [self.getRandomName(10) for _ in range(lall)]

            dssn = self.__rnd.sample(adss, self.__rnd.randint(1, lall))
            chs = self.__rnd.sample(adss, self.__rnd.randint(1, lall))
            cdss = self.__rnd.sample(adss, self.__rnd.randint(1, lall))

            for ds in dssn:
                dss[ds] = bool(self.__rnd.randint(0, 1))
            el["DataSourceGroup"] = json.dumps(dss)

            self.dump(el)

            el.updateDataSourceGroup(chs, cdss)

            ndss = json.loads(el["DataSourceGroup"])
            existing = set(dssn) & (set(chs) | set(cdss))

            for key, value in ndss.items():
                if key in existing:
                    self.assertEqual(ndss[key], dss[key])
                else:
                    self.assertTrue(key in chs)
                    self.assertTrue(not value)
            self.compareToDump(el, ["DataSourceGroup"])

    ## deselect test
    def test_updateMntGrp(self):
        fun = sys._getframe().f_code.co_name
        print "Run: %s.%s() " % (self.__class__.__name__, fun)
        el = Selection()
        el.deselect()
        self.assertEqual(len(el.keys()), len(self._keys))
        for key, vl in self._keys:
            self.assertTrue(key in el.keys())
            self.assertEqual(el[key], vl)

        self.dump(el)

        el.updateMntGrp()
        self.assertEqual(el["MntGrp"], self.__defaultmntgrp)
        self.compareToDump(el, ["MntGrp"])

        mymg = "somthing123"
        el["MntGrp"] = mymg
        el.updateMntGrp()
        self.assertEqual(el["MntGrp"], mymg)
        self.compareToDump(el, ["MntGrp"])

        mymg = ""
        el["MntGrp"] = mymg
        el.updateMntGrp()
        self.assertEqual(el["MntGrp"], self.__defaultmntgrp)
        self.compareToDump(el, ["MntGrp"])

        el.clear()
        el.updateMntGrp()
        self.assertEqual(el["MntGrp"], self.__defaultmntgrp)

    ## deselect test
    def test_updateTimeZone(self):
        fun = sys._getframe().f_code.co_name
        print "Run: %s.%s() " % (self.__class__.__name__, fun)
        el = Selection()
        el.deselect()
        self.assertEqual(len(el.keys()), len(self._keys))
        for key, vl in self._keys:
            self.assertTrue(key in el.keys())
            self.assertEqual(el[key], vl)

        self.dump(el)

        el.updateTimeZone()
        self.assertEqual(el["TimeZone"], self.__defaultzone)
        self.compareToDump(el, ["TimeZone"])

        mymg = "somthing123"
        el["TimeZone"] = mymg
        el.updateTimeZone()
        self.assertEqual(el["TimeZone"], mymg)
        self.compareToDump(el, ["TimeZone"])

        mymg = ""
        el["TimeZone"] = mymg
        el.updateTimeZone()
        self.assertEqual(el["TimeZone"], self.__defaultzone)
        self.compareToDump(el, ["TimeZone"])

        el.clear()
        el.updateTimeZone()
        self.assertEqual(el["TimeZone"], self.__defaultzone)

    ## deselect test
    def test_resetMntGrp(self):
        fun = sys._getframe().f_code.co_name
        print "Run: %s.%s() " % (self.__class__.__name__, fun)
        el = Selection()
        el.deselect()
        self.assertEqual(len(el.keys()), len(self._keys))
        for key, vl in self._keys:
            self.assertTrue(key in el.keys())
            self.assertEqual(el[key], vl)

        self.dump(el)

        el.resetMntGrp()
        self.assertEqual(el["MntGrp"], self.__defaultmntgrp)
        self.compareToDump(el, ["MntGrp"])

        mymg = "somthing123"
        el["MntGrp"] = mymg
        el.resetMntGrp()
        self.assertEqual(el["MntGrp"], mymg)
        self.compareToDump(el, ["MntGrp"])

        mymg = ""
        el["MntGrp"] = mymg
        el.resetMntGrp()
        self.assertEqual(el["MntGrp"], self.__defaultmntgrp)
        self.compareToDump(el, ["MntGrp"])

    ## deselect test
    def test_resetTimeZone(self):
        fun = sys._getframe().f_code.co_name
        print "Run: %s.%s() " % (self.__class__.__name__, fun)
        el = Selection()
        el.deselect()
        self.assertEqual(len(el.keys()), len(self._keys))
        for key, vl in self._keys:
            self.assertTrue(key in el.keys())
            self.assertEqual(el[key], vl)

        self.dump(el)

        el.resetTimeZone()
        self.assertEqual(el["TimeZone"], self.__defaultzone)
        self.compareToDump(el, ["TimeZone"])

        mymg = "somthing123"
        el["TimeZone"] = mymg
        el.resetTimeZone()
        self.assertEqual(el["TimeZone"], mymg)
        self.compareToDump(el, ["TimeZone"])

        mymg = ""
        el["TimeZone"] = mymg
        el.resetTimeZone()
        self.assertEqual(el["TimeZone"], self.__defaultzone)
        self.compareToDump(el, ["TimeZone"])

    ## updateOrderedChannels test
    def test_resetAutomaticComponents(self):
        fun = sys._getframe().f_code.co_name
        print "Run: %s.%s() " % (self.__class__.__name__, fun)
        for i in range(20):
            el = Selection()
            self.assertEqual(len(el.keys()), len(self._keys))
            for key, vl in self._keys:
                self.assertTrue(key in el.keys())
                self.assertEqual(el[key], vl)

            lds1 = self.__rnd.randint(1, 40)
            dss1 = [self.getRandomName(10) for _ in range(lds1)]

            cps = {}
            lcp = self.__rnd.randint(1, 40)
            for i in range(lcp):
                cps[self.getRandomName(10)] = bool(self.__rnd.randint(0, 1))
            el["AutomaticComponentGroup"] = json.dumps(cps)

            self.dump(el)

            el.resetAutomaticComponents(dss1)

            self.compareToDump(el, ["AutomaticComponentGroup"])

            ndss = json.loads(el["AutomaticComponentGroup"])
            for ds in dss1:
                self.assertTrue(ds in ndss.keys())
                self.assertEqual(ndss[ds], False)


if __name__ == '__main__':
    unittest.main()
