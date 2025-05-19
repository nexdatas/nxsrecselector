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
# \file Settings_test.py
# unittests for TangoDsItemTest running Tango Server
#
import unittest
import os
import sys
import struct
import json
import pickle

try:
    import tango
except Exception:
    import PyTango as tango

try:
    import TestMacroServerSetUp
except Exception:
    from . import TestMacroServerSetUp
try:
    import TestPoolSetUp
except Exception:
    from . import TestPoolSetUp
try:
    import TestServerSetUp
except Exception:
    from . import TestServerSetUp
try:
    import TestMGSetUp
except Exception:
    from . import TestMGSetUp
try:
    import Settings_test
except Exception:
    from . import Settings_test

from nxsrecconfig.Describer import Describer
from nxsrecconfig.Utils import TangoUtils, MSUtils, Utils

import logging
logger = logging.getLogger()

if sys.version_info > (3,):
    unicode = str

# if 64-bit machione
IS64BIT = (struct.calcsize("P") == 8)

# list of available databases
DB_AVAILABLE = []

#: tango version
TGVER = tango.__version_info__[0]

try:
    import MySQLdb
    # connection arguments to MYSQL DB
    mydb = MySQLdb.connect({})
    mydb.close()
    DB_AVAILABLE.append("MYSQL")
except Exception:
    try:
        import MySQLdb
    # connection arguments to MYSQL DB
        args = {'db': 'nxsconfig',
                'read_default_file': '/etc/my.cnf', 'use_unicode': True}
    # inscance of MySQLdb
        mydb = MySQLdb.connect(**args)
        mydb.close()
        DB_AVAILABLE.append("MYSQL")
    except Exception:
        try:
            import MySQLdb
            from os.path import expanduser
            home = expanduser("~")
        # connection arguments to MYSQL DB
            args2 = {'db': 'nxsconfig',
                     'read_default_file': '%s/.my.cnf' % home,
                     'use_unicode': True}
        # inscance of MySQLdb
            mydb = MySQLdb.connect(**args2)
            mydb.close()
            DB_AVAILABLE.append("MYSQL")

        except ImportError as e:
            print("MYSQL not available: %s" % e)
        except Exception as e:
            print("MYSQL not available: %s" % e)
        except Exception:
            print("MYSQL not available")


# test fixture
class BasicSettingsTest(Settings_test.SettingsTest):

    # constructor
    # \param methodName name of the test method

    def __init__(self, methodName):
        Settings_test.SettingsTest.__init__(self, methodName)

    # test
    def test_constructor(self):
        fun = sys._getframe().f_code.co_name
        print("Run: %s.%s() " % (self.__class__.__name__, fun))
        # val = {"ConfigDevice": self._cf.dp.name(),
        #        "WriterDevice": self._wr.dp.name(),
        #        "Door": 'doortestp09/testts/t1r228',
        #        "MntGrp": 'nxsmntgrp'}

        self.subtest_constructor()

    # test
    def test_constructor_configDevice_door(self):
        fun = sys._getframe().f_code.co_name
        print("Run: %s.%s() " % (self.__class__.__name__, fun))
        val = {"ConfigDevice": self._cf.dp.name(),
               "WriterDevice": self._wr.dp.name(),
               "Door": 'doortestp09/testts/t1r228',
               "MntGrp": 'nxsmntgrp'}

        rs = self.openRecSelector()
        rs.configDevice = val["ConfigDevice"]
        rs.door = val["Door"]
        rs.mntGrp = val["MntGrp"]
        self.assertEqual(rs.configDevice, val["ConfigDevice"])
        self.assertEqual(rs.door, val["Door"])
        self.assertEqual(rs.mntGrp, val["MntGrp"])
        self.assertEqual(rs.macroServer, list(self._ms.ms.keys())[0])
        self.assertEqual(rs.mntGrp, val["MntGrp"])

    # test
    def test_mandatory_components(self):
        fun = sys._getframe().f_code.co_name
        print("Run: %s.%s() " % (self.__class__.__name__, fun))
        val = {"ConfigDevice": self._cf.dp.name(),
               "WriterDevice": self._wr.dp.name(),
               "Door": 'doortestp09/testts/t1r228',
               "MntGrp": 'nxsmntgrp'}

        wrong = []

        rs = self.openRecSelector()
        rs.configDevice = val["ConfigDevice"]
        rs.door = val["Door"]
        rs.mntGrp = val["MntGrp"]
        self.assertEqual(rs.configDevice, val["ConfigDevice"])
        self.assertEqual(rs.door, val["Door"])
        self.assertEqual(rs.mntGrp, val["MntGrp"])
        self.assertEqual(rs.macroServer, list(self._ms.ms.keys())[0])

        self._cf.dp.SetCommandVariable(["CPDICT", json.dumps(self.mycps)])
        self._cf.dp.SetCommandVariable(["DSDICT", json.dumps(self.mydss)])
#        msp = MacroServerPools(10)

#        self.assertEqual(msp.getMacroServer(), list(self._ms.ms.keys())[0])

        self.assertEqual(set(rs.mandatoryComponents()), set())
        mncps = self._rnd.randint(1, len(list(self.mycps.keys())) - 1)
        mcps = [cp for cp in self._rnd.sample(
                list(self.mycps.keys()), mncps) if cp not in wrong]

        self._cf.dp.SetCommandVariable(["MCPLIST", json.dumps(mcps)])
        self.assertEqual(set(rs.mandatoryComponents()), set(mcps))

    # test
    def test_mandatory_components2(self):
        fun = sys._getframe().f_code.co_name
        print("Run: %s.%s() " % (self.__class__.__name__, fun))
        val = {"ConfigDevice": self._cf.dp.name(),
               "WriterDevice": self._wr.dp.name(),
               "Door": 'doortestp09/testts/t1r228',
               "MntGrp": 'nxsmntgrp'}

        wrong = []

        rs = self.openRecSelector()
        rs.configDevice = val["ConfigDevice"]
        rs.door = val["Door"]
        rs.mntGrp = val["MntGrp"]
        self.assertEqual(rs.configDevice, val["ConfigDevice"])
        self.assertEqual(rs.door, val["Door"])
        self.assertEqual(rs.mntGrp, val["MntGrp"])
        self.assertEqual(rs.macroServer, list(self._ms.ms.keys())[0])

        self._cf.dp.SetCommandVariable(["CPDICT", json.dumps(self.mycps)])
        self._cf.dp.SetCommandVariable(["DSDICT", json.dumps(self.mydss)])
#        msp = MacroServerPools(10)

#        self.assertEqual(msp.getMacroServer(), list(self._ms.ms.keys())[0])

        self.assertEqual(set(rs.mandatoryComponents()), set())
        mncps = self._rnd.randint(1, len(list(self.mycps.keys())) - 1)
        mcps = [cp for cp in self._rnd.sample(
                list(self.mycps.keys()), mncps) if cp not in wrong]

        self._cf.dp.SetCommandVariable(["MCPLIST", json.dumps(mcps)])
        self.assertEqual(set(rs.mandatoryComponents()), set(mcps))

    # available components and datasources
    def test_available_components_datasources(self):
        fun = sys._getframe().f_code.co_name
        print("Run: %s.%s() " % (self.__class__.__name__, fun))
        val = {"ConfigDevice": self._cf.dp.name(),
               "WriterDevice": self._wr.dp.name(),
               "Door": 'doortestp09/testts/t1r228',
               "MntGrp": 'nxsmntgrp'}

        # wrong = []

        rs = self.openRecSelector()
        rs.configDevice = val["ConfigDevice"]
        rs.door = val["Door"]
        rs.mntGrp = val["MntGrp"]
        self.assertEqual(rs.configDevice, val["ConfigDevice"])
        self.assertEqual(rs.door, val["Door"])
        self.assertEqual(rs.mntGrp, val["MntGrp"])
        self.assertEqual(rs.macroServer, list(self._ms.ms.keys())[0])
        self.assertEqual(set(rs.availableComponents()), set())
        self.assertEqual(set(rs.availableDataSources()), set())

        self._cf.dp.SetCommandVariable(["CPDICT", json.dumps(self.mycps)])
        self._cf.dp.SetCommandVariable(["DSDICT", json.dumps(self.mydss)])
#        msp = MacroServerPools(10)

#        self.assertEqual(msp.getMacroServer(), list(self._ms.ms.keys())[0])

        self.assertEqual(set(rs.availableComponents()), set(self.mycps.keys()))
        self.assertEqual(set(rs.availableDataSources()),
                         set(self.mydss.keys()))

    def test_available_selections(self):
        fun = sys._getframe().f_code.co_name
        print("Run: %s.%s() " % (self.__class__.__name__, fun))
        val = {"ConfigDevice": self._cf.dp.name(),
               "WriterDevice": self._wr.dp.name(),
               "Door": 'doortestp09/testts/t1r228',
               "MntGrp": 'nxsmntgrp'}

        # wrong = []

        db = tango.Database()
        db.put_device_property(list(self._ms.ms.keys())[0],
                               {'PoolNames': self._pool.dp.name()})
        self._ms.dps[list(self._ms.ms.keys())[0]].Init()
        rs = self.openRecSelector()
        rs.configDevice = val["ConfigDevice"]
        rs.door = val["Door"]
        rs.mntGrp = val["MntGrp"]

        self.assertEqual(rs.configDevice, val["ConfigDevice"])
        self.assertEqual(rs.door, val["Door"])
        self.assertEqual(rs.macroServer, list(self._ms.ms.keys())[0])
        self.assertEqual(rs.mntGrp, val["MntGrp"])
        self.assertEqual(set(rs.availableComponents()), set())
        self.assertEqual(set(rs.availableDataSources()), set())
        try:
            self.assertEqual(set(rs.availableProfiles()), set())
        except Exception:
            self.assertEqual(set(rs.availableProfiles()),
                             set([val["MntGrp"]]))

        self._cf.dp.SetCommandVariable(["SELDICT",
                                        json.dumps(self.mysel2)])

        self.assertEqual(set(rs.availableProfiles()),
                         set(self.mysel2.keys()))
        self.assertEqual(set(rs.availableComponents()), set())
        self.assertEqual(set(rs.availableDataSources()), set())

    # test
    # \brief It tests default settings
    def test_poolChannels(self):
        fun = sys._getframe().f_code.co_name
        print("Run: %s.%s() " % (self.__class__.__name__, fun))
        val = {"ConfigDevice": self._cf.dp.name(),
               "WriterDevice": self._wr.dp.name(),
               "Door": 'doortestp09/testts/t1r228',
               "MntGrp": 'nxsmntgrp'}

        db = tango.Database()
        db.put_device_property(list(self._ms.ms.keys())[0],
                               {'PoolNames': self._pool.dp.name()})
        self._ms.dps[list(self._ms.ms.keys())[0]].Init()
        rs = self.openRecSelector()
        rs.configDevice = val["ConfigDevice"]
        rs.door = val["Door"]
        rs.mntGrp = val["MntGrp"]

        db = tango.Database()
        db.put_device_property(list(self._ms.ms.keys())[0],
                               {'PoolNames': self._pool.dp.name()})

        self._ms.dps[list(self._ms.ms.keys())[0]].Init()

        self.assertEqual(rs.macroServer, list(self._ms.ms.keys())[0])
        self.assertEqual(rs.poolElementNames('ExpChannelList'), [])

        arr = [
            {"name": "test/ct/01", "controller": "counter_01/Value"},
            {"name": "test/ct/02", "controller": "counter_02/att"},
            {"name": "test/ct/03", "controller": "counter_03/value"},
            {"name": "test/ct/04", "controller": "counter_04/13"},
            {"name": "null", "controller": "counter_04"},
        ]

        arr2 = [
            ["test/mca/01", "mca_01"],
            ["test/mca/02", "mca_02"],
            ["test/sca/03", "my_sca1"],
            ["test/sca/04", "mysca_123"],
        ]

        pool = self._pool.dp
        pool.ExpChannelList = [json.dumps(a) for a in arr]

        dd = rs.poolElementNames('ExpChannelList')
        self.assertEqual(dd, [a["name"] for a in arr])

        pool.ExpChannelList = [
            json.dumps(
                {"name": a[0], "controller": a[1]}) for a in arr2]

        dd = rs.poolElementNames('ExpChannelList')
        res = [a[0] for a in arr2]
        self.assertEqual(dd, res)

        # print rs.poolElementNames('ExpChannelList')

    # test
    # \brief It tests default settings
    def test_poolChannels_bl(self):
        fun = sys._getframe().f_code.co_name
        print("Run: %s.%s() " % (self.__class__.__name__, fun))
        val = {"ConfigDevice": self._cf.dp.name(),
               "WriterDevice": self._wr.dp.name(),
               "Door": 'doortestp09/testts/t1r228',
               "MntGrp": 'nxsmntgrp'}

        db = tango.Database()
        db.put_device_property(list(self._ms.ms.keys())[0],
                               {'PoolNames': self._pool.dp.name()})
        self._ms.dps[list(self._ms.ms.keys())[0]].Init()
        rs = self.openRecSelector()
        self.setProp(rs, "poolBlacklist",
                     [self._pool.dp.name()])
        rs.configDevice = val["ConfigDevice"]
        rs.door = val["Door"]
        rs.mntGrp = val["MntGrp"]

        db = tango.Database()
        db.put_device_property(list(self._ms.ms.keys())[0],
                               {'PoolNames': self._pool.dp.name()})

        self._ms.dps[list(self._ms.ms.keys())[0]].Init()

        self.assertEqual(rs.macroServer, list(self._ms.ms.keys())[0])
        self.assertEqual(rs.poolElementNames('ExpChannelList'), [])

        arr = [
            {"name": "test/ct/01", "controller": "counter_01/Value"},
            {"name": "test/ct/02", "controller": "counter_02/att"},
            {"name": "test/ct/03", "controller": "counter_03/value"},
            {"name": "test/ct/04", "controller": "counter_04/13"},
            {"name": "null", "controller": "counter_04"},
        ]

        arr2 = [
            ["test/mca/01", "mca_01"],
            ["test/mca/02", "mca_02"],
            ["test/sca/03", "my_sca1"],
            ["test/sca/04", "mysca_123"],
        ]

        pool = self._pool.dp
        pool.ExpChannelList = [json.dumps(a) for a in arr]

        dd = rs.poolElementNames('ExpChannelList')
#        self.assertEqual(dd, [a["name"] for a in arr])
        self.assertEqual(dd, [])

        pool.ExpChannelList = [
            json.dumps(
                {"name": a[0], "controller": a[1]}) for a in arr2]

        dd = rs.poolElementNames('ExpChannelList')
#        res = [a[0] for a in arr2]
        res = []
        self.assertEqual(dd, res)

        # print rs.poolElementNames('ExpChannelList')

    # test
    # \brief It tests default settings
    def test_poolMotors(self):
        fun = sys._getframe().f_code.co_name
        print("Run: %s.%s() " % (self.__class__.__name__, fun))
        val = {"ConfigDevice": self._cf.dp.name(),
               "WriterDevice": self._wr.dp.name(),
               "Door": 'doortestp09/testts/t1r228',
               "MntGrp": 'nxsmntgrp'}

        db = tango.Database()
        db.put_device_property(list(self._ms.ms.keys())[0],
                               {'PoolNames': self._pool.dp.name()})
        self._ms.dps[list(self._ms.ms.keys())[0]].Init()
        rs = self.openRecSelector()
        rs.configDevice = val["ConfigDevice"]
        rs.door = val["Door"]
        rs.mntGrp = val["MntGrp"]

        db = tango.Database()
        db.put_device_property(list(self._ms.ms.keys())[0],
                               {'PoolNames': self._pool.dp.name()})

        self._ms.dps[list(self._ms.ms.keys())[0]].Init()

        self.assertEqual(rs.macroServer, list(self._ms.ms.keys())[0])
        self.assertEqual(rs.poolElementNames('MotorList'), [])

        arr = [
            {"name": "test/ct/01", "controller": "counter_01/Value"},
            {"name": "test/ct/02", "controller": "counter_02/att"},
            {"name": "test/ct/03", "controller": "counter_03/value"},
            {"name": "test/ct/04", "controller": "counter_04/13"},
            {"name": "null", "controller": "counter_04"},
        ]

        arr2 = [
            ["test/mca/01", "mca_01"],
            ["test/mca/02", "mca_02"],
            ["test/sca/03", "my_sca1"],
            ["test/sca/04", "mysca_123"],
        ]

        pool = self._pool.dp
        pool.MotorList = [json.dumps(a) for a in arr]

        dd = rs.poolElementNames('MotorList')
        self.assertEqual(dd, [a["name"] for a in arr])

        pool.MotorList = [
            json.dumps(
                {"name": a[0], "controller": a[1]}) for a in arr2]

        dd = rs.poolElementNames('MotorList')
        res = [a[0] for a in arr2]
        self.assertEqual(dd, res)

        # print rs.poolElementNames('MotorList')

    # test
    # \brief It tests default settings
    def test_poolMotors_bl(self):
        fun = sys._getframe().f_code.co_name
        print("Run: %s.%s() " % (self.__class__.__name__, fun))
        val = {"ConfigDevice": self._cf.dp.name(),
               "WriterDevice": self._wr.dp.name(),
               "Door": 'doortestp09/testts/t1r228',
               "MntGrp": 'nxsmntgrp'}

        db = tango.Database()
        db.put_device_property(list(self._ms.ms.keys())[0],
                               {'PoolNames': self._pool.dp.name()})
        self._ms.dps[list(self._ms.ms.keys())[0]].Init()
        rs = self.openRecSelector()
        self.setProp(rs, "poolBlacklist",
                     [self._pool.dp.name()])
        rs.configDevice = val["ConfigDevice"]
        rs.door = val["Door"]
        rs.mntGrp = val["MntGrp"]

        db = tango.Database()
        db.put_device_property(list(self._ms.ms.keys())[0],
                               {'PoolNames': self._pool.dp.name()})

        self._ms.dps[list(self._ms.ms.keys())[0]].Init()

        self.assertEqual(rs.macroServer, list(self._ms.ms.keys())[0])
        self.assertEqual(rs.poolElementNames('MotorList'), [])

        arr = [
            {"name": "test/ct/01", "controller": "counter_01/Value"},
            {"name": "test/ct/02", "controller": "counter_02/att"},
            {"name": "test/ct/03", "controller": "counter_03/value"},
            {"name": "test/ct/04", "controller": "counter_04/13"},
            {"name": "null", "controller": "counter_04"},
        ]

        arr2 = [
            ["test/mca/01", "mca_01"],
            ["test/mca/02", "mca_02"],
            ["test/sca/03", "my_sca1"],
            ["test/sca/04", "mysca_123"],
        ]

        pool = self._pool.dp
        pool.MotorList = [json.dumps(a) for a in arr]

        dd = rs.poolElementNames('MotorList')
#        self.assertEqual(dd, [a["name"] for a in arr])
        self.assertEqual(dd, [])

        pool.MotorList = [
            json.dumps(
                {"name": a[0], "controller": a[1]}) for a in arr2]

        dd = rs.poolElementNames('MotorList')
#        res = [a[0] for a in arr2]
        res = []
        self.assertEqual(dd, res)

        # print rs.poolElementNames('MotorList')

    # preselectComponents test
    # \brief It tests default settings
    def test_preselectComponents_simple(self):
        fun = sys._getframe().f_code.co_name
        print("Run: %s.%s() " % (self.__class__.__name__, fun))
        val = {"ConfigDevice": self._cf.dp.name(),
               "WriterDevice": self._wr.dp.name(),
               "Door": 'doortestp09/testts/t1r228',
               "MntGrp": 'nxsmntgrp'}

        # db = tango.Database()
        self._ms.dps[list(self._ms.ms.keys())[0]].Init()
        rs = self.openRecSelector()
        rs.configDevice = val["ConfigDevice"]
        rs.door = val["Door"]
        rs.mntGrp = val["MntGrp"]

        self._ms.dps[list(self._ms.ms.keys())[0]].Init()
        self.assertEqual(rs.macroServer, list(self._ms.ms.keys())[0])

        # channelerrors = []
        rs.preselectComponents()
        res = self.value(rs, "ComponentPreselection")
        self.assertEqual(res, '{}')
        res2 = self.value(rs, "DataSourcePreselection")
        self.assertEqual(res2, '{}')
        # print self._cf.dp.GetCommandVariable("COMMANDS")

    # preselectComponents test
    # \brief It tests default settings
    def test_preselectComponents_withcf(self):
        fun = sys._getframe().f_code.co_name
        print("Run: %s.%s() " % (self.__class__.__name__, fun))
        val = {"ConfigDevice": self._cf.dp.name(),
               "WriterDevice": self._wr.dp.name(),
               "Door": 'doortestp09/testts/t1r228',
               "MntGrp": 'nxsmntgrp'}

        # db = tango.Database()
        self._ms.dps[list(self._ms.ms.keys())[0]].Init()
        rs = self.openRecSelector()
        rs.configDevice = val["ConfigDevice"]
        rs.door = val["Door"]
        rs.mntGrp = val["MntGrp"]

        self._ms.dps[list(self._ms.ms.keys())[0]].Init()

        self.assertEqual(rs.macroServer, list(self._ms.ms.keys())[0])
        channelerrors = []
        # poolchannels = []
        componentgroup = {}

        self._cf.dp.SetCommandVariable(["CPDICT", json.dumps(self.mycps)])
        self._cf.dp.SetCommandVariable(["DSDICT", json.dumps(self.mydss)])

        rs.preselectComponents()
        res = self.value(rs, "ComponentPreselection")
        res2 = self.value(rs, "DataSourcePreselection")
        self.assertEqual(res, '{}')

        self.assertEqual(res2, '{}')
        self.assertEqual(componentgroup, {})
        self.assertEqual(channelerrors, [])
        # print self._cf.dp.GetCommandVariable("COMMANDS")

    # test
    # \brief It tests default settings
    def test_preselectComponents_withcf_cps(self):
        fun = sys._getframe().f_code.co_name
        print("Run: %s.%s() " % (self.__class__.__name__, fun))
        val = {"ConfigDevice": self._cf.dp.name(),
               "WriterDevice": self._wr.dp.name(),
               "Door": 'doortestp09/testts/t1r228',
               "MntGrp": 'nxsmntgrp'}

        # db = tango.Database()
        self._ms.dps[list(self._ms.ms.keys())[0]].Init()
        rs = self.openRecSelector()
        rs.configDevice = val["ConfigDevice"]
        rs.door = val["Door"]
        rs.mntGrp = val["MntGrp"]
        rs.writerDevice = val["WriterDevice"]

        self._ms.dps[list(self._ms.ms.keys())[0]].Init()

        channelerrors = []
        poolchannels = ["mycp"]
        componentgroup = {"mycp": None}
        datasourcegroup = {"ann2": None}

        self._cf.dp.SetCommandVariable(["CPDICT", json.dumps(self.mycps)])
        self._cf.dp.SetCommandVariable(["DSDICT", json.dumps(self.mydss)])

        cnf = json.loads(rs.profileConfiguration)
        cnf["Timer"] = '[]'
        cnf["PreselectingDataSources"] = json.dumps(poolchannels)
        cnf["ComponentPreselection"] = json.dumps(componentgroup)
        cnf["DataSourcePreselection"] = json.dumps(datasourcegroup)
        rs.profileConfiguration = json.dumps(cnf)
        rs.preselectComponents()
        res = self.value(rs, "ComponentPreselection")
        # print res
        res2 = self.value(rs, "DataSourcePreselection")
        self.myAssertDict(json.loads(res), {"mycp": True})
        self.myAssertDict(json.loads(res2), {"ann2": True})
        self.assertEqual(channelerrors, [])

        self.assertTrue(val["MntGrp"] in self._cf.dp.availableSelections())
        sed = json.loads(self._cf.dp.selections([val["MntGrp"]])[0])
        self.assertEqual(len(list(sed.keys())), len(self._keys))
        for key, vl in self._keys:
            self.assertTrue(key in sed.keys())
            if key in val:
                self.assertEqual(sed[key], val[key])
            elif key == 'ComponentPreselection':
                self.assertEqual(set(json.loads(sed[key])),
                                 set(json.loads(res)))
            elif key == 'DataSourcePreselection':
                self.assertEqual(set(json.loads(sed[key])),
                                 set(json.loads(res2)))
            elif key == 'PreselectingDataSources':
                self.assertEqual(set(json.loads(sed[key])), set(poolchannels))
            else:
                self.assertEqual(sed[key], vl)

    # test
    # \brief It tests default settings
    def test_preselectComponents_withcf_cps_false(self):
        fun = sys._getframe().f_code.co_name
        print("Run: %s.%s() " % (self.__class__.__name__, fun))
        val = {"ConfigDevice": self._cf.dp.name(),
               "WriterDevice": self._wr.dp.name(),
               "Door": 'doortestp09/testts/t1r228',
               "MntGrp": 'nxsmntgrp'}

        # db = tango.Database()
        self._ms.dps[list(self._ms.ms.keys())[0]].Init()
        rs = self.openRecSelector()
        rs.configDevice = val["ConfigDevice"]
        rs.door = val["Door"]
        rs.mntGrp = val["MntGrp"]
        rs.writerDevice = val["WriterDevice"]

        self._ms.dps[list(self._ms.ms.keys())[0]].Init()

        channelerrors = []
        poolchannels = ["mycp"]
        componentgroup = {"mycp": False}
        datasourcegroup = {"ann2": False}

        self._cf.dp.SetCommandVariable(["CPDICT", json.dumps(self.mycps)])
        self._cf.dp.SetCommandVariable(["DSDICT", json.dumps(self.mydss)])

        cnf = json.loads(rs.profileConfiguration)
        cnf["Timer"] = '[]'
        cnf["PreselectingDataSources"] = json.dumps(poolchannels)
        cnf["ComponentPreselection"] = json.dumps(componentgroup)
        cnf["DataSourcePreselection"] = json.dumps(datasourcegroup)
        rs.profileConfiguration = json.dumps(cnf)
        rs.preselectComponents()
        res = self.value(rs, "ComponentPreselection")
        # print res
        res2 = self.value(rs, "DataSourcePreselection")
        self.myAssertDict(json.loads(res), {"mycp": False})
        self.myAssertDict(json.loads(res2), {"ann2": False})
        self.assertEqual(channelerrors, [])

        self.assertTrue(val["MntGrp"] in self._cf.dp.availableSelections())
        sed = json.loads(self._cf.dp.selections([val["MntGrp"]])[0])
        self.assertEqual(len(list(sed.keys())), len(self._keys))
        for key, vl in self._keys:
            self.assertTrue(key in sed.keys())
            if key in val:
                self.assertEqual(sed[key], val[key])
            elif key == 'ComponentPreselection':
                self.assertEqual(set(json.loads(sed[key])),
                                 set(json.loads(res)))
            elif key == 'DataSourcePreselection':
                self.assertEqual(set(json.loads(sed[key])),
                                 set(json.loads(res2)))
            elif key == 'PreselectingDataSources':
                self.assertEqual(set(json.loads(sed[key])), set(poolchannels))
            else:
                self.assertEqual(sed[key], vl)

    # test
    # \brief It tests default settings
    def test_preselectComponents_withcf_cps_true(self):
        fun = sys._getframe().f_code.co_name
        print("Run: %s.%s() " % (self.__class__.__name__, fun))
        val = {"ConfigDevice": self._cf.dp.name(),
               "WriterDevice": self._wr.dp.name(),
               "Door": 'doortestp09/testts/t1r228',
               "MntGrp": 'nxsmntgrp'}

        # db = tango.Database()
        self._ms.dps[list(self._ms.ms.keys())[0]].Init()
        rs = self.openRecSelector()
        rs.configDevice = val["ConfigDevice"]
        rs.door = val["Door"]
        rs.mntGrp = val["MntGrp"]
        rs.writerDevice = val["WriterDevice"]

        self._ms.dps[list(self._ms.ms.keys())[0]].Init()

        channelerrors = []
        poolchannels = ["mycp"]
        componentgroup = {"mycp": True}
        datasourcegroup = {"ann2": True}

        self._cf.dp.SetCommandVariable(["CPDICT", json.dumps(self.mycps)])
        self._cf.dp.SetCommandVariable(["DSDICT", json.dumps(self.mydss)])

        cnf = json.loads(rs.profileConfiguration)
        cnf["Timer"] = '[]'
        cnf["PreselectingDataSources"] = json.dumps(poolchannels)
        cnf["ComponentPreselection"] = json.dumps(componentgroup)
        cnf["DataSourcePreselection"] = json.dumps(datasourcegroup)
        rs.profileConfiguration = json.dumps(cnf)
        rs.preselectComponents()
        res = self.value(rs, "ComponentPreselection")
        # print res
        res2 = self.value(rs, "DataSourcePreselection")
        self.myAssertDict(json.loads(res), {"mycp": True})
        self.myAssertDict(json.loads(res2), {"ann2": True})
        self.assertEqual(channelerrors, [])

        self.assertTrue(val["MntGrp"] in self._cf.dp.availableSelections())
        sed = json.loads(self._cf.dp.selections([val["MntGrp"]])[0])
        self.assertEqual(len(list(sed.keys())), len(self._keys))
        for key, vl in self._keys:
            self.assertTrue(key in sed.keys())
            if key in val:
                self.assertEqual(sed[key], val[key])
            elif key == 'ComponentPreselection':
                self.assertEqual(set(json.loads(sed[key])),
                                 set(json.loads(res)))
            elif key == 'DataSourcePreselection':
                self.assertEqual(set(json.loads(sed[key])),
                                 set(json.loads(res2)))
            elif key == 'PreselectingDataSources':
                self.assertEqual(set(json.loads(sed[key])), set(poolchannels))
            else:
                self.assertEqual(sed[key], vl)

    # test
    # \brief It tests default settings
    def test_preselectComponents_withcf_nocps(self):
        fun = sys._getframe().f_code.co_name
        print("Run: %s.%s() " % (self.__class__.__name__, fun))
        val = {"ConfigDevice": self._cf.dp.name(),
               "WriterDevice": self._wr.dp.name(),
               "Door": 'doortestp09/testts/t1r228',
               "MntGrp": 'nxsmntgrp'}

        # db = tango.Database()
        self._ms.dps[list(self._ms.ms.keys())[0]].Init()
        rs = self.openRecSelector()
        rs.configDevice = val["ConfigDevice"]
        rs.door = val["Door"]
        rs.mntGrp = val["MntGrp"]
        rs.writerDevice = val["WriterDevice"]

        self._ms.dps[list(self._ms.ms.keys())[0]].Init()

        channelerrors = []
        poolchannels = ["mycp"]
        componentgroup = {}
        datasourcegroup = {}

        self._cf.dp.SetCommandVariable(["CPDICT", json.dumps(self.mycps)])
        self._cf.dp.SetCommandVariable(["DSDICT", json.dumps(self.mydss)])

        cnf = json.loads(rs.profileConfiguration)
        cnf["PreselectingDataSources"] = json.dumps(poolchannels)
        cnf["ComponentPreselection"] = json.dumps(componentgroup)
        cnf["DataSourcePreselection"] = json.dumps(datasourcegroup)
        rs.profileConfiguration = json.dumps(cnf)
        rs.preselectComponents()
        res = self.value(rs, "ComponentPreselection")

        self.myAssertDict(json.loads(res), {})
        res2 = self.value(rs, "DataSourcePreselection")
        self.myAssertDict(json.loads(res2), {})
        self.assertEqual(channelerrors, [])

        # print self._cf.dp.GetCommandVariable("COMMANDS")

        self.assertTrue(val["MntGrp"] in self._cf.dp.availableSelections())

    # test
    # \brief It tests default settings
    def test_preselectComponents_withcf_nochnnel(self):
        fun = sys._getframe().f_code.co_name
        print("Run: %s.%s() " % (self.__class__.__name__, fun))
        val = {"ConfigDevice": self._cf.dp.name(),
               "WriterDevice": self._wr.dp.name(),
               "Door": 'doortestp09/testts/t1r228',
               "MntGrp": 'nxsmntgrp'}

        # db = tango.Database()
        self._ms.dps[list(self._ms.ms.keys())[0]].Init()
        rs = self.openRecSelector()
        rs.configDevice = val["ConfigDevice"]
        rs.door = val["Door"]
        rs.mntGrp = val["MntGrp"]
        rs.writerDevice = val["WriterDevice"]

        self._ms.dps[list(self._ms.ms.keys())[0]].Init()

        channelerrors = []
        poolchannels = []
        componentgroup = {"mycp": None}
        datasourcegroup = {"ann2": None}

        self._cf.dp.SetCommandVariable(["CPDICT", json.dumps(self.mycps)])
        self._cf.dp.SetCommandVariable(["DSDICT", json.dumps(self.mydss)])

        cnf = json.loads(rs.profileConfiguration)
        cnf["Timer"] = '[]'
        cnf["PreselectingDataSources"] = json.dumps(poolchannels)
        cnf["ComponentPreselection"] = json.dumps(componentgroup)
        cnf["DataSourcePreselection"] = json.dumps(datasourcegroup)
        rs.profileConfiguration = json.dumps(cnf)
        rs.preselectComponents()
        res = self.value(rs, "ComponentPreselection")
        res2 = self.value(rs, "DataSourcePreselection")

        self.myAssertDict(json.loads(res), {"mycp": True})
        self.myAssertDict(json.loads(res2), {"ann2": True})
        self.assertEqual(channelerrors, [])

        # print self._cf.dp.GetCommandVariable("COMMANDS")
        self.assertTrue(val["MntGrp"] in self._cf.dp.availableSelections())
        sed = json.loads(self._cf.dp.selections([val["MntGrp"]])[0])
        # print sed
        self.assertEqual(len(list(sed.keys())), len(self._keys))
        for key, vl in self._keys:
            self.assertTrue(key in sed.keys())
            if key in val:
                self.assertEqual(sed[key], val[key])
            elif key == 'ComponentPreselection':
                self.assertEqual(set(json.loads(sed[key])),
                                 set(json.loads(res)))
            elif key == 'DataSourcePreselection':
                self.assertEqual(set(json.loads(sed[key])),
                                 set(json.loads(res2)))
            elif key == 'PreselectingDataSources':
                self.assertEqual(set(json.loads(sed[key])), set(poolchannels))
            else:
                self.assertEqual(sed[key], vl)

    # test
    # \brief It tests default settings
    def test_preselectComponents_withcf_nochnnel_false(self):
        fun = sys._getframe().f_code.co_name
        print("Run: %s.%s() " % (self.__class__.__name__, fun))
        val = {"ConfigDevice": self._cf.dp.name(),
               "WriterDevice": self._wr.dp.name(),
               "Door": 'doortestp09/testts/t1r228',
               "MntGrp": 'nxsmntgrp'}

        # db = tango.Database()
        self._ms.dps[list(self._ms.ms.keys())[0]].Init()
        rs = self.openRecSelector()
        rs.configDevice = val["ConfigDevice"]
        rs.door = val["Door"]
        rs.mntGrp = val["MntGrp"]
        rs.writerDevice = val["WriterDevice"]

        self._ms.dps[list(self._ms.ms.keys())[0]].Init()

        channelerrors = []
        poolchannels = []
        componentgroup = {"mycp": False}
        datasourcegroup = {"ann2": False}

        self._cf.dp.SetCommandVariable(["CPDICT", json.dumps(self.mycps)])
        self._cf.dp.SetCommandVariable(["DSDICT", json.dumps(self.mydss)])

        cnf = json.loads(rs.profileConfiguration)
        cnf["Timer"] = '[]'
        cnf["PreselectingDataSources"] = json.dumps(poolchannels)
        cnf["ComponentPreselection"] = json.dumps(componentgroup)
        cnf["DataSourcePreselection"] = json.dumps(datasourcegroup)
        rs.profileConfiguration = json.dumps(cnf)
        rs.preselectComponents()
        res = self.value(rs, "ComponentPreselection")
        res2 = self.value(rs, "DataSourcePreselection")

        self.myAssertDict(json.loads(res), {"mycp": False})
        self.myAssertDict(json.loads(res2), {"ann2": False})
        self.assertEqual(channelerrors, [])

        # print self._cf.dp.GetCommandVariable("COMMANDS")
        self.assertTrue(val["MntGrp"] in self._cf.dp.availableSelections())
        sed = json.loads(self._cf.dp.selections([val["MntGrp"]])[0])
        # print sed
        self.assertEqual(len(list(sed.keys())), len(self._keys))
        for key, vl in self._keys:
            self.assertTrue(key in sed.keys())
            if key in val:
                self.assertEqual(sed[key], val[key])
            elif key == 'ComponentPreselection':
                self.assertEqual(set(json.loads(sed[key])),
                                 set(json.loads(res)))
            elif key == 'DataSourcePreselection':
                self.assertEqual(set(json.loads(sed[key])),
                                 set(json.loads(res2)))
            elif key == 'PreselectingDataSources':
                self.assertEqual(set(json.loads(sed[key])), set(poolchannels))
            else:
                self.assertEqual(sed[key], vl)

    # test
    # \brief It tests default settings
    def test_preselectComponents_withcf_nochnnel_true(self):
        fun = sys._getframe().f_code.co_name
        print("Run: %s.%s() " % (self.__class__.__name__, fun))
        val = {"ConfigDevice": self._cf.dp.name(),
               "WriterDevice": self._wr.dp.name(),
               "Door": 'doortestp09/testts/t1r228',
               "MntGrp": 'nxsmntgrp'}

        # db = tango.Database()
        self._ms.dps[list(self._ms.ms.keys())[0]].Init()
        rs = self.openRecSelector()
        rs.configDevice = val["ConfigDevice"]
        rs.door = val["Door"]
        rs.mntGrp = val["MntGrp"]
        rs.writerDevice = val["WriterDevice"]

        self._ms.dps[list(self._ms.ms.keys())[0]].Init()

        channelerrors = []
        poolchannels = []
        componentgroup = {"mycp": True}
        datasourcegroup = {"ann2": True}

        self._cf.dp.SetCommandVariable(["CPDICT", json.dumps(self.mycps)])
        self._cf.dp.SetCommandVariable(["DSDICT", json.dumps(self.mydss)])

        cnf = json.loads(rs.profileConfiguration)
        cnf["Timer"] = '[]'
        cnf["PreselectingDataSources"] = json.dumps(poolchannels)
        cnf["ComponentPreselection"] = json.dumps(componentgroup)
        cnf["DataSourcePreselection"] = json.dumps(datasourcegroup)
        rs.profileConfiguration = json.dumps(cnf)
        rs.preselectComponents()
        res = self.value(rs, "ComponentPreselection")
        res2 = self.value(rs, "DataSourcePreselection")

        self.myAssertDict(json.loads(res), {"mycp": True})
        self.myAssertDict(json.loads(res2), {"ann2": True})
        self.assertEqual(channelerrors, [])

        # print self._cf.dp.GetCommandVariable("COMMANDS")
        self.assertTrue(val["MntGrp"] in self._cf.dp.availableSelections())
        sed = json.loads(self._cf.dp.selections([val["MntGrp"]])[0])
        # print sed
        self.assertEqual(len(list(sed.keys())), len(self._keys))
        for key, vl in self._keys:
            self.assertTrue(key in sed.keys())
            if key in val:
                self.assertEqual(sed[key], val[key])
            elif key == 'ComponentPreselection':
                self.assertEqual(set(json.loads(sed[key])),
                                 set(json.loads(res)))
            elif key == 'DataSourcePreselection':
                self.assertEqual(set(json.loads(sed[key])),
                                 set(json.loads(res2)))
            elif key == 'PreselectingDataSources':
                self.assertEqual(set(json.loads(sed[key])), set(poolchannels))
            else:
                self.assertEqual(sed[key], vl)

    # test
    # \brief It tests default settings
    def test_preselectComponents_wds_t(self):
        fun = sys._getframe().f_code.co_name
        print("Run: %s.%s() " % (self.__class__.__name__, fun))
        val = {"ConfigDevice": self._cf.dp.name(),
               "WriterDevice": self._wr.dp.name(),
               "Door": 'doortestp09/testts/t1r228',
               "MntGrp": 'nxsmntgrp'}

        # db = tango.Database()
        self._ms.dps[list(self._ms.ms.keys())[0]].Init()
        rs = self.openRecSelector()
        rs.configDevice = val["ConfigDevice"]
        rs.door = val["Door"]
        rs.mntGrp = val["MntGrp"]
        rs.writerDevice = val["WriterDevice"]

        self._ms.dps[list(self._ms.ms.keys())[0]].Init()

        channelerrors = []
        poolchannels = []
        componentgroup = {"smycp": True}
        datasourcegroup = {"scalar_uchar": True}

        self._cf.dp.SetCommandVariable(["CPDICT", json.dumps(self.smycps)])
        self._cf.dp.SetCommandVariable(["DSDICT", json.dumps(self.smydss)])

        cnf = json.loads(rs.profileConfiguration)
        cnf["Timer"] = '[]'
        cnf["PreselectingDataSources"] = json.dumps(poolchannels)
        cnf["ComponentPreselection"] = json.dumps(componentgroup)
        cnf["DataSourcePreselection"] = json.dumps(datasourcegroup)
        rs.profileConfiguration = json.dumps(cnf)
        rs.preselectComponents()
        res = self.value(rs, "ComponentPreselection")
        res2 = self.value(rs, "DataSourcePreselection")

        self.myAssertDict(json.loads(res), {"smycp": True})
        self.myAssertDict(json.loads(res2), {"scalar_uchar": True})
        self.assertEqual(channelerrors, [])

        self.assertTrue(val["MntGrp"] in self._cf.dp.availableSelections())

    # test
    # \brief It tests default settings
    def test_preselectComponents_wds_false(self):
        fun = sys._getframe().f_code.co_name
        print("Run: %s.%s() " % (self.__class__.__name__, fun))
        val = {"ConfigDevice": self._cf.dp.name(),
               "WriterDevice": self._wr.dp.name(),
               "Door": 'doortestp09/testts/t1r228',
               "MntGrp": 'nxsmntgrp'}

        # db = tango.Database()
        self._ms.dps[list(self._ms.ms.keys())[0]].Init()
        rs = self.openRecSelector()
        rs.configDevice = val["ConfigDevice"]
        rs.door = val["Door"]
        rs.mntGrp = val["MntGrp"]
        rs.writerDevice = val["WriterDevice"]

        self._ms.dps[list(self._ms.ms.keys())[0]].Init()

        channelerrors = []
        poolchannels = []
        componentgroup = {"smycp": False}
        datasourcegroup = {"scalar_uchar": False}

        self._cf.dp.SetCommandVariable(["CPDICT", json.dumps(self.smycps)])
        self._cf.dp.SetCommandVariable(["DSDICT", json.dumps(self.smydss)])

        cnf = json.loads(rs.profileConfiguration)
        cnf["Timer"] = '[]'
        cnf["PreselectingDataSources"] = json.dumps(poolchannels)
        cnf["ComponentPreselection"] = json.dumps(componentgroup)
        cnf["DataSourcePreselection"] = json.dumps(datasourcegroup)
        rs.profileConfiguration = json.dumps(cnf)
        rs.preselectComponents()
        res = self.value(rs, "ComponentPreselection")
        res2 = self.value(rs, "DataSourcePreselection")

        self.myAssertDict(json.loads(res), {"smycp": False})
        self.myAssertDict(json.loads(res2), {"scalar_uchar": False})
        self.assertEqual(channelerrors, [])

        self.assertTrue(val["MntGrp"] in self._cf.dp.availableSelections())
        sed = json.loads(self._cf.dp.selections([val["MntGrp"]])[0])
        self.assertEqual(len(list(sed.keys())), len(self._keys))
        for key, vl in self._keys:
            self.assertTrue(key in sed.keys())
            if key in val:
                self.assertEqual(sed[key], val[key])
            elif key == 'ComponentPreselection':
                self.assertEqual(set(json.loads(sed[key])),
                                 set(json.loads(res)))
            elif key == 'PreselectingDataSources':
                self.assertEqual(set(json.loads(sed[key])),
                                 set(poolchannels))
            elif key == 'DataSourcePreselection':
                self.assertEqual(set(json.loads(sed[key])),
                                 set(json.loads(res2)))
            else:
                self.assertEqual(sed[key], vl)

    # test
    # \brief It tests default settings
    def test_preselectComponents_wds(self):
        fun = sys._getframe().f_code.co_name
        print("Run: %s.%s() " % (self.__class__.__name__, fun))
        val = {"ConfigDevice": self._cf.dp.name(),
               "WriterDevice": self._wr.dp.name(),
               "Door": 'doortestp09/testts/t1r228',
               "MntGrp": 'nxsmntgrp'}

        # db = tango.Database()
        self._ms.dps[list(self._ms.ms.keys())[0]].Init()
        rs = self.openRecSelector()
        rs.configDevice = val["ConfigDevice"]
        rs.door = val["Door"]
        rs.mntGrp = val["MntGrp"]
        rs.writerDevice = val["WriterDevice"]

        self._ms.dps[list(self._ms.ms.keys())[0]].Init()

        channelerrors = []
        poolchannels = []
        componentgroup = {"smycp": None}
        datasourcegroup = {"scalar_uchar": None}

        self._cf.dp.SetCommandVariable(["CPDICT", json.dumps(self.smycps)])
        self._cf.dp.SetCommandVariable(["DSDICT", json.dumps(self.smydss)])

        cnf = json.loads(rs.profileConfiguration)
        cnf["Timer"] = '[]'
        cnf["PreselectingDataSources"] = json.dumps(poolchannels)
        cnf["ComponentPreselection"] = json.dumps(componentgroup)
        cnf["DataSourcePreselection"] = json.dumps(datasourcegroup)
        rs.profileConfiguration = json.dumps(cnf)
        rs.preselectComponents()
        res = self.value(rs, "ComponentPreselection")
        res2 = self.value(rs, "DataSourcePreselection")

        self.myAssertDict(json.loads(res), {"smycp": True})
        self.myAssertDict(json.loads(res2), {"scalar_uchar": True})
        self.assertEqual(channelerrors, [])

        self.assertTrue(val["MntGrp"] in self._cf.dp.availableSelections())
        sed = json.loads(self._cf.dp.selections([val["MntGrp"]])[0])
        self.assertEqual(len(list(sed.keys())), len(self._keys))
        for key, vl in self._keys:
            self.assertTrue(key in sed.keys())
            if key in val:
                self.assertEqual(sed[key], val[key])
            elif key == 'ComponentPreselection':
                self.assertEqual(set(json.loads(sed[key])),
                                 set(json.loads(res)))
            elif key == 'PreselectingDataSources':
                self.assertEqual(set(json.loads(sed[key])),
                                 set(poolchannels))
            elif key == 'DataSourcePreselection':
                self.assertEqual(set(json.loads(sed[key])),
                                 set(json.loads(res2)))
            else:
                self.assertEqual(sed[key], vl)

    # test
    # \brief It tests default settings
    def test_preselectComponents_wds2(self):
        fun = sys._getframe().f_code.co_name
        print("Run: %s.%s() " % (self.__class__.__name__, fun))
        val = {"ConfigDevice": self._cf.dp.name(),
               "WriterDevice": self._wr.dp.name(),
               "Door": 'doortestp09/testts/t1r228',
               "MntGrp": 'nxsmntgrp'}

        # db = tango.Database()
        self._ms.dps[list(self._ms.ms.keys())[0]].Init()
        rs = self.openRecSelector()
        rs.configDevice = val["ConfigDevice"]
        rs.door = val["Door"]
        rs.mntGrp = val["MntGrp"]
        rs.writerDevice = val["WriterDevice"]

        self._ms.dps[list(self._ms.ms.keys())[0]].Init()

        channelerrors = []
        poolchannels = []
        componentgroup = {"smycp": False, "smycp2": True, "smycp3": None}
        datasourcegroup = {"scalar_uchar": None,
                           "scalar_string": False,
                           "scalar_ulong": True}

        self._cf.dp.SetCommandVariable(["CPDICT", json.dumps(self.smycps)])
        self._cf.dp.SetCommandVariable(["DSDICT", json.dumps(self.smydss)])

        cnf = json.loads(rs.profileConfiguration)
        cnf["Timer"] = '[]'
        cnf["PreselectingDataSources"] = json.dumps(poolchannels)
        cnf["ComponentPreselection"] = json.dumps(componentgroup)
        cnf["DataSourcePreselection"] = json.dumps(datasourcegroup)
        rs.profileConfiguration = json.dumps(cnf)
        rs.preselectComponents()
        res = self.value(rs, "ComponentPreselection")
        resd = self.value(rs, "DataSourcePreselection")

        self.myAssertDict(json.loads(res), {
            "smycp": False, "smycp2": True, "smycp3": True})
        self.myAssertDict(json.loads(resd), {"scalar_uchar": True,
                                             "scalar_string": False,
                                             "scalar_ulong": True})
        self.assertEqual(channelerrors, [])

        # res2 = json.loads(self._cf.dp.GetCommandVariable("VARS"))
        self.assertTrue(val["MntGrp"] in self._cf.dp.availableSelections())
        sed = json.loads(self._cf.dp.selections([val["MntGrp"]])[0])
        self.assertEqual(len(list(sed.keys())), len(self._keys))
        for key, vl in self._keys:
            self.assertTrue(key in sed.keys())
            if key in val:
                self.assertEqual(sed[key], val[key])
            elif key == 'ComponentPreselection':
                self.assertEqual(set(json.loads(sed[key])),
                                 set(json.loads(res)))
            elif key == 'DataSourcePreselection':
                self.assertEqual(set(json.loads(sed[key])),
                                 set(json.loads(resd)))
            elif key == 'PreselectingDataSources':
                self.assertEqual(set(json.loads(sed[key])),
                                 set(poolchannels))
            else:
                self.assertEqual(sed[key], vl)

    # test
    # \brief It tests default settings
    def test_preselectComponents_2wds(self):
        fun = sys._getframe().f_code.co_name
        print("Run: %s.%s() " % (self.__class__.__name__, fun))
        val = {"ConfigDevice": self._cf.dp.name(),
               "WriterDevice": self._wr.dp.name(),
               "Door": 'doortestp09/testts/t1r228',
               "MntGrp": 'nxsmntgrp'}
        simps2 = TestServerSetUp.TestServerSetUp(
            "ttestp09/testts/t2r228", "S2")
        try:
            simps2.setUp()

            db = tango.Database()
            db.put_device_property(list(self._ms.ms.keys())[0],
                                   {'PoolNames': self._pool.dp.name()})
            self._ms.dps[list(self._ms.ms.keys())[0]].Init()
            rs = self.openRecSelector()
            rs.configDevice = val["ConfigDevice"]
            rs.door = val["Door"]
            rs.mntGrp = val["MntGrp"]
            rs.writerDevice = val["WriterDevice"]

            self._ms.dps[list(self._ms.ms.keys())[0]].Init()

            channelerrors = []
            poolchannels = []
            componentgroup = {
                "smycp": None, "smycp2": None, "smycp3": None,
                "s2mycp": None, "s2mycp2": None, "s2mycp3": None
            }
            datasourcegroup = {
                "scalar_uchar": None, "scalar_string": None,
                "scalar_ulong": None,
                "scalar2_uchar": None, "scalar2_string": None,
                "scalar2_ulong": None,
            }
            cps = dict(self.smycps)
            cps.update(self.smycps2)
            dss = dict(self.smydss)
            dss.update(self.smydss2)

            self._cf.dp.SetCommandVariable(["CPDICT", json.dumps(cps)])
            self._cf.dp.SetCommandVariable(["DSDICT", json.dumps(dss)])

            cnf = json.loads(rs.profileConfiguration)
            cnf["Timer"] = '[]'
            cnf["PreselectingDataSources"] = json.dumps(poolchannels)
            cnf["ComponentPreselection"] = json.dumps(componentgroup)
            cnf["DataSourcePreselection"] = json.dumps(datasourcegroup)
            rs.profileConfiguration = json.dumps(cnf)
            rs.preselectComponents()
            res = self.value(rs, "ComponentPreselection")
            resd = self.value(rs, "DataSourcePreselection")

            self.myAssertDict(json.loads(res), {
                "smycp": True, "smycp2": True, "smycp3": True,
                "s2mycp": True, "s2mycp2": True, "s2mycp3": True})
            self.myAssertDict(json.loads(resd), {
                "scalar_uchar": True, "scalar_string": True,
                "scalar_ulong": True,
                "scalar2_uchar": True, "scalar2_string": True,
                "scalar2_ulong": True,
            })
            self.assertEqual(len(channelerrors), 0)

            # res2 = json.loads(self._cf.dp.GetCommandVariable("VARS"))
            self.assertTrue(val["MntGrp"] in self._cf.dp.availableSelections())
            sed = json.loads(self._cf.dp.selections([val["MntGrp"]])[0])
            self.assertEqual(len(list(sed.keys())), len(self._keys))
            for key, vl in self._keys:
                self.assertTrue(key in sed.keys())
                if key in val:
                    self.assertEqual(sed[key], val[key])
                elif key == 'ComponentPreselection':
                    self.assertEqual(set(json.loads(sed[key])),
                                     set(json.loads(res)))
                elif key == 'DataSourcePreselection':
                    self.assertEqual(set(json.loads(sed[key])),
                                     set(json.loads(resd)))
                elif key == 'PreselectingDataSources':
                    self.assertEqual(set(json.loads(sed[key])),
                                     set(poolchannels))
                else:
                    self.assertEqual(sed[key], vl)
        finally:
            simps2.tearDown()

    # test
    # \brief It tests default settings
    def test_preselectComponents_2wds_false(self):
        fun = sys._getframe().f_code.co_name
        print("Run: %s.%s() " % (self.__class__.__name__, fun))
        val = {"ConfigDevice": self._cf.dp.name(),
               "WriterDevice": self._wr.dp.name(),
               "Door": 'doortestp09/testts/t1r228',
               "MntGrp": 'nxsmntgrp'}
        simps2 = TestServerSetUp.TestServerSetUp(
            "ttestp09/testts/t2r228", "S2")
        try:
            simps2.setUp()

            # db = tango.Database()
            self._ms.dps[list(self._ms.ms.keys())[0]].Init()
            rs = self.openRecSelector()
            rs.configDevice = val["ConfigDevice"]
            rs.door = val["Door"]
            rs.mntGrp = val["MntGrp"]
            rs.writerDevice = val["WriterDevice"]

            self._ms.dps[list(self._ms.ms.keys())[0]].Init()

            channelerrors = []
            poolchannels = []
            componentgroup = {
                "smycp": False, "smycp2": False, "smycp3": False,
                "s2mycp": False, "s2mycp2": False,
                "s2mycp3": False}
            datasourcegroup = {
                "scalar_uchar": False, "scalar_string": False,
                "scalar_ulong": False,
                "scalar2_uchar": False, "scalar2_string": False,
                "scalar2_ulong": False,
            }

            cps = dict(self.smycps)
            cps.update(self.smycps2)
            dss = dict(self.smydss)
            dss.update(self.smydss2)

            self._cf.dp.SetCommandVariable(["CPDICT", json.dumps(cps)])
            self._cf.dp.SetCommandVariable(["DSDICT", json.dumps(dss)])

            cnf = json.loads(rs.profileConfiguration)
            cnf["Timer"] = '[]'
            cnf["PreselectingDataSources"] = json.dumps(poolchannels)
            cnf["ComponentPreselection"] = json.dumps(componentgroup)
            cnf["DataSourcePreselection"] = json.dumps(datasourcegroup)
            rs.profileConfiguration = json.dumps(cnf)
            rs.preselectComponents()
            res = self.value(rs, "ComponentPreselection")
            resd = self.value(rs, "DataSourcePreselection")

            self.myAssertDict(json.loads(res), {
                "smycp": False, "smycp2": False, "smycp3": False,
                "s2mycp": False, "s2mycp2": False, "s2mycp3": False})
            self.myAssertDict(json.loads(resd), {
                "scalar_uchar": False, "scalar_string": False,
                "scalar_ulong": False,
                "scalar2_uchar": False, "scalar2_string": False,
                "scalar2_ulong": False,
            })
            self.assertEqual(len(channelerrors), 0)

            # res2 = json.loads(self._cf.dp.GetCommandVariable("VARS"))
            self.assertTrue(val["MntGrp"] in self._cf.dp.availableSelections())
            sed = json.loads(self._cf.dp.selections([val["MntGrp"]])[0])
            self.assertEqual(len(list(sed.keys())), len(self._keys))
            for key, vl in self._keys:
                self.assertTrue(key in sed.keys())
                if key in val:
                    self.assertEqual(sed[key], val[key])
                elif key == 'ComponentPreselection':
                    self.assertEqual(set(json.loads(sed[key])),
                                     set(json.loads(res)))
                elif key == 'DataSourcePreselection':
                    self.assertEqual(set(json.loads(sed[key])),
                                     set(json.loads(resd)))
                elif key == 'PreselectingDataSources':
                    self.assertEqual(set(json.loads(sed[key])),
                                     set(poolchannels))
                else:
                    self.assertEqual(sed[key], vl)
        finally:
            simps2.tearDown()

    # test
    # \brief It tests default settings
    def test_preselectComponents_2wds_dvnorunning(self):
        fun = sys._getframe().f_code.co_name
        print("Run: %s.%s() " % (self.__class__.__name__, fun))
        val = {"ConfigDevice": self._cf.dp.name(),
               "WriterDevice": self._wr.dp.name(),
               "Door": 'doortestp09/testts/t1r228',
               "MntGrp": 'nxsmntgrp'}
        simps2 = TestServerSetUp.TestServerSetUp(
            "ttestp09/testts/t2r228", "S2")
        try:
            simps2.add()

            # db = tango.Database()
            self._ms.dps[list(self._ms.ms.keys())[0]].Init()
            rs = self.openRecSelector()
            rs.configDevice = val["ConfigDevice"]
            rs.door = val["Door"]
            rs.mntGrp = val["MntGrp"]
            rs.writerDevice = val["WriterDevice"]

            self._ms.dps[list(self._ms.ms.keys())[0]].Init()

            # channelerrors = []
            poolchannels = []
            componentgroup = {
                "smycp": True, "smycp2": False, "smycp3": None,
                "s2mycp": True, "s2mycp2": False, "s2mycp3": None}
            datasourcegroup = {
                "scalar_uchar": True, "scalar_string": None,
                "scalar_ulong": False,
                "scalar2_uchar": True, "scalar2_string": None,
                "scalar2_ulong": False,
            }

            cps = dict(self.smycps)
            cps.update(self.smycps2)
            dss = dict(self.smydss)
            dss.update(self.smydss2)

            self._cf.dp.SetCommandVariable(["CPDICT", json.dumps(cps)])
            self._cf.dp.SetCommandVariable(["DSDICT", json.dumps(dss)])

            cnf = json.loads(rs.profileConfiguration)
            cnf["Timer"] = '[]'
            cnf["PreselectingDataSources"] = json.dumps(poolchannels)
            cnf["ComponentPreselection"] = json.dumps(componentgroup)
            cnf["DataSourcePreselection"] = json.dumps(datasourcegroup)
            rs.profileConfiguration = json.dumps(cnf)
            rs.preselectComponents()
            res = self.value(rs, "ComponentPreselection")
            resd = self.value(rs, "DataSourcePreselection")

            self.myAssertDict(json.loads(res), {
                "smycp": True, "smycp2": False, "smycp3": True,
                "s2mycp": None, "s2mycp2": False, "s2mycp3": None})
            self.myAssertDict(json.loads(resd), {
                "scalar_uchar": True, "scalar_string": True,
                "scalar_ulong": False,
                "scalar2_uchar": None, "scalar2_string": None,
                "scalar2_ulong": False,
            })
            self.assertEqual(len(rs.descriptionErrors), 4)

            # res2 = json.loads(self._cf.dp.GetCommandVariable("VARS"))
            self.assertTrue(val["MntGrp"] in self._cf.dp.availableSelections())
            sed = json.loads(self._cf.dp.selections([val["MntGrp"]])[0])
            self.assertEqual(len(list(sed.keys())), len(self._keys))
            for key, vl in self._keys:
                self.assertTrue(key in sed.keys())
                if key in val:
                    self.assertEqual(sed[key], val[key])
                elif key == 'ComponentPreselection':
                    self.assertEqual(set(json.loads(sed[key])),
                                     set(json.loads(res)))
                elif key == 'DataSourcePreselection':
                    self.assertEqual(set(json.loads(sed[key])),
                                     set(json.loads(resd)))
                elif key == 'PreselectingDataSources':
                    self.assertEqual(set(json.loads(sed[key])),
                                     set(poolchannels))
                else:
                    self.assertEqual(sed[key], vl)
        finally:
            simps2.delete()

    # test
    # \brief It tests default settings
    def test_preselectComponents_2wds_dvnorunning_pe(self):
        fun = sys._getframe().f_code.co_name
        print("Run: %s.%s() " % (self.__class__.__name__, fun))
        val = {"ConfigDevice": self._cf.dp.name(),
               "WriterDevice": self._wr.dp.name(),
               "Door": 'doortestp09/testts/t1r228',
               "MntGrp": 'nxsmntgrp'}
        simps2 = TestServerSetUp.TestServerSetUp(
            "ttestp09/testts/t2r228", "S2")
        try:
            simps2.add()

            # db = tango.Database()
            self._ms.dps[list(self._ms.ms.keys())[0]].Init()
            rs = self.openRecSelector()
            rs.configDevice = val["ConfigDevice"]
            rs.door = val["Door"]
            rs.mntGrp = val["MntGrp"]
            rs.writerDevice = val["WriterDevice"]

            self._ms.dps[list(self._ms.ms.keys())[0]].Init()

            # channelerrors = []
            poolchannels = []
            componentgroup = dict((k, None) for k in self.specps.keys())
            datasourcegroup = dict((k, None) for k in self.spedss.keys())

            cps = dict(self.smycps)
            cps.update(self.smycps2)
            cps.update(self.specps)
            dss = dict(self.smydss)
            dss.update(self.smydss2)
            dss.update(self.spedss)

            self._cf.dp.SetCommandVariable(["CPDICT", json.dumps(cps)])
            self._cf.dp.SetCommandVariable(["DSDICT", json.dumps(dss)])

            cnf = json.loads(rs.profileConfiguration)
            cnf["Timer"] = '[]'
            cnf["PreselectingDataSources"] = json.dumps(poolchannels)
            cnf["ComponentPreselection"] = json.dumps(componentgroup)
            cnf["DataSourcePreselection"] = json.dumps(datasourcegroup)
            rs.profileConfiguration = json.dumps(cnf)
            rs.preselectComponents()
            res = self.value(rs, "ComponentPreselection")
            resd = self.value(rs, "DataSourcePreselection")

            self.myAssertDict(json.loads(res), {
                u'pyeval1a': True, u'pyeval2a': None, u'pyeval2c': None,
                u'pyeval2b': True, u'pyeval2': True, u'pyeval0': True,
                u'pyeval1': True})
            self.myAssertDict(json.loads(resd), {
                u'pyeval1ads': True, u'pyeval2ads': None, u'pyeval2bds': True,
                u'pyeval2cds': None, u'pyeval0ds': True, u'pyeval1ds': True,
                u'pyeval2ds': True}
            )
            self.assertEqual(len(rs.descriptionErrors), 4)

            # res2 = json.loads(self._cf.dp.GetCommandVariable("VARS"))
            self.assertTrue(val["MntGrp"] in self._cf.dp.availableSelections())
            sed = json.loads(self._cf.dp.selections([val["MntGrp"]])[0])
            self.assertEqual(len(list(sed.keys())), len(self._keys))
            for key, vl in self._keys:
                self.assertTrue(key in sed.keys())
                if key in val:
                    self.assertEqual(sed[key], val[key])
                elif key == 'ComponentPreselection':
                    self.assertEqual(set(json.loads(sed[key])),
                                     set(json.loads(res)))
                elif key == 'DataSourcePreselection':
                    self.assertEqual(set(json.loads(sed[key])),
                                     set(json.loads(resd)))
                elif key == 'PreselectingDataSources':
                    self.assertEqual(set(json.loads(sed[key])),
                                     set(poolchannels))
                else:
                    self.assertEqual(sed[key], vl)
        finally:
            simps2.delete()

    def test_preselectComponents_2wds2_dvnorunning_pe(self):
        fun = sys._getframe().f_code.co_name
        print("Run: %s.%s() " % (self.__class__.__name__, fun))
        val = {"ConfigDevice": self._cf.dp.name(),
               "WriterDevice": self._wr.dp.name(),
               "Door": 'doortestp09/testts/t1r228',
               "MntGrp": 'nxsmntgrp'}
        simps2 = TestServerSetUp.TestServerSetUp(
            "ttestp09/testts/t2r228", "S2")
        try:
            simps2.setUp()

            # db = tango.Database()
            self._ms.dps[list(self._ms.ms.keys())[0]].Init()
            rs = self.openRecSelector()
            rs.configDevice = val["ConfigDevice"]
            rs.door = val["Door"]
            rs.mntGrp = val["MntGrp"]
            rs.writerDevice = val["WriterDevice"]

            self._ms.dps[list(self._ms.ms.keys())[0]].Init()

            # channelerrors = []
            poolchannels = []
            componentgroup = dict((k, None) for k in self.specps.keys())
            datasourcegroup = dict((k, None) for k in self.spedss.keys())

            cps = dict(self.smycps)
            cps.update(self.smycps2)
            cps.update(self.specps)
            dss = dict(self.smydss)
            dss.update(self.smydss2)
            dss.update(self.spedss)

            self._cf.dp.SetCommandVariable(["CPDICT", json.dumps(cps)])
            self._cf.dp.SetCommandVariable(["DSDICT", json.dumps(dss)])

            cnf = json.loads(rs.profileConfiguration)
            cnf["Timer"] = '[]'
            cnf["PreselectingDataSources"] = json.dumps(poolchannels)
            cnf["ComponentPreselection"] = json.dumps(componentgroup)
            cnf["DataSourcePreselection"] = json.dumps(datasourcegroup)
            rs.profileConfiguration = json.dumps(cnf)
            rs.preselectComponents()
            res = self.value(rs, "ComponentPreselection")
            resd = self.value(rs, "DataSourcePreselection")

            self.myAssertDict(json.loads(res), {
                u'pyeval1a': True, u'pyeval2a': True, u'pyeval2c': True,
                u'pyeval2b': True, u'pyeval2': True, u'pyeval0': True,
                u'pyeval1': True})
            self.myAssertDict(json.loads(resd), {
                u'pyeval1ads': True, u'pyeval2ads': True, u'pyeval2bds': True,
                u'pyeval2cds': True, u'pyeval0ds': True, u'pyeval1ds': True,
                u'pyeval2ds': True}
            )
            self.assertTrue(not rs.descriptionErrors)

            # res2 = json.loads(self._cf.dp.GetCommandVariable("VARS"))
            self.assertTrue(val["MntGrp"] in self._cf.dp.availableSelections())
            sed = json.loads(self._cf.dp.selections([val["MntGrp"]])[0])
            self.assertEqual(len(list(sed.keys())), len(self._keys))
            for key, vl in self._keys:
                self.assertTrue(key in sed.keys())
                if key in val:
                    self.assertEqual(sed[key], val[key])
                elif key == 'ComponentPreselection':
                    self.assertEqual(set(json.loads(sed[key])),
                                     set(json.loads(res)))
                elif key == 'DataSourcePreselection':
                    self.assertEqual(set(json.loads(sed[key])),
                                     set(json.loads(resd)))
                elif key == 'PreselectingDataSources':
                    self.assertEqual(set(json.loads(sed[key])),
                                     set(poolchannels))
                else:
                    self.assertEqual(sed[key], vl)
        finally:
            simps2.tearDown()

    def test_preselectComponents_2wds2_dvnorunning_pe_true(self):
        fun = sys._getframe().f_code.co_name
        print("Run: %s.%s() " % (self.__class__.__name__, fun))
        val = {"ConfigDevice": self._cf.dp.name(),
               "WriterDevice": self._wr.dp.name(),
               "Door": 'doortestp09/testts/t1r228',
               "MntGrp": 'nxsmntgrp'}
        simps2 = TestServerSetUp.TestServerSetUp(
            "ttestp09/testts/t2r228", "S2")
        try:
            simps2.setUp()

            # db = tango.Database()
            self._ms.dps[list(self._ms.ms.keys())[0]].Init()
            rs = self.openRecSelector()
            rs.configDevice = val["ConfigDevice"]
            rs.door = val["Door"]
            rs.mntGrp = val["MntGrp"]
            rs.writerDevice = val["WriterDevice"]

            self._ms.dps[list(self._ms.ms.keys())[0]].Init()

            # channelerrors = []
            poolchannels = []
            componentgroup = dict((k, True) for k in self.specps.keys())
            datasourcegroup = dict((k, True) for k in self.spedss.keys())

            cps = dict(self.smycps)
            cps.update(self.smycps2)
            cps.update(self.specps)
            dss = dict(self.smydss)
            dss.update(self.smydss2)
            dss.update(self.spedss)

            self._cf.dp.SetCommandVariable(["CPDICT", json.dumps(cps)])
            self._cf.dp.SetCommandVariable(["DSDICT", json.dumps(dss)])

            cnf = json.loads(rs.profileConfiguration)
            cnf["Timer"] = '[]'
            cnf["PreselectingDataSources"] = json.dumps(poolchannels)
            cnf["ComponentPreselection"] = json.dumps(componentgroup)
            cnf["DataSourcePreselection"] = json.dumps(datasourcegroup)
            rs.profileConfiguration = json.dumps(cnf)
            rs.preselectComponents()
            res = self.value(rs, "ComponentPreselection")
            resd = self.value(rs, "DataSourcePreselection")

            self.myAssertDict(json.loads(res), {
                u'pyeval1a': True, u'pyeval2a': True, u'pyeval2c': True,
                u'pyeval2b': True, u'pyeval2': True, u'pyeval0': True,
                u'pyeval1': True})
            self.myAssertDict(json.loads(resd), {
                u'pyeval1ads': True, u'pyeval2ads': True, u'pyeval2bds': True,
                u'pyeval2cds': True, u'pyeval0ds': True, u'pyeval1ds': True,
                u'pyeval2ds': True}
            )
            self.assertTrue(not rs.descriptionErrors)

            # res2 = json.loads(self._cf.dp.GetCommandVariable("VARS"))
            self.assertTrue(val["MntGrp"] in self._cf.dp.availableSelections())
            sed = json.loads(self._cf.dp.selections([val["MntGrp"]])[0])
            self.assertEqual(len(list(sed.keys())), len(self._keys))
            for key, vl in self._keys:
                self.assertTrue(key in sed.keys())
                if key in val:
                    self.assertEqual(sed[key], val[key])
                elif key == 'ComponentPreselection':
                    self.assertEqual(set(json.loads(sed[key])),
                                     set(json.loads(res)))
                elif key == 'DataSourcePreselection':
                    self.assertEqual(set(json.loads(sed[key])),
                                     set(json.loads(resd)))
                elif key == 'PreselectingDataSources':
                    self.assertEqual(set(json.loads(sed[key])),
                                     set(poolchannels))
                else:
                    self.assertEqual(sed[key], vl)
        finally:
            simps2.tearDown()

    def test_preselectComponents_2wds2_dvnorunning_pe_false(self):
        fun = sys._getframe().f_code.co_name
        print("Run: %s.%s() " % (self.__class__.__name__, fun))
        val = {"ConfigDevice": self._cf.dp.name(),
               "WriterDevice": self._wr.dp.name(),
               "Door": 'doortestp09/testts/t1r228',
               "MntGrp": 'nxsmntgrp'}
        simps2 = TestServerSetUp.TestServerSetUp(
            "ttestp09/testts/t2r228", "S2")
        try:
            simps2.setUp()

            # db = tango.Database()
            self._ms.dps[list(self._ms.ms.keys())[0]].Init()
            rs = self.openRecSelector()
            rs.configDevice = val["ConfigDevice"]
            rs.door = val["Door"]
            rs.mntGrp = val["MntGrp"]
            rs.writerDevice = val["WriterDevice"]

            self._ms.dps[list(self._ms.ms.keys())[0]].Init()

            # channelerrors = []
            poolchannels = []
            componentgroup = dict((k, False) for k in self.specps.keys())
            datasourcegroup = dict((k, False) for k in self.spedss.keys())

            cps = dict(self.smycps)
            cps.update(self.smycps2)
            cps.update(self.specps)
            dss = dict(self.smydss)
            dss.update(self.smydss2)
            dss.update(self.spedss)

            self._cf.dp.SetCommandVariable(["CPDICT", json.dumps(cps)])
            self._cf.dp.SetCommandVariable(["DSDICT", json.dumps(dss)])

            cnf = json.loads(rs.profileConfiguration)
            cnf["Timer"] = '[]'
            cnf["PreselectingDataSources"] = json.dumps(poolchannels)
            cnf["ComponentPreselection"] = json.dumps(componentgroup)
            cnf["DataSourcePreselection"] = json.dumps(datasourcegroup)
            rs.profileConfiguration = json.dumps(cnf)
            rs.preselectComponents()
            res = self.value(rs, "ComponentPreselection")
            resd = self.value(rs, "DataSourcePreselection")

            self.myAssertDict(json.loads(res), {
                u'pyeval1a': False, u'pyeval2a': False, u'pyeval2c': False,
                u'pyeval2b': False, u'pyeval2': False, u'pyeval0': False,
                u'pyeval1': False})
            self.myAssertDict(json.loads(resd), {
                u'pyeval1ads': False, u'pyeval2ads': False,
                u'pyeval2bds': False,
                u'pyeval2cds': False, u'pyeval0ds': False,
                u'pyeval1ds': False,
                u'pyeval2ds': False}
            )
            self.assertTrue(not rs.descriptionErrors)

            # res2 = json.loads(self._cf.dp.GetCommandVariable("VARS"))
            self.assertTrue(val["MntGrp"] in self._cf.dp.availableSelections())
            sed = json.loads(self._cf.dp.selections([val["MntGrp"]])[0])
            self.assertEqual(len(list(sed.keys())), len(self._keys))
            for key, vl in self._keys:
                self.assertTrue(key in sed.keys())
                if key in val:
                    self.assertEqual(sed[key], val[key])
                elif key == 'ComponentPreselection':
                    self.assertEqual(set(json.loads(sed[key])),
                                     set(json.loads(res)))
                elif key == 'DataSourcePreselection':
                    self.assertEqual(set(json.loads(sed[key])),
                                     set(json.loads(resd)))
                elif key == 'PreselectingDataSources':
                    self.assertEqual(set(json.loads(sed[key])),
                                     set(poolchannels))
                else:
                    self.assertEqual(sed[key], vl)
        finally:
            simps2.tearDown()

    # test
    # \brief It tests default settings
    def test_preselectComponents_2wds_dvnorunning_pe_false(self):
        fun = sys._getframe().f_code.co_name
        print("Run: %s.%s() " % (self.__class__.__name__, fun))
        val = {"ConfigDevice": self._cf.dp.name(),
               "WriterDevice": self._wr.dp.name(),
               "Door": 'doortestp09/testts/t1r228',
               "MntGrp": 'nxsmntgrp'}
        simps2 = TestServerSetUp.TestServerSetUp(
            "ttestp09/testts/t2r228", "S2")
        try:
            simps2.add()

            # db = tango.Database()
            self._ms.dps[list(self._ms.ms.keys())[0]].Init()
            rs = self.openRecSelector()
            rs.configDevice = val["ConfigDevice"]
            rs.door = val["Door"]
            rs.mntGrp = val["MntGrp"]
            rs.writerDevice = val["WriterDevice"]

            self._ms.dps[list(self._ms.ms.keys())[0]].Init()

            # channelerrors = []
            poolchannels = []
            componentgroup = dict((k, False) for k in self.specps.keys())
            datasourcegroup = dict((k, False) for k in self.spedss.keys())

            cps = dict(self.smycps)
            cps.update(self.smycps2)
            cps.update(self.specps)
            dss = dict(self.smydss)
            dss.update(self.smydss2)
            dss.update(self.spedss)

            self._cf.dp.SetCommandVariable(["CPDICT", json.dumps(cps)])
            self._cf.dp.SetCommandVariable(["DSDICT", json.dumps(dss)])

            cnf = json.loads(rs.profileConfiguration)
            cnf["Timer"] = '[]'
            cnf["PreselectingDataSources"] = json.dumps(poolchannels)
            cnf["ComponentPreselection"] = json.dumps(componentgroup)
            cnf["DataSourcePreselection"] = json.dumps(datasourcegroup)
            rs.profileConfiguration = json.dumps(cnf)
            rs.preselectComponents()
            res = self.value(rs, "ComponentPreselection")
            resd = self.value(rs, "DataSourcePreselection")

            self.myAssertDict(json.loads(res), {
                u'pyeval1a': False, u'pyeval2a': False, u'pyeval2c': False,
                u'pyeval2b': False, u'pyeval2': False, u'pyeval0': False,
                u'pyeval1': False})
            self.myAssertDict(json.loads(resd), {
                u'pyeval1ads': False, u'pyeval2ads': False,
                u'pyeval2bds': False,
                u'pyeval2cds': False, u'pyeval0ds': False,
                u'pyeval1ds': False,
                u'pyeval2ds': False}
            )
            self.assertEqual(len(rs.descriptionErrors or []), 0)

            # res2 = json.loads(self._cf.dp.GetCommandVariable("VARS"))
            self.assertTrue(val["MntGrp"] in self._cf.dp.availableSelections())
            sed = json.loads(self._cf.dp.selections([val["MntGrp"]])[0])
            self.assertEqual(len(list(sed.keys())), len(self._keys))
            for key, vl in self._keys:
                self.assertTrue(key in sed.keys())
                if key in val:
                    self.assertEqual(sed[key], val[key])
                elif key == 'ComponentPreselection':
                    self.assertEqual(set(json.loads(sed[key])),
                                     set(json.loads(res)))
                elif key == 'DataSourcePreselection':
                    self.assertEqual(set(json.loads(sed[key])),
                                     set(json.loads(resd)))
                elif key == 'PreselectingDataSources':
                    self.assertEqual(set(json.loads(sed[key])),
                                     set(poolchannels))
                else:
                    self.assertEqual(sed[key], vl)
        finally:
            simps2.delete()

    # test
    # \brief It tests default settings
    def test_preselectComponents_2wds_dvnorunning_pe_true(self):
        fun = sys._getframe().f_code.co_name
        print("Run: %s.%s() " % (self.__class__.__name__, fun))
        val = {"ConfigDevice": self._cf.dp.name(),
               "WriterDevice": self._wr.dp.name(),
               "Door": 'doortestp09/testts/t1r228',
               "MntGrp": 'nxsmntgrp'}
        simps2 = TestServerSetUp.TestServerSetUp(
            "ttestp09/testts/t2r228", "S2")
        try:
            simps2.add()

            # db = tango.Database()
            self._ms.dps[list(self._ms.ms.keys())[0]].Init()
            rs = self.openRecSelector()
            rs.configDevice = val["ConfigDevice"]
            rs.door = val["Door"]
            rs.mntGrp = val["MntGrp"]
            rs.writerDevice = val["WriterDevice"]

            self._ms.dps[list(self._ms.ms.keys())[0]].Init()

            # channelerrors = []
            poolchannels = []
            componentgroup = dict((k, True) for k in self.specps.keys())
            datasourcegroup = dict((k, True) for k in self.spedss.keys())

            cps = dict(self.smycps)
            cps.update(self.smycps2)
            cps.update(self.specps)
            dss = dict(self.smydss)
            dss.update(self.smydss2)
            dss.update(self.spedss)

            self._cf.dp.SetCommandVariable(["CPDICT", json.dumps(cps)])
            self._cf.dp.SetCommandVariable(["DSDICT", json.dumps(dss)])

            cnf = json.loads(rs.profileConfiguration)
            cnf["Timer"] = '[]'
            cnf["PreselectingDataSources"] = json.dumps(poolchannels)
            cnf["ComponentPreselection"] = json.dumps(componentgroup)
            cnf["DataSourcePreselection"] = json.dumps(datasourcegroup)
            rs.profileConfiguration = json.dumps(cnf)
            rs.preselectComponents()
            res = self.value(rs, "ComponentPreselection")
            resd = self.value(rs, "DataSourcePreselection")

            self.myAssertDict(json.loads(res), {
                u'pyeval1a': True, u'pyeval2a': None, u'pyeval2c': None,
                u'pyeval2b': True, u'pyeval2': True, u'pyeval0': True,
                u'pyeval1': True})
            self.myAssertDict(json.loads(resd), {
                u'pyeval1ads': True, u'pyeval2ads': None, u'pyeval2bds': True,
                u'pyeval2cds': None, u'pyeval0ds': True, u'pyeval1ds': True,
                u'pyeval2ds': True}
            )
            self.assertEqual(len(rs.descriptionErrors), 4)

            # res2 = json.loads(self._cf.dp.GetCommandVariable("VARS"))
            self.assertTrue(val["MntGrp"] in self._cf.dp.availableSelections())
            sed = json.loads(self._cf.dp.selections([val["MntGrp"]])[0])
            self.assertEqual(len(list(sed.keys())), len(self._keys))
            for key, vl in self._keys:
                self.assertTrue(key in sed.keys())
                if key in val:
                    self.assertEqual(sed[key], val[key])
                elif key == 'ComponentPreselection':
                    self.assertEqual(set(json.loads(sed[key])),
                                     set(json.loads(res)))
                elif key == 'DataSourcePreselection':
                    self.assertEqual(set(json.loads(sed[key])),
                                     set(json.loads(resd)))
                elif key == 'PreselectingDataSources':
                    self.assertEqual(set(json.loads(sed[key])),
                                     set(poolchannels))
                else:
                    self.assertEqual(sed[key], vl)
        finally:
            simps2.delete()

    # test
    # \brief It tests default settings
    def test_preselectComponents_2wds_dvnodef(self):
        fun = sys._getframe().f_code.co_name
        print("Run: %s.%s() " % (self.__class__.__name__, fun))
        val = {"ConfigDevice": self._cf.dp.name(),
               "WriterDevice": self._wr.dp.name(),
               "Door": 'doortestp09/testts/t1r228',
               "MntGrp": 'nxsmntgrp'}

        # db = tango.Database()
        self._ms.dps[list(self._ms.ms.keys())[0]].Init()
        rs = self.openRecSelector()
        rs.configDevice = val["ConfigDevice"]
        rs.door = val["Door"]
        rs.mntGrp = val["MntGrp"]
        rs.writerDevice = val["WriterDevice"]

        self._ms.dps[list(self._ms.ms.keys())[0]].Init()

        # channelerrors = []
        poolchannels = []
        componentgroup = {"smycp": None, "smycp2": False, "smycp3": True,
                          "s2mycp": None, "s2mycp2": False, "s2mycp3": True}
        datasourcegroup = {
            "scalar_uchar": True, "scalar_string": None,
            "scalar_ulong": False,
            "scalar2_uchar": True, "scalar2_string": None,
            "scalar2_ulong": False,
        }

        cps = dict(self.smycps)
        cps.update(self.smycps2)
        dss = dict(self.smydss)
        dss.update(self.smydss2)

        self._cf.dp.SetCommandVariable(["CPDICT", json.dumps(cps)])
        self._cf.dp.SetCommandVariable(["DSDICT", json.dumps(dss)])

        cnf = json.loads(rs.profileConfiguration)
        cnf["Timer"] = '[]'
        cnf["PreselectingDataSources"] = json.dumps(poolchannels)
        cnf["ComponentPreselection"] = json.dumps(componentgroup)
        cnf["DataSourcePreselection"] = json.dumps(datasourcegroup)
        rs.profileConfiguration = json.dumps(cnf)
        rs.preselectComponents()
        res = self.value(rs, "ComponentPreselection")
        resd = self.value(rs, "DataSourcePreselection")

        self.myAssertDict(json.loads(res), {
            "smycp": True, "smycp2": False, "smycp3": True,
            "s2mycp": None, "s2mycp2": False, "s2mycp3": None})
        self.myAssertDict(json.loads(resd), {
            "scalar_uchar": True, "scalar_string": True,
            "scalar_ulong": False,
            "scalar2_uchar": None, "scalar2_string": None,
            "scalar2_ulong": False,
        })
        self.assertEqual(len(rs.descriptionErrors), 4)

        # res2 = json.loads(self._cf.dp.GetCommandVariable("VARS"))
        self.assertTrue(val["MntGrp"] in self._cf.dp.availableSelections())
        sed = json.loads(self._cf.dp.selections([val["MntGrp"]])[0])
        self.assertEqual(len(list(sed.keys())), len(self._keys))
        for key, vl in self._keys:
            self.assertTrue(key in sed.keys())
            if key in val:
                self.assertEqual(sed[key], val[key])
            elif key == 'ComponentPreselection':
                self.assertEqual(set(json.loads(sed[key])),
                                 set(json.loads(res)))
            elif key == 'DataSourcePreselection':
                self.assertEqual(set(json.loads(sed[key])),
                                 set(json.loads(resd)))
            elif key == 'PreselectingDataSources':
                self.assertEqual(set(json.loads(sed[key])),
                                 set(poolchannels))
            else:
                self.assertEqual(sed[key], vl)

    # test
    # \brief It tests default settings
    def test_preselectComponents_2wds_nods(self):
        fun = sys._getframe().f_code.co_name
        print("Run: %s.%s() " % (self.__class__.__name__, fun))
        val = {"ConfigDevice": self._cf.dp.name(),
               "WriterDevice": self._wr.dp.name(),
               "Door": 'doortestp09/testts/t1r228',
               "MntGrp": 'nxsmntgrp'}
        simps2 = TestServerSetUp.TestServerSetUp(
            "ttestp09/testts/t2r228", "S2")
        try:
            simps2.setUp()

            # db = tango.Database()
            self._ms.dps[list(self._ms.ms.keys())[0]].Init()
            rs = self.openRecSelector()
            rs.configDevice = val["ConfigDevice"]
            rs.door = val["Door"]
            rs.mntGrp = val["MntGrp"]
            rs.writerDevice = val["WriterDevice"]

            self._ms.dps[list(self._ms.ms.keys())[0]].Init()

            # channelerrors = []
            poolchannels = []
            componentgroup = {
                "smycp": False, "smycp2": None, "smycp3": True,
                "s2mycp": False, "s2mycp2": None, "s2mycp3": True}
            datasourcegroup = {
                "scalar_uchar": True, "scalar_string": None,
                "scalar_ulong": False,
                "scalar2_uchar": True, "scalar2_string": None,
                "scalar2_ulong": False,
            }

            cps = dict(self.smycps)
            cps.update(self.smycps2)
            dss = dict(self.smydss)
#            dss.update(self.smydss2)

            self._cf.dp.SetCommandVariable(["CPDICT", json.dumps(cps)])
            self._cf.dp.SetCommandVariable(["DSDICT", json.dumps(dss)])

            cnf = json.loads(rs.profileConfiguration)
            cnf["Timer"] = '[]'
            cnf["PreselectingDataSources"] = json.dumps(poolchannels)
            cnf["ComponentPreselection"] = json.dumps(componentgroup)
            cnf["DataSourcePreselection"] = json.dumps(datasourcegroup)
            rs.profileConfiguration = json.dumps(cnf)
            rs.preselectComponents()
            res = self.value(rs, "ComponentPreselection")
            resd = self.value(rs, "DataSourcePreselection")

            self.myAssertDict(json.loads(res), {
                "smycp": False, "smycp2": True, "smycp3": True,
                "s2mycp": False, "s2mycp2": None, "s2mycp3": None})
            self.myAssertDict(json.loads(resd), {
                "scalar_uchar": True, "scalar_string": True,
                "scalar_ulong": False,
                "scalar2_uchar": None, "scalar2_string": None,
                "scalar2_ulong": False,
            })
            self.assertEqual(len(rs.descriptionErrors), 4)

            # res2 = json.loads(self._cf.dp.GetCommandVariable("VARS"))
            self.assertTrue(val["MntGrp"] in self._cf.dp.availableSelections())
            sed = json.loads(self._cf.dp.selections([val["MntGrp"]])[0])
            self.assertEqual(len(list(sed.keys())), len(self._keys))
            for key, vl in self._keys:
                self.assertTrue(key in sed.keys())
                if key in val:
                    self.assertEqual(sed[key], val[key])
                elif key == 'ComponentPreselection':
                    self.assertEqual(set(json.loads(sed[key])),
                                     set(json.loads(res)))
                elif key == 'DataSourcePreselection':
                    self.assertEqual(set(json.loads(sed[key])),
                                     set(json.loads(resd)))
                elif key == 'PreselectingDataSources':
                    self.assertEqual(set(json.loads(sed[key])),
                                     set(poolchannels))
                else:
                    self.assertEqual(sed[key], vl)
        finally:
            simps2.tearDown()

    # test
    # \brief It tests default settings
    def test_preselectComponents_2wds_nodspool(self):
        fun = sys._getframe().f_code.co_name
        print("Run: %s.%s() " % (self.__class__.__name__, fun))
        val = {"ConfigDevice": self._cf.dp.name(),
               "WriterDevice": self._wr.dp.name(),
               "Door": 'doortestp09/testts/t1r228',
               "MntGrp": 'nxsmntgrp'}
        simps2 = TestServerSetUp.TestServerSetUp(
            "ttestp09/testts/t2r228", "S2")
        try:
            simps2.setUp()
            # db = tango.Database()
            self._ms.dps[list(self._ms.ms.keys())[0]].Init()
            rs = self.openRecSelector()
            rs.configDevice = val["ConfigDevice"]
            rs.door = val["Door"]
            rs.mntGrp = val["MntGrp"]
            rs.writerDevice = val["WriterDevice"]

            self._ms.dps[list(self._ms.ms.keys())[0]].Init()

            poolchannels = ["scalar2_long", "spectrum2_short",
                            "scalar2_uchar", "scalar2_string"]
            componentgroup = {
                "smycp": None, "smycp2": False, "smycp3": True,
                "s2mycp": None, "s2mycp2": False, "s2mycp3": True}
            datasourcegroup = {
                "scalar_uchar": True, "scalar_string": None,
                "scalar_ulong": False,
                "scalar2_uchar": True, "scalar2_string": None,
                "scalar2_ulong": False,
            }

            cps = dict(self.smycps)
            cps.update(self.smycps2)
            dss = dict(self.smydss)
#            dss.update(self.smydss2)

            self._cf.dp.SetCommandVariable(["CPDICT", json.dumps(cps)])
            self._cf.dp.SetCommandVariable(["DSDICT", json.dumps(dss)])

            cnf = json.loads(rs.profileConfiguration)
            cnf["PreselectingDataSources"] = json.dumps(poolchannels)
            cnf["Timer"] = '[]'
            cnf["ComponentPreselection"] = json.dumps(componentgroup)
            cnf["DataSourcePreselection"] = json.dumps(datasourcegroup)
            rs.profileConfiguration = json.dumps(cnf)
            rs.preselectComponents()
            res = self.value(rs, "ComponentPreselection")
            resd = self.value(rs, "DataSourcePreselection")

            self.myAssertDict(json.loads(res), {
                "smycp": True, "smycp2": False, "smycp3": True,
                "s2mycp": None, "s2mycp2": False, "s2mycp3": None})
            self.myAssertDict(json.loads(resd), {
                "scalar_uchar": True, "scalar_string": True,
                "scalar_ulong": False,
                "scalar2_uchar": None, "scalar2_string": None,
                "scalar2_ulong": False
            })
            self.assertEqual(len(rs.descriptionErrors), 4)

            # res2 = json.loads(self._cf.dp.GetCommandVariable("VARS"))
            self.assertTrue(val["MntGrp"] in self._cf.dp.availableSelections())
            sed = json.loads(self._cf.dp.selections([val["MntGrp"]])[0])
            self.assertEqual(len(list(sed.keys())), len(self._keys))
            for key, vl in self._keys:
                self.assertTrue(key in sed.keys())
                if key in val:
                    self.assertEqual(sed[key], val[key])
                elif key == 'ComponentPreselection':
                    self.assertEqual(set(json.loads(sed[key])),
                                     set(json.loads(res)))
                elif key == 'DataSourcePreselection':
                    self.assertEqual(set(json.loads(sed[key])),
                                     set(json.loads(resd)))
                elif key == 'PreselectingDataSources':
                    self.assertEqual(set(json.loads(sed[key])),
                                     set(poolchannels))
                else:
                    self.assertEqual(sed[key], vl)
        finally:
            simps2.tearDown()

    # test
    # \brief It tests default settings
    def test_preselectComponents_2wds_notangods(self):
        fun = sys._getframe().f_code.co_name
        print("Run: %s.%s() " % (self.__class__.__name__, fun))
        val = {"ConfigDevice": self._cf.dp.name(),
               "WriterDevice": self._wr.dp.name(),
               "Door": 'doortestp09/testts/t1r228',
               "MntGrp": 'nxsmntgrp'}
        simps2 = TestServerSetUp.TestServerSetUp(
            "ttestp09/testts/t2r228", "S2")
        try:
            simps2.setUp()

            # db = tango.Database()
            self._ms.dps[list(self._ms.ms.keys())[0]].Init()
            rs = self.openRecSelector()
            rs.configDevice = val["ConfigDevice"]
            rs.door = val["Door"]
            rs.mntGrp = val["MntGrp"]
            rs.writerDevice = val["WriterDevice"]

            self._ms.dps[list(self._ms.ms.keys())[0]].Init()

            poolchannels = ["scalar2_long", "spectrum2_short"]
            componentgroup = {
                "smycp": False, "smycp2": None, "smycp3": True,
                "smycpnt1": None,
                "s2mycp": False, "s2mycp2": None, "s2mycp3": True}
            datasourcegroup = {
                "scalar_uchar": True, "scalar_string": None,
                "scalar_ulong": False,
                "ann3": None,
                "scalar2_uchar": True, "scalar2_string": None,
                "scalar2_ulong": False,
            }

            cps = dict(self.smycps)
            cps.update(self.smycps2)
            dss = dict(self.smydss)
            dss.update(self.smydss2)
            dss.update(self.mydss)

            self._cf.dp.SetCommandVariable(["CPDICT", json.dumps(cps)])
            self._cf.dp.SetCommandVariable(["DSDICT", json.dumps(dss)])

            cnf = json.loads(rs.profileConfiguration)
            cnf["PreselectingDataSources"] = json.dumps(poolchannels)
            cnf["Timer"] = '[]'
            cnf["ComponentPreselection"] = json.dumps(componentgroup)
            cnf["DataSourcePreselection"] = json.dumps(datasourcegroup)
            rs.profileConfiguration = json.dumps(cnf)
            rs.preselectComponents()
            res = self.value(rs, "ComponentPreselection")
            resd = self.value(rs, "DataSourcePreselection")

            self.myAssertDict(json.loads(res), {
                "smycp": False, "smycp2": True, "smycp3": True,
                "s2mycp": False, "s2mycp2": True, "s2mycp3": True,
                "smycpnt1": True})
            self.myAssertDict(json.loads(resd), {
                "scalar_uchar": True, "scalar_string": True,
                "scalar_ulong": False,
                "scalar2_uchar": True, "scalar2_string": True,
                "scalar2_ulong": False,
                "ann3": True,
            })
            self.assertTrue(not rs.descriptionErrors)

    #        # print self._cf.dp.GetCommandVariable("COMMANDS")
            # res2 = json.loads(self._cf.dp.GetCommandVariable("VARS"))
            self.assertTrue(val["MntGrp"] in self._cf.dp.availableSelections())
            sed = json.loads(self._cf.dp.selections([val["MntGrp"]])[0])
            self.assertEqual(len(list(sed.keys())), len(self._keys))
            for key, vl in self._keys:
                self.assertTrue(key in sed.keys())
                if key in val:
                    self.assertEqual(sed[key], val[key])
                elif key == 'ComponentPreselection':
                    self.assertEqual(set(json.loads(sed[key])),
                                     set(json.loads(res)))
                elif key == 'DataSourcePreselection':
                    self.assertEqual(set(json.loads(sed[key])),
                                     set(json.loads(resd)))
                elif key == 'PreselectingDataSources':
                    self.assertEqual(set(json.loads(sed[key])),
                                     set(poolchannels))
                else:
                    self.assertEqual(sed[key], vl)
        finally:
            simps2.tearDown()

    # test
    # \brief It tests default settings
    def test_preselectComponents_2wds_notangodsnopool(self):
        fun = sys._getframe().f_code.co_name
        print("Run: %s.%s() " % (self.__class__.__name__, fun))
        val = {"ConfigDevice": self._cf.dp.name(),
               "WriterDevice": self._wr.dp.name(),
               "Door": 'doortestp09/testts/t1r228',
               "MntGrp": 'nxsmntgrp'}
        simps2 = TestServerSetUp.TestServerSetUp(
            "ttestp09/testts/t2r228", "S2")
        try:
            simps2.setUp()

            # db = tango.Database()
            self._ms.dps[list(self._ms.ms.keys())[0]].Init()
            rs = self.openRecSelector()
            rs.configDevice = val["ConfigDevice"]
            rs.door = val["Door"]
            rs.mntGrp = val["MntGrp"]
            rs.writerDevice = val["WriterDevice"]

            self._ms.dps[list(self._ms.ms.keys())[0]].Init()

            poolchannels = ["scalar2_long", "spectrum2_short", "client_long",
                            "scalar2_uchar", "scalar2_string", "ann3"]
            componentgroup = {"smycp": None, "smycp2": True,
                              "smycp3": None, "smycpnt1": None,
                              "s2mycp": None, "s2mycp2": True,
                              "s2mycp3": False}
            datasourcegroup = {
                "scalar_uchar": True, "scalar_string": None,
                "scalar_ulong": False,
                "ann3": None,
                "scalar2_uchar": True, "scalar2_string": None,
                "scalar2_ulong": False,
            }

            cps = dict(self.smycps)
            cps.update(self.smycps2)
            dss = dict(self.smydss)
            dss.update(self.smydss2)
            dss.update(self.mydss)
            self._cf.dp.SetCommandVariable(["CPDICT", json.dumps(cps)])
            self._cf.dp.SetCommandVariable(["DSDICT", json.dumps(dss)])

            cnf = json.loads(rs.profileConfiguration)
            cnf["Timer"] = '[]'
            cnf["PreselectingDataSources"] = json.dumps(poolchannels)
            cnf["ComponentPreselection"] = json.dumps(componentgroup)
            cnf["DataSourcePreselection"] = json.dumps(datasourcegroup)
            rs.profileConfiguration = json.dumps(cnf)
            rs.preselectComponents()
            res = self.value(rs, "ComponentPreselection")
            resd = self.value(rs, "DataSourcePreselection")

            self.myAssertDict(json.loads(res), {
                "smycp": True, "smycp2": True, "smycp3": True,
                "s2mycp": True, "s2mycp2": True, "s2mycp3": False,
                "smycpnt1": None})
            self.myAssertDict(json.loads(resd), {
                "scalar_uchar": True, "scalar_string": True,
                "scalar_ulong": False,
                "scalar2_uchar": True, "scalar2_string": True,
                "scalar2_ulong": False,
                "ann3": None,
            })
            self.assertEqual(len(rs.descriptionErrors), 2)

    #        # print self._cf.dp.GetCommandVariable("COMMANDS")
            # res2 = json.loads(self._cf.dp.GetCommandVariable("VARS"))
            self.assertTrue(val["MntGrp"] in self._cf.dp.availableSelections())
            sed = json.loads(self._cf.dp.selections([val["MntGrp"]])[0])
            self.assertEqual(len(list(sed.keys())), len(self._keys))
            for key, vl in self._keys:
                self.assertTrue(key in sed.keys())
                if key in val:
                    self.assertEqual(sed[key], val[key])
                elif key == 'ComponentPreselection':
                    self.assertEqual(set(json.loads(sed[key])),
                                     set(json.loads(res)))
                elif key == 'DataSourcePreselection':
                    self.assertEqual(set(json.loads(sed[key])),
                                     set(json.loads(resd)))
                elif key == 'PreselectingDataSources':
                    self.assertEqual(set(json.loads(sed[key])),
                                     set(poolchannels))
                else:
                    self.assertEqual(sed[key], vl)
        finally:
            simps2.tearDown()

    def test_preselectComponents_2wds_notangodsnopool_false(self):
        fun = sys._getframe().f_code.co_name
        print("Run: %s.%s() " % (self.__class__.__name__, fun))
        val = {"ConfigDevice": self._cf.dp.name(),
               "WriterDevice": self._wr.dp.name(),
               "Door": 'doortestp09/testts/t1r228',
               "MntGrp": 'nxsmntgrp'}
        simps2 = TestServerSetUp.TestServerSetUp(
            "ttestp09/testts/t2r228", "S2")
        try:
            simps2.setUp()

            # db = tango.Database()
            self._ms.dps[list(self._ms.ms.keys())[0]].Init()
            rs = self.openRecSelector()
            rs.configDevice = val["ConfigDevice"]
            rs.door = val["Door"]
            rs.mntGrp = val["MntGrp"]
            rs.writerDevice = val["WriterDevice"]

            self._ms.dps[list(self._ms.ms.keys())[0]].Init()

            poolchannels = ["scalar2_long", "spectrum2_short", "client_long",
                            "scalar2_uchar", "scalar2_string", "ann3"]
            componentgroup = {"smycp": None, "smycp2": True,
                              "smycp3": None, "smycpnt1": False,
                              "s2mycp": None, "s2mycp2": True,
                              "s2mycp3": False}
            datasourcegroup = {
                "scalar_uchar": True, "scalar_string": None,
                "scalar_ulong": False,
                "ann3": False,
                "scalar2_uchar": True, "scalar2_string": None,
                "scalar2_ulong": False,
            }

            cps = dict(self.smycps)
            cps.update(self.smycps2)
            dss = dict(self.smydss)
            dss.update(self.smydss2)
            dss.update(self.mydss)
            self._cf.dp.SetCommandVariable(["CPDICT", json.dumps(cps)])
            self._cf.dp.SetCommandVariable(["DSDICT", json.dumps(dss)])

            cnf = json.loads(rs.profileConfiguration)
            cnf["Timer"] = '[]'
            cnf["PreselectingDataSources"] = json.dumps(poolchannels)
            cnf["ComponentPreselection"] = json.dumps(componentgroup)
            cnf["DataSourcePreselection"] = json.dumps(datasourcegroup)
            rs.profileConfiguration = json.dumps(cnf)
            rs.preselectComponents()
            res = self.value(rs, "ComponentPreselection")
            resd = self.value(rs, "DataSourcePreselection")

            self.myAssertDict(json.loads(res), {
                "smycp": True, "smycp2": True, "smycp3": True,
                "s2mycp": True, "s2mycp2": True, "s2mycp3": False,
                "smycpnt1": False})
            self.myAssertDict(json.loads(resd), {
                "scalar_uchar": True, "scalar_string": True,
                "scalar_ulong": False,
                "scalar2_uchar": True, "scalar2_string": True,
                "scalar2_ulong": False,
                "ann3": False,
            })
            self.assertEqual(len(rs.descriptionErrors or []), 0)

    #        # print self._cf.dp.GetCommandVariable("COMMANDS")
            # res2 = json.loads(self._cf.dp.GetCommandVariable("VARS"))
            self.assertTrue(val["MntGrp"] in self._cf.dp.availableSelections())
            sed = json.loads(self._cf.dp.selections([val["MntGrp"]])[0])
            self.assertEqual(len(list(sed.keys())), len(self._keys))
            for key, vl in self._keys:
                self.assertTrue(key in sed.keys())
                if key in val:
                    self.assertEqual(sed[key], val[key])
                elif key == 'ComponentPreselection':
                    self.assertEqual(set(json.loads(sed[key])),
                                     set(json.loads(res)))
                elif key == 'DataSourcePreselection':
                    self.assertEqual(set(json.loads(sed[key])),
                                     set(json.loads(resd)))
                elif key == 'PreselectingDataSources':
                    self.assertEqual(set(json.loads(sed[key])),
                                     set(poolchannels))
                else:
                    self.assertEqual(sed[key], vl)
        finally:
            simps2.tearDown()

    # test
    # \brief It tests default settings
    def test_preselectComponents_2wds_notangodsnopool2(self):
        fun = sys._getframe().f_code.co_name
        print("Run: %s.%s() " % (self.__class__.__name__, fun))
        val = {"ConfigDevice": self._cf.dp.name(),
               "WriterDevice": self._wr.dp.name(),
               "Door": 'doortestp09/testts/t1r228',
               "MntGrp": 'nxsmntgrp'}
        simps2 = TestServerSetUp.TestServerSetUp(
            "ttestp09/testts/t2r228", "S2")
        try:
            simps2.setUp()

            # db = tango.Database()
            self._ms.dps[list(self._ms.ms.keys())[0]].Init()
            rs = self.openRecSelector()
            rs.configDevice = val["ConfigDevice"]
            rs.door = val["Door"]
            rs.mntGrp = val["MntGrp"]
            rs.writerDevice = val["WriterDevice"]

            self._ms.dps[list(self._ms.ms.keys())[0]].Init()

            poolchannels = ["scalar2_long", "spectrum2_short", "client_long",
                            "scalar2_uchar", "scalar2_string", "ann3"]
            componentgroup = {"smycp": False, "smycp2": True,
                              "smycp3": True, "smycpnt1": None,
                              "s2mycp": True, "s2mycp2": True,
                              "s2mycp3": False}
            datasourcegroup = {
                "scalar_uchar": True, "scalar_string": None,
                "scalar_ulong": False,
                "ann3": None,
                "scalar2_uchar": True, "scalar2_string": None,
                "scalar2_ulong": False,
            }

            cps = dict(self.smycps)
            cps.update(self.smycps2)
            dss = dict(self.smydss)
            dss.update(self.smydss2)
            dss.update(self.mydss)

            self._cf.dp.SetCommandVariable(["CPDICT", json.dumps(cps)])
            self._cf.dp.SetCommandVariable(["DSDICT", json.dumps(dss)])

            cnf = json.loads(rs.profileConfiguration)
            cnf["PreselectingDataSources"] = json.dumps(poolchannels)
            cnf["Timer"] = '[]'
            cnf["ComponentPreselection"] = json.dumps(componentgroup)
            cnf["DataSourcePreselection"] = json.dumps(datasourcegroup)
            rs.profileConfiguration = json.dumps(cnf)
            rs.preselectComponents()
            res = self.value(rs, "ComponentPreselection")
            resd = self.value(rs, "DataSourcePreselection")

            self.myAssertDict(json.loads(res), {
                "smycp": False, "smycp2": True, "smycp3": True,
                "s2mycp": True, "s2mycp2": True, "s2mycp3": False,
                "smycpnt1": None})
            self.myAssertDict(json.loads(resd), {
                "scalar_uchar": True, "scalar_string": True,
                "scalar_ulong": False,
                "scalar2_uchar": True, "scalar2_string": True,
                "scalar2_ulong": False,
                "ann3": None,
            })
            self.assertEqual(len(rs.descriptionErrors), 2)

    #        print self._cf.dp.GetCommandVariable("COMMANDS")
            # res2 = json.loads(self._cf.dp.GetCommandVariable("VARS"))
            self.assertTrue(val["MntGrp"] in self._cf.dp.availableSelections())
            sed = json.loads(self._cf.dp.selections([val["MntGrp"]])[0])
            self.assertEqual(len(list(sed.keys())), len(self._keys))
            for key, vl in self._keys:
                self.assertTrue(key in sed.keys())
                if key in val:
                    self.assertEqual(sed[key], val[key])
                elif key == 'ComponentPreselection':
                    self.assertEqual(set(json.loads(sed[key])),
                                     set(json.loads(res)))
                elif key == 'DataSourcePreselection':
                    self.assertEqual(set(json.loads(sed[key])),
                                     set(json.loads(resd)))
                elif key == 'PreselectingDataSources':
                    self.assertEqual(set(json.loads(sed[key])),
                                     set(poolchannels))
                else:
                    self.assertEqual(sed[key], vl)
        finally:
            simps2.tearDown()

    # test
    # \brief It tests default settings
    def test_preselectComponents_2wds_notangodsnopool2_false(self):
        fun = sys._getframe().f_code.co_name
        print("Run: %s.%s() " % (self.__class__.__name__, fun))
        val = {"ConfigDevice": self._cf.dp.name(),
               "WriterDevice": self._wr.dp.name(),
               "Door": 'doortestp09/testts/t1r228',
               "MntGrp": 'nxsmntgrp'}
        simps2 = TestServerSetUp.TestServerSetUp(
            "ttestp09/testts/t2r228", "S2")
        try:
            simps2.setUp()

            # db = tango.Database()
            self._ms.dps[list(self._ms.ms.keys())[0]].Init()
            rs = self.openRecSelector()
            rs.configDevice = val["ConfigDevice"]
            rs.door = val["Door"]
            rs.mntGrp = val["MntGrp"]
            rs.writerDevice = val["WriterDevice"]

            self._ms.dps[list(self._ms.ms.keys())[0]].Init()

            poolchannels = ["scalar2_long", "spectrum2_short", "client_long",
                            "scalar2_uchar", "scalar2_string", "ann3"]
            componentgroup = {"smycp": False, "smycp2": True,
                              "smycp3": True, "smycpnt1": False,
                              "s2mycp": True, "s2mycp2": True,
                              "s2mycp3": False}
            datasourcegroup = {
                "scalar_uchar": True, "scalar_string": None,
                "scalar_ulong": False,
                "ann3": False,
                "scalar2_uchar": True, "scalar2_string": None,
                "scalar2_ulong": False,
            }

            cps = dict(self.smycps)
            cps.update(self.smycps2)
            dss = dict(self.smydss)
            dss.update(self.smydss2)
            dss.update(self.mydss)

            self._cf.dp.SetCommandVariable(["CPDICT", json.dumps(cps)])
            self._cf.dp.SetCommandVariable(["DSDICT", json.dumps(dss)])

            cnf = json.loads(rs.profileConfiguration)
            cnf["Timer"] = '[]'
            cnf["PreselectingDataSources"] = json.dumps(poolchannels)
            cnf["ComponentPreselection"] = json.dumps(componentgroup)
            cnf["DataSourcePreselection"] = json.dumps(datasourcegroup)
            rs.profileConfiguration = json.dumps(cnf)
            rs.preselectComponents()
            res = self.value(rs, "ComponentPreselection")
            resd = self.value(rs, "DataSourcePreselection")

            self.myAssertDict(json.loads(res), {
                "smycp": False, "smycp2": True, "smycp3": True,
                "s2mycp": True, "s2mycp2": True, "s2mycp3": False,
                "smycpnt1": False})
            self.myAssertDict(json.loads(resd), {
                "scalar_uchar": True, "scalar_string": True,
                "scalar_ulong": False,
                "scalar2_uchar": True, "scalar2_string": True,
                "scalar2_ulong": False,
                "ann3": False,
            })
            self.assertEqual(len(rs.descriptionErrors or []), 0)

    #        print self._cf.dp.GetCommandVariable("COMMANDS")
            # res2 = json.loads(self._cf.dp.GetCommandVariable("VARS"))
            self.assertTrue(val["MntGrp"] in self._cf.dp.availableSelections())
            sed = json.loads(self._cf.dp.selections([val["MntGrp"]])[0])
            self.assertEqual(len(list(sed.keys())), len(self._keys))
            for key, vl in self._keys:
                self.assertTrue(key in sed.keys())
                if key in val:
                    self.assertEqual(sed[key], val[key])
                elif key == 'ComponentPreselection':
                    self.assertEqual(set(json.loads(sed[key])),
                                     set(json.loads(res)))
                elif key == 'DataSourcePreselection':
                    self.assertEqual(set(json.loads(sed[key])),
                                     set(json.loads(resd)))
                elif key == 'PreselectingDataSources':
                    self.assertEqual(set(json.loads(sed[key])),
                                     set(poolchannels))
                else:
                    self.assertEqual(sed[key], vl)
        finally:
            simps2.tearDown()

    # test
    # \brief It tests default settings
    def test_preselectComponents_2wds_notangods2(self):
        fun = sys._getframe().f_code.co_name
        print("Run: %s.%s() " % (self.__class__.__name__, fun))
        val = {"ConfigDevice": self._cf.dp.name(),
               "WriterDevice": self._wr.dp.name(),
               "Door": 'doortestp09/testts/t1r228',
               "MntGrp": 'nxsmntgrp'}
        simps2 = TestServerSetUp.TestServerSetUp(
            "ttestp09/testts/t2r228", "S2")

        arr = [
            {"name": "client_long",
             "full_name": "ttestp09/testts/t1r228/Value"},
            {"name": "client_short",
             "full_name": "ttestp09/testts/t1r228/Value"},
        ]

        try:
            simps2.setUp()

            db = tango.Database()
            db.put_device_property(list(self._ms.ms.keys())[0],
                                   {'PoolNames': self._pool.dp.name()})
            self._ms.dps[list(self._ms.ms.keys())[0]].Init()
            rs = self.openRecSelector()
            rs.configDevice = val["ConfigDevice"]
            rs.door = val["Door"]
            rs.mntGrp = val["MntGrp"]
            rs.writerDevice = val["WriterDevice"]

            self._ms.dps[list(self._ms.ms.keys())[0]].Init()

            # channelerrors = []
            poolchannels = []
            componentgroup = {"smycp": False, "smycp2": None,
                              "smycp3": True, "smycpnt1": None,
                              "s2mycp": True, "s2mycp2": False,
                              "s2mycp3": True}
            datasourcegroup = {
                "scalar_uchar": True, "scalar_string": None,
                "scalar_ulong": False,
                "ann3": None,
                "scalar2_uchar": True, "scalar2_string": None,
                "scalar2_ulong": False,
            }

            cps = dict(self.smycps)
            cps.update(self.smycps2)
            dss = dict(self.smydss)
            dss.update(self.smydss2)
            dss.update(self.mydss)

            self._cf.dp.SetCommandVariable(["CPDICT", json.dumps(cps)])
            self._cf.dp.SetCommandVariable(["DSDICT", json.dumps(dss)])

            pool = self._pool.dp
            pool.AcqChannelList = [json.dumps(a) for a in arr]

            cnf = json.loads(rs.profileConfiguration)
            cnf["PreselectingDataSources"] = json.dumps(poolchannels)
            cnf["ComponentPreselection"] = json.dumps(componentgroup)
            cnf["DataSourcePreselection"] = json.dumps(datasourcegroup)
            cnf["Timer"] = '[]'
            rs.profileConfiguration = json.dumps(cnf)
            rs.preselectComponents()
            res = self.value(rs, "ComponentPreselection")
            resd = self.value(rs, "DataSourcePreselection")
            self.myAssertDict(json.loads(res), {
                "smycp": False, "smycp2": True, "smycp3": True,
                "s2mycp": True, "s2mycp2": False, "s2mycp3": True,
                "smycpnt1": True})
            self.myAssertDict(json.loads(resd), {
                "scalar_uchar": True, "scalar_string": True,
                "scalar_ulong": False,
                "scalar2_uchar": True, "scalar2_string": True,
                "scalar2_ulong": False,
                "ann3": True,
            })

            self.assertTrue(not rs.descriptionErrors)

            # res2 = json.loads(self._cf.dp.GetCommandVariable("VARS"))
            self.assertTrue(val["MntGrp"] in self._cf.dp.availableSelections())
            sed = json.loads(self._cf.dp.selections([val["MntGrp"]])[0])
            self.assertEqual(len(list(sed.keys())), len(self._keys))
            for key, vl in self._keys:
                self.assertTrue(key in sed.keys())
                if key in val:
                    self.assertEqual(sed[key], val[key])
                elif key == 'ComponentPreselection':
                    self.assertEqual(set(json.loads(sed[key])),
                                     set(json.loads(res)))
                elif key == 'DataSourcePreselection':
                    self.assertEqual(set(json.loads(sed[key])),
                                     set(json.loads(resd)))
                elif key == 'PreselectingDataSources':
                    self.assertEqual(set(json.loads(sed[key])),
                                     set(poolchannels))
                else:
                    self.assertEqual(sed[key], vl)
        finally:
            simps2.tearDown()

    # test
    # \brief It tests default settings
    def test_preselectComponents_2wds_notangods2_false(self):
        fun = sys._getframe().f_code.co_name
        print("Run: %s.%s() " % (self.__class__.__name__, fun))
        val = {"ConfigDevice": self._cf.dp.name(),
               "WriterDevice": self._wr.dp.name(),
               "Door": 'doortestp09/testts/t1r228',
               "MntGrp": 'nxsmntgrp'}
        simps2 = TestServerSetUp.TestServerSetUp(
            "ttestp09/testts/t2r228", "S2")

        arr = [
            {"name": "client_long",
             "full_name": "ttestp09/testts/t1r228/Value"},
            {"name": "client_short",
             "full_name": "ttestp09/testts/t1r228/Value"},
        ]

        try:
            simps2.setUp()

            db = tango.Database()
            db.put_device_property(list(self._ms.ms.keys())[0],
                                   {'PoolNames': self._pool.dp.name()})
            self._ms.dps[list(self._ms.ms.keys())[0]].Init()
            rs = self.openRecSelector()
            rs.configDevice = val["ConfigDevice"]
            rs.door = val["Door"]
            rs.mntGrp = val["MntGrp"]
            rs.writerDevice = val["WriterDevice"]

            self._ms.dps[list(self._ms.ms.keys())[0]].Init()

            # channelerrors = []
            poolchannels = []
            componentgroup = {"smycp": False, "smycp2": None,
                              "smycp3": True, "smycpnt1": False,
                              "s2mycp": True, "s2mycp2": False,
                              "s2mycp3": True}
            datasourcegroup = {
                "scalar_uchar": True, "scalar_string": None,
                "scalar_ulong": False,
                "ann3": False,
                "scalar2_uchar": True, "scalar2_string": None,
                "scalar2_ulong": False,
            }

            cps = dict(self.smycps)
            cps.update(self.smycps2)
            dss = dict(self.smydss)
            dss.update(self.smydss2)
            dss.update(self.mydss)

            self._cf.dp.SetCommandVariable(["CPDICT", json.dumps(cps)])
            self._cf.dp.SetCommandVariable(["DSDICT", json.dumps(dss)])

            pool = self._pool.dp
            pool.AcqChannelList = [json.dumps(a) for a in arr]

            cnf = json.loads(rs.profileConfiguration)
            cnf["Timer"] = '[]'
            cnf["PreselectingDataSources"] = json.dumps(poolchannels)
            cnf["ComponentPreselection"] = json.dumps(componentgroup)
            cnf["DataSourcePreselection"] = json.dumps(datasourcegroup)
            rs.profileConfiguration = json.dumps(cnf)
            rs.preselectComponents()
            res = self.value(rs, "ComponentPreselection")
            resd = self.value(rs, "DataSourcePreselection")
            self.myAssertDict(json.loads(res), {
                "smycp": False, "smycp2": True, "smycp3": True,
                "s2mycp": True, "s2mycp2": False, "s2mycp3": True,
                "smycpnt1": False})
            self.myAssertDict(json.loads(resd), {
                "scalar_uchar": True, "scalar_string": True,
                "scalar_ulong": False,
                "scalar2_uchar": True, "scalar2_string": True,
                "scalar2_ulong": False,
                "ann3": False,
            })

            self.assertTrue(not rs.descriptionErrors)

            # res2 = json.loads(self._cf.dp.GetCommandVariable("VARS"))
            self.assertTrue(val["MntGrp"] in self._cf.dp.availableSelections())
            sed = json.loads(self._cf.dp.selections([val["MntGrp"]])[0])
            self.assertEqual(len(list(sed.keys())), len(self._keys))
            for key, vl in self._keys:
                self.assertTrue(key in sed.keys())
                if key in val:
                    self.assertEqual(sed[key], val[key])
                elif key == 'ComponentPreselection':
                    self.assertEqual(set(json.loads(sed[key])),
                                     set(json.loads(res)))
                elif key == 'DataSourcePreselection':
                    self.assertEqual(set(json.loads(sed[key])),
                                     set(json.loads(resd)))
                elif key == 'PreselectingDataSources':
                    self.assertEqual(set(json.loads(sed[key])),
                                     set(poolchannels))
                else:
                    self.assertEqual(sed[key], vl)
        finally:
            simps2.tearDown()

    # test
    # \brief It tests default settings
    def test_preselectComponents_2wds_notangods2_bl(self):
        fun = sys._getframe().f_code.co_name
        print("Run: %s.%s() " % (self.__class__.__name__, fun))
        val = {"ConfigDevice": self._cf.dp.name(),
               "WriterDevice": self._wr.dp.name(),
               "Door": 'doortestp09/testts/t1r228',
               "MntGrp": 'nxsmntgrp'}
        simps2 = TestServerSetUp.TestServerSetUp(
            "ttestp09/testts/t2r228", "S2")

        arr = [
            {"name": "client_long",
             "full_name": "ttestp09/testts/t1r228/Value"},
            {"name": "client_short",
             "full_name": "ttestp09/testts/t1r228/Value"},
        ]

        try:
            simps2.setUp()

            db = tango.Database()
            db.put_device_property(list(self._ms.ms.keys())[0],
                                   {'PoolNames': self._pool.dp.name()})
            self._ms.dps[list(self._ms.ms.keys())[0]].Init()
            rs = self.openRecSelector()
            self.setProp(rs, "poolBlacklist",
                         [self._pool.dp.name()])
            rs.configDevice = val["ConfigDevice"]
            rs.door = val["Door"]
            rs.mntGrp = val["MntGrp"]
            rs.writerDevice = val["WriterDevice"]

            self._ms.dps[list(self._ms.ms.keys())[0]].Init()

            # channelerrors = []
            poolchannels = []
            componentgroup = {"smycp": False, "smycp2": None,
                              "smycp3": True, "smycpnt1": None,
                              "s2mycp": True, "s2mycp2": False,
                              "s2mycp3": True}
            datasourcegroup = {
                "scalar_uchar": True, "scalar_string": None,
                "scalar_ulong": False,
                "ann3": None,
                "scalar2_uchar": True, "scalar2_string": None,
                "scalar2_ulong": False,
            }

            cps = dict(self.smycps)
            cps.update(self.smycps2)
            dss = dict(self.smydss)
            dss.update(self.smydss2)
            dss.update(self.mydss)

            self._cf.dp.SetCommandVariable(["CPDICT", json.dumps(cps)])
            self._cf.dp.SetCommandVariable(["DSDICT", json.dumps(dss)])

            pool = self._pool.dp
            pool.AcqChannelList = [json.dumps(a) for a in arr]

            cnf = json.loads(rs.profileConfiguration)
            cnf["Timer"] = '[]'
            cnf["PreselectingDataSources"] = json.dumps(poolchannels)
            cnf["ComponentPreselection"] = json.dumps(componentgroup)
            cnf["DataSourcePreselection"] = json.dumps(datasourcegroup)
            rs.profileConfiguration = json.dumps(cnf)
            rs.preselectComponents()
            res = self.value(rs, "ComponentPreselection")
            resd = self.value(rs, "DataSourcePreselection")

            self.myAssertDict(json.loads(res), {
                "smycp": False, "smycp2": True, "smycp3": True,
                "s2mycp": True, "s2mycp2": False, "s2mycp3": True,
                "smycpnt1": True})
            self.myAssertDict(json.loads(resd), {
                "scalar_uchar": True, "scalar_string": True,
                "scalar_ulong": False,
                "scalar2_uchar": True, "scalar2_string": True,
                "scalar2_ulong": False,
                "ann3": True,
            })
            self.assertTrue(not rs.descriptionErrors)

            # res2 = json.loads(self._cf.dp.GetCommandVariable("VARS"))
            self.assertTrue(val["MntGrp"] in self._cf.dp.availableSelections())
            sed = json.loads(self._cf.dp.selections([val["MntGrp"]])[0])
            self.assertEqual(len(list(sed.keys())), len(self._keys))
            for key, vl in self._keys:
                self.assertTrue(key in sed.keys())
                if key in val:
                    self.assertEqual(sed[key], val[key])
                elif key == 'ComponentPreselection':
                    self.assertEqual(set(json.loads(sed[key])),
                                     set(json.loads(res)))
                elif key == 'DataSourcePreselection':
                    self.assertEqual(set(json.loads(sed[key])),
                                     set(json.loads(resd)))
                elif key == 'PreselectingDataSources':
                    self.assertEqual(set(json.loads(sed[key])),
                                     set(poolchannels))
                else:
                    self.assertEqual(sed[key], vl)
        finally:
            simps2.tearDown()

    # test
    # \brief It tests default settings
    def test_preselectComponents_2wds_notangodspool_error(self):
        fun = sys._getframe().f_code.co_name
        print("Run: %s.%s() " % (self.__class__.__name__, fun))
        val = {"ConfigDevice": self._cf.dp.name(),
               "WriterDevice": self._wr.dp.name(),
               "Door": 'doortestp09/testts/t1r228',
               "MntGrp": 'nxsmntgrp'}
        simps2 = TestServerSetUp.TestServerSetUp(
            "ttestp09/testts/t2r228", "S2")

        arr = [
            {"name": "client_long",
             "full_name": "ttestp09/testts/t1r228/Value"},
            {"name": "client_short",
             "full_name": "ttestp09/testts/t1r228/Value"},
        ]

        try:
            simps2.setUp()

            db = tango.Database()
            db.put_device_property(list(self._ms.ms.keys())[0],
                                   {'PoolNames': self._pool.dp.name()})
            self._ms.dps[list(self._ms.ms.keys())[0]].Init()
            rs = self.openRecSelector()
            rs.configDevice = val["ConfigDevice"]
            rs.door = val["Door"]
            rs.mntGrp = val["MntGrp"]
            rs.writerDevice = val["WriterDevice"]

            self._ms.dps[list(self._ms.ms.keys())[0]].Init()

            # channelerrors = []
            poolchannels = ["scalar2_long", "spectrum2_short", "client_long",
                            "client_short",
                            "scalar2_uchar", "scalar2_string", "ann3"]
            componentgroup = {
                "smycp": False, "smycp2": True, "smycp3": None,
                "smycpnt1": None,
                "s2mycp": False, "s2mycp2": True, "s2mycp3": None
            }
            datasourcegroup = {
                "scalar_uchar": True, "scalar_string": None,
                "scalar_ulong": False,
                "ann3": None,
                "scalar2_uchar": True, "scalar2_string": None,
                "scalar2_ulong": False,
            }

            cps = dict(self.smycps)
            cps.update(self.smycps2)
            dss = dict(self.smydss)
            dss.update(self.smydss2)
            dss.update(self.mydss)

            self._cf.dp.SetCommandVariable(["CPDICT", json.dumps(cps)])
            self._cf.dp.SetCommandVariable(["DSDICT", json.dumps(dss)])

            pool = self._pool.dp
            pool.AcqChannelList = [json.dumps(a) for a in arr]

            cnf = json.loads(rs.profileConfiguration)
            cnf["Timer"] = '[]'
            cnf["PreselectingDataSources"] = json.dumps(poolchannels)
            cnf["ComponentPreselection"] = json.dumps(componentgroup)
            cnf["DataSourcePreselection"] = json.dumps(datasourcegroup)
            rs.profileConfiguration = json.dumps(cnf)
            rs.preselectComponents()
            res = self.value(rs, "ComponentPreselection")
            resd = self.value(rs, "DataSourcePreselection")

            self.myAssertDict(json.loads(res), {
                "smycp": False, "smycp2": True, "smycp3": True,
                "s2mycp": False, "s2mycp2": True, "s2mycp3": True,
                "smycpnt1": None})
            self.myAssertDict(json.loads(resd), {
                "scalar_uchar": True, "scalar_string": True,
                "scalar_ulong": False,
                "scalar2_uchar": True, "scalar2_string": True,
                "scalar2_ulong": False,
                "ann3": None,
            })
            self.assertEqual(len(rs.descriptionErrors), 2)

    #        print self._cf.dp.GetCommandVariable("COMMANDS")
            # res2 = json.loads(self._cf.dp.GetCommandVariable("VARS"))
            self.assertTrue(val["MntGrp"] in self._cf.dp.availableSelections())
            sed = json.loads(self._cf.dp.selections([val["MntGrp"]])[0])
            self.assertEqual(len(list(sed.keys())), len(self._keys))
            for key, vl in self._keys:
                self.assertTrue(key in sed.keys())
                if key in val:
                    self.assertEqual(sed[key], val[key])
                elif key == 'ComponentPreselection':
                    self.assertEqual(set(json.loads(sed[key])),
                                     set(json.loads(res)))
                elif key == 'DataSourcePreselection':
                    self.assertEqual(set(json.loads(sed[key])),
                                     set(json.loads(resd)))
                elif key == 'PreselectingDataSources':
                    self.assertEqual(set(json.loads(sed[key])),
                                     set(poolchannels))
                else:
                    self.assertEqual(sed[key], vl)
        finally:
            simps2.tearDown()

    # test
    # \brief It tests default settings
    def test_preselectComponents_2wds_notangodspool_error_false(self):
        fun = sys._getframe().f_code.co_name
        print("Run: %s.%s() " % (self.__class__.__name__, fun))
        val = {"ConfigDevice": self._cf.dp.name(),
               "WriterDevice": self._wr.dp.name(),
               "Door": 'doortestp09/testts/t1r228',
               "MntGrp": 'nxsmntgrp'}
        simps2 = TestServerSetUp.TestServerSetUp(
            "ttestp09/testts/t2r228", "S2")

        arr = [
            {"name": "client_long",
             "full_name": "ttestp09/testts/t1r228/Value"},
            {"name": "client_short",
             "full_name": "ttestp09/testts/t1r228/Value"},
        ]

        try:
            simps2.setUp()

            db = tango.Database()
            db.put_device_property(list(self._ms.ms.keys())[0],
                                   {'PoolNames': self._pool.dp.name()})
            self._ms.dps[list(self._ms.ms.keys())[0]].Init()
            rs = self.openRecSelector()
            rs.configDevice = val["ConfigDevice"]
            rs.door = val["Door"]
            rs.mntGrp = val["MntGrp"]
            rs.writerDevice = val["WriterDevice"]

            self._ms.dps[list(self._ms.ms.keys())[0]].Init()

            # channelerrors = []
            poolchannels = ["scalar2_long", "spectrum2_short", "client_long",
                            "client_short",
                            "scalar2_uchar", "scalar2_string", "ann3"]
            componentgroup = {
                "smycp": False, "smycp2": True, "smycp3": None,
                "smycpnt1": False,
                "s2mycp": False, "s2mycp2": True, "s2mycp3": None
            }
            datasourcegroup = {
                "scalar_uchar": True, "scalar_string": None,
                "scalar_ulong": False,
                "ann3": False,
                "scalar2_uchar": True, "scalar2_string": None,
                "scalar2_ulong": False,
            }

            cps = dict(self.smycps)
            cps.update(self.smycps2)
            dss = dict(self.smydss)
            dss.update(self.smydss2)
            dss.update(self.mydss)

            self._cf.dp.SetCommandVariable(["CPDICT", json.dumps(cps)])
            self._cf.dp.SetCommandVariable(["DSDICT", json.dumps(dss)])

            pool = self._pool.dp
            pool.AcqChannelList = [json.dumps(a) for a in arr]

            cnf = json.loads(rs.profileConfiguration)
            cnf["Timer"] = '[]'
            cnf["PreselectingDataSources"] = json.dumps(poolchannels)
            cnf["ComponentPreselection"] = json.dumps(componentgroup)
            cnf["DataSourcePreselection"] = json.dumps(datasourcegroup)
            rs.profileConfiguration = json.dumps(cnf)
            rs.preselectComponents()
            res = self.value(rs, "ComponentPreselection")
            resd = self.value(rs, "DataSourcePreselection")

            self.myAssertDict(json.loads(res), {
                "smycp": False, "smycp2": True, "smycp3": True,
                "s2mycp": False, "s2mycp2": True, "s2mycp3": True,
                "smycpnt1": False})
            self.myAssertDict(json.loads(resd), {
                "scalar_uchar": True, "scalar_string": True,
                "scalar_ulong": False,
                "scalar2_uchar": True, "scalar2_string": True,
                "scalar2_ulong": False,
                "ann3": False,
            })
            self.assertEqual(len(rs.descriptionErrors or []), 0)

    #        print self._cf.dp.GetCommandVariable("COMMANDS")
            # res2 = json.loads(self._cf.dp.GetCommandVariable("VARS"))
            self.assertTrue(val["MntGrp"] in self._cf.dp.availableSelections())
            sed = json.loads(self._cf.dp.selections([val["MntGrp"]])[0])
            self.assertEqual(len(list(sed.keys())), len(self._keys))
            for key, vl in self._keys:
                self.assertTrue(key in sed.keys())
                if key in val:
                    self.assertEqual(sed[key], val[key])
                elif key == 'ComponentPreselection':
                    self.assertEqual(set(json.loads(sed[key])),
                                     set(json.loads(res)))
                elif key == 'DataSourcePreselection':
                    self.assertEqual(set(json.loads(sed[key])),
                                     set(json.loads(resd)))
                elif key == 'PreselectingDataSources':
                    self.assertEqual(set(json.loads(sed[key])),
                                     set(poolchannels))
                else:
                    self.assertEqual(sed[key], vl)
        finally:
            simps2.tearDown()

    # test
    # \brief It tests default settings
    def test_preselectComponents_2wds_notangodspool_error_bl(self):
        fun = sys._getframe().f_code.co_name
        print("Run: %s.%s() " % (self.__class__.__name__, fun))
        val = {"ConfigDevice": self._cf.dp.name(),
               "WriterDevice": self._wr.dp.name(),
               "Door": 'doortestp09/testts/t1r228',
               "MntGrp": 'nxsmntgrp'}
        simps2 = TestServerSetUp.TestServerSetUp(
            "ttestp09/testts/t2r228", "S2")

        arr = [
            {"name": "client_long",
             "full_name": "ttestp09/testts/t1r228/Value"},
            {"name": "client_short",
             "full_name": "ttestp09/testts/t1r228/Value"},
        ]

        try:
            simps2.setUp()

            db = tango.Database()
            db.put_device_property(list(self._ms.ms.keys())[0],
                                   {'PoolNames': self._pool.dp.name()})
            self._ms.dps[list(self._ms.ms.keys())[0]].Init()
            rs = self.openRecSelector()
            self.setProp(rs, "poolBlacklist",
                         [self._pool.dp.name()])
            rs.configDevice = val["ConfigDevice"]
            rs.door = val["Door"]
            rs.mntGrp = val["MntGrp"]
            rs.writerDevice = val["WriterDevice"]

            self._ms.dps[list(self._ms.ms.keys())[0]].Init()

            # channelerrors = []
            poolchannels = ["scalar2_long", "spectrum2_short", "client_long",
                            "client_short",
                            "scalar2_uchar", "scalar2_string", "ann3"]
            componentgroup = {
                "smycp": False, "smycp2": True, "smycp3": None,
                "smycpnt1": None,
                "s2mycp": False, "s2mycp2": True, "s2mycp3": None
            }
            datasourcegroup = {
                "scalar_uchar": True, "scalar_string": None,
                "scalar_ulong": False,
                "ann3": None,
                "scalar2_uchar": True, "scalar2_string": None,
                "scalar2_ulong": False,
            }

            cps = dict(self.smycps)
            cps.update(self.smycps2)
            dss = dict(self.smydss)
            dss.update(self.smydss2)
            dss.update(self.mydss)

            self._cf.dp.SetCommandVariable(["CPDICT", json.dumps(cps)])
            self._cf.dp.SetCommandVariable(["DSDICT", json.dumps(dss)])

            pool = self._pool.dp
            pool.AcqChannelList = [json.dumps(a) for a in arr]

            cnf = json.loads(rs.profileConfiguration)
            cnf["Timer"] = '[]'
            cnf["PreselectingDataSources"] = json.dumps(poolchannels)
            cnf["ComponentPreselection"] = json.dumps(componentgroup)
            cnf["DataSourcePreselection"] = json.dumps(datasourcegroup)
            rs.profileConfiguration = json.dumps(cnf)
            rs.preselectComponents()
            res = self.value(rs, "ComponentPreselection")
            resd = self.value(rs, "DataSourcePreselection")

            self.myAssertDict(json.loads(res), {
                "smycp": False, "smycp2": True, "smycp3": True,
                "s2mycp": False, "s2mycp2": True, "s2mycp3": True,
                "smycpnt1": None})
            self.myAssertDict(json.loads(resd), {
                "scalar_uchar": True, "scalar_string": True,
                "scalar_ulong": False,
                "scalar2_uchar": True, "scalar2_string": True,
                "scalar2_ulong": False,
                "ann3": None,
            })
            self.assertEqual(len(rs.descriptionErrors), 2)

    #        print self._cf.dp.GetCommandVariable("COMMANDS")
            # res2 = json.loads(self._cf.dp.GetCommandVariable("VARS"))
            self.assertTrue(val["MntGrp"] in self._cf.dp.availableSelections())
            sed = json.loads(self._cf.dp.selections([val["MntGrp"]])[0])
            self.assertEqual(len(list(sed.keys())), len(self._keys))
            for key, vl in self._keys:
                self.assertTrue(key in sed.keys())
                if key in val:
                    self.assertEqual(sed[key], val[key])
                elif key == 'ComponentPreselection':
                    self.assertEqual(set(json.loads(sed[key])),
                                     set(json.loads(res)))
                elif key == 'DataSourcePreselection':
                    self.assertEqual(set(json.loads(sed[key])),
                                     set(json.loads(resd)))
                elif key == 'PreselectingDataSources':
                    self.assertEqual(set(json.loads(sed[key])),
                                     set(poolchannels))
                else:
                    self.assertEqual(sed[key], vl)
        finally:
            simps2.tearDown()

    # test
    # \brief It tests default settings
    def test_preselectComponents_2wds_notangodspool(self):
        fun = sys._getframe().f_code.co_name
        print("Run: %s.%s() " % (self.__class__.__name__, fun))
        val = {"ConfigDevice": self._cf.dp.name(),
               "WriterDevice": self._wr.dp.name(),
               "Door": 'doortestp09/testts/t1r228',
               "MntGrp": 'nxsmntgrp'}
        simps2 = TestServerSetUp.TestServerSetUp(
            "ttestp09/testts/t2r228", "S2")

        arr = [
            {"name": "client_short", "full_name": "ttestp09/testts/t1r228"},
        ]

        try:
            simps2.setUp()

            db = tango.Database()
            db.put_device_property(list(self._ms.ms.keys())[0],
                                   {'PoolNames': self._pool.dp.name()})
            self._ms.dps[list(self._ms.ms.keys())[0]].Init()
            rs = self.openRecSelector()
            rs.configDevice = val["ConfigDevice"]
            rs.door = val["Door"]
            rs.mntGrp = val["MntGrp"]
            rs.writerDevice = val["WriterDevice"]

            self._ms.dps[list(self._ms.ms.keys())[0]].Init()

            # channelerrors = []

            poolchannels = ["scalar2_long", "spectrum2_short", "client_short",
                            "scalar2_uchar", "scalar2_string", "ann3"]
            componentgroup = {
                "smycp": True, "smycp2": False, "smycp3": None,
                "smycpnt1": None,
                "s2mycp": False, "s2mycp2": True, "s2mycp3": None,
            }
            datasourcegroup = {
                "scalar_uchar": True, "scalar_string": None,
                "scalar_ulong": False,
                "ann3": None,
                "scalar2_uchar": True, "scalar2_string": None,
                "scalar2_ulong": False,
            }

            cps = dict(self.smycps)
            cps.update(self.smycps2)
            dss = dict(self.smydss)
            dss.update(self.smydss2)
            dss.update(self.mydss)

            self._cf.dp.SetCommandVariable(["CPDICT", json.dumps(cps)])
            self._cf.dp.SetCommandVariable(["DSDICT", json.dumps(dss)])

            pool = self._pool.dp
            pool.AcqChannelList = [json.dumps(a) for a in arr]

            self._simps.dp.ChangeValueType("ScalarShort")
            self._simps.dp.Value = 43

            cnf = json.loads(rs.profileConfiguration)
            cnf["Timer"] = '[]'
            cnf["PreselectingDataSources"] = json.dumps(poolchannels)
            cnf["ComponentPreselection"] = json.dumps(componentgroup)
            cnf["DataSourcePreselection"] = json.dumps(datasourcegroup)
            rs.profileConfiguration = json.dumps(cnf)
            rs.preselectComponents()
            res = self.value(rs, "ComponentPreselection")
            resd = self.value(rs, "DataSourcePreselection")

            self.myAssertDict(json.loads(res), {
                "smycp": True, "smycp2": False, "smycp3": True,
                "s2mycp": False, "s2mycp2": True, "s2mycp3": True,
                "smycpnt1": None})
            self.myAssertDict(json.loads(resd), {
                "scalar_uchar": True, "scalar_string": True,
                "scalar_ulong": False,
                "scalar2_uchar": True, "scalar2_string": True,
                "scalar2_ulong": False,
                "ann3": None,
            })
            self.assertEqual(len(rs.descriptionErrors), 2)

            # res2 = json.loads(self._cf.dp.GetCommandVariable("VARS"))
            self.assertTrue(val["MntGrp"] in self._cf.dp.availableSelections())
            sed = json.loads(self._cf.dp.selections([val["MntGrp"]])[0])
            self.assertEqual(len(list(sed.keys())), len(self._keys))
            for key, vl in self._keys:
                self.assertTrue(key in sed.keys())
                if key in val:
                    self.assertEqual(sed[key], val[key])
                elif key == 'ComponentPreselection':
                    self.assertEqual(set(json.loads(sed[key])),
                                     set(json.loads(res)))
                elif key == 'DataSourcePreselection':
                    self.assertEqual(set(json.loads(sed[key])),
                                     set(json.loads(resd)))
                elif key == 'PreselectingDataSources':
                    self.assertEqual(set(json.loads(sed[key])),
                                     set(poolchannels))
                else:
                    self.assertEqual(sed[key], vl)
        finally:
            simps2.tearDown()

    # test
    # \brief It tests default settings
    def test_preselectComponents_2wds_notangodspool_false(self):
        fun = sys._getframe().f_code.co_name
        print("Run: %s.%s() " % (self.__class__.__name__, fun))
        val = {"ConfigDevice": self._cf.dp.name(),
               "WriterDevice": self._wr.dp.name(),
               "Door": 'doortestp09/testts/t1r228',
               "MntGrp": 'nxsmntgrp'}
        simps2 = TestServerSetUp.TestServerSetUp(
            "ttestp09/testts/t2r228", "S2")

        arr = [
            {"name": "client_short", "full_name": "ttestp09/testts/t1r228"},
        ]

        try:
            simps2.setUp()

            db = tango.Database()
            db.put_device_property(list(self._ms.ms.keys())[0],
                                   {'PoolNames': self._pool.dp.name()})
            self._ms.dps[list(self._ms.ms.keys())[0]].Init()
            rs = self.openRecSelector()
            rs.configDevice = val["ConfigDevice"]
            rs.door = val["Door"]
            rs.mntGrp = val["MntGrp"]
            rs.writerDevice = val["WriterDevice"]

            self._ms.dps[list(self._ms.ms.keys())[0]].Init()

            # channelerrors = []

            poolchannels = ["scalar2_long", "spectrum2_short", "client_short",
                            "scalar2_uchar", "scalar2_string", "ann3"]
            componentgroup = {
                "smycp": True, "smycp2": False, "smycp3": None,
                "smycpnt1": False,
                "s2mycp": False, "s2mycp2": True, "s2mycp3": None,
            }
            datasourcegroup = {
                "scalar_uchar": True, "scalar_string": None,
                "scalar_ulong": False,
                "ann3": False,
                "scalar2_uchar": True, "scalar2_string": None,
                "scalar2_ulong": False,
            }

            cps = dict(self.smycps)
            cps.update(self.smycps2)
            dss = dict(self.smydss)
            dss.update(self.smydss2)
            dss.update(self.mydss)

            self._cf.dp.SetCommandVariable(["CPDICT", json.dumps(cps)])
            self._cf.dp.SetCommandVariable(["DSDICT", json.dumps(dss)])

            pool = self._pool.dp
            pool.AcqChannelList = [json.dumps(a) for a in arr]

            self._simps.dp.ChangeValueType("ScalarShort")
            self._simps.dp.Value = 43

            cnf = json.loads(rs.profileConfiguration)
            cnf["Timer"] = '[]'
            cnf["PreselectingDataSources"] = json.dumps(poolchannels)
            cnf["ComponentPreselection"] = json.dumps(componentgroup)
            cnf["DataSourcePreselection"] = json.dumps(datasourcegroup)
            rs.profileConfiguration = json.dumps(cnf)
            rs.preselectComponents()
            res = self.value(rs, "ComponentPreselection")
            resd = self.value(rs, "DataSourcePreselection")

            self.myAssertDict(json.loads(res), {
                "smycp": True, "smycp2": False, "smycp3": True,
                "s2mycp": False, "s2mycp2": True, "s2mycp3": True,
                "smycpnt1": False})
            self.myAssertDict(json.loads(resd), {
                "scalar_uchar": True, "scalar_string": True,
                "scalar_ulong": False,
                "scalar2_uchar": True, "scalar2_string": True,
                "scalar2_ulong": False,
                "ann3": False,
            })
            self.assertEqual(len(rs.descriptionErrors or []), 0)

            # res2 = json.loads(self._cf.dp.GetCommandVariable("VARS"))
            self.assertTrue(val["MntGrp"] in self._cf.dp.availableSelections())
            sed = json.loads(self._cf.dp.selections([val["MntGrp"]])[0])
            self.assertEqual(len(list(sed.keys())), len(self._keys))
            for key, vl in self._keys:
                self.assertTrue(key in sed.keys())
                if key in val:
                    self.assertEqual(sed[key], val[key])
                elif key == 'ComponentPreselection':
                    self.assertEqual(set(json.loads(sed[key])),
                                     set(json.loads(res)))
                elif key == 'DataSourcePreselection':
                    self.assertEqual(set(json.loads(sed[key])),
                                     set(json.loads(resd)))
                elif key == 'PreselectingDataSources':
                    self.assertEqual(set(json.loads(sed[key])),
                                     set(poolchannels))
                else:
                    self.assertEqual(sed[key], vl)
        finally:
            simps2.tearDown()

    # test
    # \brief It tests default settings
    def test_preselectComponents_2wds_notangodspool_alias(self):
        fun = sys._getframe().f_code.co_name
        print("Run: %s.%s() " % (self.__class__.__name__, fun))
        val = {"ConfigDevice": self._cf.dp.name(),
               "WriterDevice": self._wr.dp.name(),
               "Door": 'doortestp09/testts/t1r228',
               "MntGrp": 'nxsmntgrp'}
        simps2 = TestServerSetUp.TestServerSetUp(
            "ttestp09/testts/t2r228", "S2")

        arr = [
            {"name": "client_short", "full_name": "ttestp09/testts/t1r228"},
        ]

        try:
            db = tango.Database()
            simps2.setUp()
            db.put_device_alias(arr[0]["full_name"], arr[0]["name"])
            db.put_device_property(list(self._ms.ms.keys())[0],
                                   {'PoolNames': self._pool.dp.name()})

            self._ms.dps[list(self._ms.ms.keys())[0]].Init()
            rs = self.openRecSelector()
            rs.configDevice = val["ConfigDevice"]
            rs.door = val["Door"]
            rs.mntGrp = val["MntGrp"]
            rs.writerDevice = val["WriterDevice"]

            self._ms.dps[list(self._ms.ms.keys())[0]].Init()

            # channelerrors = []
            poolchannels = ["scalar2_long", "spectrum2_short", "client_short",
                            "scalar2_uchar", "scalar2_string", "ann3"]
            componentgroup = {
                "smycp": None, "smycp2": True, "smycp3": False,
                "smycpnt1": None,
                "s2mycp": None, "s2mycp2": True, "s2mycp3": False
            }
            datasourcegroup = {
                "scalar_uchar": True, "scalar_string": None,
                "scalar_ulong": False,
                "ann3": None,
                "scalar2_uchar": True, "scalar2_string": None,
                "scalar2_ulong": False,
            }

            cps = dict(self.smycps)
            cps.update(self.smycps2)
            dss = dict(self.smydss)
            dss.update(self.smydss2)
            dss.update(self.mydss)

            self._cf.dp.SetCommandVariable(["CPDICT", json.dumps(cps)])
            self._cf.dp.SetCommandVariable(["DSDICT", json.dumps(dss)])

            pool = self._pool.dp
            pool.AcqChannelList = [json.dumps(a) for a in arr]

            self._simps.dp.ChangeValueType("ScalarShort")
            self._simps.dp.Value = 43

            cnf = json.loads(rs.profileConfiguration)
            cnf["Timer"] = '[]'
            cnf["PreselectingDataSources"] = json.dumps(poolchannels)
            cnf["ComponentPreselection"] = json.dumps(componentgroup)
            cnf["DataSourcePreselection"] = json.dumps(datasourcegroup)
            rs.profileConfiguration = json.dumps(cnf)
            rs.preselectComponents()
            res = self.value(rs, "ComponentPreselection")
            resd = self.value(rs, "DataSourcePreselection")

            self.myAssertDict(json.loads(res), {
                "smycp": True, "smycp2": True, "smycp3": False,
                "s2mycp": True, "s2mycp2": True, "s2mycp3": False,
                "smycpnt1": True})
            self.myAssertDict(json.loads(resd), {
                "scalar_uchar": True, "scalar_string": True,
                "scalar_ulong": False,
                "scalar2_uchar": True, "scalar2_string": True,
                "scalar2_ulong": False,
                "ann3": None
            })
            self.assertEqual(len(rs.descriptionErrors), 1)

            # res2 = json.loads(self._cf.dp.GetCommandVariable("VARS"))
            self.assertTrue(val["MntGrp"] in self._cf.dp.availableSelections())
            sed = json.loads(self._cf.dp.selections([val["MntGrp"]])[0])
            self.assertEqual(len(list(sed.keys())), len(self._keys))
            for key, vl in self._keys:
                self.assertTrue(key in sed.keys())
                if key in val:
                    self.assertEqual(sed[key], val[key])
                elif key == 'ComponentPreselection':
                    self.assertEqual(set(json.loads(sed[key])),
                                     set(json.loads(res)))
                elif key == 'DataSourcePreselection':
                    self.assertEqual(set(json.loads(sed[key])),
                                     set(json.loads(resd)))
                elif key == 'PreselectingDataSources':
                    self.assertEqual(set(json.loads(sed[key])),
                                     set(poolchannels))
                else:
                    self.assertEqual(sed[key], vl)
        finally:
            db.delete_device_alias(arr[0]["name"])
            simps2.tearDown()

    # test
    # \brief It tests default settings
    def test_preselectComponents_2wds_notangodspool_alias_false(self):
        fun = sys._getframe().f_code.co_name
        print("Run: %s.%s() " % (self.__class__.__name__, fun))
        val = {"ConfigDevice": self._cf.dp.name(),
               "WriterDevice": self._wr.dp.name(),
               "Door": 'doortestp09/testts/t1r228',
               "MntGrp": 'nxsmntgrp'}
        simps2 = TestServerSetUp.TestServerSetUp(
            "ttestp09/testts/t2r228", "S2")

        arr = [
            {"name": "client_short", "full_name": "ttestp09/testts/t1r228"},
        ]

        try:
            db = tango.Database()
            simps2.setUp()
            db.put_device_alias(arr[0]["full_name"], arr[0]["name"])
            db.put_device_property(list(self._ms.ms.keys())[0],
                                   {'PoolNames': self._pool.dp.name()})

            self._ms.dps[list(self._ms.ms.keys())[0]].Init()
            rs = self.openRecSelector()
            rs.configDevice = val["ConfigDevice"]
            rs.door = val["Door"]
            rs.mntGrp = val["MntGrp"]
            rs.writerDevice = val["WriterDevice"]

            self._ms.dps[list(self._ms.ms.keys())[0]].Init()

            # channelerrors = []
            poolchannels = ["scalar2_long", "spectrum2_short", "client_short",
                            "scalar2_uchar", "scalar2_string", "ann3"]
            componentgroup = {
                "smycp": None, "smycp2": True, "smycp3": False,
                "smycpnt1": False,
                "s2mycp": None, "s2mycp2": True, "s2mycp3": False
            }
            datasourcegroup = {
                "scalar_uchar": True, "scalar_string": None,
                "scalar_ulong": False,
                "ann3": False,
                "scalar2_uchar": True, "scalar2_string": None,
                "scalar2_ulong": False,
            }

            cps = dict(self.smycps)
            cps.update(self.smycps2)
            dss = dict(self.smydss)
            dss.update(self.smydss2)
            dss.update(self.mydss)

            self._cf.dp.SetCommandVariable(["CPDICT", json.dumps(cps)])
            self._cf.dp.SetCommandVariable(["DSDICT", json.dumps(dss)])

            pool = self._pool.dp
            pool.AcqChannelList = [json.dumps(a) for a in arr]

            self._simps.dp.ChangeValueType("ScalarShort")
            self._simps.dp.Value = 43

            cnf = json.loads(rs.profileConfiguration)
            cnf["Timer"] = '[]'
            cnf["PreselectingDataSources"] = json.dumps(poolchannels)
            cnf["ComponentPreselection"] = json.dumps(componentgroup)
            cnf["DataSourcePreselection"] = json.dumps(datasourcegroup)
            rs.profileConfiguration = json.dumps(cnf)
            rs.preselectComponents()
            res = self.value(rs, "ComponentPreselection")
            resd = self.value(rs, "DataSourcePreselection")

            self.myAssertDict(json.loads(res), {
                "smycp": True, "smycp2": True, "smycp3": False,
                "s2mycp": True, "s2mycp2": True, "s2mycp3": False,
                "smycpnt1": False})
            self.myAssertDict(json.loads(resd), {
                "scalar_uchar": True, "scalar_string": True,
                "scalar_ulong": False,
                "scalar2_uchar": True, "scalar2_string": True,
                "scalar2_ulong": False,
                "ann3": False
            })
            self.assertEqual(len(rs.descriptionErrors or []), 0)

            # res2 = json.loads(self._cf.dp.GetCommandVariable("VARS"))
            self.assertTrue(val["MntGrp"] in self._cf.dp.availableSelections())
            sed = json.loads(self._cf.dp.selections([val["MntGrp"]])[0])
            self.assertEqual(len(list(sed.keys())), len(self._keys))
            for key, vl in self._keys:
                self.assertTrue(key in sed.keys())
                if key in val:
                    self.assertEqual(sed[key], val[key])
                elif key == 'ComponentPreselection':
                    self.assertEqual(set(json.loads(sed[key])),
                                     set(json.loads(res)))
                elif key == 'DataSourcePreselection':
                    self.assertEqual(set(json.loads(sed[key])),
                                     set(json.loads(resd)))
                elif key == 'PreselectingDataSources':
                    self.assertEqual(set(json.loads(sed[key])),
                                     set(poolchannels))
                else:
                    self.assertEqual(sed[key], vl)
        finally:
            db.delete_device_alias(arr[0]["name"])
            simps2.tearDown()

    # test
    # \brief It tests default settings
    def test_preselectComponents_2wds_notangodspool_alias_bl(self):
        fun = sys._getframe().f_code.co_name
        print("Run: %s.%s() " % (self.__class__.__name__, fun))
        val = {"ConfigDevice": self._cf.dp.name(),
               "WriterDevice": self._wr.dp.name(),
               "Door": 'doortestp09/testts/t1r228',
               "MntGrp": 'nxsmntgrp'}
        simps2 = TestServerSetUp.TestServerSetUp(
            "ttestp09/testts/t2r228", "S2")

        arr = [
            {"name": "client_short", "full_name": "ttestp09/testts/t1r228"},
        ]

        try:
            db = tango.Database()
            simps2.setUp()
            db.put_device_alias(arr[0]["full_name"], arr[0]["name"])
            db.put_device_property(list(self._ms.ms.keys())[0],
                                   {'PoolNames': self._pool.dp.name()})

            self._ms.dps[list(self._ms.ms.keys())[0]].Init()
            rs = self.openRecSelector()
            self.setProp(rs, "poolBlacklist",
                         [self._pool.dp.name()])
            rs.configDevice = val["ConfigDevice"]
            rs.door = val["Door"]
            rs.mntGrp = val["MntGrp"]
            rs.writerDevice = val["WriterDevice"]

            self._ms.dps[list(self._ms.ms.keys())[0]].Init()

            # channelerrors = []
            poolchannels = ["scalar2_long", "spectrum2_short", "client_short",
                            "scalar2_uchar", "scalar2_string", "ann3"]
            componentgroup = {
                "smycp": None, "smycp2": True, "smycp3": False,
                "smycpnt1": None,
                "s2mycp": None, "s2mycp2": True, "s2mycp3": False
            }
            datasourcegroup = {
                "scalar_uchar": True, "scalar_string": None,
                "scalar_ulong": False,
                "ann3": None,
                "scalar2_uchar": True, "scalar2_string": None,
                "scalar2_ulong": False,
            }

            cps = dict(self.smycps)
            cps.update(self.smycps2)
            dss = dict(self.smydss)
            dss.update(self.smydss2)
            dss.update(self.mydss)

            self._cf.dp.SetCommandVariable(["CPDICT", json.dumps(cps)])
            self._cf.dp.SetCommandVariable(["DSDICT", json.dumps(dss)])

            pool = self._pool.dp
            pool.AcqChannelList = [json.dumps(a) for a in arr]

            self._simps.dp.ChangeValueType("ScalarShort")
            self._simps.dp.Value = 43

            cnf = json.loads(rs.profileConfiguration)
            cnf["Timer"] = '[]'
            cnf["PreselectingDataSources"] = json.dumps(poolchannels)
            cnf["ComponentPreselection"] = json.dumps(componentgroup)
            cnf["DataSourcePreselection"] = json.dumps(datasourcegroup)
            rs.profileConfiguration = json.dumps(cnf)
            rs.preselectComponents()
            res = self.value(rs, "ComponentPreselection")
            resd = self.value(rs, "DataSourcePreselection")

            self.myAssertDict(json.loads(res), {
                "smycp": True, "smycp2": True, "smycp3": False,
                "s2mycp": True, "s2mycp2": True, "s2mycp3": False,
                "smycpnt1": None})
            self.myAssertDict(json.loads(resd), {
                "scalar_uchar": True, "scalar_string": True,
                "scalar_ulong": False,
                "scalar2_uchar": True, "scalar2_string": True,
                "scalar2_ulong": False,
                "ann3": None
            })
            self.assertEqual(len(rs.descriptionErrors), 2)

            # res2 = json.loads(self._cf.dp.GetCommandVariable("VARS"))
            self.assertTrue(val["MntGrp"] in self._cf.dp.availableSelections())
            sed = json.loads(self._cf.dp.selections([val["MntGrp"]])[0])
            self.assertEqual(len(list(sed.keys())), len(self._keys))
            for key, vl in self._keys:
                self.assertTrue(key in sed.keys())
                if key in val:
                    self.assertEqual(sed[key], val[key])
                elif key == 'ComponentPreselection':
                    self.assertEqual(set(json.loads(sed[key])),
                                     set(json.loads(res)))
                elif key == 'DataSourcePreselection':
                    self.assertEqual(set(json.loads(sed[key])),
                                     set(json.loads(resd)))
                elif key == 'PreselectingDataSources':
                    self.assertEqual(set(json.loads(sed[key])),
                                     set(poolchannels))
                else:
                    self.assertEqual(sed[key], vl)
        finally:
            db.delete_device_alias(arr[0]["name"])
            simps2.tearDown()

    # test
    # \brief It tests default settings
    def test_preselectComponents_2wds_notangodspool_alias_value(self):
        fun = sys._getframe().f_code.co_name
        print("Run: %s.%s() " % (self.__class__.__name__, fun))
        val = {"ConfigDevice": self._cf.dp.name(),
               "WriterDevice": self._wr.dp.name(),
               "Door": 'doortestp09/testts/t1r228',
               "MntGrp": 'nxsmntgrp'}
        simps2 = TestServerSetUp.TestServerSetUp(
            "ttestp09/testts/t2r228", "S2")

        arr = [
            {"name": "client_short", "full_name": "ttestp09/testts/t1r228"},
        ]

        try:
            db = tango.Database()
            simps2.setUp()

            db.put_device_alias(arr[0]["full_name"], arr[0]["name"])
            db.put_device_property(list(self._ms.ms.keys())[0],
                                   {'PoolNames': self._pool.dp.name()})

            self._ms.dps[list(self._ms.ms.keys())[0]].Init()
            rs = self.openRecSelector()
            rs.configDevice = val["ConfigDevice"]
            rs.door = val["Door"]
            rs.mntGrp = val["MntGrp"]
            rs.writerDevice = val["WriterDevice"]

            self._ms.dps[list(self._ms.ms.keys())[0]].Init()

            # channelerrors = []
            poolchannels = ["scalar2_long", "spectrum2_short", "client_short"]
            componentgroup = {
                "smycp": False, "smycp2": True, "smycp3": None,
                "smycpnt1": None,
                "s2mycp": False, "s2mycp2": True, "s2mycp3": None
            }
            cps = dict(self.smycps)
            cps.update(self.smycps2)
            dss = dict(self.smydss)
            dss.update(self.smydss2)

            self._cf.dp.SetCommandVariable(["CPDICT", json.dumps(cps)])
            self._cf.dp.SetCommandVariable(["DSDICT", json.dumps(dss)])

            pool = self._pool.dp
            pool.AcqChannelList = [json.dumps(a) for a in arr]

            cnf = json.loads(rs.profileConfiguration)
            cnf["Timer"] = '[]'
            cnf["PreselectingDataSources"] = json.dumps(poolchannels)
            cnf["ComponentPreselection"] = json.dumps(componentgroup)
            rs.profileConfiguration = json.dumps(cnf)
            rs.preselectComponents()
            res = self.value(rs, "ComponentPreselection")

            self.myAssertDict(json.loads(res), {
                "smycp": False, "smycp2": True, "smycp3": True,
                "s2mycp": False, "s2mycp2": True, "s2mycp3": True,
                "smycpnt1": True})
            self.assertTrue(not rs.descriptionErrors)

    #        print self._cf.dp.GetCommandVariable("COMMANDS")
            # res2 = json.loads(self._cf.dp.GetCommandVariable("VARS"))
            self.assertTrue(val["MntGrp"] in self._cf.dp.availableSelections())
            sed = json.loads(self._cf.dp.selections([val["MntGrp"]])[0])
            self.assertEqual(len(list(sed.keys())), len(self._keys))
            for key, vl in self._keys:
                self.assertTrue(key in sed.keys())
                if key in val:
                    self.assertEqual(sed[key], val[key])
                elif key == 'ComponentPreselection':
                    self.assertEqual(set(json.loads(sed[key])),
                                     set(json.loads(res)))
                elif key == 'PreselectingDataSources':
                    self.assertEqual(set(json.loads(sed[key])),
                                     set(poolchannels))
                else:
                    self.assertEqual(sed[key], vl)
        finally:
            db.delete_device_alias(arr[0]["name"])
            simps2.tearDown()

    # test
    # \brief It tests default settings
    def test_preselectComponents_2wds_notangodspool_alias_value_false(self):
        fun = sys._getframe().f_code.co_name
        print("Run: %s.%s() " % (self.__class__.__name__, fun))
        val = {"ConfigDevice": self._cf.dp.name(),
               "WriterDevice": self._wr.dp.name(),
               "Door": 'doortestp09/testts/t1r228',
               "MntGrp": 'nxsmntgrp'}
        simps2 = TestServerSetUp.TestServerSetUp(
            "ttestp09/testts/t2r228", "S2")

        arr = [
            {"name": "client_short", "full_name": "ttestp09/testts/t1r228"},
        ]

        try:
            db = tango.Database()
            simps2.setUp()

            db.put_device_alias(arr[0]["full_name"], arr[0]["name"])
            db.put_device_property(list(self._ms.ms.keys())[0],
                                   {'PoolNames': self._pool.dp.name()})

            self._ms.dps[list(self._ms.ms.keys())[0]].Init()
            rs = self.openRecSelector()
            rs.configDevice = val["ConfigDevice"]
            rs.door = val["Door"]
            rs.mntGrp = val["MntGrp"]
            rs.writerDevice = val["WriterDevice"]

            self._ms.dps[list(self._ms.ms.keys())[0]].Init()

            # channelerrors = []
            poolchannels = ["scalar2_long", "spectrum2_short", "client_short"]
            componentgroup = {
                "smycp": False, "smycp2": True, "smycp3": None,
                "smycpnt1": False,
                "s2mycp": False, "s2mycp2": True, "s2mycp3": None
            }
            cps = dict(self.smycps)
            cps.update(self.smycps2)
            dss = dict(self.smydss)
            dss.update(self.smydss2)

            self._cf.dp.SetCommandVariable(["CPDICT", json.dumps(cps)])
            self._cf.dp.SetCommandVariable(["DSDICT", json.dumps(dss)])

            pool = self._pool.dp
            pool.AcqChannelList = [json.dumps(a) for a in arr]

            cnf = json.loads(rs.profileConfiguration)
            cnf["Timer"] = '[]'
            cnf["PreselectingDataSources"] = json.dumps(poolchannels)
            cnf["ComponentPreselection"] = json.dumps(componentgroup)
            rs.profileConfiguration = json.dumps(cnf)
            rs.preselectComponents()
            res = self.value(rs, "ComponentPreselection")

            self.myAssertDict(json.loads(res), {
                "smycp": False, "smycp2": True, "smycp3": True,
                "s2mycp": False, "s2mycp2": True, "s2mycp3": True,
                "smycpnt1": False})
            self.assertTrue(not rs.descriptionErrors)

    #        print self._cf.dp.GetCommandVariable("COMMANDS")
            # res2 = json.loads(self._cf.dp.GetCommandVariable("VARS"))
            self.assertTrue(val["MntGrp"] in self._cf.dp.availableSelections())
            sed = json.loads(self._cf.dp.selections([val["MntGrp"]])[0])
            self.assertEqual(len(list(sed.keys())), len(self._keys))
            for key, vl in self._keys:
                self.assertTrue(key in sed.keys())
                if key in val:
                    self.assertEqual(sed[key], val[key])
                elif key == 'ComponentPreselection':
                    self.assertEqual(set(json.loads(sed[key])),
                                     set(json.loads(res)))
                elif key == 'PreselectingDataSources':
                    self.assertEqual(set(json.loads(sed[key])),
                                     set(poolchannels))
                else:
                    self.assertEqual(sed[key], vl)
        finally:
            db.delete_device_alias(arr[0]["name"])
            simps2.tearDown()

    # test
    # \brief It tests default settings
    def test_preselectComponents_2wds_notangodspool_alias_value_bl(self):
        fun = sys._getframe().f_code.co_name
        print("Run: %s.%s() " % (self.__class__.__name__, fun))
        val = {"ConfigDevice": self._cf.dp.name(),
               "WriterDevice": self._wr.dp.name(),
               "Door": 'doortestp09/testts/t1r228',
               "MntGrp": 'nxsmntgrp'}
        simps2 = TestServerSetUp.TestServerSetUp(
            "ttestp09/testts/t2r228", "S2")

        arr = [
            {"name": "client_short", "full_name": "ttestp09/testts/t1r228"},
        ]

        try:
            db = tango.Database()
            simps2.setUp()

            db.put_device_alias(arr[0]["full_name"], arr[0]["name"])
            db.put_device_property(list(self._ms.ms.keys())[0],
                                   {'PoolNames': self._pool.dp.name()})

            self._ms.dps[list(self._ms.ms.keys())[0]].Init()
            rs = self.openRecSelector()
            self.setProp(rs, "poolBlacklist",
                         [self._pool.dp.name()])
            rs.configDevice = val["ConfigDevice"]
            rs.door = val["Door"]
            rs.mntGrp = val["MntGrp"]
            rs.writerDevice = val["WriterDevice"]

            self._ms.dps[list(self._ms.ms.keys())[0]].Init()

            # channelerrors = []
            poolchannels = ["scalar2_long", "spectrum2_short", "client_short"]
            componentgroup = {
                "smycp": False, "smycp2": True, "smycp3": None,
                "smycpnt1": None,
                "s2mycp": False, "s2mycp2": True, "s2mycp3": None
            }
            cps = dict(self.smycps)
            cps.update(self.smycps2)
            dss = dict(self.smydss)
            dss.update(self.smydss2)

            self._cf.dp.SetCommandVariable(["CPDICT", json.dumps(cps)])
            self._cf.dp.SetCommandVariable(["DSDICT", json.dumps(dss)])

            pool = self._pool.dp
            pool.AcqChannelList = [json.dumps(a) for a in arr]

            cnf = json.loads(rs.profileConfiguration)
            cnf["Timer"] = '[]'
            cnf["PreselectingDataSources"] = json.dumps(poolchannels)
            cnf["ComponentPreselection"] = json.dumps(componentgroup)
            rs.profileConfiguration = json.dumps(cnf)
            rs.preselectComponents()
            res = self.value(rs, "ComponentPreselection")

            self.myAssertDict(json.loads(res), {
                "smycp": False, "smycp2": True, "smycp3": True,
                "s2mycp": False, "s2mycp2": True, "s2mycp3": True,
                "smycpnt1": None})
            self.assertTrue(rs.descriptionErrors)

    #        print self._cf.dp.GetCommandVariable("COMMANDS")
            # res2 = json.loads(self._cf.dp.GetCommandVariable("VARS"))
            self.assertTrue(val["MntGrp"] in self._cf.dp.availableSelections())
            sed = json.loads(self._cf.dp.selections([val["MntGrp"]])[0])
            self.assertEqual(len(list(sed.keys())), len(self._keys))
            for key, vl in self._keys:
                self.assertTrue(key in sed.keys())
                if key in val:
                    self.assertEqual(sed[key], val[key])
                elif key == 'ComponentPreselection':
                    self.assertEqual(set(json.loads(sed[key])),
                                     set(json.loads(res)))
                elif key == 'PreselectingDataSources':
                    self.assertEqual(set(json.loads(sed[key])),
                                     set(poolchannels))
                else:
                    self.assertEqual(sed[key], vl)
        finally:
            db.delete_device_alias(arr[0]["name"])
            simps2.tearDown()

    # test
    # \brief It tests default settings
    def test_preselectComponents_2wds_notangodspool_alias_novalue(self):
        fun = sys._getframe().f_code.co_name
        print("Run: %s.%s() " % (self.__class__.__name__, fun))
        val = {"ConfigDevice": self._cf.dp.name(),
               "WriterDevice": self._wr.dp.name(),
               "Door": 'doortestp09/testts/t1r228',
               "MntGrp": 'nxsmntgrp'}
        simps2 = TestServerSetUp.TestServerSetUp(
            "ttestp09/testts/t2r228", "S2")

        arr = [
            {"name": "client_short", "full_name": "ttestp09/testts/t1r228"},
        ]

        try:
            db = tango.Database()
            simps2.setUp()

            db.put_device_alias(arr[0]["full_name"], arr[0]["name"])
            db.put_device_property(list(self._ms.ms.keys())[0],
                                   {'PoolNames': self._pool.dp.name()})

            self._ms.dps[list(self._ms.ms.keys())[0]].Init()
            rs = self.openRecSelector()
            rs.configDevice = val["ConfigDevice"]
            rs.door = val["Door"]
            rs.mntGrp = val["MntGrp"]
            rs.writerDevice = val["WriterDevice"]

            self._ms.dps[list(self._ms.ms.keys())[0]].Init()

            # channelerrors = []
            poolchannels = ["scalar2_long", "spectrum2_short", "client2_short"]
            componentgroup = {
                "smycp": False, "smycp2": True, "smycp3": None,
                "s2mycpnt1": None,
                #   "s2mycp": False, "s2mycp2": False, "s2mycp3": False
            }

            cps = dict(self.smycps)
            cps.update(self.smycps2)
            dss = dict(self.smydss)
            dss.update(self.smydss2)

            self._cf.dp.SetCommandVariable(["CPDICT", json.dumps(cps)])
            self._cf.dp.SetCommandVariable(["DSDICT", json.dumps(dss)])

            pool = self._pool.dp
            pool.AcqChannelList = [json.dumps(a) for a in arr]

            cnf = json.loads(rs.profileConfiguration)
            cnf["Timer"] = '[]'
            cnf["PreselectingDataSources"] = json.dumps(poolchannels)
            cnf["ComponentPreselection"] = json.dumps(componentgroup)
            rs.profileConfiguration = json.dumps(cnf)
            rs.preselectComponents()
            res = self.value(rs, "ComponentPreselection")

            self.myAssertDict(json.loads(res), {
                "smycp": False, "smycp2": True, "smycp3": True,
                "s2mycpnt1": None})
            self.assertEqual(len(rs.descriptionErrors), 1)

    #        print self._cf.dp.GetCommandVariable("COMMANDS")
            # res2 = json.loads(self._cf.dp.GetCommandVariable("VARS"))
            self.assertTrue(val["MntGrp"] in self._cf.dp.availableSelections())
            sed = json.loads(self._cf.dp.selections([val["MntGrp"]])[0])
            self.assertEqual(len(list(sed.keys())), len(self._keys))
            for key, vl in self._keys:
                self.assertTrue(key in sed.keys())
                if key in val:
                    self.assertEqual(sed[key], val[key])
                elif key == 'ComponentPreselection':
                    self.assertEqual(set(json.loads(sed[key])),
                                     set(json.loads(res)))
                elif key == 'PreselectingDataSources':
                    self.assertEqual(set(json.loads(sed[key])),
                                     set(poolchannels))
                else:
                    self.assertEqual(sed[key], vl)
        finally:
            db.delete_device_alias(arr[0]["name"])
            simps2.tearDown()

    # test
    # \brief It tests default settings
    def test_preselectComponents_2wds_notangodspool_alias_novalue_false(self):
        fun = sys._getframe().f_code.co_name
        print("Run: %s.%s() " % (self.__class__.__name__, fun))
        val = {"ConfigDevice": self._cf.dp.name(),
               "WriterDevice": self._wr.dp.name(),
               "Door": 'doortestp09/testts/t1r228',
               "MntGrp": 'nxsmntgrp'}
        simps2 = TestServerSetUp.TestServerSetUp(
            "ttestp09/testts/t2r228", "S2")

        arr = [
            {"name": "client_short", "full_name": "ttestp09/testts/t1r228"},
        ]

        try:
            db = tango.Database()
            simps2.setUp()

            db.put_device_alias(arr[0]["full_name"], arr[0]["name"])
            db.put_device_property(list(self._ms.ms.keys())[0],
                                   {'PoolNames': self._pool.dp.name()})

            self._ms.dps[list(self._ms.ms.keys())[0]].Init()
            rs = self.openRecSelector()
            rs.configDevice = val["ConfigDevice"]
            rs.door = val["Door"]
            rs.mntGrp = val["MntGrp"]
            rs.writerDevice = val["WriterDevice"]

            self._ms.dps[list(self._ms.ms.keys())[0]].Init()

            # channelerrors = []
            poolchannels = ["scalar2_long", "spectrum2_short", "client2_short"]
            componentgroup = {
                "smycp": False, "smycp2": True, "smycp3": None,
                "s2mycpnt1": False,
                #   "s2mycp": False, "s2mycp2": False, "s2mycp3": False
            }

            cps = dict(self.smycps)
            cps.update(self.smycps2)
            dss = dict(self.smydss)
            dss.update(self.smydss2)

            self._cf.dp.SetCommandVariable(["CPDICT", json.dumps(cps)])
            self._cf.dp.SetCommandVariable(["DSDICT", json.dumps(dss)])

            pool = self._pool.dp
            pool.AcqChannelList = [json.dumps(a) for a in arr]

            cnf = json.loads(rs.profileConfiguration)
            cnf["Timer"] = '[]'
            cnf["PreselectingDataSources"] = json.dumps(poolchannels)
            cnf["ComponentPreselection"] = json.dumps(componentgroup)
            rs.profileConfiguration = json.dumps(cnf)
            rs.preselectComponents()
            res = self.value(rs, "ComponentPreselection")

            self.myAssertDict(json.loads(res), {
                "smycp": False, "smycp2": True, "smycp3": True,
                "s2mycpnt1": False})
            self.assertEqual(len(rs.descriptionErrors or []), 0)

    #        print self._cf.dp.GetCommandVariable("COMMANDS")
            # res2 = json.loads(self._cf.dp.GetCommandVariable("VARS"))
            self.assertTrue(val["MntGrp"] in self._cf.dp.availableSelections())
            sed = json.loads(self._cf.dp.selections([val["MntGrp"]])[0])
            self.assertEqual(len(list(sed.keys())), len(self._keys))
            for key, vl in self._keys:
                self.assertTrue(key in sed.keys())
                if key in val:
                    self.assertEqual(sed[key], val[key])
                elif key == 'ComponentPreselection':
                    self.assertEqual(set(json.loads(sed[key])),
                                     set(json.loads(res)))
                elif key == 'PreselectingDataSources':
                    self.assertEqual(set(json.loads(sed[key])),
                                     set(poolchannels))
                else:
                    self.assertEqual(sed[key], vl)
        finally:
            db.delete_device_alias(arr[0]["name"])
            simps2.tearDown()

    # test
    # \brief It tests default settings
    def test_preselectComponents_2wds_notangodspool_alias_novalue_bl(self):
        fun = sys._getframe().f_code.co_name
        print("Run: %s.%s() " % (self.__class__.__name__, fun))
        val = {"ConfigDevice": self._cf.dp.name(),
               "WriterDevice": self._wr.dp.name(),
               "Door": 'doortestp09/testts/t1r228',
               "MntGrp": 'nxsmntgrp'}
        simps2 = TestServerSetUp.TestServerSetUp(
            "ttestp09/testts/t2r228", "S2")

        arr = [
            {"name": "client_short", "full_name": "ttestp09/testts/t1r228"},
        ]

        try:
            db = tango.Database()
            simps2.setUp()

            db.put_device_alias(arr[0]["full_name"], arr[0]["name"])
            db.put_device_property(list(self._ms.ms.keys())[0],
                                   {'PoolNames': self._pool.dp.name()})

            self._ms.dps[list(self._ms.ms.keys())[0]].Init()
            rs = self.openRecSelector()
            self.setProp(rs, "poolBlacklist",
                         [self._pool.dp.name()])
            rs.configDevice = val["ConfigDevice"]
            rs.door = val["Door"]
            rs.mntGrp = val["MntGrp"]
            rs.writerDevice = val["WriterDevice"]

            self._ms.dps[list(self._ms.ms.keys())[0]].Init()

            # channelerrors = []
            poolchannels = ["scalar2_long", "spectrum2_short", "client2_short"]
            componentgroup = {
                "smycp": False, "smycp2": True, "smycp3": None,
                "s2mycpnt1": None,
                #   "s2mycp": False, "s2mycp2": False, "s2mycp3": False
            }

            cps = dict(self.smycps)
            cps.update(self.smycps2)
            dss = dict(self.smydss)
            dss.update(self.smydss2)

            self._cf.dp.SetCommandVariable(["CPDICT", json.dumps(cps)])
            self._cf.dp.SetCommandVariable(["DSDICT", json.dumps(dss)])

            pool = self._pool.dp
            pool.AcqChannelList = [json.dumps(a) for a in arr]

            cnf = json.loads(rs.profileConfiguration)
            cnf["Timer"] = '[]'
            cnf["PreselectingDataSources"] = json.dumps(poolchannels)
            cnf["ComponentPreselection"] = json.dumps(componentgroup)
            rs.profileConfiguration = json.dumps(cnf)
            rs.preselectComponents()
            res = self.value(rs, "ComponentPreselection")

            self.myAssertDict(json.loads(res), {
                "smycp": False, "smycp2": True, "smycp3": True,
                "s2mycpnt1": None})
            self.assertEqual(len(rs.descriptionErrors), 1)

    #        print self._cf.dp.GetCommandVariable("COMMANDS")
            # res2 = json.loads(self._cf.dp.GetCommandVariable("VARS"))
            self.assertTrue(val["MntGrp"] in self._cf.dp.availableSelections())
            sed = json.loads(self._cf.dp.selections([val["MntGrp"]])[0])
            self.assertEqual(len(list(sed.keys())), len(self._keys))
            for key, vl in self._keys:
                self.assertTrue(key in sed.keys())
                if key in val:
                    self.assertEqual(sed[key], val[key])
                elif key == 'ComponentPreselection':
                    self.assertEqual(set(json.loads(sed[key])),
                                     set(json.loads(res)))
                elif key == 'PreselectingDataSources':
                    self.assertEqual(set(json.loads(sed[key])),
                                     set(poolchannels))
                else:
                    self.assertEqual(sed[key], vl)
        finally:
            db.delete_device_alias(arr[0]["name"])
            simps2.tearDown()

    # test
    # \brief It tests default settings
    def test_preselectComponents_2wds_nocomponents(self):
        fun = sys._getframe().f_code.co_name
        print("Run: %s.%s() " % (self.__class__.__name__, fun))
        val = {"ConfigDevice": self._cf.dp.name(),
               "WriterDevice": self._wr.dp.name(),
               "Door": 'doortestp09/testts/t1r228',
               "MntGrp": 'nxsmntgrp'}
        simps2 = TestServerSetUp.TestServerSetUp(
            "ttestp09/testts/t2r228", "S2")

        # arr = [
        #     {"name": "client_short", "full_name": "ttestp09/testts/t1r228"},
        # ]

        try:
            # db = tango.Database()
            simps2.setUp()

            self._ms.dps[list(self._ms.ms.keys())[0]].Init()
            rs = self.openRecSelector()
            rs.configDevice = val["ConfigDevice"]
            rs.door = val["Door"]
            rs.mntGrp = val["MntGrp"]
            rs.writerDevice = val["WriterDevice"]

            self._ms.dps[list(self._ms.ms.keys())[0]].Init()

            # channelerrors = []
            poolchannels = []
            componentgroup = {
                "smycp": False, "smycp2": True, "smycp3": None,
                "s2mycp": False, "s2mycp2": True, "s2mycp3": None}

            cps = dict(self.smycps)
#            cps.update(self.smycps2)
            dss = dict(self.smydss)
#            dss.update(self.smydss2)

            self._cf.dp.SetCommandVariable(["CPDICT", json.dumps(cps)])
            self._cf.dp.SetCommandVariable(["DSDICT", json.dumps(dss)])

            cnf = json.loads(rs.profileConfiguration)
            cnf["Timer"] = '[]'
            cnf["PreselectingDataSources"] = json.dumps(poolchannels)
            cnf["ComponentPreselection"] = json.dumps(componentgroup)
            rs.profileConfiguration = json.dumps(cnf)
            rs.preselectComponents()
            res = self.value(rs, "ComponentPreselection")

            self.myAssertDict(json.loads(res), {
                "smycp": False, "smycp2": True, "smycp3": True,
                "s2mycp": False, "s2mycp2": None, "s2mycp3": None})
            self.assertEqual(len(rs.descriptionErrors), 2)

    #        print self._cf.dp.GetCommandVariable("COMMANDS")
            # res2 = json.loads(self._cf.dp.GetCommandVariable("VARS"))
            self.assertTrue(val["MntGrp"] in self._cf.dp.availableSelections())
            sed = json.loads(self._cf.dp.selections([val["MntGrp"]])[0])
            self.assertEqual(len(list(sed.keys())), len(self._keys))
            for key, vl in self._keys:
                self.assertTrue(key in sed.keys())
                if key in val:
                    self.assertEqual(sed[key], val[key])
                elif key == 'ComponentPreselection':
                    self.assertEqual(set(json.loads(sed[key])),
                                     set(json.loads(res)))
                elif key == 'PreselectingDataSources':
                    self.assertEqual(set(json.loads(sed[key])),
                                     set(poolchannels))
                else:
                    self.assertEqual(sed[key], vl)
        finally:
            simps2.tearDown()

    # resetPreselectedComponents test
    # \brief It tests default settings
    def test_resetPreselectedComponents_simple(self):
        fun = sys._getframe().f_code.co_name
        print("Run: %s.%s() " % (self.__class__.__name__, fun))
        val = {"ConfigDevice": self._cf.dp.name(),
               "WriterDevice": self._wr.dp.name(),
               "Door": 'doortestp09/testts/t1r228',
               "MntGrp": 'nxsmntgrp'}

        db = tango.Database()
        db.put_device_property(list(self._ms.ms.keys())[0],
                               {'PoolNames': self._pool.dp.name()})
        self._ms.dps[list(self._ms.ms.keys())[0]].Init()
        rs = self.openRecSelector()
        rs.configDevice = val["ConfigDevice"]
        rs.door = val["Door"]
        rs.mntGrp = val["MntGrp"]

        self._ms.dps[list(self._ms.ms.keys())[0]].Init()

        # channelerrors = []
        self.dump(rs)
        rs.resetPreselectedComponents()
        # sed2 =
        json.loads(self._cf.dp.selections([val["MntGrp"]])[0])
        res = self.value(rs, "ComponentPreselection")
        self.assertEqual(res, '{}')
        rs.profileConfiguration = '{}'
        rs.configDevice = val["ConfigDevice"]
        rs.door = val["Door"]
        rs.mntGrp = val["MntGrp"]
        rs.fetchProfile()
        res = self.value(rs, "ComponentPreselection")
        self.assertEqual(res, '{}')
        res2 = self.value(rs, "DataSourcePreselection")
        self.assertEqual(res2, '{}')

        self.compareToDump(
            rs,
            ["ComponentPreselection", "PreselectingDataSources", "Timer"])
        self.assertEqual(self.value(rs, "Timer"), '[]')
        self.assertEqual(self.value(rs, "PreselectingDataSources"), '[]')

    # resetPreselectedComponents test
    # \brief It tests default settings
    def test_resetPreselectedComponents_withcf(self):
        fun = sys._getframe().f_code.co_name
        print("Run: %s.%s() " % (self.__class__.__name__, fun))
        val = {"ConfigDevice": self._cf.dp.name(),
               "WriterDevice": self._wr.dp.name(),
               "Door": 'doortestp09/testts/t1r228',
               "MntGrp": 'nxsmntgrp'}

        # db = tango.Database()
        self._ms.dps[list(self._ms.ms.keys())[0]].Init()
        rs = self.openRecSelector()
        rs.configDevice = val["ConfigDevice"]
        rs.door = val["Door"]
        rs.mntGrp = val["MntGrp"]

        self._ms.dps[list(self._ms.ms.keys())[0]].Init()

        channelerrors = []
        # poolchannels = []
        componentgroup = {}

        self._cf.dp.SetCommandVariable(["CPDICT", json.dumps(self.mycps)])
        self._cf.dp.SetCommandVariable(["DSDICT", json.dumps(self.mydss)])

        self.dump(rs)
        rs.resetPreselectedComponents()
        # sed2 =
        json.loads(self._cf.dp.selections([val["MntGrp"]])[0])
        res = self.value(rs, "ComponentPreselection")
        res2 = self.value(rs, "DataSourcePreselection")
        self.compareToDump(rs, ["ComponentPreselection",
                                "PreselectingDataSources"])
        self.assertEqual(set(self.value(rs, "PreselectingDataSources")),
                         set(self.getDump("PreselectingDataSources")))

        self.assertEqual(res, '{}')
        self.assertEqual(res2, '{}')
        self.assertEqual(componentgroup, {})
        self.assertEqual(channelerrors, [])
        # print self._cf.dp.GetCommandVariable("COMMANDS")

        rs.profileConfiguration = '{}'
        rs.configDevice = val["ConfigDevice"]
        rs.door = val["Door"]
        rs.mntGrp = val["MntGrp"]
        rs.fetchProfile()
        res = self.value(rs, "ComponentPreselection")
        self.assertEqual(res, '{}')

    # test
    # \brief It tests default settings
    def test_resetPreselectedComponents_withcf_cps(self):
        fun = sys._getframe().f_code.co_name
        print("Run: %s.%s() " % (self.__class__.__name__, fun))
        val = {"ConfigDevice": self._cf.dp.name(),
               "WriterDevice": self._wr.dp.name(),
               "Door": 'doortestp09/testts/t1r228',
               "MntGrp": 'nxsmntgrp'}

        channelerrors = []
        poolchannels = ["mycp"]
        componentgroup = {"mycp": None}
        datasourcegroup = {"ann2": None}

        self._cf.dp.SetCommandVariable(["CPDICT", json.dumps(self.mycps)])
        self._cf.dp.SetCommandVariable(["DSDICT", json.dumps(self.mydss)])

        # db = tango.Database()
        self._ms.dps[list(self._ms.ms.keys())[0]].Init()
        rs = self.openRecSelector()
        self.setProp(rs, "defaultPreselectedComponents",
                     list(componentgroup.keys()))
        rs.configDevice = val["ConfigDevice"]
        rs.door = val["Door"]
        rs.mntGrp = val["MntGrp"]
        rs.writerDevice = val["WriterDevice"]

        self._ms.dps[list(self._ms.ms.keys())[0]].Init()

        cnf = json.loads(rs.profileConfiguration)
        cnf["Timer"] = '[]'
        cnf["ComponentPreselection"] = json.dumps(componentgroup)
        cnf["DataSourcePreselection"] = json.dumps(datasourcegroup)
        cnf["PreselectingDataSources"] = json.dumps(poolchannels)
        rs.profileConfiguration = json.dumps(cnf)
        # rs.defaultPreselectedComponents = list(componentgroup.keys())
        self.dump(rs)
        sed1 = json.loads(self._cf.dp.selections([val["MntGrp"]])[0])
        rs.resetPreselectedComponents()
        # print "VALUE"
        res = self.value(rs, "ComponentPreselection")
        res2 = self.value(rs, "DataSourcePreselection")
        pds = self.value(rs, "PreselectingDataSources")
        self.compareToDump(
            rs, ["ComponentPreselection",
                 "DataSourcePreselection",
                 "PreselectingDataSources"])

        self.assertEqual(
            set(json.loads(self.getDump("PreselectingDataSources"))),
            set(json.loads(pds)))
        self.myAssertDict(json.loads(res), {"mycp": True})
        self.myAssertDict(json.loads(res2), {})
        self.assertEqual(channelerrors, [])

        self.assertTrue(val["MntGrp"] in self._cf.dp.availableSelections())
        sed = json.loads(self._cf.dp.selections([val["MntGrp"]])[0])
        self.assertEqual(len(list(sed.keys())), len(self._keys))
        for key, vl in self._keys:
            self.assertTrue(key in sed.keys())
            self.assertTrue(key in sed1.keys())
            if key in val:
                self.assertEqual(sed[key], val[key])
                self.assertEqual(sed1[key], val[key])
            elif key == 'ComponentPreselection':
                self.myAssertDict(json.loads(sed[key]), json.loads(res))
                self.assertNotEqual(sed1[key], res)
            elif key == 'DataSourcePreselection':
                self.assertEqual(set(json.loads(sed[key])),
                                 set(json.loads(res2)))
            elif key == 'PreselectingDataSources':
                self.assertEqual(set(json.loads(sed[key])), set(poolchannels))
                self.assertEqual(set(json.loads(sed1[key])), set(poolchannels))
            else:
                self.assertEqual(sed[key], vl)
                self.assertEqual(sed1[key], vl)

    # test
    # \brief It tests default settings
    def test_resetPreselectedComponents_withcf_cps_t(self):
        fun = sys._getframe().f_code.co_name
        print("Run: %s.%s() " % (self.__class__.__name__, fun))
        val = {"ConfigDevice": self._cf.dp.name(),
               "WriterDevice": self._wr.dp.name(),
               "Door": 'doortestp09/testts/t1r228',
               "MntGrp": 'nxsmntgrp'}

        # db = tango.Database()
        self._ms.dps[list(self._ms.ms.keys())[0]].Init()
        self._ms.dps[list(self._ms.ms.keys())[0]].Init()

        channelerrors = []
        poolchannels = ["mycp"]
        componentgroup = {"mycp": True}
        datasourcegroup = {"ann2": True}

        self._cf.dp.SetCommandVariable(["CPDICT", json.dumps(self.mycps)])
        self._cf.dp.SetCommandVariable(["DSDICT", json.dumps(self.mydss)])

        rs = self.openRecSelector()
        self.setProp(rs, "defaultPreselectedComponents",
                     list(componentgroup.keys()))
        rs.configDevice = val["ConfigDevice"]
        rs.door = val["Door"]
        rs.mntGrp = val["MntGrp"]
        rs.writerDevice = val["WriterDevice"]

        cnf = json.loads(rs.profileConfiguration)
        cnf["Timer"] = '[]'
        cnf["PreselectingDataSources"] = json.dumps(poolchannels)
        cnf["DataSourcePreselection"] = json.dumps(datasourcegroup)
        rs.profileConfiguration = json.dumps(cnf)
        self.dump(rs)
        # sed1 =
        json.loads(self._cf.dp.selections([val["MntGrp"]])[0])
        rs.resetPreselectedComponents()
        # sed2 =
        json.loads(self._cf.dp.selections([val["MntGrp"]])[0])
        res = self.value(rs, "ComponentPreselection")
        res2 = self.value(rs, "DataSourcePreselection")
        pds = self.value(rs, "PreselectingDataSources")
        self.compareToDump(
            rs, ["ComponentPreselection",
                 "DataSourcePreselection",
                 "PreselectingDataSources"])

        self.assertEqual(
            set(json.loads(self.getDump("PreselectingDataSources"))),
            set(json.loads(pds)))
        self.myAssertDict(json.loads(res), {"mycp": True})
        self.myAssertDict(json.loads(res2), {})
        self.assertEqual(channelerrors, [])

        self.assertTrue(val["MntGrp"] in self._cf.dp.availableSelections())

    # test
    # \brief It tests default settings
    def test_resetPreselectedComponents_withcf_cps_false(self):
        fun = sys._getframe().f_code.co_name
        print("Run: %s.%s() " % (self.__class__.__name__, fun))
        val = {"ConfigDevice": self._cf.dp.name(),
               "WriterDevice": self._wr.dp.name(),
               "Door": 'doortestp09/testts/t1r228',
               "MntGrp": 'nxsmntgrp'}

        # db = tango.Database()
        self._ms.dps[list(self._ms.ms.keys())[0]].Init()
        self._ms.dps[list(self._ms.ms.keys())[0]].Init()

        channelerrors = []
        poolchannels = ["mycp"]
        componentgroup = {"mycp": False}
        datasourcegroup = {"ann2": False}

        self._cf.dp.SetCommandVariable(["CPDICT", json.dumps(self.mycps)])
        self._cf.dp.SetCommandVariable(["DSDICT", json.dumps(self.mydss)])

        rs = self.openRecSelector()
        self.setProp(rs, "defaultPreselectedComponents",
                     list(componentgroup.keys()))
        rs.configDevice = val["ConfigDevice"]
        rs.door = val["Door"]
        rs.mntGrp = val["MntGrp"]
        rs.writerDevice = val["WriterDevice"]

        cnf = json.loads(rs.profileConfiguration)
        cnf["Timer"] = '[]'
        cnf["PreselectingDataSources"] = json.dumps(poolchannels)
        cnf["DataSourcePreselection"] = json.dumps(datasourcegroup)
        rs.profileConfiguration = json.dumps(cnf)
        self.dump(rs)
        # sed1 =
        json.loads(self._cf.dp.selections([val["MntGrp"]])[0])
        rs.resetPreselectedComponents()
        # sed2 =
        json.loads(self._cf.dp.selections([val["MntGrp"]])[0])
        res = self.value(rs, "ComponentPreselection")
        res2 = self.value(rs, "DataSourcePreselection")
        pds = self.value(rs, "PreselectingDataSources")
        self.compareToDump(
            rs, ["ComponentPreselection",
                 "DataSourcePreselection",
                 "PreselectingDataSources"])

        self.assertEqual(
            set(json.loads(self.getDump("PreselectingDataSources"))),
            set(json.loads(pds)))
        self.myAssertDict(json.loads(res), {"mycp": True})
        self.myAssertDict(json.loads(res2), {})
        self.assertEqual(channelerrors, [])

        self.assertTrue(val["MntGrp"] in self._cf.dp.availableSelections())

    # test
    # \brief It tests default settings
    def test_resetPreselectedComponents_withcf_nocps(self):
        fun = sys._getframe().f_code.co_name
        print("Run: %s.%s() " % (self.__class__.__name__, fun))
        val = {"ConfigDevice": self._cf.dp.name(),
               "WriterDevice": self._wr.dp.name(),
               "Door": 'doortestp09/testts/t1r228',
               "MntGrp": 'nxsmntgrp'}

        # db = tango.Database()
        self._ms.dps[list(self._ms.ms.keys())[0]].Init()

        self._ms.dps[list(self._ms.ms.keys())[0]].Init()

        channelerrors = []
        poolchannels = ["mycp"]
        componentgroup = {}

        self._cf.dp.SetCommandVariable(["CPDICT", json.dumps(self.mycps)])
        self._cf.dp.SetCommandVariable(["DSDICT", json.dumps(self.mydss)])

        rs = self.openRecSelector()
        self.setProp(rs, "defaultPreselectedComponents",
                     list(componentgroup.keys()))
        rs.configDevice = val["ConfigDevice"]
        rs.door = val["Door"]
        rs.mntGrp = val["MntGrp"]
        rs.writerDevice = val["WriterDevice"]

        cnf = json.loads(rs.profileConfiguration)
        cnf["PreselectingDataSources"] = json.dumps(poolchannels)
        rs.profileConfiguration = json.dumps(cnf)
        self.dump(rs)
        # sed1 =
        json.loads(self._cf.dp.selections([val["MntGrp"]])[0])
        rs.resetPreselectedComponents()
        # sed2 =
        json.loads(self._cf.dp.selections([val["MntGrp"]])[0])
        res = self.value(rs, "ComponentPreselection")
        pds = self.value(rs, "PreselectingDataSources")
        self.compareToDump(
            rs, ["ComponentPreselection",
                 "DataSourcePreselection",
                 "PreselectingDataSources"])

        self.assertEqual(
            set(json.loads(self.getDump("PreselectingDataSources"))),
            set(json.loads(pds)))
        self.myAssertDict(json.loads(res), {})
        self.assertEqual(channelerrors, [])

        # print self._cf.dp.GetCommandVariable("COMMANDS")

        self.assertTrue(val["MntGrp"] in self._cf.dp.availableSelections())

    # test
    # \brief It tests default settings
    def test_resetPreselectedComponents_withcf_nochnnel_false(self):
        fun = sys._getframe().f_code.co_name
        print("Run: %s.%s() " % (self.__class__.__name__, fun))
        val = {"ConfigDevice": self._cf.dp.name(),
               "WriterDevice": self._wr.dp.name(),
               "Door": 'doortestp09/testts/t1r228',
               "MntGrp": 'nxsmntgrp'}

        # db = tango.Database()
        self._ms.dps[list(self._ms.ms.keys())[0]].Init()

        channelerrors = []
        poolchannels = []
        componentgroup = {"mycp": False}
        datasourcegroup = {"ann2": False}

        self._cf.dp.SetCommandVariable(["CPDICT", json.dumps(self.mycps)])
        self._cf.dp.SetCommandVariable(["DSDICT", json.dumps(self.mydss)])
        rs = self.openRecSelector()
        self.setProp(rs, "defaultPreselectedComponents",
                     list(componentgroup.keys()))
        rs.configDevice = val["ConfigDevice"]
        rs.door = val["Door"]
        rs.mntGrp = val["MntGrp"]
        rs.writerDevice = val["WriterDevice"]

        self._ms.dps[list(self._ms.ms.keys())[0]].Init()

        cnf = json.loads(rs.profileConfiguration)
        cnf["Timer"] = '[]'
        cnf["PreselectingDataSources"] = json.dumps(poolchannels)
        cnf["DataSourcePreselection"] = json.dumps(datasourcegroup)
        rs.profileConfiguration = json.dumps(cnf)
        self.dump(rs)
        sed1 = json.loads(self._cf.dp.selections([val["MntGrp"]])[0])
        rs.resetPreselectedComponents()
        res = self.value(rs, "ComponentPreselection")
        pds = self.value(rs, "PreselectingDataSources")
        self.compareToDump(
            rs, ["ComponentPreselection",
                 "DataSourcePreselection",
                 "PreselectingDataSources"])

        self.assertEqual(
            set(json.loads(self.getDump("PreselectingDataSources"))),
            set(json.loads(pds)))
        res2 = self.value(rs, "DataSourcePreselection")

        self.myAssertDict(json.loads(res), {"mycp": True})
        self.myAssertDict(json.loads(res2), {})
        self.assertEqual(channelerrors, [])

        # print self._cf.dp.GetCommandVariable("COMMANDS")
        self.assertTrue(val["MntGrp"] in self._cf.dp.availableSelections())
        sed = json.loads(self._cf.dp.selections([val["MntGrp"]])[0])
        # print sed
        self.assertEqual(len(list(sed.keys())), len(self._keys))
        for key, vl in self._keys:
            self.assertTrue(key in sed.keys())
            if key in val:
                self.assertEqual(sed[key], val[key])
                self.assertEqual(sed1[key], val[key])
            elif key == 'ComponentPreselection':
                self.myAssertDict(json.loads(sed[key]),
                                  json.loads(res))
                self.assertNotEqual(sed1[key], res)
            elif key == 'DataSourcePreselection':
                self.assertEqual(set(json.loads(sed[key])),
                                 set(json.loads(res2)))
            elif key == 'PreselectingDataSources':
                self.assertEqual(set(json.loads(sed[key])), set(poolchannels))
                self.assertEqual(set(json.loads(sed1[key])), set(poolchannels))
            else:
                self.assertEqual(sed[key], vl)
                self.assertEqual(sed1[key], vl)

    # test
    # \brief It tests default settings
    def test_resetPreselectedComponents_withcf_nochnnel_true(self):
        fun = sys._getframe().f_code.co_name
        print("Run: %s.%s() " % (self.__class__.__name__, fun))
        val = {"ConfigDevice": self._cf.dp.name(),
               "WriterDevice": self._wr.dp.name(),
               "Door": 'doortestp09/testts/t1r228',
               "MntGrp": 'nxsmntgrp'}

        # db = tango.Database()
        self._ms.dps[list(self._ms.ms.keys())[0]].Init()

        channelerrors = []
        poolchannels = []
        componentgroup = {"mycp": True}
        datasourcegroup = {"ann2": True}

        self._cf.dp.SetCommandVariable(["CPDICT", json.dumps(self.mycps)])
        self._cf.dp.SetCommandVariable(["DSDICT", json.dumps(self.mydss)])
        rs = self.openRecSelector()
        self.setProp(rs, "defaultPreselectedComponents",
                     list(componentgroup.keys()))
        rs.configDevice = val["ConfigDevice"]
        rs.door = val["Door"]
        rs.mntGrp = val["MntGrp"]
        rs.writerDevice = val["WriterDevice"]

        self._ms.dps[list(self._ms.ms.keys())[0]].Init()

        cnf = json.loads(rs.profileConfiguration)
        cnf["Timer"] = '[]'
        cnf["PreselectingDataSources"] = json.dumps(poolchannels)
        cnf["DataSourcePreselection"] = json.dumps(datasourcegroup)
        rs.profileConfiguration = json.dumps(cnf)
        self.dump(rs)
        sed1 = json.loads(self._cf.dp.selections([val["MntGrp"]])[0])
        rs.resetPreselectedComponents()
        res = self.value(rs, "ComponentPreselection")
        pds = self.value(rs, "PreselectingDataSources")
        self.compareToDump(
            rs, ["ComponentPreselection",
                 "DataSourcePreselection",
                 "PreselectingDataSources"])

        self.assertEqual(
            set(json.loads(self.getDump("PreselectingDataSources"))),
            set(json.loads(pds)))
        res2 = self.value(rs, "DataSourcePreselection")

        self.myAssertDict(json.loads(res), {"mycp": True})
        self.myAssertDict(json.loads(res2), {})
        self.assertEqual(channelerrors, [])

        # print self._cf.dp.GetCommandVariable("COMMANDS")
        self.assertTrue(val["MntGrp"] in self._cf.dp.availableSelections())
        sed = json.loads(self._cf.dp.selections([val["MntGrp"]])[0])
        # print sed
        self.assertEqual(len(list(sed.keys())), len(self._keys))
        for key, vl in self._keys:
            self.assertTrue(key in sed.keys())
            if key in val:
                self.assertEqual(sed[key], val[key])
                self.assertEqual(sed1[key], val[key])
            elif key == 'ComponentPreselection':
                self.myAssertDict(json.loads(sed[key]),
                                  json.loads(res))
                self.assertNotEqual(sed1[key], res)
            elif key == 'DataSourcePreselection':
                self.assertEqual(set(json.loads(sed[key])),
                                 set(json.loads(res2)))
            elif key == 'PreselectingDataSources':
                self.assertEqual(set(json.loads(sed[key])), set(poolchannels))
                self.assertEqual(set(json.loads(sed1[key])), set(poolchannels))
            else:
                self.assertEqual(sed[key], vl)
                self.assertEqual(sed1[key], vl)

    # test
    # \brief It tests default settings
    def test_resetPreselectedComponents_withcf_nochnnel(self):
        fun = sys._getframe().f_code.co_name
        print("Run: %s.%s() " % (self.__class__.__name__, fun))
        val = {"ConfigDevice": self._cf.dp.name(),
               "WriterDevice": self._wr.dp.name(),
               "Door": 'doortestp09/testts/t1r228',
               "MntGrp": 'nxsmntgrp'}

        # db = tango.Database()
        self._ms.dps[list(self._ms.ms.keys())[0]].Init()

        channelerrors = []
        poolchannels = []
        componentgroup = {"mycp": None}
        datasourcegroup = {"ann2": None}

        self._cf.dp.SetCommandVariable(["CPDICT", json.dumps(self.mycps)])
        self._cf.dp.SetCommandVariable(["DSDICT", json.dumps(self.mydss)])
        rs = self.openRecSelector()
        self.setProp(rs, "defaultPreselectedComponents",
                     list(componentgroup.keys()))
        rs.configDevice = val["ConfigDevice"]
        rs.door = val["Door"]
        rs.mntGrp = val["MntGrp"]
        rs.writerDevice = val["WriterDevice"]

        self._ms.dps[list(self._ms.ms.keys())[0]].Init()

        cnf = json.loads(rs.profileConfiguration)
        cnf["Timer"] = '[]'
        cnf["PreselectingDataSources"] = json.dumps(poolchannels)
        cnf["DataSourcePreselection"] = json.dumps(datasourcegroup)
        rs.profileConfiguration = json.dumps(cnf)
        self.dump(rs)
        sed1 = json.loads(self._cf.dp.selections([val["MntGrp"]])[0])
        rs.resetPreselectedComponents()
        res = self.value(rs, "ComponentPreselection")
        pds = self.value(rs, "PreselectingDataSources")
        self.compareToDump(
            rs, ["ComponentPreselection",
                 "DataSourcePreselection",
                 "PreselectingDataSources"])

        self.assertEqual(
            set(json.loads(self.getDump("PreselectingDataSources"))),
            set(json.loads(pds)))
        res2 = self.value(rs, "DataSourcePreselection")

        self.myAssertDict(json.loads(res), {"mycp": True})
        self.myAssertDict(json.loads(res2), {})
        self.assertEqual(channelerrors, [])

        # print self._cf.dp.GetCommandVariable("COMMANDS")
        self.assertTrue(val["MntGrp"] in self._cf.dp.availableSelections())
        sed = json.loads(self._cf.dp.selections([val["MntGrp"]])[0])
        # print sed
        self.assertEqual(len(list(sed.keys())), len(self._keys))
        for key, vl in self._keys:
            self.assertTrue(key in sed.keys())
            if key in val:
                self.assertEqual(sed[key], val[key])
                self.assertEqual(sed1[key], val[key])
            elif key == 'ComponentPreselection':
                self.myAssertDict(json.loads(sed[key]),
                                  json.loads(res))
                self.assertNotEqual(sed1[key], res)
            elif key == 'DataSourcePreselection':
                self.assertEqual(set(json.loads(sed[key])),
                                 set(json.loads(res2)))
            elif key == 'PreselectingDataSources':
                self.assertEqual(set(json.loads(sed[key])), set(poolchannels))
                self.assertEqual(set(json.loads(sed1[key])), set(poolchannels))
            else:
                self.assertEqual(sed[key], vl)
                self.assertEqual(sed1[key], vl)

    # test
    # \brief It tests default settings
    def test_resetPreselectedComponents_wds_t(self):
        fun = sys._getframe().f_code.co_name
        print("Run: %s.%s() " % (self.__class__.__name__, fun))
        val = {"ConfigDevice": self._cf.dp.name(),
               "WriterDevice": self._wr.dp.name(),
               "Door": 'doortestp09/testts/t1r228',
               "MntGrp": 'nxsmntgrp'}

        # db = tango.Database()
        self._ms.dps[list(self._ms.ms.keys())[0]].Init()
        channelerrors = []
        poolchannels = []
        componentgroup = {"smycp": True}
        datasourcegroup = {"scalar_uchar": True}

        self._cf.dp.SetCommandVariable(["CPDICT", json.dumps(self.smycps)])
        self._cf.dp.SetCommandVariable(["DSDICT", json.dumps(self.smydss)])
        rs = self.openRecSelector()
        self.setProp(rs, "defaultPreselectedComponents",
                     list(componentgroup.keys()))
        rs.configDevice = val["ConfigDevice"]
        rs.door = val["Door"]
        rs.mntGrp = val["MntGrp"]
        rs.writerDevice = val["WriterDevice"]

        self._ms.dps[list(self._ms.ms.keys())[0]].Init()

        cnf = json.loads(rs.profileConfiguration)
        cnf["DataSourcePreselection"] = json.dumps(datasourcegroup)
        cnf["PreselectingDataSources"] = json.dumps(poolchannels)
        rs.profileConfiguration = json.dumps(cnf)
        self.dump(rs)
        # sed1 =
        json.loads(self._cf.dp.selections([val["MntGrp"]])[0])
        rs.resetPreselectedComponents()
        # sed2 =
        json.loads(self._cf.dp.selections([val["MntGrp"]])[0])
        res = self.value(rs, "ComponentPreselection")
        res2 = self.value(rs, "DataSourcePreselection")
        pds = self.value(rs, "PreselectingDataSources")
        self.compareToDump(
            rs, ["ComponentPreselection",
                 "DataSourcePreselection",
                 "PreselectingDataSources"])

        self.assertEqual(
            set(json.loads(self.getDump("PreselectingDataSources"))),
            set(json.loads(pds)))
        self.myAssertDict(json.loads(res), {"smycp": True})
        self.myAssertDict(json.loads(res2), {})
        self.assertEqual(channelerrors, [])

        self.assertTrue(val["MntGrp"] in self._cf.dp.availableSelections())

    # test
    # \brief It tests default settings
    def test_resetPreselectedComponents_wds_false(self):
        fun = sys._getframe().f_code.co_name
        print("Run: %s.%s() " % (self.__class__.__name__, fun))
        val = {"ConfigDevice": self._cf.dp.name(),
               "WriterDevice": self._wr.dp.name(),
               "Door": 'doortestp09/testts/t1r228',
               "MntGrp": 'nxsmntgrp'}

        # db = tango.Database()
        self._ms.dps[list(self._ms.ms.keys())[0]].Init()
        channelerrors = []
        poolchannels = []
        componentgroup = {"smycp": False}
        datasourcegroup = {"scalar_uchar": False}

        self._cf.dp.SetCommandVariable(["CPDICT", json.dumps(self.smycps)])
        self._cf.dp.SetCommandVariable(["DSDICT", json.dumps(self.smydss)])
        rs = self.openRecSelector()
        self.setProp(rs, "defaultPreselectedComponents",
                     list(componentgroup.keys()))
        rs.configDevice = val["ConfigDevice"]
        rs.door = val["Door"]
        rs.mntGrp = val["MntGrp"]
        rs.writerDevice = val["WriterDevice"]

        self._ms.dps[list(self._ms.ms.keys())[0]].Init()

        cnf = json.loads(rs.profileConfiguration)
        cnf["DataSourcePreselection"] = json.dumps(datasourcegroup)
        cnf["PreselectingDataSources"] = json.dumps(poolchannels)
        rs.profileConfiguration = json.dumps(cnf)
        self.dump(rs)
        # sed1 =
        json.loads(self._cf.dp.selections([val["MntGrp"]])[0])
        rs.resetPreselectedComponents()
        # sed2 =
        json.loads(self._cf.dp.selections([val["MntGrp"]])[0])
        res = self.value(rs, "ComponentPreselection")
        res2 = self.value(rs, "DataSourcePreselection")
        pds = self.value(rs, "PreselectingDataSources")
        self.compareToDump(
            rs, ["ComponentPreselection",
                 "DataSourcePreselection",
                 "PreselectingDataSources"])

        self.assertEqual(
            set(json.loads(self.getDump("PreselectingDataSources"))),
            set(json.loads(pds)))
        self.myAssertDict(json.loads(res), {"smycp": True})
        self.myAssertDict(json.loads(res2), {})
        self.assertEqual(channelerrors, [])

        self.assertTrue(val["MntGrp"] in self._cf.dp.availableSelections())

    # test
    # \brief It tests default settings
    def test_resetPreselectedComponents_wds(self):
        fun = sys._getframe().f_code.co_name
        print("Run: %s.%s() " % (self.__class__.__name__, fun))
        val = {"ConfigDevice": self._cf.dp.name(),
               "WriterDevice": self._wr.dp.name(),
               "Door": 'doortestp09/testts/t1r228',
               "MntGrp": 'nxsmntgrp'}

        # db = tango.Database()
        self._ms.dps[list(self._ms.ms.keys())[0]].Init()
        channelerrors = []
        poolchannels = []
        componentgroup = {"smycp": None}
        datasourcegroup = {"scalar_uchar": None}

        self._cf.dp.SetCommandVariable(["CPDICT", json.dumps(self.smycps)])
        self._cf.dp.SetCommandVariable(["DSDICT", json.dumps(self.smydss)])
        rs = self.openRecSelector()
        self.setProp(rs, "defaultPreselectedComponents",
                     list(componentgroup.keys()))
        rs.configDevice = val["ConfigDevice"]
        rs.door = val["Door"]
        rs.mntGrp = val["MntGrp"]
        rs.writerDevice = val["WriterDevice"]

        self._ms.dps[list(self._ms.ms.keys())[0]].Init()

        cnf = json.loads(rs.profileConfiguration)
        cnf["DataSourcePreselection"] = json.dumps(datasourcegroup)
        cnf["PreselectingDataSources"] = json.dumps(poolchannels)
        rs.profileConfiguration = json.dumps(cnf)
        self.dump(rs)
        # sed1 =
        json.loads(self._cf.dp.selections([val["MntGrp"]])[0])
        rs.resetPreselectedComponents()
        # sed2 =
        json.loads(self._cf.dp.selections([val["MntGrp"]])[0])
        res = self.value(rs, "ComponentPreselection")
        res2 = self.value(rs, "DataSourcePreselection")
        pds = self.value(rs, "PreselectingDataSources")
        self.compareToDump(
            rs, ["ComponentPreselection",
                 "DataSourcePreselection",
                 "PreselectingDataSources"])

        self.assertEqual(
            set(json.loads(self.getDump("PreselectingDataSources"))),
            set(json.loads(pds)))
        self.myAssertDict(json.loads(res), {"smycp": True})
        self.myAssertDict(json.loads(res2), {})
        self.assertEqual(channelerrors, [])

        self.assertTrue(val["MntGrp"] in self._cf.dp.availableSelections())

    # test
    # \brief It tests default settings
    def test_resetPreselectedComponents_wds2(self):
        fun = sys._getframe().f_code.co_name
        print("Run: %s.%s() " % (self.__class__.__name__, fun))
        val = {"ConfigDevice": self._cf.dp.name(),
               "WriterDevice": self._wr.dp.name(),
               "Door": 'doortestp09/testts/t1r228',
               "MntGrp": 'nxsmntgrp'}

        # db = tango.Database()
        self._ms.dps[list(self._ms.ms.keys())[0]].Init()

        channelerrors = []
        poolchannels = []
        componentgroup = {"smycp": False, "smycp2": True, "smycp3": None}
        datasourcegroup = {"scalar_uchar": None,
                           "scalar_string": False,
                           "scalar_ulong": True}

        self._cf.dp.SetCommandVariable(["CPDICT", json.dumps(self.smycps)])
        self._cf.dp.SetCommandVariable(["DSDICT", json.dumps(self.smydss)])
        rs = self.openRecSelector()
        self.setProp(rs, "defaultPreselectedComponents",
                     list(componentgroup.keys()))
        rs.configDevice = val["ConfigDevice"]
        rs.door = val["Door"]
        rs.mntGrp = val["MntGrp"]
        rs.writerDevice = val["WriterDevice"]

        self._ms.dps[list(self._ms.ms.keys())[0]].Init()

        cnf = json.loads(rs.profileConfiguration)
        cnf["Timer"] = '[]'
        cnf["PreselectingDataSources"] = json.dumps(poolchannels)
        cnf["DataSourcePreselection"] = json.dumps(datasourcegroup)
        rs.profileConfiguration = json.dumps(cnf)
        self.dump(rs)
        sed1 = json.loads(self._cf.dp.selections([val["MntGrp"]])[0])
        rs.resetPreselectedComponents()
        res = self.value(rs, "ComponentPreselection")
        resd = self.value(rs, "DataSourcePreselection")
        pds = self.value(rs, "PreselectingDataSources")
        self.compareToDump(
            rs, ["ComponentPreselection",
                 "DataSourcePreselection",
                 "PreselectingDataSources"])

        self.assertEqual(
            set(json.loads(self.getDump("PreselectingDataSources"))),
            set(json.loads(pds)))
        self.myAssertDict(json.loads(resd), {})

        self.myAssertDict(json.loads(res), {
            "smycp": True, "smycp2": True, "smycp3": True})
        self.assertEqual(channelerrors, [])

        # res2 = json.loads(self._cf.dp.GetCommandVariable("VARS"))
        self.assertTrue(val["MntGrp"] in self._cf.dp.availableSelections())
        sed = json.loads(self._cf.dp.selections([val["MntGrp"]])[0])
        self.assertEqual(len(list(sed.keys())), len(self._keys))
        for key, vl in self._keys:
            self.assertTrue(key in sed.keys())
            if key in val:
                self.assertEqual(sed[key], val[key])
                self.assertEqual(sed1[key], val[key])
            elif key == 'DataSourcePreselection':
                self.assertEqual(set(json.loads(sed[key])),
                                 set(json.loads(resd)))
            elif key == 'ComponentPreselection':
                self.myAssertDict(json.loads(sed[key]),
                                  json.loads(res))
                self.assertNotEqual(sed1[key], res)
            elif key == 'PreselectingDataSources':
                self.assertEqual(set(json.loads(sed[key])),
                                 set(poolchannels))
                self.assertEqual(set(json.loads(sed1[key])),
                                 set(poolchannels))
            else:
                self.assertEqual(sed[key], vl)
                self.assertEqual(sed1[key], vl)

    # test
    # \brief It tests default settings
    def test_resetPreselectedComponents_2wds(self):
        fun = sys._getframe().f_code.co_name
        print("Run: %s.%s() " % (self.__class__.__name__, fun))
        val = {"ConfigDevice": self._cf.dp.name(),
               "WriterDevice": self._wr.dp.name(),
               "Door": 'doortestp09/testts/t1r228',
               "MntGrp": 'nxsmntgrp'}
        simps2 = TestServerSetUp.TestServerSetUp(
            "ttestp09/testts/t2r228", "S2")
        try:
            simps2.setUp()

            # db = tango.Database()
            self._ms.dps[list(self._ms.ms.keys())[0]].Init()

            channelerrors = []
            poolchannels = []
            componentgroup = {
                "smycp": None, "smycp2": None, "smycp3": None,
                "s2mycp": None, "s2mycp2": None, "s2mycp3": None
            }
            datasourcegroup = {
                "scalar_uchar": None, "scalar_string": None,
                "scalar_ulong": None,
                "scalar2_uchar": None, "scalar2_string": None,
                "scalar2_ulong": None,
            }

            cps = dict(self.smycps)
            cps.update(self.smycps2)
            dss = dict(self.smydss)
            dss.update(self.smydss2)

            self._cf.dp.SetCommandVariable(["CPDICT", json.dumps(cps)])
            self._cf.dp.SetCommandVariable(["DSDICT", json.dumps(dss)])
            rs = self.openRecSelector()
            self.setProp(rs, "defaultPreselectedComponents",
                         list(componentgroup.keys()))
            rs.configDevice = val["ConfigDevice"]
            rs.door = val["Door"]
            rs.mntGrp = val["MntGrp"]
            rs.writerDevice = val["WriterDevice"]

            self._ms.dps[list(self._ms.ms.keys())[0]].Init()

            cnf = json.loads(rs.profileConfiguration)
            cnf["Timer"] = '[]'
            cnf["PreselectingDataSources"] = json.dumps(poolchannels)
            cnf["DataSourcePreselection"] = json.dumps(datasourcegroup)
            rs.profileConfiguration = json.dumps(cnf)
            self.dump(rs)
            sed1 = json.loads(self._cf.dp.selections([val["MntGrp"]])[0])
            rs.resetPreselectedComponents()
            res = self.value(rs, "ComponentPreselection")
            resd = self.value(rs, "DataSourcePreselection")
            pds = self.value(rs, "PreselectingDataSources")
            self.compareToDump(
                rs, ["ComponentPreselection",
                     "DataSourcePreselection",
                     "PreselectingDataSources"])

            self.assertEqual(
                set(json.loads(self.getDump("PreselectingDataSources"))),
                set(json.loads(pds)))
            self.myAssertDict(json.loads(resd), {})

            self.myAssertDict(json.loads(res), {
                "smycp": True, "smycp2": True, "smycp3": True,
                "s2mycp": True, "s2mycp2": True, "s2mycp3": True})
            self.assertEqual(len(channelerrors), 0)

            # res2 = json.loads(self._cf.dp.GetCommandVariable("VARS"))
            self.assertTrue(val["MntGrp"] in self._cf.dp.availableSelections())
            sed = json.loads(self._cf.dp.selections([val["MntGrp"]])[0])
            self.assertEqual(len(list(sed.keys())), len(self._keys))
            for key, vl in self._keys:
                self.assertTrue(key in sed.keys())
                if key in val:
                    self.assertEqual(sed[key], val[key])
                    self.assertEqual(sed1[key], val[key])
                elif key == 'ComponentPreselection':
                    self.myAssertDict(json.loads(sed[key]),
                                      json.loads(res))
                    self.assertNotEqual(sed1[key], res)
                elif key == 'DataSourcePreselection':
                    self.assertEqual(set(json.loads(sed[key])),
                                     set(json.loads(resd)))
                elif key == 'PreselectingDataSources':
                    self.assertEqual(set(json.loads(sed[key])),
                                     set(poolchannels))
                    self.assertEqual(set(json.loads(sed1[key])),
                                     set(poolchannels))
                else:
                    self.assertEqual(sed[key], vl)
                    self.assertEqual(sed1[key], vl)
        finally:
            simps2.tearDown()

    # test
    # \brief It tests default settings
    def test_resetPreselectedComponents_2wds_dvnorunning_pe(self):
        fun = sys._getframe().f_code.co_name
        print("Run: %s.%s() " % (self.__class__.__name__, fun))
        val = {"ConfigDevice": self._cf.dp.name(),
               "WriterDevice": self._wr.dp.name(),
               "Door": 'doortestp09/testts/t1r228',
               "MntGrp": 'nxsmntgrp'}
        simps2 = TestServerSetUp.TestServerSetUp(
            "ttestp09/testts/t2r228", "S2")
        try:
            simps2.add()

            # db = tango.Database()
            self._ms.dps[list(self._ms.ms.keys())[0]].Init()

            # channelerrors = []
            poolchannels = []
            componentgroup = dict((k, None) for k in self.specps.keys())
            datasourcegroup = dict((k, None) for k in self.spedss.keys())

            cps = dict(self.smycps)
            cps.update(self.smycps2)
            cps.update(self.specps)
            dss = dict(self.smydss)
            dss.update(self.smydss2)
            dss.update(self.spedss)

            self._cf.dp.SetCommandVariable(["CPDICT", json.dumps(cps)])
            self._cf.dp.SetCommandVariable(["DSDICT", json.dumps(dss)])

            rs = self.openRecSelector()
            self.setProp(rs, "defaultPreselectedComponents",
                         list(componentgroup.keys()))
            rs.configDevice = val["ConfigDevice"]
            rs.door = val["Door"]
            rs.mntGrp = val["MntGrp"]
            rs.writerDevice = val["WriterDevice"]

            self._ms.dps[list(self._ms.ms.keys())[0]].Init()

            cnf = json.loads(rs.profileConfiguration)
            cnf["Timer"] = '[]'
            cnf["PreselectingDataSources"] = json.dumps(poolchannels)
            cnf["DataSourcePreselection"] = json.dumps(datasourcegroup)
            rs.profileConfiguration = json.dumps(cnf)
            self.dump(rs)
            sed1 = json.loads(self._cf.dp.selections([val["MntGrp"]])[0])
            rs.resetPreselectedComponents()
            res = self.value(rs, "ComponentPreselection")
            resd = self.value(rs, "DataSourcePreselection")
            pds = self.value(rs, "PreselectingDataSources")
            self.compareToDump(
                rs, ["ComponentPreselection",
                     "DataSourcePreselection",
                     "PreselectingDataSources"])

            self.assertEqual(
                set(json.loads(self.getDump("PreselectingDataSources"))),
                set(json.loads(pds)))
            self.myAssertDict(json.loads(resd), {})

            self.myAssertDict(json.loads(res), {
                u'pyeval1a': True, u'pyeval2a': None, u'pyeval2c': None,
                u'pyeval2b': True, u'pyeval2': True, u'pyeval0': True,
                u'pyeval1': True})
            self.assertEqual(len(rs.descriptionErrors), 2)

            # res2 = json.loads(self._cf.dp.GetCommandVariable("VARS"))
            self.assertTrue(val["MntGrp"] in self._cf.dp.availableSelections())
            sed = json.loads(self._cf.dp.selections([val["MntGrp"]])[0])
            self.assertEqual(len(list(sed.keys())), len(self._keys))
            for key, vl in self._keys:
                self.assertTrue(key in sed.keys())
                if key in val:
                    self.assertEqual(sed[key], val[key])
                    self.assertEqual(sed1[key], val[key])
                elif key == 'DataSourcePreselection':
                    self.assertEqual(set(json.loads(sed[key])),
                                     set(json.loads(resd)))
                elif key == 'ComponentPreselection':
                    self.myAssertDict(json.loads(sed[key]), json.loads(res))
                    self.assertNotEqual(sed1[key], res)
                elif key == 'PreselectingDataSources':
                    self.assertEqual(set(json.loads(sed[key])),
                                     set(poolchannels))
                    self.assertEqual(set(json.loads(sed1[key])),
                                     set(poolchannels))
                else:
                    self.assertEqual(sed[key], vl)
                    self.assertEqual(sed1[key], vl)
        finally:
            simps2.delete()

    # test
    # \brief It tests default settings
    def test_resetPreselectedComponents_2wds2_dvnorunning_pe(self):
        fun = sys._getframe().f_code.co_name
        print("Run: %s.%s() " % (self.__class__.__name__, fun))
        val = {"ConfigDevice": self._cf.dp.name(),
               "WriterDevice": self._wr.dp.name(),
               "Door": 'doortestp09/testts/t1r228',
               "MntGrp": 'nxsmntgrp'}
        simps2 = TestServerSetUp.TestServerSetUp(
            "ttestp09/testts/t2r228", "S2")
        try:
            simps2.setUp()

            # db = tango.Database()
            self._ms.dps[list(self._ms.ms.keys())[0]].Init()

            # channelerrors = []
            poolchannels = []
            componentgroup = dict((k, None) for k in self.specps.keys())
            datasourcegroup = dict((k, None) for k in self.spedss.keys())

            cps = dict(self.smycps)
            cps.update(self.smycps2)
            cps.update(self.specps)
            dss = dict(self.smydss)
            dss.update(self.smydss2)
            dss.update(self.spedss)

            self._cf.dp.SetCommandVariable(["CPDICT", json.dumps(cps)])
            self._cf.dp.SetCommandVariable(["DSDICT", json.dumps(dss)])

            rs = self.openRecSelector()
            self.setProp(rs, "defaultPreselectedComponents",
                         list(componentgroup.keys()))
            rs.configDevice = val["ConfigDevice"]
            rs.door = val["Door"]
            rs.mntGrp = val["MntGrp"]
            rs.writerDevice = val["WriterDevice"]

            self._ms.dps[list(self._ms.ms.keys())[0]].Init()

            cnf = json.loads(rs.profileConfiguration)
            cnf["Timer"] = '[]'
            cnf["PreselectingDataSources"] = json.dumps(poolchannels)
            cnf["DataSourcePreselection"] = json.dumps(datasourcegroup)
            rs.profileConfiguration = json.dumps(cnf)
            self.dump(rs)
            sed1 = json.loads(self._cf.dp.selections([val["MntGrp"]])[0])
            rs.resetPreselectedComponents()
            res = self.value(rs, "ComponentPreselection")
            resd = self.value(rs, "DataSourcePreselection")
            pds = self.value(rs, "PreselectingDataSources")
            self.compareToDump(
                rs, ["ComponentPreselection",
                     "DataSourcePreselection",
                     "PreselectingDataSources"])

            self.assertEqual(
                set(json.loads(self.getDump("PreselectingDataSources"))),
                set(json.loads(pds)))
            self.myAssertDict(json.loads(resd), {})

            self.myAssertDict(json.loads(res), {
                u'pyeval1a': True, u'pyeval2a': True, u'pyeval2c': True,
                u'pyeval2b': True, u'pyeval2': True, u'pyeval0': True,
                u'pyeval1': True})
            self.assertTrue(not rs.descriptionErrors)

            # res2 = json.loads(self._cf.dp.GetCommandVariable("VARS"))
            self.assertTrue(val["MntGrp"] in self._cf.dp.availableSelections())
            sed = json.loads(self._cf.dp.selections([val["MntGrp"]])[0])
            self.assertEqual(len(list(sed.keys())), len(self._keys))
            for key, vl in self._keys:
                self.assertTrue(key in sed.keys())
                if key in val:
                    self.assertEqual(sed[key], val[key])
                    self.assertEqual(sed1[key], val[key])
                elif key == 'DataSourcePreselection':
                    self.assertEqual(set(json.loads(sed[key])),
                                     set(json.loads(resd)))
                elif key == 'ComponentPreselection':
                    self.myAssertDict(json.loads(sed[key]), json.loads(res))
                    self.assertNotEqual(sed1[key], res)
                elif key == 'PreselectingDataSources':
                    self.assertEqual(set(json.loads(sed[key])),
                                     set(poolchannels))
                    self.assertEqual(set(json.loads(sed1[key])),
                                     set(poolchannels))
                else:
                    self.assertEqual(sed[key], vl)
                    self.assertEqual(sed1[key], vl)
        finally:
            simps2.tearDown()

    # test
    # \brief It tests default settings
    def test_resetPreselectedComponents_2wds2_dvnorunning_pe_true(self):
        fun = sys._getframe().f_code.co_name
        print("Run: %s.%s() " % (self.__class__.__name__, fun))
        val = {"ConfigDevice": self._cf.dp.name(),
               "WriterDevice": self._wr.dp.name(),
               "Door": 'doortestp09/testts/t1r228',
               "MntGrp": 'nxsmntgrp'}
        simps2 = TestServerSetUp.TestServerSetUp(
            "ttestp09/testts/t2r228", "S2")
        try:
            simps2.setUp()

            # db = tango.Database()
            self._ms.dps[list(self._ms.ms.keys())[0]].Init()

            # channelerrors = []
            poolchannels = []
            componentgroup = dict((k, True) for k in self.specps.keys())
            datasourcegroup = dict((k, True) for k in self.spedss.keys())

            cps = dict(self.smycps)
            cps.update(self.smycps2)
            cps.update(self.specps)
            dss = dict(self.smydss)
            dss.update(self.smydss2)
            dss.update(self.spedss)

            self._cf.dp.SetCommandVariable(["CPDICT", json.dumps(cps)])
            self._cf.dp.SetCommandVariable(["DSDICT", json.dumps(dss)])

            rs = self.openRecSelector()
            self.setProp(rs, "defaultPreselectedComponents",
                         list(componentgroup.keys()))
            rs.configDevice = val["ConfigDevice"]
            rs.door = val["Door"]
            rs.mntGrp = val["MntGrp"]
            rs.writerDevice = val["WriterDevice"]

            self._ms.dps[list(self._ms.ms.keys())[0]].Init()

            cnf = json.loads(rs.profileConfiguration)
            cnf["Timer"] = '[]'
            cnf["PreselectingDataSources"] = json.dumps(poolchannels)
            cnf["DataSourcePreselection"] = json.dumps(datasourcegroup)
            rs.profileConfiguration = json.dumps(cnf)
            self.dump(rs)
            sed1 = json.loads(self._cf.dp.selections([val["MntGrp"]])[0])
            rs.resetPreselectedComponents()
            res = self.value(rs, "ComponentPreselection")
            resd = self.value(rs, "DataSourcePreselection")
            pds = self.value(rs, "PreselectingDataSources")
            self.compareToDump(
                rs, ["ComponentPreselection",
                     "DataSourcePreselection",
                     "PreselectingDataSources"])

            self.assertEqual(
                set(json.loads(self.getDump("PreselectingDataSources"))),
                set(json.loads(pds)))
            self.myAssertDict(json.loads(resd), {})

            self.myAssertDict(json.loads(res), {
                u'pyeval1a': True, u'pyeval2a': True, u'pyeval2c': True,
                u'pyeval2b': True, u'pyeval2': True, u'pyeval0': True,
                u'pyeval1': True})
            self.assertTrue(not rs.descriptionErrors)

            # res2 = json.loads(self._cf.dp.GetCommandVariable("VARS"))
            self.assertTrue(val["MntGrp"] in self._cf.dp.availableSelections())
            sed = json.loads(self._cf.dp.selections([val["MntGrp"]])[0])
            self.assertEqual(len(list(sed.keys())), len(self._keys))
            for key, vl in self._keys:
                self.assertTrue(key in sed.keys())
                if key in val:
                    self.assertEqual(sed[key], val[key])
                    self.assertEqual(sed1[key], val[key])
                elif key == 'DataSourcePreselection':
                    self.assertEqual(set(json.loads(sed[key])),
                                     set(json.loads(resd)))
                elif key == 'ComponentPreselection':
                    self.myAssertDict(json.loads(sed[key]), json.loads(res))
                    self.assertNotEqual(sed1[key], res)
                elif key == 'PreselectingDataSources':
                    self.assertEqual(set(json.loads(sed[key])),
                                     set(poolchannels))
                    self.assertEqual(set(json.loads(sed1[key])),
                                     set(poolchannels))
                else:
                    self.assertEqual(sed[key], vl)
                    self.assertEqual(sed1[key], vl)
        finally:
            simps2.tearDown()

    # test
    # \brief It tests default settings
    def test_resetPreselectedComponents_2wds2_dvnorunning_pe_false(self):
        fun = sys._getframe().f_code.co_name
        print("Run: %s.%s() " % (self.__class__.__name__, fun))
        val = {"ConfigDevice": self._cf.dp.name(),
               "WriterDevice": self._wr.dp.name(),
               "Door": 'doortestp09/testts/t1r228',
               "MntGrp": 'nxsmntgrp'}
        simps2 = TestServerSetUp.TestServerSetUp(
            "ttestp09/testts/t2r228", "S2")
        try:
            simps2.setUp()

            # db = tango.Database()
            self._ms.dps[list(self._ms.ms.keys())[0]].Init()

            # channelerrors = []
            poolchannels = []
            componentgroup = dict((k, False) for k in self.specps.keys())
            datasourcegroup = dict((k, False) for k in self.spedss.keys())

            cps = dict(self.smycps)
            cps.update(self.smycps2)
            cps.update(self.specps)
            dss = dict(self.smydss)
            dss.update(self.smydss2)
            dss.update(self.spedss)

            self._cf.dp.SetCommandVariable(["CPDICT", json.dumps(cps)])
            self._cf.dp.SetCommandVariable(["DSDICT", json.dumps(dss)])

            rs = self.openRecSelector()
            self.setProp(rs, "defaultPreselectedComponents",
                         list(componentgroup.keys()))
            rs.configDevice = val["ConfigDevice"]
            rs.door = val["Door"]
            rs.mntGrp = val["MntGrp"]
            rs.writerDevice = val["WriterDevice"]

            self._ms.dps[list(self._ms.ms.keys())[0]].Init()

            cnf = json.loads(rs.profileConfiguration)
            cnf["Timer"] = '[]'
            cnf["PreselectingDataSources"] = json.dumps(poolchannels)
            cnf["DataSourcePreselection"] = json.dumps(datasourcegroup)
            rs.profileConfiguration = json.dumps(cnf)
            self.dump(rs)
            sed1 = json.loads(self._cf.dp.selections([val["MntGrp"]])[0])
            rs.resetPreselectedComponents()
            res = self.value(rs, "ComponentPreselection")
            resd = self.value(rs, "DataSourcePreselection")
            pds = self.value(rs, "PreselectingDataSources")
            self.compareToDump(
                rs, ["ComponentPreselection",
                     "DataSourcePreselection",
                     "PreselectingDataSources"])

            self.assertEqual(
                set(json.loads(self.getDump("PreselectingDataSources"))),
                set(json.loads(pds)))
            self.myAssertDict(json.loads(resd), {})

            self.myAssertDict(json.loads(res), {
                u'pyeval1a': True, u'pyeval2a': True, u'pyeval2c': True,
                u'pyeval2b': True, u'pyeval2': True, u'pyeval0': True,
                u'pyeval1': True})
            self.assertTrue(not rs.descriptionErrors)

            # res2 = json.loads(self._cf.dp.GetCommandVariable("VARS"))
            self.assertTrue(val["MntGrp"] in self._cf.dp.availableSelections())
            sed = json.loads(self._cf.dp.selections([val["MntGrp"]])[0])
            self.assertEqual(len(list(sed.keys())), len(self._keys))
            for key, vl in self._keys:
                self.assertTrue(key in sed.keys())
                if key in val:
                    self.assertEqual(sed[key], val[key])
                    self.assertEqual(sed1[key], val[key])
                elif key == 'DataSourcePreselection':
                    self.assertEqual(set(json.loads(sed[key])),
                                     set(json.loads(resd)))
                elif key == 'ComponentPreselection':
                    self.myAssertDict(json.loads(sed[key]), json.loads(res))
                    self.assertNotEqual(sed1[key], res)
                elif key == 'PreselectingDataSources':
                    self.assertEqual(set(json.loads(sed[key])),
                                     set(poolchannels))
                    self.assertEqual(set(json.loads(sed1[key])),
                                     set(poolchannels))
                else:
                    self.assertEqual(sed[key], vl)
                    self.assertEqual(sed1[key], vl)
        finally:
            simps2.tearDown()

    # test
    # \brief It tests default settings
    def test_resetPreselectedComponents_2wds_dvnorunning_pe_true(self):
        fun = sys._getframe().f_code.co_name
        print("Run: %s.%s() " % (self.__class__.__name__, fun))
        val = {"ConfigDevice": self._cf.dp.name(),
               "WriterDevice": self._wr.dp.name(),
               "Door": 'doortestp09/testts/t1r228',
               "MntGrp": 'nxsmntgrp'}
        simps2 = TestServerSetUp.TestServerSetUp(
            "ttestp09/testts/t2r228", "S2")
        try:
            simps2.add()

            # db = tango.Database()
            self._ms.dps[list(self._ms.ms.keys())[0]].Init()

            # channelerrors = []
            poolchannels = []
            componentgroup = dict((k, True) for k in self.specps.keys())
            datasourcegroup = dict((k, True) for k in self.spedss.keys())

            cps = dict(self.smycps)
            cps.update(self.smycps2)
            cps.update(self.specps)
            dss = dict(self.smydss)
            dss.update(self.smydss2)
            dss.update(self.spedss)

            self._cf.dp.SetCommandVariable(["CPDICT", json.dumps(cps)])
            self._cf.dp.SetCommandVariable(["DSDICT", json.dumps(dss)])

            rs = self.openRecSelector()
            self.setProp(rs, "defaultPreselectedComponents",
                         list(componentgroup.keys()))
            rs.configDevice = val["ConfigDevice"]
            rs.door = val["Door"]
            rs.mntGrp = val["MntGrp"]
            rs.writerDevice = val["WriterDevice"]

            self._ms.dps[list(self._ms.ms.keys())[0]].Init()

            cnf = json.loads(rs.profileConfiguration)
            cnf["Timer"] = '[]'
            cnf["PreselectingDataSources"] = json.dumps(poolchannels)
            cnf["DataSourcePreselection"] = json.dumps(datasourcegroup)
            rs.profileConfiguration = json.dumps(cnf)
            self.dump(rs)
            sed1 = json.loads(self._cf.dp.selections([val["MntGrp"]])[0])
            rs.resetPreselectedComponents()
            res = self.value(rs, "ComponentPreselection")
            resd = self.value(rs, "DataSourcePreselection")
            pds = self.value(rs, "PreselectingDataSources")
            self.compareToDump(
                rs, ["ComponentPreselection",
                     "DataSourcePreselection",
                     "PreselectingDataSources"])

            self.assertEqual(
                set(json.loads(self.getDump("PreselectingDataSources"))),
                set(json.loads(pds)))
            self.myAssertDict(json.loads(resd), {})

            self.myAssertDict(json.loads(res), {
                u'pyeval1a': True, u'pyeval2a': None, u'pyeval2c': None,
                u'pyeval2b': True, u'pyeval2': True, u'pyeval0': True,
                u'pyeval1': True})
            self.assertEqual(len(rs.descriptionErrors), 2)

            # res2 = json.loads(self._cf.dp.GetCommandVariable("VARS"))
            self.assertTrue(val["MntGrp"] in self._cf.dp.availableSelections())
            sed = json.loads(self._cf.dp.selections([val["MntGrp"]])[0])
            self.assertEqual(len(list(sed.keys())), len(self._keys))
            for key, vl in self._keys:
                self.assertTrue(key in sed.keys())
                if key in val:
                    self.assertEqual(sed[key], val[key])
                    self.assertEqual(sed1[key], val[key])
                elif key == 'DataSourcePreselection':
                    self.assertEqual(set(json.loads(sed[key])),
                                     set(json.loads(resd)))
                elif key == 'ComponentPreselection':
                    self.myAssertDict(json.loads(sed[key]), json.loads(res))
                    self.assertNotEqual(sed1[key], res)
                elif key == 'PreselectingDataSources':
                    self.assertEqual(set(json.loads(sed[key])),
                                     set(poolchannels))
                    self.assertEqual(set(json.loads(sed1[key])),
                                     set(poolchannels))
                else:
                    self.assertEqual(sed[key], vl)
                    self.assertEqual(sed1[key], vl)
        finally:
            simps2.delete()

    # test
    # \brief It tests default settings
    def test_resetPreselectedComponents_2wds_dvnorunning_pe_false(self):
        fun = sys._getframe().f_code.co_name
        print("Run: %s.%s() " % (self.__class__.__name__, fun))
        val = {"ConfigDevice": self._cf.dp.name(),
               "WriterDevice": self._wr.dp.name(),
               "Door": 'doortestp09/testts/t1r228',
               "MntGrp": 'nxsmntgrp'}
        simps2 = TestServerSetUp.TestServerSetUp(
            "ttestp09/testts/t2r228", "S2")
        try:
            simps2.add()

            # db = tango.Database()
            self._ms.dps[list(self._ms.ms.keys())[0]].Init()

            # channelerrors = []
            poolchannels = []
            componentgroup = dict((k, False) for k in self.specps.keys())
            datasourcegroup = dict((k, False) for k in self.spedss.keys())

            cps = dict(self.smycps)
            cps.update(self.smycps2)
            cps.update(self.specps)
            dss = dict(self.smydss)
            dss.update(self.smydss2)
            dss.update(self.spedss)

            self._cf.dp.SetCommandVariable(["CPDICT", json.dumps(cps)])
            self._cf.dp.SetCommandVariable(["DSDICT", json.dumps(dss)])

            rs = self.openRecSelector()
            self.setProp(rs, "defaultPreselectedComponents",
                         list(componentgroup.keys()))
            rs.configDevice = val["ConfigDevice"]
            rs.door = val["Door"]
            rs.mntGrp = val["MntGrp"]
            rs.writerDevice = val["WriterDevice"]

            self._ms.dps[list(self._ms.ms.keys())[0]].Init()

            cnf = json.loads(rs.profileConfiguration)
            cnf["Timer"] = '[]'
            cnf["PreselectingDataSources"] = json.dumps(poolchannels)
            cnf["DataSourcePreselection"] = json.dumps(datasourcegroup)
            rs.profileConfiguration = json.dumps(cnf)
            self.dump(rs)
            sed1 = json.loads(self._cf.dp.selections([val["MntGrp"]])[0])
            rs.resetPreselectedComponents()
            res = self.value(rs, "ComponentPreselection")
            resd = self.value(rs, "DataSourcePreselection")
            pds = self.value(rs, "PreselectingDataSources")
            self.compareToDump(
                rs, ["ComponentPreselection",
                     "DataSourcePreselection",
                     "PreselectingDataSources"])

            self.assertEqual(
                set(json.loads(self.getDump("PreselectingDataSources"))),
                set(json.loads(pds)))
            self.myAssertDict(json.loads(resd), {})

            self.myAssertDict(json.loads(res), {
                u'pyeval1a': True, u'pyeval2a': None, u'pyeval2c': None,
                u'pyeval2b': True, u'pyeval2': True, u'pyeval0': True,
                u'pyeval1': True})
            self.assertEqual(len(rs.descriptionErrors), 2)

            # res2 = json.loads(self._cf.dp.GetCommandVariable("VARS"))
            self.assertTrue(val["MntGrp"] in self._cf.dp.availableSelections())
            sed = json.loads(self._cf.dp.selections([val["MntGrp"]])[0])
            self.assertEqual(len(list(sed.keys())), len(self._keys))
            for key, vl in self._keys:
                self.assertTrue(key in sed.keys())
                if key in val:
                    self.assertEqual(sed[key], val[key])
                    self.assertEqual(sed1[key], val[key])
                elif key == 'DataSourcePreselection':
                    self.assertEqual(set(json.loads(sed[key])),
                                     set(json.loads(resd)))
                elif key == 'ComponentPreselection':
                    self.myAssertDict(json.loads(sed[key]), json.loads(res))
                    self.assertNotEqual(sed1[key], res)
                elif key == 'PreselectingDataSources':
                    self.assertEqual(set(json.loads(sed[key])),
                                     set(poolchannels))
                    self.assertEqual(set(json.loads(sed1[key])),
                                     set(poolchannels))
                else:
                    self.assertEqual(sed[key], vl)
                    self.assertEqual(sed1[key], vl)
        finally:
            simps2.delete()

    # test
    # \brief It tests default settings
    def test_resetPreselectedComponents_2wds_dvnorunning(self):
        fun = sys._getframe().f_code.co_name
        print("Run: %s.%s() " % (self.__class__.__name__, fun))
        val = {"ConfigDevice": self._cf.dp.name(),
               "WriterDevice": self._wr.dp.name(),
               "Door": 'doortestp09/testts/t1r228',
               "MntGrp": 'nxsmntgrp'}
        simps2 = TestServerSetUp.TestServerSetUp(
            "ttestp09/testts/t2r228", "S2")
        try:
            simps2.add()

            # db = tango.Database()
            self._ms.dps[list(self._ms.ms.keys())[0]].Init()

            # channelerrors = []
            poolchannels = []
            componentgroup = {
                "smycp": False, "smycp2": False, "smycp3": False,
                "s2mycp": False, "s2mycp2": False,
                "s2mycp3": False}
            datasourcegroup = {
                "scalar_uchar": False, "scalar_string": False,
                "scalar_ulong": False,
                "scalar2_uchar": False, "scalar2_string": False,
                "scalar2_ulong": False,
            }

            cps = dict(self.smycps)
            cps.update(self.smycps2)
            dss = dict(self.smydss)
            dss.update(self.smydss2)

            self._cf.dp.SetCommandVariable(["CPDICT", json.dumps(cps)])
            self._cf.dp.SetCommandVariable(["DSDICT", json.dumps(dss)])

            rs = self.openRecSelector()
            self.setProp(rs, "defaultPreselectedComponents",
                         list(componentgroup.keys()))
            rs.configDevice = val["ConfigDevice"]
            rs.door = val["Door"]
            rs.mntGrp = val["MntGrp"]
            rs.writerDevice = val["WriterDevice"]

            self._ms.dps[list(self._ms.ms.keys())[0]].Init()

            cnf = json.loads(rs.profileConfiguration)
            cnf["Timer"] = '[]'
            cnf["PreselectingDataSources"] = json.dumps(poolchannels)
            cnf["DataSourcePreselection"] = json.dumps(datasourcegroup)
            rs.profileConfiguration = json.dumps(cnf)
            self.dump(rs)
            sed1 = json.loads(self._cf.dp.selections([val["MntGrp"]])[0])
            rs.resetPreselectedComponents()
            res = self.value(rs, "ComponentPreselection")
            resd = self.value(rs, "DataSourcePreselection")
            pds = self.value(rs, "PreselectingDataSources")
            self.compareToDump(
                rs, ["ComponentPreselection",
                     "DataSourcePreselection",
                     "PreselectingDataSources"])

            self.assertEqual(
                set(json.loads(self.getDump("PreselectingDataSources"))),
                set(json.loads(pds)))
            self.myAssertDict(json.loads(resd), {})

            self.myAssertDict(json.loads(res), {
                "smycp": True, "smycp2": True, "smycp3": True,
                "s2mycp": None, "s2mycp2": None, "s2mycp3": None})
            self.assertEqual(len(rs.descriptionErrors), 3)

            # res2 = json.loads(self._cf.dp.GetCommandVariable("VARS"))
            self.assertTrue(val["MntGrp"] in self._cf.dp.availableSelections())
            sed = json.loads(self._cf.dp.selections([val["MntGrp"]])[0])
            self.assertEqual(len(list(sed.keys())), len(self._keys))
            for key, vl in self._keys:
                self.assertTrue(key in sed.keys())
                if key in val:
                    self.assertEqual(sed[key], val[key])
                    self.assertEqual(sed1[key], val[key])
                elif key == 'DataSourcePreselection':
                    self.assertEqual(set(json.loads(sed[key])),
                                     set(json.loads(resd)))
                elif key == 'ComponentPreselection':
                    self.myAssertDict(json.loads(sed[key]), json.loads(res))
                    self.assertNotEqual(sed1[key], res)
                elif key == 'PreselectingDataSources':
                    self.assertEqual(set(json.loads(sed[key])),
                                     set(poolchannels))
                    self.assertEqual(set(json.loads(sed1[key])),
                                     set(poolchannels))
                else:
                    self.assertEqual(sed[key], vl)
                    self.assertEqual(sed1[key], vl)
        finally:
            simps2.delete()

    # test
    # \brief It tests default settings
    def test_resetPreselectedComponents_2wds_dvnodef(self):
        fun = sys._getframe().f_code.co_name
        print("Run: %s.%s() " % (self.__class__.__name__, fun))
        val = {"ConfigDevice": self._cf.dp.name(),
               "WriterDevice": self._wr.dp.name(),
               "Door": 'doortestp09/testts/t1r228',
               "MntGrp": 'nxsmntgrp'}

        # db = tango.Database()
        self._ms.dps[list(self._ms.ms.keys())[0]].Init()
        # channelerrors = []
        poolchannels = []
        componentgroup = {"smycp": None, "smycp2": False, "smycp3": True,
                          "s2mycp": None, "s2mycp2": False, "s2mycp3": True}
        datasourcegroup = {
            "scalar_uchar": True, "scalar_string": None,
            "scalar_ulong": False,
            "scalar2_uchar": True, "scalar2_string": None,
            "scalar2_ulong": False,
        }
        cps = dict(self.smycps)
        cps.update(self.smycps2)
        dss = dict(self.smydss)
        dss.update(self.smydss2)

        self._cf.dp.SetCommandVariable(["CPDICT", json.dumps(cps)])
        self._cf.dp.SetCommandVariable(["DSDICT", json.dumps(dss)])
        rs = self.openRecSelector()
        self.setProp(rs, "defaultPreselectedComponents",
                     list(componentgroup.keys()))
        rs.configDevice = val["ConfigDevice"]
        rs.door = val["Door"]
        rs.mntGrp = val["MntGrp"]
        rs.writerDevice = val["WriterDevice"]

        self._ms.dps[list(self._ms.ms.keys())[0]].Init()

        cnf = json.loads(rs.profileConfiguration)
        cnf["Timer"] = '[]'
        cnf["PreselectingDataSources"] = json.dumps(poolchannels)
        cnf["DataSourcePreselection"] = json.dumps(datasourcegroup)
        rs.profileConfiguration = json.dumps(cnf)
        self.dump(rs)
        sed1 = json.loads(self._cf.dp.selections([val["MntGrp"]])[0])
        rs.resetPreselectedComponents()
        res = self.value(rs, "ComponentPreselection")
        resd = self.value(rs, "DataSourcePreselection")
        pds = self.value(rs, "PreselectingDataSources")
        self.compareToDump(
            rs, ["ComponentPreselection",
                 "DataSourcePreselection",
                 "PreselectingDataSources"])

        self.assertEqual(
            set(json.loads(self.getDump("PreselectingDataSources"))),
            set(json.loads(pds)))
        self.myAssertDict(json.loads(resd), {})

        self.myAssertDict(json.loads(res), {
            "smycp": True, "smycp2": True, "smycp3": True,
            "s2mycp": None, "s2mycp2": None, "s2mycp3": None})
        self.assertEqual(len(rs.descriptionErrors), 3)

        # res2 = json.loads(self._cf.dp.GetCommandVariable("VARS"))
        self.assertTrue(val["MntGrp"] in self._cf.dp.availableSelections())
        sed = json.loads(self._cf.dp.selections([val["MntGrp"]])[0])
        self.assertEqual(len(list(sed.keys())), len(self._keys))
        for key, vl in self._keys:
            self.assertTrue(key in sed.keys())
            if key in val:
                self.assertEqual(sed[key], val[key])
                self.assertEqual(sed1[key], val[key])
            elif key == 'ComponentPreselection':
                self.myAssertDict(json.loads(sed[key]), json.loads(res))
                self.assertNotEqual(sed1[key], res)
            elif key == 'DataSourcePreselection':
                self.assertEqual(set(json.loads(sed[key])),
                                 set(json.loads(resd)))
            elif key == 'PreselectingDataSources':
                self.assertEqual(set(json.loads(sed[key])),
                                 set(poolchannels))
                self.assertEqual(set(json.loads(sed1[key])),
                                 set(poolchannels))
            else:
                self.assertEqual(sed[key], vl)
                self.assertEqual(sed1[key], vl)

    # test
    # \brief It tests default settings
    def test_resetPreselectedComponents_2wds_nods(self):
        fun = sys._getframe().f_code.co_name
        print("Run: %s.%s() " % (self.__class__.__name__, fun))
        val = {"ConfigDevice": self._cf.dp.name(),
               "WriterDevice": self._wr.dp.name(),
               "Door": 'doortestp09/testts/t1r228',
               "MntGrp": 'nxsmntgrp'}
        simps2 = TestServerSetUp.TestServerSetUp(
            "ttestp09/testts/t2r228", "S2")
        try:
            simps2.setUp()

            # db = tango.Database()
            self._ms.dps[list(self._ms.ms.keys())[0]].Init()

            # channelerrors = []
            poolchannels = []
            componentgroup = {
                "smycp": False, "smycp2": None, "smycp3": True,
                "s2mycp": False, "s2mycp2": None, "s2mycp3": True}
            datasourcegroup = {
                "scalar_uchar": True, "scalar_string": None,
                "scalar_ulong": False,
                "scalar2_uchar": True, "scalar2_string": None,
                "scalar2_ulong": False,
            }

            cps = dict(self.smycps)
            cps.update(self.smycps2)
            dss = dict(self.smydss)
            #            dss.update(self.smydss2)

            rs = self.openRecSelector()
            self.setProp(rs, "defaultPreselectedComponents",
                         list(componentgroup.keys()))
            rs.configDevice = val["ConfigDevice"]
            rs.door = val["Door"]
            rs.mntGrp = val["MntGrp"]
            rs.writerDevice = val["WriterDevice"]

            self._ms.dps[list(self._ms.ms.keys())[0]].Init()

            self._cf.dp.SetCommandVariable(["CPDICT", json.dumps(cps)])
            self._cf.dp.SetCommandVariable(["DSDICT", json.dumps(dss)])

            cnf = json.loads(rs.profileConfiguration)
            cnf["Timer"] = '[]'
            cnf["PreselectingDataSources"] = json.dumps(poolchannels)
            cnf["DataSourcePreselection"] = json.dumps(datasourcegroup)
            rs.profileConfiguration = json.dumps(cnf)
            self.dump(rs)
            sed1 = json.loads(self._cf.dp.selections([val["MntGrp"]])[0])
            rs.resetPreselectedComponents()
            res = self.value(rs, "ComponentPreselection")
            resd = self.value(rs, "DataSourcePreselection")
            pds = self.value(rs, "PreselectingDataSources")
            self.compareToDump(
                rs, ["ComponentPreselection",
                     "DataSourcePreselection",
                     "PreselectingDataSources"])

            self.assertEqual(
                set(json.loads(self.getDump("PreselectingDataSources"))),
                set(json.loads(pds)))
            self.myAssertDict(json.loads(resd), {})

            self.myAssertDict(json.loads(res), {
                "smycp": True, "smycp2": True, "smycp3": True,
                "s2mycp": None, "s2mycp2": None, "s2mycp3": None})
            self.assertEqual(len(rs.descriptionErrors), 3)

            # res2 = json.loads(self._cf.dp.GetCommandVariable("VARS"))
            self.assertTrue(val["MntGrp"] in self._cf.dp.availableSelections())
            sed = json.loads(self._cf.dp.selections([val["MntGrp"]])[0])
            self.assertEqual(len(list(sed.keys())), len(self._keys))
            for key, vl in self._keys:
                self.assertTrue(key in sed.keys())
                if key in val:
                    self.assertEqual(sed[key], val[key])
                    self.assertEqual(sed1[key], val[key])
                elif key == 'ComponentPreselection':
                    self.myAssertDict(json.loads(sed[key]), json.loads(res))
                    self.assertNotEqual(sed1[key], res)
                elif key == 'DataSourcePreselection':
                    self.assertEqual(set(json.loads(sed[key])),
                                     set(json.loads(resd)))
                elif key == 'PreselectingDataSources':
                    self.assertEqual(set(json.loads(sed[key])),
                                     set(poolchannels))
                    self.assertEqual(set(json.loads(sed1[key])),
                                     set(poolchannels))
                else:
                    self.assertEqual(sed[key], vl)
                    self.assertEqual(sed1[key], vl)
        finally:
            simps2.tearDown()

    # test
    # \brief It tests default settings
    def test_resetPreselectedComponents_2wds_nodspool(self):
        fun = sys._getframe().f_code.co_name
        print("Run: %s.%s() " % (self.__class__.__name__, fun))
        val = {"ConfigDevice": self._cf.dp.name(),
               "WriterDevice": self._wr.dp.name(),
               "Door": 'doortestp09/testts/t1r228',
               "MntGrp": 'nxsmntgrp'}
        simps2 = TestServerSetUp.TestServerSetUp(
            "ttestp09/testts/t2r228", "S2")
        try:
            simps2.setUp()
            # db = tango.Database()
            self._ms.dps[list(self._ms.ms.keys())[0]].Init()

            poolchannels = ["scalar2_long", "spectrum2_short",
                            "scalar2_uchar", "scalar2_string"]
            componentgroup = {
                "smycp": None, "smycp2": False, "smycp3": True,
                "s2mycp": None, "s2mycp2": False, "s2mycp3": False}
            datasourcegroup = {
                "scalar_uchar": True, "scalar_string": None,
                "scalar_ulong": False,
                "scalar2_uchar": True, "scalar2_string": None,
                "scalar2_ulong": False,
            }

            cps = dict(self.smycps)
            cps.update(self.smycps2)
            dss = dict(self.smydss)
#            dss.update(self.smydss2)

            self._cf.dp.SetCommandVariable(["CPDICT", json.dumps(cps)])
            self._cf.dp.SetCommandVariable(["DSDICT", json.dumps(dss)])

            rs = self.openRecSelector()
            self.setProp(rs, "defaultPreselectedComponents",
                         list(componentgroup.keys()))
            rs.configDevice = val["ConfigDevice"]
            rs.door = val["Door"]
            rs.mntGrp = val["MntGrp"]
            rs.writerDevice = val["WriterDevice"]

            self._ms.dps[list(self._ms.ms.keys())[0]].Init()

            cnf = json.loads(rs.profileConfiguration)
            cnf["Timer"] = '[]'
            cnf["PreselectingDataSources"] = json.dumps(poolchannels)
            cnf["DataSourcePreselection"] = json.dumps(datasourcegroup)
            rs.profileConfiguration = json.dumps(cnf)
            self.dump(rs)
            sed1 = json.loads(self._cf.dp.selections([val["MntGrp"]])[0])
            rs.resetPreselectedComponents()
            res = self.value(rs, "ComponentPreselection")
            resd = self.value(rs, "DataSourcePreselection")
            pds = self.value(rs, "PreselectingDataSources")
            self.compareToDump(
                rs, ["ComponentPreselection",
                     "DataSourcePreselection",
                     "PreselectingDataSources"])

            self.assertEqual(
                set(json.loads(self.getDump("PreselectingDataSources"))),
                set(json.loads(pds)))
            self.myAssertDict(json.loads(resd), {})

            # print res
            self.myAssertDict(json.loads(res), {
                "smycp": True, "smycp2": True, "smycp3": True,
                "s2mycp": None, "s2mycp2": None, "s2mycp3": None})
            self.assertEqual(len(rs.descriptionErrors), 3)
            # print "DES", rs.descriptionErrors

            # res2 = json.loads(self._cf.dp.GetCommandVariable("VARS"))
            self.assertTrue(val["MntGrp"] in self._cf.dp.availableSelections())
            sed = json.loads(self._cf.dp.selections([val["MntGrp"]])[0])
            self.assertEqual(len(list(sed.keys())), len(self._keys))
            for key, vl in self._keys:
                self.assertTrue(key in sed.keys())
                self.assertTrue(key in sed1.keys())
                if key in val:
                    self.assertEqual(sed[key], val[key])
                elif key == 'DataSourcePreselection':
                    self.assertEqual(set(json.loads(sed[key])),
                                     set(json.loads(resd)))
                elif key == 'ComponentPreselection':
                    self.myAssertDict(json.loads(sed[key]), json.loads(res))
                    self.assertNotEqual(sed1[key], res)
                elif key == 'PreselectingDataSources':
                    self.assertEqual(set(json.loads(sed[key])),
                                     set(poolchannels))
                    self.assertEqual(set(json.loads(sed1[key])),
                                     set(poolchannels))
                else:
                    self.assertEqual(sed[key], vl)
                    self.assertEqual(sed1[key], vl)
        finally:
            simps2.tearDown()

    # test
    # \brief It tests default settings
    def test_resetPreselectedComponents_2wds_notangods(self):
        fun = sys._getframe().f_code.co_name
        print("Run: %s.%s() " % (self.__class__.__name__, fun))
        val = {"ConfigDevice": self._cf.dp.name(),
               "WriterDevice": self._wr.dp.name(),
               "Door": 'doortestp09/testts/t1r228',
               "MntGrp": 'nxsmntgrp'}
        simps2 = TestServerSetUp.TestServerSetUp(
            "ttestp09/testts/t2r228", "S2")
        try:
            simps2.setUp()

            # db = tango.Database()
            self._ms.dps[list(self._ms.ms.keys())[0]].Init()
            poolchannels = ["scalar2_long", "spectrum2_short"]
            componentgroup = {"smycp": False, "smycp2": False,
                              "smycp3": False, "smycpnt1": False,
                              "s2mycp": False, "s2mycp2": False,
                              "s2mycp3": False}
            datasourcegroup = {
                "scalar_uchar": True, "scalar_string": None,
                "scalar_ulong": False,
                "ann3": None,
                "scalar2_uchar": True, "scalar2_string": None,
                "scalar2_ulong": False,
            }

            cps = dict(self.smycps)
            cps.update(self.smycps2)
            dss = dict(self.smydss)
            dss.update(self.smydss2)

            self._cf.dp.SetCommandVariable(["CPDICT", json.dumps(cps)])
            self._cf.dp.SetCommandVariable(["DSDICT", json.dumps(dss)])

            rs = self.openRecSelector()
            self.setProp(rs, "defaultPreselectedComponents",
                         list(componentgroup.keys()))
            rs.configDevice = val["ConfigDevice"]
            rs.door = val["Door"]
            rs.mntGrp = val["MntGrp"]
            rs.writerDevice = val["WriterDevice"]

            self._ms.dps[list(self._ms.ms.keys())[0]].Init()

            cnf = json.loads(rs.profileConfiguration)
            cnf["Timer"] = '[]'
            cnf["PreselectingDataSources"] = json.dumps(poolchannels)
            cnf["DataSourcePreselection"] = json.dumps(datasourcegroup)
            rs.profileConfiguration = json.dumps(cnf)
            self.dump(rs)
            sed1 = json.loads(self._cf.dp.selections([val["MntGrp"]])[0])
            rs.resetPreselectedComponents()
            res = self.value(rs, "ComponentPreselection")
            resd = self.value(rs, "DataSourcePreselection")
            pds = self.value(rs, "PreselectingDataSources")
            self.compareToDump(
                rs, ["ComponentPreselection",
                     "DataSourcePreselection",
                     "PreselectingDataSources"])

            self.assertEqual(
                set(json.loads(self.getDump("PreselectingDataSources"))),
                set(json.loads(pds)))

            self.myAssertDict(json.loads(resd), {})

            self.myAssertDict(json.loads(res), {
                "smycp": True, "smycp2": True, "smycp3": True,
                "s2mycp": True, "s2mycp2": True, "s2mycp3": True,
                "smycpnt1": True})
            self.assertTrue(not rs.descriptionErrors)

    #        # print self._cf.dp.GetCommandVariable("COMMANDS")
            # res2 = json.loads(self._cf.dp.GetCommandVariable("VARS"))
            self.assertTrue(val["MntGrp"] in self._cf.dp.availableSelections())
            sed = json.loads(self._cf.dp.selections([val["MntGrp"]])[0])
            self.assertEqual(len(list(sed.keys())), len(self._keys))
            for key, vl in self._keys:
                self.assertTrue(key in sed.keys())
                if key in val:
                    self.assertEqual(sed[key], val[key])
                    self.assertEqual(sed1[key], val[key])
                elif key == 'ComponentPreselection':
                    self.myAssertDict(json.loads(sed[key]), json.loads(res))
                    self.assertNotEqual(sed1[key], res)
                elif key == 'DataSourcePreselection':
                    self.assertEqual(set(json.loads(sed[key])),
                                     set(json.loads(resd)))
                elif key == 'PreselectingDataSources':
                    self.assertEqual(set(json.loads(sed[key])),
                                     set(poolchannels))
                    self.assertEqual(set(json.loads(sed1[key])),
                                     set(poolchannels))
                else:
                    self.assertEqual(sed[key], vl)
                    self.assertEqual(sed1[key], vl)
        finally:
            simps2.tearDown()

    # test
    # \brief It tests default settings
    def test_resetPreselectedComponents_2wds_notangodsnopool(self):
        fun = sys._getframe().f_code.co_name
        print("Run: %s.%s() " % (self.__class__.__name__, fun))
        val = {"ConfigDevice": self._cf.dp.name(),
               "WriterDevice": self._wr.dp.name(),
               "Door": 'doortestp09/testts/t1r228',
               "MntGrp": 'nxsmntgrp'}
        simps2 = TestServerSetUp.TestServerSetUp(
            "ttestp09/testts/t2r228", "S2")
        try:
            simps2.setUp()

            # db = tango.Database()
            self._ms.dps[list(self._ms.ms.keys())[0]].Init()

            poolchannels = ["scalar2_long", "spectrum2_short", "client_long"]
            componentgroup = {"smycp": None, "smycp2": True,
                              "smycp3": None, "smycpnt1": None,
                              "s2mycp": None, "s2mycp2": True,
                              "s2mycp3": False}
            datasourcegroup = {
                "scalar_uchar": True, "scalar_string": None,
                "scalar_ulong": False,
                "ann3": None,
                "scalar2_uchar": True, "scalar2_string": None,
                "scalar2_ulong": False,
            }

            cps = dict(self.smycps)
            cps.update(self.smycps2)
            dss = dict(self.smydss)
            dss.update(self.smydss2)
            dss.update(self.mydss)
            rs = self.openRecSelector()

            self.setProp(rs, "defaultPreselectedComponents",
                         list(componentgroup.keys()))
            rs.configDevice = val["ConfigDevice"]
            rs.door = val["Door"]
            rs.mntGrp = val["MntGrp"]
            rs.writerDevice = val["WriterDevice"]

            self._ms.dps[list(self._ms.ms.keys())[0]].Init()

            self._cf.dp.SetCommandVariable(["CPDICT", json.dumps(cps)])
            self._cf.dp.SetCommandVariable(["DSDICT", json.dumps(dss)])

            cnf = json.loads(rs.profileConfiguration)
            cnf["Timer"] = '[]'
            cnf["PreselectingDataSources"] = json.dumps(poolchannels)
            cnf["DataSourcePreselection"] = json.dumps(datasourcegroup)
            rs.profileConfiguration = json.dumps(cnf)
            self.dump(rs)
            sed1 = json.loads(self._cf.dp.selections([val["MntGrp"]])[0])
            rs.resetPreselectedComponents()
            res = self.value(rs, "ComponentPreselection")
            resd = self.value(rs, "DataSourcePreselection")
            pds = self.value(rs, "PreselectingDataSources")
            self.compareToDump(
                rs, ["ComponentPreselection",
                     "DataSourcePreselection",
                     "PreselectingDataSources"])

            self.assertEqual(
                set(json.loads(self.getDump("PreselectingDataSources"))),
                set(json.loads(pds)))
            self.myAssertDict(json.loads(resd), {})

            self.myAssertDict(json.loads(res), {
                "smycp": True, "smycp2": True, "smycp3": True,
                "s2mycp": True, "s2mycp2": True, "s2mycp3": True,
                "smycpnt1": None})
            self.assertEqual(len(rs.descriptionErrors), 1)

    #        print self._cf.dp.GetCommandVariable("COMMANDS")
            # res2 = json.loads(self._cf.dp.GetCommandVariable("VARS"))
            self.assertTrue(val["MntGrp"] in self._cf.dp.availableSelections())
            sed = json.loads(self._cf.dp.selections([val["MntGrp"]])[0])
            self.assertEqual(len(list(sed.keys())), len(self._keys))
            for key, vl in self._keys:
                self.assertTrue(key in sed.keys())
                if key in val:
                    self.assertEqual(sed[key], val[key])
                    self.assertEqual(sed1[key], val[key])
                elif key == 'ComponentPreselection':
                    self.myAssertDict(json.loads(sed[key]), json.loads(res))
                    self.assertNotEqual(sed1[key], res)
                elif key == 'DataSourcePreselection':
                    self.assertEqual(set(json.loads(sed[key])),
                                     set(json.loads(resd)))
                elif key == 'PreselectingDataSources':
                    self.assertEqual(set(json.loads(sed[key])),
                                     set(poolchannels))
                    self.assertEqual(set(json.loads(sed1[key])),
                                     set(poolchannels))
                else:
                    self.assertEqual(sed[key], vl)
                    self.assertEqual(sed1[key], vl)
        finally:
            simps2.tearDown()

    # test
    # \brief It tests default settings
    def test_resetPreselectedComponents_2wds_notangodsnopool_false(self):
        fun = sys._getframe().f_code.co_name
        print("Run: %s.%s() " % (self.__class__.__name__, fun))
        val = {"ConfigDevice": self._cf.dp.name(),
               "WriterDevice": self._wr.dp.name(),
               "Door": 'doortestp09/testts/t1r228',
               "MntGrp": 'nxsmntgrp'}
        simps2 = TestServerSetUp.TestServerSetUp(
            "ttestp09/testts/t2r228", "S2")
        try:
            simps2.setUp()

            # db = tango.Database()
            self._ms.dps[list(self._ms.ms.keys())[0]].Init()

            poolchannels = ["scalar2_long", "spectrum2_short", "client_long"]
            componentgroup = {"smycp": None, "smycp2": True,
                              "smycp3": None, "smycpnt1": False,
                              "s2mycp": None, "s2mycp2": True,
                              "s2mycp3": False}
            datasourcegroup = {
                "scalar_uchar": True, "scalar_string": None,
                "scalar_ulong": False,
                "ann3": False,
                "scalar2_uchar": True, "scalar2_string": None,
                "scalar2_ulong": False,
            }

            cps = dict(self.smycps)
            cps.update(self.smycps2)
            dss = dict(self.smydss)
            dss.update(self.smydss2)
            dss.update(self.mydss)
            rs = self.openRecSelector()

            self.setProp(rs, "defaultPreselectedComponents",
                         list(componentgroup.keys()))
            rs.configDevice = val["ConfigDevice"]
            rs.door = val["Door"]
            rs.mntGrp = val["MntGrp"]
            rs.writerDevice = val["WriterDevice"]

            self._ms.dps[list(self._ms.ms.keys())[0]].Init()

            self._cf.dp.SetCommandVariable(["CPDICT", json.dumps(cps)])
            self._cf.dp.SetCommandVariable(["DSDICT", json.dumps(dss)])

            cnf = json.loads(rs.profileConfiguration)
            cnf["Timer"] = '[]'
            cnf["PreselectingDataSources"] = json.dumps(poolchannels)
            cnf["DataSourcePreselection"] = json.dumps(datasourcegroup)
            rs.profileConfiguration = json.dumps(cnf)
            self.dump(rs)
            sed1 = json.loads(self._cf.dp.selections([val["MntGrp"]])[0])
            rs.resetPreselectedComponents()
            res = self.value(rs, "ComponentPreselection")
            resd = self.value(rs, "DataSourcePreselection")
            pds = self.value(rs, "PreselectingDataSources")
            self.compareToDump(
                rs, ["ComponentPreselection",
                     "DataSourcePreselection",
                     "PreselectingDataSources"])

            self.assertEqual(
                set(json.loads(self.getDump("PreselectingDataSources"))),
                set(json.loads(pds)))
            self.myAssertDict(json.loads(resd), {})

            self.myAssertDict(json.loads(res), {
                "smycp": True, "smycp2": True, "smycp3": True,
                "s2mycp": True, "s2mycp2": True, "s2mycp3": True,
                "smycpnt1": None})
            self.assertEqual(len(rs.descriptionErrors), 1)

    #        print self._cf.dp.GetCommandVariable("COMMANDS")
            # res2 = json.loads(self._cf.dp.GetCommandVariable("VARS"))
            self.assertTrue(val["MntGrp"] in self._cf.dp.availableSelections())
            sed = json.loads(self._cf.dp.selections([val["MntGrp"]])[0])
            self.assertEqual(len(list(sed.keys())), len(self._keys))
            for key, vl in self._keys:
                self.assertTrue(key in sed.keys())
                if key in val:
                    self.assertEqual(sed[key], val[key])
                    self.assertEqual(sed1[key], val[key])
                elif key == 'ComponentPreselection':
                    self.myAssertDict(json.loads(sed[key]), json.loads(res))
                    self.assertNotEqual(sed1[key], res)
                elif key == 'DataSourcePreselection':
                    self.assertEqual(set(json.loads(sed[key])),
                                     set(json.loads(resd)))
                elif key == 'PreselectingDataSources':
                    self.assertEqual(set(json.loads(sed[key])),
                                     set(poolchannels))
                    self.assertEqual(set(json.loads(sed1[key])),
                                     set(poolchannels))
                else:
                    self.assertEqual(sed[key], vl)
                    self.assertEqual(sed1[key], vl)
        finally:
            simps2.tearDown()

    # test
    # \brief It tests default settings
    def test_resetPreselectedComponents_2wds_notangodsnopool_true(self):
        fun = sys._getframe().f_code.co_name
        print("Run: %s.%s() " % (self.__class__.__name__, fun))
        val = {"ConfigDevice": self._cf.dp.name(),
               "WriterDevice": self._wr.dp.name(),
               "Door": 'doortestp09/testts/t1r228',
               "MntGrp": 'nxsmntgrp'}
        simps2 = TestServerSetUp.TestServerSetUp(
            "ttestp09/testts/t2r228", "S2")
        try:
            simps2.setUp()

            # db = tango.Database()
            self._ms.dps[list(self._ms.ms.keys())[0]].Init()

            poolchannels = ["scalar2_long", "spectrum2_short", "client_long"]
            componentgroup = {"smycp": None, "smycp2": True,
                              "smycp3": None, "smycpnt1": True,
                              "s2mycp": None, "s2mycp2": True,
                              "s2mycp3": False}
            datasourcegroup = {
                "scalar_uchar": True, "scalar_string": None,
                "scalar_ulong": False,
                "ann3": True,
                "scalar2_uchar": True, "scalar2_string": None,
                "scalar2_ulong": False,
            }

            cps = dict(self.smycps)
            cps.update(self.smycps2)
            dss = dict(self.smydss)
            dss.update(self.smydss2)
            dss.update(self.mydss)
            rs = self.openRecSelector()

            self.setProp(rs, "defaultPreselectedComponents",
                         list(componentgroup.keys()))
            rs.configDevice = val["ConfigDevice"]
            rs.door = val["Door"]
            rs.mntGrp = val["MntGrp"]
            rs.writerDevice = val["WriterDevice"]

            self._ms.dps[list(self._ms.ms.keys())[0]].Init()

            self._cf.dp.SetCommandVariable(["CPDICT", json.dumps(cps)])
            self._cf.dp.SetCommandVariable(["DSDICT", json.dumps(dss)])

            cnf = json.loads(rs.profileConfiguration)
            cnf["Timer"] = '[]'
            cnf["PreselectingDataSources"] = json.dumps(poolchannels)
            cnf["DataSourcePreselection"] = json.dumps(datasourcegroup)
            rs.profileConfiguration = json.dumps(cnf)
            self.dump(rs)
            sed1 = json.loads(self._cf.dp.selections([val["MntGrp"]])[0])
            rs.resetPreselectedComponents()
            res = self.value(rs, "ComponentPreselection")
            resd = self.value(rs, "DataSourcePreselection")
            pds = self.value(rs, "PreselectingDataSources")
            self.compareToDump(
                rs, ["ComponentPreselection",
                     "DataSourcePreselection",
                     "PreselectingDataSources"])

            self.assertEqual(
                set(json.loads(self.getDump("PreselectingDataSources"))),
                set(json.loads(pds)))
            self.myAssertDict(json.loads(resd), {})

            self.myAssertDict(json.loads(res), {
                "smycp": True, "smycp2": True, "smycp3": True,
                "s2mycp": True, "s2mycp2": True, "s2mycp3": True,
                "smycpnt1": None})
            self.assertEqual(len(rs.descriptionErrors), 1)

    #        print self._cf.dp.GetCommandVariable("COMMANDS")
            # res2 = json.loads(self._cf.dp.GetCommandVariable("VARS"))
            self.assertTrue(val["MntGrp"] in self._cf.dp.availableSelections())
            sed = json.loads(self._cf.dp.selections([val["MntGrp"]])[0])
            self.assertEqual(len(list(sed.keys())), len(self._keys))
            for key, vl in self._keys:
                self.assertTrue(key in sed.keys())
                if key in val:
                    self.assertEqual(sed[key], val[key])
                    self.assertEqual(sed1[key], val[key])
                elif key == 'ComponentPreselection':
                    self.myAssertDict(json.loads(sed[key]), json.loads(res))
                    self.assertNotEqual(sed1[key], res)
                elif key == 'DataSourcePreselection':
                    self.assertEqual(set(json.loads(sed[key])),
                                     set(json.loads(resd)))
                elif key == 'PreselectingDataSources':
                    self.assertEqual(set(json.loads(sed[key])),
                                     set(poolchannels))
                    self.assertEqual(set(json.loads(sed1[key])),
                                     set(poolchannels))
                else:
                    self.assertEqual(sed[key], vl)
                    self.assertEqual(sed1[key], vl)
        finally:
            simps2.tearDown()

    # test
    # \brief It tests default settings
    def test_resetPreselectedComponents_2wds_notangodsnopool2(self):
        fun = sys._getframe().f_code.co_name
        print("Run: %s.%s() " % (self.__class__.__name__, fun))
        val = {"ConfigDevice": self._cf.dp.name(),
               "WriterDevice": self._wr.dp.name(),
               "Door": 'doortestp09/testts/t1r228',
               "MntGrp": 'nxsmntgrp'}
        simps2 = TestServerSetUp.TestServerSetUp(
            "ttestp09/testts/t2r228", "S2")
        try:
            simps2.setUp()

            # db = tango.Database()
            self._ms.dps[list(self._ms.ms.keys())[0]].Init()
            poolchannels = ["scalar2_long", "spectrum2_short", "client_long"]
            componentgroup = {"smycp": False, "smycp2": True,
                              "smycp3": True, "smycpnt1": None,
                              "s2mycp": True, "s2mycp2": True,
                              "s2mycp3": False}
            datasourcegroup = {
                "scalar_uchar": True, "scalar_string": None,
                "scalar_ulong": False,
                "ann3": None,
                "scalar2_uchar": True, "scalar2_string": None,
                "scalar2_ulong": False,
            }

            cps = dict(self.smycps)
            cps.update(self.smycps2)
            dss = dict(self.smydss)
            dss.update(self.smydss2)
            dss.update(self.mydss)

            self._cf.dp.SetCommandVariable(["CPDICT", json.dumps(cps)])
            self._cf.dp.SetCommandVariable(["DSDICT", json.dumps(dss)])
            rs = self.openRecSelector()
            self.setProp(rs, "defaultPreselectedComponents",
                         list(componentgroup.keys()))
            rs.configDevice = val["ConfigDevice"]
            rs.door = val["Door"]
            rs.mntGrp = val["MntGrp"]
            rs.writerDevice = val["WriterDevice"]

            self._ms.dps[list(self._ms.ms.keys())[0]].Init()

            cnf = json.loads(rs.profileConfiguration)
            cnf["Timer"] = '[]'
            cnf["PreselectingDataSources"] = json.dumps(poolchannels)
            cnf["DataSourcePreselection"] = json.dumps(datasourcegroup)
            rs.profileConfiguration = json.dumps(cnf)
            self.dump(rs)
            sed1 = json.loads(self._cf.dp.selections([val["MntGrp"]])[0])
            rs.resetPreselectedComponents()
            res = self.value(rs, "ComponentPreselection")
            resd = self.value(rs, "DataSourcePreselection")
            pds = self.value(rs, "PreselectingDataSources")
            self.compareToDump(
                rs, ["ComponentPreselection",
                     "DataSourcePreselection",
                     "PreselectingDataSources"])

            self.assertEqual(
                set(json.loads(self.getDump("PreselectingDataSources"))),
                set(json.loads(pds)))
            self.myAssertDict(json.loads(resd), {})

            self.myAssertDict(json.loads(res), {
                "smycp": True, "smycp2": True, "smycp3": True,
                "s2mycp": True, "s2mycp2": True, "s2mycp3": True,
                "smycpnt1": None})
            self.assertEqual(len(rs.descriptionErrors), 1)

    #        print self._cf.dp.GetCommandVariable("COMMANDS")
            # res2 = json.loads(self._cf.dp.GetCommandVariable("VARS"))
            self.assertTrue(val["MntGrp"] in self._cf.dp.availableSelections())
            sed = json.loads(self._cf.dp.selections([val["MntGrp"]])[0])
            self.assertEqual(len(list(sed.keys())), len(self._keys))
            for key, vl in self._keys:
                self.assertTrue(key in sed.keys())
                if key in val:
                    self.assertEqual(sed[key], val[key])
                    self.assertEqual(sed1[key], val[key])
                elif key == 'ComponentPreselection':
                    self.myAssertDict(json.loads(sed[key]), json.loads(res))
                    self.assertNotEqual(sed1[key], res)
                elif key == 'DataSourcePreselection':
                    self.assertEqual(set(json.loads(sed[key])),
                                     set(json.loads(resd)))
                elif key == 'PreselectingDataSources':
                    self.assertEqual(set(json.loads(sed[key])),
                                     set(poolchannels))
                    self.assertEqual(set(json.loads(sed1[key])),
                                     set(poolchannels))
                else:
                    self.assertEqual(sed[key], vl)
                    self.assertEqual(sed1[key], vl)
        finally:
            simps2.tearDown()

    # test
    # \brief It tests default settings
    def test_resetPreselectedComponents_2wds_notangodsnopool2_true(self):
        fun = sys._getframe().f_code.co_name
        print("Run: %s.%s() " % (self.__class__.__name__, fun))
        val = {"ConfigDevice": self._cf.dp.name(),
               "WriterDevice": self._wr.dp.name(),
               "Door": 'doortestp09/testts/t1r228',
               "MntGrp": 'nxsmntgrp'}
        simps2 = TestServerSetUp.TestServerSetUp(
            "ttestp09/testts/t2r228", "S2")
        try:
            simps2.setUp()

            # db = tango.Database()
            self._ms.dps[list(self._ms.ms.keys())[0]].Init()
            poolchannels = ["scalar2_long", "spectrum2_short", "client_long"]
            componentgroup = {"smycp": False, "smycp2": True,
                              "smycp3": True, "smycpnt1": True,
                              "s2mycp": True, "s2mycp2": True,
                              "s2mycp3": False}
            datasourcegroup = {
                "scalar_uchar": True, "scalar_string": None,
                "scalar_ulong": False,
                "ann3": True,
                "scalar2_uchar": True, "scalar2_string": None,
                "scalar2_ulong": False,
            }

            cps = dict(self.smycps)
            cps.update(self.smycps2)
            dss = dict(self.smydss)
            dss.update(self.smydss2)
            dss.update(self.mydss)

            self._cf.dp.SetCommandVariable(["CPDICT", json.dumps(cps)])
            self._cf.dp.SetCommandVariable(["DSDICT", json.dumps(dss)])
            rs = self.openRecSelector()
            self.setProp(rs, "defaultPreselectedComponents",
                         list(componentgroup.keys()))
            rs.configDevice = val["ConfigDevice"]
            rs.door = val["Door"]
            rs.mntGrp = val["MntGrp"]
            rs.writerDevice = val["WriterDevice"]

            self._ms.dps[list(self._ms.ms.keys())[0]].Init()

            cnf = json.loads(rs.profileConfiguration)
            cnf["Timer"] = '[]'
            cnf["PreselectingDataSources"] = json.dumps(poolchannels)
            cnf["DataSourcePreselection"] = json.dumps(datasourcegroup)
            rs.profileConfiguration = json.dumps(cnf)
            self.dump(rs)
            sed1 = json.loads(self._cf.dp.selections([val["MntGrp"]])[0])
            rs.resetPreselectedComponents()
            res = self.value(rs, "ComponentPreselection")
            resd = self.value(rs, "DataSourcePreselection")
            pds = self.value(rs, "PreselectingDataSources")
            self.compareToDump(
                rs, ["ComponentPreselection",
                     "DataSourcePreselection",
                     "PreselectingDataSources"])

            self.assertEqual(
                set(json.loads(self.getDump("PreselectingDataSources"))),
                set(json.loads(pds)))
            self.myAssertDict(json.loads(resd), {})

            self.myAssertDict(json.loads(res), {
                "smycp": True, "smycp2": True, "smycp3": True,
                "s2mycp": True, "s2mycp2": True, "s2mycp3": True,
                "smycpnt1": None})
            self.assertEqual(len(rs.descriptionErrors), 1)

    #        print self._cf.dp.GetCommandVariable("COMMANDS")
            # res2 = json.loads(self._cf.dp.GetCommandVariable("VARS"))
            self.assertTrue(val["MntGrp"] in self._cf.dp.availableSelections())
            sed = json.loads(self._cf.dp.selections([val["MntGrp"]])[0])
            self.assertEqual(len(list(sed.keys())), len(self._keys))
            for key, vl in self._keys:
                self.assertTrue(key in sed.keys())
                if key in val:
                    self.assertEqual(sed[key], val[key])
                    self.assertEqual(sed1[key], val[key])
                elif key == 'ComponentPreselection':
                    self.myAssertDict(json.loads(sed[key]), json.loads(res))
                    self.assertNotEqual(sed1[key], res)
                elif key == 'DataSourcePreselection':
                    self.assertEqual(set(json.loads(sed[key])),
                                     set(json.loads(resd)))
                elif key == 'PreselectingDataSources':
                    self.assertEqual(set(json.loads(sed[key])),
                                     set(poolchannels))
                    self.assertEqual(set(json.loads(sed1[key])),
                                     set(poolchannels))
                else:
                    self.assertEqual(sed[key], vl)
                    self.assertEqual(sed1[key], vl)
        finally:
            simps2.tearDown()

    # test
    # \brief It tests default settings
    def test_resetPreselectedComponents_2wds_notangodsnopool2_false(self):
        fun = sys._getframe().f_code.co_name
        print("Run: %s.%s() " % (self.__class__.__name__, fun))
        val = {"ConfigDevice": self._cf.dp.name(),
               "WriterDevice": self._wr.dp.name(),
               "Door": 'doortestp09/testts/t1r228',
               "MntGrp": 'nxsmntgrp'}
        simps2 = TestServerSetUp.TestServerSetUp(
            "ttestp09/testts/t2r228", "S2")
        try:
            simps2.setUp()

            # db = tango.Database()
            self._ms.dps[list(self._ms.ms.keys())[0]].Init()
            poolchannels = ["scalar2_long", "spectrum2_short", "client_long"]
            componentgroup = {"smycp": False, "smycp2": True,
                              "smycp3": True, "smycpnt1": False,
                              "s2mycp": True, "s2mycp2": True,
                              "s2mycp3": False}
            datasourcegroup = {
                "scalar_uchar": True, "scalar_string": None,
                "scalar_ulong": False,
                "ann3": False,
                "scalar2_uchar": True, "scalar2_string": None,
                "scalar2_ulong": False,
            }

            cps = dict(self.smycps)
            cps.update(self.smycps2)
            dss = dict(self.smydss)
            dss.update(self.smydss2)
            dss.update(self.mydss)

            self._cf.dp.SetCommandVariable(["CPDICT", json.dumps(cps)])
            self._cf.dp.SetCommandVariable(["DSDICT", json.dumps(dss)])
            rs = self.openRecSelector()
            self.setProp(rs, "defaultPreselectedComponents",
                         list(componentgroup.keys()))
            rs.configDevice = val["ConfigDevice"]
            rs.door = val["Door"]
            rs.mntGrp = val["MntGrp"]
            rs.writerDevice = val["WriterDevice"]

            self._ms.dps[list(self._ms.ms.keys())[0]].Init()

            cnf = json.loads(rs.profileConfiguration)
            cnf["Timer"] = '[]'
            cnf["PreselectingDataSources"] = json.dumps(poolchannels)
            cnf["DataSourcePreselection"] = json.dumps(datasourcegroup)
            rs.profileConfiguration = json.dumps(cnf)
            self.dump(rs)
            sed1 = json.loads(self._cf.dp.selections([val["MntGrp"]])[0])
            rs.resetPreselectedComponents()
            res = self.value(rs, "ComponentPreselection")
            resd = self.value(rs, "DataSourcePreselection")
            pds = self.value(rs, "PreselectingDataSources")
            self.compareToDump(
                rs, ["ComponentPreselection",
                     "DataSourcePreselection",
                     "PreselectingDataSources"])

            self.assertEqual(
                set(json.loads(self.getDump("PreselectingDataSources"))),
                set(json.loads(pds)))
            self.myAssertDict(json.loads(resd), {})

            self.myAssertDict(json.loads(res), {
                "smycp": True, "smycp2": True, "smycp3": True,
                "s2mycp": True, "s2mycp2": True, "s2mycp3": True,
                "smycpnt1": None})
            self.assertEqual(len(rs.descriptionErrors), 1)

    #        print self._cf.dp.GetCommandVariable("COMMANDS")
            # res2 = json.loads(self._cf.dp.GetCommandVariable("VARS"))
            self.assertTrue(val["MntGrp"] in self._cf.dp.availableSelections())
            sed = json.loads(self._cf.dp.selections([val["MntGrp"]])[0])
            self.assertEqual(len(list(sed.keys())), len(self._keys))
            for key, vl in self._keys:
                self.assertTrue(key in sed.keys())
                if key in val:
                    self.assertEqual(sed[key], val[key])
                    self.assertEqual(sed1[key], val[key])
                elif key == 'ComponentPreselection':
                    self.myAssertDict(json.loads(sed[key]), json.loads(res))
                    self.assertNotEqual(sed1[key], res)
                elif key == 'DataSourcePreselection':
                    self.assertEqual(set(json.loads(sed[key])),
                                     set(json.loads(resd)))
                elif key == 'PreselectingDataSources':
                    self.assertEqual(set(json.loads(sed[key])),
                                     set(poolchannels))
                    self.assertEqual(set(json.loads(sed1[key])),
                                     set(poolchannels))
                else:
                    self.assertEqual(sed[key], vl)
                    self.assertEqual(sed1[key], vl)
        finally:
            simps2.tearDown()

    # test
    # \brief It tests default settings
    def test_resetPreselectedComponents_2wds_notangods2(self):
        fun = sys._getframe().f_code.co_name
        print("Run: %s.%s() " % (self.__class__.__name__, fun))
        val = {"ConfigDevice": self._cf.dp.name(),
               "WriterDevice": self._wr.dp.name(),
               "Door": 'doortestp09/testts/t1r228',
               "MntGrp": 'nxsmntgrp'}
        simps2 = TestServerSetUp.TestServerSetUp(
            "ttestp09/testts/t2r228", "S2")

        arr = [
            {"name": "client_long",
             "full_name": "ttestp09/testts/t1r228/Value"},
            {"name": "client_short",
             "full_name": "ttestp09/testts/t1r228/Value"},
        ]

        try:
            simps2.setUp()

            db = tango.Database()
            db.put_device_property(list(self._ms.ms.keys())[0],
                                   {'PoolNames': self._pool.dp.name()})
            self._ms.dps[list(self._ms.ms.keys())[0]].Init()
            # channelerrors = []
            poolchannels = []
            componentgroup = {"smycp": False, "smycp2": None,
                              "smycp3": True, "smycpnt1": None,
                              "s2mycp": True, "s2mycp2": False,
                              "s2mycp3": True}
            datasourcegroup = {
                "scalar_uchar": True, "scalar_string": None,
                "scalar_ulong": False,
                "ann3": None,
                "scalar2_uchar": True, "scalar2_string": None,
                "scalar2_ulong": False,
            }

            cps = dict(self.smycps)
            cps.update(self.smycps2)
            dss = dict(self.smydss)
            dss.update(self.smydss2)
            dss.update(self.mydss)

            self._cf.dp.SetCommandVariable(["CPDICT", json.dumps(cps)])
            self._cf.dp.SetCommandVariable(["DSDICT", json.dumps(dss)])

            rs = self.openRecSelector()
            self.setProp(rs, "defaultPreselectedComponents",
                         list(componentgroup.keys()))
            rs.configDevice = val["ConfigDevice"]
            rs.door = val["Door"]
            rs.mntGrp = val["MntGrp"]
            rs.writerDevice = val["WriterDevice"]

            self._ms.dps[list(self._ms.ms.keys())[0]].Init()

            pool = self._pool.dp
            pool.AcqChannelList = [json.dumps(a) for a in arr]

            cnf = json.loads(rs.profileConfiguration)
            cnf["Timer"] = '[]'
            cnf["PreselectingDataSources"] = json.dumps(poolchannels)
            cnf["DataSourcePreselection"] = json.dumps(datasourcegroup)
            rs.profileConfiguration = json.dumps(cnf)
            self.dump(rs)
            sed1 = json.loads(self._cf.dp.selections([val["MntGrp"]])[0])
            rs.resetPreselectedComponents()
            res = self.value(rs, "ComponentPreselection")
            resd = self.value(rs, "DataSourcePreselection")
            pds = self.value(rs, "PreselectingDataSources")
            self.compareToDump(
                rs, ["ComponentPreselection",
                     "DataSourcePreselection",
                     "PreselectingDataSources"])

            self.assertEqual(
                set(json.loads(self.getDump("PreselectingDataSources"))),
                set(json.loads(pds)))
            self.myAssertDict(json.loads(resd), {})

            self.myAssertDict(json.loads(res), {
                "smycp": True, "smycp2": True, "smycp3": True,
                "s2mycp": True, "s2mycp2": True, "s2mycp3": True,
                "smycpnt1": True})
            self.assertTrue(not rs.descriptionErrors)

            # res2 = json.loads(self._cf.dp.GetCommandVariable("VARS"))
            self.assertTrue(val["MntGrp"] in self._cf.dp.availableSelections())
            sed = json.loads(self._cf.dp.selections([val["MntGrp"]])[0])
            self.assertEqual(len(list(sed.keys())), len(self._keys))
            for key, vl in self._keys:
                self.assertTrue(key in sed.keys())
                if key in val:
                    self.assertEqual(sed[key], val[key])
                    self.assertEqual(sed1[key], val[key])
                elif key == 'ComponentPreselection':
                    self.myAssertDict(json.loads(sed[key]), json.loads(res))
                    self.assertNotEqual(sed1[key], res)
                elif key == 'DataSourcePreselection':
                    self.assertEqual(set(json.loads(sed[key])),
                                     set(json.loads(resd)))
                elif key == 'PreselectingDataSources':
                    self.assertEqual(set(json.loads(sed[key])),
                                     set(poolchannels))
                    self.assertEqual(set(json.loads(sed1[key])),
                                     set(poolchannels))
                else:
                    self.assertEqual(sed[key], vl)
                    self.assertEqual(sed1[key], vl)
        finally:
            simps2.tearDown()

    # test
    # \brief It tests default settings
    def test_resetPreselectedComponents_2wds_notangods2_bl(self):
        fun = sys._getframe().f_code.co_name
        print("Run: %s.%s() " % (self.__class__.__name__, fun))
        val = {"ConfigDevice": self._cf.dp.name(),
               "WriterDevice": self._wr.dp.name(),
               "Door": 'doortestp09/testts/t1r228',
               "MntGrp": 'nxsmntgrp'}
        simps2 = TestServerSetUp.TestServerSetUp(
            "ttestp09/testts/t2r228", "S2")

        arr = [
            {"name": "client_long",
             "full_name": "ttestp09/testts/t1r228/Value"},
            {"name": "client_short",
             "full_name": "ttestp09/testts/t1r228/Value"},
        ]

        try:
            simps2.setUp()

            db = tango.Database()
            db.put_device_property(list(self._ms.ms.keys())[0],
                                   {'PoolNames': self._pool.dp.name()})
            self._ms.dps[list(self._ms.ms.keys())[0]].Init()
            # channelerrors = []
            poolchannels = []
            componentgroup = {"smycp": False, "smycp2": False,
                              "smycp3": False, "smycpnt1": False,
                              "s2mycp": False, "s2mycp2": False,
                              "s2mycp3": False}

            cps = dict(self.smycps)
            cps.update(self.smycps2)
            dss = dict(self.smydss)
            dss.update(self.smydss2)

            self._cf.dp.SetCommandVariable(["CPDICT", json.dumps(cps)])
            self._cf.dp.SetCommandVariable(["DSDICT", json.dumps(dss)])

            rs = self.openRecSelector()
            self.setProp(rs, "poolBlacklist",
                         [self._pool.dp.name()])
            self.setProp(rs, "defaultPreselectedComponents",
                         list(componentgroup.keys()))
            rs.configDevice = val["ConfigDevice"]
            rs.door = val["Door"]
            rs.mntGrp = val["MntGrp"]
            rs.writerDevice = val["WriterDevice"]

            self._ms.dps[list(self._ms.ms.keys())[0]].Init()

            pool = self._pool.dp
            pool.AcqChannelList = [json.dumps(a) for a in arr]

            cnf = json.loads(rs.profileConfiguration)
            cnf["PreselectingDataSources"] = json.dumps(poolchannels)
            cnf["Timer"] = '[]'
            rs.profileConfiguration = json.dumps(cnf)
            self.dump(rs)
            sed1 = json.loads(self._cf.dp.selections([val["MntGrp"]])[0])
            rs.resetPreselectedComponents()
            res = self.value(rs, "ComponentPreselection")
            pds = self.value(rs, "PreselectingDataSources")
            self.compareToDump(
                rs, ["ComponentPreselection",
                     "DataSourcePreselection",
                     "PreselectingDataSources"])

            self.assertEqual(
                set(json.loads(self.getDump("PreselectingDataSources"))),
                set(json.loads(pds)))

            self.myAssertDict(json.loads(res), {
                "smycp": True, "smycp2": True, "smycp3": True,
                "s2mycp": True, "s2mycp2": True, "s2mycp3": True,
                "smycpnt1": True})
            self.assertTrue(not rs.descriptionErrors)

            # res2 = json.loads(self._cf.dp.GetCommandVariable("VARS"))
            self.assertTrue(val["MntGrp"] in self._cf.dp.availableSelections())
            sed = json.loads(self._cf.dp.selections([val["MntGrp"]])[0])
            self.assertEqual(len(list(sed.keys())), len(self._keys))
            for key, vl in self._keys:
                self.assertTrue(key in sed.keys())
                if key in val:
                    self.assertEqual(sed[key], val[key])
                    self.assertEqual(sed1[key], val[key])
                elif key == 'ComponentPreselection':
                    self.myAssertDict(json.loads(sed[key]), json.loads(res))
                    self.assertNotEqual(sed1[key], res)
                elif key == 'PreselectingDataSources':
                    self.assertEqual(set(json.loads(sed[key])),
                                     set(poolchannels))
                    self.assertEqual(set(json.loads(sed1[key])),
                                     set(poolchannels))
                else:
                    self.assertEqual(sed[key], vl)
                    self.assertEqual(sed1[key], vl)
        finally:
            simps2.tearDown()

    # test
    # \brief It tests default settings
    def test_resetPreselectedComponents_2wds_notangodspool_error(self):
        fun = sys._getframe().f_code.co_name
        print("Run: %s.%s() " % (self.__class__.__name__, fun))
        val = {"ConfigDevice": self._cf.dp.name(),
               "WriterDevice": self._wr.dp.name(),
               "Door": 'doortestp09/testts/t1r228',
               "MntGrp": 'nxsmntgrp'}
        simps2 = TestServerSetUp.TestServerSetUp(
            "ttestp09/testts/t2r228", "S2")

        arr = [
            {"name": "client_long",
             "full_name": "ttestp09/testts/t1r228/Value"},
            {"name": "client_short",
             "full_name": "ttestp09/testts/t1r228/Value"},
        ]

        try:
            simps2.setUp()

            db = tango.Database()
            db.put_device_property(list(self._ms.ms.keys())[0],
                                   {'PoolNames': self._pool.dp.name()})
            self._ms.dps[list(self._ms.ms.keys())[0]].Init()

            # channelerrors = []
            poolchannels = ["scalar2_long", "spectrum2_short", "client_long",
                            "client_short"]
            componentgroup = {
                "smycp": False, "smycp2": False, "smycp3": False,
                "smycpnt1": False,
                "s2mycp": False, "s2mycp2": False, "s2mycp3": False
            }

            cps = dict(self.smycps)
            cps.update(self.smycps2)
            dss = dict(self.smydss)
            dss.update(self.smydss2)

            self._cf.dp.SetCommandVariable(["CPDICT", json.dumps(cps)])
            self._cf.dp.SetCommandVariable(["DSDICT", json.dumps(dss)])
            rs = self.openRecSelector()
            self.setProp(rs, "defaultPreselectedComponents",
                         list(componentgroup.keys()))
            rs.configDevice = val["ConfigDevice"]
            rs.door = val["Door"]
            rs.mntGrp = val["MntGrp"]
            rs.writerDevice = val["WriterDevice"]

            self._ms.dps[list(self._ms.ms.keys())[0]].Init()

            pool = self._pool.dp
            pool.AcqChannelList = [json.dumps(a) for a in arr]

            cnf = json.loads(rs.profileConfiguration)
            cnf["Timer"] = '[]'
            cnf["PreselectingDataSources"] = json.dumps(poolchannels)
            rs.profileConfiguration = json.dumps(cnf)
            self.dump(rs)
            sed1 = json.loads(self._cf.dp.selections([val["MntGrp"]])[0])
            rs.resetPreselectedComponents()
            res = self.value(rs, "ComponentPreselection")
            self.compareToDump(rs, ["ComponentPreselection",
                                    "PreselectingDataSources"])

            pds = self.value(rs, "PreselectingDataSources")
            self.assertEqual(
                set(json.loads(self.getDump("PreselectingDataSources"))),
                set(json.loads(pds)))

            self.myAssertDict(json.loads(res), {
                "smycp": True, "smycp2": True, "smycp3": True,
                "s2mycp": True, "s2mycp2": True, "s2mycp3": True,
                "smycpnt1": None})
            self.assertEqual(len(rs.descriptionErrors), 1)

    #        print self._cf.dp.GetCommandVariable("COMMANDS")
            # res2 = json.loads(self._cf.dp.GetCommandVariable("VARS"))
            self.assertTrue(val["MntGrp"] in self._cf.dp.availableSelections())
            sed = json.loads(self._cf.dp.selections([val["MntGrp"]])[0])
            self.assertEqual(len(list(sed.keys())), len(self._keys))
            for key, vl in self._keys:
                self.assertTrue(key in sed.keys())
                if key in val:
                    self.assertEqual(sed[key], val[key])
                    self.assertEqual(sed1[key], val[key])
                elif key == 'ComponentPreselection':
                    self.myAssertDict(json.loads(sed[key]), json.loads(res))
                    self.assertNotEqual(sed1[key], res)
                elif key == 'PreselectingDataSources':
                    self.assertEqual(set(json.loads(sed[key])),
                                     set(poolchannels))
                    self.assertEqual(set(json.loads(sed1[key])),
                                     set(poolchannels))
                else:
                    self.assertEqual(sed[key], vl)
                    self.assertEqual(sed1[key], vl)
        finally:
            simps2.tearDown()

    # test
    # \brief It tests default settings
    def test_resetPreselectedComponents_2wds_notangodspool(self):
        fun = sys._getframe().f_code.co_name
        print("Run: %s.%s() " % (self.__class__.__name__, fun))
        val = {"ConfigDevice": self._cf.dp.name(),
               "WriterDevice": self._wr.dp.name(),
               "Door": 'doortestp09/testts/t1r228',
               "MntGrp": 'nxsmntgrp'}
        simps2 = TestServerSetUp.TestServerSetUp(
            "ttestp09/testts/t2r228", "S2")

        arr = [
            {"name": "client_short", "full_name": "ttestp09/testts/t1r228"},
        ]

        try:
            simps2.setUp()

            db = tango.Database()
            db.put_device_property(list(self._ms.ms.keys())[0],
                                   {'PoolNames': self._pool.dp.name()})
            self._ms.dps[list(self._ms.ms.keys())[0]].Init()

            # channelerrors = []

            poolchannels = ["scalar2_long", "spectrum2_short", "client_short"]
            componentgroup = {
                "smycp": False, "smycp2": False, "smycp3": False,
                "smycpnt1": False,
                "s2mycp": False, "s2mycp2": False, "s2mycp3": False
            }

            cps = dict(self.smycps)
            cps.update(self.smycps2)
            dss = dict(self.smydss)
            dss.update(self.smydss2)

            self._cf.dp.SetCommandVariable(["CPDICT", json.dumps(cps)])
            self._cf.dp.SetCommandVariable(["DSDICT", json.dumps(dss)])
            rs = self.openRecSelector()
            self.setProp(rs, "defaultPreselectedComponents",
                         list(componentgroup.keys()))
            rs.configDevice = val["ConfigDevice"]
            rs.door = val["Door"]
            rs.mntGrp = val["MntGrp"]
            rs.writerDevice = val["WriterDevice"]

            self._ms.dps[list(self._ms.ms.keys())[0]].Init()

            pool = self._pool.dp
            pool.AcqChannelList = [json.dumps(a) for a in arr]

            self._simps.dp.ChangeValueType("ScalarShort")
            self._simps.dp.Value = 43

            cnf = json.loads(rs.profileConfiguration)
            cnf["PreselectingDataSources"] = json.dumps(poolchannels)
            cnf["Timer"] = '[]'
            rs.profileConfiguration = json.dumps(cnf)
            self.dump(rs)
            sed1 = json.loads(self._cf.dp.selections([val["MntGrp"]])[0])
            rs.resetPreselectedComponents()
            res = self.value(rs, "ComponentPreselection")
            pds = self.value(rs, "PreselectingDataSources")
            self.compareToDump(
                rs, ["ComponentPreselection",
                     "DataSourcePreselection",
                     "PreselectingDataSources"])

            self.assertEqual(
                set(json.loads(self.getDump("PreselectingDataSources"))),
                set(json.loads(pds)))

            self.myAssertDict(json.loads(res), {
                "smycp": True, "smycp2": True, "smycp3": True,
                "s2mycp": True, "s2mycp2": True, "s2mycp3": True,
                "smycpnt1": None})
            self.assertEqual(len(rs.descriptionErrors), 1)

            # res2 = json.loads(self._cf.dp.GetCommandVariable("VARS"))
            self.assertTrue(val["MntGrp"] in self._cf.dp.availableSelections())
            sed = json.loads(self._cf.dp.selections([val["MntGrp"]])[0])
            self.assertEqual(len(list(sed.keys())), len(self._keys))
            for key, vl in self._keys:
                self.assertTrue(key in sed.keys())
                if key in val:
                    self.assertEqual(sed[key], val[key])
                    self.assertEqual(sed1[key], val[key])
                elif key == 'ComponentPreselection':
                    self.myAssertDict(json.loads(sed[key]), json.loads(res))
                    self.assertNotEqual(sed1[key], res)
                elif key == 'PreselectingDataSources':
                    self.assertEqual(set(json.loads(sed[key])),
                                     set(poolchannels))
                    self.assertEqual(set(json.loads(sed1[key])),
                                     set(poolchannels))
                else:
                    self.assertEqual(sed[key], vl)
                    self.assertEqual(sed1[key], vl)
        finally:
            simps2.tearDown()

    # test
    # \brief It tests default settings
    def test_resetPreselectedComponents_2wds_notangodspool_alias(self):
        fun = sys._getframe().f_code.co_name
        print("Run: %s.%s() " % (self.__class__.__name__, fun))
        val = {"ConfigDevice": self._cf.dp.name(),
               "WriterDevice": self._wr.dp.name(),
               "Door": 'doortestp09/testts/t1r228',
               "MntGrp": 'nxsmntgrp'}
        simps2 = TestServerSetUp.TestServerSetUp(
            "ttestp09/testts/t2r228", "S2")

        arr = [
            {"name": "client_short", "full_name": "ttestp09/testts/t1r228"},
        ]

        try:
            db = tango.Database()
            simps2.setUp()
            db.put_device_alias(arr[0]["full_name"], arr[0]["name"])
            db.put_device_property(list(self._ms.ms.keys())[0],
                                   {'PoolNames': self._pool.dp.name()})

            self._ms.dps[list(self._ms.ms.keys())[0]].Init()

            # channelerrors = []
            poolchannels = ["scalar2_long", "spectrum2_short", "client_short"]
            componentgroup = {
                "smycp": False, "smycp2": False, "smycp3": False,
                "smycpnt1": None,
                "s2mycp": False, "s2mycp2": False, "s2mycp3": False
            }

            cps = dict(self.smycps)
            cps.update(self.smycps2)
            dss = dict(self.smydss)
            dss.update(self.smydss2)

            self._cf.dp.SetCommandVariable(["CPDICT", json.dumps(cps)])
            self._cf.dp.SetCommandVariable(["DSDICT", json.dumps(dss)])

            rs = self.openRecSelector()
            self.setProp(rs, "defaultPreselectedComponents",
                         list(componentgroup.keys()))
            rs.configDevice = val["ConfigDevice"]
            rs.door = val["Door"]
            rs.mntGrp = val["MntGrp"]
            rs.writerDevice = val["WriterDevice"]

            self._ms.dps[list(self._ms.ms.keys())[0]].Init()
            pool = self._pool.dp
            pool.AcqChannelList = [json.dumps(a) for a in arr]

            self._simps.dp.ChangeValueType("ScalarShort")
            self._simps.dp.Value = 43

            cnf = json.loads(rs.profileConfiguration)
            cnf["PreselectingDataSources"] = json.dumps(poolchannels)
            cnf["Timer"] = '[]'
            rs.profileConfiguration = json.dumps(cnf)
            self.dump(rs)
            sed1 = json.loads(self._cf.dp.selections([val["MntGrp"]])[0])
            rs.resetPreselectedComponents()
            res = self.value(rs, "ComponentPreselection")
            self.compareToDump(rs, ["ComponentPreselection",
                                    "PreselectingDataSources"])

            pds = self.value(rs, "PreselectingDataSources")
            self.assertEqual(
                set(json.loads(self.getDump("PreselectingDataSources"))),
                set(json.loads(pds)))

            self.myAssertDict(json.loads(res), {
                "smycp": True, "smycp2": True, "smycp3": True,
                "s2mycp": True, "s2mycp2": True, "s2mycp3": True,
                "smycpnt1": True})
            self.assertTrue(not rs.descriptionErrors)

            # res2 = json.loads(self._cf.dp.GetCommandVariable("VARS"))
            self.assertTrue(val["MntGrp"] in self._cf.dp.availableSelections())
            sed = json.loads(self._cf.dp.selections([val["MntGrp"]])[0])
            self.assertEqual(len(list(sed.keys())), len(self._keys))
            for key, vl in self._keys:
                self.assertTrue(key in sed.keys())
                self.assertTrue(key in sed1.keys())
                if key in val:
                    self.assertEqual(sed[key], val[key])
                    self.assertEqual(sed1[key], val[key])
                elif key == 'ComponentPreselection':
                    self.myAssertDict(json.loads(sed[key]), json.loads(res))
                    self.assertNotEqual(sed1[key], res)
                elif key == 'PreselectingDataSources':
                    self.assertEqual(set(json.loads(sed[key])),
                                     set(poolchannels))
                    self.assertEqual(set(json.loads(sed1[key])),
                                     set(poolchannels))
                else:
                    self.assertEqual(sed[key], vl)
                    self.assertEqual(sed1[key], vl)
        finally:
            db.delete_device_alias(arr[0]["name"])
            simps2.tearDown()

    # test
    # \brief It tests default settings
    def test_resetPreselectedComponents_2wds_notangodspool_alias_bl(self):
        fun = sys._getframe().f_code.co_name
        print("Run: %s.%s() " % (self.__class__.__name__, fun))
        val = {"ConfigDevice": self._cf.dp.name(),
               "WriterDevice": self._wr.dp.name(),
               "Door": 'doortestp09/testts/t1r228',
               "MntGrp": 'nxsmntgrp'}
        simps2 = TestServerSetUp.TestServerSetUp(
            "ttestp09/testts/t2r228", "S2")

        arr = [
            {"name": "client_short", "full_name": "ttestp09/testts/t1r228"},
        ]

        try:
            db = tango.Database()
            simps2.setUp()
            db.put_device_alias(arr[0]["full_name"], arr[0]["name"])
            db.put_device_property(list(self._ms.ms.keys())[0],
                                   {'PoolNames': self._pool.dp.name()})

            self._ms.dps[list(self._ms.ms.keys())[0]].Init()

            # channelerrors = []
            poolchannels = ["scalar2_long", "spectrum2_short", "client_short"]
            componentgroup = {
                "smycp": False, "smycp2": False, "smycp3": False,
                "smycpnt1": False,
                "s2mycp": False, "s2mycp2": False, "s2mycp3": False
            }

            cps = dict(self.smycps)
            cps.update(self.smycps2)
            dss = dict(self.smydss)
            dss.update(self.smydss2)

            self._cf.dp.SetCommandVariable(["CPDICT", json.dumps(cps)])
            self._cf.dp.SetCommandVariable(["DSDICT", json.dumps(dss)])

            rs = self.openRecSelector()
            self.setProp(rs, "defaultPreselectedComponents",
                         list(componentgroup.keys()))
            self.setProp(rs, "poolBlacklist",
                         [self._pool.dp.name()])
            rs.configDevice = val["ConfigDevice"]
            rs.door = val["Door"]
            rs.mntGrp = val["MntGrp"]
            rs.writerDevice = val["WriterDevice"]

            self._ms.dps[list(self._ms.ms.keys())[0]].Init()
            pool = self._pool.dp
            pool.AcqChannelList = [json.dumps(a) for a in arr]

            self._simps.dp.ChangeValueType("ScalarShort")
            self._simps.dp.Value = 43

            cnf = json.loads(rs.profileConfiguration)
            cnf["PreselectingDataSources"] = json.dumps(poolchannels)
            cnf["Timer"] = '[]'
            rs.profileConfiguration = json.dumps(cnf)
            self.dump(rs)
            sed1 = json.loads(self._cf.dp.selections([val["MntGrp"]])[0])
            rs.resetPreselectedComponents()
            res = self.value(rs, "ComponentPreselection")
            self.compareToDump(rs, ["ComponentPreselection",
                                    "PreselectingDataSources"])

            pds = self.value(rs, "PreselectingDataSources")
            self.assertEqual(
                set(json.loads(self.getDump("PreselectingDataSources"))),
                set(json.loads(pds)))

            self.myAssertDict(json.loads(res), {
                "smycp": True, "smycp2": True, "smycp3": True,
                "s2mycp": True, "s2mycp2": True, "s2mycp3": True,
                "smycpnt1": None})
            self.assertTrue(rs.descriptionErrors)

            # res2 = json.loads(self._cf.dp.GetCommandVariable("VARS"))
            self.assertTrue(val["MntGrp"] in self._cf.dp.availableSelections())
            sed = json.loads(self._cf.dp.selections([val["MntGrp"]])[0])
            self.assertEqual(len(list(sed.keys())), len(self._keys))
            for key, vl in self._keys:
                self.assertTrue(key in sed.keys())
                self.assertTrue(key in sed1.keys())
                if key in val:
                    self.assertEqual(sed[key], val[key])
                    self.assertEqual(sed1[key], val[key])
                elif key == 'ComponentPreselection':
                    self.myAssertDict(json.loads(sed[key]), json.loads(res))
                    self.assertNotEqual(sed1[key], res)
                elif key == 'PreselectingDataSources':
                    self.assertEqual(set(json.loads(sed[key])),
                                     set(poolchannels))
                    self.assertEqual(set(json.loads(sed1[key])),
                                     set(poolchannels))
                else:
                    self.assertEqual(sed[key], vl)
                    self.assertEqual(sed1[key], vl)
        finally:
            db.delete_device_alias(arr[0]["name"])
            simps2.tearDown()

    # test
    # \brief It tests default settings
    def test_resetPreselectedComponents_2wds_notangodspool_alias_value(self):
        fun = sys._getframe().f_code.co_name
        print("Run: %s.%s() " % (self.__class__.__name__, fun))
        val = {"ConfigDevice": self._cf.dp.name(),
               "WriterDevice": self._wr.dp.name(),
               "Door": 'doortestp09/testts/t1r228',
               "MntGrp": 'nxsmntgrp'}
        simps2 = TestServerSetUp.TestServerSetUp(
            "ttestp09/testts/t2r228", "S2")

        arr = [
            {"name": "client_short", "full_name": "ttestp09/testts/t1r228"},
        ]

        try:
            db = tango.Database()
            simps2.setUp()

            db.put_device_alias(arr[0]["full_name"], arr[0]["name"])
            db.put_device_property(list(self._ms.ms.keys())[0],
                                   {'PoolNames': self._pool.dp.name()})

            self._ms.dps[list(self._ms.ms.keys())[0]].Init()
            # channelerrors = []
            poolchannels = ["scalar2_long", "spectrum2_short", "client_short"]
            componentgroup = {
                "smycp": False, "smycp2": False, "smycp3": False,
                "smycpnt1": False,
                "s2mycp": False, "s2mycp2": False, "s2mycp3": False
            }

            cps = dict(self.smycps)
            cps.update(self.smycps2)
            dss = dict(self.smydss)
            dss.update(self.smydss2)

            self._cf.dp.SetCommandVariable(["CPDICT", json.dumps(cps)])
            self._cf.dp.SetCommandVariable(["DSDICT", json.dumps(dss)])
            rs = self.openRecSelector()
            self.setProp(rs, "defaultPreselectedComponents",
                         list(componentgroup.keys()))
            rs.configDevice = val["ConfigDevice"]
            rs.door = val["Door"]
            rs.mntGrp = val["MntGrp"]
            rs.writerDevice = val["WriterDevice"]

            self._ms.dps[list(self._ms.ms.keys())[0]].Init()

            pool = self._pool.dp
            pool.AcqChannelList = [json.dumps(a) for a in arr]

            cnf = json.loads(rs.profileConfiguration)
            cnf["PreselectingDataSources"] = json.dumps(poolchannels)
            cnf["Timer"] = '[]'
            rs.profileConfiguration = json.dumps(cnf)
            self.dump(rs)
            sed1 = json.loads(self._cf.dp.selections([val["MntGrp"]])[0])
            rs.resetPreselectedComponents()
            res = self.value(rs, "ComponentPreselection")
            pds = self.value(rs, "PreselectingDataSources")
            self.compareToDump(
                rs, ["ComponentPreselection",
                     "DataSourcePreselection",
                     "PreselectingDataSources"])

            self.assertEqual(
                set(json.loads(self.getDump("PreselectingDataSources"))),
                set(json.loads(pds)))

            self.myAssertDict(json.loads(res), {
                "smycp": True, "smycp2": True, "smycp3": True,
                "s2mycp": True, "s2mycp2": True, "s2mycp3": True,
                "smycpnt1": True})
            self.assertTrue(not rs.descriptionErrors)

    #        print self._cf.dp.GetCommandVariable("COMMANDS")
            # res2 = json.loads(self._cf.dp.GetCommandVariable("VARS"))
            self.assertTrue(val["MntGrp"] in self._cf.dp.availableSelections())
            sed = json.loads(self._cf.dp.selections([val["MntGrp"]])[0])
            self.assertEqual(len(list(sed.keys())), len(self._keys))
            for key, vl in self._keys:
                self.assertTrue(key in sed.keys())
                self.assertTrue(key in sed1.keys())
                if key in val:
                    self.assertEqual(sed[key], val[key])
                    self.assertEqual(sed1[key], val[key])
                elif key == 'ComponentPreselection':
                    self.myAssertDict(json.loads(sed[key]), json.loads(res))
                    self.assertNotEqual(sed1[key], res)
                elif key == 'PreselectingDataSources':
                    self.assertEqual(set(json.loads(sed[key])),
                                     set(poolchannels))
                    self.assertEqual(set(json.loads(sed1[key])),
                                     set(poolchannels))
                else:
                    self.assertEqual(sed[key], vl)
                    self.assertEqual(sed1[key], vl)
        finally:
            db.delete_device_alias(arr[0]["name"])
            simps2.tearDown()

    # test
    # \brief It tests default settings
    def test_resetPreselectedComponents_2wds_ntp_alias_value_bl(self):
        fun = sys._getframe().f_code.co_name
        print("Run: %s.%s() " % (self.__class__.__name__, fun))
        val = {"ConfigDevice": self._cf.dp.name(),
               "WriterDevice": self._wr.dp.name(),
               "Door": 'doortestp09/testts/t1r228',
               "MntGrp": 'nxsmntgrp'}
        simps2 = TestServerSetUp.TestServerSetUp(
            "ttestp09/testts/t2r228", "S2")

        arr = [
            {"name": "client_short", "full_name": "ttestp09/testts/t1r228"},
        ]

        try:
            db = tango.Database()
            simps2.setUp()

            db.put_device_alias(arr[0]["full_name"], arr[0]["name"])
            db.put_device_property(list(self._ms.ms.keys())[0],
                                   {'PoolNames': self._pool.dp.name()})

            self._ms.dps[list(self._ms.ms.keys())[0]].Init()
            # channelerrors = []
            poolchannels = ["scalar2_long", "spectrum2_short", "client_short"]
            componentgroup = {
                "smycp": False, "smycp2": False, "smycp3": False,
                "smycpnt1": False,
                "s2mycp": False, "s2mycp2": False, "s2mycp3": False
            }

            cps = dict(self.smycps)
            cps.update(self.smycps2)
            dss = dict(self.smydss)
            dss.update(self.smydss2)

            self._cf.dp.SetCommandVariable(["CPDICT", json.dumps(cps)])
            self._cf.dp.SetCommandVariable(["DSDICT", json.dumps(dss)])
            rs = self.openRecSelector()
            self.setProp(rs, "defaultPreselectedComponents",
                         list(componentgroup.keys()))
            self.setProp(rs, "poolBlacklist",
                         [self._pool.dp.name()])
            rs.configDevice = val["ConfigDevice"]
            rs.door = val["Door"]
            rs.mntGrp = val["MntGrp"]
            rs.writerDevice = val["WriterDevice"]

            self._ms.dps[list(self._ms.ms.keys())[0]].Init()

            pool = self._pool.dp
            pool.AcqChannelList = [json.dumps(a) for a in arr]

            cnf = json.loads(rs.profileConfiguration)
            cnf["PreselectingDataSources"] = json.dumps(poolchannels)
            cnf["Timer"] = '[]'
            rs.profileConfiguration = json.dumps(cnf)
            self.dump(rs)
            sed1 = json.loads(self._cf.dp.selections([val["MntGrp"]])[0])
            rs.resetPreselectedComponents()
            res = self.value(rs, "ComponentPreselection")
            pds = self.value(rs, "PreselectingDataSources")
            self.compareToDump(
                rs, ["ComponentPreselection",
                     "DataSourcePreselection",
                     "PreselectingDataSources"])

            self.assertEqual(
                set(json.loads(self.getDump("PreselectingDataSources"))),
                set(json.loads(pds)))

            self.myAssertDict(json.loads(res), {
                "smycp": True, "smycp2": True, "smycp3": True,
                "s2mycp": True, "s2mycp2": True, "s2mycp3": True,
                "smycpnt1": None})
            self.assertTrue(rs.descriptionErrors)

    #        print self._cf.dp.GetCommandVariable("COMMANDS")
            # res2 = json.loads(self._cf.dp.GetCommandVariable("VARS"))
            self.assertTrue(val["MntGrp"] in self._cf.dp.availableSelections())
            sed = json.loads(self._cf.dp.selections([val["MntGrp"]])[0])
            self.assertEqual(len(list(sed.keys())), len(self._keys))
            for key, vl in self._keys:
                self.assertTrue(key in sed.keys())
                self.assertTrue(key in sed1.keys())
                if key in val:
                    self.assertEqual(sed[key], val[key])
                    self.assertEqual(sed1[key], val[key])
                elif key == 'ComponentPreselection':
                    self.myAssertDict(json.loads(sed[key]), json.loads(res))
                    self.assertNotEqual(sed1[key], res)
                elif key == 'PreselectingDataSources':
                    self.assertEqual(set(json.loads(sed[key])),
                                     set(poolchannels))
                    self.assertEqual(set(json.loads(sed1[key])),
                                     set(poolchannels))
                else:
                    self.assertEqual(sed[key], vl)
                    self.assertEqual(sed1[key], vl)
        finally:
            db.delete_device_alias(arr[0]["name"])
            simps2.tearDown()

    # test
    # \brief It tests default settings
    def test_resetPreselectedComponents_2wds_notngdspool_alias_novalue(self):
        fun = sys._getframe().f_code.co_name
        print("Run: %s.%s() " % (self.__class__.__name__, fun))
        val = {"ConfigDevice": self._cf.dp.name(),
               "WriterDevice": self._wr.dp.name(),
               "Door": 'doortestp09/testts/t1r228',
               "MntGrp": 'nxsmntgrp'}
        simps2 = TestServerSetUp.TestServerSetUp(
            "ttestp09/testts/t2r228", "S2")

        arr = [
            {"name": "client_short", "full_name": "ttestp09/testts/t1r228"},
        ]

        try:
            db = tango.Database()
            simps2.setUp()

            db.put_device_alias(arr[0]["full_name"], arr[0]["name"])
            db.put_device_property(list(self._ms.ms.keys())[0],
                                   {'PoolNames': self._pool.dp.name()})

            self._ms.dps[list(self._ms.ms.keys())[0]].Init()

            # channelerrors = []
            poolchannels = ["scalar2_long", "spectrum2_short", "client2_short"]
            componentgroup = {
                "smycp": False, "smycp2": False, "smycp3": False,
                "s2mycpnt1": False,
                #   "s2mycp": False, "s2mycp2": False, "s2mycp3": False
            }

            cps = dict(self.smycps)
            cps.update(self.smycps2)
            dss = dict(self.smydss)
            dss.update(self.smydss2)

            self._cf.dp.SetCommandVariable(["CPDICT", json.dumps(cps)])
            self._cf.dp.SetCommandVariable(["DSDICT", json.dumps(dss)])
            rs = self.openRecSelector()
            self.setProp(rs, "defaultPreselectedComponents",
                         list(componentgroup.keys()))
            rs.configDevice = val["ConfigDevice"]
            rs.door = val["Door"]
            rs.mntGrp = val["MntGrp"]
            rs.writerDevice = val["WriterDevice"]

            self._ms.dps[list(self._ms.ms.keys())[0]].Init()

            pool = self._pool.dp
            pool.AcqChannelList = [json.dumps(a) for a in arr]

            cnf = json.loads(rs.profileConfiguration)
            cnf["PreselectingDataSources"] = json.dumps(poolchannels)
            cnf["Timer"] = '[]'
            rs.profileConfiguration = json.dumps(cnf)
            self.dump(rs)
            sed1 = json.loads(self._cf.dp.selections([val["MntGrp"]])[0])
            rs.resetPreselectedComponents()
            res = self.value(rs, "ComponentPreselection")
            pds = self.value(rs, "PreselectingDataSources")
            self.compareToDump(
                rs, ["ComponentPreselection",
                     "DataSourcePreselection",
                     "PreselectingDataSources"])

            self.assertEqual(
                set(json.loads(self.getDump("PreselectingDataSources"))),
                set(json.loads(pds)))

            self.myAssertDict(json.loads(res), {
                "smycp": True, "smycp2": True, "smycp3": True,
                "s2mycpnt1": None})
            self.assertEqual(len(rs.descriptionErrors), 1)

    #        print self._cf.dp.GetCommandVariable("COMMANDS")
            # res2 = json.loads(self._cf.dp.GetCommandVariable("VARS"))
            self.assertTrue(val["MntGrp"] in self._cf.dp.availableSelections())
            sed = json.loads(self._cf.dp.selections([val["MntGrp"]])[0])
            self.assertEqual(len(list(sed.keys())), len(self._keys))
            for key, vl in self._keys:
                self.assertTrue(key in sed.keys())
                self.assertTrue(key in sed1.keys())
                if key in val:
                    self.assertEqual(sed[key], val[key])
                    self.assertEqual(sed1[key], val[key])
                elif key == 'ComponentPreselection':
                    self.myAssertDict(json.loads(sed[key]), json.loads(res))
                    self.assertNotEqual(sed1[key], res)
                elif key == 'PreselectingDataSources':
                    self.assertEqual(set(json.loads(sed[key])),
                                     set(poolchannels))
                    self.assertEqual(set(json.loads(sed1[key])),
                                     set(poolchannels))
                else:
                    self.assertEqual(sed[key], vl)
                    self.assertEqual(sed1[key], vl)
        finally:
            db.delete_device_alias(arr[0]["name"])
            simps2.tearDown()

    # test
    # \brief It tests default settings
    def test_resetPreselectedComponents_2wds_nocomponents(self):
        fun = sys._getframe().f_code.co_name
        print("Run: %s.%s() " % (self.__class__.__name__, fun))
        val = {"ConfigDevice": self._cf.dp.name(),
               "WriterDevice": self._wr.dp.name(),
               "Door": 'doortestp09/testts/t1r228',
               "MntGrp": 'nxsmntgrp'}
        simps2 = TestServerSetUp.TestServerSetUp(
            "ttestp09/testts/t2r228", "S2")

        # arr = [
        #     {"name": "client_short", "full_name": "ttestp09/testts/t1r228"},
        # ]

        try:
            # db = tango.Database()
            simps2.setUp()

            self._ms.dps[list(self._ms.ms.keys())[0]].Init()
            # channelerrors = []
            poolchannels = []
            componentgroup = {
                "smycp": False, "smycp2": False, "smycp3": False,
                "s2mycp": False, "s2mycp2": False, "s2mycp3": False}

            cps = dict(self.smycps)
#            cps.update(self.smycps2)
            dss = dict(self.smydss)
#            dss.update(self.smydss2)

            self._cf.dp.SetCommandVariable(["CPDICT", json.dumps(cps)])
            self._cf.dp.SetCommandVariable(["DSDICT", json.dumps(dss)])

            rs = self.openRecSelector()
            self.setProp(rs, "defaultPreselectedComponents",
                         list(componentgroup.keys()))
            rs.configDevice = val["ConfigDevice"]
            rs.door = val["Door"]
            rs.mntGrp = val["MntGrp"]
            rs.writerDevice = val["WriterDevice"]

            self._ms.dps[list(self._ms.ms.keys())[0]].Init()

            cnf = json.loads(rs.profileConfiguration)
            cnf["PreselectingDataSources"] = json.dumps(poolchannels)
            cnf["Timer"] = '[]'
            rs.profileConfiguration = json.dumps(cnf)
            self.dump(rs)
            sed1 = json.loads(self._cf.dp.selections([val["MntGrp"]])[0])
            rs.resetPreselectedComponents()
            res = self.value(rs, "ComponentPreselection")

            self.myAssertDict(json.loads(res), {
                "smycp": True, "smycp2": True, "smycp3": True,
                "s2mycp": None, "s2mycp2": None, "s2mycp3": None})
            self.assertEqual(len(rs.descriptionErrors), 3)

            #        print self._cf.dp.GetCommandVariable("COMMANDS")
            # res2 = json.loads(self._cf.dp.GetCommandVariable("VARS"))
            self.assertTrue(val["MntGrp"] in self._cf.dp.availableSelections())
            sed = json.loads(self._cf.dp.selections([val["MntGrp"]])[0])
            self.assertEqual(len(list(sed.keys())), len(self._keys))
            for key, vl in self._keys:
                self.assertTrue(key in sed.keys())
                self.assertTrue(key in sed1.keys())
                if key in val:
                    self.assertEqual(sed[key], val[key])
                    self.assertEqual(sed1[key], val[key])
                elif key == 'ComponentPreselection':
                    self.myAssertDict(json.loads(sed[key]), json.loads(res))
                    self.assertNotEqual(sed1[key], res)
                elif key == 'PreselectingDataSources':
                    self.assertEqual(set(json.loads(sed[key])),
                                     set(poolchannels))
                    self.assertEqual(set(json.loads(sed1[key])),
                                     set(poolchannels))
                else:
                    self.assertEqual(sed[key], vl)
                    self.assertEqual(sed1[key], vl)
        finally:
            simps2.tearDown()

    # test
    # \brief It tests default settings
    def test_availableTimers_empty(self):
        fun = sys._getframe().f_code.co_name
        print("Run: %s.%s() " % (self.__class__.__name__, fun))
        val = {"ConfigDevice": self._cf.dp.name(),
               "WriterDevice": self._wr.dp.name(),
               "Door": 'doortestp09/testts/t1r228',
               "MntGrp": 'nxsmntgrp'}

        rs = self.openRecSelector()
        rs.configDevice = val["ConfigDevice"]
        rs.door = val["Door"]
        rs.mntGrp = val["MntGrp"]

        self.assertTrue(not rs.availableTimers())

#            rs = self.openRecSelector()

    # test
    # \brief It tests default settings
    def test_availableTimers_pool1(self):
        fun = sys._getframe().f_code.co_name
        print("Run: %s.%s() " % (self.__class__.__name__, fun))
        val = {"ConfigDevice": self._cf.dp.name(),
               "WriterDevice": self._wr.dp.name(),
               "Door": 'doortestp09/testts/t1r228',
               "MntGrp": 'nxsmntgrp'}

        db = tango.Database()
        db.put_device_property(list(self._ms.ms.keys())[0],
                               {'PoolNames': self._pool.dp.name()})
        self._ms.dps[list(self._ms.ms.keys())[0]].Init()
        rs = self.openRecSelector()
        rs.configDevice = val["ConfigDevice"]
        rs.door = val["Door"]
        rs.mntGrp = val["MntGrp"]

        db = tango.Database()
        db.put_device_property(list(self._ms.ms.keys())[0],
                               {'PoolNames': self._pool.dp.name()})

        self._ms.dps[list(self._ms.ms.keys())[0]].Init()

        arr = [
            ["test/ct/01", ["CTExpChannel"],
             "haso228k:10000/expchan/dgg2_exp_00/1/Value"],
            ["test/ct/02", ["conem", "CTExpChannel"],
             "haso228k:10000/expchan/dgg2_exp_01/1/Value"],
            ["test/ct/03", ["CTExpChannel", "ZeroDChannel"],
             "haso228k:10000/expchan/dgg2_exp_02/1/Value"],
            ["test/ct/04", ["oneD", "CTExpChannel"],
             "haso228k:10000/expchan/dgg2_exp_03/1/Value"],
            ["null", ["counter_04"],
             "haso228k:10000/expchan/dg2_exp_01/1/Value"],
        ]

        pool = self._pool.dp

        pool.ExpChannelList = [json.dumps(
            {"name": a[0], "interfaces": a[1], "source": a[2]}) for a in arr]

        lst = [ar[0] for ar in arr if "CTExpChannel" in ar[1]]

        dd = rs.availableTimers()
        self.assertEqual(set(dd), set(lst))

    # test
    # \brief It tests default settings
    def test_availableTimers_pool1_bl(self):
        fun = sys._getframe().f_code.co_name
        print("Run: %s.%s() " % (self.__class__.__name__, fun))
        val = {"ConfigDevice": self._cf.dp.name(),
               "WriterDevice": self._wr.dp.name(),
               "Door": 'doortestp09/testts/t1r228',
               "MntGrp": 'nxsmntgrp'}

        db = tango.Database()
        db.put_device_property(list(self._ms.ms.keys())[0],
                               {'PoolNames': self._pool.dp.name()})
        self._ms.dps[list(self._ms.ms.keys())[0]].Init()
        rs = self.openRecSelector()
        self.setProp(rs, "poolBlacklist",
                     [self._pool.dp.name()])
        rs.configDevice = val["ConfigDevice"]
        rs.door = val["Door"]
        rs.mntGrp = val["MntGrp"]

        db = tango.Database()
        db.put_device_property(list(self._ms.ms.keys())[0],
                               {'PoolNames': self._pool.dp.name()})

        self._ms.dps[list(self._ms.ms.keys())[0]].Init()

        arr = [
            ["test/ct/01", ["CTExpChannel"],
             "haso228k:10000/expchan/dgg2_exp_00/1/Value"],
            ["test/ct/02", ["conem", "CTExpChannel"],
             "haso228k:10000/expchan/dgg2_exp_01/1/Value"],
            ["test/ct/03", ["CTExpChannel", "ZeroDChannel"],
             "haso228k:10000/expchan/dgg2_exp_02/1/Value"],
            ["test/ct/04", ["oneD", "CTExpChannel"],
             "haso228k:10000/expchan/dgg2_exp_03/1/Value"],
            ["null", ["counter_04"],
             "haso228k:10000/expchan/dg2_exp_01/1/Value"],
        ]

        pool = self._pool.dp

        pool.ExpChannelList = [json.dumps(
            {"name": a[0], "interfaces": a[1], "source": a[2]}) for a in arr]

        # lst = [ar[0] for ar in arr if "CTExpChannel" in ar[1]]

        dd = rs.availableTimers()
        self.assertTrue(not dd)

    # test
    # \brief It tests default settings
    def test_availableTimers_pool1_filter(self):
        fun = sys._getframe().f_code.co_name
        print("Run: %s.%s() " % (self.__class__.__name__, fun))
        val = {"ConfigDevice": self._cf.dp.name(),
               "WriterDevice": self._wr.dp.name(),
               "Door": 'doortestp09/testts/t1r228',
               "MntGrp": 'nxsmntgrp'}

        db = tango.Database()
        db.put_device_property(list(self._ms.ms.keys())[0],
                               {'PoolNames': self._pool.dp.name()})
        self._ms.dps[list(self._ms.ms.keys())[0]].Init()
        rs = self.openRecSelector()
        self.setProp(rs, "timerFilters",
                     ["*dgg2_exp_00*", "*dgg2_exp_01*"])
        rs.configDevice = val["ConfigDevice"]
        rs.door = val["Door"]
        rs.mntGrp = val["MntGrp"]

        db = tango.Database()
        db.put_device_property(list(self._ms.ms.keys())[0],
                               {'PoolNames': self._pool.dp.name()})

        self._ms.dps[list(self._ms.ms.keys())[0]].Init()

        arr = [
            ["test/ct/01", ["CTExpChannel"],
             "haso228k:10000/expchan/dgg2_exp_00/1/Value"],
            ["test/ct/02", ["conem", "CTExpChannel"],
             "haso228k:10000/expchan/dgg2_exp_01/1/Value"],
            ["test/ct/03", ["CTExpChannel", "ZeroDChannel"],
             "haso228k:10000/expchan/dgg2_exp_02/1/Value"],
            ["test/ct/04", ["oneD", "CTExpChannel"],
             "haso228k:10000/expchan/dgg2_exp_03/1/Value"],
            ["null", ["counter_04"],
             "haso228k:10000/expchan/dg2_exp_01/1/Value"],
        ]

        pool = self._pool.dp

        pool.ExpChannelList = [json.dumps(
            {"name": a[0], "interfaces": a[1], "source": a[2]}) for a in arr]

        lst = [ar[0] for ar in arr[:2] if "CTExpChannel" in ar[1]]

        dd = rs.availableTimers()
        self.assertEqual(set(dd), set(lst))

    # test
    # \brief It tests default settings
    def test_availableTimers_2pools(self):
        fun = sys._getframe().f_code.co_name
        print("Run: %s.%s() " % (self.__class__.__name__, fun))
        val = {"ConfigDevice": self._cf.dp.name(),
               "WriterDevice": self._wr.dp.name(),
               "Door": 'doortestp09/testts/t1r228',
               "MntGrp": 'nxsmntgrp'}

        try:
            tpool2 = TestPoolSetUp.TestPoolSetUp(
                "pooltestp09/testts/t2r228", "POOLTESTS2")
            tpool2.setUp()

            db = tango.Database()
            db.put_device_property(
                list(self._ms.ms.keys())[0],
                {'PoolNames': [
                    tpool2.dp.name(), self._pool.dp.name()]})
            pool = self._pool.dp
            pool2 = tpool2.dp
            self._ms.dps[list(self._ms.ms.keys())[0]].Init()

            rs = self.openRecSelector()
            rs.configDevice = val["ConfigDevice"]
            rs.door = val["Door"]
            rs.mntGrp = val["MntGrp"]

            arr = [
                ["test/ct/01", ["CTExpChannel"],
                 "haso228k:10000/expchan/dgg2_exp_00/1/Value"],
                ["test/ct/02", ["conem", "CTExpChannel"],
                 "haso228k:10000/expchan/dgg2_exp_01/1/Value"],
                ["test/ct/03", ["CTExpChannel", "ZeroDChannel"],
                 "haso228k:10000/expchan/dgg2_exp_02/1/Value"],
                ["test/ct/04", ["oneD", "CTExpChannel"],
                 "haso228k:10000/expchan/dgg2_exp_03/1/Value"],
                ["null", ["counter_04"],
                 "haso228k:10000/expchan/dg2_exp_01/1/Value"],
            ]

            arr2 = [
                ["test/mca/01", ["CTExpChannel"],
                 "haso228k:10000/expchan/dgg2_exp_01/1/Value"],
                ["test/mca/02", ["CTExpChannel2", "CTExpChannel1"],
                 "haso228k:10000/expchan/dg2_exp_01/1/Value"],
                ["test/sca/03", ["CTExpChannel3", "CTExpChannel123"],
                 "haso228k:10000/expchan/dg2_exp_01/1/Value"],
                ["test/sca/04", ["CTExpChannel", "CTExpChannel2",
                                 "CTExpChannel3"],
                 "haso228k:10000/expchan/dgg2_exp_01/1/Value"],
            ]

            dd = rs.availableTimers()
            self.assertTrue(not dd)

            pool.ExpChannelList = [
                json.dumps(
                    {"name": a[0], "interfaces": a[1], "source": a[2]}
                ) for a in arr
            ]

            lst = [ar[0] for ar in arr if "CTExpChannel" in ar[1]]

            dd = rs.availableTimers()
            self.assertEqual(set(dd), set(lst))

            pool2.ExpChannelList = [
                json.dumps(
                    {"name": a[0], "interfaces": a[1], "source": a[2]}
                )
                for a in arr2]
            lst.extend([ar[0] for ar in arr2 if "CTExpChannel" in ar[1]])

            dd = rs.availableTimers()
            self.assertEqual(set(dd), set(lst))

        finally:
            tpool2.tearDown()

    # test
    # \brief It tests default settings
    def test_availableTimers_2pools_bl(self):
        fun = sys._getframe().f_code.co_name
        print("Run: %s.%s() " % (self.__class__.__name__, fun))
        val = {"ConfigDevice": self._cf.dp.name(),
               "WriterDevice": self._wr.dp.name(),
               "Door": 'doortestp09/testts/t1r228',
               "MntGrp": 'nxsmntgrp'}

        try:
            tpool2 = TestPoolSetUp.TestPoolSetUp(
                "pooltestp09/testts/t2r228", "POOLTESTS2")
            tpool2.setUp()

            db = tango.Database()
            db.put_device_property(
                list(self._ms.ms.keys())[0],
                {'PoolNames': [
                    tpool2.dp.name(), self._pool.dp.name()]})
            pool = self._pool.dp
            pool2 = tpool2.dp
            self._ms.dps[list(self._ms.ms.keys())[0]].Init()

            rs = self.openRecSelector()
            self.setProp(rs, "poolBlacklist",
                         [tpool2.dp.name()])
            rs.configDevice = val["ConfigDevice"]
            rs.door = val["Door"]
            rs.mntGrp = val["MntGrp"]

            arr = [
                ["test/ct/01", ["CTExpChannel"],
                 "haso228k:10000/expchan/dgg2_exp_00/1/Value"],
                ["test/ct/02", ["conem", "CTExpChannel"],
                 "haso228k:10000/expchan/dgg2_exp_01/1/Value"],
                ["test/ct/03", ["CTExpChannel", "ZeroDChannel"],
                 "haso228k:10000/expchan/dgg2_exp_02/1/Value"],
                ["test/ct/04", ["oneD", "CTExpChannel"],
                 "haso228k:10000/expchan/dgg2_exp_03/1/Value"],
                ["null", ["counter_04"],
                 "haso228k:10000/expchan/dg2_exp_01/1/Value"],
            ]

            arr2 = [
                ["test/mca/01", ["CTExpChannel"],
                 "haso228k:10000/expchan/dgg2_exp_01/1/Value"],
                ["test/mca/02", ["CTExpChannel2", "CTExpChannel1"],
                 "haso228k:10000/expchan/dg2_exp_01/1/Value"],
                ["test/sca/03", ["CTExpChannel3", "CTExpChannel123"],
                 "haso228k:10000/expchan/dg2_exp_01/1/Value"],
                ["test/sca/04", ["CTExpChannel", "CTExpChannel2",
                                 "CTExpChannel3"],
                 "haso228k:10000/expchan/dgg2_exp_01/1/Value"],
            ]

            dd = rs.availableTimers()
            self.assertTrue(not dd)

            pool.ExpChannelList = [
                json.dumps(
                    {"name": a[0], "interfaces": a[1], "source": a[2]}
                ) for a in arr
            ]

            lst = [ar[0] for ar in arr if "CTExpChannel" in ar[1]]

            dd = rs.availableTimers()
            self.assertEqual(set(dd), set(lst))

            pool2.ExpChannelList = [
                json.dumps(
                    {"name": a[0], "interfaces": a[1], "source": a[2]}
                )
                for a in arr2]
#            lst.extend([ar[0] for ar in arr2 if "CTExpChannel" in ar[1]])

            dd = rs.availableTimers()
            self.assertEqual(set(dd), set(lst))

        finally:
            tpool2.tearDown()

    # test
    # \brief It tests default settings
    def test_availableTimers_2pools_filter_bl(self):
        fun = sys._getframe().f_code.co_name
        print("Run: %s.%s() " % (self.__class__.__name__, fun))
        val = {"ConfigDevice": self._cf.dp.name(),
               "WriterDevice": self._wr.dp.name(),
               "Door": 'doortestp09/testts/t1r228',
               "MntGrp": 'nxsmntgrp'}

        try:
            tpool2 = TestPoolSetUp.TestPoolSetUp(
                "pooltestp09/testts/t2r228", "POOLTESTS2")
            tpool2.setUp()

            db = tango.Database()
            db.put_device_property(
                list(self._ms.ms.keys())[0],
                {'PoolNames': [
                    tpool2.dp.name(), self._pool.dp.name()]})
            pool = self._pool.dp
            pool2 = tpool2.dp
            self._ms.dps[list(self._ms.ms.keys())[0]].Init()

            rs = self.openRecSelector()
            self.setProp(rs, "timerFilters",
                         ["*exp_00*", "*exp_01*"])
            self.setProp(rs, "poolBlacklist",
                         [tpool2.dp.name()])
            rs.configDevice = val["ConfigDevice"]
            rs.door = val["Door"]
            rs.mntGrp = val["MntGrp"]

            arr = [
                ["test/ct/01", ["CTExpChannel"],
                 "haso228k:10000/expchan/dgg2_exp_00/1/Value"],
                ["test/ct/02", ["conem", "CTExpChannel"],
                 "haso228k:10000/expchan/dgg2_exp_01/1/Value"],
                ["test/ct/03", ["CTExpChannel", "ZeroDChannel"],
                 "haso228k:10000/expchan/dgg2_exp_02/1/Value"],
                ["test/ct/04", ["oneD", "CTExpChannel"],
                 "haso228k:10000/expchan/dgg2_exp_03/1/Value"],
                ["null", ["counter_04"],
                 "haso228k:10000/expchan/dg2_exp_01/1/Value"],
            ]

            arr2 = [
                ["test/mca/01", ["CTExpChannel"],
                 "haso228k:10000/expchan/dgg2_exp_01/1/Value"],
                ["test/mca/02", ["CTExpChannel2", "CTExpChannel1"],
                 "haso228k:10000/expchan/dg2_exp_01/1/Value"],
                ["test/sca/03", ["CTExpChannel3", "CTExpChannel123"],
                 "haso228k:10000/expchan/dg2_exp_01/1/Value"],
                ["test/sca/04", ["CTExpChannel", "CTExpChannel2",
                                 "CTExpChannel3"],
                 "haso228k:10000/expchan/dgg2_exp_01/1/Value"],
            ]

            dd = rs.availableTimers()
            self.assertTrue(not dd)

            pool.ExpChannelList = [
                json.dumps(
                    {"name": a[0], "interfaces": a[1], "source": a[2]}
                )
                for a in arr]

            lst = [ar[0] for ar in arr if (
                "CTExpChannel" in ar[1] and (
                    'exp_00' in ar[2] or 'exp_01' in ar[2]))]

            dd = rs.availableTimers()
            self.assertEqual(set(dd), set(lst))

            pool2.ExpChannelList = [
                json.dumps(
                    {"name": a[0], "interfaces": a[1], "source": a[2]}
                )
                for a in arr2]
#            lst.extend(
#                [ar[0] for ar in arr2 if (
#                    "CTExpChannel" in ar[1] and (
#                        'exp_00' in ar[2] or 'exp_01' in ar[2]))])

            dd = rs.availableTimers()
            self.assertEqual(set(dd), set(lst))

        finally:
            tpool2.tearDown()

    # test
    # \brief It tests default settings
    def test_availableTimers_2pools_filter(self):
        fun = sys._getframe().f_code.co_name
        print("Run: %s.%s() " % (self.__class__.__name__, fun))
        val = {"ConfigDevice": self._cf.dp.name(),
               "WriterDevice": self._wr.dp.name(),
               "Door": 'doortestp09/testts/t1r228',
               "MntGrp": 'nxsmntgrp'}

        try:
            tpool2 = TestPoolSetUp.TestPoolSetUp(
                "pooltestp09/testts/t2r228", "POOLTESTS2")
            tpool2.setUp()

            db = tango.Database()
            db.put_device_property(
                list(self._ms.ms.keys())[0],
                {'PoolNames': [
                    tpool2.dp.name(), self._pool.dp.name()]})
            pool = self._pool.dp
            pool2 = tpool2.dp
            self._ms.dps[list(self._ms.ms.keys())[0]].Init()

            rs = self.openRecSelector()
            self.setProp(rs, "timerFilters",
                         ["*exp_00*", "*exp_01*"])
            rs.configDevice = val["ConfigDevice"]
            rs.door = val["Door"]
            rs.mntGrp = val["MntGrp"]

            arr = [
                ["test/ct/01", ["CTExpChannel"],
                 "haso228k:10000/expchan/dgg2_exp_00/1/Value"],
                ["test/ct/02", ["conem", "CTExpChannel"],
                 "haso228k:10000/expchan/dgg2_exp_01/1/Value"],
                ["test/ct/03", ["CTExpChannel", "ZeroDChannel"],
                 "haso228k:10000/expchan/dgg2_exp_02/1/Value"],
                ["test/ct/04", ["oneD", "CTExpChannel"],
                 "haso228k:10000/expchan/dgg2_exp_03/1/Value"],
                ["null", ["counter_04"],
                 "haso228k:10000/expchan/dg2_exp_01/1/Value"],
            ]

            arr2 = [
                ["test/mca/01", ["CTExpChannel"],
                 "haso228k:10000/expchan/dgg2_exp_01/1/Value"],
                ["test/mca/02", ["CTExpChannel2", "CTExpChannel1"],
                 "haso228k:10000/expchan/dg2_exp_01/1/Value"],
                ["test/sca/03", ["CTExpChannel3", "CTExpChannel123"],
                 "haso228k:10000/expchan/dg2_exp_01/1/Value"],
                ["test/sca/04", ["CTExpChannel", "CTExpChannel2",
                                 "CTExpChannel3"],
                 "haso228k:10000/expchan/dgg2_exp_01/1/Value"],
            ]

            dd = rs.availableTimers()
            self.assertTrue(not dd)

            pool.ExpChannelList = [
                json.dumps(
                    {"name": a[0], "interfaces": a[1], "source": a[2]}
                )
                for a in arr]

            lst = [ar[0] for ar in arr if (
                "CTExpChannel" in ar[1] and (
                    'exp_00' in ar[2] or 'exp_01' in ar[2]))]

            dd = rs.availableTimers()
            self.assertEqual(set(dd), set(lst))

            pool2.ExpChannelList = [
                json.dumps(
                    {"name": a[0], "interfaces": a[1], "source": a[2]}
                )
                for a in arr2]
            lst.extend(
                [ar[0] for ar in arr2 if (
                    "CTExpChannel" in ar[1] and (
                        'exp_00' in ar[2] or 'exp_01' in ar[2]))])

            dd = rs.availableTimers()
            self.assertEqual(set(dd), set(lst))

        finally:
            tpool2.tearDown()

    # test
    # \brief It tests default settings
    def test_mutedChannels_empty(self):
        fun = sys._getframe().f_code.co_name
        print("Run: %s.%s() " % (self.__class__.__name__, fun))
        val = {"ConfigDevice": self._cf.dp.name(),
               "WriterDevice": self._wr.dp.name(),
               "Door": 'doortestp09/testts/t1r228',
               "MntGrp": 'nxsmntgrp'}

        rs = self.openRecSelector()
        rs.configDevice = val["ConfigDevice"]
        rs.door = val["Door"]
        rs.mntGrp = val["MntGrp"]

        self.assertTrue(not rs.mutedChannels())

#            rs = self.openRecSelector()

    # test
    # \brief It tests default settings
    def test_mutedChannels_pool1(self):
        fun = sys._getframe().f_code.co_name
        print("Run: %s.%s() " % (self.__class__.__name__, fun))
        val = {"ConfigDevice": self._cf.dp.name(),
               "WriterDevice": self._wr.dp.name(),
               "Door": 'doortestp09/testts/t1r228',
               "MntGrp": 'nxsmntgrp'}

        db = tango.Database()
        db.put_device_property(list(self._ms.ms.keys())[0],
                               {'PoolNames': self._pool.dp.name()})
        self._ms.dps[list(self._ms.ms.keys())[0]].Init()
        rs = self.openRecSelector()
        rs.configDevice = val["ConfigDevice"]
        rs.door = val["Door"]
        rs.mntGrp = val["MntGrp"]

        db = tango.Database()
        db.put_device_property(list(self._ms.ms.keys())[0],
                               {'PoolNames': self._pool.dp.name()})

        self._ms.dps[list(self._ms.ms.keys())[0]].Init()

        arr = [
            ["test/ct/01",
             "haso228k:10000/expchan/dgg2_exp_00/1"],
            ["test/ct/02",
             "haso228k:10000/expchan/dgg2_exp_01/1"],
            ["test/ct/03",
             "haso228k:10000/expchan/tip551_exp_02/1"],
            ["test/ct/04",
             "haso228k:10000/expchan/dgg2_exp_03/1"],
            ["null",
             "haso228k:10000/expchan/tip551_exp_01/1"],
        ]

        pool = self._pool.dp

        pool.AcqChannelList = [json.dumps(
            {"name": a[0], "full_name": a[1]}) for a in arr]

        lst = [ar[0] for ar in arr if 'tip551' in ar[1]]

        dd = rs.mutedChannels()
        self.assertEqual(set(dd), set(lst))

    # test
    # \brief It tests default settings
    def test_mutedChannels_pool1_bl(self):
        fun = sys._getframe().f_code.co_name
        print("Run: %s.%s() " % (self.__class__.__name__, fun))
        val = {"ConfigDevice": self._cf.dp.name(),
               "WriterDevice": self._wr.dp.name(),
               "Door": 'doortestp09/testts/t1r228',
               "MntGrp": 'nxsmntgrp'}

        db = tango.Database()
        db.put_device_property(list(self._ms.ms.keys())[0],
                               {'PoolNames': self._pool.dp.name()})
        self._ms.dps[list(self._ms.ms.keys())[0]].Init()
        rs = self.openRecSelector()
        self.setProp(rs, "poolBlacklist",
                     [self._pool.dp.name()])
        rs.configDevice = val["ConfigDevice"]
        rs.door = val["Door"]
        rs.mntGrp = val["MntGrp"]

        db = tango.Database()
        db.put_device_property(list(self._ms.ms.keys())[0],
                               {'PoolNames': self._pool.dp.name()})

        self._ms.dps[list(self._ms.ms.keys())[0]].Init()

        arr = [
            ["test/ct/01",
             "haso228k:10000/expchan/dgg2_exp_00/1"],
            ["test/ct/02",
             "haso228k:10000/expchan/dgg2_exp_01/1"],
            ["test/ct/03",
             "haso228k:10000/expchan/tip551_exp_02/1"],
            ["test/ct/04",
             "haso228k:10000/expchan/tip551_exp_03/1"],
            ["null",
             "haso228k:10000/expchan/dg2_exp_01/1"],
        ]

        pool = self._pool.dp

        pool.AcqChannelList = [json.dumps(
            {"name": a[0], "full_name": a[1]}) for a in arr]

        # lst = [ar[0] for ar in arr if "tip551" in ar[1]]
        dd = rs.mutedChannels()
        self.assertTrue(not dd)

    # test
    # \brief It tests default settings
    def test_mutedChannels_pool1_filter_config(self):
        fun = sys._getframe().f_code.co_name
        print("Run: %s.%s() " % (self.__class__.__name__, fun))
        val = {"ConfigDevice": self._cf.dp.name(),
               "WriterDevice": self._wr.dp.name(),
               "Door": 'doortestp09/testts/t1r228',
               "MntGrp": 'nxsmntgrp'}

        db = tango.Database()
        db.put_device_property(list(self._ms.ms.keys())[0],
                               {'PoolNames': self._pool.dp.name()})
        self._ms.dps[list(self._ms.ms.keys())[0]].Init()
        rs = self.openRecSelector()
        self.setProp(rs, "mutedChannelFilters",
                     ["*dgg2_exp_00*", "*dgg2_exp_01*", "*testts*"])
        rs.configDevice = val["ConfigDevice"]
        rs.door = val["Door"]
        rs.mntGrp = val["MntGrp"]
        self._cf.dp.SetCommandVariable(["DSDICT", json.dumps(self.smydss)])

        db = tango.Database()
        db.put_device_property(list(self._ms.ms.keys())[0],
                               {'PoolNames': self._pool.dp.name()})

        self._ms.dps[list(self._ms.ms.keys())[0]].Init()

        arr = [
            ["test/ct/01",
             "haso228k:10000/expchan/dgg2_exp_00/1/Value"],
            ["test/ct/02",
             "haso228k:10000/expchan/dgg2_exp_01/1/Value"],
            ["test/ct/03",
             "haso228k:10000/expchan/dgg2_exp_02/1/Value"],
            ["test/ct/04",
             "haso228k:10000/expchan/dgg2_exp_03/1/Value"],
            ["null",
             "haso228k:10000/expchan/dg2_exp_01/1/Value"],
        ]

        pool = self._pool.dp

        pool.AcqChannelList = [json.dumps(
            {"name": a[0], "full_name": a[1]}) for a in arr]

        lst = [ar[0] for ar in arr[:2]
               if ('dgg2_exp_00' in ar[1] or 'dgg2_exp_01' in ar[1])]

        dd = rs.mutedChannels()
        self.assertEqual(set(dd),
                         set(lst + list(self.smydss.keys()))
                         - set(['client_long', 'client_short']))

    # test
    # \brief It tests default settings
    def test_mutedChannels_pool1_filter(self):
        fun = sys._getframe().f_code.co_name
        print("Run: %s.%s() " % (self.__class__.__name__, fun))
        val = {"ConfigDevice": self._cf.dp.name(),
               "WriterDevice": self._wr.dp.name(),
               "Door": 'doortestp09/testts/t1r228',
               "MntGrp": 'nxsmntgrp'}

        db = tango.Database()
        db.put_device_property(list(self._ms.ms.keys())[0],
                               {'PoolNames': self._pool.dp.name()})
        self._ms.dps[list(self._ms.ms.keys())[0]].Init()
        rs = self.openRecSelector()
        self.setProp(rs, "mutedChannelFilters",
                     ["*dgg2_exp_00*", "*dgg2_exp_01*"])
        rs.configDevice = val["ConfigDevice"]
        rs.door = val["Door"]
        rs.mntGrp = val["MntGrp"]

        db = tango.Database()
        db.put_device_property(list(self._ms.ms.keys())[0],
                               {'PoolNames': self._pool.dp.name()})

        self._ms.dps[list(self._ms.ms.keys())[0]].Init()

        arr = [
            ["test/ct/01",
             "haso228k:10000/expchan/dgg2_exp_00/1/Value"],
            ["test/ct/02",
             "haso228k:10000/expchan/dgg2_exp_01/1/Value"],
            ["test/ct/03",
             "haso228k:10000/expchan/dgg2_exp_02/1/Value"],
            ["test/ct/04",
             "haso228k:10000/expchan/dgg2_exp_03/1/Value"],
            ["null",
             "haso228k:10000/expchan/dg2_exp_01/1/Value"],
        ]

        pool = self._pool.dp

        pool.AcqChannelList = [json.dumps(
            {"name": a[0], "full_name": a[1]}) for a in arr]

        lst = [ar[0] for ar in arr[:2]
               if ('dgg2_exp_00' in ar[1] or 'dgg2_exp_01' in ar[1])]

        dd = rs.mutedChannels()
        self.assertEqual(set(dd), set(lst))

    # test
    # \brief It tests default settings
    def test_mutedChannels_2pools(self):
        fun = sys._getframe().f_code.co_name
        print("Run: %s.%s() " % (self.__class__.__name__, fun))
        val = {"ConfigDevice": self._cf.dp.name(),
               "WriterDevice": self._wr.dp.name(),
               "Door": 'doortestp09/testts/t1r228',
               "MntGrp": 'nxsmntgrp'}

        try:
            tpool2 = TestPoolSetUp.TestPoolSetUp(
                "pooltestp09/testts/t2r228", "POOLTESTS2")
            tpool2.setUp()

            db = tango.Database()
            db.put_device_property(
                list(self._ms.ms.keys())[0],
                {'PoolNames': [
                    tpool2.dp.name(), self._pool.dp.name()]})
            pool = self._pool.dp
            pool2 = tpool2.dp
            self._ms.dps[list(self._ms.ms.keys())[0]].Init()

            rs = self.openRecSelector()
            rs.configDevice = val["ConfigDevice"]
            rs.door = val["Door"]
            rs.mntGrp = val["MntGrp"]

            arr = [
                ["test/ct/01",
                 "haso228k:10000/extip551pchan/dgg2_exp_00/1"],
                ["test/ct/02",
                 "haso228k:10000/expchan/dgg2_exp_01/1"],
                ["test/ct/03",
                 "haso228k:10000/expchan/dgg2_exp_02/1"],
                ["test/ct/04",
                 "haso228k:10000/expchan/dgg2_exp_03/1Value"],
                ["null",
                 "haso228k:10000/extip551p/dg2_exp_01/1Value"],
            ]

            arr2 = [
                ["test/mca/01",
                 "haso228k:10000/expchan/dgg2_exp_01/1Value"],
                ["test/mca/02",
                 "haso228k:10000/tip551/dg2_exp_01/1Value"],
                ["test/sca/03",
                 "haso228k:10000/expchan/dg2_exp_01/1Value"],
                ["test/sca/04",
                 "haso228k:10000/tip551/dgg2_exp_01/1Value"],
            ]

            dd = rs.mutedChannels()
            self.assertTrue(not dd)

            pool.AcqChannelList = [
                json.dumps(
                    {"name": a[0], "full_name": a[1]}
                ) for a in arr
            ]

            lst = [ar[0] for ar in arr if 'tip551' in ar[1]]

            dd = rs.mutedChannels()
            self.assertEqual(set(dd), set(lst))

            pool2.AcqChannelList = [
                json.dumps(
                    {"name": a[0], "full_name": a[1]}
                )
                for a in arr2]
            lst.extend([ar[0] for ar in arr2 if 'tip551' in ar[1]])

            dd = rs.mutedChannels()
            self.assertEqual(set(dd), set(lst))

        finally:
            tpool2.tearDown()

    # test
    # \brief It tests default settings
    def test_mutedChannels_2pools_bl(self):
        fun = sys._getframe().f_code.co_name
        print("Run: %s.%s() " % (self.__class__.__name__, fun))
        val = {"ConfigDevice": self._cf.dp.name(),
               "WriterDevice": self._wr.dp.name(),
               "Door": 'doortestp09/testts/t1r228',
               "MntGrp": 'nxsmntgrp'}

        try:
            tpool2 = TestPoolSetUp.TestPoolSetUp(
                "pooltestp09/testts/t2r228", "POOLTESTS2")
            tpool2.setUp()

            db = tango.Database()
            db.put_device_property(
                list(self._ms.ms.keys())[0],
                {'PoolNames': [
                    tpool2.dp.name(), self._pool.dp.name()]})
            pool = self._pool.dp
            pool2 = tpool2.dp
            self._ms.dps[list(self._ms.ms.keys())[0]].Init()

            rs = self.openRecSelector()
            self.setProp(rs, "poolBlacklist",
                         [tpool2.dp.name()])
            rs.configDevice = val["ConfigDevice"]
            rs.door = val["Door"]
            rs.mntGrp = val["MntGrp"]

            arr = [
                ["test/ct/01",
                 "haso228k:10000/expchan/dgg2_exp_00/1tip551e"],
                ["test/ct/02",
                 "haso228k:10000/expchan/dtip551gg2_exp_01/1/Value"],
                ["test/ct/03",
                 "haso228k:10000/tip551han/dgg2_exp_02/1/Value"],
                ["test/ct/04",
                 "haso228k:10000/expchan/dgg2_exp_03/1/Value"],
                ["null",
                 "haso228k:10000/expchan/dg2_exp_01/1/Value"],
            ]

            arr2 = [
                ["test/mca/01",
                 "haso228k:10000/expchan/dgg2_exp_01/1/Value"],
                ["test/mca/02",
                 "haso228k:10000/expchan/dg2_exp_01/1/Value"],
                ["test/sca/03",
                 "haso228k:10000/expchan/dg2_tip551exp_01/1/Value"],
                ["test/sca/04",
                 "haso228k:10000/expchan/dgg2_exp_01/1tip551"],
            ]

            dd = rs.mutedChannels()
            self.assertTrue(not dd)

            pool.AcqChannelList = [
                json.dumps(
                    {"name": a[0], "full_name": a[1]}
                ) for a in arr
            ]

            lst = [ar[0] for ar in arr if 'tip551' in ar[1]]

            dd = rs.mutedChannels()
            self.assertEqual(set(dd), set(lst))

            pool2.AcqChannelList = [
                json.dumps(
                    {"name": a[0], "full_name": a[1]}
                )
                for a in arr2]
#            lst.extend([ar[0] for ar in arr2 if "CTExpChannel" in ar[1]])

            dd = rs.mutedChannels()
            self.assertEqual(set(dd), set(lst))

        finally:
            tpool2.tearDown()

    # test
    # \brief It tests default settings
    def test_mutedChannels_2pools_filter_bl(self):
        fun = sys._getframe().f_code.co_name
        print("Run: %s.%s() " % (self.__class__.__name__, fun))
        val = {"ConfigDevice": self._cf.dp.name(),
               "WriterDevice": self._wr.dp.name(),
               "Door": 'doortestp09/testts/t1r228',
               "MntGrp": 'nxsmntgrp'}

        try:
            tpool2 = TestPoolSetUp.TestPoolSetUp(
                "pooltestp09/testts/t2r228", "POOLTESTS2")
            tpool2.setUp()

            db = tango.Database()
            db.put_device_property(
                list(self._ms.ms.keys())[0],
                {'PoolNames': [
                    tpool2.dp.name(), self._pool.dp.name()]})
            pool = self._pool.dp
            pool2 = tpool2.dp
            self._ms.dps[list(self._ms.ms.keys())[0]].Init()

            rs = self.openRecSelector()
            self.setProp(rs, "mutedChannelFilters",
                         ["*exp_00*", "*exp_01*"])
            self.setProp(rs, "poolBlacklist",
                         [tpool2.dp.name()])
            rs.configDevice = val["ConfigDevice"]
            rs.door = val["Door"]
            rs.mntGrp = val["MntGrp"]

            arr = [
                ["test/ct/01",
                 "haso228k:10000/expchan/dgg2_exp_00/1/Value"],
                ["test/ct/02",
                 "haso228k:10000/expchan/dgg2_exp_01/1/Value"],
                ["test/ct/03",
                 "haso228k:10000/expchan/dgg2_exp_02/1/Value"],
                ["test/ct/04",
                 "haso228k:10000/expchan/dgg2_exp_03/1/Value"],
                ["null",
                 "haso228k:10000/expchan/dg2_exp_01/1/Value"],
            ]

            arr2 = [
                ["test/mca/01",
                 "haso228k:10000/expchan/dgg2_exp_01/1/Value"],
                ["test/mca/02",
                 "haso228k:10000/expchan/dg2_exp_01/1/Value"],
                ["test/sca/03",
                 "haso228k:10000/expchan/dg2_exp_01/1/Value"],
                ["test/sca/04",
                 "haso228k:10000/expchan/dgg2_exp_01/1/Value"],
            ]

            dd = rs.mutedChannels()
            self.assertTrue(not dd)

            pool.AcqChannelList = [
                json.dumps(
                    {"name": a[0], "full_name": a[1]}
                )
                for a in arr]

            lst = [ar[0] for ar in arr if (
                'exp_00' in ar[1] or 'exp_01' in ar[1])]

            dd = rs.mutedChannels()
            self.assertEqual(set(dd), set(lst))

            pool2.AcqChannelList = [
                json.dumps(
                    {"name": a[0], "full_name": a[1]}
                )
                for a in arr2]
            dd = rs.mutedChannels()
            self.assertEqual(set(dd), set(lst))

        finally:
            tpool2.tearDown()

    # test
    # \brief It tests default settings
    def test_mutedChannels_2pools_filter(self):
        fun = sys._getframe().f_code.co_name
        print("Run: %s.%s() " % (self.__class__.__name__, fun))
        val = {"ConfigDevice": self._cf.dp.name(),
               "WriterDevice": self._wr.dp.name(),
               "Door": 'doortestp09/testts/t1r228',
               "MntGrp": 'nxsmntgrp'}

        try:
            tpool2 = TestPoolSetUp.TestPoolSetUp(
                "pooltestp09/testts/t2r228", "POOLTESTS2")
            tpool2.setUp()

            db = tango.Database()
            db.put_device_property(
                list(self._ms.ms.keys())[0],
                {'PoolNames': [
                    tpool2.dp.name(), self._pool.dp.name()]})
            pool = self._pool.dp
            pool2 = tpool2.dp
            self._ms.dps[list(self._ms.ms.keys())[0]].Init()

            rs = self.openRecSelector()
            self.setProp(rs, "mutedChannelFilters",
                         ["*exp_00*", "*exp_01*"])
            rs.configDevice = val["ConfigDevice"]
            rs.door = val["Door"]
            rs.mntGrp = val["MntGrp"]

            arr = [
                ["test/ct/01",
                 "haso228k:10000/expchan/dgg2_exp_00/1/Value"],
                ["test/ct/02",
                 "haso228k:10000/expchan/dgg2_exp_01/1/Value"],
                ["test/ct/03",
                 "haso228k:10000/expchan/dgg2_exp_02/1/Value"],
                ["test/ct/04",
                 "haso228k:10000/expchan/dgg2_exp_03/1/Value"],
                ["null",
                 "haso228k:10000/expchan/dg2_exp_01/1/Value"],
            ]

            arr2 = [
                ["test/mca/01",
                 "haso228k:10000/expchan/dgg2_exp_01/1/Value"],
                ["test/mca/02",
                 "haso228k:10000/expchan/dg2_exp_01/1/Value"],
                ["test/sca/03",
                 "haso228k:10000/expchan/dg2_exp_01/1/Value"],
                ["test/sca/04",
                 "haso228k:10000/expchan/dgg2_exp_01/1/Value"],
            ]

            dd = rs.mutedChannels()
            self.assertTrue(not dd)

            pool.AcqChannelList = [
                json.dumps(
                    {"name": a[0], "full_name": a[1]}
                )
                for a in arr]

            lst = [ar[0] for ar in arr if (
                'exp_00' in ar[1] or 'exp_01' in ar[1])]

            dd = rs.mutedChannels()
            self.assertEqual(set(dd), set(lst))

            pool2.AcqChannelList = [
                json.dumps(
                    {"name": a[0], "full_name": a[1]}
                )
                for a in arr2]
            lst.extend(
                [ar[0] for ar in arr2 if (
                    'exp_00' in ar[1] or 'exp_01' in ar[1])])

            dd = rs.mutedChannels()
            self.assertEqual(set(dd), set(lst))

        finally:
            tpool2.tearDown()

    # getDeviceName test
    def test_fullDeviceNames_empty(self):
        fun = sys._getframe().f_code.co_name
        print("Run: %s.%s() " % (self.__class__.__name__, fun))
        val = {"ConfigDevice": self._cf.dp.name(),
               "WriterDevice": self._wr.dp.name(),
               "Door": 'doortestp09/testts/t1r228',
               "MntGrp": 'nxsmntgrp'}

        db = tango.Database()
        db.put_device_property(list(self._ms.ms.keys())[0],
                               {'PoolNames': self._pool.dp.name()})
        self._ms.dps[list(self._ms.ms.keys())[0]].Init()
        rs = self.openRecSelector()
        rs.configDevice = val["ConfigDevice"]
        rs.door = val["Door"]
        rs.mntGrp = val["MntGrp"]

        self.assertEqual({}, json.loads(rs.fullDeviceNames()))

    # getDeviceName test
    def test_fullDeviceNames_pool1(self):
        fun = sys._getframe().f_code.co_name
        print("Run: %s.%s() " % (self.__class__.__name__, fun))
        val = {"ConfigDevice": self._cf.dp.name(),
               "WriterDevice": self._wr.dp.name(),
               "Door": 'doortestp09/testts/t1r228',
               "MntGrp": 'nxsmntgrp'}

        db = tango.Database()
        db.put_device_property(list(self._ms.ms.keys())[0],
                               {'PoolNames': self._pool.dp.name()})
        self._ms.dps[list(self._ms.ms.keys())[0]].Init()
        rs = self.openRecSelector()
        rs.configDevice = val["ConfigDevice"]
        rs.door = val["Door"]
        rs.mntGrp = val["MntGrp"]

        db = tango.Database()
        db.put_device_property(list(self._ms.ms.keys())[0],
                               {'PoolNames': self._pool.dp.name()})

        self._ms.dps[list(self._ms.ms.keys())[0]].Init()

        arr = [
            ["test/ct/01", "counter_01", "Value"],
            ["test/ct/02", "counter_02", "att"],
            ["test/ct/03", "counter_03", "value"],
            ["test/ct/04", "counter_04", "13"],
            ["null", "counter_04", ""],
        ]

        pool = self._pool.dp

        pool.AcqChannelList = [
            json.dumps(
                {"name": a[0], "full_name": "%s/%s" % (a[1], a[2])})
            for a in arr]

        dd = json.loads(rs.fullDeviceNames())
        self.myAssertDict(dd, dict((ar[0], ar[1]) for ar in arr))

    def test_fullDeviceNames_pool2(self):
        fun = sys._getframe().f_code.co_name
        print("Run: %s.%s() " % (self.__class__.__name__, fun))
        val = {"ConfigDevice": self._cf.dp.name(),
               "WriterDevice": self._wr.dp.name(),
               "Door": 'doortestp09/testts/t1r228',
               "MntGrp": 'nxsmntgrp'}

        try:
            tpool2 = TestPoolSetUp.TestPoolSetUp(
                "pooltestp09/testts/t2r228", "POOLTESTS2")
            tpool2.setUp()

            db = tango.Database()
            db.put_device_property(
                list(self._ms.ms.keys())[0],
                {'PoolNames': [
                    tpool2.dp.name(), self._pool.dp.name()]})
            pool = self._pool.dp
            pool2 = tpool2.dp
            self._ms.dps[list(self._ms.ms.keys())[0]].Init()

            rs = self.openRecSelector()
            rs.configDevice = val["ConfigDevice"]
            rs.door = val["Door"]
            rs.mntGrp = val["MntGrp"]

            arr = [
                ["test/ct/01", "counter_01", "Value"],
                ["test/ct/02", "counter_02", "att"],
                ["test/ct/03", "counter_03", "value"],
                ["test/ct/04", "counter_04", "13"],
                ["null", "counter_04", ""],
            ]

            arr2 = [
                ["test/mca/01", "mca_01", "1"],
                ["test/mca/02", "mca_02", "a"],
                ["test/sca/03", "my_sca_03", "1"],
                ["test/sca/04", "mysca_04", "123"],
            ]

            pool.AcqChannelList = [
                json.dumps(
                    {"name": a[0], "full_name": "%s/%s" % (a[1], a[2])})
                for a in arr]

            dd = json.loads(rs.fullDeviceNames())
            dct = dict((ar[0], ar[1]) for ar in arr)
            self.myAssertDict(dd, dct)

            pool2.AcqChannelList = [
                json.dumps(
                    {"name": a[0], "full_name": "%s/%s" % (a[1], a[2])})
                for a in arr2]

            dct2 = dict((ar[0], ar[1]) for ar in arr2)
            dd = json.loads(rs.fullDeviceNames())
            dct.update(dct2)
            self.myAssertDict(dd, dct)

        finally:
            tpool2.tearDown()

    def test_fullDeviceNames_pool2_bl(self):
        fun = sys._getframe().f_code.co_name
        print("Run: %s.%s() " % (self.__class__.__name__, fun))
        val = {"ConfigDevice": self._cf.dp.name(),
               "WriterDevice": self._wr.dp.name(),
               "Door": 'doortestp09/testts/t1r228',
               "MntGrp": 'nxsmntgrp'}

        try:
            tpool2 = TestPoolSetUp.TestPoolSetUp(
                "pooltestp09/testts/t2r228", "POOLTESTS2")
            tpool2.setUp()

            db = tango.Database()
            db.put_device_property(
                list(self._ms.ms.keys())[0],
                {'PoolNames': [
                    tpool2.dp.name(), self._pool.dp.name()]})
            pool = self._pool.dp
            pool2 = tpool2.dp
            self._ms.dps[list(self._ms.ms.keys())[0]].Init()

            rs = self.openRecSelector()
            self.setProp(rs, "poolBlacklist",
                         [tpool2.dp.name()])
            rs.configDevice = val["ConfigDevice"]
            rs.door = val["Door"]
            rs.mntGrp = val["MntGrp"]

            arr = [
                ["test/ct/01", "counter_01", "Value"],
                ["test/ct/02", "counter_02", "att"],
                ["test/ct/03", "counter_03", "value"],
                ["test/ct/04", "counter_04", "13"],
                ["null", "counter_04", ""],
            ]

            arr2 = [
                ["test/mca/01", "mca_01", "1"],
                ["test/mca/02", "mca_02", "a"],
                ["test/sca/03", "my_sca_03", "1"],
                ["test/sca/04", "mysca_04", "123"],
            ]

            pool.AcqChannelList = [
                json.dumps(
                    {"name": a[0], "full_name": "%s/%s" % (a[1], a[2])})
                for a in arr]

            dd = json.loads(rs.fullDeviceNames())
            dct = dict((ar[0], ar[1]) for ar in arr)
            self.myAssertDict(dd, dct)

            pool2.AcqChannelList = [
                json.dumps(
                    {"name": a[0], "full_name": "%s/%s" % (a[1], a[2])})
                for a in arr2]

            # dct2 = dict((ar[0], ar[1]) for ar in arr2)
            dd = json.loads(rs.fullDeviceNames())
            #            dct.update(dct2)
            self.myAssertDict(dd, dct)

        finally:
            tpool2.tearDown()

    # setEnv test
    def test_scanDir(self):
        fun = sys._getframe().f_code.co_name
        print("Run: %s.%s() " % (self.__class__.__name__, fun))

        val = {"ConfigDevice": self._cf.dp.name(),
               "WriterDevice": self._wr.dp.name(),
               "Door": 'doortestp09/testts/t1r228',
               "MntGrp": 'nxsmntgrp'}

        db = tango.Database()
        db.put_device_property(list(self._ms.ms.keys())[0],
                               {'PoolNames': self._pool.dp.name()})
        self._ms.dps[list(self._ms.ms.keys())[0]].Init()
        rs = self.openRecSelector()
        rs.configDevice = val["ConfigDevice"]
        rs.door = val["Door"]
        rs.mntGrp = val["MntGrp"]

        db = tango.Database()
        db.put_device_property(list(self._ms.ms.keys())[0],
                               {'PoolNames': self._pool.dp.name()})

        self._ms.dps[list(self._ms.ms.keys())[0]].Init()

        arr = [
            [u'/tmp/', "/tmp/sardana/"],
            [u'/tmp/', "/tmp/sard234ana/"],
            [u'/tmp/', "/tmp/sardan23a/"],
            [u'/tmp/', "/tmp/sarda234na/"],
        ]
        for vl in arr:
            self.assertEqual(vl[0], rs.scanDir)

        for vl in arr:
            rs.scanDir = vl[1]

            self.assertEqual(
                self._ms.dps[list(self._ms.ms.keys())[0]].Environment[0],
                'pickle')
            en = Utils.pickleloads(
                self._ms.dps[list(self._ms.ms.keys())[0]].Environment[1]
            )['new']
            self.assertEqual(en['ScanDir'], rs.scanDir)
            self.assertEqual(vl[1], rs.scanDir)

    # setEnv test
    def test_scanID(self):
        fun = sys._getframe().f_code.co_name
        print("Run: %s.%s() " % (self.__class__.__name__, fun))

        val = {"ConfigDevice": self._cf.dp.name(),
               "WriterDevice": self._wr.dp.name(),
               "Door": 'doortestp09/testts/t1r228',
               "MntGrp": 'nxsmntgrp'}

        db = tango.Database()
        db.put_device_property(list(self._ms.ms.keys())[0],
                               {'PoolNames': self._pool.dp.name()})
        self._ms.dps[list(self._ms.ms.keys())[0]].Init()
        rs = self.openRecSelector()
        rs.configDevice = val["ConfigDevice"]
        rs.door = val["Door"]
        rs.mntGrp = val["MntGrp"]

        db = tango.Database()
        db.put_device_property(list(self._ms.ms.keys())[0],
                               {'PoolNames': self._pool.dp.name()})

        self._ms.dps[list(self._ms.ms.keys())[0]].Init()

        arr = [
            [192, 123],
            [192, 1223],
            [192, 12313],
        ]
        for vl in arr:
            self.assertEqual(vl[0], rs.scanID)

        for vl in arr:
            rs.scanID = vl[1]

            self.assertEqual(
                self._ms.dps[list(self._ms.ms.keys())[0]].Environment[0],
                'pickle')
            en = Utils.pickleloads(
                self._ms.dps[list(self._ms.ms.keys())[0]].Environment[1]
            )['new']
            self.assertEqual(en['ScanID'], rs.scanID)
            self.assertEqual(int(vl[1]), rs.scanID)

    # scanfile test
    def test_scanFile(self):
        fun = sys._getframe().f_code.co_name
        print("Run: %s.%s() " % (self.__class__.__name__, fun))

        val = {"ConfigDevice": self._cf.dp.name(),
               "WriterDevice": self._wr.dp.name(),
               "Door": 'doortestp09/testts/t1r228',
               "MntGrp": 'nxsmntgrp'}

        db = tango.Database()
        db.put_device_property(list(self._ms.ms.keys())[0],
                               {'PoolNames': self._pool.dp.name()})
        self._ms.dps[list(self._ms.ms.keys())[0]].Init()
        rs = self.openRecSelector()
        rs.configDevice = val["ConfigDevice"]
        rs.door = val["Door"]
        rs.mntGrp = val["MntGrp"]

        db = tango.Database()
        db.put_device_property(list(self._ms.ms.keys())[0],
                               {'PoolNames': self._pool.dp.name()})

        self._ms.dps[list(self._ms.ms.keys())[0]].Init()

        arr = [
            [[u'sar4r.nxs'], ['sar4r.nxs', 'sar5r.nxs']],
            [[u'sar4r.nxs'], ['sssar3r.nxs']],
        ]
        for vl in arr:
            self.assertEqual(list(vl[0]), json.loads(rs.scanFile))

        for vl in arr:
            rs.scanFile = json.dumps(vl[1])
            # print "SF", rs.scanFile
            self.assertEqual(
                self._ms.dps[list(self._ms.ms.keys())[0]].Environment[0],
                'pickle')
            en = Utils.pickleloads(
                self._ms.dps[list(self._ms.ms.keys())[0]].Environment[1]
            )['new']
            if isinstance(en['ScanFile'], (str, unicode)):
                try:
                    sc = json.loads(rs.scanFile)[0]
                except Exception:
                    sc = rs.scanFile
                if len(sc) == 1:
                    sc = sc[0]
                self.assertEqual(en['ScanFile'], sc)
            else:
                sc = json.loads(rs.scanFile)
#                if len(sc) == 1:
#                    sc = sc[0]
                self.assertEqual(list(en['ScanFile']), sc)
            if not isinstance(sc, list):
                sc = [sc]
            self.assertEqual(list(vl[1]), sc)

    # configvariables test
    def test_configVariables(self):
        fun = sys._getframe().f_code.co_name
        print("Run: %s.%s() " % (self.__class__.__name__, fun))
        val = {"ConfigDevice": self._cf.dp.name(),
               "WriterDevice": self._wr.dp.name(),
               "Door": 'doortestp09/testts/t1r228',
               "MntGrp": 'nxsmntgrp'}

        db = tango.Database()
        db.put_device_property(list(self._ms.ms.keys())[0],
                               {'PoolNames': self._pool.dp.name()})
        self._ms.dps[list(self._ms.ms.keys())[0]].Init()
        self._cf.dp.SetCommandVariable(["CPDICT", json.dumps(self.smycps)])
        self._cf.dp.SetCommandVariable(["DSDICT", json.dumps(self.smydss)])

        filename = "__testprofile__.json"
        while os.path.exists(filename):
            filename = "_" + filename

        mg = self.getRandomName(10)
        while mg == val["MntGrp"]:
            mg = self.getRandomName(10)

        for i in range(6):
            rs = self.openRecSelector()
            rs.configDevice = val["ConfigDevice"]
            rs.door = val["Door"]
            rs.mntGrp = mg

            rs.profileFile = filename

            db = tango.Database()
            db.put_device_property(list(self._ms.ms.keys())[0],
                                   {'PoolNames': self._pool.dp.name()})

            self._ms.dps[list(self._ms.ms.keys())[0]].Init()

            self.dump(rs)

            cps = {}
            lcp = self._rnd.randint(1, 40)
            for _ in range(lcp):
                cps[self.getRandomName(10)] = self.getRandomName(
                    self._rnd.randint(1, 40))

            rs.configVariables = str(json.dumps(cps))

            mydict = {}
            if (i / 2) % 2:
                mydict = json.loads(rs.profileConfiguration)
            elif (i / 2) % 4 == 0:
                rs.exportEnvProfile()
                env = Utils.pickleloads(
                    self._ms.dps[list(self._ms.ms.keys())[0]].Environment[1])
                jmd = json.loads(rs.profileConfiguration)
                for k in self.names(rs):
                    if k == "PreselectingDataSources":
                        self.assertEqual(
                            set(json.loads(jmd[k])),
                            set(env["new"]["NeXusConfiguration"][k]))

                        continue
                    try:
                        self.assertEqual(
                            json.loads(jmd[k]),
                            env["new"]["NeXusConfiguration"][k])
                    except Exception:
                        self.assertEqual(
                            jmd[k],
                            env["new"]["NeXusConfiguration"][k])
            elif (i / 2) % 2 == 0:
                rs.saveProfile()
            else:
                rs.mntGrp = mg
                rs.storeProfile()

            self.compareToDump(
                rs, ["ConfigVariables", "PreselectingDataSources"])
            self.assertEqual(set(self.value(rs, "PreselectingDataSources")),
                             set(self.getDump("PreselectingDataSources")))

            ndss = json.loads(rs.configVariables)
            for ds in cps.keys():
                self.assertTrue(ds in ndss.keys())
                self.assertEqual(ndss[ds], cps[ds])

            rs.profileConfiguration = str(
                json.dumps({
                    "Version": "3.0.0",
                    "ConfigDevice": val["ConfigDevice"],
                    "Door": val["Door"],
                    "MntGrp": val["MntGrp"],
                })
            )
            rs.configDevice = val["ConfigDevice"]
            rs.door = val["Door"]
            rs.mntGrp = val["MntGrp"]

            self.assertEqual(rs.configVariables, "{}")

            # mydata = {}
            if (i / 2) % 2:
                rs.profileConfiguration = str(json.dumps(mydict))
            elif (i / 2) % 4 == 0:
                rs.importEnvProfile()
            elif (i / 2) % 2 == 0:
                rs.loadProfile()
            else:
                rs.mntGrp = mg
                rs.fetchProfile()

            ndss = json.loads(rs.configVariables)
            for ds in cps.keys():
                self.assertTrue(ds in ndss.keys())
                self.assertEqual(ndss[ds], cps[ds])
        os.remove(filename)

    # userdata test
    def test_userData(self):
        fun = sys._getframe().f_code.co_name
        print("Run: %s.%s() " % (self.__class__.__name__, fun))
        val = {"ConfigDevice": self._cf.dp.name(),
               "WriterDevice": self._wr.dp.name(),
               "Door": 'doortestp09/testts/t1r228',
               "MntGrp": 'nxsmntgrp'}

        db = tango.Database()
        db.put_device_property(list(self._ms.ms.keys())[0],
                               {'PoolNames': self._pool.dp.name()})
        self._ms.dps[list(self._ms.ms.keys())[0]].Init()
        self._cf.dp.SetCommandVariable(["CPDICT", json.dumps(self.smycps)])
        self._cf.dp.SetCommandVariable(["DSDICT", json.dumps(self.smydss)])

        filename = "__testprofile__.json"
        while os.path.exists(filename):
            filename = "_" + filename

        mg = self.getRandomName(10)
        while mg == val["MntGrp"]:
            mg = self.getRandomName(10)

        for i in range(6):
            rs = self.openRecSelector()
            rs.configDevice = val["ConfigDevice"]
            rs.door = val["Door"]
            rs.mntGrp = mg

            rs.profileFile = filename

            db = tango.Database()
            db.put_device_property(list(self._ms.ms.keys())[0],
                                   {'PoolNames': self._pool.dp.name()})

            self._ms.dps[list(self._ms.ms.keys())[0]].Init()

            self.dump(rs)

            cps = {}
            lcp = self._rnd.randint(1, 40)
            for _ in range(lcp):
                cps[self.getRandomName(10)] = self.getRandomName(
                    self._rnd.randint(1, 40))

            rs.userData = str(json.dumps(cps))

            mydict = {}
            if (i / 2) % 2:
                mydict = json.loads(rs.profileConfiguration)
            elif (i / 2) % 4 == 0:
                rs.exportEnvProfile()
                env = Utils.pickleloads(
                    self._ms.dps[list(self._ms.ms.keys())[0]].Environment[1])
                jmd = json.loads(rs.profileConfiguration)
                for k in self.names(rs):
                    if k == "PreselectingDataSources":
                        self.assertEqual(
                            set(json.loads(jmd[k])),
                            set(env["new"]["NeXusConfiguration"][k]))
                        continue
                    try:
                        self.assertEqual(
                            json.loads(jmd[k]),
                            env["new"]["NeXusConfiguration"][k])
                    except Exception:
                        self.assertEqual(
                            jmd[k],
                            env["new"]["NeXusConfiguration"][k])
            elif (i / 2) % 2 == 0:
                rs.saveProfile()
            else:
                rs.mntGrp = mg
                rs.storeProfile()

            self.compareToDump(rs, ["PreselectingDataSources", "UserData"])
            self.assertEqual(set(self.value(rs, "PreselectingDataSources")),
                             set(self.getDump("PreselectingDataSources")))

            ndss = json.loads(rs.userData)
            for ds in cps.keys():
                self.assertTrue(ds in ndss.keys())
                self.assertEqual(ndss[ds], cps[ds])

            rs.profileConfiguration = str(
                json.dumps({
                    "Version": "3.0.0",
                    "ConfigDevice": val["ConfigDevice"],
                    "Door": val["Door"],
                    "MntGrp": val["MntGrp"],
                })
            )
            rs.configDevice = val["ConfigDevice"]
            rs.door = val["Door"]
            rs.mntGrp = val["MntGrp"]

            self.assertEqual(rs.userData, "{}")

            # mydata = {}
            if (i / 2) % 2:
                rs.profileConfiguration = str(json.dumps(mydict))
            elif (i / 2) % 4 == 0:
                rs.importEnvProfile()
            elif (i / 2) % 2 == 0:
                rs.loadProfile()
            else:
                rs.mntGrp = mg
                rs.fetchProfile()

            ndss = json.loads(rs.userData)
            for ds in cps.keys():
                self.assertTrue(ds in ndss.keys())
                self.assertEqual(ndss[ds], cps[ds])
        os.remove(filename)

    # mntgrp test
    def test_mntGrp(self):
        fun = sys._getframe().f_code.co_name
        print("Run: %s.%s() " % (self.__class__.__name__, fun))
        val = {"ConfigDevice": self._cf.dp.name(),
               "WriterDevice": self._wr.dp.name(),
               "Door": 'doortestp09/testts/t1r228',
               "MntGrp": 'nxsmntgrp'}

        db = tango.Database()
        db.put_device_property(list(self._ms.ms.keys())[0],
                               {'PoolNames': self._pool.dp.name()})
        self._ms.dps[list(self._ms.ms.keys())[0]].Init()
        self._cf.dp.SetCommandVariable(["CPDICT", json.dumps(self.smycps)])
        self._cf.dp.SetCommandVariable(["DSDICT", json.dumps(self.smydss)])

        filename = "__testprofile__.json"
        while os.path.exists(filename):
            filename = "_" + filename

        for i in range(6):
            rs = self.openRecSelector()
            rs.configDevice = val["ConfigDevice"]
            rs.door = val["Door"]
            rs.mntGrp = val["MntGrp"]
            self.assertEqual(rs.mntGrp, val["MntGrp"])
            mg = self.getRandomName(10)
            while mg == val["MntGrp"]:
                mg = self.getRandomName(10)

            rs.mntGrp = mg
            self.assertEqual(rs.mntGrp, mg)

            rs.profileFile = filename

            db = tango.Database()
            db.put_device_property(list(self._ms.ms.keys())[0],
                                   {'PoolNames': self._pool.dp.name()})

            self._ms.dps[list(self._ms.ms.keys())[0]].Init()

            self.dump(rs)

            mydict = {}
            if (i / 2) % 2:
                mydict = json.loads(rs.profileConfiguration)
            elif (i / 2) % 4 == 0:
                rs.exportEnvProfile()
                env = Utils.pickleloads(
                    self._ms.dps[list(self._ms.ms.keys())[0]].Environment[1])
                jmd = json.loads(rs.profileConfiguration)
                for k in self.names(rs):
                    if k == "PreselectingDataSources":
                        self.assertEqual(
                            set(json.loads(jmd[k])),
                            set(env["new"]["NeXusConfiguration"][k]))
                        continue
                    try:
                        self.assertEqual(
                            json.loads(jmd[k]),
                            env["new"]["NeXusConfiguration"][k])
                    except Exception:
                        self.assertEqual(
                            jmd[k],
                            env["new"]["NeXusConfiguration"][k])
            elif (i / 2) % 2 == 0:
                rs.saveProfile()
            else:
                rs.storeProfile()

            self.compareToDump(rs, ["MntGrp"])
            self.assertEqual(rs.mntGrp, mg)

            rs.profileConfiguration = str(
                json.dumps({
                    "Version": "3.0.0",
                    "ConfigDevice": val["ConfigDevice"],
                    "Door": val["Door"],
                    "MntGrp": val["MntGrp"],
                })
            )
            rs.configDevice = val["ConfigDevice"]
            rs.door = val["Door"]
            rs.mntGrp = val["MntGrp"]

            self.assertEqual(rs.mntGrp, val["MntGrp"])

            # mydata = {}
            if (i / 2) % 2:
                rs.profileConfiguration = str(json.dumps(mydict))
            elif (i / 2) % 4 == 0:
                rs.importEnvProfile()
            elif (i / 2) % 2 == 0:
                rs.loadProfile()
            else:
                rs.mntGrp = mg
                rs.fetchProfile()

            self.compareToDump(rs, ["MntGrp", "PreselectingDataSources"])
            self.assertEqual(set(self.value(rs, "PreselectingDataSources")),
                             set(self.getDump("PreselectingDataSources")))
            self.assertEqual(rs.mntGrp, mg)

        os.remove(filename)

    # appendentry test
    def test_appendEntry(self):
        fun = sys._getframe().f_code.co_name
        print("Run: %s.%s() " % (self.__class__.__name__, fun))
        val = {"ConfigDevice": self._cf.dp.name(),
               "WriterDevice": self._wr.dp.name(),
               "Door": 'doortestp09/testts/t1r228',
               "MntGrp": 'nxsmntgrp'}

        db = tango.Database()
        db.put_device_property(list(self._ms.ms.keys())[0],
                               {'PoolNames': self._pool.dp.name()})
        self._ms.dps[list(self._ms.ms.keys())[0]].Init()
        self._cf.dp.SetCommandVariable(["CPDICT", json.dumps(self.smycps)])
        self._cf.dp.SetCommandVariable(["DSDICT", json.dumps(self.smydss)])

        filename = "__testprofile__.json"
        while os.path.exists(filename):
            filename = "_" + filename

        mg = self.getRandomName(10)
        while mg == val["MntGrp"]:
            mg = self.getRandomName(10)

        for i in range(6):
            rs = self.openRecSelector()
            rs.configDevice = val["ConfigDevice"]
            rs.door = val["Door"]
            rs.mntGrp = mg
            self.assertEqual(rs.mntGrp, mg)

            ap = bool(self._rnd.randint(0, 1))
            rs.appendEntry = ap
            self.assertEqual(rs.appendEntry, ap)

            rs.profileFile = filename

            db = tango.Database()
            db.put_device_property(list(self._ms.ms.keys())[0],
                                   {'PoolNames': self._pool.dp.name()})

            self._ms.dps[list(self._ms.ms.keys())[0]].Init()

            self.dump(rs)

            mydict = {}
            if (i / 2) % 2:
                mydict = json.loads(rs.profileConfiguration)
            elif (i / 2) % 4 == 0:
                rs.exportEnvProfile()
                env = Utils.pickleloads(
                    self._ms.dps[list(self._ms.ms.keys())[0]].Environment[1])
                jmd = json.loads(rs.profileConfiguration)
                for k in self.names(rs):
                    if k == "PreselectingDataSources":
                        self.assertEqual(
                            set(json.loads(jmd[k])),
                            set(env["new"]["NeXusConfiguration"][k]))

                        continue
                    try:
                        self.assertEqual(
                            json.loads(jmd[k]),
                            env["new"]["NeXusConfiguration"][k])
                    except Exception:
                        self.assertEqual(
                            jmd[k],
                            env["new"]["NeXusConfiguration"][k])
            elif (i / 2) % 2 == 0:
                rs.saveProfile()
            else:
                rs.mntGrp = mg
                rs.storeProfile()

            self.compareToDump(rs, ["AppendEntry"])
            self.assertEqual(rs.appendEntry, ap)

            rs.profileConfiguration = str(
                json.dumps({
                    "Version": "3.0.0",
                    "ConfigDevice": val["ConfigDevice"],
                    "Door": val["Door"],
                    "MntGrp": val["MntGrp"],
                })
            )
            rs.configDevice = val["ConfigDevice"]
            rs.door = val["Door"]
            rs.mntGrp = val["MntGrp"]

            self.assertEqual(rs.appendEntry, False)

            # mydata = {}
            if (i / 2) % 2:
                rs.profileConfiguration = str(json.dumps(mydict))
            elif (i / 2) % 4 == 0:
                rs.importEnvProfile()
            elif (i / 2) % 2 == 0:
                rs.loadProfile()
            else:
                rs.mntGrp = mg
                rs.fetchProfile()

            self.compareToDump(rs, ["AppendEntry", "PreselectingDataSources"])
            self.assertEqual(rs.appendEntry, ap)
            self.assertEqual(set(self.value(rs, "PreselectingDataSources")),
                             set(self.getDump("PreselectingDataSources")))

        os.remove(filename)

    # test
    def test_writerDevice(self):
        fun = sys._getframe().f_code.co_name
        print("Run: %s.%s() " % (self.__class__.__name__, fun))
        val = {"ConfigDevice": self._cf.dp.name(),
               "WriterDevice": self._wr.dp.name(),
               "Door": 'doortestp09/testts/t1r228',
               "MntGrp": 'nxsmntgrp'}

        db = tango.Database()
        db.put_device_property(list(self._ms.ms.keys())[0],
                               {'PoolNames': self._pool.dp.name()})
        self._ms.dps[list(self._ms.ms.keys())[0]].Init()
        self._cf.dp.SetCommandVariable(["CPDICT", json.dumps(self.smycps)])
        self._cf.dp.SetCommandVariable(["DSDICT", json.dumps(self.smydss)])

        filename = "__testprofile__.json"
        while os.path.exists(filename):
            filename = "_" + filename

        mg = self.getRandomName(10)
        while mg == val["MntGrp"]:
            mg = self.getRandomName(10)

        for i in range(6):
            rs = self.openRecSelector()
            rs.configDevice = val["ConfigDevice"]
            rs.door = val["Door"]
            rs.mntGrp = mg
            self.assertEqual(rs.mntGrp, mg)

            wd = self.getRandomName(10)
            rs.writerDevice = wd
            self.assertEqual(rs.writerDevice, wd)

            rs.profileFile = filename

            db = tango.Database()
            db.put_device_property(list(self._ms.ms.keys())[0],
                                   {'PoolNames': self._pool.dp.name()})

            self._ms.dps[list(self._ms.ms.keys())[0]].Init()

            self.dump(rs)

            mydict = {}
            if (i / 2) % 2:
                mydict = json.loads(rs.profileConfiguration)
            elif (i / 2) % 4 == 0:
                rs.exportEnvProfile()
                env = Utils.pickleloads(
                    self._ms.dps[list(self._ms.ms.keys())[0]].Environment[1])
                jmd = json.loads(rs.profileConfiguration)
                for k in self.names(rs):
                    if k == "PreselectingDataSources":
                        self.assertEqual(
                            set(json.loads(jmd[k])),
                            set(env["new"]["NeXusConfiguration"][k]))
                        continue
                    try:
                        self.assertEqual(
                            json.loads(jmd[k]),
                            env["new"]["NeXusConfiguration"][k])
                    except Exception:
                        self.assertEqual(
                            jmd[k],
                            env["new"]["NeXusConfiguration"][k])
            elif (i / 2) % 2 == 0:
                rs.saveProfile()
            else:
                rs.mntGrp = mg
                rs.storeProfile()

            self.compareToDump(rs, ["WriterDevice"])
            self.assertEqual(rs.writerDevice, wd)

            rs.profileConfiguration = str(
                json.dumps({
                    "Version": "3.0.0",
                    "ConfigDevice": val["ConfigDevice"],
                    "Door": val["Door"],
                    "MntGrp": val["MntGrp"],
                })
            )
            rs.configDevice = val["ConfigDevice"]
            rs.door = val["Door"]
            rs.mntGrp = val["MntGrp"]

            self.assertEqual(rs.mntGrp, val["MntGrp"])

            # mydata = {}
            if (i / 2) % 2:
                rs.profileConfiguration = str(json.dumps(mydict))
            elif (i / 2) % 4 == 0:
                rs.importEnvProfile()
            elif (i / 2) % 2 == 0:
                rs.loadProfile()
            else:
                rs.mntGrp = mg
                rs.fetchProfile()

            self.compareToDump(rs, ["WriterDevice", "PreselectingDataSources"])
            self.assertEqual(set(self.value(rs, "PreselectingDataSources")),
                             set(self.getDump("PreselectingDataSources")))
            self.assertEqual(rs.writerDevice, wd)

        os.remove(filename)

    # test
    def test_door(self):
        fun = sys._getframe().f_code.co_name
        print("Run: %s.%s() " % (self.__class__.__name__, fun))
        val = {"ConfigDevice": self._cf.dp.name(),
               "WriterDevice": self._wr.dp.name(),
               "Door": 'doortestp09/testts/t1r228',
               "MntGrp": 'nxsmntgrp'}
        doors = ["door2testp09/testts/t1r228",
                 "door2testp09/testts/t2r228",
                 "door2testp09/testts/t3r228"]
        msname = "ms2testp09/testts/t1r228"
        try:

            ms2 = TestMacroServerSetUp.TestMacroServerSetUp(
                "MSTESTS1TO3", [msname], doors)
            ms2.setUp()

            db = tango.Database()
            db.put_device_property(list(ms2.ms.keys())[0],
                                   {'PoolNames': self._pool.dp.name()})
            # print "KKKK", ms2.dps.keys()
            ms2.dps[list(ms2.ms.keys())[0]].Init()
            self._cf.dp.SetCommandVariable(["CPDICT", json.dumps(self.smycps)])
            self._cf.dp.SetCommandVariable(["DSDICT", json.dumps(self.smydss)])
            ms2.dps[list(ms2.ms.keys())[0]].DoorList = doors

            filename = "__testprofile__.json"
            while os.path.exists(filename):
                filename = "_" + filename

            mg = self.getRandomName(10)
            while mg == val["MntGrp"]:
                mg = self.getRandomName(10)

            for i in range(6):
                rs = self.openRecSelector()
                rs.configDevice = val["ConfigDevice"]
                rs.door = doors[i % 3]
                rs.mntGrp = mg
                self.assertEqual(rs.mntGrp, mg)
                self.assertEqual(rs.door, doors[i % 3])
                self.assertEqual(rs.macroServer, list(ms2.ms.keys())[0])

                rs.profileFile = filename

                self.dump(rs)

                # print "I", i
                mydict = {}
                if (i / 2) % 2:
                    mydict = json.loads(rs.profileConfiguration)
                elif (i / 2) % 4 == 0:
                    rs.exportEnvProfile()
                    env = Utils.pickleloads(
                        ms2.dps[list(ms2.ms.keys())[0]].Environment[1])
                    jmd = json.loads(rs.profileConfiguration)
                    for k in self.names(rs):
                        if k == "PreselectingDataSources":
                            self.assertEqual(
                                set(json.loads(jmd[k])),
                                set(env["new"]["NeXusConfiguration"][k]))
                            continue
                        try:
                            self.assertEqual(
                                json.loads(jmd[k]),
                                env["new"]["NeXusConfiguration"][k])
                        except Exception:
                            self.assertEqual(
                                jmd[k],
                                env["new"]["NeXusConfiguration"][k])
                elif (i / 2) % 2 == 0:
                    rs.saveProfile()
                else:
                    rs.mntGrp = mg
                    rs.storeProfile()

                self.compareToDump(rs, [])

                rs.profileConfiguration = str(
                    json.dumps({
                        "Version": "3.0.0",
                        "ConfigDevice": val["ConfigDevice"],
                        "Door": val["Door"],
                        "MntGrp": val["MntGrp"],
                    })
                )
                rs.configDevice = val["ConfigDevice"]
                rs.door = val["Door"]
                rs.mntGrp = val["MntGrp"]

                self.assertEqual(rs.mntGrp, val["MntGrp"])

                # mydata = {}
                if (i / 2) % 2:
                    rs.profileConfiguration = str(json.dumps(mydict))
                elif (i / 2) % 4 == 0:
                    rs.door = doors[i % 3]
                    rs.importEnvProfile()
                elif (i / 2) % 2 == 0:
                    rs.loadProfile()
                else:
                    rs.mntGrp = mg
                    rs.fetchProfile()

                self.compareToDump(rs, ["PreselectingDataSources"])
                self.assertEqual(
                    set(self.value(rs, "PreselectingDataSources")),
                    set(self.getDump("PreselectingDataSources")))
                self.assertEqual(rs.door, doors[i % 3])
                self.assertEqual(rs.macroServer, list(ms2.ms.keys())[0])
            os.remove(filename)
        finally:
            ms2.tearDown()

    # test
    def test_configDevice(self):
        fun = sys._getframe().f_code.co_name
        print("Run: %s.%s() " % (self.__class__.__name__, fun))
        val = {"ConfigDevice": self._cf.dp.name(),
               "WriterDevice": self._wr.dp.name(),
               "Door": 'doortestp09/testts/t1r228',
               "MntGrp": 'nxsmntgrp'}

        db = tango.Database()
        db.put_device_property(list(self._ms.ms.keys())[0],
                               {'PoolNames': self._pool.dp.name()})
        self._ms.dps[list(self._ms.ms.keys())[0]].Init()
        self._cf.dp.SetCommandVariable(["CPDICT", json.dumps(self.smycps)])
        self._cf.dp.SetCommandVariable(["DSDICT", json.dumps(self.smydss)])

        filename = "__testprofile__.json"
        while os.path.exists(filename):
            filename = "_" + filename

        mg = self.getRandomName(10)
        while mg == val["MntGrp"]:
            mg = self.getRandomName(10)

        for i in range(6):
            rs = self.openRecSelector()
            rs.configDevice = val["ConfigDevice"]
            rs.door = val["Door"]
            rs.mntGrp = mg
            self.assertEqual(rs.mntGrp, mg)

            rs.profileFile = filename

            db = tango.Database()
            db.put_device_property(list(self._ms.ms.keys())[0],
                                   {'PoolNames': self._pool.dp.name()})

            self._ms.dps[list(self._ms.ms.keys())[0]].Init()

            self.dump(rs)

            mydict = {}
            if (i / 2) % 2:
                mydict = json.loads(rs.profileConfiguration)
            elif (i / 2) % 4 == 0:
                rs.exportEnvProfile()
                env = Utils.pickleloads(
                    self._ms.dps[list(self._ms.ms.keys())[0]].Environment[1])
                jmd = json.loads(rs.profileConfiguration)
                for k in self.names(rs):
                    if k == "PreselectingDataSources":
                        self.assertEqual(
                            set(json.loads(jmd[k])),
                            set(env["new"]["NeXusConfiguration"][k]))

                        continue
                    try:
                        self.assertEqual(
                            json.loads(jmd[k]),
                            env["new"]["NeXusConfiguration"][k])
                    except Exception:
                        self.assertEqual(
                            jmd[k],
                            env["new"]["NeXusConfiguration"][k])
            elif (i / 2) % 2 == 0:
                rs.saveProfile()
            else:
                rs.mntGrp = mg
                rs.storeProfile()

            self.compareToDump(rs, [])
            rs.configDevice = "module"
            self.assertEqual(rs.configDevice, "module")
            rs.configDevice = ""
            self.assertTrue(
                rs.configDevice,
                TangoUtils.getDeviceName(db, "NXSConfigServer"))

            rs.profileConfiguration = str(
                json.dumps({
                    "Version": "3.0.0",
                    "ConfigDevice": val["ConfigDevice"],
                    "Door": val["Door"],
                    "MntGrp": val["MntGrp"],
                })
            )
            rs.configDevice = val["ConfigDevice"]
            rs.door = val["Door"]
            rs.mntGrp = val["MntGrp"]

            self.assertEqual(rs.mntGrp, val["MntGrp"])

            # mydata = {}
            if (i / 2) % 2:
                rs.profileConfiguration = str(json.dumps(mydict))
            elif (i / 2) % 4 == 0:
                rs.importEnvProfile()
            elif (i / 2) % 2 == 0:
                rs.loadProfile()
            else:
                rs.configDevice = val["ConfigDevice"]
                rs.mntGrp = mg
                rs.fetchProfile()

            self.compareToDump(rs, ["PreselectingDataSources"])
            self.assertEqual(set(self.value(rs, "PreselectingDataSources")),
                             set(self.getDump("PreselectingDataSources")))

        os.remove(filename)

    # userdata test
    def test_channelProperties(self):
        fun = sys._getframe().f_code.co_name
        print("Run: %s.%s() " % (self.__class__.__name__, fun))
        self.maxDiff = None
        val = {"ConfigDevice": self._cf.dp.name(),
               "WriterDevice": self._wr.dp.name(),
               "Door": 'doortestp09/testts/t1r228',
               "MntGrp": 'nxsmntgrp'}

        db = tango.Database()
        db.put_device_property(list(self._ms.ms.keys())[0],
                               {'PoolNames': self._pool.dp.name()})
        self._ms.dps[list(self._ms.ms.keys())[0]].Init()
        self._cf.dp.SetCommandVariable(["CPDICT", json.dumps(self.smycps)])
        self._cf.dp.SetCommandVariable(["DSDICT", json.dumps(self.smydss)])

        filename = "__testprofile__.json"
        while os.path.exists(filename):
            filename = "_" + filename

        mg = self.getRandomName(10)
        while mg == val["MntGrp"]:
            mg = self.getRandomName(10)
        simp2 = TestServerSetUp.MultiTestServerSetUp(
            devices=['ttestp09/testts/t%02dr228' %
                     i for i in range(1, 37)])
        sets = ["PreselectingDataSources"]
        try:
            simp2.setUp()

            for i in range(8):

                rs = self.openRecSelector()
                rs.configDevice = val["ConfigDevice"]
                rs.door = val["Door"]
                rs.mntGrp = mg
                profconf = self.generateProfile(
                    val["Door"], mg,
                    val["ConfigDevice"],
                    val["WriterDevice"])
                rs.profileConfiguration = profconf

                rs.profileFile = filename
                db = tango.Database()
                db.put_device_property(list(self._ms.ms.keys())[0],
                                       {'PoolNames': self._pool.dp.name()})

                self._ms.dps[list(self._ms.ms.keys())[0]].Init()

                self.dump(rs)

                mydict = {}
                if (i / 2) % 2:
                    mydict = json.loads(rs.profileConfiguration)
                elif (i / 2) % 4 == 0:
                    rs.exportEnvProfile()
                    env = Utils.pickleloads(
                        self._ms.dps[
                            list(self._ms.ms.keys())[0]].Environment[1])
                    jmd = json.loads(rs.profileConfiguration)
                    for k in self.names(rs):
                        try:
                            self.assertEqual(
                                jmd[k],
                                env["new"]["NeXusConfiguration"][k])
                        except Exception:
                            if k in sets:
                                self.assertEqual(
                                    set(json.loads(jmd[k])),
                                    set(env["new"]["NeXusConfiguration"][k]))
                            else:
                                self.assertEqual(
                                    json.loads(jmd[k]),
                                    env["new"]["NeXusConfiguration"][k])
                elif (i / 2) % 2 == 0:
                    rs.saveProfile()
                else:
                    rs.mntGrp = mg
                    rs.storeProfile()

                self.compareToDumpJSON(rs, sets)
                self.compareToDumpJSONSets(rs, sets)

                rs.profileConfiguration = str(
                    json.dumps({
                        "Version": "3.0.0",
                        "ConfigDevice": val["ConfigDevice"],
                        "Door": val["Door"],
                        "MntGrp": val["MntGrp"],
                    })
                )
                rs.configDevice = val["ConfigDevice"]
                rs.door = val["Door"]
                rs.mntGrp = val["MntGrp"]

                self.assertEqual(rs.userData, "{}")

                # mydata = {}
                if (i / 2) % 2:
                    rs.profileConfiguration = str(json.dumps(mydict))
                elif (i / 2) % 4 == 0:
                    rs.importEnvProfile()
                elif (i / 2) % 2 == 0:
                    rs.loadProfile()
                else:
                    rs.mntGrp = mg
                    rs.fetchProfile()

                self.compareToDumpJSON(rs, sets)
                self.compareToDumpJSONSets(rs, sets)
                prt = rs.profileConfiguration
                rs.profileConfiguration = prt
                self.compareToDumpJSON(rs, sets)
                self.compareToDumpJSONSets(rs, sets)
            os.remove(filename)
        finally:
            simp2.tearDown()

    # userdata test
    def test_profileConfiguration(self):
        fun = sys._getframe().f_code.co_name
        print("Run: %s.%s() " % (self.__class__.__name__, fun))
        self.maxDiff = None
        val = {"ConfigDevice": self._cf.dp.name(),
               "WriterDevice": self._wr.dp.name(),
               "Door": 'doortestp09/testts/t1r228',
               "MntGrp": 'nxsmntgrp'}

        db = tango.Database()
        db.put_device_property(list(self._ms.ms.keys())[0],
                               {'PoolNames': self._pool.dp.name()})
        self._ms.dps[list(self._ms.ms.keys())[0]].Init()
        self._cf.dp.SetCommandVariable(["CPDICT", json.dumps(self.smycps)])
        self._cf.dp.SetCommandVariable(["DSDICT", json.dumps(self.smydss)])

        filename = "__testprofile__.json"
        while os.path.exists(filename):
            filename = "_" + filename

        mg = self.getRandomName(10)
        while mg == val["MntGrp"]:
            mg = self.getRandomName(10)
        simp2 = TestServerSetUp.MultiTestServerSetUp(
            devices=['ttestp09/testts/t%02dr228' %
                     i for i in range(1, 37)])
        sets = ["PreselectingDataSources"]
        try:
            simp2.setUp()

            for i in range(8):

                rs = self.openRecSelector()
                rs.configDevice = val["ConfigDevice"]
                rs.door = val["Door"]
                rs.mntGrp = mg
                profconf = self.generateProfile(
                    val["Door"], mg,
                    val["ConfigDevice"],
                    val["WriterDevice"])
                rs.profileConfiguration = profconf

                rs.profileFile = filename
                db = tango.Database()
                db.put_device_property(list(self._ms.ms.keys())[0],
                                       {'PoolNames': self._pool.dp.name()})

                self._ms.dps[list(self._ms.ms.keys())[0]].Init()
                chprop = json.loads(self.generateChannelProperties())
                for nm, vl in chprop.items():
                    rs.setChannelProperties([nm, json.dumps(vl)])

                self.dump(rs)

                mydict = {}
                if (i / 2) % 2:
                    mydict = json.loads(rs.profileConfiguration)
                elif (i / 2) % 4 == 0:
                    rs.exportEnvProfile()
                    env = Utils.pickleloads(
                        self._ms.dps[
                            list(self._ms.ms.keys())[0]].Environment[1])
                    jmd = json.loads(rs.profileConfiguration)
                    for k in self.names(rs):
                        try:
                            self.assertEqual(
                                jmd[k],
                                env["new"]["NeXusConfiguration"][k])
                        except Exception:
                            if k in sets:
                                self.assertEqual(
                                    set(json.loads(jmd[k])),
                                    set(env["new"]["NeXusConfiguration"][k]))
                            else:
                                self.assertEqual(
                                    json.loads(jmd[k]),
                                    env["new"]["NeXusConfiguration"][k])
                elif (i / 2) % 2 == 0:
                    rs.saveProfile()
                else:
                    rs.mntGrp = mg
                    rs.storeProfile()

                self.compareToDumpJSON(rs, sets)
                self.compareToDumpJSONSets(rs, sets)

                rs.profileConfiguration = str(
                    json.dumps({
                        "Version": "3.0.0",
                        "ConfigDevice": val["ConfigDevice"],
                        "Door": val["Door"],
                        "MntGrp": val["MntGrp"],
                    })
                )
                rs.configDevice = val["ConfigDevice"]
                rs.door = val["Door"]
                rs.mntGrp = val["MntGrp"]

                self.assertEqual(rs.userData, "{}")

                # mydata = {}
                if (i / 2) % 2:
                    rs.profileConfiguration = str(json.dumps(mydict))
                elif (i / 2) % 4 == 0:
                    rs.importEnvProfile()
                elif (i / 2) % 2 == 0:
                    rs.loadProfile()
                else:
                    rs.mntGrp = mg
                    rs.fetchProfile()

                self.compareToDumpJSON(rs, sets)
                self.compareToDumpJSONSets(rs, sets)
                prt = rs.profileConfiguration
                rs.profileConfiguration = prt
                self.compareToDumpJSON(rs, sets)
                self.compareToDumpJSONSets(rs, sets)
                for nm, vl in chprop.items():
                    vl2 = json.loads(rs.channelProperties(nm))
                    self.myAssertDict(vl, vl2)
            os.remove(filename)
        finally:
            simp2.tearDown()

    # test
    # \brief It tests default settings
    def test_scanEnvVariables(self):
        fun = sys._getframe().f_code.co_name
        print("Run: %s.%s() " % (self.__class__.__name__, fun))
        val = {"ConfigDevice": self._cf.dp.name(),
               "WriterDevice": self._wr.dp.name(),
               "Door": 'doortestp09/testts/t1r228',
               "MntGrp": 'nxsmntgrp'}
        db = tango.Database()
        db.put_device_property(list(self._ms.ms.keys())[0],
                               {'PoolNames': self._pool.dp.name()})
        self._ms.dps[list(self._ms.ms.keys())[0]].Init()
        rs = self.openRecSelector()
        rs.configDevice = val["ConfigDevice"]
        rs.door = val["Door"]
        rs.mntGrp = val["MntGrp"]

        db = tango.Database()
        db.put_device_property(list(self._ms.ms.keys())[0],
                               {'PoolNames': self._pool.dp.name()})

        self._ms.dps[list(self._ms.ms.keys())[0]].Init()

        envs = [
            pickle.dumps(
                {
                    "new": {"ScanDir": "/tmp"}
                }, protocol=2
            ),
            pickle.dumps(
                {
                    "new": {"ScanDir": "/tmp", "ScanID": 11}
                }, protocol=2
            ),
            pickle.dumps(
                {
                    "new": {"ScanDir": "/tmp", "ScanFile": ["file.nxs"]}
                }, protocol=2
            ),
            pickle.dumps(
                {
                    "new": {
                        "ScanDir": "/tmp", "ScanID": 13,
                        "ScanFile": ["file.nxs"],
                        "NeXusConfigServer": "ptr/ert/ert",
                    }
                }, protocol=2
            ),
            pickle.dumps(
                {
                    "new": {
                        "ScanDir": "/tmp",
                        "ScanFile": ["file.nxs", "file2.nxs"],
                        "NeXusSelectorDevice": "p09/nxsrecselector/1",
                        "NeXusConfiguration": {"ConfigServer": "ptr/ert/ert2"},
                    }
                }, protocol=2
            ),
            pickle.dumps(
                {
                    "new": {
                        "ScanDir": "/tmp", "ScanID": 15,
                        "ScanFile": "file.nxs",
                        "NeXusSelectorDevice": "p09/nxsrecselector/1",
                        "NeXusConfigServer": "ptr/ert/ert",
                        "NeXusConfiguration": {"ConfigServer": "ptr/ert/ert2"},
                    }
                }, protocol=2
            ),
            pickle.dumps(
                {
                    "new": {
                        "ScanDir": "/tmp",
                        "ScanFile": ["file.nxs"],
                        "NeXusConfigServer": u'ptr/ert/ert',
                        "NeXusBool": True,
                        "NeXusInt": 234,
                        "NeXusSelectorDevice": "p09/nxsrecselector/1",
                        "NeXusFloat": 123.123,
                        "NeXusSomething": ("dgfg",),
                        "NeXusDict": {"dgfg": 123, "sdf": "345"},
                    }
                }, protocol=2
            ),
            pickle.dumps(
                {
                    "new": {
                        "ScanDir": "/tmp", "ScanID": 17,
                        "ScanFile": ["file.nxs"],
                        "NeXusSelectorDevice": "p09/nxsrecselector/1",
                        "NeXusConfiguration": {
                            "ConfigServer": u'ptr/ert/ert',
                            "Bool": True,
                            "Int": 234,
                            "Float": 123.123,
                            "Something": ("dgfg",),
                            "Dict": {"dgfg": 123, "sdf": "345"}}
                    }
                }, protocol=2
            ),
        ]

        edats = [
            {"ScanDir": "/tmp"},
            {"ScanDir": "/tmp", "ScanID": 11},
            {"ScanDir": "/tmp", "ScanFile": ["file.nxs"]},
            {"ScanDir": "/tmp", "ScanFile": ["file.nxs"], "ScanID": 13},
            {"ScanDir": "/tmp", "ScanFile": ["file.nxs", "file2.nxs"],
             "NeXusSelectorDevice": "p09/nxsrecselector/1"},
            {"ScanDir": "/tmp", "ScanFile": "file.nxs", "ScanID": 15,
             "NeXusSelectorDevice": "p09/nxsrecselector/1"},
            {"ScanDir": "/tmp", "ScanFile": ["file.nxs"],
             "NeXusSelectorDevice": "p09/nxsrecselector/1"},
            {"ScanDir": "/tmp", "ScanFile": ["file.nxs"], "ScanID": 17,
             "NeXusSelectorDevice": "p09/nxsrecselector/1"},
        ]

        data = {"ScanID": 192,
                "NeXusSelectorDevice": "p09/nxsrecselector/1",
                "ScanFile": ["sar4r.nxs"], "ScanDir": "/tmp/"}
        res = rs.scanEnvVariables()
        self.myAssertDict(json.loads(res), data)

        for i, dt in enumerate(edats):
            data = {}
            edl = list(json.loads(res).keys())
            self._ms.dps[list(self._ms.ms.keys())[0]].Environment = (
                'pickle', pickle.dumps({"del": edl}, protocol=2))
            self._ms.dps[list(self._ms.ms.keys())[0]].Environment = (
                'pickle', envs[i])
            dwt = rs.scanEnvVariables()
            res = rs.scanEnvVariables()
            self.myAssertDict(edats[i], dt)
            self.myAssertDict(edats[i], json.loads(dwt))

    # test
    # \brief It tests default settings
    def test_setScanEnvVariables(self):
        fun = sys._getframe().f_code.co_name
        print("Run: %s.%s() " % (self.__class__.__name__, fun))
        val = {"ConfigDevice": self._cf.dp.name(),
               "WriterDevice": self._wr.dp.name(),
               "Door": 'doortestp09/testts/t1r228',
               "MntGrp": 'nxsmntgrp'}
        db = tango.Database()
        db.put_device_property(list(self._ms.ms.keys())[0],
                               {'PoolNames': self._pool.dp.name()})

        self._ms.dps[list(self._ms.ms.keys())[0]].Init()
        rs = self.openRecSelector()
        rs.configDevice = val["ConfigDevice"]
        rs.door = val["Door"]
        rs.mntGrp = val["MntGrp"]

        db = tango.Database()
        db.put_device_property(list(self._ms.ms.keys())[0],
                               {'PoolNames': self._pool.dp.name()})

        self._ms.dps[list(self._ms.ms.keys())[0]].Init()

        envs = [
            {
                "new": {
                    'ScanID': 192,
                    'NeXusSelectorDevice': u'p09/nxsrecselector/1',
                    'ScanFile': [u'sar4r.nxs'],
                    'ActiveMntGrp': 'nxsmntgrp',
                    '_ViewOptions': {'ShowDial': True},
                    'DataCompressionRank': 0,
                    'ScanDir': '/tmp/'}
            },
            {
                "new": {
                    'ScanID': 192,
                    'NeXusSelectorDevice': u'p09/nxsrecselector/1',
                    'ScanFile': [u'sar4r.nxs'],
                    'ActiveMntGrp': 'nxsmntgrp',
                    '_ViewOptions': {'ShowDial': True},
                    'DataCompressionRank': 0,
                    'ScanDir': '/tmp'}
            },
            {
                "new": {
                    'ScanID': 11,
                    'NeXusSelectorDevice': u'p09/nxsrecselector/1',
                    'ActiveMntGrp': 'nxsmntgrp',
                    '_ViewOptions': {'ShowDial': True},
                    'DataCompressionRank': 0,
                    "ScanDir": "/tmp",
                    "ScanFile": ["file.nxs"]
                }
            },
            {
                "new": {
                    "ScanDir": "/tmp",
                    'ScanID': 11,
                    'NeXusSelectorDevice': u'p09/nxsrecselector/1',
                    "ConfigServer": "ptr/ert/ert",
                    'ActiveMntGrp': 'nxsmntgrp',
                    '_ViewOptions': {'ShowDial': True},
                    'DataCompressionRank': 0,
                    "ScanFile": ["file.nxs"],
                }
            },
            {
                "new": {
                    "ScanDir": "/tmp",
                    'ScanID': 13,
                    'NeXusSelectorDevice': u'p09/nxsrecselector/1',
                    "ConfigServer": "ptr/ert/ert2",
                    'ActiveMntGrp': 'nxsmntgrp',
                    '_ViewOptions': {'ShowDial': True},
                    'DataCompressionRank': 0,
                    "ScanFile": ["file.nxs", "file2.nxs"],
                }
            },
            {
                "new": {
                    "ScanDir": "/tmp",
                    'ScanID': 13,
                    'NeXusSelectorDevice': u'p09/nxsrecselector/1',
                    "ConfigServer": "ptr/ert/ert",
                    'ActiveMntGrp': 'nxsmntgrp',
                    '_ViewOptions': {'ShowDial': True},
                    'DataCompressionRank': 0,
                    "ScanFile": "file.nxs",
                }
            },
            {
                "new": {
                    "ScanDir": "/tmp",
                    'ScanID': 15,
                    'NeXusSelectorDevice': u'p09/nxsrecselector/1',
                    "ConfigServer": 'ptr/ert/ert',
                    "Bool": True,
                    "Int": 234,
                    "Float": 123.123,
                    "Something": ["dgfg"],
                    "Dict": {"dgfg": 123, "sdf": "345"},
                    'ActiveMntGrp': 'nxsmntgrp',
                    '_ViewOptions': {'ShowDial': True},
                    'DataCompressionRank': 0,
                    "ScanFile": ["file.nxs"],
                }
            },
            {
                "new": {
                    "ScanDir": "/tmp",
                    'ScanID': 15,
                    'NeXusSelectorDevice': u'p09/nxsrecselector/1',
                    "ConfigServer": 'ptr/ert/ert',
                    "Bool": True,
                    "Int": 234,
                    "Float": 123.124,
                    "Something": ["dgfg"],
                    "Dict": {"dgfg": 123, "sdf": "345"},
                    'ActiveMntGrp': 'nxsmntgrp',
                    '_ViewOptions': {'ShowDial': True},
                    'DataCompressionRank': 0,
                    "ScanFile": ["file.nxs"],
                }
            },
            {
                "new": {
                    "ScanDir": "/tmp",
                    'ScanID': 17,
                    'NeXusSelectorDevice': u'p09/nxsrecselector/1',
                    "ConfigServer": 'ptr/ert/ert',
                    "Bool": True,
                    "Int": 234,
                    "Float": 123.124,
                    "Something": ["dgfg"],
                    "Dict": {"dgfg": 123, "sdf": "345"},
                    'ActiveMntGrp': 'nxsmntgrp',
                    '_ViewOptions': {'ShowDial': True},
                    'DataCompressionRank': 0,
                    "ScanFile": ["file.nxs"],
                }
            },
            {
                "new": {
                    "ScanDir": "/tmp",
                    'ScanID': 17,
                    'NeXusSelectorDevice': u'p09/nxsrecselector/1',
                    "ConfigServer": 'ptr/ert/ert',
                    "Bool": True,
                    "Int": 234,
                    "Float": 123.124,
                    "Something": ["dgfg"],
                    "Dict": {"dgfg": 123, "sdf": "345"},
                    'ActiveMntGrp': 'nxsmntgrp',
                    '_ViewOptions': {'ShowDial': True},
                    'DataCompressionRank': 0,
                    "ScanFile": ["file.nxs"],
                }
            },
        ]

        edats = [
            {},
            {"ScanDir": "/tmp"},
            {"ScanDir": "/tmp", "ScanFile": ["file.nxs"], "ScanID": 11},
            {"ScanDir": "/tmp", "ScanFile": ["file.nxs"],
             "ConfigServer": "ptr/ert/ert"},
            {"ScanDir": "/tmp", "ScanFile": ["file.nxs", "file2.nxs"],
             "ConfigServer": "ptr/ert/ert2", "ScanID": 13},
            {"ScanDir": "/tmp", "ScanFile": "file.nxs",
             "ConfigServer": "ptr/ert/ert"},
            {"ScanDir": "/tmp", "ScanFile": ["file.nxs"],
             "ConfigServer": "ptr/ert/ert", "ScanID": 15,
             "Bool": True, "Int": 234, "Float": 123.123, "Something": ["dgfg"],
             "Dict": {"dgfg": 123, "sdf": "345"},
             },
            {"ScanDir": "/tmp", "ScanFile": ["file.nxs"],
             "ConfigServer": "ptr/ert/ert",
             "Bool": True, "Int": 234, "Float": 123.124, "Something": ["dgfg"],
             "Dict": {"dgfg": 123, "sdf": "345"},
             },
            {"ScanDir": "/tmp", "ScanFile": ["file.nxs"],
             "ConfigServer": "ptr/ert/ert", "ScanID": 17,
             "Bool": True, "Int": 234, "Float": 123.124, "Something": ["dgfg"],
             "Dict": {"dgfg": 123, "sdf": "345"},
             },
            {"ScanDir": "/tmp", "ScanFile": ["file.nxs"],
             "ConfigServer": "ptr/ert/ert",
             "Bool": True, "Int": 234, "Float": 123.124, "Something": ["dgfg"],
             "Dict": {"dgfg": 123, "sdf": "345"},
             },
        ]

        sids = [192, 192, 11, 11, 13, 13, 15, 15, 17, 17]

        rs.setScanEnvVariables("{}")
        for i, dt in enumerate(edats):
            sid = rs.setScanEnvVariables(json.dumps(dt))
            # print "I = ", i, sid
            self.assertEqual(sid, sids[i])
            # data = {}
            env = Utils.pickleloads(
                self._ms.dps[list(self._ms.ms.keys())[0]].Environment[1])
            self.myAssertDict(envs[i], env)

    # test
    def test_administratorDataNames(self):
        fun = sys._getframe().f_code.co_name
        print("Run: %s.%s() " % (self.__class__.__name__, fun))
        val = {"ConfigDevice": self._cf.dp.name(),
               "WriterDevice": self._wr.dp.name(),
               "Door": 'doortestp09/testts/t1r228',
               "MntGrp": 'nxsmntgrp'}

        rs = self.openRecSelector()
        rs.configDevice = val["ConfigDevice"]
        rs.door = val["Door"]
        rs.mntGrp = val["MntGrp"]
        self.assertEqual(rs.configDevice, val["ConfigDevice"])
        self.assertEqual(rs.door, val["Door"])
        self.assertEqual(rs.administratorDataNames(), [])

        for _ in range(6):
            lcp = self._rnd.randint(1, 10)
            anames = list(set([self.getRandomName(
                self._rnd.randint(1, 10)) for _ in range(lcp)]))
            self.setProp(rs, "adminDataNames",
                         anames)
            self.assertEqual(rs.administratorDataNames(), anames)

    # test
    def test_getDeviceGroups(self):
        fun = sys._getframe().f_code.co_name
        print("Run: %s.%s() " % (self.__class__.__name__, fun))
        val = {"ConfigDevice": self._cf.dp.name(),
               "WriterDevice": self._wr.dp.name(),
               "Door": 'doortestp09/testts/t1r228',
               "MntGrp": 'nxsmntgrp'}

        rs = self.openRecSelector()
        rs.configDevice = val["ConfigDevice"]
        rs.door = val["Door"]
        rs.mntGrp = val["MntGrp"]
        self.assertEqual(rs.configDevice, val["ConfigDevice"])
        self.assertEqual(rs.door, val["Door"])
        ddg = '{"timer": ["*exp_t*"], "dac": ["*exp_dac*"], ' \
              + '"counter": ["*exp_c*"], "mca": ["*exp_mca*"], ' \
              + '"adc": ["*exp_adc*"], "motor": ["*exp_mot*"]}'

        self.assertEqual(rs.deviceGroups, ddg)

        for _ in range(6):
            lcp = self._rnd.randint(1, 10)
            anames = list(set([self.getRandomName(
                self._rnd.randint(1, 10)) for _ in range(lcp)]))
            dg = {}
            for an in anames:
                lp = self._rnd.randint(1, 10)
                gr = list(set([self.getRandomName(
                    self._rnd.randint(1, 10)) for _ in range(lp)]))
                dg[an] = gr
            jdg = json.dumps(dg)
            rs.deviceGroups = jdg
            self.assertEqual(rs.deviceGroups, jdg)

        for _ in range(6):
            rnm = self.getRandomName(self._rnd.randint(1, 10))
            rs.deviceGroups = rnm
            try:
                ld = json.loads(rnm)
            except Exception:
                self.assertEqual(rs.deviceGroups, ddg)
            else:
                good = True
                if not isinstance(ld, dict):
                    good = False
                else:
                    for vl in ld.values():
                        if not isinstance(vl, list):
                            good = False
                            break
                    if good:
                        self.assertEqual(rs.deviceGroups, rnm)
                    else:
                        self.assertEqual(rs.deviceGroups, ddg)

    # test
    def test_stepdatasources(self):
        fun = sys._getframe().f_code.co_name
        print("Run: %s.%s() " % (self.__class__.__name__, fun))
        val = {"ConfigDevice": self._cf.dp.name(),
               "WriterDevice": self._wr.dp.name(),
               "Door": 'doortestp09/testts/t1r228',
               "MntGrp": 'nxsmntgrp'}

        rs = self.openRecSelector()
        rs.configDevice = val["ConfigDevice"]
        rs.door = val["Door"]
        rs.mntGrp = val["MntGrp"]
        self.assertEqual(rs.configDevice, val["ConfigDevice"])
        self.assertEqual(rs.door, val["Door"])
        self.assertEqual(rs.stepdatasources, '[]')
        self.assertEqual(rs.linkdatasources, '[]')

        for _ in range(6):
            lcp = self._rnd.randint(1, 10)
            anames = list(set([self.getRandomName(
                self._rnd.randint(1, 10)) for _ in range(lcp)]))
            rs.stepdatasources = str(json.dumps(anames))
            mds2 = json.loads(self._cf.dp.stepdatasources)
            mds = json.loads(rs.stepdatasources)
            self.assertEqual(set(mds), set(anames))
            self.assertEqual(set(mds2), set(anames))

        for _ in range(6):
            lcp = self._rnd.randint(1, 10)
            anames = list(set([self.getRandomName(
                self._rnd.randint(1, 10)) for _ in range(lcp)]))
            self._cf.dp.stepdatasources = str(json.dumps(anames))
            mds2 = json.loads(self._cf.dp.stepdatasources)
            mds = json.loads(rs.stepdatasources)
            self.assertEqual(set(mds), set(anames))
            self.assertEqual(set(mds2), set(anames))

    # test
    def test_linkdatasources(self):
        fun = sys._getframe().f_code.co_name
        print("Run: %s.%s() " % (self.__class__.__name__, fun))
        val = {"ConfigDevice": self._cf.dp.name(),
               "WriterDevice": self._wr.dp.name(),
               "Door": 'doortestp09/testts/t1r228',
               "MntGrp": 'nxsmntgrp'}

        rs = self.openRecSelector()
        rs.configDevice = val["ConfigDevice"]
        rs.door = val["Door"]
        rs.mntGrp = val["MntGrp"]
        self.assertEqual(rs.configDevice, val["ConfigDevice"])
        self.assertEqual(rs.door, val["Door"])
        self.assertEqual(rs.stepdatasources, '[]')
        self.assertEqual(rs.linkdatasources, '[]')

        for _ in range(6):
            lcp = self._rnd.randint(1, 10)
            anames = list(set([self.getRandomName(
                self._rnd.randint(1, 10)) for _ in range(lcp)]))
            rs.linkdatasources = str(json.dumps(anames))
            mds2 = json.loads(self._cf.dp.linkdatasources)
            mds = json.loads(rs.linkdatasources)
            self.assertEqual(set(mds), set(anames))
            self.assertEqual(set(mds2), set(anames))

        for _ in range(6):
            lcp = self._rnd.randint(1, 10)
            anames = list(set([self.getRandomName(
                self._rnd.randint(1, 10)) for _ in range(lcp)]))
            self._cf.dp.linkdatasources = str(json.dumps(anames))
            mds2 = json.loads(self._cf.dp.linkdatasources)
            mds = json.loads(rs.linkdatasources)
            self.assertEqual(set(mds), set(anames))
            self.assertEqual(set(mds2), set(anames))

    # test
    def test_deleteAllProfiles(self):
        fun = sys._getframe().f_code.co_name
        print("Run: %s.%s() " % (self.__class__.__name__, fun))
        val = {"ConfigDevice": self._cf.dp.name(),
               "WriterDevice": self._wr.dp.name(),
               "Door": 'doortestp09/testts/t1r228',
               "MntGrp": 'nxsmntgrp'}

        rs = self.openRecSelector()
        rs.configDevice = val["ConfigDevice"]
        rs.door = val["Door"]
        rs.mntGrp = val["MntGrp"]
        self.assertEqual(rs.configDevice, val["ConfigDevice"])
        self.assertEqual(rs.door, val["Door"])

        self._cf.dp.Init()
        self._cf.dp.SetCommandVariable(["SELDICT", json.dumps(self.mysel2)])
        sl1 = self._cf.dp.availableSelections()
        self.assertEqual(set(sl1), set(self.mysel2.keys()))
        rs.deleteAllProfiles()
        sl2 = self._cf.dp.availableSelections()
        self.assertEqual(set(sl2), set())

        self._cf.dp.Init()
        self._cf.dp.SetCommandVariable(["SELDICT", json.dumps(self.mysel)])
        sl1 = self._cf.dp.availableSelections()
        self.assertEqual(set(sl1), set(self.mysel.keys()))
        rs.deleteAllProfiles()
        sl2 = self._cf.dp.availableSelections()
        self.assertEqual(set(sl2), set())

    # availableMntGrps test
    def test_availableMntGrps(self):
        fun = sys._getframe().f_code.co_name
        print("Run: %s.%s() " % (self.__class__.__name__, fun))
        val = {"ConfigDevice": self._cf.dp.name(),
               "WriterDevice": self._wr.dp.name(),
               "Door": 'doortestp09/testts/t1r228',
               "MntGrp": 'nxsmntgrp'}

        rs = self.openRecSelector()
        rs.configDevice = val["ConfigDevice"]
        rs.door = val["Door"]
        rs.mntGrp = val["MntGrp"]
        self.assertEqual(rs.configDevice, val["ConfigDevice"])
        self.assertEqual(rs.door, val["Door"])

        self.assertEqual(rs.availableMntGrps(), [])

        db = tango.Database()
        db.put_device_property(list(self._ms.ms.keys())[0],
                               {'PoolNames': self._pool.dp.name()})
        pool = self._pool.dp
        self._ms.dps[list(self._ms.ms.keys())[0]].Init()

        self.assertEqual(rs.availableMntGrps(), [])

        arr = [
            {"name": "test/ct/01", "full_name": "mntgrp_01e"},
            {"name": "test/ct/02", "full_name": "mntgrp_02att"},
            {"name": "test/ct/03", "full_name": "mntgrp_03value"},
            {"name": "test/ct/04", "full_name": "mntgrp_04/13"},
            {"name": "null", "full_name": "mntgrp_04"},
        ]

        pool.MeasurementGroupList = [json.dumps(a) for a in arr]

        dd = rs.availableMntGrps()
        self.assertEqual(set(dd), set([a["name"] for a in arr]))

        for ar in arr:

            MSUtils.setEnv('ActiveMntGrp', ar["name"],
                           list(self._ms.ms.keys())[0])
            MSUtils.getEnv('ActiveMntGrp', list(self._ms.ms.keys())[0])
            dd = rs.availableMntGrps()
            self.assertEqual(dd[0], ar["name"])
            self.assertEqual(set(dd), set([a["name"] for a in arr]))

    # availableMntGrps test
    def test_availableMntGrps_twopools(self):
        fun = sys._getframe().f_code.co_name
        print("Run: %s.%s() " % (self.__class__.__name__, fun))
        val = {"ConfigDevice": self._cf.dp.name(),
               "WriterDevice": self._wr.dp.name(),
               "Door": 'doortestp09/testts/t1r228',
               "MntGrp": 'nxsmntgrp'}

        rs = self.openRecSelector()
        rs.configDevice = val["ConfigDevice"]
        rs.door = val["Door"]
        rs.mntGrp = val["MntGrp"]
        self.assertEqual(rs.configDevice, val["ConfigDevice"])
        self.assertEqual(rs.door, val["Door"])

        self.assertEqual(rs.availableMntGrps(), [])

        try:
            tpool2 = TestPoolSetUp.TestPoolSetUp(
                "pooltestp09/testts/t2r228", "POOLTESTS2")
            tpool2.setUp()

            db = tango.Database()
            db.put_device_property(
                list(self._ms.ms.keys())[0],
                {'PoolNames': [
                    tpool2.dp.name(), self._pool.dp.name()]})
            pool = self._pool.dp
            pool2 = tpool2.dp
            self._ms.dps[list(self._ms.ms.keys())[0]].Init()

            self.assertEqual(rs.availableMntGrps(), [])
            arr1 = [
                {"name": "test/ct/01", "full_name": "mntgrp_01e"},
                {"name": "test/ct/02", "full_name": "mntgrp_02att"},
                {"name": "test/ct/03", "full_name": "mntgrp_03value"},
                {"name": "test/ct/04", "full_name": "mntgrp_04/13"},
                {"name": "null", "full_name": "mntgrp_04"},
            ]

            arr2 = [
                {"name": "test/ct/011", "full_name": "mntgrp_01e1"},
                {"name": "test/ct/021", "full_name": "mntgrp_02att1"},
                {"name": "test/ct/031", "full_name": "mntgrp_03value1"},
                {"name": "test/ct/041", "full_name": "mntgrp_04/131"},
                {"name": "null", "full_name": "mntgrp_041"},
            ]

            pool.MeasurementGroupList = [json.dumps(a) for a in arr1]
            pool2.MeasurementGroupList = [json.dumps(a) for a in arr2]

            self._ms.dps[
                list(self._ms.ms.keys())[0]
            ].get_property("PoolNames")["PoolNames"]
            dd = rs.availableMntGrps()

            if set(dd) == set([a["name"] for a in arr1]):
                arr = arr1
                self.assertEqual(set(dd), set([a["name"] for a in arr]))
            else:
                arr = arr2
                self.assertEqual(set(dd), set([a["name"] for a in arr]))

            for ar in arr1:

                MSUtils.setEnv('ActiveMntGrp', ar["name"],
                               list(self._ms.ms.keys())[0])
                dd = rs.availableMntGrps()
                self.assertEqual(dd[0], ar["name"])
                if arr1 == arr or ar["name"] != 'null':
                    self.assertEqual(set(dd), set([a["name"] for a in arr1]))
                else:
                    self.assertEqual(set(dd), set([a["name"] for a in arr]))

            for ar in arr2:
                MSUtils.setEnv('ActiveMntGrp', ar["name"],
                               list(self._ms.ms.keys())[0])
                dd = rs.availableMntGrps()
                self.assertEqual(dd[0], ar["name"])
                if arr2 == arr or ar["name"] != 'null':
                    self.assertEqual(set(dd), set([a["name"] for a in arr2]))
                else:
                    self.assertEqual(set(dd), set([a["name"] for a in arr]))
        finally:
            tpool2.tearDown()

    # deleteProfile test
    def test_deleteProfile(self):
        fun = sys._getframe().f_code.co_name
        print("Run: %s.%s() " % (self.__class__.__name__, fun))
        val = {"ConfigDevice": self._cf.dp.name(),
               "WriterDevice": self._wr.dp.name(),
               "Door": 'doortestp09/testts/t1r228',
               "MntGrp": 'nxsmntgrp'}

        rs = self.openRecSelector()
        rs.configDevice = val["ConfigDevice"]
        rs.door = val["Door"]
        rs.mntGrp = val["MntGrp"]
        self.assertEqual(rs.configDevice, val["ConfigDevice"])
        self.assertEqual(rs.door, val["Door"])

        db = tango.Database()
        db.put_device_property(list(self._ms.ms.keys())[0],
                               {'PoolNames': self._pool.dp.name()})
        pool = self._pool.dp
        self._ms.dps[list(self._ms.ms.keys())[0]].Init()

        self.assertEqual(rs.availableMntGrps(), [])

        arr = [
            {"full_name": "test/ct/01", "name": "mntgrp_01e"},
            {"full_name": "test/ct/02", "name": "mntgrp_02att"},
            {"full_name": "test/ct/03", "name": "mntgrp_03value"},
            {"full_name": "test/ct/04", "name": "mntgrp_04_13"},
            {"full_name": "null", "name": "mntgrp_04"},
        ]

        pool.MeasurementGroupList = [json.dumps(a) for a in arr]

        dd2 = rs.availableMntGrps()
        self.assertEqual(set(dd2), set([a["name"] for a in arr]))

        self._cf.dp.Init()
        self._cf.dp.SetCommandVariable(["SELDICT", json.dumps(self.mysel2)])
        sl2 = self._cf.dp.availableSelections()

        dl = []
        mgs = [ar["name"] for ar in arr] + list(self.mysel2.keys())
        # print mgs
        for ar in mgs:
            MSUtils.setEnv('ActiveMntGrp', ar, list(self._ms.ms.keys())[0])
            rs.deleteProfile(ar)
            dl.append(ar)
            self.assertEqual(MSUtils.getEnv(
                'ActiveMntGrp', list(self._ms.ms.keys())[0]), "")
            dd = rs.availableMntGrps()
            self.assertEqual(set(dd), set(dd2) - set(dl))
            sl = self._cf.dp.availableSelections()
            self.assertEqual(set(sl), set(sl2) - set(dl))

    # deleteProfile test
    def test_deleteProfile_twopools(self):
        fun = sys._getframe().f_code.co_name
        print("Run: %s.%s() " % (self.__class__.__name__, fun))
        val = {"ConfigDevice": self._cf.dp.name(),
               "WriterDevice": self._wr.dp.name(),
               "Door": 'doortestp09/testts/t1r228',
               "MntGrp": 'nxsmntgrp'}

        rs = self.openRecSelector()
        rs.configDevice = val["ConfigDevice"]
        rs.door = val["Door"]
        rs.mntGrp = val["MntGrp"]
        self.assertEqual(rs.configDevice, val["ConfigDevice"])
        self.assertEqual(rs.door, val["Door"])

        self.assertEqual(rs.availableMntGrps(), [])

        try:
            tpool2 = TestPoolSetUp.TestPoolSetUp(
                "pooltestp09/testts/t2r228", "POOLTESTS2")
            tpool2.setUp()

            db = tango.Database()
            db.put_device_property(
                list(self._ms.ms.keys())[0],
                {
                    'PoolNames': [
                        tpool2.dp.name(), self._pool.dp.name()]})
            pool = self._pool.dp
            pool2 = tpool2.dp
            self._ms.dps[list(self._ms.ms.keys())[0]].Init()

            self.assertEqual(rs.availableMntGrps(), [])

            arr = [
                {"full_name": "test/ct/01", "name": "mntgrp_01e"},
                {"full_name": "test/ct/02", "name": "mntgrp_02att"},
                {"full_name": "test/ct/03", "name": "mntgrp_03value"},
                {"full_name": "test/ct/04", "name": "mntgrp_04_13"},
                {"full_name": "null", "name": "mntgrp_04"},
            ]

            arr2 = [
                {"full_name": "test/ct/011", "name": "mntgrp_01e1"},
                {"full_name": "test/ct/021", "name": "mntgrp_02att"},
                {"full_name": "test/ct/031", "name": "mntgrp_03value1"},
                {"full_name": "test/ct/041", "name": "mntgrp_04/131"},
                {"full_name": "null", "name": "mntgrp_04"},
            ]

            pool.MeasurementGroupList = [json.dumps(a) for a in arr]
            pool2.MeasurementGroupList = [json.dumps(a) for a in arr2]

            MSUtils.setEnv(
                'ActiveMntGrp', arr[0]["name"], list(self._ms.ms.keys())[0])

            dd1 = [json.loads(mg)["name"]
                   for mg in pool.MeasurementGroupList]
            dd2 = [json.loads(mg)["name"]
                   for mg in pool2.MeasurementGroupList]
            self.assertEqual(set(dd1), set([a["name"] for a in arr]))
            self.assertEqual(set(dd2), set([a["name"] for a in arr2]))

            self._cf.dp.Init()
            self._cf.dp.SetCommandVariable(
                ["SELDICT", json.dumps(self.mysel2)])
            sl2 = self._cf.dp.availableSelections()

            dl = []
            mgs = [ar["name"] for ar in arr] + list(self.mysel2.keys())
            for ar in mgs:
                MSUtils.setEnv('ActiveMntGrp', ar, list(self._ms.ms.keys())[0])
                rs.deleteProfile(ar)
                dl.append(ar)
                self.assertEqual(MSUtils.getEnv(
                    'ActiveMntGrp', list(self._ms.ms.keys())[0]), "")
                dd = [json.loads(mg)["name"]
                      for mg in pool.MeasurementGroupList]
                dd_2 = [json.loads(mg)["name"]
                        for mg in pool2.MeasurementGroupList]
                self.assertEqual(set(dd), set(dd1) - set(dl))
                self.assertEqual(set(dd_2), set(dd2) - set(dl))
                sl = self._cf.dp.availableSelections()
                self.assertEqual(set(sl), set(sl2) - set(dl))

            dl = []
            mgs = [ar["name"] for ar in arr2] + list(self.mysel2.keys())
            dd1 = [json.loads(mg)["name"] for mg in pool.MeasurementGroupList]
            dd2 = [json.loads(mg)["name"] for mg in pool2.MeasurementGroupList]
            sl2 = self._cf.dp.availableSelections()
            for ar in mgs:
                MSUtils.setEnv('ActiveMntGrp', ar, list(self._ms.ms.keys())[0])
                rs.deleteProfile(ar)
                dl.append(ar)
                self.assertEqual(MSUtils.getEnv(
                    'ActiveMntGrp', list(self._ms.ms.keys())[0]), "")
                dd = [json.loads(mg)["name"]
                      for mg in pool.MeasurementGroupList]
                dd_2 = [json.loads(mg)["name"]
                        for mg in pool2.MeasurementGroupList]
                self.assertEqual(set(dd), set(dd1) - set(dl))
                self.assertEqual(set(dd_2), set(dd2) - set(dl))
                sl = self._cf.dp.availableSelections()
                self.assertEqual(set(sl), set(sl2) - set(dl))

        finally:
            tpool2.tearDown()

    # test
    def test_preselectedComponents(self):
        fun = sys._getframe().f_code.co_name
        print("Run: %s.%s() " % (self.__class__.__name__, fun))
        val = {"ConfigDevice": self._cf.dp.name(),
               "WriterDevice": self._wr.dp.name(),
               "Door": 'doortestp09/testts/t1r228',
               "MntGrp": 'nxsmntgrp'}

        for i in range(6):
            rs = self.openRecSelector()
            rs.configDevice = val["ConfigDevice"]
            rs.door = val["Door"]
            rs.mntGrp = val["MntGrp"]
            self.assertEqual(rs.configDevice, val["ConfigDevice"])
            self.assertEqual(rs.door, val["Door"])

            cps = {}
            lcp = self._rnd.randint(1, 40)
            for i in range(lcp):
                cps[self.getRandomName(10)] = bool(self._rnd.randint(0, 1))
            mp = json.loads(rs.profileConfiguration)
            mp["ComponentPreselection"] = json.dumps(cps)
            rs.profileConfiguration = str(json.dumps(mp))
            self.dump(rs)

            ac = rs.preselectedComponents()
            mp = json.loads(rs.profileConfiguration)
            self.compareToDump(
                rs,
                ["ComponentPreselection", "PreselectingDataSources"])
            self.assertEqual(set(self.value(rs, "PreselectingDataSources")),
                             set(self.getDump("PreselectingDataSources")))
            ndss = json.loads(mp["ComponentPreselection"])

            acp = []
            for ds in cps.keys():
                self.assertTrue(ds in ndss.keys())
                self.assertEqual(ndss[ds], cps[ds])
                if ndss[ds]:
                    acp.append(ds)

            self.assertEqual(set(ac), set(acp))

    # test
    def test_selectedcomponents(self):
        fun = sys._getframe().f_code.co_name
        print("Run: %s.%s() " % (self.__class__.__name__, fun))
        val = {"ConfigDevice": self._cf.dp.name(),
               "WriterDevice": self._wr.dp.name(),
               "Door": 'doortestp09/testts/t1r228',
               "MntGrp": 'nxsmntgrp'}

        for i in range(6):
            rs = self.openRecSelector()
            rs.configDevice = val["ConfigDevice"]
            rs.door = val["Door"]
            rs.mntGrp = val["MntGrp"]
            rs.writerDevice = val["WriterDevice"]
            self.assertEqual(rs.configDevice, val["ConfigDevice"])
            self.assertEqual(rs.door, val["Door"])

            db = tango.Database()
            db.put_device_property(list(self._ms.ms.keys())[0],
                                   {'PoolNames': self._pool.dp.name()})
            pool = self._pool.dp
            pool.ExpChannelList = []
            self._ms.dps[list(self._ms.ms.keys())[0]].Init()

            mp = json.loads(rs.profileConfiguration)
            mp["OrderedChannels"] = json.dumps([])
            rs.profileConfiguration = str(json.dumps(mp))

            cps = {}
            dss = {}
            lcp = self._rnd.randint(1, 40)
            lds = self._rnd.randint(1, 40)
            for i in range(lcp):
                cps[self.getRandomName(10)] = bool(self._rnd.randint(0, 1))
            for i in range(lds):
                dss[self.getRandomName(10)] = bool(self._rnd.randint(0, 1))
            ddss = self._rnd.sample(list(dss.keys()), self._rnd.randint(
                1, len(list(dss.keys()))))
            dcps = dict(cps)
            for ds in ddss:
                dcps[ds] = bool(self._rnd.randint(0, 1))

            self._cf.dp.SetCommandVariable(["CPDICT", json.dumps(dcps)])
            self._cf.dp.SetCommandVariable(["DSDICT", json.dumps(dss)])

            mp = json.loads(rs.profileConfiguration)
            mp["ComponentSelection"] = json.dumps(cps)
            mp["DataSourceSelection"] = json.dumps(dss)
            rs.profileConfiguration = str(json.dumps(mp))
            mp = json.loads(rs.profileConfiguration)

            ndss = json.loads(mp["DataSourceSelection"])
            common = set(cps.keys()) & set(list(dss.keys()))
            self.dump(rs)

            ncps = json.loads(mp["ComponentSelection"])
            ndss = json.loads(mp["DataSourceSelection"])
            tdss = [ds for ds in ndss if ndss[ds]]
            tcps = [cp for cp in ncps if ncps[cp]]

            pmcp = rs.selectedComponents()
            self.assertEqual(len(set(cps.keys())),
                             len(set(ncps.keys()) | set(common)))
            for key in cps.keys():
                if key not in common:
                    self.assertTrue(key in ncps.keys())
                    self.assertEqual(ncps[key], cps[key])
            self.compareToDumpJSON(rs, ["ComponentSelection"])
            ac = self._cf.dp.availableComponents()
            for cp in pmcp:
                self.assertTrue(cp in ac)
            mfcp = set(tcps) | (set(tdss) & set(ac))
            self.assertEqual(set(pmcp), set(mfcp))

    # test
    def test_componentDescription_unknown(self):
        fun = sys._getframe().f_code.co_name
        print("Run: %s.%s() " % (self.__class__.__name__, fun))
        val = {"ConfigDevice": self._cf.dp.name(),
               "WriterDevice": self._wr.dp.name(),
               "Door": 'doortestp09/testts/t1r228',
               "MntGrp": 'nxsmntgrp'}

        rs = self.openRecSelector()
        rs.configDevice = val["ConfigDevice"]
        rs.door = val["Door"]
        rs.mntGrp = val["MntGrp"]
        rs.writerDevice = val["WriterDevice"]
        self.assertEqual(rs.configDevice, val["ConfigDevice"])
        self.assertEqual(rs.door, val["Door"])
        db = tango.Database()
        db.put_device_property(list(self._ms.ms.keys())[0],
                               {'PoolNames': self._pool.dp.name()})
        pool = self._pool.dp
        pool.ExpChannelList = []
        self._ms.dps[list(self._ms.ms.keys())[0]].Init()

        mp = json.loads(rs.profileConfiguration)
        mp["OrderedChannels"] = json.dumps([])
        rs.profileConfiguration = str(json.dumps(mp))

        cps = {}
        dss = {}
        # lcp = self._rnd.randint(1, 40)
        # lds = self._rnd.randint(1, 40)

        dsdict = {
            "ann": self.mydss["ann"]
        }

        self._cf.dp.SetCommandVariable(["CPDICT", json.dumps({})])
        self._cf.dp.SetCommandVariable(["DSDICT", json.dumps(dsdict)])

        mp = json.loads(rs.profileConfiguration)
        mp["ComponentSelection"] = json.dumps(cps)
        mp["DataSourceSelection"] = json.dumps(dss)
        rs.profileConfiguration = str(json.dumps(mp))
        mp = json.loads(rs.profileConfiguration)

        # ndss =
        json.loads(mp["DataSourceSelection"])
        # common = set(cps) & set(dss)
        self.dump(rs)

        # ncps =
        json.loads(mp["ComponentSelection"])
        # ndss =
        json.loads(mp["DataSourceSelection"])
        # tdss = [ds for ds in ndss if ndss[ds]]
        # tcps = [cp for cp in ncps if ncps[cp]]

        self.assertEqual(rs.componentDescription(), '[{}]')
        mp = json.loads(rs.profileConfiguration)
        mp["ComponentSelection"] = json.dumps({"unknown": True})
        rs.profileConfiguration = str(json.dumps(mp))
        self.assertEqual(rs.componentDescription(), '[{}]')
        mp = json.loads(rs.profileConfiguration)
        mp["DataSourceSelection"] = json.dumps({"unknown": True})
        rs.profileConfiguration = str(json.dumps(mp))
        self.assertEqual(rs.componentDescription(), '[{}]')
        self._cf.dp.SetCommandVariable(["MCPLIST", json.dumps(["unknown"])])
        self.assertEqual(rs.componentDescription(), '[{}]')

    # test
    def test_componentDescription_full(self):
        fun = sys._getframe().f_code.co_name
        print("Run: %s.%s() " % (self.__class__.__name__, fun))
        val = {"ConfigDevice": self._cf.dp.name(),
               "WriterDevice": self._wr.dp.name(),
               "Door": 'doortestp09/testts/t1r228',
               "MntGrp": 'nxsmntgrp'}

        for i in range(6):
            rs = self.openRecSelector()
            rs.configDevice = val["ConfigDevice"]
            rs.door = val["Door"]
            rs.mntGrp = val["MntGrp"]
            rs.writerDevice = val["WriterDevice"]
            self.assertEqual(rs.configDevice, val["ConfigDevice"])
            self.assertEqual(rs.door, val["Door"])
            db = tango.Database()
            db.put_device_property(list(self._ms.ms.keys())[0],
                                   {'PoolNames': self._pool.dp.name()})
            pool = self._pool.dp
            pool.ExpChannelList = []
            self._ms.dps[list(self._ms.ms.keys())[0]].Init()

            mp = json.loads(rs.profileConfiguration)
            mp["OrderedChannels"] = json.dumps([])
            rs.profileConfiguration = str(json.dumps(mp))

            # dsdict = {
            #     "ann": self.mydss["ann"]
            # }

            cps = {}
            dss = {}
            # lcp = self._rnd.randint(1, 40)
            # lds = self._rnd.randint(1, 40)

            self._cf.dp.SetCommandVariable(["CPDICT", json.dumps(self.mycps)])
            self._cf.dp.SetCommandVariable(["DSDICT", json.dumps(self.mydss)])

            ncps = self._rnd.randint(1, len(list(self.mycps.keys())) - 1)
            lcps = self._rnd.sample(list(self.mycps.keys()), ncps)
            for cp in lcps:
                cps[cp] = bool(self._rnd.randint(0, 1))

            mncps = self._rnd.randint(1, len(list(self.mycps.keys())) - 1)
            mcps = self._rnd.sample(list(self.mycps.keys()), mncps)

            # tdss = [ds for ds in dss if dss[ds]]
            # tcps = [cp for cp in cps if cps[cp]]

            self._cf.dp.SetCommandVariable(["MCPLIST", json.dumps(mcps)])
            self._cf.dp.SetCommandVariable(["CPDICT", json.dumps(self.mycps)])
            self._cf.dp.SetCommandVariable(["DSDICT", json.dumps(self.mydss)])

            mp = json.loads(rs.profileConfiguration)
            mp["ComponentSelection"] = json.dumps(cps)
            mp["DataSourceSelection"] = json.dumps(dss)
            rs.profileConfiguration = str(json.dumps(mp))
            mp = json.loads(rs.profileConfiguration)
            # ndss =
            json.loads(mp["DataSourceSelection"])
            # common = set(cps) & set(dss)
            self.dump(rs)

            res = json.loads(rs.componentDescription())
            self.checkCP(res, list(self.rescps.keys()))

    # updateProfile test
    def test_componentdatasources(self):
        fun = sys._getframe().f_code.co_name
        print("Run: %s.%s() " % (self.__class__.__name__, fun))
        val = {"ConfigDevice": self._cf.dp.name(),
               "WriterDevice": self._wr.dp.name(),
               "Door": 'doortestp09/testts/t1r228',
               "MntGrp": 'nxsmntgrp'}

        for i in range(6):
            rs = self.openRecSelector()
            rs.configDevice = val["ConfigDevice"]
            rs.door = val["Door"]
            rs.mntGrp = val["MntGrp"]
            rs.writerDevice = val["WriterDevice"]
            self.assertEqual(rs.configDevice, val["ConfigDevice"])
            self.assertEqual(rs.door, val["Door"])
            db = tango.Database()
            db.put_device_property(list(self._ms.ms.keys())[0],
                                   {'PoolNames': self._pool.dp.name()})
            pool = self._pool.dp
            pool.ExpChannelList = []
            self._ms.dps[list(self._ms.ms.keys())[0]].Init()

            mp = json.loads(rs.profileConfiguration)
            mp["OrderedChannels"] = json.dumps([])
            rs.profileConfiguration = str(json.dumps(mp))

            cps = {}
            dss = {}
            # lcp = self._rnd.randint(1, 40)
            lds = self._rnd.randint(1, 40)

            self._cf.dp.SetCommandVariable(["CPDICT", json.dumps(self.mycps)])
            self._cf.dp.SetCommandVariable(["DSDICT", json.dumps(self.mydss)])

            ncps = self._rnd.randint(1, len(list(self.mycps.keys())) - 1)
            lcps = self._rnd.sample(list(self.mycps.keys()), ncps)
            for cp in lcps:
                cps[cp] = bool(self._rnd.randint(0, 1))

            ndss = self._rnd.randint(1, len(list(self.mycps.keys())) - 1)
            ldss = self._rnd.sample(list(self.mycps.keys()), ndss)
            for ds in ldss:
                if ds in self.mydss.keys():
                    dss[ds] = bool(self._rnd.randint(0, 1))

            mncps = self._rnd.randint(1, len(list(self.mycps.keys())) - 1)
            mcps = self._rnd.sample(list(self.mycps.keys()), mncps)

            # tdss = [ds for ds in dss if dss[ds]]
            # tcps = [cp for cp in cps if cps[cp]]
            mp = json.loads(rs.profileConfiguration)
            mp["ComponentSelection"] = json.dumps(cps)
            mp["DataSourceSelection"] = json.dumps(dss)
            rs.profileConfiguration = str(json.dumps(mp))
            mp = json.loads(rs.profileConfiguration)

            self._cf.dp.SetCommandVariable(["MCPLIST", json.dumps(mcps)])
            ndss = json.loads(mp["DataSourceSelection"])
            # common = set(cps) & set(dss)
            self.dump(rs)

            dds = rs.componentDataSources()
            res = json.loads(rs.componentDescription())
            wcps = rs.components
            mdds = set()
            for cp, mdss in res[0].items():
                if cp in wcps:
                    if isinstance(mdss, dict):
                        for ds, lds in mdss.items():
                            for ld in lds:
                                if ld[0] == 'STEP':
                                    mdds.add(ds)
                                    break
            self.assertEqual(len(mdds), len(dds))
            self.assertEqual(mdds, set(dds))

    # updateProfile test
    def test_selectedDatasources(self):
        fun = sys._getframe().f_code.co_name
        print("Run: %s.%s() " % (self.__class__.__name__, fun))
        val = {"ConfigDevice": self._cf.dp.name(),
               "WriterDevice": self._wr.dp.name(),
               "Door": 'doortestp09/testts/t1r228',
               "MntGrp": 'nxsmntgrp'}

        for i in range(6):
            rs = self.openRecSelector()
            rs.configDevice = val["ConfigDevice"]
            rs.door = val["Door"]
            rs.mntGrp = val["MntGrp"]
            rs.writerDevice = val["WriterDevice"]
            self.assertEqual(rs.configDevice, val["ConfigDevice"])
            self.assertEqual(rs.door, val["Door"])
            db = tango.Database()
            db.put_device_property(list(self._ms.ms.keys())[0],
                                   {'PoolNames': self._pool.dp.name()})
            pool = self._pool.dp
            pool.ExpChannelList = []
            self._ms.dps[list(self._ms.ms.keys())[0]].Init()

            mp = json.loads(rs.profileConfiguration)
            mp["OrderedChannels"] = json.dumps([])
            rs.profileConfiguration = str(json.dumps(mp))

            cps = {}
            dss = {}
            # lcp = self._rnd.randint(1, 40)
            # lds = self._rnd.randint(1, 40)

            self._cf.dp.SetCommandVariable(["CPDICT", json.dumps(self.mycps)])
            self._cf.dp.SetCommandVariable(["DSDICT", json.dumps(self.mydss)])

            ncps = self._rnd.randint(1, len(list(self.mycps.keys())) - 1)
            lcps = self._rnd.sample(list(self.mycps.keys()), ncps)
            for cp in lcps:
                cps[cp] = bool(self._rnd.randint(0, 1))

            ndss = self._rnd.randint(1, len(list(self.mycps.keys())) - 1)
            ldss = self._rnd.sample(list(self.mycps.keys()), ndss)
            for ds in ldss:
                if ds in self.mydss.keys():
                    dss[ds] = bool(self._rnd.randint(0, 1))

            ndss = self._rnd.randint(1, len(list(self.mydss.keys())) - 1)
            ldss = self._rnd.sample(list(self.mydss.keys()), ndss)
            for ds in ldss:
                if ds in self.mydss.keys():
                    dss[ds] = bool(self._rnd.randint(0, 1))

            mncps = self._rnd.randint(1, len(list(self.mycps.keys())) - 1)
            mcps = self._rnd.sample(list(self.mycps.keys()), mncps)

            mp = json.loads(rs.profileConfiguration)
            mp["ComponentSelection"] = json.dumps(cps)
            mp["DataSourceSelection"] = json.dumps(dss)
            rs.profileConfiguration = str(json.dumps(mp))
            mp = json.loads(rs.profileConfiguration)
            self._cf.dp.SetCommandVariable(["MCPLIST", json.dumps(mcps)])
            ndss = json.loads(mp["DataSourceSelection"])
            # common = set(cps) & set(dss)
            self.dump(rs)

            dds = rs.componentDataSources()
            rdss = rs.selectedDataSources()
            tdss = [ds for ds in dss if dss[ds] and ds not in dds]

            self.assertEqual(set(tdss), set(rdss))
            self.assertEqual(len(tdss), len(rdss))

    # updateProfile test
    def test_datasources(self):
        fun = sys._getframe().f_code.co_name
        print("Run: %s.%s() " % (self.__class__.__name__, fun))
        val = {"ConfigDevice": self._cf.dp.name(),
               "WriterDevice": self._wr.dp.name(),
               "Door": 'doortestp09/testts/t1r228',
               "MntGrp": 'nxsmntgrp'}

        for i in range(6):
            rs = self.openRecSelector()
            rs.configDevice = val["ConfigDevice"]
            rs.door = val["Door"]
            rs.mntGrp = val["MntGrp"]
            rs.writerDevice = val["WriterDevice"]
            self.assertEqual(rs.configDevice, val["ConfigDevice"])
            self.assertEqual(rs.door, val["Door"])
            db = tango.Database()
            db.put_device_property(list(self._ms.ms.keys())[0],
                                   {'PoolNames': self._pool.dp.name()})
            pool = self._pool.dp
            pool.ExpChannelList = []
            self._ms.dps[list(self._ms.ms.keys())[0]].Init()

            mp = json.loads(rs.profileConfiguration)
            mp["OrderedChannels"] = json.dumps([])
            rs.profileConfiguration = str(json.dumps(mp))

            cps = {}
            dss = {}
            # lcp = self._rnd.randint(1, 40)
            # lds = self._rnd.randint(1, 40)

            self._cf.dp.SetCommandVariable(["CPDICT", json.dumps(self.mycps)])
            self._cf.dp.SetCommandVariable(["DSDICT", json.dumps(self.mydss)])

            ncps = self._rnd.randint(1, len(list(self.mycps.keys())) - 1)
            lcps = self._rnd.sample(list(self.mycps.keys()), ncps)
            for cp in lcps:
                cps[cp] = bool(self._rnd.randint(0, 1))

            ndss = self._rnd.randint(1, len(list(self.mycps.keys())) - 1)
            ldss = self._rnd.sample(list(self.mycps.keys()), ndss)
            for ds in ldss:
                if ds in self.mydss.keys():
                    dss[ds] = bool(self._rnd.randint(0, 1))

            ndss = self._rnd.randint(1, len(list(self.mydss.keys())) - 1)
            ldss = self._rnd.sample(list(self.mydss.keys()), ndss)
            for ds in ldss:
                if ds in self.mydss.keys():
                    dss[ds] = bool(self._rnd.randint(0, 1))

            mncps = self._rnd.randint(1, len(list(self.mycps.keys())) - 1)
            mcps = self._rnd.sample(list(self.mycps.keys()), mncps)

            mp = json.loads(rs.profileConfiguration)
            mp["ComponentSelection"] = json.dumps(cps)
            mp["DataSourceSelection"] = json.dumps(dss)
            rs.profileConfiguration = str(json.dumps(mp))
            mp = json.loads(rs.profileConfiguration)
            self._cf.dp.SetCommandVariable(["MCPLIST", json.dumps(mcps)])
            ndss = json.loads(mp["DataSourceSelection"])
            # common = set(cps) & set(dss)
            self.dump(rs)

            mds = rs.dataSources or []
            dds = rs.componentDataSources() or []
            rdss = rs.selectedDataSources() or []

            self.assertEqual(set(mds), set(dds) | set(rdss))

    # test
    def test_selectedcomponents2(self):
        fun = sys._getframe().f_code.co_name
        print("Run: %s.%s() " % (self.__class__.__name__, fun))
        val = {"ConfigDevice": self._cf.dp.name(),
               "WriterDevice": self._wr.dp.name(),
               "Door": 'doortestp09/testts/t1r228',
               "MntGrp": 'nxsmntgrp'}

        for i in range(6):
            rs = self.openRecSelector()
            rs.configDevice = val["ConfigDevice"]
            rs.door = val["Door"]
            rs.mntGrp = val["MntGrp"]
            rs.writerDevice = val["WriterDevice"]
            self.assertEqual(rs.configDevice, val["ConfigDevice"])
            self.assertEqual(rs.door, val["Door"])

            db = tango.Database()
            db.put_device_property(list(self._ms.ms.keys())[0],
                                   {'PoolNames': self._pool.dp.name()})
            pool = self._pool.dp
            pool.ExpChannelList = []
            self._ms.dps[list(self._ms.ms.keys())[0]].Init()

            mp = json.loads(rs.profileConfiguration)
            mp["OrderedChannels"] = json.dumps([])
            rs.profileConfiguration = str(json.dumps(mp))

            mncps = self._rnd.randint(1, len(list(self.mycps.keys())) - 1)
            mcps = [cp for cp in self._rnd.sample(
                list(self.mycps.keys()), mncps)]

            cps = {}
            dss = {}
            lcp = self._rnd.randint(1, 40)
            lds = self._rnd.randint(1, 40)
            for i in range(lcp):
                cps[self.getRandomName(10)] = bool(self._rnd.randint(0, 1))
            for i in range(lds):
                dss[self.getRandomName(10)] = bool(self._rnd.randint(0, 1))
            ddss = self._rnd.sample(list(dss.keys()), self._rnd.randint(
                1, len(list(dss.keys()))))
            dcps = dict(cps)
            for ds in ddss:
                dcps[ds] = bool(self._rnd.randint(0, 1))

            pcps = {}
            plcp = self._rnd.randint(1, 40)
            for i in range(plcp):
                pcps[self.getRandomName(10)] = bool(self._rnd.randint(0, 1))

            self._cf.dp.SetCommandVariable(["CPDICT", json.dumps(dcps)])
            self._cf.dp.SetCommandVariable(["DSDICT", json.dumps(dss)])
            self._cf.dp.SetCommandVariable(["MCPLIST", json.dumps(mcps)])

            mp = json.loads(rs.profileConfiguration)
            mp["ComponentSelection"] = json.dumps(cps)
            mp["DataSourceSelection"] = json.dumps(dss)
            mp["ComponentPreselection"] = json.dumps(cps)
            rs.profileConfiguration = str(json.dumps(mp))
            # ac =
            rs.preselectedComponents()
            mp = json.loads(rs.profileConfiguration)

            # ndss =
            json.loads(mp["DataSourceSelection"])
            # common = set(cps.keys()) & set(list(dss.keys()))
            self.dump(rs)

            # ncps =
            json.loads(mp["ComponentSelection"])
            # ndss =
            json.loads(mp["DataSourceSelection"])
            # tdss = [ds for ds in ndss if ndss[ds]]
            # tcps = [cp for cp in ncps if ncps[cp]]

            rcp = rs.components
            mcp = rs.mandatoryComponents()
            scp = rs.selectedComponents()
            pcp = rs.preselectedComponents()

            self.assertEqual(set(rcp), set(mcp) | set(scp) | set(pcp))

    # updateMntGrp test
    def test_updateMntGrp_empty(self):
        fun = sys._getframe().f_code.co_name
        print("Run: %s.%s() " % (self.__class__.__name__, fun))
        val = {"ConfigDevice": self._cf.dp.name(),
               "WriterDevice": self._wr.dp.name(),
               "Door": 'doortestp09/testts/t1r228',
               "MntGrp": 'nxsmntgrp2'}

        rs = self.openRecSelector()
        rs.configDevice = val["ConfigDevice"]
        rs.door = val["Door"]
        rs.mntGrp = val["MntGrp"]
        rs.writerDevice = val["WriterDevice"]
        self.assertEqual(rs.configDevice, val["ConfigDevice"])
        self.assertEqual(rs.door, val["Door"])

        db = tango.Database()
        db.put_device_property(list(self._ms.ms.keys())[0],
                               {'PoolNames': self._pool.dp.name()})
        pool = self._pool.dp
        pool.ExpChannelList = []
        self._ms.dps[list(self._ms.ms.keys())[0]].Init()

        self.assertEqual(rs.availableMntGrps(), [])

        arr = [
            {"full_name": "test/ct/01/Value", "name": "ct01"},
            {"full_name": "test/ct/02/Value", "name": "ct02"},
            {"full_name": "test/ct/03/value", "name": "ct03"},
            {"full_name": "test/ct/04/value", "name": "ct04"},
            {"full_name": "null/val", "name": "mntgrp_04"},
        ]
        pool.AcqChannelList = [json.dumps(a) for a in arr]

#        self.myAssertRaise(Exception, rs.updateMntGrp)
        for ar in arr:
            tmg = TestMGSetUp.TestMeasurementGroupSetUp(name=val["MntGrp"])
            dv = "/".join(ar["full_name"].split("/")[0:-1])
            smg = {"controllers": {},
                   "monitor": "%s" % dv,
                   "description": "Measurement Group",
                   "timer": "%s" % dv,
                   "label": "nxsmntgrp2"}
            mp = json.loads(rs.profileConfiguration)
            mp["Timer"] = '["%s"]' % ar["name"]
            rs.profileConfiguration = str(json.dumps(mp))
            mp = json.loads(rs.profileConfiguration)

            try:
                self.assertEqual(json.loads(mp["ComponentPreselection"]), {})
                self.assertEqual(json.loads(mp["ComponentSelection"]), {})
                self.assertEqual(json.loads(mp["DataSourceSelection"]), {})
                self.assertEqual(json.loads(mp["UnplottedComponents"]), [])
                self.assertEqual(json.loads(mp["OrderedChannels"]), [])
                self.assertEqual(json.loads(mp["UserData"]), {})
                self.assertEqual(json.loads(mp["Timer"]), [ar["name"]])
                self.assertEqual(mp["MntGrp"], val["MntGrp"])
                jpcnf = rs.updateMntGrp()
                pcnf = json.loads(jpcnf)
                mgdp = tango.DeviceProxy(tmg.new_device_info_writer.name)
                jcnf = mgdp.Configuration
                cnf = json.loads(jcnf)
                mp = json.loads(rs.profileConfiguration)
                self.assertEqual(json.loads(mp["ComponentPreselection"]), {})
                self.assertEqual(json.loads(mp["ComponentSelection"]), {})
                self.assertEqual(json.loads(mp["DataSourceSelection"]), {})
                self.assertEqual(json.loads(mp["UnplottedComponents"]), [])
                self.assertEqual(json.loads(mp["OrderedChannels"]), [])
                self.assertEqual(json.loads(mp["UserData"]), {})
                self.assertEqual(json.loads(mp["Timer"]), [ar["name"]])
                self.assertEqual(mp["MntGrp"], val["MntGrp"])
                self.myAssertDict(smg, cnf)
                self.myAssertDict(smg, pcnf)
                rs.fetchProfile()
                mp = json.loads(rs.profileConfiguration)
                rs.storeProfile()

                rs.mntGrp = "nxsmntgrp"

                rs.profileConfiguration = str(json.dumps({}))
                rs.configDevice = val["ConfigDevice"]
                rs.door = val["Door"]
                rs.mntGrp = val["MntGrp"]
                rs.fetchProfile()
                mp = json.loads(rs.profileConfiguration)
                self.assertEqual(json.loads(mp["ComponentPreselection"]), {})
                self.assertEqual(json.loads(mp["ComponentSelection"]), {})
                self.assertEqual(json.loads(mp["DataSourceSelection"]), {})
                self.assertEqual(json.loads(mp["UnplottedComponents"]), [])
                self.assertEqual(json.loads(mp["OrderedChannels"]), [])
                self.assertEqual(json.loads(mp["UserData"]), {})
                self.assertEqual(json.loads(mp["Timer"]), [ar["name"]])
                self.assertEqual(mp["MntGrp"], "nxsmntgrp2")
            finally:
                rs.deleteProfile(val["MntGrp"])
                tmg.tearDown()

    # updateMntGrp test
    def test_updateMntGrp_merge(self):
        fun = sys._getframe().f_code.co_name
        print("Run: %s.%s() " % (self.__class__.__name__, fun))
        val = {"ConfigDevice": self._cf.dp.name(),
               "WriterDevice": self._wr.dp.name(),
               "Door": 'doortestp09/testts/t1r228',
               "MntGrp": 'nxsmntgrp2'}

        rs = self.openRecSelector()
        self.setProp(rs, "mergeProfilesToMntGrps", [True])
        rs.configDevice = val["ConfigDevice"]
        rs.door = val["Door"]
        rs.mntGrp = val["MntGrp"]
        rs.writerDevice = val["WriterDevice"]
        self.assertEqual(rs.configDevice, val["ConfigDevice"])
        self.assertEqual(rs.door, val["Door"])

        db = tango.Database()
        db.put_device_property(list(self._ms.ms.keys())[0],
                               {'PoolNames': self._pool.dp.name()})
        pool = self._pool.dp
        pool.ExpChannelList = []
        self._ms.dps[list(self._ms.ms.keys())[0]].Init()

        self.assertEqual(rs.availableMntGrps(), [val["MntGrp"]])

        arr = [
            {"full_name": "test/ct/01/Value", "name": "ct01"},
            {"full_name": "test/ct/02/Value", "name": "ct02"},
            {"full_name": "test/ct/03/value", "name": "ct03"},
            {"full_name": "test/ct/04/value", "name": "ct04"},
            {"full_name": "null/val", "name": "mntgrp_04"},
        ]
        pool.AcqChannelList = [json.dumps(a) for a in arr]

#        self.myAssertRaise(Exception, rs.updateMntGrp)
        for ar in arr:
            tmg = TestMGSetUp.TestMeasurementGroupSetUp(name=val["MntGrp"])
            dv = "/".join(ar["full_name"].split("/")[0:-1])
            smg = {"controllers": {},
                   "monitor": "%s" % dv,
                   "description": "Measurement Group",
                   "timer": "%s" % dv,
                   "label": "nxsmntgrp2"}
            mp = json.loads(rs.profileConfiguration)
            mp["Timer"] = '["%s"]' % ar["name"]
            rs.profileConfiguration = str(json.dumps(mp))
            mp = json.loads(rs.profileConfiguration)

            try:
                self.assertEqual(json.loads(mp["ComponentPreselection"]), {})
                self.assertEqual(json.loads(mp["ComponentSelection"]), {})
                self.assertEqual(json.loads(mp["DataSourceSelection"]), {})
                self.assertEqual(json.loads(mp["UnplottedComponents"]), [])
                self.assertEqual(json.loads(mp["OrderedChannels"]), [])
                self.assertEqual(json.loads(mp["UserData"]), {})
                self.assertEqual(json.loads(mp["Timer"]), [ar["name"]])
                self.assertEqual(mp["MntGrp"], val["MntGrp"])
                jpcnf = rs.updateMntGrp()
                pcnf = json.loads(jpcnf)
                mgdp = tango.DeviceProxy(tmg.new_device_info_writer.name)
                jcnf = mgdp.Configuration
                cnf = json.loads(jcnf)
                mp = json.loads(rs.profileConfiguration)
                self.assertEqual(json.loads(mp["ComponentPreselection"]), {})
                self.assertEqual(json.loads(mp["ComponentSelection"]), {})
                self.assertEqual(json.loads(mp["DataSourceSelection"]), {})
                self.assertEqual(json.loads(mp["UnplottedComponents"]), [])
                self.assertEqual(json.loads(mp["OrderedChannels"]), [])
                self.assertEqual(json.loads(mp["UserData"]), {})
                self.assertEqual(json.loads(mp["Timer"]), [ar["name"]])
                self.assertEqual(mp["MntGrp"], val["MntGrp"])
                self.myAssertDict(smg, cnf)
                self.myAssertDict(smg, pcnf)
                rs.fetchProfile()
                mp = json.loads(rs.profileConfiguration)
                rs.storeProfile()

                rs.mntGrp = "nxsmntgrp"

                rs.profileConfiguration = str(json.dumps({}))
                rs.configDevice = val["ConfigDevice"]
                rs.door = val["Door"]
                rs.mntGrp = val["MntGrp"]
                rs.fetchProfile()
                mp = json.loads(rs.profileConfiguration)
                self.assertEqual(json.loads(mp["ComponentPreselection"]), {})
                self.assertEqual(json.loads(mp["ComponentSelection"]), {})
                self.assertEqual(json.loads(mp["DataSourceSelection"]), {})
                self.assertEqual(json.loads(mp["UnplottedComponents"]), [])
                self.assertEqual(json.loads(mp["OrderedChannels"]), [])
                self.assertEqual(json.loads(mp["UserData"]), {})
                self.assertEqual(json.loads(mp["Timer"]), [ar["name"]])
                self.assertEqual(mp["MntGrp"], "nxsmntgrp2")
            finally:
                rs.deleteProfile(val["MntGrp"])
                tmg.tearDown()

    # updateMntGrp test
    def test_updateMntGrp_components_nopool(self):
        fun = sys._getframe().f_code.co_name
        print("Run: %s.%s() " % (self.__class__.__name__, fun))
        val = {"ConfigDevice": self._cf.dp.name(),
               "WriterDevice": self._wr.dp.name(),
               "Door": 'doortestp09/testts/t1r228',
               "MntGrp": 'nxsmntgrp2'}

        wrong = ['nn', 'ann', 'nn2', 'tann1', 'tann0', 'tann1b', 'tann1c',
                 'dim1', 'dim2', 'dim3', 'dim4', 'dim5', 'dim5', 'dim6',
                 'dim7', 'dim8', 'tann1c', 'mycp3', 'exp_t01']

        rs = self.openRecSelector()
        rs.configDevice = val["ConfigDevice"]
        rs.door = val["Door"]
        rs.mntGrp = val["MntGrp"]
        rs.writerDevice = val["WriterDevice"]
        self.assertEqual(rs.configDevice, val["ConfigDevice"])
        self.assertEqual(rs.door, val["Door"])

        db = tango.Database()
        db.put_device_property(list(self._ms.ms.keys())[0],
                               {'PoolNames': self._pool.dp.name()})
        pool = self._pool.dp
        pool.ExpChannelList = []
        self._ms.dps[list(self._ms.ms.keys())[0]].Init()

        self.assertEqual(rs.availableMntGrps(), [])

        arr = [
            {"full_name": "test/ct/01/Value", "name": "ct01"},
            {"full_name": "test/ct/02/Value", "name": "ct02"},
            {"full_name": "test/ct/03/value", "name": "ct03"},
            {"full_name": "test/ct/04/value", "name": "ct04"},
            {"full_name": "null/val", "name": "mntgrp_04"},
        ]
        pool.AcqChannelList = [json.dumps(a) for a in arr]
        # print "pool", pool.name()
#        if ct0? exists no error
#        self.myAssertRaise(Exception, rs.updateMntGrp)
        self._cf.dp.SetCommandVariable(["CPDICT", json.dumps(self.mycps)])
        self._cf.dp.SetCommandVariable(["DSDICT", json.dumps(self.mydss)])
        for i in range(6):
            ar = arr[i % len(arr)]
            cps = {}
            acps = {}
            dss = {}
            # lcp = self._rnd.randint(1, 40)
            # lds = self._rnd.randint(1, 40)

            self._cf.dp.SetCommandVariable(["CPDICT", json.dumps(self.mycps)])
            self._cf.dp.SetCommandVariable(["DSDICT", json.dumps(self.mydss)])

            ncps = self._rnd.randint(1, len(list(self.mycps.keys())) - 1)
            lcps = self._rnd.sample(list(self.mycps.keys()), ncps)
            for cp in lcps:
                if cp not in wrong:
                    cps[cp] = bool(self._rnd.randint(0, 1))

            ancps = self._rnd.randint(1, len(list(self.mycps.keys())) - 1)
            alcps = self._rnd.sample(list(self.mycps.keys()), ancps)
            for cp in alcps:
                if cp not in wrong:
                    acps[cp] = bool(self._rnd.randint(0, 1))

            ndss = self._rnd.randint(1, len(list(self.mycps.keys())) - 1)
            ldss = self._rnd.sample(list(self.mycps.keys()), ndss)
            for ds in ldss:
                if ds in self.mydss.keys():
                    if ds not in wrong:
                        dss[ds] = bool(self._rnd.randint(0, 1))

            ndss = self._rnd.randint(1, len(list(self.mydss.keys())) - 1)
            ldss = self._rnd.sample(list(self.mydss.keys()), ndss)
            for ds in ldss:
                if ds in self.mydss.keys():
                    if ds not in wrong:
                        dss[ds] = bool(self._rnd.randint(0, 1))

            mncps = self._rnd.randint(1, len(list(self.mycps.keys())) - 1)
            mcps = [cp for cp in self._rnd.sample(
                    list(self.mycps.keys()), mncps) if cp not in wrong]

            mp = json.loads(rs.profileConfiguration)
            mp["ComponentSelection"] = json.dumps(cps)
            mp["ComponentPreselection"] = json.dumps(acps)
            mp["DataSourceSelection"] = json.dumps(dss)
            self._cf.dp.SetCommandVariable(["MCPLIST", json.dumps(mcps)])
            rs.profileConfiguration = str(json.dumps(mp))
            mp = json.loads(rs.profileConfiguration)

            records = {}
            describer = Describer(self._cf.dp, True)
            cpres = describer.components(dstype='CLIENT')
            for grp in cpres:
                for idss in grp.values():
                    for idsrs in idss.values():
                        for idsr in idsrs:
                            records[str(idsr[2])] = "1234"
            dsres = describer.dataSources(list(dss.keys()), dstype='CLIENT')[0]
            for dsr in dsres.values():
                records[str(dsr.record)] = '2345'

            mp = json.loads(rs.profileConfiguration)
            mp["Timer"] = '["%s"]' % ar["name"]
            mp["UserData"] = json.dumps(records)
            rs.profileConfiguration = str(json.dumps(mp))
            mp = json.loads(rs.profileConfiguration)

            tmg = TestMGSetUp.TestMeasurementGroupSetUp(name='nxsmntgrp2')
            dv = "/".join(ar["full_name"].split("/")[0:-1])
            smg = {"controllers": {},
                   "monitor": "%s" % dv,
                   "description": "Measurement Group",
                   "timer": "%s" % dv,
                   "label": "nxsmntgrp2"}
            try:
                self.myAssertDict(json.loads(mp["ComponentPreselection"]),
                                  acps)
                self.myAssertDict(json.loads(mp["ComponentSelection"]), cps)
                self.myAssertDict(json.loads(mp["DataSourceSelection"]), dss)
                self.assertEqual(json.loads(mp["UnplottedComponents"]), [])
                self.assertEqual(json.loads(mp["OrderedChannels"]), [])
                self.myAssertDict(json.loads(mp["UserData"]), records)
                self.assertEqual(json.loads(mp["Timer"]), [ar["name"]])
                self.assertEqual(mp["MntGrp"], "nxsmntgrp2")
                # mdds = set()

                jpcnf = rs.updateMntGrp()
                pcnf = json.loads(jpcnf)
                mgdp = tango.DeviceProxy(tmg.new_device_info_writer.name)
                jcnf = mgdp.Configuration
                cnf = json.loads(jcnf)
                mp = json.loads(rs.profileConfiguration)
                self.myAssertDict(json.loads(mp["ComponentPreselection"]),
                                  acps)
                self.myAssertDict(json.loads(mp["ComponentSelection"]), cps)
                self.myAssertDict(json.loads(mp["DataSourceSelection"]), dss)
                self.assertEqual(json.loads(mp["UnplottedComponents"]), [])
                self.assertEqual(json.loads(mp["OrderedChannels"]), [])
                self.myAssertDict(json.loads(mp["UserData"]), records)
                self.assertEqual(json.loads(mp["Timer"]), [ar["name"]])
                self.assertEqual(mp["MntGrp"], "nxsmntgrp2")
                self.myAssertDict(smg, cnf)
                self.myAssertDict(smg, pcnf)
                rs.mntGrp = "nxsmntgrp"
                rs.profileConfiguration = str(json.dumps({}))
                rs.configDevice = val["ConfigDevice"]
                rs.door = val["Door"]
                rs.mntGrp = val["MntGrp"]
                rs.fetchProfile()
                mp = json.loads(rs.profileConfiguration)
                self.myAssertDict(json.loads(mp["ComponentPreselection"]),
                                  acps)
                self.myAssertDict(json.loads(mp["ComponentSelection"]), cps)
                self.myAssertDict(json.loads(mp["DataSourceSelection"]), dss)
                self.assertEqual(json.loads(mp["UnplottedComponents"]), [])
                self.assertEqual(json.loads(mp["OrderedChannels"]), [])
                self.myAssertDict(json.loads(mp["UserData"]), records)
                self.assertEqual(json.loads(mp["Timer"]), [ar["name"]])
                self.assertEqual(mp["MntGrp"], "nxsmntgrp2")
            finally:
                rs.deleteProfile("nxsmntgrp2")
                try:
                    tmg.tearDown()
                except Exception:
                    pass

    # updateMntGrp test
    def test_updateMntGrp_nodevice(self):
        fun = sys._getframe().f_code.co_name
        print("Run: %s.%s() " % (self.__class__.__name__, fun))
        val = {"ConfigDevice": self._cf.dp.name(),
               "WriterDevice": self._wr.dp.name(),
               "Door": 'doortestp09/testts/t1r228',
               "MntGrp": 'nxsmntgrp2'}

        wrong = ['nn', 'ann', 'nn2', 'tann1b', 'tann1c',
                 'dim1', 'dim2', 'dim3', 'dim4', 'dim5', 'dim5', 'dim6',
                 'dim7', 'dim8', 'tann1c']
        rs = self.openRecSelector()
        rs.configDevice = val["ConfigDevice"]
        rs.door = val["Door"]
        rs.mntGrp = val["MntGrp"]
        rs.writerDevice = val["WriterDevice"]
        self.assertEqual(rs.configDevice, val["ConfigDevice"])
        self.assertEqual(rs.door, val["Door"])

        db = tango.Database()
        db.put_device_property(list(self._ms.ms.keys())[0],
                               {'PoolNames': self._pool.dp.name()})
        pool = self._pool.dp
        pool.ExpChannelList = []
        self._ms.dps[list(self._ms.ms.keys())[0]].Init()

        self.assertEqual(rs.availableMntGrps(), [])

        arr = [
            {"full_name": "test/ct/01/Value", "name": "ct01"},
            {"full_name": "test/ct/02/Value", "name": "ct02"},
            {"full_name": "test/ct/03/value", "name": "ct03"},
            {"full_name": "test/ct/04/value", "name": "ct04"},
            {"full_name": "null/val", "name": "mntgrp_04"},
        ]
        pool.AcqChannelList = [json.dumps(a) for a in arr]

#        self.myAssertRaise(Exception, rs.updateMntGrp)
        self._cf.dp.SetCommandVariable(["CPDICT", json.dumps(self.mycps)])
        self._cf.dp.SetCommandVariable(["DSDICT", json.dumps(self.mydss)])

        ar = arr[0]

        cps = {}
        acps = {}
        dss = {}
        # lcp = self._rnd.randint(1, 40)
        # lds = self._rnd.randint(1, 40)

        self._cf.dp.SetCommandVariable(["CPDICT", json.dumps(self.mycps)])
        self._cf.dp.SetCommandVariable(["DSDICT", json.dumps(self.mydss)])

        for wds in wrong:
            lcps = []
            for cp in lcps:
                cps[cp] = True

            alcps = []
            for cp in alcps:
                acps[cp] = True

            ldss = [wds]
            for ds in ldss:
                if ds in self.mydss.keys():
                    dss[ds] = True

            mcps = []

            mp = json.loads(rs.profileConfiguration)
            mp["ComponentSelection"] = json.dumps(cps)
            mp["ComponentPreselection"] = json.dumps(acps)
            mp["DataSourceSelection"] = json.dumps(dss)
            self._cf.dp.SetCommandVariable(["MCPLIST", json.dumps(mcps)])
            rs.profileConfiguration = str(json.dumps(mp))
            mp = json.loads(rs.profileConfiguration)

            records = {}
            describer = Describer(self._cf.dp, True)
            cpres = describer.components(dstype='CLIENT')
            for grp in cpres:
                for idss in grp.values():
                    for idsrs in idss.values():
                        for idsr in idsrs:
                            records[str(idsr[2])] = "1234"
            dsres = describer.dataSources(list(dss.keys()), dstype='CLIENT')[0]
            for dsr in dsres.values():
                records[str(dsr.record)] = '2345'

            mp = json.loads(rs.profileConfiguration)
            mp["Timer"] = '["%s"]' % ar["name"]
            mp["UserData"] = json.dumps(records)
            rs.profileConfiguration = str(json.dumps(mp))
            mp = json.loads(rs.profileConfiguration)

            tmg = TestMGSetUp.TestMeasurementGroupSetUp(name='nxsmntgrp2')
            # dv = "/".join(ar["full_name"].split("/")[0:-1])
            # smg = {"controllers": {},
            #        "monitor": "%s" % dv,
            #        "description": "Measurement Group",
            #        "timer": "%s" % dv,
            #        "label": "nxsmntgrp2"}
            try:
                self.myAssertDict(json.loads(mp["ComponentPreselection"]),
                                  acps)
                self.myAssertDict(json.loads(mp["ComponentSelection"]), cps)
                self.myAssertDict(json.loads(mp["DataSourceSelection"]), dss)
                self.assertEqual(json.loads(mp["UnplottedComponents"]), [])
                self.assertEqual(json.loads(mp["OrderedChannels"]), [])
                self.myAssertDict(json.loads(mp["UserData"]), records)
                self.assertEqual(json.loads(mp["Timer"]), [ar["name"]])
                self.assertEqual(mp["MntGrp"], "nxsmntgrp2")
                self.myAssertRaise(Exception, rs.updateMntGrp)
            finally:
                rs.deleteProfile("nxsmntgrp2")
                try:
                    tmg.tearDown()
                except Exception:
                    pass

    # updateMntGrp test
    def test_updateMntGrp_nodevice_cp(self):
        fun = sys._getframe().f_code.co_name
        print("Run: %s.%s() " % (self.__class__.__name__, fun))
        val = {"ConfigDevice": self._cf.dp.name(),
               "WriterDevice": self._wr.dp.name(),
               "Door": 'doortestp09/testts/t1r228',
               "MntGrp": 'nxsmntgrp2'}

        wrong = ['mycp3']
        rs = self.openRecSelector()
        rs.configDevice = val["ConfigDevice"]
        rs.door = val["Door"]
        rs.mntGrp = val["MntGrp"]
        rs.writerDevice = val["WriterDevice"]
        self.assertEqual(rs.configDevice, val["ConfigDevice"])
        self.assertEqual(rs.door, val["Door"])

        db = tango.Database()
        db.put_device_property(list(self._ms.ms.keys())[0],
                               {'PoolNames': self._pool.dp.name()})
        pool = self._pool.dp
        pool.ExpChannelList = []
        self._ms.dps[list(self._ms.ms.keys())[0]].Init()

        self.assertEqual(rs.availableMntGrps(), [])

        arr = [
            {"full_name": "test/ct/01/Value", "name": "ct01"},
            {"full_name": "test/ct/02/Value", "name": "ct02"},
            {"full_name": "test/ct/03/value", "name": "ct03"},
            {"full_name": "test/ct/04/value", "name": "ct04"},
            {"full_name": "null/val", "name": "mntgrp_04"},
        ]
        pool.AcqChannelList = [json.dumps(a) for a in arr]

#        self.myAssertRaise(Exception, rs.updateMntGrp)
        self._cf.dp.SetCommandVariable(["CPDICT", json.dumps(self.mycps)])
        self._cf.dp.SetCommandVariable(["DSDICT", json.dumps(self.mydss)])

        ar = arr[0]

        cps = {}
        acps = {}
        dss = {}
        # lcp = self._rnd.randint(1, 40)
        # lds = self._rnd.randint(1, 40)

        self._cf.dp.SetCommandVariable(["CPDICT", json.dumps(self.mycps)])
        self._cf.dp.SetCommandVariable(["DSDICT", json.dumps(self.mydss)])

        for wds in wrong:
            lcps = [wds]
            for cp in lcps:
                cps[cp] = True

            alcps = []
            for cp in alcps:
                acps[cp] = True

            ldss = []
            for ds in ldss:
                if ds in self.mydss.keys():
                    dss[ds] = True

            mcps = []

            mp = json.loads(rs.profileConfiguration)
            mp["ComponentSelection"] = json.dumps(cps)
            mp["ComponentPreselection"] = json.dumps(acps)
            mp["DataSourceSelection"] = json.dumps(dss)
            self._cf.dp.SetCommandVariable(["MCPLIST", json.dumps(mcps)])
            rs.profileConfiguration = str(json.dumps(mp))
            mp = json.loads(rs.profileConfiguration)

            records = {}
            describer = Describer(self._cf.dp, True)
            cpres = describer.components(dstype='CLIENT')
            for grp in cpres:
                for idss in grp.values():
                    for idsrs in idss.values():
                        for idsr in idsrs:
                            records[str(idsr[2])] = "1234"
            dsres = describer.dataSources(list(dss.keys()), dstype='CLIENT')[0]
            for dsr in dsres.values():
                records[str(dsr.record)] = '2345'

            mp = json.loads(rs.profileConfiguration)
            mp["Timer"] = '["%s"]' % ar["name"]
            mp["UserData"] = json.dumps(records)
            rs.profileConfiguration = str(json.dumps(mp))
            mp = json.loads(rs.profileConfiguration)

            tmg = TestMGSetUp.TestMeasurementGroupSetUp(name='nxsmntgrp2')
            # dv = "/".join(ar["full_name"].split("/")[0:-1])
            # smg = {"controllers": {},
            #        "monitor": "%s" % dv,
            #        "description": "Measurement Group",
            #        "timer": "%s" % dv,
            #        "label": "nxsmntgrp2"}
            try:
                self.myAssertDict(json.loads(mp["ComponentPreselection"]),
                                  acps)
                self.myAssertDict(json.loads(mp["ComponentSelection"]), cps)
                self.myAssertDict(json.loads(mp["DataSourceSelection"]), dss)
                self.assertEqual(json.loads(mp["UnplottedComponents"]), [])
                self.assertEqual(json.loads(mp["OrderedChannels"]), [])
                self.myAssertDict(json.loads(mp["UserData"]), records)
                self.assertEqual(json.loads(mp["Timer"]), [ar["name"]])
                self.assertEqual(mp["MntGrp"], "nxsmntgrp2")
                self.myAssertRaise(Exception, rs.updateMntGrp)
            finally:
                try:
                    tmg.tearDown()
                except Exception:
                    pass

    # updateMntGrp test
    def test_updateMntGrp_wrongdevice(self):
        fun = sys._getframe().f_code.co_name
        print("Run: %s.%s() " % (self.__class__.__name__, fun))
        val = {"ConfigDevice": self._cf.dp.name(),
               "WriterDevice": self._wr.dp.name(),
               "Door": 'doortestp09/testts/t1r228',
               "MntGrp": 'nxsmntgrp2'}

        wrong = ['tann1', 'tann0']
        rs = self.openRecSelector()
        rs.configDevice = val["ConfigDevice"]
        rs.door = val["Door"]
        rs.mntGrp = val["MntGrp"]
        rs.writerDevice = val["WriterDevice"]
        self.assertEqual(rs.configDevice, val["ConfigDevice"])
        self.assertEqual(rs.door, val["Door"])

        db = tango.Database()
        db.put_device_property(list(self._ms.ms.keys())[0],
                               {'PoolNames': self._pool.dp.name()})
        pool = self._pool.dp
        pool.ExpChannelList = []
        self._ms.dps[list(self._ms.ms.keys())[0]].Init()

        self.assertEqual(rs.availableMntGrps(), [])

        arr = [
            {"full_name": "test/ct/01/Value", "name": "ct01"},
            {"full_name": "test/ct/02/Value", "name": "ct02"},
            {"full_name": "test/ct/03/value", "name": "ct03"},
            {"full_name": "test/ct/04/value", "name": "ct04"},
            {"full_name": "null/val", "name": "mntgrp_04"},
        ]
        pool.AcqChannelList = [json.dumps(a) for a in arr]

#        self.myAssertRaise(Exception, rs.updateMntGrp)
        self._cf.dp.SetCommandVariable(["CPDICT", json.dumps(self.mycps)])
        self._cf.dp.SetCommandVariable(["DSDICT", json.dumps(self.mydss)])

        ar = arr[0]

        cps = {}
        acps = {}
        dss = {}
        # lcp = self._rnd.randint(1, 40)
        # lds = self._rnd.randint(1, 40)

        self._cf.dp.SetCommandVariable(["CPDICT", json.dumps(self.mycps)])
        self._cf.dp.SetCommandVariable(["DSDICT", json.dumps(self.mydss)])

        for wds in wrong:
            lcps = []
            for cp in lcps:
                cps[cp] = True

            alcps = []
            for cp in alcps:
                acps[cp] = True

            ldss = [wds]
            for ds in ldss:
                if ds in self.mydss.keys():
                    dss[ds] = True

            mcps = []

            mp = json.loads(rs.profileConfiguration)
            mp["ComponentSelection"] = json.dumps(cps)
            mp["ComponentPreselection"] = json.dumps(acps)
            mp["DataSourceSelection"] = json.dumps(dss)
            self._cf.dp.SetCommandVariable(["MCPLIST", json.dumps(mcps)])
            rs.profileConfiguration = str(json.dumps(mp))
            mp = json.loads(rs.profileConfiguration)

            records = {}
            describer = Describer(self._cf.dp, True)
            cpres = describer.components(dstype='CLIENT')
            for grp in cpres:
                for idss in grp.values():
                    for idsrs in idss.values():
                        for idsr in idsrs:
                            records[str(idsr[2])] = "1234"
            dsres = describer.dataSources(list(dss.keys()), dstype='CLIENT')[0]
            for dsr in dsres.values():
                records[str(dsr.record)] = '2345'

            mp = json.loads(rs.profileConfiguration)
            mp["Timer"] = '["%s"]' % ar["name"]
            mp["UserData"] = json.dumps(records)
            rs.profileConfiguration = str(json.dumps(mp))
            mp = json.loads(rs.profileConfiguration)

            tmg = TestMGSetUp.TestMeasurementGroupSetUp(name='nxsmntgrp2')
            # dv = "/".join(ar["full_name"].split("/")[0:-1])
            # smg = {"controllers": {},
            #        "monitor": "%s" % dv,
            #        "description": "Measurement Group",
            #        "timer": "%s" % dv,
            #        "label": "nxsmntgrp2"}
            try:
                self.myAssertDict(json.loads(mp["ComponentPreselection"]),
                                  acps)
                self.myAssertDict(json.loads(mp["ComponentSelection"]), cps)
                self.myAssertDict(json.loads(mp["DataSourceSelection"]), dss)
                self.assertEqual(json.loads(mp["UnplottedComponents"]), [])
                self.assertEqual(json.loads(mp["OrderedChannels"]), [])
                self.myAssertDict(json.loads(mp["UserData"]), records)
                self.assertEqual(json.loads(mp["Timer"]), [ar["name"]])
                self.assertEqual(mp["MntGrp"], "nxsmntgrp2")
                self.myAssertRaise(Exception, rs.updateMntGrp)
            finally:
                try:
                    tmg.tearDown()
                except Exception:
                    pass

    # updateMntGrp test
    def test_updateMntGrp_components_nopool_tango_masterfirst(self):
        fun = sys._getframe().f_code.co_name
        print("Run: %s.%s() " % (self.__class__.__name__, fun))
        val = {"ConfigDevice": self._cf.dp.name(),
               "WriterDevice": self._wr.dp.name(),
               "Door": 'doortestp09/testts/t1r228',
               "MntGrp": 'nxsmntgrp2'}

        wrong = []
        rs = self.openRecSelector()
        self.setProp(rs, "masterTimerFirst", [True])
        rs.configDevice = val["ConfigDevice"]
        rs.door = val["Door"]
        rs.mntGrp = val["MntGrp"]
        rs.writerDevice = val["WriterDevice"]
        self.assertEqual(rs.configDevice, val["ConfigDevice"])
        self.assertEqual(rs.door, val["Door"])

        db = tango.Database()
        db.put_device_property(list(self._ms.ms.keys())[0],
                               {'PoolNames': self._pool.dp.name()})
        pool = self._pool.dp
        pool.ExpChannelList = []
        self._ms.dps[list(self._ms.ms.keys())[0]].Init()

        self.assertEqual(rs.availableMntGrps(), [])

        arr = [
            {"full_name": "test/ct/01/Value", "name": "ct01"},
            {"full_name": "test/ct/02/Value", "name": "ct02"},
            {"full_name": "test/ct/03/value", "name": "ct03"},
            {"full_name": "test/ct/04/value", "name": "ct04"},
            {"full_name": "null/val", "name": "mntgrp_04"},
        ]
        pool.AcqChannelList = [json.dumps(a) for a in arr]

#        self.myAssertRaise(Exception, rs.updateMntGrp)
        self._cf.dp.SetCommandVariable(["CPDICT", json.dumps(self.smycps)])
        self._cf.dp.SetCommandVariable(["DSDICT", json.dumps(self.smydss)])

        for i in range(6):
            ar = arr[i % len(arr)]

            cps = {}
            acps = {}
            dss = {}
            # lcp = self._rnd.randint(1, 40)
            # lds = self._rnd.randint(1, 40)

            self._cf.dp.SetCommandVariable(["CPDICT", json.dumps(self.smycps)])
            self._cf.dp.SetCommandVariable(["DSDICT", json.dumps(self.smydss)])

            ncps = self._rnd.randint(1, len(list(self.smycps.keys())) - 1)
            lcps = self._rnd.sample(list(self.smycps.keys()), ncps)
            for cp in lcps:
                if cp not in wrong:
                    cps[cp] = bool(self._rnd.randint(0, 1))

            ancps = self._rnd.randint(1, len(list(self.smycps.keys())) - 1)
            alcps = self._rnd.sample(list(self.smycps.keys()), ancps)
            for cp in alcps:
                if cp not in wrong:
                    acps[cp] = bool(self._rnd.randint(0, 1))

            ndss = self._rnd.randint(1, len(list(self.smycps.keys())) - 1)
            ldss = self._rnd.sample(list(self.smycps.keys()), ndss)
            for ds in ldss:
                if ds in self.smydss.keys():
                    if ds not in wrong:
                        dss[ds] = bool(self._rnd.randint(0, 1))

            ndss = self._rnd.randint(1, len(list(self.smydss.keys())) - 1)
            ldss = self._rnd.sample(list(self.smydss.keys()), ndss)
            for ds in ldss:
                if ds in self.smydss.keys():
                    if ds not in wrong:
                        dss[ds] = bool(self._rnd.randint(0, 1))

            mncps = self._rnd.randint(1, len(list(self.smycps.keys())) - 1)
            mcps = [cp for cp in self._rnd.sample(
                    list(self.smycps.keys()), mncps) if cp not in wrong]

            mp = json.loads(rs.profileConfiguration)
            mp["ComponentSelection"] = json.dumps(cps)
            mp["ComponentPreselection"] = json.dumps(acps)
            mp["DataSourceSelection"] = json.dumps(dss)
            self._cf.dp.SetCommandVariable(["MCPLIST", json.dumps(mcps)])
            rs.profileConfiguration = str(json.dumps(mp))
            mp = json.loads(rs.profileConfiguration)

            records = {}
            describer = Describer(self._cf.dp, True)
            cpres = describer.components(dstype='CLIENT')
            for grp in cpres:
                for idss in grp.values():
                    for idsrs in idss.values():
                        for idsr in idsrs:
                            records[str(idsr[2])] = "1234"
            dsres = describer.dataSources(list(dss.keys()), dstype='CLIENT')[0]
            for dsr in dsres.values():
                records[str(dsr.record)] = '2345'

            mp = json.loads(rs.profileConfiguration)
            mp["Timer"] = '["%s"]' % ar["name"]
            mp["UserData"] = json.dumps(records)
            rs.profileConfiguration = str(json.dumps(mp))
            mp = json.loads(rs.profileConfiguration)
            tmg = TestMGSetUp.TestMeasurementGroupSetUp(name='nxsmntgrp2')
            dv = "/".join(ar["full_name"].split("/")[0:-1])
            chds = rs.selectedDataSources()
            chds.extend(rs.componentDataSources())
            chds = sorted([ds for ds in chds if not ds.startswith('client')])

            tgc = {}

            mp = json.loads(rs.profileConfiguration)
            try:
                self.myAssertDict(json.loads(mp["ComponentPreselection"]),
                                  acps)
                self.myAssertDict(json.loads(mp["ComponentSelection"]), cps)
                self.myAssertDict(json.loads(mp["DataSourceSelection"]), dss)
                self.assertEqual(json.loads(mp["UnplottedComponents"]), [])
                self.assertEqual(json.loads(mp["OrderedChannels"]), [])
                self.myAssertDict(json.loads(mp["UserData"]), records)
                self.assertEqual(json.loads(mp["Timer"]), [ar["name"]])
                self.assertEqual(mp["MntGrp"], "nxsmntgrp2")

                wwcp = rs.components
                describer = Describer(self._cf.dp, True)
                res = describer.components(wwcp, "STEP", "")

                # mdds = set()
                for mdss in res[0].values():
                    if isinstance(mdss, dict):
                        for ds in mdss.keys():
                            dss[ds] = True

                jpcnf = rs.updateMntGrp()
                pcnf = json.loads(jpcnf)
                mgdp = tango.DeviceProxy(tmg.new_device_info_writer.name)
                jcnf = mgdp.Configuration
                cnf = json.loads(jcnf)
                mp = json.loads(rs.profileConfiguration)
                self.myAssertDict(json.loads(mp["ComponentPreselection"]),
                                  acps)
                self.myAssertDict(json.loads(mp["ComponentSelection"]), cps)
                self.myAssertDict(json.loads(mp["DataSourceSelection"]), dss)
                self.assertEqual(json.loads(mp["UnplottedComponents"]), [])
                self.assertEqual(json.loads(mp["OrderedChannels"]), [])
                self.myAssertDict(json.loads(mp["UserData"]), records)
                self.assertEqual(json.loads(mp["Timer"]), [ar["name"]])
                self.assertEqual(mp["MntGrp"], "nxsmntgrp2")
                #                print "CNF", cnf
                #                print "CHDS", chds
                i = 1
                for ds in chds:
                    if ds == ar['name']:
                        cri = i
                        i = 0
                    cnt = self.smychs[str(ds)]
                    try:
                        chn = {'ndim': len(cnt['shape']),
                               'index': i,
                               'name': str(ds),
                               'data_type': cnt['data_type'],
                               'plot_type': cnt['plot_type'],
                               'data_units': cnt['data_units'],
                               'enabled': True,
                               'label': cnt['source'],
                               'instrument': None,
                               'shape': cnt['shape'],
                               '_controller_name': '__tango__',
                               'conditioning': '',
                               'full_name': '%s%s' % (
                                   'tango://', cnt['source']),
                               '_unit_id': '0',
                               'output': True,
                               'plot_axes': cnt['plot_axes'],
                               'nexus_path': '',
                               'normalization': 0,
                               'source': cnt['source']}
                        tgc[chn["full_name"]] = chn
                    except Exception:
                        # print ds, cnt
                        raise
                    if ds == ar['name']:
                        i = cri
                    else:
                        i += 1
                if tgc:
                    smg = {"controllers":
                           {'__tango__':
                            {'units':
                             {'0':
                              {'channels': tgc,
                               'monitor': dv,
                               'id': 0,
                               'timer': dv,
                               'trigger_type': 0}}}},
                           "monitor": "%s" % dv,
                           "description": "Measurement Group",
                           "timer": "%s" % dv,
                           "label": "nxsmntgrp2"}
                else:
                    smg = {"controllers":
                           {},
                           "monitor": "%s" % dv,
                           "description": "Measurement Group",
                           "timer": "%s" % dv,
                           "label": "nxsmntgrp2"}
#                print "SMG", smg
                self.myAssertDict(smg, pcnf)
                self.myAssertDict(pcnf, cnf)
                rs.mntGrp = "nxsmntgrp"
                rs.profileConfiguration = str(json.dumps({}))
                rs.configDevice = val["ConfigDevice"]
                rs.door = val["Door"]
                rs.mntGrp = val["MntGrp"]
                rs.fetchProfile()
                mp = json.loads(rs.profileConfiguration)
                self.myAssertDict(json.loads(mp["ComponentPreselection"]),
                                  acps)
                self.myAssertDict(json.loads(mp["ComponentSelection"]), cps)
                self.myAssertDict(json.loads(mp["DataSourceSelection"]), dss)
                self.assertEqual(json.loads(mp["UnplottedComponents"]), [])
                self.assertEqual(json.loads(mp["OrderedChannels"]), [])
                self.myAssertDict(json.loads(mp["UserData"]), records)
                self.assertEqual(json.loads(mp["Timer"]), [ar["name"]])
                self.assertEqual(mp["MntGrp"], "nxsmntgrp2")
            finally:
                rs.deleteProfile("nxsmntgrp2")
                try:
                    tmg.tearDown()
                except Exception:
                    pass

    # updateMntGrp test
    def test_updateMntGrp_components_nopool_tango(self):
        fun = sys._getframe().f_code.co_name
        print("Run: %s.%s() " % (self.__class__.__name__, fun))
        val = {"ConfigDevice": self._cf.dp.name(),
               "WriterDevice": self._wr.dp.name(),
               "Door": 'doortestp09/testts/t1r228',
               "MntGrp": 'nxsmntgrp2'}

        wrong = []
        rs = self.openRecSelector()
        rs.configDevice = val["ConfigDevice"]
        rs.door = val["Door"]
        rs.mntGrp = val["MntGrp"]
        rs.writerDevice = val["WriterDevice"]
        self.assertEqual(rs.configDevice, val["ConfigDevice"])
        self.assertEqual(rs.door, val["Door"])

        db = tango.Database()
        db.put_device_property(list(self._ms.ms.keys())[0],
                               {'PoolNames': self._pool.dp.name()})
        pool = self._pool.dp
        pool.ExpChannelList = []
        self._ms.dps[list(self._ms.ms.keys())[0]].Init()

        self.assertEqual(rs.availableMntGrps(), [])

        arr = [
            {"full_name": "test/ct/01/Value", "name": "ct01"},
            {"full_name": "test/ct/02/Value", "name": "ct02"},
            {"full_name": "test/ct/03/value", "name": "ct03"},
            {"full_name": "test/ct/04/value", "name": "ct04"},
            {"full_name": "null/val", "name": "mntgrp_04"},
        ]
        pool.AcqChannelList = [json.dumps(a) for a in arr]

#        self.myAssertRaise(Exception, rs.updateMntGrp)
        self._cf.dp.SetCommandVariable(["CPDICT", json.dumps(self.smycps)])
        self._cf.dp.SetCommandVariable(["DSDICT", json.dumps(self.smydss)])

        for i in range(6):
            ar = arr[i % len(arr)]

            cps = {}
            acps = {}
            dss = {}
            # lcp = self._rnd.randint(1, 40)
            # lds = self._rnd.randint(1, 40)

            self._cf.dp.SetCommandVariable(["CPDICT", json.dumps(self.smycps)])
            self._cf.dp.SetCommandVariable(["DSDICT", json.dumps(self.smydss)])

            ncps = self._rnd.randint(1, len(list(self.smycps.keys())) - 1)
            lcps = self._rnd.sample(list(self.smycps.keys()), ncps)
            for cp in lcps:
                if cp not in wrong:
                    cps[cp] = bool(self._rnd.randint(0, 1))

            ancps = self._rnd.randint(1, len(list(self.smycps.keys())) - 1)
            alcps = self._rnd.sample(list(self.smycps.keys()), ancps)
            for cp in alcps:
                if cp not in wrong:
                    acps[cp] = bool(self._rnd.randint(0, 1))

            ndss = self._rnd.randint(1, len(list(self.smycps.keys())) - 1)
            ldss = self._rnd.sample(list(self.smycps.keys()), ndss)
            for ds in ldss:
                if ds in self.smydss.keys():
                    if ds not in wrong:
                        dss[ds] = bool(self._rnd.randint(0, 1))

            ndss = self._rnd.randint(1, len(list(self.smydss.keys())) - 1)
            ldss = self._rnd.sample(list(self.smydss.keys()), ndss)
            for ds in ldss:
                if ds in self.smydss.keys():
                    if ds not in wrong:
                        dss[ds] = bool(self._rnd.randint(0, 1))

            mncps = self._rnd.randint(1, len(list(self.smycps.keys())) - 1)
            mcps = [cp for cp in self._rnd.sample(
                    list(self.smycps.keys()), mncps) if cp not in wrong]

            mp = json.loads(rs.profileConfiguration)
            mp["ComponentSelection"] = json.dumps(cps)
            mp["ComponentPreselection"] = json.dumps(acps)
            mp["DataSourceSelection"] = json.dumps(dss)
            self._cf.dp.SetCommandVariable(["MCPLIST", json.dumps(mcps)])
            rs.profileConfiguration = str(json.dumps(mp))
            mp = json.loads(rs.profileConfiguration)

            records = {}
            describer = Describer(self._cf.dp, True)
            cpres = describer.components(dstype='CLIENT')
            for grp in cpres:
                for idss in grp.values():
                    for idsrs in idss.values():
                        for idsr in idsrs:
                            records[str(idsr[2])] = "1234"
            dsres = describer.dataSources(list(dss.keys()), dstype='CLIENT')[0]
            for dsr in dsres.values():
                records[str(dsr.record)] = '2345'

            mp = json.loads(rs.profileConfiguration)
            mp["Timer"] = '["%s"]' % ar["name"]
            mp["UserData"] = json.dumps(records)
            rs.profileConfiguration = str(json.dumps(mp))
            mp = json.loads(rs.profileConfiguration)
            tmg = TestMGSetUp.TestMeasurementGroupSetUp(name='nxsmntgrp2')
            dv = "/".join(ar["full_name"].split("/")[0:-1])
            chds = rs.selectedDataSources()
            chds.extend(rs.componentDataSources())
            chds = sorted([ds for ds in chds if not ds.startswith('client')])

            tgc = {}

            mp = json.loads(rs.profileConfiguration)
            try:
                self.myAssertDict(json.loads(mp["ComponentPreselection"]),
                                  acps)
                self.myAssertDict(json.loads(mp["ComponentSelection"]), cps)
                self.myAssertDict(json.loads(mp["DataSourceSelection"]), dss)
                self.assertEqual(json.loads(mp["UnplottedComponents"]), [])
                self.assertEqual(json.loads(mp["OrderedChannels"]), [])
                self.myAssertDict(json.loads(mp["UserData"]), records)
                self.assertEqual(json.loads(mp["Timer"]), [ar["name"]])
                self.assertEqual(mp["MntGrp"], "nxsmntgrp2")

                wwcp = rs.components
                describer = Describer(self._cf.dp, True)
                res = describer.components(wwcp, "STEP", "")

                # mdds = set()
                for mdss in res[0].values():
                    if isinstance(mdss, dict):
                        for ds in mdss.keys():
                            dss[ds] = True

                jpcnf = rs.updateMntGrp()
                pcnf = json.loads(jpcnf)
                mgdp = tango.DeviceProxy(tmg.new_device_info_writer.name)
                jcnf = mgdp.Configuration
                cnf = json.loads(jcnf)
                mp = json.loads(rs.profileConfiguration)
                self.myAssertDict(json.loads(mp["ComponentPreselection"]),
                                  acps)
                self.myAssertDict(json.loads(mp["ComponentSelection"]), cps)
                self.myAssertDict(json.loads(mp["DataSourceSelection"]), dss)
                self.assertEqual(json.loads(mp["UnplottedComponents"]), [])
                self.assertEqual(json.loads(mp["OrderedChannels"]), [])
                self.myAssertDict(json.loads(mp["UserData"]), records)
                self.assertEqual(json.loads(mp["Timer"]), [ar["name"]])
                self.assertEqual(mp["MntGrp"], "nxsmntgrp2")
#                print "CNF", cnf
#                print "CHDS", chds
                for i, ds in enumerate(chds):
                    cnt = self.smychs[str(ds)]
                    try:
                        chn = {'ndim': len(cnt['shape']),
                               'index': i,
                               'name': str(ds),
                               'data_type': cnt['data_type'],
                               'plot_type': cnt['plot_type'],
                               'data_units': cnt['data_units'],
                               'enabled': True,
                               'label': cnt['source'],
                               'instrument': None,
                               'shape': cnt['shape'],
                               '_controller_name': '__tango__',
                               'conditioning': '',
                               'full_name': '%s%s' % (
                                   'tango://', cnt['source']),
                               '_unit_id': '0',
                               'output': True,
                               'plot_axes': cnt['plot_axes'],
                               'nexus_path': '',
                               'normalization': 0,
                               'source': cnt['source']}
                        tgc[chn["full_name"]] = chn
                    except Exception:
                        # print ds, cnt
                        raise
                if tgc:
                    smg = {"controllers":
                           {'__tango__':
                            {'units':
                             {'0':
                              {'channels': tgc,
                               'monitor': dv,
                               'id': 0,
                               'timer': dv,
                               'trigger_type': 0}}}},
                           "monitor": "%s" % dv,
                           "description": "Measurement Group",
                           "timer": "%s" % dv,
                           "label": "nxsmntgrp2"}
                else:
                    smg = {"controllers":
                           {},
                           "monitor": "%s" % dv,
                           "description": "Measurement Group",
                           "timer": "%s" % dv,
                           "label": "nxsmntgrp2"}
#                print "SMG", smg
                self.myAssertDict(smg, pcnf)
                self.myAssertDict(pcnf, cnf)
                rs.mntGrp = "nxsmntgrp"
                rs.profileConfiguration = str(json.dumps({}))
                rs.configDevice = val["ConfigDevice"]
                rs.door = val["Door"]
                rs.mntGrp = val["MntGrp"]
                rs.fetchProfile()
                mp = json.loads(rs.profileConfiguration)
                self.myAssertDict(json.loads(mp["ComponentPreselection"]),
                                  acps)
                self.myAssertDict(json.loads(mp["ComponentSelection"]), cps)
                self.myAssertDict(json.loads(mp["DataSourceSelection"]), dss)
                self.assertEqual(json.loads(mp["UnplottedComponents"]), [])
                self.assertEqual(json.loads(mp["OrderedChannels"]), [])
                self.myAssertDict(json.loads(mp["UserData"]), records)
                self.assertEqual(json.loads(mp["Timer"]), [ar["name"]])
                self.assertEqual(mp["MntGrp"], "nxsmntgrp2")
            finally:
                rs.deleteProfile("nxsmntgrp2")
                try:
                    tmg.tearDown()
                except Exception:
                    pass

    # updateProfile test
    def test_updateMntGrp_components_nopool_tango_unplottedcomponents(self):
        fun = sys._getframe().f_code.co_name
        print("Run: %s.%s() " % (self.__class__.__name__, fun))
        val = {"ConfigDevice": self._cf.dp.name(),
               "WriterDevice": self._wr.dp.name(),
               "Door": 'doortestp09/testts/t1r228',
               "MntGrp": 'nxsmntgrp2'}

        wrong = []
        rs = self.openRecSelector()
        rs.configDevice = val["ConfigDevice"]
        rs.door = val["Door"]
        rs.mntGrp = val["MntGrp"]
        rs.writerDevice = val["WriterDevice"]
        self.assertEqual(rs.configDevice, val["ConfigDevice"])
        self.assertEqual(rs.door, val["Door"])

        db = tango.Database()
        db.put_device_property(list(self._ms.ms.keys())[0],
                               {'PoolNames': self._pool.dp.name()})
        pool = self._pool.dp
        pool.ExpChannelList = []
        self._ms.dps[list(self._ms.ms.keys())[0]].Init()

        self.assertEqual(rs.availableMntGrps(), [])

        arr = [
            {"full_name": "test/ct/01/Value", "name": "ct01"},
            {"full_name": "test/ct/02/Value", "name": "ct02"},
            {"full_name": "test/ct/03/value", "name": "ct03"},
            {"full_name": "test/ct/04/value", "name": "ct04"},
            {"full_name": "null/val", "name": "mntgrp_04"},
        ]
        pool.AcqChannelList = [json.dumps(a) for a in arr]

#        self.myAssertRaise(Exception, rs.updateMntGrp)
        self._cf.dp.SetCommandVariable(["CPDICT", json.dumps(self.smycps)])
        self._cf.dp.SetCommandVariable(["DSDICT", json.dumps(self.smydss)])

        for i in range(6):
            ar = arr[i % len(arr)]

            cps = {}
            acps = {}
            dss = {}
            # lcp = self._rnd.randint(1, 40)
            # lds = self._rnd.randint(1, 40)

            self._cf.dp.SetCommandVariable(["CPDICT", json.dumps(self.smycps)])
            self._cf.dp.SetCommandVariable(["DSDICT", json.dumps(self.smydss)])

            comps = set()
            ncps = self._rnd.randint(1, len(list(self.smycps.keys())) - 1)
            lcps = self._rnd.sample(list(self.smycps.keys()), ncps)
            for cp in lcps:
                if cp not in wrong:
                    cps[cp] = bool(self._rnd.randint(0, 1))
                    if cps[cp]:
                        comps.add(cp)

            ancps = self._rnd.randint(1, len(list(self.smycps.keys())) - 1)
            alcps = self._rnd.sample(list(self.smycps.keys()), ancps)
            for cp in alcps:
                if cp not in wrong:
                    acps[cp] = bool(self._rnd.randint(0, 1))
                    if acps[cp]:
                        comps.add(cp)

            ndss = self._rnd.randint(1, len(list(self.smycps.keys())) - 1)
            ldss = self._rnd.sample(list(self.smycps.keys()), ndss)
            for ds in ldss:
                if ds in self.smydss.keys():
                    if ds not in wrong:
                        dss[ds] = bool(self._rnd.randint(0, 1))

            ndss = self._rnd.randint(1, len(list(self.smydss.keys())) - 1)
            ldss = self._rnd.sample(list(self.smydss.keys()), ndss)
            for ds in ldss:
                if ds in self.smydss.keys():
                    if ds not in wrong:
                        dss[ds] = bool(self._rnd.randint(0, 1))

            mncps = self._rnd.randint(1, len(list(self.smycps.keys())) - 1)
            mcps = [cp for cp in self._rnd.sample(
                    list(self.smycps.keys()), mncps) if cp not in wrong]
            for cp in mcps:
                comps.add(cp)

            mp = json.loads(rs.profileConfiguration)
            mp["ComponentSelection"] = json.dumps(cps)
            mp["ComponentPreselection"] = json.dumps(acps)
            mp["DataSourceSelection"] = json.dumps(dss)
            self._cf.dp.SetCommandVariable(["MCPLIST", json.dumps(mcps)])
            self._cf.dp.SetCommandVariable(["MCPLIST", json.dumps(mcps)])
            rs.profileConfiguration = str(json.dumps(mp))
            mp = json.loads(rs.profileConfiguration)

            records = {}
            describer = Describer(self._cf.dp, True)
            cpres = describer.components(dstype='CLIENT')
            for grp in cpres:
                for idss in grp.values():
                    for idsrs in idss.values():
                        for idsr in idsrs:
                            records[str(idsr[2])] = "1234"
            dsres = describer.dataSources(list(dss.keys()), dstype='CLIENT')[0]
            for dsr in dsres.values():
                records[str(dsr.record)] = '2345'

            mp = json.loads(rs.profileConfiguration)
            mp["Timer"] = '["%s"]' % ar["name"]
            mp["UserData"] = json.dumps(records)
            rs.profileConfiguration = str(json.dumps(mp))
            mp = json.loads(rs.profileConfiguration)

            tmg = TestMGSetUp.TestMeasurementGroupSetUp(name='nxsmntgrp2')
            dv = "/".join(ar["full_name"].split("/")[0:-1])
            chds = [ds for ds in rs.selectedDataSources()
                    if not ds.startswith('client')]
            # chds1 = list(chds)
            chds2 = [ds for ds in rs.componentDataSources()
                     if not ds.startswith('client')]
            chds.extend(chds2)
            chds = sorted(chds)

            lheds = []
            if chds:
                nhe = self._rnd.randint(0, len(set(chds)) - 1)
                lheds = self._rnd.sample(list(chds), nhe)

            lhecp = []
            if comps:
                nhe = self._rnd.randint(0, len(set(comps)) - 1)
                lhecp = self._rnd.sample(list(comps), nhe)

            lhe = lheds + lhecp

            mp = json.loads(rs.profileConfiguration)
            mp["UnplottedComponents"] = json.dumps(lhe)
            rs.profileConfiguration = str(json.dumps(mp))
            mp = json.loads(rs.profileConfiguration)

            lhe2 = []
            for el in lhe:
                found = False
                for cp in comps:
                    if el in self.smycpsstep[cp]:
                        if cp not in lhecp:
                            found = True
                if not found:
                    lhe2.append(el)

            tgc = {}
            mp = json.loads(rs.profileConfiguration)

            try:
                self.myAssertDict(json.loads(mp["ComponentPreselection"]),
                                  acps)
                self.myAssertDict(json.loads(mp["ComponentSelection"]), cps)
                self.myAssertDict(json.loads(mp["DataSourceSelection"]), dss)
                self.assertEqual(set(json.loads(mp["UnplottedComponents"])),
                                 set(lhe))
                self.assertEqual(json.loads(mp["OrderedChannels"]), [])
                self.myAssertDict(json.loads(mp["UserData"]), records)
                self.assertEqual(json.loads(mp["Timer"]), [ar["name"]])
                self.assertEqual(mp["MntGrp"], "nxsmntgrp2")
                wwcp = rs.components
                describer = Describer(self._cf.dp, True)
                res = describer.components(wwcp, "STEP", "")

                # mdds = set()
                for mdss in res[0].values():
                    if isinstance(mdss, dict):
                        for ds in mdss.keys():
                            dss[ds] = True

                jpcnf = rs.updateMntGrp()
                pcnf = json.loads(jpcnf)
                mgdp = tango.DeviceProxy(tmg.new_device_info_writer.name)
                jcnf = mgdp.Configuration
                cnf = json.loads(jcnf)
                mp = json.loads(rs.profileConfiguration)
                self.myAssertDict(json.loads(mp["ComponentPreselection"]),
                                  acps)
                self.myAssertDict(json.loads(mp["ComponentSelection"]), cps)
                self.myAssertDict(json.loads(mp["DataSourceSelection"]), dss)
                self.assertEqual(set(json.loads(mp["UnplottedComponents"])),
                                 set(lhe2))
                self.assertEqual(json.loads(mp["OrderedChannels"]), [])
                self.myAssertDict(json.loads(mp["UserData"]), records)
                self.assertEqual(json.loads(mp["Timer"]), [ar["name"]])
                self.assertEqual(mp["MntGrp"], "nxsmntgrp2")
#                print "CNF", cnf
#                print "CHDS", chds
                for i, ds in enumerate(chds):
                    cnt = self.smychs[str(ds)]
                    try:
                        chn = {'ndim': len(cnt['shape']),
                               'index': i,
                               'name': str(ds),
                               'data_type': cnt['data_type'],
                               'plot_type': (
                                   cnt['plot_type']
                                   if ds not in lhe2 else 0),
                               'data_units': cnt['data_units'],
                               'enabled': True,
                               'label': cnt['source'],
                               'instrument': None,
                               'shape': cnt['shape'],
                               '_controller_name': '__tango__',
                               'conditioning': '',
                               'full_name': '%s%s' % (
                                   'tango://', cnt['source']),
                               '_unit_id': '0',
                               'output': True,
                               'plot_axes': (
                                   cnt['plot_axes']
                                   if ds not in lhe2 else []),
                               'nexus_path': '',
                               'normalization': 0,
                               'source': cnt['source']}
                        tgc[chn["full_name"]] = chn
                    except Exception:
                        # print ds, cnt
                        raise
                if tgc:
                    smg = {"controllers":
                           {'__tango__':
                            {'units':
                             {'0':
                              {'channels': tgc,
                               'monitor': dv,
                               'id': 0,
                               'timer': dv,
                               'trigger_type': 0}}}},
                           "monitor": "%s" % dv,
                           "description": "Measurement Group",
                           "timer": "%s" % dv,
                           "label": "nxsmntgrp2"}
                else:
                    smg = {"controllers":
                           {},
                           "monitor": "%s" % dv,
                           "description": "Measurement Group",
                           "timer": "%s" % dv,
                           "label": "nxsmntgrp2"}

#                print "SMG", smg
                self.myAssertDict(smg, pcnf)
                self.myAssertDict(pcnf, cnf)
                rs.mntGrp = "nxsmntgrp"
                rs.profileConfiguration = str(json.dumps({}))
                rs.configDevice = val["ConfigDevice"]
                rs.door = val["Door"]
                rs.mntGrp = val["MntGrp"]
                rs.fetchProfile()
                mp = json.loads(rs.profileConfiguration)
                self.myAssertDict(json.loads(mp["ComponentPreselection"]),
                                  acps)
                self.myAssertDict(json.loads(mp["ComponentSelection"]), cps)
                self.myAssertDict(json.loads(mp["DataSourceSelection"]), dss)
                self.assertEqual(set(json.loads(mp["UnplottedComponents"])),
                                 set(lhe2))
                self.assertEqual(json.loads(mp["OrderedChannels"]), [])
                self.myAssertDict(json.loads(mp["UserData"]), records)
                self.assertEqual(json.loads(mp["Timer"]), [ar["name"]])
                self.assertEqual(mp["MntGrp"], "nxsmntgrp2")
            finally:
                rs.deleteProfile("nxsmntgrp2")
                try:
                    tmg.tearDown()
                except Exception:
                    pass

    # updateMntGrp test
    def test_updateMntGrp_components_pool_tango(self):
        fun = sys._getframe().f_code.co_name
        print("Run: %s.%s() " % (self.__class__.__name__, fun))
        val = {"ConfigDevice": self._cf.dp.name(),
               "WriterDevice": self._wr.dp.name(),
               "Door": 'doortestp09/testts/t1r228',
               "MntGrp": 'nxsmntgrp2'}

        wrong = []
        rs = self.openRecSelector()
        rs.configDevice = val["ConfigDevice"]
        rs.door = val["Door"]
        rs.mntGrp = val["MntGrp"]
        rs.writerDevice = val["WriterDevice"]
        self.assertEqual(rs.configDevice, val["ConfigDevice"])
        self.assertEqual(rs.door, val["Door"])

        db = tango.Database()
        db.put_device_property(list(self._ms.ms.keys())[0],
                               {'PoolNames': self._pool.dp.name()})
        pool = self._pool.dp
        pool.ExpChannelList = []
        self._ms.dps[list(self._ms.ms.keys())[0]].Init()

        self.assertEqual(rs.availableMntGrps(), [])
        scalar_ctrl = 'ttestp09/testts/t1r228'
        spectrum_ctrl = 'ttestp09/testts/t2r228'
        image_ctrl = 'ttestp09/testts/t3r228'
        ctrls = [scalar_ctrl, spectrum_ctrl, image_ctrl, "__tango__"]

        simp2 = TestServerSetUp.MultiTestServerSetUp(
            devices=['ttestp09/testts/t%02dr228' % i for i in range(1, 37)])
        try:
            simp2.setUp()

            expch = []
            pdss = []
            for ds, vl in self.smychsXX.items():
                if vl:
                    exp = {}
                    exp["name"] = ds
                    exp["source"] = vl["source"]
                    if ds.startswith("image"):
                        exp["controller"] = image_ctrl
                        exp["type"] = "TwoDExpChannel"
                    if ds.startswith("spectrum"):
                        exp["controller"] = spectrum_ctrl
                        exp["type"] = "OneDExpChannel"
                    else:
                        exp["controller"] = scalar_ctrl
                        exp["type"] = "CTExpChannel"
                    expch.append(exp)
                    pdss.append(ds)
            pdss = sorted(pdss)

            acqch = [
                {"full_name": "test/ct/01/Value", "name": "ct01"},
                {"full_name": "test/ct/02/Value", "name": "ct02"},
                {"full_name": "test/ct/03/value", "name": "ct03"},
                {"full_name": "test/ct/04/value", "name": "ct04"},
                {"full_name": "null/val", "name": "mntgrp_04"}
            ]

            for ch in expch:
                ach = {}
                ach["name"] = ch["name"]
                ach["full_name"] = ch["source"]
                acqch.append(ach)

            pool.AcqChannelList = [json.dumps(a) for a in acqch]
            pool.ExpChannelList = [json.dumps(a) for a in expch]

#            self.myAssertRaise(Exception, rs.updateMntGrp)
            self._cf.dp.SetCommandVariable(
                ["CPDICT", json.dumps(self.smycps2)])
            self._cf.dp.SetCommandVariable(
                ["DSDICT", json.dumps(self.smydssXX)])

            for i in range(6):
                try:
                    ar = acqch[i % 5]
                    cps = {}
                    acps = {}
                    dss = {}
                    # lcp = self._rnd.randint(1, 40)
                    # lds = self._rnd.randint(1, 40)

                    self._cf.dp.SetCommandVariable(
                        ["CPDICT", json.dumps(self.smycps2)])
                    self._cf.dp.SetCommandVariable(
                        ["DSDICT", json.dumps(self.smydssXX)])

                    ncps = self._rnd.randint(
                        1, len(list(self.smycps2.keys())) - 1)
                    lcps = self._rnd.sample(list(self.smycps2.keys()), ncps)
                    for cp in lcps:
                        if cp not in wrong:
                            cps[cp] = bool(self._rnd.randint(0, 1))

                    ancps = self._rnd.randint(
                        1, len(list(self.smycps2.keys())) - 1)
                    alcps = self._rnd.sample(list(self.smycps2.keys()), ancps)
                    for cp in alcps:
                        if cp not in wrong:
                            acps[cp] = bool(self._rnd.randint(0, 1))

                    ndss = self._rnd.randint(
                        1, len(list(self.smycps2.keys())) - 1)
                    ldss = self._rnd.sample(list(self.smycps2.keys()), ndss)
                    for ds in ldss:
                        if ds in self.smydssXX.keys():
                            if ds not in wrong:
                                dss[ds] = bool(self._rnd.randint(0, 1))

                    ndss = self._rnd.randint(
                        1, len(list(self.smydssXX.keys())) - 1)
                    ldss = self._rnd.sample(list(self.smydssXX.keys()), ndss)
                    for ds in ldss:
                        if ds in self.smydssXX.keys():
                            if ds not in wrong:
                                dss[ds] = bool(self._rnd.randint(0, 1))

                    mncps = self._rnd.randint(
                        1, len(list(self.smycps2.keys())) - 1)
                    mcps = [
                        cp for cp in self._rnd.sample(
                            list(self.smycps2.keys()), mncps)
                        if cp not in wrong]

                    adss = dict(dss)
                    for ch in expch:
                        if ch["name"] not in adss.keys():
                            adss[ch["name"]] = False

                    mp = json.loads(rs.profileConfiguration)
                    mp["ComponentSelection"] = json.dumps(cps)
                    mp["ComponentPreselection"] = json.dumps(acps)
                    mp["DataSourceSelection"] = json.dumps(dss)
                    self._cf.dp.SetCommandVariable(["MCPLIST",
                                                    json.dumps(mcps)])
                    rs.profileConfiguration = str(json.dumps(mp))
                    mp = json.loads(rs.profileConfiguration)

                    records = {}
                    describer = Describer(self._cf.dp, True)
                    cpres = describer.components(dstype='CLIENT')
                    for grp in cpres:
                        for idss in grp.values():
                            for idsrs in idss.values():
                                for idsr in idsrs:
                                    records[str(idsr[2])] = "1234"
                    dsres = describer.dataSources(
                        list(dss.keys()), dstype='CLIENT')[0]
                    for dsr in dsres.values():
                        records[str(dsr.record)] = '2345'

                    mp = json.loads(rs.profileConfiguration)
                    mp["Timer"] = '["%s"]' % ar["name"]
                    mp["UserData"] = json.dumps(records)
                    rs.profileConfiguration = str(json.dumps(mp))
                    mp = json.loads(rs.profileConfiguration)

                    tmg = TestMGSetUp.TestMeasurementGroupSetUp(
                        name='nxsmntgrp2')
                    dv = "/".join(ar["full_name"].split("/")[0:-1])
                    chds = rs.selectedDataSources()
                    chds.extend(rs.componentDataSources())
                    chds = sorted([
                        ds for ds in chds if not ds.startswith('client')])

                    mp = json.loads(rs.profileConfiguration)
                    self.myAssertDict(
                        json.loads(mp["ComponentPreselection"]),
                        acps)
                    self.myAssertDict(
                        json.loads(mp["ComponentSelection"]), cps)
                    self.myAssertDict(
                        json.loads(mp["DataSourceSelection"]), adss)
                    self.assertEqual(json.loads(mp["UnplottedComponents"]), [])
                    self.assertEqual(json.loads(mp["OrderedChannels"]), pdss)
                    self.myAssertDict(json.loads(mp["UserData"]), records)
                    self.assertEqual(json.loads(mp["Timer"]), [ar["name"]])
                    self.assertEqual(mp["MntGrp"], "nxsmntgrp2")

                    wwcp = rs.components
                    describer = Describer(self._cf.dp, True)
                    res = describer.components(wwcp, "STEP", "")

                    # mdds = set()
                    for mdss in res[0].values():
                        if isinstance(mdss, dict):
                            for ds in mdss.keys():
                                adss[ds] = True

                    jpcnf = rs.updateMntGrp()
                    pcnf = json.loads(jpcnf)
                    mgdp = tango.DeviceProxy(tmg.new_device_info_writer.name)
                    jcnf = mgdp.Configuration
                    cnf = json.loads(jcnf)
                    mp = json.loads(rs.profileConfiguration)
                    self.myAssertDict(
                        json.loads(mp["ComponentPreselection"]),
                        acps)
                    self.myAssertDict(
                        json.loads(mp["ComponentSelection"]), cps)
                    self.myAssertDict(
                        json.loads(mp["DataSourceSelection"]), adss)
                    self.assertEqual(json.loads(mp["UnplottedComponents"]), [])
                    self.assertEqual(json.loads(mp["OrderedChannels"]), pdss)
                    self.myAssertDict(json.loads(mp["UserData"]), records)
                    self.assertEqual(json.loads(mp["Timer"]), [ar["name"]])
                    self.assertEqual(mp["MntGrp"], "nxsmntgrp2")
                    myctrls = {}
                    for cl in ctrls:
                        tgc = {}
                        ttdv = None
                        idmax = 10000
                        for exp in expch:
                            ds = exp["name"]
                            if ds in chds and cl == exp['controller']:
                                cnt = self.smychsXX[str(ds)]
                                i = chds.index(str(ds))
                                try:
                                    tdv = "/".join(
                                        cnt['source'].split("/")[:-1])
                                    if i < idmax:
                                        idmax = i
                                        ttdv = tdv
                                    chn = {'ndim': len(cnt['shape']),
                                           'index': i,
                                           'name': str(ds),
                                           'data_type': cnt['data_type'],
                                           'plot_type': cnt['plot_type'],
                                           'data_units': cnt['data_units'],
                                           'enabled': True,
                                           'label': ds,
                                           'instrument': None,
                                           'shape': cnt['shape'],
                                           '_controller_name': cl,
                                           'conditioning': '',
                                           'full_name': tdv,
                                           '_unit_id': '0',
                                           'output': True,
                                           'plot_axes': cnt['plot_axes'],
                                           'nexus_path': '',
                                           'normalization': 0,
                                           'source': cnt['source']}
                                    tgc[tdv] = chn
                                except Exception:
                                    raise
                        if tgc:
                            myctrls[cl] = {'units':
                                           {'0':
                                            {'channels': tgc,
                                             'monitor': ttdv,
                                             'id': 0,
                                             'timer': ttdv,
                                             'trigger_type': 0}}}

                    smg = {"controllers": myctrls,
                           "monitor": "%s" % dv,
                           "description": "Measurement Group",
                           "timer": "%s" % dv,
                           "label": "nxsmntgrp2"}
                    self.myAssertDict(smg, pcnf)
                    self.myAssertDict(pcnf, cnf)
                    rs.mntGrp = "nxsmntgrp"
                    rs.profileConfiguration = str(json.dumps({}))
                    rs.configDevice = val["ConfigDevice"]
                    rs.door = val["Door"]
                    rs.mntGrp = val["MntGrp"]
                    rs.fetchProfile()
                    mp = json.loads(rs.profileConfiguration)
                    self.myAssertDict(
                        json.loads(mp["ComponentPreselection"]),
                        acps)
                    self.myAssertDict(
                        json.loads(mp["ComponentSelection"]), cps)
                    self.myAssertDict(
                        json.loads(mp["DataSourceSelection"]), adss)
                    self.assertEqual(json.loads(mp["UnplottedComponents"]), [])
                    self.assertEqual(json.loads(mp["OrderedChannels"]), pdss)
                    self.myAssertDict(json.loads(mp["UserData"]), records)
                    self.assertEqual(json.loads(mp["Timer"]), [ar["name"]])
                    self.assertEqual(mp["MntGrp"], "nxsmntgrp2")
                finally:
                    rs.deleteProfile("nxsmntgrp2")
                    try:
                        tmg.tearDown()
                    except Exception:
                        pass
        finally:
            simp2.tearDown()

    # updateMntGrp test
    def test_updateMntGrp_components_pool_tango_unplottedcomponents(self):
        fun = sys._getframe().f_code.co_name
        print("Run: %s.%s() " % (self.__class__.__name__, fun))
        val = {"ConfigDevice": self._cf.dp.name(),
               "WriterDevice": self._wr.dp.name(),
               "Door": 'doortestp09/testts/t1r228',
               "MntGrp": 'nxsmntgrp2'}

        wrong = []
        rs = self.openRecSelector()
        rs.configDevice = val["ConfigDevice"]
        rs.door = val["Door"]
        rs.mntGrp = val["MntGrp"]
        rs.writerDevice = val["WriterDevice"]
        self.assertEqual(rs.configDevice, val["ConfigDevice"])
        self.assertEqual(rs.door, val["Door"])

        db = tango.Database()
        db.put_device_property(list(self._ms.ms.keys())[0],
                               {'PoolNames': self._pool.dp.name()})
        pool = self._pool.dp
        pool.ExpChannelList = []
        self._ms.dps[list(self._ms.ms.keys())[0]].Init()

        self.assertEqual(rs.availableMntGrps(), [])
        scalar_ctrl = 'ttestp09/testts/t1r228'
        spectrum_ctrl = 'ttestp09/testts/t2r228'
        image_ctrl = 'ttestp09/testts/t3r228'
        ctrls = [scalar_ctrl, spectrum_ctrl, image_ctrl, "__tango__"]

        simp2 = TestServerSetUp.MultiTestServerSetUp(
            devices=['ttestp09/testts/t%02dr228' % i for i in range(1, 37)])
        try:
            simp2.setUp()

            expch = []
            pdss = []
            for ds, vl in self.smychsXX.items():
                if vl:
                    exp = {}
                    exp["name"] = ds
                    exp["source"] = vl["source"]
                    if ds.startswith("image"):
                        exp["controller"] = image_ctrl
                        exp["type"] = "TwoDExpChannel"
                    if ds.startswith("spectrum"):
                        exp["controller"] = spectrum_ctrl
                        exp["type"] = "OneDExpChannel"
                    else:
                        exp["controller"] = scalar_ctrl
                        exp["type"] = "CTExpChannel"
                    expch.append(exp)
                    pdss.append(ds)
            pdss = sorted(pdss)

            acqch = [
                {"full_name": "test/ct/01/Value", "name": "ct01"},
                {"full_name": "test/ct/02/Value", "name": "ct02"},
                {"full_name": "test/ct/03/value", "name": "ct03"},
                {"full_name": "test/ct/04/value", "name": "ct04"},
                {"full_name": "null/val", "name": "mntgrp_04"}
            ]

            for ch in expch:
                ach = {}
                ach["name"] = ch["name"]
                ach["full_name"] = ch["source"]
                acqch.append(ach)

            pool.AcqChannelList = [json.dumps(a) for a in acqch]
            pool.ExpChannelList = [json.dumps(a) for a in expch]

#            self.myAssertRaise(Exception, rs.updateMntGrp)
            self._cf.dp.SetCommandVariable(
                ["CPDICT", json.dumps(self.smycps2)])
            self._cf.dp.SetCommandVariable(
                ["DSDICT", json.dumps(self.smydssXX)])

            for i in range(6):
                try:
                    ar = acqch[i % 5]
                    cps = {}
                    acps = {}
                    dss = {}
                    # lcp = self._rnd.randint(1, 40)
                    # lds = self._rnd.randint(1, 40)

                    self._cf.dp.SetCommandVariable(
                        ["CPDICT", json.dumps(self.smycps2)])
                    self._cf.dp.SetCommandVariable(
                        ["DSDICT", json.dumps(self.smydssXX)])
                    comps = set()

                    ncps = self._rnd.randint(
                        1, len(list(self.smycps2.keys())) - 1)
                    lcps = self._rnd.sample(list(self.smycps2.keys()), ncps)
                    for cp in lcps:
                        if cp not in wrong:
                            cps[cp] = bool(self._rnd.randint(0, 1))
                            if cps[cp]:
                                comps.add(cp)

                    ancps = self._rnd.randint(
                        1, len(list(self.smycps2.keys())) - 1)
                    alcps = self._rnd.sample(list(self.smycps2.keys()), ancps)
                    for cp in alcps:
                        if cp not in wrong:
                            acps[cp] = bool(self._rnd.randint(0, 1))
                            if acps[cp]:
                                comps.add(cp)

                    ndss = self._rnd.randint(
                        1, len(list(self.smycps2.keys())) - 1)
                    ldss = self._rnd.sample(list(self.smycps2.keys()), ndss)
                    for ds in ldss:
                        if ds in self.smydssXX.keys():
                            if ds not in wrong:
                                dss[ds] = bool(self._rnd.randint(0, 1))

                    ndss = self._rnd.randint(
                        1, len(list(self.smydssXX.keys())) - 1)
                    ldss = self._rnd.sample(list(self.smydssXX.keys()), ndss)
                    for ds in ldss:
                        if ds in self.smydssXX.keys():
                            if ds not in wrong:
                                dss[ds] = bool(self._rnd.randint(0, 1))

                    mncps = self._rnd.randint(
                        1, len(list(self.smycps2.keys())) - 1)
                    mcps = [cp for cp in self._rnd.sample(
                            list(self.smycps2.keys()), mncps)
                            if cp not in wrong]
                    for cp in mcps:
                        comps.add(cp)

                    adss = dict(dss)
                    for ch in expch:
                        if ch["name"] not in adss.keys():
                            adss[ch["name"]] = False
                    mp = json.loads(rs.profileConfiguration)
                    mp["ComponentSelection"] = json.dumps(cps)
                    mp["ComponentPreselection"] = json.dumps(acps)
                    mp["DataSourceSelection"] = json.dumps(dss)
                    self._cf.dp.SetCommandVariable(["MCPLIST",
                                                    json.dumps(mcps)])
                    rs.profileConfiguration = str(json.dumps(mp))
                    mp = json.loads(rs.profileConfiguration)

                    records = {}
                    describer = Describer(self._cf.dp, True)
                    cpres = describer.components(dstype='CLIENT')
                    for grp in cpres:
                        for idss in grp.values():
                            for idsrs in idss.values():
                                for idsr in idsrs:
                                    records[str(idsr[2])] = "1234"
                    dsres = describer.dataSources(
                        list(dss.keys()), dstype='CLIENT')[0]
                    for dsr in dsres.values():
                        records[str(dsr.record)] = '2345'

                    mp = json.loads(rs.profileConfiguration)
                    mp["Timer"] = '["%s"]' % ar["name"]
                    mp["UserData"] = json.dumps(records)
                    rs.profileConfiguration = str(json.dumps(mp))
                    mp = json.loads(rs.profileConfiguration)

                    tmg = TestMGSetUp.TestMeasurementGroupSetUp(
                        name='nxsmntgrp2')
                    dv = "/".join(ar["full_name"].split("/")[0:-1])
                    chds = [ds for ds in rs.selectedDataSources()
                            if not ds.startswith('client')]
                    # chds1 = list(chds)
                    chds2 = [ds for ds in rs.componentDataSources()
                             if not ds.startswith('client')]
                    chds.extend(chds2)
                    chds = sorted(chds)

                    lheds = []
                    if chds:
                        nhe = self._rnd.randint(0, len(set(chds)) - 1)
                        lheds = self._rnd.sample(list(chds), nhe)

                    lhecp = []
                    if comps:
                        nhe = self._rnd.randint(0, len(set(comps)) - 1)
                        lhecp = self._rnd.sample(list(comps), nhe)

                    lhe = lheds + lhecp

                    mp = json.loads(rs.profileConfiguration)
                    mp["UnplottedComponents"] = json.dumps(lhe)
                    rs.profileConfiguration = str(json.dumps(mp))
                    mp = json.loads(rs.profileConfiguration)

                    lhe2 = []
                    for el in lhe:
                        found = False
                        for cp in comps:
                            if el in self.smycpsstep2[cp]:
                                if cp not in lhecp:
                                    found = True
                        if not found:
                            lhe2.append(el)

                    self.myAssertDict(
                        json.loads(mp["ComponentPreselection"]),
                        acps)
                    self.myAssertDict(
                        json.loads(mp["ComponentSelection"]), cps)
                    self.myAssertDict(
                        json.loads(mp["DataSourceSelection"]), adss)
                    self.assertEqual(
                        set(json.loads(mp["UnplottedComponents"])),
                        set(lhe))
                    self.assertEqual(json.loads(mp["OrderedChannels"]), pdss)
                    self.myAssertDict(json.loads(mp["UserData"]), records)
                    self.assertEqual(json.loads(mp["Timer"]), [ar["name"]])
                    self.assertEqual(mp["MntGrp"], "nxsmntgrp2")

                    wwcp = rs.components
                    describer = Describer(self._cf.dp, True)
                    res = describer.components(wwcp, "STEP", "")

                    # mdds = set()
                    for mdss in res[0].values():
                        if isinstance(mdss, dict):
                            for ds in mdss.keys():
                                adss[ds] = True

                    jpcnf = rs.updateMntGrp()
                    pcnf = json.loads(jpcnf)
                    mgdp = tango.DeviceProxy(tmg.new_device_info_writer.name)
                    jcnf = mgdp.Configuration
                    cnf = json.loads(jcnf)
                    mp = json.loads(rs.profileConfiguration)
                    self.myAssertDict(
                        json.loads(mp["ComponentPreselection"]),
                        acps)
                    self.myAssertDict(
                        json.loads(mp["ComponentSelection"]), cps)
                    self.myAssertDict(
                        json.loads(mp["DataSourceSelection"]), adss)
                    self.assertEqual(
                        set(json.loads(mp["UnplottedComponents"])),
                        set(lhe2))
                    self.assertEqual(json.loads(mp["OrderedChannels"]), pdss)
                    self.myAssertDict(json.loads(mp["UserData"]), records)
                    self.assertEqual(json.loads(mp["Timer"]), [ar["name"]])
                    self.assertEqual(mp["MntGrp"], "nxsmntgrp2")
#                    print "CNF", cnf
#                    print "CHDS", chds
                    myctrls = {}
                    for cl in ctrls:
                        tgc = {}
                        ttdv = None
                        idmax = 10000
                        for exp in expch:
                            ds = exp["name"]
                            if ds in chds and cl == exp['controller']:
                                cnt = self.smychsXX[str(ds)]
                                i = chds.index(str(ds))
#                                print "INDEX", i, ds
                                try:
                                    tdv = "/".join(
                                        cnt['source'].split("/")[:-1])
                                    if i < idmax:
                                        idmax = i
                                        ttdv = tdv
                                    chn = {'ndim': len(cnt['shape']),
                                           'index': i,
                                           'name': str(ds),
                                           'data_type': cnt['data_type'],
                                           'plot_type': (
                                               cnt['plot_type']
                                               if ds not in lhe2 else 0),
                                           'data_units': cnt['data_units'],
                                           'enabled': True,
                                           'label': ds,
                                           'instrument': None,
                                           'shape': cnt['shape'],
                                           '_controller_name': cl,
                                           'conditioning': '',
                                           'full_name': tdv,
                                           '_unit_id': '0',
                                           'output': True,
                                           'plot_axes': (
                                               cnt['plot_axes']
                                               if ds not in lhe2 else []),
                                           'nexus_path': '',
                                           'normalization': 0,
                                           'source': cnt['source']}
                                    tgc[tdv] = chn
                                except Exception:
                                    raise
                        if tgc:
                            myctrls[cl] = {
                                'units':
                                    {'0':
                                     {'channels': tgc,
                                      'monitor': ttdv,
                                      'id': 0,
                                      'timer': ttdv,
                                      'trigger_type': 0}}}

                    smg = {"controllers": myctrls,
                           "monitor": "%s" % dv,
                           "description": "Measurement Group",
                           "timer": "%s" % dv,
                           "label": "nxsmntgrp2"}
#                    print "SMG", smg
                    self.myAssertDict(smg, pcnf)
                    self.myAssertDict(pcnf, cnf)
                    rs.mntGrp = "nxsmntgrp"
                    rs.profileConfiguration = str(json.dumps({}))
                    rs.configDevice = val["ConfigDevice"]
                    rs.door = val["Door"]
                    rs.mntGrp = val["MntGrp"]
                    rs.fetchProfile()
                    mp = json.loads(rs.profileConfiguration)
                    self.myAssertDict(
                        json.loads(mp["ComponentPreselection"]),
                        acps)
                    self.myAssertDict(
                        json.loads(mp["ComponentSelection"]), cps)
                    self.myAssertDict(
                        json.loads(mp["DataSourceSelection"]), adss)
                    self.assertEqual(
                        set(json.loads(mp["UnplottedComponents"])),
                        set(lhe2))
                    self.assertEqual(json.loads(mp["OrderedChannels"]), pdss)
                    self.myAssertDict(json.loads(mp["UserData"]), records)
                    self.assertEqual(json.loads(mp["Timer"]), [ar["name"]])
                    self.assertEqual(mp["MntGrp"], "nxsmntgrp2")
                finally:
                    rs.deleteProfile("nxsmntgrp2")
                    try:
                        tmg.tearDown()
                    except Exception:
                        pass
        finally:
            simp2.tearDown()

    # updateMntGrp test
    def test_updateMntGrp_components_mixed_tango_unplottedcomponents(self):
        fun = sys._getframe().f_code.co_name
        print("Run: %s.%s() " % (self.__class__.__name__, fun))
        val = {"ConfigDevice": self._cf.dp.name(),
               "WriterDevice": self._wr.dp.name(),
               "Door": 'doortestp09/testts/t1r228',
               "MntGrp": 'nxsmntgrp2'}

        wrong = []
        rs = self.openRecSelector()
        rs.configDevice = val["ConfigDevice"]
        rs.door = val["Door"]
        rs.mntGrp = val["MntGrp"]
        rs.writerDevice = val["WriterDevice"]
        self.assertEqual(rs.configDevice, val["ConfigDevice"])
        self.assertEqual(rs.door, val["Door"])

        db = tango.Database()
        db.put_device_property(list(self._ms.ms.keys())[0],
                               {'PoolNames': self._pool.dp.name()})
        pool = self._pool.dp
        pool.ExpChannelList = []
        self._ms.dps[list(self._ms.ms.keys())[0]].Init()

        self.assertEqual(rs.availableMntGrps(), [])
        scalar_ctrl = 'ttestp09/testts/t1r228'
        spectrum_ctrl = 'ttestp09/testts/t2r228'
        image_ctrl = 'ttestp09/testts/t3r228'
        ctrls = [scalar_ctrl, spectrum_ctrl, image_ctrl, "__tango__"]

        simp2 = TestServerSetUp.MultiTestServerSetUp(
            devices=['ttestp09/testts/t%02dr228' % i for i in range(1, 37)])
        try:
            simp2.setUp()

            expch = []
            pdss = []
            for ds, vl in self.smychsXX.items():
                if vl:
                    exp = {}
                    exp["name"] = ds
                    exp["source"] = vl["source"]
                    if ds.startswith("image"):
                        exp["controller"] = image_ctrl
                        exp["type"] = "TwoDExpChannel"
                    if ds.startswith("spectrum"):
                        exp["controller"] = spectrum_ctrl
                        exp["type"] = "OneDExpChannel"
                    else:
                        exp["controller"] = scalar_ctrl
                        exp["type"] = "CTExpChannel"
                    expch.append(exp)
                    pdss.append(ds)
            pdss = sorted(pdss)

            acqch = [
                {"full_name": "test/ct/01/Value", "name": "ct01"},
                {"full_name": "test/ct/02/Value", "name": "ct02"},
                {"full_name": "test/ct/03/value", "name": "ct03"},
                {"full_name": "test/ct/04/value", "name": "ct04"},
                {"full_name": "null/val", "name": "mntgrp_04"}
            ]

            for ch in expch:
                ach = {}
                ach["name"] = ch["name"]
                ach["full_name"] = ch["source"]
                acqch.append(ach)

            pool.AcqChannelList = [json.dumps(a) for a in acqch]
            pool.ExpChannelList = [json.dumps(a) for a in expch]

#            self.myAssertRaise(Exception, rs.updateMntGrp)
            amycps = dict(self.smycps2)
            amycps.update(self.smycps)
            amydss = dict(self.smydssXX)
            amydss.update(self.smydss)
            amycpsstep = dict(self.smycpsstep)
            amycpsstep.update(self.smycpsstep2)
            self._cf.dp.SetCommandVariable(
                ["CPDICT", json.dumps(amycps)])
            self._cf.dp.SetCommandVariable(
                ["DSDICT", json.dumps(amydss)])

            for i in range(6):
                try:
                    ar = acqch[i % 5]
                    cps = {}
                    acps = {}
                    dss = {}
                    # lcp = self._rnd.randint(1, 40)
                    # lds = self._rnd.randint(1, 40)

                    self._cf.dp.SetCommandVariable(
                        ["CPDICT", json.dumps(amycps)])
                    self._cf.dp.SetCommandVariable(
                        ["DSDICT", json.dumps(amydss)])
                    comps = set()

                    ncps = self._rnd.randint(1, len(amycps) - 1)
                    lcps = self._rnd.sample(list(amycps.keys()), ncps)
                    for cp in lcps:
                        if cp not in wrong:
                            cps[cp] = bool(self._rnd.randint(0, 1))
                            if cps[cp]:
                                comps.add(cp)

                    ancps = self._rnd.randint(1, len(list(amycps.keys())) - 1)
                    alcps = self._rnd.sample(list(amycps.keys()), ancps)
                    for cp in alcps:
                        if cp not in wrong:
                            acps[cp] = bool(self._rnd.randint(0, 1))
                            if acps[cp]:
                                comps.add(cp)

                    ndss = self._rnd.randint(1, len(list(amycps.keys())) - 1)
                    ldss = self._rnd.sample(list(amycps.keys()), ndss)
                    for ds in ldss:
                        if ds in amydss.keys():
                            if ds not in wrong:
                                dss[ds] = bool(self._rnd.randint(0, 1))

                    ndss = self._rnd.randint(1, len(list(amydss.keys())) - 1)
                    ldss = self._rnd.sample(list(amydss.keys()), ndss)
                    for ds in ldss:
                        if ds in amydss.keys():
                            if ds not in wrong:
                                dss[ds] = bool(self._rnd.randint(0, 1))

                    mncps = self._rnd.randint(1, len(list(amycps.keys())) - 1)
                    mcps = [cp for cp in self._rnd.sample(
                            list(amycps.keys()), mncps) if cp not in wrong]
                    for cp in mcps:
                        comps.add(cp)

                    adss = dict(dss)
                    for ch in expch:
                        if ch["name"] not in adss.keys():
                            adss[ch["name"]] = False
                    mp = json.loads(rs.profileConfiguration)
                    mp["ComponentSelection"] = json.dumps(cps)
                    mp["ComponentPreselection"] = json.dumps(acps)
                    mp["DataSourceSelection"] = json.dumps(dss)
                    self._cf.dp.SetCommandVariable(["MCPLIST",
                                                    json.dumps(mcps)])

                    rs.profileConfiguration = str(json.dumps(mp))
                    mp = json.loads(rs.profileConfiguration)
                    records = {}
                    describer = Describer(self._cf.dp, True)
                    cpres = describer.components(dstype='CLIENT')
                    for grp in cpres:
                        for idss in grp.values():
                            for idsrs in idss.values():
                                for idsr in idsrs:
                                    records[str(idsr[2])] = "1234"
                    dsres = describer.dataSources(
                        list(dss.keys()), dstype='CLIENT')[0]
                    for dsr in dsres.values():
                        records[str(dsr.record)] = '2345'

                    mp = json.loads(rs.profileConfiguration)
                    mp["Timer"] = '["%s"]' % ar["name"]
                    mp["UserData"] = json.dumps(records)
                    rs.profileConfiguration = str(json.dumps(mp))
                    mp = json.loads(rs.profileConfiguration)

                    tmg = TestMGSetUp.TestMeasurementGroupSetUp(
                        name='nxsmntgrp2')
                    dv = "/".join(ar["full_name"].split("/")[0:-1])
                    chds = [ds for ds in rs.selectedDataSources()
                            if not ds.startswith('client')]
                    # chds1 = list(chds)
                    chds2 = [ds for ds in rs.componentDataSources()
                             if not ds.startswith('client')]
                    chds.extend(chds2)
                    tmpchds = sorted(chds)
                    chds = []
                    for ds in tmpchds:
                        if ds in pdss:
                            chds.append(ds)
                    for ds in tmpchds:
                        if ds not in pdss:
                            chds.append(ds)

                    lheds = []
                    if chds:
                        nhe = self._rnd.randint(0, len(set(chds)) - 1)
                        lheds = self._rnd.sample(list(chds), nhe)

                    lhecp = []
                    if comps:
                        nhe = self._rnd.randint(0, len(set(comps)) - 1)
                        lhecp = self._rnd.sample(list(comps), nhe)

                    lhe = lheds + lhecp

                    mp = json.loads(rs.profileConfiguration)
                    mp["UnplottedComponents"] = json.dumps(lhe)
                    mp["OrderedChannels"] = json.dumps(pdss)
                    rs.profileConfiguration = str(json.dumps(mp))
                    mp = json.loads(rs.profileConfiguration)

                    lhe2 = []
                    for el in lhe:
                        found = False
                        for cp in comps:
                            if el in amycpsstep[cp]:
                                if cp not in lhecp:
                                    found = True
                        if not found:
                            lhe2.append(el)

                    self.myAssertDict(
                        json.loads(mp["ComponentPreselection"]),
                        acps)
                    self.myAssertDict(
                        json.loads(mp["ComponentSelection"]), cps)
                    self.myAssertDict(
                        json.loads(mp["DataSourceSelection"]), adss)
                    self.assertEqual(
                        set(json.loads(mp["UnplottedComponents"])),
                        set(lhe))
                    self.assertEqual(json.loads(mp["OrderedChannels"]), pdss)
                    self.myAssertDict(json.loads(mp["UserData"]), records)
                    self.assertEqual(json.loads(mp["Timer"]), [ar["name"]])
                    self.assertEqual(mp["MntGrp"], "nxsmntgrp2")

                    wwcp = rs.components
                    describer = Describer(self._cf.dp, True)
                    res = describer.components(wwcp, "STEP", "")

                    # mdds = set()
                    for mdss in res[0].values():
                        if isinstance(mdss, dict):
                            for ds in mdss.keys():
                                adss[ds] = True

                    jpcnf = rs.updateMntGrp()
                    pcnf = json.loads(jpcnf)
                    mgdp = tango.DeviceProxy(tmg.new_device_info_writer.name)
                    jcnf = mgdp.Configuration
                    cnf = json.loads(jcnf)
                    mp = json.loads(rs.profileConfiguration)
                    self.myAssertDict(
                        json.loads(mp["ComponentPreselection"]),
                        acps)
                    self.myAssertDict(
                        json.loads(mp["ComponentSelection"]), cps)
                    self.myAssertDict(
                        json.loads(mp["DataSourceSelection"]), adss)
                    self.assertEqual(
                        set(json.loads(mp["UnplottedComponents"])),
                        set(lhe2))
                    self.assertEqual(json.loads(mp["OrderedChannels"]), pdss)
                    self.myAssertDict(json.loads(mp["UserData"]), records)
                    self.assertEqual(json.loads(mp["Timer"]), [ar["name"]])
                    self.assertEqual(mp["MntGrp"], "nxsmntgrp2")
#                    print "CNF", cnf
#                    print "CHDS", chds
                    myctrls = {}
                    for cl in ctrls:
                        tgc = {}
                        ttdv = None
                        idmax = 10000
                        for exp in expch:
                            ds = exp["name"]
                            if ds in chds and cl == exp['controller']:
                                if ds in self.smychsXX.keys():
                                    cnt = self.smychsXX[str(ds)]
                                    i = chds.index(str(ds))
#                                    print "INDEX", i, ds
                                    try:
                                        tdv = "/".join(
                                            cnt['source'].split("/")[:-1])
                                        if i < idmax:
                                            idmax = i
                                            ttdv = tdv
                                        chn = {'ndim': len(cnt['shape']),
                                               'index': i,
                                               'name': str(ds),
                                               'data_type': cnt['data_type'],
                                               'plot_type': (
                                                   cnt['plot_type']
                                                   if ds not in lhe2 else 0),
                                               'data_units': cnt['data_units'],
                                               'enabled': True,
                                               'label': ds,
                                               'instrument': None,
                                               'shape': cnt['shape'],
                                               '_controller_name': cl,
                                               'conditioning': '',
                                               'full_name': tdv,
                                               '_unit_id': '0',
                                               'output': True,
                                               'plot_axes': (
                                                   cnt['plot_axes']
                                                   if ds not in lhe2 else []),
                                               'nexus_path': '',
                                               'normalization': 0,
                                               'source': cnt['source']}
                                        tgc[tdv] = chn
                                    except Exception:
                                        raise
                        if tgc:
                            myctrls[cl] = {'units':
                                           {'0':
                                            {'channels': tgc,
                                             'monitor': ttdv,
                                             'id': 0,
                                             'timer': ttdv,
                                             'trigger_type': 0}}}

                    tgc = {}
                    for ds in chds:
                        if ds in self.smychs:
                            cnt = self.smychs[str(ds)]
                            i = chds.index(str(ds))
#                            print "INDEX", i, ds
                            try:
                                chn = {'ndim': len(cnt['shape']),
                                       'index': i,
                                       'name': str(ds),
                                       'data_type': cnt['data_type'],
                                       'plot_type': (
                                           cnt['plot_type']
                                           if ds not in lhe2 else 0),
                                       'data_units': cnt['data_units'],
                                       'enabled': True,
                                       'label': cnt['source'],
                                       'instrument': None,
                                       'shape': cnt['shape'],
                                       '_controller_name': '__tango__',
                                       'conditioning': '',
                                       'full_name': '%s%s' % (
                                           'tango://', cnt['source']),
                                       '_unit_id': '0',
                                       'output': True,
                                       'plot_axes': (
                                           cnt['plot_axes']
                                           if ds not in lhe2 else []),
                                       'nexus_path': '',
                                       'normalization': 0,
                                       'source': cnt['source']}
                                tgc[chn["full_name"]] = chn
                            except Exception:
                                raise
                    if tgc:
                        myctrls['__tango__'] = {'units':
                                                {'0':
                                                 {'channels': tgc,
                                                  'monitor': dv,
                                                  'id': 0,
                                                  'timer': dv,
                                                  'trigger_type': 0}}}

                    smg = {"controllers": myctrls,
                           "monitor": "%s" % dv,
                           "description": "Measurement Group",
                           "timer": "%s" % dv,
                           "label": "nxsmntgrp2"}
#                    print "SMG", smg
                    self.myAssertDict(smg, pcnf)
                    self.myAssertDict(pcnf, cnf)
                    rs.mntGrp = "nxsmntgrp"
                    rs.profileConfiguration = str(json.dumps({}))
                    rs.configDevice = val["ConfigDevice"]
                    rs.door = val["Door"]
                    rs.mntGrp = val["MntGrp"]
                    rs.fetchProfile()
                    mp = json.loads(rs.profileConfiguration)
                    self.myAssertDict(
                        json.loads(mp["ComponentPreselection"]),
                        acps)
                    self.myAssertDict(
                        json.loads(mp["ComponentSelection"]), cps)
                    self.myAssertDict(
                        json.loads(mp["DataSourceSelection"]), adss)
                    self.assertEqual(
                        set(json.loads(mp["UnplottedComponents"])),
                        set(lhe2))
                    self.assertEqual(json.loads(mp["OrderedChannels"]), pdss)
                    self.myAssertDict(json.loads(mp["UserData"]), records)
                    self.assertEqual(json.loads(mp["Timer"]), [ar["name"]])
                    self.assertEqual(mp["MntGrp"], "nxsmntgrp2")
                finally:
                    rs.deleteProfile("nxsmntgrp2")
                    try:
                        tmg.tearDown()
                    except Exception:
                        pass
        finally:
            simp2.tearDown()

    # updateMntGrp test
    def test_updateMntGrp_components_mixed_tango_orderedchannels(self):
        fun = sys._getframe().f_code.co_name
        print("Run: %s.%s() " % (self.__class__.__name__, fun))
        val = {"ConfigDevice": self._cf.dp.name(),
               "WriterDevice": self._wr.dp.name(),
               "Door": 'doortestp09/testts/t1r228',
               "MntGrp": 'mg2'}

        wrong = []
        rs = self.openRecSelector()
        rs.configDevice = val["ConfigDevice"]
        rs.door = val["Door"]
        # print "DOOR", rs.door
        rs.mntGrp = val["MntGrp"]
        rs.writerDevice = val["WriterDevice"]
        self.assertEqual(rs.configDevice, val["ConfigDevice"])
        self.assertEqual(rs.door, val["Door"])

        db = tango.Database()
        db.put_device_property(list(self._ms.ms.keys())[0],
                               {'PoolNames': self._pool.dp.name()})
        pool = self._pool.dp
        pool.ExpChannelList = []
        self._ms.dps[list(self._ms.ms.keys())[0]].Init()

        self.assertEqual(rs.availableMntGrps(), [])
#        self.myAssertRaise(Exception, rs.updateMntGrp)

        db = tango.Database()
        db.put_device_property(list(self._ms.ms.keys())[0],
                               {'PoolNames': self._pool.dp.name()})
        pool = self._pool.dp
        self._ms.dps[list(self._ms.ms.keys())[0]].Init()

        self.assertEqual(rs.availableMntGrps(), [])
        scalar_ctrl = 'ttestp09/testts/t1r228'
        spectrum_ctrl = 'ttestp09/testts/t2r228'
        image_ctrl = 'ttestp09/testts/t3r228'
        ctrls = [scalar_ctrl, spectrum_ctrl, image_ctrl, "__tango__"]

        simp2 = TestServerSetUp.MultiTestServerSetUp(
            devices=['ttestp09/testts/t%02dr228' % i for i in range(1, 37)])
        try:
            simp2.setUp()

            expch = []
            pdss = []
            for ds, vl in self.smychsXX.items():
                if vl:
                    exp = {}
                    exp["name"] = ds
                    exp["source"] = vl["source"]
                    if ds.startswith("image"):
                        exp["controller"] = image_ctrl
                        exp["type"] = "TwoDExpChannel"
                    if ds.startswith("spectrum"):
                        exp["controller"] = spectrum_ctrl
                        exp["type"] = "OneDExpChannel"
                    else:
                        exp["controller"] = scalar_ctrl
                        exp["type"] = "CTExpChannel"
                    expch.append(exp)
                    pdss.append(ds)
            pdss = sorted(pdss)
            self._rnd.shuffle(pdss)

            acqch = [
                {"full_name": "test/ct/01/Value", "name": "ct01"},
                {"full_name": "test/ct/02/Value", "name": "ct02"},
                {"full_name": "test/ct/03/value", "name": "ct03"},
                {"full_name": "test/ct/04/value", "name": "ct04"},
                {"full_name": "null/val", "name": "mntgrp_04"}
            ]

            for ch in expch:
                ach = {}
                ach["name"] = ch["name"]
                ach["full_name"] = ch["source"]
                acqch.append(ach)

            pool.AcqChannelList = [json.dumps(a) for a in acqch]
            pool.ExpChannelList = [json.dumps(a) for a in expch]

#            self.myAssertRaise(Exception, rs.updateMntGrp)
            amycps = dict(self.smycps2)
            amycps.update(self.smycps)
            amydss = dict(self.smydssXX)
            amydss.update(self.smydss)
            amycpsstep = dict(self.smycpsstep)
            amycpsstep.update(self.smycpsstep2)
            self._cf.dp.SetCommandVariable(
                ["CPDICT", json.dumps(amycps)])
            self._cf.dp.SetCommandVariable(
                ["DSDICT", json.dumps(amydss)])

            for i in range(6):
                try:
                    ar = acqch[i % 5]
                    cps = {}
                    acps = {}
                    dss = {}
                    # lcp = self._rnd.randint(1, 40)
                    # lds = self._rnd.randint(1, 40)

                    self._cf.dp.SetCommandVariable(
                        ["CPDICT", json.dumps(amycps)])
                    self._cf.dp.SetCommandVariable(
                        ["DSDICT", json.dumps(amydss)])
                    comps = set()

                    ncps = self._rnd.randint(1, len(amycps) - 1)
                    lcps = self._rnd.sample(list(amycps.keys()), ncps)
                    for cp in lcps:
                        if cp not in wrong:
                            cps[cp] = bool(self._rnd.randint(0, 1))
                            if cps[cp]:
                                comps.add(cp)

                    ancps = self._rnd.randint(1, len(list(amycps.keys())) - 1)
                    alcps = self._rnd.sample(list(amycps.keys()), ancps)
                    for cp in alcps:
                        if cp not in wrong:
                            acps[cp] = bool(self._rnd.randint(0, 1))
                            if acps[cp]:
                                comps.add(cp)

                    ndss = self._rnd.randint(1, len(list(amycps.keys())) - 1)
                    ldss = self._rnd.sample(list(amycps.keys()), ndss)
                    for ds in ldss:
                        if ds in amydss.keys():
                            if ds not in wrong:
                                dss[ds] = bool(self._rnd.randint(0, 1))

                    ndss = self._rnd.randint(1, len(list(amydss.keys())) - 1)
                    ldss = self._rnd.sample(list(amydss.keys()), ndss)
                    for ds in ldss:
                        if ds in amydss.keys():
                            if ds not in wrong:
                                dss[ds] = bool(self._rnd.randint(0, 1))

                    mncps = self._rnd.randint(1, len(list(amycps.keys())) - 1)
                    mcps = [cp for cp in self._rnd.sample(
                        list(amycps.keys()), mncps) if cp not in wrong]
                    for cp in mcps:
                        comps.add(cp)

                    adss = dict(dss)
                    for ch in expch:
                        if ch["name"] not in adss.keys():
                            adss[ch["name"]] = False
                    mp = json.loads(rs.profileConfiguration)
                    mp["ComponentSelection"] = json.dumps(cps)
                    mp["ComponentPreselection"] = json.dumps(acps)
                    mp["DataSourceSelection"] = json.dumps(dss)
                    self._cf.dp.SetCommandVariable(["MCPLIST",
                                                    json.dumps(mcps)])
                    rs.profileConfiguration = str(json.dumps(mp))
                    mp = json.loads(rs.profileConfiguration)

                    records = {}
                    describer = Describer(self._cf.dp, True)
                    cpres = describer.components(dstype='CLIENT')
                    for grp in cpres:
                        for idss in grp.values():
                            for idsrs in idss.values():
                                for idsr in idsrs:
                                    records[str(idsr[2])] = "1234"
                    dsres = describer.dataSources(
                        list(dss.keys()), dstype='CLIENT')[0]
                    for dsr in dsres.values():
                        records[str(dsr.record)] = '2345'

                    mp = json.loads(rs.profileConfiguration)
                    mp["Timer"] = '["%s"]' % ar["name"]
                    mp["UserData"] = json.dumps(records)
                    rs.profileConfiguration = str(json.dumps(mp))
                    mp = json.loads(rs.profileConfiguration)

                    tmg = TestMGSetUp.TestMeasurementGroupSetUp(
                        name='mg2')
                    dv = "/".join(ar["full_name"].split("/")[0:-1])
                    chds = [ds for ds in rs.selectedDataSources()
                            if not ds.startswith('client')]
                    # chds1 = list(chds)
                    chds2 = [ds for ds in rs.componentDataSources()
                             if not ds.startswith('client')]
                    chds.extend(chds2)
                    tmpchds = sorted(chds)
                    chds = []
                    for ds in pdss:
                        if ds in tmpchds:
                            chds.append(ds)
                    for ds in tmpchds:
                        if ds not in pdss:
                            chds.append(ds)

                    lheds = []
                    if chds:
                        nhe = self._rnd.randint(0, len(set(chds)) - 1)
                        lheds = self._rnd.sample(list(chds), nhe)

                    lhecp = []
                    if comps:
                        nhe = self._rnd.randint(0, len(set(comps)) - 1)
                        lhecp = self._rnd.sample(list(comps), nhe)

                    lhe = lheds + lhecp

                    mp = json.loads(rs.profileConfiguration)
                    mp["UnplottedComponents"] = json.dumps(lhe)
                    mp["OrderedChannels"] = json.dumps(pdss)
                    rs.profileConfiguration = str(json.dumps(mp))
                    mp = json.loads(rs.profileConfiguration)

                    lhe2 = []
                    for el in lhe:
                        found = False
                        for cp in comps:
                            if el in amycpsstep[cp]:
                                if cp not in lhecp:
                                    found = True
                        if not found:
                            lhe2.append(el)

#                    print "LHE", lhe
#                    print "LHE2", lhe2
#                    print "LHECP", lhecp
#                    print "COMPS", comps

#                    print "COMP", rs.components()
#                    print "ACOMP", rs.preselectedComponents()
#                    print "MCP", mcps
#                    print "DS", rs.dataSources()
#                    print "DDS", rs.componentDataSources()

                    self.myAssertDict(
                        json.loads(mp["ComponentPreselection"]),
                        acps)
                    self.myAssertDict(
                        json.loads(mp["ComponentSelection"]), cps)
                    self.myAssertDict(
                        json.loads(mp["DataSourceSelection"]), adss)
                    self.assertEqual(
                        set(json.loads(mp["UnplottedComponents"])),
                        set(lhe))
                    self.assertEqual(json.loads(mp["OrderedChannels"]), pdss)
                    self.myAssertDict(json.loads(mp["UserData"]), records)
                    self.assertEqual(json.loads(mp["Timer"]), [ar["name"]])
                    self.assertEqual(mp["MntGrp"], "mg2")

                    wwcp = rs.components
                    describer = Describer(self._cf.dp, True)
                    res = describer.components(wwcp, "STEP", "")

                    # mdds = set()
                    for mdss in res[0].values():
                        if isinstance(mdss, dict):
                            for ds in mdss.keys():
                                adss[ds] = True

                    # print "UPGRAGE MNT"
                    jpcnf = rs.updateMntGrp()
                    pcnf = json.loads(jpcnf)
                    mgdp = tango.DeviceProxy(tmg.new_device_info_writer.name)
                    jcnf = mgdp.Configuration
                    cnf = json.loads(jcnf)
                    mp = json.loads(rs.profileConfiguration)
                    self.myAssertDict(
                        json.loads(mp["ComponentPreselection"]),
                        acps)
                    self.myAssertDict(
                        json.loads(mp["ComponentSelection"]), cps)
                    self.myAssertDict(
                        json.loads(mp["DataSourceSelection"]), adss)
                    self.assertEqual(
                        set(json.loads(mp["UnplottedComponents"])),
                        set(lhe2))
                    self.assertEqual(json.loads(mp["OrderedChannels"]), pdss)
                    self.myAssertDict(json.loads(mp["UserData"]), records)
                    self.assertEqual(json.loads(mp["Timer"]), [ar["name"]])
                    self.assertEqual(mp["MntGrp"], "mg2")
#                    print "CNF", cnf
#                    print "CHDS", chds
                    myctrls = {}
                    for cl in ctrls:
                        tgc = {}
                        ttdv = None
                        idmax = 10000
                        for exp in expch:
                            ds = exp["name"]
                            if ds in chds and cl == exp['controller']:
                                if ds in self.smychsXX.keys():
                                    cnt = self.smychsXX[str(ds)]
                                    i = chds.index(str(ds))
#                                    print "INDEX", i, ds
                                    try:
                                        tdv = "/".join(
                                            cnt['source'].split("/")[:-1])
                                        if i < idmax:
                                            idmax = i
                                            ttdv = tdv
                                        chn = {'ndim': len(cnt['shape']),
                                               'index': i,
                                               'name': str(ds),
                                               'data_type': cnt['data_type'],
                                               'plot_type': (
                                                   cnt['plot_type']
                                                   if ds not in lhe2 else 0),
                                               'data_units': cnt['data_units'],
                                               'enabled': True,
                                               'label': ds,
                                               'instrument': None,
                                               'shape': cnt['shape'],
                                               '_controller_name': cl,
                                               'conditioning': '',
                                               'full_name': tdv,
                                               '_unit_id': '0',
                                               'output': True,
                                               'plot_axes': (
                                                   cnt['plot_axes']
                                                   if ds not in lhe2 else []),
                                               'nexus_path': '',
                                               'normalization': 0,
                                               'source': cnt['source']}
                                        tgc[tdv] = chn
                                    except Exception:
                                        raise
                        if tgc:
                            myctrls[cl] = {'units':
                                           {'0':
                                            {'channels': tgc,
                                             'monitor': ttdv,
                                             'id': 0,
                                             'timer': ttdv,
                                             'trigger_type': 0}}}

                    tgc = {}
                    for ds in chds:
                        if ds in self.smychs:
                            cnt = self.smychs[str(ds)]
                            i = chds.index(str(ds))
#                            print "INDEX", i, ds
                            try:
                                chn = {'ndim': len(cnt['shape']),
                                       'index': i,
                                       'name': str(ds),
                                       'data_type': cnt['data_type'],
                                       'plot_type': (
                                           cnt['plot_type']
                                           if ds not in lhe2 else 0),
                                       'data_units': cnt['data_units'],
                                       'enabled': True,
                                       'label': cnt['source'],
                                       'instrument': None,
                                       'shape': cnt['shape'],
                                       '_controller_name': '__tango__',
                                       'conditioning': '',
                                       'full_name': '%s%s' % (
                                           'tango://', cnt['source']),
                                       '_unit_id': '0',
                                       'output': True,
                                       'plot_axes': (
                                           cnt['plot_axes']
                                           if ds not in lhe2 else []),
                                       'nexus_path': '',
                                       'normalization': 0,
                                       'source': cnt['source']}
                                tgc[chn["full_name"]] = chn
                            except Exception:
                                raise

                    if tgc:
                        myctrls['__tango__'] = {'units':
                                                {'0':
                                                 {'channels': tgc,
                                                  'monitor': dv,
                                                  'id': 0,
                                                  'timer': dv,
                                                  'trigger_type': 0}}}

                    smg = {"controllers": myctrls,
                           "monitor": "%s" % dv,
                           "description": "Measurement Group",
                           "timer": "%s" % dv,
                           "label": "mg2"}
                    self.myAssertDict(smg, pcnf)
                    self.myAssertDict(pcnf, cnf)
                    rs.mntGrp = "nxsmntgrp"
                    rs.profileConfiguration = str(json.dumps({}))
                    rs.configDevice = val["ConfigDevice"]
                    rs.door = val["Door"]
                    rs.mntGrp = "mg2"
                    rs.fetchProfile()
                    mp = json.loads(rs.profileConfiguration)
                    self.myAssertDict(
                        json.loads(mp["ComponentPreselection"]),
                        acps)
                    self.myAssertDict(
                        json.loads(mp["ComponentSelection"]), cps)
                    self.myAssertDict(
                        json.loads(mp["DataSourceSelection"]), adss)
                    self.assertEqual(
                        set(json.loads(mp["UnplottedComponents"])),
                        set(lhe2))
                    self.assertEqual(json.loads(mp["OrderedChannels"]), pdss)
                    self.myAssertDict(json.loads(mp["UserData"]), records)
                    self.assertEqual(json.loads(mp["Timer"]), [ar["name"]])
                    self.assertEqual(mp["MntGrp"], "mg2")
                finally:
                    rs.deleteProfile("mg2")
                    try:
                        tmg.tearDown()
                    except Exception:
                        pass
        finally:
            simp2.tearDown()


if __name__ == '__main__':
    unittest.main()
