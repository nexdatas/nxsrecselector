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
            ("DynamicPath", self.__defaultpath),
            ("TimeZone", self.__defaultzone),
            ("ConfigDevice", ''),
            ("WriterDevice", ''),
            ("Door", ''),
            ("MntGrp", '')
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
                res.append(ds)
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

    def getRandomName(self, maxsize):
        letters = string.lowercase + string.uppercase + string.digits
        size = self.__rnd.randint(1, maxsize)
        return ''.join(self.__rnd.choice(letters) for _ in range(size))

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

    def openRecSelector(self):
        return Settings()

    def subtest_constructor(self):
        # properties

        db = PyTango.Database()
        msp = MacroServerPools(10)

        icf = TangoUtils.getDeviceName(db, "NXSConfigServer")
        idoor = TangoUtils.getDeviceName(db, "Door")
        msp.getPools(idoor)

        rs = self.openRecSelector()

        se = Selector(msp)
        pm = ProfileManager(se)
        print "AMGs", pm.availableMntGrps()
        amntgrp = MSUtils.getEnv('ActiveMntGrp', msp.getMacroServer(idoor))
        print "ActiveMntGrp", amntgrp
        self.assertEqual(rs.numberOfThreads, 20)
        self.assertEqual(rs.timerFilterList, ["*dgg*", "*/ctctrl0*"])
        # memorize attirbutes
        self.assertEqual(
            rs.deviceGroups,
            '{"timer": ["*exp_t*"], "dac": ["*exp_dac*"], '
            '"counter": ["*exp_c*"], "mca": ["*exp_mca*"], '
            '"adc": ["*exp_adc*"], "motor": ["*exp_mot*"]}')
        self.assertEqual(rs.adminData, '[]')
        self.assertEqual(rs.configFile, '/tmp/nxsrecconfig.cfg')
        self.assertEqual(rs.configDevice, icf)
        self.assertEqual(rs.door, idoor)
        cf = PyTango.DeviceProxy(rs.configDevice)
        self.assertEqual(
            cf.availableSelections(),
            rs.availableSelections())
        print "AMGs", pm.availableMntGrps()
        print "AvSels", cf.availableSelections()
        if amntgrp in pm.availableMntGrps():
            self.assertEqual(rs.mntGrp, amntgrp)
        elif cf.availableSelections():
            self.assertEqual(rs.mntGrp, cf.availableSelections()[0])
        else:
            self.assertEqual('nxsmntgrp', amntgrp)
        self.assertEqual(set(self.names(rs)),
                         set([k[0] for k in self._keys]))

        for nm in self.names(rs):
            if nm not in ["Timer",
                          "DataSourceGroup",
                          "AutomaticDataSources"]:
                if self.value(rs, nm) != se[nm]:
                    print ("DICT NAME %s" % nm)
                self.assertEqual(self.value(rs, nm), se[nm])
        self.assertEqual(self.value(rs, "UNKNOWN_VARIABLE_34535"), '')

        print "MntGrp", rs.mntGrp
        # memorize attirbutes
        print "ConfigDevice", rs.configDevice
        print "Door", rs.door
        print "DeviceGroups", rs.deviceGroups
        print "AdminData", rs.adminData

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
            self.assertEqual(set(rs.availableSelections()), set())
        except:
            self.assertEqual(set(rs.availableSelections()),
                             set([val["MntGrp"]]))

        self._cf.dp.SetCommandVariable(["SELDICT",
                                        json.dumps(self.mysel2)])

        self.assertEqual(set(rs.availableSelections()),
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

        self.assertEqual(rs.poolChannels(), [])

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

        dd = rs.poolChannels()
        self.assertEqual(dd, [a["name"] for a in arr])

        pool.ExpChannelList = [
            json.dumps(
                {"name": a[0], "controller": a[1]}) for a in arr2]

        dd = rs.poolChannels()
        res = [a[0] for a in arr2]
        self.assertEqual(dd, res)

        print rs.poolChannels()

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

        self.assertEqual(rs.poolMotors(), [])

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

        dd = rs.poolMotors()
        self.assertEqual(dd, [a["name"] for a in arr])

        pool.MotorList = [
            json.dumps(
                {"name": a[0], "controller": a[1]}) for a in arr2]

        dd = rs.poolMotors()
        res = [a[0] for a in arr2]
        self.assertEqual(dd, res)

        print rs.poolMotors()

    ## test
    # \brief It tests default settings
    def test_findMntGrp_empty(self):
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

        self.assertEqual(rs.findMntGrp("blemble"), '')
        self.assertEqual(rs.findMntGrp("blembl2e"), '')

    ## test
    # \brief It tests default settings
    def test_findMntGrp_pool1(self):
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

        self.assertEqual(rs.findMntGrp("somethin"), '')

        arr = [
            ["test/ct/01", "mntgrp_01Value"],
            ["test/ct/02", "mntgrp_02att"],
            ["test/ct/03", "mntgrp_03value"],
            ["test/ct/04", "mntgrp_0413"],
            ["null", "mntgrp_04"],
        ]

        pool = self._pool.dp

        pool.MeasurementGroupList = [json.dumps(
            {"name": a[0], "full_name": a[1]}) for a in arr]

        for ar in arr:
            dd = rs.findMntGrp(ar[0])
            self.assertEqual(dd, ar[1])

        dd = rs.findMntGrp("adsasd")
        self.assertEqual(dd, '')

    ## test
    # \brief It tests default settings
    def test_findMntGrp_pool2(self):
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

            self.assertEqual(rs.findMntGrp("somethin"), '')

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

            pool.MeasurementGroupList = [json.dumps(
                {"name": a[0], "full_name": a[1]}) for a in arr]
            pool2.MeasurementGroupList = [json.dumps(
                {"name": a[0], "full_name": a[1]}) for a in arr2]

            for ar in arr:
                dd = rs.findMntGrp(ar[0])
                self.assertEqual(dd, ar[1])

            for ar in arr2:
                dd = rs.findMntGrp(ar[0])
                self.assertEqual(dd, ar[1])

            dd = rs.findMntGrp("adsasd")
            self.assertEqual(dd, '')
        finally:
            tpool2.tearDown()

    ## updateControllers test
    # \brief It tests default settings
    def test_updateControllers_simple(self):
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
        rs.updateControllers()
        res = self.value(rs, "AutomaticComponentGroup")
        self.assertEqual(res, '{}')
        print self._cf.dp.GetCommandVariable("COMMANDS")

    ## updateControllers test
    # \brief It tests default settings
    def test_updateControllers_withcf(self):
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

        rs.updateControllers()
        res = self.value(rs, "AutomaticComponentGroup")

        self.assertEqual(res, '{}')
        self.assertEqual(componentgroup, {})
        self.assertEqual(channelerrors, [])
        print self._cf.dp.GetCommandVariable("COMMANDS")

    ## test
    # \brief It tests default settings
    def test_updateControllers_withcf_cps(self):
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

        cnf = json.loads(rs.configuration)
        cnf["AutomaticDataSources"] = json.dumps(poolchannels)
        cnf["AutomaticComponentGroup"] = json.dumps(componentgroup)
        rs.configuration = json.dumps(cnf)
        rs.updateControllers()
        res = self.value(rs, "AutomaticComponentGroup")
        self.myAssertDict(json.loads(res), {"mycp": True})
        self.assertEqual(channelerrors, [])

        self.assertTrue(val["MntGrp"] in self._cf.dp.availableSelections())
        sed = json.loads(self._cf.dp.selections([val["MntGrp"]])[0])
        self.assertEqual(len(sed.keys()), len(self._keys))
        for key, vl in self._keys:
            self.assertTrue(key in sed.keys())
            if key in val:
                self.assertEqual(sed[key], val[key])
            elif key == 'AutomaticComponentGroup':
                self.assertEqual(set(json.loads(sed[key])),
                                 set(json.loads(res)))
            elif key == 'AutomaticDataSources':
                self.assertEqual(set(json.loads(sed[key])), set(poolchannels))
            else:
                self.assertEqual(sed[key], vl)

    ## test
    # \brief It tests default settings
    def test_updateControllers_withcf_cps_t(self):
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

        cnf = json.loads(rs.configuration)
        cnf["AutomaticDataSources"] = json.dumps(poolchannels)
        cnf["AutomaticComponentGroup"] = json.dumps(componentgroup)
        rs.configuration = json.dumps(cnf)
        rs.updateControllers()
        res = self.value(rs, "AutomaticComponentGroup")
        self.myAssertDict(json.loads(res), {"mycp": True})
        self.assertEqual(channelerrors, [])

        self.assertTrue(val["MntGrp"] in self._cf.dp.availableSelections())

    ## test
    # \brief It tests default settings
    def test_updateControllers_withcf_nocps(self):
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

        cnf = json.loads(rs.configuration)
        cnf["AutomaticDataSources"] = json.dumps(poolchannels)
        cnf["AutomaticComponentGroup"] = json.dumps(componentgroup)
        rs.configuration = json.dumps(cnf)
        rs.updateControllers()
        res = self.value(rs, "AutomaticComponentGroup")

        self.myAssertDict(json.loads(res), {})
        self.assertEqual(channelerrors, [])

        print self._cf.dp.GetCommandVariable("COMMANDS")

        self.assertTrue(val["MntGrp"] in self._cf.dp.availableSelections())

    ## test
    # \brief It tests default settings
    def test_updateControllers_withcf_nochnnel(self):
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

        cnf = json.loads(rs.configuration)
        cnf["AutomaticDataSources"] = json.dumps(poolchannels)
        cnf["AutomaticComponentGroup"] = json.dumps(componentgroup)
        rs.configuration = json.dumps(cnf)
        rs.updateControllers()
        res = self.value(rs, "AutomaticComponentGroup")

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
            elif key == 'AutomaticComponentGroup':
                self.assertEqual(set(json.loads(sed[key])),
                                 set(json.loads(res)))
            elif key == 'AutomaticDataSources':
                self.assertEqual(set(json.loads(sed[key])), set(poolchannels))
            else:
                self.assertEqual(sed[key], vl)

    ## test
    # \brief It tests default settings
    def test_updateControllers_withcf_nochnnel_t(self):
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

        cnf = json.loads(rs.configuration)
        cnf["AutomaticDataSources"] = json.dumps(poolchannels)
        cnf["AutomaticComponentGroup"] = json.dumps(componentgroup)
        rs.configuration = json.dumps(cnf)
        rs.updateControllers()
        res = self.value(rs, "AutomaticComponentGroup")

        self.myAssertDict(json.loads(res), {"mycp": True})
        self.assertEqual(channelerrors, [])

        self.assertTrue(val["MntGrp"] in self._cf.dp.availableSelections())

    ## test
    # \brief It tests default settings
    def test_updateControllers_wds_t(self):
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

        cnf = json.loads(rs.configuration)
        cnf["AutomaticDataSources"] = json.dumps(poolchannels)
        cnf["AutomaticComponentGroup"] = json.dumps(componentgroup)
        rs.configuration = json.dumps(cnf)
        rs.updateControllers()
        res = self.value(rs, "AutomaticComponentGroup")

        self.myAssertDict(json.loads(res), {"smycp": True})
        self.assertEqual(channelerrors, [])

        self.assertTrue(val["MntGrp"] in self._cf.dp.availableSelections())

    ## test
    # \brief It tests default settings
    def test_updateControllers_wds(self):
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

        cnf = json.loads(rs.configuration)
        cnf["AutomaticDataSources"] = json.dumps(poolchannels)
        cnf["AutomaticComponentGroup"] = json.dumps(componentgroup)
        rs.configuration = json.dumps(cnf)
        rs.updateControllers()
        res = self.value(rs, "AutomaticComponentGroup")

        self.myAssertDict(json.loads(res), {"smycp": True})
        self.assertEqual(channelerrors, [])

        self.assertTrue(val["MntGrp"] in self._cf.dp.availableSelections())
        sed = json.loads(self._cf.dp.selections([val["MntGrp"]])[0])
        self.assertEqual(len(sed.keys()), len(self._keys))
        for key, vl in self._keys:
            self.assertTrue(key in sed.keys())
            if key in val:
                self.assertEqual(sed[key], val[key])
            elif key == 'AutomaticComponentGroup':
                self.assertEqual(set(json.loads(sed[key])),
                                 set(json.loads(res)))
            elif key == 'AutomaticDataSources':
                self.assertEqual(set(json.loads(sed[key])),
                                 set(poolchannels))
            else:
                self.assertEqual(sed[key], vl)

    ## test
    # \brief It tests default settings
    def test_updateControllers_wds2(self):
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

        cnf = json.loads(rs.configuration)
        cnf["AutomaticDataSources"] = json.dumps(poolchannels)
        cnf["AutomaticComponentGroup"] = json.dumps(componentgroup)
        rs.configuration = json.dumps(cnf)
        rs.updateControllers()
        res = self.value(rs, "AutomaticComponentGroup")

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
            elif key == 'AutomaticComponentGroup':
                self.assertEqual(set(json.loads(sed[key])),
                                 set(json.loads(res)))
            elif key == 'AutomaticDataSources':
                self.assertEqual(set(json.loads(sed[key])),
                                 set(poolchannels))
            else:
                self.assertEqual(sed[key], vl)

    ## test
    # \brief It tests default settings
    def test_updateControllers_2wds(self):
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

            cnf = json.loads(rs.configuration)
            cnf["AutomaticDataSources"] = json.dumps(poolchannels)
            cnf["AutomaticComponentGroup"] = json.dumps(componentgroup)
            rs.configuration = json.dumps(cnf)
            rs.updateControllers()
            res = self.value(rs, "AutomaticComponentGroup")

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
                elif key == 'AutomaticComponentGroup':
                    self.assertEqual(set(json.loads(sed[key])),
                                     set(json.loads(res)))
                elif key == 'AutomaticDataSources':
                    self.assertEqual(set(json.loads(sed[key])),
                                     set(poolchannels))
                else:
                    self.assertEqual(sed[key], vl)
        finally:
            simps2.tearDown()

    ## test
    # \brief It tests default settings
    def test_updateControllers_2wds_dvnorunning(self):
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

            cnf = json.loads(rs.configuration)
            cnf["AutomaticDataSources"] = json.dumps(poolchannels)
            cnf["AutomaticComponentGroup"] = json.dumps(componentgroup)
            rs.configuration = json.dumps(cnf)
            rs.updateControllers()
            res = self.value(rs, "AutomaticComponentGroup")

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
                elif key == 'AutomaticComponentGroup':
                    self.assertEqual(set(json.loads(sed[key])),
                                     set(json.loads(res)))
                elif key == 'AutomaticDataSources':
                    self.assertEqual(set(json.loads(sed[key])),
                                     set(poolchannels))
                else:
                    self.assertEqual(sed[key], vl)
        finally:
            simps2.delete()

    ## test
    # \brief It tests default settings
    def test_updateControllers_2wds_dvnodef(self):
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

        cnf = json.loads(rs.configuration)
        cnf["AutomaticDataSources"] = json.dumps(poolchannels)
        cnf["AutomaticComponentGroup"] = json.dumps(componentgroup)
        rs.configuration = json.dumps(cnf)
        rs.updateControllers()
        res = self.value(rs, "AutomaticComponentGroup")

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
            elif key == 'AutomaticComponentGroup':
                self.assertEqual(set(json.loads(sed[key])),
                                 set(json.loads(res)))
            elif key == 'AutomaticDataSources':
                self.assertEqual(set(json.loads(sed[key])),
                                 set(poolchannels))
            else:
                self.assertEqual(sed[key], vl)

    ## test
    # \brief It tests default settings
    def test_updateControllers_2wds_nods(self):
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

            cnf = json.loads(rs.configuration)
            cnf["AutomaticDataSources"] = json.dumps(poolchannels)
            cnf["AutomaticComponentGroup"] = json.dumps(componentgroup)
            rs.configuration = json.dumps(cnf)
            rs.updateControllers()
            res = self.value(rs, "AutomaticComponentGroup")

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
                elif key == 'AutomaticComponentGroup':
                    self.assertEqual(set(json.loads(sed[key])),
                                     set(json.loads(res)))
                elif key == 'AutomaticDataSources':
                    self.assertEqual(set(json.loads(sed[key])),
                                     set(poolchannels))
                else:
                    self.assertEqual(sed[key], vl)
        finally:
            simps2.tearDown()

    ## test
    # \brief It tests default settings
    def test_updateControllers_2wds_nodspool(self):
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

            cnf = json.loads(rs.configuration)
            cnf["AutomaticDataSources"] = json.dumps(poolchannels)
            cnf["AutomaticComponentGroup"] = json.dumps(componentgroup)
            rs.configuration = json.dumps(cnf)
            rs.updateControllers()
            res = self.value(rs, "AutomaticComponentGroup")

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
                elif key == 'AutomaticComponentGroup':
                    self.assertEqual(set(json.loads(sed[key])),
                                     set(json.loads(res)))
                elif key == 'AutomaticDataSources':
                    self.assertEqual(set(json.loads(sed[key])),
                                     set(poolchannels))
                else:
                    self.assertEqual(sed[key], vl)
        finally:
            simps2.tearDown()

    ## test
    # \brief It tests default settings
    def test_updateControllers_2wds_notangods(self):
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

            cnf = json.loads(rs.configuration)
            cnf["AutomaticDataSources"] = json.dumps(poolchannels)
            cnf["AutomaticComponentGroup"] = json.dumps(componentgroup)
            rs.configuration = json.dumps(cnf)
            rs.updateControllers()
            res = self.value(rs, "AutomaticComponentGroup")

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
                elif key == 'AutomaticComponentGroup':
                    self.assertEqual(set(json.loads(sed[key])),
                                     set(json.loads(res)))
                elif key == 'AutomaticDataSources':
                    self.assertEqual(set(json.loads(sed[key])),
                                     set(poolchannels))
                else:
                    self.assertEqual(sed[key], vl)
        finally:
            simps2.tearDown()

    ## test
    # \brief It tests default settings
    def test_updateControllers_2wds_notangodsnopool(self):
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

            cnf = json.loads(rs.configuration)
            cnf["AutomaticDataSources"] = json.dumps(poolchannels)
            cnf["AutomaticComponentGroup"] = json.dumps(componentgroup)
            rs.configuration = json.dumps(cnf)
            rs.updateControllers()
            res = self.value(rs, "AutomaticComponentGroup")

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
                elif key == 'AutomaticComponentGroup':
                    self.assertEqual(set(json.loads(sed[key])),
                                     set(json.loads(res)))
                elif key == 'AutomaticDataSources':
                    self.assertEqual(set(json.loads(sed[key])),
                                     set(poolchannels))
                else:
                    self.assertEqual(sed[key], vl)
        finally:
            simps2.tearDown()

    ## test
    # \brief It tests default settings
    def test_updateControllers_2wds_notangodsnopool2(self):
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

            cnf = json.loads(rs.configuration)
            cnf["AutomaticDataSources"] = json.dumps(poolchannels)
            cnf["AutomaticComponentGroup"] = json.dumps(componentgroup)
            rs.configuration = json.dumps(cnf)
            rs.updateControllers()
            res = self.value(rs, "AutomaticComponentGroup")

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
                elif key == 'AutomaticComponentGroup':
                    self.assertEqual(set(json.loads(sed[key])),
                                     set(json.loads(res)))
                elif key == 'AutomaticDataSources':
                    self.assertEqual(set(json.loads(sed[key])),
                                     set(poolchannels))
                else:
                    self.assertEqual(sed[key], vl)
        finally:
            simps2.tearDown()

    ## test
    # \brief It tests default settings
    def test_updateControllers_2wds_notangods2(self):
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

            cnf = json.loads(rs.configuration)
            cnf["AutomaticDataSources"] = json.dumps(poolchannels)
            cnf["AutomaticComponentGroup"] = json.dumps(componentgroup)
            rs.configuration = json.dumps(cnf)
            rs.updateControllers()
            res = self.value(rs, "AutomaticComponentGroup")

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
                elif key == 'AutomaticComponentGroup':
                    self.assertEqual(set(json.loads(sed[key])),
                                     set(json.loads(res)))
                elif key == 'AutomaticDataSources':
                    self.assertEqual(set(json.loads(sed[key])),
                                     set(poolchannels))
                else:
                    self.assertEqual(sed[key], vl)
        finally:
            simps2.tearDown()

    ## test
    # \brief It tests default settings
    def test_updateControllers_2wds_notangodspool_error(self):
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

            cnf = json.loads(rs.configuration)
            cnf["AutomaticDataSources"] = json.dumps(poolchannels)
            cnf["AutomaticComponentGroup"] = json.dumps(componentgroup)
            rs.configuration = json.dumps(cnf)
            rs.updateControllers()
            res = self.value(rs, "AutomaticComponentGroup")

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
                elif key == 'AutomaticComponentGroup':
                    self.assertEqual(set(json.loads(sed[key])),
                                     set(json.loads(res)))
                elif key == 'AutomaticDataSources':
                    self.assertEqual(set(json.loads(sed[key])),
                                     set(poolchannels))
                else:
                    self.assertEqual(sed[key], vl)
        finally:
            simps2.tearDown()

    ## test
    # \brief It tests default settings
    def test_updateControllers_2wds_notangodspool(self):
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

            cnf = json.loads(rs.configuration)
            cnf["AutomaticDataSources"] = json.dumps(poolchannels)
            cnf["AutomaticComponentGroup"] = json.dumps(componentgroup)
            rs.configuration = json.dumps(cnf)
            rs.updateControllers()
            res = self.value(rs, "AutomaticComponentGroup")

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
                elif key == 'AutomaticComponentGroup':
                    self.assertEqual(set(json.loads(sed[key])),
                                     set(json.loads(res)))
                elif key == 'AutomaticDataSources':
                    self.assertEqual(set(json.loads(sed[key])),
                                     set(poolchannels))
                else:
                    self.assertEqual(sed[key], vl)
        finally:
            simps2.tearDown()

    ## test
    # \brief It tests default settings
    def test_updateControllers_2wds_notangodspool_alias(self):
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

            cnf = json.loads(rs.configuration)
            cnf["AutomaticDataSources"] = json.dumps(poolchannels)
            cnf["AutomaticComponentGroup"] = json.dumps(componentgroup)
            rs.configuration = json.dumps(cnf)
            rs.updateControllers()
            res = self.value(rs, "AutomaticComponentGroup")

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
                elif key == 'AutomaticComponentGroup':
                    self.assertEqual(set(json.loads(sed[key])),
                                     set(json.loads(res)))
                elif key == 'AutomaticDataSources':
                    self.assertEqual(set(json.loads(sed[key])),
                                     set(poolchannels))
                else:
                    self.assertEqual(sed[key], vl)
        finally:
            db.delete_device_alias(arr[0]["name"])
            simps2.tearDown()

    ## test
    # \brief It tests default settings
    def test_updateControllers_2wds_notangodspool_alias_value(self):
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

            cnf = json.loads(rs.configuration)
            cnf["AutomaticDataSources"] = json.dumps(poolchannels)
            cnf["AutomaticComponentGroup"] = json.dumps(componentgroup)
            rs.configuration = json.dumps(cnf)
            rs.updateControllers()
            res = self.value(rs, "AutomaticComponentGroup")

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
                elif key == 'AutomaticComponentGroup':
                    self.assertEqual(set(json.loads(sed[key])),
                                     set(json.loads(res)))
                elif key == 'AutomaticDataSources':
                    self.assertEqual(set(json.loads(sed[key])),
                                     set(poolchannels))
                else:
                    self.assertEqual(sed[key], vl)
        finally:
            db.delete_device_alias(arr[0]["name"])
            simps2.tearDown()

    ## test
    # \brief It tests default settings
    def test_updateControllers_2wds_notangodspool_alias_novalue(self):
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

            cnf = json.loads(rs.configuration)
            cnf["AutomaticDataSources"] = json.dumps(poolchannels)
            cnf["AutomaticComponentGroup"] = json.dumps(componentgroup)
            rs.configuration = json.dumps(cnf)
            rs.updateControllers()
            res = self.value(rs, "AutomaticComponentGroup")

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
                elif key == 'AutomaticComponentGroup':
                    self.assertEqual(set(json.loads(sed[key])),
                                     set(json.loads(res)))
                elif key == 'AutomaticDataSources':
                    self.assertEqual(set(json.loads(sed[key])),
                                     set(poolchannels))
                else:
                    self.assertEqual(sed[key], vl)
        finally:
            db.delete_device_alias(arr[0]["name"])
            simps2.tearDown()

    ## test
    # \brief It tests default settings
    def test_updateControllers_2wds_nocomponents(self):
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

            cnf = json.loads(rs.configuration)
            cnf["AutomaticDataSources"] = json.dumps(poolchannels)
            cnf["AutomaticComponentGroup"] = json.dumps(componentgroup)
            rs.configuration = json.dumps(cnf)
            rs.updateControllers()
            res = self.value(rs, "AutomaticComponentGroup")

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
                elif key == 'AutomaticComponentGroup':
                    self.assertEqual(set(json.loads(sed[key])),
                                     set(json.loads(res)))
                elif key == 'AutomaticDataSources':
                    self.assertEqual(set(json.loads(sed[key])),
                                     set(poolchannels))
                else:
                    self.assertEqual(sed[key], vl)
        finally:
            simps2.tearDown()

    ## resetAutomaticComponents test
    # \brief It tests default settings
    def test_resetAutomaticComponents_simple(self):
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
        rs.resetAutomaticComponents()
        sed2 = json.loads(self._cf.dp.selections([val["MntGrp"]])[0])
        res = self.value(rs, "AutomaticComponentGroup")
        self.assertEqual(res, '{}')
        rs.configuration = '{}'
        rs.configDevice = val["ConfigDevice"]
        rs.door = val["Door"]
        rs.mntGrp = val["MntGrp"]
        rs.fetchConfiguration()
        res = self.value(rs, "AutomaticComponentGroup")
        self.assertEqual(res, '{}')

        self.compareToDump(rs, ["AutomaticComponentGroup"])

    ## resetAutomaticComponents test
    # \brief It tests default settings
    def test_resetAutomaticComponents_withcf(self):
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
        rs.resetAutomaticComponents()
        sed2 = json.loads(self._cf.dp.selections([val["MntGrp"]])[0])
        res = self.value(rs, "AutomaticComponentGroup")
        self.compareToDump(rs, ["AutomaticComponentGroup"])

        self.assertEqual(res, '{}')
        self.assertEqual(componentgroup, {})
        self.assertEqual(channelerrors, [])
        print self._cf.dp.GetCommandVariable("COMMANDS")

        rs.configuration = '{}'
        rs.configDevice = val["ConfigDevice"]
        rs.door = val["Door"]
        rs.mntGrp = val["MntGrp"]
        rs.fetchConfiguration()
        res = self.value(rs, "AutomaticComponentGroup")
        self.assertEqual(res, '{}')

    ## test
    # \brief It tests default settings
    def test_resetAutomaticComponents_withcf_cps(self):
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
        self.setProp(rs, "defaultAutomaticComponents",
                     list(componentgroup.keys()))
        rs.configDevice = val["ConfigDevice"]
        rs.door = val["Door"]
        rs.mntGrp = val["MntGrp"]
        rs.writerDevice = val["WriterDevice"]

        self._ms.dps[self._ms.ms.keys()[0]].Init()

        cnf = json.loads(rs.configuration)
        cnf["AutomaticDataSources"] = json.dumps(poolchannels)
        rs.configuration = json.dumps(cnf)
        # rs.defaultAutomaticComponents = list(componentgroup.keys())
        self.dump(rs)
        sed1 = json.loads(self._cf.dp.selections([val["MntGrp"]])[0])
        rs.resetAutomaticComponents()
        res = self.value(rs, "AutomaticComponentGroup")
        self.compareToDump(rs, ["AutomaticComponentGroup"])
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
            elif key == 'AutomaticComponentGroup':
                self.myAssertDict(json.loads(sed[key]), json.loads(res))
                self.assertNotEqual(sed1[key], res)
            elif key == 'AutomaticDataSources':
                self.assertEqual(set(json.loads(sed[key])), set(poolchannels))
                self.assertEqual(set(json.loads(sed1[key])), set(poolchannels))
            else:
                self.assertEqual(sed[key], vl)
                self.assertEqual(sed1[key], vl)

    ## test
    # \brief It tests default settings
    def test_resetAutomaticComponents_withcf_cps_t(self):
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
        self.setProp(rs, "defaultAutomaticComponents",
                     list(componentgroup.keys()))
        rs.configDevice = val["ConfigDevice"]
        rs.door = val["Door"]
        rs.mntGrp = val["MntGrp"]
        rs.writerDevice = val["WriterDevice"]

        cnf = json.loads(rs.configuration)
        cnf["AutomaticDataSources"] = json.dumps(poolchannels)
        rs.configuration = json.dumps(cnf)
        self.dump(rs)
        sed1 = json.loads(self._cf.dp.selections([val["MntGrp"]])[0])
        rs.resetAutomaticComponents()
        sed2 = json.loads(self._cf.dp.selections([val["MntGrp"]])[0])
        self.compareToDump(rs, ["AutomaticComponentGroup"])
        res = self.value(rs, "AutomaticComponentGroup")
        self.myAssertDict(json.loads(res), {"mycp": True})
        self.assertEqual(channelerrors, [])

        self.assertTrue(val["MntGrp"] in self._cf.dp.availableSelections())

    ## test
    # \brief It tests default settings
    def test_resetAutomaticComponents_withcf_nocps(self):
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
        self.setProp(rs, "defaultAutomaticComponents",
                     list(componentgroup.keys()))
        rs.configDevice = val["ConfigDevice"]
        rs.door = val["Door"]
        rs.mntGrp = val["MntGrp"]
        rs.writerDevice = val["WriterDevice"]

        cnf = json.loads(rs.configuration)
        cnf["AutomaticDataSources"] = json.dumps(poolchannels)
        rs.configuration = json.dumps(cnf)
        self.dump(rs)
        sed1 = json.loads(self._cf.dp.selections([val["MntGrp"]])[0])
        rs.resetAutomaticComponents()
        sed2 = json.loads(self._cf.dp.selections([val["MntGrp"]])[0])
        self.compareToDump(rs, ["AutomaticComponentGroup"])
        res = self.value(rs, "AutomaticComponentGroup")

        self.myAssertDict(json.loads(res), {})
        self.assertEqual(channelerrors, [])

        print self._cf.dp.GetCommandVariable("COMMANDS")

        self.assertTrue(val["MntGrp"] in self._cf.dp.availableSelections())

    ## test
    # \brief It tests default settings
    def test_resetAutomaticComponents_withcf_nochnnel(self):
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
        self.setProp(rs, "defaultAutomaticComponents",
                     list(componentgroup.keys()))
        rs.configDevice = val["ConfigDevice"]
        rs.door = val["Door"]
        rs.mntGrp = val["MntGrp"]
        rs.writerDevice = val["WriterDevice"]

        self._ms.dps[self._ms.ms.keys()[0]].Init()

        cnf = json.loads(rs.configuration)
        cnf["AutomaticDataSources"] = json.dumps(poolchannels)
        rs.configuration = json.dumps(cnf)
        self.dump(rs)
        sed1 = json.loads(self._cf.dp.selections([val["MntGrp"]])[0])
        rs.resetAutomaticComponents()
        res = self.value(rs, "AutomaticComponentGroup")
        self.compareToDump(rs, ["AutomaticComponentGroup"])

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
            elif key == 'AutomaticComponentGroup':
                self.myAssertDict(json.loads(sed[key]),
                                  json.loads(res))
                self.assertNotEqual(sed1[key], res)
            elif key == 'AutomaticDataSources':
                self.assertEqual(set(json.loads(sed[key])), set(poolchannels))
                self.assertEqual(set(json.loads(sed1[key])), set(poolchannels))
            else:
                self.assertEqual(sed[key], vl)
                self.assertEqual(sed1[key], vl)

    ## test
    # \brief It tests default settings
    def test_resetAutomaticComponents_withcf_nochnnel_t(self):
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
        self.setProp(rs, "defaultAutomaticComponents",
                     list(componentgroup.keys()))
        rs.configDevice = val["ConfigDevice"]
        rs.door = val["Door"]
        rs.mntGrp = val["MntGrp"]
        rs.writerDevice = val["WriterDevice"]

        self._ms.dps[self._ms.ms.keys()[0]].Init()

        cnf = json.loads(rs.configuration)
        cnf["AutomaticDataSources"] = json.dumps(poolchannels)
        rs.configuration = json.dumps(cnf)
        self.dump(rs)
        sed1 = json.loads(self._cf.dp.selections([val["MntGrp"]])[0])
        rs.resetAutomaticComponents()
        sed2 = json.loads(self._cf.dp.selections([val["MntGrp"]])[0])
        res = self.value(rs, "AutomaticComponentGroup")
        self.compareToDump(rs, ["AutomaticComponentGroup"])

        self.myAssertDict(json.loads(res), {"mycp": True})
        self.assertEqual(channelerrors, [])

        self.assertTrue(val["MntGrp"] in self._cf.dp.availableSelections())

    ## test
    # \brief It tests default settings
    def test_resetAutomaticComponents_wds_t(self):
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
        self.setProp(rs, "defaultAutomaticComponents",
                     list(componentgroup.keys()))
        rs.configDevice = val["ConfigDevice"]
        rs.door = val["Door"]
        rs.mntGrp = val["MntGrp"]
        rs.writerDevice = val["WriterDevice"]

        self._ms.dps[self._ms.ms.keys()[0]].Init()

        cnf = json.loads(rs.configuration)
        cnf["AutomaticDataSources"] = json.dumps(poolchannels)
        rs.configuration = json.dumps(cnf)
        self.dump(rs)
        sed1 = json.loads(self._cf.dp.selections([val["MntGrp"]])[0])
        rs.resetAutomaticComponents()
        sed2 = json.loads(self._cf.dp.selections([val["MntGrp"]])[0])
        res = self.value(rs, "AutomaticComponentGroup")
        self.compareToDump(rs, ["AutomaticComponentGroup"])

        self.myAssertDict(json.loads(res), {"smycp": True})
        self.assertEqual(channelerrors, [])

        self.assertTrue(val["MntGrp"] in self._cf.dp.availableSelections())

    ## test
    # \brief It tests default settings
    def test_resetAutomaticComponents_wds(self):
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
        self.setProp(rs, "defaultAutomaticComponents",
                     list(componentgroup.keys()))
        rs.configDevice = val["ConfigDevice"]
        rs.door = val["Door"]
        rs.mntGrp = val["MntGrp"]
        rs.writerDevice = val["WriterDevice"]

        self._ms.dps[self._ms.ms.keys()[0]].Init()
        cnf = json.loads(rs.configuration)
        cnf["AutomaticDataSources"] = json.dumps(poolchannels)
        rs.configuration = json.dumps(cnf)
        self.dump(rs)
        sed1 = json.loads(self._cf.dp.selections([val["MntGrp"]])[0])
        rs.resetAutomaticComponents()
        res = self.value(rs, "AutomaticComponentGroup")
        self.compareToDump(rs, ["AutomaticComponentGroup"])

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
            elif key == 'AutomaticComponentGroup':
                self.myAssertDict(json.loads(sed[key]),
                                  json.loads(res))
                self.assertNotEqual(sed1[key], res)
            elif key == 'AutomaticDataSources':
                self.assertEqual(set(json.loads(sed[key])),
                                 set(poolchannels))
                self.assertEqual(set(json.loads(sed1[key])),
                                 set(poolchannels))
            else:
                self.assertEqual(sed[key], vl)
                self.assertEqual(sed1[key], vl)

    ## test
    # \brief It tests default settings
    def test_resetAutomaticComponents_wds2(self):
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
        self.setProp(rs, "defaultAutomaticComponents",
                     list(componentgroup.keys()))
        rs.configDevice = val["ConfigDevice"]
        rs.door = val["Door"]
        rs.mntGrp = val["MntGrp"]
        rs.writerDevice = val["WriterDevice"]

        self._ms.dps[self._ms.ms.keys()[0]].Init()

        cnf = json.loads(rs.configuration)
        cnf["AutomaticDataSources"] = json.dumps(poolchannels)
        rs.configuration = json.dumps(cnf)
        self.dump(rs)
        sed1 = json.loads(self._cf.dp.selections([val["MntGrp"]])[0])
        rs.resetAutomaticComponents()
        res = self.value(rs, "AutomaticComponentGroup")
        self.compareToDump(rs, ["AutomaticComponentGroup"])

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
            elif key == 'AutomaticComponentGroup':
                self.myAssertDict(json.loads(sed[key]),
                                  json.loads(res))
                self.assertNotEqual(sed1[key], res)
            elif key == 'AutomaticDataSources':
                self.assertEqual(set(json.loads(sed[key])),
                                 set(poolchannels))
                self.assertEqual(set(json.loads(sed1[key])),
                                 set(poolchannels))
            else:
                self.assertEqual(sed[key], vl)
                self.assertEqual(sed1[key], vl)

    ## test
    # \brief It tests default settings
    def test_resetAutomaticComponents_2wds(self):
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
            self.setProp(rs, "defaultAutomaticComponents",
                         list(componentgroup.keys()))
            rs.configDevice = val["ConfigDevice"]
            rs.door = val["Door"]
            rs.mntGrp = val["MntGrp"]
            rs.writerDevice = val["WriterDevice"]

            self._ms.dps[self._ms.ms.keys()[0]].Init()

            cnf = json.loads(rs.configuration)
            cnf["AutomaticDataSources"] = json.dumps(poolchannels)
            rs.configuration = json.dumps(cnf)
            self.dump(rs)
            sed1 = json.loads(self._cf.dp.selections([val["MntGrp"]])[0])
            rs.resetAutomaticComponents()
            res = self.value(rs, "AutomaticComponentGroup")
            self.compareToDump(rs, ["AutomaticComponentGroup"])

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
                elif key == 'AutomaticComponentGroup':
                    self.myAssertDict(json.loads(sed[key]),
                                      json.loads(res))
                    self.assertNotEqual(sed1[key], res)
                elif key == 'AutomaticDataSources':
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
    def test_resetAutomaticComponents_2wds_dvnorunning(self):
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
            self.setProp(rs, "defaultAutomaticComponents",
                         list(componentgroup.keys()))
            rs.configDevice = val["ConfigDevice"]
            rs.door = val["Door"]
            rs.mntGrp = val["MntGrp"]
            rs.writerDevice = val["WriterDevice"]

            self._ms.dps[self._ms.ms.keys()[0]].Init()

            cnf = json.loads(rs.configuration)
            cnf["AutomaticDataSources"] = json.dumps(poolchannels)
            rs.configuration = json.dumps(cnf)
            self.dump(rs)
            sed1 = json.loads(self._cf.dp.selections([val["MntGrp"]])[0])
            rs.resetAutomaticComponents()
            res = self.value(rs, "AutomaticComponentGroup")
            self.compareToDump(rs, ["AutomaticComponentGroup"])

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
                elif key == 'AutomaticComponentGroup':
                    self.myAssertDict(json.loads(sed[key]), json.loads(res))
                    self.assertNotEqual(sed1[key], res)
                elif key == 'AutomaticDataSources':
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
    def test_resetAutomaticComponents_2wds_dvnodef(self):
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
        self.setProp(rs, "defaultAutomaticComponents",
                     list(componentgroup.keys()))
        rs.configDevice = val["ConfigDevice"]
        rs.door = val["Door"]
        rs.mntGrp = val["MntGrp"]
        rs.writerDevice = val["WriterDevice"]

        self._ms.dps[self._ms.ms.keys()[0]].Init()

        cnf = json.loads(rs.configuration)
        cnf["AutomaticDataSources"] = json.dumps(poolchannels)
        rs.configuration = json.dumps(cnf)
        self.dump(rs)
        sed1 = json.loads(self._cf.dp.selections([val["MntGrp"]])[0])
        rs.resetAutomaticComponents()
        res = self.value(rs, "AutomaticComponentGroup")
        self.compareToDump(rs, ["AutomaticComponentGroup"])

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
            elif key == 'AutomaticComponentGroup':
                self.myAssertDict(json.loads(sed[key]), json.loads(res))
                self.assertNotEqual(sed1[key], res)
            elif key == 'AutomaticDataSources':
                self.assertEqual(set(json.loads(sed[key])),
                                 set(poolchannels))
                self.assertEqual(set(json.loads(sed1[key])),
                                 set(poolchannels))
            else:
                self.assertEqual(sed[key], vl)
                self.assertEqual(sed1[key], vl)

    ## test
    # \brief It tests default settings
    def test_resetAutomaticComponents_2wds_nods(self):
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
            self.setProp(rs, "defaultAutomaticComponents",
                         list(componentgroup.keys()))
            rs.configDevice = val["ConfigDevice"]
            rs.door = val["Door"]
            rs.mntGrp = val["MntGrp"]
            rs.writerDevice = val["WriterDevice"]

            self._ms.dps[self._ms.ms.keys()[0]].Init()

            self._cf.dp.SetCommandVariable(["CPDICT", json.dumps(cps)])
            self._cf.dp.SetCommandVariable(["DSDICT", json.dumps(dss)])

            cnf = json.loads(rs.configuration)
            cnf["AutomaticDataSources"] = json.dumps(poolchannels)
            rs.configuration = json.dumps(cnf)
            self.dump(rs)
            sed1 = json.loads(self._cf.dp.selections([val["MntGrp"]])[0])
            rs.resetAutomaticComponents()
            res = self.value(rs, "AutomaticComponentGroup")
            self.compareToDump(rs, ["AutomaticComponentGroup"])

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
                elif key == 'AutomaticComponentGroup':
                    self.myAssertDict(json.loads(sed[key]), json.loads(res))
                    self.assertNotEqual(sed1[key], res)
                elif key == 'AutomaticDataSources':
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
    def test_resetAutomaticComponents_2wds_nodspool(self):
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
            self.setProp(rs, "defaultAutomaticComponents",
                         list(componentgroup.keys()))
            rs.configDevice = val["ConfigDevice"]
            rs.door = val["Door"]
            rs.mntGrp = val["MntGrp"]
            rs.writerDevice = val["WriterDevice"]

            self._ms.dps[self._ms.ms.keys()[0]].Init()

            cnf = json.loads(rs.configuration)
            cnf["AutomaticDataSources"] = json.dumps(poolchannels)
            rs.configuration = json.dumps(cnf)
            self.dump(rs)
            sed1 = json.loads(self._cf.dp.selections([val["MntGrp"]])[0])
            rs.resetAutomaticComponents()
            res = self.value(rs, "AutomaticComponentGroup")
            self.compareToDump(rs, ["AutomaticComponentGroup"])

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
                elif key == 'AutomaticComponentGroup':
                    self.myAssertDict(json.loads(sed[key]), json.loads(res))
                    self.assertNotEqual(sed1[key], res)
                elif key == 'AutomaticDataSources':
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
    def test_resetAutomaticComponents_2wds_notangods(self):
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
            self.setProp(rs, "defaultAutomaticComponents",
                         list(componentgroup.keys()))
            rs.configDevice = val["ConfigDevice"]
            rs.door = val["Door"]
            rs.mntGrp = val["MntGrp"]
            rs.writerDevice = val["WriterDevice"]

            self._ms.dps[self._ms.ms.keys()[0]].Init()

            cnf = json.loads(rs.configuration)
            cnf["AutomaticDataSources"] = json.dumps(poolchannels)
            rs.configuration = json.dumps(cnf)
            self.dump(rs)
            sed1 = json.loads(self._cf.dp.selections([val["MntGrp"]])[0])
            rs.resetAutomaticComponents()
            res = self.value(rs, "AutomaticComponentGroup")
            self.compareToDump(rs, ["AutomaticComponentGroup"])

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
                elif key == 'AutomaticComponentGroup':
                    self.myAssertDict(json.loads(sed[key]), json.loads(res))
                    self.assertNotEqual(sed1[key], res)
                elif key == 'AutomaticDataSources':
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
    def test_resetAutomaticComponents_2wds_notangodsnopool(self):
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

            self.setProp(rs, "defaultAutomaticComponents",
                         list(componentgroup.keys()))
            rs.configDevice = val["ConfigDevice"]
            rs.door = val["Door"]
            rs.mntGrp = val["MntGrp"]
            rs.writerDevice = val["WriterDevice"]

            self._ms.dps[self._ms.ms.keys()[0]].Init()

            self._cf.dp.SetCommandVariable(["CPDICT", json.dumps(cps)])
            self._cf.dp.SetCommandVariable(["DSDICT", json.dumps(dss)])

            cnf = json.loads(rs.configuration)
            cnf["AutomaticDataSources"] = json.dumps(poolchannels)
            rs.configuration = json.dumps(cnf)
            self.dump(rs)
            sed1 = json.loads(self._cf.dp.selections([val["MntGrp"]])[0])
            rs.resetAutomaticComponents()
            res = self.value(rs, "AutomaticComponentGroup")
            self.compareToDump(rs, ["AutomaticComponentGroup"])

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
                elif key == 'AutomaticComponentGroup':
                    self.myAssertDict(json.loads(sed[key]), json.loads(res))
                    self.assertNotEqual(sed1[key], res)
                elif key == 'AutomaticDataSources':
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
    def test_resetAutomaticComponents_2wds_notangodsnopool2(self):
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
            self.setProp(rs, "defaultAutomaticComponents",
                         list(componentgroup.keys()))
            rs.configDevice = val["ConfigDevice"]
            rs.door = val["Door"]
            rs.mntGrp = val["MntGrp"]
            rs.writerDevice = val["WriterDevice"]

            self._ms.dps[self._ms.ms.keys()[0]].Init()

            cnf = json.loads(rs.configuration)
            cnf["AutomaticDataSources"] = json.dumps(poolchannels)
            rs.configuration = json.dumps(cnf)
            self.dump(rs)
            sed1 = json.loads(self._cf.dp.selections([val["MntGrp"]])[0])
            rs.resetAutomaticComponents()
            res = self.value(rs, "AutomaticComponentGroup")
            self.compareToDump(rs, ["AutomaticComponentGroup"])

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
                elif key == 'AutomaticComponentGroup':
                    self.myAssertDict(json.loads(sed[key]), json.loads(res))
                    self.assertNotEqual(sed1[key], res)
                elif key == 'AutomaticDataSources':
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
    def test_resetAutomaticComponents_2wds_notangods2(self):
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
            self.setProp(rs, "defaultAutomaticComponents",
                         list(componentgroup.keys()))
            rs.configDevice = val["ConfigDevice"]
            rs.door = val["Door"]
            rs.mntGrp = val["MntGrp"]
            rs.writerDevice = val["WriterDevice"]

            self._ms.dps[self._ms.ms.keys()[0]].Init()

            pool = self._pool.dp
            pool.AcqChannelList = [json.dumps(a) for a in arr]

            cnf = json.loads(rs.configuration)
            cnf["AutomaticDataSources"] = json.dumps(poolchannels)
            rs.configuration = json.dumps(cnf)
            self.dump(rs)
            sed1 = json.loads(self._cf.dp.selections([val["MntGrp"]])[0])
            rs.resetAutomaticComponents()
            res = self.value(rs, "AutomaticComponentGroup")
            self.compareToDump(rs, ["AutomaticComponentGroup"])

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
                elif key == 'AutomaticComponentGroup':
                    self.myAssertDict(json.loads(sed[key]), json.loads(res))
                    self.assertNotEqual(sed1[key], res)
                elif key == 'AutomaticDataSources':
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
    def test_resetAutomaticComponents_2wds_notangodspool_error(self):
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
            self.setProp(rs, "defaultAutomaticComponents",
                         list(componentgroup.keys()))
            rs.configDevice = val["ConfigDevice"]
            rs.door = val["Door"]
            rs.mntGrp = val["MntGrp"]
            rs.writerDevice = val["WriterDevice"]

            self._ms.dps[self._ms.ms.keys()[0]].Init()

            pool = self._pool.dp
            pool.AcqChannelList = [json.dumps(a) for a in arr]

            cnf = json.loads(rs.configuration)
            cnf["AutomaticDataSources"] = json.dumps(poolchannels)
            rs.configuration = json.dumps(cnf)
            self.dump(rs)
            sed1 = json.loads(self._cf.dp.selections([val["MntGrp"]])[0])
            rs.resetAutomaticComponents()
            res = self.value(rs, "AutomaticComponentGroup")
            self.compareToDump(rs, ["AutomaticComponentGroup"])

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
                elif key == 'AutomaticComponentGroup':
                    self.myAssertDict(json.loads(sed[key]), json.loads(res))
                    self.assertNotEqual(sed1[key], res)
                elif key == 'AutomaticDataSources':
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
    def test_resetAutomaticComponents_2wds_notangodspool(self):
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
            self.setProp(rs, "defaultAutomaticComponents",
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

            cnf = json.loads(rs.configuration)
            cnf["AutomaticDataSources"] = json.dumps(poolchannels)
            rs.configuration = json.dumps(cnf)
            self.dump(rs)
            sed1 = json.loads(self._cf.dp.selections([val["MntGrp"]])[0])
            rs.resetAutomaticComponents()
            res = self.value(rs, "AutomaticComponentGroup")
            self.compareToDump(rs, ["AutomaticComponentGroup"])

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
                elif key == 'AutomaticComponentGroup':
                    self.myAssertDict(json.loads(sed[key]), json.loads(res))
                    self.assertNotEqual(sed1[key], res)
                elif key == 'AutomaticDataSources':
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
    def test_resetAutomaticComponents_2wds_notangodspool_alias(self):
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
            self.setProp(rs, "defaultAutomaticComponents",
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

            cnf = json.loads(rs.configuration)
            cnf["AutomaticDataSources"] = json.dumps(poolchannels)
            rs.configuration = json.dumps(cnf)
            self.dump(rs)
            sed1 = json.loads(self._cf.dp.selections([val["MntGrp"]])[0])
            rs.resetAutomaticComponents()
            res = self.value(rs, "AutomaticComponentGroup")
            self.compareToDump(rs, ["AutomaticComponentGroup"])

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
                elif key == 'AutomaticComponentGroup':
                    self.myAssertDict(json.loads(sed[key]), json.loads(res))
                    self.assertNotEqual(sed1[key], res)
                elif key == 'AutomaticDataSources':
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
    def test_resetAutomaticComponents_2wds_notangodspool_alias_value(self):
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
            self.setProp(rs, "defaultAutomaticComponents",
                         list(componentgroup.keys()))
            rs.configDevice = val["ConfigDevice"]
            rs.door = val["Door"]
            rs.mntGrp = val["MntGrp"]
            rs.writerDevice = val["WriterDevice"]

            self._ms.dps[self._ms.ms.keys()[0]].Init()

            pool = self._pool.dp
            pool.AcqChannelList = [json.dumps(a) for a in arr]

            cnf = json.loads(rs.configuration)
            cnf["AutomaticDataSources"] = json.dumps(poolchannels)
            rs.configuration = json.dumps(cnf)
            self.dump(rs)
            sed1 = json.loads(self._cf.dp.selections([val["MntGrp"]])[0])
            rs.resetAutomaticComponents()
            res = self.value(rs, "AutomaticComponentGroup")
            self.compareToDump(rs, ["AutomaticComponentGroup"])

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
                elif key == 'AutomaticComponentGroup':
                    self.myAssertDict(json.loads(sed[key]), json.loads(res))
                    self.assertNotEqual(sed1[key], res)
                elif key == 'AutomaticDataSources':
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
    def test_resetAutomaticComponents_2wds_notangodspool_alias_novalue(self):
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
            self.setProp(rs, "defaultAutomaticComponents",
                         list(componentgroup.keys()))
            rs.configDevice = val["ConfigDevice"]
            rs.door = val["Door"]
            rs.mntGrp = val["MntGrp"]
            rs.writerDevice = val["WriterDevice"]

            self._ms.dps[self._ms.ms.keys()[0]].Init()

            pool = self._pool.dp
            pool.AcqChannelList = [json.dumps(a) for a in arr]

            cnf = json.loads(rs.configuration)
            cnf["AutomaticDataSources"] = json.dumps(poolchannels)
            rs.configuration = json.dumps(cnf)
            self.dump(rs)
            sed1 = json.loads(self._cf.dp.selections([val["MntGrp"]])[0])
            rs.resetAutomaticComponents()
            res = self.value(rs, "AutomaticComponentGroup")
            self.compareToDump(rs, ["AutomaticComponentGroup"])

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
                elif key == 'AutomaticComponentGroup':
                    self.myAssertDict(json.loads(sed[key]), json.loads(res))
                    self.assertNotEqual(sed1[key], res)
                elif key == 'AutomaticDataSources':
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
    def test_resetAutomaticComponents_2wds_nocomponents(self):
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
            self.setProp(rs, "defaultAutomaticComponents",
                         list(componentgroup.keys()))
            rs.configDevice = val["ConfigDevice"]
            rs.door = val["Door"]
            rs.mntGrp = val["MntGrp"]
            rs.writerDevice = val["WriterDevice"]

            self._ms.dps[self._ms.ms.keys()[0]].Init()

            cnf = json.loads(rs.configuration)
            cnf["AutomaticDataSources"] = json.dumps(poolchannels)
            rs.configuration = json.dumps(cnf)
            self.dump(rs)
            sed1 = json.loads(self._cf.dp.selections([val["MntGrp"]])[0])
            rs.resetAutomaticComponents()
            res = self.value(rs, "AutomaticComponentGroup")

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
                elif key == 'AutomaticComponentGroup':
                    self.myAssertDict(json.loads(sed[key]), json.loads(res))
                    self.assertNotEqual(sed1[key], res)
                elif key == 'AutomaticDataSources':
                    self.assertEqual(set(json.loads(sed[key])),
                                     set(poolchannels))
                    self.assertEqual(set(json.loads(sed1[key])),
                                     set(poolchannels))
                else:
                    self.assertEqual(sed[key], vl)
                    self.assertEqual(sed1[key], vl)
        finally:
            simps2.tearDown()


if __name__ == '__main__':
    unittest.main()
