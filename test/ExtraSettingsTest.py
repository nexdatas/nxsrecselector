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
# \file SettingsTest.py
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
import json
import pickle
import string
import time
import nxsrecconfig
import xml

import logging
logger = logging.getLogger()

import TestMacroServerSetUp
import TestPoolSetUp
import TestServerSetUp
import TestConfigServerSetUp
import TestWriterSetUp
import TestMGSetUp
import SettingsTest


from nxsrecconfig.MacroServerPools import MacroServerPools
from nxsrecconfig.Selector import Selector
from nxsrecconfig.ProfileManager import ProfileManager
from nxsrecconfig.Describer import Describer
from nxsrecconfig.Settings import Settings
from nxsrecconfig.Utils import TangoUtils, MSUtils
from nxsconfigserver.XMLConfigurator import XMLConfigurator
from nxsrecconfig.Utils import TangoUtils, MSUtils, Utils

# if 64-bit machione
IS64BIT = (struct.calcsize("P") == 8)

# list of available databases
DB_AVAILABLE = []

#: tango version
TGVER = PyTango.__version_info__[0]

try:
    import MySQLdb
    # connection arguments to MYSQL DB
    mydb = MySQLdb.connect({})
    mydb.close()
    DB_AVAILABLE.append("MYSQL")
except:
    try:
        import MySQLdb
    # connection arguments to MYSQL DB
        args = {'host': 'localhost', 'db': 'nxsconfig',
                'read_default_file': '/etc/my.cnf', 'use_unicode': True}
    # inscance of MySQLdb
        mydb = MySQLdb.connect(**args)
        mydb.close()
        DB_AVAILABLE.append("MYSQL")
    except:
        try:
            import MySQLdb
            from os.path import expanduser
            home = expanduser("~")
        # connection arguments to MYSQL DB
            args2 = {'host': 'localhost', 'db': 'nxsconfig',
                     'read_default_file': '%s/.my.cnf' % home,
                     'use_unicode': True}
        # inscance of MySQLdb
            mydb = MySQLdb.connect(**args2)
            mydb.close()
            DB_AVAILABLE.append("MYSQL")

        except ImportError, e:
            print "MYSQL not available: %s" % e
        except Exception, e:
            print "MYSQL not available: %s" % e
        except:
            print "MYSQL not available"


# test fixture
class ExtraSettingsTest(SettingsTest.SettingsTest):

    # constructor
    # \param methodName name of the test method

    def __init__(self, methodName):
        SettingsTest.SettingsTest.__init__(self, methodName)

    # updateMntGrp test
    def test_updateMntGrp_components_mixed_tango_timers(self):
        fun = sys._getframe().f_code.co_name
        print "Run: %s.%s() " % (self.__class__.__name__, fun)
        val = {"ConfigDevice": self._cf.dp.name(),
               "WriterDevice": self._wr.dp.name(),
               "Door": 'doortestp09/testts/t1r228',
               "MntGrp": 'mg2'}

        wrong = []
        rs = self.openRecSelector()
        rs.configDevice = val["ConfigDevice"]
        rs.door = val["Door"]
        rs.mntGrp = val["MntGrp"]
        rs.writerDevice = val["WriterDevice"]
        self.assertEqual(rs.configDevice, val["ConfigDevice"])
        self.assertEqual(rs.door, val["Door"])

        db = PyTango.Database()
        db.put_device_property(self._ms.ms.keys()[0],
                               {'PoolNames': self._pool.dp.name()})
        pool = self._pool.dp
        pool.ExpChannelList = []
        self._ms.dps[self._ms.ms.keys()[0]].Init()

        self.assertEqual(rs.availableMntGrps(), [])
        self.myAssertRaise(Exception, rs.updateMntGrp)

        db = PyTango.Database()
        db.put_device_property(self._ms.ms.keys()[0],
                               {'PoolNames': self._pool.dp.name()})
        pool = self._pool.dp
        self._ms.dps[self._ms.ms.keys()[0]].Init()

        self.assertEqual(rs.availableMntGrps(), [])
        scalar_ctrl = 'ttestp09/testts/t1r228'
        spectrum_ctrl = 'ttestp09/testts/t2r228'
        image_ctrl = 'ttestp09/testts/t3r228'

        simp2 = TestServerSetUp.MultiTestServerSetUp(
            devices=['ttestp09/testts/t%02dr228' % i for i in range(1, 37)])
        try:
            simp2.setUp()
            for i in range(30):

                ctrls = [scalar_ctrl, spectrum_ctrl, image_ctrl, "__tango__"]
                expch = []
                pdss = []

                timers = {}
                ntms = self._rnd.randint(1, 5)
                tms = self._rnd.sample(set(
                    [ch for ch in self.smychsXX.keys()
                     if not ch.startswith("client")]), ntms)
                for tm in tms:
                    myct = ("ctrl_%s" % tm).replace("_", "/")
                    timers[myct] = tm
                    ctrls.append(myct)
                ltimers = timers.values()

                for ds, vl in self.smychsXX.items():
                    if vl:
                        exp = {}
                        exp["name"] = ds
                        exp["source"] = vl["source"]
                        myct = None
                        for ct, ch in timers.items():
                            if ds == ch:
                                myct = ct
                                break

                        if myct:
                            exp["controller"] = myct
                            exp["type"] = "CTExpChannel"
                        elif ds.startswith("image"):
                            exp["controller"] = image_ctrl
                            exp["type"] = "TwoDExpChannel"
                        elif ds.startswith("spectrum"):
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

                try:
                    cps = {}
                    acps = {}
                    dss = {}
                    lcp = self._rnd.randint(1, 40)
                    lds = self._rnd.randint(1, 40)

                    self._cf.dp.SetCommandVariable(
                        ["CPDICT", json.dumps(amycps)])
                    self._cf.dp.SetCommandVariable(
                        ["DSDICT", json.dumps(amydss)])
                    comps = set()

                    ncps = self._rnd.randint(1, len(amycps) - 1)
                    lcps = self._rnd.sample(set(amycps.keys()), ncps)
                    for cp in lcps:
                        if cp not in wrong:
                            cps[cp] = bool(self._rnd.randint(0, 1))
                            if cps[cp]:
                                comps.add(cp)

                    ancps = self._rnd.randint(1, len(amycps.keys()) - 1)
                    alcps = self._rnd.sample(set(amycps.keys()), ancps)
                    for cp in alcps:
                        if cp not in wrong:
                            acps[cp] = bool(self._rnd.randint(0, 1))
                            if acps[cp]:
                                comps.add(cp)

                    ndss = self._rnd.randint(1, len(amycps.keys()) - 1)
                    ldss = self._rnd.sample(set(amycps.keys()), ndss)
                    for ds in ldss:
                        if ds in amydss.keys():
                            if ds not in wrong:
                                dss[ds] = bool(self._rnd.randint(0, 1))

                    ndss = self._rnd.randint(1, len(amydss.keys()) - 1)
                    ldss = self._rnd.sample(set(amydss.keys()), ndss)
                    for ds in ldss:
                        if ds in amydss.keys():
                            if ds not in wrong:
                                dss[ds] = bool(self._rnd.randint(0, 1))

                    for tm in ltimers:
                        dss[tm] = bool(self._rnd.randint(0, 1))

                    mncps = self._rnd.randint(1, len(amycps.keys()) - 1)
                    mcps = [cp for cp in self._rnd.sample(
                            set(amycps.keys()), mncps) if cp not in wrong]
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
                        dss.keys(), dstype='CLIENT')[0]
                    for dsr in dsres.values():
                        records[str(dsr.record)] = '2345'

                    mp = json.loads(rs.profileConfiguration)
                    mp["Timer"] = json.dumps(ltimers)
                    mp["UserData"] = json.dumps(records)
                    rs.profileConfiguration = str(json.dumps(mp))
                    mp = json.loads(rs.profileConfiguration)

                    tmg = TestMGSetUp.TestMeasurementGroupSetUp(
                        name='mg2')
#                    dv = "/".join(ar["full_name"].split("/")[0:-1])
                    chds = [ds for ds in rs.selectedDataSources()
                            if not ds.startswith('client')]
                    chds1 = list(chds)
                    chds2 = [ds for ds in rs.componentDataSources()
                             if not ds.startswith('client')]
                    chds.extend(chds2)
                    bchds = list(chds)
                    chds.extend(ltimers)
                    tmpchds = sorted(list(set(chds)))
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
                        lheds = self._rnd.sample(set(chds), nhe)

                    lhecp = []
                    if comps:
                        nhe = self._rnd.randint(0, len(set(comps)) - 1)
                        lhecp = self._rnd.sample(set(comps), nhe)

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
                    self.assertEqual(json.loads(mp["Timer"]), ltimers)
                    self.assertEqual(mp["MntGrp"], "mg2")

                    wwcp = rs.components
                    describer = Describer(self._cf.dp, True)
                    res = describer.components(wwcp, "STEP", "")

                    mdds = set()
                    for mdss in res[0].values():
                        if isinstance(mdss, dict):
                            for ds in mdss.keys():
                                adss[ds] = True

                    for tm in ltimers:
                        if tm in lhe2:
                            if tm in adss.keys():
                                adss[tm] = False

                    jpcnf = rs.updateMntGrp()
                    pcnf = json.loads(jpcnf)
                    mgdp = PyTango.DeviceProxy(tmg.new_device_info_writer.name)
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
                    self.assertEqual(json.loads(mp["Timer"]), ltimers)
                    self.assertEqual(mp["MntGrp"], "mg2")
                    myctrls = {}
                    fgtm = "/".join(
                        self.smychsXX[str(ltimers[0])]['source'].split(
                            "/")[:-1])
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
                                    try:
                                        tdv = "/".join(
                                            cnt['source'].split("/")[:-1])
                                        if i < idmax:
                                            idmax = i
                                            ttdv = tdv
                                        chn = {'ndim': 0,
                                               'index': i,
                                               'name': str(ds),
                                               'data_type': cnt['data_type'],
                                               'plot_type': (
                                                   cnt['plot_type']
                                                   if (ds not in lhe2
                                                       and ds in bchds)
                                                   else 0),
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
                                                   if (ds not in lhe2
                                                       and ds in bchds)
                                                   else []),
                                               'nexus_path': '',
                                               'normalization': 0,
                                               'source': cnt['source']}
                                        tgc[tdv] = chn
                                    except:
                                        raise
                        if tgc:
                            ltm = timers[cl] if cl in timers.keys() \
                                else ltimers[0]
                            fltm = "/".join(
                                self.smychsXX[str(ltm)]['source'].split(
                                    "/")[:-1])
                            myctrls[cl] = {
                                'units':
                                    {'0':
                                     {
                                         'channels': tgc,
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
                                chn = {'ndim': 0,
                                       'index': i,
                                       'name': str(ds),
                                       'data_type': cnt['data_type'],
                                       'plot_type': (cnt['plot_type']
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
                            except:
                                raise

                    if tgc:
                        myctrls['__tango__'] = {'units':
                                                {'0':
                                                 {'channels': tgc,
                                                  'monitor': fgtm,
                                                  'id': 0,
                                                  'timer': fgtm,
                                                  'trigger_type': 0}}}

                    smg = {"controllers": myctrls,
                           "monitor": "%s" % fgtm,
                           "description": "Measurement Group",
                           "timer": "%s" % fgtm,
                           "label": "mg2"}
#                    print "SMG", smg
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
                    self.assertEqual(json.loads(mp["Timer"]), ltimers)
                    self.assertEqual(mp["MntGrp"], "mg2")
                finally:
                    try:
                        rs.deleteProfile("mg2")
                    except:
                        pass
                    try:
                        tmg.tearDown()
                    except:
                        pass
        finally:
            simp2.tearDown()

    # updateMntGrp test
    def test_updateMntGrp_mntGrpConfiguration_isMntGrpUpdated(self):
        fun = sys._getframe().f_code.co_name
        print "Run: %s.%s() " % (self.__class__.__name__, fun)
        val = {"ConfigDevice": self._cf.dp.name(),
               "WriterDevice": self._wr.dp.name(),
               "Door": 'doortestp09/testts/t1r228',
               "MntGrp": 'mg2'}

        wrong = []
        rs = self.openRecSelector()
        rs.configDevice = val["ConfigDevice"]
        rs.door = val["Door"]
        rs.mntGrp = val["MntGrp"]
        rs.writerDevice = val["WriterDevice"]
        self.assertEqual(rs.configDevice, val["ConfigDevice"])
        self.assertEqual(rs.door, val["Door"])

        db = PyTango.Database()
        db.put_device_property(self._ms.ms.keys()[0],
                               {'PoolNames': self._pool.dp.name()})
        pool = self._pool.dp
        pool.ExpChannelList = []
        self._ms.dps[self._ms.ms.keys()[0]].Init()

        self.assertEqual(rs.availableMntGrps(), [])
        self.myAssertRaise(Exception, rs.updateMntGrp)

        db = PyTango.Database()
        db.put_device_property(self._ms.ms.keys()[0],
                               {'PoolNames': self._pool.dp.name()})
        pool = self._pool.dp
        self._ms.dps[self._ms.ms.keys()[0]].Init()

        self.assertEqual(rs.availableMntGrps(), [])
        scalar_ctrl = 'ttestp09/testts/t1r228'
        spectrum_ctrl = 'ttestp09/testts/t2r228'
        image_ctrl = 'ttestp09/testts/t3r228'

        simp2 = TestServerSetUp.MultiTestServerSetUp(
            devices=['ttestp09/testts/t%02dr228' % i for i in range(1, 37)])
        try:
            simp2.setUp()
            for i in range(30):

                ctrls = [scalar_ctrl, spectrum_ctrl, image_ctrl, "__tango__"]
                expch = []
                pdss = []

                timers = {}
                ntms = self._rnd.randint(1, 5)
                tms = self._rnd.sample(set(
                    [ch for ch in self.smychsXX.keys()
                     if not ch.startswith("client")]), ntms)
                for tm in tms:
                    myct = ("ctrl_%s" % tm).replace("_", "/")
                    timers[myct] = tm
                    ctrls.append(myct)
                ltimers = timers.values()

                for ds, vl in self.smychsXX.items():
                    if vl:
                        exp = {}
                        exp["name"] = ds
                        exp["source"] = vl["source"]
                        myct = None
                        for ct, ch in timers.items():
                            if ds == ch:
                                myct = ct
                                break

                        if myct:
                            exp["controller"] = myct
                            exp["type"] = "CTExpChannel"
                        elif ds.startswith("image"):
                            exp["controller"] = image_ctrl
                            exp["type"] = "TwoDExpChannel"
                        elif ds.startswith("spectrum"):
                            exp["controller"] = spectrum_ctrl
                            exp["type"] = "OneDExpChannel"
                        else:
                            exp["controller"] = scalar_ctrl
                            exp["type"] = "CTExpChannel"
                        exp["interfaces"] = [exp["type"]]
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

                try:
                    cps = {}
                    acps = {}
                    dss = {}
                    lcp = self._rnd.randint(1, 40)
                    lds = self._rnd.randint(1, 40)

                    self._cf.dp.SetCommandVariable(
                        ["CPDICT", json.dumps(amycps)])
                    self._cf.dp.SetCommandVariable(
                        ["DSDICT", json.dumps(amydss)])
                    comps = set()

                    ncps = self._rnd.randint(1, len(amycps) - 1)
                    lcps = self._rnd.sample(set(amycps.keys()), ncps)
                    for cp in lcps:
                        if cp not in wrong:
                            cps[cp] = bool(self._rnd.randint(0, 1))
                            if cps[cp]:
                                comps.add(cp)

                    ancps = self._rnd.randint(1, len(amycps.keys()) - 1)
                    alcps = self._rnd.sample(set(amycps.keys()), ancps)
                    for cp in alcps:
                        if cp not in wrong:
                            acps[cp] = bool(self._rnd.randint(0, 1))
                            if acps[cp]:
                                comps.add(cp)

                    ndss = self._rnd.randint(1, len(amycps.keys()) - 1)
                    ldss = self._rnd.sample(set(amycps.keys()), ndss)
                    for ds in ldss:
                        if ds in amydss.keys():
                            if ds not in wrong:
                                dss[ds] = bool(self._rnd.randint(0, 1))

                    ndss = self._rnd.randint(1, len(amydss.keys()) - 1)
                    ldss = self._rnd.sample(set(amydss.keys()), ndss)
                    for ds in ldss:
                        if ds in amydss.keys():
                            if ds not in wrong:
                                dss[ds] = bool(self._rnd.randint(0, 1))

                    nadss = self._rnd.randint(1, len(amydss.keys()) - 1)
                    aadss = [ds for ds in self._rnd.sample(
                        set(amydss.keys()), nadss)]
                    nadss = self._rnd.randint(1, len(amydss.keys()) - 1)
                    indss = [ds for ds in self._rnd.sample(
                        set(amydss.keys()), nadss)]

                    for tm in ltimers:
                        dss[tm] = bool(self._rnd.randint(0, 1))

                    mncps = self._rnd.randint(1, len(amycps.keys()) - 1)
                    mcps = [cp for cp in self._rnd.sample(
                        set(amycps.keys()), mncps) if cp not in wrong]
                    oncps = self._rnd.randint(1, len(amycps.keys()) - 1)
                    ocps = [cp for cp in self._rnd.sample(
                        set(amycps.keys()), oncps) if cp not in wrong]
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
                    mp["PreselectingDataSources"] = json.dumps(aadss)
                    mp["OptionalComponents"] = json.dumps(ocps)
                    mp["DataSourcePreselection"] = json.dumps(indss)
                    mp["AppendEntry"] = bool(self._rnd.randint(0, 1))
                    mp["ComponentsFromMntGrp"] = bool(self._rnd.randint(0, 1))
                    mp["DynamicComponents"] = bool(self._rnd.randint(0, 1))
                    mp["DefaultDynamicLinks"] = bool(self._rnd.randint(0, 1))
                    mp["DefaultDynamicPath"] = self.getRandomName(20)
                    mp["TimeZone"] = self.getRandomName(20)

                    mp["ConfigVariables"] = json.dumps(dict(
                        (self.getRandomName(10),
                         self.getRandomName(15)) for _ in
                        range(self._rnd.randint(1, 40))))

                    paths = dict(
                        (self.getRandomName(10),
                         self.getRandomName(15)) for _ in
                        range(self._rnd.randint(1, 40)))
                    labels = dict(
                        (self.getRandomName(10),
                         self.getRandomName(15)) for _ in
                        range(self._rnd.randint(1, 40)))
                    links = dict(
                        (self.getRandomName(10),
                         bool(self._rnd.randint(0, 1))) for _ in
                        range(self._rnd.randint(1, 40)))
                    types = dict(
                        (self.getRandomName(10),
                         self.getRandomName(15)) for _ in
                        range(self._rnd.randint(1, 40)))
                    shapes = dict(
                        (self.getRandomName(10),
                         [self._rnd.randint(1, 40)
                          for _ in range(self._rnd.randint(0, 3))])
                        for _ in range(self._rnd.randint(1, 40)))
                    mp["ChannelProperties"] = json.dumps(
                        {
                            "label": labels,
                            "nexus_path": paths,
                            "link": links,
                            "data_type": types,
                            "shape": shapes
                        }
                    )

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
                        dss.keys(), dstype='CLIENT')[0]
                    for dsr in dsres.values():
                        records[str(dsr.record)] = '2345'

                    mp = json.loads(rs.profileConfiguration)
                    mp["Timer"] = json.dumps(ltimers)
                    mp["UserData"] = json.dumps(records)
                    rs.profileConfiguration = str(json.dumps(mp))
                    mp = json.loads(rs.profileConfiguration)

                    tmg = TestMGSetUp.TestMeasurementGroupSetUp(
                        name='mg2')
#                    dv = "/".join(ar["full_name"].split("/")[0:-1])
                    chds = [ds for ds in rs.selectedDataSources()
                            if not ds.startswith('client')]
                    chds1 = list(chds)
                    chds2 = [ds for ds in rs.componentDataSources()
                             if not ds.startswith('client')]
                    chds.extend(chds2)
                    bchds = list(chds)
                    chds.extend(ltimers)
                    tmpchds = sorted(list(set(chds)))
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
                        lheds = self._rnd.sample(set(chds), nhe)

                    lhecp = []
                    if comps:
                        nhe = self._rnd.randint(0, len(set(comps)) - 1)
                        lhecp = self._rnd.sample(set(comps), nhe)

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
                    self.assertEqual(json.loads(mp["Timer"]), ltimers)
                    self.assertEqual(mp["MntGrp"], "mg2")
                    self.dump(rs)
                    self.assertTrue(not rs.isMntGrpUpdated())
                    self.assertTrue(not rs.isMntGrpUpdated())

                    wwcp = rs.components
                    describer = Describer(self._cf.dp, True)
                    res = describer.components(wwcp, "STEP", "")

                    mdds = set()
                    for mdss in res[0].values():
                        if isinstance(mdss, dict):
                            for ds in mdss.keys():
                                adss[ds] = True

                    for tm in ltimers:
                        if tm in lhe2:
                            if tm in adss.keys():
                                adss[tm] = False

                    jpcnf = rs.updateMntGrp()
                    self.dump(rs)
                    self.assertTrue(rs.isMntGrpUpdated())
                    self.assertTrue(rs.isMntGrpUpdated())
                    pcnf = json.loads(jpcnf)
                    mgdp = PyTango.DeviceProxy(tmg.new_device_info_writer.name)
                    jcnf = rs.mntGrpConfiguration()
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
                    self.assertEqual(json.loads(mp["Timer"]), ltimers)
                    self.assertEqual(mp["MntGrp"], "mg2")
                    myctrls = {}
                    fgtm = "/".join(
                        self.smychsXX[str(ltimers[0])]['source'].split(
                            "/")[:-1])
                    for cl in ctrls:
                        tgc = {}
                        ttdv = None
                        idmax = 10000
                        for exp in expch:
                            ds = exp["name"]
#                            if cl == exp['controller']:
#                                print "DS", ds , ds in chds
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
                                        chn = {'ndim': 0,
                                               'index': i,
                                               'name': str(ds),
                                               'data_type': cnt['data_type'],
                                               'plot_type': (
                                                   cnt['plot_type']
                                                   if (ds not in lhe2
                                                       and ds in bchds)
                                                   else 0),
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
                                                   if (ds not in lhe2
                                                       and ds in bchds)
                                                   else []),
                                               'nexus_path': '',
                                               'normalization': 0,
                                               'source': cnt['source']}
                                        tgc[tdv] = chn
                                    except:
                                        raise
                        if tgc:
                            ltm = timers[cl] if cl in timers.keys() \
                                else ltimers[0]
                            fltm = "/".join(
                                self.smychsXX[str(ltm)]['source'].split(
                                    "/")[:-1])
                            myctrls[cl] = {
                                'units':
                                    {'0':
                                     {
                                         'channels': tgc,
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
                                chn = {'ndim': 0,
                                       'index': i,
                                       'name': str(ds),
                                       'data_type': cnt['data_type'],
                                       'plot_type': (cnt['plot_type']
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
                            except:
                                raise

                    if tgc:
                        myctrls['__tango__'] = {'units':
                                                {'0':
                                                 {'channels': tgc,
                                                  'monitor': fgtm,
                                                  'id': 0,
                                                  'timer': fgtm,
                                                  'trigger_type': 0}}}

                    smg = {"controllers": myctrls,
                           "monitor": "%s" % fgtm,
                           "description": "Measurement Group",
                           "timer": "%s" % fgtm,
                           "label": "mg2"}
#                    print "SMG", smg
                    self.myAssertDict(smg, pcnf)
                    self.myAssertDict(pcnf, cnf)
                    rs.mntGrp = "nxsmntgrp"
                    rs.profileConfiguration = str(json.dumps({}))
                    rs.configDevice = val["ConfigDevice"]
                    rs.door = val["Door"]
                    rs.mntGrp = "mg2"
                    rs.fetchProfile()
                    mp = json.loads(rs.profileConfiguration)

                    self.assertTrue(rs.isMntGrpUpdated())
                    self.assertTrue(rs.isMntGrpUpdated())

                    mp = json.loads(rs.profileConfiguration)
                    self.compareToDumpJSON(
                        rs, ["ComponentPreselection",
                             "ComponentSelection",
                             "DataSourceSelection",
                             "UnplottedComponents",
                             "PreselectingDataSources"])

                    self.myAssertDict(
                        json.loads(mp["ComponentPreselection"]), acps)
                    self.myAssertDict(
                        json.loads(mp["ComponentSelection"]), cps)
                    self.myAssertDict(
                        json.loads(mp["DataSourceSelection"]), adss)
                    self.assertEqual(
                        set(json.loads(mp["PreselectingDataSources"])),
                        set(aadss))
                    self.assertEqual(
                        set(json.loads(mp["UnplottedComponents"])),
                        set(lhe2))
                    self.assertEqual(json.loads(mp["OrderedChannels"]), pdss)
                    self.myAssertDict(json.loads(mp["UserData"]), records)
                    self.assertEqual(json.loads(mp["Timer"]), ltimers)
                    self.assertEqual(mp["MntGrp"], "mg2")
                finally:
                    try:
                        rs.deleteProfile("mg2")
                    except:
                        pass
                    try:
                        tmg.tearDown()
                    except:
                        pass
        finally:
            simp2.tearDown()

    def switchProfile(self, rs, flag):
        rs.switchProfile(flag)

    # test
    def test_switchProfile_importMntGrp(self):
        fun = sys._getframe().f_code.co_name
        print "Run: %s.%s() " % (self.__class__.__name__, fun)
        self.subtest_switchProfile_importMntGrp()

    # test
    def subtest_switchProfile_importMntGrp(self):
        val = {"ConfigDevice": self._cf.dp.name(),
               "WriterDevice": self._wr.dp.name(),
               "Door": 'doortestp09/testts/t1r228',
               "MntGrp": 'mg2'}

        self.maxDiff = None
        self.tearDown()
        try:
            for j in range(10):
                self.setUp()
                db = PyTango.Database()
                db.put_device_property(self._ms.ms.keys()[0],
                                       {'PoolNames': self._pool.dp.name()})

                wrong = []

                mgs = [
                    "mg1", "mg2", "mg3",
                    "mntgrp", "somegroup"
                ]
                rs = {}
                mp = {}
                msp = {}
                tmg = {}
                cps = {}
                acps = {}
                adss = {}
                aadss = {}
                pdss = {}
                lhe2 = {}
                records = {}
                ltimers = {}

                pool = self._pool.dp
                self._ms.dps[self._ms.ms.keys()[0]].Init()
                scalar_ctrl = 'ttestp09/testts/t1r228'
                spectrum_ctrl = 'ttestp09/testts/t2r228'
                image_ctrl = 'ttestp09/testts/t3r228'
                simp2 = TestServerSetUp.MultiTestServerSetUp(
                    devices=['ttestp09/testts/t%02dr228' %
                             i for i in range(1, 37)])

                try:
                    simp2.setUp()

                    # create mntgrps

                    for i, mg in enumerate(mgs):

                        rs[mg] = self.openRecSelector()
                        rs[mg].configDevice = val["ConfigDevice"]
                        rs[mg].door = val["Door"]
                        rs[mg].mntGrp = mg
                        self.assertEqual(rs[mg].configDevice,
                                         val["ConfigDevice"])
                        self.assertEqual(rs[mg].door, val["Door"])

                        self.assertEqual(
                            set(rs[mg].availableMntGrps()), set(mgs[:(i)]))
#                        self.myAssertRaise(Exception, rs[mg].updateMntGrp)

                        self.assertEqual(
                            set(rs[mg].availableMntGrps()), set(mgs[:(i)]))

                        ctrls = [scalar_ctrl, spectrum_ctrl, image_ctrl,
                                 "__tango__"]
                        expch = []
                        pdss[mg] = []

                        timers = {}
                        ntms = 1  # self._rnd.randint(1, 5)
                        tms = self._rnd.sample(set(
                            [ch for ch in self.smychsXX.keys()
                             if not ch.startswith("client")]), ntms)
                        for tm in tms:
                            myct = ("ctrl_%s" % tm).replace("_", "/")
                            timers[myct] = tm
                            ctrls.append(myct)
#                        print "TIMERSL", tms
#                        print "TIMERSD", timers
                        ltimers[mg] = timers.values()
#                        print "LTIMER", ltimers[mg]

                        for ds, vl in self.smychsXX.items():
                            if vl:
                                exp = {}
                                exp["name"] = ds
                                exp["source"] = vl["source"]
                                myct = None
                                for ct, ch in timers.items():
                                    if ds == ch:
                                        myct = ct
                                        break

                                if myct:
                                    exp["controller"] = myct
                                    exp["type"] = "CTExpChannel"
                                elif ds.startswith("image"):
                                    exp["controller"] = image_ctrl
                                    exp["type"] = "TwoDExpChannel"
                                elif ds.startswith("spectrum"):
                                    exp["controller"] = spectrum_ctrl
                                    exp["type"] = "OneDExpChannel"
                                else:
                                    exp["controller"] = scalar_ctrl
                                    exp["type"] = "CTExpChannel"
                                exp["interfaces"] = [exp["type"]]
                                expch.append(exp)
                                pdss[mg].append(ds)
                        pdss[mg] = sorted(pdss[mg])
                        self._rnd.shuffle(pdss[mg])

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

                        cps[mg] = {}
                        acps[mg] = {}
                        dss = {}
                        lcp = self._rnd.randint(1, 40)
                        lds = self._rnd.randint(1, 40)

                        self._cf.dp.SetCommandVariable(
                            ["CPDICT", json.dumps(amycps)])
                        self._cf.dp.SetCommandVariable(
                            ["DSDICT", json.dumps(amydss)])
                        comps = set()

                        ncps = self._rnd.randint(1, len(amycps) - 1)
                        lcps = self._rnd.sample(set(amycps.keys()), ncps)
                        for cp in lcps:
                            if cp not in wrong:
                                cps[mg][cp] = bool(self._rnd.randint(0, 1))
                                if cps[mg][cp]:
                                    comps.add(cp)

                        ancps = self._rnd.randint(1, len(amycps.keys()) - 1)
                        alcps = self._rnd.sample(set(amycps.keys()), ancps)
                        for cp in alcps:
                            if cp not in wrong:
                                acps[mg][cp] = bool(self._rnd.randint(0, 1))
                                if acps[mg][cp]:
                                    comps.add(cp)

                        ndss = self._rnd.randint(1, len(amycps.keys()) - 1)
                        ldss = self._rnd.sample(set(amycps.keys()), ndss)
                        for ds in ldss:
                            if ds in amydss.keys():
                                if ds not in wrong:
                                    dss[ds] = bool(self._rnd.randint(0, 1))

                        ndss = self._rnd.randint(1, len(amydss.keys()) - 1)
                        ldss = self._rnd.sample(set(amydss.keys()), ndss)
                        for ds in ldss:
                            if ds in amydss.keys():
                                if ds not in wrong:
                                    dss[ds] = bool(self._rnd.randint(0, 1))

                        nadss = self._rnd.randint(1, len(amydss.keys()) - 1)
                        aadss[mg] = [ds for ds in self._rnd.sample(
                            set(amydss.keys()), nadss)]
                        nadss = self._rnd.randint(1, len(amydss.keys()) - 1)
                        indss = [ds for ds in self._rnd.sample(
                            set(amydss.keys()), nadss)]

                        aindss = {}
                        for cp in indss:
                            if cp not in wrong:
                                aindss[cp] = bool(self._rnd.randint(0, 1))

                        for tm in ltimers[mg]:
                            dss[tm] = bool(self._rnd.randint(0, 1))

                        mncps = self._rnd.randint(1, len(amycps.keys()) - 1)
                        mcps = [cp for cp in self._rnd.sample(
                                set(amycps.keys()), mncps) if cp not in wrong]
                        oncps = self._rnd.randint(1, len(amycps.keys()) - 1)
                        ocps = [cp for cp in self._rnd.sample(
                                set(amycps.keys()), oncps) if cp not in wrong]
                        for cp in mcps:
                            comps.add(cp)

                        adss[mg] = dict(dss)
                        for ch in expch:
                            if ch["name"] not in adss[mg].keys():
                                adss[mg][ch["name"]] = False
                        mp[mg] = json.loads(rs[mg].profileConfiguration)
                        mp[mg]["ComponentSelection"] = json.dumps(cps[mg])
                        mp[mg]["ComponentPreselection"] = json.dumps(
                            acps[mg])
                        mp[mg]["DataSourceSelection"] = json.dumps(dss)
                        mp[mg]["PreselectingDataSources"] = \
                            json.dumps(aadss[mg])
                        mp[mg]["OptionalComponents"] = json.dumps(ocps)
                        mp[mg]["DataSourcePreselection"] = json.dumps(aindss)
                        mp[mg]["AppendEntry"] = bool(self._rnd.randint(0, 1))
                        mp[mg]["ComponentsFromMntGrp"] = bool(
                            self._rnd.randint(0, 1))
                        mp[mg]["DynamicComponents"] = bool(
                            self._rnd.randint(0, 1))
                        mp[mg]["DefaultDynamicLinks"] = \
                            bool(self._rnd.randint(0, 1))
                        mp[mg]["DefaultDynamicPath"] = self.getRandomName(20)
                        mp[mg]["TimeZone"] = self.getRandomName(20)

                        mp[mg]["ConfigVariables"] = json.dumps(dict(
                            (self.getRandomName(10),
                             self.getRandomName(15)) for _ in
                            range(self._rnd.randint(1, 40))))
                        paths = dict(
                            (self.getRandomName(10),
                             self.getRandomName(15)) for _ in
                            range(self._rnd.randint(1, 40)))
                        labels = dict(
                            (self.getRandomName(10),
                             self.getRandomName(15)) for _ in
                            range(self._rnd.randint(1, 40)))
                        links = dict(
                            (self.getRandomName(10),
                             bool(self._rnd.randint(0, 1))) for _ in
                            range(self._rnd.randint(1, 40)))
                        types = dict(
                            (self.getRandomName(10),
                             self.getRandomName(15)) for _ in
                            range(self._rnd.randint(1, 40)))
                        shapes = dict(
                            (self.getRandomName(10),
                             [self._rnd.randint(1, 40)
                              for _ in range(self._rnd.randint(0, 3))])
                            for _ in range(self._rnd.randint(1, 40)))

                        mp[mg]["ChannelProperties"] = json.dumps(
                            {
                                "label": labels,
                                "nexus_path": paths,
                                "link": links,
                                "data_type": types,
                                "shape": shapes
                            }
                        )

                        rs[mg].profileConfiguration = str(json.dumps(mp[mg]))
                        mp[mg] = json.loads(rs[mg].profileConfiguration)
                        self._cf.dp.SetCommandVariable(["MCPLIST",
                                                        json.dumps(mcps)])

                        records[mg] = {}
                        describer = Describer(self._cf.dp, True)
                        cpres = describer.components(dstype='CLIENT')
                        for grp in cpres:
                            for idss in grp.values():
                                for idsrs in idss.values():
                                    for idsr in idsrs:
                                        records[mg][str(idsr[2])] = "1234"
                        dsres = describer.dataSources(
                            dss.keys(), dstype='CLIENT')[0]
                        for dsr in dsres.values():
                            records[mg][str(dsr.record)] = '2345'

                        mp[mg] = json.loads(rs[mg].profileConfiguration)
                        mp[mg]["Timer"] = json.dumps(ltimers[mg])
                        mp[mg]["UserData"] = json.dumps(records[mg])
                        rs[mg].profileConfiguration = str(json.dumps(mp[mg]))
                        mp[mg] = json.loads(rs[mg].profileConfiguration)

                        tmg[mg] = TestMGSetUp.TestMeasurementGroupSetUp(
                            name=mg)
        #                    dv = "/".join(ar["full_name"].split("/")[0:-1])
                        chds = [ds for ds in rs[mg].selectedDataSources()
                                if not ds.startswith('client')]
                        chds1 = list(chds)
                        chds2 = [ds for ds in rs[mg].componentDataSources()
                                 if not ds.startswith('client')]
                        chds.extend(chds2)
                        bchds = list(chds)
                        chds.extend(ltimers[mg])
                        tmpchds = sorted(list(set(chds)))
                        chds = []
                        for ds in pdss[mg]:
                            if ds in tmpchds:
                                chds.append(ds)
                        for ds in tmpchds:
                            if ds not in pdss[mg]:
                                chds.append(ds)

                        lheds = []
                        if chds:
                            nhe = self._rnd.randint(0, len(set(chds)) - 1)
                            lheds = self._rnd.sample(set(chds), nhe)

                        lhecp = []
                        if comps:
                            nhe = self._rnd.randint(0, len(set(comps)) - 1)
                            lhecp = self._rnd.sample(set(comps), nhe)

                        lhe = lheds + lhecp

                        mp[mg] = json.loads(rs[mg].profileConfiguration)
                        mp[mg]["UnplottedComponents"] = json.dumps(lhe)
                        mp[mg]["OrderedChannels"] = json.dumps(pdss[mg])
                        rs[mg].profileConfiguration = str(json.dumps(mp[mg]))
                        mp[mg] = json.loads(rs[mg].profileConfiguration)

                        lhe2[mg] = []
                        for el in lhe:
                            found = False
                            for cp in comps:
                                if el in amycpsstep[cp]:
                                    if cp not in lhecp:
                                        found = True
                            if not found:
                                lhe2[mg].append(el)

                        self.myAssertDict(
                            json.loads(mp[mg]["ComponentPreselection"]),
                            acps[mg])
                        self.myAssertDict(
                            json.loads(mp[mg]["ComponentSelection"]), cps[mg])
                        self.myAssertDict(
                            json.loads(mp[mg]["DataSourceSelection"]),
                            adss[mg])
                        self.assertEqual(
                            set(json.loads(mp[mg]["UnplottedComponents"])),
                            set(lhe))
                        self.assertEqual(
                            json.loads(mp[mg]["OrderedChannels"]), pdss[mg])
                        self.myAssertDict(
                            json.loads(mp[mg]["UserData"]), records[mg])
                        self.assertEqual(
                            json.loads(mp[mg]["Timer"]), ltimers[mg])
                        self.assertEqual(mp[mg]["MntGrp"], mg)
                        self.dump(rs[mg], name=mg)
                        self.assertTrue(not rs[mg].isMntGrpUpdated())
                        self.assertTrue(not rs[mg].isMntGrpUpdated())

                        wwcp = rs[mg].components
                        describer = Describer(self._cf.dp, True)
                        res = describer.components(wwcp, "STEP", "")

                        mdds = set()
                        for mdss in res[0].values():
                            if isinstance(mdss, dict):
                                for ds in mdss.keys():
                                    adss[mg][ds] = True

                        for tm in ltimers[mg]:
                            if tm in lhe2[mg]:
                                if tm in adss[mg].keys():
#                                    print "DES", tm
                                    adss[mg][tm] = False

                        jpcnf = rs[mg].updateMntGrp()
                        self.dump(rs[mg], name=mg)
                        self.assertTrue(rs[mg].isMntGrpUpdated())
                        self.assertTrue(rs[mg].isMntGrpUpdated())
                        pcnf = json.loads(jpcnf)
                        mgdp = PyTango.DeviceProxy(
                            tmg[mg].new_device_info_writer.name)
                        jcnf = rs[mg].mntGrpConfiguration()
                        cnf = json.loads(jcnf)
                        mp[mg] = json.loads(rs[mg].profileConfiguration)
                        self.myAssertDict(
                            json.loads(mp[mg]["ComponentPreselection"]),
                            acps[mg])
                        self.myAssertDict(
                            json.loads(mp[mg]["ComponentSelection"]), cps[mg])
                        self.myAssertDict(
                            json.loads(
                                mp[mg]["DataSourceSelection"]), adss[mg])
                        self.assertEqual(
                            set(json.loads(mp[mg]["UnplottedComponents"])),
                            set(lhe2[mg]))
                        self.assertEqual(
                            json.loads(mp[mg]["OrderedChannels"]), pdss[mg])
                        self.myAssertDict(
                            json.loads(mp[mg]["UserData"]), records[mg])
                        self.assertEqual(
                            json.loads(mp[mg]["Timer"]), ltimers[mg])
                        self.assertEqual(mp[mg]["MntGrp"], mg)
                        myctrls = {}
                        fgtm = "/".join(
                            self.smychsXX[str(ltimers[mg][0])]['source'].split(
                                "/")[:-1])
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
                                        try:
                                            tdv = "/".join(
                                                cnt['source'].split("/")[:-1])
                                            if i < idmax:
                                                idmax = i
                                                ttdv = tdv
                                            chn = {'ndim': 0,
                                                   'index': i,
                                                   'name': str(ds),
                                                   'data_type':
                                                       cnt['data_type'],
                                                   'plot_type': (
                                                       cnt['plot_type']
                                                       if (ds not in lhe2[mg]
                                                           and ds in bchds)
                                                       else 0),
                                                   'data_units':
                                                       cnt['data_units'],
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
                                                       if (ds not in lhe2[mg]
                                                           and ds in bchds)
                                                       else []),
                                                   'nexus_path': '',
                                                   'normalization': 0,
                                                   'source': cnt['source']}
                                            tgc[tdv] = chn
                                        except:
                                            raise
                            if tgc:
                                ltm = timers[cl] if cl in timers.keys() \
                                    else ltimers[mg][0]
                                fltm = "/".join(
                                    self.smychsXX[str(ltm)]['source'].split(
                                        "/")[:-1])
                                myctrls[cl] = {
                                    'units':
                                        {'0':
                                         {
                                             'channels': tgc,
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
                                    chn = {'ndim': 0,
                                           'index': i,
                                           'name': str(ds),
                                           'data_type': cnt['data_type'],
                                           'plot_type': (
                                               cnt['plot_type']
                                               if ds not in lhe2[mg] else 0),
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
                                               if ds not in lhe2[mg] else []),
                                           'nexus_path': '',
                                           'normalization': 0,
                                           'source': cnt['source']}
                                    tgc[chn["full_name"]] = chn
                                except:
                                    raise

                        if tgc:
                            myctrls['__tango__'] = {
                                'units':
                                    {'0':
                                     {'channels': tgc,
                                      'monitor': fgtm,
                                      'id': 0,
                                      'timer': fgtm,
                                      'trigger_type': 0}}}

                        smg = {"controllers": myctrls,
                               "monitor": "%s" % fgtm,
                               "description": "Measurement Group",
                               "timer": "%s" % fgtm,
                               "label": mg}
        #                    print "SMG", smg
                        self.myAssertDict(smg, pcnf)
                        self.myAssertDict(pcnf, cnf)
                        rs[mg].mntGrp = "nxsmntgrp"
                        rs[mg].profileConfiguration = str(json.dumps({}))
                        rs[mg].configDevice = val["ConfigDevice"]
                        rs[mg].door = val["Door"]
#                        print "MG", mg
                        rs[mg].mntGrp = mg
                        rs[mg].fetchProfile()
                        mp[mg] = json.loads(rs[mg].profileConfiguration)
#                        self.myAssertRaise(Exception, rs[mg].isMntGrpUpdated)
#                       rs[mg].fetchProfile()
#                        mp[mg] = json.loads(rs[mg].profileConfiguration)

                        self.assertTrue(rs[mg].isMntGrpUpdated())
                        self.assertTrue(rs[mg].isMntGrpUpdated())

                        self.compareToDumpJSON(
                            rs[mg],
                            ["DataSourceSelection",
                             "UnplottedComponents",
                             "PreselectingDataSources",
                             "UnplottedComponents"],
                            name=mg)
                        mp[mg] = json.loads(rs[mg].profileConfiguration)
                        self.myAssertDict(
                            json.loads(
                                mp[mg]["DataSourceSelection"]), adss[mg])
                        self.assertEqual(
                            set(json.loads(mp[mg]["PreselectingDataSources"])),
                            set(aadss[mg]))
#                        print "PDS1", set(aadss[mg])
                        self.assertEqual(
                            set(json.loads(mp[mg]["UnplottedComponents"])),
                            set(lhe2[mg]))
                        self.assertEqual(
                            json.loads(mp[mg]["OrderedChannels"]), pdss[mg])
                        self.myAssertDict(
                            json.loads(mp[mg]["UserData"]), records[mg])
                        self.assertEqual(
                            json.loads(mp[mg]["Timer"]), ltimers[mg])
                        self.assertEqual(mp[mg]["MntGrp"], mg)

                    # check profile commands
                    mg1, mg2, mg3, mg4 = tuple(self._rnd.sample(mgs, 4))
#                    print "MGS", mg1, mg2, mg3, mg4

                    self.compareToDumpJSON(
                        rs[mg1],
                        ["DataSourceSelection",
                         "UnplottedComponents",
                         "PreselectingDataSources"],
                        name=mg1)
                    self.compareToDumpJSON(
                        rs[mg2],
                        ["DataSourceSelection",
                         "UnplottedComponents",
                         "PreselectingDataSources"],
                        name=mg2)
                    self.compareToDumpJSON(
                        rs[mg3],
                        ["DataSourceSelection",
                         "UnplottedComponents",
                         "PreselectingDataSources"],
                        name=mg3)
                    self.compareToDumpJSON(
                        rs[mg4],
                        ["DataSourceSelection",
                         "UnplottedComponents",
                         "PreselectingDataSources"],
                        name=mg4)

                    lrs = self.openRecSelector()
                    lrs.configDevice = val["ConfigDevice"]
                    lrs.door = val["Door"]
                    lrs.mntGrp = mg1
                    self.assertEqual(lrs.configDevice, val["ConfigDevice"])

                    self.assertEqual(lrs.door, val["Door"])
                    lmp = json.loads(lrs.profileConfiguration)

#                    self.myAssertRaise(Exception, lrs.isMntGrpUpdated)

                    self.switchProfile(lrs, False)
                    lmp = json.loads(lrs.profileConfiguration)

                    self.compareToDumpJSON(
                        lrs, [
                            "DataSourceSelection",
                            "UnplottedComponents",
                            "PreselectingDataSources",
                            "Timer"
                        ],
                        name=mg1)
                    tmpcf = json.loads(rs[mg1].mntGrpConfiguration())
                    ltmpcf = json.loads(lrs.mntGrpConfiguration())
                    self.myAssertDict(tmpcf, ltmpcf)

                    self.assertEqual(
                        set(json.loads(lmp["PreselectingDataSources"])),
                        set(aadss[mg1]))
                    self.myAssertDict(
                        json.loads(lmp["DataSourceSelection"]), adss[mg1])
                    self.assertEqual(
                        json.loads(lmp["OrderedChannels"]), pdss[mg1])
                    self.myAssertDict(
                        json.loads(lmp["UserData"]), records[mg1])
                    self.assertEqual(
                        json.loads(lmp["Timer"])[0], ltimers[mg1][0])
                    self.assertEqual(
                        set(json.loads(lmp["Timer"])), set(ltimers[mg1]))
                    self.assertEqual(lmp["MntGrp"], mg1)

#                    print "MGS", mg1, mg2, mg3, mg4

                    # import mntgrp another defined by selector MntGrp
                    lrs.mntGrp = mg2

                    self.assertTrue(not lrs.isMntGrpUpdated())
                    self.assertTrue(not lrs.isMntGrpUpdated())

                    lrs.importMntGrp()
                    lmp = json.loads(lrs.profileConfiguration)
                    self.assertTrue(not lrs.isMntGrpUpdated())
                    self.assertTrue(not lrs.isMntGrpUpdated())

                    tmpcf1 = json.loads(rs[mg1].mntGrpConfiguration())
                    tmpcf2 = json.loads(rs[mg2].mntGrpConfiguration())
                    ltmpcf = json.loads(lrs.mntGrpConfiguration())
#                    self.myAssertDict(tmpcf1, ltmpcf)
                    self.myAssertDict(tmpcf2, ltmpcf)
#                    print "RSmg2",
                    self.compareToDumpJSON(
                        rs[mg2],
                        ["DataSourceSelection",
                         "UnplottedComponents",
                         "PreselectingDataSources"],
                        name=mg2)
                    self.compareToDumpJSON(
                        lrs,
                        ["DataSourceSelection",
                         "UnplottedComponents",
                         "PreselectingDataSources",
                         "Timer",
                         "MntGrp"],
                        name=mg1)

                    tmpcf = json.loads(rs[mg2].mntGrpConfiguration())
                    ltmpcf = json.loads(lrs.mntGrpConfiguration())
                    self.myAssertDict(tmpcf, ltmpcf)

                    self.assertEqual(
                        set(json.loads(lmp["PreselectingDataSources"])),
                        set(aadss[mg1]))
                    self.assertEqual(
                        json.loads(lmp["OrderedChannels"]), pdss[mg1])
                    self.myAssertDict(
                        json.loads(lmp["UserData"]), records[mg1])

                    self.assertEqual(
                        json.loads(lmp["Timer"])[0], ltimers[mg2][0])
                    self.assertEqual(
                        set(json.loads(lmp["Timer"])), set(ltimers[mg2]))
                    self.assertEqual(lmp["MntGrp"], mg2)

                    self.myAssertDict(
                        json.loads(mp[mg1]["DataSourceSelection"]),
                        adss[mg1])
                    self.myAssertDict(
                        json.loads(mp[mg2]["DataSourceSelection"]),
                        adss[mg2])

                    self.assertEqual(
                        set(json.loads(mp[mg1]["UnplottedComponents"])),
                        set(lhe2[mg1]))
                    self.assertEqual(
                        set(json.loads(mp[mg2]["UnplottedComponents"])),
                        set(lhe2[mg2]))

                    compds = rs[mg1].componentDataSources()

                    tangods = [ds for ds in
                               set(self.smychs.keys())
                               | set(self.smychsXX.keys())
                               if (not ds.startswith("client")
                                   and ds not in compds)]

                    ladss = {}
                    llhe = set()
                    for ds, vl in adss[mg1].items():
                        if ds in tangods:
                            ladss[ds] = False
                        else:
                            ladss[ds] = vl
                    for nd in lhe2[mg1]:
                        if nd not in self.smychsXX.keys():
                            if nd not in tangods:
                                llhe.add(nd)

                    for ds, vl in adss[mg2].items():
                        if vl:
                            if ds in self.smychs.keys() and \
                                    self.smychs[ds]:
                                ladss[ds] = vl
                                if ds in lhe2[mg2]:
                                    llhe.add(ds)
                                elif ds in llhe:
                                    llhe.remove(ds)
                            elif ds in self.smychsXX.keys() and \
                                    self.smychsXX[ds]:
                                ladss[ds] = vl
                                if ds in lhe2[mg2]:
                                    llhe.add(ds)
                                elif ds in llhe:
                                    llhe.remove(ds)
                            if ds not in self.smychs.keys() and \
                                    ds not in self.smychsXX.keys():
                                ladss[ds] = vl
                                if ds in lhe2[mg2]:
                                    llhe.add(ds)
                                elif ds in llhe:
                                    llhe.remove(ds)
                        elif ds in adss[mg1].keys():
                            if ds in self.smychsXX.keys() \
                                    and self.smychsXX[ds]:
                                ladss[ds] = vl
                                if ds in lhe2[mg2]:
                                    llhe.add(ds)
                                elif ds in llhe:
                                    llhe.remove(ds)
                            else:
                                if ds not in tangods:
                                    ladss[ds] = adss[mg1][ds]
                                else:
                                    ladss[ds] = False

                    for tm in json.loads(mp[mg2]["Timer"]):
                        if tm in ladss:
                            if tm in llhe:
                                ladss[tm] = False
                                llhe.remove(tm)
                    for tm in json.loads(mp[mg1]["Timer"]):
                        if tm in ladss:
                            if tm in json.loads(
                                    mp[mg2]["UnplottedComponents"]):
                                ladss[tm] = False
                                if tm not in json.loads(mp[mg2]["Timer"]):
                                    if tm in llhe:
                                        llhe.remove(tm)

#                    print "T1", json.loads(mp[mg1]["Timer"])
#                    print "T2", json.loads(mp[mg2]["Timer"])
#                    print "LT", json.loads(lmp["Timer"])
                    self.myAssertDict(
                        json.loads(lmp["DataSourceSelection"]), ladss)

                    self.assertEqual(
                        set(json.loads(lmp["UnplottedComponents"])),
                        set(llhe))

                    # import mntgrp mg2 (with content mg1)
                    # after change in mntgrp device

                    lrs.mntGrp = mg2
                    tmpcf = json.loads(rs[mg1].mntGrpConfiguration())
                    tmpcf2 = json.loads(rs[mg2].mntGrpConfiguration())
                    ltmpcf = json.loads(lrs.mntGrpConfiguration())
                    self.assertEqual(ltmpcf, tmpcf2)
                    tmpcf['label'] = mg2
                    mgdp = PyTango.DeviceProxy(
                        tmg[mg2].new_device_info_writer.name)
#                    print "name", tmg[mg2].new_device_info_writer.name
                    mgdp.Configuration = json.dumps(tmpcf)
                    self.assertTrue(not lrs.isMntGrpUpdated())
                    self.assertTrue(not lrs.isMntGrpUpdated())

                    tmpcf1 = json.loads(rs[mg1].mntGrpConfiguration())
                    tmpcf2 = json.loads(rs[mg2].mntGrpConfiguration())
                    ltmpcf = json.loads(lrs.mntGrpConfiguration())
#                    self.myAssertDict(tmpcf1, ltmpcf)
                    self.myAssertDict(tmpcf2, ltmpcf)

                    lrs.importMntGrp()
                    # ???

                    ltmpcf2 = json.loads(lrs.mntGrpConfiguration())
                    if not Utils.compareDict(ltmpcf2, ltmpcf):
                        self.assertTrue(not lrs.isMntGrpUpdated())
                        self.assertTrue(not lrs.isMntGrpUpdated())

                    tmpcf1 = json.loads(rs[mg1].mntGrpConfiguration())
                    tmpcf2 = json.loads(rs[mg2].mntGrpConfiguration())
                    ltmpcf = json.loads(lrs.mntGrpConfiguration())
#                    self.myAssertDict(tmpcf1, ltmpcf)
                    self.myAssertDict(tmpcf2, ltmpcf)

                    self.compareToDumpJSON(
                        lrs,
                        ["ComponentPreselection",
                         "ComponentSelection",
                         "DataSourceSelection",
                         "UnplottedComponents",
                         "PreselectingDataSources",
                         "Timer",
                         "MntGrp"],
                        name=mg1)

                    self.compareToDump(
                        rs[mg2],
                        ["ComponentPreselection",
                         "ComponentSelection",
                         "DataSourceSelection",
                         "UnplottedComponents",
                         "PreselectingDataSources",
                         "Timer"],
                        name=mg2)

                    self.myAssertDict(
                        json.loads(mp[mg2]["ComponentPreselection"]),
                        acps[mg2])
                    self.myAssertDict(
                        json.loads(mp[mg2]["ComponentSelection"]),
                        cps[mg2])
                    self.myAssertDict(
                        json.loads(mp[mg2]["DataSourceSelection"]), adss[mg2])
                    self.assertEqual(
                        set(json.loads(mp[mg2]["PreselectingDataSources"])),
                        set(aadss[mg2]))
                    self.assertEqual(
                        set(json.loads(mp[mg2]["UnplottedComponents"])),
                        set(lhe2[mg2]))
                    self.assertEqual(
                        json.loads(mp[mg2]["OrderedChannels"]), pdss[mg2])
                    self.myAssertDict(json.loads(mp[mg2]["UserData"]),
                                      records[mg2])
                    self.assertEqual(
                        json.loads(mp[mg2]["Timer"]), ltimers[mg2])
                    self.assertEqual(mp[mg2]["MntGrp"], mg2)

                    # switch to active profile mg3
                    lrs.mntGrp = mg2
                    MSUtils.setEnv('ActiveMntGrp', mg3, self._ms.ms.keys()[0])

                    tmpcf1 = json.loads(rs[mg1].mntGrpConfiguration())
                    tmpcf2 = json.loads(rs[mg2].mntGrpConfiguration())
                    tmpcf3 = json.loads(rs[mg3].mntGrpConfiguration())
                    ltmpcf = json.loads(lrs.mntGrpConfiguration())
#                    self.myAssertDict(tmpcf1, ltmpcf)
                    self.myAssertDict(tmpcf2, ltmpcf)
#                    self.myAssertDict(tmpcf3, ltmpcf)

                    lrs.switchProfile()

                    tmpcf1 = json.loads(rs[mg1].mntGrpConfiguration())
                    tmpcf2 = json.loads(rs[mg2].mntGrpConfiguration())
                    tmpcf3 = json.loads(rs[mg3].mntGrpConfiguration())
                    ltmpcf = json.loads(lrs.mntGrpConfiguration())
                    self.myAssertDict(tmpcf3, ltmpcf)
#                    self.myAssertDict(tmpcf1, ltmpcf)
#                    self.myAssertDict(tmpcf2, ltmpcf)

                    self.compareToDumpJSON(
                        lrs,
                        [
                            "DataSourceSelection",
                            "UnplottedComponents",
                            "PreselectingDataSources",
                            "Timer"],
                        name=mg3)
                    lmp = json.loads(lrs.profileConfiguration)
                    self.myAssertDict(json.loads(lmp["DataSourceSelection"]),
                                      adss[mg3])
                    self.assertEqual(
                        set(json.loads(lmp["PreselectingDataSources"])),
                        set(aadss[mg3]))

                    mylhe = set(lhe2[mg3])
                    for tm in json.loads(mp[mg3]["Timer"]):
                        if tm in adss[mg3].keys():
                            if not adss[mg3][tm]:
                                if tm in mylhe:
                                    mylhe.remove(tm)
                    lmp = json.loads(lrs.profileConfiguration)

                    self.assertEqual(
                        set(json.loads(lmp["UnplottedComponents"])),
                        mylhe)
                    self.assertEqual(json.loads(lmp["OrderedChannels"]),
                                     pdss[mg3])
                    self.myAssertDict(json.loads(lmp["UserData"]),
                                      records[mg3])
                    self.assertEqual(json.loads(lmp["Timer"])[0],
                                     ltimers[mg3][0])
                    self.assertEqual(set(json.loads(lmp["Timer"])),
                                     set(ltimers[mg3]))
                    self.assertEqual(lmp["MntGrp"], mg3)

                    # switch to nonexisting active profile

#                    self.assertTrue(lrs.isMntGrpUpdated())
#                    self.assertTrue(lrs.isMntGrpUpdated())
                    wmg = "wrong_mg"
                    lrs.mntGrp = mg3
                    MSUtils.setEnv('ActiveMntGrp', wmg, self._ms.ms.keys()[0])
                    lrs.switchProfile()
                    self.assertEqual(
                        wmg,
                        MSUtils.getEnv('ActiveMntGrp', self._ms.ms.keys()[0]))

                    self.compareToDumpJSON(
                        lrs,
                        [
                            "DataSourceSelection",
                            "UnplottedComponents",
                            "PreselectingDataSources",
                            "Timer",
                            "MntGrp"],
                        name=mg3)
                    lmp = json.loads(lrs.profileConfiguration)
                    mydsg = dict(json.loads(lmp["DataSourceSelection"]))
                    for ds in self.smychsXX.keys():
                        if ds in expch:
                            mydsg[ds] = False
                    cpdss = rs[mg3].componentDataSources()
                    mylhe2 = set(mylhe)
                    for ds in list(mylhe2):
                        if ds in self.smychsXX.keys() or (
                                ds in self.smychs.keys() and ds not in cpdss):
                            mylhe2.remove(ds)

                    self.myAssertDict(json.loads(lmp["DataSourceSelection"]),
                                      mydsg)
                    self.assertEqual(
                        set(json.loads(lmp["PreselectingDataSources"])),
                        set(aadss[mg3]))
                    self.assertEqual(
                        set(json.loads(lmp["UnplottedComponents"])),
                        mylhe2)
                    self.assertEqual(json.loads(lmp["OrderedChannels"]),
                                     pdss[mg3])
                    self.myAssertDict(json.loads(lmp["UserData"]),
                                      records[mg3])
                    self.assertEqual(json.loads(lmp["Timer"])[0],
                                     ltimers[mg3][0])
                    self.assertEqual(set(json.loads(lmp["Timer"])),
                                     set(ltimers[mg3]))
                    self.assertEqual(lmp["MntGrp"], wmg)

                    # switch to active profile mg3
                    lrs.mntGrp = mg2
                    self.assertTrue(not lrs.isMntGrpUpdated())
                    self.assertTrue(not lrs.isMntGrpUpdated())
                    MSUtils.setEnv('ActiveMntGrp', mg3, self._ms.ms.keys()[0])

                    tmpcf1 = json.loads(rs[mg1].mntGrpConfiguration())
                    tmpcf2 = json.loads(rs[mg2].mntGrpConfiguration())
                    tmpcf3 = json.loads(rs[mg3].mntGrpConfiguration())
                    ltmpcf = json.loads(lrs.mntGrpConfiguration())
#                    self.myAssertDict(tmpcf1, ltmpcf)
                    self.myAssertDict(tmpcf2, ltmpcf)
#                    self.myAssertDict(tmpcf3, ltmpcf)

                    self.switchProfile(lrs, True)

                    tmpcf1 = json.loads(rs[mg1].mntGrpConfiguration())
                    tmpcf2 = json.loads(rs[mg2].mntGrpConfiguration())
                    tmpcf3 = json.loads(rs[mg3].mntGrpConfiguration())
                    ltmpcf = json.loads(lrs.mntGrpConfiguration())
                    self.myAssertDict(tmpcf3, ltmpcf)
#                    self.myAssertDict(tmpcf1, ltmpcf)
#                    self.myAssertDict(tmpcf2, ltmpcf)

                    lmp = json.loads(lrs.profileConfiguration)
                    self.compareToDumpJSON(
                        lrs,
                        [
                            "DataSourceSelection",
                            "UnplottedComponents",
                            "PreselectingDataSources",
                            "Timer"],
                        name=mg3)
                    self.myAssertDict(json.loads(lmp["DataSourceSelection"]),
                                      adss[mg3])
                    self.assertEqual(
                        set(json.loads(lmp["PreselectingDataSources"])),
                        set(aadss[mg3]))

                    self.assertEqual(
                        set(json.loads(lmp["UnplottedComponents"])),
                        mylhe)
                    self.assertEqual(json.loads(lmp["OrderedChannels"]),
                                     pdss[mg3])
                    self.myAssertDict(json.loads(lmp["UserData"]),
                                      records[mg3])
                    self.assertEqual(json.loads(lmp["Timer"])[0],
                                     ltimers[mg3][0])
                    self.assertEqual(set(json.loads(lmp["Timer"])),
                                     set(ltimers[mg3]))
                    self.assertEqual(lmp["MntGrp"], mg3)

                    # try switch to unnamed active profile
                    # and then to selector mg3

#                    self.assertTrue(lrs.isMntGrpUpdated())
#                    self.assertTrue(lrs.isMntGrpUpdated())
                    wmg = ""
                    lrs.mntGrp = mg3
                    MSUtils.setEnv('ActiveMntGrp', wmg, self._ms.ms.keys()[0])
                    lrs.switchProfile()
                    self.assertEqual(
                        wmg,
                        MSUtils.getEnv('ActiveMntGrp', self._ms.ms.keys()[0]))

                    tmpcf1 = json.loads(rs[mg1].mntGrpConfiguration())
                    tmpcf2 = json.loads(rs[mg2].mntGrpConfiguration())
                    tmpcf3 = json.loads(rs[mg3].mntGrpConfiguration())
                    ltmpcf = json.loads(lrs.mntGrpConfiguration())
                    self.myAssertDict(tmpcf3, ltmpcf)
#                    self.myAssertDict(tmpcf1, ltmpcf)
#                    self.myAssertDict(tmpcf2, ltmpcf)

                    self.compareToDumpJSON(
                        lrs,
                        [
                            "DataSourceSelection",
                            "UnplottedComponents",
                            "PreselectingDataSources",
                            "Timer"],
                        name=mg3)
                    lmp = json.loads(lrs.profileConfiguration)
                    self.myAssertDict(json.loads(lmp["DataSourceSelection"]),
                                      adss[mg3])
                    self.assertEqual(
                        set(json.loads(lmp["PreselectingDataSources"])),
                        set(aadss[mg3]))

                    self.assertEqual(
                        set(json.loads(lmp["UnplottedComponents"])),
                        mylhe)
                    self.assertEqual(json.loads(lmp["OrderedChannels"]),
                                     pdss[mg3])
                    self.myAssertDict(json.loads(lmp["UserData"]),
                                      records[mg3])
                    self.assertEqual(json.loads(lmp["Timer"])[0],
                                     ltimers[mg3][0])
                    self.assertEqual(set(json.loads(lmp["Timer"])),
                                     set(ltimers[mg3]))
                    self.assertEqual(lmp["MntGrp"], mg3)

                    # try switch to unnamed active profile
                    # and then to selector mg3

#                    self.assertTrue(lrs.isMntGrpUpdated())
#                    self.assertTrue(lrs.isMntGrpUpdated())
                    wmg = ""
                    lrs.mntGrp = mg3
                    MSUtils.usetEnv('ActiveMntGrp', self._ms.ms.keys()[0])
                    lrs.switchProfile()

                    tmpcf1 = json.loads(rs[mg1].mntGrpConfiguration())
                    tmpcf2 = json.loads(rs[mg2].mntGrpConfiguration())
                    tmpcf3 = json.loads(rs[mg3].mntGrpConfiguration())
                    ltmpcf = json.loads(lrs.mntGrpConfiguration())
                    self.myAssertDict(tmpcf3, ltmpcf)
#                    self.myAssertDict(tmpcf1, ltmpcf)
#                    self.myAssertDict(tmpcf2, ltmpcf)

                    self.compareToDumpJSON(
                        lrs,
                        [
                            "DataSourceSelection",
                            "UnplottedComponents",
                            "PreselectingDataSources",
                            "Timer"],
                        name=mg3)
                    lmp = json.loads(lrs.profileConfiguration)
                    self.myAssertDict(json.loads(lmp["DataSourceSelection"]),
                                      adss[mg3])
                    self.assertEqual(
                        set(json.loads(lmp["PreselectingDataSources"])),
                        set(aadss[mg3]))

                    self.assertEqual(
                        set(json.loads(lmp["UnplottedComponents"])),
                        mylhe)
                    self.assertEqual(json.loads(lmp["OrderedChannels"]),
                                     pdss[mg3])
                    self.myAssertDict(json.loads(lmp["UserData"]),
                                      records[mg3])
                    self.assertEqual(json.loads(lmp["Timer"])[0],
                                     ltimers[mg3][0])
                    self.assertEqual(set(json.loads(lmp["Timer"])),
                                     set(ltimers[mg3]))
                    self.assertEqual(lmp["MntGrp"], mg3)

                    # fetch non-existing mg
                    wmg = "wrong_mg2"
                    lrs.mntGrp = wmg
                    lrs.fetchProfile()

                    tmpcf1 = json.loads(rs[mg1].mntGrpConfiguration())
                    tmpcf2 = json.loads(rs[mg2].mntGrpConfiguration())
                    tmpcf3 = json.loads(rs[mg3].mntGrpConfiguration())
                    ltmpcf = json.loads(lrs.mntGrpConfiguration())
#                    self.myAssertDict(tmpcf3, ltmpcf)
#                    self.myAssertDict(tmpcf1, ltmpcf)
#                    self.myAssertDict(tmpcf2, ltmpcf)

                    self.compareToDumpJSON(
                        lrs,
                        [
                            "DataSourceSelection",
                            "UnplottedComponents",
                            "PreselectingDataSources",
                            "Timer", "MntGrp"],
                        name=mg3)
                    lmp = json.loads(lrs.profileConfiguration)
                    self.myAssertDict(json.loads(lmp["DataSourceSelection"]),
                                      adss[mg3])
                    self.assertEqual(
                        set(json.loads(lmp["PreselectingDataSources"])),
                        set(aadss[mg3]))

                    self.assertEqual(
                        set(json.loads(lmp["UnplottedComponents"])),
                        mylhe)
                    self.assertEqual(json.loads(lmp["OrderedChannels"]),
                                     pdss[mg3])
                    self.myAssertDict(json.loads(lmp["UserData"]),
                                      records[mg3])
                    self.assertEqual(json.loads(lmp["Timer"])[0],
                                     ltimers[mg3][0])
                    self.assertEqual(set(json.loads(lmp["Timer"])),
                                     set(ltimers[mg3]))
                    self.assertEqual(lmp["MntGrp"], wmg)

                    # fetch non-existing selection
                    self._cf.dp.deleteSelection(mg4)
                    lrs.mntGrp = mg4
                    self.assertTrue(
                        mg4 not in self._cf.dp.availableSelections())
                    self.assertTrue(mg4 in lrs.availableMntGrps())
                    if j % 2:
                        lrs.defaultPreselectedComponents = \
                            list(json.loads(lmp["ComponentPreselection"]
                                            ).keys())

                    lrs.fetchProfile()
                    tmpcf1 = json.loads(rs[mg1].mntGrpConfiguration())
                    tmpcf2 = json.loads(rs[mg2].mntGrpConfiguration())
                    tmpcf3 = json.loads(rs[mg3].mntGrpConfiguration())
                    tmpcf4 = json.loads(rs[mg4].mntGrpConfiguration())
                    ltmpcf = json.loads(lrs.mntGrpConfiguration())
                    self.myAssertDict(tmpcf4, ltmpcf)
#                    self.myAssertDict(tmpcf3, ltmpcf)
#                    self.myAssertDict(tmpcf1, ltmpcf)
#                    self.myAssertDict(tmpcf2, ltmpcf)

                    self.compareToDumpJSON(
                        lrs,
                        [
                            "DataSourcePreselection",
                            "PreselectingDataSources",
                            "ComponentPreselection",
                            "Timer",
                            "MntGrp",

                            "ComponentSelection",
                            "DataSourceSelection",
                            "UnplottedComponents",
                        ],
                        name=mg3)
                    lmp = json.loads(lrs.profileConfiguration)
                    self.assertEqual(
                        set(json.loads(lmp["PreselectingDataSources"])),
                        set(aadss[mg3]))
                    self.assertEqual(
                        set(json.loads(lmp["DataSourcePreselection"])),
                        set())

                    if j % 2:

                        cpgood = self.smycps.keys() + self.smycps2.keys()
                        if "client_long" in aadss[mg3] \
                                or "client_short" in aadss[mg3]:
                            cpgood.remove("smycpnt1")
                        if "client2_long" in aadss[mg3] \
                                or "client2_short" in aadss[mg3]:
                            cpgood.remove("s2mycpnt1")

                        myacps = dict(acps[mg3])
                        for cp in myacps.keys():
                            myacps[cp] = True if cp in cpgood else None
                        self.myAssertDict(
                            json.loads(lmp["ComponentPreselection"]),
                            myacps)
                    else:
                        self.myAssertDict(
                            json.loads(lmp["ComponentPreselection"]),
                            {})

                    mycps = dict(cps[mg3])
                    for cp in mycps:
                        mycps[cp] = False
                    self.myAssertDict(
                        json.loads(lmp["ComponentSelection"]), mycps)

                    self.assertEqual(json.loads(lmp["OrderedChannels"]),
                                     pdss[mg3])
                    self.myAssertDict(json.loads(lmp["UserData"]),
                                      records[mg3])
                    self.assertEqual(json.loads(lmp["Timer"])[0],
                                     ltimers[mg4][0])
                    self.assertEqual(set(json.loads(lmp["Timer"])),
                                     set(ltimers[mg4]))
                    self.assertEqual(lmp["MntGrp"], mg4)

                    ladss = {}
                    for ds, vl in adss[mg3].items():
                        ladss[ds] = False

                    for ds, vl in adss[mg4].items():
                        if vl:
                            if ds in self.smychs.keys() and \
                                    self.smychs[ds]:
                                ladss[ds] = vl
                            elif ds in self.smychsXX.keys() and \
                                    self.smychsXX[ds]:
                                ladss[ds] = vl
                            if ds not in self.smychs.keys() and \
                                    ds not in self.smychsXX.keys():
                                ladss[ds] = vl
                        elif ds in adss[mg3].keys():
                            if ds in self.smychsXX.keys() \
                                    and self.smychsXX[ds]:
                                ladss[ds] = vl
                            else:
                                ladss[ds] = vl

                    llhe = set()

                    for ds in json.loads(mp[mg3]["UnplottedComponents"]):
                        if ds not in self.smychsXX.keys() \
                           and ds in self.smychs.keys() and ds in cpdss:
                            llhe.add(ds)

                    for ds in ladss.keys():
                        if ds in lhe2[mg4]:
                            llhe.add(ds)

                    for tm in json.loads(mp[mg4]["Timer"]):
                        if tm in ladss:
                            if tm in llhe:
                                ladss[tm] = False
                                llhe.remove(tm)
                    for tm in json.loads(mp[mg3]["Timer"]):
                        if tm in ladss:
                            if tm in json.loads(
                                    mp[mg4]["UnplottedComponents"]):
                                ladss[tm] = False
                                if tm not in json.loads(mp[mg4]["Timer"]):
                                    if tm in llhe:
                                        llhe.remove(tm)

                    for ds in self.smychs.keys():
                        if ds in llhe:
                            if ds in lhe2[mg3] and ds not in lhe2[mg4]:
                                llhe.remove(ds)

                    self.myAssertDict(json.loads(lmp["DataSourceSelection"]),
                                      ladss)

                    self.assertEqual(
                        set(json.loads(lmp["UnplottedComponents"])),
                        llhe)

                finally:
                    for mg in rs.keys():
                        try:
                            rs[mg].deleteProfile(mgs[mg])
                        except:
                            pass
                    for mg in tmg.keys():
                        try:
                            tmg[mg].tearDown()
                        except:
                            pass
                    simp2.tearDown()
                    try:
                        self.tearDown()
                    except:
                        pass
        finally:
            try:
                self.setUp()
            except:
                pass

    # updateMntGrp test
    def test_myswitchProfile_importMntGrp(self):
        fun = sys._getframe().f_code.co_name
        print "Run: %s.%s() " % (self.__class__.__name__, fun)
        val = {"ConfigDevice": self._cf.dp.name(),
               "WriterDevice": self._wr.dp.name(),
               "Door": 'doortestp09/testts/t1r228',
               "MntGrp": 'mg2'}

        self.maxDiff = None
        self.tearDown()
#        print "DOWN"
#        print "UP"
        try:
            for j in range(10):
                print "JJJ:", j
                self.setUp()
                self.mySetUp()
                db = PyTango.Database()
                db.put_device_property(self._ms.ms.keys()[0],
                                       {'PoolNames': self._pool.dp.name()})

                wrong = []

                mgs = ["mg1", "mg2", "mg3",
                       "mntgrp", "somegroup"
                       ]
                ors = None

                mp = {}
                msp = {}
                tmg = {}
                cps = {}
                acps = {}
                adss = {}
                aadss = {}
                pdss = {}
                lhe2 = {}
                records = {}
                ltimers = {}

                pool = self._pool.dp
                self._ms.dps[self._ms.ms.keys()[0]].Init()
                scalar_ctrl = 'ttestp09/testts/t1r228'
                spectrum_ctrl = 'ttestp09/testts/t2r228'
                image_ctrl = 'ttestp09/testts/t3r228'
                simp2 = TestServerSetUp.MultiTestServerSetUp(
                    devices=['ttestp09/testts/t%02dr228' %
                             i for i in range(1, 37)])

                try:
#                    print "SIMP2 SETUP"
                    simp2.setUp()

                    # create mntgrps

                    for i, mg in enumerate(mgs):
#                        print "OPEN RS"
                        ors = self.openRecSelector()
#                        print "OPEN RS END"
                        ors.configDevice = val["ConfigDevice"]
                        ors.door = val["Door"]
                        ors.mntGrp = mg
                        self.assertEqual(ors.configDevice, val["ConfigDevice"])
                        self.assertEqual(ors.door, val["Door"])

                        self.assertEqual(
                            set(ors.availableMntGrps()), set(mgs[:(i)]))
#                        self.myAssertRaise(Exception, ors.updateMntGrp)

                        self.assertEqual(
                            set(ors.availableMntGrps()), set(mgs[:(i)]))

                        ctrls = [scalar_ctrl, spectrum_ctrl, image_ctrl,
                                 "__tango__"]
                        expch = []
                        pdss[mg] = []

                        timers = {}
                        ntms = 1  # self._rnd.randint(1, 5)
                        tms = self._rnd.sample(set(
                            [ch for ch in self.smychsXX.keys()
                             if not ch.startswith("client")]), ntms)
                        for tm in tms:
                            myct = ("ctrl_%s" % tm).replace("_", "/")
                            timers[myct] = tm
                            ctrls.append(myct)
#                        print "TIMERSL", tms
#                        print "TIMERSD", timers
                        ltimers[mg] = timers.values()
#                        print "LTIMER", ltimers[mg]

                        for ds, vl in self.smychsXX.items():
                            if vl:
                                exp = {}
                                exp["name"] = ds
                                exp["source"] = vl["source"]
                                myct = None
                                for ct, ch in timers.items():
                                    if ds == ch:
                                        myct = ct
                                        break

                                if myct:
                                    exp["controller"] = myct
                                    exp["type"] = "CTExpChannel"
                                elif ds.startswith("image"):
                                    exp["controller"] = image_ctrl
                                    exp["type"] = "TwoDExpChannel"
                                elif ds.startswith("spectrum"):
                                    exp["controller"] = spectrum_ctrl
                                    exp["type"] = "OneDExpChannel"
                                else:
                                    exp["controller"] = scalar_ctrl
                                    exp["type"] = "CTExpChannel"
                                exp["interfaces"] = [exp["type"]]
                                expch.append(exp)
                                pdss[mg].append(ds)
                        pdss[mg] = sorted(pdss[mg])
                        self._rnd.shuffle(pdss[mg])

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

                        cps[mg] = {}
                        acps[mg] = {}
                        dss = {}
                        lcp = self._rnd.randint(1, 40)
                        lds = self._rnd.randint(1, 40)

                        self._cf.dp.SetCommandVariable(
                            ["CPDICT", json.dumps(amycps)])
                        self._cf.dp.SetCommandVariable(
                            ["DSDICT", json.dumps(amydss)])
                        comps = set()

                        ncps = self._rnd.randint(1, len(amycps) - 1)
                        lcps = self._rnd.sample(set(amycps.keys()), ncps)
                        for cp in lcps:
                            if cp not in wrong:
                                cps[mg][cp] = bool(self._rnd.randint(0, 1))
                                if cps[mg][cp]:
                                    comps.add(cp)

                        ancps = self._rnd.randint(1, len(amycps.keys()) - 1)
                        alcps = self._rnd.sample(set(amycps.keys()), ancps)
                        for cp in alcps:
                            if cp not in wrong:
                                acps[mg][cp] = bool(self._rnd.randint(0, 1))
                                if acps[mg][cp]:
                                    comps.add(cp)

                        ndss = self._rnd.randint(1, len(amycps.keys()) - 1)
                        ldss = self._rnd.sample(set(amycps.keys()), ndss)
                        for ds in ldss:
                            if ds in amydss.keys():
                                if ds not in wrong:
                                    dss[ds] = bool(self._rnd.randint(0, 1))

                        ndss = self._rnd.randint(1, len(amydss.keys()) - 1)
                        ldss = self._rnd.sample(set(amydss.keys()), ndss)
                        for ds in ldss:
                            if ds in amydss.keys():
                                if ds not in wrong:
                                    dss[ds] = bool(self._rnd.randint(0, 1))

                        nadss = self._rnd.randint(1, len(amydss.keys()) - 1)
                        aadss[mg] = [ds for ds in self._rnd.sample(
                            set(amydss.keys()), nadss)]
                        nadss = self._rnd.randint(1, len(amydss.keys()) - 1)
                        indss = [ds for ds in self._rnd.sample(
                            set(amydss.keys()), nadss)]
                        aindss = {}
                        for cp in indss:
                            if cp not in wrong:
                                aindss[cp] = bool(self._rnd.randint(0, 1))

                        for tm in ltimers[mg]:
                            dss[tm] = bool(self._rnd.randint(0, 1))

                        mncps = self._rnd.randint(1, len(amycps.keys()) - 1)
                        mcps = [cp for cp in self._rnd.sample(
                                set(amycps.keys()), mncps) if cp not in wrong]
                        oncps = self._rnd.randint(1, len(amycps.keys()) - 1)
                        ocps = [cp for cp in self._rnd.sample(
                                set(amycps.keys()), oncps) if cp not in wrong]
                        for cp in mcps:
                            comps.add(cp)

                        adss[mg] = dict(dss)
                        for ch in expch:
                            if ch["name"] not in adss[mg].keys():
                                adss[mg][ch["name"]] = False
                        mp[mg] = json.loads(ors.profileConfiguration)
                        mp[mg]["ComponentSelection"] = json.dumps(cps[mg])
                        mp[mg]["ComponentPreselection"] = json.dumps(
                            acps[mg])
                        mp[mg]["DataSourceSelection"] = json.dumps(dss)
                        mp[mg]["PreselectingDataSources"] = \
                            json.dumps(aadss[mg])
                        mp[mg]["OptionalComponents"] = json.dumps(ocps)
                        mp[mg]["DataSourcePreselection"] = json.dumps(aindss)
                        mp[mg]["AppendEntry"] = bool(self._rnd.randint(0, 1))
                        mp[mg]["ComponentsFromMntGrp"] = bool(
                            self._rnd.randint(0, 1))
                        mp[mg]["DynamicComponents"] = bool(
                            self._rnd.randint(0, 1))
                        mp[mg]["DefaultDynamicLinks"] = \
                            bool(self._rnd.randint(0, 1))
                        mp[mg]["DefaultDynamicPath"] = self.getRandomName(20)
                        mp[mg]["TimeZone"] = self.getRandomName(20)

                        mp[mg]["ConfigVariables"] = json.dumps(dict(
                            (self.getRandomName(10),
                             self.getRandomName(15)) for _ in
                            range(self._rnd.randint(1, 40))))
                        paths = dict(
                            (self.getRandomName(10),
                             self.getRandomName(15)) for _ in
                            range(self._rnd.randint(1, 40)))
                        labels = dict(
                            (self.getRandomName(10),
                             self.getRandomName(15)) for _ in
                            range(self._rnd.randint(1, 40)))
                        links = dict(
                            (self.getRandomName(10),
                             bool(self._rnd.randint(0, 1))) for _ in
                            range(self._rnd.randint(1, 40)))
                        types = dict(
                            (self.getRandomName(10),
                             self.getRandomName(15)) for _ in
                            range(self._rnd.randint(1, 40)))
                        shapes = dict(
                            (self.getRandomName(10),
                             [self._rnd.randint(1, 40)
                              for _ in range(self._rnd.randint(0, 3))])
                            for _ in range(self._rnd.randint(1, 40)))

                        mp[mg]["ChannelProperties"] = json.dumps(
                            {
                                "label": labels,
                                "nexus_path": paths,
                                "link": links,
                                "data_type": types,
                                "shape": shapes
                            }
                        )

                        ors.profileConfiguration = str(json.dumps(mp[mg]))
                        mp[mg] = json.loads(ors.profileConfiguration)
                        self._cf.dp.SetCommandVariable(["MCPLIST",
                                                        json.dumps(mcps)])

                        records[mg] = {}
                        describer = Describer(self._cf.dp, True)
                        cpres = describer.components(dstype='CLIENT')
                        for grp in cpres:
                            for idss in grp.values():
                                for idsrs in idss.values():
                                    for idsr in idsrs:
                                        records[mg][str(idsr[2])] = "1234"
                        dsres = describer.dataSources(
                            dss.keys(), dstype='CLIENT')[0]
                        for dsr in dsres.values():
                            records[mg][str(dsr.record)] = '2345'

                        mp[mg] = json.loads(ors.profileConfiguration)
                        mp[mg]["Timer"] = json.dumps(ltimers[mg])
                        mp[mg]["UserData"] = json.dumps(records[mg])
                        ors.profileConfiguration = str(json.dumps(mp[mg]))
                        mp[mg] = json.loads(ors.profileConfiguration)

                        tmg[mg] = TestMGSetUp.TestMeasurementGroupSetUp(
                            name=mg)
        #                    dv = "/".join(ar["full_name"].split("/")[0:-1])
                        chds = [ds for ds in ors.selectedDataSources()
                                if not ds.startswith('client')]
                        chds1 = list(chds)
                        chds2 = [ds for ds in ors.componentDataSources()
                                 if not ds.startswith('client')]
                        chds.extend(chds2)
                        bchds = list(chds)
                        chds.extend(ltimers[mg])
                        tmpchds = sorted(list(set(chds)))
                        chds = []
                        for ds in pdss[mg]:
                            if ds in tmpchds:
                                chds.append(ds)
                        for ds in tmpchds:
                            if ds not in pdss[mg]:
                                chds.append(ds)

                        lheds = []
                        if chds:
                            nhe = self._rnd.randint(0, len(set(chds)) - 1)
                            lheds = self._rnd.sample(set(chds), nhe)

                        lhecp = []
                        if comps:
                            nhe = self._rnd.randint(0, len(set(comps)) - 1)
                            lhecp = self._rnd.sample(set(comps), nhe)

                        lhe = lheds + lhecp

                        mp[mg] = json.loads(ors.profileConfiguration)
                        mp[mg]["UnplottedComponents"] = json.dumps(lhe)
                        mp[mg]["OrderedChannels"] = json.dumps(pdss[mg])
                        ors.profileConfiguration = str(json.dumps(mp[mg]))
                        mp[mg] = json.loads(ors.profileConfiguration)

                        lhe2[mg] = []
                        for el in lhe:
                            found = False
                            for cp in comps:
                                if el in amycpsstep[cp]:
                                    if cp not in lhecp:
                                        found = True
                            if not found:
                                lhe2[mg].append(el)

                        self.myAssertDict(
                            json.loads(mp[mg]["ComponentPreselection"]),
                            acps[mg])
                        self.myAssertDict(
                            json.loads(mp[mg]["ComponentSelection"]), cps[mg])
                        self.myAssertDict(
                            json.loads(mp[mg]["DataSourceSelection"]),
                            adss[mg])
                        self.assertEqual(
                            set(json.loads(mp[mg]["UnplottedComponents"])),
                            set(lhe))
                        self.assertEqual(
                            json.loads(mp[mg]["OrderedChannels"]), pdss[mg])
                        self.myAssertDict(
                            json.loads(mp[mg]["UserData"]), records[mg])
                        self.assertEqual(
                            json.loads(mp[mg]["Timer"]), ltimers[mg])
                        self.assertEqual(mp[mg]["MntGrp"], mg)
                        self.dump(ors, name=mg)
                        self.assertTrue(not ors.isMntGrpUpdated())
                        self.assertTrue(not ors.isMntGrpUpdated())

                        wwcp = ors.components
                        describer = Describer(self._cf.dp, True)
                        res = describer.components(wwcp, "STEP", "")

                        mdds = set()
                        for mdss in res[0].values():
                            if isinstance(mdss, dict):
                                for ds in mdss.keys():
                                    adss[mg][ds] = True

                        for tm in ltimers[mg]:
                            if tm in lhe2[mg]:
                                if tm in adss[mg].keys():
#                                    print "DES", tm
                                    adss[mg][tm] = False

                        jpcnf = ors.updateMntGrp()
                        self.dump(ors, name=mg)
                        self.assertTrue(ors.isMntGrpUpdated())
                        self.assertTrue(ors.isMntGrpUpdated())
                        pcnf = json.loads(jpcnf)
                        mgdp = PyTango.DeviceProxy(
                            tmg[mg].new_device_info_writer.name)
                        jcnf = ors.mntGrpConfiguration()
                        cnf = json.loads(jcnf)
                        mp[mg] = json.loads(ors.profileConfiguration)
                        self.myAssertDict(
                            json.loads(mp[mg]["ComponentPreselection"]),
                            acps[mg])
                        self.myAssertDict(
                            json.loads(mp[mg]["ComponentSelection"]), cps[mg])
                        self.myAssertDict(
                            json.loads(
                                mp[mg]["DataSourceSelection"]), adss[mg])
                        self.assertEqual(
                            set(json.loads(mp[mg]["UnplottedComponents"])),
                            set(lhe2[mg]))
                        self.assertEqual(
                            json.loads(mp[mg]["OrderedChannels"]), pdss[mg])
                        self.myAssertDict(
                            json.loads(mp[mg]["UserData"]), records[mg])
                        self.assertEqual(
                            json.loads(mp[mg]["Timer"]), ltimers[mg])
                        self.assertEqual(mp[mg]["MntGrp"], mg)
                        myctrls = {}
                        fgtm = "/".join(
                            self.smychsXX[str(ltimers[mg][0])]['source'].split(
                                "/")[:-1])
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
                                        try:
                                            tdv = "/".join(
                                                cnt['source'].split("/")[:-1])
                                            if i < idmax:
                                                idmax = i
                                                ttdv = tdv
                                            chn = {'ndim': 0,
                                                   'index': i,
                                                   'name': str(ds),
                                                   'data_type':
                                                       cnt['data_type'],
                                                   'plot_type': (
                                                       cnt['plot_type']
                                                       if (ds not in lhe2[mg]
                                                           and ds in bchds)
                                                       else 0),
                                                   'data_units':
                                                       cnt['data_units'],
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
                                                       if (ds not in lhe2[mg]
                                                           and ds in bchds)
                                                       else []),
                                                   'nexus_path': '',
                                                   'normalization': 0,
                                                   'source': cnt['source']}
                                            tgc[tdv] = chn
                                        except:
                                            raise
                            if tgc:
                                ltm = timers[cl] if cl in timers.keys() \
                                    else ltimers[mg][0]
                                fltm = "/".join(
                                    self.smychsXX[str(ltm)]['source'].split(
                                        "/")[:-1])
                                myctrls[cl] = {
                                    'units':
                                        {'0':
                                         {
                                             'channels': tgc,
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
                                    chn = {'ndim': 0,
                                           'index': i,
                                           'name': str(ds),
                                           'data_type': cnt['data_type'],
                                           'plot_type': (
                                               cnt['plot_type']
                                               if ds not in lhe2[mg] else 0),
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
                                               if ds not in lhe2[mg] else []),
                                           'nexus_path': '',
                                           'normalization': 0,
                                           'source': cnt['source']}
                                    tgc[chn["full_name"]] = chn
                                except:
                                    raise

                        if tgc:
                            myctrls['__tango__'] = {
                                'units':
                                    {'0':
                                     {'channels': tgc,
                                      'monitor': fgtm,
                                      'id': 0,
                                      'timer': fgtm,
                                      'trigger_type': 0}}}

                        smg = {"controllers": myctrls,
                               "monitor": "%s" % fgtm,
                               "description": "Measurement Group",
                               "timer": "%s" % fgtm,
                               "label": mg}
        #                    print "SMG", smg
                        self.myAssertDict(smg, pcnf)
                        self.myAssertDict(pcnf, cnf)
                        ors.mntGrp = "nxsmntgrp"
                        ors.profileConfiguration = str(json.dumps({}))
                        ors.configDevice = val["ConfigDevice"]
                        ors.door = val["Door"]
#                        print "MG", mg
                        ors.mntGrp = mg
                        ors.fetchProfile()
                        mp[mg] = json.loads(ors.profileConfiguration)
#                        self.myAssertRaise(Exception, ors.isMntGrpUpdated)
#                       ors.fetchProfile()
#                        mp[mg] = json.loads(ors.profileConfiguration)

                        self.assertTrue(ors.isMntGrpUpdated())
                        self.assertTrue(ors.isMntGrpUpdated())

                        self.compareToDumpJSON(
                            ors,
                            ["DataSourceSelection",
                             "UnplottedComponents",
                             "PreselectingDataSources",
                             "UnplottedComponents"],
                            name=mg)
                        mp[mg] = json.loads(ors.profileConfiguration)
                        self.myAssertDict(
                            json.loads(
                                mp[mg]["DataSourceSelection"]), adss[mg])
                        self.assertEqual(
                            set(json.loads(mp[mg]["PreselectingDataSources"])),
                            set(aadss[mg]))
#                        print "PDS1", set(aadss[mg])
                        self.assertEqual(
                            set(json.loads(mp[mg]["UnplottedComponents"])),
                            set(lhe2[mg]))
                        self.assertEqual(
                            json.loads(mp[mg]["OrderedChannels"]), pdss[mg])
                        self.myAssertDict(
                            json.loads(mp[mg]["UserData"]), records[mg])
                        self.assertEqual(
                            json.loads(mp[mg]["Timer"]), ltimers[mg])
                        self.assertEqual(mp[mg]["MntGrp"], mg)
#                        print "WWWMG", mg
                        self.compareToDumpJSON(
                            ors,
                            ["DataSourceSelection",
                             "UnplottedComponents",
                             "PreselectingDataSources"],
                            name=mg)

                    # check profile commands
                    mg1, mg2, mg3, mg4 = tuple(self._rnd.sample(mgs, 4))
#                    print "MGS", mg1, mg2, mg3, mg4
                    ors.profileConfiguration = str(json.dumps(mp[mg1]))
                    self.compareToDumpJSON(
                        ors,
                        ["DataSourceSelection",
                         "UnplottedComponents",
                         "PreselectingDataSources"],
                        name=mg1)
                    ors.profileConfiguration = str(json.dumps(mp[mg2]))
                    self.compareToDumpJSON(
                        ors,
                        ["DataSourceSelection",
                         "UnplottedComponents",
                         "PreselectingDataSources"],
                        name=mg2)
                    ors.profileConfiguration = str(json.dumps(mp[mg3]))
                    self.compareToDumpJSON(
                        ors,
                        ["DataSourceSelection",
                         "UnplottedComponents",
                         "PreselectingDataSources"],
                        name=mg3)
                    ors.profileConfiguration = str(json.dumps(mp[mg4]))
                    self.compareToDumpJSON(
                        ors,
                        ["DataSourceSelection",
                         "UnplottedComponents",
                         "PreselectingDataSources"],
                        name=mg4)

                    lrs = self.openRecSelector2()
                    lrs.configDevice = val["ConfigDevice"]
                    lrs.door = val["Door"]
                    lrs.mntGrp = mg1
                    self.assertEqual(lrs.configDevice, val["ConfigDevice"])

                    self.assertEqual(lrs.door, val["Door"])
                    lmp = json.loads(lrs.profileConfiguration)

#                    self.myAssertRaise(Exception, lrs.isMntGrpUpdated)

                    self.switchProfile(lrs, False)
                    lmp = json.loads(lrs.profileConfiguration)

                    self.compareToDumpJSON(
                        lrs, [
                            "DataSourceSelection",
                            "UnplottedComponents",
                            "PreselectingDataSources",
                            "Timer"
                        ],
                        name=mg1)
                    ors.profileConfiguration = str(json.dumps(mp[mg1]))
                    tmpcf = json.loads(ors.mntGrpConfiguration())
                    ltmpcf = json.loads(lrs.mntGrpConfiguration())
                    self.myAssertDict(tmpcf, ltmpcf)

                    self.assertEqual(
                        set(json.loads(lmp["PreselectingDataSources"])),
                        set(aadss[mg1]))
                    self.myAssertDict(
                        json.loads(lmp["DataSourceSelection"]), adss[mg1])
                    self.assertEqual(
                        json.loads(lmp["OrderedChannels"]), pdss[mg1])
                    self.myAssertDict(
                        json.loads(lmp["UserData"]), records[mg1])
                    self.assertEqual(
                        json.loads(lmp["Timer"])[0], ltimers[mg1][0])
                    self.assertEqual(
                        set(json.loads(lmp["Timer"])), set(ltimers[mg1]))
                    self.assertEqual(lmp["MntGrp"], mg1)

#                    print "MGS", mg1, mg2, mg3, mg4

                    # import mntgrp another defined by selector MntGrp
                    lrs.mntGrp = mg2

                    myoldmg = json.loads(lrs.mntGrpConfiguration())
                    self.assertTrue(not lrs.isMntGrpUpdated())
                    self.assertTrue(not lrs.isMntGrpUpdated())

                    lrs.importMntGrp()
                    mynewmg = json.loads(lrs.mntGrpConfiguration())
                    lmp = json.loads(lrs.profileConfiguration)

                    try:
                        self.myCompDict(mynewmg, myoldmg)
                        self.assertTrue(lrs.isMntGrpUpdated())
                        self.assertTrue(lrs.isMntGrpUpdated())
                    except:
                        self.assertTrue(not lrs.isMntGrpUpdated())
                        self.assertTrue(not lrs.isMntGrpUpdated())

                    ors.profileConfiguration = str(json.dumps(mp[mg1]))
                    tmpcf1 = json.loads(ors.mntGrpConfiguration())
                    ors.profileConfiguration = str(json.dumps(mp[mg2]))
                    tmpcf2 = json.loads(ors.mntGrpConfiguration())
                    ltmpcf = json.loads(lrs.mntGrpConfiguration())
#                    self.myAssertDict(tmpcf1, ltmpcf)
                    self.myAssertDict(tmpcf2, ltmpcf)
#                    print "RSmg2",
                    ors.profileConfiguration = str(json.dumps(mp[mg2]))
                    self.compareToDumpJSON(
                        ors,
                        ["DataSourceSelection",
                         "UnplottedComponents",
                         "PreselectingDataSources"],
                        name=mg2)
                    self.compareToDumpJSON(
                        lrs,
                        ["DataSourceSelection",
                         "UnplottedComponents",
                         "PreselectingDataSources",
                         "Timer",
                         "MntGrp"],
                        name=mg1)

                    continue
                    ors.profileConfiguration = str(json.dumps(mp[mg2]))
                    tmpcf = json.loads(ors.mntGrpConfiguration())
                    ltmpcf = json.loads(lrs.mntGrpConfiguration())
                    self.myAssertDict(tmpcf, ltmpcf)

                    self.assertEqual(
                        set(json.loads(lmp["PreselectingDataSources"])),
                        set(aadss[mg1]))
                    self.assertEqual(
                        json.loads(lmp["OrderedChannels"]), pdss[mg1])
                    self.myAssertDict(
                        json.loads(lmp["UserData"]), records[mg1])

                    self.assertEqual(
                        json.loads(lmp["Timer"])[0], ltimers[mg2][0])
                    self.assertEqual(
                        set(json.loads(lmp["Timer"])), set(ltimers[mg2]))
                    self.assertEqual(lmp["MntGrp"], mg2)

                    self.myAssertDict(
                        json.loads(mp[mg1]["DataSourceSelection"]),
                        adss[mg1])
                    self.myAssertDict(
                        json.loads(mp[mg2]["DataSourceSelection"]),
                        adss[mg2])

                    self.assertEqual(
                        set(json.loads(mp[mg1]["UnplottedComponents"])),
                        set(lhe2[mg1]))
                    self.assertEqual(
                        set(json.loads(mp[mg2]["UnplottedComponents"])),
                        set(lhe2[mg2]))

                    ladss = {}
                    llhe = set()
                    for ds, vl in adss[mg1].items():
                        ladss[ds] = vl
                    for nd in lhe2[mg1]:
                        if nd not in self.smychsXX.keys():
                            llhe.add(nd)

                    for ds, vl in adss[mg2].items():
                        if vl:
                            if ds in self.smychs.keys() and \
                                    self.smychs[ds]:
                                ladss[ds] = vl
                                if ds in lhe2[mg2]:
                                    llhe.add(ds)
                                elif ds in llhe:
                                    llhe.remove(ds)
                            elif ds in self.smychsXX.keys() and \
                                    self.smychsXX[ds]:
                                ladss[ds] = vl
                                if ds in lhe2[mg2]:
                                    llhe.add(ds)
                                elif ds in llhe:
                                    llhe.remove(ds)
                            if ds not in self.smychs.keys() and \
                                    ds not in self.smychsXX.keys():
                                ladss[ds] = vl
                                if ds in lhe2[mg2]:
                                    llhe.add(ds)
                                elif ds in llhe:
                                    llhe.remove(ds)
                        elif ds in adss[mg1].keys():
                            if ds in self.smychsXX.keys() \
                                    and self.smychsXX[ds]:
                                ladss[ds] = vl
                                if ds in lhe2[mg2]:
                                    llhe.add(ds)
                                elif ds in llhe:
                                    llhe.remove(ds)
                            else:
                                ladss[ds] = adss[mg1][ds]

                    for tm in json.loads(mp[mg2]["Timer"]):
                        if tm in ladss:
                            if tm in llhe:
                                ladss[tm] = False
                                llhe.remove(tm)
                    for tm in json.loads(mp[mg1]["Timer"]):
                        if tm in ladss:
                            if tm in json.loads(
                                    mp[mg2]["UnplottedComponents"]):
                                ladss[tm] = False
                                if tm not in json.loads(mp[mg2]["Timer"]):
                                    if tm in llhe:
                                        llhe.remove(tm)

#                    print "T1", json.loads(mp[mg1]["Timer"])
#                    print "T2", json.loads(mp[mg2]["Timer"])
#                    print "LT", json.loads(lmp["Timer"])
                    # ???
                    self.myAssertDict(
                        json.loads(lmp["DataSourceSelection"]), ladss)
                    # ???
                    self.assertEqual(
                        set(json.loads(lmp["UnplottedComponents"])),
                        set(llhe))

                    # import mntgrp mg2 (with content mg1)
                    # after change in mntgrp device

                    lrs.mntGrp = mg2
                    ors.profileConfiguration = str(json.dumps(mp[mg1]))
                    tmpcf = json.loads(ors.mntGrpConfiguration())
                    ors.profileConfiguration = str(json.dumps(mp[mg2]))
                    tmpcf2 = json.loads(ors.mntGrpConfiguration())
                    ltmpcf = json.loads(lrs.mntGrpConfiguration())
                    self.assertEqual(ltmpcf, tmpcf2)
                    tmpcf['label'] = mg2
                    mgdp = PyTango.DeviceProxy(
                        tmg[mg2].new_device_info_writer.name)
#                    print "name", tmg[mg2].new_device_info_writer.name
                    mgdp.Configuration = json.dumps(tmpcf)
                    self.assertTrue(not lrs.isMntGrpUpdated())
                    self.assertTrue(not lrs.isMntGrpUpdated())

                    ors.profileConfiguration = str(json.dumps(mp[mg1]))
                    tmpcf1 = json.loads(ors.mntGrpConfiguration())
                    ors.profileConfiguration = str(json.dumps(mp[mg2]))
                    tmpcf2 = json.loads(ors.mntGrpConfiguration())
                    ltmpcf = json.loads(lrs.mntGrpConfiguration())
#                    self.myAssertDict(tmpcf1, ltmpcf)
                    self.myAssertDict(tmpcf2, ltmpcf)

                    lrs.importMntGrp()
                    # ???

                    ltmpcf2 = json.loads(lrs.mntGrpConfiguration())
                    if not Utils.compareDict(ltmpcf2, ltmpcf):
                        self.assertTrue(not lrs.isMntGrpUpdated())
                        self.assertTrue(not lrs.isMntGrpUpdated())

                    ors.profileConfiguration = str(json.dumps(mp[mg1]))
                    tmpcf1 = json.loads(ors.mntGrpConfiguration())
                    ors.profileConfiguration = str(json.dumps(mp[mg2]))
                    tmpcf2 = json.loads(ors.mntGrpConfiguration())
                    ltmpcf = json.loads(lrs.mntGrpConfiguration())
#                    self.myAssertDict(tmpcf1, ltmpcf)
                    self.myAssertDict(tmpcf2, ltmpcf)

                    self.compareToDumpJSON(
                        lrs,
                        ["ComponentPreselection",
                         "ComponentSelection",
                         "DataSourceSelection",
                         "UnplottedComponents",
                         "PreselectingDataSources",
                         "Timer",
                         "MntGrp"],
                        name=mg1)

                    ors.profileConfiguration = str(json.dumps(mp[mg2]))
                    self.compareToDump(
                        ors,
                        ["ComponentPreselection",
                         "ComponentSelection",
                         "DataSourceSelection",
                         "UnplottedComponents",
                         "PreselectingDataSources",
                         "Timer"],
                        name=mg2)

                    self.myAssertDict(
                        json.loads(mp[mg2]["ComponentPreselection"]),
                        acps[mg2])
                    self.myAssertDict(
                        json.loads(mp[mg2]["ComponentSelection"]),
                        cps[mg2])
                    self.myAssertDict(
                        json.loads(mp[mg2]["DataSourceSelection"]), adss[mg2])
                    self.assertEqual(
                        set(json.loads(mp[mg2]["PreselectingDataSources"])),
                        set(aadss[mg2]))
                    self.assertEqual(
                        set(json.loads(mp[mg2]["UnplottedComponents"])),
                        set(lhe2[mg2]))
                    self.assertEqual(
                        json.loads(mp[mg2]["OrderedChannels"]), pdss[mg2])
                    self.myAssertDict(json.loads(mp[mg2]["UserData"]),
                                      records[mg2])
                    self.assertEqual(
                        json.loads(mp[mg2]["Timer"]), ltimers[mg2])
                    self.assertEqual(mp[mg2]["MntGrp"], mg2)

                    # switch to active profile mg3
                    lrs.mntGrp = mg2
                    MSUtils.setEnv('ActiveMntGrp', mg3, self._ms.ms.keys()[0])

                    ors.profileConfiguration = str(json.dumps(mp[mg1]))
                    tmpcf1 = json.loads(ors.mntGrpConfiguration())
                    ors.profileConfiguration = str(json.dumps(mp[mg2]))
                    tmpcf2 = json.loads(ors.mntGrpConfiguration())
                    ors.profileConfiguration = str(json.dumps(mp[mg3]))
                    tmpcf3 = json.loads(ors.mntGrpConfiguration())
                    ltmpcf = json.loads(lrs.mntGrpConfiguration())
#                    self.myAssertDict(tmpcf1, ltmpcf)
                    self.myAssertDict(tmpcf2, ltmpcf)
#                    self.myAssertDict(tmpcf3, ltmpcf)

                    lrs.switchProfile()

                    ors.profileConfiguration = str(json.dumps(mp[mg1]))
                    tmpcf1 = json.loads(ors.mntGrpConfiguration())
                    ors.profileConfiguration = str(json.dumps(mp[mg2]))
                    tmpcf2 = json.loads(ors.mntGrpConfiguration())
                    ors.profileConfiguration = str(json.dumps(mp[mg3]))
                    tmpcf3 = json.loads(ors.mntGrpConfiguration())
                    ltmpcf = json.loads(lrs.mntGrpConfiguration())
                    self.myAssertDict(tmpcf3, ltmpcf)
#                    self.myAssertDict(tmpcf1, ltmpcf)
#                    self.myAssertDict(tmpcf2, ltmpcf)

                    self.compareToDumpJSON(
                        lrs,
                        [
                            "DataSourceSelection",
                            "UnplottedComponents",
                            "PreselectingDataSources",
                            "Timer"],
                        name=mg3)
                    lmp = json.loads(lrs.profileConfiguration)
                    self.myAssertDict(json.loads(lmp["DataSourceSelection"]),
                                      adss[mg3])
                    self.assertEqual(
                        set(json.loads(lmp["PreselectingDataSources"])),
                        set(aadss[mg3]))

                    mylhe = set(lhe2[mg3])
                    for tm in json.loads(mp[mg3]["Timer"]):
                        if tm in adss[mg3].keys():
                            if not adss[mg3][tm]:
                                if tm in mylhe:
                                    mylhe.remove(tm)
                    lmp = json.loads(lrs.profileConfiguration)

                    self.assertEqual(
                        set(json.loads(lmp["UnplottedComponents"])),
                        mylhe)
                    self.assertEqual(json.loads(lmp["OrderedChannels"]),
                                     pdss[mg3])
                    self.myAssertDict(json.loads(lmp["UserData"]),
                                      records[mg3])
                    self.assertEqual(json.loads(lmp["Timer"])[0],
                                     ltimers[mg3][0])
                    self.assertEqual(set(json.loads(lmp["Timer"])),
                                     set(ltimers[mg3]))
                    self.assertEqual(lmp["MntGrp"], mg3)

                    # switch to nonexisting active profile

#                    self.assertTrue(lrs.isMntGrpUpdated())
#                    self.assertTrue(lrs.isMntGrpUpdated())
                    wmg = "wrong_mg"
                    lrs.mntGrp = mg3
                    MSUtils.setEnv('ActiveMntGrp', wmg, self._ms.ms.keys()[0])
                    lrs.switchProfile()
                    self.assertEqual(
                        wmg,
                        MSUtils.getEnv('ActiveMntGrp', self._ms.ms.keys()[0]))

                    self.compareToDumpJSON(
                        lrs,
                        [
                            "DataSourceSelection",
                            "UnplottedComponents",
                            "PreselectingDataSources",
                            "Timer",
                            "MntGrp"],
                        name=mg3)
                    lmp = json.loads(lrs.profileConfiguration)
                    mydsg = dict(json.loads(lmp["DataSourceSelection"]))
                    for ds in self.smychsXX.keys():
                        if ds in expch:
                            mydsg[ds] = False
                    mylhe2 = set(mylhe)
                    for ds in self.smychsXX.keys():
                        if ds in mylhe2:
                            mylhe2.remove(ds)

                    self.myAssertDict(json.loads(lmp["DataSourceSelection"]),
                                      mydsg)
                    self.assertEqual(
                        set(json.loads(lmp["PreselectingDataSources"])),
                        set(aadss[mg3]))
                    self.assertEqual(
                        set(json.loads(lmp["UnplottedComponents"])),
                        mylhe2)
                    self.assertEqual(json.loads(lmp["OrderedChannels"]),
                                     pdss[mg3])
                    self.myAssertDict(json.loads(lmp["UserData"]),
                                      records[mg3])
                    self.assertEqual(json.loads(lmp["Timer"])[0],
                                     ltimers[mg3][0])
                    self.assertEqual(set(json.loads(lmp["Timer"])),
                                     set(ltimers[mg3]))
                    self.assertEqual(lmp["MntGrp"], wmg)

                    # switch to active profile mg3
                    lrs.mntGrp = mg2
                    self.assertTrue(not lrs.isMntGrpUpdated())
                    self.assertTrue(not lrs.isMntGrpUpdated())
                    MSUtils.setEnv('ActiveMntGrp', mg3, self._ms.ms.keys()[0])

                    ors.profileConfiguration = str(json.dumps(mp[mg1]))
                    tmpcf1 = json.loads(ors.mntGrpConfiguration())
                    ors.profileConfiguration = str(json.dumps(mp[mg2]))
                    tmpcf2 = json.loads(ors.mntGrpConfiguration())
                    ors.profileConfiguration = str(json.dumps(mp[mg3]))
                    tmpcf3 = json.loads(ors.mntGrpConfiguration())
                    ltmpcf = json.loads(lrs.mntGrpConfiguration())
#                    self.myAssertDict(tmpcf1, ltmpcf)
                    self.myAssertDict(tmpcf2, ltmpcf)
#                    self.myAssertDict(tmpcf3, ltmpcf)

                    self.switchProfile(lrs, True)

                    ors.profileConfiguration = str(json.dumps(mp[mg1]))
                    tmpcf1 = json.loads(ors.mntGrpConfiguration())
                    ors.profileConfiguration = str(json.dumps(mp[mg2]))
                    tmpcf2 = json.loads(ors.mntGrpConfiguration())
                    ors.profileConfiguration = str(json.dumps(mp[mg3]))
                    tmpcf3 = json.loads(ors.mntGrpConfiguration())
                    ltmpcf = json.loads(lrs.mntGrpConfiguration())
                    self.myAssertDict(tmpcf3, ltmpcf)
#                    self.myAssertDict(tmpcf1, ltmpcf)
#                    self.myAssertDict(tmpcf2, ltmpcf)

                    lmp = json.loads(lrs.profileConfiguration)
                    self.compareToDumpJSON(
                        lrs,
                        [
                            "DataSourceSelection",
                            "UnplottedComponents",
                            "PreselectingDataSources",
                            "Timer"],
                        name=mg3)
                    self.myAssertDict(json.loads(lmp["DataSourceSelection"]),
                                      adss[mg3])
                    self.assertEqual(
                        set(json.loads(lmp["PreselectingDataSources"])),
                        set(aadss[mg3]))

                    self.assertEqual(
                        set(json.loads(lmp["UnplottedComponents"])),
                        mylhe)
                    self.assertEqual(json.loads(lmp["OrderedChannels"]),
                                     pdss[mg3])
                    self.myAssertDict(json.loads(lmp["UserData"]),
                                      records[mg3])
                    self.assertEqual(json.loads(lmp["Timer"])[0],
                                     ltimers[mg3][0])
                    self.assertEqual(set(json.loads(lmp["Timer"])),
                                     set(ltimers[mg3]))
                    self.assertEqual(lmp["MntGrp"], mg3)

                    # try switch to unnamed active profile
                    # and then to selector mg3

#                    self.assertTrue(lrs.isMntGrpUpdated())
#                    self.assertTrue(lrs.isMntGrpUpdated())
                    wmg = ""
                    lrs.mntGrp = mg3
                    MSUtils.setEnv('ActiveMntGrp', wmg, self._ms.ms.keys()[0])
                    lrs.switchProfile()
                    self.assertEqual(
                        wmg,
                        MSUtils.getEnv('ActiveMntGrp', self._ms.ms.keys()[0]))

                    ors.profileConfiguration = str(json.dumps(mp[mg1]))
                    tmpcf1 = json.loads(ors.mntGrpConfiguration())
                    ors.profileConfiguration = str(json.dumps(mp[mg2]))
                    tmpcf2 = json.loads(ors.mntGrpConfiguration())
                    ors.profileConfiguration = str(json.dumps(mp[mg3]))
                    tmpcf3 = json.loads(ors.mntGrpConfiguration())
                    ltmpcf = json.loads(lrs.mntGrpConfiguration())
                    self.myAssertDict(tmpcf3, ltmpcf)
#                    self.myAssertDict(tmpcf1, ltmpcf)
#                    self.myAssertDict(tmpcf2, ltmpcf)

                    self.compareToDumpJSON(
                        lrs,
                        [
                            "DataSourceSelection",
                            "UnplottedComponents",
                            "PreselectingDataSources",
                            "Timer"],
                        name=mg3)
                    lmp = json.loads(lrs.profileConfiguration)
                    self.myAssertDict(json.loads(lmp["DataSourceSelection"]),
                                      adss[mg3])
                    self.assertEqual(
                        set(json.loads(lmp["PreselectingDataSources"])),
                        set(aadss[mg3]))

                    self.assertEqual(
                        set(json.loads(lmp["UnplottedComponents"])),
                        mylhe)
                    self.assertEqual(json.loads(lmp["OrderedChannels"]),
                                     pdss[mg3])
                    self.myAssertDict(json.loads(lmp["UserData"]),
                                      records[mg3])
                    self.assertEqual(json.loads(lmp["Timer"])[0],
                                     ltimers[mg3][0])
                    self.assertEqual(set(json.loads(lmp["Timer"])),
                                     set(ltimers[mg3]))
                    self.assertEqual(lmp["MntGrp"], mg3)

                    # try switch to unnamed active profile
                    # and then to selector mg3

#                    self.assertTrue(lrs.isMntGrpUpdated())
#                    self.assertTrue(lrs.isMntGrpUpdated())
                    wmg = ""
                    lrs.mntGrp = mg3
                    MSUtils.usetEnv('ActiveMntGrp', self._ms.ms.keys()[0])
                    lrs.switchProfile()

                    ors.profileConfiguration = str(json.dumps(mp[mg1]))
                    tmpcf1 = json.loads(ors.mntGrpConfiguration())
                    ors.profileConfiguration = str(json.dumps(mp[mg2]))
                    tmpcf2 = json.loads(ors.mntGrpConfiguration())
                    ors.profileConfiguration = str(json.dumps(mp[mg3]))
                    tmpcf3 = json.loads(ors.mntGrpConfiguration())
                    ltmpcf = json.loads(lrs.mntGrpConfiguration())
                    self.myAssertDict(tmpcf3, ltmpcf)
#                    self.myAssertDict(tmpcf1, ltmpcf)
#                    self.myAssertDict(tmpcf2, ltmpcf)

                    self.compareToDumpJSON(
                        lrs,
                        [
                            "DataSourceSelection",
                            "UnplottedComponents",
                            "PreselectingDataSources",
                            "Timer"],
                        name=mg3)
                    lmp = json.loads(lrs.profileConfiguration)
                    self.myAssertDict(json.loads(lmp["DataSourceSelection"]),
                                      adss[mg3])
                    self.assertEqual(
                        set(json.loads(lmp["PreselectingDataSources"])),
                        set(aadss[mg3]))

                    self.assertEqual(
                        set(json.loads(lmp["UnplottedComponents"])),
                        mylhe)
                    self.assertEqual(json.loads(lmp["OrderedChannels"]),
                                     pdss[mg3])
                    self.myAssertDict(json.loads(lmp["UserData"]),
                                      records[mg3])
                    self.assertEqual(json.loads(lmp["Timer"])[0],
                                     ltimers[mg3][0])
                    self.assertEqual(set(json.loads(lmp["Timer"])),
                                     set(ltimers[mg3]))
                    self.assertEqual(lmp["MntGrp"], mg3)

                    # fetch non-existing mg
                    wmg = "wrong_mg2"
                    lrs.mntGrp = wmg
                    lrs.fetchProfile()

                    ors.profileConfiguration = str(json.dumps(mp[mg1]))
                    tmpcf1 = json.loads(ors.mntGrpConfiguration())
                    ors.profileConfiguration = str(json.dumps(mp[mg2]))
                    tmpcf2 = json.loads(ors.mntGrpConfiguration())
                    ors.profileConfiguration = str(json.dumps(mp[mg3]))
                    tmpcf3 = json.loads(ors.mntGrpConfiguration())
                    ltmpcf = json.loads(lrs.mntGrpConfiguration())
#                    self.myAssertDict(tmpcf3, ltmpcf)
#                    self.myAssertDict(tmpcf1, ltmpcf)
#                    self.myAssertDict(tmpcf2, ltmpcf)

                    self.compareToDumpJSON(
                        lrs,
                        [
                            "DataSourceSelection",
                            "UnplottedComponents",
                            "PreselectingDataSources",
                            "Timer", "MntGrp"],
                        name=mg3)
                    lmp = json.loads(lrs.profileConfiguration)
                    self.myAssertDict(json.loads(lmp["DataSourceSelection"]),
                                      adss[mg3])
                    self.assertEqual(
                        set(json.loads(lmp["PreselectingDataSources"])),
                        set(aadss[mg3]))

                    self.assertEqual(
                        set(json.loads(lmp["UnplottedComponents"])),
                        mylhe)
                    self.assertEqual(json.loads(lmp["OrderedChannels"]),
                                     pdss[mg3])
                    self.myAssertDict(json.loads(lmp["UserData"]),
                                      records[mg3])
                    self.assertEqual(json.loads(lmp["Timer"])[0],
                                     ltimers[mg3][0])
                    self.assertEqual(set(json.loads(lmp["Timer"])),
                                     set(ltimers[mg3]))
                    self.assertEqual(lmp["MntGrp"], wmg)

                    # fetch non-existing selection
                    self._cf.dp.deleteSelection(mg4)
                    lrs.mntGrp = mg4
                    self.assertTrue(
                        mg4 not in self._cf.dp.availableSelections())
                    self.assertTrue(mg4 in lrs.availableMntGrps())
                    if j % 2:
                        lrs.defaultPreselectedComponents = \
                            list(json.loads(lmp["ComponentPreselection"]
                                            ).keys())

                    lrs.fetchProfile()
                    ors.profileConfiguration = str(json.dumps(mp[mg1]))
                    tmpcf1 = json.loads(ors.mntGrpConfiguration())
                    ors.profileConfiguration = str(json.dumps(mp[mg2]))
                    tmpcf2 = json.loads(ors.mntGrpConfiguration())
                    ors.profileConfiguration = str(json.dumps(mp[mg3]))
                    tmpcf3 = json.loads(ors.mntGrpConfiguration())
                    ors.profileConfiguration = str(json.dumps(mp[mg4]))
                    tmpcf4 = json.loads(ors.mntGrpConfiguration())
                    ltmpcf = json.loads(lrs.mntGrpConfiguration())
                    self.myAssertDict(tmpcf4, ltmpcf)
#                    self.myAssertDict(tmpcf3, ltmpcf)
#                    self.myAssertDict(tmpcf1, ltmpcf)
#                    self.myAssertDict(tmpcf2, ltmpcf)

                    self.compareToDumpJSON(
                        lrs,
                        [
                            "DataSourcePreselection",
                            "PreselectingDataSources",
                            "ComponentPreselection",
                            "Timer",
                            "MntGrp",

                            "ComponentSelection",
                            "DataSourceSelection",
                            "UnplottedComponents",
                        ],
                        name=mg3)
                    lmp = json.loads(lrs.profileConfiguration)
                    self.assertEqual(
                        set(json.loads(lmp["PreselectingDataSources"])),
                        set(aadss[mg3]))
                    self.assertEqual(
                        set(json.loads(lmp["DataSourcePreselection"])),
                        set())

                    if j % 2:

                        cpgood = self.smycps.keys() + self.smycps2.keys()
                        if "client_long" in aadss[mg3] \
                                or "client_short" in aadss[mg3]:
                            cpgood.remove("smycpnt1")
                        if "client2_long" in aadss[mg3] \
                                or "client2_short" in aadss[mg3]:
                            cpgood.remove("s2mycpnt1")

                        myacps = dict(acps[mg3])
                        for cp in myacps.keys():
                            myacps[cp] = cp in cpgood
                        self.myAssertDict(
                            json.loads(lmp["ComponentPreselection"]),
                            myacps)
                    else:
                        self.myAssertDict(
                            json.loads(lmp["ComponentPreselection"]),
                            {})

                    mycps = dict(cps[mg3])
                    for cp in mycps:
                        mycps[cp] = False
                    self.myAssertDict(
                        json.loads(lmp["ComponentSelection"]), mycps)

                    self.assertEqual(json.loads(lmp["OrderedChannels"]),
                                     pdss[mg3])
                    self.myAssertDict(json.loads(lmp["UserData"]),
                                      records[mg3])
                    self.assertEqual(json.loads(lmp["Timer"])[0],
                                     ltimers[mg4][0])
                    self.assertEqual(set(json.loads(lmp["Timer"])),
                                     set(ltimers[mg4]))
                    self.assertEqual(lmp["MntGrp"], mg4)

                    ladss = {}
                    for ds, vl in adss[mg3].items():
                        ladss[ds] = False

                    for ds, vl in adss[mg4].items():
                        if vl:
                            if ds in self.smychs.keys() and \
                                    self.smychs[ds]:
                                ladss[ds] = vl
                            elif ds in self.smychsXX.keys() and \
                                    self.smychsXX[ds]:
                                ladss[ds] = vl
                            if ds not in self.smychs.keys() and \
                                    ds not in self.smychsXX.keys():
                                ladss[ds] = vl
                        elif ds in adss[mg3].keys():
                            if ds in self.smychsXX.keys() \
                                    and self.smychsXX[ds]:
                                ladss[ds] = vl
                            else:
                                ladss[ds] = vl

                    llhe = set()

                    for ds in json.loads(mp[mg3]["UnplottedComponents"]):
                        if ds not in self.smychsXX.keys():
                            llhe.add(ds)

                    for ds in ladss.keys():
                        if ds in lhe2[mg4]:
                            llhe.add(ds)

                    for tm in json.loads(mp[mg4]["Timer"]):
                        if tm in ladss:
                            if tm in llhe:
                                ladss[tm] = False
                                llhe.remove(tm)
                    for tm in json.loads(mp[mg3]["Timer"]):
                        if tm in ladss:
                            if tm in json.loads(
                                    mp[mg4]["UnplottedComponents"]):
                                ladss[tm] = False
                                if tm not in json.loads(mp[mg4]["Timer"]):
                                    if tm in llhe:
                                        llhe.remove(tm)

                    for ds in self.smychs.keys():
                        if ds in llhe:
                            if ds in lhe2[mg3] and ds not in lhe2[mg4]:
                                if ds in ladss and ladss[ds]:
                                    llhe.remove(ds)

                    self.myAssertDict(json.loads(lmp["DataSourceSelection"]),
                                      ladss)

                    self.assertEqual(
                        set(json.loads(lmp["UnplottedComponents"])),
                        llhe)

                finally:
                    for mg in mp.keys():
                        try:
                            ors.deleteProfile(mgs[mg])
                        except:
                            pass
                    for mg in tmg.keys():
                        try:
                            tmg[mg].tearDown()
                        except:
                            pass
                    simp2.tearDown()
                    try:
                        self.tearDown()
                        self.myTearDown()
                    except:
                        pass
        finally:
            try:
                self.setUp()
            except:
                pass

    # constructor test
    # \brief It tests default settings
    def test_dataSourceDescription(self):
        fun = sys._getframe().f_code.co_name
        print "Run: %s.%s() " % (self.__class__.__name__, fun)
        dsdict = {
            "ann": self.mydss["ann"]
        }

        val = {"ConfigDevice": self._cf.dp.name(),
               "WriterDevice": self._wr.dp.name(),
               "Door": 'doortestp09/testts/t1r228',
               "MntGrp": 'nxsmntgrp'}
        rs = self.openRecSelector()
        rs.configDevice = val["ConfigDevice"]
        rs.door = val["Door"]
        rs.mntGrp = val["MntGrp"]
        self._cf.dp.SetCommandVariable(["DSDICT", json.dumps(dsdict)])

        self.assertEqual(rs.dataSourceDescription(["myds2"]), [])

        res = rs.dataSourceDescription(["ann"])
        self.checkDSList(res, ["ann"])

    # constructor test
    # \brief It tests default settings
    def test_dataSourceDescription_noargs(self):
        fun = sys._getframe().f_code.co_name
        print "Run: %s.%s() " % (self.__class__.__name__, fun)
        val = {"ConfigDevice": self._cf.dp.name(),
               "WriterDevice": self._wr.dp.name(),
               "Door": 'doortestp09/testts/t1r228',
               "MntGrp": 'nxsmntgrp'}
        rs = self.openRecSelector()
        rs.configDevice = val["ConfigDevice"]
        rs.door = val["Door"]
        rs.mntGrp = val["MntGrp"]
        self._cf.dp.SetCommandVariable(["DSDICT", json.dumps(self.mydss)])

        if isinstance(rs, Settings):
            res = rs.dataSourceDescription(None)
            self.checkDSList(res, self.resdss.keys())
        res = rs.dataSourceDescription(self.mydss.keys())
        self.checkDSList(res, self.resdss.keys())

    # constructor test
    # \brief It tests default settings
    def test_dataSourceDescription_names(self):
        fun = sys._getframe().f_code.co_name
        print "Run: %s.%s() " % (self.__class__.__name__, fun)

        val = {"ConfigDevice": self._cf.dp.name(),
               "WriterDevice": self._wr.dp.name(),
               "Door": 'doortestp09/testts/t1r228',
               "MntGrp": 'nxsmntgrp'}
        rs = self.openRecSelector()
        rs.configDevice = val["ConfigDevice"]
        rs.door = val["Door"]
        rs.mntGrp = val["MntGrp"]
        self._cf.dp.SetCommandVariable(["DSDICT", json.dumps(self.mydss)])

        names_list = [
            [],
            ["ann3"],
            ["ann", "nn2", "tann0", "dbtest", "slt1vgap"],
            ['nn', 'nn2', 'ann', 'ann2', 'ann3', 'ann4', 'ann5',
             'tann0', 'tann1', 'tann1b', 'tann1c', 'P1M_postrun',
             'dbtest', 'dbds', 'slt1vgap']
        ]

        for names in names_list:
            res = rs.dataSourceDescription(names)
            self.checkDSList(res, names)

    # constructor test
    # \brief It tests default settings
    def test_componentClientSources_unknown(self):
        fun = sys._getframe().f_code.co_name
        print "Run: %s.%s() " % (self.__class__.__name__, fun)
        dsdict = {
            "ann": self.mydss["ann"]
        }
        val = {"ConfigDevice": self._cf.dp.name(),
               "WriterDevice": self._wr.dp.name(),
               "Door": 'doortestp09/testts/t1r228',
               "MntGrp": 'nxsmntgrp'}
        rs = self.openRecSelector()
        rs.configDevice = val["ConfigDevice"]
        rs.door = val["Door"]
        rs.mntGrp = val["MntGrp"]
        self._cf.dp.SetCommandVariable(["DSDICT", json.dumps(dsdict)])

        self.assertEqual(rs.componentClientSources([]), '[]')
        self.assertEqual(rs.componentClientSources(["unknown"]), '[]')

        self.assertEqual(rs.componentClientSources([]), '[]')
        self.assertEqual(rs.componentClientSources(["unknown"]), '[]')
        if isinstance(rs, Settings):
            self.assertEqual(rs.componentClientSources(None), '[]')
            self.assertEqual(rs.componentClientSources(["unknown"]), '[]')

            self.assertEqual(rs.componentClientSources(None), '[]')
            self.assertEqual(rs.componentClientSources(["unknown"]), '[]')

    # constructor test
    # \brief It tests default settings
    def test_componentClientSources_dstype(self):
        val = {"ConfigDevice": self._cf.dp.name(),
               "WriterDevice": self._wr.dp.name(),
               "Door": 'doortestp09/testts/t1r228',
               "MntGrp": 'nxsmntgrp'}
        rs = self.openRecSelector()
        rs.configDevice = val["ConfigDevice"]
        rs.door = val["Door"]
        rs.mntGrp = val["MntGrp"]
        self._cf.dp.SetCommandVariable(["DSDICT", json.dumps(self.mydss)])
        self._cf.dp.SetCommandVariable(["CPDICT", json.dumps(self.mycps)])

        for cp in self.mycps.keys():
            res = json.loads(rs.componentClientSources([cp]))
            self.checkICP(res, [cp],
                          strategy=None, dstype='CLIENT')
        res = json.loads(rs.componentClientSources(self.mycps.keys()))
        self.checkICP(res, self.rescps.keys(),
                      strategy=None, dstype='CLIENT')

    # constructor test
    # \brief It tests default settings
    def test_componentClientSources_mem(self):
        val = {"ConfigDevice": self._cf.dp.name(),
               "WriterDevice": self._wr.dp.name(),
               "Door": 'doortestp09/testts/t1r228',
               "MntGrp": 'nxsmntgrp'}
        rs = self.openRecSelector()
        rs.configDevice = val["ConfigDevice"]
        rs.door = val["Door"]
        rs.mntGrp = val["MntGrp"]
        for i in range(20):
            self._cf.dp.SetCommandVariable(["DSDICT", json.dumps(self.mydss)])
            self._cf.dp.SetCommandVariable(["CPDICT", json.dumps(self.mycps)])
            nmem = self._rnd.randint(1, len(self.mycps.keys()) - 1)
            mem = self._rnd.sample(set(self.mycps.keys()), nmem)
            self._cf.dp.SetCommandVariable(["MCPLIST", json.dumps(mem)])

            for cp in self.mycps.keys():
                res = json.loads(rs.componentClientSources([cp]))
                self.checkICP(res, [cp],
                              strategy=None, dstype='CLIENT')
            res = json.loads(rs.componentClientSources(self.mycps.keys()))
            self.checkICP(res, self.rescps.keys(),
                          strategy=None, dstype='CLIENT')

    # constructor test
    # \brief It tests default settings
    def test_componentClientSources_cps(self):
        val = {"ConfigDevice": self._cf.dp.name(),
               "WriterDevice": self._wr.dp.name(),
               "Door": 'doortestp09/testts/t1r228',
               "MntGrp": 'nxsmntgrp'}
        rs = self.openRecSelector()
        rs.configDevice = val["ConfigDevice"]
        rs.door = val["Door"]
        rs.mntGrp = val["MntGrp"]
        for i in range(20):
            self._cf.dp.SetCommandVariable(["DSDICT", json.dumps(self.mydss)])
            self._cf.dp.SetCommandVariable(["CPDICT", json.dumps(self.mycps)])
            nmem = self._rnd.randint(1, len(self.mycps.keys()) - 1)
            mem = self._rnd.sample(set(self.mycps.keys()), nmem)

            res = json.loads(rs.componentClientSources(mem))
            self.checkICP(res, mem,
                          strategy=None, dstype='CLIENT')

    # constructor test
    # \brief It tests default settings
    def test_componentClientSources_components(self):
        val = {"ConfigDevice": self._cf.dp.name(),
               "WriterDevice": self._wr.dp.name(),
               "Door": 'doortestp09/testts/t1r228',
               "MntGrp": 'nxsmntgrp'}
        rs = self.openRecSelector()
        rs.configDevice = val["ConfigDevice"]
        rs.door = val["Door"]
        rs.mntGrp = val["MntGrp"]
        for i in range(100):
            self._cf.dp.SetCommandVariable(["DSDICT", json.dumps(self.mydss)])
            self._cf.dp.SetCommandVariable(["CPDICT", json.dumps(self.mycps)])
            nmem = self._rnd.randint(1, len(self.mycps.keys()) - 1)
            mem = self._rnd.sample(set(self.mycps.keys()), nmem)
            self._cf.dp.SetCommandVariable(["MCPLIST", json.dumps(mem)])

            nccp = self._rnd.randint(1, len(self.mycps.keys()) - 1)
            ccp = self._rnd.sample(set(self.mycps.keys()), nccp)
            cps = {}
            for cp in ccp:
                cps[cp] = bool(self._rnd.randint(0, 1))

            nacp = self._rnd.randint(1, len(self.mycps.keys()) - 1)
            acp = self._rnd.sample(set(self.mycps.keys()), nacp)
            acps = {}
            for cp in acp:
                acps[cp] = bool(self._rnd.randint(0, 1))

            cnf = json.loads(rs.profileConfiguration)
            cnf["ComponentPreselection"] = json.dumps(acps)
            cnf["ComponentSelection"] = json.dumps(cps)
            rs.profileConfiguration = json.dumps(cnf)
            # print "CPS", rs.components

            res = json.loads(rs.componentClientSources([]))
            self.checkICP(res, rs.components,
                          strategy=None, dstype='CLIENT')

    # constructor test
    # \brief It tests default settings
    def test_componentClientSources_components_var(self):
        val = {"ConfigDevice": self._cf.dp.name(),
               "WriterDevice": self._wr.dp.name(),
               "Door": 'doortestp09/testts/t1r228',
               "MntGrp": 'nxsmntgrp'}
        rs = self.openRecSelector()
        rs.configDevice = val["ConfigDevice"]
        rs.door = val["Door"]
        rs.mntGrp = val["MntGrp"]
        for i in range(100):
            self._cf.dp.SetCommandVariable(
                ["DSDICT", json.dumps(self.mydss)])
            self._cf.dp.SetCommandVariable(
                ["CPDICT", json.dumps(self.mycpsvar)])
            nmem = self._rnd.randint(1, len(self.mycpsvar.keys()) - 1)
            mem = self._rnd.sample(set(self.mycpsvar.keys()), nmem)
            self._cf.dp.SetCommandVariable(["MCPLIST", json.dumps(mem)])

            nccp = self._rnd.randint(1, len(self.mycpsvar.keys()) - 1)
            ccp = self._rnd.sample(set(self.mycpsvar.keys()), nccp)
            cps = {}
            for cp in ccp:
                cps[cp] = bool(self._rnd.randint(0, 1))
            rs.configVariables = '{"c01": "exp_c01", "c02": "exp_c02", ' + \
                                 '"mca": "p09/mca/exp.02"}'
            self._cf.dp.SetCommandVariable(["CHECKVARIABLES",
                                            json.dumps(rs.configVariables)])
            nacp = self._rnd.randint(1, len(self.mycpsvar.keys()) - 1)
            acp = self._rnd.sample(set(self.mycpsvar.keys()), nacp)
            acps = {}
            for cp in acp:
                acps[cp] = bool(self._rnd.randint(0, 1))

            cnf = json.loads(rs.profileConfiguration)
            cnf["ComponentPreselection"] = json.dumps(acps)
            cnf["ComponentSelection"] = json.dumps(cps)
            rs.profileConfiguration = json.dumps(cnf)
#            print "CPS", rs.components

            res = rs.componentClientSources([])
            res = json.loads(
                res.replace(
                    "$var.c01", "exp_c01").replace(
                        "$var.c02", "exp_c02").replace(
                            "$var.mca", "p09/mca/exp.02"))
            self.checkICP(res, rs.components,
                          strategy=None, dstype='CLIENT')

    # constructor test
    # \brief It tests default settings
    def test_componentSources_unknown(self):
        fun = sys._getframe().f_code.co_name
        print "Run: %s.%s() " % (self.__class__.__name__, fun)
        dsdict = {
            "ann": self.mydss["ann"]
        }
        val = {"ConfigDevice": self._cf.dp.name(),
               "WriterDevice": self._wr.dp.name(),
               "Door": 'doortestp09/testts/t1r228',
               "MntGrp": 'nxsmntgrp'}
        rs = self.openRecSelector()
        rs.configDevice = val["ConfigDevice"]
        rs.door = val["Door"]
        rs.mntGrp = val["MntGrp"]
        self._cf.dp.SetCommandVariable(["DSDICT", json.dumps(dsdict)])

        self.assertEqual(rs.componentSources([]), '[]')
        self.assertEqual(rs.componentSources(["unknown"]), '[]')

        self.assertEqual(rs.componentSources([]), '[]')
        self.assertEqual(rs.componentSources(["unknown"]), '[]')
        if isinstance(rs, Settings):
            self.assertEqual(rs.componentSources(None), '[]')
            self.assertEqual(rs.componentSources(["unknown"]), '[]')

            self.assertEqual(rs.componentSources(None), '[]')
            self.assertEqual(rs.componentSources(["unknown"]), '[]')

    # constructor test
    # \brief It tests default settings
    def test_componentSources_dstype(self):
        val = {"ConfigDevice": self._cf.dp.name(),
               "WriterDevice": self._wr.dp.name(),
               "Door": 'doortestp09/testts/t1r228',
               "MntGrp": 'nxsmntgrp'}
        rs = self.openRecSelector()
        rs.configDevice = val["ConfigDevice"]
        rs.door = val["Door"]
        rs.mntGrp = val["MntGrp"]
        self._cf.dp.SetCommandVariable(["DSDICT", json.dumps(self.mydss)])
        self._cf.dp.SetCommandVariable(["CPDICT", json.dumps(self.mycps)])

        for cp in self.mycps.keys():
            res = json.loads(rs.componentSources([cp]))
            self.checkICP(res, [cp],
                          strategy=None, dstype=None)
        res = json.loads(rs.componentSources(self.mycps.keys()))
        self.checkICP(res, self.rescps.keys(),
                      strategy=None, dstype=None)

    # constructor test
    # \brief It tests default settings
    def test_componentSources_mem(self):
        val = {"ConfigDevice": self._cf.dp.name(),
               "WriterDevice": self._wr.dp.name(),
               "Door": 'doortestp09/testts/t1r228',
               "MntGrp": 'nxsmntgrp'}
        rs = self.openRecSelector()
        rs.configDevice = val["ConfigDevice"]
        rs.door = val["Door"]
        rs.mntGrp = val["MntGrp"]
        for i in range(20):
            self._cf.dp.SetCommandVariable(["DSDICT", json.dumps(self.mydss)])
            self._cf.dp.SetCommandVariable(["CPDICT", json.dumps(self.mycps)])
            nmem = self._rnd.randint(1, len(self.mycps.keys()) - 1)
            mem = self._rnd.sample(set(self.mycps.keys()), nmem)
            self._cf.dp.SetCommandVariable(["MCPLIST", json.dumps(mem)])

            for cp in self.mycps.keys():
                res = json.loads(rs.componentSources([cp]))
                self.checkICP(res, [cp],
                              strategy=None)
            res = json.loads(rs.componentSources(self.mycps.keys()))
            self.checkICP(res, self.rescps.keys(),
                          strategy=None)

    # constructor test
    # \brief It tests default settings
    def test_componentSources_cps(self):
        val = {"ConfigDevice": self._cf.dp.name(),
               "WriterDevice": self._wr.dp.name(),
               "Door": 'doortestp09/testts/t1r228',
               "MntGrp": 'nxsmntgrp'}
        rs = self.openRecSelector()
        rs.configDevice = val["ConfigDevice"]
        rs.door = val["Door"]
        rs.mntGrp = val["MntGrp"]
        for i in range(20):
            self._cf.dp.SetCommandVariable(["DSDICT", json.dumps(self.mydss)])
            self._cf.dp.SetCommandVariable(["CPDICT", json.dumps(self.mycps)])
            nmem = self._rnd.randint(1, len(self.mycps.keys()) - 1)
            mem = self._rnd.sample(set(self.mycps.keys()), nmem)

            res = json.loads(rs.componentSources(mem))
            self.checkICP(res, mem,
                          strategy=None)

    # constructor test
    # \brief It tests default settings
    def test_componentSources_components(self):
        val = {"ConfigDevice": self._cf.dp.name(),
               "WriterDevice": self._wr.dp.name(),
               "Door": 'doortestp09/testts/t1r228',
               "MntGrp": 'nxsmntgrp'}
        rs = self.openRecSelector()
        rs.configDevice = val["ConfigDevice"]
        rs.door = val["Door"]
        rs.mntGrp = val["MntGrp"]
        for i in range(100):
            self._cf.dp.SetCommandVariable(["DSDICT", json.dumps(self.mydss)])
            self._cf.dp.SetCommandVariable(["CPDICT", json.dumps(self.mycps)])
            nmem = self._rnd.randint(1, len(self.mycps.keys()) - 1)
            mem = self._rnd.sample(set(self.mycps.keys()), nmem)
            self._cf.dp.SetCommandVariable(["MCPLIST", json.dumps(mem)])

            nccp = self._rnd.randint(1, len(self.mycps.keys()) - 1)
            ccp = self._rnd.sample(set(self.mycps.keys()), nccp)
            cps = {}
            for cp in ccp:
                cps[cp] = bool(self._rnd.randint(0, 1))

            nacp = self._rnd.randint(1, len(self.mycps.keys()) - 1)
            acp = self._rnd.sample(set(self.mycps.keys()), nacp)
            acps = {}
            for cp in acp:
                acps[cp] = bool(self._rnd.randint(0, 1))

            cnf = json.loads(rs.profileConfiguration)
            cnf["ComponentPreselection"] = json.dumps(acps)
            cnf["ComponentSelection"] = json.dumps(cps)
            rs.profileConfiguration = json.dumps(cnf)
            # print "CPS", rs.components

            res = json.loads(rs.componentSources([]))
            self.checkICP(res, rs.components,
                          strategy=None)

    # constructor test
    # \brief It tests default settings
    def test_componentSources_components_var(self):
        val = {"ConfigDevice": self._cf.dp.name(),
               "WriterDevice": self._wr.dp.name(),
               "Door": 'doortestp09/testts/t1r228',
               "MntGrp": 'nxsmntgrp'}
        rs = self.openRecSelector()
        rs.configDevice = val["ConfigDevice"]
        rs.door = val["Door"]
        rs.mntGrp = val["MntGrp"]
        for i in range(100):
            self._cf.dp.SetCommandVariable(
                ["DSDICT", json.dumps(self.mydss)])
            self._cf.dp.SetCommandVariable(
                ["CPDICT", json.dumps(self.mycpsvar)])
            nmem = self._rnd.randint(1, len(self.mycpsvar.keys()) - 1)
            mem = self._rnd.sample(set(self.mycpsvar.keys()), nmem)
            self._cf.dp.SetCommandVariable(["MCPLIST", json.dumps(mem)])

            nccp = self._rnd.randint(1, len(self.mycpsvar.keys()) - 1)
            ccp = self._rnd.sample(set(self.mycpsvar.keys()), nccp)
            cps = {}
            for cp in ccp:
                cps[cp] = bool(self._rnd.randint(0, 1))
            rs.configVariables = '{"c01": "exp_c01", "c02": "exp_c02", ' + \
                                 '"mca": "p09/mca/exp.02"}'
            self._cf.dp.SetCommandVariable(["CHECKVARIABLES",
                                            json.dumps(rs.configVariables)])
            nacp = self._rnd.randint(1, len(self.mycpsvar.keys()) - 1)
            acp = self._rnd.sample(set(self.mycpsvar.keys()), nacp)
            acps = {}
            for cp in acp:
                acps[cp] = bool(self._rnd.randint(0, 1))

            cnf = json.loads(rs.profileConfiguration)
            cnf["ComponentPreselection"] = json.dumps(acps)
            cnf["ComponentSelection"] = json.dumps(cps)
            rs.profileConfiguration = json.dumps(cnf)
#            print "CPS", rs.components

            res = rs.componentSources([])
            res = json.loads(
                res.replace(
                    "$var.c01", "exp_c01").replace(
                        "$var.c02", "exp_c02").replace(
                            "$var.mca", "p09/mca/exp.02"))
            self.checkICP(res, rs.components,
                          strategy=None)

    # constructor test
    # \brief It tests default settings
    def test_create_remove_DynamicComponent(self):
        fun = sys._getframe().f_code.co_name
        print "Run: %s.%s() " % (self.__class__.__name__, fun)
        val = {"ConfigDevice": self._cf.dp.name(),
               "WriterDevice": self._wr.dp.name(),
               "Door": 'doortestp09/testts/t1r228',
               "MntGrp": 'nxsmntgrp'}
        rs = self.openRecSelector()
        rs.configDevice = val["ConfigDevice"]
        rs.door = val["Door"]
        rs.mntGrp = val["MntGrp"]

        cps = {"empty":
               '<?xml version="1.0" ?>\n<definition/>\n'}
        dname = "__dynamic_component__"

        cpname = rs.createDynamicComponent([])
        self.assertEqual(cpname, dname)
        self._cf.dp.Components([cpname])
        self.assertEqual(cps["empty"], self._cf.dp.Components([cpname])[0])

        cpname = rs.createDynamicComponent([])
        self.assertEqual(cpname, dname + "x")
        self._cf.dp.Components([cpname])
        self.assertEqual(cps["empty"], self._cf.dp.Components([cpname])[0])

        cpname = rs.createDynamicComponent([])
        self.assertEqual(cpname, dname + "xx")
        self._cf.dp.Components([cpname])
        self.assertEqual(cps["empty"], self._cf.dp.Components([cpname])[0])

        cpname = rs.createDynamicComponent([])
        self.assertEqual(cpname, dname + "xxx")
        self._cf.dp.Components([cpname])
        self.assertEqual(cps["empty"], self._cf.dp.Components([cpname])[0])

        rs.removeDynamicComponent(dname + "xx")
        self.assertEqual(self._cf.dp.Components([dname + "xx"]), [])

        cpname = rs.createDynamicComponent([])
        self.assertEqual(cpname, dname + "xx")
        self._cf.dp.Components([cpname])
        self.assertEqual(cps["empty"], self._cf.dp.Components([cpname])[0])

        rs.removeDynamicComponent(dname + "x")
        self.assertEqual(self._cf.dp.Components([dname + "x"]), [])

        rs.removeDynamicComponent(dname + "xxx")
        self.assertEqual(self._cf.dp.Components([dname + "xxx"]), [])

        rs.removeDynamicComponent(dname + "xx")
        self.assertEqual(self._cf.dp.Components([dname + "xx"]), [])

        rs.removeDynamicComponent(dname + "xx")
        self.assertEqual(self._cf.dp.Components([dname + "xx"]), [])

        rs.removeDynamicComponent(dname)
        self.assertEqual(self._cf.dp.Components([dname]), [])

        self.myAssertRaise(Exception, rs.removeDynamicComponent, "sdfsdf")

    # constructor test
    # \brief It tests default settings
    def test_create_dict(self):
        fun = sys._getframe().f_code.co_name
        print "Run: %s.%s() " % (self.__class__.__name__, fun)
        val = {"ConfigDevice": self._cf.dp.name(),
               "WriterDevice": self._wr.dp.name(),
               "Door": 'doortestp09/testts/t1r228',
               "MntGrp": 'nxsmntgrp'}
        rs = self.openRecSelector()
        rs.configDevice = val["ConfigDevice"]
        rs.door = val["Door"]
        rs.mntGrp = val["MntGrp"]
        cps = {
            "empty":
                '<?xml version="1.0" ?>\n<definition/>\n',
            "one":
                '<?xml version="1.0" ?>\n<definition>\n'
            '<group name="scan$var.serialno" type="NXentry">\n'
            '<group name="instrument" type="NXinstrument">\n'
            '<group name="collection" type="NXcollection">\n'
            '<field name="onename" type="NX_CHAR">\n<strategy mode="STEP"/>\n'
            '<datasource name="onename" type="CLIENT">\n'
            '<record name="onename"/>\n</datasource>\n</field>\n'
            '</group>\n</group>\n<group name="data" type="NXdata">\n'
            '<link name="onename" target="/scan$var.serialno:'
            'NXentry/NXinstrument/collection/onename"/>\n'
            '</group>\n</group>\n</definition>\n',
            "two":
                '<?xml version="1.0" ?>\n<definition>\n'
            '<group name="scan$var.serialno" type="NXentry">\n'
            '<group name="instrument" type="NXinstrument">\n'
            '<group name="collection" type="NXcollection">\n'
            '<field name="ds1" type="NX_CHAR">\n<strategy mode="STEP"/>\n'
            '<datasource name="ds1" type="CLIENT">\n<record name="ds1"/>\n'
            '</datasource>\n</field>\n</group>\n</group>\n'
            '<group name="data" type="NXdata">\n'
            '<link name="ds1" target="/scan$var.serialno:'
            'NXentry/NXinstrument/collection/ds1"/>\n</group>\n</group>\n'
            '<group name="scan$var.serialno" type="NXentry">'
            '\n<group name="instrument" type="NXinstrument">\n'
            '<group name="collection" type="NXcollection">\n'
            '<field name="ds2" type="NX_CHAR">\n<strategy mode="STEP"/>\n'
            '<datasource name="ds2" type="CLIENT">\n<record name="ds2"/>\n'
            '</datasource>\n</field>\n</group>\n</group>\n'
            '<group name="data" type="NXdata">\n'
            '<link name="ds2" target="/scan$var.serialno:'
            'NXentry/NXinstrument/collection/ds2"/>\n</group>\n'
            '</group>\n</definition>\n',
            "three":
                '<?xml version="1.0" ?>\n<definition>\n'
            '<group name="scan$var.serialno" type="NXentry">\n'
            '<group name="instrument" type="NXinstrument">\n'
            '<group name="collection" type="NXcollection">\n'
            '<field name="ds1" type="NX_CHAR">\n<strategy mode="STEP"/>\n'
            '<datasource name="ds1" type="CLIENT">\n<record name="ds1"/>\n'
            '</datasource>\n</field>\n</group>\n</group>\n'
            '<group name="data" type="NXdata">\n'
            '<link name="ds1" target="/scan$var.serialno:'
            'NXentry/NXinstrument/collection/ds1"/>\n</group>\n</group>\n'
            '<group name="scan$var.serialno" type="NXentry">'
            '\n<group name="instrument" type="NXinstrument">\n'
            '<group name="collection" type="NXcollection">\n'
            '<field name="ds2" type="NX_CHAR">\n<strategy mode="STEP"/>\n'
            '<datasource name="ds2" type="CLIENT">\n<record name="ds2"/>\n'
            '</datasource>\n</field>\n</group>\n</group>\n'
            '<group name="data" type="NXdata">\n'
            '<link name="ds2" target="/scan$var.serialno:'
            'NXentry/NXinstrument/collection/ds2"/>\n</group>\n</group>\n'
            '<group name="scan$var.serialno" type="NXentry">'
            '\n<group name="instrument" type="NXinstrument">\n'
            '<group name="collection" type="NXcollection">\n'
            '<field name="ds3" type="NX_CHAR">\n<strategy mode="STEP"/>\n'
            '<datasource name="ds3" type="CLIENT">\n<record name="ds3"/>\n'
            '</datasource>\n</field>\n</group>\n</group>\n'
            '<group name="data" type="NXdata">\n'
            '<link name="ds3" target="/scan$var.serialno:'
            'NXentry/NXinstrument/collection/ds3"/>\n</group>\n</group>\n'
            '</definition>\n',
            "type":
                '<?xml version="1.0" ?>\n<definition>\n'
            '<group name="scan$var.serialno" type="NXentry">\n'
            '<group name="instrument" type="NXinstrument">\n'
            '<group name="collection" type="NXcollection">\n'
            '<field name="ds1" type="NX_INT">\n<strategy mode="STEP"/>\n'
            '<datasource name="ds1" type="CLIENT">\n'
            '<record name="ds1"/>\n</datasource>\n</field>\n'
            '</group>\n</group>\n<group name="data" type="NXdata">\n'
            '<link name="ds1" target="/scan$var.serialno:'
            'NXentry/NXinstrument/collection/ds1"/>\n'
            '</group>\n</group>\n</definition>\n',
            "shape":
                '<?xml version="1.0" ?>\n<definition>\n'
            '<group name="scan$var.serialno" type="NXentry">\n'
            '<group name="instrument" type="NXinstrument">\n'
            '<group name="collection" type="NXcollection">\n'
            '<field name="ds2" type="NX_CHAR">\n<strategy mode="STEP"/>\n'
            '<datasource name="ds2" type="CLIENT">\n'
            '<record name="ds2"/>\n</datasource>\n'
            '<dimensions rank="1">\n<dim index="1" value="34"/>\n'
            '</dimensions>\n</field>\n'
            '</group>\n</group>\n<group name="data" type="NXdata">\n'
            '<link name="ds2" target="/scan$var.serialno:'
            'NXentry/NXinstrument/collection/ds2"/>\n'
            '</group>\n</group>\n</definition>\n',
            "shapetype":
                '<?xml version="1.0" ?>\n<definition>\n'
            '<group name="scan$var.serialno" type="NXentry">\n'
            '<group name="instrument" type="NXinstrument">\n'
            '<group name="collection" type="NXcollection">\n'
            '<field name="ds3" type="NX_FLOAT64">\n<strategy mode="STEP"/>\n'
            '<datasource name="ds3" type="CLIENT">\n'
            '<record name="ds3"/>\n</datasource>\n'
            '<dimensions rank="2">\n<dim index="1" value="3"/>\n'
            '<dim index="2" value="56"/>\n</dimensions>\n</field>\n'
            '</group>\n</group>\n<group name="data" type="NXdata">\n'
            '<link name="ds3" target="/scan$var.serialno:'
            'NXentry/NXinstrument/collection/ds3"/>\n'
            '</group>\n</group>\n</definition>\n',
        }
        dsdict = {
            "empty": [],
            "one": [{"name": "onename"}],
            "two": [{"name": "ds1"}, {"name": "ds2"}],
            "three": [{"name": "ds1"}, {"name": "ds2"}, {"name": "ds3"}],
            "type": [{"name": "ds1", "dtype": "int"}],
            "shape": [{"name": "ds2", "shape": [34]}],
            "shapetype": [{"name": "ds3", "dtype": "float64",
                           "shape": [3, 56]}],
        }
        dname = "__dynamic_component__"
        for lb, ds in dsdict.items():
#            print ds
            cpname = rs.createDynamicComponent(["", str(json.dumps(ds))])
            comp = self._cf.dp.Components([cpname])[0]
            self.assertEqual(cps[lb], comp)

    # constructor test
    # \brief It tests default settings
    def test_create_dict_type(self):
        fun = sys._getframe().f_code.co_name
        print "Run: %s.%s() " % (self.__class__.__name__, fun)
        val = {"ConfigDevice": self._cf.dp.name(),
               "WriterDevice": self._wr.dp.name(),
               "Door": 'doortestp09/testts/t1r228',
               "MntGrp": 'nxsmntgrp'}
        rs = self.openRecSelector()
        rs.configDevice = val["ConfigDevice"]
        rs.door = val["Door"]
        rs.mntGrp = val["MntGrp"]
        cps = {
            "type":
                '<?xml version="1.0" ?>\n<definition>\n'
            '<group name="scan$var.serialno" type="NXentry">\n'
            '<group name="instrument" type="NXinstrument">\n'
            '<group name="collection" type="NXcollection">\n'
            '<field name="ds1" type="%s">\n<strategy mode="STEP"/>\n'
            '<datasource name="ds1" type="CLIENT">\n'
            '<record name="ds1"/>\n</datasource>\n</field>\n'
            '</group>\n</group>\n<group name="data" type="NXdata">\n'
            '<link name="ds1" target="/scan$var.serialno:'
            'NXentry/NXinstrument/collection/ds1"/>\n'
            '</group>\n</group>\n</definition>\n',
        }
        dname = "__dynamic_component__"
        for tp, nxstp in self._npTn.items():
            cpname = rs.createDynamicComponent([
                "", str(json.dumps([{"name": "ds1", "dtype": tp}]))])
            comp = self._cf.dp.Components([cpname])[0]
            self.assertEqual(cps["type"] % nxstp, comp)

    # constructor test
    # \brief It tests default settings
    def test_create_dict_shape(self):
        fun = sys._getframe().f_code.co_name
        print "Run: %s.%s() " % (self.__class__.__name__, fun)
        val = {"ConfigDevice": self._cf.dp.name(),
               "WriterDevice": self._wr.dp.name(),
               "Door": 'doortestp09/testts/t1r228',
               "MntGrp": 'nxsmntgrp'}
        rs = self.openRecSelector()
        rs.configDevice = val["ConfigDevice"]
        rs.door = val["Door"]
        rs.mntGrp = val["MntGrp"]
        cps = {
            "shape":
                '<?xml version="1.0" ?>\n<definition>\n'
            '<group name="scan$var.serialno" type="NXentry">\n'
            '<group name="instrument" type="NXinstrument">\n'
            '<group name="collection" type="NXcollection">\n'
            '<field name="ds2" type="NX_CHAR">\n<strategy mode="STEP"/>\n'
            '<datasource name="ds2" type="CLIENT">\n'
            '<record name="ds2"/>\n</datasource>\n%s</field>\n'
            '</group>\n</group>\n<group name="data" type="NXdata">\n'
            '<link name="ds2" target="/scan$var.serialno:'
            'NXentry/NXinstrument/collection/ds2"/>\n'
            '</group>\n</group>\n</definition>\n',
        }

        dimbg = '<dimensions rank="%s">\n'
        dim = '<dim index="%s" value="%s"/>\n'
        dimend = '</dimensions>\n'

        dname = "__dynamic_component__"
        for i in range(50):
            ms = [self._rnd.randint(0, 3000)
                  for _ in range(self._rnd.randint(0, 3))]
            cpname = rs.createDynamicComponent([
                "", str(json.dumps([{"name": "ds2", "shape": ms}]))])

            mstr = ""
            if ms:
                mstr += dimbg % len(ms)
                for ind, val in enumerate(ms):
                    mstr += dim % (ind + 1, val)
                mstr += dimend

            comp = self._cf.dp.Components([cpname])[0]
            self.assertEqual(cps["shape"] % mstr, comp)

    # constructor test
    # \brief It tests default settings
    def test_create_dict_shapetype(self):
        fun = sys._getframe().f_code.co_name
        print "Run: %s.%s() " % (self.__class__.__name__, fun)
        val = {"ConfigDevice": self._cf.dp.name(),
               "WriterDevice": self._wr.dp.name(),
               "Door": 'doortestp09/testts/t1r228',
               "MntGrp": 'nxsmntgrp'}
        rs = self.openRecSelector()
        rs.configDevice = val["ConfigDevice"]
        rs.door = val["Door"]
        rs.mntGrp = val["MntGrp"]
        cnfdef = json.loads(rs.profileConfiguration)

        cps = {
            "shapetype":
                '<?xml version="1.0" ?>\n<definition>\n'
            '<group name="scan$var.serialno" type="NXentry">\n'
            '<group name="instrument" type="NXinstrument">\n'
            '<group name="collection" type="NXcollection">\n'
            '<field name="%s" type="%s">\n<strategy mode="STEP"/>\n'
            '<datasource name="%s" type="CLIENT">\n'
            '<record name="%s"/>\n</datasource>\n'
            '%s</field>\n'
            '</group>\n</group>\n%s</group>\n</definition>\n',
        }

        link = '<group name="data" type="NXdata">\n' + \
            '<link name="%s" target="/scan$var.serialno:' + \
            'NXentry/NXinstrument/collection/%s"/>\n</group>\n'

        dimbg = '<dimensions rank="%s">\n'
        dim = '<dim index="%s" value="%s"/>\n'
        dimend = '</dimensions>\n'

        dname = "__dynamic_component__"

        arr = [
            {"name": "client", "full_name": "client"},
            {"name": "client_short", "full_name": "ttestp09/testts/t1r228"},
            {"name": "client_long", "full_name": "ttestp09/testts/t2r228"},
            {"name": "myclient_long", "full_name": "ttestp09/testts/t3r228"},
            {"name": "client", "full_name": "client"},
            {"name": "client_short", "full_name": "ttestp09/testts/t1r228"},
            {"name": "client_long", "full_name": "ttestp09/testts/t2r228"},
            {"name": "myclient_long", "full_name": "ttestp09/testts/t3r228"},
            {"name": "client", "full_name": "client"},
            {"name": "client_short", "full_name": "ttestp09/testts/t1r228"},
            {"name": "client_long", "full_name": "ttestp09/testts/t2r228"},
            {"name": "myclient_long", "full_name": "ttestp09/testts/t3r228"},
        ]

        simps2 = TestServerSetUp.TestServerSetUp(
            "ttestp09/testts/t2r228", "S2")
        simps3 = TestServerSetUp.TestServerSetUp(
            "ttestp09/testts/t3r228", "S3")

        db = PyTango.Database()
        try:
            simps2.setUp()
            simps3.setUp()

            for i, ar in enumerate(arr):
                if '/' in ar["full_name"]:
                    db.put_device_alias(ar["full_name"], ar["name"])
                for tp, nxstp in self._npTn.items():
                    lbl = self.getRandomName(20)
                    ms = [self._rnd.randint(0, 3000)
                          for _ in range(self._rnd.randint(0, 3))]
                    ms2 = [self._rnd.randint(0, 3000)
                           for _ in range(self._rnd.randint(0, 3))]
                    tmptp = self._rnd.choice(self._npTn.keys())
                    cnf = dict(cnfdef)
                    labels = {}
                    paths = {}
                    links = {}
                    types = {}
                    shapes = {}

                    if i == 0:
                        cnf["DefaultDynamicLinks"] = False
                        cnf["DefaultDynamicPath"] = self._defaultpath
                    elif i == 1:
                        cnf["DefaultDynamicLinks"] = True
                        cnf["DefaultDynamicPath"] = self._defaultpath
                    elif i == 2:
                        links = {ar["name"]: False}
                    elif i == 3:
                        links = {ar["name"]: True}
                    elif i == 4:
                        cnf["DefaultDynamicLinks"] = True
                        cnf["DefaultDynamicPath"] = self._defaultpath
                        links = {ar["name"]: False}
                    elif i == 5:
                        cnf["DefaultDynamicLinks"] = False
                        cnf["DefaultDynamicPath"] = self._defaultpath
                        links = {ar["name"]: True}
                    elif i == 6:
                        cnf["DefaultDynamicLinks"] = False
                        cnf["DefaultDynamicPath"] = self._defaultpath
                        links = {ar["full_name"]: True}
                        shapes = {ar["name"]: ms2}
                    elif i == 7:
                        types = {ar["name"]: tmptp}
                    elif i == 8:
                        cnf["DefaultDynamicLinks"] = True
                        cnf["DefaultDynamicPath"] = self._defaultpath
                        labels = {ar["name"]: lbl}
                        links = {lbl: False}
                    elif i == 9:
                        cnf["DefaultDynamicLinks"] = False
                        cnf["DefaultDynamicPath"] = self._defaultpath
                        labels = {ar["name"]: lbl}
                        links = {lbl: True}
                    elif i == 10:
                        cnf["DefaultDynamicLinks"] = False
                        cnf["DefaultDynamicPath"] = self._defaultpath
                        labels = {ar["name"]: lbl}
                        links = {ar["full_name"]: True}
                        shapes = {lbl: ms2}
                    elif i == 11:
                        labels = {ar["name"]: lbl}
                        types = {lbl: tmptp}
                        shapes = {lbl: ms2}
                    cnf["ChannelProperties"] = json.dumps(
                        {
                            "label": labels,
                            "nexus_path": paths,
                            "link": links,
                            "data_type": types,
                            "shape": shapes
                        }
                    )
#                    print "I = ", i
                    rs.profileConfiguration = str(json.dumps(cnf))
                    cpname = rs.createDynamicComponent([
                        "", str(json.dumps([{"name": ar["full_name"],
                                             "shape": ms,
                                             "dtype": tp}]))])
                    mstr = ""
                    if ms:
                        mstr += dimbg % len(ms)
                        for ind, val in enumerate(ms):
                            mstr += dim % (ind + 1, val)
                        mstr += dimend

                    comp = self._cf.dp.Components([cpname])[0]
                    ds = ar["name"]
                    lk = link % (ds, ds)
                    self.assertEqual(
                        cps["shapetype"] % (
                            ds,
                            nxstp, ds, ar["full_name"], mstr,
                            lk if i % 2 else ""),
                        comp)
        finally:
            for ar in arr:
                if '/' in ar["full_name"]:
                    db.delete_device_alias(ar["name"])

            simps3.tearDown()
            simps2.tearDown()

    # constructor test
    # \brief It tests default settings
    def test_create_dict_fieldpath(self):
        fun = sys._getframe().f_code.co_name
        print "Run: %s.%s() " % (self.__class__.__name__, fun)
        val = {"ConfigDevice": self._cf.dp.name(),
               "WriterDevice": self._wr.dp.name(),
               "Door": 'doortestp09/testts/t1r228',
               "MntGrp": 'nxsmntgrp'}
        rs = self.openRecSelector()
        rs.configDevice = val["ConfigDevice"]
        rs.door = val["Door"]
        rs.mntGrp = val["MntGrp"]
        cnfdef = json.loads(rs.profileConfiguration)
        cps = {
            "shapetype":
            '<?xml version="1.0" ?>\n<definition>\n'
            '<group name="scan$var.serialno" type="NXentry">\n'
            '<group name="instrument" type="NXinstrument">\n'
            '<group name="collection" type="NXcollection">\n%s'
            '</group>\n</group>\n%s</group>\n</definition>\n',
        }

        defbg = '<?xml version="1.0" ?>\n<definition>\n'
        defend = '</definition>\n'
        groupbg = '<group name="%s" type="%s">\n'
        groupend = '</group>\n'

        field = '<field name="%s" type="%s">\n<strategy mode="STEP"/>\n' + \
            '<datasource name="%s" type="CLIENT">\n' + \
            '<record name="%s"/>\n</datasource>\n%s</field>\n'

        link = '<group name="data" type="NXdata">\n' + \
            '<link name="%s" target="%s/%s"/>\n</group>\n'

        dimbg = '<dimensions rank="%s">\n'
        dim = '<dim index="%s" value="%s"/>\n'
        dimend = '</dimensions>\n'

        dname = "__dynamic_component__"

        arr = [
            {"name": "client", "full_name": "client"},
            {"name": "client_short", "full_name": "ttestp09/testts/t1r228"},
            {"name": "client_long", "full_name": "ttestp09/testts/t2r228"},
            {"name": "myclient_long", "full_name": "ttestp09/testts/t3r228"},
            {"name": "client", "full_name": "client"},
            {"name": "client_short", "full_name": "ttestp09/testts/t1r228"},
            {"name": "client_long", "full_name": "ttestp09/testts/t2r228"},
            {"name": "myclient_long", "full_name": "ttestp09/testts/t3r228"},
        ]

        simps2 = TestServerSetUp.TestServerSetUp(
            "ttestp09/testts/t2r228", "S2")
        simps3 = TestServerSetUp.TestServerSetUp(
            "ttestp09/testts/t3r228", "S3")

        db = PyTango.Database()
        try:
            simps2.setUp()
            simps3.setUp()

            for i, ar in enumerate(arr):
                if '/' in ar["full_name"]:
                    db.put_device_alias(ar["full_name"], ar["name"])
#                print "I = ", i
                for tp, nxstp in self._npTn.items():
                    cnf = dict(cnfdef)
                    labels = {}
                    paths = {}
                    links = {}
                    types = {}
                    shapes = {}

                    lbl = self.getRandomName(20)
                    fieldname = self.getRandomName(20)
#                    print "FIELD", fieldname
                    path = [
                        (self.getRandomName(20)
                         if self._rnd.randint(0, 1) else None,
                         ("NX" + self.getRandomName(20))
                         if self._rnd.randint(0, 1) else None)
                        for _ in range(self._rnd.randint(0, 10))]
#                    print "path0", path, len(path)
                    path = [nd for nd in path if (
                            nd != (None, None) and
                            nd[0] and not nd[0].startswith("NX"))]
#                    print "path1", path, len(path)
                    mypath = ""
                    for node in path:
                        mypath += "/"
                        if node[0]:
                            mypath += node[0]
                            if node[1]:
                                mypath += ":"
                        if node[1]:
                            mypath += node[1]
#                    mypath += fieldname
#                    print "path2", path, len(path)
#                    print "PATH", path, mypath
#                    print "TP = ", tp
                    ms = [self._rnd.randint(0, 3000)
                          for _ in range(self._rnd.randint(0, 3))]
                    ms2 = [self._rnd.randint(0, 3000)
                           for _ in range(self._rnd.randint(0, 3))]
                    tmptp = self._rnd.choice(self._npTn.keys())
                    if i == 0:
                        cnf["DefaultDynamicLinks"] = False
                        cnf["DefaultDynamicPath"] = mypath
                    elif i == 1:
                        cnf["DefaultDynamicLinks"] = True
                        cnf["DefaultDynamicPath"] = mypath
                    elif i == 2:
                        paths = {ar["name"]: mypath + "/" + fieldname}
                        links = {ar["name"]: False}
                    elif i == 3:
                        paths = {ar["name"]: mypath + "/" + fieldname}
                        links = {ar["name"]: True}
                    elif i == 4:
                        cnf["DefaultDynamicLinks"] = False
                        cnf["DefaultDynamicPath"] = mypath
                        labels = {ar["name"]: lbl}
                    elif i == 5:
                        cnf["DefaultDynamicLinks"] = True
                        cnf["DefaultDynamicPath"] = mypath
                        labels = {ar["name"]: lbl}
                    elif i == 6:
                        labels = {ar["name"]: lbl}
                        paths = {lbl: mypath + "/" + fieldname}
                        links = {lbl: False}
                    elif i == 7:
                        labels = {ar["name"]: lbl}
                        paths = {lbl: mypath + "/" + fieldname}
                        links = {lbl: True}
                    cnf["ChannelProperties"] = json.dumps(
                        {
                            "label": labels,
                            "nexus_path": paths,
                            "link": links,
                            "data_type": types,
                            "shape": shapes
                        }
                    )
#                    print "I = ", i
                    rs.profileConfiguration = str(json.dumps(cnf))
                    cpname = rs.createDynamicComponent([
                        "", str(json.dumps([{"name": ar["full_name"],
                                             "shape": ms,
                                             "dtype": tp}]))])
                    mstr = ""
                    if ms:
                        mstr += dimbg % len(ms)
                        for ind, val in enumerate(ms):
                            mstr += dim % (ind + 1, val)
                        mstr += dimend

                    comp = self._cf.dp.Components([cpname])[0]
                    ds = ar["name"]
                    lk = link % (ds, mypath, ds)
                    if i % 4 < 2:
                        fd = field % (ds, nxstp, ds, ar["full_name"], mstr)
                    else:
                        fname = fieldname.lower()
                        fd = field % (fieldname.lower(), nxstp, ds,
                                      ar["full_name"], mstr)

#                    print "path3", path, len(path), bool(path)
                    if path or i % 4 > 1:

                        if i % 4 < 2:
                            lk = link % (ds, mypath, ds)
                        else:
                            lk = link % (fieldname.lower(), mypath,
                                         fieldname.lower())
                        mycps = defbg
                        for nm, gtp in path:
                            if not nm:
                                nm = gtp[2:]
                            if not gtp:
                                gtp = 'NX' + nm
                            mycps += groupbg % (nm, gtp)
                        mycps += fd

                        for j in range(len(path) - 1):
                            mycps += groupend
                        mycps += lk if i % 2 else ""
                        mycps += groupend
                        mycps += defend

                        mycps2 = defbg
                        for k, (nm, gtp) in enumerate(path):
                            if not nm:
                                nm = gtp[2:]
                            if not gtp:
                                gtp = 'NX' + nm
                            mycps2 += groupbg % (nm, gtp)
                            if not k:
                                mycps2 += lk if i % 2 else ""
                        mycps2 += fd

                        for _ in path:
                            mycps2 += groupend
                        mycps2 += defend
#                        print "FIRST"
                    else:
                        if i % 4 < 2:
                            lk = link % (ds, self._defaultpath, ds)
                        else:
                            lk = link % (fieldname.lower(), self._defaultpath,
                                         fieldname.lower())
                        mycps = cps["shapetype"] % (
                            fd,
                            lk if i % 2 else "")
                        mycps2 = mycps
                    try:
                        self.assertEqual(comp, mycps)
                    except:
                        self.assertEqual(comp, mycps2)
        finally:
            for ar in arr:
                if '/' in ar["full_name"]:
                    db.delete_device_alias(ar["name"])

            simps3.tearDown()
            simps2.tearDown()

    # constructor test
    # \brief It tests default settings
    def test_create_dict_datasource_attr(self):
        fun = sys._getframe().f_code.co_name
        print "Run: %s.%s() " % (self.__class__.__name__, fun)
        val = {"ConfigDevice": self._cf.dp.name(),
               "WriterDevice": self._wr.dp.name(),
               "Door": 'doortestp09/testts/t1r228',
               "MntGrp": 'nxsmntgrp'}
        rs = self.openRecSelector()
        rs.configDevice = val["ConfigDevice"]
        rs.door = val["Door"]
        rs.mntGrp = val["MntGrp"]
        cnfdef = json.loads(rs.profileConfiguration)
        cps = {
            "shapetype":
                '<?xml version="1.0" ?>\n<definition>\n%s'
            '</group>\n</group>\n%s</group>\n</definition>\n',
        }

        defbg = '<?xml version="1.0" ?>\n<definition>\n'
        defend = '</definition>\n'
        groupbg = '<group name="scan$var.serialno" type="NXentry">\n' + \
            '<group name="instrument" type="NXinstrument">\n' + \
            '<group name="collection" type="NXcollection">\n'
        groupend = '</group>\n'

        fieldbg = '<field name="%s" type="%s">\n<strategy mode="STEP"/>\n'

        dsclient = '<datasource name="%s" type="CLIENT">\n' + \
            '<record name="%s"/>\n</datasource>\n'

        dstango = '<datasource name="%s" type="TANGO">\n' + \
            '<device member="attribute" name="%s"/>\n' + \
            '<record name="%s"/>\n</datasource>\n'

        fieldend = '</field>\n'

        link = '<group name="data" type="NXdata">\n' + \
            '<link name="%s" target="%s/%s"/>\n</group>\n'

        dimbg = '<dimensions rank="%s">\n'
        dim = '<dim index="%s" value="%s"/>\n'
        dimend = '</dimensions>\n'

        dname = "__dynamic_component__"

        arr = [
            {"name": "client_short", "full_name": "ttestp09/testts/t1r228",
             "source": "ttestp09/testts/t1r228"},
            {"name": "client_long", "full_name": "ttestp09/testts/t2r228",
             "source": "ttestp09/testts/t1r228/Value"},
            {"name": "myclient_long", "full_name": "ttestp09/testts/t3r228",
             "source": "ttestp09/testts/t1r228/NonExisting"},
            {"name": "myclient", "full_name": "ttestp09/testts/t4r228",
             "source": "ttestp09/testts/t1r228/ImageDouble"},
        ]

        simps2 = TestServerSetUp.TestServerSetUp(
            "ttestp09/testts/t2r228", "S2")
        simps3 = TestServerSetUp.TestServerSetUp(
            "ttestp09/testts/t3r228", "S3")
        simps4 = TestServerSetUp.TestServerSetUp(
            "ttestp09/testts/t4r228", "S4")

        db = PyTango.Database()
        try:
            simps2.setUp()
            simps3.setUp()
            simps4.setUp()
            self._simps.dp.CreateAttribute("DataSource")
            simps2.dp.CreateAttribute("DataSource")
            simps3.dp.CreateAttribute("DataSource")
            simps4.dp.CreateAttribute("DataSource")
            self._simps.dp.DataSource = arr[0]["source"]
            simps2.dp.DataSource = arr[1]["source"]
            simps3.dp.DataSource = arr[2]["source"]
            simps4.dp.DataSource = arr[3]["source"]

            for i, ar in enumerate(arr):
#                print "I = ", i, ar["name"]
                db.put_device_alias(ar["full_name"], ar["name"])

                cpname = rs.createDynamicComponent([
                    "", str(json.dumps([{"name": ar["full_name"]}]))])

                comp = self._cf.dp.Components([cpname])[0]
                mycps = defbg + groupbg + fieldbg % (ar["name"], "NX_CHAR")
                if i % 2:
                    sso = ar["source"].split("/")
#                    mycps += dstango % (
#                        ar["name"], "/".join(sso[:-1]), sso[-1])
                    mycps += dsclient % (ar["name"], ar["full_name"])
                else:
                    mycps += dsclient % (ar["name"], ar["full_name"])
                mycps += fieldend + groupend + groupend
                mycps += link % (ar["name"], self._defaultpath,
                                 ar["name"])
                mycps += groupend + defend

                self.assertEqual(comp, mycps)
#                print comp
        finally:
            for ar in arr:
                if '/' in ar["full_name"]:
                    db.delete_device_alias(ar["name"])

            simps4.tearDown()
            simps3.tearDown()
            simps2.tearDown()

    # constructor test
    # \brief It tests default settings
    def test_create_step(self):
        fun = sys._getframe().f_code.co_name
        print "Run: %s.%s() " % (self.__class__.__name__, fun)
        val = {"ConfigDevice": self._cf.dp.name(),
               "WriterDevice": self._wr.dp.name(),
               "Door": 'doortestp09/testts/t1r228',
               "MntGrp": 'nxsmntgrp'}
        rs = self.openRecSelector()
        rs.configDevice = val["ConfigDevice"]
        rs.door = val["Door"]
        rs.mntGrp = val["MntGrp"]
        cnfdef = json.loads(rs.profileConfiguration)
        cps = {
            "empty":
                '<?xml version="1.0" ?>\n<definition/>\n',
            "one":
                '<?xml version="1.0" ?>\n<definition>\n'
            '<group name="scan$var.serialno" type="NXentry">\n'
            '<group name="instrument" type="NXinstrument">\n'
            '<group name="collection" type="NXcollection">\n'
            '<field name="one" type="NX_CHAR">\n<strategy mode="STEP"/>\n'
            '<datasource name="one" type="CLIENT">\n<record name="one"/>\n'
            '</datasource>\n</field>\n'
            '</group>\n</group>\n'
            '<group name="data" type="NXdata">\n'
            '<link name="one" target="/scan$var.serialno:'
            'NXentry/NXinstrument/collection/one"/>\n'
            '</group>\n</group>\n'
            '</definition>\n',
            "two":
                '<?xml version="1.0" ?>\n<definition>\n'
            '<group name="scan$var.serialno" type="NXentry">\n'
            '<group name="instrument" type="NXinstrument">\n'
            '<group name="collection" type="NXcollection">\n'
            '<field name="d1" type="NX_CHAR">\n<strategy mode="STEP"/>\n'
            '<datasource name="d1" type="CLIENT">\n<record name="d1"/>\n'
            '</datasource>\n</field>\n'
            '</group>\n</group>\n'
            '<group name="data" type="NXdata">\n'
            '<link name="d1" target="/scan$var.serialno:'
            'NXentry/NXinstrument/collection/d1"/>\n'
            '</group>\n</group>\n'
            '<group name="scan$var.serialno" type="NXentry">\n'
            '<group name="instrument" type="NXinstrument">\n'
            '<group name="collection" type="NXcollection">\n'
            '<field name="d2" type="NX_CHAR">\n<strategy mode="STEP"/>\n'
            '<datasource name="d2" type="CLIENT">\n<record name="d2"/>\n'
            '</datasource>\n</field>\n</group>\n</group>\n'
            '<group name="data" type="NXdata">\n'
            '<link name="d2" target="/scan$var.serialno:'
            'NXentry/NXinstrument/collection/d2"/>\n'
            '</group>\n</group>\n'
            '</definition>\n',
            "three":
                '<?xml version="1.0" ?>\n<definition>\n'
            '<group name="scan$var.serialno" type="NXentry">\n'
            '<group name="instrument" type="NXinstrument">\n'
            '<group name="collection" type="NXcollection">\n'
            '<field name="ds1" type="NX_CHAR">\n<strategy mode="STEP"/>\n'
            '<datasource name="ds1" type="CLIENT">\n<record name="ds1"/>\n'
            '</datasource>\n</field>\n'
            '</group>\n</group>\n'
            '<group name="data" type="NXdata">\n'
            '<link name="ds1" target="/scan$var.serialno:'
            'NXentry/NXinstrument/collection/ds1"/>\n'
            '</group>\n</group>\n'
            '<group name="scan$var.serialno" type="NXentry">\n'
            '<group name="instrument" type="NXinstrument">\n'
            '<group name="collection" type="NXcollection">\n'
            '<field name="ds2" type="NX_CHAR">\n<strategy mode="STEP"/>\n'
            '<datasource name="ds2" type="CLIENT">\n<record name="ds2"/>\n'
            '</datasource>\n</field>\n</group>\n</group>\n'
            '<group name="data" type="NXdata">\n'
            '<link name="ds2" target="/scan$var.serialno:'
            'NXentry/NXinstrument/collection/ds2"/>\n'
            '</group>\n</group>\n'
            '<group name="scan$var.serialno" type="NXentry">\n'
            '<group name="instrument" type="NXinstrument">\n'
            '<group name="collection" type="NXcollection">\n'
            '<field name="ds3" type="NX_CHAR">\n<strategy mode="STEP"/>\n'
            '<datasource name="ds3" type="CLIENT">\n<record name="ds3"/>\n'
            '</datasource>\n</field>\n</group>\n</group>\n'
            '<group name="data" type="NXdata">\n'
            '<link name="ds3" target="/scan$var.serialno:'
            'NXentry/NXinstrument/collection/ds3"/>\n'
            '</group>\n</group>\n'
            '</definition>\n'
        }
        dsdict = {
            "empty": [],
            "one": ["one"],
            "two": ["d1", "d2"],
            "three": ["ds1", "ds2", "ds3"],
        }
        dname = "__dynamic_component__"
        for lb, ds in dsdict.items():

            cpname = rs.createDynamicComponent([
                str(json.dumps(ds))])
            comp = self._cf.dp.Components([cpname])[0]
            self.assertEqual(cps[lb], comp)

    # constructor test
    # \brief It tests default settings
    def test_create_sel(self):
        fun = sys._getframe().f_code.co_name
        print "Run: %s.%s() " % (self.__class__.__name__, fun)
        val = {"ConfigDevice": self._cf.dp.name(),
               "WriterDevice": self._wr.dp.name(),
               "Door": 'doortestp09/testts/t1r228',
               "MntGrp": 'nxsmntgrp'}
        rs = self.openRecSelector()
        rs.configDevice = val["ConfigDevice"]
        rs.door = val["Door"]
        rs.mntGrp = val["MntGrp"]
        cnfdef = json.loads(rs.profileConfiguration)
        cps = {
            "empty":
                '<?xml version="1.0" ?>\n<definition/>\n',
            "one":
                '<?xml version="1.0" ?>\n<definition>\n'
            '<group name="scan$var.serialno" type="NXentry">\n'
            '<group name="instrument" type="NXinstrument">\n'
            '<group name="collection" type="NXcollection">\n'
            '<field name="one" type="NX_CHAR">\n<strategy mode="STEP"/>\n'
            '<datasource name="one" type="CLIENT">\n<record name="one"/>\n'
            '</datasource>\n</field>\n'
            '</group>\n</group>\n'
            '<group name="data" type="NXdata">\n'
            '<link name="one" target="/scan$var.serialno:'
            'NXentry/NXinstrument/collection/one"/>\n'
            '</group>\n</group>\n'
            '</definition>\n',
            "two":
                '<?xml version="1.0" ?>\n<definition>\n'
            '<group name="scan$var.serialno" type="NXentry">\n'
            '<group name="instrument" type="NXinstrument">\n'
            '<group name="collection" type="NXcollection">\n'
            '<field name="d1" type="NX_CHAR">\n<strategy mode="STEP"/>\n'
            '<datasource name="d1" type="CLIENT">\n<record name="d1"/>\n'
            '</datasource>\n</field>\n'
            '</group>\n</group>\n'
            '<group name="data" type="NXdata">\n'
            '<link name="d1" target="/scan$var.serialno:'
            'NXentry/NXinstrument/collection/d1"/>\n'
            '</group>\n</group>\n'
            '<group name="scan$var.serialno" type="NXentry">\n'
            '<group name="instrument" type="NXinstrument">\n'
            '<group name="collection" type="NXcollection">\n'
            '<field name="d2" type="NX_CHAR">\n<strategy mode="STEP"/>\n'
            '<datasource name="d2" type="CLIENT">\n<record name="d2"/>\n'
            '</datasource>\n</field>\n</group>\n</group>\n'
            '<group name="data" type="NXdata">\n'
            '<link name="d2" target="/scan$var.serialno:'
            'NXentry/NXinstrument/collection/d2"/>\n'
            '</group>\n</group>\n'
            '</definition>\n',
            "three":
                '<?xml version="1.0" ?>\n<definition>\n'
            '<group name="scan$var.serialno" type="NXentry">\n'
            '<group name="instrument" type="NXinstrument">\n'
            '<group name="collection" type="NXcollection">\n'
            '<field name="ds1" type="NX_CHAR">\n<strategy mode="STEP"/>\n'
            '<datasource name="ds1" type="CLIENT">\n<record name="ds1"/>\n'
            '</datasource>\n</field>\n'
            '</group>\n</group>\n'
            '<group name="data" type="NXdata">\n'
            '<link name="ds1" target="/scan$var.serialno:'
            'NXentry/NXinstrument/collection/ds1"/>\n'
            '</group>\n</group>\n'
            '<group name="scan$var.serialno" type="NXentry">\n'
            '<group name="instrument" type="NXinstrument">\n'
            '<group name="collection" type="NXcollection">\n'
            '<field name="ds2" type="NX_CHAR">\n<strategy mode="STEP"/>\n'
            '<datasource name="ds2" type="CLIENT">\n<record name="ds2"/>\n'
            '</datasource>\n</field>\n</group>\n</group>\n'
            '<group name="data" type="NXdata">\n'
            '<link name="ds2" target="/scan$var.serialno:'
            'NXentry/NXinstrument/collection/ds2"/>\n'
            '</group>\n</group>\n'
            '<group name="scan$var.serialno" type="NXentry">\n'
            '<group name="instrument" type="NXinstrument">\n'
            '<group name="collection" type="NXcollection">\n'
            '<field name="ds3" type="NX_CHAR">\n<strategy mode="STEP"/>\n'
            '<datasource name="ds3" type="CLIENT">\n<record name="ds3"/>\n'
            '</datasource>\n</field>\n</group>\n</group>\n'
            '<group name="data" type="NXdata">\n'
            '<link name="ds3" target="/scan$var.serialno:'
            'NXentry/NXinstrument/collection/ds3"/>\n'
            '</group>\n</group>\n'
            '</definition>\n'
        }
        dsdict = {
            "empty": [],
            "one": ["one"],
            "two": ["d1", "d2"],
            "three": ["ds1", "ds2", "ds3"],
        }
        dname = "__dynamic_component__"
        for lb, ds in dsdict.items():
            cnf = dict(cnfdef)
            cnf["DataSourceSelection"] = json.dumps(
                dict((dd, True) for dd in ds))
            rs.profileConfiguration = str(json.dumps(cnf))
            _ = rs.selectedDataSources()
            cpname = rs.createDynamicComponent([])
            comp = self._cf.dp.Components([cpname])[0]
            self.assertEqual(cps["empty"], comp)

    # constructor test
    # \brief It tests default settings
    def test_create_step_no_type(self):
        fun = sys._getframe().f_code.co_name
        print "Run: %s.%s() " % (self.__class__.__name__, fun)
        val = {"ConfigDevice": self._cf.dp.name(),
               "WriterDevice": self._wr.dp.name(),
               "Door": 'doortestp09/testts/t1r228',
               "MntGrp": 'nxsmntgrp'}
        rs = self.openRecSelector()
        rs.configDevice = val["ConfigDevice"]
        rs.door = val["Door"]
        rs.mntGrp = val["MntGrp"]
        cnfdef = json.loads(rs.profileConfiguration)
        cps = {
            "type":
                '<?xml version="1.0" ?>\n<definition>\n'
            '<group name="scan$var.serialno" type="NXentry">\n'
            '<group name="instrument" type="NXinstrument">\n'
            '<group name="collection" type="NXcollection">\n'
            '<field name="ds1" type="%s">\n<strategy mode="STEP"/>\n'
            '<datasource name="ds1" type="CLIENT">\n'
            '<record name="ds1"/>\n</datasource>\n</field>\n'
            '</group>\n</group>\n<group name="data" type="NXdata">\n'
            '<link name="ds1" target="/scan$var.serialno:'
            'NXentry/NXinstrument/collection/ds1"/>\n'
            '</group>\n</group>\n</definition>\n',
        }
        dname = "__dynamic_component__"
        for tp, nxstp in self._npTn.items():
            cpname = rs.createDynamicComponent([
                str(json.dumps(["ds1"]))])

            comp = self._cf.dp.Components([cpname])[0]
            self.assertEqual(cps["type"] % "NX_CHAR", comp)

    # constructor test
    # \brief It tests default settings
    def test_create_init_no_type(self):
        fun = sys._getframe().f_code.co_name
        print "Run: %s.%s() " % (self.__class__.__name__, fun)
        val = {"ConfigDevice": self._cf.dp.name(),
               "WriterDevice": self._wr.dp.name(),
               "Door": 'doortestp09/testts/t1r228',
               "MntGrp": 'nxsmntgrp'}
        rs = self.openRecSelector()
        rs.configDevice = val["ConfigDevice"]
        rs.door = val["Door"]
        rs.mntGrp = val["MntGrp"]
        cnfdef = json.loads(rs.profileConfiguration)
        cps = {
            "type":
                '<?xml version="1.0" ?>\n<definition>\n'
            '<group name="scan$var.serialno" type="NXentry">\n'
            '<group name="instrument" type="NXinstrument">\n'
            '<group name="collection" type="NXcollection">\n'
            '<field name="ds1" type="%s">\n<strategy mode="INIT"/>\n'
            '<datasource name="ds1" type="CLIENT">\n'
            '<record name="ds1"/>\n</datasource>\n</field>\n'
            '</group>\n'
            '</group>\n</group>\n</definition>\n',
        }
        dname = "__dynamic_component__"
        for tp, nxstp in self._npTn.items():
            cpname = rs.createDynamicComponent([
                "", "",
                str(json.dumps(["ds1"]))])

            comp = self._cf.dp.Components([cpname])[0]
            self.assertEqual(cps["type"] % "NX_CHAR", comp)

    # constructor test
    # \brief It tests default settings
    def test_create_step_type_param(self):
        fun = sys._getframe().f_code.co_name
        print "Run: %s.%s() " % (self.__class__.__name__, fun)
        val = {"ConfigDevice": self._cf.dp.name(),
               "WriterDevice": self._wr.dp.name(),
               "Door": 'doortestp09/testts/t1r228',
               "MntGrp": 'nxsmntgrp'}
        rs = self.openRecSelector()
        rs.configDevice = val["ConfigDevice"]
        rs.door = val["Door"]
        rs.mntGrp = val["MntGrp"]
        cnfdef = json.loads(rs.profileConfiguration)
        cps = {
            "type":
                '<?xml version="1.0" ?>\n<definition>\n'
            '<group name="scan$var.serialno" type="NXentry">\n'
            '<group name="instrument" type="NXinstrument">\n'
            '<group name="collection" type="NXcollection">\n'
            '<field name="ds1" type="%s">\n<strategy mode="STEP"/>\n'
            '<datasource name="ds1" type="CLIENT">\n'
            '<record name="ds1"/>\n</datasource>\n</field>\n'
            '</group>\n</group>\n<group name="data" type="NXdata">\n'
            '<link name="ds1" target="/scan$var.serialno:'
            'NXentry/NXinstrument/collection/ds1"/>\n'
            '</group>\n</group>\n</definition>\n',
        }
        dname = "__dynamic_component__"
        for tp, nxstp in self._npTn.items():
            cnf = dict(cnfdef)
            cnf["ChannelProperties"] = json.dumps(
                {
                    "label": {},
                    "nexus_path": {},
                    "link": {},
                    "data_type": {"ds1": nxstp},
                    "shape": {}
                }
            )
            rs.profileConfiguration = str(json.dumps(cnf))
            cpname = rs.createDynamicComponent([
                str(json.dumps(["ds1"]))])


#            dc.setStepDSources(["ds1"])
#            cpname = dc.create()
            comp = self._cf.dp.Components([cpname])[0]
            self.assertEqual(cps["type"] % nxstp, comp)

    # constructor test
    # \brief It tests default settings
    def test_create_init_type_param(self):
        fun = sys._getframe().f_code.co_name
        print "Run: %s.%s() " % (self.__class__.__name__, fun)
        val = {"ConfigDevice": self._cf.dp.name(),
               "WriterDevice": self._wr.dp.name(),
               "Door": 'doortestp09/testts/t1r228',
               "MntGrp": 'nxsmntgrp'}
        rs = self.openRecSelector()
        rs.configDevice = val["ConfigDevice"]
        rs.door = val["Door"]
        rs.mntGrp = val["MntGrp"]
        cnfdef = json.loads(rs.profileConfiguration)
        cps = {
            "type":
                '<?xml version="1.0" ?>\n<definition>\n'
            '<group name="scan$var.serialno" type="NXentry">\n'
            '<group name="instrument" type="NXinstrument">\n'
            '<group name="collection" type="NXcollection">\n'
            '<field name="ds1" type="%s">\n<strategy mode="INIT"/>\n'
            '<datasource name="ds1" type="CLIENT">\n'
            '<record name="ds1"/>\n</datasource>\n</field>\n'
            '</group>\n'
            '</group>\n</group>\n</definition>\n',
        }
        dname = "__dynamic_component__"
        for tp, nxstp in self._npTn.items():
            cnf = dict(cnfdef)
            cnf["ChannelProperties"] = json.dumps(
                {
                    "label": {},
                    "nexus_path": {},
                    "link": {},
                    "data_type": {"ds1": nxstp},
                    "shape": {}
                }
            )
            rs.profileConfiguration = str(json.dumps(cnf))
            cpname = rs.createDynamicComponent([
                "", "", str(json.dumps(["ds1"]))])

            comp = self._cf.dp.Components([cpname])[0]
            self.assertEqual(cps["type"] % nxstp, comp)

    # constructor test
    # \brief It tests default settings
    def test_create_step_shape(self):
        fun = sys._getframe().f_code.co_name
        print "Run: %s.%s() " % (self.__class__.__name__, fun)
        val = {"ConfigDevice": self._cf.dp.name(),
               "WriterDevice": self._wr.dp.name(),
               "Door": 'doortestp09/testts/t1r228',
               "MntGrp": 'nxsmntgrp'}
        rs = self.openRecSelector()
        rs.configDevice = val["ConfigDevice"]
        rs.door = val["Door"]
        rs.mntGrp = val["MntGrp"]
        cnfdef = json.loads(rs.profileConfiguration)
        cps = {
            "shape":
                '<?xml version="1.0" ?>\n<definition>\n'
            '<group name="scan$var.serialno" type="NXentry">\n'
            '<group name="instrument" type="NXinstrument">\n'
            '<group name="collection" type="NXcollection">\n'
            '<field name="ds2" type="NX_CHAR">\n<strategy mode="STEP"/>\n'
            '<datasource name="ds2" type="CLIENT">\n'
            '<record name="ds2"/>\n</datasource>\n%s</field>\n'
            '</group>\n</group>\n<group name="data" type="NXdata">\n'
            '<link name="ds2" target="/scan$var.serialno:'
            'NXentry/NXinstrument/collection/ds2"/>\n'
            '</group>\n</group>\n</definition>\n',
        }

        dimbg = '<dimensions rank="%s">\n'
        dim = '<dim index="%s" value="%s"/>\n'
        dimend = '</dimensions>\n'

        dname = "__dynamic_component__"
        for i in range(50):
            ms = [self._rnd.randint(0, 3000)
                  for _ in range(self._rnd.randint(0, 3))]

            cnf = dict(cnfdef)
            cnf["ChannelProperties"] = json.dumps(
                {
                    "label": {},
                    "nexus_path": {},
                    "link": {},
                    "data_type": {},
                    "shape": {"ds2": ms}
                }
            )
            rs.profileConfiguration = str(json.dumps(cnf))
            cpname = rs.createDynamicComponent([
                str(json.dumps(["ds2"]))])
            mstr = ""
            if ms:
                mstr += dimbg % len(ms)
                for ind, val in enumerate(ms):
                    mstr += dim % (ind + 1, val)
                mstr += dimend

            comp = self._cf.dp.Components([cpname])[0]
            self.assertEqual(cps["shape"] % mstr, comp)

    # constructor test
    # \brief It tests default settings
    def test_create_init_shape(self):
        fun = sys._getframe().f_code.co_name
        print "Run: %s.%s() " % (self.__class__.__name__, fun)
        val = {"ConfigDevice": self._cf.dp.name(),
               "WriterDevice": self._wr.dp.name(),
               "Door": 'doortestp09/testts/t1r228',
               "MntGrp": 'nxsmntgrp'}
        rs = self.openRecSelector()
        rs.configDevice = val["ConfigDevice"]
        rs.door = val["Door"]
        rs.mntGrp = val["MntGrp"]
        cnfdef = json.loads(rs.profileConfiguration)
        cps = {
            "shape":
                '<?xml version="1.0" ?>\n<definition>\n'
            '<group name="scan$var.serialno" type="NXentry">\n'
            '<group name="instrument" type="NXinstrument">\n'
            '<group name="collection" type="NXcollection">\n'
            '<field name="ds2" type="NX_CHAR">\n<strategy mode="INIT"/>\n'
            '<datasource name="ds2" type="CLIENT">\n'
            '<record name="ds2"/>\n</datasource>\n%s</field>\n'
            '</group>\n'
            '</group>\n</group>\n</definition>\n',
        }

        dimbg = '<dimensions rank="%s">\n'
        dim = '<dim index="%s" value="%s"/>\n'
        dimend = '</dimensions>\n'

        dname = "__dynamic_component__"
        for i in range(50):
            ms = [self._rnd.randint(0, 3000)
                  for _ in range(self._rnd.randint(0, 3))]
            cnf = dict(cnfdef)
            cnf["ChannelProperties"] = json.dumps(
                {
                    "label": {},
                    "nexus_path": {},
                    "link": {},
                    "data_type": {},
                    "shape": {"ds2": ms}
                }
            )
            rs.profileConfiguration = str(json.dumps(cnf))
            cpname = rs.createDynamicComponent([
                "", "",
                str(json.dumps(["ds2"]))])
            mstr = ""
            if ms:
                mstr += dimbg % len(ms)
                for ind, val in enumerate(ms):
                    mstr += dim % (ind + 1, val)
                mstr += dimend

            comp = self._cf.dp.Components([cpname])[0]
            self.assertEqual(cps["shape"] % mstr, comp)

    # constructor test
    # \brief It tests default settings
    def test_create_step_shapetype(self):
        fun = sys._getframe().f_code.co_name
        print "Run: %s.%s() " % (self.__class__.__name__, fun)
        val = {"ConfigDevice": self._cf.dp.name(),
               "WriterDevice": self._wr.dp.name(),
               "Door": 'doortestp09/testts/t1r228',
               "MntGrp": 'nxsmntgrp'}
        rs = self.openRecSelector()
        rs.configDevice = val["ConfigDevice"]
        rs.door = val["Door"]
        rs.mntGrp = val["MntGrp"]
        cnfdef = json.loads(rs.profileConfiguration)
        cps = {
            "shapetype":
                '<?xml version="1.0" ?>\n<definition>\n'
            '<group name="scan$var.serialno" type="NXentry">\n'
            '<group name="instrument" type="NXinstrument">\n'
            '<group name="collection" type="NXcollection">\n'
            '<field name="%s" type="%s">\n<strategy mode="STEP"/>\n'
            '<datasource name="%s" type="CLIENT">\n'
            '<record name="%s"/>\n</datasource>\n'
            '%s</field>\n'
            '</group>\n</group>\n%s</group>\n</definition>\n',
        }

        link = '<group name="data" type="NXdata">\n' + \
            '<link name="%s" target="/scan$var.serialno:' + \
            'NXentry/NXinstrument/collection/%s"/>\n</group>\n'

        dimbg = '<dimensions rank="%s">\n'
        dim = '<dim index="%s" value="%s"/>\n'
        dimend = '</dimensions>\n'

        dname = "__dynamic_component__"

        arr = [
            {"name": "client"},
            {"name": "client_short"},
            {"name": "client_long"},
            {"name": "myclient_long"},
            {"name": "client"},
            {"name": "client_short"},
            {"name": "client_long"},
            {"name": "myclient_long"},
            {"name": "client"},
            {"name": "client_short"},
            {"name": "client_long"},
            {"name": "myclient_long"},
            {"name": "client"},
            {"name": "client_short"},
            {"name": "client_long"},
            {"name": "myclient_long"},
        ]

        db = PyTango.Database()
        try:
            for i, ar in enumerate(arr):
                for tp, nxstp in self._npTn.items():
                    lbl = self.getRandomName(20)
                    ms = [self._rnd.randint(0, 3000)
                          for _ in range(self._rnd.randint(0, 3))]
                    ms2 = [self._rnd.randint(0, 3000)
                           for _ in range(self._rnd.randint(0, 3))]
                    tmptp = self._rnd.choice(self._npTn.keys())
                    cnf = dict(cnfdef)
                    labels = {}
                    paths = {}
                    links = {}
                    types = {}
                    shapes = {}

                    if i == 0:
                        cnf["DefaultDynamicLinks"] = False
                        cnf["DefaultDynamicPath"] = self._defaultpath
                        types = {ar["name"]: nxstp}
                        shapes = {ar["name"]: ms}
                    elif i == 1:
                        cnf["DefaultDynamicLinks"] = True
                        cnf["DefaultDynamicPath"] = self._defaultpath
                        types = {ar["name"]: nxstp}
                        shapes = {ar["name"]: ms}
                    elif i == 2:
                        links = {ar["name"]: False}
                        types = {ar["name"]: nxstp}
                        shapes = {ar["name"]: ms}
                    elif i == 3:
                        links = {ar["name"]: True}
                        types = {ar["name"]: nxstp}
                        shapes = {ar["name"]: ms}
                    elif i == 4:
                        cnf["DefaultDynamicLinks"] = True
                        cnf["DefaultDynamicPath"] = self._defaultpath
                        links = {ar["name"]: False}
                        types = {ar["name"]: nxstp}
                        shapes = {ar["name"]: ms}
                    elif i == 5:
                        cnf["DefaultDynamicLinks"] = False
                        cnf["DefaultDynamicPath"] = self._defaultpath
                        links = {ar["name"]: True}
                        types = {ar["name"]: nxstp}
                        shapes = {ar["name"]: ms}
                    elif i == 6:
                        cnf["DefaultDynamicLinks"] = False
                        cnf["DefaultDynamicPath"] = self._defaultpath
                        links = {"dssd": True}
                        types = {ar["name"]: nxstp}
                        shapes = {ar["name"]: ms}
                    elif i == 7:
                        labels = {ar["name"]: lbl}
                        types = {ar["name"]: nxstp}
                        shapes = {ar["name"]: ms}
                    elif i == 8:
                        pass
                        cnf["DefaultDynamicLinks"] = False
                        cnf["DefaultDynamicPath"] = self._defaultpath
                        labels = {ar["name"]: lbl}
                        types = {ar["name"]: nxstp}
                        shapes = {ar["name"]: ms}
                    elif i == 9:
                        cnf["DefaultDynamicLinks"] = True
                        cnf["DefaultDynamicPath"] = self._defaultpath
                        labels = {ar["name"]: lbl}
                        types = {ar["name"]: nxstp}
                        shapes = {ar["name"]: ms}
                    elif i == 10:
                        labels = {ar["name"]: lbl}
                        links = {lbl: False}
                        types = {ar["name"]: nxstp}
                        shapes = {ar["name"]: ms}
                    elif i == 11:
                        labels = {ar["name"]: lbl}
                        links = {lbl: True}
                        types = {ar["name"]: nxstp}
                        shapes = {ar["name"]: ms}
                    elif i == 12:
                        cnf["DefaultDynamicLinks"] = True
                        cnf["DefaultDynamicPath"] = self._defaultpath
                        labels = {ar["name"]: lbl}
                        links = {lbl: False}
                        types = {ar["name"]: nxstp}
                        shapes = {ar["name"]: ms}
                    elif i == 13:
                        cnf["DefaultDynamicLinks"] = False
                        cnf["DefaultDynamicPath"] = self._defaultpath
                        labels = {ar["name"]: lbl}
                        links = {lbl: True}
                        types = {ar["name"]: nxstp}
                        shapes = {ar["name"]: ms}
                    elif i == 14:
                        cnf["DefaultDynamicLinks"] = False
                        cnf["DefaultDynamicPath"] = self._defaultpath
                        labels = {ar["name"]: lbl}
                        links = {"dssd": True}
                        types = {ar["name"]: nxstp}
                        shapes = {ar["name"]: ms}
                    elif i == 15:
                        labels = {ar["name"]: lbl}
                        types = {ar["name"]: nxstp}
                        shapes = {ar["name"]: ms}

                    cnf["ChannelProperties"] = json.dumps(
                        {
                            "label": labels,
                            "nexus_path": paths,
                            "link": links,
                            "data_type": types,
                            "shape": shapes
                        }
                    )
#                    print "I = ", i
                    rs.profileConfiguration = str(json.dumps(cnf))
                    cpname = rs.createDynamicComponent([
                        str(json.dumps([ar["name"]]))])
                    mstr = ""
                    if ms:
                        mstr += dimbg % len(ms)
                        for ind, val in enumerate(ms):
                            mstr += dim % (ind + 1, val)
                        mstr += dimend

                    comp = self._cf.dp.Components([cpname])[0]
                    ds = ar["name"]
                    lk = link % (ds, ds)
                    self.assertEqual(
                        cps["shapetype"] % (
                            ds,
                            nxstp, ds, ar["name"], mstr,
                            lk if i % 2 else ""),
                        comp)
        finally:
            pass

    # constructor test
    # \brief It tests default settings
    def test_create_init_shapetype(self):
        fun = sys._getframe().f_code.co_name
        print "Run: %s.%s() " % (self.__class__.__name__, fun)
        val = {"ConfigDevice": self._cf.dp.name(),
               "WriterDevice": self._wr.dp.name(),
               "Door": 'doortestp09/testts/t1r228',
               "MntGrp": 'nxsmntgrp'}
        rs = self.openRecSelector()
        rs.configDevice = val["ConfigDevice"]
        rs.door = val["Door"]
        rs.mntGrp = val["MntGrp"]
        cnfdef = json.loads(rs.profileConfiguration)
        cps = {
            "shapetype":
                '<?xml version="1.0" ?>\n<definition>\n'
            '<group name="scan$var.serialno" type="NXentry">\n'
            '<group name="instrument" type="NXinstrument">\n'
            '<group name="collection" type="NXcollection">\n'
            '<field name="%s" type="%s">\n<strategy mode="INIT"/>\n'
            '<datasource name="%s" type="CLIENT">\n'
            '<record name="%s"/>\n</datasource>\n'
            '%s</field>\n'
            '</group>\n</group>\n%s</group>\n</definition>\n',
        }

        link = '<group name="data" type="NXdata">\n' + \
            '<link name="%s" target="/scan$var.serialno:' + \
            'NXentry/NXinstrument/collection/%s"/>\n</group>\n'

        dimbg = '<dimensions rank="%s">\n'
        dim = '<dim index="%s" value="%s"/>\n'
        dimend = '</dimensions>\n'

        dname = "__dynamic_component__"

        arr = [
            {"name": "client"},
            {"name": "client_short"},
            {"name": "client_long"},
            {"name": "myclient_long"},
            {"name": "client"},
            {"name": "client_short"},
            {"name": "client_long"},
            {"name": "myclient_long"},
            {"name": "client"},
            {"name": "client_short"},
            {"name": "client_long"},
            {"name": "myclient_long"},
            {"name": "client"},
            {"name": "client_short"},
            {"name": "client_long"},
            {"name": "myclient_long"},
        ]

        db = PyTango.Database()
        try:
            for i, ar in enumerate(arr):
                for tp, nxstp in self._npTn.items():
                    lbl = self.getRandomName(20)
#                    print "TP = ", tp, i
                    ms = [self._rnd.randint(0, 3000)
                          for _ in range(self._rnd.randint(0, 3))]
                    ms2 = [self._rnd.randint(0, 3000)
                           for _ in range(self._rnd.randint(0, 3))]
                    tmptp = self._rnd.choice(self._npTn.keys())
                    cnf = dict(cnfdef)
                    labels = {}
                    paths = {}
                    links = {}
                    types = {}
                    shapes = {}

                    if i == 0:
                        cnf["DefaultDynamicLinks"] = False
                        cnf["DefaultDynamicPath"] = self._defaultpath
                        types = {ar["name"]: nxstp}
                        shapes = {ar["name"]: ms}
                    elif i == 1:
                        cnf["DefaultDynamicLinks"] = True
                        cnf["DefaultDynamicPath"] = self._defaultpath
                        links = {ar["name"]: True}
                        types = {ar["name"]: nxstp}
                        shapes = {ar["name"]: ms}
                    elif i == 2:
                        links = {ar["name"]: False}
                        types = {ar["name"]: nxstp}
                        shapes = {ar["name"]: ms}
                    elif i == 3:
                        links = {ar["name"]: True}
                        types = {ar["name"]: nxstp}
                        shapes = {ar["name"]: ms}
                    elif i == 4:
                        cnf["DefaultDynamicLinks"] = True
                        cnf["DefaultDynamicPath"] = self._defaultpath
                        links = {ar["name"]: False}
                        types = {ar["name"]: nxstp}
                        shapes = {ar["name"]: ms}
                    elif i == 5:
                        cnf["DefaultDynamicLinks"] = False
                        cnf["DefaultDynamicPath"] = self._defaultpath
                        links = {ar["name"]: True}
                        types = {ar["name"]: nxstp}
                        shapes = {ar["name"]: ms}
                    elif i == 6:
                        cnf["DefaultDynamicLinks"] = False
                        cnf["DefaultDynamicPath"] = self._defaultpath
                        links = {"dssd": True}
                        types = {ar["name"]: nxstp}
                        shapes = {ar["name"]: ms}
                    elif i == 7:
                        labels = {ar["name"]: lbl}
                        types = {ar["name"]: nxstp}
                        shapes = {ar["name"]: ms}
                        links = {ar["name"]: True}
                    elif i == 8:
                        pass
                        cnf["DefaultDynamicLinks"] = False
                        cnf["DefaultDynamicPath"] = self._defaultpath
                        labels = {ar["name"]: lbl}
                        types = {ar["name"]: nxstp}
                        shapes = {ar["name"]: ms}
                    elif i == 9:
                        cnf["DefaultDynamicLinks"] = True
                        cnf["DefaultDynamicPath"] = self._defaultpath
                        labels = {ar["name"]: lbl}
                        types = {ar["name"]: nxstp}
                        shapes = {ar["name"]: ms}
                        links = {ar["name"]: True}
                    elif i == 10:
                        labels = {ar["name"]: lbl}
                        links = {lbl: False}
                        types = {ar["name"]: nxstp}
                        shapes = {ar["name"]: ms}
                    elif i == 11:
                        labels = {ar["name"]: lbl}
                        links = {lbl: True}
                        types = {ar["name"]: nxstp}
                        shapes = {ar["name"]: ms}
                    elif i == 12:
                        cnf["DefaultDynamicLinks"] = True
                        cnf["DefaultDynamicPath"] = self._defaultpath
                        labels = {ar["name"]: lbl}
                        links = {lbl: False}
                        types = {ar["name"]: nxstp}
                        shapes = {ar["name"]: ms}
                    elif i == 13:
                        cnf["DefaultDynamicLinks"] = False
                        cnf["DefaultDynamicPath"] = self._defaultpath
                        labels = {ar["name"]: lbl}
                        links = {lbl: True}
                        types = {ar["name"]: nxstp}
                        shapes = {ar["name"]: ms}
                    elif i == 14:
                        cnf["DefaultDynamicLinks"] = False
                        cnf["DefaultDynamicPath"] = self._defaultpath
                        labels = {ar["name"]: lbl}
                        links = {"dssd": True}
                        types = {ar["name"]: nxstp}
                        shapes = {ar["name"]: ms}
                    elif i == 15:
                        labels = {ar["name"]: lbl}
                        types = {ar["name"]: nxstp}
                        shapes = {ar["name"]: ms}
                        links = {ar["name"]: True}

                    cnf["ChannelProperties"] = json.dumps(
                        {
                            "label": labels,
                            "nexus_path": paths,
                            "link": links,
                            "data_type": types,
                            "shape": shapes
                        }
                    )
#                    print "I = ", i
                    rs.profileConfiguration = str(json.dumps(cnf))
                    cpname = rs.createDynamicComponent([
                        "", "",
                        str(json.dumps([ar["name"]]))])
                    mstr = ""
                    if ms:
                        mstr += dimbg % len(ms)
                        for ind, val in enumerate(ms):
                            mstr += dim % (ind + 1, val)
                        mstr += dimend

                    comp = self._cf.dp.Components([cpname])[0]
                    ds = ar["name"]
                    lk = link % (ds, ds)
                    self.assertEqual(
                        cps["shapetype"] % (
                            ds,
                            nxstp, ds, ar["name"], mstr,
                            lk if i % 2 else ""),
                        comp)
        finally:
            pass

    # constructor test
    # \brief It tests default settings
    def test_create_step_typeshape_tango_nods(self):
        fun = sys._getframe().f_code.co_name
        print "Run: %s.%s() " % (self.__class__.__name__, fun)
        val = {"ConfigDevice": self._cf.dp.name(),
               "WriterDevice": self._wr.dp.name(),
               "Door": 'doortestp09/testts/t1r228',
               "MntGrp": 'nxsmntgrp'}
        rs = self.openRecSelector()
        rs.configDevice = val["ConfigDevice"]
        rs.door = val["Door"]
        rs.mntGrp = val["MntGrp"]
        cnfdef = json.loads(rs.profileConfiguration)

        defbg = '<?xml version="1.0" ?>\n<definition>\n'
        defend = '</definition>\n'
        groupbg = '<group name="scan$var.serialno" type="NXentry">\n' + \
            '<group name="instrument" type="NXinstrument">\n' + \
            '<group name="collection" type="NXcollection">\n'
        groupend = '</group>\n'

        fieldbg = '<field name="%s" type="%s">\n<strategy mode="STEP"/>\n'
        fieldend = '</field>\n'

        dsclient = '<datasource name="%s" type="CLIENT">\n' + \
            '<record name="%s"/>\n</datasource>\n'

        link = '<group name="data" type="NXdata">\n' + \
            '<link name="%s" target="%s/%s"/>\n</group>\n'

        dimbg = '<dimensions rank="%s">\n'
        dim = '<dim index="%s" value="%s"/>\n'
        dimend = '</dimensions>\n'

#        self._cf.dp.SetCommandVariable(["DSDICT", json.dumps(self.smydss)])
#        dc = DynamicComponent(self._cf.dp)
        for i in range(4):
            for ds, dsxml in self.smydss.items():
                ms = self.smydsspar[ds]
                sds = ds.split("_")
                tp = sds[1]
                cnf = dict(cnfdef)
                labels = {}
                paths = {}
                links = {}
                types = {}
                shapes = {}

                if i == 0:
                    cnf["DefaultDynamicLinks"] = False
                    cnf["DefaultDynamicPath"] = self._defaultpath
                elif i == 1:
                    cnf["DefaultDynamicLinks"] = True
                    cnf["DefaultDynamicPath"] = self._defaultpath
                elif i == 2:
                    links = {ds: False}
                elif i == 3:
                    links = {ds: True}
                cnf["ChannelProperties"] = json.dumps(
                    {
                        "label": labels,
                        "nexus_path": paths,
                        "link": links,
                        "data_type": types,
                        "shape": shapes
                    }
                )
                rs.profileConfiguration = str(json.dumps(cnf))
                cpname = rs.createDynamicComponent([
                    str(json.dumps([ds]))])

#                dc.setStepDSources([ds])
#                cpname = dc.create()
                comp = self._cf.dp.Components([cpname])[0]

                nxstype = 'NX_CHAR'
                mycps = defbg + groupbg + fieldbg % (
                    ds.lower(), nxstype)

                mycps += dsclient % (ds, ds)
                mstr = ""

                mycps += mstr
                mycps += fieldend + groupend + groupend
                lk = link % (ds.lower(), self._defaultpath,
                             ds.lower())
                mycps += lk if i % 2 else ""
                mycps += groupend + defend

                self.assertEqual(comp, mycps)

    # constructor test
    # \brief It tests default settings
    def test_create_step_typeshape_tango_nods_attr(self):
        fun = sys._getframe().f_code.co_name
        print "Run: %s.%s() " % (self.__class__.__name__, fun)
        val = {"ConfigDevice": self._cf.dp.name(),
               "WriterDevice": self._wr.dp.name(),
               "Door": 'doortestp09/testts/t1r228',
               "MntGrp": 'nxsmntgrp'}
        rs = self.openRecSelector()
        rs.configDevice = val["ConfigDevice"]
        rs.door = val["Door"]
        rs.mntGrp = val["MntGrp"]
        cnfdef = json.loads(rs.profileConfiguration)

        defbg = '<?xml version="1.0" ?>\n<definition>\n'
        defend = '</definition>\n'
        groupbg = '<group name="scan$var.serialno" type="NXentry">\n' + \
            '<group name="instrument" type="NXinstrument">\n' + \
            '<group name="collection" type="NXcollection">\n'
        groupend = '</group>\n'

        fieldbg = '<field name="%s" type="%s">\n<strategy mode="STEP"/>\n'
        fieldend = '</field>\n'

        dsclient = '<datasource name="%s" type="CLIENT">\n' + \
            '<record name="%s"/>\n</datasource>\n'
        dstango = '<datasource name="%s" type="TANGO">\n' + \
            '<device member="attribute" name="%s"/>\n' + \
            '<record name="%s"/>\n</datasource>\n'

        link = '<group name="data" type="NXdata">\n' + \
            '<link name="%s" target="%s/%s"/>\n</group>\n'

        dimbg = '<dimensions rank="%s">\n'
        dim = '<dim index="%s" value="%s"/>\n'
        dimend = '</dimensions>\n'

        arr = [
            {"name": "client_short", "full_name": "ttestp09/testts/t1r228",
             "source": "ttestp09/testts/t1r228"},
            {"name": "client_long", "full_name": "ttestp09/testts/t2r228",
             "source": "ttestp09/testts/t1r228/Value"},
            {"name": "myclient_long", "full_name": "ttestp09/testts/t3r228",
             "source": "ttestp09/testts/t1r228/NonExisting"},
            {"name": "myclient", "full_name": "ttestp09/testts/t4r228",
             "source": "ttestp09/testts/t1r228/ImageDouble"},
        ]
        simps2 = TestServerSetUp.TestServerSetUp(
            "ttestp09/testts/t2r228", "S2")
        simps3 = TestServerSetUp.TestServerSetUp(
            "ttestp09/testts/t3r228", "S3")
        simps4 = TestServerSetUp.TestServerSetUp(
            "ttestp09/testts/t4r228", "S4")

        db = PyTango.Database()

        try:
            simps2.setUp()
            simps3.setUp()
            simps4.setUp()
            self._simps.dp.CreateAttribute("DataSource")
            simps2.dp.CreateAttribute("DataSource")
            simps3.dp.CreateAttribute("DataSource")
            simps4.dp.CreateAttribute("DataSource")
            self._simps.dp.DataSource = arr[0]["source"]
            simps2.dp.DataSource = arr[1]["source"]
            simps3.dp.DataSource = arr[2]["source"]
            simps4.dp.DataSource = arr[3]["source"]
            for i, ar in enumerate(arr):
                db.put_device_alias(ar["full_name"], ar["name"])
                cpname = rs.createDynamicComponent([
                    str(json.dumps([ar["name"]]))])

                comp = self._cf.dp.Components([cpname])[0]
                mycps = defbg + groupbg + fieldbg % (ar["name"], "NX_CHAR")
                if i % 2:
                    sso = ar["source"].split("/")
                    mycps += dstango % (
                        ar["name"], "/".join(sso[:-1]), sso[-1])
                else:
                    mycps += dsclient % (ar["name"], ar["name"])
                mycps += fieldend + groupend + groupend
                mycps += link % (ar["name"], self._defaultpath,
                                 ar["name"])
                mycps += groupend + defend

                self.assertEqual(comp, mycps)
        finally:
            for ar in arr:
                if '/' in ar["full_name"]:
                    db.delete_device_alias(ar["name"])

            simps4.tearDown()
            simps3.tearDown()
            simps2.tearDown()

    # constructor test
    # \brief It tests default settings
    def test_create_init_typeshape_tango_nods_attr(self):
        fun = sys._getframe().f_code.co_name
        print "Run: %s.%s() " % (self.__class__.__name__, fun)
        val = {"ConfigDevice": self._cf.dp.name(),
               "WriterDevice": self._wr.dp.name(),
               "Door": 'doortestp09/testts/t1r228',
               "MntGrp": 'nxsmntgrp'}
        rs = self.openRecSelector()
        rs.configDevice = val["ConfigDevice"]
        rs.door = val["Door"]
        rs.mntGrp = val["MntGrp"]
        cnfdef = json.loads(rs.profileConfiguration)

        defbg = '<?xml version="1.0" ?>\n<definition>\n'
        defend = '</definition>\n'
        groupbg = '<group name="scan$var.serialno" type="NXentry">\n' + \
            '<group name="instrument" type="NXinstrument">\n' + \
            '<group name="collection" type="NXcollection">\n'
        groupend = '</group>\n'

        fieldbg = '<field name="%s" type="%s">\n<strategy mode="INIT"/>\n'
        fieldend = '</field>\n'

        dsclient = '<datasource name="%s" type="CLIENT">\n' + \
            '<record name="%s"/>\n</datasource>\n'
        dstango = '<datasource name="%s" type="TANGO">\n' + \
            '<device member="attribute" name="%s"/>\n' + \
            '<record name="%s"/>\n</datasource>\n'

        link = '<group name="data" type="NXdata">\n' + \
            '<link name="%s" target="%s/%s"/>\n</group>\n'
        link = ''
        dimbg = '<dimensions rank="%s">\n'
        dim = '<dim index="%s" value="%s"/>\n'
        dimend = '</dimensions>\n'

        arr = [
            {"name": "client_short", "full_name": "ttestp09/testts/t1r228",
             "source": "ttestp09/testts/t1r228"},
            {"name": "client_long", "full_name": "ttestp09/testts/t2r228",
             "source": "ttestp09/testts/t1r228/Value"},
            {"name": "myclient_long", "full_name": "ttestp09/testts/t3r228",
             "source": "ttestp09/testts/t1r228/NonExisting"},
            {"name": "myclient", "full_name": "ttestp09/testts/t4r228",
             "source": "ttestp09/testts/t1r228/ImageDouble"},
        ]
        simps2 = TestServerSetUp.TestServerSetUp(
            "ttestp09/testts/t2r228", "S2")
        simps3 = TestServerSetUp.TestServerSetUp(
            "ttestp09/testts/t3r228", "S3")
        simps4 = TestServerSetUp.TestServerSetUp(
            "ttestp09/testts/t4r228", "S4")

        db = PyTango.Database()

        try:
            simps2.setUp()
            simps3.setUp()
            simps4.setUp()
            self._simps.dp.CreateAttribute("DataSource")
            simps2.dp.CreateAttribute("DataSource")
            simps3.dp.CreateAttribute("DataSource")
            simps4.dp.CreateAttribute("DataSource")
            self._simps.dp.DataSource = arr[0]["source"]
            simps2.dp.DataSource = arr[1]["source"]
            simps3.dp.DataSource = arr[2]["source"]
            simps4.dp.DataSource = arr[3]["source"]
            for i, ar in enumerate(arr):
                db.put_device_alias(ar["full_name"], ar["name"])
                cpname = rs.createDynamicComponent([
                    "", "",
                    str(json.dumps([ar["name"]]))])
                comp = self._cf.dp.Components([cpname])[0]
                mycps = defbg + groupbg + fieldbg % (ar["name"], "NX_CHAR")
                if i % 2:
                    sso = ar["source"].split("/")
                    mycps += dstango % (
                        ar["name"], "/".join(sso[:-1]), sso[-1])
                else:
                    mycps += dsclient % (ar["name"], ar["name"])
                mycps += fieldend + groupend + groupend
                mycps += link  # % (ar["name"], self._defaultpath,
                              #   ar["name"])
                mycps += groupend + defend

                self.assertEqual(comp, mycps)
#                print comp
        finally:
            for ar in arr:
                if '/' in ar["full_name"]:
                    db.delete_device_alias(ar["name"])

            simps4.tearDown()
            simps3.tearDown()
            simps2.tearDown()

    # constructor test
    # \brief It tests default settings
    def test_create_init_typeshape_tango_nods(self):
        fun = sys._getframe().f_code.co_name
        print "Run: %s.%s() " % (self.__class__.__name__, fun)
        val = {"ConfigDevice": self._cf.dp.name(),
               "WriterDevice": self._wr.dp.name(),
               "Door": 'doortestp09/testts/t1r228',
               "MntGrp": 'nxsmntgrp'}
        rs = self.openRecSelector()
        rs.configDevice = val["ConfigDevice"]
        rs.door = val["Door"]
        rs.mntGrp = val["MntGrp"]
        cnfdef = json.loads(rs.profileConfiguration)

        defbg = '<?xml version="1.0" ?>\n<definition>\n'
        defend = '</definition>\n'
        groupbg = '<group name="scan$var.serialno" type="NXentry">\n' + \
            '<group name="instrument" type="NXinstrument">\n' + \
            '<group name="collection" type="NXcollection">\n'
        groupend = '</group>\n'

        fieldbg = '<field name="%s" type="%s">\n<strategy mode="INIT"/>\n'
        fieldend = '</field>\n'

        dsclient = '<datasource name="%s" type="CLIENT">\n' + \
            '<record name="%s"/>\n</datasource>\n'

        link = '<group name="data" type="NXdata">\n' + \
            '<link name="%s" target="%s/%s"/>\n</group>\n'

        dimbg = '<dimensions rank="%s">\n'
        dim = '<dim index="%s" value="%s"/>\n'
        dimend = '</dimensions>\n'

        for i in range(4):
            for ds, dsxml in self.smydss.items():
                ms = self.smydsspar[ds]
                sds = ds.split("_")
                tp = sds[1]
                cnf = dict(cnfdef)
                labels = {}
                paths = {}
                links = {}
                types = {}
                shapes = {}

                if i == 0:
                    cnf["DefaultDynamicLinks"] = False
                    cnf["DefaultDynamicPath"] = self._defaultpath
                elif i == 1:
                    cnf["DefaultDynamicLinks"] = True
                    cnf["DefaultDynamicPath"] = self._defaultpath
                    links = {ds: True}
                elif i == 2:
                    links = {ds: False}
                elif i == 3:
                    links = {ds: True}
                cnf["ChannelProperties"] = json.dumps(
                    {
                        "label": labels,
                        "nexus_path": paths,
                        "link": links,
                        "data_type": types,
                        "shape": shapes
                    }
                )
                rs.profileConfiguration = str(json.dumps(cnf))
                cpname = rs.createDynamicComponent([
                    "", "",
                    str(json.dumps([ds]))])

                comp = self._cf.dp.Components([cpname])[0]

                nxstype = 'NX_CHAR'
                mycps = defbg + groupbg + fieldbg % (
                    ds.lower(), nxstype)

                mycps += dsclient % (ds, ds)
                mstr = ""

                mycps += mstr
                mycps += fieldend + groupend + groupend
                lk = link % (ds.lower(), self._defaultpath,
                             ds.lower())
                mycps += lk if i % 2 else ""
                mycps += groupend + defend

                self.assertEqual(comp, mycps)

    # constructor test
    # \brief It tests default settings
    def test_create_sel_typeshape_tango(self):
        fun = sys._getframe().f_code.co_name
        print "Run: %s.%s() " % (self.__class__.__name__, fun)
        val = {"ConfigDevice": self._cf.dp.name(),
               "WriterDevice": self._wr.dp.name(),
               "Door": 'doortestp09/testts/t1r228',
               "MntGrp": 'nxsmntgrp'}
        rs = self.openRecSelector()
        rs.configDevice = val["ConfigDevice"]
        rs.door = val["Door"]
        rs.mntGrp = val["MntGrp"]
        cnfdef = json.loads(rs.profileConfiguration)

        defbg = '<?xml version="1.0" ?>\n<definition>\n'
        defend = '</definition>\n'
        groupbg = '<group name="scan$var.serialno" type="NXentry">\n' + \
            '<group name="instrument" type="NXinstrument">\n' + \
            '<group name="collection" type="NXcollection">\n'
        groupend = '</group>\n'

        fieldbg = '<field name="%s" type="%s">\n<strategy mode="STEP"/>\n'
        fieldend = '</field>\n'

        link = '<group name="data" type="NXdata">\n' + \
            '<link name="%s" target="%s/%s"/>\n</group>\n'

        dimbg = '<dimensions rank="%s">\n'
        dim = '<dim index="%s" value="%s"/>\n'
        dimend = '</dimensions>\n'

        self._cf.dp.SetCommandVariable(["DSDICT", json.dumps(self.smydss)])
        for i, nxstp in enumerate(self._npTn.values()):
            for ds, dsxml in self.smydss.items():
                ms = self.smydsspar[ds]
                ms2 = [self._rnd.randint(0, 3000)
                       for _ in range(self._rnd.randint(0, 3))]
                lbl = self.getRandomName(20)
                sds = ds.split("_")
                tp = sds[1]
                cnf = dict(cnfdef)
                labels = {}
                paths = {}
                links = {}
                types = {}
                shapes = {}

                if i == 0:
                    cnf["DefaultDynamicLinks"] = False
                    cnf["DefaultDynamicPath"] = self._defaultpath
                    types = {ds: nxstp}
                    shapes = {ds: ms2}
                elif i == 1:
                    cnf["DefaultDynamicLinks"] = True
                    cnf["DefaultDynamicPath"] = self._defaultpath
                    types = {ds: nxstp}
                    shapes = {ds: ms2}
                elif i == 2:
                    links = {ds: False}
                    types = {ds: nxstp}
                    shapes = {ds: ms2}
                elif i == 3:
                    links = {ds: True}
                    types = {ds: nxstp}
                    shapes = {ds: ms2}
                elif i == 4:
                    cnf["DefaultDynamicLinks"] = True
                    cnf["DefaultDynamicPath"] = self._defaultpath
                    links = {ds: False}
                    types = {ds: nxstp}
                    shapes = {ds: ms2}
                elif i == 5:
                    cnf["DefaultDynamicLinks"] = False
                    cnf["DefaultDynamicPath"] = self._defaultpath
                    links = {ds: True}
                    types = {ds: nxstp}
                    shapes = {ds: ms2}
                elif i == 6:
                    cnf["DefaultDynamicLinks"] = False
                    cnf["DefaultDynamicPath"] = self._defaultpath
                    links = {"dssd": True}
                    types = {ds: nxstp}
                    shapes = {ds: ms2}
                elif i == 7:
                    labels = {ds: lbl}
                    types = {ds: nxstp}
                    shapes = {ds: ms2}
                elif i == 8:
                    pass
                    cnf["DefaultDynamicLinks"] = False
                    cnf["DefaultDynamicPath"] = self._defaultpath
                    labels = {ds: lbl}
                    types = {ds: nxstp}
                    shapes = {ds: ms2}
                elif i == 9:
                    cnf["DefaultDynamicLinks"] = True
                    cnf["DefaultDynamicPath"] = self._defaultpath
                    labels = {ds: lbl}
                    types = {ds: nxstp}
                    shapes = {ds: ms2}
                elif i == 10:
                    labels = {ds: lbl}
                    links = {lbl: False}
                    types = {ds: nxstp}
                    shapes = {ds: ms2}
                elif i == 11:
                    labels = {ds: lbl}
                    links = {lbl: True}
                    types = {ds: nxstp}
                    shapes = {ds: ms2}
                elif i == 12:
                    cnf["DefaultDynamicLinks"] = True
                    cnf["DefaultDynamicPath"] = self._defaultpath
                    labels = {ds: lbl}
                    links = {lbl: False}
                    types = {ds: nxstp}
                    shapes = {ds: ms2}
                elif i == 13:
                    cnf["DefaultDynamicLinks"] = False
                    cnf["DefaultDynamicPath"] = self._defaultpath
                    labels = {ds: lbl}
                    links = {lbl: True}
                    types = {ds: nxstp}
                    shapes = {ds: ms2}
                elif i == 14:
                    cnf["DefaultDynamicLinks"] = False
                    cnf["DefaultDynamicPath"] = self._defaultpath
                    labels = {ds: lbl}
                    links = {"dssd": True}
                    types = {ds: nxstp}
                    shapes = {ds: ms2}
                elif i == 15:
                    labels = {ds: lbl}
                    types = {ds: nxstp}
                    shapes = {ds: ms2}

                cnf["ChannelProperties"] = json.dumps(
                    {
                        "label": labels,
                        "nexus_path": paths,
                        "link": links,
                        "data_type": types,
                        "shape": shapes
                    }
                )
#                print "I = ", i
                cnf["DataSourceSelection"] = json.dumps({ds: True})
                rs.profileConfiguration = str(json.dumps(cnf))
                cpname = rs.createDynamicComponent([])

#                dc.setStepDSources([ds])
#                cpname = dc.create()
                comp = self._cf.dp.Components([cpname])[0]

                indom = xml.dom.minidom.parseString(dsxml)
                dss = indom.getElementsByTagName("datasource")
                nxstype = nxstp
                mycps = defbg + groupbg + fieldbg % (
                    ds.lower(), nxstype)

                mycps += dss[0].toprettyxml(indent="")
                mstr = ""
                if ms2:
                    mstr += dimbg % len(ms2)
                    for ind, val in enumerate(ms2):
                        mstr += dim % (ind + 1, val)
                    mstr += dimend

                mycps += mstr
                mycps += fieldend + groupend + groupend
                lk = link % (ds.lower(), self._defaultpath,
                             ds.lower())
                mycps += lk if i % 2 else ""
                mycps += groupend + defend

                self.assertEqual(comp, mycps)

    # constructor test
    # \brief It tests default settings
    def test_create_step_typeshape_tango(self):
        fun = sys._getframe().f_code.co_name
        print "Run: %s.%s() " % (self.__class__.__name__, fun)
        val = {"ConfigDevice": self._cf.dp.name(),
               "WriterDevice": self._wr.dp.name(),
               "Door": 'doortestp09/testts/t1r228',
               "MntGrp": 'nxsmntgrp'}
        rs = self.openRecSelector()
        rs.configDevice = val["ConfigDevice"]
        rs.door = val["Door"]
        rs.mntGrp = val["MntGrp"]
        cnfdef = json.loads(rs.profileConfiguration)

        defbg = '<?xml version="1.0" ?>\n<definition>\n'
        defend = '</definition>\n'
        groupbg = '<group name="scan$var.serialno" type="NXentry">\n' + \
            '<group name="instrument" type="NXinstrument">\n' + \
            '<group name="collection" type="NXcollection">\n'
        groupend = '</group>\n'

        fieldbg = '<field name="%s" type="%s">\n<strategy mode="STEP"/>\n'
        fieldend = '</field>\n'

        link = '<group name="data" type="NXdata">\n' + \
            '<link name="%s" target="%s/%s"/>\n</group>\n'

        dimbg = '<dimensions rank="%s">\n'
        dim = '<dim index="%s" value="%s"/>\n'
        dimend = '</dimensions>\n'

        self._cf.dp.SetCommandVariable(["DSDICT", json.dumps(self.smydss)])
        for i, nxstp in enumerate(self._npTn.values()):
            for ds, dsxml in self.smydss.items():
                ms = self.smydsspar[ds]
                ms2 = [self._rnd.randint(0, 3000)
                       for _ in range(self._rnd.randint(0, 3))]
                lbl = self.getRandomName(20)
                sds = ds.split("_")
                tp = sds[1]
                cnf = dict(cnfdef)
                labels = {}
                paths = {}
                links = {}
                types = {}
                shapes = {}

                if i == 0:
                    cnf["DefaultDynamicLinks"] = False
                    cnf["DefaultDynamicPath"] = self._defaultpath
                    types = {ds: nxstp}
                    shapes = {ds: ms2}
                elif i == 1:
                    cnf["DefaultDynamicLinks"] = True
                    cnf["DefaultDynamicPath"] = self._defaultpath
                    types = {ds: nxstp}
                    shapes = {ds: ms2}
                elif i == 2:
                    links = {ds: False}
                    types = {ds: nxstp}
                    shapes = {ds: ms2}
                elif i == 3:
                    links = {ds: True}
                    types = {ds: nxstp}
                    shapes = {ds: ms2}
                elif i == 4:
                    cnf["DefaultDynamicLinks"] = True
                    cnf["DefaultDynamicPath"] = self._defaultpath
                    links = {ds: False}
                    types = {ds: nxstp}
                    shapes = {ds: ms2}
                elif i == 5:
                    cnf["DefaultDynamicLinks"] = False
                    cnf["DefaultDynamicPath"] = self._defaultpath
                    links = {ds: True}
                    types = {ds: nxstp}
                    shapes = {ds: ms2}
                elif i == 6:
                    cnf["DefaultDynamicLinks"] = False
                    cnf["DefaultDynamicPath"] = self._defaultpath
                    links = {"dssd": True}
                    types = {ds: nxstp}
                    shapes = {ds: ms2}
                elif i == 7:
                    labels = {ds: lbl}
                    types = {ds: nxstp}
                    shapes = {ds: ms2}
                elif i == 8:
                    pass
                    cnf["DefaultDynamicLinks"] = False
                    cnf["DefaultDynamicPath"] = self._defaultpath
                    labels = {ds: lbl}
                    types = {ds: nxstp}
                    shapes = {ds: ms2}
                elif i == 9:
                    cnf["DefaultDynamicLinks"] = True
                    cnf["DefaultDynamicPath"] = self._defaultpath
                    labels = {ds: lbl}
                    types = {ds: nxstp}
                    shapes = {ds: ms2}
                elif i == 10:
                    labels = {ds: lbl}
                    links = {lbl: False}
                    types = {ds: nxstp}
                    shapes = {ds: ms2}
                elif i == 11:
                    labels = {ds: lbl}
                    links = {lbl: True}
                    types = {ds: nxstp}
                    shapes = {ds: ms2}
                elif i == 12:
                    cnf["DefaultDynamicLinks"] = True
                    cnf["DefaultDynamicPath"] = self._defaultpath
                    labels = {ds: lbl}
                    links = {lbl: False}
                    types = {ds: nxstp}
                    shapes = {ds: ms2}
                elif i == 13:
                    cnf["DefaultDynamicLinks"] = False
                    cnf["DefaultDynamicPath"] = self._defaultpath
                    labels = {ds: lbl}
                    links = {lbl: True}
                    types = {ds: nxstp}
                    shapes = {ds: ms2}
                elif i == 14:
                    cnf["DefaultDynamicLinks"] = False
                    cnf["DefaultDynamicPath"] = self._defaultpath
                    labels = {ds: lbl}
                    links = {"dssd": True}
                    types = {ds: nxstp}
                    shapes = {ds: ms2}
                elif i == 15:
                    labels = {ds: lbl}
                    types = {ds: nxstp}
                    shapes = {ds: ms2}

                cnf["ChannelProperties"] = json.dumps(
                    {
                        "label": labels,
                        "nexus_path": paths,
                        "link": links,
                        "data_type": types,
                        "shape": shapes
                    }
                )
#                print "I = ", i
                rs.profileConfiguration = str(json.dumps(cnf))
                cpname = rs.createDynamicComponent([
                    str(json.dumps([ds]))])

#                dc.setStepDSources([ds])
#                cpname = dc.create()
                comp = self._cf.dp.Components([cpname])[0]

                indom = xml.dom.minidom.parseString(dsxml)
                dss = indom.getElementsByTagName("datasource")
                nxstype = nxstp
                mycps = defbg + groupbg + fieldbg % (
                    ds.lower(), nxstype)

                mycps += dss[0].toprettyxml(indent="")
                mstr = ""
                if ms2:
                    mstr += dimbg % len(ms2)
                    for ind, val in enumerate(ms2):
                        mstr += dim % (ind + 1, val)
                    mstr += dimend

                mycps += mstr
                mycps += fieldend + groupend + groupend
                lk = link % (ds.lower(), self._defaultpath,
                             ds.lower())
                mycps += lk if i % 2 else ""
                mycps += groupend + defend

                self.assertEqual(comp, mycps)

    # constructor test
    # \brief It tests default settings
    def test_create_init_typeshape_tango(self):
        fun = sys._getframe().f_code.co_name
        print "Run: %s.%s() " % (self.__class__.__name__, fun)
        val = {"ConfigDevice": self._cf.dp.name(),
               "WriterDevice": self._wr.dp.name(),
               "Door": 'doortestp09/testts/t1r228',
               "MntGrp": 'nxsmntgrp'}
        rs = self.openRecSelector()
        rs.configDevice = val["ConfigDevice"]
        rs.door = val["Door"]
        rs.mntGrp = val["MntGrp"]
        cnfdef = json.loads(rs.profileConfiguration)

        defbg = '<?xml version="1.0" ?>\n<definition>\n'
        defend = '</definition>\n'
        groupbg = '<group name="scan$var.serialno" type="NXentry">\n' + \
            '<group name="instrument" type="NXinstrument">\n' + \
            '<group name="collection" type="NXcollection">\n'
        groupend = '</group>\n'

        fieldbg = '<field name="%s" type="%s">\n<strategy mode="INIT"/>\n'
        fieldend = '</field>\n'

        link = '<group name="data" type="NXdata">\n' + \
            '<link name="%s" target="%s/%s"/>\n</group>\n'

        dimbg = '<dimensions rank="%s">\n'
        dim = '<dim index="%s" value="%s"/>\n'
        dimend = '</dimensions>\n'

        self._cf.dp.SetCommandVariable(["DSDICT", json.dumps(self.smydss)])
        for i, nxstp in enumerate(self._npTn.values()):
            for ds, dsxml in self.smydss.items():
                ms = self.smydsspar[ds]
                ms2 = [self._rnd.randint(0, 3000)
                       for _ in range(self._rnd.randint(0, 3))]
                lbl = self.getRandomName(20)
                sds = ds.split("_")
                tp = sds[1]
                cnf = dict(cnfdef)
                labels = {}
                paths = {}
                links = {}
                types = {}
                shapes = {}
                if i == 0:
                    cnf["DefaultDynamicLinks"] = False
                    cnf["DefaultDynamicPath"] = self._defaultpath
                    types = {ds: nxstp}
                    shapes = {ds: ms2}
                elif i == 1:
                    cnf["DefaultDynamicLinks"] = True
                    cnf["DefaultDynamicPath"] = self._defaultpath
                    types = {ds: nxstp}
                    shapes = {ds: ms2}
                    links = {ds: True}
                elif i == 2:
                    links = {ds: False}
                    types = {ds: nxstp}
                    shapes = {ds: ms2}
                elif i == 3:
                    links = {ds: True}
                    types = {ds: nxstp}
                    shapes = {ds: ms2}
                elif i == 4:
                    cnf["DefaultDynamicLinks"] = True
                    cnf["DefaultDynamicPath"] = self._defaultpath
                    links = {ds: False}
                    types = {ds: nxstp}
                    shapes = {ds: ms2}
                elif i == 5:
                    cnf["DefaultDynamicLinks"] = False
                    cnf["DefaultDynamicPath"] = self._defaultpath
                    links = {ds: True}
                    types = {ds: nxstp}
                    shapes = {ds: ms2}
                elif i == 6:
                    cnf["DefaultDynamicLinks"] = False
                    cnf["DefaultDynamicPath"] = self._defaultpath
                    links = {"dssd": True}
                    types = {ds: nxstp}
                    shapes = {ds: ms2}
                elif i == 7:
                    labels = {ds: lbl}
                    types = {ds: nxstp}
                    shapes = {ds: ms2}
                    links = {ds: True}
                elif i == 8:
                    pass
                    cnf["DefaultDynamicLinks"] = False
                    cnf["DefaultDynamicPath"] = self._defaultpath
                    labels = {ds: lbl}
                    types = {ds: nxstp}
                    shapes = {ds: ms2}
                elif i == 9:
                    links = {ds: True}
                    cnf["DefaultDynamicLinks"] = True
                    cnf["DefaultDynamicPath"] = self._defaultpath
                    labels = {ds: lbl}
                    types = {ds: nxstp}
                    shapes = {ds: ms2}
                elif i == 10:
                    labels = {ds: lbl}
                    links = {lbl: False}
                    types = {ds: nxstp}
                    shapes = {ds: ms2}
                elif i == 11:
                    labels = {ds: lbl}
                    links = {lbl: True}
                    types = {ds: nxstp}
                    shapes = {ds: ms2}
                elif i == 12:
                    cnf["DefaultDynamicLinks"] = True
                    cnf["DefaultDynamicPath"] = self._defaultpath
                    labels = {ds: lbl}
                    links = {lbl: False}
                    types = {ds: nxstp}
                    shapes = {ds: ms2}
                elif i == 13:
                    cnf["DefaultDynamicLinks"] = False
                    cnf["DefaultDynamicPath"] = self._defaultpath
                    labels = {ds: lbl}
                    links = {lbl: True}
                    types = {ds: nxstp}
                    shapes = {ds: ms2}
                elif i == 14:
                    cnf["DefaultDynamicLinks"] = False
                    cnf["DefaultDynamicPath"] = self._defaultpath
                    labels = {ds: lbl}
                    links = {"dssd": True}
                    types = {ds: nxstp}
                    shapes = {ds: ms2}
                elif i == 15:
                    labels = {ds: lbl}
                    links = {ds: True}
                    types = {ds: nxstp}
                    shapes = {ds: ms2}

                cnf["ChannelProperties"] = json.dumps(
                    {
                        "label": labels,
                        "nexus_path": paths,
                        "link": links,
                        "data_type": types,
                        "shape": shapes
                    }
                )
#                print "I = ", i
                rs.profileConfiguration = str(json.dumps(cnf))
                cpname = rs.createDynamicComponent([
                    "", "",
                    str(json.dumps([ds]))])
                comp = self._cf.dp.Components([cpname])[0]

                indom = xml.dom.minidom.parseString(dsxml)
                dss = indom.getElementsByTagName("datasource")
                nxstype = nxstp
                mycps = defbg + groupbg + fieldbg % (
                    ds.lower(), nxstype)

                mycps += dss[0].toprettyxml(indent="")
                mstr = ""
                if ms2:
                    mstr += dimbg % len(ms2)
                    for ind, val in enumerate(ms2):
                        mstr += dim % (ind + 1, val)
                    mstr += dimend

                mycps += mstr
                mycps += fieldend + groupend + groupend
                lk = link % (ds.lower(), self._defaultpath,
                             ds.lower())
                mycps += lk if i % 2 else ""
                mycps += groupend + defend

                self.assertEqual(comp, mycps)

    # constructor test
    # \brief It tests default settings
    def test_create_init_typeshape_tango_wol(self):
        fun = sys._getframe().f_code.co_name
        print "Run: %s.%s() " % (self.__class__.__name__, fun)
        val = {"ConfigDevice": self._cf.dp.name(),
               "WriterDevice": self._wr.dp.name(),
               "Door": 'doortestp09/testts/t1r228',
               "MntGrp": 'nxsmntgrp'}
        rs = self.openRecSelector()
        rs.configDevice = val["ConfigDevice"]
        rs.door = val["Door"]
        rs.mntGrp = val["MntGrp"]
        cnfdef = json.loads(rs.profileConfiguration)

        defbg = '<?xml version="1.0" ?>\n<definition>\n'
        defend = '</definition>\n'
        groupbg = '<group name="scan$var.serialno" type="NXentry">\n' + \
            '<group name="instrument" type="NXinstrument">\n' + \
            '<group name="collection" type="NXcollection">\n'
        groupend = '</group>\n'

        fieldbg = '<field name="%s" type="%s">\n<strategy mode="INIT"/>\n'
        fieldend = '</field>\n'

        link = '<group name="data" type="NXdata">\n' + \
            '<link name="%s" target="%s/%s"/>\n</group>\n'

        dimbg = '<dimensions rank="%s">\n'
        dim = '<dim index="%s" value="%s"/>\n'
        dimend = '</dimensions>\n'

        self._cf.dp.SetCommandVariable(["DSDICT", json.dumps(self.smydss)])
        self._cf.dp.SetCommandVariable(["CPDICT", json.dumps(self.smydss)])
        for i, nxstp in enumerate(self._npTn.values()):
            print i
            for ds, dsxml in self.smydss.items():
                ms = self.smydsspar[ds]
                ms2 = [self._rnd.randint(0, 3000)
                       for _ in range(self._rnd.randint(0, 3))]
                lbl = self.getRandomName(20)
                sds = ds.split("_")
                tp = sds[1]
                cnf = dict(cnfdef)
                labels = {}
                paths = {}
                links = {}
                types = {}
                shapes = {}
                if i == 0:
                    cnf["DefaultDynamicPath"] = self._defaultpath
                    types = {ds: nxstp}
                    shapes = {ds: ms2}
                elif i == 1:
                    cnf["DefaultDynamicLinks"] = True
                    links = {ds: True}
                    cnf["DefaultDynamicPath"] = self._defaultpath
                    types = {ds: nxstp}
                    shapes = {ds: ms2}
                elif i == 2:
                    types = {ds: nxstp}
                    shapes = {ds: ms2}
                elif i == 3:
                    links = {ds: True}
                    types = {ds: nxstp}
                    shapes = {ds: ms2}
                elif i == 4:
                    cnf["DefaultDynamicPath"] = self._defaultpath
                    types = {ds: nxstp}
                    shapes = {ds: ms2}
                elif i == 5:
                    cnf["DefaultDynamicLinks"] = False
                    cnf["DefaultDynamicPath"] = self._defaultpath
                    links = {ds: True}
                    types = {ds: nxstp}
                    shapes = {ds: ms2}
                elif i == 6:
                    cnf["DefaultDynamicPath"] = self._defaultpath
                    links = {"dssd": True}
                    types = {ds: nxstp}
                    shapes = {ds: ms2}
                elif i == 7:
                    labels = {ds: lbl}
                    links = {ds: True}
                    types = {ds: nxstp}
                    shapes = {ds: ms2}
                elif i == 8:
                    pass
                    cnf["DefaultDynamicPath"] = self._defaultpath
                    labels = {ds: lbl}
                    types = {ds: nxstp}
                    shapes = {ds: ms2}
                elif i == 9:
                    links = {ds: True}
                    cnf["DefaultDynamicLinks"] = True
                    cnf["DefaultDynamicPath"] = self._defaultpath
                    labels = {ds: lbl}
                    types = {ds: nxstp}
                    shapes = {ds: ms2}
                elif i == 10:
                    labels = {ds: lbl}
                    types = {ds: nxstp}
                    shapes = {ds: ms2}
                elif i == 11:
                    labels = {ds: lbl}
                    links = {lbl: True}
                    types = {ds: nxstp}
                    shapes = {ds: ms2}
                elif i == 12:
                    cnf["DefaultDynamicLinks"] = True
                    cnf["DefaultDynamicPath"] = self._defaultpath
                    labels = {ds: lbl}
                    types = {ds: nxstp}
                    shapes = {ds: ms2}
                elif i == 13:
                    cnf["DefaultDynamicLinks"] = False
                    cnf["DefaultDynamicPath"] = self._defaultpath
                    labels = {ds: lbl}
                    links = {lbl: True}
                    types = {ds: nxstp}
                    shapes = {ds: ms2}
                elif i == 14:
                    cnf["DefaultDynamicPath"] = self._defaultpath
                    labels = {ds: lbl}
                    links = {"dssd": True}
                    types = {ds: nxstp}
                    shapes = {ds: ms2}
                elif i == 15:
                    labels = {ds: lbl}
                    links = {ds: True}
                    types = {ds: nxstp}
                    shapes = {ds: ms2}

                cnf["ChannelProperties"] = json.dumps(
                    {
                        "label": labels,
                        "nexus_path": paths,
                        "link": links,
                        "data_type": types,
                        "shape": shapes
                    }
                )
#                print "I = ", i
                if i % 2 == 0:
                    cnf["ComponentSelection"] = str(json.dumps({ds: True}))
                rs.profileConfiguration = str(json.dumps(cnf))
                cpname = rs.createDynamicComponent([
                    "", "",
                    str(json.dumps([ds]))])
                comp = self._cf.dp.Components([cpname])[0]

                indom = xml.dom.minidom.parseString(dsxml)
                dss = indom.getElementsByTagName("datasource")
                nxstype = nxstp
                mycps = defbg + groupbg + fieldbg % (
                    ds.lower(), nxstype)

                mycps += dss[0].toprettyxml(indent="")
                mstr = ""
                if ms2:
                    mstr += dimbg % len(ms2)
                    for ind, val in enumerate(ms2):
                        mstr += dim % (ind + 1, val)
                    mstr += dimend

                mycps += mstr
                mycps += fieldend + groupend + groupend
                lk = link % (ds.lower(), self._defaultpath,
                             ds.lower())
                mycps += lk if i % 2 else ""
                mycps += groupend + defend

                self.assertEqual(comp, mycps)

    # constructor test
    # \brief It tests default settings
    def test_create_step_fieldpath(self):
        fun = sys._getframe().f_code.co_name
        print "Run: %s.%s() " % (self.__class__.__name__, fun)
        val = {"ConfigDevice": self._cf.dp.name(),
               "WriterDevice": self._wr.dp.name(),
               "Door": 'doortestp09/testts/t1r228',
               "MntGrp": 'nxsmntgrp'}
        rs = self.openRecSelector()
        rs.configDevice = val["ConfigDevice"]
        rs.door = val["Door"]
        rs.mntGrp = val["MntGrp"]
        cnfdef = json.loads(rs.profileConfiguration)
        cps = {
            "shapetype":
            '<?xml version="1.0" ?>\n<definition>\n'
            '<group name="scan$var.serialno" type="NXentry">\n'
            '<group name="instrument" type="NXinstrument">\n'
            '<group name="collection" type="NXcollection">\n%s'
            '</group>\n</group>\n%s</group>\n</definition>\n',
        }

        defbg = '<?xml version="1.0" ?>\n<definition>\n'
        defend = '</definition>\n'
        groupbg = '<group name="%s" type="%s">\n'
        groupend = '</group>\n'

        field = '<field name="%s" type="%s">\n<strategy mode="STEP"/>\n' + \
            '<datasource name="%s" type="CLIENT">\n' + \
            '<record name="%s"/>\n</datasource>\n%s</field>\n'
        fieldbg = '<field name="%s" type="%s">\n<strategy mode="STEP"/>\n'
        fieldend = '</field>\n'

        link = '<group name="data" type="NXdata">\n' + \
            '<link name="%s" target="%s/%s"/>\n</group>\n'

        dimbg = '<dimensions rank="%s">\n'
        dim = '<dim index="%s" value="%s"/>\n'
        dimend = '</dimensions>\n'

        dname = "__dynamic_component__"

        self._cf.dp.SetCommandVariable(["DSDICT", json.dumps(self.smydss)])

        db = PyTango.Database()
        try:
            for i in range(8):
#                print "I = ", i
                for ds, dsxml in self.smydss.items():
                    ms = self.smydsspar[ds]
                    sds = ds.split("_")
                    tp = sds[1]
                    indom = xml.dom.minidom.parseString(dsxml)
                    dss = indom.getElementsByTagName("datasource")
                    if not ds.startswith("client_") and sds[1] != 'encoded':
                        nxstp = self._npTn2[tp]
                    else:
                        nxstp = 'NX_CHAR'
#                    dc = DynamicComponent(self._cf.dp)

                    lbl = self.getRandomName(20)
                    fieldname = self.getRandomName(20)
#                    print "FIELD", fieldname
                    path = [
                        (self.getRandomName(20)
                         if self._rnd.randint(0, 1) else None,
                         ("NX" + self.getRandomName(20))
                         if self._rnd.randint(0, 1) else None)
                        for _ in range(self._rnd.randint(0, 10))]
#                    print "path0", path, len(path)
                    path = [nd for nd in path if (
                            nd != (None, None) and
                            nd[0] and not nd[0].startswith("NX"))]
#                    print "path1", path, len(path)
                    mypath = ""
                    for node in path:
                        mypath += "/"
                        if node[0]:
                            mypath += node[0]
                            if node[1]:
                                mypath += ":"
                        if node[1]:
                            mypath += node[1]
#                    mypath += fieldname
#                    print "path2", path, len(path)
#                    print "PATH", path, mypath
#                    print "TP = ", tp
                    tmptp = self._rnd.choice(self._npTn.keys())
                    cnf = dict(cnfdef)
                    labels = {}
                    paths = {}
                    links = {}
                    types = {}
                    shapes = {}

                    if i == 0:
                        cnf["DefaultDynamicLinks"] = False
                        cnf["DefaultDynamicPath"] = mypath
                    elif i == 1:
                        cnf["DefaultDynamicLinks"] = True
                        cnf["DefaultDynamicPath"] = mypath
                    elif i == 2:
                        paths = {ds: mypath + "/" + fieldname}
                        links = {ds: False}
                    elif i == 3:
                        paths = {ds: mypath + "/" + fieldname}
                        links = {ds: True}
                    elif i == 4:
                        cnf["DefaultDynamicLinks"] = False
                        cnf["DefaultDynamicPath"] = mypath
                        labels = {ds: lbl}
                    elif i == 5:
                        cnf["DefaultDynamicLinks"] = True
                        cnf["DefaultDynamicPath"] = mypath
                        labels = {ds: lbl}
                    elif i == 6:
                        labels = {ds: lbl}
                        paths = {ds: mypath + "/" + fieldname}
                        links = {ds: False}
                    elif i == 7:
                        labels = {ds: lbl}
                        paths = {ds: mypath + "/" + fieldname}
                        links = {ds: True}
                    cnf["ChannelProperties"] = json.dumps(
                        {
                            "label": labels,
                            "nexus_path": paths,
                            "link": links,
                            "data_type": types,
                            "shape": shapes
                        }
                    )
#                    print "I = ", i
                    rs.profileConfiguration = str(json.dumps(cnf))
                    cpname = rs.createDynamicComponent([
                        str(json.dumps([ds]))])
                    mstr = ""
                    if ms:
                        mstr += dimbg % len(ms)
                        for ind, val in enumerate(ms):
                            mstr += dim % (ind + 1, val)
                        mstr += dimend

                    comp = self._cf.dp.Components([cpname])[0]
                    lk = link % (ds, mypath, ds)
                    if i % 4 < 2:
                        fd = fieldbg % (ds.lower(), nxstp)
                    else:
                        fname = fieldname.lower()
                        fd = fieldbg % (fieldname.lower(), nxstp)
                    fd += dss[0].toprettyxml(indent="") + mstr + fieldend

                    if path or i % 4 > 1:

                        if i % 4 < 2:
                            lk = link % (ds.lower(), mypath, ds.lower())
                        else:
                            lk = link % (fieldname.lower(), mypath,
                                         fieldname.lower())
                        mycps = defbg
                        for nm, gtp in path:
                            if not nm:
                                nm = gtp[2:]
                            if not gtp:
                                gtp = 'NX' + nm
                            mycps += groupbg % (nm, gtp)
                        mycps += fd

                        for j in range(len(path) - 1):
                            mycps += groupend
                        mycps += lk if i % 2 else ""
                        mycps += groupend
                        mycps += defend

                        mycps2 = defbg
                        for k, (nm, gtp) in enumerate(path):
                            if not nm:
                                nm = gtp[2:]
                            if not gtp:
                                gtp = 'NX' + nm
                            mycps2 += groupbg % (nm, gtp)
                            if not k:
                                mycps2 += lk if i % 2 else ""
                        mycps2 += fd

                        for _ in path:
                            mycps2 += groupend
                        mycps2 += defend
#                        print "FIRST"
                    else:
                        if i % 4 < 2:
                            lk = link % (ds.lower(),
                                         self._defaultpath, ds.lower())
                        else:
                            lk = link % (fieldname.lower(), self._defaultpath,
                                         fieldname.lower())
                        mycps = cps["shapetype"] % (
                            fd,
                            lk if i % 2 else "")
                        mycps2 = mycps
                    try:
                        self.assertEqual(comp, mycps2)
                    except:
                        self.assertEqual(comp, mycps)
        finally:
            pass

    # constructor test
    # \brief It tests default settings
    def test_create_sel_fieldpath(self):
        fun = sys._getframe().f_code.co_name
        print "Run: %s.%s() " % (self.__class__.__name__, fun)
        val = {"ConfigDevice": self._cf.dp.name(),
               "WriterDevice": self._wr.dp.name(),
               "Door": 'doortestp09/testts/t1r228',
               "MntGrp": 'nxsmntgrp'}
        rs = self.openRecSelector()
        rs.configDevice = val["ConfigDevice"]
        rs.door = val["Door"]
        rs.mntGrp = val["MntGrp"]
        cnfdef = json.loads(rs.profileConfiguration)
        cps = {
            "shapetype":
            '<?xml version="1.0" ?>\n<definition>\n'
            '<group name="scan$var.serialno" type="NXentry">\n'
            '<group name="instrument" type="NXinstrument">\n'
            '<group name="collection" type="NXcollection">\n%s'
            '</group>\n</group>\n%s</group>\n</definition>\n',
        }

        defbg = '<?xml version="1.0" ?>\n<definition>\n'
        defend = '</definition>\n'
        groupbg = '<group name="%s" type="%s">\n'
        groupend = '</group>\n'

        field = '<field name="%s" type="%s">\n<strategy mode="STEP"/>\n' + \
            '<datasource name="%s" type="CLIENT">\n' + \
            '<record name="%s"/>\n</datasource>\n%s</field>\n'
        fieldbg = '<field name="%s" type="%s">\n<strategy mode="STEP"/>\n'
        fieldend = '</field>\n'

        link = '<group name="data" type="NXdata">\n' + \
            '<link name="%s" target="%s/%s"/>\n</group>\n'

        dimbg = '<dimensions rank="%s">\n'
        dim = '<dim index="%s" value="%s"/>\n'
        dimend = '</dimensions>\n'

        dname = "__dynamic_component__"

        self._cf.dp.SetCommandVariable(["DSDICT", json.dumps(self.smydss)])

        db = PyTango.Database()
        try:
            for i in range(8):
#                print "I = ", i
                for ds, dsxml in self.smydss.items():
                    ms = self.smydsspar[ds]
                    sds = ds.split("_")
                    tp = sds[1]
                    indom = xml.dom.minidom.parseString(dsxml)
                    dss = indom.getElementsByTagName("datasource")
                    if not ds.startswith("client_") and sds[1] != 'encoded':
                        nxstp = self._npTn2[tp]
                    else:
                        nxstp = 'NX_CHAR'
#                    dc = DynamicComponent(self._cf.dp)

                    lbl = self.getRandomName(20)
                    fieldname = self.getRandomName(20)
#                    print "FIELD", fieldname
                    path = [
                        (self.getRandomName(20)
                         if self._rnd.randint(0, 1) else None,
                         ("NX" + self.getRandomName(20))
                         if self._rnd.randint(0, 1) else None)
                        for _ in range(self._rnd.randint(0, 10))]
#                    print "path0", path, len(path)
                    path = [nd for nd in path if (
                            nd != (None, None) and
                            nd[0] and not nd[0].startswith("NX"))]
#                    print "path1", path, len(path)
                    mypath = ""
                    for node in path:
                        mypath += "/"
                        if node[0]:
                            mypath += node[0]
                            if node[1]:
                                mypath += ":"
                        if node[1]:
                            mypath += node[1]
#                    mypath += fieldname
#                    print "path2", path, len(path)
#                    print "PATH", path, mypath
#                    print "TP = ", tp
                    tmptp = self._rnd.choice(self._npTn.keys())
                    cnf = dict(cnfdef)
                    labels = {}
                    paths = {}
                    links = {}
                    types = {}
                    shapes = {}

                    if i == 0:
                        cnf["DefaultDynamicLinks"] = False
                        cnf["DefaultDynamicPath"] = mypath
                    elif i == 1:
                        cnf["DefaultDynamicLinks"] = True
                        cnf["DefaultDynamicPath"] = mypath
                    elif i == 2:
                        paths = {ds: mypath + "/" + fieldname}
                        links = {ds: False}
                    elif i == 3:
                        paths = {ds: mypath + "/" + fieldname}
                        links = {ds: True}
                    elif i == 4:
                        cnf["DefaultDynamicLinks"] = False
                        cnf["DefaultDynamicPath"] = mypath
                        labels = {ds: lbl}
                    elif i == 5:
                        cnf["DefaultDynamicLinks"] = True
                        cnf["DefaultDynamicPath"] = mypath
                        labels = {ds: lbl}
                    elif i == 6:
                        labels = {ds: lbl}
                        paths = {ds: mypath + "/" + fieldname}
                        links = {ds: False}
                    elif i == 7:
                        labels = {ds: lbl}
                        paths = {ds: mypath + "/" + fieldname}
                        links = {ds: True}
                    cnf["ChannelProperties"] = json.dumps(
                        {
                            "label": labels,
                            "nexus_path": paths,
                            "link": links,
                            "data_type": types,
                            "shape": shapes
                        }
                    )
                    cnf["DataSourceSelection"] = json.dumps({ds: True})

#                    print "I = ", i
                    rs.profileConfiguration = str(json.dumps(cnf))
                    cpname = rs.createDynamicComponent([])
                    mstr = ""
                    if ms:
                        mstr += dimbg % len(ms)
                        for ind, val in enumerate(ms):
                            mstr += dim % (ind + 1, val)
                        mstr += dimend

                    comp = self._cf.dp.Components([cpname])[0]
                    lk = link % (ds, mypath, ds)
                    if i % 4 < 2:
                        fd = fieldbg % (ds.lower(), nxstp)
                    else:
                        fname = fieldname.lower()
                        fd = fieldbg % (fieldname.lower(), nxstp)
                    fd += dss[0].toprettyxml(indent="") + mstr + fieldend

                    if path or i % 4 > 1:

                        if i % 4 < 2:
                            lk = link % (ds.lower(), mypath, ds.lower())
                        else:
                            lk = link % (fieldname.lower(), mypath,
                                         fieldname.lower())
                        mycps = defbg
                        for nm, gtp in path:
                            if not nm:
                                nm = gtp[2:]
                            if not gtp:
                                gtp = 'NX' + nm
                            mycps += groupbg % (nm, gtp)
                        mycps += fd

                        for j in range(len(path) - 1):
                            mycps += groupend
                        mycps += lk if i % 2 else ""
                        mycps += groupend
                        mycps += defend

                        mycps2 = defbg
                        for k, (nm, gtp) in enumerate(path):
                            if not nm:
                                nm = gtp[2:]
                            if not gtp:
                                gtp = 'NX' + nm
                            mycps2 += groupbg % (nm, gtp)
                            if not k:
                                mycps2 += lk if i % 2 else ""
                        mycps2 += fd

                        for _ in path:
                            mycps2 += groupend
                        mycps2 += defend
#                        print "FIRST"
                    else:
                        if i % 4 < 2:
                            lk = link % (ds.lower(),
                                         self._defaultpath, ds.lower())
                        else:
                            lk = link % (fieldname.lower(), self._defaultpath,
                                         fieldname.lower())
                        mycps = cps["shapetype"] % (
                            fd,
                            lk if i % 2 else "")
                        mycps2 = mycps
                    try:
                        self.assertEqual(comp, mycps2)
                    except:
                        self.assertEqual(comp, mycps)
        finally:
            pass

    # constructor test
    # \brief It tests default settings
    def test_create_init_fieldpath(self):
        fun = sys._getframe().f_code.co_name
        print "Run: %s.%s() " % (self.__class__.__name__, fun)
        val = {"ConfigDevice": self._cf.dp.name(),
               "WriterDevice": self._wr.dp.name(),
               "Door": 'doortestp09/testts/t1r228',
               "MntGrp": 'nxsmntgrp'}
        rs = self.openRecSelector()
        rs.configDevice = val["ConfigDevice"]
        rs.door = val["Door"]
        rs.mntGrp = val["MntGrp"]
        cnfdef = json.loads(rs.profileConfiguration)
        cps = {
            "shapetype":
                '<?xml version="1.0" ?>\n<definition>\n'
            '<group name="scan$var.serialno" type="NXentry">\n'
            '<group name="instrument" type="NXinstrument">\n'
            '<group name="collection" type="NXcollection">\n%s'
            '</group>\n</group>\n%s</group>\n</definition>\n',
        }

        defbg = '<?xml version="1.0" ?>\n<definition>\n'
        defend = '</definition>\n'
        groupbg = '<group name="%s" type="%s">\n'
        groupend = '</group>\n'

        field = '<field name="%s" type="%s">\n<strategy mode="INIT"/>\n' + \
            '<datasource name="%s" type="CLIENT">\n' + \
            '<record name="%s"/>\n</datasource>\n%s</field>\n'
        fieldbg = '<field name="%s" type="%s">\n<strategy mode="INIT"/>\n'
        fieldend = '</field>\n'

        link = '<group name="data" type="NXdata">\n' + \
            '<link name="%s" target="%s/%s"/>\n</group>\n'

        dimbg = '<dimensions rank="%s">\n'
        dim = '<dim index="%s" value="%s"/>\n'
        dimend = '</dimensions>\n'

        dname = "__dynamic_component__"

        self._cf.dp.SetCommandVariable(["DSDICT", json.dumps(self.smydss)])

        db = PyTango.Database()
        try:
            for i in range(8):
                for ds, dsxml in self.smydss.items():
                    ms = self.smydsspar[ds]
                    sds = ds.split("_")
                    tp = sds[1]
                    indom = xml.dom.minidom.parseString(dsxml)
                    dss = indom.getElementsByTagName("datasource")
                    if not ds.startswith("client_") and sds[1] != 'encoded':
                        nxstp = self._npTn2[tp]
                    else:
                        nxstp = 'NX_CHAR'

                    lbl = self.getRandomName(20)
                    fieldname = self.getRandomName(20)
#                    print "FIELD", fieldname
                    path = [
                        (self.getRandomName(20)
                         if self._rnd.randint(0, 1) else None,
                         ("NX" + self.getRandomName(20))
                         if self._rnd.randint(0, 1) else None)
                        for _ in range(self._rnd.randint(0, 10))]
#                    print "path0", path, len(path)
                    path = [nd for nd in path if (
                            nd != (None, None) and
                            nd[0] and not nd[0].startswith("NX"))]
#                    print "path1", path, len(path)
                    mypath = ""
                    for node in path:
                        mypath += "/"
                        if node[0]:
                            mypath += node[0]
                            if node[1]:
                                mypath += ":"
                        if node[1]:
                            mypath += node[1]
#                    mypath += fieldname
#                    print "path2", path, len(path)
#                    print "PATH", path, mypath
#                    print "TP = ", tp
                    tmptp = self._rnd.choice(self._npTn.keys())
                    cnf = dict(cnfdef)
                    labels = {}
                    paths = {}
                    links = {}
                    types = {}
                    shapes = {}

                    if i == 0:
                        cnf["DefaultDynamicLinks"] = False
                        cnf["DefaultDynamicPath"] = mypath
                    elif i == 1:
                        links = {ds: True}
                        cnf["DefaultDynamicLinks"] = True
                        cnf["DefaultDynamicPath"] = mypath
                    elif i == 2:
                        paths = {ds: mypath + "/" + fieldname}
                        links = {ds: False}
                    elif i == 3:
                        paths = {ds: mypath + "/" + fieldname}
                        links = {ds: True}
                    elif i == 4:
                        cnf["DefaultDynamicLinks"] = False
                        cnf["DefaultDynamicPath"] = mypath
                        labels = {ds: lbl}
                    elif i == 5:
                        cnf["DefaultDynamicLinks"] = True
                        cnf["DefaultDynamicPath"] = mypath
                        links = {ds: True}
                        labels = {ds: lbl}
                    elif i == 6:
                        labels = {ds: lbl}
                        paths = {ds: mypath + "/" + fieldname}
                        links = {ds: False}
                    elif i == 7:
                        labels = {ds: lbl}
                        paths = {ds: mypath + "/" + fieldname}
                        links = {ds: True}
                    cnf["ChannelProperties"] = json.dumps(
                        {
                            "label": labels,
                            "nexus_path": paths,
                            "link": links,
                            "data_type": types,
                            "shape": shapes
                        }
                    )
#                    print "I = ", i
                    rs.profileConfiguration = str(json.dumps(cnf))

                    cpname = rs.createDynamicComponent([
                        "", "",
                        str(json.dumps([ds]))])
                    mstr = ""
                    if ms:
                        mstr += dimbg % len(ms)
                        for ind, val in enumerate(ms):
                            mstr += dim % (ind + 1, val)
                        mstr += dimend

                    comp = self._cf.dp.Components([cpname])[0]
                    lk = link % (ds, mypath, ds)
                    if i % 4 < 2:
                        fd = fieldbg % (ds.lower(), nxstp)
                    else:
                        fname = fieldname.lower()
                        fd = fieldbg % (fieldname.lower(), nxstp)
                    fd += dss[0].toprettyxml(indent="") + mstr + fieldend

                    if path or i % 4 > 1:

                        if i % 4 < 2:
                            lk = link % (ds.lower(), mypath, ds.lower())
                        else:
                            lk = link % (fieldname.lower(), mypath,
                                         fieldname.lower())
                        mycps = defbg
                        for nm, gtp in path:
                            if not nm:
                                nm = gtp[2:]
                            if not gtp:
                                gtp = 'NX' + nm
                            mycps += groupbg % (nm, gtp)
                        mycps += fd

                        for j in range(len(path) - 1):
                            mycps += groupend
                        mycps += lk if i % 2 else ""
                        mycps += groupend
                        mycps += defend

                        mycps2 = defbg
                        for k, (nm, gtp) in enumerate(path):
                            if not nm:
                                nm = gtp[2:]
                            if not gtp:
                                gtp = 'NX' + nm
                            mycps2 += groupbg % (nm, gtp)
                            if not k:
                                mycps2 += lk if i % 2 else ""
                        mycps2 += fd

                        for _ in path:
                            mycps2 += groupend
                        mycps2 += defend
                    else:
                        if i % 4 < 2:
                            lk = link % (ds.lower(),
                                         self._defaultpath, ds.lower())
                        else:
                            lk = link % (fieldname.lower(), self._defaultpath,
                                         fieldname.lower())
                        mycps = cps["shapetype"] % (
                            fd,
                            lk if i % 2 else "")
                        mycps2 = mycps
                    try:
                        self.assertEqual(comp, mycps2)
                    except:
                        self.assertEqual(comp, mycps)
        finally:
            pass

    # constructor test
    # \brief It tests default settings
    def test_create_init_fieldpath_wol(self):
        fun = sys._getframe().f_code.co_name
        print "Run: %s.%s() " % (self.__class__.__name__, fun)
        val = {"ConfigDevice": self._cf.dp.name(),
               "WriterDevice": self._wr.dp.name(),
               "Door": 'doortestp09/testts/t1r228',
               "MntGrp": 'nxsmntgrp'}
        rs = self.openRecSelector()
        rs.configDevice = val["ConfigDevice"]
        rs.door = val["Door"]
        rs.mntGrp = val["MntGrp"]
        cnfdef = json.loads(rs.profileConfiguration)
        cps = {
            "shapetype":
                '<?xml version="1.0" ?>\n<definition>\n'
            '<group name="scan$var.serialno" type="NXentry">\n'
            '<group name="instrument" type="NXinstrument">\n'
            '<group name="collection" type="NXcollection">\n%s'
            '</group>\n</group>\n%s</group>\n</definition>\n',
        }

        defbg = '<?xml version="1.0" ?>\n<definition>\n'
        defend = '</definition>\n'
        groupbg = '<group name="%s" type="%s">\n'
        groupend = '</group>\n'

        field = '<field name="%s" type="%s">\n<strategy mode="INIT"/>\n' + \
            '<datasource name="%s" type="CLIENT">\n' + \
            '<record name="%s"/>\n</datasource>\n%s</field>\n'
        fieldbg = '<field name="%s" type="%s">\n<strategy mode="INIT"/>\n'
        fieldend = '</field>\n'

        link = '<group name="data" type="NXdata">\n' + \
            '<link name="%s" target="%s/%s"/>\n</group>\n'

        dimbg = '<dimensions rank="%s">\n'
        dim = '<dim index="%s" value="%s"/>\n'
        dimend = '</dimensions>\n'

        dname = "__dynamic_component__"

        self._cf.dp.SetCommandVariable(["DSDICT", json.dumps(self.smydss)])
        self._cf.dp.SetCommandVariable(["CPDICT", json.dumps(self.smydss)])

        db = PyTango.Database()
        try:
            for i in range(8):
#                print "I = ", i
                for ds, dsxml in self.smydss.items():
                    ms = self.smydsspar[ds]
                    sds = ds.split("_")
                    tp = sds[1]
                    indom = xml.dom.minidom.parseString(dsxml)
                    dss = indom.getElementsByTagName("datasource")
                    if not ds.startswith("client_") and sds[1] != 'encoded':
                        nxstp = self._npTn2[tp]
                    else:
                        nxstp = 'NX_CHAR'

                    lbl = self.getRandomName(20)
                    fieldname = self.getRandomName(20)
#                    print "FIELD", fieldname
                    path = [
                        (self.getRandomName(20)
                         if self._rnd.randint(0, 1) else None,
                         ("NX" + self.getRandomName(20))
                         if self._rnd.randint(0, 1) else None)
                        for _ in range(self._rnd.randint(0, 10))]
#                    print "path0", path, len(path)
                    path = [nd for nd in path if (
                            nd != (None, None) and
                            nd[0] and not nd[0].startswith("NX"))]
#                    print "path1", path, len(path)
                    mypath = ""
                    for node in path:
                        mypath += "/"
                        if node[0]:
                            mypath += node[0]
                            if node[1]:
                                mypath += ":"
                        if node[1]:
                            mypath += node[1]
#                    mypath += fieldname
#                    print "path2", path, len(path)
#                    print "PATH", path, mypath
#                    print "TP = ", tp
                    tmptp = self._rnd.choice(self._npTn.keys())
                    cnf = dict(cnfdef)
                    labels = {}
                    paths = {}
                    links = {}
                    types = {}
                    shapes = {}

                    if i == 0:
                        cnf["DefaultDynamicPath"] = mypath
                    elif i == 1:
                        cnf["DefaultDynamicLinks"] = True
                        cnf["DefaultDynamicPath"] = mypath
                        links = {ds: True}
                    elif i == 2:
                        paths = {ds: mypath + "/" + fieldname}
                    elif i == 3:
                        paths = {ds: mypath + "/" + fieldname}
                        links = {ds: True}
                    elif i == 4:
                        cnf["DefaultDynamicPath"] = mypath
                        labels = {ds: lbl}
                    elif i == 5:
                        cnf["DefaultDynamicLinks"] = True
                        cnf["DefaultDynamicPath"] = mypath
                        links = {ds: True}
                        labels = {ds: lbl}
                    elif i == 6:
                        labels = {ds: lbl}
                        paths = {ds: mypath + "/" + fieldname}
                    elif i == 7:
                        labels = {ds: lbl}
                        paths = {ds: mypath + "/" + fieldname}
                        links = {ds: True}
                    cnf["ChannelProperties"] = json.dumps(
                        {
                            "label": labels,
                            "nexus_path": paths,
                            "link": links,
                            "data_type": types,
                            "shape": shapes
                        }
                    )
#                    print "I = ", i
                    if i % 2 == 0:
                        cnf["ComponentSelection"] = str(json.dumps({ds: True}))
                    rs.profileConfiguration = str(json.dumps(cnf))

                    cpname = rs.createDynamicComponent([
                        "", "",
                        str(json.dumps([ds]))])
                    mstr = ""
                    if ms:
                        mstr += dimbg % len(ms)
                        for ind, val in enumerate(ms):
                            mstr += dim % (ind + 1, val)
                        mstr += dimend

                    comp = self._cf.dp.Components([cpname])[0]
                    lk = link % (ds, mypath, ds)
                    if i % 4 < 2:
                        fd = fieldbg % (ds.lower(), nxstp)
                    else:
                        fname = fieldname.lower()
                        fd = fieldbg % (fieldname.lower(), nxstp)
                    fd += dss[0].toprettyxml(indent="") + mstr + fieldend

                    if path or i % 4 > 1:

                        if i % 4 < 2:
                            lk = link % (ds.lower(), mypath, ds.lower())
                        else:
                            lk = link % (fieldname.lower(), mypath,
                                         fieldname.lower())
                        mycps = defbg
                        for nm, gtp in path:
                            if not nm:
                                nm = gtp[2:]
                            if not gtp:
                                gtp = 'NX' + nm
                            mycps += groupbg % (nm, gtp)
                        mycps += fd

                        for j in range(len(path) - 1):
                            mycps += groupend
                        mycps += lk if i % 2 else ""
                        mycps += groupend
                        mycps += defend

                        mycps2 = defbg
                        for k, (nm, gtp) in enumerate(path):
                            if not nm:
                                nm = gtp[2:]
                            if not gtp:
                                gtp = 'NX' + nm
                            mycps2 += groupbg % (nm, gtp)
                            if not k:
                                mycps2 += lk if i % 2 else ""
                        mycps2 += fd

                        for _ in path:
                            mycps2 += groupend
                        mycps2 += defend
                    else:
                        if i % 4 < 2:
                            lk = link % (ds.lower(),
                                         self._defaultpath, ds.lower())
                        else:
                            lk = link % (fieldname.lower(), self._defaultpath,
                                         fieldname.lower())
                        mycps = cps["shapetype"] % (
                            fd,
                            lk if i % 2 else "")
                        mycps2 = mycps
                    try:
                        self.assertEqual(comp, mycps2)
                    except:
                        self.assertEqual(comp, mycps)
        finally:
            pass

    # test
    def test_variableComponents_empty(self):
        fun = sys._getframe().f_code.co_name
        print "Run: %s.%s() " % (self.__class__.__name__, fun)
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

        self._cf.dp.SetCommandVariable(["CPDICT", json.dumps(self.mycps)])
        self._cf.dp.SetCommandVariable(["DSDICT", json.dumps(self.mydss)])
        self.assertEqual(rs.variableComponents(), '{}')

    # test
    def test_variableComponents_cpvar(self):
        fun = sys._getframe().f_code.co_name
        print "Run: %s.%s() " % (self.__class__.__name__, fun)
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

        self._cf.dp.SetCommandVariable(["CPDICT", json.dumps(self.mycpsvar)])
        self.myAssertDict(
            json.loads(rs.variableComponents()),
            {"c01": ["scan3"], "c02": ["scan"], "mca": ["scan2"]}
        )

    # test
    def test_variableComponents_mixed(self):
        fun = sys._getframe().f_code.co_name
        print "Run: %s.%s() " % (self.__class__.__name__, fun)
        val = {"ConfigDevice": self._cf.dp.name(),
               "WriterDevice": self._wr.dp.name(),
               "Door": 'doortestp09/testts/t1r228',
               "MntGrp": 'nxsmntgrp'}

        wrong = []
        mycps = {
            'mycp': (
                '<?xml version=\'1.0\'?>'
                '<definition>'
                '<group type="NXcollection" name="$var.entry"/>'
                '<group type="NXentry" name="$var.entry2"/>'
                '</definition>'
            ),
            'mycp2': (
                '<?xml version=\'1.0\'?>'
                '<definition>'
                '<group type="NXcollection" name="$var.myvar"/>'
                '<group type="NXentry" name="$var.entry2"/>'
                '</definition>'
            ),
            'mycp3': (
                '<?xml version=\'1.0\'?>'
                '<definition>'
                '<group type="NXcollection" name="$var.entry"/>'
                '<group type="NXentry" name="$var.something"/>'
                '</definition>'
            ),
            'mycp4': (
                '<?xml version=\'1.0\'?>'
                '<definition>'
                '<group type="NXcollection" name="$var.entry2"/>'
                '<group type="NXentry" name="$var.something2"/>'
                '<group type="NXentry" name="$var.new"/>'
                '</definition>'
            ),
        }
        cpvar = {
            "mycp": ["entry", "entry2"],
            "mycp2": ["myvar", "entry2"],
            "mycp3": ["entry", "something"],
            "mycp4": ["entry2", "something2", "new"],
        }
        rs = self.openRecSelector()
        rs.configDevice = val["ConfigDevice"]
        rs.door = val["Door"]
        rs.mntGrp = val["MntGrp"]
        self.assertEqual(rs.configDevice, val["ConfigDevice"])
        self.assertEqual(rs.door, val["Door"])
        self.assertEqual(rs.mntGrp, val["MntGrp"])

        for i in range(20):
            mncps = self._rnd.randint(0, len(mycps.keys()))
            mcps = [
                cp for cp in self._rnd.sample(set(mycps.keys()), mncps)
            ]

            gencp = dict((cp, mycps[cp]) for cp in mcps)
            self._cf.dp.SetCommandVariable(["CPDICT", json.dumps(gencp)])
            res = json.loads(rs.variableComponents())
            res2 = {}
#            print mcps
            for cp in mcps:
                for vr in cpvar[cp]:
                    if vr not in res2:
                        res2[vr] = []
                    res2[vr].append(cp)

            self.myAssertDictJSON(res, res2)

    # test
    def test_createWriterConfiguration_default(self):
        fun = sys._getframe().f_code.co_name
        print "Run: %s.%s() " % (self.__class__.__name__, fun)
        self.maxDiff = None
        val = {"ConfigDevice": self._cf.dp.name(),
               "WriterDevice": self._wr.dp.name(),
               "Door": 'doortestp09/testts/t1r228',
               "MntGrp": 'nxsmntgrp'}

        db = PyTango.Database()
        db.put_device_property(self._ms.ms.keys()[0],
                               {'PoolNames': self._pool.dp.name()})
        self._ms.dps[self._ms.ms.keys()[0]].Init()
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
                components = rs.components
                res2 = ""
                for cp in components:
                    if cp in self.smycps:
                        res2 += self.smycps[cp]
                    else:
                        res2 += "$components.%s " % cp
                self._cf.dp.xmlstring = str(res2)
                res = rs.createWriterConfiguration([])
                cmds = json.loads(self._cf.dp.GetCommandVariable("COMMANDS"))
                vrs = json.loads(self._cf.dp.GetCommandVariable("VARS"))
                self.assertEqual(cmds[-1], "CreateConfiguration")
                self.assertEqual(set(vrs[-1]), set(components))
                self.assertEqual(res, res2)
        finally:
            simp2.tearDown()

    # test
    def test_createWriterConfiguration_given(self):
        fun = sys._getframe().f_code.co_name
        print "Run: %s.%s() " % (self.__class__.__name__, fun)
        self.maxDiff = None
        val = {"ConfigDevice": self._cf.dp.name(),
               "WriterDevice": self._wr.dp.name(),
               "Door": 'doortestp09/testts/t1r228',
               "MntGrp": 'nxsmntgrp'}

        db = PyTango.Database()
        db.put_device_property(self._ms.ms.keys()[0],
                               {'PoolNames': self._pool.dp.name()})
        self._ms.dps[self._ms.ms.keys()[0]].Init()
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

                mncps = self._rnd.randint(0, len(self.smycps.keys()))
                components = [
                    cp for cp in self._rnd.sample(
                        set(self.smycps.keys()),
                        mncps
                    )
                ]

                res2 = ""
                for cp in components:
                    if cp in self.smycps:
                        res2 += self.smycps[cp]
                    else:
                        res2 += "$components.%s " % cp
                self._cf.dp.xmlstring = str(res2)
                res = rs.createWriterConfiguration([])
                cmds = self._cf.dp.GetCommandVariable("COMMANDS")
#                print cmds
#                print res
                self._cf.dp.xmlstring = str(res2)
                res3 = self._cf.dp.createConfiguration(components)
                cmds = json.loads(self._cf.dp.GetCommandVariable("COMMANDS"))
                vrs = json.loads(self._cf.dp.GetCommandVariable("VARS"))
                self.assertEqual(cmds[-1], "CreateConfiguration")
                self.assertEqual(set(vrs[-1]), set(components))
                self.assertEqual(res, res2)
        finally:
            simp2.tearDown()

    # test
    def test_updateConfigVariables_noserialno(self):
        fun = sys._getframe().f_code.co_name
        print "Run: %s.%s() " % (self.__class__.__name__, fun)
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

        for i in range(20):
            rs.appendEntry = bool(i % 2)
            rscv = {}
            lcp = self._rnd.randint(1, 40)
            for _ in range(lcp):
                vrname = self.getRandomName(10)
                if vrname != 'serialno':
                    rscv[vrname] = self.getRandomName(
                        self._rnd.randint(1, 40))
            rs.configVariables = str(json.dumps(rscv))

            cscv = {}
            lcp = self._rnd.randint(1, 40)
            for _ in range(lcp):
                vrname = self.getRandomName(10)
                if vrname != 'serialno':
                    cscv[vrname] = self.getRandomName(
                        self._rnd.randint(1, 40))
            self._cf.dp.variables = str(json.dumps(cscv))

            rs.updateConfigVariables()

            res = self._cf.dp.variables
            if i % 2:
                rscv["serialno"] = "1"
            self.myAssertDict(json.loads(res), rscv)

    # test
    def test_updateConfigVariables_rsserialno(self):
        fun = sys._getframe().f_code.co_name
        print "Run: %s.%s() " % (self.__class__.__name__, fun)
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

        for i in range(20):
            rs.appendEntry = bool(i % 2)
            rscv = {}
            lcp = self._rnd.randint(1, 40)
            for _ in range(lcp):
                vrname = self.getRandomName(10)
                if vrname != 'serialno':
                    rscv[vrname] = self.getRandomName(
                        self._rnd.randint(1, 40))
            slno = str(self._rnd.randint(1, 40))
            rscv["serialno"] = str(slno)
            rs.configVariables = str(json.dumps(rscv))

            cscv = {}
            lcp = self._rnd.randint(1, 40)
            for _ in range(lcp):
                vrname = self.getRandomName(10)
                if vrname != 'serialno':
                    cscv[vrname] = self.getRandomName(
                        self._rnd.randint(1, 40))
            self._cf.dp.variables = str(json.dumps(cscv))

            rs.updateConfigVariables()

            res = self._cf.dp.variables
            self.myAssertDict(json.loads(res), rscv)

    # test
    def test_updateConfigVariables_cfserialno(self):
        fun = sys._getframe().f_code.co_name
        print "Run: %s.%s() " % (self.__class__.__name__, fun)
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

        for i in range(20):
            rs.appendEntry = bool(i % 2)
            rscv = {}
            lcp = self._rnd.randint(1, 40)
            for _ in range(lcp):
                vrname = self.getRandomName(10)
                if vrname != 'serialno':
                    rscv[vrname] = self.getRandomName(
                        self._rnd.randint(1, 40))
            rs.configVariables = str(json.dumps(rscv))

            cscv = {}
            lcp = self._rnd.randint(1, 40)
            for _ in range(lcp):
                vrname = self.getRandomName(10)
                if vrname != 'serialno':
                    cscv[vrname] = self.getRandomName(
                        self._rnd.randint(1, 40))
            slno = self._rnd.randint(1, 40)
            cscv["serialno"] = str(slno)
            self._cf.dp.variables = str(json.dumps(cscv))

            rs.updateConfigVariables()

            res = self._cf.dp.variables
            if i % 2:
                rscv["serialno"] = str(slno + 1)
            self.myAssertDict(json.loads(res), rscv)

    # test
    def test_updateConfigVariables_rscfserialno(self):
        fun = sys._getframe().f_code.co_name
        print "Run: %s.%s() " % (self.__class__.__name__, fun)
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

        for i in range(20):
            rs.appendEntry = bool(i % 2)
            rscv = {}
            lcp = self._rnd.randint(1, 40)
            for _ in range(lcp):
                vrname = self.getRandomName(10)
                if vrname != 'serialno':
                    rscv[vrname] = self.getRandomName(
                        self._rnd.randint(1, 40))
            slno = self._rnd.randint(1, 40)
            rscv["serialno"] = str(slno)
            rs.configVariables = str(json.dumps(rscv))

            cscv = {}
            lcp = self._rnd.randint(1, 40)
            for _ in range(lcp):
                vrname = self.getRandomName(10)
                if vrname != 'serialno':
                    cscv[vrname] = self.getRandomName(
                        self._rnd.randint(1, 40))
            slno2 = self._rnd.randint(1, 40)
            cscv["serialno"] = str(slno2)
            self._cf.dp.variables = str(json.dumps(cscv))

            rs.updateConfigVariables()

            res = self._cf.dp.variables
            self.myAssertDict(json.loads(res), rscv)


if __name__ == '__main__':
    unittest.main()
