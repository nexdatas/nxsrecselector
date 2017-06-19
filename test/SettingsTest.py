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
class SettingsTest(unittest.TestCase):

    # constructor
    # \param methodName name of the test method

    def __init__(self, methodName):
        unittest.TestCase.__init__(self, methodName)

        self._bint = "int64" if IS64BIT else "int32"
        self._buint = "uint64" if IS64BIT else "uint32"
        self._bfloat = "float64" if IS64BIT else "float32"

        self._ms = TestMacroServerSetUp.TestMacroServerSetUp()
        self._cf = TestConfigServerSetUp.TestConfigServerSetUp()
        self._wr = TestWriterSetUp.TestWriterSetUp()
        self._pool = TestPoolSetUp.TestPoolSetUp()
        self._simps = TestServerSetUp.TestServerSetUp()

        try:
            self._seed = long(binascii.hexlify(os.urandom(16)), 16)
        except NotImplementedError:
            self._seed = long(time.time() * 256)

        #        self._seed = 133807022068754062020588864622821989794
        #        self._seed = 252610957556978915330732248482858942194
        self._rnd = random.Random(self._seed)

        self._dump = {}

        # default zone
        self._defaultzone = 'Europe/Berlin'
        # default mntgrp
        self._defaultmntgrp = 'nxsmntgrp'
        # default path
        self._defaultpath = \
            '/scan$var.serialno:NXentry/NXinstrument/collection'

        self._npTn = {"float32": "NX_FLOAT32", "float64": "NX_FLOAT64",
                      "float": "NX_FLOAT32", "double": "NX_FLOAT64",
                      "int": "NX_INT", "int64": "NX_INT64",
                      "int32": "NX_INT32", "int16": "NX_INT16",
                      "int8": "NX_INT8", "uint64": "NX_UINT64",
                      "uint32": "NX_UINT32", "uint16": "NX_UINT16",
                      "uint8": "NX_UINT8", "uint": "NX_UINT64",
                      "string": "NX_CHAR", "bool": "NX_BOOLEAN"}
        self._npTn2 = {"float32": "NX_FLOAT32", "float64": "NX_FLOAT64",
                       "float": "NX_FLOAT32", "double": "NX_FLOAT64",
                       "long": "NX_INT32",
                       "long64": "NX_INT64",
                       "long32": "NX_INT32",
                       "ulong64": "NX_UINT64",
                       "ulong32": "NX_UINT32",
                       "ulong": "NX_UINT32",
                       "ushort": "NX_UINT16",
                       "uchar": "NX_UINT8",
                       "short": "NX_INT16",
                       "int": "NX_INT",
                       "int64": "NX_INT64",
                       "int32": "NX_INT32",
                       "int16": "NX_INT16",
                       "int8": "NX_INT8",
                       "uint64": "NX_UINT64",
                       "uint32": "NX_UINT32",
                       "uint16": "NX_UINT16",
                       "uint8": "NX_UINT8",
                       "uint": "NX_UINT64",
                       "string": "NX_CHAR",
                       "bool": "NX_BOOLEAN"}

        # selection version
        self.version = nxsrecconfig.__version__

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
            ("UnplottedComponents", '[]'),
            ("ChannelProperties", '{}'),
            ("DynamicComponents", True),
            ("DefaultDynamicLinks", True),
            ("DefaultDynamicPath", self._defaultpath),
            ("TimeZone", self._defaultzone),
            ("ConfigDevice", ''),
            ("WriterDevice", ''),
            ("Door", ''),
            ("MntGrp", ''),
            ("MntGrpConfiguration", ''),
            ("Version", self.version)

        ]
        self.mysel = {
            'mysl': (
                '{}'),
            'mysl2': (
                json.dumps({key: value for (key, value) in self._keys})),
        }

        self.mysel2 = {
            'mntgrp_01e': (
                '{}'),
            'mntgrp_02att': (
                json.dumps({key: value for (key, value) in self._keys})),
            'mntgrp_04_13': (
                json.dumps({key: value for (key, value) in self._keys})),
            'mntgrp_04213': (
                json.dumps({key: value for (key, value) in self._keys})),
            'mntgrp_012313': (
                json.dumps({key: value for (key, value) in self._keys})),
        }

        self.mycps = {
            'mycp': (
                '<?xml version=\'1.0\'?>'
                '<definition>'
                '<group type="NXcollection" name="dddd"/>'
                '</definition>'),
            'mycp2': (
                '<definition><group type="NXcollection" name="dddd">'
                '<field><datasource type="TANGO" name="ann" /></field>'
                '</group></definition>'),
            'mycp3': (
                '<definition><group type="NXcollection" name="dddd">'
                '<field><datasource type="TANGO" name="ann" />'
                '<strategy mode="STEP" />'
                '</field></group></definition>'),
            'exp_t01': (
                '<?xml version=\'1.0\'?>'
                '<definition>'
                '<group type="NXentry" name="entry1">'
                '<group type="NXinstrument" name="instrument">'
                '<group type="NXdetector" name="detector">'
                '<field units="s" type="NX_FLOAT" name="exp_t01">'
                '<strategy mode="STEP"/>'
                '<datasource type="CLIENT" name="exp_t01">'
                '<record name="haso228k:10000/expchan/dgg2_exp_01/1"/>'
                '</datasource></field></group></group>'
                '</group></definition>'),
            'dim1': (
                '<definition><group type="NXentry">'
                '<field type="NX_INT8" name="field1">'
                '<datasource type="TANGO" name="tann1c">'
                '<record name="myattr2"/>'
                '<device member="attribute" name="dsf/sd/we"/>'
                '</datasource>'
                '<strategy mode="INIT"/>'
                '<dimensions rank="1">'
                '<dim index="1" value="34">'
                '</dim></dimensions>'
                '</field></group>'
                '</definition>'),
            'dim2': (
                '<definition><group type="NXentry">'
                '<field type="NX_INT8" name="field1">'
                '<datasource type="TANGO" name="tann1c">'
                '<record name="myattr2"/>'
                '<device member="attribute" name="dsf/sd/we"/>'
                '</datasource>'
                '<strategy mode="INIT"/>'
                '<dimensions rank="1">'
                '<dim index="1" value="$datasources.ann">'
                '</dim></dimensions>'
                '</field></group>'
                '</definition>'),
            'dim3': (
                '<definition><group type="NXentry">'
                '<field type="NX_INT8" name="field1">'
                '<datasource type="TANGO" name="tann1c">'
                '<record name="myattr2"/>'
                '<device member="attribute" name="dsf/sd/we"/>'
                '</datasource>'
                '<strategy mode="INIT"/>'
                '<dimensions rank="1">'
                '<dim index="1">1234'
                '</dim></dimensions>'
                '</field></group>'
                '</definition>'),
            'dim4': (
                '<definition><group type="NXentry">'
                '<field type="NX_INT8" name="field1">'
                '<datasource type="TANGO" name="tann1c">'
                '<record name="myattr2"/>'
                '<device member="attribute" name="dsf/sd/we"/>'
                '</datasource>'
                '<strategy mode="INIT"/>'
                '<dimensions rank="1">'
                '<dim index="1">$datasources.ann2<strategy mode="CONFIG" />'
                '</dim></dimensions>'
                '</field></group>'
                '</definition>'),
            'dim5': (
                '<definition><group type="NXentry">'
                '<field type="NX_INT8" name="field1">'
                '<datasource type="TANGO" name="tann1c">'
                '<record name="myattr2"/>'
                '<device member="attribute" name="dsf/sd/we"/>'
                '</datasource>'
                '<strategy mode="INIT"/>'
                '<dimensions rank="1">'
                '<dim index="1"><strategy mode="CONFIG" />'
                '<datasource type="TANGO" name="ann" />'
                '</dim></dimensions>'
                '</field></group>'
                '</definition>'),
            'dim6': (
                '<definition><group type="NXentry">'
                '<field type="NX_INT8" name="field1">'
                '<datasource type="TANGO" name="tann1c">'
                '<record name="myattr2"/>'
                '<device member="attribute" name="dsf/sd/we"/>'
                '</datasource>'
                '<strategy mode="INIT"/>'
                '<dimensions rank="2">'
                '<dim index="1" value="$datasources.ann" />'
                '<dim index="2" value="123" />'
                '</dimensions>'
                '</field></group>'
                '</definition>'),
            'dim7': (
                '<definition><group type="NXentry">'
                '<field type="NX_INT8" name="field1">'
                '<datasource type="TANGO" name="tann1c">'
                '<record name="myattr2"/>'
                '<device member="attribute" name="dsf/sd/we"/>'
                '</datasource>'
                '<strategy mode="INIT"/>'
                '<dimensions rank="2" />'
                '</field></group>'
                '</definition>'),
            'dim8': (
                '<definition><group type="NXentry">'
                '<field type="NX_INT8" name="field1">'
                '<datasource type="TANGO" name="tann1c">'
                '<record name="myattr2"/>'
                '<device member="attribute" name="dsf/sd/we"/>'
                '</datasource>'
                '<strategy mode="INIT"/>'
                '<dimensions rank="2">'
                '<dim index="2" value="123" />'
                '</dimensions>'
                '</field></group>'
                '</definition>'),
            'scan': (
                '<definition><group type="NXentry" name="entry1">'
                '<group type="NXinstrument" name="instrument">'
                '<group type="NXdetector" name="detector">'
                '<field units="m" type="NX_FLOAT" name="counter1">'
                '<strategy mode="STEP"/>'
                '<datasource type="CLIENT"><record name="exp_c01"/>'
                '</datasource></field>'
                '<field units="s" type="NX_FLOAT" name="counter2">'
                '<strategy mode="STEP"/><datasource type="CLIENT">'
                '<record name="exp_c02"/></datasource></field>'
                '<field units="" type="NX_FLOAT" name="mca">'
                '<dimensions rank="1"><dim value="2048" index="1"/>'
                '</dimensions><strategy mode="STEP"/>'
                '<datasource type="CLIENT"><record name="p09/mca/exp.02"/>'
                '</datasource></field></group></group></group></definition>'
            ),

            'scan2': (
                '<definition><group type="NXentry" name="entry1">'
                '<group type="NXinstrument" name="instrument">'
                '<group type="NXdetector" name="detector">'
                '<field units="m" type="NX_FLOAT" name="counter1">'
                '<strategy mode="STEP"/>'
                '<datasource name="c01" type="CLIENT">'
                '<record name="exp_c01"/></datasource></field>'
                '<field units="s" type="NX_FLOAT" name="counter2">'
                '<strategy mode="STEP"/>'
                '<datasource type="CLIENT" name="c02">'
                '<record name="exp_c02"/></datasource></field>'
                '<field units="" type="NX_FLOAT" name="mca">'
                '<dimensions rank="1"><dim value="2048" index="1"/>'
                '</dimensions><strategy mode="STEP"/>'
                '<datasource type="CLIENT"  name="mca">'
                '<record name="p09/mca/exp.02"/>'
                '</datasource></field></group></group></group></definition>'
            ),
            'scan3': (
                '<definition><group type="NXentry" name="entry1">'
                '<group type="NXinstrument" name="instrument">'
                '<group type="NXdetector" name="detector">'
                '<field units="m" type="NX_FLOAT" name="counter1">'
                '<strategy mode="STEP"/>'
                '<datasource name="c01" type="CLIENT">'
                '<record name="exp_c01"/></datasource></field>'
                '<field units="s" type="NX_FLOAT" name="counter2">'
                '<strategy mode="INIT"/>'
                '<datasource type="CLIENT" name="c01">'
                '<record name="exp_c01"/></datasource></field>'
                '<field units="" type="NX_FLOAT" name="mca">'
                '<dimensions rank="1"><dim value="2048" index="1"/>'
                '</dimensions><strategy mode="STEP"/>'
                '<datasource type="CLIENT"  name="mca">'
                '<record name="p09/mca/exp.02"/>'
                '</datasource></field></group></group></group></definition>'
            ),

        }

        self.mycpsvar = {
            'mycp': (
                '<?xml version=\'1.0\'?>'
                '<definition>'
                '<group type="NXcollection" name="dddd"/>'
                '</definition>'),
            'scan': (
                '<definition><group type="NXentry" name="entry1">'
                '<group type="NXinstrument" name="instrument">'
                '<group type="NXdetector" name="detector">'
                '<field units="m" type="NX_FLOAT" name="counter1">'
                '<strategy mode="STEP"/>'
                '<datasource type="CLIENT"><record name="exp_c01"/>'
                '</datasource></field>'
                '<field units="s" type="NX_FLOAT" name="counter2">'
                '<strategy mode="STEP"/><datasource type="CLIENT">'
                '<record name="$var.c02"/></datasource></field>'
                '<field units="" type="NX_FLOAT" name="mca">'
                '<dimensions rank="1"><dim value="2048" index="1"/>'
                '</dimensions><strategy mode="STEP"/>'
                '<datasource type="CLIENT"><record name="p09/mca/exp.02"/>'
                '</datasource></field></group></group></group></definition>'
            ),

            'scan2': (
                '<definition><group type="NXentry" name="entry1">'
                '<group type="NXinstrument" name="instrument">'
                '<group type="NXdetector" name="detector">'
                '<field units="m" type="NX_FLOAT" name="counter1">'
                '<strategy mode="STEP"/>'
                '<datasource name="c01" type="CLIENT">'
                '<record name="exp_c01"/></datasource></field>'
                '<field units="s" type="NX_FLOAT" name="counter2">'
                '<strategy mode="STEP"/>'
                '<datasource type="CLIENT" name="c02">'
                '<record name="exp_c02"/></datasource></field>'
                '<field units="" type="NX_FLOAT" name="mca">'
                '<dimensions rank="1"><dim value="2048" index="1"/>'
                '</dimensions><strategy mode="STEP"/>'
                '<datasource type="CLIENT"  name="mca">'
                '<record name="$var.mca"/>'
                '</datasource></field></group></group></group></definition>'
            ),
            'scan3': (
                '<definition><group type="NXentry" name="entry1">'
                '<group type="NXinstrument" name="instrument">'
                '<group type="NXdetector" name="detector">'
                '<field units="m" type="NX_FLOAT" name="counter1">'
                '<strategy mode="STEP"/>'
                '<datasource name="c01" type="CLIENT">'
                '<record name="exp_c01"/></datasource></field>'
                '<field units="s" type="NX_FLOAT" name="counter2">'
                '<strategy mode="INIT"/>'
                '<datasource type="CLIENT" name="c01">'
                '<record name="$var.c01"/></datasource></field>'
                '<field units="" type="NX_FLOAT" name="mca">'
                '<dimensions rank="1"><dim value="2048" index="1"/>'
                '</dimensions><strategy mode="STEP"/>'
                '<datasource type="CLIENT"  name="mca">'
                '<record name="p09/mca/exp.02"/>'
                '</datasource></field></group></group></group></definition>'
            ),

        }

        self.specps = {
            'pyeval0': (
                '<definition><group type="NXentry">'
                '<field type="NX_INT8" name="field1">'
                '$datasources.pyeval0ds'
                '<strategy mode="INIT"/>'
                '</field></group>'
                '</definition>'
            ),
            'pyeval1': (
                '<definition><group type="NXentry">'
                '<field type="NX_INT32" name="field1">'
                '$datasources.pyeval1ds'
                '<strategy mode="STEP"/>'
                '</field></group>'
                '</definition>'
            ),
            'pyeval1a': (
                '<definition><group type="NXentry">'
                '<field type="NX_INT32" name="field1">'
                '$datasources.pyeval1ads'
                '<strategy mode="STEP"/>'
                '</field></group>'
                '</definition>'
            ),
            'pyeval2': (
                '<definition><group type="NXentry">'
                '<field type="NX_FLOAT" name="field1">'
                '$datasources.pyeval2ds'
                '<strategy mode="STEP"/>'
                '</field></group>'
                '</definition>'
            ),
            'pyeval2a': (
                '<definition><group type="NXentry">'
                '<field type="NX_FLOAT" name="field1">'
                '$datasources.pyeval2ads'
                '<strategy mode="STEP"/>'
                '</field></group>'
                '</definition>'
            ),
            'pyeval2b': (
                '<definition><group type="NXentry">'
                '<field type="NX_FLOAT64" name="field1">'
                '$datasources.pyeval2bds'
                '<strategy mode="FINAL"/>'
                '</field></group>'
                '</definition>'
            ),
            'pyeval2c': (
                '<definition><group type="NXentry">'
                '<field type="NX_FLOAT64" name="field1">'
                '$datasources.pyeval2cds'
                '<strategy mode="FINAL"/>'
                '</field></group>'
                '</definition>'
            )
        }

        self.spedss = {
            'pyeval0ds': (
                '<definition>'
                '<datasource type="PYEVAL" name="pyeval0ds">'
                '<result name="myattr2">'
                'ds.myattr = "SomeThing"'
                '</result>'
                '</datasource>'
                '</definition>'
            ),
            'pyeval1ds': (
                '<definition>'
                '<datasource type="PYEVAL" name="pyeval1ds">'
                '$datasources.scalar2_uchar'
                '<result name="myattr2">'
                'ds.myattr2 = 12'
                '</result>'
                '</datasource>'
                '</definition>'
            ),
            'pyeval1ads': (
                '<definition>'
                '<datasource type="PYEVAL" name="pyeval1ads">'
                '$datasources.scalar2_long'
                '<result name="myattr2">'
                'ds.myattr2 = ds.tann1c'
                '</result>'
                '</datasource>'
                '</definition>'
            ),
            'pyeval2ds': (
                '<definition>'
                '<datasource type="PYEVAL" name="pyeval2ds">'
                '$datasources.scalar2_long'
                '$datasources.scalar2_uchar'
                '<result name="myattr2">'
                'ds.myattr2 = 123.3'
                '</result>'
                '</datasource>'
                '</definition>'
            ),
            'pyeval2ads': (
                '<definition>'
                '<datasource type="PYEVAL" name="pyeval2ads">'
                '$datasources.scalar_long'
                '$datasources.scalar2_uchar'
                '<result name="myattr2">'
                'ds.myattr2 = float(ds.scalar_long + ds.scalar2_uchar)'
                '</result>'
                '</datasource>'
                '</definition>'
            ),
            'pyeval2bds': (
                '<definition>'
                '<datasource type="PYEVAL" name="pyeval2bds">'
                '$datasources.scalar_long'
                '$datasources.scalar2_uchar'
                '<result name="myattr2">'
                'ds.myattr2 = float(ds.scalar_long)'
                '</result>'
                '</datasource>'
                '</definition>'
            ),
            'pyeval2cds': (
                '<definition>'
                '<datasource type="PYEVAL" name="pyeval2cds">'
                '$datasources.scalar_long'
                '$datasources.scalar2_uchar'
                '<result name="myattr2">'
                'ds.myattr2 = float(ds.scalar2_uchar)'
                '</result>'
                '</datasource>'
                '</definition>'
            ),
        }

        self.rescps = {
            'mycp': {},
            'mycp2': {},
            'mycp3': {'ann': [('STEP', 'TANGO', '', None, None)]},
            'exp_t01': {
                'exp_t01': [
                    ('STEP', 'CLIENT', 'haso228k:10000/expchan/dgg2_exp_01/1',
                     'NX_FLOAT', None)]},
            'dim1': {
                'tann1c': [
                    ('INIT', 'TANGO', 'dsf/sd/we/myattr2', 'NX_INT8', [34])]},
            'dim2': {
                'tann1c': [
                    ('INIT', 'TANGO', 'dsf/sd/we/myattr2', 'NX_INT8',
                     ['$datasources.ann'])]},
            'dim3': {
                'tann1c': [
                    ('INIT', 'TANGO', 'dsf/sd/we/myattr2', 'NX_INT8',
                     [1234])]},
            'dim4': {
                'tann1c': [
                    ('INIT', 'TANGO', 'dsf/sd/we/myattr2', 'NX_INT8',
                     ['$datasources.ann2'])],
                     'ann2': [
                         ('CONFIG', 'CLIENT', '', None, None)],
            },
            'dim5': {
                'tann1c': [
                    ('INIT', 'TANGO', 'dsf/sd/we/myattr2', 'NX_INT8',
                     ['$datasources.ann'])],
                'ann': [('CONFIG', 'TANGO', '', None, None)],
            },
            'dim6': {'tann1c': [
                ('INIT', 'TANGO', 'dsf/sd/we/myattr2', 'NX_INT8',
                 ['$datasources.ann', 123])]},
            'dim7': {'tann1c': [
                ('INIT', 'TANGO', 'dsf/sd/we/myattr2', 'NX_INT8',
                 [None, None])]},
            'dim8': {'tann1c': [
                ('INIT', 'TANGO', 'dsf/sd/we/myattr2', 'NX_INT8',
                 [None, 123])]},
            'scan': {'__unnamed__1': [('STEP', 'CLIENT', 'exp_c01',
                                       'NX_FLOAT', None)],
                     '__unnamed__2': [('STEP', 'CLIENT', 'exp_c02',
                                       'NX_FLOAT', None)],
                     '__unnamed__3': [('STEP', 'CLIENT', 'p09/mca/exp.02',
                                       'NX_FLOAT', [2048])],
                     },
            'scan2': {
                'c01': [('STEP', 'CLIENT', 'exp_c01', 'NX_FLOAT', None)],
                'c02': [('STEP', 'CLIENT', 'exp_c02', 'NX_FLOAT', None)],
                'mca': [('STEP', 'CLIENT', 'p09/mca/exp.02', 'NX_FLOAT',
                         [2048])],
            },
            'scan3': {
                'c01': [('STEP', 'CLIENT', 'exp_c01', 'NX_FLOAT', None),
                        ('INIT', 'CLIENT', 'exp_c01', 'NX_FLOAT', None)],
                'mca': [('STEP', 'CLIENT', 'p09/mca/exp.02', 'NX_FLOAT',
                         [2048])],
            },
        }

        self.smycps = {
            'smycp': (
                '<definition><group type="NXcollection" name="dddd">'
                '<field name="long">'
                '$datasources.scalar_long<strategy mode="STEP"/></field>'
                '<field name="short">'
                '$datasources.scalar_short<strategy mode="STEP"/></field>'
                '</group></definition>'),
            'smycp2': (
                '<definition><group type="NXcollection" name="dddd">'
                '<field name="long">'
                '$datasources.spectrum_long<strategy mode="INIT"/></field>'
                '<field name="short">'
                '$datasources.spectrum_short<strategy mode="STEP"/></field>'
                '</group></definition>'),
            'smycp3': (
                '<definition><group type="NXcollection" name="dddd">'
                '<field name="long">'
                '$datasources.image_long<strategy mode="FINAL"/></field>'
                '<field name="short">'
                '$datasources.image_short<strategy mode="STEP"/></field>'
                '</group></definition>'),
            'smycpnt1': (
                '<definition><group type="NXcollection" name="ddddnt">'
                '<field name="long">'
                '$datasources.client_long<strategy mode="FINAL"/></field>'
                '<field name="short">'
                '$datasources.client_short<strategy mode="STEP"/></field>'
                '</group></definition>'),
        }

        self.smycpsstep = {
            'smycp': ("scalar_long", "scalar_short"),
            'smycp2': ("spectrum_short",),
            'smycp3': ("image_short",),
            'smycpnt1': ("client_short",),
        }
        self.smycpsstep2 = {
            's2mycp': ("scalar2_long", "scalar2_short"),
            's2mycp2': ("spectrum2_long",),
            's2mycp3': ("image2_long",),
            's2mycpnt1': ("client2_short",),
        }

        self.smycps2 = {
            's2mycp': (
                '<definition><group type="NXcollection" name="dddd2">'
                '<field name="long">'
                '$datasources.scalar2_long<strategy mode="STEP"/></field>'
                '<field name="short">'
                '$datasources.scalar2_short<strategy mode="STEP"/></field>'
                '</group></definition>'),
            's2mycp2': (
                '<definition><group type="NXcollection" name="dddd2">'
                '<field name="long">'
                '$datasources.spectrum2_long<strategy mode="STEP"/></field>'
                '<field name="short">'
                '$datasources.spectrum2_short<strategy mode="FINAL"/></field>'
                '</group></definition>'),
            's2mycp3': (
                '<definition><group type="NXcollection" name="dddd2">'
                '<field name="long">'
                '$datasources.image2_long<strategy mode="STEP"/></field>'
                '<field name="short">'
                '$datasources.image2_short<strategy mode="INIT"/></field>'
                '</group></definition>'),
            's2mycpnt1': (
                '<definition><group type="NXcollection" name="dddd2nt">'
                '<field name="long">'
                '$datasources.client2_long<strategy mode="FINAL"/></field>'
                '<field name="short">'
                '$datasources.client2_short<strategy mode="STEP"/></field>'
                '</group></definition>'),
        }

        self.smydss = {
            'scalar_long': (
                '<definition><datasource type="TANGO" name="scalar_long">'
                '<record name="ScalarLong"/>'
                '<device member="attribute" name="ttestp09/testts/t1r228"/>'
                '</datasource></definition>'),
            'scalar_bool': (
                '<definition><datasource type="TANGO" name="scalar_bool">'
                '<record name="ScalarBoolean"/>'
                '<device member="attribute" name="ttestp09/testts/t1r228"/>'
                '</datasource></definition>'),
            'scalar_short': (
                '<definition><datasource type="TANGO" name="scalar_short">'
                '<record name="ScalarShort"/>'
                '<device member="attribute" name="ttestp09/testts/t1r228"/>'
                '</datasource></definition>'),
            'scalar_ushort': (
                '<definition><datasource type="TANGO" name="scalar_ushort">'
                '<record name="ScalarUShort"/>'
                '<device member="attribute" name="ttestp09/testts/t1r228"/>'
                '</datasource></definition>'),
            'scalar_ulong': (
                '<definition><datasource type="TANGO" name="scalar_ulong">'
                '<record name="ScalarULong"/>'
                '<device member="attribute" name="ttestp09/testts/t1r228"/>'
                '</datasource></definition>'),
            'scalar_long64': (
                '<definition><datasource type="TANGO" name="scalar_long64">'
                '<record name="ScalarLong64"/>'
                '<device member="attribute" name="ttestp09/testts/t1r228"/>'
                '</datasource></definition>'),
            'scalar_ulong64': (
                '<definition><datasource type="TANGO" name="scalar_ulong64">'
                '<record name="ScalarULong64"/>'
                '<device member="attribute" name="ttestp09/testts/t1r228"/>'
                '</datasource></definition>'),
            'scalar_float': (
                '<definition><datasource type="TANGO" name="scalar_float">'
                '<record name="ScalarFloat"/>'
                '<device member="attribute" name="ttestp09/testts/t1r228"/>'
                '</datasource></definition>'),
            'scalar_double': (
                '<definition><datasource type="TANGO" name="scalar_double">'
                '<record name="ScalarDouble"/>'
                '<device member="attribute" name="ttestp09/testts/t1r228"/>'
                '</datasource></definition>'),
            'scalar_string': (
                '<definition><datasource type="TANGO" name="scalar_string">'
                '<record name="ScalarString"/>'
                '<device member="attribute" name="ttestp09/testts/t1r228"/>'
                '</datasource></definition>'),
            'scalar_encoded': (
                '<definition><datasource type="TANGO" name="scalar_encoded">'
                '<record name="ScalarEncoded"/>'
                '<device member="attribute" name="ttestp09/testts/t1r228"/>'
                '</datasource></definition>'),
            'scalar_uchar': (
                '<definition><datasource type="TANGO" name="scalar_uchar">'
                '<record name="ScalarUChar"/>'
                '<device member="attribute" name="ttestp09/testts/t1r228"/>'
                '</datasource></definition>'),
            'spectrum_long': (
                '<definition><datasource type="TANGO" name="spectrum_long">'
                '<record name="SpectrumLong"/>'
                '<device member="attribute" name="ttestp09/testts/t1r228"/>'
                '</datasource></definition>'),
            'spectrum_bool': (
                '<definition><datasource type="TANGO" name="spectrum_bool">'
                '<record name="SpectrumBoolean"/>'
                '<device member="attribute" name="ttestp09/testts/t1r228"/>'
                '</datasource></definition>'),
            'spectrum_short': (
                '<definition><datasource type="TANGO" name="spectrum_short">'
                '<record name="SpectrumShort"/>'
                '<device member="attribute" name="ttestp09/testts/t1r228"/>'
                '</datasource></definition>'),
            'spectrum_ushort': (
                '<definition><datasource type="TANGO" name="spectrum_ushort">'
                '<record name="SpectrumUShort"/>'
                '<device member="attribute" name="ttestp09/testts/t1r228"/>'
                '</datasource></definition>'),
            'spectrum_ulong': (
                '<definition><datasource type="TANGO" name="spectrum_ulong">'
                '<record name="SpectrumULong"/>'
                '<device member="attribute" name="ttestp09/testts/t1r228"/>'
                '</datasource></definition>'),
            'spectrum_long64': (
                '<definition><datasource type="TANGO" name="spectrum_long64">'
                '<record name="SpectrumLong64"/>'
                '<device member="attribute" name="ttestp09/testts/t1r228"/>'
                '</datasource></definition>'),
            'spectrum_ulong64': (
                '<definition><datasource type="TANGO" name="spectrum_ulong64">'
                '<record name="SpectrumULong64"/>'
                '<device member="attribute" name="ttestp09/testts/t1r228"/>'
                '</datasource></definition>'),
            'spectrum_float': (
                '<definition><datasource type="TANGO" name="spectrum_float">'
                '<record name="SpectrumFloat"/>'
                '<device member="attribute" name="ttestp09/testts/t1r228"/>'
                '</datasource></definition>'),
            'spectrum_double': (
                '<definition><datasource type="TANGO" name="spectrum_double">'
                '<record name="SpectrumDouble"/>'
                '<device member="attribute" name="ttestp09/testts/t1r228"/>'
                '</datasource></definition>'),
            'spectrum_string': (
                '<definition><datasource type="TANGO" name="spectrum_string">'
                '<record name="SpectrumString"/>'
                '<device member="attribute" name="ttestp09/testts/t1r228"/>'
                '</datasource></definition>'),
            'spectrum_encoded': (
                '<definition><datasource type="TANGO" name="spectrum_encoded">'
                '<record name="SpectrumEncoded"/>'
                '<device member="attribute" name="ttestp09/testts/t1r228"/>'
                '</datasource></definition>'),
            'spectrum_uchar': (
                '<definition><datasource type="TANGO" name="spectrum_uchar">'
                '<record name="SpectrumUChar"/>'
                '<device member="attribute" name="ttestp09/testts/t1r228"/>'
                '</datasource></definition>'),
            'image_long': (
                '<definition><datasource type="TANGO" name="image_long">'
                '<record name="ImageLong"/>'
                '<device member="attribute" name="ttestp09/testts/t1r228"/>'
                '</datasource></definition>'),
            'image_bool': (
                '<definition><datasource type="TANGO" name="image_bool">'
                '<record name="ImageBoolean"/>'
                '<device member="attribute" name="ttestp09/testts/t1r228"/>'
                '</datasource></definition>'),
            'image_short': (
                '<definition><datasource type="TANGO" name="image_short">'
                '<record name="ImageShort"/>'
                '<device member="attribute" name="ttestp09/testts/t1r228"/>'
                '</datasource></definition>'),
            'image_ushort': (
                '<definition><datasource type="TANGO" name="image_ushort">'
                '<record name="ImageUShort"/>'
                '<device member="attribute" name="ttestp09/testts/t1r228"/>'
                '</datasource></definition>'),
            'image_ulong': (
                '<definition><datasource type="TANGO" name="image_ulong">'
                '<record name="ImageULong"/>'
                '<device member="attribute" name="ttestp09/testts/t1r228"/>'
                '</datasource></definition>'),
            'image_long64':
                ('<definition><datasource type="TANGO" name="image_long64">'
                 '<record name="ImageLong64"/>'
                 '<device member="attribute" name="ttestp09/testts/t1r228"/>'
                 '</datasource></definition>'),
            'image_ulong64':
                ('<definition><datasource type="TANGO" name="image_ulong64">'
                 '<record name="ImageULong64"/>'
                 '<device member="attribute" name="ttestp09/testts/t1r228"/>'
                 '</datasource></definition>'),
            'image_float':
                ('<definition><datasource type="TANGO" name="image_float">'
                 '<record name="ImageFloat"/>'
                 '<device member="attribute" name="ttestp09/testts/t1r228"/>'
                 '</datasource></definition>'),
            'image_double':
                ('<definition><datasource type="TANGO" name="image_double">'
                 '<record name="ImageDouble"/>'
                 '<device member="attribute" name="ttestp09/testts/t1r228"/>'
                 '</datasource></definition>'),
            'image_string':
                ('<definition><datasource type="TANGO" name="image_string">'
                 '<record name="ImageString"/>'
                 '<device member="attribute" name="ttestp09/testts/t1r228"/>'
                 '</datasource></definition>'),
            'image_encoded':
                ('<definition><datasource type="TANGO" name="image_encoded">'
                 '<record name="ImageEncoded"/>'
                 '<device member="attribute" name="ttestp09/testts/t1r228"/>'
                 '</datasource></definition>'),
            'image_uchar':
                ('<definition><datasource type="TANGO" name="image_uchar">'
                 '<record name="ImageUChar"/>'
                 '<device member="attribute" name="ttestp09/testts/t1r228"/>'
                 '</datasource></definition>'),
            'client_long':
                ('<definition><datasource type="CLIENT" name="client_long">'
                 '<record name="ClientLong"/>'
                 '</datasource></definition>'),
            'client_short':
                ('<definition><datasource type="CLIENT" name="client_short">'
                 '<record name="ClientShort"/>'
                 '</datasource></definition>'),
        }

        self.smydsspar = {
            'scalar_long': ([]),
            'scalar_bool': ([]),
            'scalar_short': ([]),
            'scalar_ushort': ([]),
            'scalar_ulong': ([]),
            'scalar_long64': ([]),
            'scalar_ulong64': ([]),
            'scalar_float': ([]),
            'scalar_double': ([]),
            'scalar_string': ([]),
            'scalar_encoded': ([]),
            'scalar_uchar': ([]),
            'spectrum_long': ([4]),
            'spectrum_bool': ([2]),
            'spectrum_short': ([3]),
            'spectrum_ushort': ([4]),
            'spectrum_ulong': ([4]),
            'spectrum_long64': ([4]),
            'spectrum_ulong64': ([4]),
            'spectrum_float': ([4]),
            'spectrum_double': ([4]),
            'spectrum_string': ([4]),
            'spectrum_encoded': ([]),
            'spectrum_uchar': ([2]),
            'image_long': ([2, 2]),
            'image_bool': ([1, 1]),
            'image_short': ([2, 2]),
            'image_ushort': ([2, 2]),
            'image_ulong': ([2, 2]),
            'image_long64':
                ([2, 2]),
            'image_ulong64':
                ([2, 2]),
            'image_float':
                ([2, 2]),
            'image_double':
                ([2, 2]),
            'image_string':
                ([1, 1]),
            'image_encoded':
                ([]),
            'image_uchar':
                ([2, 2]),
            'client_long':
                ([]),
            'client_short':
                ([]),
        }

        self.smydssXX = {
            'scalar2_long': (
                '<definition><datasource type="TANGO" name="scalar2_long">'
                '<record name="ScalarLong"/>'
                '<device member="attribute" name="ttestp09/testts/t01r228"/>'
                '</datasource></definition>'),
            'scalar2_bool': (
                '<definition><datasource type="TANGO" name="scalar2_bool">'
                '<record name="ScalarBoolean"/>'
                '<device member="attribute" name="ttestp09/testts/t02r228"/>'
                '</datasource></definition>'),
            'scalar2_short': (
                '<definition><datasource type="TANGO" name="scalar2_short">'
                '<record name="ScalarShort"/>'
                '<device member="attribute" name="ttestp09/testts/t03r228"/>'
                '</datasource></definition>'),
            'scalar2_ushort': (
                '<definition><datasource type="TANGO" name="scalar2_ushort">'
                '<record name="ScalarUShort"/>'
                '<device member="attribute" name="ttestp09/testts/t04r228"/>'
                '</datasource></definition>'),
            'scalar2_ulong': (
                '<definition><datasource type="TANGO" name="scalar2_ulong">'
                '<record name="ScalarULong"/>'
                '<device member="attribute" name="ttestp09/testts/t05r228"/>'
                '</datasource></definition>'),
            'scalar2_long64': (
                '<definition><datasource type="TANGO" name="scalar2_long64">'
                '<record name="ScalarLong64"/>'
                '<device member="attribute" name="ttestp09/testts/t06r228"/>'
                '</datasource></definition>'),
            'scalar2_ulong64': (
                '<definition><datasource type="TANGO" name="scalar2_ulong64">'
                '<record name="ScalarULong64"/>'
                '<device member="attribute" name="ttestp09/testts/t07r228"/>'
                '</datasource></definition>'),
            'scalar2_float': (
                '<definition><datasource type="TANGO" name="scalar2_float">'
                '<record name="ScalarFloat"/>'
                '<device member="attribute" name="ttestp09/testts/t08r228"/>'
                '</datasource></definition>'),
            'scalar2_double': (
                '<definition><datasource type="TANGO" name="scalar2_double">'
                '<record name="ScalarDouble"/>'
                '<device member="attribute" name="ttestp09/testts/t09r228"/>'
                '</datasource></definition>'),
            'scalar2_string': (
                '<definition><datasource type="TANGO" name="scalar2_string">'
                '<record name="ScalarString"/>'
                '<device member="attribute" name="ttestp09/testts/t10r228"/>'
                '</datasource></definition>'),
            'scalar2_encoded': (
                '<definition><datasource type="TANGO" name="scalar2_encoded">'
                '<record name="ScalarEncoded"/>'
                '<device member="attribute" name="ttestp09/testts/t11r228"/>'
                '</datasource></definition>'),
            'scalar2_uchar': (
                '<definition><datasource type="TANGO" name="scalar2_uchar">'
                '<record name="ScalarUChar"/>'
                '<device member="attribute" name="ttestp09/testts/t12r228"/>'
                '</datasource></definition>'),
            'spectrum2_long': (
                '<definition><datasource type="TANGO" name="spectrum2_long">'
                '<record name="SpectrumLong"/>'
                '<device member="attribute" name="ttestp09/testts/t13r228"/>'
                '</datasource></definition>'),
            'spectrum2_bool': (
                '<definition><datasource type="TANGO" name="spectrum2_bool">'
                '<record name="SpectrumBoolean"/>'
                '<device member="attribute" name="ttestp09/testts/t14r228"/>'
                '</datasource></definition>'),
            'spectrum2_short': (
                '<definition><datasource type="TANGO" name="spectrum2_short">'
                '<record name="SpectrumShort"/>'
                '<device member="attribute" name="ttestp09/testts/t15r228"/>'
                '</datasource></definition>'),
            'spectrum2_ushort': (
                '<definition><datasource type="TANGO" name="spectrum2_ushort">'
                '<record name="SpectrumUShort"/>'
                '<device member="attribute" name="ttestp09/testts/t16r228"/>'
                '</datasource></definition>'),
            'spectrum2_ulong': (
                '<definition><datasource type="TANGO" name="spectrum2_ulong">'
                '<record name="SpectrumULong"/>'
                '<device member="attribute" name="ttestp09/testts/t17r228"/>'
                '</datasource></definition>'),
            'spectrum2_long64': (
                '<definition><datasource type="TANGO" name="spectrum2_long64">'
                '<record name="SpectrumLong64"/>'
                '<device member="attribute" name="ttestp09/testts/t18r228"/>'
                '</datasource></definition>'),
            'spectrum2_ulong64': (
                '<definition>'
                '<datasource type="TANGO" name="spectrum2_ulong64">'
                '<record name="SpectrumULong64"/>'
                '<device member="attribute" name="ttestp09/testts/t19r228"/>'
                '</datasource></definition>'),
            'spectrum2_float': (
                '<definition><datasource type="TANGO" name="spectrum2_float">'
                '<record name="SpectrumFloat"/>'
                '<device member="attribute" name="ttestp09/testts/t20r228"/>'
                '</datasource></definition>'),
            'spectrum2_double': (
                '<definition><datasource type="TANGO" name="spectrum2_double">'
                '<record name="SpectrumDouble"/>'
                '<device member="attribute" name="ttestp09/testts/t21r228"/>'
                '</datasource></definition>'),
            'spectrum2_string': (
                '<definition><datasource type="TANGO" name="spectrum2_string">'
                '<record name="SpectrumString"/>'
                '<device member="attribute" name="ttestp09/testts/t22r228"/>'
                '</datasource></definition>'),
            'spectrum2_encoded': (
                '<definition>'
                '<datasource type="TANGO" name="spectrum2_encoded">'
                '<record name="SpectrumEncoded"/>'
                '<device member="attribute" name="ttestp09/testts/t23r228"/>'
                '</datasource></definition>'),
            'spectrum2_uchar': (
                '<definition><datasource type="TANGO" name="spectrum2_uchar">'
                '<record name="SpectrumUChar"/>'
                '<device member="attribute" name="ttestp09/testts/t24r228"/>'
                '</datasource></definition>'),
            'image2_long': (
                '<definition><datasource type="TANGO" name="image2_long">'
                '<record name="ImageLong"/>'
                '<device member="attribute" name="ttestp09/testts/t25r228"/>'
                '</datasource></definition>'),
            'image2_bool': (
                '<definition><datasource type="TANGO" name="image2_bool">'
                '<record name="ImageBoolean"/>'
                '<device member="attribute" name="ttestp09/testts/t26r228"/>'
                '</datasource></definition>'),
            'image2_short': (
                '<definition><datasource type="TANGO" name="image2_short">'
                '<record name="ImageShort"/>'
                '<device member="attribute" name="ttestp09/testts/t27r228"/>'
                '</datasource></definition>'),
            'image2_ushort': (
                '<definition><datasource type="TANGO" name="image2_ushort">'
                '<record name="ImageUShort"/>'
                '<device member="attribute" name="ttestp09/testts/t28r228"/>'
                '</datasource></definition>'),
            'image2_ulong': (
                '<definition><datasource type="TANGO" name="image2_ulong">'
                '<record name="ImageULong"/>'
                '<device member="attribute" name="ttestp09/testts/t29r228"/>'
                '</datasource></definition>'),
            'image2_long64':
                ('<definition><datasource type="TANGO" name="image2_long64">'
                 '<record name="ImageLong64"/>'
                 '<device member="attribute" name="ttestp09/testts/t30r228"/>'
                 '</datasource></definition>'),
            'image2_ulong64':
                ('<definition><datasource type="TANGO" name="image2_ulong64">'
                 '<record name="ImageULong64"/>'
                 '<device member="attribute" name="ttestp09/testts/t31r228"/>'
                 '</datasource></definition>'),
            'image2_float':
                ('<definition><datasource type="TANGO" name="image2_float">'
                 '<record name="ImageFloat"/>'
                 '<device member="attribute" name="ttestp09/testts/t32r228"/>'
                 '</datasource></definition>'),
            'image2_double':
                ('<definition><datasource type="TANGO" name="image2_double">'
                 '<record name="ImageDouble"/>'
                 '<device member="attribute" name="ttestp09/testts/t33r228"/>'
                 '</datasource></definition>'),
            'image2_string':
                ('<definition><datasource type="TANGO" name="image2_string">'
                 '<record name="ImageString"/>'
                 '<device member="attribute" name="ttestp09/testts/t34r228"/>'
                 '</datasource></definition>'),
            'image2_encoded':
                ('<definition><datasource type="TANGO" name="image2_encoded">'
                 '<record name="ImageEncoded"/>'
                 '<device member="attribute" name="ttestp09/testts/t35r228"/>'
                 '</datasource></definition>'),
            'image2_uchar':
                ('<definition><datasource type="TANGO" name="image2_uchar">'
                 '<record name="ImageUChar"/>'
                 '<device member="attribute" name="ttestp09/testts/t36r228"/>'
                 '</datasource></definition>'),
            'client2_long':
                ('<definition><datasource type="CLIENT" name="client2_long">'
                 '<record name="ClientLong"/>'
                 '</datasource></definition>'),
            'client2_short':
                ('<definition><datasource type="CLIENT" name="client2_short">'
                 '<record name="ClientShort"/>'
                 '</datasource></definition>'),
        }

        self.smychs = {
            'scalar_long': {
                'data_type': 'int32',
                'plot_type': 1,
                'data_units': 'No unit' if TGVER < 9 else '',
                'shape': [],
                'plot_axes': ['<mov>'],
                'source': 'ttestp09/testts/t1r228/ScalarLong'},
            'scalar_bool': {
                'data_type': 'bool',
                'plot_type': 1,
                'data_units': 'No unit' if TGVER < 9 else '',
                'shape': [],
                'plot_axes': ['<mov>'],
                'source': 'ttestp09/testts/t1r228/ScalarBoolean'},
            'scalar_short': {
                'data_type': 'int16',
                'plot_type': 1,
                'data_units': 'No unit' if TGVER < 9 else '',
                'shape': [],
                'plot_axes': ['<mov>'],
                'source': 'ttestp09/testts/t1r228/ScalarShort'},
            'scalar_ushort': {
                'data_type': 'uint16',
                'plot_type': 1,
                'data_units': 'No unit' if TGVER < 9 else '',
                'shape': [],
                'plot_axes': ['<mov>'],
                'source': 'ttestp09/testts/t1r228/ScalarUShort'},
            'scalar_ulong': {
                'data_type': 'uint32',
                'plot_type': 1,
                'data_units': 'No unit' if TGVER < 9 else '',
                'shape': [],
                'plot_axes': ['<mov>'],
                'source': 'ttestp09/testts/t1r228/ScalarULong'},
            'scalar_long64': {
                'data_type': 'int64',
                'plot_type': 1,
                'data_units': 'No unit' if TGVER < 9 else '',
                'shape': [],
                'plot_axes': ['<mov>'],
                'source': 'ttestp09/testts/t1r228/ScalarLong64'},
            'scalar_ulong64': {
                'data_type': 'uint64',
                'plot_type': 1,
                'data_units': 'No unit' if TGVER < 9 else '',
                'shape': [],
                'plot_axes': ['<mov>'],
                'source': 'ttestp09/testts/t1r228/ScalarULong64'},
            'scalar_float': {
                'data_type': 'float32',
                'plot_type': 1,
                'data_units': 'No unit' if TGVER < 9 else '',
                'shape': [],
                'plot_axes': ['<mov>'],
                'source': 'ttestp09/testts/t1r228/ScalarFloat'},
            'scalar_double': {
                'data_type': 'float64',
                'plot_type': 1,
                'data_units': 'No unit' if TGVER < 9 else '',
                'shape': [],
                'plot_axes': ['<mov>'],
                'source': 'ttestp09/testts/t1r228/ScalarDouble'},
            'scalar_string': {
                'data_type': 'string',
                'plot_type': 1,
                'data_units': 'No unit' if TGVER < 9 else '',
                'shape': [],
                'plot_axes': ['<mov>'],
                'source': 'ttestp09/testts/t1r228/ScalarString'},
            'scalar_encoded': {
                'data_type': 'encoded',
                'plot_type': 1,
                'data_units': 'No unit' if TGVER < 9 else '',
                'shape': [],
                'plot_axes': ['<mov>'],
                'source': 'ttestp09/testts/t1r228/ScalarEncoded'},
            'scalar_uchar': {
                'data_type': 'uint8',
                'plot_type': 1,
                'data_units': 'No unit' if TGVER < 9 else '',
                'shape': [],
                'plot_axes': ['<mov>'],
                'source': 'ttestp09/testts/t1r228/ScalarUChar'},
            'spectrum_long': {
                'data_type': 'int32',
                'plot_type': 1,
                'data_units': 'No unit' if TGVER < 9 else '',
                'shape': [4],
                'plot_axes': ['<idx>'],
                'source': 'ttestp09/testts/t1r228/SpectrumLong'},
            'spectrum_bool': {
                'data_type': 'bool',
                'plot_type': 1,
                'data_units': 'No unit' if TGVER < 9 else '',
                'shape': [2],
                'plot_axes': ['<idx>'],
                'source': 'ttestp09/testts/t1r228/SpectrumBoolean'},
            'spectrum_short': {
                'data_type': 'int16',
                'plot_type': 1,
                'data_units': 'No unit' if TGVER < 9 else '',
                'shape': [3],
                'plot_axes': ['<idx>'],
                'source': 'ttestp09/testts/t1r228/SpectrumShort'},
            'spectrum_ushort': {
                'data_type': 'uint16',
                'plot_type': 1,
                'data_units': 'No unit' if TGVER < 9 else '',
                'shape': [4],
                'plot_axes': ['<idx>'],
                'source': 'ttestp09/testts/t1r228/SpectrumUShort'},
            'spectrum_ulong': {
                'data_type': 'uint32',
                'plot_type': 1,
                'data_units': 'No unit' if TGVER < 9 else '',
                'shape': [4],
                'plot_axes': ['<idx>'],
                'source': 'ttestp09/testts/t1r228/SpectrumULong'},
            'spectrum_long64': {
                'data_type': 'int64',
                'plot_type': 1,
                'data_units': 'No unit' if TGVER < 9 else '',
                'shape': [4],
                'plot_axes': ['<idx>'],
                'source': 'ttestp09/testts/t1r228/SpectrumLong64'},
            'spectrum_ulong64': {
                'data_type': 'uint64',
                'plot_type': 1,
                'data_units': 'No unit' if TGVER < 9 else '',
                'shape': [4],
                'plot_axes': ['<idx>'],
                'source': 'ttestp09/testts/t1r228/SpectrumULong64'},
            'spectrum_float': {
                'data_type': 'float32',
                'plot_type': 1,
                'data_units': 'No unit' if TGVER < 9 else '',
                'shape': [4],
                'plot_axes': ['<idx>'],
                'source': 'ttestp09/testts/t1r228/SpectrumFloat'},
            'spectrum_double': {
                'data_type': 'float64',
                'plot_type': 1,
                'data_units': 'No unit' if TGVER < 9 else '',
                'shape': [4],
                'plot_axes': ['<idx>'],
                'source': 'ttestp09/testts/t1r228/SpectrumDouble'},
            'spectrum_string': {
                'data_type': 'string',
                'plot_type': 1,
                'data_units': 'No unit' if TGVER < 9 else '',
                'shape': [4],
                'plot_axes': ['<idx>'],
                'source': 'ttestp09/testts/t1r228/SpectrumString'},
            'spectrum_encoded': {
                'data_type': 'encoded',
                'plot_type': 1,
                'data_units': 'No unit' if TGVER < 9 else '',
                'shape': [],
                'plot_axes': ['<mov>'],
                'source': 'ttestp09/testts/t1r228/SpectrumEncoded'},
            'spectrum_uchar': {
                'data_type': 'uint8',
                'plot_type': 1,
                'data_units': 'No unit' if TGVER < 9 else '',
                'shape': [2],
                'plot_axes': ['<idx>'],
                'source': 'ttestp09/testts/t1r228/SpectrumUChar'},

            'image_long': {
                'data_type': 'int32',
                'plot_type': 2,
                'data_units': 'No unit' if TGVER < 9 else '',
                'shape': [2, 2],
                'plot_axes': ['<idx>', '<idx>'],
                'source': 'ttestp09/testts/t1r228/ImageLong'},
            'image_bool': {
                'data_type': 'bool',
                'plot_type': 2,
                'data_units': 'No unit' if TGVER < 9 else '',
                'shape': [1, 1],
                'plot_axes': ['<idx>', '<idx>'],
                'source': 'ttestp09/testts/t1r228/ImageBoolean'},
            'image_short': {
                'data_type': 'int16',
                'plot_type': 2,
                'data_units': 'No unit' if TGVER < 9 else '',
                'shape': [2, 2],
                'plot_axes': ['<idx>', '<idx>'],
                'source': 'ttestp09/testts/t1r228/ImageShort'},
            'image_ushort': {
                'data_type': 'uint16',
                'plot_type': 2,
                'data_units': 'No unit' if TGVER < 9 else '',
                'shape': [2, 2],
                'plot_axes': ['<idx>', '<idx>'],
                'source': 'ttestp09/testts/t1r228/ImageUShort'},
            'image_ulong': {
                'data_type': 'uint32',
                'plot_type': 2,
                'data_units': 'No unit' if TGVER < 9 else '',
                'shape': [2, 2],
                'plot_axes': ['<idx>', '<idx>'],
                'source': 'ttestp09/testts/t1r228/ImageULong'},
            'image_long64': {
                'data_type': 'int64',
                'plot_type': 2,
                'data_units': 'No unit' if TGVER < 9 else '',
                'shape': [2, 2],
                'plot_axes': ['<idx>', '<idx>'],
                'source': 'ttestp09/testts/t1r228/ImageLong64'},
            'image_ulong64': {
                'data_type': 'uint64',
                'plot_type': 2,
                'data_units': 'No unit' if TGVER < 9 else '',
                'shape': [2, 2],
                'plot_axes': ['<idx>', '<idx>'],
                'source': 'ttestp09/testts/t1r228/ImageULong64'},
            'image_float': {
                'data_type': 'float32',
                'plot_type': 2,
                'data_units': 'No unit' if TGVER < 9 else '',
                'shape': [2, 2],
                'plot_axes': ['<idx>', '<idx>'],
                'source': 'ttestp09/testts/t1r228/ImageFloat'},
            'image_double': {
                'data_type': 'float64',
                'plot_type': 2,
                'data_units': 'No unit' if TGVER < 9 else '',
                'shape': [2, 2],
                'plot_axes': ['<idx>', '<idx>'],
                'source': 'ttestp09/testts/t1r228/ImageDouble'},
            'image_string': {
                'data_type': 'string',
                'plot_type': 2,
                'data_units': 'No unit' if TGVER < 9 else '',
                'shape': [1, 1],
                'plot_axes': ['<idx>', '<idx>'],
                'source': 'ttestp09/testts/t1r228/ImageString'},
            'image_encoded': {
                'data_type': 'encoded',
                'plot_type': 1,
                'data_units': 'No unit' if TGVER < 9 else '',
                'shape': [],
                'plot_axes': ['<mov>'],
                'source': 'ttestp09/testts/t1r228/ImageEncoded'},
            'image_uchar': {
                'data_type': 'uint8',
                'plot_type': 2,
                'data_units': 'No unit' if TGVER < 9 else '',
                'shape': [2, 2],
                'plot_axes': ['<idx>', '<idx>'],
                'source': 'ttestp09/testts/t1r228/ImageUChar'},
            'client_long': {},
            'client_short': {},
        }

        self.smychsXX = {
            'scalar2_long': {
                'data_type': 'int32',
                'plot_type': 1,
                'data_units': 'No unit' if TGVER < 9 else '',
                'shape': [],
                'plot_axes': ['<mov>'],
                'source': 'ttestp09/testts/t01r228/ScalarLong'},
            'scalar2_bool': {
                'data_type': 'bool',
                'plot_type': 1,
                'data_units': 'No unit' if TGVER < 9 else '',
                'shape': [],
                'plot_axes': ['<mov>'],
                'source': 'ttestp09/testts/t02r228/ScalarBoolean'},
            'scalar2_short': {
                'data_type': 'int16',
                'plot_type': 1,
                'data_units': 'No unit' if TGVER < 9 else '',
                'shape': [],
                'plot_axes': ['<mov>'],
                'source': 'ttestp09/testts/t03r228/ScalarShort'},
            'scalar2_ushort': {
                'data_type': 'uint16',
                'plot_type': 1,
                'data_units': 'No unit' if TGVER < 9 else '',
                'shape': [],
                'plot_axes': ['<mov>'],
                'source': 'ttestp09/testts/t04r228/ScalarUShort'},
            'scalar2_ulong': {
                'data_type': 'uint32',
                'plot_type': 1,
                'data_units': 'No unit' if TGVER < 9 else '',
                'shape': [],
                'plot_axes': ['<mov>'],
                'source': 'ttestp09/testts/t05r228/ScalarULong'},
            'scalar2_long64': {
                'data_type': 'int64',
                'plot_type': 1,
                'data_units': 'No unit' if TGVER < 9 else '',
                'shape': [],
                'plot_axes': ['<mov>'],
                'source': 'ttestp09/testts/t06r228/ScalarLong64'},
            'scalar2_ulong64': {
                'data_type': 'uint64',
                'plot_type': 1,
                'data_units': 'No unit' if TGVER < 9 else '',
                'shape': [],
                'plot_axes': ['<mov>'],
                'source': 'ttestp09/testts/t07r228/ScalarULong64'},
            'scalar2_float': {
                'data_type': 'float32',
                'plot_type': 1,
                'data_units': 'No unit' if TGVER < 9 else '',
                'shape': [],
                'plot_axes': ['<mov>'],
                'source': 'ttestp09/testts/t08r228/ScalarFloat'},
            'scalar2_double': {
                'data_type': 'float64',
                'plot_type': 1,
                'data_units': 'No unit' if TGVER < 9 else '',
                'shape': [],
                'plot_axes': ['<mov>'],
                'source': 'ttestp09/testts/t09r228/ScalarDouble'},
            'scalar2_string': {
                'data_type': 'string',
                'plot_type': 1,
                'data_units': 'No unit' if TGVER < 9 else '',
                'shape': [],
                'plot_axes': ['<mov>'],
                'source': 'ttestp09/testts/t10r228/ScalarString'},
            'scalar2_encoded': {
                'data_type': 'encoded',
                'plot_type': 1,
                'data_units': 'No unit' if TGVER < 9 else '',
                'shape': [],
                'plot_axes': ['<mov>'],
                'source': 'ttestp09/testts/t11r228/ScalarEncoded'},
            'scalar2_uchar': {
                'data_type': 'uint8',
                'plot_type': 1,
                'data_units': 'No unit' if TGVER < 9 else '',
                'shape': [],
                'plot_axes': ['<mov>'],
                'source': 'ttestp09/testts/t12r228/ScalarUChar'},
            'spectrum2_long': {
                'data_type': 'int32',
                'plot_type': 1,
                'data_units': 'No unit' if TGVER < 9 else '',
                'shape': [4],
                'plot_axes': ['<idx>'],
                'source': 'ttestp09/testts/t13r228/SpectrumLong'},
            'spectrum2_bool': {
                'data_type': 'bool',
                'plot_type': 1,
                'data_units': 'No unit' if TGVER < 9 else '',
                'shape': [2],
                'plot_axes': ['<idx>'],
                'source': 'ttestp09/testts/t14r228/SpectrumBoolean'},
            'spectrum2_short': {
                'data_type': 'int16',
                'plot_type': 1,
                'data_units': 'No unit' if TGVER < 9 else '',
                'shape': [3],
                'plot_axes': ['<idx>'],
                'source': 'ttestp09/testts/t15r228/SpectrumShort'},
            'spectrum2_ushort': {
                'data_type': 'uint16',
                'plot_type': 1,
                'data_units': 'No unit' if TGVER < 9 else '',
                'shape': [4],
                'plot_axes': ['<idx>'],
                'source': 'ttestp09/testts/t16r228/SpectrumUShort'},
            'spectrum2_ulong': {
                'data_type': 'uint32',
                'plot_type': 1,
                'data_units': 'No unit' if TGVER < 9 else '',
                'shape': [4],
                'plot_axes': ['<idx>'],
                'source': 'ttestp09/testts/t17r228/SpectrumULong'},
            'spectrum2_long64': {
                'data_type': 'int64',
                'plot_type': 1,
                'data_units': 'No unit' if TGVER < 9 else '',
                'shape': [4],
                'plot_axes': ['<idx>'],
                'source': 'ttestp09/testts/t18r228/SpectrumLong64'},
            'spectrum2_ulong64': {
                'data_type': 'uint64',
                'plot_type': 1,
                'data_units': 'No unit' if TGVER < 9 else '',
                'shape': [4],
                'plot_axes': ['<idx>'],
                'source': 'ttestp09/testts/t19r228/SpectrumULong64'},
            'spectrum2_float': {
                'data_type': 'float32',
                'plot_type': 1,
                'data_units': 'No unit' if TGVER < 9 else '',
                'shape': [4],
                'plot_axes': ['<idx>'],
                'source': 'ttestp09/testts/t20r228/SpectrumFloat'},
            'spectrum2_double': {
                'data_type': 'float64',
                'plot_type': 1,
                'data_units': 'No unit' if TGVER < 9 else '',
                'shape': [4],
                'plot_axes': ['<idx>'],
                'source': 'ttestp09/testts/t21r228/SpectrumDouble'},
            'spectrum2_string': {
                'data_type': 'string',
                'plot_type': 1,
                'data_units': 'No unit' if TGVER < 9 else '',
                'shape': [4],
                'plot_axes': ['<idx>'],
                'source': 'ttestp09/testts/t22r228/SpectrumString'},
            'spectrum2_encoded': {
                'data_type': 'encoded',
                'plot_type': 1,
                'data_units': 'No unit' if TGVER < 9 else '',
                'shape': [],
                'plot_axes': ['<mov>'],
                'source': 'ttestp09/testts/t23r228/SpectrumEncoded'},
            'spectrum2_uchar': {
                'data_type': 'uint8',
                'plot_type': 1,
                'data_units': 'No unit' if TGVER < 9 else '',
                'shape': [2],
                'plot_axes': ['<idx>'],
                'source': 'ttestp09/testts/t24r228/SpectrumUChar'},

            'image2_long': {
                'data_type': 'int32',
                'plot_type': 2,
                'data_units': 'No unit' if TGVER < 9 else '',
                'shape': [2, 2],
                'plot_axes': ['<idx>', '<idx>'],
                'source': 'ttestp09/testts/t25r228/ImageLong'},
            'image2_bool': {
                'data_type': 'bool',
                'plot_type': 2,
                'data_units': 'No unit' if TGVER < 9 else '',
                'shape': [1, 1],
                'plot_axes': ['<idx>', '<idx>'],
                'source': 'ttestp09/testts/t26r228/ImageBoolean'},
            'image2_short': {
                'data_type': 'int16',
                'plot_type': 2,
                'data_units': 'No unit' if TGVER < 9 else '',
                'shape': [2, 2],
                'plot_axes': ['<idx>', '<idx>'],
                'source': 'ttestp09/testts/t27r228/ImageShort'},
            'image2_ushort': {
                'data_type': 'uint16',
                'plot_type': 2,
                'data_units': 'No unit' if TGVER < 9 else '',
                'shape': [2, 2],
                'plot_axes': ['<idx>', '<idx>'],
                'source': 'ttestp09/testts/t28r228/ImageUShort'},
            'image2_ulong': {
                'data_type': 'uint32',
                'plot_type': 2,
                'data_units': 'No unit' if TGVER < 9 else '',
                'shape': [2, 2],
                'plot_axes': ['<idx>', '<idx>'],
                'source': 'ttestp09/testts/t29r228/ImageULong'},
            'image2_long64': {
                'data_type': 'int64',
                'plot_type': 2,
                'data_units': 'No unit' if TGVER < 9 else '',
                'shape': [2, 2],
                'plot_axes': ['<idx>', '<idx>'],
                'source': 'ttestp09/testts/t30r228/ImageLong64'},
            'image2_ulong64': {
                'data_type': 'uint64',
                'plot_type': 2,
                'data_units': 'No unit' if TGVER < 9 else '',
                'shape': [2, 2],
                'plot_axes': ['<idx>', '<idx>'],
                'source': 'ttestp09/testts/t31r228/ImageULong64'},
            'image2_float': {
                'data_type': 'float32',
                'plot_type': 2,
                'data_units': 'No unit' if TGVER < 9 else '',
                'shape': [2, 2],
                'plot_axes': ['<idx>', '<idx>'],
                'source': 'ttestp09/testts/t32r228/ImageFloat'},
            'image2_double': {
                'data_type': 'float64',
                'plot_type': 2,
                'data_units': 'No unit' if TGVER < 9 else '',
                'shape': [2, 2],
                'plot_axes': ['<idx>', '<idx>'],
                'source': 'ttestp09/testts/t33r228/ImageDouble'},
            'image2_string': {
                'data_type': 'string',
                'plot_type': 2,
                'data_units': 'No unit' if TGVER < 9 else '',
                'shape': [1, 1],
                'plot_axes': ['<idx>', '<idx>'],
                'source': 'ttestp09/testts/t34r228/ImageString'},
            'image2_encoded': {
                'data_type': 'encoded',
                'plot_type': 1,
                'data_units': 'No unit' if TGVER < 9 else '',
                'shape': [],
                'plot_axes': ['<mov>'],
                'source': 'ttestp09/testts/t35r228/ImageEncoded'},
            'image2_uchar': {
                'data_type': 'uint8',
                'plot_type': 2,
                'data_units': 'No unit' if TGVER < 9 else '',
                'shape': [2, 2],
                'plot_axes': ['<idx>', '<idx>'],
                'source': 'ttestp09/testts/t36r228/ImageUChar'},
            'client2_long': {},
            'client2_short': {},
        }

        self.smydss2 = {
            'scalar2_long':
                ('<definition><datasource type="TANGO" name="scalar2_long">'
                 '<record name="ScalarLong"/>'
                 '<device member="attribute" name="ttestp09/testts/t2r228"/>'
                 '</datasource></definition>'),
            'scalar2_bool':
                ('<definition><datasource type="TANGO" name="scalar2_bool">'
                 '<record name="ScalarBoolean"/>'
                 '<device member="attribute" name="ttestp09/testts/t2r228"/>'
                 '</datasource></definition>'),
            'scalar2_short':
                ('<definition><datasource type="TANGO" name="scalar2_short">'
                 '<record name="ScalarShort"/>'
                 '<device member="attribute" name="ttestp09/testts/t2r228"/>'
                 '</datasource></definition>'),
            'scalar2_ushort':
                ('<definition><datasource type="TANGO" name="scalar2_ushort">'
                 '<record name="ScalarUShort"/>'
                 '<device member="attribute" name="ttestp09/testts/t2r228"/>'
                 '</datasource></definition>'),
            'scalar2_ulong':
                ('<definition><datasource type="TANGO" name="scalar2_ulong">'
                 '<record name="ScalarULong"/>'
                 '<device member="attribute" name="ttestp09/testts/t2r228"/>'
                 '</datasource></definition>'),
            'scalar2_long64':
                ('<definition><datasource type="TANGO" name="scalar2_long64">'
                 '<record name="ScalarLong64"/>'
                 '<device member="attribute" name="ttestp09/testts/t2r228"/>'
                 '</datasource></definition>'),
            'scalar2_ulong64':
                ('<definition><datasource type="TANGO" name="scalar2_ulong64">'
                 '<record name="ScalarULong64"/>'
                 '<device member="attribute" name="ttestp09/testts/t2r228"/>'
                 '</datasource></definition>'),
            'scalar2_float':
                ('<definition><datasource type="TANGO" name="scalar2_float">'
                 '<record name="ScalarFloat"/>'
                 '<device member="attribute" name="ttestp09/testts/t2r228"/>'
                 '</datasource></definition>'),
            'scalar2_double':
                ('<definition><datasource type="TANGO" name="scalar2_double">'
                 '<record name="ScalarDouble"/>'
                 '<device member="attribute" name="ttestp09/testts/t2r228"/>'
                 '</datasource></definition>'),
            'scalar2_string':
                ('<definition><datasource type="TANGO" name="scalar2_string">'
                 '<record name="ScalarString"/>'
                 '<device member="attribute" name="ttestp09/testts/t2r228"/>'
                 '</datasource></definition>'),
            'scalar2_encoded':
                ('<definition><datasource type="TANGO" name="scalar2_encoded">'
                 '<record name="ScalarEncoded"/>'
                 '<device member="attribute" name="ttestp09/testts/t2r228"/>'
                 '</datasource></definition>'),
            'scalar2_uchar':
                ('<definition><datasource type="TANGO" name="scalar2_uchar">'
                 '<record name="ScalarUChar"/>'
                 '<device member="attribute" name="ttestp09/testts/t2r228"/>'
                 '</datasource></definition>'),
            'spectrum2_long':
                ('<definition><datasource type="TANGO" name="spectrum2_long">'
                 '<record name="SpectrumLong"/>'
                 '<device member="attribute" name="ttestp09/testts/t2r228"/>'
                 '</datasource></definition>'),
            'spectrum2_bool':
                ('<definition><datasource type="TANGO" name="spectrum2_bool">'
                 '<record name="SpectrumBoolean"/>'
                 '<device member="attribute" name="ttestp09/testts/t2r228"/>'
                 '</datasource></definition>'),
            'spectrum2_short':
                ('<definition>'
                 '<datasource type="TANGO" name="spectrum2_short">'
                 '<record name="SpectrumShort"/>'
                 '<device member="attribute" name="ttestp09/testts/t2r228"/>'
                 '</datasource></definition>'),
            'spectrum2_ushort':
                ('<definition>'
                 '<datasource type="TANGO" name="spectrum2_ushort">'
                 '<record name="SpectrumUShort"/>'
                 '<device member="attribute" name="ttestp09/testts/t2r228"/>'
                 '</datasource></definition>'),
            'spectrum2_ulong':
                ('<definition>'
                 '<datasource type="TANGO" name="spectrum2_ulong">'
                 '<record name="SpectrumULong"/>'
                 '<device member="attribute" name="ttestp09/testts/t2r228"/>'
                 '</datasource></definition>'),
            'spectrum2_long64':
                ('<definition>'
                 '<datasource type="TANGO" name="spectrum2_long64">'
                 '<record name="SpectrumLong64"/>'
                 '<device member="attribute" name="ttestp09/testts/t2r228"/>'
                 '</datasource></definition>'),
            'spectrum2_ulong64':
                ('<definition>'
                 '<datasource type="TANGO" name="spectrum2_ulong64">'
                 '<record name="SpectrumULong64"/>'
                 '<device member="attribute" name="ttestp09/testts/t2r228"/>'
                 '</datasource></definition>'),
            'spectrum2_float':
                ('<definition><datasource type="TANGO" name="spectrum2_float">'
                 '<record name="SpectrumFloat"/>'
                 '<device member="attribute" name="ttestp09/testts/t2r228"/>'
                 '</datasource></definition>'),
            'spectrum2_double':
                ('<definition>'
                 '<datasource type="TANGO" name="spectrum2_double">'
                 '<record name="SpectrumDouble"/>'
                 '<device member="attribute" name="ttestp09/testts/t2r228"/>'
                 '</datasource></definition>'),
            'spectrum2_string':
                ('<definition>'
                 '<datasource type="TANGO" name="spectrum2_string">'
                 '<record name="SpectrumString"/>'
                 '<device member="attribute" name="ttestp09/testts/t2r228"/>'
                 '</datasource></definition>'),
            'spectrum2_encoded':
                ('<definition>'
                 '<datasource type="TANGO" name="spectrum2_encoded">'
                 '<record name="SpectrumEncoded"/>'
                 '<device member="attribute" name="ttestp09/testts/t2r228"/>'
                 '</datasource></definition>'),
            'spectrum2_uchar':
                ('<definition><datasource type="TANGO" name="spectrum2_uchar">'
                 '<record name="SpectrumUChar"/>'
                 '<device member="attribute" name="ttestp09/testts/t2r228"/>'
                 '</datasource></definition>'),
            'image2_long':
                ('<definition><datasource type="TANGO" name="image2_long">'
                 '<record name="ImageLong"/>'
                 '<device member="attribute" name="ttestp09/testts/t2r228"/>'
                 '</datasource></definition>'),
            'image2_bool':
                ('<definition><datasource type="TANGO" name="image2_bool">'
                 '<record name="ImageBoolean"/>'
                 '<device member="attribute" name="ttestp09/testts/t2r228"/>'
                 '</datasource></definition>'),
            'image2_short':
                ('<definition><datasource type="TANGO" name="image2_short">'
                 '<record name="ImageShort"/>'
                 '<device member="attribute" name="ttestp09/testts/t2r228"/>'
                 '</datasource></definition>'),
            'image2_ushort':
                ('<definition><datasource type="TANGO" name="image2_ushort">'
                 '<record name="ImageUShort"/>'
                 '<device member="attribute" name="ttestp09/testts/t2r228"/>'
                 '</datasource></definition>'),
            'image2_ulong':
                ('<definition><datasource type="TANGO" name="image2_ulong">'
                 '<record name="ImageULong"/>'
                 '<device member="attribute" name="ttestp09/testts/t2r228"/>'
                 '</datasource></definition>'),
            'image2_long64':
                ('<definition><datasource type="TANGO" name="image2_long64">'
                 '<record name="ImageLong64"/>'
                 '<device member="attribute" name="ttestp09/testts/t2r228"/>'
                 '</datasource></definition>'),
            'image2_ulong64':
                ('<definition><datasource type="TANGO" name="image2_ulong64">'
                 '<record name="ImageULong64"/>'
                 '<device member="attribute" name="ttestp09/testts/t2r228"/>'
                 '</datasource></definition>'),
            'image2_float':
                ('<definition><datasource type="TANGO" name="image2_float">'
                 '<record name="ImageFloat"/>'
                 '<device member="attribute" name="ttestp09/testts/t2r228"/>'
                 '</datasource></definition>'),
            'image2_double':
                ('<definition><datasource type="TANGO" name="image2_double">'
                 '<record name="ImageDouble"/>'
                 '<device member="attribute" name="ttestp09/testts/t2r228"/>'
                 '</datasource></definition>'),
            'image2_string':
                ('<definition><datasource type="TANGO" name="image2_string">'
                 '<record name="ImageString"/>'
                 '<device member="attribute" name="ttestp09/testts/t2r228"/>'
                 '</datasource></definition>'),
            'image2_encoded':
                ('<definition><datasource type="TANGO" name="image2_encoded">'
                 '<record name="ImageEncoded"/>'
                 '<device member="attribute" name="ttestp09/testts/t2r228"/>'
                 '</datasource></definition>'),
            'image2_uchar':
                ('<definition><datasource type="TANGO" name="image2_uchar">'
                 '<record name="ImageUChar"/>'
                 '<device member="attribute" name="ttestp09/testts/t2r228"/>'
                 '</datasource></definition>'),
            'client2_long':
                ('<definition><datasource type="CLIENT" name="client2_long">'
                 '<record name="Client2Long"/>'
                 '</datasource></definition>'),
            'client2_short':
                ('<definition><datasource type="CLIENT" name="client2_short">'
                 '<record name="Client2Short"/>'
                 '</datasource></definition>'),
        }

        self.mydss = {
            'nn':
            ('<?xml version=\'1.0\'?><definition><datasource type="TANGO">'
             '</datasource></definition>'),
            'nn2': ('<definition><datasource type="TANGO" name="">'
                    '</datasource></definition>'),
            'ann': ('<definition><datasource type="TANGO" name="ann">'
                    '</datasource></definition>'),
            'ann2': ('<definition><datasource type="CLIENT" name="ann2">'
                     '</datasource></definition>'),
            'ann3': ('<definition><datasource type="DB" name="ann3">'
                     '</datasource></definition>'),
            'ann4': ('<definition><datasource type="PYEVAL" name="ann4">'
                     '</datasource></definition>'),
            'ann5': ('<definition><datasource type="NEW" name="ann5">'
                     '</datasource></definition>'),
            'tann0': ('<definition><datasource type="TANGO" name="tann0">'
                      '<record name="myattr"/>'
                      '<device port="12345" encoding="sfd" hostname="sf" '
                      'member="attribute" name="dsff"/>'
                      '</datasource></definition>'),
            'tann1': ('<definition><datasource type="TANGO" name="tann1">'
                      '<record name="myattr2"/>'
                      '<device port="10000" encoding="sfd" hostname="sfa" '
                      'member="attribute" name="dsf"/>'
                      '</datasource></definition>'),
            'tann1b': ('<definition><datasource type="TANGO" name="tann1b">'
                       '<record name="myattr2"/>'
                       '<device member="attribute" name="dsf"/>'
                       '</datasource></definition>'),
            'tann1c': ('<definition><datasource type="TANGO" name="tann1c">'
                       '<record name="myattr2"/>'
                       '<device member="attribute" name="dsf/sd/we"/>'
                       '</datasource></definition>'),
            'P1M_postrun': (
                '<definition>'
                '<datasource type="PYEVAL" name="P1M_postrun">'
                '<result name="result">'
                'ds.result = "" + ds.P1M_fileDir + "/" + ds.P1M_filePrefix + '
                '"%03i" + ds.P1M_filePostfix + ":1:" + '
                ' str(ds.P1M_fileStartNum)</result>'
                ' $datasources.P1M_fileStartNum'
                ' $datasources.P1M_fileDir'
                ' $datasources.P1M_filePostfix'
                ' $datasources.P1M_filePrefix</datasource>'
                '</definition>'),
            'dbtest': (
                '<definition>'
                '<datasource type="DB" name="dbtest">'
                '<database dbtype="MYSQL"/>'
                '<query format="SPECTRUM">select name for device;</query>'
                '</datasource>'
                '</definition>'),
            'dbds': (
                '<definition>'
                '<datasource type="DB">'
                '<database dbtype="MYSQL">complicated DSN string</database>'
                '<query format="IMAGE">select * from device</query>'
                '<doc>test database datasource</doc>'
                '</datasource>'
                '</definition>'),
            'slt1vgap': (
                '<definition>'
                '<datasource type="CLIENT" name="slt1vgap">'
                '<record name="p02/slt/exp.07"/>'
                '</datasource>'
                '</definition>'
            ),
        }

        self.resdss = {
            'nn': ("nn", "TANGO", ""),
            'nn2': ("", "TANGO", ""),
            'ann': ("ann", "TANGO", ""),
            'ann2': ("ann2", "CLIENT", ""),
            'ann3': ("ann3", "DB", ""),
            'ann4': ("ann4", "PYEVAL", ""),
            'ann5': ("ann5", "NEW", ""),
            'tann0': ("tann0", "TANGO", "sf:12345/dsff/myattr"),
            'tann1': ("tann1", "TANGO", "sfa:10000/dsf/myattr2"),
            'tann1b': ("tann1b", "TANGO", "dsf/myattr2"),
            'tann1c': ("tann1c", "TANGO", "dsf/sd/we/myattr2"),
            'P1M_postrun': ('P1M_postrun', "PYEVAL", ""),
            'dbtest': ('dbtest', "DB", ""),
            'dbds': ('dbds', "DB", ""),
            'slt1vgap': ('slt1vgap', "CLIENT", "p02/slt/exp.07"),
        }

    # test starter
    # \brief Common set up
    def setUp(self):
        print "SEED =", self._seed
        self._wr.setUp()
        self._ms.setUp()
        self._cf.setUp()
        self._pool.setUp()
#        self._ms2.setUp()
        self._simps.setUp()
#        self._simps2.setUp()
#        self._simps3.setUp()
#        self._simps4.setUp()
#        self._simpsoff.add()
        print "\nsetting up..."

    # test closer
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
        self._cf.tearDown()
        self._ms.tearDown()
        self._wr.tearDown()

    def checkDS(self, rv, cv):
        self.assertEqual(sorted(rv.keys()), sorted(cv))
        for vl in cv:
            self.assertEqual(self.resdss[vl][0], rv[vl].name)
            self.assertEqual(self.resdss[vl][1], rv[vl].dstype)
            self.assertEqual(self.resdss[vl][2], rv[vl].record)

    def checkDSList(self, rv, cv):
        self.assertEqual(len(rv), len(cv))

        mset = set()
        for jr in rv:
            rr = json.loads(jr)
            vl = rr["dsname"]
            mset.add(vl)
            if not vl:
                vl = 'nn2'
            self.assertEqual(self.resdss[vl][0], rr["dsname"])
            self.assertEqual(self.resdss[vl][1], rr["dstype"])
            self.assertEqual(self.resdss[vl][2], rr["record"])
        self.assertEqual(len(rv), len(mset))

    def hasds(self, dslist, strategy, dstype):
        for dss in dslist:
            for ds in dss:
                dsfound = True if dstype is None else False
                stfound = True if strategy is None else False
                if dsfound and stfound:
                    break
                if not dsfound and ds[1] == dstype:
                    dsfound = True
                if not stfound and ds[0] == strategy:
                    stfound = True
#        print "FOUND", dslist, dsfound and stfound
        return dsfound and stfound

    @classmethod
    def dsfilter(cls, dss, strategy, dstype):
        res = []
        for ds in dss:
            dsfound = True if dstype is None else False
            stfound = True if strategy is None else False
            if not dsfound and ds[1] == dstype:
                dsfound = True
            if not stfound and ds[0] == strategy:
                stfound = True
            if dsfound and stfound:
                res.append(list(ds))
        return res

    def checkCP(self, rv, cv, strategy=None, dstype=None):
        self.assertEqual(sorted(set(rv[0].keys())), sorted(cv))
        for i in range(1):
            for cp, vl in rv[i].items():
                cres = self.rescps[cp]
                cresk = [ds for ds in cres.keys()
                         if self.dsfilter(cres[ds], strategy, dstype)]

                self.assertEqual(sorted(vl.keys()), sorted(cresk))
                for ds in cresk:
                    self.assertEqual(
                        sorted(self.dsfilter(cres[ds], strategy, dstype)),
                        sorted(vl[ds]))

    def dump(self, el, name="default"):
        self._dump[name] = {}

        for key in self.names(el):
            self._dump[name][key] = self.value(el, key)

    def compareToDump(self, el, excluded=None, name="default"):
        exc = set(excluded or [])
        dks = set(self._dump[name].keys()) - exc
        eks = set(self.names(el)) - exc
#        print "SE4", el["TimeZone"]
        self.assertEqual(dks, eks)
        for key in dks:
#            print " K:", key,
            if self._dump[name][key] != self.value(el, key):
                print "COMP", key
            self.assertEqual(self._dump[name][key], self.value(el, key))

    def getDump(self, key, name="default"):
        return self._dump[name][key]

    def value(self, rs, name):
        return rs.value(name)

    def names(self, rs):
        return rs.names()

    def setProp(self, rc, name, value):
        setattr(rc, name, value)

    def compareToDumpJSON(self, el, excluded=None, name="default"):
        exc = set(excluded or [])
        dks = set(self._dump[name].keys()) - exc
        eks = set(self.names(el)) - exc
        self.assertEqual(dks, eks)
        for key in dks:
#            print " K:", key,
            try:
                w1 = json.loads(self._dump[name][key])
                w2 = json.loads(self.value(el, key))
            except:
                self.assertEqual(self._dump[name][key], self.value(el, key))
            else:
                if isinstance(w1, dict):
                    self.myAssertDict(w1, w2)
                else:
                    if self._dump[name][key] != self.value(el, key):
                        print "COMP", key
                    self.assertEqual(
                        self._dump[name][key],
                        self.value(el, key))

    def compareToDumpJSONSets(self, el, sets, name="default"):
        exc = set(sets or [])
        for key in exc:
            try:
                w1 = json.loads(self._dump[name][key])
                w2 = json.loads(self.value(el, key))
            except:
                self.assertEqual(self._dump[name][key], self.value(el, key))
            else:
                if isinstance(w1, dict):
                    self.myAssertDict(w1, w2)
                else:
                    if set(self._dump[name][key]) != set(self.value(el, key)):
                        print "COMP", key
                    self.assertEqual(
                        set(self._dump[name][key]),
                        set(self.value(el, key)))

    def getRandomName(self, maxsize):
        letters = string.lowercase + string.uppercase + string.digits
        size = self._rnd.randint(1, maxsize)
        return ''.join(self._rnd.choice(letters) for _ in range(size))

    @classmethod
    def findElement(cls, cp, ds, vds, rv):
        found = False
        for el in rv:
            if el["cpname"] == cp and el["dsname"] == ds \
                    and el["strategy"] == vds[0] \
                    and el["dstype"] == vds[1] \
                    and el["record"] == vds[2] \
                    and el["nxtype"] == vds[3] \
                    and el["shape"] == vds[4]:
                found = True
                break
        if not found:
            print "NOT FOUND", cp, ds, vds, rv
        return found

    def checkICP(self, rv, cv, strategy=None, dstype=None):
        dscnt = 0
        tcv = [k for k in cv if self.rescps[k]]
        for cp in tcv:
            for ds, dss in self.rescps[cp].items():
                for vds in dss:
                    if strategy is not None:
                        if vds[0] != strategy:
                            continue
                    if dstype is not None:
                        if vds[1] != dstype:
                            continue
                    self.assertTrue(self.findElement(cp, ds, vds, rv))
                    dscnt += 1
        self.assertEqual(dscnt, len(rv))

    # test starter
    # \brief Common set up of Tango Server
    def mySetUp(self):
        pass

    # test closer
    # \brief Common tear down oif Tango Server
    def myTearDown(self):
        pass

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

    def myCompDict(self, dct, dct2):
        logger.debug('dict %s' % type(dct))
        logger.debug("\n%s\n%s" % (dct, dct2))
        if not isinstance(dct, dict):
            raise Exception("DCT1 %s" % dct)
        if not isinstance(dct2, dict):
            print "NOT DICT", type(dct2), dct2
            print "DICT", type(dct), dct
            raise Exception("DCT2 %s" % dct2)
        logger.debug("%s %s" % (len(dct.keys()), len(dct2.keys())))
        if set(dct.keys()) ^ set(dct2.keys()):
            print 'DCT', dct.keys()
            print 'DCT2', dct2.keys()
            print "DIFF", set(dct.keys()) ^ set(dct2.keys())
        if len(dct.keys()) != len(dct2.keys()):
            raise Exception("LEN %s %s" % (dct, dct2))

        for k, v in dct.items():
            logger.debug("%s  in %s" % (str(k), str(dct2.keys())))
            if k not in dct2.keys():
                raise Exception("%s not in %s" % (k, dct2))
            if isinstance(v, dict):
                self.myCompDict(v, dct2[k])
            else:
                logger.debug("%s , %s" % (str(v), str(dct2[k])))
                if v != dct2[k]:
                    print 'VALUES', k, v, dct2[k]
                    raise Exception("VALUE %s %s %s" % (k, v, dct2[k]))

    def myAssertDictJSON(self, dct, dct2):
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
                self.myAssertDictJSON(v, dct2[k])
            if isinstance(v, list):
                self.assertEqual(set(v), set(dct2[k]))
            else:
                logger.debug("%s , %s" % (str(v), str(dct2[k])))
                if v != dct2[k]:
                    print 'VALUES', k, v, dct2[k]
                self.assertEqual(v, dct2[k])

    def openRecSelector(self):
        return Settings()

    def openRecSelector2(self):
        return Settings()

    def subtest_constructor(self):
        # properties

        db = PyTango.Database()
        msp = MacroServerPools(10)

        icf = TangoUtils.getDeviceName(db, "NXSConfigServer")
        idoor = TangoUtils.getDeviceName(db, "Door")
        msp.getPools(idoor)

        rs = self.openRecSelector()

        se = Selector(msp, self.version)
        pm = ProfileManager(se)
        amgs = pm.availableMntGrps()
        # print "AMGs", amgs
        amntgrp = MSUtils.getEnv('ActiveMntGrp', msp.getMacroServer(idoor))
        # print "ActiveMntGrp", amntgrp
        self.assertEqual(rs.numberOfThreads, 20)
        self.assertEqual(rs.timerFilters,
                         ["*dgg*", "*/timer/*", "*/ctctrl0*"])
        # memorize attirbutes
        self.assertEqual(
            rs.deviceGroups,
            '{"timer": ["*exp_t*"], "dac": ["*exp_dac*"], '
            '"counter": ["*exp_c*"], "mca": ["*exp_mca*"], '
            '"adc": ["*exp_adc*"], "motor": ["*exp_mot*"]}')
        self.assertEqual(rs.adminDataNames, [])
        self.assertEqual(rs.profileFile, '/tmp/nxsrecconfig.cfg')
        self.assertEqual(rs.configDevice, icf)
        self.assertEqual(rs.door, idoor)
        cf = PyTango.DeviceProxy(rs.configDevice)
        self.assertEqual(
            cf.availableSelections(),
            rs.availableProfiles())
        # print "AMGs", pm.availableMntGrps()
        # print "AvSels", cf.availableSelections()
        if amntgrp in pm.availableMntGrps():
            self.assertEqual(rs.mntGrp, amntgrp)
        elif cf.availableSelections():
            self.assertEqual(rs.mntGrp, cf.availableSelections()[0])
        elif amgs:
            self.assertEqual('', amntgrp)
        else:
            self.assertEqual('nxsmntgrp', amntgrp)
        self.assertEqual(set(self.names(rs)),
                         set([k[0] for k in self._keys]))

        for nm in self.names(rs):
            if nm not in ["Timer",
                          "DataSourceSelection",
                          "PreselectingDataSources"]:
                if self.value(rs, nm) != se[nm]:
                    print ("DICT NAME %s" % nm)
                self.assertEqual(self.value(rs, nm), se[nm])
        self.assertEqual(self.value(rs, "UNKNOWN_VARIABLE_34535"), '')

        print "MntGrp", rs.mntGrp
        # memorize attirbutes
        print "ConfigDevice", rs.configDevice
        print "Door", rs.door
        print "DeviceGroups", rs.deviceGroups
        print "AdminDataNames", rs.adminDataNames

    def generateProfile(self, door, mg, cfdv, wrdv):
        msp = MacroServerPools(10)
        se = Selector(msp, "3.0.0")
        se["Door"] = door
        se["ConfigDevice"] = cfdv
        se["WriterDevice"] = wrdv
        se["MntGrp"] = mg
        msp.updateMacroServer(self._ms.door.keys()[0])
        wrong = []

        cps = {}
        lcp = self._rnd.randint(1, 10)
        for _ in range(lcp):
            cps[self.getRandomName(10)] = self.getRandomName(
                self._rnd.randint(1, 10))
        se["UserData"] = str(json.dumps(cps))

        cps = {}
        lcp = self._rnd.randint(1, 10)
        for _ in range(lcp):
            cps[self.getRandomName(10)] = self.getRandomName(
                self._rnd.randint(1, 10))
        se["ConfigVariables"] = str(json.dumps(cps))
        se["DefaultDynamicPath"] = self.getRandomName(10)
        se["TimeZone"] = self.getRandomName(10)
        se["AppendEntry"] = bool(self._rnd.randint(0, 1))
        se["DynamicComponents"] = bool(self._rnd.randint(0, 1))
        se["DefaultDynamicLinks"] = bool(self._rnd.randint(0, 1))
        se["ComponentsFromMntGrp"] = bool(self._rnd.randint(0, 1))
        scalar_ctrl = 'ttestp09/testts/t1r228'
        spectrum_ctrl = 'ttestp09/testts/t2r228'
        image_ctrl = 'ttestp09/testts/t3r228'
        ctrls = [scalar_ctrl, spectrum_ctrl, image_ctrl,
                 "__tango__"]
        expch = []
        pdss = []
        mgt = ProfileManager(se)

        pool = self._pool.dp
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
        se["Timer"] = json.dumps(ltimers)

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
                elif ds.startswith("image"):
                    exp["controller"] = image_ctrl
                elif ds.startswith("spectrum"):
                    exp["controller"] = spectrum_ctrl
                else:
                    exp["controller"] = scalar_ctrl
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
        indss = [ds for ds in self._rnd.sample(
            set(amydss.keys()), nadss)]

        aindss = {}
        for cp in indss:
            if cp not in wrong:
                aindss[cp] = bool(self._rnd.randint(0, 1))

        nadss = self._rnd.randint(1, len(amydss.keys()) - 1)
        aadss = [ds for ds in self._rnd.sample(
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
        se["ComponentSelection"] = json.dumps(cps)
        se["ComponentPreselection"] = json.dumps(
            acps)
        se["DataSourceSelection"] = json.dumps(dss)
        se["PreselectingDataSources"] = \
            json.dumps(aadss)
        se["OptionalComponents"] = json.dumps(ocps)
        se["DataSourcePreselection"] = json.dumps(aindss)
        se["AppendEntry"] = bool(self._rnd.randint(0, 1))
        se["ComponentsFromMntGrp"] = bool(
            self._rnd.randint(0, 1))
        se["DynamicComponents"] = bool(
            self._rnd.randint(0, 1))
        se["DefaultDynamicLinks"] = \
            bool(self._rnd.randint(0, 1))
        se["DefaultDynamicPath"] = self.getRandomName(20)
        se["TimeZone"] = self.getRandomName(20)

        se["ConfigVariables"] = json.dumps(dict(
            (self.getRandomName(10),
             self.getRandomName(15)) for _ in
            range(self._rnd.randint(1, 40))))
        se["ChannelProperties"] = self.generateChannelProperties()
        self._cf.dp.SetCommandVariable(["MCPLIST",
                                        json.dumps(mcps)])

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

        se["Timer"] = json.dumps(ltimers)
        se["UserData"] = json.dumps(records)

        tmg = TestMGSetUp.TestMeasurementGroupSetUp(
            name=mg)
#                    dv = "/".join(ar["full_name"].split("/")[0:-1])
        chds = [ds for ds in mgt.dataSources()
                if not ds.startswith('client')]
        chds1 = list(chds)
        chds2 = [ds for ds in mgt.componentDataSources()
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

        se["UnplottedComponents"] = json.dumps(lhe)
        se["OrderedChannels"] = json.dumps(pdss)

        se.preselect()
        return str(json.dumps(se.get()))

    def generateChannelProperties(self):
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

        return json.dumps(
            {
                "label": labels,
                "nexus_path": paths,
                "link": links,
                "data_type": types,
                "shape": shapes
            }
        )


if __name__ == '__main__':
    unittest.main()
