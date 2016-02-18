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
## \file SettingsTest.py
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

## if 64-bit machione
IS64BIT = (struct.calcsize("P") == 8)

## list of available databases
DB_AVAILABLE = []

try:
    import MySQLdb
    ## connection arguments to MYSQL DB
    mydb = MySQLdb.connect({})
    mydb.close()
    DB_AVAILABLE.append("MYSQL")
except:
    try:
        import MySQLdb
    ## connection arguments to MYSQL DB
        args = {'host': 'localhost', 'db': 'nxsconfig',
                'read_default_file': '/etc/my.cnf', 'use_unicode': True}
    ## inscance of MySQLdb
        mydb = MySQLdb.connect(**args)
        mydb.close()
        DB_AVAILABLE.append("MYSQL")
    except:
        try:
            import MySQLdb
            from os.path import expanduser
            home = expanduser("~")
        ## connection arguments to MYSQL DB
            args2 = {'host': 'localhost', 'db': 'nxsconfig',
                     'read_default_file': '%s/.my.cnf' % home,
                     'use_unicode': True}
        ## inscance of MySQLdb
            mydb = MySQLdb.connect(**args2)
            mydb.close()
            DB_AVAILABLE.append("MYSQL")

        except ImportError, e:
            print "MYSQL not available: %s" % e
        except Exception, e:
            print "MYSQL not available: %s" % e
        except:
            print "MYSQL not available"


## test fixture
class SettingsTest(unittest.TestCase):

    ## constructor
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
            self.__seed = long(binascii.hexlify(os.urandom(16)), 16)
        except NotImplementedError:
            self.__seed = long(time.time() * 256)

        self.__rnd = random.Random(self.__seed)

        self.__dump = {}

        ## default zone
        self.__defaultzone = 'Europe/Berlin'
        ## default mntgrp
        self.__defaultmntgrp = 'nxsmntgrp'
        ## default path
        self.__defaultpath = \
            '/entry$var.serialno:NXentry/NXinstrument/collection'

        self.__npTn = {"float32": "NX_FLOAT32", "float64": "NX_FLOAT64",
                       "float": "NX_FLOAT32", "double": "NX_FLOAT64",
                       "int": "NX_INT", "int64": "NX_INT64",
                       "int32": "NX_INT32", "int16": "NX_INT16",
                       "int8": "NX_INT8", "uint64": "NX_UINT64",
                       "uint32": "NX_UINT32", "uint16": "NX_UINT16",
                       "uint8": "NX_UINT8", "uint": "NX_UINT64",
                       "string": "NX_CHAR", "bool": "NX_BOOLEAN"}
        self.__npTn2 = {"float32": "NX_FLOAT32", "float64": "NX_FLOAT64",
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

        ## selection version
        self.version = nxsrecconfig.__version__

        self._keys = [
            ("Timer", '[]'),
            ("OrderedChannels", '[]'),
            ("ComponentSelection", '{}'),
            ("ComponentPreselection", '{}'),
            ("PreselectedDataSources", '[]'),
            ("DataSourceSelection", '{}'),
            ("InitDataSources", '[]'),
            ("OptionalComponents", '[]'),
            ("AppendEntry", False),
            ("ComponentsFromMntGrp", False),
            ("ConfigVariables", '{}'),
            ("UserData", '{}'),
            ("UnplottedComponents", '[]'),
            ("ChannelProperties", '{}'),
            ("DynamicComponents", True),
            ("DefaultDynamicLinks", True),
            ("DefaultDynamicPath", self.__defaultpath),
            ("TimeZone", self.__defaultzone),
            ("ConfigDevice", ''),
            ("WriterDevice", ''),
            ("Door", ''),
            ("MntGrp", ''),
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
                '<dim index="1" value="$datasource.ann">'
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
                '<dim index="1">$datasource.ann2<strategy mode="CONFIG" />'
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
                '<dim index="1" value="$datasource.ann" />'
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
                     ['$datasource.ann'])]},
            'dim3': {
                'tann1c': [
                    ('INIT', 'TANGO', 'dsf/sd/we/myattr2', 'NX_INT8',
                     [1234])]},
            'dim4': {
                'tann1c': [
                    ('INIT', 'TANGO', 'dsf/sd/we/myattr2', 'NX_INT8',
                     ['$datasource.ann2'])]},
            'dim5': {
                'tann1c': [
                    ('INIT', 'TANGO', 'dsf/sd/we/myattr2', 'NX_INT8',
                     ['$datasource.ann'])],
                'ann': [('CONFIG', 'TANGO', '', None, None)],
            },
            'dim6': {'tann1c': [
                ('INIT', 'TANGO', 'dsf/sd/we/myattr2', 'NX_INT8',
                 ['$datasource.ann', 123])]},
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
                'data_units': 'No unit',
                'shape': [],
                'plot_axes': ['<mov>'],
                'source': 'ttestp09/testts/t1r228/ScalarLong'},
            'scalar_bool': {
                'data_type': 'bool',
                'plot_type': 1,
                'data_units': 'No unit',
                'shape': [],
                'plot_axes': ['<mov>'],
                'source': 'ttestp09/testts/t1r228/ScalarBoolean'},
            'scalar_short': {
                'data_type': 'int16',
                'plot_type': 1,
                'data_units': 'No unit',
                'shape': [],
                'plot_axes': ['<mov>'],
                'source': 'ttestp09/testts/t1r228/ScalarShort'},
            'scalar_ushort': {
                'data_type': 'uint16',
                'plot_type': 1,
                'data_units': 'No unit',
                'shape': [],
                'plot_axes': ['<mov>'],
                'source': 'ttestp09/testts/t1r228/ScalarUShort'},
            'scalar_ulong': {
                'data_type': 'uint32',
                'plot_type': 1,
                'data_units': 'No unit',
                'shape': [],
                'plot_axes': ['<mov>'],
                'source': 'ttestp09/testts/t1r228/ScalarULong'},
            'scalar_long64': {
                'data_type': 'int64',
                'plot_type': 1,
                'data_units': 'No unit',
                'shape': [],
                'plot_axes': ['<mov>'],
                'source': 'ttestp09/testts/t1r228/ScalarLong64'},
            'scalar_ulong64': {
                'data_type': 'uint64',
                'plot_type': 1,
                'data_units': 'No unit',
                'shape': [],
                'plot_axes': ['<mov>'],
                'source': 'ttestp09/testts/t1r228/ScalarULong64'},
            'scalar_float': {
                'data_type': 'float32',
                'plot_type': 1,
                'data_units': 'No unit',
                'shape': [],
                'plot_axes': ['<mov>'],
                'source': 'ttestp09/testts/t1r228/ScalarFloat'},
            'scalar_double': {
                'data_type': 'float64',
                'plot_type': 1,
                'data_units': 'No unit',
                'shape': [],
                'plot_axes': ['<mov>'],
                'source': 'ttestp09/testts/t1r228/ScalarDouble'},
            'scalar_string': {
                'data_type': 'string',
                'plot_type': 1,
                'data_units': 'No unit',
                'shape': [],
                'plot_axes': ['<mov>'],
                'source': 'ttestp09/testts/t1r228/ScalarString'},
            'scalar_encoded': {
                'data_type': 'encoded',
                'plot_type': 1,
                'data_units': 'No unit',
                'shape': [],
                'plot_axes': ['<mov>'],
                'source': 'ttestp09/testts/t1r228/ScalarEncoded'},
            'scalar_uchar': {
                'data_type': 'uint8',
                'plot_type': 1,
                'data_units': 'No unit',
                'shape': [],
                'plot_axes': ['<mov>'],
                'source': 'ttestp09/testts/t1r228/ScalarUChar'},
            'spectrum_long': {
                'data_type': 'int32',
                'plot_type': 1,
                'data_units': 'No unit',
                'shape': [4],
                'plot_axes': ['<idx>'],
                'source': 'ttestp09/testts/t1r228/SpectrumLong'},
            'spectrum_bool': {
                'data_type': 'bool',
                'plot_type': 1,
                'data_units': 'No unit',
                'shape': [2],
                'plot_axes': ['<idx>'],
                'source': 'ttestp09/testts/t1r228/SpectrumBoolean'},
            'spectrum_short': {
                'data_type': 'int16',
                'plot_type': 1,
                'data_units': 'No unit',
                'shape': [3],
                'plot_axes': ['<idx>'],
                'source': 'ttestp09/testts/t1r228/SpectrumShort'},
            'spectrum_ushort': {
                'data_type': 'uint16',
                'plot_type': 1,
                'data_units': 'No unit',
                'shape': [4],
                'plot_axes': ['<idx>'],
                'source': 'ttestp09/testts/t1r228/SpectrumUShort'},
            'spectrum_ulong': {
                'data_type': 'uint32',
                'plot_type': 1,
                'data_units': 'No unit',
                'shape': [4],
                'plot_axes': ['<idx>'],
                'source': 'ttestp09/testts/t1r228/SpectrumULong'},
            'spectrum_long64': {
                'data_type': 'int64',
                'plot_type': 1,
                'data_units': 'No unit',
                'shape': [4],
                'plot_axes': ['<idx>'],
                'source': 'ttestp09/testts/t1r228/SpectrumLong64'},
            'spectrum_ulong64': {
                'data_type': 'uint64',
                'plot_type': 1,
                'data_units': 'No unit',
                'shape': [4],
                'plot_axes': ['<idx>'],
                'source': 'ttestp09/testts/t1r228/SpectrumULong64'},
            'spectrum_float': {
                'data_type': 'float32',
                'plot_type': 1,
                'data_units': 'No unit',
                'shape': [4],
                'plot_axes': ['<idx>'],
                'source': 'ttestp09/testts/t1r228/SpectrumFloat'},
            'spectrum_double': {
                'data_type': 'float64',
                'plot_type': 1,
                'data_units': 'No unit',
                'shape': [4],
                'plot_axes': ['<idx>'],
                'source': 'ttestp09/testts/t1r228/SpectrumDouble'},
            'spectrum_string': {
                'data_type': 'string',
                'plot_type': 1,
                'data_units': 'No unit',
                'shape': [4],
                'plot_axes': ['<idx>'],
                'source': 'ttestp09/testts/t1r228/SpectrumString'},
            'spectrum_encoded': {
                'data_type': 'encoded',
                'plot_type': 1,
                'data_units': 'No unit',
                'shape': [],
                'plot_axes': ['<mov>'],
                'source': 'ttestp09/testts/t1r228/SpectrumEncoded'},
            'spectrum_uchar': {
                'data_type': 'uint8',
                'plot_type': 1,
                'data_units': 'No unit',
                'shape': [2],
                'plot_axes': ['<idx>'],
                'source': 'ttestp09/testts/t1r228/SpectrumUChar'},

            'image_long': {
                'data_type': 'int32',
                'plot_type': 2,
                'data_units': 'No unit',
                'shape': [2, 2],
                'plot_axes': ['<idx>', '<idx>'],
                'source': 'ttestp09/testts/t1r228/ImageLong'},
            'image_bool': {
                'data_type': 'bool',
                'plot_type': 2,
                'data_units': 'No unit',
                'shape': [1, 1],
                'plot_axes': ['<idx>', '<idx>'],
                'source': 'ttestp09/testts/t1r228/ImageBoolean'},
            'image_short': {
                'data_type': 'int16',
                'plot_type': 2,
                'data_units': 'No unit',
                'shape': [2, 2],
                'plot_axes': ['<idx>', '<idx>'],
                'source': 'ttestp09/testts/t1r228/ImageShort'},
            'image_ushort': {
                'data_type': 'uint16',
                'plot_type': 2,
                'data_units': 'No unit',
                'shape': [2, 2],
                'plot_axes': ['<idx>', '<idx>'],
                'source': 'ttestp09/testts/t1r228/ImageUShort'},
            'image_ulong': {
                'data_type': 'uint32',
                'plot_type': 2,
                'data_units': 'No unit',
                'shape': [2, 2],
                'plot_axes': ['<idx>', '<idx>'],
                'source': 'ttestp09/testts/t1r228/ImageULong'},
            'image_long64': {
                'data_type': 'int64',
                'plot_type': 2,
                'data_units': 'No unit',
                'shape': [2, 2],
                'plot_axes': ['<idx>', '<idx>'],
                'source': 'ttestp09/testts/t1r228/ImageLong64'},
            'image_ulong64': {
                'data_type': 'uint64',
                'plot_type': 2,
                'data_units': 'No unit',
                'shape': [2, 2],
                'plot_axes': ['<idx>', '<idx>'],
                'source': 'ttestp09/testts/t1r228/ImageULong64'},
            'image_float': {
                'data_type': 'float32',
                'plot_type': 2,
                'data_units': 'No unit',
                'shape': [2, 2],
                'plot_axes': ['<idx>', '<idx>'],
                'source': 'ttestp09/testts/t1r228/ImageFloat'},
            'image_double': {
                'data_type': 'float64',
                'plot_type': 2,
                'data_units': 'No unit',
                'shape': [2, 2],
                'plot_axes': ['<idx>', '<idx>'],
                'source': 'ttestp09/testts/t1r228/ImageDouble'},
            'image_string': {
                'data_type': 'string',
                'plot_type': 2,
                'data_units': 'No unit',
                'shape': [1, 1],
                'plot_axes': ['<idx>', '<idx>'],
                'source': 'ttestp09/testts/t1r228/ImageString'},
            'image_encoded': {
                'data_type': 'encoded',
                'plot_type': 1,
                'data_units': 'No unit',
                'shape': [],
                'plot_axes': ['<mov>'],
                'source': 'ttestp09/testts/t1r228/ImageEncoded'},
            'image_uchar': {
                'data_type': 'uint8',
                'plot_type': 2,
                'data_units': 'No unit',
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
                'data_units': 'No unit',
                'shape': [],
                'plot_axes': ['<mov>'],
                'source': 'ttestp09/testts/t01r228/ScalarLong'},
            'scalar2_bool': {
                'data_type': 'bool',
                'plot_type': 1,
                'data_units': 'No unit',
                'shape': [],
                'plot_axes': ['<mov>'],
                'source': 'ttestp09/testts/t02r228/ScalarBoolean'},
            'scalar2_short': {
                'data_type': 'int16',
                'plot_type': 1,
                'data_units': 'No unit',
                'shape': [],
                'plot_axes': ['<mov>'],
                'source': 'ttestp09/testts/t03r228/ScalarShort'},
            'scalar2_ushort': {
                'data_type': 'uint16',
                'plot_type': 1,
                'data_units': 'No unit',
                'shape': [],
                'plot_axes': ['<mov>'],
                'source': 'ttestp09/testts/t04r228/ScalarUShort'},
            'scalar2_ulong': {
                'data_type': 'uint32',
                'plot_type': 1,
                'data_units': 'No unit',
                'shape': [],
                'plot_axes': ['<mov>'],
                'source': 'ttestp09/testts/t05r228/ScalarULong'},
            'scalar2_long64': {
                'data_type': 'int64',
                'plot_type': 1,
                'data_units': 'No unit',
                'shape': [],
                'plot_axes': ['<mov>'],
                'source': 'ttestp09/testts/t06r228/ScalarLong64'},
            'scalar2_ulong64': {
                'data_type': 'uint64',
                'plot_type': 1,
                'data_units': 'No unit',
                'shape': [],
                'plot_axes': ['<mov>'],
                'source': 'ttestp09/testts/t07r228/ScalarULong64'},
            'scalar2_float': {
                'data_type': 'float32',
                'plot_type': 1,
                'data_units': 'No unit',
                'shape': [],
                'plot_axes': ['<mov>'],
                'source': 'ttestp09/testts/t08r228/ScalarFloat'},
            'scalar2_double': {
                'data_type': 'float64',
                'plot_type': 1,
                'data_units': 'No unit',
                'shape': [],
                'plot_axes': ['<mov>'],
                'source': 'ttestp09/testts/t09r228/ScalarDouble'},
            'scalar2_string': {
                'data_type': 'string',
                'plot_type': 1,
                'data_units': 'No unit',
                'shape': [],
                'plot_axes': ['<mov>'],
                'source': 'ttestp09/testts/t10r228/ScalarString'},
            'scalar2_encoded': {
                'data_type': 'encoded',
                'plot_type': 1,
                'data_units': 'No unit',
                'shape': [],
                'plot_axes': ['<mov>'],
                'source': 'ttestp09/testts/t11r228/ScalarEncoded'},
            'scalar2_uchar': {
                'data_type': 'uint8',
                'plot_type': 1,
                'data_units': 'No unit',
                'shape': [],
                'plot_axes': ['<mov>'],
                'source': 'ttestp09/testts/t12r228/ScalarUChar'},
            'spectrum2_long': {
                'data_type': 'int32',
                'plot_type': 1,
                'data_units': 'No unit',
                'shape': [4],
                'plot_axes': ['<idx>'],
                'source': 'ttestp09/testts/t13r228/SpectrumLong'},
            'spectrum2_bool': {
                'data_type': 'bool',
                'plot_type': 1,
                'data_units': 'No unit',
                'shape': [2],
                'plot_axes': ['<idx>'],
                'source': 'ttestp09/testts/t14r228/SpectrumBoolean'},
            'spectrum2_short': {
                'data_type': 'int16',
                'plot_type': 1,
                'data_units': 'No unit',
                'shape': [3],
                'plot_axes': ['<idx>'],
                'source': 'ttestp09/testts/t15r228/SpectrumShort'},
            'spectrum2_ushort': {
                'data_type': 'uint16',
                'plot_type': 1,
                'data_units': 'No unit',
                'shape': [4],
                'plot_axes': ['<idx>'],
                'source': 'ttestp09/testts/t16r228/SpectrumUShort'},
            'spectrum2_ulong': {
                'data_type': 'uint32',
                'plot_type': 1,
                'data_units': 'No unit',
                'shape': [4],
                'plot_axes': ['<idx>'],
                'source': 'ttestp09/testts/t17r228/SpectrumULong'},
            'spectrum2_long64': {
                'data_type': 'int64',
                'plot_type': 1,
                'data_units': 'No unit',
                'shape': [4],
                'plot_axes': ['<idx>'],
                'source': 'ttestp09/testts/t18r228/SpectrumLong64'},
            'spectrum2_ulong64': {
                'data_type': 'uint64',
                'plot_type': 1,
                'data_units': 'No unit',
                'shape': [4],
                'plot_axes': ['<idx>'],
                'source': 'ttestp09/testts/t19r228/SpectrumULong64'},
            'spectrum2_float': {
                'data_type': 'float32',
                'plot_type': 1,
                'data_units': 'No unit',
                'shape': [4],
                'plot_axes': ['<idx>'],
                'source': 'ttestp09/testts/t20r228/SpectrumFloat'},
            'spectrum2_double': {
                'data_type': 'float64',
                'plot_type': 1,
                'data_units': 'No unit',
                'shape': [4],
                'plot_axes': ['<idx>'],
                'source': 'ttestp09/testts/t21r228/SpectrumDouble'},
            'spectrum2_string': {
                'data_type': 'string',
                'plot_type': 1,
                'data_units': 'No unit',
                'shape': [4],
                'plot_axes': ['<idx>'],
                'source': 'ttestp09/testts/t22r228/SpectrumString'},
            'spectrum2_encoded': {
                'data_type': 'encoded',
                'plot_type': 1,
                'data_units': 'No unit',
                'shape': [],
                'plot_axes': ['<mov>'],
                'source': 'ttestp09/testts/t23r228/SpectrumEncoded'},
            'spectrum2_uchar': {
                'data_type': 'uint8',
                'plot_type': 1,
                'data_units': 'No unit',
                'shape': [2],
                'plot_axes': ['<idx>'],
                'source': 'ttestp09/testts/t24r228/SpectrumUChar'},

            'image2_long': {
                'data_type': 'int32',
                'plot_type': 2,
                'data_units': 'No unit',
                'shape': [2, 2],
                'plot_axes': ['<idx>', '<idx>'],
                'source': 'ttestp09/testts/t25r228/ImageLong'},
            'image2_bool': {
                'data_type': 'bool',
                'plot_type': 2,
                'data_units': 'No unit',
                'shape': [1, 1],
                'plot_axes': ['<idx>', '<idx>'],
                'source': 'ttestp09/testts/t26r228/ImageBoolean'},
            'image2_short': {
                'data_type': 'int16',
                'plot_type': 2,
                'data_units': 'No unit',
                'shape': [2, 2],
                'plot_axes': ['<idx>', '<idx>'],
                'source': 'ttestp09/testts/t27r228/ImageShort'},
            'image2_ushort': {
                'data_type': 'uint16',
                'plot_type': 2,
                'data_units': 'No unit',
                'shape': [2, 2],
                'plot_axes': ['<idx>', '<idx>'],
                'source': 'ttestp09/testts/t28r228/ImageUShort'},
            'image2_ulong': {
                'data_type': 'uint32',
                'plot_type': 2,
                'data_units': 'No unit',
                'shape': [2, 2],
                'plot_axes': ['<idx>', '<idx>'],
                'source': 'ttestp09/testts/t29r228/ImageULong'},
            'image2_long64': {
                'data_type': 'int64',
                'plot_type': 2,
                'data_units': 'No unit',
                'shape': [2, 2],
                'plot_axes': ['<idx>', '<idx>'],
                'source': 'ttestp09/testts/t30r228/ImageLong64'},
            'image2_ulong64': {
                'data_type': 'uint64',
                'plot_type': 2,
                'data_units': 'No unit',
                'shape': [2, 2],
                'plot_axes': ['<idx>', '<idx>'],
                'source': 'ttestp09/testts/t31r228/ImageULong64'},
            'image2_float': {
                'data_type': 'float32',
                'plot_type': 2,
                'data_units': 'No unit',
                'shape': [2, 2],
                'plot_axes': ['<idx>', '<idx>'],
                'source': 'ttestp09/testts/t32r228/ImageFloat'},
            'image2_double': {
                'data_type': 'float64',
                'plot_type': 2,
                'data_units': 'No unit',
                'shape': [2, 2],
                'plot_axes': ['<idx>', '<idx>'],
                'source': 'ttestp09/testts/t33r228/ImageDouble'},
            'image2_string': {
                'data_type': 'string',
                'plot_type': 2,
                'data_units': 'No unit',
                'shape': [1, 1],
                'plot_axes': ['<idx>', '<idx>'],
                'source': 'ttestp09/testts/t34r228/ImageString'},
            'image2_encoded': {
                'data_type': 'encoded',
                'plot_type': 1,
                'data_units': 'No unit',
                'shape': [],
                'plot_axes': ['<mov>'],
                'source': 'ttestp09/testts/t35r228/ImageEncoded'},
            'image2_uchar': {
                'data_type': 'uint8',
                'plot_type': 2,
                'data_units': 'No unit',
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

    ## test starter
    # \brief Common set up
    def setUp(self):
        print "SEED =", self.__seed
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
        self.__dump[name] = {}

        for key in self.names(el):
            self.__dump[name][key] = self.value(el, key)

    def compareToDump(self, el, excluded=None, name="default"):
        exc = set(excluded or [])
        dks = set(self.__dump[name].keys()) - exc
        eks = set(self.names(el)) - exc
#        print "SE4", el["TimeZone"]
        self.assertEqual(dks, eks)
        for key in dks:
            print " K:", key,
            if self.__dump[name][key] != self.value(el, key):
                print "COMP", key
            self.assertEqual(self.__dump[name][key], self.value(el, key))

    def getDump(self, key, name="default"):
        return self.__dump[name][key]

    def value(self, rs, name):
        return rs.value(name)

    def names(self, rs):
        return rs.names()

    def setProp(self, rc, name, value):
        setattr(rc, name, value)

    def compareToDumpJSON(self, el, excluded=None, name="default"):
        exc = set(excluded or [])
        dks = set(self.__dump[name].keys()) - exc
        eks = set(self.names(el)) - exc
        self.assertEqual(dks, eks)
        for key in dks:
            print " K:", key,
            try:
                w1 = json.loads(self.__dump[name][key])
                w2 = json.loads(self.value(el, key))
            except:
                self.assertEqual(self.__dump[name][key], self.value(el, key))
            else:
                if isinstance(w1, dict):
                    self.myAssertDict(w1, w2)
                else:
                    if self.__dump[name][key] != self.value(el, key):
                        print "COMP", key
                    self.assertEqual(
                        self.__dump[name][key],
                        self.value(el, key))

    def compareToDumpJSONSets(self, el, sets, name="default"):
        exc = set(sets or [])
        for key in exc:
            try:
                w1 = json.loads(self.__dump[name][key])
                w2 = json.loads(self.value(el, key))
            except:
                self.assertEqual(self.__dump[name][key], self.value(el, key))
            else:
                if isinstance(w1, dict):
                    self.myAssertDict(w1, w2)
                else:
                    if set(self.__dump[name][key]) != set(self.value(el, key)):
                        print "COMP", key
                    self.assertEqual(
                        set(self.__dump[name][key]),
                        set(self.value(el, key)))

    def getRandomName(self, maxsize):
        letters = string.lowercase + string.uppercase + string.digits
        size = self.__rnd.randint(1, maxsize)
        return ''.join(self.__rnd.choice(letters) for _ in range(size))

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

    ## test starter
    # \brief Common set up of Tango Server
    def mySetUp(self):
        pass

    ## test closer
    # \brief Common tear down oif Tango Server
    def myTearDown(self):
        pass

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
        print "AMGs", amgs
        amntgrp = MSUtils.getEnv('ActiveMntGrp', msp.getMacroServer(idoor))
        print "ActiveMntGrp", amntgrp
        self.assertEqual(rs.numberOfThreads, 20)
        self.assertEqual(rs.timerFilters, ["*dgg*", "*/ctctrl0*"])
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
        print "AMGs", pm.availableMntGrps()
        print "AvSels", cf.availableSelections()
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
                          "PreselectedDataSources"]:
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

    ## test
    def test_constructor(self):
        fun = sys._getframe().f_code.co_name
        print "Run: %s.%s() " % (self.__class__.__name__, fun)
        val = {"ConfigDevice": self._cf.dp.name(),
               "WriterDevice": self._wr.dp.name(),
               "Door": 'doortestp09/testts/t1r228',
               "MntGrp": 'nxsmntgrp'}

        self.subtest_constructor()

    ## test
    def test_constructor_configDevice_door(self):
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
        self.assertEqual(rs.configDevice, val["ConfigDevice"])
        self.assertEqual(rs.door, val["Door"])
        self.assertEqual(rs.mntGrp, val["MntGrp"])

    ## test
    def test_mandatory_components(self):
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
#        msp = MacroServerPools(10)

#        self.assertEqual(msp.getMacroServer(), self._ms.ms.keys()[0])

        self.assertEqual(set(rs.mandatoryComponents()), set())
        mncps = self.__rnd.randint(1, len(self.mycps.keys()) - 1)
        mcps = [cp for cp in self.__rnd.sample(
                set(self.mycps.keys()), mncps) if cp not in wrong]

        self._cf.dp.SetCommandVariable(["MCPLIST", json.dumps(mcps)])
        self.assertEqual(set(rs.mandatoryComponents()), set(mcps))

    ## test
    def test_mandatory_components(self):
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
#        msp = MacroServerPools(10)

#        self.assertEqual(msp.getMacroServer(), self._ms.ms.keys()[0])

        self.assertEqual(set(rs.mandatoryComponents()), set())
        mncps = self.__rnd.randint(1, len(self.mycps.keys()) - 1)
        mcps = [cp for cp in self.__rnd.sample(
                set(self.mycps.keys()), mncps) if cp not in wrong]

        self._cf.dp.SetCommandVariable(["MCPLIST", json.dumps(mcps)])
        self.assertEqual(set(rs.mandatoryComponents()), set(mcps))

    ## available components and datasources
    def test_available_components_datasources(self):
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
        self.assertEqual(set(rs.availableComponents()), set())
        self.assertEqual(set(rs.availableDataSources()), set())

        self._cf.dp.SetCommandVariable(["CPDICT", json.dumps(self.mycps)])
        self._cf.dp.SetCommandVariable(["DSDICT", json.dumps(self.mydss)])
#        msp = MacroServerPools(10)

#        self.assertEqual(msp.getMacroServer(), self._ms.ms.keys()[0])

        self.assertEqual(set(rs.availableComponents()), set(self.mycps.keys()))
        self.assertEqual(set(rs.availableDataSources()),
                         set(self.mydss.keys()))

    def test_available_selections(self):
        fun = sys._getframe().f_code.co_name
        print "Run: %s.%s() " % (self.__class__.__name__, fun)
        val = {"ConfigDevice": self._cf.dp.name(),
               "WriterDevice": self._wr.dp.name(),
               "Door": 'doortestp09/testts/t1r228',
               "MntGrp": 'nxsmntgrp'}

        wrong = []

        db = PyTango.Database()
        db.put_device_property(self._ms.ms.keys()[0],
                               {'PoolNames': self._pool.dp.name()})
        self._ms.dps[self._ms.ms.keys()[0]].Init()
        rs = self.openRecSelector()
        rs.configDevice = val["ConfigDevice"]
        rs.door = val["Door"]
        rs.mntGrp = val["MntGrp"]

        self.assertEqual(rs.configDevice, val["ConfigDevice"])
        self.assertEqual(rs.door, val["Door"])
        self.assertEqual(rs.mntGrp, val["MntGrp"])
        self.assertEqual(set(rs.availableComponents()), set())
        self.assertEqual(set(rs.availableDataSources()), set())
        try:
            self.assertEqual(set(rs.availableProfiles()), set())
        except:
            self.assertEqual(set(rs.availableProfiles()),
                             set([val["MntGrp"]]))

        self._cf.dp.SetCommandVariable(["SELDICT",
                                        json.dumps(self.mysel2)])

        self.assertEqual(set(rs.availableProfiles()),
                         set(self.mysel2.keys()))
        self.assertEqual(set(rs.availableComponents()), set())
        self.assertEqual(set(rs.availableDataSources()), set())

    ## test
    # \brief It tests default settings
    def test_poolChannels(self):
        fun = sys._getframe().f_code.co_name
        print "Run: %s.%s() " % (self.__class__.__name__, fun)
        val = {"ConfigDevice": self._cf.dp.name(),
               "WriterDevice": self._wr.dp.name(),
               "Door": 'doortestp09/testts/t1r228',
               "MntGrp": 'nxsmntgrp'}

        db = PyTango.Database()
        db.put_device_property(self._ms.ms.keys()[0],
                               {'PoolNames': self._pool.dp.name()})
        self._ms.dps[self._ms.ms.keys()[0]].Init()
        rs = self.openRecSelector()
        rs.configDevice = val["ConfigDevice"]
        rs.door = val["Door"]
        rs.mntGrp = val["MntGrp"]

        db = PyTango.Database()
        db.put_device_property(self._ms.ms.keys()[0],
                               {'PoolNames': self._pool.dp.name()})

        self._ms.dps[self._ms.ms.keys()[0]].Init()

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

        print rs.poolElementNames('ExpChannelList')

    ## test
    # \brief It tests default settings
    def test_poolChannels_bl(self):
        fun = sys._getframe().f_code.co_name
        print "Run: %s.%s() " % (self.__class__.__name__, fun)
        val = {"ConfigDevice": self._cf.dp.name(),
               "WriterDevice": self._wr.dp.name(),
               "Door": 'doortestp09/testts/t1r228',
               "MntGrp": 'nxsmntgrp'}

        db = PyTango.Database()
        db.put_device_property(self._ms.ms.keys()[0],
                               {'PoolNames': self._pool.dp.name()})
        self._ms.dps[self._ms.ms.keys()[0]].Init()
        rs = self.openRecSelector()
        self.setProp(rs, "poolBlacklist",
                     [self._pool.dp.name()])
        rs.configDevice = val["ConfigDevice"]
        rs.door = val["Door"]
        rs.mntGrp = val["MntGrp"]

        db = PyTango.Database()
        db.put_device_property(self._ms.ms.keys()[0],
                               {'PoolNames': self._pool.dp.name()})

        self._ms.dps[self._ms.ms.keys()[0]].Init()

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

        print rs.poolElementNames('ExpChannelList')

    ## test
    # \brief It tests default settings
    def test_poolMotors(self):
        fun = sys._getframe().f_code.co_name
        print "Run: %s.%s() " % (self.__class__.__name__, fun)
        val = {"ConfigDevice": self._cf.dp.name(),
               "WriterDevice": self._wr.dp.name(),
               "Door": 'doortestp09/testts/t1r228',
               "MntGrp": 'nxsmntgrp'}

        db = PyTango.Database()
        db.put_device_property(self._ms.ms.keys()[0],
                               {'PoolNames': self._pool.dp.name()})
        self._ms.dps[self._ms.ms.keys()[0]].Init()
        rs = self.openRecSelector()
        rs.configDevice = val["ConfigDevice"]
        rs.door = val["Door"]
        rs.mntGrp = val["MntGrp"]

        db = PyTango.Database()
        db.put_device_property(self._ms.ms.keys()[0],
                               {'PoolNames': self._pool.dp.name()})

        self._ms.dps[self._ms.ms.keys()[0]].Init()

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

        print rs.poolElementNames('MotorList')

    ## test
    # \brief It tests default settings
    def test_poolMotors_bl(self):
        fun = sys._getframe().f_code.co_name
        print "Run: %s.%s() " % (self.__class__.__name__, fun)
        val = {"ConfigDevice": self._cf.dp.name(),
               "WriterDevice": self._wr.dp.name(),
               "Door": 'doortestp09/testts/t1r228',
               "MntGrp": 'nxsmntgrp'}

        db = PyTango.Database()
        db.put_device_property(self._ms.ms.keys()[0],
                               {'PoolNames': self._pool.dp.name()})
        self._ms.dps[self._ms.ms.keys()[0]].Init()
        rs = self.openRecSelector()
        self.setProp(rs, "poolBlacklist",
                     [self._pool.dp.name()])
        rs.configDevice = val["ConfigDevice"]
        rs.door = val["Door"]
        rs.mntGrp = val["MntGrp"]

        db = PyTango.Database()
        db.put_device_property(self._ms.ms.keys()[0],
                               {'PoolNames': self._pool.dp.name()})

        self._ms.dps[self._ms.ms.keys()[0]].Init()

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

        print rs.poolElementNames('MotorList')

    ## preselectComponents test
    # \brief It tests default settings
    def test_preselectComponents_simple(self):
        fun = sys._getframe().f_code.co_name
        print "Run: %s.%s() " % (self.__class__.__name__, fun)
        val = {"ConfigDevice": self._cf.dp.name(),
               "WriterDevice": self._wr.dp.name(),
               "Door": 'doortestp09/testts/t1r228',
               "MntGrp": 'nxsmntgrp'}

        db = PyTango.Database()
        self._ms.dps[self._ms.ms.keys()[0]].Init()
        rs = self.openRecSelector()
        rs.configDevice = val["ConfigDevice"]
        rs.door = val["Door"]
        rs.mntGrp = val["MntGrp"]

        self._ms.dps[self._ms.ms.keys()[0]].Init()

        channelerrors = []
        rs.preselectComponents()
        res = self.value(rs, "ComponentPreselection")
        self.assertEqual(res, '{}')
        print self._cf.dp.GetCommandVariable("COMMANDS")

    ## preselectComponents test
    # \brief It tests default settings
    def test_preselectComponents_withcf(self):
        fun = sys._getframe().f_code.co_name
        print "Run: %s.%s() " % (self.__class__.__name__, fun)
        val = {"ConfigDevice": self._cf.dp.name(),
               "WriterDevice": self._wr.dp.name(),
               "Door": 'doortestp09/testts/t1r228',
               "MntGrp": 'nxsmntgrp'}

        db = PyTango.Database()
        self._ms.dps[self._ms.ms.keys()[0]].Init()
        rs = self.openRecSelector()
        rs.configDevice = val["ConfigDevice"]
        rs.door = val["Door"]
        rs.mntGrp = val["MntGrp"]

        self._ms.dps[self._ms.ms.keys()[0]].Init()

        channelerrors = []
        poolchannels = []
        componentgroup = {}

        self._cf.dp.SetCommandVariable(["CPDICT", json.dumps(self.mycps)])
        self._cf.dp.SetCommandVariable(["DSDICT", json.dumps(self.mydss)])

        rs.preselectComponents()
        res = self.value(rs, "ComponentPreselection")

        self.assertEqual(res, '{}')
        self.assertEqual(componentgroup, {})
        self.assertEqual(channelerrors, [])
        print self._cf.dp.GetCommandVariable("COMMANDS")

    ## test
    # \brief It tests default settings
    def test_preselectComponents_withcf_cps(self):
        fun = sys._getframe().f_code.co_name
        print "Run: %s.%s() " % (self.__class__.__name__, fun)
        val = {"ConfigDevice": self._cf.dp.name(),
               "WriterDevice": self._wr.dp.name(),
               "Door": 'doortestp09/testts/t1r228',
               "MntGrp": 'nxsmntgrp'}

        db = PyTango.Database()
        self._ms.dps[self._ms.ms.keys()[0]].Init()
        rs = self.openRecSelector()
        rs.configDevice = val["ConfigDevice"]
        rs.door = val["Door"]
        rs.mntGrp = val["MntGrp"]
        rs.writerDevice = val["WriterDevice"]

        self._ms.dps[self._ms.ms.keys()[0]].Init()

        channelerrors = []
        poolchannels = ["mycp"]
        componentgroup = {"mycp": False}

        self._cf.dp.SetCommandVariable(["CPDICT", json.dumps(self.mycps)])
        self._cf.dp.SetCommandVariable(["DSDICT", json.dumps(self.mydss)])

        cnf = json.loads(rs.profileConfiguration)
        cnf["PreselectedDataSources"] = json.dumps(poolchannels)
        cnf["ComponentPreselection"] = json.dumps(componentgroup)
        rs.profileConfiguration = json.dumps(cnf)
        rs.preselectComponents()
        res = self.value(rs, "ComponentPreselection")
        self.myAssertDict(json.loads(res), {"mycp": True})
        self.assertEqual(channelerrors, [])

        self.assertTrue(val["MntGrp"] in self._cf.dp.availableSelections())
        sed = json.loads(self._cf.dp.selections([val["MntGrp"]])[0])
        self.assertEqual(len(sed.keys()), len(self._keys))
        for key, vl in self._keys:
            self.assertTrue(key in sed.keys())
            if key in val:
                self.assertEqual(sed[key], val[key])
            elif key == 'ComponentPreselection':
                self.assertEqual(set(json.loads(sed[key])),
                                 set(json.loads(res)))
            elif key == 'PreselectedDataSources':
                self.assertEqual(set(json.loads(sed[key])), set(poolchannels))
            else:
                self.assertEqual(sed[key], vl)

    ## test
    # \brief It tests default settings
    def test_preselectComponents_withcf_cps_t(self):
        fun = sys._getframe().f_code.co_name
        print "Run: %s.%s() " % (self.__class__.__name__, fun)
        val = {"ConfigDevice": self._cf.dp.name(),
               "WriterDevice": self._wr.dp.name(),
               "Door": 'doortestp09/testts/t1r228',
               "MntGrp": 'nxsmntgrp'}

        db = PyTango.Database()
        self._ms.dps[self._ms.ms.keys()[0]].Init()
        rs = self.openRecSelector()
        rs.configDevice = val["ConfigDevice"]
        rs.door = val["Door"]
        rs.mntGrp = val["MntGrp"]
        rs.writerDevice = val["WriterDevice"]

        self._ms.dps[self._ms.ms.keys()[0]].Init()

        channelerrors = []
        poolchannels = ["mycp"]
        componentgroup = {"mycp": True}

        self._cf.dp.SetCommandVariable(["CPDICT", json.dumps(self.mycps)])
        self._cf.dp.SetCommandVariable(["DSDICT", json.dumps(self.mydss)])

        cnf = json.loads(rs.profileConfiguration)
        cnf["PreselectedDataSources"] = json.dumps(poolchannels)
        cnf["ComponentPreselection"] = json.dumps(componentgroup)
        rs.profileConfiguration = json.dumps(cnf)
        rs.preselectComponents()
        res = self.value(rs, "ComponentPreselection")
        self.myAssertDict(json.loads(res), {"mycp": True})
        self.assertEqual(channelerrors, [])

        self.assertTrue(val["MntGrp"] in self._cf.dp.availableSelections())

    ## test
    # \brief It tests default settings
    def test_preselectComponents_withcf_nocps(self):
        fun = sys._getframe().f_code.co_name
        print "Run: %s.%s() " % (self.__class__.__name__, fun)
        val = {"ConfigDevice": self._cf.dp.name(),
               "WriterDevice": self._wr.dp.name(),
               "Door": 'doortestp09/testts/t1r228',
               "MntGrp": 'nxsmntgrp'}

        db = PyTango.Database()
        self._ms.dps[self._ms.ms.keys()[0]].Init()
        rs = self.openRecSelector()
        rs.configDevice = val["ConfigDevice"]
        rs.door = val["Door"]
        rs.mntGrp = val["MntGrp"]
        rs.writerDevice = val["WriterDevice"]

        self._ms.dps[self._ms.ms.keys()[0]].Init()

        channelerrors = []
        poolchannels = ["mycp"]
        componentgroup = {}

        self._cf.dp.SetCommandVariable(["CPDICT", json.dumps(self.mycps)])
        self._cf.dp.SetCommandVariable(["DSDICT", json.dumps(self.mydss)])

        cnf = json.loads(rs.profileConfiguration)
        cnf["PreselectedDataSources"] = json.dumps(poolchannels)
        cnf["ComponentPreselection"] = json.dumps(componentgroup)
        rs.profileConfiguration = json.dumps(cnf)
        rs.preselectComponents()
        res = self.value(rs, "ComponentPreselection")

        self.myAssertDict(json.loads(res), {})
        self.assertEqual(channelerrors, [])

        print self._cf.dp.GetCommandVariable("COMMANDS")

        self.assertTrue(val["MntGrp"] in self._cf.dp.availableSelections())

    ## test
    # \brief It tests default settings
    def test_preselectComponents_withcf_nochnnel(self):
        fun = sys._getframe().f_code.co_name
        print "Run: %s.%s() " % (self.__class__.__name__, fun)
        val = {"ConfigDevice": self._cf.dp.name(),
               "WriterDevice": self._wr.dp.name(),
               "Door": 'doortestp09/testts/t1r228',
               "MntGrp": 'nxsmntgrp'}

        db = PyTango.Database()
        self._ms.dps[self._ms.ms.keys()[0]].Init()
        rs = self.openRecSelector()
        rs.configDevice = val["ConfigDevice"]
        rs.door = val["Door"]
        rs.mntGrp = val["MntGrp"]
        rs.writerDevice = val["WriterDevice"]

        self._ms.dps[self._ms.ms.keys()[0]].Init()

        channelerrors = []
        poolchannels = []
        componentgroup = {"mycp": False}

        self._cf.dp.SetCommandVariable(["CPDICT", json.dumps(self.mycps)])
        self._cf.dp.SetCommandVariable(["DSDICT", json.dumps(self.mydss)])

        cnf = json.loads(rs.profileConfiguration)
        cnf["PreselectedDataSources"] = json.dumps(poolchannels)
        cnf["ComponentPreselection"] = json.dumps(componentgroup)
        rs.profileConfiguration = json.dumps(cnf)
        rs.preselectComponents()
        res = self.value(rs, "ComponentPreselection")

        self.myAssertDict(json.loads(res), {"mycp": True})
        self.assertEqual(channelerrors, [])

        print self._cf.dp.GetCommandVariable("COMMANDS")
        self.assertTrue(val["MntGrp"] in self._cf.dp.availableSelections())
        sed = json.loads(self._cf.dp.selections([val["MntGrp"]])[0])
        print sed
        self.assertEqual(len(sed.keys()), len(self._keys))
        for key, vl in self._keys:
            self.assertTrue(key in sed.keys())
            if key in val:
                self.assertEqual(sed[key], val[key])
            elif key == 'ComponentPreselection':
                self.assertEqual(set(json.loads(sed[key])),
                                 set(json.loads(res)))
            elif key == 'PreselectedDataSources':
                self.assertEqual(set(json.loads(sed[key])), set(poolchannels))
            else:
                self.assertEqual(sed[key], vl)

    ## test
    # \brief It tests default settings
    def test_preselectComponents_withcf_nochnnel_t(self):
        fun = sys._getframe().f_code.co_name
        print "Run: %s.%s() " % (self.__class__.__name__, fun)
        val = {"ConfigDevice": self._cf.dp.name(),
               "WriterDevice": self._wr.dp.name(),
               "Door": 'doortestp09/testts/t1r228',
               "MntGrp": 'nxsmntgrp'}

        db = PyTango.Database()
        self._ms.dps[self._ms.ms.keys()[0]].Init()
        rs = self.openRecSelector()
        rs.configDevice = val["ConfigDevice"]
        rs.door = val["Door"]
        rs.mntGrp = val["MntGrp"]
        rs.writerDevice = val["WriterDevice"]

        self._ms.dps[self._ms.ms.keys()[0]].Init()

        channelerrors = []
        poolchannels = []
        componentgroup = {"mycp": True}

        self._cf.dp.SetCommandVariable(["CPDICT", json.dumps(self.mycps)])
        self._cf.dp.SetCommandVariable(["DSDICT", json.dumps(self.mydss)])

        cnf = json.loads(rs.profileConfiguration)
        cnf["PreselectedDataSources"] = json.dumps(poolchannels)
        cnf["ComponentPreselection"] = json.dumps(componentgroup)
        rs.profileConfiguration = json.dumps(cnf)
        rs.preselectComponents()
        res = self.value(rs, "ComponentPreselection")

        self.myAssertDict(json.loads(res), {"mycp": True})
        self.assertEqual(channelerrors, [])

        self.assertTrue(val["MntGrp"] in self._cf.dp.availableSelections())

    ## test
    # \brief It tests default settings
    def test_preselectComponents_wds_t(self):
        fun = sys._getframe().f_code.co_name
        print "Run: %s.%s() " % (self.__class__.__name__, fun)
        val = {"ConfigDevice": self._cf.dp.name(),
               "WriterDevice": self._wr.dp.name(),
               "Door": 'doortestp09/testts/t1r228',
               "MntGrp": 'nxsmntgrp'}

        db = PyTango.Database()
        self._ms.dps[self._ms.ms.keys()[0]].Init()
        rs = self.openRecSelector()
        rs.configDevice = val["ConfigDevice"]
        rs.door = val["Door"]
        rs.mntGrp = val["MntGrp"]
        rs.writerDevice = val["WriterDevice"]

        self._ms.dps[self._ms.ms.keys()[0]].Init()

        channelerrors = []
        poolchannels = []
        componentgroup = {"smycp": True}

        self._cf.dp.SetCommandVariable(["CPDICT", json.dumps(self.smycps)])
        self._cf.dp.SetCommandVariable(["DSDICT", json.dumps(self.smydss)])

        cnf = json.loads(rs.profileConfiguration)
        cnf["PreselectedDataSources"] = json.dumps(poolchannels)
        cnf["ComponentPreselection"] = json.dumps(componentgroup)
        rs.profileConfiguration = json.dumps(cnf)
        rs.preselectComponents()
        res = self.value(rs, "ComponentPreselection")

        self.myAssertDict(json.loads(res), {"smycp": True})
        self.assertEqual(channelerrors, [])

        self.assertTrue(val["MntGrp"] in self._cf.dp.availableSelections())

    ## test
    # \brief It tests default settings
    def test_preselectComponents_wds(self):
        fun = sys._getframe().f_code.co_name
        print "Run: %s.%s() " % (self.__class__.__name__, fun)
        val = {"ConfigDevice": self._cf.dp.name(),
               "WriterDevice": self._wr.dp.name(),
               "Door": 'doortestp09/testts/t1r228',
               "MntGrp": 'nxsmntgrp'}

        db = PyTango.Database()
        self._ms.dps[self._ms.ms.keys()[0]].Init()
        rs = self.openRecSelector()
        rs.configDevice = val["ConfigDevice"]
        rs.door = val["Door"]
        rs.mntGrp = val["MntGrp"]
        rs.writerDevice = val["WriterDevice"]

        self._ms.dps[self._ms.ms.keys()[0]].Init()

        channelerrors = []
        poolchannels = []
        componentgroup = {"smycp": False}

        self._cf.dp.SetCommandVariable(["CPDICT", json.dumps(self.smycps)])
        self._cf.dp.SetCommandVariable(["DSDICT", json.dumps(self.smydss)])

        cnf = json.loads(rs.profileConfiguration)
        cnf["PreselectedDataSources"] = json.dumps(poolchannels)
        cnf["ComponentPreselection"] = json.dumps(componentgroup)
        rs.profileConfiguration = json.dumps(cnf)
        rs.preselectComponents()
        res = self.value(rs, "ComponentPreselection")

        self.myAssertDict(json.loads(res), {"smycp": True})
        self.assertEqual(channelerrors, [])

        self.assertTrue(val["MntGrp"] in self._cf.dp.availableSelections())
        sed = json.loads(self._cf.dp.selections([val["MntGrp"]])[0])
        self.assertEqual(len(sed.keys()), len(self._keys))
        for key, vl in self._keys:
            self.assertTrue(key in sed.keys())
            if key in val:
                self.assertEqual(sed[key], val[key])
            elif key == 'ComponentPreselection':
                self.assertEqual(set(json.loads(sed[key])),
                                 set(json.loads(res)))
            elif key == 'PreselectedDataSources':
                self.assertEqual(set(json.loads(sed[key])),
                                 set(poolchannels))
            else:
                self.assertEqual(sed[key], vl)

    ## test
    # \brief It tests default settings
    def test_preselectComponents_wds2(self):
        fun = sys._getframe().f_code.co_name
        print "Run: %s.%s() " % (self.__class__.__name__, fun)
        val = {"ConfigDevice": self._cf.dp.name(),
               "WriterDevice": self._wr.dp.name(),
               "Door": 'doortestp09/testts/t1r228',
               "MntGrp": 'nxsmntgrp'}

        db = PyTango.Database()
        self._ms.dps[self._ms.ms.keys()[0]].Init()
        rs = self.openRecSelector()
        rs.configDevice = val["ConfigDevice"]
        rs.door = val["Door"]
        rs.mntGrp = val["MntGrp"]
        rs.writerDevice = val["WriterDevice"]

        self._ms.dps[self._ms.ms.keys()[0]].Init()

        channelerrors = []
        poolchannels = []
        componentgroup = {"smycp": False, "smycp2": False, "smycp3": False}

        self._cf.dp.SetCommandVariable(["CPDICT", json.dumps(self.smycps)])
        self._cf.dp.SetCommandVariable(["DSDICT", json.dumps(self.smydss)])

        cnf = json.loads(rs.profileConfiguration)
        cnf["PreselectedDataSources"] = json.dumps(poolchannels)
        cnf["ComponentPreselection"] = json.dumps(componentgroup)
        rs.profileConfiguration = json.dumps(cnf)
        rs.preselectComponents()
        res = self.value(rs, "ComponentPreselection")

        self.myAssertDict(json.loads(res), {
            "smycp": True, "smycp2": True, "smycp3": True})
        self.assertEqual(channelerrors, [])

        res2 = json.loads(self._cf.dp.GetCommandVariable("VARS"))
        self.assertTrue(val["MntGrp"] in self._cf.dp.availableSelections())
        sed = json.loads(self._cf.dp.selections([val["MntGrp"]])[0])
        self.assertEqual(len(sed.keys()), len(self._keys))
        for key, vl in self._keys:
            self.assertTrue(key in sed.keys())
            if key in val:
                self.assertEqual(sed[key], val[key])
            elif key == 'ComponentPreselection':
                self.assertEqual(set(json.loads(sed[key])),
                                 set(json.loads(res)))
            elif key == 'PreselectedDataSources':
                self.assertEqual(set(json.loads(sed[key])),
                                 set(poolchannels))
            else:
                self.assertEqual(sed[key], vl)

    ## test
    # \brief It tests default settings
    def test_preselectComponents_2wds(self):
        fun = sys._getframe().f_code.co_name
        print "Run: %s.%s() " % (self.__class__.__name__, fun)
        val = {"ConfigDevice": self._cf.dp.name(),
               "WriterDevice": self._wr.dp.name(),
               "Door": 'doortestp09/testts/t1r228',
               "MntGrp": 'nxsmntgrp'}
        simps2 = TestServerSetUp.TestServerSetUp(
            "ttestp09/testts/t2r228", "S2")
        try:
            simps2.setUp()

            db = PyTango.Database()
            self._ms.dps[self._ms.ms.keys()[0]].Init()
            rs = self.openRecSelector()
            rs.configDevice = val["ConfigDevice"]
            rs.door = val["Door"]
            rs.mntGrp = val["MntGrp"]
            rs.writerDevice = val["WriterDevice"]

            self._ms.dps[self._ms.ms.keys()[0]].Init()

            channelerrors = []
            poolchannels = []
            componentgroup = {"smycp": False, "smycp2": False, "smycp3": False,
                              "s2mycp": False, "s2mycp2": False,
                              "s2mycp3": False}

            cps = dict(self.smycps)
            cps.update(self.smycps2)
            dss = dict(self.smydss)
            dss.update(self.smydss2)

            self._cf.dp.SetCommandVariable(["CPDICT", json.dumps(cps)])
            self._cf.dp.SetCommandVariable(["DSDICT", json.dumps(dss)])

            cnf = json.loads(rs.profileConfiguration)
            cnf["PreselectedDataSources"] = json.dumps(poolchannels)
            cnf["ComponentPreselection"] = json.dumps(componentgroup)
            rs.profileConfiguration = json.dumps(cnf)
            rs.preselectComponents()
            res = self.value(rs, "ComponentPreselection")

            self.myAssertDict(json.loads(res), {
                "smycp": True, "smycp2": True, "smycp3": True,
                "s2mycp": True, "s2mycp2": True, "s2mycp3": True})
            self.assertEqual(len(channelerrors), 0)

            res2 = json.loads(self._cf.dp.GetCommandVariable("VARS"))
            self.assertTrue(val["MntGrp"] in self._cf.dp.availableSelections())
            sed = json.loads(self._cf.dp.selections([val["MntGrp"]])[0])
            self.assertEqual(len(sed.keys()), len(self._keys))
            for key, vl in self._keys:
                self.assertTrue(key in sed.keys())
                if key in val:
                    self.assertEqual(sed[key], val[key])
                elif key == 'ComponentPreselection':
                    self.assertEqual(set(json.loads(sed[key])),
                                     set(json.loads(res)))
                elif key == 'PreselectedDataSources':
                    self.assertEqual(set(json.loads(sed[key])),
                                     set(poolchannels))
                else:
                    self.assertEqual(sed[key], vl)
        finally:
            simps2.tearDown()

    ## test
    # \brief It tests default settings
    def test_preselectComponents_2wds_dvnorunning(self):
        fun = sys._getframe().f_code.co_name
        print "Run: %s.%s() " % (self.__class__.__name__, fun)
        val = {"ConfigDevice": self._cf.dp.name(),
               "WriterDevice": self._wr.dp.name(),
               "Door": 'doortestp09/testts/t1r228',
               "MntGrp": 'nxsmntgrp'}
        simps2 = TestServerSetUp.TestServerSetUp(
            "ttestp09/testts/t2r228", "S2")
        try:
            simps2.add()

            db = PyTango.Database()
            self._ms.dps[self._ms.ms.keys()[0]].Init()
            rs = self.openRecSelector()
            rs.configDevice = val["ConfigDevice"]
            rs.door = val["Door"]
            rs.mntGrp = val["MntGrp"]
            rs.writerDevice = val["WriterDevice"]

            self._ms.dps[self._ms.ms.keys()[0]].Init()

            channelerrors = []
            poolchannels = []
            componentgroup = {"smycp": False, "smycp2": False, "smycp3": False,
                              "s2mycp": False, "s2mycp2": False,
                              "s2mycp3": False}

            cps = dict(self.smycps)
            cps.update(self.smycps2)
            dss = dict(self.smydss)
            dss.update(self.smydss2)

            self._cf.dp.SetCommandVariable(["CPDICT", json.dumps(cps)])
            self._cf.dp.SetCommandVariable(["DSDICT", json.dumps(dss)])

            cnf = json.loads(rs.profileConfiguration)
            cnf["PreselectedDataSources"] = json.dumps(poolchannels)
            cnf["ComponentPreselection"] = json.dumps(componentgroup)
            rs.profileConfiguration = json.dumps(cnf)
            rs.preselectComponents()
            res = self.value(rs, "ComponentPreselection")

            self.myAssertDict(json.loads(res), {
                "smycp": True, "smycp2": True, "smycp3": True,
                "s2mycp": False, "s2mycp2": False, "s2mycp3": False})
            self.assertEqual(len(rs.descriptionErrors), 3)

            res2 = json.loads(self._cf.dp.GetCommandVariable("VARS"))
            self.assertTrue(val["MntGrp"] in self._cf.dp.availableSelections())
            sed = json.loads(self._cf.dp.selections([val["MntGrp"]])[0])
            self.assertEqual(len(sed.keys()), len(self._keys))
            for key, vl in self._keys:
                self.assertTrue(key in sed.keys())
                if key in val:
                    self.assertEqual(sed[key], val[key])
                elif key == 'ComponentPreselection':
                    self.assertEqual(set(json.loads(sed[key])),
                                     set(json.loads(res)))
                elif key == 'PreselectedDataSources':
                    self.assertEqual(set(json.loads(sed[key])),
                                     set(poolchannels))
                else:
                    self.assertEqual(sed[key], vl)
        finally:
            simps2.delete()

    ## test
    # \brief It tests default settings
    def test_preselectComponents_2wds_dvnodef(self):
        fun = sys._getframe().f_code.co_name
        print "Run: %s.%s() " % (self.__class__.__name__, fun)
        val = {"ConfigDevice": self._cf.dp.name(),
               "WriterDevice": self._wr.dp.name(),
               "Door": 'doortestp09/testts/t1r228',
               "MntGrp": 'nxsmntgrp'}

        db = PyTango.Database()
        self._ms.dps[self._ms.ms.keys()[0]].Init()
        rs = self.openRecSelector()
        rs.configDevice = val["ConfigDevice"]
        rs.door = val["Door"]
        rs.mntGrp = val["MntGrp"]
        rs.writerDevice = val["WriterDevice"]

        self._ms.dps[self._ms.ms.keys()[0]].Init()

        channelerrors = []
        poolchannels = []
        componentgroup = {"smycp": False, "smycp2": False, "smycp3": False,
                          "s2mycp": False, "s2mycp2": False, "s2mycp3": False}

        cps = dict(self.smycps)
        cps.update(self.smycps2)
        dss = dict(self.smydss)
        dss.update(self.smydss2)

        self._cf.dp.SetCommandVariable(["CPDICT", json.dumps(cps)])
        self._cf.dp.SetCommandVariable(["DSDICT", json.dumps(dss)])

        cnf = json.loads(rs.profileConfiguration)
        cnf["PreselectedDataSources"] = json.dumps(poolchannels)
        cnf["ComponentPreselection"] = json.dumps(componentgroup)
        rs.profileConfiguration = json.dumps(cnf)
        rs.preselectComponents()
        res = self.value(rs, "ComponentPreselection")

        self.myAssertDict(json.loads(res), {
            "smycp": True, "smycp2": True, "smycp3": True,
            "s2mycp": False, "s2mycp2": False, "s2mycp3": False})
        self.assertEqual(len(rs.descriptionErrors), 3)

        res2 = json.loads(self._cf.dp.GetCommandVariable("VARS"))
        self.assertTrue(val["MntGrp"] in self._cf.dp.availableSelections())
        sed = json.loads(self._cf.dp.selections([val["MntGrp"]])[0])
        self.assertEqual(len(sed.keys()), len(self._keys))
        for key, vl in self._keys:
            self.assertTrue(key in sed.keys())
            if key in val:
                self.assertEqual(sed[key], val[key])
            elif key == 'ComponentPreselection':
                self.assertEqual(set(json.loads(sed[key])),
                                 set(json.loads(res)))
            elif key == 'PreselectedDataSources':
                self.assertEqual(set(json.loads(sed[key])),
                                 set(poolchannels))
            else:
                self.assertEqual(sed[key], vl)

    ## test
    # \brief It tests default settings
    def test_preselectComponents_2wds_nods(self):
        fun = sys._getframe().f_code.co_name
        print "Run: %s.%s() " % (self.__class__.__name__, fun)
        val = {"ConfigDevice": self._cf.dp.name(),
               "WriterDevice": self._wr.dp.name(),
               "Door": 'doortestp09/testts/t1r228',
               "MntGrp": 'nxsmntgrp'}
        simps2 = TestServerSetUp.TestServerSetUp(
            "ttestp09/testts/t2r228", "S2")
        try:
            simps2.setUp()

            db = PyTango.Database()
            self._ms.dps[self._ms.ms.keys()[0]].Init()
            rs = self.openRecSelector()
            rs.configDevice = val["ConfigDevice"]
            rs.door = val["Door"]
            rs.mntGrp = val["MntGrp"]
            rs.writerDevice = val["WriterDevice"]

            self._ms.dps[self._ms.ms.keys()[0]].Init()

            channelerrors = []
            poolchannels = []
            componentgroup = {"smycp": False, "smycp2": False, "smycp3": False,
                              "s2mycp": False, "s2mycp2": False,
                              "s2mycp3": False}

            cps = dict(self.smycps)
            cps.update(self.smycps2)
            dss = dict(self.smydss)
#            dss.update(self.smydss2)

            self._cf.dp.SetCommandVariable(["CPDICT", json.dumps(cps)])
            self._cf.dp.SetCommandVariable(["DSDICT", json.dumps(dss)])

            cnf = json.loads(rs.profileConfiguration)
            cnf["PreselectedDataSources"] = json.dumps(poolchannels)
            cnf["ComponentPreselection"] = json.dumps(componentgroup)
            rs.profileConfiguration = json.dumps(cnf)
            rs.preselectComponents()
            res = self.value(rs, "ComponentPreselection")

            self.myAssertDict(json.loads(res), {
                "smycp": True, "smycp2": True, "smycp3": True,
                "s2mycp": True, "s2mycp2": True, "s2mycp3": True})
            self.assertTrue(not rs.descriptionErrors)

            res2 = json.loads(self._cf.dp.GetCommandVariable("VARS"))
            self.assertTrue(val["MntGrp"] in self._cf.dp.availableSelections())
            sed = json.loads(self._cf.dp.selections([val["MntGrp"]])[0])
            self.assertEqual(len(sed.keys()), len(self._keys))
            for key, vl in self._keys:
                self.assertTrue(key in sed.keys())
                if key in val:
                    self.assertEqual(sed[key], val[key])
                elif key == 'ComponentPreselection':
                    self.assertEqual(set(json.loads(sed[key])),
                                     set(json.loads(res)))
                elif key == 'PreselectedDataSources':
                    self.assertEqual(set(json.loads(sed[key])),
                                     set(poolchannels))
                else:
                    self.assertEqual(sed[key], vl)
        finally:
            simps2.tearDown()

    ## test
    # \brief It tests default settings
    def test_preselectComponents_2wds_nodspool(self):
        fun = sys._getframe().f_code.co_name
        print "Run: %s.%s() " % (self.__class__.__name__, fun)
        val = {"ConfigDevice": self._cf.dp.name(),
               "WriterDevice": self._wr.dp.name(),
               "Door": 'doortestp09/testts/t1r228',
               "MntGrp": 'nxsmntgrp'}
        simps2 = TestServerSetUp.TestServerSetUp(
            "ttestp09/testts/t2r228", "S2")
        try:
            simps2.setUp()
            db = PyTango.Database()
            self._ms.dps[self._ms.ms.keys()[0]].Init()
            rs = self.openRecSelector()
            rs.configDevice = val["ConfigDevice"]
            rs.door = val["Door"]
            rs.mntGrp = val["MntGrp"]
            rs.writerDevice = val["WriterDevice"]

            self._ms.dps[self._ms.ms.keys()[0]].Init()

            poolchannels = ["scalar2_long", "spectrum2_short"]
            componentgroup = {"smycp": False, "smycp2": False, "smycp3": False,
                              "s2mycp": False, "s2mycp2": False,
                              "s2mycp3": False}

            cps = dict(self.smycps)
            cps.update(self.smycps2)
            dss = dict(self.smydss)
#            dss.update(self.smydss2)

            self._cf.dp.SetCommandVariable(["CPDICT", json.dumps(cps)])
            self._cf.dp.SetCommandVariable(["DSDICT", json.dumps(dss)])

            cnf = json.loads(rs.profileConfiguration)
            cnf["PreselectedDataSources"] = json.dumps(poolchannels)
            cnf["ComponentPreselection"] = json.dumps(componentgroup)
            rs.profileConfiguration = json.dumps(cnf)
            rs.preselectComponents()
            res = self.value(rs, "ComponentPreselection")

            self.myAssertDict(json.loads(res), {
                "smycp": True, "smycp2": True, "smycp3": True,
                "s2mycp": False, "s2mycp2": False, "s2mycp3": True})
            self.assertEqual(len(rs.descriptionErrors), 2)

            res2 = json.loads(self._cf.dp.GetCommandVariable("VARS"))
            self.assertTrue(val["MntGrp"] in self._cf.dp.availableSelections())
            sed = json.loads(self._cf.dp.selections([val["MntGrp"]])[0])
            self.assertEqual(len(sed.keys()), len(self._keys))
            for key, vl in self._keys:
                self.assertTrue(key in sed.keys())
                if key in val:
                    self.assertEqual(sed[key], val[key])
                elif key == 'ComponentPreselection':
                    self.assertEqual(set(json.loads(sed[key])),
                                     set(json.loads(res)))
                elif key == 'PreselectedDataSources':
                    self.assertEqual(set(json.loads(sed[key])),
                                     set(poolchannels))
                else:
                    self.assertEqual(sed[key], vl)
        finally:
            simps2.tearDown()

    ## test
    # \brief It tests default settings
    def test_preselectComponents_2wds_notangods(self):
        fun = sys._getframe().f_code.co_name
        print "Run: %s.%s() " % (self.__class__.__name__, fun)
        val = {"ConfigDevice": self._cf.dp.name(),
               "WriterDevice": self._wr.dp.name(),
               "Door": 'doortestp09/testts/t1r228',
               "MntGrp": 'nxsmntgrp'}
        simps2 = TestServerSetUp.TestServerSetUp(
            "ttestp09/testts/t2r228", "S2")
        try:
            simps2.setUp()

            db = PyTango.Database()
            self._ms.dps[self._ms.ms.keys()[0]].Init()
            rs = self.openRecSelector()
            rs.configDevice = val["ConfigDevice"]
            rs.door = val["Door"]
            rs.mntGrp = val["MntGrp"]
            rs.writerDevice = val["WriterDevice"]

            self._ms.dps[self._ms.ms.keys()[0]].Init()

            poolchannels = ["scalar2_long", "spectrum2_short"]
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

            cnf = json.loads(rs.profileConfiguration)
            cnf["PreselectedDataSources"] = json.dumps(poolchannels)
            cnf["ComponentPreselection"] = json.dumps(componentgroup)
            rs.profileConfiguration = json.dumps(cnf)
            rs.preselectComponents()
            res = self.value(rs, "ComponentPreselection")

            self.myAssertDict(json.loads(res), {
                "smycp": True, "smycp2": True, "smycp3": True,
                "s2mycp": True, "s2mycp2": True, "s2mycp3": True,
                "smycpnt1": True})
            self.assertTrue(not rs.descriptionErrors)

    #        print self._cf.dp.GetCommandVariable("COMMANDS")
            res2 = json.loads(self._cf.dp.GetCommandVariable("VARS"))
            self.assertTrue(val["MntGrp"] in self._cf.dp.availableSelections())
            sed = json.loads(self._cf.dp.selections([val["MntGrp"]])[0])
            self.assertEqual(len(sed.keys()), len(self._keys))
            for key, vl in self._keys:
                self.assertTrue(key in sed.keys())
                if key in val:
                    self.assertEqual(sed[key], val[key])
                elif key == 'ComponentPreselection':
                    self.assertEqual(set(json.loads(sed[key])),
                                     set(json.loads(res)))
                elif key == 'PreselectedDataSources':
                    self.assertEqual(set(json.loads(sed[key])),
                                     set(poolchannels))
                else:
                    self.assertEqual(sed[key], vl)
        finally:
            simps2.tearDown()

    ## test
    # \brief It tests default settings
    def test_preselectComponents_2wds_notangodsnopool(self):
        fun = sys._getframe().f_code.co_name
        print "Run: %s.%s() " % (self.__class__.__name__, fun)
        val = {"ConfigDevice": self._cf.dp.name(),
               "WriterDevice": self._wr.dp.name(),
               "Door": 'doortestp09/testts/t1r228',
               "MntGrp": 'nxsmntgrp'}
        simps2 = TestServerSetUp.TestServerSetUp(
            "ttestp09/testts/t2r228", "S2")
        try:
            simps2.setUp()

            db = PyTango.Database()
            self._ms.dps[self._ms.ms.keys()[0]].Init()
            rs = self.openRecSelector()
            rs.configDevice = val["ConfigDevice"]
            rs.door = val["Door"]
            rs.mntGrp = val["MntGrp"]
            rs.writerDevice = val["WriterDevice"]

            self._ms.dps[self._ms.ms.keys()[0]].Init()

            poolchannels = ["scalar2_long", "spectrum2_short", "client_long"]
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

            cnf = json.loads(rs.profileConfiguration)
            cnf["PreselectedDataSources"] = json.dumps(poolchannels)
            cnf["ComponentPreselection"] = json.dumps(componentgroup)
            rs.profileConfiguration = json.dumps(cnf)
            rs.preselectComponents()
            res = self.value(rs, "ComponentPreselection")

            self.myAssertDict(json.loads(res), {
                "smycp": True, "smycp2": True, "smycp3": True,
                "s2mycp": True, "s2mycp2": True, "s2mycp3": True,
                "smycpnt1": False})
            self.assertEqual(len(rs.descriptionErrors), 1)

    #        print self._cf.dp.GetCommandVariable("COMMANDS")
            res2 = json.loads(self._cf.dp.GetCommandVariable("VARS"))
            self.assertTrue(val["MntGrp"] in self._cf.dp.availableSelections())
            sed = json.loads(self._cf.dp.selections([val["MntGrp"]])[0])
            self.assertEqual(len(sed.keys()), len(self._keys))
            for key, vl in self._keys:
                self.assertTrue(key in sed.keys())
                if key in val:
                    self.assertEqual(sed[key], val[key])
                elif key == 'ComponentPreselection':
                    self.assertEqual(set(json.loads(sed[key])),
                                     set(json.loads(res)))
                elif key == 'PreselectedDataSources':
                    self.assertEqual(set(json.loads(sed[key])),
                                     set(poolchannels))
                else:
                    self.assertEqual(sed[key], vl)
        finally:
            simps2.tearDown()

    ## test
    # \brief It tests default settings
    def test_preselectComponents_2wds_notangodsnopool2(self):
        fun = sys._getframe().f_code.co_name
        print "Run: %s.%s() " % (self.__class__.__name__, fun)
        val = {"ConfigDevice": self._cf.dp.name(),
               "WriterDevice": self._wr.dp.name(),
               "Door": 'doortestp09/testts/t1r228',
               "MntGrp": 'nxsmntgrp'}
        simps2 = TestServerSetUp.TestServerSetUp(
            "ttestp09/testts/t2r228", "S2")
        try:
            simps2.setUp()

            db = PyTango.Database()
            self._ms.dps[self._ms.ms.keys()[0]].Init()
            rs = self.openRecSelector()
            rs.configDevice = val["ConfigDevice"]
            rs.door = val["Door"]
            rs.mntGrp = val["MntGrp"]
            rs.writerDevice = val["WriterDevice"]

            self._ms.dps[self._ms.ms.keys()[0]].Init()

            poolchannels = ["scalar2_long", "spectrum2_short", "client_long"]
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

            cnf = json.loads(rs.profileConfiguration)
            cnf["PreselectedDataSources"] = json.dumps(poolchannels)
            cnf["ComponentPreselection"] = json.dumps(componentgroup)
            rs.profileConfiguration = json.dumps(cnf)
            rs.preselectComponents()
            res = self.value(rs, "ComponentPreselection")

            self.myAssertDict(json.loads(res), {
                "smycp": True, "smycp2": True, "smycp3": True,
                "s2mycp": True, "s2mycp2": True, "s2mycp3": True,
                "smycpnt1": False})
            self.assertEqual(len(rs.descriptionErrors), 1)

    #        print self._cf.dp.GetCommandVariable("COMMANDS")
            res2 = json.loads(self._cf.dp.GetCommandVariable("VARS"))
            self.assertTrue(val["MntGrp"] in self._cf.dp.availableSelections())
            sed = json.loads(self._cf.dp.selections([val["MntGrp"]])[0])
            self.assertEqual(len(sed.keys()), len(self._keys))
            for key, vl in self._keys:
                self.assertTrue(key in sed.keys())
                if key in val:
                    self.assertEqual(sed[key], val[key])
                elif key == 'ComponentPreselection':
                    self.assertEqual(set(json.loads(sed[key])),
                                     set(json.loads(res)))
                elif key == 'PreselectedDataSources':
                    self.assertEqual(set(json.loads(sed[key])),
                                     set(poolchannels))
                else:
                    self.assertEqual(sed[key], vl)
        finally:
            simps2.tearDown()

    ## test
    # \brief It tests default settings
    def test_preselectComponents_2wds_notangods2(self):
        fun = sys._getframe().f_code.co_name
        print "Run: %s.%s() " % (self.__class__.__name__, fun)
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

            db = PyTango.Database()
            db.put_device_property(self._ms.ms.keys()[0],
                                   {'PoolNames': self._pool.dp.name()})
            self._ms.dps[self._ms.ms.keys()[0]].Init()
            rs = self.openRecSelector()
            rs.configDevice = val["ConfigDevice"]
            rs.door = val["Door"]
            rs.mntGrp = val["MntGrp"]
            rs.writerDevice = val["WriterDevice"]

            self._ms.dps[self._ms.ms.keys()[0]].Init()

            channelerrors = []
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

            pool = self._pool.dp
            pool.AcqChannelList = [json.dumps(a) for a in arr]

            cnf = json.loads(rs.profileConfiguration)
            cnf["PreselectedDataSources"] = json.dumps(poolchannels)
            cnf["ComponentPreselection"] = json.dumps(componentgroup)
            rs.profileConfiguration = json.dumps(cnf)
            rs.preselectComponents()
            res = self.value(rs, "ComponentPreselection")

            self.myAssertDict(json.loads(res), {
                "smycp": True, "smycp2": True, "smycp3": True,
                "s2mycp": True, "s2mycp2": True, "s2mycp3": True,
                "smycpnt1": True})
            self.assertTrue(not rs.descriptionErrors)

            res2 = json.loads(self._cf.dp.GetCommandVariable("VARS"))
            self.assertTrue(val["MntGrp"] in self._cf.dp.availableSelections())
            sed = json.loads(self._cf.dp.selections([val["MntGrp"]])[0])
            self.assertEqual(len(sed.keys()), len(self._keys))
            for key, vl in self._keys:
                self.assertTrue(key in sed.keys())
                if key in val:
                    self.assertEqual(sed[key], val[key])
                elif key == 'ComponentPreselection':
                    self.assertEqual(set(json.loads(sed[key])),
                                     set(json.loads(res)))
                elif key == 'PreselectedDataSources':
                    self.assertEqual(set(json.loads(sed[key])),
                                     set(poolchannels))
                else:
                    self.assertEqual(sed[key], vl)
        finally:
            simps2.tearDown()

    ## test
    # \brief It tests default settings
    def test_preselectComponents_2wds_notangods2_bl(self):
        fun = sys._getframe().f_code.co_name
        print "Run: %s.%s() " % (self.__class__.__name__, fun)
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

            db = PyTango.Database()
            db.put_device_property(self._ms.ms.keys()[0],
                                   {'PoolNames': self._pool.dp.name()})
            self._ms.dps[self._ms.ms.keys()[0]].Init()
            rs = self.openRecSelector()
            self.setProp(rs, "poolBlacklist",
                         [self._pool.dp.name()])
            rs.configDevice = val["ConfigDevice"]
            rs.door = val["Door"]
            rs.mntGrp = val["MntGrp"]
            rs.writerDevice = val["WriterDevice"]

            self._ms.dps[self._ms.ms.keys()[0]].Init()

            channelerrors = []
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

            pool = self._pool.dp
            pool.AcqChannelList = [json.dumps(a) for a in arr]

            cnf = json.loads(rs.profileConfiguration)
            cnf["PreselectedDataSources"] = json.dumps(poolchannels)
            cnf["ComponentPreselection"] = json.dumps(componentgroup)
            rs.profileConfiguration = json.dumps(cnf)
            rs.preselectComponents()
            res = self.value(rs, "ComponentPreselection")

            self.myAssertDict(json.loads(res), {
                "smycp": True, "smycp2": True, "smycp3": True,
                "s2mycp": True, "s2mycp2": True, "s2mycp3": True,
                "smycpnt1": True})
            self.assertTrue(not rs.descriptionErrors)

            res2 = json.loads(self._cf.dp.GetCommandVariable("VARS"))
            self.assertTrue(val["MntGrp"] in self._cf.dp.availableSelections())
            sed = json.loads(self._cf.dp.selections([val["MntGrp"]])[0])
            self.assertEqual(len(sed.keys()), len(self._keys))
            for key, vl in self._keys:
                self.assertTrue(key in sed.keys())
                if key in val:
                    self.assertEqual(sed[key], val[key])
                elif key == 'ComponentPreselection':
                    self.assertEqual(set(json.loads(sed[key])),
                                     set(json.loads(res)))
                elif key == 'PreselectedDataSources':
                    self.assertEqual(set(json.loads(sed[key])),
                                     set(poolchannels))
                else:
                    self.assertEqual(sed[key], vl)
        finally:
            simps2.tearDown()

    ## test
    # \brief It tests default settings
    def test_preselectComponents_2wds_notangodspool_error(self):
        fun = sys._getframe().f_code.co_name
        print "Run: %s.%s() " % (self.__class__.__name__, fun)
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

            db = PyTango.Database()
            db.put_device_property(self._ms.ms.keys()[0],
                                   {'PoolNames': self._pool.dp.name()})
            self._ms.dps[self._ms.ms.keys()[0]].Init()
            rs = self.openRecSelector()
            rs.configDevice = val["ConfigDevice"]
            rs.door = val["Door"]
            rs.mntGrp = val["MntGrp"]
            rs.writerDevice = val["WriterDevice"]

            self._ms.dps[self._ms.ms.keys()[0]].Init()

            channelerrors = []
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

            pool = self._pool.dp
            pool.AcqChannelList = [json.dumps(a) for a in arr]

            cnf = json.loads(rs.profileConfiguration)
            cnf["PreselectedDataSources"] = json.dumps(poolchannels)
            cnf["ComponentPreselection"] = json.dumps(componentgroup)
            rs.profileConfiguration = json.dumps(cnf)
            rs.preselectComponents()
            res = self.value(rs, "ComponentPreselection")

            self.myAssertDict(json.loads(res), {
                "smycp": True, "smycp2": True, "smycp3": True,
                "s2mycp": True, "s2mycp2": True, "s2mycp3": True,
                "smycpnt1": False})
            self.assertEqual(len(rs.descriptionErrors), 1)

    #        print self._cf.dp.GetCommandVariable("COMMANDS")
            res2 = json.loads(self._cf.dp.GetCommandVariable("VARS"))
            self.assertTrue(val["MntGrp"] in self._cf.dp.availableSelections())
            sed = json.loads(self._cf.dp.selections([val["MntGrp"]])[0])
            self.assertEqual(len(sed.keys()), len(self._keys))
            for key, vl in self._keys:
                self.assertTrue(key in sed.keys())
                if key in val:
                    self.assertEqual(sed[key], val[key])
                elif key == 'ComponentPreselection':
                    self.assertEqual(set(json.loads(sed[key])),
                                     set(json.loads(res)))
                elif key == 'PreselectedDataSources':
                    self.assertEqual(set(json.loads(sed[key])),
                                     set(poolchannels))
                else:
                    self.assertEqual(sed[key], vl)
        finally:
            simps2.tearDown()

    ## test
    # \brief It tests default settings
    def test_preselectComponents_2wds_notangodspool_error_bl(self):
        fun = sys._getframe().f_code.co_name
        print "Run: %s.%s() " % (self.__class__.__name__, fun)
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

            db = PyTango.Database()
            db.put_device_property(self._ms.ms.keys()[0],
                                   {'PoolNames': self._pool.dp.name()})
            self._ms.dps[self._ms.ms.keys()[0]].Init()
            rs = self.openRecSelector()
            self.setProp(rs, "poolBlacklist",
                         [self._pool.dp.name()])
            rs.configDevice = val["ConfigDevice"]
            rs.door = val["Door"]
            rs.mntGrp = val["MntGrp"]
            rs.writerDevice = val["WriterDevice"]

            self._ms.dps[self._ms.ms.keys()[0]].Init()

            channelerrors = []
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

            pool = self._pool.dp
            pool.AcqChannelList = [json.dumps(a) for a in arr]

            cnf = json.loads(rs.profileConfiguration)
            cnf["PreselectedDataSources"] = json.dumps(poolchannels)
            cnf["ComponentPreselection"] = json.dumps(componentgroup)
            rs.profileConfiguration = json.dumps(cnf)
            rs.preselectComponents()
            res = self.value(rs, "ComponentPreselection")

            self.myAssertDict(json.loads(res), {
                "smycp": True, "smycp2": True, "smycp3": True,
                "s2mycp": True, "s2mycp2": True, "s2mycp3": True,
                "smycpnt1": False})
            self.assertEqual(len(rs.descriptionErrors), 1)

    #        print self._cf.dp.GetCommandVariable("COMMANDS")
            res2 = json.loads(self._cf.dp.GetCommandVariable("VARS"))
            self.assertTrue(val["MntGrp"] in self._cf.dp.availableSelections())
            sed = json.loads(self._cf.dp.selections([val["MntGrp"]])[0])
            self.assertEqual(len(sed.keys()), len(self._keys))
            for key, vl in self._keys:
                self.assertTrue(key in sed.keys())
                if key in val:
                    self.assertEqual(sed[key], val[key])
                elif key == 'ComponentPreselection':
                    self.assertEqual(set(json.loads(sed[key])),
                                     set(json.loads(res)))
                elif key == 'PreselectedDataSources':
                    self.assertEqual(set(json.loads(sed[key])),
                                     set(poolchannels))
                else:
                    self.assertEqual(sed[key], vl)
        finally:
            simps2.tearDown()

    ## test
    # \brief It tests default settings
    def test_preselectComponents_2wds_notangodspool(self):
        fun = sys._getframe().f_code.co_name
        print "Run: %s.%s() " % (self.__class__.__name__, fun)
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

            db = PyTango.Database()
            db.put_device_property(self._ms.ms.keys()[0],
                                   {'PoolNames': self._pool.dp.name()})
            self._ms.dps[self._ms.ms.keys()[0]].Init()
            rs = self.openRecSelector()
            rs.configDevice = val["ConfigDevice"]
            rs.door = val["Door"]
            rs.mntGrp = val["MntGrp"]
            rs.writerDevice = val["WriterDevice"]

            self._ms.dps[self._ms.ms.keys()[0]].Init()

            channelerrors = []

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

            pool = self._pool.dp
            pool.AcqChannelList = [json.dumps(a) for a in arr]

            self._simps.dp.ChangeValueType("ScalarShort")
            self._simps.dp.Value = 43

            cnf = json.loads(rs.profileConfiguration)
            cnf["PreselectedDataSources"] = json.dumps(poolchannels)
            cnf["ComponentPreselection"] = json.dumps(componentgroup)
            rs.profileConfiguration = json.dumps(cnf)
            rs.preselectComponents()
            res = self.value(rs, "ComponentPreselection")

            self.myAssertDict(json.loads(res), {
                "smycp": True, "smycp2": True, "smycp3": True,
                "s2mycp": True, "s2mycp2": True, "s2mycp3": True,
                "smycpnt1": False})
            self.assertEqual(len(rs.descriptionErrors), 1)

            res2 = json.loads(self._cf.dp.GetCommandVariable("VARS"))
            self.assertTrue(val["MntGrp"] in self._cf.dp.availableSelections())
            sed = json.loads(self._cf.dp.selections([val["MntGrp"]])[0])
            self.assertEqual(len(sed.keys()), len(self._keys))
            for key, vl in self._keys:
                self.assertTrue(key in sed.keys())
                if key in val:
                    self.assertEqual(sed[key], val[key])
                elif key == 'ComponentPreselection':
                    self.assertEqual(set(json.loads(sed[key])),
                                     set(json.loads(res)))
                elif key == 'PreselectedDataSources':
                    self.assertEqual(set(json.loads(sed[key])),
                                     set(poolchannels))
                else:
                    self.assertEqual(sed[key], vl)
        finally:
            simps2.tearDown()

    ## test
    # \brief It tests default settings
    def test_preselectComponents_2wds_notangodspool_alias(self):
        fun = sys._getframe().f_code.co_name
        print "Run: %s.%s() " % (self.__class__.__name__, fun)
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
            db = PyTango.Database()
            simps2.setUp()
            db.put_device_alias(arr[0]["full_name"], arr[0]["name"])
            db.put_device_property(self._ms.ms.keys()[0],
                                   {'PoolNames': self._pool.dp.name()})

            self._ms.dps[self._ms.ms.keys()[0]].Init()
            rs = self.openRecSelector()
            rs.configDevice = val["ConfigDevice"]
            rs.door = val["Door"]
            rs.mntGrp = val["MntGrp"]
            rs.writerDevice = val["WriterDevice"]

            self._ms.dps[self._ms.ms.keys()[0]].Init()

            channelerrors = []
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

            pool = self._pool.dp
            pool.AcqChannelList = [json.dumps(a) for a in arr]

            self._simps.dp.ChangeValueType("ScalarShort")
            self._simps.dp.Value = 43

            cnf = json.loads(rs.profileConfiguration)
            cnf["PreselectedDataSources"] = json.dumps(poolchannels)
            cnf["ComponentPreselection"] = json.dumps(componentgroup)
            rs.profileConfiguration = json.dumps(cnf)
            rs.preselectComponents()
            res = self.value(rs, "ComponentPreselection")

            self.myAssertDict(json.loads(res), {
                "smycp": True, "smycp2": True, "smycp3": True,
                "s2mycp": True, "s2mycp2": True, "s2mycp3": True,
                "smycpnt1": True})
            self.assertTrue(not rs.descriptionErrors)

            res2 = json.loads(self._cf.dp.GetCommandVariable("VARS"))
            self.assertTrue(val["MntGrp"] in self._cf.dp.availableSelections())
            sed = json.loads(self._cf.dp.selections([val["MntGrp"]])[0])
            self.assertEqual(len(sed.keys()), len(self._keys))
            for key, vl in self._keys:
                self.assertTrue(key in sed.keys())
                if key in val:
                    self.assertEqual(sed[key], val[key])
                elif key == 'ComponentPreselection':
                    self.assertEqual(set(json.loads(sed[key])),
                                     set(json.loads(res)))
                elif key == 'PreselectedDataSources':
                    self.assertEqual(set(json.loads(sed[key])),
                                     set(poolchannels))
                else:
                    self.assertEqual(sed[key], vl)
        finally:
            db.delete_device_alias(arr[0]["name"])
            simps2.tearDown()

    ## test
    # \brief It tests default settings
    def test_preselectComponents_2wds_notangodspool_alias_bl(self):
        fun = sys._getframe().f_code.co_name
        print "Run: %s.%s() " % (self.__class__.__name__, fun)
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
            db = PyTango.Database()
            simps2.setUp()
            db.put_device_alias(arr[0]["full_name"], arr[0]["name"])
            db.put_device_property(self._ms.ms.keys()[0],
                                   {'PoolNames': self._pool.dp.name()})

            self._ms.dps[self._ms.ms.keys()[0]].Init()
            rs = self.openRecSelector()
            self.setProp(rs, "poolBlacklist",
                         [self._pool.dp.name()])
            rs.configDevice = val["ConfigDevice"]
            rs.door = val["Door"]
            rs.mntGrp = val["MntGrp"]
            rs.writerDevice = val["WriterDevice"]

            self._ms.dps[self._ms.ms.keys()[0]].Init()

            channelerrors = []
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

            pool = self._pool.dp
            pool.AcqChannelList = [json.dumps(a) for a in arr]

            self._simps.dp.ChangeValueType("ScalarShort")
            self._simps.dp.Value = 43

            cnf = json.loads(rs.profileConfiguration)
            cnf["PreselectedDataSources"] = json.dumps(poolchannels)
            cnf["ComponentPreselection"] = json.dumps(componentgroup)
            rs.profileConfiguration = json.dumps(cnf)
            rs.preselectComponents()
            res = self.value(rs, "ComponentPreselection")

            self.myAssertDict(json.loads(res), {
                "smycp": True, "smycp2": True, "smycp3": True,
                "s2mycp": True, "s2mycp2": True, "s2mycp3": True,
                "smycpnt1": False})
            self.assertTrue(rs.descriptionErrors)

            res2 = json.loads(self._cf.dp.GetCommandVariable("VARS"))
            self.assertTrue(val["MntGrp"] in self._cf.dp.availableSelections())
            sed = json.loads(self._cf.dp.selections([val["MntGrp"]])[0])
            self.assertEqual(len(sed.keys()), len(self._keys))
            for key, vl in self._keys:
                self.assertTrue(key in sed.keys())
                if key in val:
                    self.assertEqual(sed[key], val[key])
                elif key == 'ComponentPreselection':
                    self.assertEqual(set(json.loads(sed[key])),
                                     set(json.loads(res)))
                elif key == 'PreselectedDataSources':
                    self.assertEqual(set(json.loads(sed[key])),
                                     set(poolchannels))
                else:
                    self.assertEqual(sed[key], vl)
        finally:
            db.delete_device_alias(arr[0]["name"])
            simps2.tearDown()

    ## test
    # \brief It tests default settings
    def test_preselectComponents_2wds_notangodspool_alias_value(self):
        fun = sys._getframe().f_code.co_name
        print "Run: %s.%s() " % (self.__class__.__name__, fun)
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
            db = PyTango.Database()
            simps2.setUp()

            db.put_device_alias(arr[0]["full_name"], arr[0]["name"])
            db.put_device_property(self._ms.ms.keys()[0],
                                   {'PoolNames': self._pool.dp.name()})

            self._ms.dps[self._ms.ms.keys()[0]].Init()
            rs = self.openRecSelector()
            rs.configDevice = val["ConfigDevice"]
            rs.door = val["Door"]
            rs.mntGrp = val["MntGrp"]
            rs.writerDevice = val["WriterDevice"]

            self._ms.dps[self._ms.ms.keys()[0]].Init()

            channelerrors = []
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

            pool = self._pool.dp
            pool.AcqChannelList = [json.dumps(a) for a in arr]

            cnf = json.loads(rs.profileConfiguration)
            cnf["PreselectedDataSources"] = json.dumps(poolchannels)
            cnf["ComponentPreselection"] = json.dumps(componentgroup)
            rs.profileConfiguration = json.dumps(cnf)
            rs.preselectComponents()
            res = self.value(rs, "ComponentPreselection")

            self.myAssertDict(json.loads(res), {
                "smycp": True, "smycp2": True, "smycp3": True,
                "s2mycp": True, "s2mycp2": True, "s2mycp3": True,
                "smycpnt1": True})
            self.assertTrue(not rs.descriptionErrors)

    #        print self._cf.dp.GetCommandVariable("COMMANDS")
            res2 = json.loads(self._cf.dp.GetCommandVariable("VARS"))
            self.assertTrue(val["MntGrp"] in self._cf.dp.availableSelections())
            sed = json.loads(self._cf.dp.selections([val["MntGrp"]])[0])
            self.assertEqual(len(sed.keys()), len(self._keys))
            for key, vl in self._keys:
                self.assertTrue(key in sed.keys())
                if key in val:
                    self.assertEqual(sed[key], val[key])
                elif key == 'ComponentPreselection':
                    self.assertEqual(set(json.loads(sed[key])),
                                     set(json.loads(res)))
                elif key == 'PreselectedDataSources':
                    self.assertEqual(set(json.loads(sed[key])),
                                     set(poolchannels))
                else:
                    self.assertEqual(sed[key], vl)
        finally:
            db.delete_device_alias(arr[0]["name"])
            simps2.tearDown()

    ## test
    # \brief It tests default settings
    def test_preselectComponents_2wds_notangodspool_alias_value_bl(self):
        fun = sys._getframe().f_code.co_name
        print "Run: %s.%s() " % (self.__class__.__name__, fun)
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
            db = PyTango.Database()
            simps2.setUp()

            db.put_device_alias(arr[0]["full_name"], arr[0]["name"])
            db.put_device_property(self._ms.ms.keys()[0],
                                   {'PoolNames': self._pool.dp.name()})

            self._ms.dps[self._ms.ms.keys()[0]].Init()
            rs = self.openRecSelector()
            self.setProp(rs, "poolBlacklist",
                         [self._pool.dp.name()])
            rs.configDevice = val["ConfigDevice"]
            rs.door = val["Door"]
            rs.mntGrp = val["MntGrp"]
            rs.writerDevice = val["WriterDevice"]

            self._ms.dps[self._ms.ms.keys()[0]].Init()

            channelerrors = []
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

            pool = self._pool.dp
            pool.AcqChannelList = [json.dumps(a) for a in arr]

            cnf = json.loads(rs.profileConfiguration)
            cnf["PreselectedDataSources"] = json.dumps(poolchannels)
            cnf["ComponentPreselection"] = json.dumps(componentgroup)
            rs.profileConfiguration = json.dumps(cnf)
            rs.preselectComponents()
            res = self.value(rs, "ComponentPreselection")

            self.myAssertDict(json.loads(res), {
                "smycp": True, "smycp2": True, "smycp3": True,
                "s2mycp": True, "s2mycp2": True, "s2mycp3": True,
                "smycpnt1": False})
            self.assertTrue(rs.descriptionErrors)

    #        print self._cf.dp.GetCommandVariable("COMMANDS")
            res2 = json.loads(self._cf.dp.GetCommandVariable("VARS"))
            self.assertTrue(val["MntGrp"] in self._cf.dp.availableSelections())
            sed = json.loads(self._cf.dp.selections([val["MntGrp"]])[0])
            self.assertEqual(len(sed.keys()), len(self._keys))
            for key, vl in self._keys:
                self.assertTrue(key in sed.keys())
                if key in val:
                    self.assertEqual(sed[key], val[key])
                elif key == 'ComponentPreselection':
                    self.assertEqual(set(json.loads(sed[key])),
                                     set(json.loads(res)))
                elif key == 'PreselectedDataSources':
                    self.assertEqual(set(json.loads(sed[key])),
                                     set(poolchannels))
                else:
                    self.assertEqual(sed[key], vl)
        finally:
            db.delete_device_alias(arr[0]["name"])
            simps2.tearDown()

    ## test
    # \brief It tests default settings
    def test_preselectComponents_2wds_notangodspool_alias_novalue(self):
        fun = sys._getframe().f_code.co_name
        print "Run: %s.%s() " % (self.__class__.__name__, fun)
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
            db = PyTango.Database()
            simps2.setUp()

            db.put_device_alias(arr[0]["full_name"], arr[0]["name"])
            db.put_device_property(self._ms.ms.keys()[0],
                                   {'PoolNames': self._pool.dp.name()})

            self._ms.dps[self._ms.ms.keys()[0]].Init()
            rs = self.openRecSelector()
            rs.configDevice = val["ConfigDevice"]
            rs.door = val["Door"]
            rs.mntGrp = val["MntGrp"]
            rs.writerDevice = val["WriterDevice"]

            self._ms.dps[self._ms.ms.keys()[0]].Init()

            channelerrors = []
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

            pool = self._pool.dp
            pool.AcqChannelList = [json.dumps(a) for a in arr]

            cnf = json.loads(rs.profileConfiguration)
            cnf["PreselectedDataSources"] = json.dumps(poolchannels)
            cnf["ComponentPreselection"] = json.dumps(componentgroup)
            rs.profileConfiguration = json.dumps(cnf)
            rs.preselectComponents()
            res = self.value(rs, "ComponentPreselection")

            self.myAssertDict(json.loads(res), {
                "smycp": True, "smycp2": True, "smycp3": True,
                "s2mycpnt1": False})
            self.assertEqual(len(rs.descriptionErrors), 1)

    #        print self._cf.dp.GetCommandVariable("COMMANDS")
            res2 = json.loads(self._cf.dp.GetCommandVariable("VARS"))
            self.assertTrue(val["MntGrp"] in self._cf.dp.availableSelections())
            sed = json.loads(self._cf.dp.selections([val["MntGrp"]])[0])
            self.assertEqual(len(sed.keys()), len(self._keys))
            for key, vl in self._keys:
                self.assertTrue(key in sed.keys())
                if key in val:
                    self.assertEqual(sed[key], val[key])
                elif key == 'ComponentPreselection':
                    self.assertEqual(set(json.loads(sed[key])),
                                     set(json.loads(res)))
                elif key == 'PreselectedDataSources':
                    self.assertEqual(set(json.loads(sed[key])),
                                     set(poolchannels))
                else:
                    self.assertEqual(sed[key], vl)
        finally:
            db.delete_device_alias(arr[0]["name"])
            simps2.tearDown()

    ## test
    # \brief It tests default settings
    def test_preselectComponents_2wds_notangodspool_alias_novalue_bl(self):
        fun = sys._getframe().f_code.co_name
        print "Run: %s.%s() " % (self.__class__.__name__, fun)
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
            db = PyTango.Database()
            simps2.setUp()

            db.put_device_alias(arr[0]["full_name"], arr[0]["name"])
            db.put_device_property(self._ms.ms.keys()[0],
                                   {'PoolNames': self._pool.dp.name()})

            self._ms.dps[self._ms.ms.keys()[0]].Init()
            rs = self.openRecSelector()
            self.setProp(rs, "poolBlacklist",
                         [self._pool.dp.name()])
            rs.configDevice = val["ConfigDevice"]
            rs.door = val["Door"]
            rs.mntGrp = val["MntGrp"]
            rs.writerDevice = val["WriterDevice"]

            self._ms.dps[self._ms.ms.keys()[0]].Init()

            channelerrors = []
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

            pool = self._pool.dp
            pool.AcqChannelList = [json.dumps(a) for a in arr]

            cnf = json.loads(rs.profileConfiguration)
            cnf["PreselectedDataSources"] = json.dumps(poolchannels)
            cnf["ComponentPreselection"] = json.dumps(componentgroup)
            rs.profileConfiguration = json.dumps(cnf)
            rs.preselectComponents()
            res = self.value(rs, "ComponentPreselection")

            self.myAssertDict(json.loads(res), {
                "smycp": True, "smycp2": True, "smycp3": True,
                "s2mycpnt1": False})
            self.assertEqual(len(rs.descriptionErrors), 1)

    #        print self._cf.dp.GetCommandVariable("COMMANDS")
            res2 = json.loads(self._cf.dp.GetCommandVariable("VARS"))
            self.assertTrue(val["MntGrp"] in self._cf.dp.availableSelections())
            sed = json.loads(self._cf.dp.selections([val["MntGrp"]])[0])
            self.assertEqual(len(sed.keys()), len(self._keys))
            for key, vl in self._keys:
                self.assertTrue(key in sed.keys())
                if key in val:
                    self.assertEqual(sed[key], val[key])
                elif key == 'ComponentPreselection':
                    self.assertEqual(set(json.loads(sed[key])),
                                     set(json.loads(res)))
                elif key == 'PreselectedDataSources':
                    self.assertEqual(set(json.loads(sed[key])),
                                     set(poolchannels))
                else:
                    self.assertEqual(sed[key], vl)
        finally:
            db.delete_device_alias(arr[0]["name"])
            simps2.tearDown()

    ## test
    # \brief It tests default settings
    def test_preselectComponents_2wds_nocomponents(self):
        fun = sys._getframe().f_code.co_name
        print "Run: %s.%s() " % (self.__class__.__name__, fun)
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
            db = PyTango.Database()
            simps2.setUp()

            self._ms.dps[self._ms.ms.keys()[0]].Init()
            rs = self.openRecSelector()
            rs.configDevice = val["ConfigDevice"]
            rs.door = val["Door"]
            rs.mntGrp = val["MntGrp"]
            rs.writerDevice = val["WriterDevice"]

            self._ms.dps[self._ms.ms.keys()[0]].Init()

            channelerrors = []
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

            cnf = json.loads(rs.profileConfiguration)
            cnf["PreselectedDataSources"] = json.dumps(poolchannels)
            cnf["ComponentPreselection"] = json.dumps(componentgroup)
            rs.profileConfiguration = json.dumps(cnf)
            rs.preselectComponents()
            res = self.value(rs, "ComponentPreselection")

            self.myAssertDict(json.loads(res), {
                "smycp": True, "smycp2": True, "smycp3": True,
                "s2mycp": False, "s2mycp2": False, "s2mycp3": False})
            self.assertEqual(len(rs.descriptionErrors), 3)

    #        print self._cf.dp.GetCommandVariable("COMMANDS")
            res2 = json.loads(self._cf.dp.GetCommandVariable("VARS"))
            self.assertTrue(val["MntGrp"] in self._cf.dp.availableSelections())
            sed = json.loads(self._cf.dp.selections([val["MntGrp"]])[0])
            self.assertEqual(len(sed.keys()), len(self._keys))
            for key, vl in self._keys:
                self.assertTrue(key in sed.keys())
                if key in val:
                    self.assertEqual(sed[key], val[key])
                elif key == 'ComponentPreselection':
                    self.assertEqual(set(json.loads(sed[key])),
                                     set(json.loads(res)))
                elif key == 'PreselectedDataSources':
                    self.assertEqual(set(json.loads(sed[key])),
                                     set(poolchannels))
                else:
                    self.assertEqual(sed[key], vl)
        finally:
            simps2.tearDown()

    ## resetPreselectedComponents test
    # \brief It tests default settings
    def test_resetPreselectedComponents_simple(self):
        fun = sys._getframe().f_code.co_name
        print "Run: %s.%s() " % (self.__class__.__name__, fun)
        val = {"ConfigDevice": self._cf.dp.name(),
               "WriterDevice": self._wr.dp.name(),
               "Door": 'doortestp09/testts/t1r228',
               "MntGrp": 'nxsmntgrp'}

        db = PyTango.Database()
        self._ms.dps[self._ms.ms.keys()[0]].Init()
        rs = self.openRecSelector()
        rs.configDevice = val["ConfigDevice"]
        rs.door = val["Door"]
        rs.mntGrp = val["MntGrp"]

        self._ms.dps[self._ms.ms.keys()[0]].Init()

        channelerrors = []
        self.dump(rs)
        rs.resetPreselectedComponents()
        sed2 = json.loads(self._cf.dp.selections([val["MntGrp"]])[0])
        res = self.value(rs, "ComponentPreselection")
        self.assertEqual(res, '{}')
        rs.profileConfiguration = '{}'
        rs.configDevice = val["ConfigDevice"]
        rs.door = val["Door"]
        rs.mntGrp = val["MntGrp"]
        rs.fetchProfile()
        res = self.value(rs, "ComponentPreselection")
        self.assertEqual(res, '{}')

        self.compareToDump(rs, ["ComponentPreselection"])

    ## resetPreselectedComponents test
    # \brief It tests default settings
    def test_resetPreselectedComponents_withcf(self):
        fun = sys._getframe().f_code.co_name
        print "Run: %s.%s() " % (self.__class__.__name__, fun)
        val = {"ConfigDevice": self._cf.dp.name(),
               "WriterDevice": self._wr.dp.name(),
               "Door": 'doortestp09/testts/t1r228',
               "MntGrp": 'nxsmntgrp'}

        db = PyTango.Database()
        self._ms.dps[self._ms.ms.keys()[0]].Init()
        rs = self.openRecSelector()
        rs.configDevice = val["ConfigDevice"]
        rs.door = val["Door"]
        rs.mntGrp = val["MntGrp"]

        self._ms.dps[self._ms.ms.keys()[0]].Init()

        channelerrors = []
        poolchannels = []
        componentgroup = {}

        self._cf.dp.SetCommandVariable(["CPDICT", json.dumps(self.mycps)])
        self._cf.dp.SetCommandVariable(["DSDICT", json.dumps(self.mydss)])

        self.dump(rs)
        rs.resetPreselectedComponents()
        sed2 = json.loads(self._cf.dp.selections([val["MntGrp"]])[0])
        res = self.value(rs, "ComponentPreselection")
        self.compareToDump(rs, ["ComponentPreselection"])

        self.assertEqual(res, '{}')
        self.assertEqual(componentgroup, {})
        self.assertEqual(channelerrors, [])
        print self._cf.dp.GetCommandVariable("COMMANDS")

        rs.profileConfiguration = '{}'
        rs.configDevice = val["ConfigDevice"]
        rs.door = val["Door"]
        rs.mntGrp = val["MntGrp"]
        rs.fetchProfile()
        res = self.value(rs, "ComponentPreselection")
        self.assertEqual(res, '{}')

    ## test
    # \brief It tests default settings
    def test_resetPreselectedComponents_withcf_cps(self):
        fun = sys._getframe().f_code.co_name
        print "Run: %s.%s() " % (self.__class__.__name__, fun)
        val = {"ConfigDevice": self._cf.dp.name(),
               "WriterDevice": self._wr.dp.name(),
               "Door": 'doortestp09/testts/t1r228',
               "MntGrp": 'nxsmntgrp'}

        channelerrors = []
        poolchannels = ["mycp"]
        componentgroup = {"mycp": False}

        self._cf.dp.SetCommandVariable(["CPDICT", json.dumps(self.mycps)])
        self._cf.dp.SetCommandVariable(["DSDICT", json.dumps(self.mydss)])

        db = PyTango.Database()
        self._ms.dps[self._ms.ms.keys()[0]].Init()
        rs = self.openRecSelector()
        self.setProp(rs, "defaultPreselectedComponents",
                     list(componentgroup.keys()))
        rs.configDevice = val["ConfigDevice"]
        rs.door = val["Door"]
        rs.mntGrp = val["MntGrp"]
        rs.writerDevice = val["WriterDevice"]

        self._ms.dps[self._ms.ms.keys()[0]].Init()

        cnf = json.loads(rs.profileConfiguration)
        cnf["PreselectedDataSources"] = json.dumps(poolchannels)
        rs.profileConfiguration = json.dumps(cnf)
        # rs.defaultPreselectedComponents = list(componentgroup.keys())
        self.dump(rs)
        sed1 = json.loads(self._cf.dp.selections([val["MntGrp"]])[0])
        rs.resetPreselectedComponents()
        print "VALUE"
        res = self.value(rs, "ComponentPreselection")
        print "VALUE 2"
        self.compareToDump(rs, ["ComponentPreselection"])
        print "RES", res
        self.myAssertDict(json.loads(res), {"mycp": True})
        self.assertEqual(channelerrors, [])

        self.assertTrue(val["MntGrp"] in self._cf.dp.availableSelections())
        sed = json.loads(self._cf.dp.selections([val["MntGrp"]])[0])
        self.assertEqual(len(sed.keys()), len(self._keys))
        for key, vl in self._keys:
            self.assertTrue(key in sed.keys())
            self.assertTrue(key in sed1.keys())
            if key in val:
                self.assertEqual(sed[key], val[key])
                self.assertEqual(sed1[key], val[key])
            elif key == 'ComponentPreselection':
                self.myAssertDict(json.loads(sed[key]), json.loads(res))
                self.assertNotEqual(sed1[key], res)
            elif key == 'PreselectedDataSources':
                self.assertEqual(set(json.loads(sed[key])), set(poolchannels))
                self.assertEqual(set(json.loads(sed1[key])), set(poolchannels))
            else:
                self.assertEqual(sed[key], vl)
                self.assertEqual(sed1[key], vl)

    ## test
    # \brief It tests default settings
    def test_resetPreselectedComponents_withcf_cps_t(self):
        fun = sys._getframe().f_code.co_name
        print "Run: %s.%s() " % (self.__class__.__name__, fun)
        val = {"ConfigDevice": self._cf.dp.name(),
               "WriterDevice": self._wr.dp.name(),
               "Door": 'doortestp09/testts/t1r228',
               "MntGrp": 'nxsmntgrp'}

        db = PyTango.Database()
        self._ms.dps[self._ms.ms.keys()[0]].Init()
        self._ms.dps[self._ms.ms.keys()[0]].Init()

        channelerrors = []
        poolchannels = ["mycp"]
        componentgroup = {"mycp": True}

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
        cnf["PreselectedDataSources"] = json.dumps(poolchannels)
        rs.profileConfiguration = json.dumps(cnf)
        self.dump(rs)
        sed1 = json.loads(self._cf.dp.selections([val["MntGrp"]])[0])
        rs.resetPreselectedComponents()
        sed2 = json.loads(self._cf.dp.selections([val["MntGrp"]])[0])
        self.compareToDump(rs, ["ComponentPreselection"])
        res = self.value(rs, "ComponentPreselection")
        self.myAssertDict(json.loads(res), {"mycp": True})
        self.assertEqual(channelerrors, [])

        self.assertTrue(val["MntGrp"] in self._cf.dp.availableSelections())

    ## test
    # \brief It tests default settings
    def test_resetPreselectedComponents_withcf_nocps(self):
        fun = sys._getframe().f_code.co_name
        print "Run: %s.%s() " % (self.__class__.__name__, fun)
        val = {"ConfigDevice": self._cf.dp.name(),
               "WriterDevice": self._wr.dp.name(),
               "Door": 'doortestp09/testts/t1r228',
               "MntGrp": 'nxsmntgrp'}

        db = PyTango.Database()
        self._ms.dps[self._ms.ms.keys()[0]].Init()

        self._ms.dps[self._ms.ms.keys()[0]].Init()

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
        cnf["PreselectedDataSources"] = json.dumps(poolchannels)
        rs.profileConfiguration = json.dumps(cnf)
        self.dump(rs)
        sed1 = json.loads(self._cf.dp.selections([val["MntGrp"]])[0])
        rs.resetPreselectedComponents()
        sed2 = json.loads(self._cf.dp.selections([val["MntGrp"]])[0])
        self.compareToDump(rs, ["ComponentPreselection"])
        res = self.value(rs, "ComponentPreselection")

        self.myAssertDict(json.loads(res), {})
        self.assertEqual(channelerrors, [])

        print self._cf.dp.GetCommandVariable("COMMANDS")

        self.assertTrue(val["MntGrp"] in self._cf.dp.availableSelections())

    ## test
    # \brief It tests default settings
    def test_resetPreselectedComponents_withcf_nochnnel(self):
        fun = sys._getframe().f_code.co_name
        print "Run: %s.%s() " % (self.__class__.__name__, fun)
        val = {"ConfigDevice": self._cf.dp.name(),
               "WriterDevice": self._wr.dp.name(),
               "Door": 'doortestp09/testts/t1r228',
               "MntGrp": 'nxsmntgrp'}

        db = PyTango.Database()
        self._ms.dps[self._ms.ms.keys()[0]].Init()

        channelerrors = []
        poolchannels = []
        componentgroup = {"mycp": False}

        self._cf.dp.SetCommandVariable(["CPDICT", json.dumps(self.mycps)])
        self._cf.dp.SetCommandVariable(["DSDICT", json.dumps(self.mydss)])
        rs = self.openRecSelector()
        self.setProp(rs, "defaultPreselectedComponents",
                     list(componentgroup.keys()))
        rs.configDevice = val["ConfigDevice"]
        rs.door = val["Door"]
        rs.mntGrp = val["MntGrp"]
        rs.writerDevice = val["WriterDevice"]

        self._ms.dps[self._ms.ms.keys()[0]].Init()

        cnf = json.loads(rs.profileConfiguration)
        cnf["PreselectedDataSources"] = json.dumps(poolchannels)
        rs.profileConfiguration = json.dumps(cnf)
        self.dump(rs)
        sed1 = json.loads(self._cf.dp.selections([val["MntGrp"]])[0])
        rs.resetPreselectedComponents()
        res = self.value(rs, "ComponentPreselection")
        self.compareToDump(rs, ["ComponentPreselection"])

        self.myAssertDict(json.loads(res), {"mycp": True})
        self.assertEqual(channelerrors, [])

        print self._cf.dp.GetCommandVariable("COMMANDS")
        self.assertTrue(val["MntGrp"] in self._cf.dp.availableSelections())
        sed = json.loads(self._cf.dp.selections([val["MntGrp"]])[0])
        print sed
        self.assertEqual(len(sed.keys()), len(self._keys))
        for key, vl in self._keys:
            self.assertTrue(key in sed.keys())
            if key in val:
                self.assertEqual(sed[key], val[key])
                self.assertEqual(sed1[key], val[key])
            elif key == 'ComponentPreselection':
                self.myAssertDict(json.loads(sed[key]),
                                  json.loads(res))
                self.assertNotEqual(sed1[key], res)
            elif key == 'PreselectedDataSources':
                self.assertEqual(set(json.loads(sed[key])), set(poolchannels))
                self.assertEqual(set(json.loads(sed1[key])), set(poolchannels))
            else:
                self.assertEqual(sed[key], vl)
                self.assertEqual(sed1[key], vl)

    ## test
    # \brief It tests default settings
    def test_resetPreselectedComponents_withcf_nochnnel_t(self):
        fun = sys._getframe().f_code.co_name
        print "Run: %s.%s() " % (self.__class__.__name__, fun)
        val = {"ConfigDevice": self._cf.dp.name(),
               "WriterDevice": self._wr.dp.name(),
               "Door": 'doortestp09/testts/t1r228',
               "MntGrp": 'nxsmntgrp'}

        db = PyTango.Database()
        self._ms.dps[self._ms.ms.keys()[0]].Init()
        channelerrors = []
        poolchannels = []
        componentgroup = {"mycp": True}

        self._cf.dp.SetCommandVariable(["CPDICT", json.dumps(self.mycps)])
        self._cf.dp.SetCommandVariable(["DSDICT", json.dumps(self.mydss)])
        rs = self.openRecSelector()
        self.setProp(rs, "defaultPreselectedComponents",
                     list(componentgroup.keys()))
        rs.configDevice = val["ConfigDevice"]
        rs.door = val["Door"]
        rs.mntGrp = val["MntGrp"]
        rs.writerDevice = val["WriterDevice"]

        self._ms.dps[self._ms.ms.keys()[0]].Init()

        cnf = json.loads(rs.profileConfiguration)
        cnf["PreselectedDataSources"] = json.dumps(poolchannels)
        rs.profileConfiguration = json.dumps(cnf)
        self.dump(rs)
        sed1 = json.loads(self._cf.dp.selections([val["MntGrp"]])[0])
        rs.resetPreselectedComponents()
        sed2 = json.loads(self._cf.dp.selections([val["MntGrp"]])[0])
        res = self.value(rs, "ComponentPreselection")
        self.compareToDump(rs, ["ComponentPreselection"])

        self.myAssertDict(json.loads(res), {"mycp": True})
        self.assertEqual(channelerrors, [])

        self.assertTrue(val["MntGrp"] in self._cf.dp.availableSelections())

    ## test
    # \brief It tests default settings
    def test_resetPreselectedComponents_wds_t(self):
        fun = sys._getframe().f_code.co_name
        print "Run: %s.%s() " % (self.__class__.__name__, fun)
        val = {"ConfigDevice": self._cf.dp.name(),
               "WriterDevice": self._wr.dp.name(),
               "Door": 'doortestp09/testts/t1r228',
               "MntGrp": 'nxsmntgrp'}

        db = PyTango.Database()
        self._ms.dps[self._ms.ms.keys()[0]].Init()
        channelerrors = []
        poolchannels = []
        componentgroup = {"smycp": True}

        self._cf.dp.SetCommandVariable(["CPDICT", json.dumps(self.smycps)])
        self._cf.dp.SetCommandVariable(["DSDICT", json.dumps(self.smydss)])
        rs = self.openRecSelector()
        self.setProp(rs, "defaultPreselectedComponents",
                     list(componentgroup.keys()))
        rs.configDevice = val["ConfigDevice"]
        rs.door = val["Door"]
        rs.mntGrp = val["MntGrp"]
        rs.writerDevice = val["WriterDevice"]

        self._ms.dps[self._ms.ms.keys()[0]].Init()

        cnf = json.loads(rs.profileConfiguration)
        cnf["PreselectedDataSources"] = json.dumps(poolchannels)
        rs.profileConfiguration = json.dumps(cnf)
        self.dump(rs)
        sed1 = json.loads(self._cf.dp.selections([val["MntGrp"]])[0])
        rs.resetPreselectedComponents()
        sed2 = json.loads(self._cf.dp.selections([val["MntGrp"]])[0])
        res = self.value(rs, "ComponentPreselection")
        self.compareToDump(rs, ["ComponentPreselection"])

        self.myAssertDict(json.loads(res), {"smycp": True})
        self.assertEqual(channelerrors, [])

        self.assertTrue(val["MntGrp"] in self._cf.dp.availableSelections())

    ## test
    # \brief It tests default settings
    def test_resetPreselectedComponents_wds(self):
        fun = sys._getframe().f_code.co_name
        print "Run: %s.%s() " % (self.__class__.__name__, fun)
        val = {"ConfigDevice": self._cf.dp.name(),
               "WriterDevice": self._wr.dp.name(),
               "Door": 'doortestp09/testts/t1r228',
               "MntGrp": 'nxsmntgrp'}

        db = PyTango.Database()
        self._ms.dps[self._ms.ms.keys()[0]].Init()

        channelerrors = []
        poolchannels = []
        componentgroup = {"smycp": False}

        self._cf.dp.SetCommandVariable(["CPDICT", json.dumps(self.smycps)])
        self._cf.dp.SetCommandVariable(["DSDICT", json.dumps(self.smydss)])

        rs = self.openRecSelector()
        self.setProp(rs, "defaultPreselectedComponents",
                     list(componentgroup.keys()))
        rs.configDevice = val["ConfigDevice"]
        rs.door = val["Door"]
        rs.mntGrp = val["MntGrp"]
        rs.writerDevice = val["WriterDevice"]

        self._ms.dps[self._ms.ms.keys()[0]].Init()
        cnf = json.loads(rs.profileConfiguration)
        cnf["PreselectedDataSources"] = json.dumps(poolchannels)
        rs.profileConfiguration = json.dumps(cnf)
        self.dump(rs)
        sed1 = json.loads(self._cf.dp.selections([val["MntGrp"]])[0])
        rs.resetPreselectedComponents()
        res = self.value(rs, "ComponentPreselection")
        self.compareToDump(rs, ["ComponentPreselection"])

        self.myAssertDict(json.loads(res), {"smycp": True})
        self.assertEqual(channelerrors, [])

        self.assertTrue(val["MntGrp"] in self._cf.dp.availableSelections())
        sed = json.loads(self._cf.dp.selections([val["MntGrp"]])[0])
        self.assertEqual(len(sed.keys()), len(self._keys))
        for key, vl in self._keys:
            self.assertTrue(key in sed.keys())
            if key in val:
                self.assertEqual(sed[key], val[key])
                self.assertEqual(sed1[key], val[key])
            elif key == 'ComponentPreselection':
                self.myAssertDict(json.loads(sed[key]),
                                  json.loads(res))
                self.assertNotEqual(sed1[key], res)
            elif key == 'PreselectedDataSources':
                self.assertEqual(set(json.loads(sed[key])),
                                 set(poolchannels))
                self.assertEqual(set(json.loads(sed1[key])),
                                 set(poolchannels))
            else:
                self.assertEqual(sed[key], vl)
                self.assertEqual(sed1[key], vl)

    ## test
    # \brief It tests default settings
    def test_resetPreselectedComponents_wds2(self):
        fun = sys._getframe().f_code.co_name
        print "Run: %s.%s() " % (self.__class__.__name__, fun)
        val = {"ConfigDevice": self._cf.dp.name(),
               "WriterDevice": self._wr.dp.name(),
               "Door": 'doortestp09/testts/t1r228',
               "MntGrp": 'nxsmntgrp'}

        db = PyTango.Database()
        self._ms.dps[self._ms.ms.keys()[0]].Init()

        channelerrors = []
        poolchannels = []
        componentgroup = {"smycp": False, "smycp2": False, "smycp3": False}

        self._cf.dp.SetCommandVariable(["CPDICT", json.dumps(self.smycps)])
        self._cf.dp.SetCommandVariable(["DSDICT", json.dumps(self.smydss)])
        rs = self.openRecSelector()
        self.setProp(rs, "defaultPreselectedComponents",
                     list(componentgroup.keys()))
        rs.configDevice = val["ConfigDevice"]
        rs.door = val["Door"]
        rs.mntGrp = val["MntGrp"]
        rs.writerDevice = val["WriterDevice"]

        self._ms.dps[self._ms.ms.keys()[0]].Init()

        cnf = json.loads(rs.profileConfiguration)
        cnf["PreselectedDataSources"] = json.dumps(poolchannels)
        rs.profileConfiguration = json.dumps(cnf)
        self.dump(rs)
        sed1 = json.loads(self._cf.dp.selections([val["MntGrp"]])[0])
        rs.resetPreselectedComponents()
        res = self.value(rs, "ComponentPreselection")
        self.compareToDump(rs, ["ComponentPreselection"])

        self.myAssertDict(json.loads(res), {
            "smycp": True, "smycp2": True, "smycp3": True})
        self.assertEqual(channelerrors, [])

        res2 = json.loads(self._cf.dp.GetCommandVariable("VARS"))
        self.assertTrue(val["MntGrp"] in self._cf.dp.availableSelections())
        sed = json.loads(self._cf.dp.selections([val["MntGrp"]])[0])
        self.assertEqual(len(sed.keys()), len(self._keys))
        for key, vl in self._keys:
            self.assertTrue(key in sed.keys())
            if key in val:
                self.assertEqual(sed[key], val[key])
                self.assertEqual(sed1[key], val[key])
            elif key == 'ComponentPreselection':
                self.myAssertDict(json.loads(sed[key]),
                                  json.loads(res))
                self.assertNotEqual(sed1[key], res)
            elif key == 'PreselectedDataSources':
                self.assertEqual(set(json.loads(sed[key])),
                                 set(poolchannels))
                self.assertEqual(set(json.loads(sed1[key])),
                                 set(poolchannels))
            else:
                self.assertEqual(sed[key], vl)
                self.assertEqual(sed1[key], vl)

    ## test
    # \brief It tests default settings
    def test_resetPreselectedComponents_2wds(self):
        fun = sys._getframe().f_code.co_name
        print "Run: %s.%s() " % (self.__class__.__name__, fun)
        val = {"ConfigDevice": self._cf.dp.name(),
               "WriterDevice": self._wr.dp.name(),
               "Door": 'doortestp09/testts/t1r228',
               "MntGrp": 'nxsmntgrp'}
        simps2 = TestServerSetUp.TestServerSetUp(
            "ttestp09/testts/t2r228", "S2")
        try:
            simps2.setUp()

            db = PyTango.Database()
            self._ms.dps[self._ms.ms.keys()[0]].Init()

            channelerrors = []
            poolchannels = []
            componentgroup = {"smycp": False, "smycp2": False, "smycp3": False,
                              "s2mycp": False, "s2mycp2": False,
                              "s2mycp3": False}

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

            self._ms.dps[self._ms.ms.keys()[0]].Init()

            cnf = json.loads(rs.profileConfiguration)
            cnf["PreselectedDataSources"] = json.dumps(poolchannels)
            rs.profileConfiguration = json.dumps(cnf)
            self.dump(rs)
            sed1 = json.loads(self._cf.dp.selections([val["MntGrp"]])[0])
            rs.resetPreselectedComponents()
            res = self.value(rs, "ComponentPreselection")
            self.compareToDump(rs, ["ComponentPreselection"])

            self.myAssertDict(json.loads(res), {
                "smycp": True, "smycp2": True, "smycp3": True,
                "s2mycp": True, "s2mycp2": True, "s2mycp3": True})
            self.assertEqual(len(channelerrors), 0)

            res2 = json.loads(self._cf.dp.GetCommandVariable("VARS"))
            self.assertTrue(val["MntGrp"] in self._cf.dp.availableSelections())
            sed = json.loads(self._cf.dp.selections([val["MntGrp"]])[0])
            self.assertEqual(len(sed.keys()), len(self._keys))
            for key, vl in self._keys:
                self.assertTrue(key in sed.keys())
                if key in val:
                    self.assertEqual(sed[key], val[key])
                    self.assertEqual(sed1[key], val[key])
                elif key == 'ComponentPreselection':
                    self.myAssertDict(json.loads(sed[key]),
                                      json.loads(res))
                    self.assertNotEqual(sed1[key], res)
                elif key == 'PreselectedDataSources':
                    self.assertEqual(set(json.loads(sed[key])),
                                     set(poolchannels))
                    self.assertEqual(set(json.loads(sed1[key])),
                                     set(poolchannels))
                else:
                    self.assertEqual(sed[key], vl)
                    self.assertEqual(sed1[key], vl)
        finally:
            simps2.tearDown()

    ## test
    # \brief It tests default settings
    def test_resetPreselectedComponents_2wds_dvnorunning(self):
        fun = sys._getframe().f_code.co_name
        print "Run: %s.%s() " % (self.__class__.__name__, fun)
        val = {"ConfigDevice": self._cf.dp.name(),
               "WriterDevice": self._wr.dp.name(),
               "Door": 'doortestp09/testts/t1r228',
               "MntGrp": 'nxsmntgrp'}
        simps2 = TestServerSetUp.TestServerSetUp(
            "ttestp09/testts/t2r228", "S2")
        try:
            simps2.add()

            db = PyTango.Database()
            self._ms.dps[self._ms.ms.keys()[0]].Init()

            channelerrors = []
            poolchannels = []
            componentgroup = {"smycp": False, "smycp2": False, "smycp3": False,
                              "s2mycp": False, "s2mycp2": False,
                              "s2mycp3": False}

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

            self._ms.dps[self._ms.ms.keys()[0]].Init()

            cnf = json.loads(rs.profileConfiguration)
            cnf["PreselectedDataSources"] = json.dumps(poolchannels)
            rs.profileConfiguration = json.dumps(cnf)
            self.dump(rs)
            sed1 = json.loads(self._cf.dp.selections([val["MntGrp"]])[0])
            rs.resetPreselectedComponents()
            res = self.value(rs, "ComponentPreselection")
            self.compareToDump(rs, ["ComponentPreselection"])

            self.myAssertDict(json.loads(res), {
                "smycp": True, "smycp2": True, "smycp3": True,
                "s2mycp": False, "s2mycp2": False, "s2mycp3": False})
            self.assertEqual(len(rs.descriptionErrors), 3)

            res2 = json.loads(self._cf.dp.GetCommandVariable("VARS"))
            self.assertTrue(val["MntGrp"] in self._cf.dp.availableSelections())
            sed = json.loads(self._cf.dp.selections([val["MntGrp"]])[0])
            self.assertEqual(len(sed.keys()), len(self._keys))
            for key, vl in self._keys:
                self.assertTrue(key in sed.keys())
                if key in val:
                    self.assertEqual(sed[key], val[key])
                    self.assertEqual(sed1[key], val[key])
                elif key == 'ComponentPreselection':
                    self.myAssertDict(json.loads(sed[key]), json.loads(res))
                    self.assertNotEqual(sed1[key], res)
                elif key == 'PreselectedDataSources':
                    self.assertEqual(set(json.loads(sed[key])),
                                     set(poolchannels))
                    self.assertEqual(set(json.loads(sed1[key])),
                                     set(poolchannels))
                else:
                    self.assertEqual(sed[key], vl)
                    self.assertEqual(sed1[key], vl)
        finally:
            simps2.delete()

    ## test
    # \brief It tests default settings
    def test_resetPreselectedComponents_2wds_dvnodef(self):
        fun = sys._getframe().f_code.co_name
        print "Run: %s.%s() " % (self.__class__.__name__, fun)
        val = {"ConfigDevice": self._cf.dp.name(),
               "WriterDevice": self._wr.dp.name(),
               "Door": 'doortestp09/testts/t1r228',
               "MntGrp": 'nxsmntgrp'}

        db = PyTango.Database()
        self._ms.dps[self._ms.ms.keys()[0]].Init()
        channelerrors = []
        poolchannels = []
        componentgroup = {"smycp": False, "smycp2": False, "smycp3": False,
                          "s2mycp": False, "s2mycp2": False, "s2mycp3": False}

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

        self._ms.dps[self._ms.ms.keys()[0]].Init()

        cnf = json.loads(rs.profileConfiguration)
        cnf["PreselectedDataSources"] = json.dumps(poolchannels)
        rs.profileConfiguration = json.dumps(cnf)
        self.dump(rs)
        sed1 = json.loads(self._cf.dp.selections([val["MntGrp"]])[0])
        rs.resetPreselectedComponents()
        res = self.value(rs, "ComponentPreselection")
        self.compareToDump(rs, ["ComponentPreselection"])

        self.myAssertDict(json.loads(res), {
            "smycp": True, "smycp2": True, "smycp3": True,
            "s2mycp": False, "s2mycp2": False, "s2mycp3": False})
        self.assertEqual(len(rs.descriptionErrors), 3)

        res2 = json.loads(self._cf.dp.GetCommandVariable("VARS"))
        self.assertTrue(val["MntGrp"] in self._cf.dp.availableSelections())
        sed = json.loads(self._cf.dp.selections([val["MntGrp"]])[0])
        self.assertEqual(len(sed.keys()), len(self._keys))
        for key, vl in self._keys:
            self.assertTrue(key in sed.keys())
            if key in val:
                self.assertEqual(sed[key], val[key])
                self.assertEqual(sed1[key], val[key])
            elif key == 'ComponentPreselection':
                self.myAssertDict(json.loads(sed[key]), json.loads(res))
                self.assertNotEqual(sed1[key], res)
            elif key == 'PreselectedDataSources':
                self.assertEqual(set(json.loads(sed[key])),
                                 set(poolchannels))
                self.assertEqual(set(json.loads(sed1[key])),
                                 set(poolchannels))
            else:
                self.assertEqual(sed[key], vl)
                self.assertEqual(sed1[key], vl)

    ## test
    # \brief It tests default settings
    def test_resetPreselectedComponents_2wds_nods(self):
        fun = sys._getframe().f_code.co_name
        print "Run: %s.%s() " % (self.__class__.__name__, fun)
        val = {"ConfigDevice": self._cf.dp.name(),
               "WriterDevice": self._wr.dp.name(),
               "Door": 'doortestp09/testts/t1r228',
               "MntGrp": 'nxsmntgrp'}
        simps2 = TestServerSetUp.TestServerSetUp(
            "ttestp09/testts/t2r228", "S2")
        try:
            simps2.setUp()

            db = PyTango.Database()
            self._ms.dps[self._ms.ms.keys()[0]].Init()

            channelerrors = []
            poolchannels = []
            componentgroup = {"smycp": False, "smycp2": False, "smycp3": False,
                              "s2mycp": False, "s2mycp2": False,
                              "s2mycp3": False}

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

            self._ms.dps[self._ms.ms.keys()[0]].Init()

            self._cf.dp.SetCommandVariable(["CPDICT", json.dumps(cps)])
            self._cf.dp.SetCommandVariable(["DSDICT", json.dumps(dss)])

            cnf = json.loads(rs.profileConfiguration)
            cnf["PreselectedDataSources"] = json.dumps(poolchannels)
            rs.profileConfiguration = json.dumps(cnf)
            self.dump(rs)
            sed1 = json.loads(self._cf.dp.selections([val["MntGrp"]])[0])
            rs.resetPreselectedComponents()
            res = self.value(rs, "ComponentPreselection")
            self.compareToDump(rs, ["ComponentPreselection"])

            self.myAssertDict(json.loads(res), {
                "smycp": True, "smycp2": True, "smycp3": True,
                "s2mycp": True, "s2mycp2": True, "s2mycp3": True})
            self.assertTrue(not rs.descriptionErrors)

            res2 = json.loads(self._cf.dp.GetCommandVariable("VARS"))
            self.assertTrue(val["MntGrp"] in self._cf.dp.availableSelections())
            sed = json.loads(self._cf.dp.selections([val["MntGrp"]])[0])
            self.assertEqual(len(sed.keys()), len(self._keys))
            for key, vl in self._keys:
                self.assertTrue(key in sed.keys())
                if key in val:
                    self.assertEqual(sed[key], val[key])
                    self.assertEqual(sed1[key], val[key])
                elif key == 'ComponentPreselection':
                    self.myAssertDict(json.loads(sed[key]), json.loads(res))
                    self.assertNotEqual(sed1[key], res)
                elif key == 'PreselectedDataSources':
                    self.assertEqual(set(json.loads(sed[key])),
                                     set(poolchannels))
                    self.assertEqual(set(json.loads(sed1[key])),
                                     set(poolchannels))
                else:
                    self.assertEqual(sed[key], vl)
                    self.assertEqual(sed1[key], vl)
        finally:
            simps2.tearDown()

    ## test
    # \brief It tests default settings
    def test_resetPreselectedComponents_2wds_nodspool(self):
        fun = sys._getframe().f_code.co_name
        print "Run: %s.%s() " % (self.__class__.__name__, fun)
        val = {"ConfigDevice": self._cf.dp.name(),
               "WriterDevice": self._wr.dp.name(),
               "Door": 'doortestp09/testts/t1r228',
               "MntGrp": 'nxsmntgrp'}
        simps2 = TestServerSetUp.TestServerSetUp(
            "ttestp09/testts/t2r228", "S2")
        try:
            simps2.setUp()
            db = PyTango.Database()
            self._ms.dps[self._ms.ms.keys()[0]].Init()

            poolchannels = ["scalar2_long", "spectrum2_short"]
            componentgroup = {"smycp": False, "smycp2": False, "smycp3": False,
                              "s2mycp": False, "s2mycp2": False,
                              "s2mycp3": False}

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

            self._ms.dps[self._ms.ms.keys()[0]].Init()

            cnf = json.loads(rs.profileConfiguration)
            cnf["PreselectedDataSources"] = json.dumps(poolchannels)
            rs.profileConfiguration = json.dumps(cnf)
            self.dump(rs)
            sed1 = json.loads(self._cf.dp.selections([val["MntGrp"]])[0])
            rs.resetPreselectedComponents()
            res = self.value(rs, "ComponentPreselection")
            self.compareToDump(rs, ["ComponentPreselection"])

            self.myAssertDict(json.loads(res), {
                "smycp": True, "smycp2": True, "smycp3": True,
                "s2mycp": False, "s2mycp2": False, "s2mycp3": True})
            self.assertEqual(len(rs.descriptionErrors), 2)

            res2 = json.loads(self._cf.dp.GetCommandVariable("VARS"))
            self.assertTrue(val["MntGrp"] in self._cf.dp.availableSelections())
            sed = json.loads(self._cf.dp.selections([val["MntGrp"]])[0])
            self.assertEqual(len(sed.keys()), len(self._keys))
            for key, vl in self._keys:
                self.assertTrue(key in sed.keys())
                self.assertTrue(key in sed1.keys())
                if key in val:
                    self.assertEqual(sed[key], val[key])
                elif key == 'ComponentPreselection':
                    self.myAssertDict(json.loads(sed[key]), json.loads(res))
                    self.assertNotEqual(sed1[key], res)
                elif key == 'PreselectedDataSources':
                    self.assertEqual(set(json.loads(sed[key])),
                                     set(poolchannels))
                    self.assertEqual(set(json.loads(sed1[key])),
                                     set(poolchannels))
                else:
                    self.assertEqual(sed[key], vl)
                    self.assertEqual(sed1[key], vl)
        finally:
            simps2.tearDown()

    ## test
    # \brief It tests default settings
    def test_resetPreselectedComponents_2wds_notangods(self):
        fun = sys._getframe().f_code.co_name
        print "Run: %s.%s() " % (self.__class__.__name__, fun)
        val = {"ConfigDevice": self._cf.dp.name(),
               "WriterDevice": self._wr.dp.name(),
               "Door": 'doortestp09/testts/t1r228',
               "MntGrp": 'nxsmntgrp'}
        simps2 = TestServerSetUp.TestServerSetUp(
            "ttestp09/testts/t2r228", "S2")
        try:
            simps2.setUp()

            db = PyTango.Database()
            self._ms.dps[self._ms.ms.keys()[0]].Init()
            poolchannels = ["scalar2_long", "spectrum2_short"]
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
            self.setProp(rs, "defaultPreselectedComponents",
                         list(componentgroup.keys()))
            rs.configDevice = val["ConfigDevice"]
            rs.door = val["Door"]
            rs.mntGrp = val["MntGrp"]
            rs.writerDevice = val["WriterDevice"]

            self._ms.dps[self._ms.ms.keys()[0]].Init()

            cnf = json.loads(rs.profileConfiguration)
            cnf["PreselectedDataSources"] = json.dumps(poolchannels)
            rs.profileConfiguration = json.dumps(cnf)
            self.dump(rs)
            sed1 = json.loads(self._cf.dp.selections([val["MntGrp"]])[0])
            rs.resetPreselectedComponents()
            res = self.value(rs, "ComponentPreselection")
            self.compareToDump(rs, ["ComponentPreselection"])

            self.myAssertDict(json.loads(res), {
                "smycp": True, "smycp2": True, "smycp3": True,
                "s2mycp": True, "s2mycp2": True, "s2mycp3": True,
                "smycpnt1": True})
            self.assertTrue(not rs.descriptionErrors)

    #        print self._cf.dp.GetCommandVariable("COMMANDS")
            res2 = json.loads(self._cf.dp.GetCommandVariable("VARS"))
            self.assertTrue(val["MntGrp"] in self._cf.dp.availableSelections())
            sed = json.loads(self._cf.dp.selections([val["MntGrp"]])[0])
            self.assertEqual(len(sed.keys()), len(self._keys))
            for key, vl in self._keys:
                self.assertTrue(key in sed.keys())
                if key in val:
                    self.assertEqual(sed[key], val[key])
                    self.assertEqual(sed1[key], val[key])
                elif key == 'ComponentPreselection':
                    self.myAssertDict(json.loads(sed[key]), json.loads(res))
                    self.assertNotEqual(sed1[key], res)
                elif key == 'PreselectedDataSources':
                    self.assertEqual(set(json.loads(sed[key])),
                                     set(poolchannels))
                    self.assertEqual(set(json.loads(sed1[key])),
                                     set(poolchannels))
                else:
                    self.assertEqual(sed[key], vl)
                    self.assertEqual(sed1[key], vl)
        finally:
            simps2.tearDown()

    ## test
    # \brief It tests default settings
    def test_resetPreselectedComponents_2wds_notangodsnopool(self):
        fun = sys._getframe().f_code.co_name
        print "Run: %s.%s() " % (self.__class__.__name__, fun)
        val = {"ConfigDevice": self._cf.dp.name(),
               "WriterDevice": self._wr.dp.name(),
               "Door": 'doortestp09/testts/t1r228',
               "MntGrp": 'nxsmntgrp'}
        simps2 = TestServerSetUp.TestServerSetUp(
            "ttestp09/testts/t2r228", "S2")
        try:
            simps2.setUp()

            db = PyTango.Database()
            self._ms.dps[self._ms.ms.keys()[0]].Init()

            poolchannels = ["scalar2_long", "spectrum2_short", "client_long"]
            componentgroup = {"smycp": False, "smycp2": False,
                              "smycp3": False, "smycpnt1": False,
                              "s2mycp": False, "s2mycp2": False,
                              "s2mycp3": False}

            cps = dict(self.smycps)
            cps.update(self.smycps2)
            dss = dict(self.smydss)
            dss.update(self.smydss2)
            rs = self.openRecSelector()

            self.setProp(rs, "defaultPreselectedComponents",
                         list(componentgroup.keys()))
            rs.configDevice = val["ConfigDevice"]
            rs.door = val["Door"]
            rs.mntGrp = val["MntGrp"]
            rs.writerDevice = val["WriterDevice"]

            self._ms.dps[self._ms.ms.keys()[0]].Init()

            self._cf.dp.SetCommandVariable(["CPDICT", json.dumps(cps)])
            self._cf.dp.SetCommandVariable(["DSDICT", json.dumps(dss)])

            cnf = json.loads(rs.profileConfiguration)
            cnf["PreselectedDataSources"] = json.dumps(poolchannels)
            rs.profileConfiguration = json.dumps(cnf)
            self.dump(rs)
            sed1 = json.loads(self._cf.dp.selections([val["MntGrp"]])[0])
            rs.resetPreselectedComponents()
            res = self.value(rs, "ComponentPreselection")
            self.compareToDump(rs, ["ComponentPreselection"])

            self.myAssertDict(json.loads(res), {
                "smycp": True, "smycp2": True, "smycp3": True,
                "s2mycp": True, "s2mycp2": True, "s2mycp3": True,
                "smycpnt1": False})
            self.assertEqual(len(rs.descriptionErrors), 1)

    #        print self._cf.dp.GetCommandVariable("COMMANDS")
            res2 = json.loads(self._cf.dp.GetCommandVariable("VARS"))
            self.assertTrue(val["MntGrp"] in self._cf.dp.availableSelections())
            sed = json.loads(self._cf.dp.selections([val["MntGrp"]])[0])
            self.assertEqual(len(sed.keys()), len(self._keys))
            for key, vl in self._keys:
                self.assertTrue(key in sed.keys())
                if key in val:
                    self.assertEqual(sed[key], val[key])
                    self.assertEqual(sed1[key], val[key])
                elif key == 'ComponentPreselection':
                    self.myAssertDict(json.loads(sed[key]), json.loads(res))
                    self.assertNotEqual(sed1[key], res)
                elif key == 'PreselectedDataSources':
                    self.assertEqual(set(json.loads(sed[key])),
                                     set(poolchannels))
                    self.assertEqual(set(json.loads(sed1[key])),
                                     set(poolchannels))
                else:
                    self.assertEqual(sed[key], vl)
                    self.assertEqual(sed1[key], vl)
        finally:
            simps2.tearDown()

    ## test
    # \brief It tests default settings
    def test_resetPreselectedComponents_2wds_notangodsnopool2(self):
        fun = sys._getframe().f_code.co_name
        print "Run: %s.%s() " % (self.__class__.__name__, fun)
        val = {"ConfigDevice": self._cf.dp.name(),
               "WriterDevice": self._wr.dp.name(),
               "Door": 'doortestp09/testts/t1r228',
               "MntGrp": 'nxsmntgrp'}
        simps2 = TestServerSetUp.TestServerSetUp(
            "ttestp09/testts/t2r228", "S2")
        try:
            simps2.setUp()

            db = PyTango.Database()
            self._ms.dps[self._ms.ms.keys()[0]].Init()
            poolchannels = ["scalar2_long", "spectrum2_short", "client_long"]
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
            self.setProp(rs, "defaultPreselectedComponents",
                         list(componentgroup.keys()))
            rs.configDevice = val["ConfigDevice"]
            rs.door = val["Door"]
            rs.mntGrp = val["MntGrp"]
            rs.writerDevice = val["WriterDevice"]

            self._ms.dps[self._ms.ms.keys()[0]].Init()

            cnf = json.loads(rs.profileConfiguration)
            cnf["PreselectedDataSources"] = json.dumps(poolchannels)
            rs.profileConfiguration = json.dumps(cnf)
            self.dump(rs)
            sed1 = json.loads(self._cf.dp.selections([val["MntGrp"]])[0])
            rs.resetPreselectedComponents()
            res = self.value(rs, "ComponentPreselection")
            self.compareToDump(rs, ["ComponentPreselection"])

            self.myAssertDict(json.loads(res), {
                "smycp": True, "smycp2": True, "smycp3": True,
                "s2mycp": True, "s2mycp2": True, "s2mycp3": True,
                "smycpnt1": False})
            self.assertEqual(len(rs.descriptionErrors), 1)

    #        print self._cf.dp.GetCommandVariable("COMMANDS")
            res2 = json.loads(self._cf.dp.GetCommandVariable("VARS"))
            self.assertTrue(val["MntGrp"] in self._cf.dp.availableSelections())
            sed = json.loads(self._cf.dp.selections([val["MntGrp"]])[0])
            self.assertEqual(len(sed.keys()), len(self._keys))
            for key, vl in self._keys:
                self.assertTrue(key in sed.keys())
                if key in val:
                    self.assertEqual(sed[key], val[key])
                    self.assertEqual(sed1[key], val[key])
                elif key == 'ComponentPreselection':
                    self.myAssertDict(json.loads(sed[key]), json.loads(res))
                    self.assertNotEqual(sed1[key], res)
                elif key == 'PreselectedDataSources':
                    self.assertEqual(set(json.loads(sed[key])),
                                     set(poolchannels))
                    self.assertEqual(set(json.loads(sed1[key])),
                                     set(poolchannels))
                else:
                    self.assertEqual(sed[key], vl)
                    self.assertEqual(sed1[key], vl)
        finally:
            simps2.tearDown()

    ## test
    # \brief It tests default settings
    def test_resetPreselectedComponents_2wds_notangods2(self):
        fun = sys._getframe().f_code.co_name
        print "Run: %s.%s() " % (self.__class__.__name__, fun)
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

            db = PyTango.Database()
            db.put_device_property(self._ms.ms.keys()[0],
                                   {'PoolNames': self._pool.dp.name()})
            self._ms.dps[self._ms.ms.keys()[0]].Init()
            channelerrors = []
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
            self.setProp(rs, "defaultPreselectedComponents",
                         list(componentgroup.keys()))
            rs.configDevice = val["ConfigDevice"]
            rs.door = val["Door"]
            rs.mntGrp = val["MntGrp"]
            rs.writerDevice = val["WriterDevice"]

            self._ms.dps[self._ms.ms.keys()[0]].Init()

            pool = self._pool.dp
            pool.AcqChannelList = [json.dumps(a) for a in arr]

            cnf = json.loads(rs.profileConfiguration)
            cnf["PreselectedDataSources"] = json.dumps(poolchannels)
            rs.profileConfiguration = json.dumps(cnf)
            self.dump(rs)
            sed1 = json.loads(self._cf.dp.selections([val["MntGrp"]])[0])
            rs.resetPreselectedComponents()
            res = self.value(rs, "ComponentPreselection")
            self.compareToDump(rs, ["ComponentPreselection"])

            self.myAssertDict(json.loads(res), {
                "smycp": True, "smycp2": True, "smycp3": True,
                "s2mycp": True, "s2mycp2": True, "s2mycp3": True,
                "smycpnt1": True})
            self.assertTrue(not rs.descriptionErrors)

            res2 = json.loads(self._cf.dp.GetCommandVariable("VARS"))
            self.assertTrue(val["MntGrp"] in self._cf.dp.availableSelections())
            sed = json.loads(self._cf.dp.selections([val["MntGrp"]])[0])
            self.assertEqual(len(sed.keys()), len(self._keys))
            for key, vl in self._keys:
                self.assertTrue(key in sed.keys())
                if key in val:
                    self.assertEqual(sed[key], val[key])
                    self.assertEqual(sed1[key], val[key])
                elif key == 'ComponentPreselection':
                    self.myAssertDict(json.loads(sed[key]), json.loads(res))
                    self.assertNotEqual(sed1[key], res)
                elif key == 'PreselectedDataSources':
                    self.assertEqual(set(json.loads(sed[key])),
                                     set(poolchannels))
                    self.assertEqual(set(json.loads(sed1[key])),
                                     set(poolchannels))
                else:
                    self.assertEqual(sed[key], vl)
                    self.assertEqual(sed1[key], vl)
        finally:
            simps2.tearDown()

    ## test
    # \brief It tests default settings
    def test_resetPreselectedComponents_2wds_notangods2_bl(self):
        fun = sys._getframe().f_code.co_name
        print "Run: %s.%s() " % (self.__class__.__name__, fun)
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

            db = PyTango.Database()
            db.put_device_property(self._ms.ms.keys()[0],
                                   {'PoolNames': self._pool.dp.name()})
            self._ms.dps[self._ms.ms.keys()[0]].Init()
            channelerrors = []
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

            self._ms.dps[self._ms.ms.keys()[0]].Init()

            pool = self._pool.dp
            pool.AcqChannelList = [json.dumps(a) for a in arr]

            cnf = json.loads(rs.profileConfiguration)
            cnf["PreselectedDataSources"] = json.dumps(poolchannels)
            rs.profileConfiguration = json.dumps(cnf)
            self.dump(rs)
            sed1 = json.loads(self._cf.dp.selections([val["MntGrp"]])[0])
            rs.resetPreselectedComponents()
            res = self.value(rs, "ComponentPreselection")
            self.compareToDump(rs, ["ComponentPreselection"])

            self.myAssertDict(json.loads(res), {
                "smycp": True, "smycp2": True, "smycp3": True,
                "s2mycp": True, "s2mycp2": True, "s2mycp3": True,
                "smycpnt1": True})
            self.assertTrue(not rs.descriptionErrors)

            res2 = json.loads(self._cf.dp.GetCommandVariable("VARS"))
            self.assertTrue(val["MntGrp"] in self._cf.dp.availableSelections())
            sed = json.loads(self._cf.dp.selections([val["MntGrp"]])[0])
            self.assertEqual(len(sed.keys()), len(self._keys))
            for key, vl in self._keys:
                self.assertTrue(key in sed.keys())
                if key in val:
                    self.assertEqual(sed[key], val[key])
                    self.assertEqual(sed1[key], val[key])
                elif key == 'ComponentPreselection':
                    self.myAssertDict(json.loads(sed[key]), json.loads(res))
                    self.assertNotEqual(sed1[key], res)
                elif key == 'PreselectedDataSources':
                    self.assertEqual(set(json.loads(sed[key])),
                                     set(poolchannels))
                    self.assertEqual(set(json.loads(sed1[key])),
                                     set(poolchannels))
                else:
                    self.assertEqual(sed[key], vl)
                    self.assertEqual(sed1[key], vl)
        finally:
            simps2.tearDown()

    ## test
    # \brief It tests default settings
    def test_resetPreselectedComponents_2wds_notangodspool_error(self):
        fun = sys._getframe().f_code.co_name
        print "Run: %s.%s() " % (self.__class__.__name__, fun)
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

            db = PyTango.Database()
            db.put_device_property(self._ms.ms.keys()[0],
                                   {'PoolNames': self._pool.dp.name()})
            self._ms.dps[self._ms.ms.keys()[0]].Init()

            channelerrors = []
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

            self._ms.dps[self._ms.ms.keys()[0]].Init()

            pool = self._pool.dp
            pool.AcqChannelList = [json.dumps(a) for a in arr]

            cnf = json.loads(rs.profileConfiguration)
            cnf["PreselectedDataSources"] = json.dumps(poolchannels)
            rs.profileConfiguration = json.dumps(cnf)
            self.dump(rs)
            sed1 = json.loads(self._cf.dp.selections([val["MntGrp"]])[0])
            rs.resetPreselectedComponents()
            res = self.value(rs, "ComponentPreselection")
            self.compareToDump(rs, ["ComponentPreselection"])

            self.myAssertDict(json.loads(res), {
                "smycp": True, "smycp2": True, "smycp3": True,
                "s2mycp": True, "s2mycp2": True, "s2mycp3": True,
                "smycpnt1": False})
            self.assertEqual(len(rs.descriptionErrors), 1)

    #        print self._cf.dp.GetCommandVariable("COMMANDS")
            res2 = json.loads(self._cf.dp.GetCommandVariable("VARS"))
            self.assertTrue(val["MntGrp"] in self._cf.dp.availableSelections())
            sed = json.loads(self._cf.dp.selections([val["MntGrp"]])[0])
            self.assertEqual(len(sed.keys()), len(self._keys))
            for key, vl in self._keys:
                self.assertTrue(key in sed.keys())
                if key in val:
                    self.assertEqual(sed[key], val[key])
                    self.assertEqual(sed1[key], val[key])
                elif key == 'ComponentPreselection':
                    self.myAssertDict(json.loads(sed[key]), json.loads(res))
                    self.assertNotEqual(sed1[key], res)
                elif key == 'PreselectedDataSources':
                    self.assertEqual(set(json.loads(sed[key])),
                                     set(poolchannels))
                    self.assertEqual(set(json.loads(sed1[key])),
                                     set(poolchannels))
                else:
                    self.assertEqual(sed[key], vl)
                    self.assertEqual(sed1[key], vl)
        finally:
            simps2.tearDown()

    ## test
    # \brief It tests default settings
    def test_resetPreselectedComponents_2wds_notangodspool(self):
        fun = sys._getframe().f_code.co_name
        print "Run: %s.%s() " % (self.__class__.__name__, fun)
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

            db = PyTango.Database()
            db.put_device_property(self._ms.ms.keys()[0],
                                   {'PoolNames': self._pool.dp.name()})
            self._ms.dps[self._ms.ms.keys()[0]].Init()

            channelerrors = []

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

            self._ms.dps[self._ms.ms.keys()[0]].Init()

            pool = self._pool.dp
            pool.AcqChannelList = [json.dumps(a) for a in arr]

            self._simps.dp.ChangeValueType("ScalarShort")
            self._simps.dp.Value = 43

            cnf = json.loads(rs.profileConfiguration)
            cnf["PreselectedDataSources"] = json.dumps(poolchannels)
            rs.profileConfiguration = json.dumps(cnf)
            self.dump(rs)
            sed1 = json.loads(self._cf.dp.selections([val["MntGrp"]])[0])
            rs.resetPreselectedComponents()
            res = self.value(rs, "ComponentPreselection")
            self.compareToDump(rs, ["ComponentPreselection"])

            self.myAssertDict(json.loads(res), {
                "smycp": True, "smycp2": True, "smycp3": True,
                "s2mycp": True, "s2mycp2": True, "s2mycp3": True,
                "smycpnt1": False})
            self.assertEqual(len(rs.descriptionErrors), 1)

            res2 = json.loads(self._cf.dp.GetCommandVariable("VARS"))
            self.assertTrue(val["MntGrp"] in self._cf.dp.availableSelections())
            sed = json.loads(self._cf.dp.selections([val["MntGrp"]])[0])
            self.assertEqual(len(sed.keys()), len(self._keys))
            for key, vl in self._keys:
                self.assertTrue(key in sed.keys())
                if key in val:
                    self.assertEqual(sed[key], val[key])
                    self.assertEqual(sed1[key], val[key])
                elif key == 'ComponentPreselection':
                    self.myAssertDict(json.loads(sed[key]), json.loads(res))
                    self.assertNotEqual(sed1[key], res)
                elif key == 'PreselectedDataSources':
                    self.assertEqual(set(json.loads(sed[key])),
                                     set(poolchannels))
                    self.assertEqual(set(json.loads(sed1[key])),
                                     set(poolchannels))
                else:
                    self.assertEqual(sed[key], vl)
                    self.assertEqual(sed1[key], vl)
        finally:
            simps2.tearDown()

    ## test
    # \brief It tests default settings
    def test_resetPreselectedComponents_2wds_notangodspool_alias(self):
        fun = sys._getframe().f_code.co_name
        print "Run: %s.%s() " % (self.__class__.__name__, fun)
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
            db = PyTango.Database()
            simps2.setUp()
            db.put_device_alias(arr[0]["full_name"], arr[0]["name"])
            db.put_device_property(self._ms.ms.keys()[0],
                                   {'PoolNames': self._pool.dp.name()})

            self._ms.dps[self._ms.ms.keys()[0]].Init()

            channelerrors = []
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

            self._ms.dps[self._ms.ms.keys()[0]].Init()
            pool = self._pool.dp
            pool.AcqChannelList = [json.dumps(a) for a in arr]

            self._simps.dp.ChangeValueType("ScalarShort")
            self._simps.dp.Value = 43

            cnf = json.loads(rs.profileConfiguration)
            cnf["PreselectedDataSources"] = json.dumps(poolchannels)
            rs.profileConfiguration = json.dumps(cnf)
            self.dump(rs)
            sed1 = json.loads(self._cf.dp.selections([val["MntGrp"]])[0])
            rs.resetPreselectedComponents()
            res = self.value(rs, "ComponentPreselection")
            self.compareToDump(rs, ["ComponentPreselection"])

            self.myAssertDict(json.loads(res), {
                "smycp": True, "smycp2": True, "smycp3": True,
                "s2mycp": True, "s2mycp2": True, "s2mycp3": True,
                "smycpnt1": True})
            self.assertTrue(not rs.descriptionErrors)

            res2 = json.loads(self._cf.dp.GetCommandVariable("VARS"))
            self.assertTrue(val["MntGrp"] in self._cf.dp.availableSelections())
            sed = json.loads(self._cf.dp.selections([val["MntGrp"]])[0])
            self.assertEqual(len(sed.keys()), len(self._keys))
            for key, vl in self._keys:
                self.assertTrue(key in sed.keys())
                self.assertTrue(key in sed1.keys())
                if key in val:
                    self.assertEqual(sed[key], val[key])
                    self.assertEqual(sed1[key], val[key])
                elif key == 'ComponentPreselection':
                    self.myAssertDict(json.loads(sed[key]), json.loads(res))
                    self.assertNotEqual(sed1[key], res)
                elif key == 'PreselectedDataSources':
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

    ## test
    # \brief It tests default settings
    def test_resetPreselectedComponents_2wds_notangodspool_alias_bl(self):
        fun = sys._getframe().f_code.co_name
        print "Run: %s.%s() " % (self.__class__.__name__, fun)
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
            db = PyTango.Database()
            simps2.setUp()
            db.put_device_alias(arr[0]["full_name"], arr[0]["name"])
            db.put_device_property(self._ms.ms.keys()[0],
                                   {'PoolNames': self._pool.dp.name()})

            self._ms.dps[self._ms.ms.keys()[0]].Init()

            channelerrors = []
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

            self._ms.dps[self._ms.ms.keys()[0]].Init()
            pool = self._pool.dp
            pool.AcqChannelList = [json.dumps(a) for a in arr]

            self._simps.dp.ChangeValueType("ScalarShort")
            self._simps.dp.Value = 43

            cnf = json.loads(rs.profileConfiguration)
            cnf["PreselectedDataSources"] = json.dumps(poolchannels)
            rs.profileConfiguration = json.dumps(cnf)
            self.dump(rs)
            sed1 = json.loads(self._cf.dp.selections([val["MntGrp"]])[0])
            rs.resetPreselectedComponents()
            res = self.value(rs, "ComponentPreselection")
            self.compareToDump(rs, ["ComponentPreselection"])

            self.myAssertDict(json.loads(res), {
                "smycp": True, "smycp2": True, "smycp3": True,
                "s2mycp": True, "s2mycp2": True, "s2mycp3": True,
                "smycpnt1": False})
            self.assertTrue(rs.descriptionErrors)

            res2 = json.loads(self._cf.dp.GetCommandVariable("VARS"))
            self.assertTrue(val["MntGrp"] in self._cf.dp.availableSelections())
            sed = json.loads(self._cf.dp.selections([val["MntGrp"]])[0])
            self.assertEqual(len(sed.keys()), len(self._keys))
            for key, vl in self._keys:
                self.assertTrue(key in sed.keys())
                self.assertTrue(key in sed1.keys())
                if key in val:
                    self.assertEqual(sed[key], val[key])
                    self.assertEqual(sed1[key], val[key])
                elif key == 'ComponentPreselection':
                    self.myAssertDict(json.loads(sed[key]), json.loads(res))
                    self.assertNotEqual(sed1[key], res)
                elif key == 'PreselectedDataSources':
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

    ## test
    # \brief It tests default settings
    def test_resetPreselectedComponents_2wds_notangodspool_alias_value(self):
        fun = sys._getframe().f_code.co_name
        print "Run: %s.%s() " % (self.__class__.__name__, fun)
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
            db = PyTango.Database()
            simps2.setUp()

            db.put_device_alias(arr[0]["full_name"], arr[0]["name"])
            db.put_device_property(self._ms.ms.keys()[0],
                                   {'PoolNames': self._pool.dp.name()})

            self._ms.dps[self._ms.ms.keys()[0]].Init()
            channelerrors = []
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

            self._ms.dps[self._ms.ms.keys()[0]].Init()

            pool = self._pool.dp
            pool.AcqChannelList = [json.dumps(a) for a in arr]

            cnf = json.loads(rs.profileConfiguration)
            cnf["PreselectedDataSources"] = json.dumps(poolchannels)
            rs.profileConfiguration = json.dumps(cnf)
            self.dump(rs)
            sed1 = json.loads(self._cf.dp.selections([val["MntGrp"]])[0])
            rs.resetPreselectedComponents()
            res = self.value(rs, "ComponentPreselection")
            self.compareToDump(rs, ["ComponentPreselection"])

            self.myAssertDict(json.loads(res), {
                "smycp": True, "smycp2": True, "smycp3": True,
                "s2mycp": True, "s2mycp2": True, "s2mycp3": True,
                "smycpnt1": True})
            self.assertTrue(not rs.descriptionErrors)

    #        print self._cf.dp.GetCommandVariable("COMMANDS")
            res2 = json.loads(self._cf.dp.GetCommandVariable("VARS"))
            self.assertTrue(val["MntGrp"] in self._cf.dp.availableSelections())
            sed = json.loads(self._cf.dp.selections([val["MntGrp"]])[0])
            self.assertEqual(len(sed.keys()), len(self._keys))
            for key, vl in self._keys:
                self.assertTrue(key in sed.keys())
                self.assertTrue(key in sed1.keys())
                if key in val:
                    self.assertEqual(sed[key], val[key])
                    self.assertEqual(sed1[key], val[key])
                elif key == 'ComponentPreselection':
                    self.myAssertDict(json.loads(sed[key]), json.loads(res))
                    self.assertNotEqual(sed1[key], res)
                elif key == 'PreselectedDataSources':
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

    ## test
    # \brief It tests default settings
    def test_resetPreselectedComponents_2wds_ntp_alias_value_bl(self):
        fun = sys._getframe().f_code.co_name
        print "Run: %s.%s() " % (self.__class__.__name__, fun)
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
            db = PyTango.Database()
            simps2.setUp()

            db.put_device_alias(arr[0]["full_name"], arr[0]["name"])
            db.put_device_property(self._ms.ms.keys()[0],
                                   {'PoolNames': self._pool.dp.name()})

            self._ms.dps[self._ms.ms.keys()[0]].Init()
            channelerrors = []
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

            self._ms.dps[self._ms.ms.keys()[0]].Init()

            pool = self._pool.dp
            pool.AcqChannelList = [json.dumps(a) for a in arr]

            cnf = json.loads(rs.profileConfiguration)
            cnf["PreselectedDataSources"] = json.dumps(poolchannels)
            rs.profileConfiguration = json.dumps(cnf)
            self.dump(rs)
            sed1 = json.loads(self._cf.dp.selections([val["MntGrp"]])[0])
            rs.resetPreselectedComponents()
            res = self.value(rs, "ComponentPreselection")
            self.compareToDump(rs, ["ComponentPreselection"])

            self.myAssertDict(json.loads(res), {
                "smycp": True, "smycp2": True, "smycp3": True,
                "s2mycp": True, "s2mycp2": True, "s2mycp3": True,
                "smycpnt1": False})
            self.assertTrue(rs.descriptionErrors)

    #        print self._cf.dp.GetCommandVariable("COMMANDS")
            res2 = json.loads(self._cf.dp.GetCommandVariable("VARS"))
            self.assertTrue(val["MntGrp"] in self._cf.dp.availableSelections())
            sed = json.loads(self._cf.dp.selections([val["MntGrp"]])[0])
            self.assertEqual(len(sed.keys()), len(self._keys))
            for key, vl in self._keys:
                self.assertTrue(key in sed.keys())
                self.assertTrue(key in sed1.keys())
                if key in val:
                    self.assertEqual(sed[key], val[key])
                    self.assertEqual(sed1[key], val[key])
                elif key == 'ComponentPreselection':
                    self.myAssertDict(json.loads(sed[key]), json.loads(res))
                    self.assertNotEqual(sed1[key], res)
                elif key == 'PreselectedDataSources':
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

    ## test
    # \brief It tests default settings
    def test_resetPreselectedComponents_2wds_notngdspool_alias_novalue(self):
        fun = sys._getframe().f_code.co_name
        print "Run: %s.%s() " % (self.__class__.__name__, fun)
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
            db = PyTango.Database()
            simps2.setUp()

            db.put_device_alias(arr[0]["full_name"], arr[0]["name"])
            db.put_device_property(self._ms.ms.keys()[0],
                                   {'PoolNames': self._pool.dp.name()})

            self._ms.dps[self._ms.ms.keys()[0]].Init()

            channelerrors = []
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

            self._ms.dps[self._ms.ms.keys()[0]].Init()

            pool = self._pool.dp
            pool.AcqChannelList = [json.dumps(a) for a in arr]

            cnf = json.loads(rs.profileConfiguration)
            cnf["PreselectedDataSources"] = json.dumps(poolchannels)
            rs.profileConfiguration = json.dumps(cnf)
            self.dump(rs)
            sed1 = json.loads(self._cf.dp.selections([val["MntGrp"]])[0])
            rs.resetPreselectedComponents()
            res = self.value(rs, "ComponentPreselection")
            self.compareToDump(rs, ["ComponentPreselection"])

            self.myAssertDict(json.loads(res), {
                "smycp": True, "smycp2": True, "smycp3": True,
                "s2mycpnt1": False})
            self.assertEqual(len(rs.descriptionErrors), 1)

    #        print self._cf.dp.GetCommandVariable("COMMANDS")
            res2 = json.loads(self._cf.dp.GetCommandVariable("VARS"))
            self.assertTrue(val["MntGrp"] in self._cf.dp.availableSelections())
            sed = json.loads(self._cf.dp.selections([val["MntGrp"]])[0])
            self.assertEqual(len(sed.keys()), len(self._keys))
            for key, vl in self._keys:
                self.assertTrue(key in sed.keys())
                self.assertTrue(key in sed1.keys())
                if key in val:
                    self.assertEqual(sed[key], val[key])
                    self.assertEqual(sed1[key], val[key])
                elif key == 'ComponentPreselection':
                    self.myAssertDict(json.loads(sed[key]), json.loads(res))
                    self.assertNotEqual(sed1[key], res)
                elif key == 'PreselectedDataSources':
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

    ## test
    # \brief It tests default settings
    def test_resetPreselectedComponents_2wds_nocomponents(self):
        fun = sys._getframe().f_code.co_name
        print "Run: %s.%s() " % (self.__class__.__name__, fun)
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
            db = PyTango.Database()
            simps2.setUp()

            self._ms.dps[self._ms.ms.keys()[0]].Init()
            channelerrors = []
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

            self._ms.dps[self._ms.ms.keys()[0]].Init()

            cnf = json.loads(rs.profileConfiguration)
            cnf["PreselectedDataSources"] = json.dumps(poolchannels)
            rs.profileConfiguration = json.dumps(cnf)
            self.dump(rs)
            sed1 = json.loads(self._cf.dp.selections([val["MntGrp"]])[0])
            rs.resetPreselectedComponents()
            res = self.value(rs, "ComponentPreselection")

            self.myAssertDict(json.loads(res), {
                "smycp": True, "smycp2": True, "smycp3": True,
                "s2mycp": False, "s2mycp2": False, "s2mycp3": False})
            self.assertEqual(len(rs.descriptionErrors), 3)

    #        print self._cf.dp.GetCommandVariable("COMMANDS")
            res2 = json.loads(self._cf.dp.GetCommandVariable("VARS"))
            self.assertTrue(val["MntGrp"] in self._cf.dp.availableSelections())
            sed = json.loads(self._cf.dp.selections([val["MntGrp"]])[0])
            self.assertEqual(len(sed.keys()), len(self._keys))
            for key, vl in self._keys:
                self.assertTrue(key in sed.keys())
                self.assertTrue(key in sed1.keys())
                if key in val:
                    self.assertEqual(sed[key], val[key])
                    self.assertEqual(sed1[key], val[key])
                elif key == 'ComponentPreselection':
                    self.myAssertDict(json.loads(sed[key]), json.loads(res))
                    self.assertNotEqual(sed1[key], res)
                elif key == 'PreselectedDataSources':
                    self.assertEqual(set(json.loads(sed[key])),
                                     set(poolchannels))
                    self.assertEqual(set(json.loads(sed1[key])),
                                     set(poolchannels))
                else:
                    self.assertEqual(sed[key], vl)
                    self.assertEqual(sed1[key], vl)
        finally:
            simps2.tearDown()

    ## test
    # \brief It tests default settings
    def test_availableTimers_empty(self):
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

        self.assertTrue(not rs.availableTimers())

#            rs = self.openRecSelector()

    ## test
    # \brief It tests default settings
    def test_availableTimers_pool1(self):
        fun = sys._getframe().f_code.co_name
        print "Run: %s.%s() " % (self.__class__.__name__, fun)
        val = {"ConfigDevice": self._cf.dp.name(),
               "WriterDevice": self._wr.dp.name(),
               "Door": 'doortestp09/testts/t1r228',
               "MntGrp": 'nxsmntgrp'}

        db = PyTango.Database()
        db.put_device_property(self._ms.ms.keys()[0],
                               {'PoolNames': self._pool.dp.name()})
        self._ms.dps[self._ms.ms.keys()[0]].Init()
        rs = self.openRecSelector()
        rs.configDevice = val["ConfigDevice"]
        rs.door = val["Door"]
        rs.mntGrp = val["MntGrp"]

        db = PyTango.Database()
        db.put_device_property(self._ms.ms.keys()[0],
                               {'PoolNames': self._pool.dp.name()})

        self._ms.dps[self._ms.ms.keys()[0]].Init()

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

    ## test
    # \brief It tests default settings
    def test_availableTimers_pool1_bl(self):
        fun = sys._getframe().f_code.co_name
        print "Run: %s.%s() " % (self.__class__.__name__, fun)
        val = {"ConfigDevice": self._cf.dp.name(),
               "WriterDevice": self._wr.dp.name(),
               "Door": 'doortestp09/testts/t1r228',
               "MntGrp": 'nxsmntgrp'}

        db = PyTango.Database()
        db.put_device_property(self._ms.ms.keys()[0],
                               {'PoolNames': self._pool.dp.name()})
        self._ms.dps[self._ms.ms.keys()[0]].Init()
        rs = self.openRecSelector()
        self.setProp(rs, "poolBlacklist",
                     [self._pool.dp.name()])
        rs.configDevice = val["ConfigDevice"]
        rs.door = val["Door"]
        rs.mntGrp = val["MntGrp"]

        db = PyTango.Database()
        db.put_device_property(self._ms.ms.keys()[0],
                               {'PoolNames': self._pool.dp.name()})

        self._ms.dps[self._ms.ms.keys()[0]].Init()

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
        self.assertTrue(not dd)

    ## test
    # \brief It tests default settings
    def test_availableTimers_pool1_filter(self):
        fun = sys._getframe().f_code.co_name
        print "Run: %s.%s() " % (self.__class__.__name__, fun)
        val = {"ConfigDevice": self._cf.dp.name(),
               "WriterDevice": self._wr.dp.name(),
               "Door": 'doortestp09/testts/t1r228',
               "MntGrp": 'nxsmntgrp'}

        db = PyTango.Database()
        db.put_device_property(self._ms.ms.keys()[0],
                               {'PoolNames': self._pool.dp.name()})
        self._ms.dps[self._ms.ms.keys()[0]].Init()
        rs = self.openRecSelector()
        self.setProp(rs, "timerFilters",
                     ["*dgg2_exp_00*", "*dgg2_exp_01*"])
        rs.configDevice = val["ConfigDevice"]
        rs.door = val["Door"]
        rs.mntGrp = val["MntGrp"]

        db = PyTango.Database()
        db.put_device_property(self._ms.ms.keys()[0],
                               {'PoolNames': self._pool.dp.name()})

        self._ms.dps[self._ms.ms.keys()[0]].Init()

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

    ## test
    # \brief It tests default settings
    def test_availableTimers_2pools(self):
        fun = sys._getframe().f_code.co_name
        print "Run: %s.%s() " % (self.__class__.__name__, fun)
        val = {"ConfigDevice": self._cf.dp.name(),
               "WriterDevice": self._wr.dp.name(),
               "Door": 'doortestp09/testts/t1r228',
               "MntGrp": 'nxsmntgrp'}

        try:
            tpool2 = TestPoolSetUp.TestPoolSetUp(
                "pooltestp09/testts/t2r228", "POOLTESTS2")
            tpool2.setUp()

            db = PyTango.Database()
            db.put_device_property(
                self._ms.ms.keys()[0],
                {'PoolNames': [
                    tpool2.dp.name(), self._pool.dp.name()]})
            pool = self._pool.dp
            pool2 = tpool2.dp
            self._ms.dps[self._ms.ms.keys()[0]].Init()

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

    ## test
    # \brief It tests default settings
    def test_availableTimers_2pools_bl(self):
        fun = sys._getframe().f_code.co_name
        print "Run: %s.%s() " % (self.__class__.__name__, fun)
        val = {"ConfigDevice": self._cf.dp.name(),
               "WriterDevice": self._wr.dp.name(),
               "Door": 'doortestp09/testts/t1r228',
               "MntGrp": 'nxsmntgrp'}

        try:
            tpool2 = TestPoolSetUp.TestPoolSetUp(
                "pooltestp09/testts/t2r228", "POOLTESTS2")
            tpool2.setUp()

            db = PyTango.Database()
            db.put_device_property(
                self._ms.ms.keys()[0],
                {'PoolNames': [
                    tpool2.dp.name(), self._pool.dp.name()]})
            pool = self._pool.dp
            pool2 = tpool2.dp
            self._ms.dps[self._ms.ms.keys()[0]].Init()

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

    ## test
    # \brief It tests default settings
    def test_availableTimers_2pools_filter_bl(self):
        fun = sys._getframe().f_code.co_name
        print "Run: %s.%s() " % (self.__class__.__name__, fun)
        val = {"ConfigDevice": self._cf.dp.name(),
               "WriterDevice": self._wr.dp.name(),
               "Door": 'doortestp09/testts/t1r228',
               "MntGrp": 'nxsmntgrp'}

        try:
            tpool2 = TestPoolSetUp.TestPoolSetUp(
                "pooltestp09/testts/t2r228", "POOLTESTS2")
            tpool2.setUp()

            db = PyTango.Database()
            db.put_device_property(
                self._ms.ms.keys()[0],
                {'PoolNames': [
                    tpool2.dp.name(), self._pool.dp.name()]})
            pool = self._pool.dp
            pool2 = tpool2.dp
            self._ms.dps[self._ms.ms.keys()[0]].Init()

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

    ## test
    # \brief It tests default settings
    def test_availableTimers_2pools_filter(self):
        fun = sys._getframe().f_code.co_name
        print "Run: %s.%s() " % (self.__class__.__name__, fun)
        val = {"ConfigDevice": self._cf.dp.name(),
               "WriterDevice": self._wr.dp.name(),
               "Door": 'doortestp09/testts/t1r228',
               "MntGrp": 'nxsmntgrp'}

        try:
            tpool2 = TestPoolSetUp.TestPoolSetUp(
                "pooltestp09/testts/t2r228", "POOLTESTS2")
            tpool2.setUp()

            db = PyTango.Database()
            db.put_device_property(
                self._ms.ms.keys()[0],
                {'PoolNames': [
                    tpool2.dp.name(), self._pool.dp.name()]})
            pool = self._pool.dp
            pool2 = tpool2.dp
            self._ms.dps[self._ms.ms.keys()[0]].Init()

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

    ## test
    # \brief It tests default settings
    def test_mutedChannels_empty(self):
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

        self.assertTrue(not rs.mutedChannels())

#            rs = self.openRecSelector()

    ## test
    # \brief It tests default settings
    def test_mutedChannels_pool1(self):
        fun = sys._getframe().f_code.co_name
        print "Run: %s.%s() " % (self.__class__.__name__, fun)
        val = {"ConfigDevice": self._cf.dp.name(),
               "WriterDevice": self._wr.dp.name(),
               "Door": 'doortestp09/testts/t1r228',
               "MntGrp": 'nxsmntgrp'}

        db = PyTango.Database()
        db.put_device_property(self._ms.ms.keys()[0],
                               {'PoolNames': self._pool.dp.name()})
        self._ms.dps[self._ms.ms.keys()[0]].Init()
        rs = self.openRecSelector()
        rs.configDevice = val["ConfigDevice"]
        rs.door = val["Door"]
        rs.mntGrp = val["MntGrp"]

        db = PyTango.Database()
        db.put_device_property(self._ms.ms.keys()[0],
                               {'PoolNames': self._pool.dp.name()})

        self._ms.dps[self._ms.ms.keys()[0]].Init()

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

    ## test
    # \brief It tests default settings
    def test_mutedChannels_pool1_bl(self):
        fun = sys._getframe().f_code.co_name
        print "Run: %s.%s() " % (self.__class__.__name__, fun)
        val = {"ConfigDevice": self._cf.dp.name(),
               "WriterDevice": self._wr.dp.name(),
               "Door": 'doortestp09/testts/t1r228',
               "MntGrp": 'nxsmntgrp'}

        db = PyTango.Database()
        db.put_device_property(self._ms.ms.keys()[0],
                               {'PoolNames': self._pool.dp.name()})
        self._ms.dps[self._ms.ms.keys()[0]].Init()
        rs = self.openRecSelector()
        self.setProp(rs, "poolBlacklist",
                     [self._pool.dp.name()])
        rs.configDevice = val["ConfigDevice"]
        rs.door = val["Door"]
        rs.mntGrp = val["MntGrp"]

        db = PyTango.Database()
        db.put_device_property(self._ms.ms.keys()[0],
                               {'PoolNames': self._pool.dp.name()})

        self._ms.dps[self._ms.ms.keys()[0]].Init()

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

        lst = [ar[0] for ar in arr if "tip551" in ar[1]]
        dd = rs.mutedChannels()
        self.assertTrue(not dd)

    ## test
    # \brief It tests default settings
    def test_mutedChannels_pool1_filter(self):
        fun = sys._getframe().f_code.co_name
        print "Run: %s.%s() " % (self.__class__.__name__, fun)
        val = {"ConfigDevice": self._cf.dp.name(),
               "WriterDevice": self._wr.dp.name(),
               "Door": 'doortestp09/testts/t1r228',
               "MntGrp": 'nxsmntgrp'}

        db = PyTango.Database()
        db.put_device_property(self._ms.ms.keys()[0],
                               {'PoolNames': self._pool.dp.name()})
        self._ms.dps[self._ms.ms.keys()[0]].Init()
        rs = self.openRecSelector()
        self.setProp(rs, "mutedChannelFilters",
                     ["*dgg2_exp_00*", "*dgg2_exp_01*"])
        rs.configDevice = val["ConfigDevice"]
        rs.door = val["Door"]
        rs.mntGrp = val["MntGrp"]

        db = PyTango.Database()
        db.put_device_property(self._ms.ms.keys()[0],
                               {'PoolNames': self._pool.dp.name()})

        self._ms.dps[self._ms.ms.keys()[0]].Init()

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

    ## test
    # \brief It tests default settings
    def test_mutedChannels_2pools(self):
        fun = sys._getframe().f_code.co_name
        print "Run: %s.%s() " % (self.__class__.__name__, fun)
        val = {"ConfigDevice": self._cf.dp.name(),
               "WriterDevice": self._wr.dp.name(),
               "Door": 'doortestp09/testts/t1r228',
               "MntGrp": 'nxsmntgrp'}

        try:
            tpool2 = TestPoolSetUp.TestPoolSetUp(
                "pooltestp09/testts/t2r228", "POOLTESTS2")
            tpool2.setUp()

            db = PyTango.Database()
            db.put_device_property(
                self._ms.ms.keys()[0],
                {'PoolNames': [
                    tpool2.dp.name(), self._pool.dp.name()]})
            pool = self._pool.dp
            pool2 = tpool2.dp
            self._ms.dps[self._ms.ms.keys()[0]].Init()

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
            lst.extend([ar[0] for ar in arr2  if 'tip551' in ar[1]])

            dd = rs.mutedChannels()
            self.assertEqual(set(dd), set(lst))

        finally:
            tpool2.tearDown()

    ## test
    # \brief It tests default settings
    def test_mutedChannels_2pools_bl(self):
        fun = sys._getframe().f_code.co_name
        print "Run: %s.%s() " % (self.__class__.__name__, fun)
        val = {"ConfigDevice": self._cf.dp.name(),
               "WriterDevice": self._wr.dp.name(),
               "Door": 'doortestp09/testts/t1r228',
               "MntGrp": 'nxsmntgrp'}

        try:
            tpool2 = TestPoolSetUp.TestPoolSetUp(
                "pooltestp09/testts/t2r228", "POOLTESTS2")
            tpool2.setUp()

            db = PyTango.Database()
            db.put_device_property(
                self._ms.ms.keys()[0],
                {'PoolNames': [
                    tpool2.dp.name(), self._pool.dp.name()]})
            pool = self._pool.dp
            pool2 = tpool2.dp
            self._ms.dps[self._ms.ms.keys()[0]].Init()

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

    ## test
    # \brief It tests default settings
    def test_mutedChannels_2pools_filter_bl(self):
        fun = sys._getframe().f_code.co_name
        print "Run: %s.%s() " % (self.__class__.__name__, fun)
        val = {"ConfigDevice": self._cf.dp.name(),
               "WriterDevice": self._wr.dp.name(),
               "Door": 'doortestp09/testts/t1r228',
               "MntGrp": 'nxsmntgrp'}

        try:
            tpool2 = TestPoolSetUp.TestPoolSetUp(
                "pooltestp09/testts/t2r228", "POOLTESTS2")
            tpool2.setUp()

            db = PyTango.Database()
            db.put_device_property(
                self._ms.ms.keys()[0],
                {'PoolNames': [
                    tpool2.dp.name(), self._pool.dp.name()]})
            pool = self._pool.dp
            pool2 = tpool2.dp
            self._ms.dps[self._ms.ms.keys()[0]].Init()

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

    ## test
    # \brief It tests default settings
    def test_mutedChannels_2pools_filter(self):
        fun = sys._getframe().f_code.co_name
        print "Run: %s.%s() " % (self.__class__.__name__, fun)
        val = {"ConfigDevice": self._cf.dp.name(),
               "WriterDevice": self._wr.dp.name(),
               "Door": 'doortestp09/testts/t1r228',
               "MntGrp": 'nxsmntgrp'}

        try:
            tpool2 = TestPoolSetUp.TestPoolSetUp(
                "pooltestp09/testts/t2r228", "POOLTESTS2")
            tpool2.setUp()

            db = PyTango.Database()
            db.put_device_property(
                self._ms.ms.keys()[0],
                {'PoolNames': [
                    tpool2.dp.name(), self._pool.dp.name()]})
            pool = self._pool.dp
            pool2 = tpool2.dp
            self._ms.dps[self._ms.ms.keys()[0]].Init()

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

            dd = rs.mutedChannels()
            self.assertTrue(not dd)

            pool.ExpChannelList = [
                json.dumps(
                    {"name": a[0], "interfaces": a[1], "source": a[2]}
                )
                for a in arr]

            lst = [ar[0] for ar in arr if (
                "CTExpChannel" in ar[1] and (
                    'exp_00' in ar[2] or 'exp_01' in ar[2]))]

            dd = rs.mutedChannels()
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

            dd = rs.mutedChannels()
            self.assertEqual(set(dd), set(lst))

        finally:
            tpool2.tearDown()



            
    ## getDeviceName test
    def test_fullDeviceNames_empty(self):
        fun = sys._getframe().f_code.co_name
        print "Run: %s.%s() " % (self.__class__.__name__, fun)
        val = {"ConfigDevice": self._cf.dp.name(),
               "WriterDevice": self._wr.dp.name(),
               "Door": 'doortestp09/testts/t1r228',
               "MntGrp": 'nxsmntgrp'}

        db = PyTango.Database()
        db.put_device_property(self._ms.ms.keys()[0],
                               {'PoolNames': self._pool.dp.name()})
        self._ms.dps[self._ms.ms.keys()[0]].Init()
        rs = self.openRecSelector()
        rs.configDevice = val["ConfigDevice"]
        rs.door = val["Door"]
        rs.mntGrp = val["MntGrp"]

        self.assertEqual({}, json.loads(rs.fullDeviceNames()))

    ## getDeviceName test
    def test_fullDeviceNames_pool1(self):
        fun = sys._getframe().f_code.co_name
        print "Run: %s.%s() " % (self.__class__.__name__, fun)
        val = {"ConfigDevice": self._cf.dp.name(),
               "WriterDevice": self._wr.dp.name(),
               "Door": 'doortestp09/testts/t1r228',
               "MntGrp": 'nxsmntgrp'}

        db = PyTango.Database()
        db.put_device_property(self._ms.ms.keys()[0],
                               {'PoolNames': self._pool.dp.name()})
        self._ms.dps[self._ms.ms.keys()[0]].Init()
        rs = self.openRecSelector()
        rs.configDevice = val["ConfigDevice"]
        rs.door = val["Door"]
        rs.mntGrp = val["MntGrp"]

        db = PyTango.Database()
        db.put_device_property(self._ms.ms.keys()[0],
                               {'PoolNames': self._pool.dp.name()})

        self._ms.dps[self._ms.ms.keys()[0]].Init()

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
        print "Run: %s.%s() " % (self.__class__.__name__, fun)
        val = {"ConfigDevice": self._cf.dp.name(),
               "WriterDevice": self._wr.dp.name(),
               "Door": 'doortestp09/testts/t1r228',
               "MntGrp": 'nxsmntgrp'}

        try:
            tpool2 = TestPoolSetUp.TestPoolSetUp(
                "pooltestp09/testts/t2r228", "POOLTESTS2")
            tpool2.setUp()

            db = PyTango.Database()
            db.put_device_property(
                self._ms.ms.keys()[0],
                {'PoolNames': [
                    tpool2.dp.name(), self._pool.dp.name()]})
            pool = self._pool.dp
            pool2 = tpool2.dp
            self._ms.dps[self._ms.ms.keys()[0]].Init()

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
        print "Run: %s.%s() " % (self.__class__.__name__, fun)
        val = {"ConfigDevice": self._cf.dp.name(),
               "WriterDevice": self._wr.dp.name(),
               "Door": 'doortestp09/testts/t1r228',
               "MntGrp": 'nxsmntgrp'}

        try:
            tpool2 = TestPoolSetUp.TestPoolSetUp(
                "pooltestp09/testts/t2r228", "POOLTESTS2")
            tpool2.setUp()

            db = PyTango.Database()
            db.put_device_property(
                self._ms.ms.keys()[0],
                {'PoolNames': [
                    tpool2.dp.name(), self._pool.dp.name()]})
            pool = self._pool.dp
            pool2 = tpool2.dp
            self._ms.dps[self._ms.ms.keys()[0]].Init()

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

            dct2 = dict((ar[0], ar[1]) for ar in arr2)
            dd = json.loads(rs.fullDeviceNames())
#            dct.update(dct2)
            self.myAssertDict(dd, dct)

        finally:
            tpool2.tearDown()

    ## setEnv test
    def test_scanDir(self):
        fun = sys._getframe().f_code.co_name
        print "Run: %s.%s() " % (self.__class__.__name__, fun)

        val = {"ConfigDevice": self._cf.dp.name(),
               "WriterDevice": self._wr.dp.name(),
               "Door": 'doortestp09/testts/t1r228',
               "MntGrp": 'nxsmntgrp'}

        db = PyTango.Database()
        db.put_device_property(self._ms.ms.keys()[0],
                               {'PoolNames': self._pool.dp.name()})
        self._ms.dps[self._ms.ms.keys()[0]].Init()
        rs = self.openRecSelector()
        rs.configDevice = val["ConfigDevice"]
        rs.door = val["Door"]
        rs.mntGrp = val["MntGrp"]

        db = PyTango.Database()
        db.put_device_property(self._ms.ms.keys()[0],
                               {'PoolNames': self._pool.dp.name()})

        self._ms.dps[self._ms.ms.keys()[0]].Init()

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
                self._ms.dps[self._ms.ms.keys()[0]].Environment[0],
                'pickle')
            en = pickle.loads(
                self._ms.dps[self._ms.ms.keys()[0]].Environment[1]
            )['new']
            self.assertEqual(en['ScanDir'], rs.scanDir)
            self.assertEqual(vl[1], rs.scanDir)

    ## setEnv test
    def test_scanID(self):
        fun = sys._getframe().f_code.co_name
        print "Run: %s.%s() " % (self.__class__.__name__, fun)

        val = {"ConfigDevice": self._cf.dp.name(),
               "WriterDevice": self._wr.dp.name(),
               "Door": 'doortestp09/testts/t1r228',
               "MntGrp": 'nxsmntgrp'}

        db = PyTango.Database()
        db.put_device_property(self._ms.ms.keys()[0],
                               {'PoolNames': self._pool.dp.name()})
        self._ms.dps[self._ms.ms.keys()[0]].Init()
        rs = self.openRecSelector()
        rs.configDevice = val["ConfigDevice"]
        rs.door = val["Door"]
        rs.mntGrp = val["MntGrp"]

        db = PyTango.Database()
        db.put_device_property(self._ms.ms.keys()[0],
                               {'PoolNames': self._pool.dp.name()})

        self._ms.dps[self._ms.ms.keys()[0]].Init()

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
                self._ms.dps[self._ms.ms.keys()[0]].Environment[0],
                'pickle')
            en = pickle.loads(
                self._ms.dps[self._ms.ms.keys()[0]].Environment[1]
            )['new']
            self.assertEqual(en['ScanID'], rs.scanID)
            self.assertEqual(int(vl[1]), rs.scanID)

    ## scanfile test
    def test_scanFile(self):
        fun = sys._getframe().f_code.co_name
        print "Run: %s.%s() " % (self.__class__.__name__, fun)

        val = {"ConfigDevice": self._cf.dp.name(),
               "WriterDevice": self._wr.dp.name(),
               "Door": 'doortestp09/testts/t1r228',
               "MntGrp": 'nxsmntgrp'}

        db = PyTango.Database()
        db.put_device_property(self._ms.ms.keys()[0],
                               {'PoolNames': self._pool.dp.name()})
        self._ms.dps[self._ms.ms.keys()[0]].Init()
        rs = self.openRecSelector()
        rs.configDevice = val["ConfigDevice"]
        rs.door = val["Door"]
        rs.mntGrp = val["MntGrp"]

        db = PyTango.Database()
        db.put_device_property(self._ms.ms.keys()[0],
                               {'PoolNames': self._pool.dp.name()})

        self._ms.dps[self._ms.ms.keys()[0]].Init()

        arr = [
            [[u'sar4r.nxs'], ['sar4r.nxs', 'sar5r.nxs']],
            [[u'sar4r.nxs'], ['sssar3r.nxs']],
        ]
        for vl in arr:
            self.assertEqual(list(vl[0]), json.loads(rs.scanFile))

        for vl in arr:
            rs.scanFile = json.dumps(vl[1])
            print "SF", rs.scanFile
            self.assertEqual(
                self._ms.dps[self._ms.ms.keys()[0]].Environment[0],
                'pickle')
            en = pickle.loads(
                self._ms.dps[self._ms.ms.keys()[0]].Environment[1]
            )['new']
            if isinstance(en['ScanFile'], (str, unicode)):
                try:
                    sc = json.loads(rs.scanFile)[0]
                except:
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

    ## configvariables test
    def test_configVariables(self):
        fun = sys._getframe().f_code.co_name
        print "Run: %s.%s() " % (self.__class__.__name__, fun)
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

        for i in range(20):
            rs = self.openRecSelector()
            rs.configDevice = val["ConfigDevice"]
            rs.door = val["Door"]
            rs.mntGrp = mg

            rs.profileFile = filename

            db = PyTango.Database()
            db.put_device_property(self._ms.ms.keys()[0],
                                   {'PoolNames': self._pool.dp.name()})

            self._ms.dps[self._ms.ms.keys()[0]].Init()

            self.dump(rs)

            cps = {}
            lcp = self.__rnd.randint(1, 40)
            for _ in range(lcp):
                cps[self.getRandomName(10)] = self.getRandomName(
                    self.__rnd.randint(1, 40))

            rs.configVariables = str(json.dumps(cps))

            mydict = {}
            if (i / 2) % 2:
                mydict = json.loads(rs.profileConfiguration)
            elif (i / 2) % 4 == 0:
                rs.exportEnvProfile()
                env = pickle.loads(
                    self._ms.dps[self._ms.ms.keys()[0]].Environment[1])
                jmd = json.loads(rs.profileConfiguration)
                for k in self.names(rs):
                    try:
                        self.assertEqual(
                            json.loads(jmd[k]),
                            env["new"]["NeXusConfiguration"][k])
                    except:
                        self.assertEqual(
                            jmd[k],
                            env["new"]["NeXusConfiguration"][k])
            elif (i / 2) % 2 == 0:
                rs.saveProfile()
            else:
                rs.mntGrp = mg
                rs.storeProfile()

            self.compareToDump(rs, ["ConfigVariables"])

            ndss = json.loads(rs.configVariables)
            for ds in cps.keys():
                self.assertTrue(ds in ndss.keys())
                self.assertEqual(ndss[ds], cps[ds])

            rs.profileConfiguration = str(
                json.dumps({
                    "Version": "2.0.0",
                    "ConfigDevice": val["ConfigDevice"],
                    "Door": val["Door"],
                    "MntGrp": val["MntGrp"],
                })
            )
            rs.configDevice = val["ConfigDevice"]
            rs.door = val["Door"]
            rs.mntGrp = val["MntGrp"]

            self.assertEqual(rs.configVariables, "{}")

            mydata = {}
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

    ## userdata test
    def test_userData(self):
        fun = sys._getframe().f_code.co_name
        print "Run: %s.%s() " % (self.__class__.__name__, fun)
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

        for i in range(20):
            rs = self.openRecSelector()
            rs.configDevice = val["ConfigDevice"]
            rs.door = val["Door"]
            rs.mntGrp = mg

            rs.profileFile = filename

            db = PyTango.Database()
            db.put_device_property(self._ms.ms.keys()[0],
                                   {'PoolNames': self._pool.dp.name()})

            self._ms.dps[self._ms.ms.keys()[0]].Init()

            self.dump(rs)

            cps = {}
            lcp = self.__rnd.randint(1, 40)
            for _ in range(lcp):
                cps[self.getRandomName(10)] = self.getRandomName(
                    self.__rnd.randint(1, 40))

            rs.userData = str(json.dumps(cps))

            mydict = {}
            if (i / 2) % 2:
                mydict = json.loads(rs.profileConfiguration)
            elif (i / 2) % 4 == 0:
                rs.exportEnvProfile()
                env = pickle.loads(
                    self._ms.dps[self._ms.ms.keys()[0]].Environment[1])
                jmd = json.loads(rs.profileConfiguration)
                for k in self.names(rs):
                    try:
                        self.assertEqual(
                            json.loads(jmd[k]),
                            env["new"]["NeXusConfiguration"][k])
                    except:
                        self.assertEqual(
                            jmd[k],
                            env["new"]["NeXusConfiguration"][k])
            elif (i / 2) % 2 == 0:
                rs.saveProfile()
            else:
                rs.mntGrp = mg
                rs.storeProfile()

            self.compareToDump(rs, ["UserData"])

            ndss = json.loads(rs.userData)
            for ds in cps.keys():
                self.assertTrue(ds in ndss.keys())
                self.assertEqual(ndss[ds], cps[ds])

            rs.profileConfiguration = str(
                json.dumps({
                    "Version": "2.0.0",
                    "ConfigDevice": val["ConfigDevice"],
                    "Door": val["Door"],
                    "MntGrp": val["MntGrp"],
                })
            )
            rs.configDevice = val["ConfigDevice"]
            rs.door = val["Door"]
            rs.mntGrp = val["MntGrp"]

            self.assertEqual(rs.userData, "{}")

            mydata = {}
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

    ## mntgrp test
    def test_mntGrp(self):
        fun = sys._getframe().f_code.co_name
        print "Run: %s.%s() " % (self.__class__.__name__, fun)
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

        for i in range(20):
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

            db = PyTango.Database()
            db.put_device_property(self._ms.ms.keys()[0],
                                   {'PoolNames': self._pool.dp.name()})

            self._ms.dps[self._ms.ms.keys()[0]].Init()

            self.dump(rs)

            mydict = {}
            if (i / 2) % 2:
                mydict = json.loads(rs.profileConfiguration)
            elif (i / 2) % 4 == 0:
                rs.exportEnvProfile()
                env = pickle.loads(
                    self._ms.dps[self._ms.ms.keys()[0]].Environment[1])
                jmd = json.loads(rs.profileConfiguration)
                for k in self.names(rs):
                    try:
                        self.assertEqual(
                            json.loads(jmd[k]),
                            env["new"]["NeXusConfiguration"][k])
                    except:
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
                    "Version": "2.0.0",
                    "ConfigDevice": val["ConfigDevice"],
                    "Door": val["Door"],
                    "MntGrp": val["MntGrp"],
                })
            )
            rs.configDevice = val["ConfigDevice"]
            rs.door = val["Door"]
            rs.mntGrp = val["MntGrp"]

            self.assertEqual(rs.mntGrp, val["MntGrp"])

            mydata = {}
            if (i / 2) % 2:
                rs.profileConfiguration = str(json.dumps(mydict))
            elif (i / 2) % 4 == 0:
                rs.importEnvProfile()
            elif (i / 2) % 2 == 0:
                rs.loadProfile()
            else:
                rs.mntGrp = mg
                rs.fetchProfile()

            self.compareToDump(rs, ["MntGrp"])
            self.assertEqual(rs.mntGrp, mg)

        os.remove(filename)

    ## appendentry test
    def test_appendEntry(self):
        fun = sys._getframe().f_code.co_name
        print "Run: %s.%s() " % (self.__class__.__name__, fun)
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

        for i in range(20):
            rs = self.openRecSelector()
            rs.configDevice = val["ConfigDevice"]
            rs.door = val["Door"]
            rs.mntGrp = mg
            self.assertEqual(rs.mntGrp, mg)

            ap = bool(self.__rnd.randint(0, 1))
            rs.appendEntry = ap
            self.assertEqual(rs.appendEntry, ap)

            rs.profileFile = filename

            db = PyTango.Database()
            db.put_device_property(self._ms.ms.keys()[0],
                                   {'PoolNames': self._pool.dp.name()})

            self._ms.dps[self._ms.ms.keys()[0]].Init()

            self.dump(rs)

            mydict = {}
            if (i / 2) % 2:
                mydict = json.loads(rs.profileConfiguration)
            elif (i / 2) % 4 == 0:
                rs.exportEnvProfile()
                env = pickle.loads(
                    self._ms.dps[self._ms.ms.keys()[0]].Environment[1])
                jmd = json.loads(rs.profileConfiguration)
                for k in self.names(rs):
                    try:
                        self.assertEqual(
                            json.loads(jmd[k]),
                            env["new"]["NeXusConfiguration"][k])
                    except:
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
                    "Version": "2.0.0",
                    "ConfigDevice": val["ConfigDevice"],
                    "Door": val["Door"],
                    "MntGrp": val["MntGrp"],
                })
            )
            rs.configDevice = val["ConfigDevice"]
            rs.door = val["Door"]
            rs.mntGrp = val["MntGrp"]

            self.assertEqual(rs.appendEntry, False)

            mydata = {}
            if (i / 2) % 2:
                rs.profileConfiguration = str(json.dumps(mydict))
            elif (i / 2) % 4 == 0:
                rs.importEnvProfile()
            elif (i / 2) % 2 == 0:
                rs.loadProfile()
            else:
                rs.mntGrp = mg
                rs.fetchProfile()

            self.compareToDump(rs, ["AppendEntry"])
            self.assertEqual(rs.appendEntry, ap)

        os.remove(filename)

    ## test
    def test_writerDevice(self):
        fun = sys._getframe().f_code.co_name
        print "Run: %s.%s() " % (self.__class__.__name__, fun)
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

        for i in range(20):
            rs = self.openRecSelector()
            rs.configDevice = val["ConfigDevice"]
            rs.door = val["Door"]
            rs.mntGrp = mg
            self.assertEqual(rs.mntGrp, mg)

            wd = self.getRandomName(10)
            rs.writerDevice = wd
            self.assertEqual(rs.writerDevice, wd)

            rs.profileFile = filename

            db = PyTango.Database()
            db.put_device_property(self._ms.ms.keys()[0],
                                   {'PoolNames': self._pool.dp.name()})

            self._ms.dps[self._ms.ms.keys()[0]].Init()

            self.dump(rs)

            mydict = {}
            if (i / 2) % 2:
                mydict = json.loads(rs.profileConfiguration)
            elif (i / 2) % 4 == 0:
                rs.exportEnvProfile()
                env = pickle.loads(
                    self._ms.dps[self._ms.ms.keys()[0]].Environment[1])
                jmd = json.loads(rs.profileConfiguration)
                for k in self.names(rs):
                    try:
                        self.assertEqual(
                            json.loads(jmd[k]),
                            env["new"]["NeXusConfiguration"][k])
                    except:
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
                    "Version": "2.0.0",
                    "ConfigDevice": val["ConfigDevice"],
                    "Door": val["Door"],
                    "MntGrp": val["MntGrp"],
                })
            )
            rs.configDevice = val["ConfigDevice"]
            rs.door = val["Door"]
            rs.mntGrp = val["MntGrp"]

            self.assertEqual(rs.mntGrp, val["MntGrp"])

            mydata = {}
            if (i / 2) % 2:
                rs.profileConfiguration = str(json.dumps(mydict))
            elif (i / 2) % 4 == 0:
                rs.importEnvProfile()
            elif (i / 2) % 2 == 0:
                rs.loadProfile()
            else:
                rs.mntGrp = mg
                rs.fetchProfile()

            self.compareToDump(rs, ["WriterDevice"])
            self.assertEqual(rs.writerDevice, wd)

        os.remove(filename)

    ## test
    def test_door(self):
        fun = sys._getframe().f_code.co_name
        print "Run: %s.%s() " % (self.__class__.__name__, fun)
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

            db = PyTango.Database()
            db.put_device_property(ms2.ms.keys()[0],
                                   {'PoolNames': self._pool.dp.name()})
            print "KKKK", ms2.dps.keys()
            ms2.dps[ms2.ms.keys()[0]].Init()
            self._cf.dp.SetCommandVariable(["CPDICT", json.dumps(self.smycps)])
            self._cf.dp.SetCommandVariable(["DSDICT", json.dumps(self.smydss)])
            ms2.dps[ms2.ms.keys()[0]].DoorList = doors

            filename = "__testprofile__.json"
            while os.path.exists(filename):
                filename = "_" + filename

            mg = self.getRandomName(10)
            while mg == val["MntGrp"]:
                mg = self.getRandomName(10)

            for i in range(20):
                rs = self.openRecSelector()
                rs.configDevice = val["ConfigDevice"]
                rs.door = doors[i % 3]
                rs.mntGrp = mg
                self.assertEqual(rs.mntGrp, mg)
                self.assertEqual(rs.door, doors[i % 3])

                rs.profileFile = filename

                self.dump(rs)

                print "I", i
                mydict = {}
                if (i / 2) % 2:
                    mydict = json.loads(rs.profileConfiguration)
                elif (i / 2) % 4 == 0:
                    rs.exportEnvProfile()
                    env = pickle.loads(
                        ms2.dps[ms2.ms.keys()[0]].Environment[1])
                    jmd = json.loads(rs.profileConfiguration)
                    for k in self.names(rs):
                        try:
                            self.assertEqual(
                                json.loads(jmd[k]),
                                env["new"]["NeXusConfiguration"][k])
                        except:
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
                        "Version": "2.0.0",
                        "ConfigDevice": val["ConfigDevice"],
                        "Door": val["Door"],
                        "MntGrp": val["MntGrp"],
                    })
                )
                rs.configDevice = val["ConfigDevice"]
                rs.door = val["Door"]
                rs.mntGrp = val["MntGrp"]

                self.assertEqual(rs.mntGrp, val["MntGrp"])

                mydata = {}
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

                self.compareToDump(rs, [])
                self.assertEqual(rs.door, doors[i % 3])
            os.remove(filename)
        finally:
            ms2.tearDown()

    ## test
    def test_configDevice(self):
        fun = sys._getframe().f_code.co_name
        print "Run: %s.%s() " % (self.__class__.__name__, fun)
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

        for i in range(20):
            rs = self.openRecSelector()
            rs.configDevice = val["ConfigDevice"]
            rs.door = val["Door"]
            rs.mntGrp = mg
            self.assertEqual(rs.mntGrp, mg)

            rs.profileFile = filename

            db = PyTango.Database()
            db.put_device_property(self._ms.ms.keys()[0],
                                   {'PoolNames': self._pool.dp.name()})

            self._ms.dps[self._ms.ms.keys()[0]].Init()

            self.dump(rs)

            mydict = {}
            if (i / 2) % 2:
                mydict = json.loads(rs.profileConfiguration)
            elif (i / 2) % 4 == 0:
                rs.exportEnvProfile()
                env = pickle.loads(
                    self._ms.dps[self._ms.ms.keys()[0]].Environment[1])
                jmd = json.loads(rs.profileConfiguration)
                for k in self.names(rs):
                    try:
                        self.assertEqual(
                            json.loads(jmd[k]),
                            env["new"]["NeXusConfiguration"][k])
                    except:
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
                    "Version": "2.0.0",
                    "ConfigDevice": val["ConfigDevice"],
                    "Door": val["Door"],
                    "MntGrp": val["MntGrp"],
                })
            )
            rs.configDevice = val["ConfigDevice"]
            rs.door = val["Door"]
            rs.mntGrp = val["MntGrp"]

            self.assertEqual(rs.mntGrp, val["MntGrp"])

            mydata = {}
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

            self.compareToDump(rs, [])

        os.remove(filename)

    def generateChannelProperties(self):
        paths = dict(
            (self.getRandomName(10),
             self.getRandomName(15)) for _ in
            range(self.__rnd.randint(1, 40)))
        labels = dict(
            (self.getRandomName(10),
             self.getRandomName(15)) for _ in
            range(self.__rnd.randint(1, 40)))
        links = dict(
            (self.getRandomName(10),
             bool(self.__rnd.randint(0, 1))) for _ in
            range(self.__rnd.randint(1, 40)))
        types = dict(
            (self.getRandomName(10),
             self.getRandomName(15)) for _ in
            range(self.__rnd.randint(1, 40)))
        shapes = dict(
            (self.getRandomName(10),
             [self.__rnd.randint(1, 40)
              for _ in range(self.__rnd.randint(0, 3))])
            for _ in range(self.__rnd.randint(1, 40)))

        return json.dumps(
            {
                "label": labels,
                "nexus_path": paths,
                "link": links,
                "data_type": types,
                "shape": shapes
            }
        )

    def generateProfile(self, door, mg, cfdv, wrdv):
        msp = MacroServerPools(10)
        se = Selector(msp, "2.0.0")
        se["Door"] = door
        se["ConfigDevice"] = cfdv
        se["WriterDevice"] = wrdv
        se["MntGrp"] = mg
        msp.updateMacroServer(self._ms.door.keys()[0])
        wrong = []

        cps = {}
        lcp = self.__rnd.randint(1, 10)
        for _ in range(lcp):
            cps[self.getRandomName(10)] = self.getRandomName(
                self.__rnd.randint(1, 10))
        se["UserData"] = str(json.dumps(cps))

        cps = {}
        lcp = self.__rnd.randint(1, 10)
        for _ in range(lcp):
            cps[self.getRandomName(10)] = self.getRandomName(
                self.__rnd.randint(1, 10))
        se["ConfigVariables"] = str(json.dumps(cps))
        se["DefaultDynamicPath"] = self.getRandomName(10)
        se["TimeZone"] = self.getRandomName(10)
        se["AppendEntry"] = bool(self.__rnd.randint(0, 1))
        se["DynamicComponents"] = bool(self.__rnd.randint(0, 1))
        se["DefaultDynamicLinks"] = bool(self.__rnd.randint(0, 1))
        se["ComponentsFromMntGrp"] = bool(self.__rnd.randint(0, 1))
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
        ntms = self.__rnd.randint(1, 5)
        tms = self.__rnd.sample(set(
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
        self.__rnd.shuffle(pdss)

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
        lcp = self.__rnd.randint(1, 40)
        lds = self.__rnd.randint(1, 40)

        self._cf.dp.SetCommandVariable(
            ["CPDICT", json.dumps(amycps)])
        self._cf.dp.SetCommandVariable(
            ["DSDICT", json.dumps(amydss)])
        comps = set()

        ncps = self.__rnd.randint(1, len(amycps) - 1)
        lcps = self.__rnd.sample(set(amycps.keys()), ncps)
        for cp in lcps:
            if cp not in wrong:
                cps[cp] = bool(self.__rnd.randint(0, 1))
                if cps[cp]:
                    comps.add(cp)

        ancps = self.__rnd.randint(1, len(amycps.keys()) - 1)
        alcps = self.__rnd.sample(set(amycps.keys()), ancps)
        for cp in alcps:
            if cp not in wrong:
                acps[cp] = bool(self.__rnd.randint(0, 1))
                if acps[cp]:
                    comps.add(cp)

        ndss = self.__rnd.randint(1, len(amycps.keys()) - 1)
        ldss = self.__rnd.sample(set(amycps.keys()), ndss)
        for ds in ldss:
            if ds in amydss.keys():
                if ds not in wrong:
                    dss[ds] = bool(self.__rnd.randint(0, 1))

        ndss = self.__rnd.randint(1, len(amydss.keys()) - 1)
        ldss = self.__rnd.sample(set(amydss.keys()), ndss)
        for ds in ldss:
            if ds in amydss.keys():
                if ds not in wrong:
                    dss[ds] = bool(self.__rnd.randint(0, 1))

        nadss = self.__rnd.randint(1, len(amydss.keys()) - 1)
        aadss = [ds for ds in self.__rnd.sample(
            set(amydss.keys()), nadss)]
        nadss = self.__rnd.randint(1, len(amydss.keys()) - 1)
        indss = [ds for ds in self.__rnd.sample(
            set(amydss.keys()), nadss)]

        for tm in ltimers:
            dss[tm] = bool(self.__rnd.randint(0, 1))

        mncps = self.__rnd.randint(1, len(amycps.keys()) - 1)
        mcps = [cp for cp in self.__rnd.sample(
                set(amycps.keys()), mncps) if cp not in wrong]
        oncps = self.__rnd.randint(1, len(amycps.keys()) - 1)
        ocps = [cp for cp in self.__rnd.sample(
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
        se["PreselectedDataSources"] = \
            json.dumps(aadss)
        se["OptionalComponents"] = json.dumps(ocps)
        se["InitDataSources"] = json.dumps(indss)
        se["AppendEntry"] = bool(self.__rnd.randint(0, 1))
        se["ComponentsFromMntGrp"] = bool(
            self.__rnd.randint(0, 1))
        se["DynamicComponents"] = bool(
            self.__rnd.randint(0, 1))
        se["DefaultDynamicLinks"] = \
            bool(self.__rnd.randint(0, 1))
        se["DefaultDynamicPath"] = self.getRandomName(20)
        se["TimeZone"] = self.getRandomName(20)

        se["ConfigVariables"] = json.dumps(dict(
            (self.getRandomName(10),
             self.getRandomName(15)) for _ in
            range(self.__rnd.randint(1, 40))))
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
            nhe = self.__rnd.randint(0, len(set(chds)) - 1)
            lheds = self.__rnd.sample(set(chds), nhe)

        lhecp = []
        if comps:
            nhe = self.__rnd.randint(0, len(set(comps)) - 1)
            lhecp = self.__rnd.sample(set(comps), nhe)

        lhe = lheds + lhecp

        se["UnplottedComponents"] = json.dumps(lhe)
        se["OrderedChannels"] = json.dumps(pdss)

        se.updatePreselectedComponents()
        return str(json.dumps(se.get()))

    ## userdata test
    def test_channelProperties(self):
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
        sets = ["PreselectedDataSources"]
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
                db = PyTango.Database()
                db.put_device_property(self._ms.ms.keys()[0],
                                       {'PoolNames': self._pool.dp.name()})

                self._ms.dps[self._ms.ms.keys()[0]].Init()

                self.dump(rs)

                mydict = {}
                if (i / 2) % 2:
                    mydict = json.loads(rs.profileConfiguration)
                elif (i / 2) % 4 == 0:
                    rs.exportEnvProfile()
                    env = pickle.loads(
                        self._ms.dps[self._ms.ms.keys()[0]].Environment[1])
                    jmd = json.loads(rs.profileConfiguration)
                    for k in self.names(rs):
                        try:
                            self.assertEqual(
                                jmd[k],
                                env["new"]["NeXusConfiguration"][k])
                        except:
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
                        "Version": "2.0.0",
                        "ConfigDevice": val["ConfigDevice"],
                        "Door": val["Door"],
                        "MntGrp": val["MntGrp"],
                    })
                )
                rs.configDevice = val["ConfigDevice"]
                rs.door = val["Door"]
                rs.mntGrp = val["MntGrp"]

                self.assertEqual(rs.userData, "{}")

                mydata = {}
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

    ## userdata test
    def test_profileConfiguration(self):
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
        sets = ["PreselectedDataSources"]
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
                db = PyTango.Database()
                db.put_device_property(self._ms.ms.keys()[0],
                                       {'PoolNames': self._pool.dp.name()})

                self._ms.dps[self._ms.ms.keys()[0]].Init()
                chprop = json.loads(self.generateChannelProperties())
                for nm, vl in chprop.items():
                    rs.setChannelProperties([nm, json.dumps(vl)])

                self.dump(rs)

                mydict = {}
                if (i / 2) % 2:
                    mydict = json.loads(rs.profileConfiguration)
                elif (i / 2) % 4 == 0:
                    rs.exportEnvProfile()
                    env = pickle.loads(
                        self._ms.dps[self._ms.ms.keys()[0]].Environment[1])
                    jmd = json.loads(rs.profileConfiguration)
                    for k in self.names(rs):
                        try:
                            self.assertEqual(
                                jmd[k],
                                env["new"]["NeXusConfiguration"][k])
                        except:
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
                        "Version": "2.0.0",
                        "ConfigDevice": val["ConfigDevice"],
                        "Door": val["Door"],
                        "MntGrp": val["MntGrp"],
                    })
                )
                rs.configDevice = val["ConfigDevice"]
                rs.door = val["Door"]
                rs.mntGrp = val["MntGrp"]

                self.assertEqual(rs.userData, "{}")

                mydata = {}
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

    ## test
    # \brief It tests default settings
    def test_scanEnvVariables(self):
        fun = sys._getframe().f_code.co_name
        print "Run: %s.%s() " % (self.__class__.__name__, fun)
        val = {"ConfigDevice": self._cf.dp.name(),
               "WriterDevice": self._wr.dp.name(),
               "Door": 'doortestp09/testts/t1r228',
               "MntGrp": 'nxsmntgrp'}
        db = PyTango.Database()
        db.put_device_property(self._ms.ms.keys()[0],
                               {'PoolNames': self._pool.dp.name()})
        self._ms.dps[self._ms.ms.keys()[0]].Init()
        rs = self.openRecSelector()
        rs.configDevice = val["ConfigDevice"]
        rs.door = val["Door"]
        rs.mntGrp = val["MntGrp"]

        db = PyTango.Database()
        db.put_device_property(self._ms.ms.keys()[0],
                               {'PoolNames': self._pool.dp.name()})

        self._ms.dps[self._ms.ms.keys()[0]].Init()

        envs = [
            pickle.dumps(
                {
                    "new": {"ScanDir": "/tmp"}
                }
            ),
            pickle.dumps(
                {
                    "new": {"ScanDir": "/tmp", "ScanID": 11}
                }
            ),
            pickle.dumps(
                {
                    "new": {"ScanDir": "/tmp", "ScanFile": ["file.nxs"]}
                }
            ),
            pickle.dumps(
                {
                    "new": {
                        "ScanDir": "/tmp", "ScanID": 13,
                        "ScanFile": ["file.nxs"],
                        "NeXusConfigServer": "ptr/ert/ert",
                    }
                }
            ),
            pickle.dumps(
                {
                    "new": {
                        "ScanDir": "/tmp",
                        "ScanFile": ["file.nxs", "file2.nxs"],
                        "NeXusSelectorDevice": "p09/nxsrecselector/1",
                        "NeXusConfiguration": {"ConfigServer": "ptr/ert/ert2"},
                    }
                }
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
                }
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
                }
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
                }
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
            self._ms.dps[self._ms.ms.keys()[0]].Environment = (
                'pickle', envs[i])
            dt = rs.scanEnvVariables()
            self.myAssertDict(edats[i], json.loads(dt))

    ## test
    # \brief It tests default settings
    def test_setScanEnvVariables(self):
        fun = sys._getframe().f_code.co_name
        print "Run: %s.%s() " % (self.__class__.__name__, fun)
        val = {"ConfigDevice": self._cf.dp.name(),
               "WriterDevice": self._wr.dp.name(),
               "Door": 'doortestp09/testts/t1r228',
               "MntGrp": 'nxsmntgrp'}
        db = PyTango.Database()
        db.put_device_property(self._ms.ms.keys()[0],
                               {'PoolNames': self._pool.dp.name()})

        self._ms.dps[self._ms.ms.keys()[0]].Init()
        rs = self.openRecSelector()
        rs.configDevice = val["ConfigDevice"]
        rs.door = val["Door"]
        rs.mntGrp = val["MntGrp"]

        db = PyTango.Database()
        db.put_device_property(self._ms.ms.keys()[0],
                               {'PoolNames': self._pool.dp.name()})

        self._ms.dps[self._ms.ms.keys()[0]].Init()

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
            print "I = ", i, sid
            self.assertEqual(sid, sids[i])
            data = {}
            env = pickle.loads(
                self._ms.dps[self._ms.ms.keys()[0]].Environment[1])
            self.myAssertDict(envs[i], env)

    ## test
    def test_administratorDataNames(self):
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
        self.assertEqual(rs.configDevice, val["ConfigDevice"])
        self.assertEqual(rs.door, val["Door"])
        self.assertEqual(rs.administratorDataNames(), [])

        for _ in range(20):
            lcp = self.__rnd.randint(1, 10)
            anames = list(set([self.getRandomName(
                self.__rnd.randint(1, 10)) for _ in range(lcp)]))
            self.setProp(rs, "adminDataNames",
                         anames)
            self.assertEqual(rs.administratorDataNames(), anames)

    ## test
    def test_getDeviceGroups(self):
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
        self.assertEqual(rs.configDevice, val["ConfigDevice"])
        self.assertEqual(rs.door, val["Door"])
        ddg = '{"timer": ["*exp_t*"], "dac": ["*exp_dac*"], ' \
              + '"counter": ["*exp_c*"], "mca": ["*exp_mca*"], ' \
              + '"adc": ["*exp_adc*"], "motor": ["*exp_mot*"]}'

        self.assertEqual(rs.deviceGroups, ddg)

        for _ in range(20):
            lcp = self.__rnd.randint(1, 10)
            anames = list(set([self.getRandomName(
                self.__rnd.randint(1, 10)) for _ in range(lcp)]))
            dg = {}
            for an in anames:
                lp = self.__rnd.randint(1, 10)
                gr = list(set([self.getRandomName(
                    self.__rnd.randint(1, 10)) for _ in range(lp)]))
                dg[an] = gr
            jdg = json.dumps(dg)
            rs.deviceGroups = jdg
            self.assertEqual(rs.deviceGroups, jdg)

        for _ in range(20):
            rnm = self.getRandomName(self.__rnd.randint(1, 10))
            rs.deviceGroups = rnm
            try:
                ld = json.loads(rnm)
            except:
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

    ## test
    def test_stepdatasources(self):
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
        self.assertEqual(rs.configDevice, val["ConfigDevice"])
        self.assertEqual(rs.door, val["Door"])
        self.assertEqual(rs.stepdatasources, '[]')

        for _ in range(20):
            lcp = self.__rnd.randint(1, 10)
            anames = list(set([self.getRandomName(
                self.__rnd.randint(1, 10)) for _ in range(lcp)]))
            rs.stepdatasources = str(json.dumps(anames))
            mds2 = json.loads(self._cf.dp.stepdatasources)
            mds = json.loads(rs.stepdatasources)
            self.assertEqual(set(mds), set(anames))
            self.assertEqual(set(mds2), set(anames))

        for _ in range(20):
            lcp = self.__rnd.randint(1, 10)
            anames = list(set([self.getRandomName(
                self.__rnd.randint(1, 10)) for _ in range(lcp)]))
            self._cf.dp.stepdatasources = str(json.dumps(anames))
            mds2 = json.loads(self._cf.dp.stepdatasources)
            mds = json.loads(rs.stepdatasources)
            self.assertEqual(set(mds), set(anames))
            self.assertEqual(set(mds2), set(anames))

    ## test
    def test_deleteAllProfiles(self):
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

    ## availableMntGrps test
    def test_availableMntGrps(self):
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
        self.assertEqual(rs.configDevice, val["ConfigDevice"])
        self.assertEqual(rs.door, val["Door"])

        self.assertEqual(rs.availableMntGrps(), [])

        db = PyTango.Database()
        db.put_device_property(self._ms.ms.keys()[0],
                               {'PoolNames': self._pool.dp.name()})
        pool = self._pool.dp
        self._ms.dps[self._ms.ms.keys()[0]].Init()

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
                           self._ms.ms.keys()[0])
            print MSUtils.getEnv('ActiveMntGrp', self._ms.ms.keys()[0])
            dd = rs.availableMntGrps()
            self.assertEqual(dd[0], ar["name"])
            self.assertEqual(set(dd), set([a["name"] for a in arr]))

    ## availableMntGrps test
    def test_availableMntGrps_twopools(self):
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
        self.assertEqual(rs.configDevice, val["ConfigDevice"])
        self.assertEqual(rs.door, val["Door"])

        self.assertEqual(rs.availableMntGrps(), [])

        try:
            tpool2 = TestPoolSetUp.TestPoolSetUp(
                "pooltestp09/testts/t2r228", "POOLTESTS2")
            tpool2.setUp()

            db = PyTango.Database()
            db.put_device_property(
                self._ms.ms.keys()[0],
                {'PoolNames': [
                    tpool2.dp.name(), self._pool.dp.name()]})
            pool = self._pool.dp
            pool2 = tpool2.dp
            self._ms.dps[self._ms.ms.keys()[0]].Init()

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

            pnames = self._ms.dps[
                self._ms.ms.keys()[0]
            ].get_property("PoolNames")["PoolNames"]

            if pnames[0] == "pooltestp09/testts/t2r228":
                arr = arr2
            else:
                arr = arr1

            dd = rs.availableMntGrps()
            self.assertEqual(set(dd), set([a["name"] for a in arr]))

            for ar in arr1:

                MSUtils.setEnv('ActiveMntGrp', ar["name"],
                               self._ms.ms.keys()[0])
                dd = rs.availableMntGrps()
                self.assertEqual(dd[0], ar["name"])
                if arr1 == arr or ar["name"] != 'null':
                    self.assertEqual(set(dd), set([a["name"] for a in arr1]))
                else:
                    self.assertEqual(set(dd), set([a["name"] for a in arr]))

            for ar in arr2:
                MSUtils.setEnv('ActiveMntGrp', ar["name"],
                               self._ms.ms.keys()[0])
                dd = rs.availableMntGrps()
                self.assertEqual(dd[0], ar["name"])
                if arr2 == arr or ar["name"] != 'null':
                    self.assertEqual(set(dd), set([a["name"] for a in arr2]))
                else:
                    self.assertEqual(set(dd), set([a["name"] for a in arr]))
        finally:
            tpool2.tearDown()

    ## deleteProfile test
    def test_deleteProfile(self):
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
        self.assertEqual(rs.configDevice, val["ConfigDevice"])
        self.assertEqual(rs.door, val["Door"])

        db = PyTango.Database()
        db.put_device_property(self._ms.ms.keys()[0],
                               {'PoolNames': self._pool.dp.name()})
        pool = self._pool.dp
        self._ms.dps[self._ms.ms.keys()[0]].Init()

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
        mgs = [ar["name"] for ar in arr] + self.mysel2.keys()
        print mgs
        for ar in mgs:
            MSUtils.setEnv('ActiveMntGrp', ar, self._ms.ms.keys()[0])
            rs.deleteProfile(ar)
            dl.append(ar)
            self.assertEqual(MSUtils.getEnv(
                'ActiveMntGrp', self._ms.ms.keys()[0]), "")
            dd = rs.availableMntGrps()
            self.assertEqual(set(dd), set(dd2) - set(dl))
            sl = self._cf.dp.availableSelections()
            self.assertEqual(set(sl), set(sl2) - set(dl))

    ## deleteProfile test
    def test_deleteProfile_twopools(self):
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
        self.assertEqual(rs.configDevice, val["ConfigDevice"])
        self.assertEqual(rs.door, val["Door"])

        self.assertEqual(rs.availableMntGrps(), [])

        try:
            tpool2 = TestPoolSetUp.TestPoolSetUp(
                "pooltestp09/testts/t2r228", "POOLTESTS2")
            tpool2.setUp()

            db = PyTango.Database()
            db.put_device_property(
                self._ms.ms.keys()[0],
                {
                    'PoolNames': [
                        tpool2.dp.name(), self._pool.dp.name()]})
            pool = self._pool.dp
            pool2 = tpool2.dp
            self._ms.dps[self._ms.ms.keys()[0]].Init()

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
                'ActiveMntGrp', arr[0]["name"], self._ms.ms.keys()[0])

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
            mgs = [ar["name"] for ar in arr] + self.mysel2.keys()
            for ar in mgs:
                MSUtils.setEnv('ActiveMntGrp', ar, self._ms.ms.keys()[0])
                rs.deleteProfile(ar)
                dl.append(ar)
                self.assertEqual(MSUtils.getEnv(
                    'ActiveMntGrp', self._ms.ms.keys()[0]), "")
                dd = [json.loads(mg)["name"]
                      for mg in pool.MeasurementGroupList]
                dd_2 = [json.loads(mg)["name"]
                        for mg in pool2.MeasurementGroupList]
                self.assertEqual(set(dd), set(dd1) - set(dl))
                self.assertEqual(set(dd_2), set(dd2) - set(dl))
                sl = self._cf.dp.availableSelections()
                self.assertEqual(set(sl), set(sl2) - set(dl))

            dl = []
            mgs = [ar["name"] for ar in arr2] + self.mysel2.keys()
            dd1 = [json.loads(mg)["name"] for mg in pool.MeasurementGroupList]
            dd2 = [json.loads(mg)["name"] for mg in pool2.MeasurementGroupList]
            sl2 = self._cf.dp.availableSelections()
            for ar in mgs:
                MSUtils.setEnv('ActiveMntGrp', ar, self._ms.ms.keys()[0])
                rs.deleteProfile(ar)
                dl.append(ar)
                self.assertEqual(MSUtils.getEnv(
                    'ActiveMntGrp', self._ms.ms.keys()[0]), "")
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

    ## test
    def test_preselectedComponents(self):
        fun = sys._getframe().f_code.co_name
        print "Run: %s.%s() " % (self.__class__.__name__, fun)
        val = {"ConfigDevice": self._cf.dp.name(),
               "WriterDevice": self._wr.dp.name(),
               "Door": 'doortestp09/testts/t1r228',
               "MntGrp": 'nxsmntgrp'}

        for i in range(20):
            rs = self.openRecSelector()
            rs.configDevice = val["ConfigDevice"]
            rs.door = val["Door"]
            rs.mntGrp = val["MntGrp"]
            self.assertEqual(rs.configDevice, val["ConfigDevice"])
            self.assertEqual(rs.door, val["Door"])

            cps = {}
            lcp = self.__rnd.randint(1, 40)
            for i in range(lcp):
                cps[self.getRandomName(10)] = bool(self.__rnd.randint(0, 1))
            mp = json.loads(rs.profileConfiguration)
            mp["ComponentPreselection"] = json.dumps(cps)
            rs.profileConfiguration = str(json.dumps(mp))
            self.dump(rs)

            ac = rs.preselectedComponents()
            mp = json.loads(rs.profileConfiguration)
            self.compareToDump(rs, ["ComponentPreselection"])
            ndss = json.loads(mp["ComponentPreselection"])

            acp = []
            for ds in cps.keys():
                self.assertTrue(ds in ndss.keys())
                self.assertEqual(ndss[ds], cps[ds])
                if ndss[ds]:
                    acp.append(ds)

            self.assertEqual(set(ac), set(acp))

    ## test
    def test_selectedcomponents(self):
        fun = sys._getframe().f_code.co_name
        print "Run: %s.%s() " % (self.__class__.__name__, fun)
        val = {"ConfigDevice": self._cf.dp.name(),
               "WriterDevice": self._wr.dp.name(),
               "Door": 'doortestp09/testts/t1r228',
               "MntGrp": 'nxsmntgrp'}

        for i in range(20):
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

            mp = json.loads(rs.profileConfiguration)
            mp["OrderedChannels"] = json.dumps([])
            rs.profileConfiguration = str(json.dumps(mp))

            cps = {}
            dss = {}
            lcp = self.__rnd.randint(1, 40)
            lds = self.__rnd.randint(1, 40)
            for i in range(lcp):
                cps[self.getRandomName(10)] = bool(self.__rnd.randint(0, 1))
            for i in range(lds):
                dss[self.getRandomName(10)] = bool(self.__rnd.randint(0, 1))
            ddss = self.__rnd.sample(dss, self.__rnd.randint(
                1, len(dss.keys())))
            dcps = dict(cps)
            for ds in ddss:
                dcps[ds] = bool(self.__rnd.randint(0, 1))

            self._cf.dp.SetCommandVariable(["CPDICT", json.dumps(dcps)])
            self._cf.dp.SetCommandVariable(["DSDICT", json.dumps(dss)])

            mp = json.loads(rs.profileConfiguration)
            mp["ComponentSelection"] = json.dumps(cps)
            mp["DataSourceSelection"] = json.dumps(dss)
            rs.profileConfiguration = str(json.dumps(mp))
            mp = json.loads(rs.profileConfiguration)

            ndss = json.loads(mp["DataSourceSelection"])
            common = set(cps.keys()) & set(dss.keys())
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

    ## test
    def test_componentDescription_unknown(self):
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
        rs.writerDevice = val["WriterDevice"]
        self.assertEqual(rs.configDevice, val["ConfigDevice"])
        self.assertEqual(rs.door, val["Door"])
        db = PyTango.Database()
        db.put_device_property(self._ms.ms.keys()[0],
                               {'PoolNames': self._pool.dp.name()})
        pool = self._pool.dp
        pool.ExpChannelList = []
        self._ms.dps[self._ms.ms.keys()[0]].Init()

        mp = json.loads(rs.profileConfiguration)
        mp["OrderedChannels"] = json.dumps([])
        rs.profileConfiguration = str(json.dumps(mp))

        cps = {}
        dss = {}
        lcp = self.__rnd.randint(1, 40)
        lds = self.__rnd.randint(1, 40)

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

        ndss = json.loads(mp["DataSourceSelection"])
        common = set(cps) & set(dss)
        self.dump(rs)

        ncps = json.loads(mp["ComponentSelection"])
        ndss = json.loads(mp["DataSourceSelection"])
        tdss = [ds for ds in ndss if ndss[ds]]
        tcps = [cp for cp in ncps if ncps[cp]]

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

    ## test
    def test_componentDescription_full(self):
        fun = sys._getframe().f_code.co_name
        print "Run: %s.%s() " % (self.__class__.__name__, fun)
        val = {"ConfigDevice": self._cf.dp.name(),
               "WriterDevice": self._wr.dp.name(),
               "Door": 'doortestp09/testts/t1r228',
               "MntGrp": 'nxsmntgrp'}

        for i in range(20):
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

            mp = json.loads(rs.profileConfiguration)
            mp["OrderedChannels"] = json.dumps([])
            rs.profileConfiguration = str(json.dumps(mp))

            dsdict = {
                "ann": self.mydss["ann"]
            }

            cps = {}
            dss = {}
            lcp = self.__rnd.randint(1, 40)
            lds = self.__rnd.randint(1, 40)

            self._cf.dp.SetCommandVariable(["CPDICT", json.dumps(self.mycps)])
            self._cf.dp.SetCommandVariable(["DSDICT", json.dumps(self.mydss)])

            ncps = self.__rnd.randint(1, len(self.mycps.keys()) - 1)
            lcps = self.__rnd.sample(set(self.mycps.keys()), ncps)
            for cp in lcps:
                cps[cp] = bool(self.__rnd.randint(0, 1))

            mncps = self.__rnd.randint(1, len(self.mycps.keys()) - 1)
            mcps = self.__rnd.sample(set(self.mycps.keys()), mncps)

            tdss = [ds for ds in dss if dss[ds]]
            tcps = [cp for cp in cps if cps[cp]]

            self._cf.dp.SetCommandVariable(["MCPLIST", json.dumps(mcps)])
            self._cf.dp.SetCommandVariable(["CPDICT", json.dumps(self.mycps)])
            self._cf.dp.SetCommandVariable(["DSDICT", json.dumps(self.mydss)])

            mp = json.loads(rs.profileConfiguration)
            mp["ComponentSelection"] = json.dumps(cps)
            mp["DataSourceSelection"] = json.dumps(dss)
            rs.profileConfiguration = str(json.dumps(mp))
            mp = json.loads(rs.profileConfiguration)
            ndss = json.loads(mp["DataSourceSelection"])
            common = set(cps) & set(dss)
            self.dump(rs)

            res = json.loads(rs.componentDescription())
            self.checkCP(res, self.rescps.keys())

    ## updateProfile test
    def test_componentdatasources(self):
        fun = sys._getframe().f_code.co_name
        print "Run: %s.%s() " % (self.__class__.__name__, fun)
        val = {"ConfigDevice": self._cf.dp.name(),
               "WriterDevice": self._wr.dp.name(),
               "Door": 'doortestp09/testts/t1r228',
               "MntGrp": 'nxsmntgrp'}

        for i in range(20):
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

            mp = json.loads(rs.profileConfiguration)
            mp["OrderedChannels"] = json.dumps([])
            rs.profileConfiguration = str(json.dumps(mp))

            cps = {}
            dss = {}
            lcp = self.__rnd.randint(1, 40)
            lds = self.__rnd.randint(1, 40)

            self._cf.dp.SetCommandVariable(["CPDICT", json.dumps(self.mycps)])
            self._cf.dp.SetCommandVariable(["DSDICT", json.dumps(self.mydss)])

            ncps = self.__rnd.randint(1, len(self.mycps.keys()) - 1)
            lcps = self.__rnd.sample(set(self.mycps.keys()), ncps)
            for cp in lcps:
                cps[cp] = bool(self.__rnd.randint(0, 1))

            ndss = self.__rnd.randint(1, len(self.mycps.keys()) - 1)
            ldss = self.__rnd.sample(set(self.mycps.keys()), ndss)
            for ds in ldss:
                if ds in self.mydss.keys():
                    dss[ds] = bool(self.__rnd.randint(0, 1))

            mncps = self.__rnd.randint(1, len(self.mycps.keys()) - 1)
            mcps = self.__rnd.sample(set(self.mycps.keys()), mncps)

            tdss = [ds for ds in dss if dss[ds]]
            tcps = [cp for cp in cps if cps[cp]]
            mp = json.loads(rs.profileConfiguration)
            mp["ComponentSelection"] = json.dumps(cps)
            mp["DataSourceSelection"] = json.dumps(dss)
            rs.profileConfiguration = str(json.dumps(mp))
            mp = json.loads(rs.profileConfiguration)

            self._cf.dp.SetCommandVariable(["MCPLIST", json.dumps(mcps)])
            ndss = json.loads(mp["DataSourceSelection"])
            common = set(cps) & set(dss)
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

    ## updateProfile test
    def test_selectedDatasources(self):
        fun = sys._getframe().f_code.co_name
        print "Run: %s.%s() " % (self.__class__.__name__, fun)
        val = {"ConfigDevice": self._cf.dp.name(),
               "WriterDevice": self._wr.dp.name(),
               "Door": 'doortestp09/testts/t1r228',
               "MntGrp": 'nxsmntgrp'}

        for i in range(20):
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

            mp = json.loads(rs.profileConfiguration)
            mp["OrderedChannels"] = json.dumps([])
            rs.profileConfiguration = str(json.dumps(mp))

            cps = {}
            dss = {}
            lcp = self.__rnd.randint(1, 40)
            lds = self.__rnd.randint(1, 40)

            self._cf.dp.SetCommandVariable(["CPDICT", json.dumps(self.mycps)])
            self._cf.dp.SetCommandVariable(["DSDICT", json.dumps(self.mydss)])

            ncps = self.__rnd.randint(1, len(self.mycps.keys()) - 1)
            lcps = self.__rnd.sample(set(self.mycps.keys()), ncps)
            for cp in lcps:
                cps[cp] = bool(self.__rnd.randint(0, 1))

            ndss = self.__rnd.randint(1, len(self.mycps.keys()) - 1)
            ldss = self.__rnd.sample(set(self.mycps.keys()), ndss)
            for ds in ldss:
                if ds in self.mydss.keys():
                    dss[ds] = bool(self.__rnd.randint(0, 1))

            ndss = self.__rnd.randint(1, len(self.mydss.keys()) - 1)
            ldss = self.__rnd.sample(set(self.mydss.keys()), ndss)
            for ds in ldss:
                if ds in self.mydss.keys():
                    dss[ds] = bool(self.__rnd.randint(0, 1))

            mncps = self.__rnd.randint(1, len(self.mycps.keys()) - 1)
            mcps = self.__rnd.sample(set(self.mycps.keys()), mncps)

            mp = json.loads(rs.profileConfiguration)
            mp["ComponentSelection"] = json.dumps(cps)
            mp["DataSourceSelection"] = json.dumps(dss)
            rs.profileConfiguration = str(json.dumps(mp))
            mp = json.loads(rs.profileConfiguration)
            self._cf.dp.SetCommandVariable(["MCPLIST", json.dumps(mcps)])
            ndss = json.loads(mp["DataSourceSelection"])
            common = set(cps) & set(dss)
            self.dump(rs)

            dds = rs.componentDataSources()
            rdss = rs.selectedDataSources()
            tdss = [ds for ds in dss if dss[ds] and ds not in dds]

            self.assertEqual(set(tdss), set(rdss))
            self.assertEqual(len(tdss), len(rdss))

    ## updateProfile test
    def test_datasources(self):
        fun = sys._getframe().f_code.co_name
        print "Run: %s.%s() " % (self.__class__.__name__, fun)
        val = {"ConfigDevice": self._cf.dp.name(),
               "WriterDevice": self._wr.dp.name(),
               "Door": 'doortestp09/testts/t1r228',
               "MntGrp": 'nxsmntgrp'}

        for i in range(20):
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

            mp = json.loads(rs.profileConfiguration)
            mp["OrderedChannels"] = json.dumps([])
            rs.profileConfiguration = str(json.dumps(mp))

            cps = {}
            dss = {}
            lcp = self.__rnd.randint(1, 40)
            lds = self.__rnd.randint(1, 40)

            self._cf.dp.SetCommandVariable(["CPDICT", json.dumps(self.mycps)])
            self._cf.dp.SetCommandVariable(["DSDICT", json.dumps(self.mydss)])

            ncps = self.__rnd.randint(1, len(self.mycps.keys()) - 1)
            lcps = self.__rnd.sample(set(self.mycps.keys()), ncps)
            for cp in lcps:
                cps[cp] = bool(self.__rnd.randint(0, 1))

            ndss = self.__rnd.randint(1, len(self.mycps.keys()) - 1)
            ldss = self.__rnd.sample(set(self.mycps.keys()), ndss)
            for ds in ldss:
                if ds in self.mydss.keys():
                    dss[ds] = bool(self.__rnd.randint(0, 1))

            ndss = self.__rnd.randint(1, len(self.mydss.keys()) - 1)
            ldss = self.__rnd.sample(set(self.mydss.keys()), ndss)
            for ds in ldss:
                if ds in self.mydss.keys():
                    dss[ds] = bool(self.__rnd.randint(0, 1))

            mncps = self.__rnd.randint(1, len(self.mycps.keys()) - 1)
            mcps = self.__rnd.sample(set(self.mycps.keys()), mncps)

            mp = json.loads(rs.profileConfiguration)
            mp["ComponentSelection"] = json.dumps(cps)
            mp["DataSourceSelection"] = json.dumps(dss)
            rs.profileConfiguration = str(json.dumps(mp))
            mp = json.loads(rs.profileConfiguration)
            self._cf.dp.SetCommandVariable(["MCPLIST", json.dumps(mcps)])
            ndss = json.loads(mp["DataSourceSelection"])
            common = set(cps) & set(dss)
            self.dump(rs)

            mds = rs.dataSources or []
            dds = rs.componentDataSources() or []
            rdss = rs.selectedDataSources() or []

            self.assertEqual(set(mds), set(dds) | set(rdss))

    ## test
    def test_selectedcomponents(self):
        fun = sys._getframe().f_code.co_name
        print "Run: %s.%s() " % (self.__class__.__name__, fun)
        val = {"ConfigDevice": self._cf.dp.name(),
               "WriterDevice": self._wr.dp.name(),
               "Door": 'doortestp09/testts/t1r228',
               "MntGrp": 'nxsmntgrp'}

        for i in range(20):
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

            mp = json.loads(rs.profileConfiguration)
            mp["OrderedChannels"] = json.dumps([])
            rs.profileConfiguration = str(json.dumps(mp))

            mncps = self.__rnd.randint(1, len(self.mycps.keys()) - 1)
            mcps = [cp for cp in self.__rnd.sample(
                set(self.mycps.keys()), mncps)]

            cps = {}
            dss = {}
            lcp = self.__rnd.randint(1, 40)
            lds = self.__rnd.randint(1, 40)
            for i in range(lcp):
                cps[self.getRandomName(10)] = bool(self.__rnd.randint(0, 1))
            for i in range(lds):
                dss[self.getRandomName(10)] = bool(self.__rnd.randint(0, 1))
            ddss = self.__rnd.sample(dss, self.__rnd.randint(
                1, len(dss.keys())))
            dcps = dict(cps)
            for ds in ddss:
                dcps[ds] = bool(self.__rnd.randint(0, 1))

            pcps = {}
            plcp = self.__rnd.randint(1, 40)
            for i in range(plcp):
                pcps[self.getRandomName(10)] = bool(self.__rnd.randint(0, 1))

            self._cf.dp.SetCommandVariable(["CPDICT", json.dumps(dcps)])
            self._cf.dp.SetCommandVariable(["DSDICT", json.dumps(dss)])
            self._cf.dp.SetCommandVariable(["MCPLIST", json.dumps(mcps)])

            mp = json.loads(rs.profileConfiguration)
            mp["ComponentSelection"] = json.dumps(cps)
            mp["DataSourceSelection"] = json.dumps(dss)
            mp["ComponentPreselection"] = json.dumps(cps)
            rs.profileConfiguration = str(json.dumps(mp))
            ac = rs.preselectedComponents()
            mp = json.loads(rs.profileConfiguration)

            ndss = json.loads(mp["DataSourceSelection"])
            common = set(cps.keys()) & set(dss.keys())
            self.dump(rs)

            ncps = json.loads(mp["ComponentSelection"])
            ndss = json.loads(mp["DataSourceSelection"])
            tdss = [ds for ds in ndss if ndss[ds]]
            tcps = [cp for cp in ncps if ncps[cp]]

            rcp = rs.components
            mcp = rs.mandatoryComponents()
            scp = rs.selectedComponents()
            pcp = rs.preselectedComponents()

            self.assertEqual(set(rcp), set(mcp) | set(scp) | set(pcp))

    ## updateMntGrp test
    def test_updateMntGrp_empty(self):
        fun = sys._getframe().f_code.co_name
        print "Run: %s.%s() " % (self.__class__.__name__, fun)
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

        db = PyTango.Database()
        db.put_device_property(self._ms.ms.keys()[0],
                               {'PoolNames': self._pool.dp.name()})
        pool = self._pool.dp
        pool.ExpChannelList = []
        self._ms.dps[self._ms.ms.keys()[0]].Init()

        self.assertEqual(rs.availableMntGrps(), [])

        arr = [
            {"full_name": "test/ct/01/Value", "name": "ct01"},
            {"full_name": "test/ct/02/Value", "name": "ct02"},
            {"full_name": "test/ct/03/value", "name": "ct03"},
            {"full_name": "test/ct/04/value", "name": "ct04"},
            {"full_name": "null/val", "name": "mntgrp_04"},
        ]
        pool.AcqChannelList = [json.dumps(a) for a in arr]

        self.myAssertRaise(Exception, rs.updateMntGrp)
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
                mgdp = PyTango.DeviceProxy(tmg.new_device_info_writer.name)
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

    ## updateMntGrp test
    def test_updateMntGrp_components_nopool(self):
        fun = sys._getframe().f_code.co_name
        print "Run: %s.%s() " % (self.__class__.__name__, fun)
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

        db = PyTango.Database()
        db.put_device_property(self._ms.ms.keys()[0],
                               {'PoolNames': self._pool.dp.name()})
        pool = self._pool.dp
        pool.ExpChannelList = []
        self._ms.dps[self._ms.ms.keys()[0]].Init()

        self.assertEqual(rs.availableMntGrps(), [])

        arr = [
            {"full_name": "test/ct/01/Value", "name": "ct01"},
            {"full_name": "test/ct/02/Value", "name": "ct02"},
            {"full_name": "test/ct/03/value", "name": "ct03"},
            {"full_name": "test/ct/04/value", "name": "ct04"},
            {"full_name": "null/val", "name": "mntgrp_04"},
        ]
        pool.AcqChannelList = [json.dumps(a) for a in arr]

        self.myAssertRaise(Exception, rs.updateMntGrp)
        self._cf.dp.SetCommandVariable(["CPDICT", json.dumps(self.mycps)])
        self._cf.dp.SetCommandVariable(["DSDICT", json.dumps(self.mydss)])

        for i in range(30):
            ar = arr[i % len(arr)]
            cps = {}
            acps = {}
            dss = {}
            lcp = self.__rnd.randint(1, 40)
            lds = self.__rnd.randint(1, 40)

            self._cf.dp.SetCommandVariable(["CPDICT", json.dumps(self.mycps)])
            self._cf.dp.SetCommandVariable(["DSDICT", json.dumps(self.mydss)])

            ncps = self.__rnd.randint(1, len(self.mycps.keys()) - 1)
            lcps = self.__rnd.sample(set(self.mycps.keys()), ncps)
            for cp in lcps:
                if cp not in wrong:
                    cps[cp] = bool(self.__rnd.randint(0, 1))

            ancps = self.__rnd.randint(1, len(self.mycps.keys()) - 1)
            alcps = self.__rnd.sample(set(self.mycps.keys()), ancps)
            for cp in alcps:
                if cp not in wrong:
                    acps[cp] = bool(self.__rnd.randint(0, 1))

            ndss = self.__rnd.randint(1, len(self.mycps.keys()) - 1)
            ldss = self.__rnd.sample(set(self.mycps.keys()), ndss)
            for ds in ldss:
                if ds in self.mydss.keys():
                    if ds not in wrong:
                        dss[ds] = bool(self.__rnd.randint(0, 1))

            ndss = self.__rnd.randint(1, len(self.mydss.keys()) - 1)
            ldss = self.__rnd.sample(set(self.mydss.keys()), ndss)
            for ds in ldss:
                if ds in self.mydss.keys():
                    if ds not in wrong:
                        dss[ds] = bool(self.__rnd.randint(0, 1))

            mncps = self.__rnd.randint(1, len(self.mycps.keys()) - 1)
            mcps = [cp for cp in self.__rnd.sample(
                    set(self.mycps.keys()), mncps) if cp not in wrong]

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
            dsres = describer.dataSources(dss.keys(), dstype='CLIENT')[0]
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
                mdds = set()

                jpcnf = rs.updateMntGrp()
                pcnf = json.loads(jpcnf)
                mgdp = PyTango.DeviceProxy(tmg.new_device_info_writer.name)
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
                except:
                    pass

    ## updateMntGrp test
    def test_updateMntGrp_nodevice(self):
        fun = sys._getframe().f_code.co_name
        print "Run: %s.%s() " % (self.__class__.__name__, fun)
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

        db = PyTango.Database()
        db.put_device_property(self._ms.ms.keys()[0],
                               {'PoolNames': self._pool.dp.name()})
        pool = self._pool.dp
        pool.ExpChannelList = []
        self._ms.dps[self._ms.ms.keys()[0]].Init()

        self.assertEqual(rs.availableMntGrps(), [])

        arr = [
            {"full_name": "test/ct/01/Value", "name": "ct01"},
            {"full_name": "test/ct/02/Value", "name": "ct02"},
            {"full_name": "test/ct/03/value", "name": "ct03"},
            {"full_name": "test/ct/04/value", "name": "ct04"},
            {"full_name": "null/val", "name": "mntgrp_04"},
        ]
        pool.AcqChannelList = [json.dumps(a) for a in arr]

        self.myAssertRaise(Exception, rs.updateMntGrp)
        self._cf.dp.SetCommandVariable(["CPDICT", json.dumps(self.mycps)])
        self._cf.dp.SetCommandVariable(["DSDICT", json.dumps(self.mydss)])

        ar = arr[0]

        cps = {}
        acps = {}
        dss = {}
        lcp = self.__rnd.randint(1, 40)
        lds = self.__rnd.randint(1, 40)

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
            dsres = describer.dataSources(dss.keys(), dstype='CLIENT')[0]
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
                self.myAssertRaise(Exception, rs.updateMntGrp)
            finally:
                rs.deleteProfile("nxsmntgrp2")
                try:
                    tmg.tearDown()
                except:
                    pass

    ## updateMntGrp test
    def test_updateMntGrp_nodevice_cp(self):
        fun = sys._getframe().f_code.co_name
        print "Run: %s.%s() " % (self.__class__.__name__, fun)
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

        db = PyTango.Database()
        db.put_device_property(self._ms.ms.keys()[0],
                               {'PoolNames': self._pool.dp.name()})
        pool = self._pool.dp
        pool.ExpChannelList = []
        self._ms.dps[self._ms.ms.keys()[0]].Init()

        self.assertEqual(rs.availableMntGrps(), [])

        arr = [
            {"full_name": "test/ct/01/Value", "name": "ct01"},
            {"full_name": "test/ct/02/Value", "name": "ct02"},
            {"full_name": "test/ct/03/value", "name": "ct03"},
            {"full_name": "test/ct/04/value", "name": "ct04"},
            {"full_name": "null/val", "name": "mntgrp_04"},
        ]
        pool.AcqChannelList = [json.dumps(a) for a in arr]

        self.myAssertRaise(Exception, rs.updateMntGrp)
        self._cf.dp.SetCommandVariable(["CPDICT", json.dumps(self.mycps)])
        self._cf.dp.SetCommandVariable(["DSDICT", json.dumps(self.mydss)])

        ar = arr[0]

        cps = {}
        acps = {}
        dss = {}
        lcp = self.__rnd.randint(1, 40)
        lds = self.__rnd.randint(1, 40)

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
            dsres = describer.dataSources(dss.keys(), dstype='CLIENT')[0]
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
                self.myAssertRaise(Exception, rs.updateMntGrp)
            finally:
                try:
                    tmg.tearDown()
                except:
                    pass

    ## updateMntGrp test
    def test_updateMntGrp_wrongdevice(self):
        fun = sys._getframe().f_code.co_name
        print "Run: %s.%s() " % (self.__class__.__name__, fun)
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

        db = PyTango.Database()
        db.put_device_property(self._ms.ms.keys()[0],
                               {'PoolNames': self._pool.dp.name()})
        pool = self._pool.dp
        pool.ExpChannelList = []
        self._ms.dps[self._ms.ms.keys()[0]].Init()

        self.assertEqual(rs.availableMntGrps(), [])

        arr = [
            {"full_name": "test/ct/01/Value", "name": "ct01"},
            {"full_name": "test/ct/02/Value", "name": "ct02"},
            {"full_name": "test/ct/03/value", "name": "ct03"},
            {"full_name": "test/ct/04/value", "name": "ct04"},
            {"full_name": "null/val", "name": "mntgrp_04"},
        ]
        pool.AcqChannelList = [json.dumps(a) for a in arr]

        self.myAssertRaise(Exception, rs.updateMntGrp)
        self._cf.dp.SetCommandVariable(["CPDICT", json.dumps(self.mycps)])
        self._cf.dp.SetCommandVariable(["DSDICT", json.dumps(self.mydss)])

        ar = arr[0]

        cps = {}
        acps = {}
        dss = {}
        lcp = self.__rnd.randint(1, 40)
        lds = self.__rnd.randint(1, 40)

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
            dsres = describer.dataSources(dss.keys(), dstype='CLIENT')[0]
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
                self.myAssertRaise(Exception, rs.updateMntGrp)
            finally:
                try:
                    tmg.tearDown()
                except:
                    pass

    ## updateMntGrp test
    def test_updateMntGrp_components_nopool_tango(self):
        fun = sys._getframe().f_code.co_name
        print "Run: %s.%s() " % (self.__class__.__name__, fun)
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

        db = PyTango.Database()
        db.put_device_property(self._ms.ms.keys()[0],
                               {'PoolNames': self._pool.dp.name()})
        pool = self._pool.dp
        pool.ExpChannelList = []
        self._ms.dps[self._ms.ms.keys()[0]].Init()

        self.assertEqual(rs.availableMntGrps(), [])

        arr = [
            {"full_name": "test/ct/01/Value", "name": "ct01"},
            {"full_name": "test/ct/02/Value", "name": "ct02"},
            {"full_name": "test/ct/03/value", "name": "ct03"},
            {"full_name": "test/ct/04/value", "name": "ct04"},
            {"full_name": "null/val", "name": "mntgrp_04"},
        ]
        pool.AcqChannelList = [json.dumps(a) for a in arr]

        self.myAssertRaise(Exception, rs.updateMntGrp)
        self._cf.dp.SetCommandVariable(["CPDICT", json.dumps(self.smycps)])
        self._cf.dp.SetCommandVariable(["DSDICT", json.dumps(self.smydss)])

        for i in range(30):
            ar = arr[i % len(arr)]

            cps = {}
            acps = {}
            dss = {}
            lcp = self.__rnd.randint(1, 40)
            lds = self.__rnd.randint(1, 40)

            self._cf.dp.SetCommandVariable(["CPDICT", json.dumps(self.smycps)])
            self._cf.dp.SetCommandVariable(["DSDICT", json.dumps(self.smydss)])

            ncps = self.__rnd.randint(1, len(self.smycps.keys()) - 1)
            lcps = self.__rnd.sample(set(self.smycps.keys()), ncps)
            for cp in lcps:
                if cp not in wrong:
                    cps[cp] = bool(self.__rnd.randint(0, 1))

            ancps = self.__rnd.randint(1, len(self.smycps.keys()) - 1)
            alcps = self.__rnd.sample(set(self.smycps.keys()), ancps)
            for cp in alcps:
                if cp not in wrong:
                    acps[cp] = bool(self.__rnd.randint(0, 1))

            ndss = self.__rnd.randint(1, len(self.smycps.keys()) - 1)
            ldss = self.__rnd.sample(set(self.smycps.keys()), ndss)
            for ds in ldss:
                if ds in self.smydss.keys():
                    if ds not in wrong:
                        dss[ds] = bool(self.__rnd.randint(0, 1))

            ndss = self.__rnd.randint(1, len(self.smydss.keys()) - 1)
            ldss = self.__rnd.sample(set(self.smydss.keys()), ndss)
            for ds in ldss:
                if ds in self.smydss.keys():
                    if ds not in wrong:
                        dss[ds] = bool(self.__rnd.randint(0, 1))

            mncps = self.__rnd.randint(1, len(self.smycps.keys()) - 1)
            mcps = [cp for cp in self.__rnd.sample(
                    set(self.smycps.keys()), mncps) if cp not in wrong]

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
            dsres = describer.dataSources(dss.keys(), dstype='CLIENT')[0]
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

                mdds = set()
                for mdss in res[0].values():
                    if isinstance(mdss, dict):
                        for ds in mdss.keys():
                            dss[ds] = True

                jpcnf = rs.updateMntGrp()
                pcnf = json.loads(jpcnf)
                mgdp = PyTango.DeviceProxy(tmg.new_device_info_writer.name)
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
                        chn = {'ndim': 0,
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
                    except:
                        print ds, cnt
                        raise

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
                except:
                    pass

    ## updateProfile test
    def test_updateMntGrp_components_nopool_tango_unplottedcomponents(self):
        fun = sys._getframe().f_code.co_name
        print "Run: %s.%s() " % (self.__class__.__name__, fun)
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

        db = PyTango.Database()
        db.put_device_property(self._ms.ms.keys()[0],
                               {'PoolNames': self._pool.dp.name()})
        pool = self._pool.dp
        pool.ExpChannelList = []
        self._ms.dps[self._ms.ms.keys()[0]].Init()

        self.assertEqual(rs.availableMntGrps(), [])

        arr = [
            {"full_name": "test/ct/01/Value", "name": "ct01"},
            {"full_name": "test/ct/02/Value", "name": "ct02"},
            {"full_name": "test/ct/03/value", "name": "ct03"},
            {"full_name": "test/ct/04/value", "name": "ct04"},
            {"full_name": "null/val", "name": "mntgrp_04"},
        ]
        pool.AcqChannelList = [json.dumps(a) for a in arr]

        self.myAssertRaise(Exception, rs.updateMntGrp)
        self._cf.dp.SetCommandVariable(["CPDICT", json.dumps(self.smycps)])
        self._cf.dp.SetCommandVariable(["DSDICT", json.dumps(self.smydss)])

        for i in range(30):
            ar = arr[i % len(arr)]

            cps = {}
            acps = {}
            dss = {}
            lcp = self.__rnd.randint(1, 40)
            lds = self.__rnd.randint(1, 40)

            self._cf.dp.SetCommandVariable(["CPDICT", json.dumps(self.smycps)])
            self._cf.dp.SetCommandVariable(["DSDICT", json.dumps(self.smydss)])

            comps = set()
            ncps = self.__rnd.randint(1, len(self.smycps.keys()) - 1)
            lcps = self.__rnd.sample(set(self.smycps.keys()), ncps)
            for cp in lcps:
                if cp not in wrong:
                    cps[cp] = bool(self.__rnd.randint(0, 1))
                    if cps[cp]:
                        comps.add(cp)

            ancps = self.__rnd.randint(1, len(self.smycps.keys()) - 1)
            alcps = self.__rnd.sample(set(self.smycps.keys()), ancps)
            for cp in alcps:
                if cp not in wrong:
                    acps[cp] = bool(self.__rnd.randint(0, 1))
                    if acps[cp]:
                        comps.add(cp)

            ndss = self.__rnd.randint(1, len(self.smycps.keys()) - 1)
            ldss = self.__rnd.sample(set(self.smycps.keys()), ndss)
            for ds in ldss:
                if ds in self.smydss.keys():
                    if ds not in wrong:
                        dss[ds] = bool(self.__rnd.randint(0, 1))

            ndss = self.__rnd.randint(1, len(self.smydss.keys()) - 1)
            ldss = self.__rnd.sample(set(self.smydss.keys()), ndss)
            for ds in ldss:
                if ds in self.smydss.keys():
                    if ds not in wrong:
                        dss[ds] = bool(self.__rnd.randint(0, 1))

            mncps = self.__rnd.randint(1, len(self.smycps.keys()) - 1)
            mcps = [cp for cp in self.__rnd.sample(
                    set(self.smycps.keys()), mncps) if cp not in wrong]
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
            dsres = describer.dataSources(dss.keys(), dstype='CLIENT')[0]
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
            chds1 = list(chds)
            chds2 = [ds for ds in rs.componentDataSources()
                     if not ds.startswith('client')]
            chds.extend(chds2)
            chds = sorted(chds)

            lheds = []
            if chds:
                nhe = self.__rnd.randint(0, len(set(chds)) - 1)
                lheds = self.__rnd.sample(set(chds), nhe)

            lhecp = []
            if comps:
                nhe = self.__rnd.randint(0, len(set(comps)) - 1)
                lhecp = self.__rnd.sample(set(comps), nhe)

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

                mdds = set()
                for mdss in res[0].values():
                    if isinstance(mdss, dict):
                        for ds in mdss.keys():
                            dss[ds] = True

                jpcnf = rs.updateMntGrp()
                pcnf = json.loads(jpcnf)
                mgdp = PyTango.DeviceProxy(tmg.new_device_info_writer.name)
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
                        chn = {'ndim': 0,
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
                    except:
                        print ds, cnt
                        raise

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
                except:
                    pass

    ## updateMntGrp test
    def test_updateMntGrp_components_pool_tango(self):
        fun = sys._getframe().f_code.co_name
        print "Run: %s.%s() " % (self.__class__.__name__, fun)
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

        db = PyTango.Database()
        db.put_device_property(self._ms.ms.keys()[0],
                               {'PoolNames': self._pool.dp.name()})
        pool = self._pool.dp
        pool.ExpChannelList = []
        self._ms.dps[self._ms.ms.keys()[0]].Init()

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
                    if ds.startswith("spectrum"):
                        exp["controller"] = spectrum_ctrl
                    else:
                        exp["controller"] = scalar_ctrl
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

            self.myAssertRaise(Exception, rs.updateMntGrp)
            self._cf.dp.SetCommandVariable(
                ["CPDICT", json.dumps(self.smycps2)])
            self._cf.dp.SetCommandVariable(
                ["DSDICT", json.dumps(self.smydssXX)])

            for i in range(30):
                try:
                    ar = acqch[i % 5]
                    cps = {}
                    acps = {}
                    dss = {}
                    lcp = self.__rnd.randint(1, 40)
                    lds = self.__rnd.randint(1, 40)

                    self._cf.dp.SetCommandVariable(
                        ["CPDICT", json.dumps(self.smycps2)])
                    self._cf.dp.SetCommandVariable(
                        ["DSDICT", json.dumps(self.smydssXX)])

                    ncps = self.__rnd.randint(1, len(self.smycps2.keys()) - 1)
                    lcps = self.__rnd.sample(set(self.smycps2.keys()), ncps)
                    for cp in lcps:
                        if cp not in wrong:
                            cps[cp] = bool(self.__rnd.randint(0, 1))

                    ancps = self.__rnd.randint(1, len(self.smycps2.keys()) - 1)
                    alcps = self.__rnd.sample(set(self.smycps2.keys()), ancps)
                    for cp in alcps:
                        if cp not in wrong:
                            acps[cp] = bool(self.__rnd.randint(0, 1))

                    ndss = self.__rnd.randint(1, len(self.smycps2.keys()) - 1)
                    ldss = self.__rnd.sample(set(self.smycps2.keys()), ndss)
                    for ds in ldss:
                        if ds in self.smydssXX.keys():
                            if ds not in wrong:
                                dss[ds] = bool(self.__rnd.randint(0, 1))

                    ndss = self.__rnd.randint(1, len(self.smydssXX.keys()) - 1)
                    ldss = self.__rnd.sample(set(self.smydssXX.keys()), ndss)
                    for ds in ldss:
                        if ds in self.smydssXX.keys():
                            if ds not in wrong:
                                dss[ds] = bool(self.__rnd.randint(0, 1))

                    mncps = self.__rnd.randint(1, len(self.smycps2.keys()) - 1)
                    mcps = [
                        cp for cp in self.__rnd.sample(
                            set(self.smycps2.keys()), mncps)
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
                        dss.keys(), dstype='CLIENT')[0]
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

                    mdds = set()
                    for mdss in res[0].values():
                        if isinstance(mdss, dict):
                            for ds in mdss.keys():
                                adss[ds] = True

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
                    self.assertEqual(json.loads(mp["UnplottedComponents"]), [])
                    self.assertEqual(json.loads(mp["OrderedChannels"]), pdss)
                    self.myAssertDict(json.loads(mp["UserData"]), records)
                    self.assertEqual(json.loads(mp["Timer"]), [ar["name"]])
                    self.assertEqual(mp["MntGrp"], "nxsmntgrp2")
                    myctrls = {}
                    for cl in ctrls:
                        tgc = {}
                        for exp in expch:
                            ds = exp["name"]
                            if ds in chds and cl == exp['controller']:
                                cnt = self.smychsXX[str(ds)]
                                i = chds.index(str(ds))
                                try:
                                    tdv = "/".join(
                                        cnt['source'].split("/")[:-1])
                                    chn = {'ndim': 0,
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
                                except:
                                    raise
                        if tgc:
                            myctrls[cl] = {'units':
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
                    except:
                        pass
        finally:
            simp2.tearDown()

    ## updateMntGrp test
    def test_updateMntGrp_components_pool_tango_unplottedcomponents(self):
        fun = sys._getframe().f_code.co_name
        print "Run: %s.%s() " % (self.__class__.__name__, fun)
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

        db = PyTango.Database()
        db.put_device_property(self._ms.ms.keys()[0],
                               {'PoolNames': self._pool.dp.name()})
        pool = self._pool.dp
        pool.ExpChannelList = []
        self._ms.dps[self._ms.ms.keys()[0]].Init()

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
                    if ds.startswith("spectrum"):
                        exp["controller"] = spectrum_ctrl
                    else:
                        exp["controller"] = scalar_ctrl
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

            self.myAssertRaise(Exception, rs.updateMntGrp)
            self._cf.dp.SetCommandVariable(
                ["CPDICT", json.dumps(self.smycps2)])
            self._cf.dp.SetCommandVariable(
                ["DSDICT", json.dumps(self.smydssXX)])

            for i in range(30):
                try:
                    ar = acqch[i % 5]
                    cps = {}
                    acps = {}
                    dss = {}
                    lcp = self.__rnd.randint(1, 40)
                    lds = self.__rnd.randint(1, 40)

                    self._cf.dp.SetCommandVariable(
                        ["CPDICT", json.dumps(self.smycps2)])
                    self._cf.dp.SetCommandVariable(
                        ["DSDICT", json.dumps(self.smydssXX)])
                    comps = set()

                    ncps = self.__rnd.randint(1, len(self.smycps2.keys()) - 1)
                    lcps = self.__rnd.sample(set(self.smycps2.keys()), ncps)
                    for cp in lcps:
                        if cp not in wrong:
                            cps[cp] = bool(self.__rnd.randint(0, 1))
                            if cps[cp]:
                                comps.add(cp)

                    ancps = self.__rnd.randint(1, len(self.smycps2.keys()) - 1)
                    alcps = self.__rnd.sample(set(self.smycps2.keys()), ancps)
                    for cp in alcps:
                        if cp not in wrong:
                            acps[cp] = bool(self.__rnd.randint(0, 1))
                            if acps[cp]:
                                comps.add(cp)

                    ndss = self.__rnd.randint(1, len(self.smycps2.keys()) - 1)
                    ldss = self.__rnd.sample(set(self.smycps2.keys()), ndss)
                    for ds in ldss:
                        if ds in self.smydssXX.keys():
                            if ds not in wrong:
                                dss[ds] = bool(self.__rnd.randint(0, 1))

                    ndss = self.__rnd.randint(1, len(self.smydssXX.keys()) - 1)
                    ldss = self.__rnd.sample(set(self.smydssXX.keys()), ndss)
                    for ds in ldss:
                        if ds in self.smydssXX.keys():
                            if ds not in wrong:
                                dss[ds] = bool(self.__rnd.randint(0, 1))

                    mncps = self.__rnd.randint(1, len(self.smycps2.keys()) - 1)
                    mcps = [cp for cp in self.__rnd.sample(
                            set(self.smycps2.keys()), mncps)
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
                        dss.keys(), dstype='CLIENT')[0]
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
                    chds1 = list(chds)
                    chds2 = [ds for ds in rs.componentDataSources()
                             if not ds.startswith('client')]
                    chds.extend(chds2)
                    chds = sorted(chds)

                    lheds = []
                    if chds:
                        nhe = self.__rnd.randint(0, len(set(chds)) - 1)
                        lheds = self.__rnd.sample(set(chds), nhe)

                    lhecp = []
                    if comps:
                        nhe = self.__rnd.randint(0, len(set(comps)) - 1)
                        lhecp = self.__rnd.sample(set(comps), nhe)

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

                    mdds = set()
                    for mdss in res[0].values():
                        if isinstance(mdss, dict):
                            for ds in mdss.keys():
                                adss[ds] = True

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
                    self.assertEqual(json.loads(mp["Timer"]), [ar["name"]])
                    self.assertEqual(mp["MntGrp"], "nxsmntgrp2")
#                    print "CNF", cnf
#                    print "CHDS", chds
                    myctrls = {}
                    for cl in ctrls:
                        tgc = {}
                        for exp in expch:
                            ds = exp["name"]
                            if ds in chds and cl == exp['controller']:
                                cnt = self.smychsXX[str(ds)]
                                i = chds.index(str(ds))
#                                print "INDEX", i, ds
                                try:
                                    tdv = "/".join(
                                        cnt['source'].split("/")[:-1])
                                    chn = {'ndim': 0,
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
                                except:
                                    raise
                        if tgc:
                            myctrls[cl] = {
                                'units':
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
                    except:
                        pass
        finally:
            simp2.tearDown()

    ## updateMntGrp test
    def test_updateMntGrp_components_mixed_tango_unplottedcomponents(self):
        fun = sys._getframe().f_code.co_name
        print "Run: %s.%s() " % (self.__class__.__name__, fun)
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

        db = PyTango.Database()
        db.put_device_property(self._ms.ms.keys()[0],
                               {'PoolNames': self._pool.dp.name()})
        pool = self._pool.dp
        pool.ExpChannelList = []
        self._ms.dps[self._ms.ms.keys()[0]].Init()

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
                    if ds.startswith("spectrum"):
                        exp["controller"] = spectrum_ctrl
                    else:
                        exp["controller"] = scalar_ctrl
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

            self.myAssertRaise(Exception, rs.updateMntGrp)
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

            for i in range(30):
                try:
                    ar = acqch[i % 5]
                    cps = {}
                    acps = {}
                    dss = {}
                    lcp = self.__rnd.randint(1, 40)
                    lds = self.__rnd.randint(1, 40)

                    self._cf.dp.SetCommandVariable(
                        ["CPDICT", json.dumps(amycps)])
                    self._cf.dp.SetCommandVariable(
                        ["DSDICT", json.dumps(amydss)])
                    comps = set()

                    ncps = self.__rnd.randint(1, len(amycps) - 1)
                    lcps = self.__rnd.sample(set(amycps.keys()), ncps)
                    for cp in lcps:
                        if cp not in wrong:
                            cps[cp] = bool(self.__rnd.randint(0, 1))
                            if cps[cp]:
                                comps.add(cp)

                    ancps = self.__rnd.randint(1, len(amycps.keys()) - 1)
                    alcps = self.__rnd.sample(set(amycps.keys()), ancps)
                    for cp in alcps:
                        if cp not in wrong:
                            acps[cp] = bool(self.__rnd.randint(0, 1))
                            if acps[cp]:
                                comps.add(cp)

                    ndss = self.__rnd.randint(1, len(amycps.keys()) - 1)
                    ldss = self.__rnd.sample(set(amycps.keys()), ndss)
                    for ds in ldss:
                        if ds in amydss.keys():
                            if ds not in wrong:
                                dss[ds] = bool(self.__rnd.randint(0, 1))

                    ndss = self.__rnd.randint(1, len(amydss.keys()) - 1)
                    ldss = self.__rnd.sample(set(amydss.keys()), ndss)
                    for ds in ldss:
                        if ds in amydss.keys():
                            if ds not in wrong:
                                dss[ds] = bool(self.__rnd.randint(0, 1))

                    mncps = self.__rnd.randint(1, len(amycps.keys()) - 1)
                    mcps = [cp for cp in self.__rnd.sample(
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
                    mp["Timer"] = '["%s"]' % ar["name"]
                    mp["UserData"] = json.dumps(records)
                    rs.profileConfiguration = str(json.dumps(mp))
                    mp = json.loads(rs.profileConfiguration)

                    tmg = TestMGSetUp.TestMeasurementGroupSetUp(
                        name='nxsmntgrp2')
                    dv = "/".join(ar["full_name"].split("/")[0:-1])
                    chds = [ds for ds in rs.selectedDataSources()
                            if not ds.startswith('client')]
                    chds1 = list(chds)
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
                        nhe = self.__rnd.randint(0, len(set(chds)) - 1)
                        lheds = self.__rnd.sample(set(chds), nhe)

                    lhecp = []
                    if comps:
                        nhe = self.__rnd.randint(0, len(set(comps)) - 1)
                        lhecp = self.__rnd.sample(set(comps), nhe)

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

                    mdds = set()
                    for mdss in res[0].values():
                        if isinstance(mdss, dict):
                            for ds in mdss.keys():
                                adss[ds] = True

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
                    self.assertEqual(json.loads(mp["Timer"]), [ar["name"]])
                    self.assertEqual(mp["MntGrp"], "nxsmntgrp2")
#                    print "CNF", cnf
#                    print "CHDS", chds
                    myctrls = {}
                    for cl in ctrls:
                        tgc = {}
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
                                        chn = {'ndim': 0,
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
                                    except:
                                        raise
                        if tgc:
                            myctrls[cl] = {'units':
                                           {'0':
                                            {'channels': tgc,
                                             'monitor': dv,
                                             'id': 0,
                                             'timer': dv,
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
                    except:
                        pass
        finally:
            simp2.tearDown()

    ## updateMntGrp test
    def test_updateMntGrp_components_mixed_tango_orderedchannels(self):
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
                    if ds.startswith("spectrum"):
                        exp["controller"] = spectrum_ctrl
                    else:
                        exp["controller"] = scalar_ctrl
                    expch.append(exp)
                    pdss.append(ds)
            pdss = sorted(pdss)
            self.__rnd.shuffle(pdss)

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

            self.myAssertRaise(Exception, rs.updateMntGrp)
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

            for i in range(30):
                try:
                    ar = acqch[i % 5]
                    cps = {}
                    acps = {}
                    dss = {}
                    lcp = self.__rnd.randint(1, 40)
                    lds = self.__rnd.randint(1, 40)

                    self._cf.dp.SetCommandVariable(
                        ["CPDICT", json.dumps(amycps)])
                    self._cf.dp.SetCommandVariable(
                        ["DSDICT", json.dumps(amydss)])
                    comps = set()

                    ncps = self.__rnd.randint(1, len(amycps) - 1)
                    lcps = self.__rnd.sample(set(amycps.keys()), ncps)
                    for cp in lcps:
                        if cp not in wrong:
                            cps[cp] = bool(self.__rnd.randint(0, 1))
                            if cps[cp]:
                                comps.add(cp)

                    ancps = self.__rnd.randint(1, len(amycps.keys()) - 1)
                    alcps = self.__rnd.sample(set(amycps.keys()), ancps)
                    for cp in alcps:
                        if cp not in wrong:
                            acps[cp] = bool(self.__rnd.randint(0, 1))
                            if acps[cp]:
                                comps.add(cp)

                    ndss = self.__rnd.randint(1, len(amycps.keys()) - 1)
                    ldss = self.__rnd.sample(set(amycps.keys()), ndss)
                    for ds in ldss:
                        if ds in amydss.keys():
                            if ds not in wrong:
                                dss[ds] = bool(self.__rnd.randint(0, 1))

                    ndss = self.__rnd.randint(1, len(amydss.keys()) - 1)
                    ldss = self.__rnd.sample(set(amydss.keys()), ndss)
                    for ds in ldss:
                        if ds in amydss.keys():
                            if ds not in wrong:
                                dss[ds] = bool(self.__rnd.randint(0, 1))

                    mncps = self.__rnd.randint(1, len(amycps.keys()) - 1)
                    mcps = [cp for cp in self.__rnd.sample(
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
                    mp["Timer"] = '["%s"]' % ar["name"]
                    mp["UserData"] = json.dumps(records)
                    rs.profileConfiguration = str(json.dumps(mp))
                    mp = json.loads(rs.profileConfiguration)

                    tmg = TestMGSetUp.TestMeasurementGroupSetUp(
                        name='mg2')
                    dv = "/".join(ar["full_name"].split("/")[0:-1])
                    chds = [ds for ds in rs.selectedDataSources()
                            if not ds.startswith('client')]
                    chds1 = list(chds)
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
                        nhe = self.__rnd.randint(0, len(set(chds)) - 1)
                        lheds = self.__rnd.sample(set(chds), nhe)

                    lhecp = []
                    if comps:
                        nhe = self.__rnd.randint(0, len(set(comps)) - 1)
                        lhecp = self.__rnd.sample(set(comps), nhe)

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

                    mdds = set()
                    for mdss in res[0].values():
                        if isinstance(mdss, dict):
                            for ds in mdss.keys():
                                adss[ds] = True

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
                    self.assertEqual(json.loads(mp["Timer"]), [ar["name"]])
                    self.assertEqual(mp["MntGrp"], "mg2")
#                    print "CNF", cnf
#                    print "CHDS", chds
                    myctrls = {}
                    for cl in ctrls:
                        tgc = {}
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
                                        chn = {'ndim': 0,
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
                                    except:
                                        raise
                        if tgc:
                            myctrls[cl] = {'units':
                                           {'0':
                                            {'channels': tgc,
                                             'monitor': dv,
                                             'id': 0,
                                             'timer': dv,
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
                                                  'monitor': dv,
                                                  'id': 0,
                                                  'timer': dv,
                                                  'trigger_type': 0}}}

                    smg = {"controllers": myctrls,
                           "monitor": "%s" % dv,
                           "description": "Measurement Group",
                           "timer": "%s" % dv,
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
                    self.assertEqual(json.loads(mp["Timer"]), [ar["name"]])
                    self.assertEqual(mp["MntGrp"], "mg2")
                finally:
                    rs.deleteProfile("mg2")
                    try:
                        tmg.tearDown()
                    except:
                        pass
        finally:
            simp2.tearDown()

    ## updateMntGrp test
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
                ntms = self.__rnd.randint(1, 5)
                tms = self.__rnd.sample(set(
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
                        elif ds.startswith("image"):
                            exp["controller"] = image_ctrl
                        elif ds.startswith("spectrum"):
                            exp["controller"] = spectrum_ctrl
                        else:
                            exp["controller"] = scalar_ctrl
                        expch.append(exp)
                        pdss.append(ds)
                pdss = sorted(pdss)
                self.__rnd.shuffle(pdss)

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
                    lcp = self.__rnd.randint(1, 40)
                    lds = self.__rnd.randint(1, 40)

                    self._cf.dp.SetCommandVariable(
                        ["CPDICT", json.dumps(amycps)])
                    self._cf.dp.SetCommandVariable(
                        ["DSDICT", json.dumps(amydss)])
                    comps = set()

                    ncps = self.__rnd.randint(1, len(amycps) - 1)
                    lcps = self.__rnd.sample(set(amycps.keys()), ncps)
                    for cp in lcps:
                        if cp not in wrong:
                            cps[cp] = bool(self.__rnd.randint(0, 1))
                            if cps[cp]:
                                comps.add(cp)

                    ancps = self.__rnd.randint(1, len(amycps.keys()) - 1)
                    alcps = self.__rnd.sample(set(amycps.keys()), ancps)
                    for cp in alcps:
                        if cp not in wrong:
                            acps[cp] = bool(self.__rnd.randint(0, 1))
                            if acps[cp]:
                                comps.add(cp)

                    ndss = self.__rnd.randint(1, len(amycps.keys()) - 1)
                    ldss = self.__rnd.sample(set(amycps.keys()), ndss)
                    for ds in ldss:
                        if ds in amydss.keys():
                            if ds not in wrong:
                                dss[ds] = bool(self.__rnd.randint(0, 1))

                    ndss = self.__rnd.randint(1, len(amydss.keys()) - 1)
                    ldss = self.__rnd.sample(set(amydss.keys()), ndss)
                    for ds in ldss:
                        if ds in amydss.keys():
                            if ds not in wrong:
                                dss[ds] = bool(self.__rnd.randint(0, 1))

                    for tm in ltimers:
                        dss[tm] = bool(self.__rnd.randint(0, 1))

                    mncps = self.__rnd.randint(1, len(amycps.keys()) - 1)
                    mcps = [cp for cp in self.__rnd.sample(
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
                        nhe = self.__rnd.randint(0, len(set(chds)) - 1)
                        lheds = self.__rnd.sample(set(chds), nhe)

                    lhecp = []
                    if comps:
                        nhe = self.__rnd.randint(0, len(set(comps)) - 1)
                        lhecp = self.__rnd.sample(set(comps), nhe)

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
                        for exp in expch:
                            ds = exp["name"]
                            if ds in chds and cl == exp['controller']:
                                if ds in self.smychsXX.keys():
                                    cnt = self.smychsXX[str(ds)]
                                    i = chds.index(str(ds))
                                    try:
                                        tdv = "/".join(
                                            cnt['source'].split("/")[:-1])
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
                                         'monitor': fltm,
                                         'id': 0,
                                         'timer': fltm,
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

    ## updateMntGrp test
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
                ntms = self.__rnd.randint(1, 5)
                tms = self.__rnd.sample(set(
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
                        elif ds.startswith("image"):
                            exp["controller"] = image_ctrl
                        elif ds.startswith("spectrum"):
                            exp["controller"] = spectrum_ctrl
                        else:
                            exp["controller"] = scalar_ctrl
                        expch.append(exp)
                        pdss.append(ds)
                pdss = sorted(pdss)
                self.__rnd.shuffle(pdss)

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
                    lcp = self.__rnd.randint(1, 40)
                    lds = self.__rnd.randint(1, 40)

                    self._cf.dp.SetCommandVariable(
                        ["CPDICT", json.dumps(amycps)])
                    self._cf.dp.SetCommandVariable(
                        ["DSDICT", json.dumps(amydss)])
                    comps = set()

                    ncps = self.__rnd.randint(1, len(amycps) - 1)
                    lcps = self.__rnd.sample(set(amycps.keys()), ncps)
                    for cp in lcps:
                        if cp not in wrong:
                            cps[cp] = bool(self.__rnd.randint(0, 1))
                            if cps[cp]:
                                comps.add(cp)

                    ancps = self.__rnd.randint(1, len(amycps.keys()) - 1)
                    alcps = self.__rnd.sample(set(amycps.keys()), ancps)
                    for cp in alcps:
                        if cp not in wrong:
                            acps[cp] = bool(self.__rnd.randint(0, 1))
                            if acps[cp]:
                                comps.add(cp)

                    ndss = self.__rnd.randint(1, len(amycps.keys()) - 1)
                    ldss = self.__rnd.sample(set(amycps.keys()), ndss)
                    for ds in ldss:
                        if ds in amydss.keys():
                            if ds not in wrong:
                                dss[ds] = bool(self.__rnd.randint(0, 1))

                    ndss = self.__rnd.randint(1, len(amydss.keys()) - 1)
                    ldss = self.__rnd.sample(set(amydss.keys()), ndss)
                    for ds in ldss:
                        if ds in amydss.keys():
                            if ds not in wrong:
                                dss[ds] = bool(self.__rnd.randint(0, 1))

                    nadss = self.__rnd.randint(1, len(amydss.keys()) - 1)
                    aadss = [ds for ds in self.__rnd.sample(
                        set(amydss.keys()), nadss)]
                    nadss = self.__rnd.randint(1, len(amydss.keys()) - 1)
                    indss = [ds for ds in self.__rnd.sample(
                        set(amydss.keys()), nadss)]

                    for tm in ltimers:
                        dss[tm] = bool(self.__rnd.randint(0, 1))

                    mncps = self.__rnd.randint(1, len(amycps.keys()) - 1)
                    mcps = [cp for cp in self.__rnd.sample(
                        set(amycps.keys()), mncps) if cp not in wrong]
                    oncps = self.__rnd.randint(1, len(amycps.keys()) - 1)
                    ocps = [cp for cp in self.__rnd.sample(
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
                    mp["PreselectedDataSources"] = json.dumps(aadss)
                    mp["OptionalComponents"] = json.dumps(ocps)
                    mp["InitDataSources"] = json.dumps(indss)
                    mp["AppendEntry"] = bool(self.__rnd.randint(0, 1))
                    mp["ComponentsFromMntGrp"] = bool(self.__rnd.randint(0, 1))
                    mp["DynamicComponents"] = bool(self.__rnd.randint(0, 1))
                    mp["DefaultDynamicLinks"] = bool(self.__rnd.randint(0, 1))
                    mp["DefaultDynamicPath"] = self.getRandomName(20)
                    mp["TimeZone"] = self.getRandomName(20)

                    mp["ConfigVariables"] = json.dumps(dict(
                        (self.getRandomName(10),
                         self.getRandomName(15)) for _ in
                        range(self.__rnd.randint(1, 40))))

                    paths = dict(
                        (self.getRandomName(10),
                         self.getRandomName(15)) for _ in
                        range(self.__rnd.randint(1, 40)))
                    labels = dict(
                        (self.getRandomName(10),
                         self.getRandomName(15)) for _ in
                        range(self.__rnd.randint(1, 40)))
                    links = dict(
                        (self.getRandomName(10),
                         bool(self.__rnd.randint(0, 1))) for _ in
                        range(self.__rnd.randint(1, 40)))
                    types = dict(
                        (self.getRandomName(10),
                         self.getRandomName(15)) for _ in
                        range(self.__rnd.randint(1, 40)))
                    shapes = dict(
                        (self.getRandomName(10),
                         [self.__rnd.randint(1, 40)
                          for _ in range(self.__rnd.randint(0, 3))])
                        for _ in range(self.__rnd.randint(1, 40)))
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
                        nhe = self.__rnd.randint(0, len(set(chds)) - 1)
                        lheds = self.__rnd.sample(set(chds), nhe)

                    lhecp = []
                    if comps:
                        nhe = self.__rnd.randint(0, len(set(comps)) - 1)
                        lhecp = self.__rnd.sample(set(comps), nhe)

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
                    self.assertTrue(rs.isMntGrpUpdated())
                    self.assertTrue(rs.isMntGrpUpdated())

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
                    self.assertTrue(not rs.isMntGrpUpdated())
                    self.assertTrue(not rs.isMntGrpUpdated())
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
                                         'monitor': fltm,
                                         'id': 0,
                                         'timer': fltm,
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

                    self.assertTrue(not rs.isMntGrpUpdated())
                    self.assertTrue(not rs.isMntGrpUpdated())

                    mp = json.loads(rs.profileConfiguration)
                    self.compareToDumpJSON(
                        rs, ["ComponentPreselection",
                             "ComponentSelection",
                             "DataSourceSelection",
                             "UnplottedComponents",
                             "PreselectedDataSources"])

                    self.myAssertDict(
                        json.loads(mp["ComponentPreselection"]), acps)
                    self.myAssertDict(
                        json.loads(mp["ComponentSelection"]), cps)
                    self.myAssertDict(
                        json.loads(mp["DataSourceSelection"]), adss)
                    self.assertEqual(
                        set(json.loads(mp["PreselectedDataSources"])),
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

    ## test
    def test_switchProfile_importMntGrp(self):
        fun = sys._getframe().f_code.co_name
        print "Run: %s.%s() " % (self.__class__.__name__, fun)
        self.subtest_switchProfile_importMntGrp()

    ## test
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
                        ntms = self.__rnd.randint(1, 5)
                        tms = self.__rnd.sample(set(
                            [ch for ch in self.smychsXX.keys()
                             if not ch.startswith("client")]), ntms)
                        for tm in tms:
                            myct = ("ctrl_%s" % tm).replace("_", "/")
                            timers[myct] = tm
                            ctrls.append(myct)
                        print "TIMERSL", tms
                        print "TIMERSD", timers
                        ltimers[mg] = timers.values()
                        print "LTIMER", ltimers[mg]

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
                                pdss[mg].append(ds)
                        pdss[mg] = sorted(pdss[mg])
                        self.__rnd.shuffle(pdss[mg])

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
                        lcp = self.__rnd.randint(1, 40)
                        lds = self.__rnd.randint(1, 40)

                        self._cf.dp.SetCommandVariable(
                            ["CPDICT", json.dumps(amycps)])
                        self._cf.dp.SetCommandVariable(
                            ["DSDICT", json.dumps(amydss)])
                        comps = set()

                        ncps = self.__rnd.randint(1, len(amycps) - 1)
                        lcps = self.__rnd.sample(set(amycps.keys()), ncps)
                        for cp in lcps:
                            if cp not in wrong:
                                cps[mg][cp] = bool(self.__rnd.randint(0, 1))
                                if cps[mg][cp]:
                                    comps.add(cp)

                        ancps = self.__rnd.randint(1, len(amycps.keys()) - 1)
                        alcps = self.__rnd.sample(set(amycps.keys()), ancps)
                        for cp in alcps:
                            if cp not in wrong:
                                acps[mg][cp] = bool(self.__rnd.randint(0, 1))
                                if acps[mg][cp]:
                                    comps.add(cp)

                        ndss = self.__rnd.randint(1, len(amycps.keys()) - 1)
                        ldss = self.__rnd.sample(set(amycps.keys()), ndss)
                        for ds in ldss:
                            if ds in amydss.keys():
                                if ds not in wrong:
                                    dss[ds] = bool(self.__rnd.randint(0, 1))

                        ndss = self.__rnd.randint(1, len(amydss.keys()) - 1)
                        ldss = self.__rnd.sample(set(amydss.keys()), ndss)
                        for ds in ldss:
                            if ds in amydss.keys():
                                if ds not in wrong:
                                    dss[ds] = bool(self.__rnd.randint(0, 1))

                        nadss = self.__rnd.randint(1, len(amydss.keys()) - 1)
                        aadss[mg] = [ds for ds in self.__rnd.sample(
                            set(amydss.keys()), nadss)]
                        nadss = self.__rnd.randint(1, len(amydss.keys()) - 1)
                        indss = [ds for ds in self.__rnd.sample(
                            set(amydss.keys()), nadss)]

                        for tm in ltimers[mg]:
                            dss[tm] = bool(self.__rnd.randint(0, 1))

                        mncps = self.__rnd.randint(1, len(amycps.keys()) - 1)
                        mcps = [cp for cp in self.__rnd.sample(
                                set(amycps.keys()), mncps) if cp not in wrong]
                        oncps = self.__rnd.randint(1, len(amycps.keys()) - 1)
                        ocps = [cp for cp in self.__rnd.sample(
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
                        mp[mg]["PreselectedDataSources"] = \
                            json.dumps(aadss[mg])
                        mp[mg]["OptionalComponents"] = json.dumps(ocps)
                        mp[mg]["InitDataSources"] = json.dumps(indss)
                        mp[mg]["AppendEntry"] = bool(self.__rnd.randint(0, 1))
                        mp[mg]["ComponentsFromMntGrp"] = bool(
                            self.__rnd.randint(0, 1))
                        mp[mg]["DynamicComponents"] = bool(
                            self.__rnd.randint(0, 1))
                        mp[mg]["DefaultDynamicLinks"] = \
                            bool(self.__rnd.randint(0, 1))
                        mp[mg]["DefaultDynamicPath"] = self.getRandomName(20)
                        mp[mg]["TimeZone"] = self.getRandomName(20)

                        mp[mg]["ConfigVariables"] = json.dumps(dict(
                            (self.getRandomName(10),
                             self.getRandomName(15)) for _ in
                            range(self.__rnd.randint(1, 40))))
                        paths = dict(
                            (self.getRandomName(10),
                             self.getRandomName(15)) for _ in
                            range(self.__rnd.randint(1, 40)))
                        labels = dict(
                            (self.getRandomName(10),
                             self.getRandomName(15)) for _ in
                            range(self.__rnd.randint(1, 40)))
                        links = dict(
                            (self.getRandomName(10),
                             bool(self.__rnd.randint(0, 1))) for _ in
                            range(self.__rnd.randint(1, 40)))
                        types = dict(
                            (self.getRandomName(10),
                             self.getRandomName(15)) for _ in
                            range(self.__rnd.randint(1, 40)))
                        shapes = dict(
                            (self.getRandomName(10),
                             [self.__rnd.randint(1, 40)
                              for _ in range(self.__rnd.randint(0, 3))])
                            for _ in range(self.__rnd.randint(1, 40)))

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
                            nhe = self.__rnd.randint(0, len(set(chds)) - 1)
                            lheds = self.__rnd.sample(set(chds), nhe)

                        lhecp = []
                        if comps:
                            nhe = self.__rnd.randint(0, len(set(comps)) - 1)
                            lhecp = self.__rnd.sample(set(comps), nhe)

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
                        self.assertTrue(rs[mg].isMntGrpUpdated())
                        self.assertTrue(rs[mg].isMntGrpUpdated())

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
                                    print "DES", tm
                                    adss[mg][tm] = False

                        jpcnf = rs[mg].updateMntGrp()
                        self.assertTrue(not rs[mg].isMntGrpUpdated())
                        self.assertTrue(not rs[mg].isMntGrpUpdated())
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
                            for exp in expch:
                                ds = exp["name"]
                                if ds in chds and cl == exp['controller']:
                                    if ds in self.smychsXX.keys():
                                        cnt = self.smychsXX[str(ds)]
                                        i = chds.index(str(ds))
                                        try:
                                            tdv = "/".join(
                                                cnt['source'].split("/")[:-1])
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
                                             'monitor': fltm,
                                             'id': 0,
                                             'timer': fltm,
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
                        print "MG", mg
                        rs[mg].mntGrp = mg
                        rs[mg].fetchProfile()
                        mp[mg] = json.loads(rs[mg].profileConfiguration)
#                        self.myAssertRaise(Exception, rs[mg].isMntGrpUpdated)
#                       rs[mg].fetchProfile()
#                        mp[mg] = json.loads(rs[mg].profileConfiguration)

                        self.assertTrue(not rs[mg].isMntGrpUpdated())
                        self.assertTrue(not rs[mg].isMntGrpUpdated())

                        self.compareToDumpJSON(
                            rs[mg],
                            ["DataSourceSelection",
                             "UnplottedComponents",
                             "PreselectedDataSources",
                             "UnplottedComponents"],
                            name=mg)
                        mp[mg] = json.loads(rs[mg].profileConfiguration)
                        self.myAssertDict(
                            json.loads(
                                mp[mg]["DataSourceSelection"]), adss[mg])
                        self.assertEqual(
                            set(json.loads(mp[mg]["PreselectedDataSources"])),
                            set(aadss[mg]))
                        print "PDS1", set(aadss[mg])
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
                    mg1, mg2, mg3, mg4 = tuple(self.__rnd.sample(mgs, 4))
                    print "MGS", mg1, mg2, mg3, mg4

                    self.compareToDumpJSON(
                        rs[mg1],
                        ["DataSourceSelection",
                         "UnplottedComponents",
                         "PreselectedDataSources"],
                        name=mg1)
                    self.compareToDumpJSON(
                        rs[mg2],
                        ["DataSourceSelection",
                         "UnplottedComponents",
                         "PreselectedDataSources"],
                        name=mg2)
                    self.compareToDumpJSON(
                        rs[mg3],
                        ["DataSourceSelection",
                         "UnplottedComponents",
                         "PreselectedDataSources"],
                        name=mg3)
                    self.compareToDumpJSON(
                        rs[mg4],
                        ["DataSourceSelection",
                         "UnplottedComponents",
                         "PreselectedDataSources"],
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
                            "PreselectedDataSources",
                            "Timer"
                        ],
                        name=mg1)
                    tmpcf = json.loads(rs[mg1].mntGrpConfiguration())
                    ltmpcf = json.loads(lrs.mntGrpConfiguration())
                    self.myAssertDict(tmpcf, ltmpcf)

                    self.assertEqual(
                        set(json.loads(lmp["PreselectedDataSources"])),
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

                    print "MGS", mg1, mg2, mg3, mg4

                    # import mntgrp another defined by selector MntGrp
                    lrs.mntGrp = mg2

                    self.assertTrue(lrs.isMntGrpUpdated())
                    self.assertTrue(lrs.isMntGrpUpdated())

                    lrs.importMntGrp()
                    lmp = json.loads(lrs.profileConfiguration)
                    self.assertTrue(lrs.isMntGrpUpdated())
                    self.assertTrue(lrs.isMntGrpUpdated())

                    tmpcf1 = json.loads(rs[mg1].mntGrpConfiguration())
                    tmpcf2 = json.loads(rs[mg2].mntGrpConfiguration())
                    ltmpcf = json.loads(lrs.mntGrpConfiguration())
#                    self.myAssertDict(tmpcf1, ltmpcf)
                    self.myAssertDict(tmpcf2, ltmpcf)
                    print "RSmg2",
                    self.compareToDumpJSON(
                        rs[mg2],
                        ["DataSourceSelection",
                         "UnplottedComponents",
                         "PreselectedDataSources"],
                        name=mg2)
                    self.compareToDumpJSON(
                        lrs,
                        ["DataSourceSelection",
                         "UnplottedComponents",
                         "PreselectedDataSources",
                         "Timer",
                         "MntGrp"],
                        name=mg1)

                    tmpcf = json.loads(rs[mg2].mntGrpConfiguration())
                    ltmpcf = json.loads(lrs.mntGrpConfiguration())
                    self.myAssertDict(tmpcf, ltmpcf)

                    self.assertEqual(
                        set(json.loads(lmp["PreselectedDataSources"])),
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

                    print "T1", json.loads(mp[mg1]["Timer"])
                    print "T2", json.loads(mp[mg2]["Timer"])
                    print "LT", json.loads(lmp["Timer"])
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
                    tmpcf = json.loads(rs[mg1].mntGrpConfiguration())
                    tmpcf2 = json.loads(rs[mg2].mntGrpConfiguration())
                    ltmpcf = json.loads(lrs.mntGrpConfiguration())
                    self.assertEqual(ltmpcf, tmpcf2)
                    tmpcf['label'] = mg2
                    mgdp = PyTango.DeviceProxy(
                        tmg[mg2].new_device_info_writer.name)
                    print "name", tmg[mg2].new_device_info_writer.name
                    mgdp.Configuration = json.dumps(tmpcf)
                    self.assertTrue(lrs.isMntGrpUpdated())
                    self.assertTrue(lrs.isMntGrpUpdated())

                    tmpcf1 = json.loads(rs[mg1].mntGrpConfiguration())
                    tmpcf2 = json.loads(rs[mg2].mntGrpConfiguration())
                    ltmpcf = json.loads(lrs.mntGrpConfiguration())
#                    self.myAssertDict(tmpcf1, ltmpcf)
                    self.myAssertDict(tmpcf2, ltmpcf)

                    lrs.importMntGrp()
                    # ???

                    ltmpcf2 = json.loads(lrs.mntGrpConfiguration())
                    if not Utils.compareDict(ltmpcf2, ltmpcf):
                        self.assertTrue(lrs.isMntGrpUpdated())
                        self.assertTrue(lrs.isMntGrpUpdated())

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
                         "PreselectedDataSources",
                         "Timer",
                         "MntGrp"],
                        name=mg1)

                    self.compareToDump(
                        rs[mg2],
                        ["ComponentPreselection",
                         "ComponentSelection",
                         "DataSourceSelection",
                         "UnplottedComponents",
                         "PreselectedDataSources",
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
                        set(json.loads(mp[mg2]["PreselectedDataSources"])),
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
                            "PreselectedDataSources",
                            "Timer"],
                        name=mg3)
                    lmp = json.loads(lrs.profileConfiguration)
                    self.myAssertDict(json.loads(lmp["DataSourceSelection"]),
                                      adss[mg3])
                    self.assertEqual(
                        set(json.loads(lmp["PreselectedDataSources"])),
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
                            "PreselectedDataSources",
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
                        set(json.loads(lmp["PreselectedDataSources"])),
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
                    self.assertTrue(lrs.isMntGrpUpdated())
                    self.assertTrue(lrs.isMntGrpUpdated())
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
                            "PreselectedDataSources",
                            "Timer"],
                        name=mg3)
                    self.myAssertDict(json.loads(lmp["DataSourceSelection"]),
                                      adss[mg3])
                    self.assertEqual(
                        set(json.loads(lmp["PreselectedDataSources"])),
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
                            "PreselectedDataSources",
                            "Timer"],
                        name=mg3)
                    lmp = json.loads(lrs.profileConfiguration)
                    self.myAssertDict(json.loads(lmp["DataSourceSelection"]),
                                      adss[mg3])
                    self.assertEqual(
                        set(json.loads(lmp["PreselectedDataSources"])),
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
                            "PreselectedDataSources",
                            "Timer"],
                        name=mg3)
                    lmp = json.loads(lrs.profileConfiguration)
                    self.myAssertDict(json.loads(lmp["DataSourceSelection"]),
                                      adss[mg3])
                    self.assertEqual(
                        set(json.loads(lmp["PreselectedDataSources"])),
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

                    ## fetch non-existing mg
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
                            "PreselectedDataSources",
                            "Timer", "MntGrp"],
                        name=mg3)
                    lmp = json.loads(lrs.profileConfiguration)
                    self.myAssertDict(json.loads(lmp["DataSourceSelection"]),
                                      adss[mg3])
                    self.assertEqual(
                        set(json.loads(lmp["PreselectedDataSources"])),
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

                    ## fetch non-existing selection
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
                            "InitDataSources",
                            "PreselectedDataSources",
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
                        set(json.loads(lmp["PreselectedDataSources"])),
                        set(aadss[mg3]))
                    self.assertEqual(
                        set(json.loads(lmp["InitDataSources"])),
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

    ## updateMntGrp test
    def test_myswitchProfile_importMntGrp(self):
        fun = sys._getframe().f_code.co_name
        print "Run: %s.%s() " % (self.__class__.__name__, fun)
        val = {"ConfigDevice": self._cf.dp.name(),
               "WriterDevice": self._wr.dp.name(),
               "Door": 'doortestp09/testts/t1r228',
               "MntGrp": 'mg2'}

        self.maxDiff = None
        self.tearDown()
        print "DOWN"
        print "UP"
        try:
            for j in range(10):
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
                    print "SIMP2 SETUP"
                    simp2.setUp()

                    # create mntgrps

                    for i, mg in enumerate(mgs):
                        print "OPEN RS"
                        ors = self.openRecSelector()
                        print "OPEN RS END"
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
                        ntms = self.__rnd.randint(1, 5)
                        tms = self.__rnd.sample(set(
                            [ch for ch in self.smychsXX.keys()
                             if not ch.startswith("client")]), ntms)
                        for tm in tms:
                            myct = ("ctrl_%s" % tm).replace("_", "/")
                            timers[myct] = tm
                            ctrls.append(myct)
                        print "TIMERSL", tms
                        print "TIMERSD", timers
                        ltimers[mg] = timers.values()
                        print "LTIMER", ltimers[mg]

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
                                pdss[mg].append(ds)
                        pdss[mg] = sorted(pdss[mg])
                        self.__rnd.shuffle(pdss[mg])

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
                        lcp = self.__rnd.randint(1, 40)
                        lds = self.__rnd.randint(1, 40)

                        self._cf.dp.SetCommandVariable(
                            ["CPDICT", json.dumps(amycps)])
                        self._cf.dp.SetCommandVariable(
                            ["DSDICT", json.dumps(amydss)])
                        comps = set()

                        ncps = self.__rnd.randint(1, len(amycps) - 1)
                        lcps = self.__rnd.sample(set(amycps.keys()), ncps)
                        for cp in lcps:
                            if cp not in wrong:
                                cps[mg][cp] = bool(self.__rnd.randint(0, 1))
                                if cps[mg][cp]:
                                    comps.add(cp)

                        ancps = self.__rnd.randint(1, len(amycps.keys()) - 1)
                        alcps = self.__rnd.sample(set(amycps.keys()), ancps)
                        for cp in alcps:
                            if cp not in wrong:
                                acps[mg][cp] = bool(self.__rnd.randint(0, 1))
                                if acps[mg][cp]:
                                    comps.add(cp)

                        ndss = self.__rnd.randint(1, len(amycps.keys()) - 1)
                        ldss = self.__rnd.sample(set(amycps.keys()), ndss)
                        for ds in ldss:
                            if ds in amydss.keys():
                                if ds not in wrong:
                                    dss[ds] = bool(self.__rnd.randint(0, 1))

                        ndss = self.__rnd.randint(1, len(amydss.keys()) - 1)
                        ldss = self.__rnd.sample(set(amydss.keys()), ndss)
                        for ds in ldss:
                            if ds in amydss.keys():
                                if ds not in wrong:
                                    dss[ds] = bool(self.__rnd.randint(0, 1))

                        nadss = self.__rnd.randint(1, len(amydss.keys()) - 1)
                        aadss[mg] = [ds for ds in self.__rnd.sample(
                            set(amydss.keys()), nadss)]
                        nadss = self.__rnd.randint(1, len(amydss.keys()) - 1)
                        indss = [ds for ds in self.__rnd.sample(
                            set(amydss.keys()), nadss)]

                        for tm in ltimers[mg]:
                            dss[tm] = bool(self.__rnd.randint(0, 1))

                        mncps = self.__rnd.randint(1, len(amycps.keys()) - 1)
                        mcps = [cp for cp in self.__rnd.sample(
                                set(amycps.keys()), mncps) if cp not in wrong]
                        oncps = self.__rnd.randint(1, len(amycps.keys()) - 1)
                        ocps = [cp for cp in self.__rnd.sample(
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
                        mp[mg]["PreselectedDataSources"] = \
                            json.dumps(aadss[mg])
                        mp[mg]["OptionalComponents"] = json.dumps(ocps)
                        mp[mg]["InitDataSources"] = json.dumps(indss)
                        mp[mg]["AppendEntry"] = bool(self.__rnd.randint(0, 1))
                        mp[mg]["ComponentsFromMntGrp"] = bool(
                            self.__rnd.randint(0, 1))
                        mp[mg]["DynamicComponents"] = bool(
                            self.__rnd.randint(0, 1))
                        mp[mg]["DefaultDynamicLinks"] = \
                            bool(self.__rnd.randint(0, 1))
                        mp[mg]["DefaultDynamicPath"] = self.getRandomName(20)
                        mp[mg]["TimeZone"] = self.getRandomName(20)

                        mp[mg]["ConfigVariables"] = json.dumps(dict(
                            (self.getRandomName(10),
                             self.getRandomName(15)) for _ in
                            range(self.__rnd.randint(1, 40))))
                        paths = dict(
                            (self.getRandomName(10),
                             self.getRandomName(15)) for _ in
                            range(self.__rnd.randint(1, 40)))
                        labels = dict(
                            (self.getRandomName(10),
                             self.getRandomName(15)) for _ in
                            range(self.__rnd.randint(1, 40)))
                        links = dict(
                            (self.getRandomName(10),
                             bool(self.__rnd.randint(0, 1))) for _ in
                            range(self.__rnd.randint(1, 40)))
                        types = dict(
                            (self.getRandomName(10),
                             self.getRandomName(15)) for _ in
                            range(self.__rnd.randint(1, 40)))
                        shapes = dict(
                            (self.getRandomName(10),
                             [self.__rnd.randint(1, 40)
                              for _ in range(self.__rnd.randint(0, 3))])
                            for _ in range(self.__rnd.randint(1, 40)))

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
                            nhe = self.__rnd.randint(0, len(set(chds)) - 1)
                            lheds = self.__rnd.sample(set(chds), nhe)

                        lhecp = []
                        if comps:
                            nhe = self.__rnd.randint(0, len(set(comps)) - 1)
                            lhecp = self.__rnd.sample(set(comps), nhe)

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
                        self.assertTrue(ors.isMntGrpUpdated())
                        self.assertTrue(ors.isMntGrpUpdated())

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
                                    print "DES", tm
                                    adss[mg][tm] = False

                        jpcnf = ors.updateMntGrp()
                        self.assertTrue(not ors.isMntGrpUpdated())
                        self.assertTrue(not ors.isMntGrpUpdated())
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
                            for exp in expch:
                                ds = exp["name"]
                                if ds in chds and cl == exp['controller']:
                                    if ds in self.smychsXX.keys():
                                        cnt = self.smychsXX[str(ds)]
                                        i = chds.index(str(ds))
                                        try:
                                            tdv = "/".join(
                                                cnt['source'].split("/")[:-1])
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
                                             'monitor': fltm,
                                             'id': 0,
                                             'timer': fltm,
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
                        print "MG", mg
                        ors.mntGrp = mg
                        ors.fetchProfile()
                        mp[mg] = json.loads(ors.profileConfiguration)
#                        self.myAssertRaise(Exception, ors.isMntGrpUpdated)
#                       ors.fetchProfile()
#                        mp[mg] = json.loads(ors.profileConfiguration)

                        self.assertTrue(not ors.isMntGrpUpdated())
                        self.assertTrue(not ors.isMntGrpUpdated())

                        self.compareToDumpJSON(
                            ors,
                            ["DataSourceSelection",
                             "UnplottedComponents",
                             "PreselectedDataSources",
                             "UnplottedComponents"],
                            name=mg)
                        mp[mg] = json.loads(ors.profileConfiguration)
                        self.myAssertDict(
                            json.loads(
                                mp[mg]["DataSourceSelection"]), adss[mg])
                        self.assertEqual(
                            set(json.loads(mp[mg]["PreselectedDataSources"])),
                            set(aadss[mg]))
                        print "PDS1", set(aadss[mg])
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
                        print "WWWMG", mg
                        self.compareToDumpJSON(
                            ors,
                            ["DataSourceSelection",
                             "UnplottedComponents",
                             "PreselectedDataSources"],
                            name=mg)

                    # check profile commands
                    mg1, mg2, mg3, mg4 = tuple(self.__rnd.sample(mgs, 4))
                    print "MGS", mg1, mg2, mg3, mg4
                    ors.profileConfiguration = str(json.dumps(mp[mg1]))
                    self.compareToDumpJSON(
                        ors,
                        ["DataSourceSelection",
                         "UnplottedComponents",
                         "PreselectedDataSources"],
                        name=mg1)
                    ors.profileConfiguration = str(json.dumps(mp[mg2]))
                    self.compareToDumpJSON(
                        ors,
                        ["DataSourceSelection",
                         "UnplottedComponents",
                         "PreselectedDataSources"],
                        name=mg2)
                    ors.profileConfiguration = str(json.dumps(mp[mg3]))
                    self.compareToDumpJSON(
                        ors,
                        ["DataSourceSelection",
                         "UnplottedComponents",
                         "PreselectedDataSources"],
                        name=mg3)
                    ors.profileConfiguration = str(json.dumps(mp[mg4]))
                    self.compareToDumpJSON(
                        ors,
                        ["DataSourceSelection",
                         "UnplottedComponents",
                         "PreselectedDataSources"],
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
                            "PreselectedDataSources",
                            "Timer"
                        ],
                        name=mg1)
                    ors.profileConfiguration = str(json.dumps(mp[mg1]))
                    tmpcf = json.loads(ors.mntGrpConfiguration())
                    ltmpcf = json.loads(lrs.mntGrpConfiguration())
                    self.myAssertDict(tmpcf, ltmpcf)

                    self.assertEqual(
                        set(json.loads(lmp["PreselectedDataSources"])),
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

                    print "MGS", mg1, mg2, mg3, mg4

                    # import mntgrp another defined by selector MntGrp
                    lrs.mntGrp = mg2

                    self.assertTrue(lrs.isMntGrpUpdated())
                    self.assertTrue(lrs.isMntGrpUpdated())

                    lrs.importMntGrp()
                    lmp = json.loads(lrs.profileConfiguration)
                    self.assertTrue(lrs.isMntGrpUpdated())
                    self.assertTrue(lrs.isMntGrpUpdated())

                    ors.profileConfiguration = str(json.dumps(mp[mg1]))
                    tmpcf1 = json.loads(ors.mntGrpConfiguration())
                    ors.profileConfiguration = str(json.dumps(mp[mg2]))
                    tmpcf2 = json.loads(ors.mntGrpConfiguration())
                    ltmpcf = json.loads(lrs.mntGrpConfiguration())
#                    self.myAssertDict(tmpcf1, ltmpcf)
                    self.myAssertDict(tmpcf2, ltmpcf)
                    print "RSmg2",
                    ors.profileConfiguration = str(json.dumps(mp[mg2]))
                    self.compareToDumpJSON(
                        ors,
                        ["DataSourceSelection",
                         "UnplottedComponents",
                         "PreselectedDataSources"],
                        name=mg2)
                    self.compareToDumpJSON(
                        lrs,
                        ["DataSourceSelection",
                         "UnplottedComponents",
                         "PreselectedDataSources",
                         "Timer",
                         "MntGrp"],
                        name=mg1)

                    continue
                    ors.profileConfiguration = str(json.dumps(mp[mg2]))
                    tmpcf = json.loads(ors.mntGrpConfiguration())
                    ltmpcf = json.loads(lrs.mntGrpConfiguration())
                    self.myAssertDict(tmpcf, ltmpcf)

                    self.assertEqual(
                        set(json.loads(lmp["PreselectedDataSources"])),
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

                    print "T1", json.loads(mp[mg1]["Timer"])
                    print "T2", json.loads(mp[mg2]["Timer"])
                    print "LT", json.loads(lmp["Timer"])
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
                    print "name", tmg[mg2].new_device_info_writer.name
                    mgdp.Configuration = json.dumps(tmpcf)
                    self.assertTrue(lrs.isMntGrpUpdated())
                    self.assertTrue(lrs.isMntGrpUpdated())

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
                        self.assertTrue(lrs.isMntGrpUpdated())
                        self.assertTrue(lrs.isMntGrpUpdated())

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
                         "PreselectedDataSources",
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
                         "PreselectedDataSources",
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
                        set(json.loads(mp[mg2]["PreselectedDataSources"])),
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
                            "PreselectedDataSources",
                            "Timer"],
                        name=mg3)
                    lmp = json.loads(lrs.profileConfiguration)
                    self.myAssertDict(json.loads(lmp["DataSourceSelection"]),
                                      adss[mg3])
                    self.assertEqual(
                        set(json.loads(lmp["PreselectedDataSources"])),
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
                            "PreselectedDataSources",
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
                        set(json.loads(lmp["PreselectedDataSources"])),
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
                    self.assertTrue(lrs.isMntGrpUpdated())
                    self.assertTrue(lrs.isMntGrpUpdated())
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
                            "PreselectedDataSources",
                            "Timer"],
                        name=mg3)
                    self.myAssertDict(json.loads(lmp["DataSourceSelection"]),
                                      adss[mg3])
                    self.assertEqual(
                        set(json.loads(lmp["PreselectedDataSources"])),
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
                            "PreselectedDataSources",
                            "Timer"],
                        name=mg3)
                    lmp = json.loads(lrs.profileConfiguration)
                    self.myAssertDict(json.loads(lmp["DataSourceSelection"]),
                                      adss[mg3])
                    self.assertEqual(
                        set(json.loads(lmp["PreselectedDataSources"])),
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
                            "PreselectedDataSources",
                            "Timer"],
                        name=mg3)
                    lmp = json.loads(lrs.profileConfiguration)
                    self.myAssertDict(json.loads(lmp["DataSourceSelection"]),
                                      adss[mg3])
                    self.assertEqual(
                        set(json.loads(lmp["PreselectedDataSources"])),
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

                    ## fetch non-existing mg
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
                            "PreselectedDataSources",
                            "Timer", "MntGrp"],
                        name=mg3)
                    lmp = json.loads(lrs.profileConfiguration)
                    self.myAssertDict(json.loads(lmp["DataSourceSelection"]),
                                      adss[mg3])
                    self.assertEqual(
                        set(json.loads(lmp["PreselectedDataSources"])),
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

                    ## fetch non-existing selection
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
                            "InitDataSources",
                            "PreselectedDataSources",
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
                        set(json.loads(lmp["PreselectedDataSources"])),
                        set(aadss[mg3]))
                    self.assertEqual(
                        set(json.loads(lmp["InitDataSources"])),
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

    ## constructor test
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

    ## constructor test
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

    ## constructor test
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

    ## constructor test
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

    ## constructor test
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

    ## constructor test
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
            nmem = self.__rnd.randint(1, len(self.mycps.keys()) - 1)
            mem = self.__rnd.sample(set(self.mycps.keys()), nmem)
            self._cf.dp.SetCommandVariable(["MCPLIST", json.dumps(mem)])

            for cp in self.mycps.keys():
                res = json.loads(rs.componentClientSources([cp]))
                self.checkICP(res, [cp],
                              strategy=None, dstype='CLIENT')
            res = json.loads(rs.componentClientSources(self.mycps.keys()))
            self.checkICP(res, self.rescps.keys(),
                          strategy=None, dstype='CLIENT')

    ## constructor test
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
            nmem = self.__rnd.randint(1, len(self.mycps.keys()) - 1)
            mem = self.__rnd.sample(set(self.mycps.keys()), nmem)

            res = json.loads(rs.componentClientSources(mem))
            self.checkICP(res, mem,
                          strategy=None, dstype='CLIENT')

    ## constructor test
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
            nmem = self.__rnd.randint(1, len(self.mycps.keys()) - 1)
            mem = self.__rnd.sample(set(self.mycps.keys()), nmem)
            self._cf.dp.SetCommandVariable(["MCPLIST", json.dumps(mem)])

            nccp = self.__rnd.randint(1, len(self.mycps.keys()) - 1)
            ccp = self.__rnd.sample(set(self.mycps.keys()), nccp)
            cps = {}
            for cp in ccp:
                cps[cp] = bool(self.__rnd.randint(0, 1))

            nacp = self.__rnd.randint(1, len(self.mycps.keys()) - 1)
            acp = self.__rnd.sample(set(self.mycps.keys()), nacp)
            acps = {}
            for cp in acp:
                acps[cp] = bool(self.__rnd.randint(0, 1))

            cnf = json.loads(rs.profileConfiguration)
            cnf["ComponentPreselection"] = json.dumps(acps)
            cnf["ComponentSelection"] = json.dumps(cps)
            rs.profileConfiguration = json.dumps(cnf)
            # print "CPS", rs.components

            res = json.loads(rs.componentClientSources([]))
            self.checkICP(res, rs.components,
                          strategy=None, dstype='CLIENT')

    ## constructor test
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
            nmem = self.__rnd.randint(1, len(self.mycpsvar.keys()) - 1)
            mem = self.__rnd.sample(set(self.mycpsvar.keys()), nmem)
            self._cf.dp.SetCommandVariable(["MCPLIST", json.dumps(mem)])

            nccp = self.__rnd.randint(1, len(self.mycpsvar.keys()) - 1)
            ccp = self.__rnd.sample(set(self.mycpsvar.keys()), nccp)
            cps = {}
            for cp in ccp:
                cps[cp] = bool(self.__rnd.randint(0, 1))
            rs.configVariables = '{"c01": "exp_c01", "c02": "exp_c02", ' + \
                                 '"mca": "p09/mca/exp.02"}'
            self._cf.dp.SetCommandVariable(["CHECKVARIABLES",
                                            json.dumps(rs.configVariables)])
            nacp = self.__rnd.randint(1, len(self.mycpsvar.keys()) - 1)
            acp = self.__rnd.sample(set(self.mycpsvar.keys()), nacp)
            acps = {}
            for cp in acp:
                acps[cp] = bool(self.__rnd.randint(0, 1))

            cnf = json.loads(rs.profileConfiguration)
            cnf["ComponentPreselection"] = json.dumps(acps)
            cnf["ComponentSelection"] = json.dumps(cps)
            rs.profileConfiguration = json.dumps(cnf)
            print "CPS", rs.components

            res = rs.componentClientSources([])
            res = json.loads(
                res.replace(
                    "$var.c01", "exp_c01").replace(
                        "$var.c02", "exp_c02").replace(
                            "$var.mca", "p09/mca/exp.02"))
            self.checkICP(res, rs.components,
                          strategy=None, dstype='CLIENT')

    ## constructor test
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

    ## constructor test
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
            '<group name="entry$var.serialno" type="NXentry">\n'
            '<group name="instrument" type="NXinstrument">\n'
            '<group name="collection" type="NXcollection">\n'
            '<field name="onename" type="NX_CHAR">\n<strategy mode="STEP"/>\n'
            '<datasource name="onename" type="CLIENT">\n'
            '<record name="onename"/>\n</datasource>\n</field>\n'
            '</group>\n</group>\n<group name="data" type="NXdata">\n'
            '<link name="onename" target="/entry$var.serialno:'
            'NXentry/NXinstrument/collection/onename"/>\n'
            '</group>\n</group>\n</definition>\n',
            "two":
                '<?xml version="1.0" ?>\n<definition>\n'
            '<group name="entry$var.serialno" type="NXentry">\n'
            '<group name="instrument" type="NXinstrument">\n'
            '<group name="collection" type="NXcollection">\n'
            '<field name="ds1" type="NX_CHAR">\n<strategy mode="STEP"/>\n'
            '<datasource name="ds1" type="CLIENT">\n<record name="ds1"/>\n'
            '</datasource>\n</field>\n</group>\n</group>\n'
            '<group name="data" type="NXdata">\n'
            '<link name="ds1" target="/entry$var.serialno:'
            'NXentry/NXinstrument/collection/ds1"/>\n</group>\n</group>\n'
            '<group name="entry$var.serialno" type="NXentry">'
            '\n<group name="instrument" type="NXinstrument">\n'
            '<group name="collection" type="NXcollection">\n'
            '<field name="ds2" type="NX_CHAR">\n<strategy mode="STEP"/>\n'
            '<datasource name="ds2" type="CLIENT">\n<record name="ds2"/>\n'
            '</datasource>\n</field>\n</group>\n</group>\n'
            '<group name="data" type="NXdata">\n'
            '<link name="ds2" target="/entry$var.serialno:'
            'NXentry/NXinstrument/collection/ds2"/>\n</group>\n'
            '</group>\n</definition>\n',
            "three":
                '<?xml version="1.0" ?>\n<definition>\n'
            '<group name="entry$var.serialno" type="NXentry">\n'
            '<group name="instrument" type="NXinstrument">\n'
            '<group name="collection" type="NXcollection">\n'
            '<field name="ds1" type="NX_CHAR">\n<strategy mode="STEP"/>\n'
            '<datasource name="ds1" type="CLIENT">\n<record name="ds1"/>\n'
            '</datasource>\n</field>\n</group>\n</group>\n'
            '<group name="data" type="NXdata">\n'
            '<link name="ds1" target="/entry$var.serialno:'
            'NXentry/NXinstrument/collection/ds1"/>\n</group>\n</group>\n'
            '<group name="entry$var.serialno" type="NXentry">'
            '\n<group name="instrument" type="NXinstrument">\n'
            '<group name="collection" type="NXcollection">\n'
            '<field name="ds2" type="NX_CHAR">\n<strategy mode="STEP"/>\n'
            '<datasource name="ds2" type="CLIENT">\n<record name="ds2"/>\n'
            '</datasource>\n</field>\n</group>\n</group>\n'
            '<group name="data" type="NXdata">\n'
            '<link name="ds2" target="/entry$var.serialno:'
            'NXentry/NXinstrument/collection/ds2"/>\n</group>\n</group>\n'
            '<group name="entry$var.serialno" type="NXentry">'
            '\n<group name="instrument" type="NXinstrument">\n'
            '<group name="collection" type="NXcollection">\n'
            '<field name="ds3" type="NX_CHAR">\n<strategy mode="STEP"/>\n'
            '<datasource name="ds3" type="CLIENT">\n<record name="ds3"/>\n'
            '</datasource>\n</field>\n</group>\n</group>\n'
            '<group name="data" type="NXdata">\n'
            '<link name="ds3" target="/entry$var.serialno:'
            'NXentry/NXinstrument/collection/ds3"/>\n</group>\n</group>\n'
            '</definition>\n',
            "type":
                '<?xml version="1.0" ?>\n<definition>\n'
            '<group name="entry$var.serialno" type="NXentry">\n'
            '<group name="instrument" type="NXinstrument">\n'
            '<group name="collection" type="NXcollection">\n'
            '<field name="ds1" type="NX_INT">\n<strategy mode="STEP"/>\n'
            '<datasource name="ds1" type="CLIENT">\n'
            '<record name="ds1"/>\n</datasource>\n</field>\n'
            '</group>\n</group>\n<group name="data" type="NXdata">\n'
            '<link name="ds1" target="/entry$var.serialno:'
            'NXentry/NXinstrument/collection/ds1"/>\n'
            '</group>\n</group>\n</definition>\n',
            "shape":
                '<?xml version="1.0" ?>\n<definition>\n'
            '<group name="entry$var.serialno" type="NXentry">\n'
            '<group name="instrument" type="NXinstrument">\n'
            '<group name="collection" type="NXcollection">\n'
            '<field name="ds2" type="NX_CHAR">\n<strategy mode="STEP"/>\n'
            '<datasource name="ds2" type="CLIENT">\n'
            '<record name="ds2"/>\n</datasource>\n'
            '<dimensions rank="1">\n<dim index="1" value="34"/>\n'
            '</dimensions>\n</field>\n'
            '</group>\n</group>\n<group name="data" type="NXdata">\n'
            '<link name="ds2" target="/entry$var.serialno:'
            'NXentry/NXinstrument/collection/ds2"/>\n'
            '</group>\n</group>\n</definition>\n',
            "shapetype":
                '<?xml version="1.0" ?>\n<definition>\n'
            '<group name="entry$var.serialno" type="NXentry">\n'
            '<group name="instrument" type="NXinstrument">\n'
            '<group name="collection" type="NXcollection">\n'
            '<field name="ds3" type="NX_FLOAT64">\n<strategy mode="STEP"/>\n'
            '<datasource name="ds3" type="CLIENT">\n'
            '<record name="ds3"/>\n</datasource>\n'
            '<dimensions rank="2">\n<dim index="1" value="3"/>\n'
            '<dim index="2" value="56"/>\n</dimensions>\n</field>\n'
            '</group>\n</group>\n<group name="data" type="NXdata">\n'
            '<link name="ds3" target="/entry$var.serialno:'
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
            print ds
            cpname = rs.createDynamicComponent(["", str(json.dumps(ds))])
            comp = self._cf.dp.Components([cpname])[0]
            self.assertEqual(cps[lb], comp)

    ## constructor test
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
            '<group name="entry$var.serialno" type="NXentry">\n'
            '<group name="instrument" type="NXinstrument">\n'
            '<group name="collection" type="NXcollection">\n'
            '<field name="ds1" type="%s">\n<strategy mode="STEP"/>\n'
            '<datasource name="ds1" type="CLIENT">\n'
            '<record name="ds1"/>\n</datasource>\n</field>\n'
            '</group>\n</group>\n<group name="data" type="NXdata">\n'
            '<link name="ds1" target="/entry$var.serialno:'
            'NXentry/NXinstrument/collection/ds1"/>\n'
            '</group>\n</group>\n</definition>\n',
        }
        dname = "__dynamic_component__"
        for tp, nxstp in self.__npTn.items():
            cpname = rs.createDynamicComponent([
                "", str(json.dumps([{"name": "ds1", "dtype": tp}]))])
            comp = self._cf.dp.Components([cpname])[0]
            self.assertEqual(cps["type"] % nxstp, comp)

    ## constructor test
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
            '<group name="entry$var.serialno" type="NXentry">\n'
            '<group name="instrument" type="NXinstrument">\n'
            '<group name="collection" type="NXcollection">\n'
            '<field name="ds2" type="NX_CHAR">\n<strategy mode="STEP"/>\n'
            '<datasource name="ds2" type="CLIENT">\n'
            '<record name="ds2"/>\n</datasource>\n%s</field>\n'
            '</group>\n</group>\n<group name="data" type="NXdata">\n'
            '<link name="ds2" target="/entry$var.serialno:'
            'NXentry/NXinstrument/collection/ds2"/>\n'
            '</group>\n</group>\n</definition>\n',
        }

        dimbg = '<dimensions rank="%s">\n'
        dim = '<dim index="%s" value="%s"/>\n'
        dimend = '</dimensions>\n'

        dname = "__dynamic_component__"
        for i in range(50):
            ms = [self.__rnd.randint(0, 3000)
                  for _ in range(self.__rnd.randint(0, 3))]
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

    ## constructor test
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
            '<group name="entry$var.serialno" type="NXentry">\n'
            '<group name="instrument" type="NXinstrument">\n'
            '<group name="collection" type="NXcollection">\n'
            '<field name="%s" type="%s">\n<strategy mode="STEP"/>\n'
            '<datasource name="%s" type="CLIENT">\n'
            '<record name="%s"/>\n</datasource>\n'
            '%s</field>\n'
            '</group>\n</group>\n%s</group>\n</definition>\n',
        }

        link = '<group name="data" type="NXdata">\n' + \
            '<link name="%s" target="/entry$var.serialno:' + \
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
                for tp, nxstp in self.__npTn.items():
                    lbl = self.getRandomName(20)
                    ms = [self.__rnd.randint(0, 3000)
                          for _ in range(self.__rnd.randint(0, 3))]
                    ms2 = [self.__rnd.randint(0, 3000)
                           for _ in range(self.__rnd.randint(0, 3))]
                    tmptp = self.__rnd.choice(self.__npTn.keys())
                    cnf = dict(cnfdef)
                    labels = {}
                    paths = {}
                    links = {}
                    types = {}
                    shapes = {}

                    if i == 0:
                        cnf["DefaultDynamicLinks"] = False
                        cnf["DefaultDynamicPath"] = self.__defaultpath
                    elif i == 1:
                        cnf["DefaultDynamicLinks"] = True
                        cnf["DefaultDynamicPath"] = self.__defaultpath
                    elif i == 2:
                        links = {ar["name"]: False}
                    elif i == 3:
                        links = {ar["name"]: True}
                    elif i == 4:
                        cnf["DefaultDynamicLinks"] = True
                        cnf["DefaultDynamicPath"] = self.__defaultpath
                        links = {ar["name"]: False}
                    elif i == 5:
                        cnf["DefaultDynamicLinks"] = False
                        cnf["DefaultDynamicPath"] = self.__defaultpath
                        links = {ar["name"]: True}
                    elif i == 6:
                        cnf["DefaultDynamicLinks"] = False
                        cnf["DefaultDynamicPath"] = self.__defaultpath
                        links = {ar["full_name"]: True}
                        shapes = {ar["name"]: ms2}
                    elif i == 7:
                        types = {ar["name"]: tmptp}
                    elif i == 8:
                        cnf["DefaultDynamicLinks"] = True
                        cnf["DefaultDynamicPath"] = self.__defaultpath
                        labels = {ar["name"]: lbl}
                        links = {lbl: False}
                    elif i == 9:
                        cnf["DefaultDynamicLinks"] = False
                        cnf["DefaultDynamicPath"] = self.__defaultpath
                        labels = {ar["name"]: lbl}
                        links = {lbl: True}
                    elif i == 10:
                        cnf["DefaultDynamicLinks"] = False
                        cnf["DefaultDynamicPath"] = self.__defaultpath
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
                    print "I = ", i
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

    ## constructor test
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
            '<group name="entry$var.serialno" type="NXentry">\n'
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
                print "I = ", i
                for tp, nxstp in self.__npTn.items():
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
                         if self.__rnd.randint(0, 1) else None,
                         ("NX" + self.getRandomName(20))
                         if self.__rnd.randint(0, 1) else None)
                        for _ in range(self.__rnd.randint(0, 10))]
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
                    ms = [self.__rnd.randint(0, 3000)
                          for _ in range(self.__rnd.randint(0, 3))]
                    ms2 = [self.__rnd.randint(0, 3000)
                           for _ in range(self.__rnd.randint(0, 3))]
                    tmptp = self.__rnd.choice(self.__npTn.keys())
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
                    print "I = ", i
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
                            lk = link % (ds, self.__defaultpath, ds)
                        else:
                            lk = link % (fieldname.lower(), self.__defaultpath,
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

    ## constructor test
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
        groupbg = '<group name="entry$var.serialno" type="NXentry">\n' + \
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
                print "I = ", i, ar["name"]
                db.put_device_alias(ar["full_name"], ar["name"])

                cpname = rs.createDynamicComponent([
                    "", str(json.dumps([{"name": ar["full_name"]}]))])

                comp = self._cf.dp.Components([cpname])[0]
                mycps = defbg + groupbg + fieldbg % (ar["name"], "NX_CHAR")
                if i % 2:
                    sso = ar["source"].split("/")
                    mycps += dstango % (
                        ar["name"], "/".join(sso[:-1]), sso[-1])
                else:
                    mycps += dsclient % (ar["name"], ar["full_name"])
                mycps += fieldend + groupend + groupend
                mycps += link % (ar["name"], self.__defaultpath,
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

    ## constructor test
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
            '<group name="entry$var.serialno" type="NXentry">\n'
            '<group name="instrument" type="NXinstrument">\n'
            '<group name="collection" type="NXcollection">\n'
            '<field name="one" type="NX_CHAR">\n<strategy mode="STEP"/>\n'
            '<datasource name="one" type="CLIENT">\n<record name="one"/>\n'
            '</datasource>\n</field>\n'
            '</group>\n</group>\n'
            '<group name="data" type="NXdata">\n'
            '<link name="one" target="/entry$var.serialno:'
            'NXentry/NXinstrument/collection/one"/>\n'
            '</group>\n</group>\n'
            '</definition>\n',
            "two":
                '<?xml version="1.0" ?>\n<definition>\n'
            '<group name="entry$var.serialno" type="NXentry">\n'
            '<group name="instrument" type="NXinstrument">\n'
            '<group name="collection" type="NXcollection">\n'
            '<field name="d1" type="NX_CHAR">\n<strategy mode="STEP"/>\n'
            '<datasource name="d1" type="CLIENT">\n<record name="d1"/>\n'
            '</datasource>\n</field>\n'
            '</group>\n</group>\n'
            '<group name="data" type="NXdata">\n'
            '<link name="d1" target="/entry$var.serialno:'
            'NXentry/NXinstrument/collection/d1"/>\n'
            '</group>\n</group>\n'
            '<group name="entry$var.serialno" type="NXentry">\n'
            '<group name="instrument" type="NXinstrument">\n'
            '<group name="collection" type="NXcollection">\n'
            '<field name="d2" type="NX_CHAR">\n<strategy mode="STEP"/>\n'
            '<datasource name="d2" type="CLIENT">\n<record name="d2"/>\n'
            '</datasource>\n</field>\n</group>\n</group>\n'
            '<group name="data" type="NXdata">\n'
            '<link name="d2" target="/entry$var.serialno:'
            'NXentry/NXinstrument/collection/d2"/>\n'
            '</group>\n</group>\n'
            '</definition>\n',
            "three":
                '<?xml version="1.0" ?>\n<definition>\n'
            '<group name="entry$var.serialno" type="NXentry">\n'
            '<group name="instrument" type="NXinstrument">\n'
            '<group name="collection" type="NXcollection">\n'
            '<field name="ds1" type="NX_CHAR">\n<strategy mode="STEP"/>\n'
            '<datasource name="ds1" type="CLIENT">\n<record name="ds1"/>\n'
            '</datasource>\n</field>\n'
            '</group>\n</group>\n'
            '<group name="data" type="NXdata">\n'
            '<link name="ds1" target="/entry$var.serialno:'
            'NXentry/NXinstrument/collection/ds1"/>\n'
            '</group>\n</group>\n'
            '<group name="entry$var.serialno" type="NXentry">\n'
            '<group name="instrument" type="NXinstrument">\n'
            '<group name="collection" type="NXcollection">\n'
            '<field name="ds2" type="NX_CHAR">\n<strategy mode="STEP"/>\n'
            '<datasource name="ds2" type="CLIENT">\n<record name="ds2"/>\n'
            '</datasource>\n</field>\n</group>\n</group>\n'
            '<group name="data" type="NXdata">\n'
            '<link name="ds2" target="/entry$var.serialno:'
            'NXentry/NXinstrument/collection/ds2"/>\n'
            '</group>\n</group>\n'
            '<group name="entry$var.serialno" type="NXentry">\n'
            '<group name="instrument" type="NXinstrument">\n'
            '<group name="collection" type="NXcollection">\n'
            '<field name="ds3" type="NX_CHAR">\n<strategy mode="STEP"/>\n'
            '<datasource name="ds3" type="CLIENT">\n<record name="ds3"/>\n'
            '</datasource>\n</field>\n</group>\n</group>\n'
            '<group name="data" type="NXdata">\n'
            '<link name="ds3" target="/entry$var.serialno:'
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

    ## constructor test
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
            '<group name="entry$var.serialno" type="NXentry">\n'
            '<group name="instrument" type="NXinstrument">\n'
            '<group name="collection" type="NXcollection">\n'
            '<field name="one" type="NX_CHAR">\n<strategy mode="STEP"/>\n'
            '<datasource name="one" type="CLIENT">\n<record name="one"/>\n'
            '</datasource>\n</field>\n'
            '</group>\n</group>\n'
            '<group name="data" type="NXdata">\n'
            '<link name="one" target="/entry$var.serialno:'
            'NXentry/NXinstrument/collection/one"/>\n'
            '</group>\n</group>\n'
            '</definition>\n',
            "two":
                '<?xml version="1.0" ?>\n<definition>\n'
            '<group name="entry$var.serialno" type="NXentry">\n'
            '<group name="instrument" type="NXinstrument">\n'
            '<group name="collection" type="NXcollection">\n'
            '<field name="d1" type="NX_CHAR">\n<strategy mode="STEP"/>\n'
            '<datasource name="d1" type="CLIENT">\n<record name="d1"/>\n'
            '</datasource>\n</field>\n'
            '</group>\n</group>\n'
            '<group name="data" type="NXdata">\n'
            '<link name="d1" target="/entry$var.serialno:'
            'NXentry/NXinstrument/collection/d1"/>\n'
            '</group>\n</group>\n'
            '<group name="entry$var.serialno" type="NXentry">\n'
            '<group name="instrument" type="NXinstrument">\n'
            '<group name="collection" type="NXcollection">\n'
            '<field name="d2" type="NX_CHAR">\n<strategy mode="STEP"/>\n'
            '<datasource name="d2" type="CLIENT">\n<record name="d2"/>\n'
            '</datasource>\n</field>\n</group>\n</group>\n'
            '<group name="data" type="NXdata">\n'
            '<link name="d2" target="/entry$var.serialno:'
            'NXentry/NXinstrument/collection/d2"/>\n'
            '</group>\n</group>\n'
            '</definition>\n',
            "three":
                '<?xml version="1.0" ?>\n<definition>\n'
            '<group name="entry$var.serialno" type="NXentry">\n'
            '<group name="instrument" type="NXinstrument">\n'
            '<group name="collection" type="NXcollection">\n'
            '<field name="ds1" type="NX_CHAR">\n<strategy mode="STEP"/>\n'
            '<datasource name="ds1" type="CLIENT">\n<record name="ds1"/>\n'
            '</datasource>\n</field>\n'
            '</group>\n</group>\n'
            '<group name="data" type="NXdata">\n'
            '<link name="ds1" target="/entry$var.serialno:'
            'NXentry/NXinstrument/collection/ds1"/>\n'
            '</group>\n</group>\n'
            '<group name="entry$var.serialno" type="NXentry">\n'
            '<group name="instrument" type="NXinstrument">\n'
            '<group name="collection" type="NXcollection">\n'
            '<field name="ds2" type="NX_CHAR">\n<strategy mode="STEP"/>\n'
            '<datasource name="ds2" type="CLIENT">\n<record name="ds2"/>\n'
            '</datasource>\n</field>\n</group>\n</group>\n'
            '<group name="data" type="NXdata">\n'
            '<link name="ds2" target="/entry$var.serialno:'
            'NXentry/NXinstrument/collection/ds2"/>\n'
            '</group>\n</group>\n'
            '<group name="entry$var.serialno" type="NXentry">\n'
            '<group name="instrument" type="NXinstrument">\n'
            '<group name="collection" type="NXcollection">\n'
            '<field name="ds3" type="NX_CHAR">\n<strategy mode="STEP"/>\n'
            '<datasource name="ds3" type="CLIENT">\n<record name="ds3"/>\n'
            '</datasource>\n</field>\n</group>\n</group>\n'
            '<group name="data" type="NXdata">\n'
            '<link name="ds3" target="/entry$var.serialno:'
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
            print rs.selectedDataSources()
            cpname = rs.createDynamicComponent([])
            comp = self._cf.dp.Components([cpname])[0]
            self.assertEqual(cps["empty"], comp)

    ## constructor test
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
            '<group name="entry$var.serialno" type="NXentry">\n'
            '<group name="instrument" type="NXinstrument">\n'
            '<group name="collection" type="NXcollection">\n'
            '<field name="ds1" type="%s">\n<strategy mode="STEP"/>\n'
            '<datasource name="ds1" type="CLIENT">\n'
            '<record name="ds1"/>\n</datasource>\n</field>\n'
            '</group>\n</group>\n<group name="data" type="NXdata">\n'
            '<link name="ds1" target="/entry$var.serialno:'
            'NXentry/NXinstrument/collection/ds1"/>\n'
            '</group>\n</group>\n</definition>\n',
        }
        dname = "__dynamic_component__"
        for tp, nxstp in self.__npTn.items():
            cpname = rs.createDynamicComponent([
                str(json.dumps(["ds1"]))])

            comp = self._cf.dp.Components([cpname])[0]
            self.assertEqual(cps["type"] % "NX_CHAR", comp)

    ## constructor test
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
            '<group name="entry$var.serialno" type="NXentry">\n'
            '<group name="instrument" type="NXinstrument">\n'
            '<group name="collection" type="NXcollection">\n'
            '<field name="ds1" type="%s">\n<strategy mode="INIT"/>\n'
            '<datasource name="ds1" type="CLIENT">\n'
            '<record name="ds1"/>\n</datasource>\n</field>\n'
            '</group>\n</group>\n<group name="data" type="NXdata">\n'
            '<link name="ds1" target="/entry$var.serialno:'
            'NXentry/NXinstrument/collection/ds1"/>\n'
            '</group>\n</group>\n</definition>\n',
        }
        dname = "__dynamic_component__"
        for tp, nxstp in self.__npTn.items():
            cpname = rs.createDynamicComponent([
                "", "",
                str(json.dumps(["ds1"]))])

            comp = self._cf.dp.Components([cpname])[0]
            self.assertEqual(cps["type"] % "NX_CHAR", comp)

    ## constructor test
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
            '<group name="entry$var.serialno" type="NXentry">\n'
            '<group name="instrument" type="NXinstrument">\n'
            '<group name="collection" type="NXcollection">\n'
            '<field name="ds1" type="%s">\n<strategy mode="STEP"/>\n'
            '<datasource name="ds1" type="CLIENT">\n'
            '<record name="ds1"/>\n</datasource>\n</field>\n'
            '</group>\n</group>\n<group name="data" type="NXdata">\n'
            '<link name="ds1" target="/entry$var.serialno:'
            'NXentry/NXinstrument/collection/ds1"/>\n'
            '</group>\n</group>\n</definition>\n',
        }
        dname = "__dynamic_component__"
        for tp, nxstp in self.__npTn.items():
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

    ## constructor test
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
            '<group name="entry$var.serialno" type="NXentry">\n'
            '<group name="instrument" type="NXinstrument">\n'
            '<group name="collection" type="NXcollection">\n'
            '<field name="ds1" type="%s">\n<strategy mode="INIT"/>\n'
            '<datasource name="ds1" type="CLIENT">\n'
            '<record name="ds1"/>\n</datasource>\n</field>\n'
            '</group>\n</group>\n<group name="data" type="NXdata">\n'
            '<link name="ds1" target="/entry$var.serialno:'
            'NXentry/NXinstrument/collection/ds1"/>\n'
            '</group>\n</group>\n</definition>\n',
        }
        dname = "__dynamic_component__"
        for tp, nxstp in self.__npTn.items():
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

    ## constructor test
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
            '<group name="entry$var.serialno" type="NXentry">\n'
            '<group name="instrument" type="NXinstrument">\n'
            '<group name="collection" type="NXcollection">\n'
            '<field name="ds2" type="NX_CHAR">\n<strategy mode="STEP"/>\n'
            '<datasource name="ds2" type="CLIENT">\n'
            '<record name="ds2"/>\n</datasource>\n%s</field>\n'
            '</group>\n</group>\n<group name="data" type="NXdata">\n'
            '<link name="ds2" target="/entry$var.serialno:'
            'NXentry/NXinstrument/collection/ds2"/>\n'
            '</group>\n</group>\n</definition>\n',
        }

        dimbg = '<dimensions rank="%s">\n'
        dim = '<dim index="%s" value="%s"/>\n'
        dimend = '</dimensions>\n'

        dname = "__dynamic_component__"
        for i in range(50):
            ms = [self.__rnd.randint(0, 3000)
                  for _ in range(self.__rnd.randint(0, 3))]

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

    ## constructor test
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
            '<group name="entry$var.serialno" type="NXentry">\n'
            '<group name="instrument" type="NXinstrument">\n'
            '<group name="collection" type="NXcollection">\n'
            '<field name="ds2" type="NX_CHAR">\n<strategy mode="INIT"/>\n'
            '<datasource name="ds2" type="CLIENT">\n'
            '<record name="ds2"/>\n</datasource>\n%s</field>\n'
            '</group>\n</group>\n<group name="data" type="NXdata">\n'
            '<link name="ds2" target="/entry$var.serialno:'
            'NXentry/NXinstrument/collection/ds2"/>\n'
            '</group>\n</group>\n</definition>\n',
        }

        dimbg = '<dimensions rank="%s">\n'
        dim = '<dim index="%s" value="%s"/>\n'
        dimend = '</dimensions>\n'

        dname = "__dynamic_component__"
        for i in range(50):
            ms = [self.__rnd.randint(0, 3000)
                  for _ in range(self.__rnd.randint(0, 3))]
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

    ## constructor test
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
            '<group name="entry$var.serialno" type="NXentry">\n'
            '<group name="instrument" type="NXinstrument">\n'
            '<group name="collection" type="NXcollection">\n'
            '<field name="%s" type="%s">\n<strategy mode="STEP"/>\n'
            '<datasource name="%s" type="CLIENT">\n'
            '<record name="%s"/>\n</datasource>\n'
            '%s</field>\n'
            '</group>\n</group>\n%s</group>\n</definition>\n',
        }

        link = '<group name="data" type="NXdata">\n' + \
            '<link name="%s" target="/entry$var.serialno:' + \
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
                for tp, nxstp in self.__npTn.items():
                    lbl = self.getRandomName(20)
                    ms = [self.__rnd.randint(0, 3000)
                          for _ in range(self.__rnd.randint(0, 3))]
                    ms2 = [self.__rnd.randint(0, 3000)
                           for _ in range(self.__rnd.randint(0, 3))]
                    tmptp = self.__rnd.choice(self.__npTn.keys())
                    cnf = dict(cnfdef)
                    labels = {}
                    paths = {}
                    links = {}
                    types = {}
                    shapes = {}

                    if i == 0:
                        cnf["DefaultDynamicLinks"] = False
                        cnf["DefaultDynamicPath"] = self.__defaultpath
                        types = {ar["name"]: nxstp}
                        shapes = {ar["name"]: ms}
                    elif i == 1:
                        cnf["DefaultDynamicLinks"] = True
                        cnf["DefaultDynamicPath"] = self.__defaultpath
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
                        cnf["DefaultDynamicPath"] = self.__defaultpath
                        links = {ar["name"]: False}
                        types = {ar["name"]: nxstp}
                        shapes = {ar["name"]: ms}
                    elif i == 5:
                        cnf["DefaultDynamicLinks"] = False
                        cnf["DefaultDynamicPath"] = self.__defaultpath
                        links = {ar["name"]: True}
                        types = {ar["name"]: nxstp}
                        shapes = {ar["name"]: ms}
                    elif i == 6:
                        cnf["DefaultDynamicLinks"] = False
                        cnf["DefaultDynamicPath"] = self.__defaultpath
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
                        cnf["DefaultDynamicPath"] = self.__defaultpath
                        labels = {ar["name"]: lbl}
                        types = {ar["name"]: nxstp}
                        shapes = {ar["name"]: ms}
                    elif i == 9:
                        cnf["DefaultDynamicLinks"] = True
                        cnf["DefaultDynamicPath"] = self.__defaultpath
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
                        cnf["DefaultDynamicPath"] = self.__defaultpath
                        labels = {ar["name"]: lbl}
                        links = {lbl: False}
                        types = {ar["name"]: nxstp}
                        shapes = {ar["name"]: ms}
                    elif i == 13:
                        cnf["DefaultDynamicLinks"] = False
                        cnf["DefaultDynamicPath"] = self.__defaultpath
                        labels = {ar["name"]: lbl}
                        links = {lbl: True}
                        types = {ar["name"]: nxstp}
                        shapes = {ar["name"]: ms}
                    elif i == 14:
                        cnf["DefaultDynamicLinks"] = False
                        cnf["DefaultDynamicPath"] = self.__defaultpath
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
                    print "I = ", i
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

    ## constructor test
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
            '<group name="entry$var.serialno" type="NXentry">\n'
            '<group name="instrument" type="NXinstrument">\n'
            '<group name="collection" type="NXcollection">\n'
            '<field name="%s" type="%s">\n<strategy mode="INIT"/>\n'
            '<datasource name="%s" type="CLIENT">\n'
            '<record name="%s"/>\n</datasource>\n'
            '%s</field>\n'
            '</group>\n</group>\n%s</group>\n</definition>\n',
        }

        link = '<group name="data" type="NXdata">\n' + \
            '<link name="%s" target="/entry$var.serialno:' + \
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
                for tp, nxstp in self.__npTn.items():
                    lbl = self.getRandomName(20)
#                    print "TP = ", tp, i
                    ms = [self.__rnd.randint(0, 3000)
                          for _ in range(self.__rnd.randint(0, 3))]
                    ms2 = [self.__rnd.randint(0, 3000)
                           for _ in range(self.__rnd.randint(0, 3))]
                    tmptp = self.__rnd.choice(self.__npTn.keys())
                    cnf = dict(cnfdef)
                    labels = {}
                    paths = {}
                    links = {}
                    types = {}
                    shapes = {}

                    if i == 0:
                        cnf["DefaultDynamicLinks"] = False
                        cnf["DefaultDynamicPath"] = self.__defaultpath
                        types = {ar["name"]: nxstp}
                        shapes = {ar["name"]: ms}
                    elif i == 1:
                        cnf["DefaultDynamicLinks"] = True
                        cnf["DefaultDynamicPath"] = self.__defaultpath
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
                        cnf["DefaultDynamicPath"] = self.__defaultpath
                        links = {ar["name"]: False}
                        types = {ar["name"]: nxstp}
                        shapes = {ar["name"]: ms}
                    elif i == 5:
                        cnf["DefaultDynamicLinks"] = False
                        cnf["DefaultDynamicPath"] = self.__defaultpath
                        links = {ar["name"]: True}
                        types = {ar["name"]: nxstp}
                        shapes = {ar["name"]: ms}
                    elif i == 6:
                        cnf["DefaultDynamicLinks"] = False
                        cnf["DefaultDynamicPath"] = self.__defaultpath
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
                        cnf["DefaultDynamicPath"] = self.__defaultpath
                        labels = {ar["name"]: lbl}
                        types = {ar["name"]: nxstp}
                        shapes = {ar["name"]: ms}
                    elif i == 9:
                        cnf["DefaultDynamicLinks"] = True
                        cnf["DefaultDynamicPath"] = self.__defaultpath
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
                        cnf["DefaultDynamicPath"] = self.__defaultpath
                        labels = {ar["name"]: lbl}
                        links = {lbl: False}
                        types = {ar["name"]: nxstp}
                        shapes = {ar["name"]: ms}
                    elif i == 13:
                        cnf["DefaultDynamicLinks"] = False
                        cnf["DefaultDynamicPath"] = self.__defaultpath
                        labels = {ar["name"]: lbl}
                        links = {lbl: True}
                        types = {ar["name"]: nxstp}
                        shapes = {ar["name"]: ms}
                    elif i == 14:
                        cnf["DefaultDynamicLinks"] = False
                        cnf["DefaultDynamicPath"] = self.__defaultpath
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
                    print "I = ", i
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

    ## constructor test
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
        groupbg = '<group name="entry$var.serialno" type="NXentry">\n' + \
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
                    cnf["DefaultDynamicPath"] = self.__defaultpath
                elif i == 1:
                    cnf["DefaultDynamicLinks"] = True
                    cnf["DefaultDynamicPath"] = self.__defaultpath
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
                lk = link % (ds.lower(), self.__defaultpath,
                             ds.lower())
                mycps += lk if i % 2 else ""
                mycps += groupend + defend

                self.assertEqual(comp, mycps)

    ## constructor test
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
        groupbg = '<group name="entry$var.serialno" type="NXentry">\n' + \
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
                mycps += link % (ar["name"], self.__defaultpath,
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

    ## constructor test
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
        groupbg = '<group name="entry$var.serialno" type="NXentry">\n' + \
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
                mycps += link % (ar["name"], self.__defaultpath,
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

    ## constructor test
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
        groupbg = '<group name="entry$var.serialno" type="NXentry">\n' + \
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
                    cnf["DefaultDynamicPath"] = self.__defaultpath
                elif i == 1:
                    cnf["DefaultDynamicLinks"] = True
                    cnf["DefaultDynamicPath"] = self.__defaultpath
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
                lk = link % (ds.lower(), self.__defaultpath,
                             ds.lower())
                mycps += lk if i % 2 else ""
                mycps += groupend + defend

                self.assertEqual(comp, mycps)

    ## constructor test
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
        groupbg = '<group name="entry$var.serialno" type="NXentry">\n' + \
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
                    cnf["DefaultDynamicPath"] = self.__defaultpath
                elif i == 1:
                    cnf["DefaultDynamicLinks"] = True
                    cnf["DefaultDynamicPath"] = self.__defaultpath
                elif i == 2:
                    links = {ds: False}
                elif i == 3:
                    links = {ds: True}
                print "I = ", i
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
                rs.profileConfiguration = str(json.dumps(cnf))
                cpname = rs.createDynamicComponent([])
                comp = self._cf.dp.Components([cpname])[0]

                indom = xml.dom.minidom.parseString(dsxml)
                dss = indom.getElementsByTagName("datasource")
                if not ds.startswith("client_") and sds[1] != 'encoded':
                    nxstype = self.__npTn2[tp]
                else:
                    nxstype = 'NX_CHAR'
                mycps = defbg + groupbg + fieldbg % (
                    ds.lower(), nxstype)

                mycps += dss[0].toprettyxml(indent="")
                mstr = ""
                if ms:
                    mstr += dimbg % len(ms)
                    for ind, val in enumerate(ms):
                        mstr += dim % (ind + 1, val)
                    mstr += dimend

                mycps += mstr
                mycps += fieldend + groupend + groupend
                lk = link % (ds.lower(), self.__defaultpath,
                             ds.lower())
                mycps += lk if i % 2 else ""
                mycps += groupend + defend

                self.assertEqual(comp, mycps)

    ## constructor test
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
        groupbg = '<group name="entry$var.serialno" type="NXentry">\n' + \
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
                    cnf["DefaultDynamicPath"] = self.__defaultpath
                elif i == 1:
                    cnf["DefaultDynamicLinks"] = True
                    cnf["DefaultDynamicPath"] = self.__defaultpath
                elif i == 2:
                    links = {ds: False}
                elif i == 3:
                    links = {ds: True}
                print "I = ", i
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
                comp = self._cf.dp.Components([cpname])[0]

                indom = xml.dom.minidom.parseString(dsxml)
                dss = indom.getElementsByTagName("datasource")
                if not ds.startswith("client_") and sds[1] != 'encoded':
                    nxstype = self.__npTn2[tp]
                else:
                    nxstype = 'NX_CHAR'
                mycps = defbg + groupbg + fieldbg % (
                    ds.lower(), nxstype)

                mycps += dss[0].toprettyxml(indent="")
                mstr = ""
                if ms:
                    mstr += dimbg % len(ms)
                    for ind, val in enumerate(ms):
                        mstr += dim % (ind + 1, val)
                    mstr += dimend

                mycps += mstr
                mycps += fieldend + groupend + groupend
                lk = link % (ds.lower(), self.__defaultpath,
                             ds.lower())
                mycps += lk if i % 2 else ""
                mycps += groupend + defend

                self.assertEqual(comp, mycps)

    ## constructor test
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
        groupbg = '<group name="entry$var.serialno" type="NXentry">\n' + \
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
                    cnf["DefaultDynamicPath"] = self.__defaultpath
                elif i == 1:
                    cnf["DefaultDynamicLinks"] = True
                    cnf["DefaultDynamicPath"] = self.__defaultpath
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

#                dc.setInitDSources([ds])
#                cpname = dc.create()
                comp = self._cf.dp.Components([cpname])[0]

                indom = xml.dom.minidom.parseString(dsxml)
                dss = indom.getElementsByTagName("datasource")
                if not ds.startswith("client_") and sds[1] != 'encoded':
                    nxstype = self.__npTn2[tp]
                else:
                    nxstype = 'NX_CHAR'
                mycps = defbg + groupbg + fieldbg % (
                    ds.lower(), nxstype)

                mycps += dss[0].toprettyxml(indent="")
                mstr = ""
                if ms:
                    mstr += dimbg % len(ms)
                    for ind, val in enumerate(ms):
                        mstr += dim % (ind + 1, val)
                    mstr += dimend

                mycps += mstr
                mycps += fieldend + groupend + groupend
                lk = link % (ds.lower(), self.__defaultpath,
                             ds.lower())
                mycps += lk if i % 2 else ""
                mycps += groupend + defend

                self.assertEqual(comp, mycps)

    ## constructor test
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
        groupbg = '<group name="entry$var.serialno" type="NXentry">\n' + \
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
        for i, nxstp in enumerate(self.__npTn.values()):
            for ds, dsxml in self.smydss.items():
                ms = self.smydsspar[ds]
                ms2 = [self.__rnd.randint(0, 3000)
                       for _ in range(self.__rnd.randint(0, 3))]
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
                    cnf["DefaultDynamicPath"] = self.__defaultpath
                    types = {ds: nxstp}
                    shapes = {ds: ms2}
                elif i == 1:
                    cnf["DefaultDynamicLinks"] = True
                    cnf["DefaultDynamicPath"] = self.__defaultpath
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
                    cnf["DefaultDynamicPath"] = self.__defaultpath
                    links = {ds: False}
                    types = {ds: nxstp}
                    shapes = {ds: ms2}
                elif i == 5:
                    cnf["DefaultDynamicLinks"] = False
                    cnf["DefaultDynamicPath"] = self.__defaultpath
                    links = {ds: True}
                    types = {ds: nxstp}
                    shapes = {ds: ms2}
                elif i == 6:
                    cnf["DefaultDynamicLinks"] = False
                    cnf["DefaultDynamicPath"] = self.__defaultpath
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
                    cnf["DefaultDynamicPath"] = self.__defaultpath
                    labels = {ds: lbl}
                    types = {ds: nxstp}
                    shapes = {ds: ms2}
                elif i == 9:
                    cnf["DefaultDynamicLinks"] = True
                    cnf["DefaultDynamicPath"] = self.__defaultpath
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
                    cnf["DefaultDynamicPath"] = self.__defaultpath
                    labels = {ds: lbl}
                    links = {lbl: False}
                    types = {ds: nxstp}
                    shapes = {ds: ms2}
                elif i == 13:
                    cnf["DefaultDynamicLinks"] = False
                    cnf["DefaultDynamicPath"] = self.__defaultpath
                    labels = {ds: lbl}
                    links = {lbl: True}
                    types = {ds: nxstp}
                    shapes = {ds: ms2}
                elif i == 14:
                    cnf["DefaultDynamicLinks"] = False
                    cnf["DefaultDynamicPath"] = self.__defaultpath
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
                print "I = ", i
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
                lk = link % (ds.lower(), self.__defaultpath,
                             ds.lower())
                mycps += lk if i % 2 else ""
                mycps += groupend + defend

                self.assertEqual(comp, mycps)

    ## constructor test
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
        groupbg = '<group name="entry$var.serialno" type="NXentry">\n' + \
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
        for i, nxstp in enumerate(self.__npTn.values()):
            for ds, dsxml in self.smydss.items():
                ms = self.smydsspar[ds]
                ms2 = [self.__rnd.randint(0, 3000)
                       for _ in range(self.__rnd.randint(0, 3))]
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
                    cnf["DefaultDynamicPath"] = self.__defaultpath
                    types = {ds: nxstp}
                    shapes = {ds: ms2}
                elif i == 1:
                    cnf["DefaultDynamicLinks"] = True
                    cnf["DefaultDynamicPath"] = self.__defaultpath
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
                    cnf["DefaultDynamicPath"] = self.__defaultpath
                    links = {ds: False}
                    types = {ds: nxstp}
                    shapes = {ds: ms2}
                elif i == 5:
                    cnf["DefaultDynamicLinks"] = False
                    cnf["DefaultDynamicPath"] = self.__defaultpath
                    links = {ds: True}
                    types = {ds: nxstp}
                    shapes = {ds: ms2}
                elif i == 6:
                    cnf["DefaultDynamicLinks"] = False
                    cnf["DefaultDynamicPath"] = self.__defaultpath
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
                    cnf["DefaultDynamicPath"] = self.__defaultpath
                    labels = {ds: lbl}
                    types = {ds: nxstp}
                    shapes = {ds: ms2}
                elif i == 9:
                    cnf["DefaultDynamicLinks"] = True
                    cnf["DefaultDynamicPath"] = self.__defaultpath
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
                    cnf["DefaultDynamicPath"] = self.__defaultpath
                    labels = {ds: lbl}
                    links = {lbl: False}
                    types = {ds: nxstp}
                    shapes = {ds: ms2}
                elif i == 13:
                    cnf["DefaultDynamicLinks"] = False
                    cnf["DefaultDynamicPath"] = self.__defaultpath
                    labels = {ds: lbl}
                    links = {lbl: True}
                    types = {ds: nxstp}
                    shapes = {ds: ms2}
                elif i == 14:
                    cnf["DefaultDynamicLinks"] = False
                    cnf["DefaultDynamicPath"] = self.__defaultpath
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
                print "I = ", i
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
                lk = link % (ds.lower(), self.__defaultpath,
                             ds.lower())
                mycps += lk if i % 2 else ""
                mycps += groupend + defend

                self.assertEqual(comp, mycps)

    ## constructor test
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
        groupbg = '<group name="entry$var.serialno" type="NXentry">\n' + \
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
        for i, nxstp in enumerate(self.__npTn.values()):
            for ds, dsxml in self.smydss.items():
                ms = self.smydsspar[ds]
                ms2 = [self.__rnd.randint(0, 3000)
                       for _ in range(self.__rnd.randint(0, 3))]
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
                    cnf["DefaultDynamicPath"] = self.__defaultpath
                    types = {ds: nxstp}
                    shapes = {ds: ms2}
                elif i == 1:
                    cnf["DefaultDynamicLinks"] = True
                    cnf["DefaultDynamicPath"] = self.__defaultpath
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
                    cnf["DefaultDynamicPath"] = self.__defaultpath
                    links = {ds: False}
                    types = {ds: nxstp}
                    shapes = {ds: ms2}
                elif i == 5:
                    cnf["DefaultDynamicLinks"] = False
                    cnf["DefaultDynamicPath"] = self.__defaultpath
                    links = {ds: True}
                    types = {ds: nxstp}
                    shapes = {ds: ms2}
                elif i == 6:
                    cnf["DefaultDynamicLinks"] = False
                    cnf["DefaultDynamicPath"] = self.__defaultpath
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
                    cnf["DefaultDynamicPath"] = self.__defaultpath
                    labels = {ds: lbl}
                    types = {ds: nxstp}
                    shapes = {ds: ms2}
                elif i == 9:
                    cnf["DefaultDynamicLinks"] = True
                    cnf["DefaultDynamicPath"] = self.__defaultpath
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
                    cnf["DefaultDynamicPath"] = self.__defaultpath
                    labels = {ds: lbl}
                    links = {lbl: False}
                    types = {ds: nxstp}
                    shapes = {ds: ms2}
                elif i == 13:
                    cnf["DefaultDynamicLinks"] = False
                    cnf["DefaultDynamicPath"] = self.__defaultpath
                    labels = {ds: lbl}
                    links = {lbl: True}
                    types = {ds: nxstp}
                    shapes = {ds: ms2}
                elif i == 14:
                    cnf["DefaultDynamicLinks"] = False
                    cnf["DefaultDynamicPath"] = self.__defaultpath
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
                print "I = ", i
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
                lk = link % (ds.lower(), self.__defaultpath,
                             ds.lower())
                mycps += lk if i % 2 else ""
                mycps += groupend + defend

                self.assertEqual(comp, mycps)

    ## constructor test
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
        groupbg = '<group name="entry$var.serialno" type="NXentry">\n' + \
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
        for i, nxstp in enumerate(self.__npTn.values()):
            for ds, dsxml in self.smydss.items():
                ms = self.smydsspar[ds]
                ms2 = [self.__rnd.randint(0, 3000)
                       for _ in range(self.__rnd.randint(0, 3))]
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
                    cnf["DefaultDynamicPath"] = self.__defaultpath
                    types = {ds: nxstp}
                    shapes = {ds: ms2}
                elif i == 1:
                    cnf["DefaultDynamicLinks"] = True
                    cnf["DefaultDynamicPath"] = self.__defaultpath
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
                    cnf["DefaultDynamicPath"] = self.__defaultpath
                    types = {ds: nxstp}
                    shapes = {ds: ms2}
                elif i == 5:
                    cnf["DefaultDynamicLinks"] = False
                    cnf["DefaultDynamicPath"] = self.__defaultpath
                    links = {ds: True}
                    types = {ds: nxstp}
                    shapes = {ds: ms2}
                elif i == 6:
                    cnf["DefaultDynamicPath"] = self.__defaultpath
                    links = {"dssd": True}
                    types = {ds: nxstp}
                    shapes = {ds: ms2}
                elif i == 7:
                    labels = {ds: lbl}
                    types = {ds: nxstp}
                    shapes = {ds: ms2}
                elif i == 8:
                    pass
                    cnf["DefaultDynamicPath"] = self.__defaultpath
                    labels = {ds: lbl}
                    types = {ds: nxstp}
                    shapes = {ds: ms2}
                elif i == 9:
                    cnf["DefaultDynamicLinks"] = True
                    cnf["DefaultDynamicPath"] = self.__defaultpath
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
                    cnf["DefaultDynamicPath"] = self.__defaultpath
                    labels = {ds: lbl}
                    types = {ds: nxstp}
                    shapes = {ds: ms2}
                elif i == 13:
                    cnf["DefaultDynamicLinks"] = False
                    cnf["DefaultDynamicPath"] = self.__defaultpath
                    labels = {ds: lbl}
                    links = {lbl: True}
                    types = {ds: nxstp}
                    shapes = {ds: ms2}
                elif i == 14:
                    cnf["DefaultDynamicPath"] = self.__defaultpath
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
                print "I = ", i
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
                lk = link % (ds.lower(), self.__defaultpath,
                             ds.lower())
                mycps += lk if i % 2 else ""
                mycps += groupend + defend

                self.assertEqual(comp, mycps)

    ## constructor test
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
            '<group name="entry$var.serialno" type="NXentry">\n'
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
                print "I = ", i
                for ds, dsxml in self.smydss.items():
                    ms = self.smydsspar[ds]
                    sds = ds.split("_")
                    tp = sds[1]
                    indom = xml.dom.minidom.parseString(dsxml)
                    dss = indom.getElementsByTagName("datasource")
                    if not ds.startswith("client_") and sds[1] != 'encoded':
                        nxstp = self.__npTn2[tp]
                    else:
                        nxstp = 'NX_CHAR'
#                    dc = DynamicComponent(self._cf.dp)

                    lbl = self.getRandomName(20)
                    fieldname = self.getRandomName(20)
#                    print "FIELD", fieldname
                    path = [
                        (self.getRandomName(20)
                         if self.__rnd.randint(0, 1) else None,
                         ("NX" + self.getRandomName(20))
                         if self.__rnd.randint(0, 1) else None)
                        for _ in range(self.__rnd.randint(0, 10))]
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
                    tmptp = self.__rnd.choice(self.__npTn.keys())
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
                    print "I = ", i
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
                                         self.__defaultpath, ds.lower())
                        else:
                            lk = link % (fieldname.lower(), self.__defaultpath,
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

    ## constructor test
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
            '<group name="entry$var.serialno" type="NXentry">\n'
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
                print "I = ", i
                for ds, dsxml in self.smydss.items():
                    ms = self.smydsspar[ds]
                    sds = ds.split("_")
                    tp = sds[1]
                    indom = xml.dom.minidom.parseString(dsxml)
                    dss = indom.getElementsByTagName("datasource")
                    if not ds.startswith("client_") and sds[1] != 'encoded':
                        nxstp = self.__npTn2[tp]
                    else:
                        nxstp = 'NX_CHAR'
#                    dc = DynamicComponent(self._cf.dp)

                    lbl = self.getRandomName(20)
                    fieldname = self.getRandomName(20)
#                    print "FIELD", fieldname
                    path = [
                        (self.getRandomName(20)
                         if self.__rnd.randint(0, 1) else None,
                         ("NX" + self.getRandomName(20))
                         if self.__rnd.randint(0, 1) else None)
                        for _ in range(self.__rnd.randint(0, 10))]
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
                    tmptp = self.__rnd.choice(self.__npTn.keys())
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

                    print "I = ", i
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
                                         self.__defaultpath, ds.lower())
                        else:
                            lk = link % (fieldname.lower(), self.__defaultpath,
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

    ## constructor test
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
            '<group name="entry$var.serialno" type="NXentry">\n'
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
                print "I = ", i
                for ds, dsxml in self.smydss.items():
                    ms = self.smydsspar[ds]
                    sds = ds.split("_")
                    tp = sds[1]
                    indom = xml.dom.minidom.parseString(dsxml)
                    dss = indom.getElementsByTagName("datasource")
                    if not ds.startswith("client_") and sds[1] != 'encoded':
                        nxstp = self.__npTn2[tp]
                    else:
                        nxstp = 'NX_CHAR'

                    lbl = self.getRandomName(20)
                    fieldname = self.getRandomName(20)
#                    print "FIELD", fieldname
                    path = [
                        (self.getRandomName(20)
                         if self.__rnd.randint(0, 1) else None,
                         ("NX" + self.getRandomName(20))
                         if self.__rnd.randint(0, 1) else None)
                        for _ in range(self.__rnd.randint(0, 10))]
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
                    tmptp = self.__rnd.choice(self.__npTn.keys())
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
                    print "I = ", i
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
                                         self.__defaultpath, ds.lower())
                        else:
                            lk = link % (fieldname.lower(), self.__defaultpath,
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

    ## constructor test
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
            '<group name="entry$var.serialno" type="NXentry">\n'
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
                print "I = ", i
                for ds, dsxml in self.smydss.items():
                    ms = self.smydsspar[ds]
                    sds = ds.split("_")
                    tp = sds[1]
                    indom = xml.dom.minidom.parseString(dsxml)
                    dss = indom.getElementsByTagName("datasource")
                    if not ds.startswith("client_") and sds[1] != 'encoded':
                        nxstp = self.__npTn2[tp]
                    else:
                        nxstp = 'NX_CHAR'

                    lbl = self.getRandomName(20)
                    fieldname = self.getRandomName(20)
#                    print "FIELD", fieldname
                    path = [
                        (self.getRandomName(20)
                         if self.__rnd.randint(0, 1) else None,
                         ("NX" + self.getRandomName(20))
                         if self.__rnd.randint(0, 1) else None)
                        for _ in range(self.__rnd.randint(0, 10))]
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
                    tmptp = self.__rnd.choice(self.__npTn.keys())
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
                    print "I = ", i
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
                                         self.__defaultpath, ds.lower())
                        else:
                            lk = link % (fieldname.lower(), self.__defaultpath,
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

    ## test
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

    ## test
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

    ## test
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
            mncps = self.__rnd.randint(0, len(mycps.keys()))
            mcps = [
                cp for cp in self.__rnd.sample(set(mycps.keys()), mncps)
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

    ## test
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
        sets = ["PreselectedDataSources"]
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
                self._cf.dp.xmlstring = res2
                res = rs.createWriterConfiguration([])
                cmds = json.loads(self._cf.dp.GetCommandVariable("COMMANDS"))
                vrs = json.loads(self._cf.dp.GetCommandVariable("VARS"))
                self.assertEqual(cmds[-1], "CreateConfiguration")
                self.assertEqual(set(vrs[-1]), set(components))
                self.assertEqual(res, res2)
        finally:
            simp2.tearDown()

    ## test
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
        sets = ["PreselectedDataSources"]
        try:
            simp2.setUp()

            for i in range(8):

                rs = self.openRecSelector()
                rs.configDevice = val["ConfigDevice"]
                rs.door = val["Door"]
                rs.mntGrp = mg

                mncps = self.__rnd.randint(0, len(self.smycps.keys()))
                components = [
                    cp for cp in self.__rnd.sample(
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
                self._cf.dp.xmlstring = res2
                res = rs.createWriterConfiguration([])
                cmds = self._cf.dp.GetCommandVariable("COMMANDS")
                print cmds
                print res
                self._cf.dp.xmlstring = res2
                res3 = self._cf.dp.createConfiguration(components)
                cmds = json.loads(self._cf.dp.GetCommandVariable("COMMANDS"))
                vrs = json.loads(self._cf.dp.GetCommandVariable("VARS"))
                self.assertEqual(cmds[-1], "CreateConfiguration")
                self.assertEqual(set(vrs[-1]), set(components))
                self.assertEqual(res, res2)
        finally:
            simp2.tearDown()

    ## test
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
            lcp = self.__rnd.randint(1, 40)
            for _ in range(lcp):
                vrname = self.getRandomName(10)
                if vrname != 'serialno':
                    rscv[vrname] = self.getRandomName(
                        self.__rnd.randint(1, 40))
            rs.configVariables = str(json.dumps(rscv))

            cscv = {}
            lcp = self.__rnd.randint(1, 40)
            for _ in range(lcp):
                vrname = self.getRandomName(10)
                if vrname != 'serialno':
                    cscv[vrname] = self.getRandomName(
                        self.__rnd.randint(1, 40))
            self._cf.dp.variables = str(json.dumps(cscv))

            rs.updateConfigVariables()

            res = self._cf.dp.variables
            if i % 2:
                rscv["serialno"] = "1"
            self.myAssertDict(json.loads(res), rscv)

    ## test
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
            lcp = self.__rnd.randint(1, 40)
            for _ in range(lcp):
                vrname = self.getRandomName(10)
                if vrname != 'serialno':
                    rscv[vrname] = self.getRandomName(
                        self.__rnd.randint(1, 40))
            slno = str(self.__rnd.randint(1, 40))
            rscv["serialno"] = str(slno)
            rs.configVariables = str(json.dumps(rscv))

            cscv = {}
            lcp = self.__rnd.randint(1, 40)
            for _ in range(lcp):
                vrname = self.getRandomName(10)
                if vrname != 'serialno':
                    cscv[vrname] = self.getRandomName(
                        self.__rnd.randint(1, 40))
            self._cf.dp.variables = str(json.dumps(cscv))

            rs.updateConfigVariables()

            res = self._cf.dp.variables
            self.myAssertDict(json.loads(res), rscv)

    ## test
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
            lcp = self.__rnd.randint(1, 40)
            for _ in range(lcp):
                vrname = self.getRandomName(10)
                if vrname != 'serialno':
                    rscv[vrname] = self.getRandomName(
                        self.__rnd.randint(1, 40))
            rs.configVariables = str(json.dumps(rscv))

            cscv = {}
            lcp = self.__rnd.randint(1, 40)
            for _ in range(lcp):
                vrname = self.getRandomName(10)
                if vrname != 'serialno':
                    cscv[vrname] = self.getRandomName(
                        self.__rnd.randint(1, 40))
            slno = self.__rnd.randint(1, 40)
            cscv["serialno"] = str(slno)
            self._cf.dp.variables = str(json.dumps(cscv))

            rs.updateConfigVariables()

            res = self._cf.dp.variables
            if i % 2:
                rscv["serialno"] = str(slno + 1)
            self.myAssertDict(json.loads(res), rscv)

    ## test
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
            lcp = self.__rnd.randint(1, 40)
            for _ in range(lcp):
                vrname = self.getRandomName(10)
                if vrname != 'serialno':
                    rscv[vrname] = self.getRandomName(
                        self.__rnd.randint(1, 40))
            slno = self.__rnd.randint(1, 40)
            rscv["serialno"] = str(slno)
            rs.configVariables = str(json.dumps(rscv))

            cscv = {}
            lcp = self.__rnd.randint(1, 40)
            for _ in range(lcp):
                vrname = self.getRandomName(10)
                if vrname != 'serialno':
                    cscv[vrname] = self.getRandomName(
                        self.__rnd.randint(1, 40))
            slno2 = self.__rnd.randint(1, 40)
            cscv["serialno"] = str(slno2)
            self._cf.dp.variables = str(json.dumps(cscv))

            rs.updateConfigVariables()

            res = self._cf.dp.variables
            self.myAssertDict(json.loads(res), rscv)


if __name__ == '__main__':
    unittest.main()
