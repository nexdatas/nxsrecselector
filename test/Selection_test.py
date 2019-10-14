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
# \package test nexdatas
# \file SelectionTest.py
# unittests for field Tags running Tango Server
#
import unittest
import os
import sys
import random
import struct
import binascii
import string
import json
import time
import nxsrecconfig

from nxsrecconfig.Selection import Selection

if sys.version_info > (3,):
    long = int


# if 64-bit machione
IS64BIT = (struct.calcsize("P") == 8)


# test fixture
class SelectionTest(unittest.TestCase):

    # constructor
    # \param methodName name of the test method

    def __init__(self, methodName):
        unittest.TestCase.__init__(self, methodName)

        self._tfname = "field"
        self._tfname = "group"
        self._fattrs = {"short_name": "test", "units": "m"}

        # default zone
        self.__defaultzone = 'Europe/Berlin'
        # default mntgrp
        self.__defaultmntgrp = 'nxsmntgrp'
        # selection version
        self.__version = nxsrecconfig.__version__

        self._bint = "int64" if IS64BIT else "int32"
        self._buint = "uint64" if IS64BIT else "uint32"
        self._bfloat = "float64" if IS64BIT else "float32"

        self._keys = [
            ("Timer", '[]'),
            ("OrderedChannels", '[]'),
            ("ComponentSelection", '{}'),
            ("ComponentPreselection", '{}'),
            ("PreselectingDataSources", '[]'),
            ("DataSourceSelection", '{}'),
            ("DataSourcePreselection", '{}'),
            ("OptionalComponents", '[]'),
            ("AppendEntry", False),
            ("ComponentsFromMntGrp", False),
            ("ConfigVariables", '{}'),
            ("UserData", '{}'),
            ("ChannelProperties", '{}'),
            ("UnplottedComponents", '[]'),
            ("DynamicComponents", True),
            ("DefaultDynamicLinks", True),
            ("DefaultDynamicPath",
             '/$var.entryname#\'scan\'$var.serialno:NXentry/NXinstrument/'
             'collection'),
            ("TimeZone", self.__defaultzone),
            ("ConfigDevice", ''),
            ("WriterDevice", ''),
            ("Door", ''),
            ("MntGrp", ''),
            ("MntGrpConfiguration", ''),
            ("Version", self.__version)
        ]
        self.__dump = {}

        try:
            self.__seed = long(binascii.hexlify(os.urandom(16)), 16)
        except NotImplementedError:
            self.__seed = long(time.time() * 256)

        self.__rnd = random.Random(self.__seed)

    # test starter
    # \brief Common set up
    def setUp(self):
        print("SEED = %s" % self.__seed)
        print("\nsetting up...")

    # test closer
    # \brief Common tear down
    def tearDown(self):
        print("tearing down ...")

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

    # constructor test
    # \brief It tests default settings
    def test_constructor(self):
        fun = sys._getframe().f_code.co_name
        print("Run: %s.%s() " % (self.__class__.__name__, fun))
        el = Selection(Version=self.__version)
        self.assertTrue(isinstance(el, dict))
        self.assertEqual(len(list(el.keys())), len(list(self._keys)))
        for key, vl in self._keys:
            self.assertTrue(key in el.keys())
            self.assertEqual(el[key], vl)

    # constructor test
    # \brief It tests default settings
    def test_reset(self):
        fun = sys._getframe().f_code.co_name
        print("Run: %s.%s() " % (self.__class__.__name__, fun))
        el = Selection(Version=self.__version)
        el.clear()
        self.assertEqual(len(list(el.keys())), 0)
        el.reset()
        self.assertTrue(isinstance(el, dict))
        self.assertEqual(len(list(el.keys())), len(self._keys))
        for key, vl in self._keys:
            self.assertTrue(key in el.keys())
            self.assertEqual(el[key], vl)

    def getRandomName(self, maxsize):
        if sys.version_info > (3,):
            letters = string.ascii_letters + string.digits
        else:
            letters = string.letters + string.digits
        size = self.__rnd.randint(1, maxsize)
        return ''.join(self.__rnd.choice(letters) for _ in range(size))

    # deselect test
    def test_deselect(self):
        fun = sys._getframe().f_code.co_name
        print("Run: %s.%s() " % (self.__class__.__name__, fun))
        for i in range(20):
            el = Selection(Version=self.__version)
            el.deselect()
            self.assertEqual(len(list(el.keys())), len(self._keys))
            for key, vl in self._keys:
                self.assertTrue(key in el.keys())
                self.assertEqual(el[key], vl)

            cps = {}
            dss = {}
            pdss = {}
            lcp = self.__rnd.randint(1, 40)
            lds = self.__rnd.randint(1, 40)
            lds2 = self.__rnd.randint(1, 40)
            for i in range(lcp):
                cps[self.getRandomName(10)] = bool(self.__rnd.randint(0, 1))
            for i in range(lds):
                dss[self.getRandomName(10)] = bool(self.__rnd.randint(0, 1))
            for i in range(lds2):
                pdss[self.getRandomName(10)] = bool(self.__rnd.randint(0, 1))
            el["ComponentSelection"] = json.dumps(cps)
            el["DataSourceSelection"] = json.dumps(dss)
            el["UnplottedComponents"] = json.dumps(
                self.__rnd.sample(set(dss.keys()), self.__rnd.randint(
                    1, len(list(dss.keys())))))
            el["DataSourcePreselection"] = json.dumps(pdss)
            self.dump(el)

            el.deselect()

            ncps = json.loads(el["ComponentSelection"])
            ndss = json.loads(el["DataSourceSelection"])

            self.assertEqual(el["UnplottedComponents"], '[]')
            self.assertEqual(el["DataSourcePreselection"], '{}')
            self.assertEqual(len(list(cps.keys())), len(list(ncps.keys())))
            self.assertEqual(len(list(dss.keys())), len(list(ndss.keys())))
            for key in cps.keys():
                self.assertTrue(key in ncps.keys())
                self.assertEqual(ncps[key], False)
            for key in dss.keys():
                self.assertTrue(key in ndss.keys())
                self.assertEqual(ndss[key], False)

            self.compareToDump(el, ["ComponentSelection",
                                    "DataSourceSelection",
                                    "DataSourcePreselection",
                                    "UnplottedComponents"])

    # updatePreselectingDataSources test
    def test_updatePreselectingDataSources(self):
        fun = sys._getframe().f_code.co_name
        print("Run: %s.%s() " % (self.__class__.__name__, fun))
        for i in range(20):
            el = Selection(Version=self.__version)
            el.updatePreselectingDataSources(None)
            self.assertEqual(len(list(el.keys())), len(self._keys))
            for key, vl in self._keys:
                self.assertTrue(key in el.keys())
                self.assertEqual(el[key], vl)

            lds1 = self.__rnd.randint(1, 40)
            lds2 = self.__rnd.randint(1, 40)
            lds3 = self.__rnd.randint(1, 40)
            dss1 = [self.getRandomName(10) for _ in range(lds1)]
            dss2 = [self.getRandomName(10) for _ in range(lds2)]
            dss3 = [self.getRandomName(10) for _ in range(lds3)]

            el["PreselectingDataSources"] = json.dumps(
                list(set(dss1) | set(dss2)))
            self.dump(el)
            el.updatePreselectingDataSources(None)

            self.compareToDump(el, ["PreselectingDataSources"])
            self.assertEqual(set(list(set(dss2) | set(dss1))),
                             set(json.loads(el["PreselectingDataSources"])))

            el.updatePreselectingDataSources(list(set(dss3) | set(dss2)))

            self.assertEqual(set(list(set(dss3) | set(dss2) | set(dss1))),
                             set(json.loads(el["PreselectingDataSources"])))

            self.compareToDump(el, ["PreselectingDataSources"])

    # updateOrderedChannels test
    def test_updateOrderedChannels(self):
        fun = sys._getframe().f_code.co_name
        print("Run: %s.%s() " % (self.__class__.__name__, fun))
        for i in range(20):
            el = Selection(Version=self.__version)
            el.updateOrderedChannels([])
            self.assertEqual(len(list(el.keys())), len(self._keys))
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

    # deselect test
    def test_updateComponentSelection(self):
        fun = sys._getframe().f_code.co_name
        print("Run: %s.%s() " % (self.__class__.__name__, fun))
        for i in range(20):
            el = Selection(Version=self.__version)
            el.deselect()
            self.assertEqual(len(list(el.keys())), len(self._keys))
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
            ccps = self.__rnd.sample(set(cps.keys()), self.__rnd.randint(
                1, len(list(cps.keys()))))
            for cp in ccps:
                dss[cp] = bool(self.__rnd.randint(0, 1))
            el["ComponentSelection"] = json.dumps(cps)
            el["DataSourceSelection"] = json.dumps(dss)
            common = set(cps) & set(dss)
            self.dump(el)

            el.updateComponentSelection()

            ncps = json.loads(el["ComponentSelection"])
            # ndss =
            json.loads(el["DataSourceSelection"])

            self.assertEqual(len(list(cps.keys())),
                             len(list(ncps.keys())) + len(common))
            for key in cps.keys():
                if key not in common:
                    self.assertTrue(key in ncps.keys())
                    self.assertEqual(ncps[key], cps[key])
            self.compareToDump(el, ["ComponentSelection"])

    # deselect test
    def test_updateDataSourceSelection(self):
        fun = sys._getframe().f_code.co_name
        print("Run: %s.%s() " % (self.__class__.__name__, fun))
        for i in range(20):
            el = Selection(Version=self.__version)
            el.deselect()
            self.assertEqual(len(list(el.keys())), len(self._keys))
            for key, vl in self._keys:
                self.assertTrue(key in el.keys())
                self.assertEqual(el[key], vl)

            dss = {}
            lall = self.__rnd.randint(1, 40)
            adss = [self.getRandomName(10) for _ in range(lall)]

            dssn = self.__rnd.sample(adss, self.__rnd.randint(1, len(adss)))
            chs = self.__rnd.sample(adss, self.__rnd.randint(1, len(adss)))
            cdss = self.__rnd.sample(adss, self.__rnd.randint(1, len(adss)))

            for ds in dssn:
                dss[ds] = bool(self.__rnd.randint(0, 1))
            el["DataSourceSelection"] = json.dumps(dss)

            self.dump(el)

            el.updateDataSourceSelection(chs, cdss)

            ndss = json.loads(el["DataSourceSelection"])
            existing = set(dssn) & (set(chs) | set(cdss))

            for key, value in ndss.items():
                if key in existing:
                    self.assertEqual(ndss[key], dss[key])
                else:
                    self.assertTrue(key in chs)
                    self.assertTrue(not value)
            self.compareToDump(el, ["DataSourceSelection"])

    # deselect test
    def test_resetMntGrp(self):
        fun = sys._getframe().f_code.co_name
        print("Run: %s.%s() " % (self.__class__.__name__, fun))
        el = Selection(Version=self.__version)
        el.deselect()
        self.assertEqual(len(list(el.keys())), len(self._keys))
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

        el.clear()
        el.resetMntGrp()
        self.assertEqual(el["MntGrp"], self.__defaultmntgrp)

    # deselect test
    def test_resetTimeZone(self):
        fun = sys._getframe().f_code.co_name
        print("Run: %s.%s() " % (self.__class__.__name__, fun))
        el = Selection(Version=self.__version)
        el.deselect()
        self.assertEqual(len(list(el.keys())), len(self._keys))
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

        el.clear()
        el.resetTimeZone()
        self.assertEqual(el["TimeZone"], self.__defaultzone)

    # updateOrderedChannels test
    def test_resetPreselectedComponents(self):
        fun = sys._getframe().f_code.co_name
        print("Run: %s.%s() " % (self.__class__.__name__, fun))
        for i in range(20):
            el = Selection(Version=self.__version)
            self.assertEqual(len(list(el.keys())), len(self._keys))
            for key, vl in self._keys:
                self.assertTrue(key in el.keys())
                self.assertEqual(el[key], vl)

            lds1 = self.__rnd.randint(1, 40)
            dss1 = [self.getRandomName(10) for _ in range(lds1)]

            cps = {}
            lcp = self.__rnd.randint(1, 40)
            for i in range(lcp):
                cps[self.getRandomName(10)] = bool(self.__rnd.randint(0, 1))
            el["ComponentPreselection"] = json.dumps(cps)

            self.dump(el)

            el.resetPreselectedComponents(dss1)

            self.compareToDump(el, ["ComponentPreselection"])

            ndss = json.loads(el["ComponentPreselection"])
            for ds in dss1:
                self.assertTrue(ds in ndss.keys())
                self.assertEqual(ndss[ds], None)


if __name__ == '__main__':
    unittest.main()
