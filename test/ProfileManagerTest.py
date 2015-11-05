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
## \file ProfileManagerTest.py
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
from nxsrecconfig.Describer import Describer
from nxsrecconfig.ProfileManager import ProfileManager
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
class ProfileManagerTest(unittest.TestCase):

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
            'exp_t01': {'exp_t01': [
                    ('STEP', 'CLIENT', 'haso228k:10000/expchan/dgg2_exp_01/1',
                     'NX_FLOAT', None)]},
            'dim1': {'tann1c': [
                    ('INIT', 'TANGO', 'dsf/sd/we/myattr2', 'NX_INT8', [34])]},
            'dim2': {'tann1c': [
                    ('INIT', 'TANGO', 'dsf/sd/we/myattr2', 'NX_INT8',
                     ['$datasource.ann'])]},
            'dim3': {'tann1c': [
                    ('INIT', 'TANGO', 'dsf/sd/we/myattr2', 'NX_INT8',
                     [1234])]},
            'dim4': {'tann1c': [
                    ('INIT', 'TANGO', 'dsf/sd/we/myattr2', 'NX_INT8',
                     ['$datasource.ann2'])]},
            'dim5': {'tann1c': [
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
            'scan2': {'c01': [('STEP', 'CLIENT', 'exp_c01', 'NX_FLOAT', None)],
                      'c02': [('STEP', 'CLIENT', 'exp_c02', 'NX_FLOAT', None)],
                      'mca': [('STEP', 'CLIENT', 'p09/mca/exp.02', 'NX_FLOAT',
                               [2048])],
                     },
            'scan3': {'c01': [('STEP', 'CLIENT', 'exp_c01', 'NX_FLOAT', None),
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
            'scalar_Encoded': (
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
            'spectrum_Encoded': (
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
            'image_Encoded':
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
            'scalar_long': (
                '<definition><datasource type="TANGO" name="scalar_long">'
                '<record name="ScalarLong"/>'
                '<device member="attribute" name="ttestp09/testts/t01r228"/>'
                '</datasource></definition>'),
            'scalar_bool': (
                '<definition><datasource type="TANGO" name="scalar_bool">'
                '<record name="ScalarBoolean"/>'
                '<device member="attribute" name="ttestp09/testts/t02r228"/>'
                '</datasource></definition>'),
            'scalar_short': (
                '<definition><datasource type="TANGO" name="scalar_short">'
                '<record name="ScalarShort"/>'
                '<device member="attribute" name="ttestp09/testts/t03r228"/>'
                '</datasource></definition>'),
            'scalar_ushort': (
                '<definition><datasource type="TANGO" name="scalar_ushort">'
                '<record name="ScalarUShort"/>'
                '<device member="attribute" name="ttestp09/testts/t04r228"/>'
                '</datasource></definition>'),
            'scalar_ulong': (
                '<definition><datasource type="TANGO" name="scalar_ulong">'
                '<record name="ScalarULong"/>'
                '<device member="attribute" name="ttestp09/testts/t05r228"/>'
                '</datasource></definition>'),
            'scalar_long64': (
                '<definition><datasource type="TANGO" name="scalar_long64">'
                '<record name="ScalarLong64"/>'
                '<device member="attribute" name="ttestp09/testts/t06r228"/>'
                '</datasource></definition>'),
            'scalar_ulong64': (
                '<definition><datasource type="TANGO" name="scalar_ulong64">'
                '<record name="ScalarULong64"/>'
                '<device member="attribute" name="ttestp09/testts/t07r228"/>'
                '</datasource></definition>'),
            'scalar_float': (
                '<definition><datasource type="TANGO" name="scalar_float">'
                '<record name="ScalarFloat"/>'
                '<device member="attribute" name="ttestp09/testts/t08r228"/>'
                '</datasource></definition>'),
            'scalar_double': (
                '<definition><datasource type="TANGO" name="scalar_double">'
                '<record name="ScalarDouble"/>'
                '<device member="attribute" name="ttestp09/testts/t09r228"/>'
                '</datasource></definition>'),
            'scalar_string': (
                '<definition><datasource type="TANGO" name="scalar_string">'
                '<record name="ScalarString"/>'
                '<device member="attribute" name="ttestp09/testts/t10r228"/>'
                '</datasource></definition>'),
            'scalar_Encoded': (
                '<definition><datasource type="TANGO" name="scalar_encoded">'
                '<record name="ScalarEncoded"/>'
                '<device member="attribute" name="ttestp09/testts/t11r228"/>'
                '</datasource></definition>'),
            'scalar_uchar': (
                '<definition><datasource type="TANGO" name="scalar_uchar">'
                '<record name="ScalarUChar"/>'
                '<device member="attribute" name="ttestp09/testts/t12r228"/>'
                '</datasource></definition>'),
            'spectrum_long': (
                '<definition><datasource type="TANGO" name="spectrum_long">'
                '<record name="SpectrumLong"/>'
                '<device member="attribute" name="ttestp09/testts/t13r228"/>'
                '</datasource></definition>'),
            'spectrum_bool': (
                '<definition><datasource type="TANGO" name="spectrum_bool">'
                '<record name="SpectrumBoolean"/>'
                '<device member="attribute" name="ttestp09/testts/t14r228"/>'
                '</datasource></definition>'),
            'spectrum_short': (
                '<definition><datasource type="TANGO" name="spectrum_short">'
                '<record name="SpectrumShort"/>'
                '<device member="attribute" name="ttestp09/testts/t15r228"/>'
                '</datasource></definition>'),
            'spectrum_ushort': (
                '<definition><datasource type="TANGO" name="spectrum_ushort">'
                '<record name="SpectrumUShort"/>'
                '<device member="attribute" name="ttestp09/testts/t16r228"/>'
                '</datasource></definition>'),
            'spectrum_ulong': (
                '<definition><datasource type="TANGO" name="spectrum_ulong">'
                '<record name="SpectrumULong"/>'
                '<device member="attribute" name="ttestp09/testts/t17r228"/>'
                '</datasource></definition>'),
            'spectrum_long64': (
                '<definition><datasource type="TANGO" name="spectrum_long64">'
                '<record name="SpectrumLong64"/>'
                '<device member="attribute" name="ttestp09/testts/t18r228"/>'
                '</datasource></definition>'),
            'spectrum_ulong64': (
                '<definition><datasource type="TANGO" name="spectrum_ulong64">'
                '<record name="SpectrumULong64"/>'
                '<device member="attribute" name="ttestp09/testts/t19r228"/>'
                '</datasource></definition>'),
            'spectrum_float': (
                '<definition><datasource type="TANGO" name="spectrum_float">'
                '<record name="SpectrumFloat"/>'
                '<device member="attribute" name="ttestp09/testts/t20r228"/>'
                '</datasource></definition>'),
            'spectrum_double': (
                '<definition><datasource type="TANGO" name="spectrum_double">'
                '<record name="SpectrumDouble"/>'
                '<device member="attribute" name="ttestp09/testts/t21r228"/>'
                '</datasource></definition>'),
            'spectrum_string': (
                '<definition><datasource type="TANGO" name="spectrum_string">'
                '<record name="SpectrumString"/>'
                '<device member="attribute" name="ttestp09/testts/t22r228"/>'
                '</datasource></definition>'),
            'spectrum_Encoded': (
                '<definition><datasource type="TANGO" name="spectrum_encoded">'
                '<record name="SpectrumEncoded"/>'
                '<device member="attribute" name="ttestp09/testts/t23r228"/>'
                '</datasource></definition>'),
            'spectrum_uchar': (
                '<definition><datasource type="TANGO" name="spectrum_uchar">'
                '<record name="SpectrumUChar"/>'
                '<device member="attribute" name="ttestp09/testts/t24r228"/>'
                '</datasource></definition>'),
            'image_long': (
                '<definition><datasource type="TANGO" name="image_long">'
                '<record name="ImageLong"/>'
                '<device member="attribute" name="ttestp09/testts/t25r228"/>'
                '</datasource></definition>'),
            'image_bool': (
                '<definition><datasource type="TANGO" name="image_bool">'
                '<record name="ImageBoolean"/>'
                '<device member="attribute" name="ttestp09/testts/t26r228"/>'
                '</datasource></definition>'),
            'image_short': (
                '<definition><datasource type="TANGO" name="image_short">'
                '<record name="ImageShort"/>'
                '<device member="attribute" name="ttestp09/testts/t27r228"/>'
                '</datasource></definition>'),
            'image_ushort': (
                '<definition><datasource type="TANGO" name="image_ushort">'
                '<record name="ImageUShort"/>'
                '<device member="attribute" name="ttestp09/testts/t28r228"/>'
                '</datasource></definition>'),
            'image_ulong': (
                '<definition><datasource type="TANGO" name="image_ulong">'
                '<record name="ImageULong"/>'
                '<device member="attribute" name="ttestp09/testts/t29r228"/>'
                '</datasource></definition>'),
            'image_long64':
                ('<definition><datasource type="TANGO" name="image_long64">'
                 '<record name="ImageLong64"/>'
                 '<device member="attribute" name="ttestp09/testts/t30r228"/>'
                 '</datasource></definition>'),
            'image_ulong64':
                ('<definition><datasource type="TANGO" name="image_ulong64">'
                 '<record name="ImageULong64"/>'
                 '<device member="attribute" name="ttestp09/testts/t31r228"/>'
                 '</datasource></definition>'),
            'image_float':
                ('<definition><datasource type="TANGO" name="image_float">'
                 '<record name="ImageFloat"/>'
                 '<device member="attribute" name="ttestp09/testts/t32r228"/>'
                 '</datasource></definition>'),
            'image_double':
                ('<definition><datasource type="TANGO" name="image_double">'
                 '<record name="ImageDouble"/>'
                 '<device member="attribute" name="ttestp09/testts/t33r228"/>'
                 '</datasource></definition>'),
            'image_string':
                ('<definition><datasource type="TANGO" name="image_string">'
                 '<record name="ImageString"/>'
                 '<device member="attribute" name="ttestp09/testts/t34r228"/>'
                 '</datasource></definition>'),
            'image_Encoded':
                ('<definition><datasource type="TANGO" name="image_encoded">'
                 '<record name="ImageEncoded"/>'
                 '<device member="attribute" name="ttestp09/testts/t35r228"/>'
                 '</datasource></definition>'),
            'image_uchar':
                ('<definition><datasource type="TANGO" name="image_uchar">'
                 '<record name="ImageUChar"/>'
                 '<device member="attribute" name="ttestp09/testts/t36r228"/>'
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
            'scalar_Encoded': {
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
            'spectrum_Encoded': {
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
            'image_Encoded': {
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
            'scalar_long': {
                'data_type': 'int32',
                'plot_type': 1,
                'data_units': 'No unit',
                'shape': [],
                'plot_axes': ['<mov>'],
                'source': 'ttestp09/testts/t01r228/ScalarLong'},
            'scalar_bool': {
                'data_type': 'bool',
                'plot_type': 1,
                'data_units': 'No unit',
                'shape': [],
                'plot_axes': ['<mov>'],
                'source': 'ttestp09/testts/t02r228/ScalarBoolean'},
            'scalar_short': {
                'data_type': 'int16',
                'plot_type': 1,
                'data_units': 'No unit',
                'shape': [],
                'plot_axes': ['<mov>'],
                'source': 'ttestp09/testts/t03r228/ScalarShort'},
            'scalar_ushort': {
                'data_type': 'uint16',
                'plot_type': 1,
                'data_units': 'No unit',
                'shape': [],
                'plot_axes': ['<mov>'],
                'source': 'ttestp09/testts/t04r228/ScalarUShort'},
            'scalar_ulong': {
                'data_type': 'uint32',
                'plot_type': 1,
                'data_units': 'No unit',
                'shape': [],
                'plot_axes': ['<mov>'],
                'source': 'ttestp09/testts/t05r228/ScalarULong'},
            'scalar_long64': {
                'data_type': 'int64',
                'plot_type': 1,
                'data_units': 'No unit',
                'shape': [],
                'plot_axes': ['<mov>'],
                'source': 'ttestp09/testts/t06r228/ScalarLong64'},
            'scalar_ulong64': {
                'data_type': 'uint64',
                'plot_type': 1,
                'data_units': 'No unit',
                'shape': [],
                'plot_axes': ['<mov>'],
                'source': 'ttestp09/testts/t07r228/ScalarULong64'},
            'scalar_float': {
                'data_type': 'float32',
                'plot_type': 1,
                'data_units': 'No unit',
                'shape': [],
                'plot_axes': ['<mov>'],
                'source': 'ttestp09/testts/t08r228/ScalarFloat'},
            'scalar_double': {
                'data_type': 'float64',
                'plot_type': 1,
                'data_units': 'No unit',
                'shape': [],
                'plot_axes': ['<mov>'],
                'source': 'ttestp09/testts/t09r228/ScalarDouble'},
            'scalar_string': {
                'data_type': 'string',
                'plot_type': 1,
                'data_units': 'No unit',
                'shape': [],
                'plot_axes': ['<mov>'],
                'source': 'ttestp09/testts/t10r228/ScalarString'},
            'scalar_Encoded': {
                'data_type': 'encoded',
                'plot_type': 1,
                'data_units': 'No unit',
                'shape': [],
                'plot_axes': ['<mov>'],
                'source': 'ttestp09/testts/t11r228/ScalarEncoded'},
            'scalar_uchar': {
                'data_type': 'uint8',
                'plot_type': 1,
                'data_units': 'No unit',
                'shape': [],
                'plot_axes': ['<mov>'],
                'source': 'ttestp09/testts/t12r228/ScalarUChar'},
            'spectrum_long': {
                'data_type': 'int32',
                'plot_type': 1,
                'data_units': 'No unit',
                'shape': [4],
                'plot_axes': ['<idx>'],
                'source': 'ttestp09/testts/t13r228/SpectrumLong'},
            'spectrum_bool': {
                'data_type': 'bool',
                'plot_type': 1,
                'data_units': 'No unit',
                'shape': [2],
                'plot_axes': ['<idx>'],
                'source': 'ttestp09/testts/t14r228/SpectrumBoolean'},
            'spectrum_short': {
                'data_type': 'int16',
                'plot_type': 1,
                'data_units': 'No unit',
                'shape': [3],
                'plot_axes': ['<idx>'],
                'source': 'ttestp09/testts/t15r228/SpectrumShort'},
            'spectrum_ushort': {
                'data_type': 'uint16',
                'plot_type': 1,
                'data_units': 'No unit',
                'shape': [4],
                'plot_axes': ['<idx>'],
                'source': 'ttestp09/testts/t16r228/SpectrumUShort'},
            'spectrum_ulong': {
                'data_type': 'uint32',
                'plot_type': 1,
                'data_units': 'No unit',
                'shape': [4],
                'plot_axes': ['<idx>'],
                'source': 'ttestp09/testts/t17r228/SpectrumULong'},
            'spectrum_long64': {
                'data_type': 'int64',
                'plot_type': 1,
                'data_units': 'No unit',
                'shape': [4],
                'plot_axes': ['<idx>'],
                'source': 'ttestp09/testts/t18r228/SpectrumLong64'},
            'spectrum_ulong64': {
                'data_type': 'uint64',
                'plot_type': 1,
                'data_units': 'No unit',
                'shape': [4],
                'plot_axes': ['<idx>'],
                'source': 'ttestp09/testts/t19r228/SpectrumULong64'},
            'spectrum_float': {
                'data_type': 'float32',
                'plot_type': 1,
                'data_units': 'No unit',
                'shape': [4],
                'plot_axes': ['<idx>'],
                'source': 'ttestp09/testts/t20r228/SpectrumFloat'},
            'spectrum_double': {
                'data_type': 'float64',
                'plot_type': 1,
                'data_units': 'No unit',
                'shape': [4],
                'plot_axes': ['<idx>'],
                'source': 'ttestp09/testts/t21r228/SpectrumDouble'},
            'spectrum_string': {
                'data_type': 'string',
                'plot_type': 1,
                'data_units': 'No unit',
                'shape': [4],
                'plot_axes': ['<idx>'],
                'source': 'ttestp09/testts/t22r228/SpectrumString'},
            'spectrum_Encoded': {
                'data_type': 'encoded',
                'plot_type': 1,
                'data_units': 'No unit',
                'shape': [],
                'plot_axes': ['<mov>'],
                'source': 'ttestp09/testts/t23r228/SpectrumEncoded'},
            'spectrum_uchar': {
                'data_type': 'uint8',
                'plot_type': 1,
                'data_units': 'No unit',
                'shape': [2],
                'plot_axes': ['<idx>'],
                'source': 'ttestp09/testts/t24r228/SpectrumUChar'},

            'image_long': {
                'data_type': 'int32',
                'plot_type': 2,
                'data_units': 'No unit',
                'shape': [2, 2],
                'plot_axes': ['<idx>', '<idx>'],
                'source': 'ttestp09/testts/t25r228/ImageLong'},
            'image_bool': {
                'data_type': 'bool',
                'plot_type': 2,
                'data_units': 'No unit',
                'shape': [1, 1],
                'plot_axes': ['<idx>', '<idx>'],
                'source': 'ttestp09/testts/t26r228/ImageBoolean'},
            'image_short': {
                'data_type': 'int16',
                'plot_type': 2,
                'data_units': 'No unit',
                'shape': [2, 2],
                'plot_axes': ['<idx>', '<idx>'],
                'source': 'ttestp09/testts/t27r228/ImageShort'},
            'image_ushort': {
                'data_type': 'uint16',
                'plot_type': 2,
                'data_units': 'No unit',
                'shape': [2, 2],
                'plot_axes': ['<idx>', '<idx>'],
                'source': 'ttestp09/testts/t28r228/ImageUShort'},
            'image_ulong': {
                'data_type': 'uint32',
                'plot_type': 2,
                'data_units': 'No unit',
                'shape': [2, 2],
                'plot_axes': ['<idx>', '<idx>'],
                'source': 'ttestp09/testts/t29r228/ImageULong'},
            'image_long64': {
                'data_type': 'int64',
                'plot_type': 2,
                'data_units': 'No unit',
                'shape': [2, 2],
                'plot_axes': ['<idx>', '<idx>'],
                'source': 'ttestp09/testts/t30r228/ImageLong64'},
            'image_ulong64': {
                'data_type': 'uint64',
                'plot_type': 2,
                'data_units': 'No unit',
                'shape': [2, 2],
                'plot_axes': ['<idx>', '<idx>'],
                'source': 'ttestp09/testts/t31r228/ImageULong64'},
            'image_float': {
                'data_type': 'float32',
                'plot_type': 2,
                'data_units': 'No unit',
                'shape': [2, 2],
                'plot_axes': ['<idx>', '<idx>'],
                'source': 'ttestp09/testts/t32r228/ImageFloat'},
            'image_double': {
                'data_type': 'float64',
                'plot_type': 2,
                'data_units': 'No unit',
                'shape': [2, 2],
                'plot_axes': ['<idx>', '<idx>'],
                'source': 'ttestp09/testts/t33r228/ImageDouble'},
            'image_string': {
                'data_type': 'string',
                'plot_type': 2,
                'data_units': 'No unit',
                'shape': [1, 1],
                'plot_axes': ['<idx>', '<idx>'],
                'source': 'ttestp09/testts/t34r228/ImageString'},
            'image_Encoded': {
                'data_type': 'encoded',
                'plot_type': 1,
                'data_units': 'No unit',
                'shape': [],
                'plot_axes': ['<mov>'],
                'source': 'ttestp09/testts/t35r228/ImageEncoded'},
            'image_uchar': {
                'data_type': 'uint8',
                'plot_type': 2,
                'data_units': 'No unit',
                'shape': [2, 2],
                'plot_axes': ['<idx>', '<idx>'],
                'source': 'ttestp09/testts/t36r228/ImageUChar'},
            'client_long': {},
            'client_short': {},
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
            'scalar2_Encoded':
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
            'spectrum2_Encoded':
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
            'image2_Encoded':
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
#                print "CP", cp
                cres = self.rescps[cp]
                cresk = [ds for ds in cres.keys()
                         if self.dsfilter(cres[ds], strategy, dstype)]

                self.assertEqual(sorted(vl.keys()), sorted(cresk))
                for ds in cresk:
#                    print "C1", sorted(cres[ds])
#                    print "C2", sorted(vl[ds])
                    self.assertEqual(
                        sorted(self.dsfilter(cres[ds], strategy, dstype)),
                        sorted(vl[ds]))

    def dump(self, el):
        self.__dump = {}
        for key in el.keys():
            self.__dump[key] = el[key]

    def compareToDump(self, el, excluded=None):
        exc = set(excluded or [])
        dks = set(self.__dump.keys()) - exc
        eks = set(el.keys()) - exc
#        print "SE4", el["TimeZone"]
        self.assertEqual(dks, eks)
        for key in dks:
            self.assertEqual(self.__dump[key], el[key])

    def compareToDumpJSON(self, el, excluded=None):
        exc = set(excluded or [])
        dks = set(self.__dump.keys()) - exc
        eks = set(el.keys()) - exc
        self.assertEqual(dks, eks)
        for key in dks:
            try:
                w1 = json.loads(self.__dump[key])
                w2 = json.loads(el[key])
            except:
                self.assertEqual(self.__dump[key], el[key])
            else:
                if isinstance(w1, dict):
                    self.myAssertDict(w1, w2)
                else:
                    self.assertEqual(self.__dump[key], el[key])

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

    ## constructor test
    def test_constructor_keys(self):
        fun = sys._getframe().f_code.co_name
        print "Run: %s.%s() " % (self.__class__.__name__, fun)
        val = {"ConfigDevice": self._cf.dp.name(),
               "WriterDevice": self._wr.dp.name(),
               "Door": 'doortestp09/testts/t1r228',
               "MntGrp": 'nxsmntgrp'}

        mgt = ProfileManager(None)

        se = Selector(None)
        mgt = ProfileManager(se)

        msp = MacroServerPools(10)
        se = Selector(msp)
        mgt = ProfileManager(se)

    ## availableMntGrps test
    def test_availableMntGrps(self):
        fun = sys._getframe().f_code.co_name
        print "Run: %s.%s() " % (self.__class__.__name__, fun)
        val = {"ConfigDevice": self._cf.dp.name(),
               "WriterDevice": self._wr.dp.name(),
               "Door": 'doortestp09/testts/t1r228',
               "MntGrp": 'nxsmntgrp'}

        mgt = ProfileManager(None)
        self.myAssertRaise(Exception, mgt.availableMntGrps)

        se = Selector(None)
        mgt = ProfileManager(se)
        self.myAssertRaise(Exception, mgt.availableMntGrps)

        msp = MacroServerPools(10)
        se = Selector(msp)
        se["Door"] = val["Door"]
        mgt = ProfileManager(se)
        self.assertEqual(mgt.availableMntGrps(), [])

        db = PyTango.Database()
        db.put_device_property(self._ms.ms.keys()[0],
                               {'PoolNames': self._pool.dp.name()})
        pool = self._pool.dp
        self._ms.dps[self._ms.ms.keys()[0]].Init()

        self.assertEqual(mgt.availableMntGrps(), [])

        arr = [
            {"name":"test/ct/01", "full_name":"mntgrp_01e"},
            {"name":"test/ct/02", "full_name":"mntgrp_02att"},
            {"name":"test/ct/03", "full_name":"mntgrp_03value"},
            {"name":"test/ct/04", "full_name":"mntgrp_04/13"},
            {"name":"null", "full_name":"mntgrp_04"},
            ]

        pool.MeasurementGroupList = [json.dumps(a) for a in arr]

        dd = mgt.availableMntGrps()
        self.assertEqual(set(dd), set([a["name"] for a in arr]))

        for ar in arr:

            MSUtils.setEnv('ActiveMntGrp', ar["name"],
                           self._ms.ms.keys()[0])
            print MSUtils.getEnv('ActiveMntGrp', self._ms.ms.keys()[0])
            dd = mgt.availableMntGrps()
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

        mgt = ProfileManager(None)
        self.myAssertRaise(Exception, mgt.availableMntGrps)

        se = Selector(None)
        mgt = ProfileManager(se)
        self.myAssertRaise(Exception, mgt.availableMntGrps)

        msp = MacroServerPools(10)
        se = Selector(msp)
        se["Door"] = val["Door"]
        mgt = ProfileManager(se)
        self.assertEqual(mgt.availableMntGrps(), [])

        try:
            tpool2 = TestPoolSetUp.TestPoolSetUp(
                "pooltestp09/testts/t2r228", "POOLTESTS2")
            tpool2.setUp()

            db = PyTango.Database()
            db.put_device_property(self._ms.ms.keys()[0],
                                   {'PoolNames': [
                        tpool2.dp.name(), self._pool.dp.name()]})
            pool = self._pool.dp
            pool2 = tpool2.dp
            self._ms.dps[self._ms.ms.keys()[0]].Init()

            self.assertEqual(mgt.availableMntGrps(), [])
            arr1 = [
                {"name":"test/ct/01", "full_name":"mntgrp_01e"},
                {"name":"test/ct/02", "full_name":"mntgrp_02att"},
                {"name":"test/ct/03", "full_name":"mntgrp_03value"},
                {"name":"test/ct/04", "full_name":"mntgrp_04/13"},
                {"name":"null", "full_name":"mntgrp_04"},
                ]

            arr2 = [
                {"name":"test/ct/011", "full_name":"mntgrp_01e1"},
                {"name":"test/ct/021", "full_name":"mntgrp_02att1"},
                {"name":"test/ct/031", "full_name":"mntgrp_03value1"},
                {"name":"test/ct/041", "full_name":"mntgrp_04/131"},
                {"name":"null", "full_name":"mntgrp_041"},
                ]

            pool.MeasurementGroupList = [json.dumps(a) for a in arr1]
            pool2.MeasurementGroupList = [json.dumps(a) for a in arr2]

            if se.getPools()[0].name() == "pooltestp09/testts/t2r228":
                arr = arr2
            else:
                arr = arr1

            dd = mgt.availableMntGrps()
            self.assertEqual(set(dd), set([a["name"] for a in arr]))

            for ar in arr1:

                MSUtils.setEnv('ActiveMntGrp', ar["name"],
                               self._ms.ms.keys()[0])
                dd = mgt.availableMntGrps()
                self.assertEqual(dd[0], ar["name"])
                if arr1 == arr or ar["name"] != 'null':
                    self.assertEqual(set(dd), set([a["name"] for a in arr1]))
                else:
                    self.assertEqual(set(dd), set([a["name"] for a in arr]))

            for ar in arr2:
                MSUtils.setEnv('ActiveMntGrp', ar["name"],
                               self._ms.ms.keys()[0])
                dd = mgt.availableMntGrps()
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

        mgt = ProfileManager(None)
        self.myAssertRaise(Exception, mgt.deleteProfile)

        se = Selector(None)
        mgt = ProfileManager(se)
        self.myAssertRaise(Exception, mgt.deleteProfile, None)

        msp = MacroServerPools(10)
        se = Selector(msp)
        se["Door"] = val["Door"]
        se["ConfigDevice"] = val["ConfigDevice"]
        mgt = ProfileManager(se)
        self.assertEqual(mgt.availableMntGrps(), [])

        db = PyTango.Database()
        db.put_device_property(self._ms.ms.keys()[0],
                               {'PoolNames': self._pool.dp.name()})
        pool = self._pool.dp
        self._ms.dps[self._ms.ms.keys()[0]].Init()

        self.assertEqual(mgt.availableMntGrps(), [])

        arr = [
            {"full_name":"test/ct/01", "name":"mntgrp_01e"},
            {"full_name":"test/ct/02", "name":"mntgrp_02att"},
            {"full_name":"test/ct/03", "name":"mntgrp_03value"},
            {"full_name":"test/ct/04", "name":"mntgrp_04_13"},
            {"full_name":"null", "name":"mntgrp_04"},
            ]

        pool.MeasurementGroupList = [json.dumps(a) for a in arr]

        dd2 = mgt.availableMntGrps()
        self.assertEqual(set(dd2), set([a["name"] for a in arr]))

        self._cf.dp.Init()
        self._cf.dp.SetCommandVariable(["SELDICT", json.dumps(self.mysel2)])
        sl2 = self._cf.dp.availableSelections()

        dl = []
        mgs = [ar["name"] for ar in arr] + self.mysel2.keys()
        print mgs
        for ar in mgs:
            MSUtils.setEnv('ActiveMntGrp', ar, self._ms.ms.keys()[0])
            mgt.deleteProfile(ar)
            dl.append(ar)
            self.assertEqual(MSUtils.getEnv(
                    'ActiveMntGrp', self._ms.ms.keys()[0]), "")
            dd = mgt.availableMntGrps()
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

        mgt = ProfileManager(None)
        self.myAssertRaise(Exception, mgt.availableMntGrps)

        se = Selector(None)
        mgt = ProfileManager(se)
        self.myAssertRaise(Exception, mgt.availableMntGrps)

        msp = MacroServerPools(10)
        se = Selector(msp)
        se["Door"] = val["Door"]
        se["ConfigDevice"] = val["ConfigDevice"]
        mgt = ProfileManager(se)
        self.assertEqual(mgt.availableMntGrps(), [])

        try:
            tpool2 = TestPoolSetUp.TestPoolSetUp(
                "pooltestp09/testts/t2r228", "POOLTESTS2")
            tpool2.setUp()

            db = PyTango.Database()
            db.put_device_property(self._ms.ms.keys()[0],
                                   {'PoolNames': [
                        tpool2.dp.name(), self._pool.dp.name()]})
            pool = self._pool.dp
            pool2 = tpool2.dp
            self._ms.dps[self._ms.ms.keys()[0]].Init()

            self.assertEqual(mgt.availableMntGrps(), [])

            arr = [
                {"full_name":"test/ct/01", "name":"mntgrp_01e"},
                {"full_name":"test/ct/02", "name":"mntgrp_02att"},
                {"full_name":"test/ct/03", "name":"mntgrp_03value"},
                {"full_name":"test/ct/04", "name":"mntgrp_04_13"},
                {"full_name":"null", "name":"mntgrp_04"},
                ]

            arr2 = [
                {"full_name":"test/ct/011", "name":"mntgrp_01e1"},
                {"full_name":"test/ct/021", "name":"mntgrp_02att"},
                {"full_name":"test/ct/031", "name":"mntgrp_03value1"},
                {"full_name":"test/ct/041", "name":"mntgrp_04/131"},
                {"full_name":"null", "name":"mntgrp_04"},
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
                mgt.deleteProfile(ar)
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
                mgt.deleteProfile(ar)
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

    ## updateProfile test
    def test_automaticComponents(self):
        fun = sys._getframe().f_code.co_name
        print "Run: %s.%s() " % (self.__class__.__name__, fun)
        val = {"ConfigDevice": self._cf.dp.name(),
               "WriterDevice": self._wr.dp.name(),
               "Door": 'doortestp09/testts/t1r228',
               "MntGrp": 'nxsmntgrp'}

        for i in range(20):
            msp = MacroServerPools(10)
            se = Selector(msp)
            se["Door"] = val["Door"]
            se["ConfigDevice"] = val["ConfigDevice"]
            se["WriterDevice"] = val["WriterDevice"]
            pm = ProfileManager(se)

            cps = {}
            lcp = self.__rnd.randint(1, 40)
            for i in range(lcp):
                cps[self.getRandomName(10)] = bool(self.__rnd.randint(0, 1))
            se["AutomaticComponentGroup"] = json.dumps(cps)

            self.dump(se)

            ac = pm.automaticComponents()
            self.compareToDump(se, ["AutomaticComponentGroup"])
            ndss = json.loads(se["AutomaticComponentGroup"])

            acp = []
            for ds in cps.keys():
                self.assertTrue(ds in ndss.keys())
                self.assertEqual(ndss[ds], cps[ds])
                if ndss[ds]:
                    acp.append(ds)

            self.assertEqual(set(ac), set(acp))

    ## updateProfile test
    def test_components(self):
        fun = sys._getframe().f_code.co_name
        print "Run: %s.%s() " % (self.__class__.__name__, fun)
        val = {"ConfigDevice": self._cf.dp.name(),
               "WriterDevice": self._wr.dp.name(),
               "Door": 'doortestp09/testts/t1r228',
               "MntGrp": 'nxsmntgrp'}

        for i in range(20):
            msp = MacroServerPools(10)
            se = Selector(msp)
            se["Door"] = val["Door"]
            se["OrderedChannels"] = json.dumps([])
            db = PyTango.Database()
            db.put_device_property(self._ms.ms.keys()[0],
                                   {'PoolNames': self._pool.dp.name()})
            pool = self._pool.dp
            pool.ExpChannelList = []
            self._ms.dps[self._ms.ms.keys()[0]].Init()

            se["Door"] = val["Door"]
            se["ConfigDevice"] = val["ConfigDevice"]
            se["WriterDevice"] = val["WriterDevice"]
            pm = ProfileManager(se)

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

            se["ComponentGroup"] = json.dumps(cps)
            se["DataSourceGroup"] = json.dumps(dss)
            ndss = json.loads(se["DataSourceGroup"])
            common = set(cps) & set(dss)
            self.dump(se)

            ncps = json.loads(se["ComponentGroup"])
            ndss = json.loads(se["DataSourceGroup"])
            tdss = [ds for ds in ndss if ndss[ds]]
            tcps = [cp for cp in ncps if ncps[cp]]

            pmcp = pm.components()
            self.assertEqual(len(cps), len(ncps) + len(common))
            for key in cps.keys():
                if key not in common:
                    self.assertTrue(key in ncps.keys())
                    self.assertEqual(ncps[key], cps[key])
            self.compareToDumpJSON(se, ["ComponentGroup"])
            ac = self._cf.dp.availableComponents()
            for cp in pmcp:
                self.assertTrue(cp in ac)
            mfcp = set(tcps) | (set(tdss) & set(ac))
            self.assertEqual(set(pmcp), set(mfcp))

    ## updateProfile test
    def test_cpdescritpion_unknown(self):
        fun = sys._getframe().f_code.co_name
        print "Run: %s.%s() " % (self.__class__.__name__, fun)
        val = {"ConfigDevice": self._cf.dp.name(),
               "WriterDevice": self._wr.dp.name(),
               "Door": 'doortestp09/testts/t1r228',
               "MntGrp": 'nxsmntgrp'}

        msp = MacroServerPools(10)
        se = Selector(msp)
        se["Door"] = val["Door"]
        se["OrderedChannels"] = json.dumps([])
        db = PyTango.Database()
        db.put_device_property(self._ms.ms.keys()[0],
                               {'PoolNames': self._pool.dp.name()})
        pool = self._pool.dp
        pool.ExpChannelList = []
        self._ms.dps[self._ms.ms.keys()[0]].Init()

        se["Door"] = val["Door"]
        se["ConfigDevice"] = val["ConfigDevice"]
        se["WriterDevice"] = val["WriterDevice"]
        pm = ProfileManager(se)

        cps = {}
        dss = {}
        lcp = self.__rnd.randint(1, 40)
        lds = self.__rnd.randint(1, 40)

        dsdict = {
            "ann": self.mydss["ann"]
            }

        self._cf.dp.SetCommandVariable(["CPDICT", json.dumps({})])
        self._cf.dp.SetCommandVariable(["DSDICT", json.dumps(dsdict)])

        se["ComponentGroup"] = json.dumps(cps)
        se["DataSourceGroup"] = json.dumps(dss)
        ndss = json.loads(se["DataSourceGroup"])
        common = set(cps) & set(dss)
        self.dump(se)

        ncps = json.loads(se["ComponentGroup"])
        ndss = json.loads(se["DataSourceGroup"])
        tdss = [ds for ds in ndss if ndss[ds]]
        tcps = [cp for cp in ncps if ncps[cp]]

        self.assertEqual(pm.cpdescription(), [{}])
        se["ComponentGroup"] = json.dumps({"unknown": True})
        self.assertEqual(pm.cpdescription(), [{}])
        se["DataSourceGroup"] = json.dumps({"unknown": True})
        self.assertEqual(pm.cpdescription(), [{}])
        self._cf.dp.SetCommandVariable(["MCPLIST", json.dumps(["unknown"])])
        self.assertEqual(pm.cpdescription(), [{}])

    ## updateProfile test
    def test_cpdescritpion_full(self):
        fun = sys._getframe().f_code.co_name
        print "Run: %s.%s() " % (self.__class__.__name__, fun)
        val = {"ConfigDevice": self._cf.dp.name(),
               "WriterDevice": self._wr.dp.name(),
               "Door": 'doortestp09/testts/t1r228',
               "MntGrp": 'nxsmntgrp'}

        msp = MacroServerPools(10)
        se = Selector(msp)
        se["Door"] = val["Door"]
        se["OrderedChannels"] = json.dumps([])
        db = PyTango.Database()
        db.put_device_property(self._ms.ms.keys()[0],
                               {'PoolNames': self._pool.dp.name()})
        pool = self._pool.dp
        pool.ExpChannelList = []
        self._ms.dps[self._ms.ms.keys()[0]].Init()

        se["Door"] = val["Door"]
        se["ConfigDevice"] = val["ConfigDevice"]
        se["WriterDevice"] = val["WriterDevice"]
        pm = ProfileManager(se)

        cps = {}
        dss = {}
        lcp = self.__rnd.randint(1, 40)
        lds = self.__rnd.randint(1, 40)

        dsdict = {
            "ann": self.mydss["ann"]
            }

        self._cf.dp.SetCommandVariable(["CPDICT", json.dumps(self.mycps)])
        self._cf.dp.SetCommandVariable(["DSDICT", json.dumps(self.mydss)])

        se["ComponentGroup"] = json.dumps({})
        se["DataSourceGroup"] = json.dumps({})
        ndss = json.loads(se["DataSourceGroup"])
        common = set(cps) & set(dss)
        self.dump(se)

        res = pm.cpdescription(True)
        self.checkCP(res, self.rescps.keys())

    ## updateProfile test
    def test_cpdescritpion_comp_nods(self):
        fun = sys._getframe().f_code.co_name
        print "Run: %s.%s() " % (self.__class__.__name__, fun)
        val = {"ConfigDevice": self._cf.dp.name(),
               "WriterDevice": self._wr.dp.name(),
               "Door": 'doortestp09/testts/t1r228',
               "MntGrp": 'nxsmntgrp'}

        for i in range(20):
            msp = MacroServerPools(10)
            se = Selector(msp)
            se["Door"] = val["Door"]
            se["OrderedChannels"] = json.dumps([])
            db = PyTango.Database()
            db.put_device_property(self._ms.ms.keys()[0],
                                   {'PoolNames': self._pool.dp.name()})
            pool = self._pool.dp
            pool.ExpChannelList = []
            self._ms.dps[self._ms.ms.keys()[0]].Init()

            se["Door"] = val["Door"]
            se["ConfigDevice"] = val["ConfigDevice"]
            se["WriterDevice"] = val["WriterDevice"]
            pm = ProfileManager(se)

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

            se["ComponentGroup"] = json.dumps(cps)
            se["DataSourceGroup"] = json.dumps(dss)
            self._cf.dp.SetCommandVariable(["MCPLIST", json.dumps(mcps)])
            ndss = json.loads(se["DataSourceGroup"])
            common = set(cps) & set(dss)
            self.dump(se)

            res = pm.cpdescription()
            self.checkCP(res, list(set(tcps) | set(tdss) | set(mcps)),
                         strategy='STEP')

    ## updateProfile test
    def test_cpdescritpion_comp_ds(self):
        fun = sys._getframe().f_code.co_name
        print "Run: %s.%s() " % (self.__class__.__name__, fun)
        val = {"ConfigDevice": self._cf.dp.name(),
               "WriterDevice": self._wr.dp.name(),
               "Door": 'doortestp09/testts/t1r228',
               "MntGrp": 'nxsmntgrp'}

        for i in range(20):
            msp = MacroServerPools(10)
            se = Selector(msp)
            se["Door"] = val["Door"]
            se["OrderedChannels"] = json.dumps([])
            db = PyTango.Database()
            db.put_device_property(self._ms.ms.keys()[0],
                                   {'PoolNames': self._pool.dp.name()})
            pool = self._pool.dp
            pool.ExpChannelList = []
            self._ms.dps[self._ms.ms.keys()[0]].Init()

            se["Door"] = val["Door"]
            se["ConfigDevice"] = val["ConfigDevice"]
            se["WriterDevice"] = val["WriterDevice"]
            pm = ProfileManager(se)

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

            se["ComponentGroup"] = json.dumps(cps)
            se["DataSourceGroup"] = json.dumps(dss)
            self._cf.dp.SetCommandVariable(["MCPLIST", json.dumps(mcps)])
            ndss = json.loads(se["DataSourceGroup"])
            common = set(cps) & set(dss)
            self.dump(se)

            res = pm.cpdescription()
            self.checkCP(res, list(set(tcps) | set(tdss) | set(mcps)),
                         strategy='STEP')

    ## updateProfile test
    def test_disabledatasources(self):
        fun = sys._getframe().f_code.co_name
        print "Run: %s.%s() " % (self.__class__.__name__, fun)
        val = {"ConfigDevice": self._cf.dp.name(),
               "WriterDevice": self._wr.dp.name(),
               "Door": 'doortestp09/testts/t1r228',
               "MntGrp": 'nxsmntgrp'}

        for i in range(20):
            msp = MacroServerPools(10)
            se = Selector(msp)
            se["Door"] = val["Door"]
            se["OrderedChannels"] = json.dumps([])
            db = PyTango.Database()
            db.put_device_property(self._ms.ms.keys()[0],
                                   {'PoolNames': self._pool.dp.name()})
            pool = self._pool.dp
            pool.ExpChannelList = []
            self._ms.dps[self._ms.ms.keys()[0]].Init()

            se["Door"] = val["Door"]
            se["ConfigDevice"] = val["ConfigDevice"]
            se["WriterDevice"] = val["WriterDevice"]
            pm = ProfileManager(se)

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

            se["ComponentGroup"] = json.dumps(cps)
            se["DataSourceGroup"] = json.dumps(dss)
            self._cf.dp.SetCommandVariable(["MCPLIST", json.dumps(mcps)])
            ndss = json.loads(se["DataSourceGroup"])
            common = set(cps) & set(dss)
            self.dump(se)

            dds = pm.disableDataSources()
            res = pm.cpdescription()

            mdds = set()
            for mdss in res[0].values():
                if isinstance(mdss, dict):
                    for ds in mdss.keys():
                        mdds.add(ds)
            self.assertEqual(mdds, set(dds))
            self.assertEqual(len(mdds), len(dds))

    ## updateProfile test
    def test_datasources(self):
        fun = sys._getframe().f_code.co_name
        print "Run: %s.%s() " % (self.__class__.__name__, fun)
        val = {"ConfigDevice": self._cf.dp.name(),
               "WriterDevice": self._wr.dp.name(),
               "Door": 'doortestp09/testts/t1r228',
               "MntGrp": 'nxsmntgrp'}

        for i in range(20):
            msp = MacroServerPools(10)
            se = Selector(msp)
            se["Door"] = val["Door"]
            se["OrderedChannels"] = json.dumps([])
            db = PyTango.Database()
            db.put_device_property(self._ms.ms.keys()[0],
                                   {'PoolNames': self._pool.dp.name()})
            pool = self._pool.dp
            pool.ExpChannelList = []
            self._ms.dps[self._ms.ms.keys()[0]].Init()

            se["Door"] = val["Door"]
            se["ConfigDevice"] = val["ConfigDevice"]
            se["WriterDevice"] = val["WriterDevice"]
            pm = ProfileManager(se)

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

            se["ComponentGroup"] = json.dumps(cps)
            se["DataSourceGroup"] = json.dumps(dss)
            self._cf.dp.SetCommandVariable(["MCPLIST", json.dumps(mcps)])
            ndss = json.loads(se["DataSourceGroup"])
            common = set(cps) & set(dss)
            self.dump(se)

            dds = pm.disableDataSources()
            rdss = pm.dataSources()
            tdss = [ds for ds in dss if dss[ds] and ds not in dds]

            self.assertEqual(set(tdss), set(rdss))
            self.assertEqual(len(tdss), len(rdss))

    ## updateProfile test
    def test_updateProfile_empty(self):
        fun = sys._getframe().f_code.co_name
        print "Run: %s.%s() " % (self.__class__.__name__, fun)
        val = {"ConfigDevice": self._cf.dp.name(),
               "WriterDevice": self._wr.dp.name(),
               "Door": 'doortestp09/testts/t1r228',
               "MntGrp": 'nxsmntgrp'}

        mgt = ProfileManager(None)
        self.myAssertRaise(Exception, mgt.updateProfile)

        se = Selector(None)
        mgt = ProfileManager(se)
        self.myAssertRaise(Exception, mgt.updateProfile)

        msp = MacroServerPools(10)
        se = Selector(msp)
        se["Door"] = val["Door"]
        se["ConfigDevice"] = val["ConfigDevice"]
        se["WriterDevice"] = val["WriterDevice"]
        mgt = ProfileManager(se)
        self.assertEqual(mgt.availableMntGrps(), [])
        self.myAssertRaise(Exception, mgt.updateProfile)

        db = PyTango.Database()
        db.put_device_property(self._ms.ms.keys()[0],
                               {'PoolNames': self._pool.dp.name()})
        pool = self._pool.dp
        self._ms.dps[self._ms.ms.keys()[0]].Init()

        self.assertEqual(mgt.availableMntGrps(), [])

        arr = [
            {"full_name":"test/ct/01/Value", "name":"ct01"},
            {"full_name":"test/ct/02/Value", "name":"ct02"},
            {"full_name":"test/ct/03/value", "name":"ct03"},
            {"full_name":"test/ct/04/value", "name":"ct04"},
            {"full_name":"null/val", "name":"mntgrp_04"},
            ]
        pool.AcqChannelList = [json.dumps(a) for a in arr]

        self.myAssertRaise(Exception, mgt.updateProfile)
        for ar in arr:

            se["Timer"] = '["%s"]' % ar["name"]

            tmg = TestMGSetUp.TestMeasurementGroupSetUp(name='nxsmntgrp')
            dv = "/".join(ar["full_name"].split("/")[0:-1])
            smg = {"controllers": {},
                   "monitor": "%s" % dv,
                   "description": "Measurement Group",
                   "timer": "%s" % dv,
                   "label": "nxsmntgrp"}
            try:
                self.assertEqual(json.loads(se["AutomaticComponentGroup"]), {})
                self.assertEqual(json.loads(se["ComponentGroup"]), {})
                self.assertEqual(json.loads(se["DataSourceGroup"]), {})
                self.assertEqual(json.loads(se["HiddenElements"]), [])
                self.assertEqual(json.loads(se["OrderedChannels"]), [])
                self.assertEqual(json.loads(se["DataRecord"]), {})
                self.assertEqual(json.loads(se["Timer"]), [ar["name"]])
                self.assertEqual(se["MntGrp"], "nxsmntgrp")
                jpcnf = mgt.updateProfile()
                pcnf = json.loads(jpcnf)
                mgdp = PyTango.DeviceProxy(tmg.new_device_info_writer.name)
                jcnf = mgdp.Configuration
                cnf = json.loads(jcnf)
                self.assertEqual(json.loads(se["AutomaticComponentGroup"]), {})
                self.assertEqual(json.loads(se["ComponentGroup"]), {})
                self.assertEqual(json.loads(se["DataSourceGroup"]), {})
                self.assertEqual(json.loads(se["HiddenElements"]), [])
                self.assertEqual(json.loads(se["OrderedChannels"]), [])
                self.assertEqual(json.loads(se["DataRecord"]), {})
                self.assertEqual(json.loads(se["Timer"]), [ar["name"]])
                self.assertEqual(se["MntGrp"], "nxsmntgrp")
                self.myAssertDict(smg, cnf)
                self.myAssertDict(smg, pcnf)
                se.reset()
                se["Door"] = val["Door"]
                se["ConfigDevice"] = val["ConfigDevice"]
                se["MntGrp"] = "nxsmntgrp"
                se.fetchSelection()
                self.assertEqual(json.loads(se["AutomaticComponentGroup"]), {})
                self.assertEqual(json.loads(se["ComponentGroup"]), {})
                self.assertEqual(json.loads(se["DataSourceGroup"]), {})
                self.assertEqual(json.loads(se["HiddenElements"]), [])
                self.assertEqual(json.loads(se["OrderedChannels"]), [])
                self.assertEqual(json.loads(se["DataRecord"]), {})
                self.assertEqual(json.loads(se["Timer"]), [ar["name"]])
                self.assertEqual(se["MntGrp"], "nxsmntgrp")
            finally:
                mgt.deleteProfile("nxsmntgrp")
                tmg.tearDown()

    ## updateProfile test
    def test_updateProfile_components_nopool(self):
        fun = sys._getframe().f_code.co_name
        print "Run: %s.%s() " % (self.__class__.__name__, fun)
        val = {"ConfigDevice": self._cf.dp.name(),
               "WriterDevice": self._wr.dp.name(),
               "Door": 'doortestp09/testts/t1r228',
               "MntGrp": 'nxsmntgrp'}

        wrong = ['nn', 'ann', 'nn2',  'tann1', 'tann0', 'tann1b', 'tann1c',
                 'dim1', 'dim2', 'dim3', 'dim4', 'dim5', 'dim5', 'dim6',
                 'dim7', 'dim8', 'tann1c', 'mycp3']

        mgt = ProfileManager(None)
        self.myAssertRaise(Exception, mgt.updateProfile)

        se = Selector(None)
        mgt = ProfileManager(se)
        self.myAssertRaise(Exception, mgt.updateProfile)

        msp = MacroServerPools(10)
        se = Selector(msp)
        se["Door"] = val["Door"]
        se["ConfigDevice"] = val["ConfigDevice"]
        mgt = ProfileManager(se)
        self.assertEqual(mgt.availableMntGrps(), [])
        self.myAssertRaise(Exception, mgt.updateProfile)

        db = PyTango.Database()
        db.put_device_property(self._ms.ms.keys()[0],
                               {'PoolNames': self._pool.dp.name()})
        pool = self._pool.dp
        self._ms.dps[self._ms.ms.keys()[0]].Init()

        self.assertEqual(mgt.availableMntGrps(), [])

        arr = [
            {"full_name":"test/ct/01/Value", "name":"ct01"},
            {"full_name":"test/ct/02/Value", "name":"ct02"},
            {"full_name":"test/ct/03/value", "name":"ct03"},
            {"full_name":"test/ct/04/value", "name":"ct04"},
            {"full_name":"null/val", "name":"mntgrp_04"},
            ]
        pool.AcqChannelList = [json.dumps(a) for a in arr]

        self.myAssertRaise(Exception, mgt.updateProfile)
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

            se["ComponentGroup"] = json.dumps(cps)
            se["AutomaticComponentGroup"] = json.dumps(acps)
            se["DataSourceGroup"] = json.dumps(dss)
            self._cf.dp.SetCommandVariable(["MCPLIST", json.dumps(mcps)])

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

            se["Timer"] = '["%s"]' % ar["name"]
            se["DataRecord"] = json.dumps(records)

            tmg = TestMGSetUp.TestMeasurementGroupSetUp(name='nxsmntgrp')
            dv = "/".join(ar["full_name"].split("/")[0:-1])
            smg = {"controllers": {},
                   "monitor": "%s" % dv,
                   "description": "Measurement Group",
                   "timer": "%s" % dv,
                   "label": "nxsmntgrp"}
            try:
                self.myAssertDict(json.loads(se["AutomaticComponentGroup"]),
                                  acps)
                self.myAssertDict(json.loads(se["ComponentGroup"]), cps)
                self.myAssertDict(json.loads(se["DataSourceGroup"]), dss)
                self.assertEqual(json.loads(se["HiddenElements"]), [])
                self.assertEqual(json.loads(se["OrderedChannels"]), [])
                self.myAssertDict(json.loads(se["DataRecord"]), records)
                self.assertEqual(json.loads(se["Timer"]), [ar["name"]])
                self.assertEqual(se["MntGrp"], "nxsmntgrp")
                print "COMP", mgt.components()
                print "ACOMP", mgt.automaticComponents()
                print "MCP", mcps
                print "DS", mgt.dataSources()
                print "DDS", mgt.disableDataSources()
                jpcnf = mgt.updateProfile()
                pcnf = json.loads(jpcnf)
                mgdp = PyTango.DeviceProxy(tmg.new_device_info_writer.name)
                jcnf = mgdp.Configuration
                cnf = json.loads(jcnf)
                self.myAssertDict(json.loads(se["AutomaticComponentGroup"]),
                                  acps)
                self.myAssertDict(json.loads(se["ComponentGroup"]), cps)
                self.myAssertDict(json.loads(se["DataSourceGroup"]), dss)
                self.assertEqual(json.loads(se["HiddenElements"]), [])
                self.assertEqual(json.loads(se["OrderedChannels"]), [])
                self.myAssertDict(json.loads(se["DataRecord"]), records)
                self.assertEqual(json.loads(se["Timer"]), [ar["name"]])
                self.assertEqual(se["MntGrp"], "nxsmntgrp")
                self.myAssertDict(smg, cnf)
                self.myAssertDict(smg, pcnf)
                se.reset()
                se["Door"] = val["Door"]
                se["ConfigDevice"] = val["ConfigDevice"]
                se["MntGrp"] = "nxsmntgrp"
                se.fetchSelection()
                self.myAssertDict(json.loads(se["AutomaticComponentGroup"]),
                                  acps)
                self.myAssertDict(json.loads(se["ComponentGroup"]), cps)
                self.myAssertDict(json.loads(se["DataSourceGroup"]), dss)
                self.assertEqual(json.loads(se["HiddenElements"]), [])
                self.assertEqual(json.loads(se["OrderedChannels"]), [])
                self.myAssertDict(json.loads(se["DataRecord"]), records)
                self.assertEqual(json.loads(se["Timer"]), [ar["name"]])
                self.assertEqual(se["MntGrp"], "nxsmntgrp")
            finally:
                mgt.deleteProfile("nxsmntgrp")
                try:
                    tmg.tearDown()
                except:
                    pass

    ## updateProfile test
    def test_updateProfile_nodevice(self):
        fun = sys._getframe().f_code.co_name
        print "Run: %s.%s() " % (self.__class__.__name__, fun)
        val = {"ConfigDevice": self._cf.dp.name(),
               "WriterDevice": self._wr.dp.name(),
               "Door": 'doortestp09/testts/t1r228',
               "MntGrp": 'nxsmntgrp'}

        wrong = ['nn', 'ann', 'nn2', 'tann1b', 'tann1c',
                 'dim1', 'dim2', 'dim3', 'dim4', 'dim5', 'dim5', 'dim6',
                 'dim7', 'dim8', 'tann1c']
        mgt = ProfileManager(None)
        self.myAssertRaise(Exception, mgt.updateProfile)

        se = Selector(None)
        mgt = ProfileManager(se)
        self.myAssertRaise(Exception, mgt.updateProfile)

        msp = MacroServerPools(10)
        se = Selector(msp)
        se["Door"] = val["Door"]
        se["ConfigDevice"] = val["ConfigDevice"]
        mgt = ProfileManager(se)
        self.assertEqual(mgt.availableMntGrps(), [])
        self.myAssertRaise(Exception, mgt.updateProfile)

        db = PyTango.Database()
        db.put_device_property(self._ms.ms.keys()[0],
                               {'PoolNames': self._pool.dp.name()})
        pool = self._pool.dp
        self._ms.dps[self._ms.ms.keys()[0]].Init()

        self.assertEqual(mgt.availableMntGrps(), [])

        arr = [
            {"full_name":"test/ct/01/Value", "name":"ct01"},
            {"full_name":"test/ct/02/Value", "name":"ct02"},
            {"full_name":"test/ct/03/value", "name":"ct03"},
            {"full_name":"test/ct/04/value", "name":"ct04"},
            {"full_name":"null/val", "name":"mntgrp_04"},
            ]
        pool.AcqChannelList = [json.dumps(a) for a in arr]

        self.myAssertRaise(Exception, mgt.updateProfile)
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

            se["ComponentGroup"] = json.dumps(cps)
            se["AutomaticComponentGroup"] = json.dumps(acps)
            se["DataSourceGroup"] = json.dumps(dss)
            self._cf.dp.SetCommandVariable(["MCPLIST", json.dumps(mcps)])

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

            se["Timer"] = '["%s"]' % ar["name"]
            se["DataRecord"] = json.dumps(records)

            tmg = TestMGSetUp.TestMeasurementGroupSetUp(name='nxsmntgrp')
            dv = "/".join(ar["full_name"].split("/")[0:-1])
            smg = {"controllers": {},
                   "monitor": "%s" % dv,
                   "description": "Measurement Group",
                   "timer": "%s" % dv,
                   "label": "nxsmntgrp"}
            try:
                self.myAssertDict(json.loads(se["AutomaticComponentGroup"]),
                                  acps)
                self.myAssertDict(json.loads(se["ComponentGroup"]), cps)
                self.myAssertDict(json.loads(se["DataSourceGroup"]), dss)
                self.assertEqual(json.loads(se["HiddenElements"]), [])
                self.assertEqual(json.loads(se["OrderedChannels"]), [])
                self.myAssertDict(json.loads(se["DataRecord"]), records)
                self.assertEqual(json.loads(se["Timer"]), [ar["name"]])
                self.assertEqual(se["MntGrp"], "nxsmntgrp")
                print "COMP", mgt.components()
                print "ACOMP", mgt.automaticComponents()
                print "MCP", mcps
                print "DS", mgt.dataSources()
                self.myAssertRaise(Exception, mgt.updateProfile)
            finally:
                mgt.deleteProfile("nxsmntgrp")
                try:
                    tmg.tearDown()
                except:
                    pass

    ## updateProfile test
    def test_updateProfile_nodevice_cp(self):
        fun = sys._getframe().f_code.co_name
        print "Run: %s.%s() " % (self.__class__.__name__, fun)
        val = {"ConfigDevice": self._cf.dp.name(),
               "WriterDevice": self._wr.dp.name(),
               "Door": 'doortestp09/testts/t1r228',
               "MntGrp": 'nxsmntgrp'}

        wrong = ['mycp3']
        mgt = ProfileManager(None)
        self.myAssertRaise(Exception, mgt.updateProfile)

        se = Selector(None)
        mgt = ProfileManager(se)
        self.myAssertRaise(Exception, mgt.updateProfile)

        msp = MacroServerPools(10)
        se = Selector(msp)
        se["Door"] = val["Door"]
        se["ConfigDevice"] = val["ConfigDevice"]
        mgt = ProfileManager(se)
        self.assertEqual(mgt.availableMntGrps(), [])
        self.myAssertRaise(Exception, mgt.updateProfile)

        db = PyTango.Database()
        db.put_device_property(self._ms.ms.keys()[0],
                               {'PoolNames': self._pool.dp.name()})
        pool = self._pool.dp
        self._ms.dps[self._ms.ms.keys()[0]].Init()

        self.assertEqual(mgt.availableMntGrps(), [])

        arr = [
            {"full_name":"test/ct/01/Value", "name":"ct01"},
            {"full_name":"test/ct/02/Value", "name":"ct02"},
            {"full_name":"test/ct/03/value", "name":"ct03"},
            {"full_name":"test/ct/04/value", "name":"ct04"},
            {"full_name":"null/val", "name":"mntgrp_04"},
            ]
        pool.AcqChannelList = [json.dumps(a) for a in arr]

        self.myAssertRaise(Exception, mgt.updateProfile)
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

            se["ComponentGroup"] = json.dumps(cps)
            se["AutomaticComponentGroup"] = json.dumps(acps)
            se["DataSourceGroup"] = json.dumps(dss)
            self._cf.dp.SetCommandVariable(["MCPLIST", json.dumps(mcps)])

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

            se["Timer"] = '["%s"]' % ar["name"]
            se["DataRecord"] = json.dumps(records)

            tmg = TestMGSetUp.TestMeasurementGroupSetUp(name='nxsmntgrp')
            dv = "/".join(ar["full_name"].split("/")[0:-1])
            smg = {"controllers": {},
                   "monitor": "%s" % dv,
                   "description": "Measurement Group",
                   "timer": "%s" % dv,
                   "label": "nxsmntgrp"}
            try:
                self.myAssertDict(json.loads(se["AutomaticComponentGroup"]),
                                  acps)
                self.myAssertDict(json.loads(se["ComponentGroup"]), cps)
                self.myAssertDict(json.loads(se["DataSourceGroup"]), dss)
                self.assertEqual(json.loads(se["HiddenElements"]), [])
                self.assertEqual(json.loads(se["OrderedChannels"]), [])
                self.myAssertDict(json.loads(se["DataRecord"]), records)
                self.assertEqual(json.loads(se["Timer"]), [ar["name"]])
                self.assertEqual(se["MntGrp"], "nxsmntgrp")
                print "COMP", mgt.components()
                print "ACOMP", mgt.automaticComponents()
                print "MCP", mcps
                print "DS", mgt.dataSources()
                self.myAssertRaise(Exception, mgt.updateProfile)
#                mgt.updateProfile()
            finally:
                mgt.deleteProfile("nxsmntgrp")
                try:
                    tmg.tearDown()
                except:
                    pass

    ## updateProfile test
    def test_updateProfile_wrongdevice(self):
        fun = sys._getframe().f_code.co_name
        print "Run: %s.%s() " % (self.__class__.__name__, fun)
        val = {"ConfigDevice": self._cf.dp.name(),
               "WriterDevice": self._wr.dp.name(),
               "Door": 'doortestp09/testts/t1r228',
               "MntGrp": 'nxsmntgrp'}

        wrong = ['tann1', 'tann0']
        mgt = ProfileManager(None)
        self.myAssertRaise(Exception, mgt.updateProfile)

        se = Selector(None)
        mgt = ProfileManager(se)
        self.myAssertRaise(Exception, mgt.updateProfile)

        msp = MacroServerPools(10)
        se = Selector(msp)
        se["Door"] = val["Door"]
        se["ConfigDevice"] = val["ConfigDevice"]
        mgt = ProfileManager(se)
        self.assertEqual(mgt.availableMntGrps(), [])
        self.myAssertRaise(Exception, mgt.updateProfile)

        db = PyTango.Database()
        db.put_device_property(self._ms.ms.keys()[0],
                               {'PoolNames': self._pool.dp.name()})
        pool = self._pool.dp
        self._ms.dps[self._ms.ms.keys()[0]].Init()

        self.assertEqual(mgt.availableMntGrps(), [])

        arr = [
            {"full_name":"test/ct/01/Value", "name":"ct01"},
            {"full_name":"test/ct/02/Value", "name":"ct02"},
            {"full_name":"test/ct/03/value", "name":"ct03"},
            {"full_name":"test/ct/04/value", "name":"ct04"},
            {"full_name":"null/val", "name":"mntgrp_04"},
            ]
        pool.AcqChannelList = [json.dumps(a) for a in arr]

        self.myAssertRaise(Exception, mgt.updateProfile)
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

            se["ComponentGroup"] = json.dumps(cps)
            se["AutomaticComponentGroup"] = json.dumps(acps)
            se["DataSourceGroup"] = json.dumps(dss)
            self._cf.dp.SetCommandVariable(["MCPLIST", json.dumps(mcps)])

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

            se["Timer"] = '["%s"]' % ar["name"]
            se["DataRecord"] = json.dumps(records)

            tmg = TestMGSetUp.TestMeasurementGroupSetUp(name='nxsmntgrp')
            dv = "/".join(ar["full_name"].split("/")[0:-1])
            smg = {"controllers": {},
                   "monitor": "%s" % dv,
                   "description": "Measurement Group",
                   "timer": "%s" % dv,
                   "label": "nxsmntgrp"}
            try:
                self.myAssertDict(json.loads(se["AutomaticComponentGroup"]),
                                  acps)
                self.myAssertDict(json.loads(se["ComponentGroup"]), cps)
                self.myAssertDict(json.loads(se["DataSourceGroup"]), dss)
                self.assertEqual(json.loads(se["HiddenElements"]), [])
                self.assertEqual(json.loads(se["OrderedChannels"]), [])
                self.myAssertDict(json.loads(se["DataRecord"]), records)
                self.assertEqual(json.loads(se["Timer"]), [ar["name"]])
                self.assertEqual(se["MntGrp"], "nxsmntgrp")
                print "COMP", mgt.components()
                print "ACOMP", mgt.automaticComponents()
                print "MCP", mcps
                print "DS", mgt.dataSources()
#                mgt.updateProfile()
                self.myAssertRaise(Exception, mgt.updateProfile)
            finally:
                mgt.deleteProfile("nxsmntgrp")
                try:
                    tmg.tearDown()
                except:
                    pass

    ## updateProfile test
    def test_updateProfile_components_nopool_tango(self):
        fun = sys._getframe().f_code.co_name
        print "Run: %s.%s() " % (self.__class__.__name__, fun)
        val = {"ConfigDevice": self._cf.dp.name(),
               "WriterDevice": self._wr.dp.name(),
               "Door": 'doortestp09/testts/t1r228',
               "MntGrp": 'nxsmntgrp'}

        wrong = []

        mgt = ProfileManager(None)
        self.myAssertRaise(Exception, mgt.updateProfile)

        se = Selector(None)
        mgt = ProfileManager(se)
        self.myAssertRaise(Exception, mgt.updateProfile)

        msp = MacroServerPools(10)
        se = Selector(msp)
        se["Door"] = val["Door"]
        se["ConfigDevice"] = val["ConfigDevice"]
        mgt = ProfileManager(se)
        self.assertEqual(mgt.availableMntGrps(), [])
        self.myAssertRaise(Exception, mgt.updateProfile)

        db = PyTango.Database()
        db.put_device_property(self._ms.ms.keys()[0],
                               {'PoolNames': self._pool.dp.name()})
        pool = self._pool.dp
        self._ms.dps[self._ms.ms.keys()[0]].Init()

        self.assertEqual(mgt.availableMntGrps(), [])

        arr = [
            {"full_name":"test/ct/01/Value", "name":"ct01"},
            {"full_name":"test/ct/02/Value", "name":"ct02"},
            {"full_name":"test/ct/03/value", "name":"ct03"},
            {"full_name":"test/ct/04/value", "name":"ct04"},
            {"full_name":"null/val", "name":"mntgrp_04"},
            ]
        pool.AcqChannelList = [json.dumps(a) for a in arr]

        self.myAssertRaise(Exception, mgt.updateProfile)
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

            se["ComponentGroup"] = json.dumps(cps)
            se["AutomaticComponentGroup"] = json.dumps(acps)
            se["DataSourceGroup"] = json.dumps(dss)
            self._cf.dp.SetCommandVariable(["MCPLIST", json.dumps(mcps)])

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

            se["Timer"] = '["%s"]' % ar["name"]
            se["DataRecord"] = json.dumps(records)

            tmg = TestMGSetUp.TestMeasurementGroupSetUp(name='nxsmntgrp')
            dv = "/".join(ar["full_name"].split("/")[0:-1])
            chds = mgt.dataSources()
            chds.extend(mgt.disableDataSources())
            chds = sorted([ds for ds in chds if not ds.startswith('client')])

            tgc = {}

            try:
                self.myAssertDict(json.loads(se["AutomaticComponentGroup"]),
                                  acps)
                self.myAssertDict(json.loads(se["ComponentGroup"]), cps)
                self.myAssertDict(json.loads(se["DataSourceGroup"]), dss)
                self.assertEqual(json.loads(se["HiddenElements"]), [])
                self.assertEqual(json.loads(se["OrderedChannels"]), [])
                self.myAssertDict(json.loads(se["DataRecord"]), records)
                self.assertEqual(json.loads(se["Timer"]), [ar["name"]])
                self.assertEqual(se["MntGrp"], "nxsmntgrp")
#                print "COMP", mgt.components()
#                print "ACOMP", mgt.automaticComponents()
#                print "MCP", mcps
#                print "DS", mgt.dataSources()
#                print "DDS", mgt.disableDataSources()
                jpcnf = mgt.updateProfile()
                pcnf = json.loads(jpcnf)
                mgdp = PyTango.DeviceProxy(tmg.new_device_info_writer.name)
                jcnf = mgdp.Configuration
                cnf = json.loads(jcnf)
                self.myAssertDict(json.loads(se["AutomaticComponentGroup"]),
                                  acps)
                self.myAssertDict(json.loads(se["ComponentGroup"]), cps)
                self.myAssertDict(json.loads(se["DataSourceGroup"]), dss)
                self.assertEqual(json.loads(se["HiddenElements"]), [])
                self.assertEqual(json.loads(se["OrderedChannels"]), [])
                self.myAssertDict(json.loads(se["DataRecord"]), records)
                self.assertEqual(json.loads(se["Timer"]), [ar["name"]])
                self.assertEqual(se["MntGrp"], "nxsmntgrp")
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
                       "label": "nxsmntgrp"}
#                print "SMG", smg
                self.myAssertDict(smg, pcnf)
                self.myAssertDict(pcnf, cnf)
                se.reset()
                se["Door"] = val["Door"]
                se["ConfigDevice"] = val["ConfigDevice"]
                se["MntGrp"] = "nxsmntgrp"
                se.fetchSelection()
                self.myAssertDict(json.loads(se["AutomaticComponentGroup"]),
                                  acps)
                self.myAssertDict(json.loads(se["ComponentGroup"]), cps)
                self.myAssertDict(json.loads(se["DataSourceGroup"]), dss)
                self.assertEqual(json.loads(se["HiddenElements"]), [])
                self.assertEqual(json.loads(se["OrderedChannels"]), [])
                self.myAssertDict(json.loads(se["DataRecord"]), records)
                self.assertEqual(json.loads(se["Timer"]), [ar["name"]])
                self.assertEqual(se["MntGrp"], "nxsmntgrp")
            finally:
                mgt.deleteProfile("nxsmntgrp")
                try:
                    tmg.tearDown()
                except:
                    pass

    ## updateProfile test
    def test_updateProfile_components_pool_tango(self):
        fun = sys._getframe().f_code.co_name
        print "Run: %s.%s() " % (self.__class__.__name__, fun)
        val = {"ConfigDevice": self._cf.dp.name(),
               "WriterDevice": self._wr.dp.name(),
               "Door": 'doortestp09/testts/t1r228',
               "MntGrp": 'nxsmntgrp'}

        wrong = []

        mgt = ProfileManager(None)
        self.myAssertRaise(Exception, mgt.updateProfile)

        se = Selector(None)
        mgt = ProfileManager(se)
        self.myAssertRaise(Exception, mgt.updateProfile)

        msp = MacroServerPools(10)
        se = Selector(msp)
        se["Door"] = val["Door"]
        se["ConfigDevice"] = val["ConfigDevice"]
        mgt = ProfileManager(se)
        self.assertEqual(mgt.availableMntGrps(), [])
        self.myAssertRaise(Exception, mgt.updateProfile)

        db = PyTango.Database()
        db.put_device_property(self._ms.ms.keys()[0],
                               {'PoolNames': self._pool.dp.name()})
        pool = self._pool.dp
        self._ms.dps[self._ms.ms.keys()[0]].Init()

        self.assertEqual(mgt.availableMntGrps(), [])
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
                    if ds.startswith("image_"):
                        exp["controller"] = image_ctrl
                    if ds.startswith("spectrum_"):
                        exp["controller"] = spectrum_ctrl
                    else:
                        exp["controller"] = scalar_ctrl
                    expch.append(exp)
                    pdss.append(ds)
            pdss = sorted(pdss)

            acqch = [
                {"full_name":"test/ct/01/Value", "name":"ct01"},
                {"full_name":"test/ct/02/Value", "name":"ct02"},
                {"full_name":"test/ct/03/value", "name":"ct03"},
                {"full_name":"test/ct/04/value", "name":"ct04"},
                {"full_name":"null/val", "name":"mntgrp_04"}
                ]

            for ch in expch:
                ach = {}
                ach["name"] = ch["name"]
                ach["full_name"] = ch["source"]
                acqch.append(ach)

            pool.AcqChannelList = [json.dumps(a) for a in acqch]
            pool.ExpChannelList = [json.dumps(a) for a in expch]

            self.myAssertRaise(Exception, mgt.updateProfile)
            self._cf.dp.SetCommandVariable(
                ["CPDICT", json.dumps(self.smycps)])
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
                        ["CPDICT", json.dumps(self.smycps)])
                    self._cf.dp.SetCommandVariable(
                        ["DSDICT", json.dumps(self.smydssXX)])

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
                        if ds in self.smydssXX.keys():
                            if ds not in wrong:
                                dss[ds] = bool(self.__rnd.randint(0, 1))

                    ndss = self.__rnd.randint(1, len(self.smydssXX.keys()) - 1)
                    ldss = self.__rnd.sample(set(self.smydssXX.keys()), ndss)
                    for ds in ldss:
                        if ds in self.smydssXX.keys():
                            if ds not in wrong:
                                dss[ds] = bool(self.__rnd.randint(0, 1))

                    mncps = self.__rnd.randint(1, len(self.smycps.keys()) - 1)
                    mcps = [cp for cp in self.__rnd.sample(
                            set(self.smycps.keys()), mncps) if cp not in wrong]

                    adss = dict(dss)
                    for ch in expch:
#                        print ch
                        if ch["name"] not in adss.keys():
                            adss[ch["name"]] = False
                    se["ComponentGroup"] = json.dumps(cps)
                    se["AutomaticComponentGroup"] = json.dumps(acps)
                    se["DataSourceGroup"] = json.dumps(dss)
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

                    se["Timer"] = '["%s"]' % ar["name"]
                    se["DataRecord"] = json.dumps(records)

                    tmg = TestMGSetUp.TestMeasurementGroupSetUp(
                        name='nxsmntgrp')
                    dv = "/".join(ar["full_name"].split("/")[0:-1])
                    chds = mgt.dataSources()
                    chds.extend(mgt.disableDataSources())
                    chds = sorted([
                            ds for ds in chds if not ds.startswith('client')])

#                    print "COMP", mgt.components()
#                    print "ACOMP", mgt.automaticComponents()
#                    print "MCP", mcps
#                    print "DS", mgt.dataSources()
#                    print "DDS", mgt.disableDataSources()
                    self.myAssertDict(
                        json.loads(se["AutomaticComponentGroup"]),
                        acps)
                    self.myAssertDict(json.loads(se["ComponentGroup"]), cps)
                    self.myAssertDict(json.loads(se["DataSourceGroup"]), adss)
                    self.assertEqual(json.loads(se["HiddenElements"]), [])
                    self.assertEqual(json.loads(se["OrderedChannels"]), pdss)
                    self.myAssertDict(json.loads(se["DataRecord"]), records)
                    self.assertEqual(json.loads(se["Timer"]), [ar["name"]])
                    self.assertEqual(se["MntGrp"], "nxsmntgrp")
                    jpcnf = mgt.updateProfile()
                    pcnf = json.loads(jpcnf)
                    mgdp = PyTango.DeviceProxy(tmg.new_device_info_writer.name)
                    jcnf = mgdp.Configuration
                    cnf = json.loads(jcnf)
                    self.myAssertDict(
                        json.loads(se["AutomaticComponentGroup"]),
                        acps)
                    self.myAssertDict(json.loads(se["ComponentGroup"]), cps)
                    self.myAssertDict(json.loads(se["DataSourceGroup"]), adss)
                    self.assertEqual(json.loads(se["HiddenElements"]), [])
                    self.assertEqual(json.loads(se["OrderedChannels"]), pdss)
                    self.myAssertDict(json.loads(se["DataRecord"]), records)
                    self.assertEqual(json.loads(se["Timer"]), [ar["name"]])
                    self.assertEqual(se["MntGrp"], "nxsmntgrp")
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
#                                    print ds, cnt
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
                           "label": "nxsmntgrp"}
#                    print "SMG", smg
                    self.myAssertDict(smg, pcnf)
                    self.myAssertDict(pcnf, cnf)
                    se.reset()
                    se["Door"] = val["Door"]
                    se["ConfigDevice"] = val["ConfigDevice"]
                    se["MntGrp"] = "nxsmntgrp"
                    se.fetchSelection()
                    self.myAssertDict(
                        json.loads(se["AutomaticComponentGroup"]),
                        acps)
                    self.myAssertDict(json.loads(se["ComponentGroup"]), cps)
                    self.myAssertDict(json.loads(se["DataSourceGroup"]), adss)
                    self.assertEqual(json.loads(se["HiddenElements"]), [])
                    self.assertEqual(json.loads(se["OrderedChannels"]), pdss)
                    self.myAssertDict(json.loads(se["DataRecord"]), records)
                    self.assertEqual(json.loads(se["Timer"]), [ar["name"]])
                    self.assertEqual(se["MntGrp"], "nxsmntgrp")
                finally:
                    mgt.deleteProfile("nxsmntgrp")
                    try:
                        tmg.tearDown()
                    except:
                        pass
        finally:
            simp2.tearDown()

if __name__ == '__main__':
    unittest.main()
