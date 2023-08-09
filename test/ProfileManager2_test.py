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
# \file ProfileManagerTest.py
# unittests for TangoDsItemTest running Tango Server
#
import unittest
import os
import sys
import random
import struct
import binascii
import json
import string
import time
import nxsrecconfig

try:
    import tango
except Exception:
    import PyTango as tango

try:
    import TestMacroServerSetUp
except Exception:
    from . import TestMacroServerSetUp
try:
    import TestPool2SetUp
except Exception:
    from . import TestPool2SetUp
try:
    import TestServerSetUp
except Exception:
    from . import TestServerSetUp
try:
    import TestConfigServerSetUp
except Exception:
    from . import TestConfigServerSetUp
try:
    import TestWriterSetUp
except Exception:
    from . import TestWriterSetUp
try:
    import TestMGSetUp
except Exception:
    from . import TestMGSetUp


from nxsrecconfig.MacroServerPools import MacroServerPools
from nxsrecconfig.Selector import Selector
from nxsrecconfig.Describer import Describer
from nxsrecconfig.ProfileManager import ProfileManager
from nxsrecconfig.Utils import MSUtils, Utils

import logging
logger = logging.getLogger()

if sys.version_info > (3,):
    long = int

# if 64-bit machione
IS64BIT = (struct.calcsize("P") == 8)

#: tango version
TGVER = tango.__version_info__[0]

# list of available databases
DB_AVAILABLE = []

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
class ProfileManager2Test(unittest.TestCase):

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
        self._pool = TestPool2SetUp.TestPool2SetUp()
        self._simps = TestServerSetUp.TestServerSetUp()

        try:
            self.__seed = long(binascii.hexlify(os.urandom(16)), 16)
        except NotImplementedError:
            self.__seed = long(time.time() * 256)
        # self.__seed  = 244826915137294083694874616207392554673
        self.__rnd = random.Random(self.__seed)

        self.__dump = {}

        # default zone
        self.__defaultzone = 'Europe/Berlin'
        # default mntgrp
        self.__defaultmntgrp = 'nxsmntgrp'
        # default path
        self.__defaultpath = \
            '/$var.entryname#\'scan\'$var.serialno:NXentry/NXinstrument/' \
            'collection'

        # selection version
        self.__version = nxsrecconfig.__version__

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
            ("DefaultDynamicPath", self.__defaultpath),
            ("TimeZone", self.__defaultzone),
            ("ConfigDevice", ''),
            ("WriterDevice", ''),
            ("Door", ''),
            ("MntGrpConfiguration", ''),
            ("MntGrp", ''),
            ("Version", self.__version)

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

        self.rescps = {
            'mycp': {},
            'mycp2': {},
            'mycp3': {'ann': [('STEP', 'TANGO', '', None, None, "field")]},
            'exp_t01': {
                'exp_t01': [
                    ('STEP', 'CLIENT', 'haso228k:10000/expchan/dgg2_exp_01/1',
                     'NX_FLOAT', None, "field")]},
            'dim1': {
                'tann1c': [
                    ('INIT', 'TANGO', 'dsf/sd/we/myattr2', 'NX_INT8',
                     [34], "field")]},
            'dim2': {
                'tann1c': [
                    ('INIT', 'TANGO', 'dsf/sd/we/myattr2', 'NX_INT8',
                     ['$datasources.ann'], "field")]},
            'dim3': {
                'tann1c': [
                    ('INIT', 'TANGO', 'dsf/sd/we/myattr2', 'NX_INT8',
                     [1234], "field")]},
            'dim4': {
                'tann1c': [
                    ('INIT', 'TANGO', 'dsf/sd/we/myattr2', 'NX_INT8',
                     ['$datasources.ann2'], "field")],
                'ann2': [
                    ('CONFIG', 'CLIENT', '', None, None, "dim")],
            },
            'dim5': {
                'tann1c': [
                    ('INIT', 'TANGO', 'dsf/sd/we/myattr2', 'NX_INT8',
                     ['$datasources.ann'], "field")],
                'ann': [('CONFIG', 'TANGO', '', None, None, "dim")],
            },
            'dim6': {'tann1c': [
                ('INIT', 'TANGO', 'dsf/sd/we/myattr2', 'NX_INT8',
                 ['$datasources.ann', 123], "field")]},
            'dim7': {'tann1c': [
                ('INIT', 'TANGO', 'dsf/sd/we/myattr2', 'NX_INT8',
                 [None, None], "field")]},
            'dim8': {'tann1c': [
                ('INIT', 'TANGO', 'dsf/sd/we/myattr2', 'NX_INT8',
                 [None, 123], "field")]},
            'scan': {'__unnamed__1': [('STEP', 'CLIENT', 'exp_c01',
                                       'NX_FLOAT', None, "field")],
                     '__unnamed__2': [('STEP', 'CLIENT', 'exp_c02',
                                       'NX_FLOAT', None, "field")],
                     '__unnamed__3': [('STEP', 'CLIENT', 'p09/mca/exp.02',
                                       'NX_FLOAT', [2048], "field")],
                     },
            'scan2': {
                'c01': [('STEP', 'CLIENT', 'exp_c01', 'NX_FLOAT', None,
                         "field")],
                'c02': [('STEP', 'CLIENT', 'exp_c02', 'NX_FLOAT', None,
                         "field")],
                'mca': [('STEP', 'CLIENT', 'p09/mca/exp.02', 'NX_FLOAT',
                         [2048], "field")],
            },
            'scan3': {
                'c01': [('STEP', 'CLIENT', 'exp_c01', 'NX_FLOAT', None,
                         "field"),
                        ('INIT', 'CLIENT', 'exp_c01', 'NX_FLOAT', None,
                         "field")],
                'mca': [('STEP', 'CLIENT', 'p09/mca/exp.02', 'NX_FLOAT',
                         [2048], "field")],
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
        print("SEED = %s" % self.__seed)
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
        print("\nsetting up...")

    # test closer
    # \brief Common tear down
    def tearDown(self):
        print("tearing down ...")
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

        for key in el.keys():
            self.__dump[name][key] = el[key]

    def compareToDump(self, el, excluded=None, name="default"):
        exc = set(excluded or [])
        dks = set(self.__dump[name].keys()) - exc
        eks = set(el.keys()) - exc
        self.assertEqual(dks, eks)
        for key in dks:
            # if self.__dump[name][key] != el[key]:
            #     print "COMP", key
            self.assertEqual(self.__dump[name][key], el[key])

    def getDump(self, key, name="default"):
        return self.__dump[name][key]

    def compareToDumpJSON(self, el, excluded=None, name="default"):
        exc = set(excluded or [])
        dks = set(self.__dump[name].keys()) - exc
        eks = set(el.keys()) - exc
        self.assertEqual(dks, eks)
        for key in dks:
            try:
                w1 = json.loads(self.__dump[name][key])
                w2 = json.loads(el[key])
            except Exception:
                self.assertEqual(self.__dump[name][key], el[key])
            else:
                if isinstance(w1, dict):
                    self.myAssertDict(w1, w2)
                else:
                    # if self.__dump[name][key] != el[key]:
                    #     print "COMP", key
                    self.assertEqual(self.__dump[name][key], el[key])

    def getRandomName(self, maxsize):
        if sys.version_info > (3,):
            letters = string.ascii_letters + string.digits
        else:
            letters = string.letters + string.digits
        size = self.__rnd.randint(1, maxsize)
        return ''.join(self.__rnd.choice(letters) for _ in range(size))

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
        except exception as e:
            error = True
            err = e
        self.assertEqual(error, True)
        return err

    def myAssertDict(self, dct, dct2):
        logger.debug('dict %s' % type(dct))
        logger.debug("\n%s\n%s" % (dct, dct2))
        self.assertTrue(isinstance(dct, dict))
        # if not isinstance(dct2, dict):
        #    print "NOT DICT", type(dct2), dct2
        #    print "DICT", type(dct), dct
        self.assertTrue(isinstance(dct2, dict))
        logger.debug("%s %s" % (len(list(dct.keys())), len(list(dct2.keys()))))
        # if set(dct.keys()) ^ set(dct2.keys()):
        #     print 'DCT', dct.keys()
        #     print 'DCT2', dct2.keys()
        #     print "DIFF", set(dct.keys()) ^ set(dct2.keys())
        self.assertEqual(len(list(dct.keys())), len(list(dct2.keys())))
        for k, v in dct.items():
            logger.debug("%s  in %s" % (str(k), str(dct2.keys())))
            self.assertTrue(k in dct2.keys())
            if isinstance(v, dict):
                self.myAssertDict(v, dct2[k])
            else:
                logger.debug("%s , %s" % (str(v), str(dct2[k])))
                # if v != dct2[k]:
                #     print 'VALUES', k, v, dct2[k]
                self.assertEqual(v, dct2[k])

    # constructor test
    def test_constructor_keys(self):
        fun = sys._getframe().f_code.co_name
        print("Run: %s.%s() " % (self.__class__.__name__, fun))
        # val = {"ConfigDevice": self._cf.dp.name(),
        #        "WriterDevice": self._wr.dp.name(),
        #        "Door": 'doortestp09/testts/t1r228',
        #        "MntGrp": 'nxsmntgrp'}

        # mgt =
        ProfileManager(None)

        se = Selector(None, self.__version)
        # mgt =
        ProfileManager(se)

        msp = MacroServerPools(10)
        se = Selector(msp, self.__version)
        # mgt =
        ProfileManager(se)

    # availableMntGrps test
    def test_availableMntGrps(self):
        fun = sys._getframe().f_code.co_name
        print("Run: %s.%s() " % (self.__class__.__name__, fun))
        val = {"ConfigDevice": self._cf.dp.name(),
               "WriterDevice": self._wr.dp.name(),
               "Door": 'doortestp09/testts/t1r228',
               "MntGrp": 'nxsmntgrp'}

        mgt = ProfileManager(None)
        mgt.masterTimer = True
        mgt.masterTimerFirst = False
        self.myAssertRaise(Exception, mgt.availableMntGrps)

        se = Selector(None, self.__version)
        mgt = ProfileManager(se)
        mgt.masterTimer = True
        mgt.masterTimerFirst = False
        self.myAssertRaise(Exception, mgt.availableMntGrps)

        msp = MacroServerPools(10)
        se = Selector(msp, self.__version)
        se["Door"] = val["Door"]
        mgt = ProfileManager(se)
        mgt.masterTimer = True
        mgt.masterTimerFirst = False
        self.assertEqual(mgt.availableMntGrps(), [])

        db = tango.Database()
        db.put_device_property(list(self._ms.ms.keys())[0],
                               {'PoolNames': self._pool.dp.name()})
        pool = self._pool.dp
        self._ms.dps[list(self._ms.ms.keys())[0]].Init()

        self.assertEqual(mgt.availableMntGrps(), [])

        arr = [
            {"name": "test/ct/01", "full_name": "mntgrp_01e"},
            {"name": "test/ct/02", "full_name": "mntgrp_02att"},
            {"name": "test/ct/03", "full_name": "mntgrp_03value"},
            {"name": "test/ct/04", "full_name": "mntgrp_04/13"},
            {"name": "null", "full_name": "mntgrp_04"},
        ]

        pool.MeasurementGroupList = [json.dumps(a) for a in arr]

        dd = mgt.availableMntGrps()
        self.assertEqual(set(dd), set([a["name"] for a in arr]))

        for ar in arr:

            MSUtils.setEnv('ActiveMntGrp', ar["name"],
                           list(self._ms.ms.keys())[0])
            # print MSUtils.getEnv('ActiveMntGrp', list(self._ms.ms.keys())[0])
            dd = mgt.availableMntGrps()
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

        mgt = ProfileManager(None)
        mgt.masterTimer = True
        mgt.masterTimerFirst = False
        self.myAssertRaise(Exception, mgt.availableMntGrps)

        se = Selector(None, self.__version)
        mgt = ProfileManager(se)
        mgt.masterTimer = True
        mgt.masterTimerFirst = False
        self.myAssertRaise(Exception, mgt.availableMntGrps)

        msp = MacroServerPools(10)
        se = Selector(msp, self.__version)
        se["Door"] = val["Door"]
        mgt = ProfileManager(se)
        mgt.masterTimer = True
        mgt.masterTimerFirst = False
        self.assertEqual(mgt.availableMntGrps(), [])

        try:
            tpool2 = TestPool2SetUp.TestPool2SetUp(
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

            self.assertEqual(mgt.availableMntGrps(), [])
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

            if se.getPools()[0].name() == "pooltestp09/testts/t2r228":
                arr = arr2
            else:
                arr = arr1

            dd = mgt.availableMntGrps()
            self.assertEqual(set(dd), set([a["name"] for a in arr]))

            for ar in arr1:

                MSUtils.setEnv('ActiveMntGrp', ar["name"],
                               list(self._ms.ms.keys())[0])
                dd = mgt.availableMntGrps()
                self.assertEqual(dd[0], ar["name"])
                if arr1 == arr or ar["name"] != 'null':
                    self.assertEqual(set(dd), set([a["name"] for a in arr1]))
                else:
                    self.assertEqual(set(dd), set([a["name"] for a in arr]))

            for ar in arr2:
                MSUtils.setEnv('ActiveMntGrp', ar["name"],
                               list(self._ms.ms.keys())[0])
                dd = mgt.availableMntGrps()
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

        mgt = ProfileManager(None)
        mgt.masterTimer = True
        mgt.masterTimerFirst = False
        self.myAssertRaise(Exception, mgt.deleteProfile)

        se = Selector(None, self.__version)
        mgt = ProfileManager(se)
        mgt.masterTimer = True
        mgt.masterTimerFirst = False
        self.myAssertRaise(Exception, mgt.deleteProfile, None)

        msp = MacroServerPools(10)
        se = Selector(msp, self.__version)
        se["Door"] = val["Door"]
        se["ConfigDevice"] = val["ConfigDevice"]
        mgt = ProfileManager(se)
        mgt.masterTimer = True
        mgt.masterTimerFirst = False
        self.assertEqual(mgt.availableMntGrps(), [])

        db = tango.Database()
        db.put_device_property(list(self._ms.ms.keys())[0],
                               {'PoolNames': self._pool.dp.name()})
        pool = self._pool.dp
        self._ms.dps[list(self._ms.ms.keys())[0]].Init()

        self.assertEqual(mgt.availableMntGrps(), [])

        arr = [
            {"full_name": "test/ct/01", "name": "mntgrp_01e"},
            {"full_name": "test/ct/02", "name": "mntgrp_02att"},
            {"full_name": "test/ct/03", "name": "mntgrp_03value"},
            {"full_name": "test/ct/04", "name": "mntgrp_04_13"},
            {"full_name": "null", "name": "mntgrp_04"},
        ]

        pool.MeasurementGroupList = [json.dumps(a) for a in arr]

        dd2 = mgt.availableMntGrps()
        self.assertEqual(set(dd2), set([a["name"] for a in arr]))

        self._cf.dp.Init()
        self._cf.dp.SetCommandVariable(["SELDICT", json.dumps(self.mysel2)])
        sl2 = self._cf.dp.availableSelections()

        dl = []
        mgs = [ar["name"] for ar in arr] + list(self.mysel2.keys())
        # print mgs
        for ar in mgs:
            MSUtils.setEnv('ActiveMntGrp', ar, list(self._ms.ms.keys())[0])
            mgt.deleteProfile(ar)
            dl.append(ar)
            self.assertEqual(MSUtils.getEnv(
                'ActiveMntGrp', list(self._ms.ms.keys())[0]), "")
            dd = mgt.availableMntGrps()
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

        mgt = ProfileManager(None)
        mgt.masterTimer = True
        mgt.masterTimerFirst = False
        self.myAssertRaise(Exception, mgt.availableMntGrps)

        se = Selector(None, self.__version)
        mgt = ProfileManager(se)
        mgt.masterTimer = True
        mgt.masterTimerFirst = False
        self.myAssertRaise(Exception, mgt.availableMntGrps)

        msp = MacroServerPools(10)
        se = Selector(msp, self.__version)
        se["Door"] = val["Door"]
        se["ConfigDevice"] = val["ConfigDevice"]
        mgt = ProfileManager(se)
        mgt.masterTimer = True
        mgt.masterTimerFirst = False
        self.assertEqual(mgt.availableMntGrps(), [])

        try:
            tpool2 = TestPool2SetUp.TestPool2SetUp(
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

            self.assertEqual(mgt.availableMntGrps(), [])

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
                mgt.deleteProfile(ar)
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
                mgt.deleteProfile(ar)
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

        for i in range(20):
            msp = MacroServerPools(10)
            se = Selector(msp, self.__version)
            se["Door"] = val["Door"]
            se["ConfigDevice"] = val["ConfigDevice"]
            se["WriterDevice"] = val["WriterDevice"]
            pm = ProfileManager(se)
            pm.masterTimer = True
            pm.masterTimerFirst = False

            cps = {}
            lcp = self.__rnd.randint(1, 40)
            for i in range(lcp):
                cps[self.getRandomName(10)] = bool(self.__rnd.randint(0, 1))
            se["ComponentPreselection"] = json.dumps(cps)

            self.dump(se)

            ac = pm.preselectedComponents()
            self.compareToDump(se, ["ComponentPreselection"])
            ndss = json.loads(se["ComponentPreselection"])

            acp = []
            for ds in cps.keys():
                self.assertTrue(ds in ndss.keys())
                self.assertEqual(ndss[ds], cps[ds])
                if ndss[ds]:
                    acp.append(ds)

            self.assertEqual(set(ac), set(acp))

    # test
    def test_components(self):
        fun = sys._getframe().f_code.co_name
        print("Run: %s.%s() " % (self.__class__.__name__, fun))
        val = {"ConfigDevice": self._cf.dp.name(),
               "WriterDevice": self._wr.dp.name(),
               "Door": 'doortestp09/testts/t1r228',
               "MntGrp": 'nxsmntgrp'}

        for i in range(20):
            msp = MacroServerPools(10)
            se = Selector(msp, self.__version)
            se["Door"] = val["Door"]
            se["OrderedChannels"] = json.dumps([])
            db = tango.Database()
            db.put_device_property(list(self._ms.ms.keys())[0],
                                   {'PoolNames': self._pool.dp.name()})
            pool = self._pool.dp
            pool.ExpChannelList = []
            self._ms.dps[list(self._ms.ms.keys())[0]].Init()

            se["Door"] = val["Door"]
            se["ConfigDevice"] = val["ConfigDevice"]
            se["WriterDevice"] = val["WriterDevice"]
            pm = ProfileManager(se)
            pm.masterTimer = True
            pm.masterTimerFirst = False

            cps = {}
            dss = {}
            lcp = self.__rnd.randint(1, 40)
            lds = self.__rnd.randint(1, 40)
            for i in range(lcp):
                cps[self.getRandomName(10)] = bool(self.__rnd.randint(0, 1))
            for i in range(lds):
                dss[self.getRandomName(10)] = bool(self.__rnd.randint(0, 1))
            ddss = self.__rnd.sample(list(dss.keys()), self.__rnd.randint(
                1, len(list(dss.keys()))))
            dcps = dict(cps)
            for ds in ddss:
                dcps[ds] = bool(self.__rnd.randint(0, 1))

            self._cf.dp.SetCommandVariable(["CPDICT", json.dumps(dcps)])
            self._cf.dp.SetCommandVariable(["DSDICT", json.dumps(dss)])

            se["ComponentSelection"] = json.dumps(cps)
            se["DataSourceSelection"] = json.dumps(dss)
            ndss = json.loads(se["DataSourceSelection"])
            common = set(cps) & set(dss)
            self.dump(se)

            ncps = json.loads(se["ComponentSelection"])
            ndss = json.loads(se["DataSourceSelection"])
            tdss = [ds for ds in ndss if ndss[ds]]
            tcps = [cp for cp in ncps if ncps[cp]]

            pmcp = pm.components()
            self.assertEqual(len(cps), len(ncps) + len(common))
            for key in cps.keys():
                if key not in common:
                    self.assertTrue(key in ncps.keys())
                    self.assertEqual(ncps[key], cps[key])
            self.compareToDumpJSON(se, ["ComponentSelection"])
            ac = self._cf.dp.availableComponents()
            for cp in pmcp:
                self.assertTrue(cp in ac)
            mfcp = set(tcps) | (set(tdss) & set(ac))
            self.assertEqual(set(pmcp), set(mfcp))

    # test
    def test_cpdescritpion_unknown(self):
        fun = sys._getframe().f_code.co_name
        print("Run: %s.%s() " % (self.__class__.__name__, fun))
        val = {"ConfigDevice": self._cf.dp.name(),
               "WriterDevice": self._wr.dp.name(),
               "Door": 'doortestp09/testts/t1r228',
               "MntGrp": 'nxsmntgrp'}

        msp = MacroServerPools(10)
        se = Selector(msp, self.__version)
        se["Door"] = val["Door"]
        se["OrderedChannels"] = json.dumps([])
        db = tango.Database()
        db.put_device_property(list(self._ms.ms.keys())[0],
                               {'PoolNames': self._pool.dp.name()})
        pool = self._pool.dp
        pool.ExpChannelList = []
        self._ms.dps[list(self._ms.ms.keys())[0]].Init()

        se["Door"] = val["Door"]
        se["ConfigDevice"] = val["ConfigDevice"]
        se["WriterDevice"] = val["WriterDevice"]
        pm = ProfileManager(se)
        pm.masterTimer = True
        pm.masterTimerFirst = False

        cps = {}
        dss = {}
        # lcp = self.__rnd.randint(1, 40)
        # lds = self.__rnd.randint(1, 40)

        dsdict = {
            "ann": self.mydss["ann"]
        }

        self._cf.dp.SetCommandVariable(["CPDICT", json.dumps({})])
        self._cf.dp.SetCommandVariable(["DSDICT", json.dumps(dsdict)])

        se["ComponentSelection"] = json.dumps(cps)
        se["DataSourceSelection"] = json.dumps(dss)
        # ndss =
        json.loads(se["DataSourceSelection"])
        # common = set(cps) & set(dss)
        self.dump(se)

        # ncps =
        json.loads(se["ComponentSelection"])
        # ndss =
        json.loads(se["DataSourceSelection"])
        # tdss = [ds for ds in ndss if ndss[ds]]
        # tcps = [cp for cp in ncps if ncps[cp]]

        self.assertEqual(pm.cpdescription(), [{}])
        se["ComponentSelection"] = json.dumps({"unknown": True})
        self.assertEqual(pm.cpdescription(), [{}])
        se["DataSourceSelection"] = json.dumps({"unknown": True})
        self.assertEqual(pm.cpdescription(), [{}])
        self._cf.dp.SetCommandVariable(["MCPLIST", json.dumps(["unknown"])])
        self.assertEqual(pm.cpdescription(), [{}])

    # test
    def test_cpdescritpion_full(self):
        fun = sys._getframe().f_code.co_name
        print("Run: %s.%s() " % (self.__class__.__name__, fun))
        val = {"ConfigDevice": self._cf.dp.name(),
               "WriterDevice": self._wr.dp.name(),
               "Door": 'doortestp09/testts/t1r228',
               "MntGrp": 'nxsmntgrp'}

        msp = MacroServerPools(10)
        se = Selector(msp, self.__version)
        se["Door"] = val["Door"]
        se["OrderedChannels"] = json.dumps([])
        db = tango.Database()
        db.put_device_property(list(self._ms.ms.keys())[0],
                               {'PoolNames': self._pool.dp.name()})
        pool = self._pool.dp
        pool.ExpChannelList = []
        self._ms.dps[list(self._ms.ms.keys())[0]].Init()

        se["Door"] = val["Door"]
        se["ConfigDevice"] = val["ConfigDevice"]
        se["WriterDevice"] = val["WriterDevice"]
        pm = ProfileManager(se)
        pm.masterTimer = True
        pm.masterTimerFirst = False

        # cps = {}
        # dss = {}
        # lcp = self.__rnd.randint(1, 40)
        # lds = self.__rnd.randint(1, 40)

        # dsdict = {
        #     "ann": self.mydss["ann"]
        # }

        self._cf.dp.SetCommandVariable(["CPDICT", json.dumps(self.mycps)])
        self._cf.dp.SetCommandVariable(["DSDICT", json.dumps(self.mydss)])

        se["ComponentSelection"] = json.dumps({})
        se["DataSourceSelection"] = json.dumps({})
        # ndss =
        json.loads(se["DataSourceSelection"])
        # common = set(cps) & set(dss)
        self.dump(se)

        res = pm.cpdescription(True)
        self.checkCP(res, list(self.rescps.keys()))

    # test
    def test_cpdescritpion_comp_nods(self):
        fun = sys._getframe().f_code.co_name
        print("Run: %s.%s() " % (self.__class__.__name__, fun))
        val = {"ConfigDevice": self._cf.dp.name(),
               "WriterDevice": self._wr.dp.name(),
               "Door": 'doortestp09/testts/t1r228',
               "MntGrp": 'nxsmntgrp'}

        for i in range(20):
            msp = MacroServerPools(10)
            se = Selector(msp, self.__version)
            se["Door"] = val["Door"]
            se["OrderedChannels"] = json.dumps([])
            db = tango.Database()
            db.put_device_property(list(self._ms.ms.keys())[0],
                                   {'PoolNames': self._pool.dp.name()})
            pool = self._pool.dp
            pool.ExpChannelList = []
            self._ms.dps[list(self._ms.ms.keys())[0]].Init()

            se["Door"] = val["Door"]
            se["ConfigDevice"] = val["ConfigDevice"]
            se["WriterDevice"] = val["WriterDevice"]
            pm = ProfileManager(se)
            pm.masterTimer = True
            pm.masterTimerFirst = False

            cps = {}
            dss = {}
            # lcp = self.__rnd.randint(1, 40)
            # lds = self.__rnd.randint(1, 40)

            self._cf.dp.SetCommandVariable(["CPDICT", json.dumps(self.mycps)])
            self._cf.dp.SetCommandVariable(["DSDICT", json.dumps(self.mydss)])

            ncps = self.__rnd.randint(1, len(list(self.mycps.keys())) - 1)
            lcps = self.__rnd.sample(list(self.mycps.keys()), ncps)
            for cp in lcps:
                cps[cp] = bool(self.__rnd.randint(0, 1))

            mncps = self.__rnd.randint(1, len(list(self.mycps.keys())) - 1)
            mcps = self.__rnd.sample(list(self.mycps.keys()), mncps)

            tdss = [ds for ds in dss if dss[ds]]
            tcps = [cp for cp in cps if cps[cp]]

            se["ComponentSelection"] = json.dumps(cps)
            se["DataSourceSelection"] = json.dumps(dss)
            self._cf.dp.SetCommandVariable(["MCPLIST", json.dumps(mcps)])
            # ndss =
            json.loads(se["DataSourceSelection"])
            # common = set(cps) & set(dss)
            self.dump(se)

            res = pm.cpdescription()
            self.checkCP(res, list(set(tcps) | set(tdss) | set(mcps)),
                         strategy='STEP')

    # test
    def test_cpdescritpion_comp_ds(self):
        fun = sys._getframe().f_code.co_name
        print("Run: %s.%s() " % (self.__class__.__name__, fun))
        val = {"ConfigDevice": self._cf.dp.name(),
               "WriterDevice": self._wr.dp.name(),
               "Door": 'doortestp09/testts/t1r228',
               "MntGrp": 'nxsmntgrp'}

        for i in range(20):
            msp = MacroServerPools(10)
            se = Selector(msp, self.__version)
            se["Door"] = val["Door"]
            se["OrderedChannels"] = json.dumps([])
            db = tango.Database()
            db.put_device_property(list(self._ms.ms.keys())[0],
                                   {'PoolNames': self._pool.dp.name()})
            pool = self._pool.dp
            pool.ExpChannelList = []
            self._ms.dps[list(self._ms.ms.keys())[0]].Init()

            se["Door"] = val["Door"]
            se["ConfigDevice"] = val["ConfigDevice"]
            se["WriterDevice"] = val["WriterDevice"]
            pm = ProfileManager(se)
            pm.masterTimer = True
            pm.masterTimerFirst = False

            cps = {}
            dss = {}
            # lcp = self.__rnd.randint(1, 40)
            # lds = self.__rnd.randint(1, 40)

            self._cf.dp.SetCommandVariable(["CPDICT", json.dumps(self.mycps)])
            self._cf.dp.SetCommandVariable(["DSDICT", json.dumps(self.mydss)])

            ncps = self.__rnd.randint(1, len(list(self.mycps.keys())) - 1)
            lcps = self.__rnd.sample(list(self.mycps.keys()), ncps)
            for cp in lcps:
                cps[cp] = bool(self.__rnd.randint(0, 1))

            ndss = self.__rnd.randint(1, len(list(self.mycps.keys())) - 1)
            ldss = self.__rnd.sample(list(self.mycps.keys()), ndss)
            for ds in ldss:
                if ds in self.mydss.keys():
                    dss[ds] = bool(self.__rnd.randint(0, 1))

            mncps = self.__rnd.randint(1, len(list(self.mycps.keys())) - 1)
            mcps = self.__rnd.sample(list(self.mycps.keys()), mncps)

            tdss = [ds for ds in dss if dss[ds]]
            tcps = [cp for cp in cps if cps[cp]]

            se["ComponentSelection"] = json.dumps(cps)
            se["DataSourceSelection"] = json.dumps(dss)
            self._cf.dp.SetCommandVariable(["MCPLIST", json.dumps(mcps)])
            ndss = json.loads(se["DataSourceSelection"])
            # common = set(cps) & set(dss)
            self.dump(se)

            res = pm.cpdescription()
            self.checkCP(res, list(set(tcps) | set(tdss) | set(mcps)),
                         strategy='STEP')

    # test
    def test_componentdatasources(self):
        fun = sys._getframe().f_code.co_name
        print("Run: %s.%s() " % (self.__class__.__name__, fun))
        val = {"ConfigDevice": self._cf.dp.name(),
               "WriterDevice": self._wr.dp.name(),
               "Door": 'doortestp09/testts/t1r228',
               "MntGrp": 'nxsmntgrp'}

        for i in range(20):
            msp = MacroServerPools(10)
            se = Selector(msp, self.__version)
            se["Door"] = val["Door"]
            se["OrderedChannels"] = json.dumps([])
            db = tango.Database()
            db.put_device_property(list(self._ms.ms.keys())[0],
                                   {'PoolNames': self._pool.dp.name()})
            pool = self._pool.dp
            pool.ExpChannelList = []
            self._ms.dps[list(self._ms.ms.keys())[0]].Init()

            se["Door"] = val["Door"]
            se["ConfigDevice"] = val["ConfigDevice"]
            se["WriterDevice"] = val["WriterDevice"]
            pm = ProfileManager(se)
            pm.masterTimer = True
            pm.masterTimerFirst = False

            cps = {}
            dss = {}
            # lcp = self.__rnd.randint(1, 40)
            # lds = self.__rnd.randint(1, 40)

            self._cf.dp.SetCommandVariable(["CPDICT", json.dumps(self.mycps)])
            self._cf.dp.SetCommandVariable(["DSDICT", json.dumps(self.mydss)])

            ncps = self.__rnd.randint(1, len(list(self.mycps.keys())) - 1)
            lcps = self.__rnd.sample(list(self.mycps.keys()), ncps)
            for cp in lcps:
                cps[cp] = bool(self.__rnd.randint(0, 1))

            ndss = self.__rnd.randint(1, len(list(self.mycps.keys())) - 1)
            ldss = self.__rnd.sample(list(self.mycps.keys()), ndss)
            for ds in ldss:
                if ds in self.mydss.keys():
                    dss[ds] = bool(self.__rnd.randint(0, 1))

            mncps = self.__rnd.randint(1, len(list(self.mycps.keys())) - 1)
            mcps = self.__rnd.sample(list(self.mycps.keys()), mncps)

            # tdss = [ds for ds in dss if dss[ds]]
            # tcps = [cp for cp in cps if cps[cp]]

            se["ComponentSelection"] = json.dumps(cps)
            se["DataSourceSelection"] = json.dumps(dss)
            self._cf.dp.SetCommandVariable(["MCPLIST", json.dumps(mcps)])
            ndss = json.loads(se["DataSourceSelection"])
            # common = set(cps) & set(dss)
            self.dump(se)

            dds = pm.componentDataSources()
            res = pm.cpdescription()

            mdds = set()
            for mdss in res[0].values():
                if isinstance(mdss, dict):
                    for ds in mdss.keys():
                        mdds.add(ds)
            self.assertEqual(mdds, set(dds))
            self.assertEqual(len(mdds), len(dds))

    # test
    def test_datasources(self):
        fun = sys._getframe().f_code.co_name
        print("Run: %s.%s() " % (self.__class__.__name__, fun))
        val = {"ConfigDevice": self._cf.dp.name(),
               "WriterDevice": self._wr.dp.name(),
               "Door": 'doortestp09/testts/t1r228',
               "MntGrp": 'nxsmntgrp'}

        for i in range(20):
            msp = MacroServerPools(10)
            se = Selector(msp, self.__version)
            se["Door"] = val["Door"]
            se["OrderedChannels"] = json.dumps([])
            db = tango.Database()
            db.put_device_property(list(self._ms.ms.keys())[0],
                                   {'PoolNames': self._pool.dp.name()})
            pool = self._pool.dp
            pool.ExpChannelList = []
            self._ms.dps[list(self._ms.ms.keys())[0]].Init()

            se["Door"] = val["Door"]
            se["ConfigDevice"] = val["ConfigDevice"]
            se["WriterDevice"] = val["WriterDevice"]
            pm = ProfileManager(se)
            pm.masterTimer = True
            pm.masterTimerFirst = False

            cps = {}
            dss = {}
            # lcp = self.__rnd.randint(1, 40)
            # lds = self.__rnd.randint(1, 40)

            self._cf.dp.SetCommandVariable(["CPDICT", json.dumps(self.mycps)])
            self._cf.dp.SetCommandVariable(["DSDICT", json.dumps(self.mydss)])

            ncps = self.__rnd.randint(1, len(list(self.mycps.keys())) - 1)
            lcps = self.__rnd.sample(list(self.mycps.keys()), ncps)
            for cp in lcps:
                cps[cp] = bool(self.__rnd.randint(0, 1))

            ndss = self.__rnd.randint(1, len(list(self.mycps.keys())) - 1)
            ldss = self.__rnd.sample(list(self.mycps.keys()), ndss)
            for ds in ldss:
                if ds in self.mydss.keys():
                    dss[ds] = bool(self.__rnd.randint(0, 1))

            ndss = self.__rnd.randint(1, len(list(self.mydss.keys())) - 1)
            ldss = self.__rnd.sample(list(self.mydss.keys()), ndss)
            for ds in ldss:
                if ds in self.mydss.keys():
                    dss[ds] = bool(self.__rnd.randint(0, 1))

            mncps = self.__rnd.randint(1, len(list(self.mycps.keys())) - 1)
            mcps = self.__rnd.sample(list(self.mycps.keys()), mncps)

            se["ComponentSelection"] = json.dumps(cps)
            se["DataSourceSelection"] = json.dumps(dss)
            self._cf.dp.SetCommandVariable(["MCPLIST", json.dumps(mcps)])
            ndss = json.loads(se["DataSourceSelection"])
            # common = set(cps) & set(dss)
            self.dump(se)

            dds = pm.componentDataSources()
            rdss = pm.dataSources()
            tdss = [ds for ds in dss if dss[ds] and ds not in dds]

            self.assertEqual(set(tdss), set(rdss))
            self.assertEqual(len(tdss), len(rdss))

    # updateProfile test
    def test_updateProfile_empty(self):
        fun = sys._getframe().f_code.co_name
        print("Run: %s.%s() " % (self.__class__.__name__, fun))
        val = {"ConfigDevice": self._cf.dp.name(),
               "WriterDevice": self._wr.dp.name(),
               "Door": 'doortestp09/testts/t1r228',
               "MntGrp": 'nxsmntgrp'}

        mgt = ProfileManager(None)
        mgt.masterTimer = True
        mgt.masterTimerFirst = False
        self.myAssertRaise(Exception, mgt.updateProfile)

        se = Selector(None, self.__version)
        mgt = ProfileManager(se)
        mgt.masterTimer = True
        mgt.masterTimerFirst = False
        self.myAssertRaise(Exception, mgt.updateProfile)

        msp = MacroServerPools(10)
        se = Selector(msp, self.__version)
        se["Door"] = val["Door"]
        se["ConfigDevice"] = val["ConfigDevice"]
        se["WriterDevice"] = val["WriterDevice"]
        mgt = ProfileManager(se)
        mgt.masterTimer = True
        mgt.masterTimerFirst = False
        self.assertEqual(mgt.availableMntGrps(), [])
        self.myAssertRaise(Exception, mgt.updateProfile)

        db = tango.Database()
        db.put_device_property(list(self._ms.ms.keys())[0],
                               {'PoolNames': self._pool.dp.name()})
        pool = self._pool.dp
        self._ms.dps[list(self._ms.ms.keys())[0]].Init()

        self.assertEqual(mgt.availableMntGrps(), [])

        arr = [
            {"full_name": "test/ct/01/Value", "name": "ct01"},
            {"full_name": "test/ct/02/Value", "name": "ct02"},
            {"full_name": "test/ct/03/value", "name": "ct03"},
            {"full_name": "test/ct/04/value", "name": "ct04"},
            {"full_name": "null/val", "name": "mntgrp_04"},
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
                self.assertEqual(json.loads(se["ComponentPreselection"]), {})
                self.assertEqual(json.loads(se["ComponentSelection"]), {})
                self.assertEqual(json.loads(se["DataSourceSelection"]), {})
                self.assertEqual(json.loads(se["UnplottedComponents"]), [])
                self.assertEqual(json.loads(se["OrderedChannels"]), [])
                self.assertEqual(json.loads(se["UserData"]), {})
                self.assertEqual(json.loads(se["Timer"]), [ar["name"]])
                self.assertEqual(se["MntGrp"], "nxsmntgrp")
                jpcnf = mgt.updateProfile()
                pcnf = json.loads(jpcnf)
                mgdp = tango.DeviceProxy(tmg.new_device_info_writer.name)
                jcnf = mgdp.Configuration
                cnf = json.loads(jcnf)
                self.assertEqual(json.loads(se["ComponentPreselection"]), {})
                self.assertEqual(json.loads(se["ComponentSelection"]), {})
                self.assertEqual(json.loads(se["DataSourceSelection"]), {})
                self.assertEqual(json.loads(se["UnplottedComponents"]), [])
                self.assertEqual(json.loads(se["OrderedChannels"]), [])
                self.assertEqual(json.loads(se["UserData"]), {})
                self.assertEqual(json.loads(se["Timer"]), [ar["name"]])
                self.assertEqual(se["MntGrp"], "nxsmntgrp")
                self.myAssertDict(smg, cnf)
                self.myAssertDict(smg, pcnf)
                se.reset()
                se["Door"] = val["Door"]
                se["ConfigDevice"] = val["ConfigDevice"]
                se["MntGrp"] = "nxsmntgrp"
                se.fetchSelection()
                self.assertEqual(json.loads(se["ComponentPreselection"]), {})
                self.assertEqual(json.loads(se["ComponentSelection"]), {})
                self.assertEqual(json.loads(se["DataSourceSelection"]), {})
                self.assertEqual(json.loads(se["UnplottedComponents"]), [])
                self.assertEqual(json.loads(se["OrderedChannels"]), [])
                self.assertEqual(json.loads(se["UserData"]), {})
                self.assertEqual(json.loads(se["Timer"]), [ar["name"]])
                self.assertEqual(se["MntGrp"], "nxsmntgrp")
            finally:
                try:
                    mgt.deleteProfile("nxsmntgrp")
                finally:
                    tmg.tearDown()

    # updateProfile test
    def test_updateProfile_components_nopool(self):
        fun = sys._getframe().f_code.co_name
        print("Run: %s.%s() " % (self.__class__.__name__, fun))
        val = {"ConfigDevice": self._cf.dp.name(),
               "WriterDevice": self._wr.dp.name(),
               "Door": 'doortestp09/testts/t1r228',
               "MntGrp": 'nxsmntgrp'}

        wrong = ['nn', 'ann', 'nn2', 'tann1', 'tann0', 'tann1b', 'tann1c',
                 'dim1', 'dim2', 'dim3', 'dim4', 'dim5', 'dim5', 'dim6',
                 'dim7', 'dim8', 'tann1c', 'mycp3', 'exp_t01']

        mgt = ProfileManager(None)
        mgt.masterTimer = True
        mgt.masterTimerFirst = False
        self.myAssertRaise(Exception, mgt.updateProfile)

        se = Selector(None, self.__version)
        mgt = ProfileManager(se)
        mgt.masterTimer = True
        mgt.masterTimerFirst = False
        self.myAssertRaise(Exception, mgt.updateProfile)

        msp = MacroServerPools(10)
        se = Selector(msp, self.__version)
        se["Door"] = val["Door"]
        se["ConfigDevice"] = val["ConfigDevice"]
        mgt = ProfileManager(se)
        mgt.masterTimer = True
        mgt.masterTimerFirst = False
        self.assertEqual(mgt.availableMntGrps(), [])
        self.myAssertRaise(Exception, mgt.updateProfile)

        db = tango.Database()
        db.put_device_property(list(self._ms.ms.keys())[0],
                               {'PoolNames': self._pool.dp.name()})
        pool = self._pool.dp
        self._ms.dps[list(self._ms.ms.keys())[0]].Init()

        self.assertEqual(mgt.availableMntGrps(), [])

        arr = [
            {"full_name": "test/ct/01/Value", "name": "ct01"},
            {"full_name": "test/ct/02/Value", "name": "ct02"},
            {"full_name": "test/ct/03/value", "name": "ct03"},
            {"full_name": "test/ct/04/value", "name": "ct04"},
            {"full_name": "null/val", "name": "mntgrp_04"},
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
            # lcp = self.__rnd.randint(1, 40)
            # lds = self.__rnd.randint(1, 40)

            self._cf.dp.SetCommandVariable(["CPDICT", json.dumps(self.mycps)])
            self._cf.dp.SetCommandVariable(["DSDICT", json.dumps(self.mydss)])

            ncps = self.__rnd.randint(1, len(list(self.mycps.keys())) - 1)
            lcps = self.__rnd.sample(list(self.mycps.keys()), ncps)
            for cp in lcps:
                if cp not in wrong:
                    cps[cp] = bool(self.__rnd.randint(0, 1))

            ancps = self.__rnd.randint(1, len(list(self.mycps.keys())) - 1)
            alcps = self.__rnd.sample(list(self.mycps.keys()), ancps)
            for cp in alcps:
                if cp not in wrong:
                    acps[cp] = bool(self.__rnd.randint(0, 1))

            ndss = self.__rnd.randint(1, len(list(self.mycps.keys())) - 1)
            ldss = self.__rnd.sample(list(self.mycps.keys()), ndss)
            for ds in ldss:
                if ds in self.mydss.keys():
                    if ds not in wrong:
                        dss[ds] = bool(self.__rnd.randint(0, 1))

            ndss = self.__rnd.randint(1, len(list(self.mydss.keys())) - 1)
            ldss = self.__rnd.sample(list(self.mydss.keys()), ndss)
            for ds in ldss:
                if ds in self.mydss.keys():
                    if ds not in wrong:
                        dss[ds] = bool(self.__rnd.randint(0, 1))

            mncps = self.__rnd.randint(1, len(list(self.mycps.keys())) - 1)
            mcps = [cp for cp in self.__rnd.sample(
                    list(self.mycps.keys()), mncps) if cp not in wrong]

            se["ComponentSelection"] = json.dumps(cps)
            se["ComponentPreselection"] = json.dumps(acps)
            se["DataSourceSelection"] = json.dumps(dss)
            self._cf.dp.SetCommandVariable(["MCPLIST", json.dumps(mcps)])

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

            se["Timer"] = '["%s"]' % ar["name"]
            se["UserData"] = json.dumps(records)

            tmg = TestMGSetUp.TestMeasurementGroupSetUp(name='nxsmntgrp')
            dv = "/".join(ar["full_name"].split("/")[0:-1])
            smg = {"controllers": {},
                   "monitor": "%s" % dv,
                   "description": "Measurement Group",
                   "timer": "%s" % dv,
                   "label": "nxsmntgrp"}
            try:
                self.myAssertDict(json.loads(se["ComponentPreselection"]),
                                  acps)
                self.myAssertDict(json.loads(se["ComponentSelection"]), cps)
                self.myAssertDict(json.loads(se["DataSourceSelection"]), dss)
                self.assertEqual(json.loads(se["UnplottedComponents"]), [])
                self.assertEqual(json.loads(se["OrderedChannels"]), [])
                self.myAssertDict(json.loads(se["UserData"]), records)
                self.assertEqual(json.loads(se["Timer"]), [ar["name"]])
                self.assertEqual(se["MntGrp"], "nxsmntgrp")
                # print "COMP", mgt.components()
                # print "ACOMP", mgt.preselectedComponents()
                # print "MCP", mcps
                # print "DS", mgt.dataSources()
                # print "DDS", mgt.componentDataSources()
                # print "TIMER", ar["name"]
                # res =
                mgt.cpdescription()
                # acp =
                self._cf.dp.AvailableComponents()
                # mdds = set()

                jpcnf = mgt.updateProfile()
                pcnf = json.loads(jpcnf)
                mgdp = tango.DeviceProxy(tmg.new_device_info_writer.name)
                jcnf = mgdp.Configuration
                cnf = json.loads(jcnf)
                self.myAssertDict(json.loads(se["ComponentPreselection"]),
                                  acps)
                self.myAssertDict(json.loads(se["ComponentSelection"]), cps)
                self.myAssertDict(json.loads(se["DataSourceSelection"]), dss)
                self.assertEqual(json.loads(se["UnplottedComponents"]), [])
                self.assertEqual(json.loads(se["OrderedChannels"]), [])
                self.myAssertDict(json.loads(se["UserData"]), records)
                self.assertEqual(json.loads(se["Timer"]), [ar["name"]])
                self.assertEqual(se["MntGrp"], "nxsmntgrp")
                self.myAssertDict(smg, cnf)
                self.myAssertDict(smg, pcnf)
                se.reset()
                se["Door"] = val["Door"]
                se["ConfigDevice"] = val["ConfigDevice"]
                se["MntGrp"] = "nxsmntgrp"
                se.fetchSelection()
                self.myAssertDict(json.loads(se["ComponentPreselection"]),
                                  acps)
                self.myAssertDict(json.loads(se["ComponentSelection"]), cps)
                self.myAssertDict(json.loads(se["DataSourceSelection"]), dss)
                self.assertEqual(json.loads(se["UnplottedComponents"]), [])
                self.assertEqual(json.loads(se["OrderedChannels"]), [])
                self.myAssertDict(json.loads(se["UserData"]), records)
                self.assertEqual(json.loads(se["Timer"]), [ar["name"]])
                self.assertEqual(se["MntGrp"], "nxsmntgrp")
            finally:
                try:
                    mgt.deleteProfile("nxsmntgrp")
                finally:
                    tmg.tearDown()

    # updateProfile test
    def test_updateProfile_nodevice(self):
        fun = sys._getframe().f_code.co_name
        print("Run: %s.%s() " % (self.__class__.__name__, fun))
        val = {"ConfigDevice": self._cf.dp.name(),
               "WriterDevice": self._wr.dp.name(),
               "Door": 'doortestp09/testts/t1r228',
               "MntGrp": 'nxsmntgrp'}

        wrong = ['nn', 'ann', 'nn2', 'tann1b', 'tann1c',
                 'dim1', 'dim2', 'dim3', 'dim4', 'dim5', 'dim5', 'dim6',
                 'dim7', 'dim8', 'tann1c']
        mgt = ProfileManager(None)
        mgt.masterTimer = True
        mgt.masterTimerFirst = False
        self.myAssertRaise(Exception, mgt.updateProfile)

        se = Selector(None, self.__version)
        mgt = ProfileManager(se)
        mgt.masterTimer = True
        mgt.masterTimerFirst = False
        self.myAssertRaise(Exception, mgt.updateProfile)

        msp = MacroServerPools(10)
        se = Selector(msp, self.__version)
        se["Door"] = val["Door"]
        se["ConfigDevice"] = val["ConfigDevice"]
        mgt = ProfileManager(se)
        mgt.masterTimer = True
        mgt.masterTimerFirst = False
        self.assertEqual(mgt.availableMntGrps(), [])
        self.myAssertRaise(Exception, mgt.updateProfile)

        db = tango.Database()
        db.put_device_property(list(self._ms.ms.keys())[0],
                               {'PoolNames': self._pool.dp.name()})
        pool = self._pool.dp
        self._ms.dps[list(self._ms.ms.keys())[0]].Init()

        self.assertEqual(mgt.availableMntGrps(), [])

        arr = [
            {"full_name": "test/ct/01/Value", "name": "ct01"},
            {"full_name": "test/ct/02/Value", "name": "ct02"},
            {"full_name": "test/ct/03/value", "name": "ct03"},
            {"full_name": "test/ct/04/value", "name": "ct04"},
            {"full_name": "null/val", "name": "mntgrp_04"},
        ]
        pool.AcqChannelList = [json.dumps(a) for a in arr]

        self.myAssertRaise(Exception, mgt.updateProfile)
        self._cf.dp.SetCommandVariable(["CPDICT", json.dumps(self.mycps)])
        self._cf.dp.SetCommandVariable(["DSDICT", json.dumps(self.mydss)])

        ar = arr[0]

        cps = {}
        acps = {}
        dss = {}
        # lcp = self.__rnd.randint(1, 40)
        # lds = self.__rnd.randint(1, 40)

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

            se["ComponentSelection"] = json.dumps(cps)
            se["ComponentPreselection"] = json.dumps(acps)
            se["DataSourceSelection"] = json.dumps(dss)
            self._cf.dp.SetCommandVariable(["MCPLIST", json.dumps(mcps)])

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

            se["Timer"] = '["%s"]' % ar["name"]
            se["UserData"] = json.dumps(records)

            tmg = TestMGSetUp.TestMeasurementGroupSetUp(name='nxsmntgrp')
            # dv = "/".join(ar["full_name"].split("/")[0:-1])
            # smg = {"controllers": {},
            #        "monitor": "%s" % dv,
            #        "description": "Measurement Group",
            #        "timer": "%s" % dv,
            #        "label": "nxsmntgrp"}
            try:
                self.myAssertDict(json.loads(se["ComponentPreselection"]),
                                  acps)
                self.myAssertDict(json.loads(se["ComponentSelection"]), cps)
                self.myAssertDict(json.loads(se["DataSourceSelection"]), dss)
                self.assertEqual(json.loads(se["UnplottedComponents"]), [])
                self.assertEqual(json.loads(se["OrderedChannels"]), [])
                self.myAssertDict(json.loads(se["UserData"]), records)
                self.assertEqual(json.loads(se["Timer"]), [ar["name"]])
                self.assertEqual(se["MntGrp"], "nxsmntgrp")
                # print "COMP", mgt.components()
                # print "ACOMP", mgt.preselectedComponents()
                # print "MCP", mcps
                # print "DS", mgt.dataSources()
                self.myAssertRaise(Exception, mgt.updateProfile)
            finally:
                try:
                    mgt.deleteProfile("nxsmntgrp")
                finally:
                    tmg.tearDown()

    # updateProfile test
    def test_updateProfile_nodevice_cp(self):
        fun = sys._getframe().f_code.co_name
        print("Run: %s.%s() " % (self.__class__.__name__, fun))
        val = {"ConfigDevice": self._cf.dp.name(),
               "WriterDevice": self._wr.dp.name(),
               "Door": 'doortestp09/testts/t1r228',
               "MntGrp": 'nxsmntgrp'}

        wrong = ['mycp3']
        mgt = ProfileManager(None)
        mgt.masterTimer = True
        mgt.masterTimerFirst = False
        self.myAssertRaise(Exception, mgt.updateProfile)

        se = Selector(None, self.__version)
        mgt = ProfileManager(se)
        mgt.masterTimer = True
        mgt.masterTimerFirst = False
        self.myAssertRaise(Exception, mgt.updateProfile)

        msp = MacroServerPools(10)
        se = Selector(msp, self.__version)
        se["Door"] = val["Door"]
        se["ConfigDevice"] = val["ConfigDevice"]
        mgt = ProfileManager(se)
        mgt.masterTimer = True
        mgt.masterTimerFirst = False
        self.assertEqual(mgt.availableMntGrps(), [])
        self.myAssertRaise(Exception, mgt.updateProfile)

        db = tango.Database()
        db.put_device_property(list(self._ms.ms.keys())[0],
                               {'PoolNames': self._pool.dp.name()})
        pool = self._pool.dp
        self._ms.dps[list(self._ms.ms.keys())[0]].Init()

        self.assertEqual(mgt.availableMntGrps(), [])

        arr = [
            {"full_name": "test/ct/01/Value", "name": "ct01"},
            {"full_name": "test/ct/02/Value", "name": "ct02"},
            {"full_name": "test/ct/03/value", "name": "ct03"},
            {"full_name": "test/ct/04/value", "name": "ct04"},
            {"full_name": "null/val", "name": "mntgrp_04"},
        ]
        pool.AcqChannelList = [json.dumps(a) for a in arr]

        self.myAssertRaise(Exception, mgt.updateProfile)
        self._cf.dp.SetCommandVariable(["CPDICT", json.dumps(self.mycps)])
        self._cf.dp.SetCommandVariable(["DSDICT", json.dumps(self.mydss)])

        ar = arr[0]

        cps = {}
        acps = {}
        dss = {}
        # lcp = self.__rnd.randint(1, 40)
        # lds = self.__rnd.randint(1, 40)

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

            se["ComponentSelection"] = json.dumps(cps)
            se["ComponentPreselection"] = json.dumps(acps)
            se["DataSourceSelection"] = json.dumps(dss)
            self._cf.dp.SetCommandVariable(["MCPLIST", json.dumps(mcps)])

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

            se["Timer"] = '["%s"]' % ar["name"]
            se["UserData"] = json.dumps(records)

            tmg = TestMGSetUp.TestMeasurementGroupSetUp(name='nxsmntgrp')
            # dv = "/".join(ar["full_name"].split("/")[0:-1])
            # smg = {"controllers": {},
            #        "monitor": "%s" % dv,
            #        "description": "Measurement Group",
            #        "timer": "%s" % dv,
            #        "label": "nxsmntgrp"}
            try:
                self.myAssertDict(json.loads(se["ComponentPreselection"]),
                                  acps)
                self.myAssertDict(json.loads(se["ComponentSelection"]), cps)
                self.myAssertDict(json.loads(se["DataSourceSelection"]), dss)
                self.assertEqual(json.loads(se["UnplottedComponents"]), [])
                self.assertEqual(json.loads(se["OrderedChannels"]), [])
                self.myAssertDict(json.loads(se["UserData"]), records)
                self.assertEqual(json.loads(se["Timer"]), [ar["name"]])
                self.assertEqual(se["MntGrp"], "nxsmntgrp")
                # print "COMP", mgt.components()
                # print "ACOMP", mgt.preselectedComponents()
                # print "MCP", mcps
                # print "DS", mgt.dataSources()
                self.myAssertRaise(Exception, mgt.updateProfile)
#                mgt.updateProfile()
            finally:
                try:
                    mgt.deleteProfile("nxsmntgrp")
                finally:
                    tmg.tearDown()

    # updateProfile test
    def test_updateProfile_wrongdevice(self):
        fun = sys._getframe().f_code.co_name
        print("Run: %s.%s() " % (self.__class__.__name__, fun))
        val = {"ConfigDevice": self._cf.dp.name(),
               "WriterDevice": self._wr.dp.name(),
               "Door": 'doortestp09/testts/t1r228',
               "MntGrp": 'nxsmntgrp'}

        wrong = ['tann1', 'tann0']
        mgt = ProfileManager(None)
        mgt.masterTimer = True
        mgt.masterTimerFirst = False
        self.myAssertRaise(Exception, mgt.updateProfile)

        se = Selector(None, self.__version)
        mgt = ProfileManager(se)
        mgt.masterTimer = True
        mgt.masterTimerFirst = False
        self.myAssertRaise(Exception, mgt.updateProfile)

        msp = MacroServerPools(10)
        se = Selector(msp, self.__version)
        se["Door"] = val["Door"]
        se["ConfigDevice"] = val["ConfigDevice"]
        mgt = ProfileManager(se)
        mgt.masterTimer = True
        mgt.masterTimerFirst = False
        self.assertEqual(mgt.availableMntGrps(), [])
        self.myAssertRaise(Exception, mgt.updateProfile)

        db = tango.Database()
        db.put_device_property(list(self._ms.ms.keys())[0],
                               {'PoolNames': self._pool.dp.name()})
        pool = self._pool.dp
        self._ms.dps[list(self._ms.ms.keys())[0]].Init()

        self.assertEqual(mgt.availableMntGrps(), [])

        arr = [
            {"full_name": "test/ct/01/Value", "name": "ct01"},
            {"full_name": "test/ct/02/Value", "name": "ct02"},
            {"full_name": "test/ct/03/value", "name": "ct03"},
            {"full_name": "test/ct/04/value", "name": "ct04"},
            {"full_name": "null/val", "name": "mntgrp_04"},
        ]
        pool.AcqChannelList = [json.dumps(a) for a in arr]

        self.myAssertRaise(Exception, mgt.updateProfile)
        self._cf.dp.SetCommandVariable(["CPDICT", json.dumps(self.mycps)])
        self._cf.dp.SetCommandVariable(["DSDICT", json.dumps(self.mydss)])

        ar = arr[0]

        cps = {}
        acps = {}
        dss = {}
        # lcp = self.__rnd.randint(1, 40)
        # lds = self.__rnd.randint(1, 40)

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

            se["ComponentSelection"] = json.dumps(cps)
            se["ComponentPreselection"] = json.dumps(acps)
            se["DataSourceSelection"] = json.dumps(dss)
            self._cf.dp.SetCommandVariable(["MCPLIST", json.dumps(mcps)])

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

            se["Timer"] = '["%s"]' % ar["name"]
            se["UserData"] = json.dumps(records)

            tmg = TestMGSetUp.TestMeasurementGroupSetUp(name='nxsmntgrp')
            # dv = "/".join(ar["full_name"].split("/")[0:-1])
            # smg = {"controllers": {},
            #        "monitor": "%s" % dv,
            #        "description": "Measurement Group",
            #        "timer": "%s" % dv,
            #        "label": "nxsmntgrp"}
            try:
                self.myAssertDict(json.loads(se["ComponentPreselection"]),
                                  acps)
                self.myAssertDict(json.loads(se["ComponentSelection"]), cps)
                self.myAssertDict(json.loads(se["DataSourceSelection"]), dss)
                self.assertEqual(json.loads(se["UnplottedComponents"]), [])
                self.assertEqual(json.loads(se["OrderedChannels"]), [])
                self.myAssertDict(json.loads(se["UserData"]), records)
                self.assertEqual(json.loads(se["Timer"]), [ar["name"]])
                self.assertEqual(se["MntGrp"], "nxsmntgrp")
                # print "COMP", mgt.components()
                # print "ACOMP", mgt.preselectedComponents()
                # print "MCP", mcps
                # print "DS", mgt.dataSources()
#                mgt.updateProfile()
                self.myAssertRaise(Exception, mgt.updateProfile)
            finally:
                try:
                    mgt.deleteProfile("nxsmntgrp")
                finally:
                    tmg.tearDown()

    # updateProfile test
    def test_updateProfile_components_nopool_tango(self):
        fun = sys._getframe().f_code.co_name
        print("Run: %s.%s() " % (self.__class__.__name__, fun))
        val = {"ConfigDevice": self._cf.dp.name(),
               "WriterDevice": self._wr.dp.name(),
               "Door": 'doortestp09/testts/t1r228',
               "MntGrp": 'nxsmntgrp'}

        wrong = []

        mgt = ProfileManager(None)
        mgt.masterTimer = True
        mgt.masterTimerFirst = False
        self.myAssertRaise(Exception, mgt.updateProfile)

        se = Selector(None, self.__version)
        mgt = ProfileManager(se)
        self.myAssertRaise(Exception, mgt.updateProfile)

        msp = MacroServerPools(10)
        se = Selector(msp, self.__version)
        se["Door"] = val["Door"]
        se["ConfigDevice"] = val["ConfigDevice"]
        mgt = ProfileManager(se)
        mgt.masterTimer = True
        mgt.masterTimerFirst = False
        self.assertEqual(mgt.availableMntGrps(), [])
        self.myAssertRaise(Exception, mgt.updateProfile)

        db = tango.Database()
        db.put_device_property(list(self._ms.ms.keys())[0],
                               {'PoolNames': self._pool.dp.name()})
        pool = self._pool.dp
        self._ms.dps[list(self._ms.ms.keys())[0]].Init()

        self.assertEqual(mgt.availableMntGrps(), [])

        arr = [
            {"full_name": "test/ct/01/Value", "name": "ct01"},
            {"full_name": "test/ct/02/Value", "name": "ct02"},
            {"full_name": "test/ct/03/value", "name": "ct03"},
            {"full_name": "test/ct/04/value", "name": "ct04"},
            {"full_name": "null/val", "name": "mntgrp_04"},
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
            # lcp = self.__rnd.randint(1, 40)
            # lds = self.__rnd.randint(1, 40)

            self._cf.dp.SetCommandVariable(["CPDICT", json.dumps(self.smycps)])
            self._cf.dp.SetCommandVariable(["DSDICT", json.dumps(self.smydss)])

            ncps = self.__rnd.randint(1, len(list(self.smycps.keys())) - 1)
            lcps = self.__rnd.sample(list(self.smycps.keys()), ncps)
            for cp in lcps:
                if cp not in wrong:
                    cps[cp] = bool(self.__rnd.randint(0, 1))

            ancps = self.__rnd.randint(1, len(list(self.smycps.keys())) - 1)
            alcps = self.__rnd.sample(list(self.smycps.keys()), ancps)
            for cp in alcps:
                if cp not in wrong:
                    acps[cp] = bool(self.__rnd.randint(0, 1))

            ndss = self.__rnd.randint(1, len(list(self.smycps.keys())) - 1)
            ldss = self.__rnd.sample(list(self.smycps.keys()), ndss)
            for ds in ldss:
                if ds in self.smydss.keys():
                    if ds not in wrong:
                        dss[ds] = bool(self.__rnd.randint(0, 1))

            ndss = self.__rnd.randint(1, len(list(self.smydss.keys())) - 1)
            ldss = self.__rnd.sample(list(self.smydss.keys()), ndss)
            for ds in ldss:
                if ds in self.smydss.keys():
                    if ds not in wrong:
                        dss[ds] = bool(self.__rnd.randint(0, 1))

            mncps = self.__rnd.randint(1, len(list(self.smycps.keys())) - 1)
            mcps = [cp for cp in self.__rnd.sample(
                    list(self.smycps.keys()), mncps) if cp not in wrong]

            se["ComponentSelection"] = json.dumps(cps)
            se["ComponentPreselection"] = json.dumps(acps)
            se["DataSourceSelection"] = json.dumps(dss)
            self._cf.dp.SetCommandVariable(["MCPLIST", json.dumps(mcps)])

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

            se["Timer"] = '["%s"]' % ar["name"]
            se["UserData"] = json.dumps(records)

            tmg = TestMGSetUp.TestMeasurementGroupSetUp(name='nxsmntgrp')
            dv = "/".join(ar["full_name"].split("/")[0:-1])
            chds = mgt.dataSources()
            chds.extend(mgt.componentDataSources())
            chds = sorted([ds for ds in chds if not ds.startswith('client')])

            tgc = {}

            try:
                self.myAssertDict(json.loads(se["ComponentPreselection"]),
                                  acps)
                self.myAssertDict(json.loads(se["ComponentSelection"]), cps)
                self.myAssertDict(json.loads(se["DataSourceSelection"]), dss)
                self.assertEqual(json.loads(se["UnplottedComponents"]), [])
                self.assertEqual(json.loads(se["OrderedChannels"]), [])
                self.myAssertDict(json.loads(se["UserData"]), records)
                self.assertEqual(json.loads(se["Timer"]), [ar["name"]])
                self.assertEqual(se["MntGrp"], "nxsmntgrp")
#                print "COMP", mgt.components()
#                print "ACOMP", mgt.preselectedComponents()
#                print "MCP", mcps
#                print "DS", mgt.dataSources()
#                print "DDS", mgt.componentDataSources()

                res = mgt.cpdescription()
                # mdds = set()
                for mdss in res[0].values():
                    if isinstance(mdss, dict):
                        for ds in mdss.keys():
                            dss[ds] = True

                jpcnf = mgt.updateProfile()
                pcnf = json.loads(jpcnf)
                mgdp = tango.DeviceProxy(tmg.new_device_info_writer.name)
                jcnf = mgdp.Configuration
                cnf = json.loads(jcnf)
                self.myAssertDict(json.loads(se["ComponentPreselection"]),
                                  acps)
                self.myAssertDict(json.loads(se["ComponentSelection"]), cps)
                self.myAssertDict(json.loads(se["DataSourceSelection"]), dss)
                self.assertEqual(json.loads(se["UnplottedComponents"]), [])
                self.assertEqual(json.loads(se["OrderedChannels"]), [])
                self.myAssertDict(json.loads(se["UserData"]), records)
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
                    except Exception:
                        # print ds, cnt
                        raise
                if tgc:
                    smg = {
                        "controllers":
                        {
                            '__tango__':
                            {
                                'channels': tgc,
                                'synchronization': 0,
                            }
                        },
                        "monitor": "%s" % dv,
                        "description": "Measurement Group",
                        "timer": "%s" % dv,
                        "label": "nxsmntgrp"}
                else:
                    smg = {"controllers":
                           {},
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
                self.myAssertDict(json.loads(se["ComponentPreselection"]),
                                  acps)
                self.myAssertDict(json.loads(se["ComponentSelection"]), cps)
                self.myAssertDict(json.loads(se["DataSourceSelection"]), dss)
                self.assertEqual(json.loads(se["UnplottedComponents"]), [])
                self.assertEqual(json.loads(se["OrderedChannels"]), [])
                self.myAssertDict(json.loads(se["UserData"]), records)
                self.assertEqual(json.loads(se["Timer"]), [ar["name"]])
                self.assertEqual(se["MntGrp"], "nxsmntgrp")
            finally:
                try:
                    mgt.deleteProfile("nxsmntgrp")
                finally:
                    tmg.tearDown()

    # updateProfile test
    def test_updateProfile_components_nopool_tango_unplottedcomponents(self):
        fun = sys._getframe().f_code.co_name
        print("Run: %s.%s() " % (self.__class__.__name__, fun))
        val = {"ConfigDevice": self._cf.dp.name(),
               "WriterDevice": self._wr.dp.name(),
               "Door": 'doortestp09/testts/t1r228',
               "MntGrp": 'nxsmntgrp'}

        wrong = []

        mgt = ProfileManager(None)
        mgt.masterTimer = True
        mgt.masterTimerFirst = False
        self.myAssertRaise(Exception, mgt.updateProfile)

        se = Selector(None, self.__version)
        mgt = ProfileManager(se)
        mgt.masterTimer = True
        mgt.masterTimerFirst = False
        self.myAssertRaise(Exception, mgt.updateProfile)

        msp = MacroServerPools(10)
        se = Selector(msp, self.__version)
        se["Door"] = val["Door"]
        se["ConfigDevice"] = val["ConfigDevice"]
        mgt = ProfileManager(se)
        mgt.masterTimer = True
        mgt.masterTimerFirst = False
        self.assertEqual(mgt.availableMntGrps(), [])
        self.myAssertRaise(Exception, mgt.updateProfile)

        db = tango.Database()
        db.put_device_property(list(self._ms.ms.keys())[0],
                               {'PoolNames': self._pool.dp.name()})
        pool = self._pool.dp
        self._ms.dps[list(self._ms.ms.keys())[0]].Init()

        self.assertEqual(mgt.availableMntGrps(), [])

        arr = [
            {"full_name": "test/ct/01/Value", "name": "ct01"},
            {"full_name": "test/ct/02/Value", "name": "ct02"},
            {"full_name": "test/ct/03/value", "name": "ct03"},
            {"full_name": "test/ct/04/value", "name": "ct04"},
            {"full_name": "null/val", "name": "mntgrp_04"},
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
            # lcp = self.__rnd.randint(1, 40)
            # lds = self.__rnd.randint(1, 40)

            self._cf.dp.SetCommandVariable(["CPDICT", json.dumps(self.smycps)])
            self._cf.dp.SetCommandVariable(["DSDICT", json.dumps(self.smydss)])

            comps = set()
            ncps = self.__rnd.randint(1, len(list(self.smycps.keys())) - 1)
            lcps = self.__rnd.sample(list(self.smycps.keys()), ncps)
            for cp in lcps:
                if cp not in wrong:
                    cps[cp] = bool(self.__rnd.randint(0, 1))
                    if cps[cp]:
                        comps.add(cp)

            ancps = self.__rnd.randint(1, len(list(self.smycps.keys())) - 1)
            alcps = self.__rnd.sample(list(self.smycps.keys()), ancps)
            for cp in alcps:
                if cp not in wrong:
                    acps[cp] = bool(self.__rnd.randint(0, 1))
                    if acps[cp]:
                        comps.add(cp)

            ndss = self.__rnd.randint(1, len(list(self.smycps.keys())) - 1)
            ldss = self.__rnd.sample(list(self.smycps.keys()), ndss)
            for ds in ldss:
                if ds in self.smydss.keys():
                    if ds not in wrong:
                        dss[ds] = bool(self.__rnd.randint(0, 1))

            ndss = self.__rnd.randint(1, len(list(self.smydss.keys())) - 1)
            ldss = self.__rnd.sample(list(self.smydss.keys()), ndss)
            for ds in ldss:
                if ds in self.smydss.keys():
                    if ds not in wrong:
                        dss[ds] = bool(self.__rnd.randint(0, 1))

            mncps = self.__rnd.randint(1, len(list(self.smycps.keys())) - 1)
            mcps = [cp for cp in self.__rnd.sample(
                    list(self.smycps.keys()), mncps) if cp not in wrong]
            for cp in mcps:
                comps.add(cp)

            se["ComponentSelection"] = json.dumps(cps)
            se["ComponentPreselection"] = json.dumps(acps)
            se["DataSourceSelection"] = json.dumps(dss)
            self._cf.dp.SetCommandVariable(["MCPLIST", json.dumps(mcps)])

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

            se["Timer"] = '["%s"]' % ar["name"]
            se["UserData"] = json.dumps(records)

            tmg = TestMGSetUp.TestMeasurementGroupSetUp(name='nxsmntgrp')
            dv = "/".join(ar["full_name"].split("/")[0:-1])
            chds = [ds for ds in mgt.dataSources()
                    if not ds.startswith('client')]
            # chds1 = list(chds)
            chds2 = [ds for ds in mgt.componentDataSources()
                     if not ds.startswith('client')]
            chds.extend(chds2)
            chds = sorted(chds)

            lheds = []
            if chds:
                nhe = self.__rnd.randint(0, len(set(chds)) - 1)
                lheds = self.__rnd.sample(list(chds), nhe)

            lhecp = []
            if comps:
                nhe = self.__rnd.randint(0, len(set(comps)) - 1)
                lhecp = self.__rnd.sample(list(comps), nhe)

            lhe = lheds + lhecp

            se["UnplottedComponents"] = json.dumps(lhe)

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

            try:
                self.myAssertDict(json.loads(se["ComponentPreselection"]),
                                  acps)
                self.myAssertDict(json.loads(se["ComponentSelection"]), cps)
                self.myAssertDict(json.loads(se["DataSourceSelection"]), dss)
                self.assertEqual(set(json.loads(se["UnplottedComponents"])),
                                 set(lhe))
                self.assertEqual(json.loads(se["OrderedChannels"]), [])
                self.myAssertDict(json.loads(se["UserData"]), records)
                self.assertEqual(json.loads(se["Timer"]), [ar["name"]])
                self.assertEqual(se["MntGrp"], "nxsmntgrp")

                res = mgt.cpdescription()
                # mdds = set()
                for mdss in res[0].values():
                    if isinstance(mdss, dict):
                        for ds in mdss.keys():
                            dss[ds] = True

                jpcnf = mgt.updateProfile()
                pcnf = json.loads(jpcnf)
                mgdp = tango.DeviceProxy(tmg.new_device_info_writer.name)
                jcnf = mgdp.Configuration
                cnf = json.loads(jcnf)
                self.myAssertDict(json.loads(se["ComponentPreselection"]),
                                  acps)
                self.myAssertDict(json.loads(se["ComponentSelection"]), cps)
                self.myAssertDict(json.loads(se["DataSourceSelection"]), dss)
                self.assertEqual(set(json.loads(se["UnplottedComponents"])),
                                 set(lhe2))
                self.assertEqual(json.loads(se["OrderedChannels"]), [])
                self.myAssertDict(json.loads(se["UserData"]), records)
                self.assertEqual(json.loads(se["Timer"]), [ar["name"]])
                self.assertEqual(se["MntGrp"], "nxsmntgrp")
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
                    except Exception:
                        # print ds, cnt
                        raise
                if tgc:
                    smg = {"controllers":
                           {'__tango__':
                            {'channels': tgc,
                             'synchronization': 0,
                             }},
                           "monitor": "%s" % dv,
                           "description": "Measurement Group",
                           "timer": "%s" % dv,
                           "label": "nxsmntgrp"}
                else:
                    smg = {"controllers":
                           {},
                           "monitor": "%s" % dv,
                           "description": "Measurement Group",
                           "timer": "%s" % dv,
                           "label": "nxsmntgrp"}

                # print "SMG", smg
                # print "PCNF", pcnf
                # print "CNF", cnf
                self.myAssertDict(smg, pcnf)
                self.myAssertDict(pcnf, cnf)
                se.reset()
                se["Door"] = val["Door"]
                se["ConfigDevice"] = val["ConfigDevice"]
                se["MntGrp"] = "nxsmntgrp"
                se.fetchSelection()
                self.myAssertDict(json.loads(se["ComponentPreselection"]),
                                  acps)
                self.myAssertDict(json.loads(se["ComponentSelection"]), cps)
                self.myAssertDict(json.loads(se["DataSourceSelection"]), dss)
                self.assertEqual(set(json.loads(se["UnplottedComponents"])),
                                 set(lhe2))
                self.assertEqual(json.loads(se["OrderedChannels"]), [])
                self.myAssertDict(json.loads(se["UserData"]), records)
                self.assertEqual(json.loads(se["Timer"]), [ar["name"]])
                self.assertEqual(se["MntGrp"], "nxsmntgrp")
            finally:
                try:
                    mgt.deleteProfile("nxsmntgrp")
                finally:
                    tmg.tearDown()

    # updateProfile test
    def test_updateProfile_components_pool_tango(self):
        fun = sys._getframe().f_code.co_name
        print("Run: %s.%s() " % (self.__class__.__name__, fun))
        val = {"ConfigDevice": self._cf.dp.name(),
               "WriterDevice": self._wr.dp.name(),
               "Door": 'doortestp09/testts/t1r228',
               "MntGrp": 'nxsmntgrp'}

        wrong = []

        mgt = ProfileManager(None)
        mgt.masterTimer = True
        mgt.masterTimerFirst = False
        self.myAssertRaise(Exception, mgt.updateProfile)

        se = Selector(None, self.__version)
        mgt = ProfileManager(se)
        mgt.masterTimer = True
        mgt.masterTimerFirst = False
        self.myAssertRaise(Exception, mgt.updateProfile)

        msp = MacroServerPools(10)
        se = Selector(msp, self.__version)
        se["Door"] = val["Door"]
        se["ConfigDevice"] = val["ConfigDevice"]
        mgt = ProfileManager(se)
        mgt.masterTimer = True
        mgt.masterTimerFirst = False
        self.assertEqual(mgt.availableMntGrps(), [])
        self.myAssertRaise(Exception, mgt.updateProfile)

        db = tango.Database()
        db.put_device_property(list(self._ms.ms.keys())[0],
                               {'PoolNames': self._pool.dp.name()})
        pool = self._pool.dp
        self._ms.dps[list(self._ms.ms.keys())[0]].Init()

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

            self.myAssertRaise(Exception, mgt.updateProfile)
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
                    # lcp = self.__rnd.randint(1, 40)
                    # lds = self.__rnd.randint(1, 40)

                    self._cf.dp.SetCommandVariable(
                        ["CPDICT", json.dumps(self.smycps2)])
                    self._cf.dp.SetCommandVariable(
                        ["DSDICT", json.dumps(self.smydssXX)])

                    ncps = self.__rnd.randint(
                        1, len(list(self.smycps2.keys())) - 1)
                    lcps = self.__rnd.sample(list(self.smycps2.keys()), ncps)
                    for cp in lcps:
                        if cp not in wrong:
                            cps[cp] = bool(self.__rnd.randint(0, 1))

                    ancps = self.__rnd.randint(
                        1, len(list(self.smycps2.keys())) - 1)
                    alcps = self.__rnd.sample(list(self.smycps2.keys()), ancps)
                    for cp in alcps:
                        if cp not in wrong:
                            acps[cp] = bool(self.__rnd.randint(0, 1))

                    ndss = self.__rnd.randint(
                        1, len(list(self.smycps2.keys())) - 1)
                    ldss = self.__rnd.sample(list(self.smycps2.keys()), ndss)
                    for ds in ldss:
                        if ds in self.smydssXX.keys():
                            if ds not in wrong:
                                dss[ds] = bool(self.__rnd.randint(0, 1))

                    ndss = self.__rnd.randint(
                        1, len(list(self.smydssXX.keys())) - 1)
                    ldss = self.__rnd.sample(list(self.smydssXX.keys()), ndss)
                    for ds in ldss:
                        if ds in self.smydssXX.keys():
                            if ds not in wrong:
                                dss[ds] = bool(self.__rnd.randint(0, 1))

                    mncps = self.__rnd.randint(
                        1, len(list(self.smycps2.keys())) - 1)
                    mcps = [
                        cp for cp in self.__rnd.sample(
                            list(self.smycps2.keys()), mncps)
                        if cp not in wrong]

                    adss = dict(dss)
                    for ch in expch:
                        if ch["name"] not in adss.keys():
                            adss[ch["name"]] = False
                    se["ComponentSelection"] = json.dumps(cps)
                    se["ComponentPreselection"] = json.dumps(acps)
                    se["DataSourceSelection"] = json.dumps(dss)
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
                        list(dss.keys()), dstype='CLIENT')[0]
                    for dsr in dsres.values():
                        records[str(dsr.record)] = '2345'

                    se["Timer"] = '["%s"]' % ar["name"]
                    se["UserData"] = json.dumps(records)

                    tmg = TestMGSetUp.TestMeasurementGroupSetUp(
                        name='nxsmntgrp')
                    dv = "/".join(ar["full_name"].split("/")[0:-1])
                    chds = mgt.dataSources()
                    chds.extend(mgt.componentDataSources())
                    chds = sorted([
                        ds for ds in chds if not ds.startswith('client')])

                    self.myAssertDict(
                        json.loads(se["ComponentPreselection"]),
                        acps)
                    self.myAssertDict(
                        json.loads(se["ComponentSelection"]), cps)
                    self.myAssertDict(
                        json.loads(se["DataSourceSelection"]), adss)
                    self.assertEqual(json.loads(se["UnplottedComponents"]), [])
                    self.assertEqual(json.loads(se["OrderedChannels"]), pdss)
                    self.myAssertDict(json.loads(se["UserData"]), records)
                    self.assertEqual(json.loads(se["Timer"]), [ar["name"]])
                    self.assertEqual(se["MntGrp"], "nxsmntgrp")

                    res = mgt.cpdescription()
                    # mdds = set()
                    for mdss in res[0].values():
                        if isinstance(mdss, dict):
                            for ds in mdss.keys():
                                adss[ds] = True

                    jpcnf = mgt.updateProfile()
                    pcnf = json.loads(jpcnf)
                    mgdp = tango.DeviceProxy(tmg.new_device_info_writer.name)
                    jcnf = mgdp.Configuration
                    cnf = json.loads(jcnf)
                    self.myAssertDict(
                        json.loads(se["ComponentPreselection"]),
                        acps)
                    self.myAssertDict(
                        json.loads(se["ComponentSelection"]), cps)
                    self.myAssertDict(
                        json.loads(se["DataSourceSelection"]), adss)
                    self.assertEqual(json.loads(se["UnplottedComponents"]), [])
                    self.assertEqual(json.loads(se["OrderedChannels"]), pdss)
                    self.myAssertDict(json.loads(se["UserData"]), records)
                    self.assertEqual(json.loads(se["Timer"]), [ar["name"]])
                    self.assertEqual(se["MntGrp"], "nxsmntgrp")
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
                                except Exception:
                                    raise
                        if tgc:
                            myctrls[cl] = {'channels': tgc,
                                           'monitor': ttdv,
                                           'synchronization': 0,
                                           'synchronizer': 'software',
                                           'timer': ttdv,
                                           }

                    smg = {"controllers": myctrls,
                           "monitor": "%s" % dv,
                           "description": "Measurement Group",
                           "timer": "%s" % dv,
                           "label": "nxsmntgrp"}
                    self.myAssertDict(smg, pcnf)
                    self.myAssertDict(pcnf, cnf)
                    se.reset()
                    se["Door"] = val["Door"]
                    se["ConfigDevice"] = val["ConfigDevice"]
                    se["MntGrp"] = "nxsmntgrp"
                    se.fetchSelection()
                    self.myAssertDict(
                        json.loads(se["ComponentPreselection"]),
                        acps)
                    self.myAssertDict(
                        json.loads(se["ComponentSelection"]), cps)
                    self.myAssertDict(
                        json.loads(se["DataSourceSelection"]), adss)
                    self.assertEqual(json.loads(se["UnplottedComponents"]), [])
                    self.assertEqual(json.loads(se["OrderedChannels"]), pdss)
                    self.myAssertDict(json.loads(se["UserData"]), records)
                    self.assertEqual(json.loads(se["Timer"]), [ar["name"]])
                    self.assertEqual(se["MntGrp"], "nxsmntgrp")
                finally:
                    try:
                        mgt.deleteProfile("nxsmntgrp")
                    finally:
                        tmg.tearDown()
        finally:
            simp2.tearDown()

    # updateProfile test
    def test_updateProfile_components_pool_tango_unplottedcomponents(self):
        fun = sys._getframe().f_code.co_name
        print("Run: %s.%s() " % (self.__class__.__name__, fun))
        val = {"ConfigDevice": self._cf.dp.name(),
               "WriterDevice": self._wr.dp.name(),
               "Door": 'doortestp09/testts/t1r228',
               "MntGrp": 'nxsmntgrp'}

        wrong = []

        mgt = ProfileManager(None)
        mgt.masterTimer = True
        mgt.masterTimerFirst = False
        self.myAssertRaise(Exception, mgt.updateProfile)

        se = Selector(None, self.__version)
        mgt = ProfileManager(se)
        mgt.masterTimer = True
        mgt.masterTimerFirst = False
        self.myAssertRaise(Exception, mgt.updateProfile)

        msp = MacroServerPools(10)
        se = Selector(msp, self.__version)
        se["Door"] = val["Door"]
        se["ConfigDevice"] = val["ConfigDevice"]
        mgt = ProfileManager(se)
        mgt.masterTimer = True
        mgt.masterTimerFirst = False
        self.assertEqual(mgt.availableMntGrps(), [])
        self.myAssertRaise(Exception, mgt.updateProfile)

        db = tango.Database()
        db.put_device_property(list(self._ms.ms.keys())[0],
                               {'PoolNames': self._pool.dp.name()})
        pool = self._pool.dp
        self._ms.dps[list(self._ms.ms.keys())[0]].Init()

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

            self.myAssertRaise(Exception, mgt.updateProfile)
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
                    # lcp = self.__rnd.randint(1, 40)
                    # lds = self.__rnd.randint(1, 40)

                    self._cf.dp.SetCommandVariable(
                        ["CPDICT", json.dumps(self.smycps2)])
                    self._cf.dp.SetCommandVariable(
                        ["DSDICT", json.dumps(self.smydssXX)])
                    comps = set()

                    ncps = self.__rnd.randint(
                        1, len(list(self.smycps2.keys())) - 1)
                    lcps = self.__rnd.sample(list(self.smycps2.keys()), ncps)
                    for cp in lcps:
                        if cp not in wrong:
                            cps[cp] = bool(self.__rnd.randint(0, 1))
                            if cps[cp]:
                                comps.add(cp)

                    ancps = self.__rnd.randint(
                        1, len(list(self.smycps2.keys())) - 1)
                    alcps = self.__rnd.sample(list(self.smycps2.keys()), ancps)
                    for cp in alcps:
                        if cp not in wrong:
                            acps[cp] = bool(self.__rnd.randint(0, 1))
                            if acps[cp]:
                                comps.add(cp)

                    ndss = self.__rnd.randint(
                        1, len(list(self.smycps2.keys())) - 1)
                    ldss = self.__rnd.sample(list(self.smycps2.keys()), ndss)
                    for ds in ldss:
                        if ds in self.smydssXX.keys():
                            if ds not in wrong:
                                dss[ds] = bool(self.__rnd.randint(0, 1))

                    ndss = self.__rnd.randint(
                        1, len(list(self.smydssXX.keys())) - 1)
                    ldss = self.__rnd.sample(list(self.smydssXX.keys()), ndss)
                    for ds in ldss:
                        if ds in self.smydssXX.keys():
                            if ds not in wrong:
                                dss[ds] = bool(self.__rnd.randint(0, 1))

                    mncps = self.__rnd.randint(
                        1, len(list(self.smycps2.keys())) - 1)
                    mcps = [cp for cp in self.__rnd.sample(
                            list(self.smycps2.keys()), mncps)
                            if cp not in wrong]
                    for cp in mcps:
                        comps.add(cp)

                    adss = dict(dss)
                    for ch in expch:
                        if ch["name"] not in adss.keys():
                            adss[ch["name"]] = False
                    se["ComponentSelection"] = json.dumps(cps)
                    se["ComponentPreselection"] = json.dumps(acps)
                    se["DataSourceSelection"] = json.dumps(dss)
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
                        list(dss.keys()), dstype='CLIENT')[0]
                    for dsr in dsres.values():
                        records[str(dsr.record)] = '2345'

                    se["Timer"] = '["%s"]' % ar["name"]
                    se["UserData"] = json.dumps(records)

                    tmg = TestMGSetUp.TestMeasurementGroupSetUp(
                        name='nxsmntgrp')
                    dv = "/".join(ar["full_name"].split("/")[0:-1])
                    chds = [ds for ds in mgt.dataSources()
                            if not ds.startswith('client')]
                    # chds1 = list(chds)
                    chds2 = [ds for ds in mgt.componentDataSources()
                             if not ds.startswith('client')]
                    chds.extend(chds2)
                    chds = sorted(chds)

                    lheds = []
                    if chds:
                        nhe = self.__rnd.randint(0, len(set(chds)) - 1)
                        lheds = self.__rnd.sample(list(chds), nhe)

                    lhecp = []
                    if comps:
                        nhe = self.__rnd.randint(0, len(set(comps)) - 1)
                        lhecp = self.__rnd.sample(list(comps), nhe)

                    lhe = lheds + lhecp

                    se["UnplottedComponents"] = json.dumps(lhe)

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
                        json.loads(se["ComponentPreselection"]),
                        acps)
                    self.myAssertDict(
                        json.loads(se["ComponentSelection"]), cps)
                    self.myAssertDict(
                        json.loads(se["DataSourceSelection"]), adss)
                    self.assertEqual(
                        set(json.loads(se["UnplottedComponents"])),
                        set(lhe))
                    self.assertEqual(json.loads(se["OrderedChannels"]), pdss)
                    self.myAssertDict(json.loads(se["UserData"]), records)
                    self.assertEqual(json.loads(se["Timer"]), [ar["name"]])
                    self.assertEqual(se["MntGrp"], "nxsmntgrp")

                    res = mgt.cpdescription()
                    # mdds = set()
                    for mdss in res[0].values():
                        if isinstance(mdss, dict):
                            for ds in mdss.keys():
                                adss[ds] = True

                    jpcnf = mgt.updateProfile()
                    pcnf = json.loads(jpcnf)
                    mgdp = tango.DeviceProxy(tmg.new_device_info_writer.name)
                    jcnf = mgdp.Configuration
                    cnf = json.loads(jcnf)
                    self.myAssertDict(
                        json.loads(se["ComponentPreselection"]),
                        acps)
                    self.myAssertDict(
                        json.loads(se["ComponentSelection"]), cps)
                    self.myAssertDict(
                        json.loads(se["DataSourceSelection"]), adss)
                    self.assertEqual(
                        set(json.loads(se["UnplottedComponents"])),
                        set(lhe2))
                    self.assertEqual(json.loads(se["OrderedChannels"]), pdss)
                    self.myAssertDict(json.loads(se["UserData"]), records)
                    self.assertEqual(json.loads(se["Timer"]), [ar["name"]])
                    self.assertEqual(se["MntGrp"], "nxsmntgrp")
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
                                except Exception:
                                    raise
                        if tgc:
                            myctrls[cl] = {
                                'channels': tgc,
                                'monitor': ttdv,
                                'timer': ttdv,
                                'synchronization': 0,
                                'synchronizer': 'software',
                            }

                    smg = {"controllers": myctrls,
                           "monitor": "%s" % dv,
                           "description": "Measurement Group",
                           "timer": "%s" % dv,
                           "label": "nxsmntgrp"}
                    self.myAssertDict(smg, pcnf)
                    self.myAssertDict(pcnf, cnf)
                    se.reset()
                    se["Door"] = val["Door"]
                    se["ConfigDevice"] = val["ConfigDevice"]
                    se["MntGrp"] = "nxsmntgrp"
                    se.fetchSelection()
                    self.myAssertDict(
                        json.loads(se["ComponentPreselection"]),
                        acps)
                    self.myAssertDict(
                        json.loads(se["ComponentSelection"]), cps)
                    self.myAssertDict(
                        json.loads(se["DataSourceSelection"]), adss)
                    self.assertEqual(
                        set(json.loads(se["UnplottedComponents"])),
                        set(lhe2))
                    self.assertEqual(json.loads(se["OrderedChannels"]), pdss)
                    self.myAssertDict(json.loads(se["UserData"]), records)
                    self.assertEqual(json.loads(se["Timer"]), [ar["name"]])
                    self.assertEqual(se["MntGrp"], "nxsmntgrp")
                finally:
                    try:
                        mgt.deleteProfile("nxsmntgrp")
                    finally:
                        tmg.tearDown()
        finally:
            simp2.tearDown()

    # updateProfile test
    def test_updateProfile_components_mixed_tango_unplottedcomponents(self):
        fun = sys._getframe().f_code.co_name
        print("Run: %s.%s() " % (self.__class__.__name__, fun))
        val = {"ConfigDevice": self._cf.dp.name(),
               "WriterDevice": self._wr.dp.name(),
               "Door": 'doortestp09/testts/t1r228',
               "MntGrp": 'nxsmntgrp2'}

        wrong = []

        mgt = ProfileManager(None)
        mgt.masterTimer = True
        mgt.masterTimerFirst = False
        self.myAssertRaise(Exception, mgt.updateProfile)

        se = Selector(None, self.__version)
        mgt = ProfileManager(se)
        mgt.masterTimer = True
        mgt.masterTimerFirst = False
        self.myAssertRaise(Exception, mgt.updateProfile)

        msp = MacroServerPools(10)
        se = Selector(msp, self.__version)
        se["Door"] = val["Door"]
        se["ConfigDevice"] = val["ConfigDevice"]
        se["MntGrp"] = val["MntGrp"]
        mgt = ProfileManager(se)
        mgt.masterTimer = True
        mgt.masterTimerFirst = False
        self.assertEqual(mgt.availableMntGrps(), [])
        self.myAssertRaise(Exception, mgt.updateProfile)

        db = tango.Database()
        db.put_device_property(list(self._ms.ms.keys())[0],
                               {'PoolNames': self._pool.dp.name()})
        pool = self._pool.dp
        self._ms.dps[list(self._ms.ms.keys())[0]].Init()

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

            self.myAssertRaise(Exception, mgt.updateProfile)
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
                    # lcp = self.__rnd.randint(1, 40)
                    # lds = self.__rnd.randint(1, 40)

                    self._cf.dp.SetCommandVariable(
                        ["CPDICT", json.dumps(amycps)])
                    self._cf.dp.SetCommandVariable(
                        ["DSDICT", json.dumps(amydss)])
                    comps = set()

                    ncps = self.__rnd.randint(1, len(amycps) - 1)
                    lcps = self.__rnd.sample(list(amycps.keys()), ncps)
                    for cp in lcps:
                        if cp not in wrong:
                            cps[cp] = bool(self.__rnd.randint(0, 1))
                            if cps[cp]:
                                comps.add(cp)

                    ancps = self.__rnd.randint(1, len(list(amycps.keys())) - 1)
                    alcps = self.__rnd.sample(list(amycps.keys()), ancps)
                    for cp in alcps:
                        if cp not in wrong:
                            acps[cp] = bool(self.__rnd.randint(0, 1))
                            if acps[cp]:
                                comps.add(cp)

                    ndss = self.__rnd.randint(1, len(list(amycps.keys())) - 1)
                    ldss = self.__rnd.sample(list(amycps.keys()), ndss)
                    for ds in ldss:
                        if ds in amydss.keys():
                            if ds not in wrong:
                                dss[ds] = bool(self.__rnd.randint(0, 1))

                    ndss = self.__rnd.randint(1, len(list(amydss.keys())) - 1)
                    ldss = self.__rnd.sample(list(amydss.keys()), ndss)
                    for ds in ldss:
                        if ds in amydss.keys():
                            if ds not in wrong:
                                dss[ds] = bool(self.__rnd.randint(0, 1))

                    mncps = self.__rnd.randint(1, len(list(amycps.keys())) - 1)
                    mcps = [cp for cp in self.__rnd.sample(
                            list(amycps.keys()), mncps) if cp not in wrong]
                    for cp in mcps:
                        comps.add(cp)

                    adss = dict(dss)
                    for ch in expch:
                        if ch["name"] not in adss.keys():
                            adss[ch["name"]] = False
                    se["ComponentSelection"] = json.dumps(cps)
                    se["ComponentPreselection"] = json.dumps(acps)
                    se["DataSourceSelection"] = json.dumps(dss)
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
                        list(dss.keys()), dstype='CLIENT')[0]
                    for dsr in dsres.values():
                        records[str(dsr.record)] = '2345'

                    se["Timer"] = '["%s"]' % ar["name"]
                    se["UserData"] = json.dumps(records)

                    tmg = TestMGSetUp.TestMeasurementGroupSetUp(
                        name='nxsmntgrp2')
                    dv = "/".join(ar["full_name"].split("/")[0:-1])
                    chds = [ds for ds in mgt.dataSources()
                            if not ds.startswith('client')]
                    # chds1 = list(chds)
                    chds2 = [ds for ds in mgt.componentDataSources()
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
                        lheds = self.__rnd.sample(list(chds), nhe)

                    lhecp = []
                    if comps:
                        nhe = self.__rnd.randint(0, len(set(comps)) - 1)
                        lhecp = self.__rnd.sample(list(comps), nhe)

                    lhe = lheds + lhecp

                    se["UnplottedComponents"] = json.dumps(lhe)
                    se["OrderedChannels"] = json.dumps(pdss)

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
                        json.loads(se["ComponentPreselection"]),
                        acps)
                    self.myAssertDict(
                        json.loads(se["ComponentSelection"]), cps)
                    self.myAssertDict(
                        json.loads(se["DataSourceSelection"]), adss)
                    self.assertEqual(
                        set(json.loads(se["UnplottedComponents"])),
                        set(lhe))
                    self.assertEqual(json.loads(se["OrderedChannels"]), pdss)
                    self.myAssertDict(json.loads(se["UserData"]), records)
                    self.assertEqual(json.loads(se["Timer"]), [ar["name"]])
                    self.assertEqual(se["MntGrp"], "nxsmntgrp2")

                    res = mgt.cpdescription()
                    # mdds = set()
                    for mdss in res[0].values():
                        if isinstance(mdss, dict):
                            for ds in mdss.keys():
                                adss[ds] = True

                    jpcnf = mgt.updateProfile()
                    pcnf = json.loads(jpcnf)
                    mgdp = tango.DeviceProxy(tmg.new_device_info_writer.name)
                    jcnf = mgdp.Configuration
                    cnf = json.loads(jcnf)
                    self.myAssertDict(
                        json.loads(se["ComponentPreselection"]),
                        acps)
                    self.myAssertDict(
                        json.loads(se["ComponentSelection"]), cps)
                    self.myAssertDict(
                        json.loads(se["DataSourceSelection"]), adss)
                    self.assertEqual(
                        set(json.loads(se["UnplottedComponents"])),
                        set(lhe2))
                    self.assertEqual(json.loads(se["OrderedChannels"]), pdss)
                    self.myAssertDict(json.loads(se["UserData"]), records)
                    self.assertEqual(json.loads(se["Timer"]), [ar["name"]])
                    self.assertEqual(se["MntGrp"], "nxsmntgrp2")
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
                            myctrls[cl] = {'channels': tgc,
                                           'monitor': ttdv,
                                           'timer': ttdv,
                                           'synchronization': 0,
                                           'synchronizer': 'software',
                                           }

                    tgc = {}
                    for ds in chds:
                        if ds in self.smychs:
                            cnt = self.smychs[str(ds)]
                            i = chds.index(str(ds))
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
                            except Exception:
                                raise
                    if tgc:
                        myctrls['__tango__'] = {'channels': tgc,
                                                'synchronization': 0,
                                                }

                    smg = {"controllers": myctrls,
                           "monitor": "%s" % dv,
                           "description": "Measurement Group",
                           "timer": "%s" % dv,
                           "label": "nxsmntgrp2"}
                    self.myAssertDict(smg, pcnf)
                    self.myAssertDict(pcnf, cnf)
                    se.reset()
                    se["Door"] = val["Door"]
                    se["ConfigDevice"] = val["ConfigDevice"]
                    se["MntGrp"] = "nxsmntgrp2"
                    se.fetchSelection()
                    self.myAssertDict(
                        json.loads(se["ComponentPreselection"]),
                        acps)
                    self.myAssertDict(
                        json.loads(se["ComponentSelection"]), cps)
                    self.myAssertDict(
                        json.loads(se["DataSourceSelection"]), adss)
                    self.assertEqual(
                        set(json.loads(se["UnplottedComponents"])),
                        set(lhe2))
                    self.assertEqual(json.loads(se["OrderedChannels"]), pdss)
                    self.myAssertDict(json.loads(se["UserData"]), records)
                    self.assertEqual(json.loads(se["Timer"]), [ar["name"]])
                    self.assertEqual(se["MntGrp"], "nxsmntgrp2")
                finally:
                    try:
                        mgt.deleteProfile("nxsmntgrp2")
                    finally:
                        tmg.tearDown()
        finally:
            simp2.tearDown()

    # updateProfile test
    def test_updateProfile_components_mixed_tango_orderedchannels(self):
        fun = sys._getframe().f_code.co_name
        print("Run: %s.%s() " % (self.__class__.__name__, fun))
        val = {"ConfigDevice": self._cf.dp.name(),
               "WriterDevice": self._wr.dp.name(),
               "Door": 'doortestp09/testts/t1r228',
               "MntGrp": 'mg2'}

        wrong = []

        mgt = ProfileManager(None)
        mgt.masterTimer = True
        mgt.masterTimerFirst = False
        self.myAssertRaise(Exception, mgt.updateProfile)

        se = Selector(None, self.__version)
        mgt = ProfileManager(se)
        mgt.masterTimer = True
        mgt.masterTimerFirst = False
        self.myAssertRaise(Exception, mgt.updateProfile)

        msp = MacroServerPools(10)
        se = Selector(msp, self.__version)
        se["Door"] = val["Door"]
        se["ConfigDevice"] = val["ConfigDevice"]
        se["MntGrp"] = val["MntGrp"]
        mgt = ProfileManager(se)
        mgt.masterTimer = True
        mgt.masterTimerFirst = False
        self.assertEqual(mgt.availableMntGrps(), [])
        self.myAssertRaise(Exception, mgt.updateProfile)

        db = tango.Database()
        db.put_device_property(list(self._ms.ms.keys())[0],
                               {'PoolNames': self._pool.dp.name()})
        pool = self._pool.dp
        self._ms.dps[list(self._ms.ms.keys())[0]].Init()

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

            self.myAssertRaise(Exception, mgt.updateProfile)
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
                    # lcp = self.__rnd.randint(1, 40)
                    # lds = self.__rnd.randint(1, 40)

                    self._cf.dp.SetCommandVariable(
                        ["CPDICT", json.dumps(amycps)])
                    self._cf.dp.SetCommandVariable(
                        ["DSDICT", json.dumps(amydss)])
                    comps = set()

                    ncps = self.__rnd.randint(1, len(amycps) - 1)
                    lcps = self.__rnd.sample(list(amycps.keys()), ncps)
                    for cp in lcps:
                        if cp not in wrong:
                            cps[cp] = bool(self.__rnd.randint(0, 1))
                            if cps[cp]:
                                comps.add(cp)

                    ancps = self.__rnd.randint(1, len(list(amycps.keys())) - 1)
                    alcps = self.__rnd.sample(list(amycps.keys()), ancps)
                    for cp in alcps:
                        if cp not in wrong:
                            acps[cp] = bool(self.__rnd.randint(0, 1))
                            if acps[cp]:
                                comps.add(cp)

                    ndss = self.__rnd.randint(1, len(list(amycps.keys())) - 1)
                    ldss = self.__rnd.sample(list(amycps.keys()), ndss)
                    for ds in ldss:
                        if ds in amydss.keys():
                            if ds not in wrong:
                                dss[ds] = bool(self.__rnd.randint(0, 1))

                    ndss = self.__rnd.randint(1, len(list(amydss.keys())) - 1)
                    ldss = self.__rnd.sample(list(amydss.keys()), ndss)
                    for ds in ldss:
                        if ds in amydss.keys():
                            if ds not in wrong:
                                dss[ds] = bool(self.__rnd.randint(0, 1))

                    mncps = self.__rnd.randint(1, len(list(amycps.keys())) - 1)
                    mcps = [cp for cp in self.__rnd.sample(
                        list(amycps.keys()), mncps) if cp not in wrong]
                    for cp in mcps:
                        comps.add(cp)

                    adss = dict(dss)
                    for ch in expch:
                        if ch["name"] not in adss.keys():
                            adss[ch["name"]] = False
                    se["ComponentSelection"] = json.dumps(cps)
                    se["ComponentPreselection"] = json.dumps(acps)
                    se["DataSourceSelection"] = json.dumps(dss)
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
                        list(dss.keys()), dstype='CLIENT')[0]
                    for dsr in dsres.values():
                        records[str(dsr.record)] = '2345'

                    se["Timer"] = '["%s"]' % ar["name"]
                    se["UserData"] = json.dumps(records)

                    tmg = TestMGSetUp.TestMeasurementGroupSetUp(
                        name='mg2')
                    dv = "/".join(ar["full_name"].split("/")[0:-1])
                    chds = [ds for ds in mgt.dataSources()
                            if not ds.startswith('client')]
                    # chds1 = list(chds)
                    chds2 = [ds for ds in mgt.componentDataSources()
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
                        lheds = self.__rnd.sample(list(chds), nhe)

                    lhecp = []
                    if comps:
                        nhe = self.__rnd.randint(0, len(set(comps)) - 1)
                        lhecp = self.__rnd.sample(list(comps), nhe)

                    lhe = lheds + lhecp

                    se["UnplottedComponents"] = json.dumps(lhe)
                    se["OrderedChannels"] = json.dumps(pdss)

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
                        json.loads(se["ComponentPreselection"]),
                        acps)
                    self.myAssertDict(
                        json.loads(se["ComponentSelection"]), cps)
                    self.myAssertDict(
                        json.loads(se["DataSourceSelection"]), adss)
                    self.assertEqual(
                        set(json.loads(se["UnplottedComponents"])),
                        set(lhe))
                    self.assertEqual(json.loads(se["OrderedChannels"]), pdss)
                    self.myAssertDict(json.loads(se["UserData"]), records)
                    self.assertEqual(json.loads(se["Timer"]), [ar["name"]])
                    self.assertEqual(se["MntGrp"], "mg2")

                    res = mgt.cpdescription()
                    # mdds = set()
                    for mdss in res[0].values():
                        if isinstance(mdss, dict):
                            for ds in mdss.keys():
                                adss[ds] = True

                    jpcnf = mgt.updateProfile()
                    pcnf = json.loads(jpcnf)
                    mgdp = tango.DeviceProxy(tmg.new_device_info_writer.name)
                    jcnf = mgdp.Configuration
                    cnf = json.loads(jcnf)
                    self.myAssertDict(
                        json.loads(se["ComponentPreselection"]),
                        acps)
                    self.myAssertDict(
                        json.loads(se["ComponentSelection"]), cps)
                    self.myAssertDict(
                        json.loads(se["DataSourceSelection"]), adss)
                    self.assertEqual(
                        set(json.loads(se["UnplottedComponents"])),
                        set(lhe2))
                    self.assertEqual(json.loads(se["OrderedChannels"]), pdss)
                    self.myAssertDict(json.loads(se["UserData"]), records)
                    self.assertEqual(json.loads(se["Timer"]), [ar["name"]])
                    self.assertEqual(se["MntGrp"], "mg2")
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
                            myctrls[cl] = {'channels': tgc,
                                           'monitor': ttdv,
                                           'synchronization': 0,
                                           'synchronizer': 'software',
                                           'timer': ttdv}

                    tgc = {}
                    for ds in chds:
                        if ds in self.smychs:
                            cnt = self.smychs[str(ds)]
                            i = chds.index(str(ds))
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
                            except Exception:
                                raise

                    if tgc:
                        myctrls['__tango__'] = {'channels': tgc,
                                                'synchronization': 0}

                    smg = {"controllers": myctrls,
                           "monitor": "%s" % dv,
                           "description": "Measurement Group",
                           "timer": "%s" % dv,
                           "label": "mg2"}
#                    print "SMG", smg
                    self.myAssertDict(smg, pcnf)
                    self.myAssertDict(pcnf, cnf)
                    se.reset()
                    se["Door"] = val["Door"]
                    se["ConfigDevice"] = val["ConfigDevice"]
                    se["MntGrp"] = "mg2"
                    se.fetchSelection()
                    self.myAssertDict(
                        json.loads(se["ComponentPreselection"]),
                        acps)
                    self.myAssertDict(
                        json.loads(se["ComponentSelection"]), cps)
                    self.myAssertDict(
                        json.loads(se["DataSourceSelection"]), adss)
                    self.assertEqual(
                        set(json.loads(se["UnplottedComponents"])),
                        set(lhe2))
                    self.assertEqual(json.loads(se["OrderedChannels"]), pdss)
                    self.myAssertDict(json.loads(se["UserData"]), records)
                    self.assertEqual(json.loads(se["Timer"]), [ar["name"]])
                    self.assertEqual(se["MntGrp"], "mg2")
                finally:
                    mgt.deleteProfile("mg2")
                    try:
                        tmg.tearDown()
                    except Exception:
                        pass
        finally:
            simp2.tearDown()

    # updateProfile test
    def test_updateProfile_components_mixed_tango_timers(self):
        fun = sys._getframe().f_code.co_name
        print("Run: %s.%s() " % (self.__class__.__name__, fun))
        val = {"ConfigDevice": self._cf.dp.name(),
               "WriterDevice": self._wr.dp.name(),
               "Door": 'doortestp09/testts/t1r228',
               "MntGrp": 'mg2'}

        wrong = []

        mgt = ProfileManager(None)
        mgt.masterTimer = True
        mgt.masterTimerFirst = False
        self.myAssertRaise(Exception, mgt.updateProfile)

        se = Selector(None, self.__version)
        mgt = ProfileManager(se)
        mgt.masterTimer = True
        mgt.masterTimerFirst = False
        self.myAssertRaise(Exception, mgt.updateProfile)

        msp = MacroServerPools(10)
        se = Selector(msp, self.__version)
        se["Door"] = val["Door"]
        se["ConfigDevice"] = val["ConfigDevice"]
        se["MntGrp"] = val["MntGrp"]
        mgt = ProfileManager(se)
        mgt.masterTimer = True
        mgt.masterTimerFirst = False
        self.assertEqual(mgt.availableMntGrps(), [])
        self.myAssertRaise(Exception, mgt.updateProfile)

        db = tango.Database()
        db.put_device_property(list(self._ms.ms.keys())[0],
                               {'PoolNames': self._pool.dp.name()})
        pool = self._pool.dp
        self._ms.dps[list(self._ms.ms.keys())[0]].Init()

        self.assertEqual(mgt.availableMntGrps(), [])
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
                tms = self.__rnd.sample(list(
                    [ch for ch in self.smychsXX.keys()
                     if not ch.startswith("client")]), ntms)
                for tm in tms:
                    myct = ("ctrl_%s" % tm).replace("_", "/")
                    timers[myct] = tm
                    ctrls.append(myct)
                ltimers = list(timers.values())

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
                    # lcp = self.__rnd.randint(1, 40)
                    # lds = self.__rnd.randint(1, 40)

                    self._cf.dp.SetCommandVariable(
                        ["CPDICT", json.dumps(amycps)])
                    self._cf.dp.SetCommandVariable(
                        ["DSDICT", json.dumps(amydss)])
                    comps = set()

                    ncps = self.__rnd.randint(1, len(amycps) - 1)
                    lcps = self.__rnd.sample(list(amycps.keys()), ncps)
                    for cp in lcps:
                        if cp not in wrong:
                            cps[cp] = bool(self.__rnd.randint(0, 1))
                            if cps[cp]:
                                comps.add(cp)

                    ancps = self.__rnd.randint(1, len(list(amycps.keys())) - 1)
                    alcps = self.__rnd.sample(list(amycps.keys()), ancps)
                    for cp in alcps:
                        if cp not in wrong:
                            acps[cp] = bool(self.__rnd.randint(0, 1))
                            if acps[cp]:
                                comps.add(cp)

                    ndss = self.__rnd.randint(1, len(list(amycps.keys())) - 1)
                    ldss = self.__rnd.sample(list(amycps.keys()), ndss)
                    for ds in ldss:
                        if ds in amydss.keys():
                            if ds not in wrong:
                                dss[ds] = bool(self.__rnd.randint(0, 1))

                    ndss = self.__rnd.randint(1, len(list(amydss.keys())) - 1)
                    ldss = self.__rnd.sample(list(amydss.keys()), ndss)
                    for ds in ldss:
                        if ds in amydss.keys():
                            if ds not in wrong:
                                dss[ds] = bool(self.__rnd.randint(0, 1))

                    for tm in ltimers:
                        dss[tm] = bool(self.__rnd.randint(0, 1))

                    mncps = self.__rnd.randint(1, len(list(amycps.keys())) - 1)
                    mcps = [cp for cp in self.__rnd.sample(
                            list(amycps.keys()), mncps) if cp not in wrong]
                    for cp in mcps:
                        comps.add(cp)

                    adss = dict(dss)
                    for ch in expch:
                        if ch["name"] not in adss.keys():
                            adss[ch["name"]] = False
                    se["ComponentSelection"] = json.dumps(cps)
                    se["ComponentPreselection"] = json.dumps(acps)
                    se["DataSourceSelection"] = json.dumps(dss)
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
                        list(dss.keys()), dstype='CLIENT')[0]
                    for dsr in dsres.values():
                        records[str(dsr.record)] = '2345'

                    se["Timer"] = json.dumps(ltimers)
                    se["UserData"] = json.dumps(records)

                    tmg = TestMGSetUp.TestMeasurementGroupSetUp(
                        name='mg2')
#                    dv = "/".join(ar["full_name"].split("/")[0:-1])
                    chds = [ds for ds in mgt.dataSources()
                            if not ds.startswith('client')]
                    # chds1 = list(chds)
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
                        lheds = self.__rnd.sample(list(chds), nhe)

                    lhecp = []
                    if comps:
                        nhe = self.__rnd.randint(0, len(set(comps)) - 1)
                        lhecp = self.__rnd.sample(list(comps), nhe)

                    lhe = lheds + lhecp

                    se["UnplottedComponents"] = json.dumps(lhe)
                    se["OrderedChannels"] = json.dumps(pdss)

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
                        json.loads(se["ComponentPreselection"]),
                        acps)
                    self.myAssertDict(
                        json.loads(se["ComponentSelection"]), cps)
                    self.myAssertDict(
                        json.loads(se["DataSourceSelection"]), adss)
                    self.assertEqual(
                        set(json.loads(se["UnplottedComponents"])),
                        set(lhe))
                    self.assertEqual(json.loads(se["OrderedChannels"]), pdss)
                    self.myAssertDict(json.loads(se["UserData"]), records)
                    self.assertEqual(json.loads(se["Timer"]), ltimers)
                    self.assertEqual(se["MntGrp"], "mg2")

                    res = mgt.cpdescription()
                    # mdds = set()
                    for mdss in res[0].values():
                        if isinstance(mdss, dict):
                            for ds in mdss.keys():
                                adss[ds] = True
                    for tm in ltimers:
                        if tm in lhe2:
                            if tm in adss.keys():
                                adss[tm] = False

                    jpcnf = mgt.updateProfile()
                    pcnf = json.loads(jpcnf)
                    mgdp = tango.DeviceProxy(tmg.new_device_info_writer.name)
                    jcnf = mgdp.Configuration
                    cnf = json.loads(jcnf)
                    self.myAssertDict(
                        json.loads(se["ComponentPreselection"]),
                        acps)
                    self.myAssertDict(
                        json.loads(se["ComponentSelection"]), cps)
                    self.myAssertDict(
                        json.loads(se["DataSourceSelection"]), adss)
                    self.assertEqual(
                        set(json.loads(se["UnplottedComponents"])),
                        set(lhe2))
                    self.assertEqual(json.loads(se["OrderedChannels"]), pdss)
                    self.myAssertDict(json.loads(se["UserData"]), records)
                    self.assertEqual(json.loads(se["Timer"]), ltimers)
                    self.assertEqual(se["MntGrp"], "mg2")
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
                                    except Exception:
                                        raise
                        if tgc:
                            ltm = timers[cl] if cl in timers.keys() \
                                else ltimers[0]
                            # fltm =
                            "/".join(
                                self.smychsXX[str(ltm)]['source'].split(
                                    "/")[:-1])
                            myctrls[cl] = {
                                'channels': tgc,
                                'monitor': ttdv,
                                'timer': ttdv,
                                'synchronization': 0,
                                'synchronizer': 'software'}

                    tgc = {}
                    for ds in chds:
                        if ds in self.smychs:
                            cnt = self.smychs[str(ds)]
                            i = chds.index(str(ds))
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
                            except Exception:
                                raise

                    if tgc:
                        myctrls['__tango__'] = {'channels': tgc,
                                                'synchronization': 0}

                    smg = {"controllers": myctrls,
                           "monitor": "%s" % fgtm,
                           "description": "Measurement Group",
                           "timer": "%s" % fgtm,
                           "label": "mg2"}
                    self.myAssertDict(smg, pcnf)
                    self.myAssertDict(pcnf, cnf)
                    se.reset()
                    se["Door"] = val["Door"]
                    se["ConfigDevice"] = val["ConfigDevice"]
                    se["MntGrp"] = "mg2"
                    se.fetchSelection()
                    self.myAssertDict(
                        json.loads(se["ComponentPreselection"]),
                        acps)
                    self.myAssertDict(
                        json.loads(se["ComponentSelection"]), cps)
                    self.myAssertDict(
                        json.loads(se["DataSourceSelection"]), adss)
                    self.assertEqual(
                        set(json.loads(se["UnplottedComponents"])),
                        set(lhe2))
                    self.assertEqual(json.loads(se["OrderedChannels"]), pdss)
                    self.myAssertDict(json.loads(se["UserData"]), records)
                    self.assertEqual(json.loads(se["Timer"]), ltimers)
                    self.assertEqual(se["MntGrp"], "mg2")
                finally:
                    try:
                        mgt.deleteProfile("mg2")
                    except Exception:
                        pass
                    try:
                        tmg.tearDown()
                    except Exception:
                        pass
        finally:
            simp2.tearDown()

    # updateProfile test
    def test_updateProfile_mntGrpConfiguration_isMntGrpUpdated(self):
        fun = sys._getframe().f_code.co_name
        print("Run: %s.%s() " % (self.__class__.__name__, fun))
        val = {"ConfigDevice": self._cf.dp.name(),
               "WriterDevice": self._wr.dp.name(),
               "Door": 'doortestp09/testts/t1r228',
               "MntGrp": 'mg2'}

        wrong = []

        mgt = ProfileManager(None)
        mgt.masterTimer = True
        mgt.masterTimerFirst = False
        self.myAssertRaise(Exception, mgt.updateProfile)

        se = Selector(None, self.__version)
        mgt = ProfileManager(se)
        mgt.masterTimer = True
        mgt.masterTimerFirst = False
        self.myAssertRaise(Exception, mgt.updateProfile)

        msp = MacroServerPools(10)
        se = Selector(msp, self.__version)
        se["Door"] = val["Door"]
        se["ConfigDevice"] = val["ConfigDevice"]
        se["MntGrp"] = val["MntGrp"]
        mgt = ProfileManager(se)
        mgt.masterTimer = True
        mgt.masterTimerFirst = False
        self.assertEqual(mgt.availableMntGrps(), [])
        self.myAssertRaise(Exception, mgt.updateProfile)

        db = tango.Database()
        db.put_device_property(list(self._ms.ms.keys())[0],
                               {'PoolNames': self._pool.dp.name()})
        pool = self._pool.dp
        self._ms.dps[list(self._ms.ms.keys())[0]].Init()

        self.assertEqual(mgt.availableMntGrps(), [])
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
                tms = self.__rnd.sample(list(
                    [ch for ch in self.smychsXX.keys()
                     if not ch.startswith("client")]), ntms)
                for tm in tms:
                    myct = ("ctrl_%s" % tm).replace("_", "/")
                    timers[myct] = tm
                    ctrls.append(myct)
                ltimers = list(timers.values())

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
                    # lcp = self.__rnd.randint(1, 40)
                    # lds = self.__rnd.randint(1, 40)

                    self._cf.dp.SetCommandVariable(
                        ["CPDICT", json.dumps(amycps)])
                    self._cf.dp.SetCommandVariable(
                        ["DSDICT", json.dumps(amydss)])
                    comps = set()

                    ncps = self.__rnd.randint(1, len(amycps) - 1)
                    lcps = self.__rnd.sample(list(amycps.keys()), ncps)
                    for cp in lcps:
                        if cp not in wrong:
                            cps[cp] = bool(self.__rnd.randint(0, 1))
                            if cps[cp]:
                                comps.add(cp)

                    ancps = self.__rnd.randint(1, len(list(amycps.keys())) - 1)
                    alcps = self.__rnd.sample(list(amycps.keys()), ancps)
                    for cp in alcps:
                        if cp not in wrong:
                            acps[cp] = bool(self.__rnd.randint(0, 1))
                            if acps[cp]:
                                comps.add(cp)

                    ndss = self.__rnd.randint(1, len(list(amycps.keys())) - 1)
                    ldss = self.__rnd.sample(list(amycps.keys()), ndss)
                    for ds in ldss:
                        if ds in amydss.keys():
                            if ds not in wrong:
                                dss[ds] = bool(self.__rnd.randint(0, 1))

                    ndss = self.__rnd.randint(1, len(list(amydss.keys())) - 1)
                    ldss = self.__rnd.sample(list(amydss.keys()), ndss)
                    for ds in ldss:
                        if ds in amydss.keys():
                            if ds not in wrong:
                                dss[ds] = bool(self.__rnd.randint(0, 1))

                    nadss = self.__rnd.randint(1, len(list(amydss.keys())) - 1)
                    aadss = [ds for ds in self.__rnd.sample(
                        list(amydss.keys()), nadss)]
                    nadss = self.__rnd.randint(1, len(list(amydss.keys())) - 1)
                    indss = dict((ds, True) for ds in self.__rnd.sample(
                        list(amydss.keys()), nadss))

                    for tm in ltimers:
                        dss[tm] = bool(self.__rnd.randint(0, 1))

                    mncps = self.__rnd.randint(1, len(list(amycps.keys())) - 1)
                    mcps = [cp for cp in self.__rnd.sample(
                        list(amycps.keys()), mncps) if cp not in wrong]
                    oncps = self.__rnd.randint(1, len(list(amycps.keys())) - 1)
                    ocps = [cp for cp in self.__rnd.sample(
                        list(amycps.keys()), oncps) if cp not in wrong]
                    for cp in mcps:
                        comps.add(cp)

                    adss = dict(dss)
                    for ch in expch:
                        if ch["name"] not in adss.keys():
                            adss[ch["name"]] = False
                    se["ComponentSelection"] = json.dumps(cps)
                    se["ComponentPreselection"] = json.dumps(acps)
                    se["DataSourceSelection"] = json.dumps(dss)
                    se["PreselectingDataSources"] = json.dumps(aadss)
                    se["OptionalComponents"] = json.dumps(ocps)
                    se["DataSourcePreselection"] = json.dumps(indss)
                    se["AppendEntry"] = bool(self.__rnd.randint(0, 1))
                    se["ComponentsFromMntGrp"] = bool(self.__rnd.randint(0, 1))
                    se["DynamicComponents"] = bool(self.__rnd.randint(0, 1))
                    se["DefaultDynamicLinks"] = bool(self.__rnd.randint(0, 1))
                    se["DefaultDynamicPath"] = self.getRandomName(20)
                    se["TimeZone"] = self.getRandomName(20)

                    se["ConfigVariables"] = json.dumps(dict(
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
                    se["ChannelProperties"] = json.dumps(
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

                    se["Timer"] = json.dumps(ltimers)
                    se["UserData"] = json.dumps(records)

                    tmg = TestMGSetUp.TestMeasurementGroupSetUp(
                        name='mg2')
#                    dv = "/".join(ar["full_name"].split("/")[0:-1])
                    chds = [ds for ds in mgt.dataSources()
                            if not ds.startswith('client')]
                    # chds1 = list(chds)
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
                        lheds = self.__rnd.sample(list(chds), nhe)

                    lhecp = []
                    if comps:
                        nhe = self.__rnd.randint(0, len(set(comps)) - 1)
                        lhecp = self.__rnd.sample(list(comps), nhe)

                    lhe = lheds + lhecp

                    se["UnplottedComponents"] = json.dumps(lhe)
                    se["OrderedChannels"] = json.dumps(pdss)

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
                        json.loads(se["ComponentPreselection"]),
                        acps)
                    self.myAssertDict(
                        json.loads(se["ComponentSelection"]), cps)
                    self.myAssertDict(
                        json.loads(se["DataSourceSelection"]), adss)
                    self.assertEqual(
                        set(json.loads(se["UnplottedComponents"])),
                        set(lhe))
                    self.assertEqual(json.loads(se["OrderedChannels"]), pdss)
                    self.myAssertDict(json.loads(se["UserData"]), records)
                    self.assertEqual(json.loads(se["Timer"]), ltimers)
                    self.assertEqual(se["MntGrp"], "mg2")
                    self.dump(se)
                    self.assertTrue(not mgt.isMntGrpUpdated())
                    self.assertTrue(not mgt.isMntGrpUpdated())

                    res = mgt.cpdescription()
                    # mdds = set()
                    for mdss in res[0].values():
                        if isinstance(mdss, dict):
                            for ds in mdss.keys():
                                adss[ds] = True

                    for tm in ltimers:
                        if tm in lhe2:
                            if tm in adss.keys():
                                adss[tm] = False

                    jpcnf = mgt.updateProfile()
                    self.dump(se)
                    self.assertTrue(mgt.isMntGrpUpdated())
                    self.assertTrue(mgt.isMntGrpUpdated())
                    pcnf = json.loads(jpcnf)
                    # mgdp =
                    tango.DeviceProxy(tmg.new_device_info_writer.name)
                    jcnf = mgt.mntGrpConfiguration()
                    cnf = json.loads(jcnf)
                    self.myAssertDict(
                        json.loads(se["ComponentPreselection"]),
                        acps)
                    self.myAssertDict(
                        json.loads(se["ComponentSelection"]), cps)
                    self.myAssertDict(
                        json.loads(se["DataSourceSelection"]), adss)
                    self.assertEqual(
                        set(json.loads(se["UnplottedComponents"])),
                        set(lhe2))
                    self.assertEqual(json.loads(se["OrderedChannels"]), pdss)
                    self.myAssertDict(json.loads(se["UserData"]), records)
                    self.assertEqual(json.loads(se["Timer"]), ltimers)
                    self.assertEqual(se["MntGrp"], "mg2")
                    myctrls = {}
                    # fgtm = "/".join(
                    #     self.smychsXX[str(ltimers[0])]['source'].split(
                    #         "/")[:-1])
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
                                    except Exception:
                                        raise
                        if tgc:
                            ltm = timers[cl] if cl in timers.keys() \
                                else ltimers[0]
                            # fltm =
                            "/".join(
                                self.smychsXX[str(ltm)]['source'].split(
                                    "/")[:-1])
                            myctrls[cl] = {
                                'channels': tgc,
                                'monitor': ttdv,
                                'synchronization': 0,
                                'synchronizer': 'software',
                                'timer': ttdv}

                    tgc = {}
                    for ds in chds:
                        if ds in self.smychs:
                            cnt = self.smychs[str(ds)]
                            i = chds.index(str(ds))
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
                            except Exception:
                                raise

                    if tgc:
                        myctrls['__tango__'] = {'channels': tgc,
                                                'synchronization': 0}
                    # smg = {"controllers": myctrls,
                    #        "monitor": "%s" % fgtm,
                    #        "description": "Measurement Group",
                    #        "timer": "%s" % fgtm,
                    #        "label": "mg2"}
                    self.myAssertDict(pcnf, cnf)
                    se.reset()
                    se["Door"] = val["Door"]
                    se["ConfigDevice"] = val["ConfigDevice"]
                    se["MntGrp"] = "mg2"
                    self.myAssertRaise(Exception, mgt.isMntGrpUpdated)
                    mgt.fetchProfile()

                    self.assertTrue(mgt.isMntGrpUpdated())
                    self.assertTrue(mgt.isMntGrpUpdated())

                    self.compareToDumpJSON(
                        se, ["ComponentPreselection",
                             "ComponentSelection",
                             "DataSourceSelection",
                             "UnplottedComponents",
                             "PreselectingDataSources"])

                    self.myAssertDict(
                        json.loads(se["ComponentPreselection"]), acps)
                    self.myAssertDict(
                        json.loads(se["ComponentSelection"]), cps)
                    self.myAssertDict(
                        json.loads(se["DataSourceSelection"]), adss)
                    self.assertEqual(
                        set(json.loads(se["PreselectingDataSources"])),
                        set(aadss))
                    self.assertEqual(
                        set(json.loads(se["UnplottedComponents"])),
                        set(lhe2))
                    self.assertEqual(json.loads(se["OrderedChannels"]), pdss)
                    self.myAssertDict(json.loads(se["UserData"]), records)
                    self.assertEqual(json.loads(se["Timer"]), ltimers)
                    self.assertEqual(se["MntGrp"], "mg2")
                finally:
                    try:
                        mgt.deleteProfile("mg2")
                    except Exception:
                        pass
                    try:
                        tmg.tearDown()
                    except Exception:
                        pass
        finally:
            simp2.tearDown()

    # updateProfile test
    def test_switchProfile_importMntGrp(self):
        fun = sys._getframe().f_code.co_name
        print("Run: %s.%s() " % (self.__class__.__name__, fun))
        val = {"ConfigDevice": self._cf.dp.name(),
               "WriterDevice": self._wr.dp.name(),
               "Door": 'doortestp09/testts/t1r228',
               "MntGrp": 'mg2'}

        self.maxDiff = None
        self.tearDown()
        try:
            for j in range(10):
                self.setUp()
                db = tango.Database()
                db.put_device_property(list(self._ms.ms.keys())[0],
                                       {'PoolNames': self._pool.dp.name()})

                wrong = []

                mgs = ["mg1", "mg2", "mg3",
                       "mntgrp", "somegroup"
                       ]
                mgt = {}
                se = {}
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
                pools = {}

                pool = self._pool.dp
                self._ms.dps[list(self._ms.ms.keys())[0]].Init()
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

                        msp[mg] = MacroServerPools(10)
                        se[mg] = Selector(msp[mg], self.__version)
                        se[mg]["Door"] = val["Door"]
                        se[mg]["ConfigDevice"] = val["ConfigDevice"]
                        se[mg]["MntGrp"] = mg
                        mgt[mg] = ProfileManager(se[mg])
                        mgt[mg].masterTimer = True
                        mgt[mg].masterTimerFirst = False
                        self.assertEqual(
                            set(mgt[mg].availableMntGrps()), set(mgs[:(i)]))
                        self.myAssertRaise(Exception, mgt[mg].updateProfile)

                        self.assertEqual(
                            set(mgt[mg].availableMntGrps()), set(mgs[:(i)]))

                        ctrls = [scalar_ctrl, spectrum_ctrl, image_ctrl,
                                 "__tango__"]
                        expch = []
                        pdss[mg] = []

                        timers = {}
                        ntms = 1  # self.__rnd.randint(1, 5)
                        tms = self.__rnd.sample(list(
                            [ch for ch in self.smychsXX.keys()
                             if not ch.startswith("client")]), ntms)
                        for tm in tms:
                            myct = ("ctrl_%s" % tm).replace("_", "/")
                            timers[myct] = tm
                            ctrls.append(myct)
                        # print "TIMERSL", tms
                        # print "TIMERSD", timers
                        ltimers[mg] = list(timers.values())
                        # print "LTIMER", ltimers[mg]

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
                        pools[mg] = [pool.AcqChannelList, pool.ExpChannelList]

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
                        # lcp = self.__rnd.randint(1, 40)
                        # lds = self.__rnd.randint(1, 40)

                        self._cf.dp.SetCommandVariable(
                            ["CPDICT", json.dumps(amycps)])
                        self._cf.dp.SetCommandVariable(
                            ["DSDICT", json.dumps(amydss)])
                        comps = set()

                        ncps = self.__rnd.randint(1, len(amycps) - 1)
                        lcps = self.__rnd.sample(list(amycps.keys()), ncps)
                        for cp in lcps:
                            if cp not in wrong:
                                cps[mg][cp] = bool(self.__rnd.randint(0, 1))
                                if cps[mg][cp]:
                                    comps.add(cp)

                        ancps = self.__rnd.randint(
                            1, len(list(amycps.keys())) - 1)
                        alcps = self.__rnd.sample(list(amycps.keys()), ancps)
                        for cp in alcps:
                            if cp not in wrong:
                                acps[mg][cp] = bool(self.__rnd.randint(0, 1))
                                if acps[mg][cp]:
                                    comps.add(cp)

                        ndss = self.__rnd.randint(
                            1, len(list(amycps.keys())) - 1)
                        ldss = self.__rnd.sample(list(amycps.keys()), ndss)
                        for ds in ldss:
                            if ds in amydss.keys():
                                if ds not in wrong:
                                    dss[ds] = bool(self.__rnd.randint(0, 1))

                        ndss = self.__rnd.randint(
                            1, len(list(amydss.keys())) - 1)
                        ldss = self.__rnd.sample(list(amydss.keys()), ndss)
                        for ds in ldss:
                            if ds in amydss.keys():
                                if ds not in wrong:
                                    dss[ds] = bool(self.__rnd.randint(0, 1))

                        nadss = self.__rnd.randint(
                            1, len(list(amydss.keys())) - 1)
                        aadss[mg] = [ds for ds in self.__rnd.sample(
                            list(amydss.keys()), nadss)]
                        nadss = self.__rnd.randint(
                            1, len(list(amydss.keys())) - 1)
                        indss = dict((ds, True) for ds in self.__rnd.sample(
                            list(amydss.keys()), nadss))

                        for tm in ltimers[mg]:
                            dss[tm] = bool(self.__rnd.randint(0, 1))

                        mncps = self.__rnd.randint(
                            1, len(list(amycps.keys())) - 1)
                        mcps = [cp for cp in self.__rnd.sample(
                                list(amycps.keys()), mncps) if cp not in wrong]
                        oncps = self.__rnd.randint(
                            1, len(list(amycps.keys())) - 1)
                        ocps = [cp for cp in self.__rnd.sample(
                                list(amycps.keys()), oncps) if cp not in wrong]
                        for cp in mcps:
                            comps.add(cp)

                        adss[mg] = dict(dss)
                        for ch in expch:
                            if ch["name"] not in adss[mg].keys():
                                adss[mg][ch["name"]] = False
                        se[mg]["ComponentSelection"] = json.dumps(cps[mg])
                        se[mg]["ComponentPreselection"] = json.dumps(
                            acps[mg])
                        se[mg]["DataSourceSelection"] = json.dumps(dss)
                        se[mg]["PreselectingDataSources"] = \
                            json.dumps(aadss[mg])
                        se[mg]["OptionalComponents"] = json.dumps(ocps)
                        se[mg]["DataSourcePreselection"] = json.dumps(indss)
                        se[mg]["AppendEntry"] = bool(self.__rnd.randint(0, 1))
                        se[mg]["ComponentsFromMntGrp"] = bool(
                            self.__rnd.randint(0, 1))
                        se[mg]["DynamicComponents"] = bool(
                            self.__rnd.randint(0, 1))
                        se[mg]["DefaultDynamicLinks"] = \
                            bool(self.__rnd.randint(0, 1))
                        se[mg]["DefaultDynamicPath"] = self.getRandomName(20)
                        se[mg]["TimeZone"] = self.getRandomName(20)

                        se[mg]["ConfigVariables"] = json.dumps(dict(
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

                        se[mg]["ChannelProperties"] = json.dumps(
                            {
                                "label": labels,
                                "nexus_path": paths,
                                "link": links,
                                "data_type": types,
                                "synchronizer": {},
                                "synchronization": {},
                                "shape": shapes
                            }
                        )

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
                            list(dss.keys()), dstype='CLIENT')[0]
                        for dsr in dsres.values():
                            records[mg][str(dsr.record)] = '2345'

                        se[mg]["Timer"] = json.dumps(ltimers[mg])
                        se[mg]["UserData"] = json.dumps(records[mg])

                        tmg[mg] = TestMGSetUp.TestMeasurementGroupSetUp(
                            name=mg)
        #                    dv = "/".join(ar["full_name"].split("/")[0:-1])
                        chds = [ds for ds in mgt[mg].dataSources()
                                if not ds.startswith('client')]
                        # chds1 = list(chds)
                        chds2 = [ds for ds in mgt[mg].componentDataSources()
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
                            lheds = self.__rnd.sample(list(chds), nhe)

                        lhecp = []
                        if comps:
                            nhe = self.__rnd.randint(0, len(set(comps)) - 1)
                            lhecp = self.__rnd.sample(list(comps), nhe)

                        lhe = lheds + lhecp

                        se[mg]["UnplottedComponents"] = json.dumps(lhe)
                        se[mg]["OrderedChannels"] = json.dumps(pdss[mg])

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
                            json.loads(se[mg]["ComponentPreselection"]),
                            acps[mg])
                        self.myAssertDict(
                            json.loads(se[mg]["ComponentSelection"]), cps[mg])
                        self.myAssertDict(
                            json.loads(se[mg]["DataSourceSelection"]),
                            adss[mg])
                        self.assertEqual(
                            set(json.loads(se[mg]["UnplottedComponents"])),
                            set(lhe))
                        self.assertEqual(
                            json.loads(se[mg]["OrderedChannels"]), pdss[mg])
                        self.myAssertDict(
                            json.loads(se[mg]["UserData"]), records[mg])
                        self.assertEqual(
                            json.loads(se[mg]["Timer"]), ltimers[mg])
                        self.assertEqual(se[mg]["MntGrp"], mg)
                        self.dump(se[mg], name=mg)
                        self.assertTrue(not mgt[mg].isMntGrpUpdated())
                        self.assertTrue(not mgt[mg].isMntGrpUpdated())

                        res = mgt[mg].cpdescription()
                        # mdds = set()
                        for mdss in res[0].values():
                            if isinstance(mdss, dict):
                                for ds in mdss.keys():
                                    adss[mg][ds] = True
                        for tm in ltimers[mg]:
                            if tm in lhe2[mg]:
                                if tm in adss[mg].keys():
                                    # print "DES", tm
                                    adss[mg][tm] = False

                        jpcnf = mgt[mg].updateProfile()
                        self.dump(se[mg], name=mg)
                        self.assertTrue(mgt[mg].isMntGrpUpdated())
                        self.assertTrue(mgt[mg].isMntGrpUpdated())
                        pcnf = json.loads(jpcnf)
                        # mgdp =
                        tango.DeviceProxy(
                            tmg[mg].new_device_info_writer.name)
                        jcnf = mgt[mg].mntGrpConfiguration()
                        cnf = json.loads(jcnf)
                        self.myAssertDict(
                            json.loads(se[mg]["ComponentPreselection"]),
                            acps[mg])
                        self.myAssertDict(
                            json.loads(se[mg]["ComponentSelection"]), cps[mg])
                        self.myAssertDict(
                            json.loads(
                                se[mg]["DataSourceSelection"]), adss[mg])
                        self.assertEqual(
                            set(json.loads(se[mg]["UnplottedComponents"])),
                            set(lhe2[mg]))
                        self.assertEqual(
                            json.loads(se[mg]["OrderedChannels"]), pdss[mg])
                        self.myAssertDict(
                            json.loads(se[mg]["UserData"]), records[mg])
                        self.assertEqual(
                            json.loads(se[mg]["Timer"]), ltimers[mg])
                        self.assertEqual(se[mg]["MntGrp"], mg)
                        myctrls = {}
                        fgtm = "/".join(
                            self.smychsXX[
                                str(ltimers[mg][0])]['source'].split(
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
                                        except Exception:
                                            raise
                            if tgc:
                                ltm = timers[cl] if cl in timers.keys() \
                                    else ltimers[mg][0]
                                # fltm =
                                "/".join(
                                    self.smychsXX[str(ltm)]['source'].split(
                                        "/")[:-1])
                                myctrls[cl] = {
                                    'synchronization': 0,
                                    'synchronizer': 'software',
                                    'channels': tgc,
                                    'monitor': ttdv,
                                    'timer': ttdv}

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
                                except Exception:
                                    raise

                        if tgc:
                            myctrls['__tango__'] = {
                                'channels': tgc,
                                'synchronization': 0}

                        smg = {"controllers": myctrls,
                               "monitor": "%s" % fgtm,
                               "description": "Measurement Group",
                               "timer": "%s" % fgtm,
                               "label": mg}
        #                    print "SMG", smg
                        self.myAssertDict(smg, pcnf)
                        self.myAssertDict(pcnf, cnf)
                        se[mg].reset()
                        se[mg]["Door"] = val["Door"]
                        se[mg]["ConfigDevice"] = val["ConfigDevice"]
                        se[mg]["MntGrp"] = mg
                        self.myAssertRaise(Exception, mgt[mg].isMntGrpUpdated)
                        mgt[mg].fetchProfile()

                        self.assertTrue(mgt[mg].isMntGrpUpdated())
                        self.assertTrue(mgt[mg].isMntGrpUpdated())
                        self.compareToDumpJSON(
                            se[mg],
                            ["DataSourceSelection",
                             "UnplottedComponents",
                             "PreselectingDataSources",
                             "UnplottedComponents"],
                            name=mg)

                        self.myAssertDict(
                            json.loads(
                                se[mg]["DataSourceSelection"]), adss[mg])
                        self.assertEqual(
                            set(json.loads(se[mg]["PreselectingDataSources"])),
                            set(aadss[mg]))
                        self.assertEqual(
                            set(json.loads(se[mg]["UnplottedComponents"])),
                            set(lhe2[mg]))
                        self.assertEqual(
                            json.loads(se[mg]["OrderedChannels"]), pdss[mg])
                        self.myAssertDict(
                            json.loads(se[mg]["UserData"]), records[mg])
                        self.assertEqual(
                            json.loads(se[mg]["Timer"]), ltimers[mg])
                        self.assertEqual(se[mg]["MntGrp"], mg)

                    # check profile commands
                    mg1, mg2, mg3, mg4 = tuple(self.__rnd.sample(mgs, 4))

                    lmsp = MacroServerPools(10)
                    lse = Selector(lmsp, self.__version)
                    lse["Door"] = val["Door"]
                    lse["ConfigDevice"] = val["ConfigDevice"]
                    # switch from empty profile to mg1
                    lse["MntGrp"] = mg1
                    pool.AcqChannelList = pools[mg1][0]
                    pool.ExpChannelList = pools[mg1][1]
                    lmgt = ProfileManager(lse)
                    lmgt.masterTimer = True
                    lmgt.masterTimerFirst = False
                    self.myAssertRaise(Exception, lmgt.isMntGrpUpdated)

                    lmgt.switchProfile(False)

                    self.compareToDumpJSON(
                        lse, [
                            "DataSourceSelection",
                            "UnplottedComponents",
                            "PreselectingDataSources",
                            "Timer"
                        ],
                        name=mg1)

                    tmpcf = json.loads(mgt[mg1].mntGrpConfiguration())
                    ltmpcf = json.loads(lmgt.mntGrpConfiguration())
                    self.myAssertDict(tmpcf, ltmpcf)

                    self.assertEqual(
                        set(json.loads(lse["PreselectingDataSources"])),
                        set(aadss[mg1]))
                    # print "ADAA", json.loads(lse["DataSourceSelection"]),
                    # adss[mg1]
                    self.myAssertDict(
                        json.loads(lse["DataSourceSelection"]), adss[mg1])
                    self.assertEqual(
                        json.loads(lse["OrderedChannels"]), pdss[mg1])
                    self.myAssertDict(
                        json.loads(lse["UserData"]), records[mg1])
                    self.assertEqual(
                        json.loads(lse["Timer"])[0], ltimers[mg1][0])
                    self.assertEqual(
                        set(json.loads(lse["Timer"])), set(ltimers[mg1]))
                    self.assertEqual(lse["MntGrp"], mg1)

                    # print "MGS", mg1, mg2, mg3, mg4

                    # import mntgrp another defined by selector MntGrp
                    lse["MntGrp"] = mg2
                    pool.AcqChannelList = pools[mg2][0]
                    pool.ExpChannelList = pools[mg2][1]
                    self.assertTrue(not lmgt.isMntGrpUpdated())
                    self.assertTrue(not lmgt.isMntGrpUpdated())

                    lmgt.importMntGrp()
                    # self.assertTrue(not lmgt.isMntGrpUpdated())
                    # self.assertTrue(not lmgt.isMntGrpUpdated())

                    # tmpcf1 =
                    json.loads(mgt[mg1].mntGrpConfiguration())
                    tmpcf2 = json.loads(mgt[mg2].mntGrpConfiguration())
                    ltmpcf = json.loads(lmgt.mntGrpConfiguration())
#                    self.myAssertDict(tmpcf1, ltmpcf)
                    self.myAssertDict(tmpcf2, ltmpcf)
                    self.compareToDumpJSON(
                        se[mg2],
                        ["DataSourceSelection",
                         "UnplottedComponents",
                         "PreselectingDataSources"],
                        name=mg2)

                    pool.AcqChannelList = pools[mg1][0]
                    pool.ExpChannelList = pools[mg1][1]
                    self.compareToDumpJSON(
                        lse,
                        ["DataSourceSelection",
                         "UnplottedComponents",
                         "PreselectingDataSources",
                         "Timer",
                         "MntGrp"],
                        name=mg1)

                    tmpcf = json.loads(mgt[mg2].mntGrpConfiguration())
                    ltmpcf = json.loads(lmgt.mntGrpConfiguration())
                    self.myAssertDict(tmpcf, ltmpcf)

                    self.assertEqual(
                        set(json.loads(lse["PreselectingDataSources"])),
                        set(aadss[mg1]))
                    self.assertEqual(
                        json.loads(lse["OrderedChannels"]), pdss[mg1])
                    self.myAssertDict(
                        json.loads(lse["UserData"]), records[mg1])

                    self.assertEqual(
                        json.loads(lse["Timer"])[0], ltimers[mg2][0])
                    # print "TIME2", ltimers[mg2]
                    self.assertEqual(
                        set(json.loads(lse["Timer"])), set(ltimers[mg2]))
                    self.assertEqual(lse["MntGrp"], mg2)

                    # print "ADDS", json.loads(se[mg1]["DataSourceSelection"]),
                    # adss[mg1]
                    self.myAssertDict(
                        json.loads(se[mg1]["DataSourceSelection"]),
                        adss[mg1])
                    self.myAssertDict(
                        json.loads(se[mg2]["DataSourceSelection"]),
                        adss[mg2])

                    self.assertEqual(
                        set(json.loads(se[mg1]["UnplottedComponents"])),
                        set(lhe2[mg1]))
                    self.assertEqual(
                        set(json.loads(se[mg2]["UnplottedComponents"])),
                        set(lhe2[mg2]))

                    compds = mgt[mg1].componentDataSources()

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

                    for tm in json.loads(se[mg2]["Timer"]):
                        if tm in ladss:
                            if tm in llhe:
                                ladss[tm] = False
                                llhe.remove(tm)
                    for tm in json.loads(se[mg1]["Timer"]):
                        if tm in ladss:
                            if tm in json.loads(
                                    se[mg2]["UnplottedComponents"]):
                                ladss[tm] = False
                                if tm not in json.loads(se[mg2]["Timer"]):
                                    if tm in llhe:
                                        llhe.remove(tm)

                    # print "T1", json.loads(se[mg1]["Timer"])
                    # print "T2", json.loads(se[mg2]["Timer"])
                    # print "LT", json.loads(lse["Timer"])
                    self.myAssertDict(
                        json.loads(lse["DataSourceSelection"]), ladss)
                    self.assertEqual(
                        set(json.loads(lse["UnplottedComponents"])),
                        set(llhe))
                    # import mntgrp mg2 (with content mg1)
                    # after change in mntgrp device

                    lse["MntGrp"] = mg2
                    tmpcf = json.loads(mgt[mg1].mntGrpConfiguration())
                    tmpcf2 = json.loads(mgt[mg2].mntGrpConfiguration())
                    ltmpcf = json.loads(lmgt.mntGrpConfiguration())
                    self.assertEqual(ltmpcf, tmpcf2)
                    tmpcf['label'] = mg2
                    mgdp = tango.DeviceProxy(
                        tmg[mg2].new_device_info_writer.name)
                    # print "name", tmg[mg2].new_device_info_writer.name
                    mgdp.Configuration = json.dumps(tmpcf)
                    self.assertTrue(not lmgt.isMntGrpUpdated())
                    self.assertTrue(not lmgt.isMntGrpUpdated())

                    # tmpcf1 =
                    json.loads(mgt[mg1].mntGrpConfiguration())
                    tmpcf2 = json.loads(mgt[mg2].mntGrpConfiguration())
                    ltmpcf = json.loads(lmgt.mntGrpConfiguration())
#                    self.myAssertDict(tmpcf1, ltmpcf)
                    self.myAssertDict(tmpcf2, ltmpcf)

                    lmgt.importMntGrp()
                    # ???

                    ltmpcf2 = json.loads(lmgt.mntGrpConfiguration())
                    if not Utils.compareDict(ltmpcf2, ltmpcf):
                        self.assertTrue(not lmgt.isMntGrpUpdated())
                        self.assertTrue(not lmgt.isMntGrpUpdated())

                    # tmpcf1 =
                    json.loads(mgt[mg1].mntGrpConfiguration())
                    tmpcf2 = json.loads(mgt[mg2].mntGrpConfiguration())
                    ltmpcf = json.loads(lmgt.mntGrpConfiguration())
#                    self.myAssertDict(tmpcf1, ltmpcf)
                    self.myAssertDict(tmpcf2, ltmpcf)

                    self.compareToDumpJSON(
                        lse,
                        ["ComponentPreselection",
                         "ComponentSelection",
                         "DataSourceSelection",
                         "UnplottedComponents",
                         "PreselectingDataSources",
                         "Timer",
                         "MntGrp"],
                        name=mg1)

                    pool.AcqChannelList = pools[mg2][0]
                    pool.ExpChannelList = pools[mg2][1]
                    self.compareToDump(
                        se[mg2],
                        ["ComponentPreselection",
                         "ComponentSelection",
                         "DataSourceSelection",
                         "UnplottedComponents",
                         "ChannelProperties",
                         "PreselectingDataSources",
                         "Timer"],
                        name=mg2)
                    self.compareToDumpJSON(
                        se[mg2],
                        ["ComponentPreselection",
                         "ComponentSelection",
                         "DataSourceSelection",
                         "UnplottedComponents",
                         "PreselectingDataSources",
                         "Timer"],
                        name=mg2)

                    self.myAssertDict(
                        json.loads(se[mg2]["ComponentPreselection"]),
                        acps[mg2])
                    self.myAssertDict(
                        json.loads(se[mg2]["ComponentSelection"]),
                        cps[mg2])
                    self.myAssertDict(
                        json.loads(se[mg2]["DataSourceSelection"]), adss[mg2])
                    self.assertEqual(
                        set(json.loads(se[mg2]["PreselectingDataSources"])),
                        set(aadss[mg2]))
                    self.assertEqual(
                        set(json.loads(se[mg2]["UnplottedComponents"])),
                        set(lhe2[mg2]))
                    self.assertEqual(
                        json.loads(se[mg2]["OrderedChannels"]), pdss[mg2])
                    self.myAssertDict(json.loads(se[mg2]["UserData"]),
                                      records[mg2])
                    self.assertEqual(
                        json.loads(se[mg2]["Timer"]), ltimers[mg2])
                    self.assertEqual(se[mg2]["MntGrp"], mg2)

                    # switch to active profile mg3
                    lse["MntGrp"] = mg2
                    pool.AcqChannelList = pools[mg2][0]
                    pool.ExpChannelList = pools[mg2][1]
                    MSUtils.setEnv(
                        'ActiveMntGrp', mg3, list(self._ms.ms.keys())[0])
                    pool.AcqChannelList = pools[mg3][0]
                    pool.ExpChannelList = pools[mg3][1]

                    # tmpcf1 =
                    json.loads(mgt[mg1].mntGrpConfiguration())
                    tmpcf2 = json.loads(mgt[mg2].mntGrpConfiguration())
                    tmpcf3 = json.loads(mgt[mg3].mntGrpConfiguration())
                    ltmpcf = json.loads(lmgt.mntGrpConfiguration())
#                    self.myAssertDict(tmpcf1, ltmpcf)
                    self.myAssertDict(tmpcf2, ltmpcf)
#                    self.myAssertDict(tmpcf3, ltmpcf)

                    lmgt.switchProfile()

                    # tmpcf1 =
                    json.loads(mgt[mg1].mntGrpConfiguration())
                    tmpcf2 = json.loads(mgt[mg2].mntGrpConfiguration())
                    tmpcf3 = json.loads(mgt[mg3].mntGrpConfiguration())
                    ltmpcf = json.loads(lmgt.mntGrpConfiguration())
                    self.myAssertDict(tmpcf3, ltmpcf)
#                    self.myAssertDict(tmpcf1, ltmpcf)
#                    self.myAssertDict(tmpcf2, ltmpcf)

                    self.compareToDumpJSON(
                        lse,
                        [
                            "DataSourceSelection",
                            "UnplottedComponents",
                            "PreselectingDataSources",
                            "Timer"],
                        name=mg3)
                    self.myAssertDict(json.loads(lse["DataSourceSelection"]),
                                      adss[mg3])
                    self.assertEqual(
                        set(json.loads(lse["PreselectingDataSources"])),
                        set(aadss[mg3]))

                    mylhe = set(lhe2[mg3])
                    for tm in json.loads(se[mg3]["Timer"]):
                        if tm in adss[mg3].keys():
                            if not adss[mg3][tm]:
                                if tm in mylhe:
                                    mylhe.remove(tm)

                    self.assertEqual(
                        set(json.loads(lse["UnplottedComponents"])),
                        mylhe)
                    self.assertEqual(json.loads(lse["OrderedChannels"]),
                                     pdss[mg3])
                    self.myAssertDict(json.loads(lse["UserData"]),
                                      records[mg3])
                    self.assertEqual(json.loads(lse["Timer"])[0],
                                     ltimers[mg3][0])
                    self.assertEqual(set(json.loads(lse["Timer"])),
                                     set(ltimers[mg3]))
                    self.assertEqual(lse["MntGrp"], mg3)

                    # switch to nonexisting active profile

#                    self.assertTrue(lmgt.isMntGrpUpdated())
#                    self.assertTrue(lmgt.isMntGrpUpdated())
                    wmg = "wrong_mg"
                    lse["MntGrp"] = mg3
                    MSUtils.setEnv(
                        'ActiveMntGrp', wmg, list(self._ms.ms.keys())[0])
                    lmgt.switchProfile()
                    self.assertEqual(
                        wmg,
                        MSUtils.getEnv(
                            'ActiveMntGrp', list(self._ms.ms.keys())[0]))

                    self.compareToDumpJSON(
                        lse,
                        [
                            "DataSourceSelection",
                            "UnplottedComponents",
                            "PreselectingDataSources",
                            "Timer",
                            "MntGrp"],
                        name=mg3)
                    mydsg = dict(json.loads(lse["DataSourceSelection"]))
                    for ds in self.smychsXX.keys():
                        if ds in expch:
                            mydsg[ds] = False
                    cpdss = mgt[mg3].componentDataSources()
                    mylhe2 = set(mylhe)
                    for ds in list(mylhe2):
                        if ds in self.smychsXX.keys() or (
                                ds in self.smychs.keys() and ds not in cpdss):
                            mylhe2.remove(ds)

                    self.myAssertDict(json.loads(lse["DataSourceSelection"]),
                                      mydsg)
                    self.assertEqual(
                        set(json.loads(lse["PreselectingDataSources"])),
                        set(aadss[mg3]))
                    self.assertEqual(
                        set(json.loads(lse["UnplottedComponents"])),
                        mylhe2)
                    self.assertEqual(json.loads(lse["OrderedChannels"]),
                                     pdss[mg3])
                    self.myAssertDict(json.loads(lse["UserData"]),
                                      records[mg3])
                    self.assertEqual(json.loads(lse["Timer"])[0],
                                     ltimers[mg3][0])
                    # print "TIME", ltimers[mg3]
                    self.assertEqual(set(json.loads(lse["Timer"])),
                                     set(ltimers[mg3]))
                    self.assertEqual(lse["MntGrp"], wmg)

                    # switch to active profile mg3
                    lse["MntGrp"] = mg2
                    self.assertTrue(not lmgt.isMntGrpUpdated())
                    self.assertTrue(not lmgt.isMntGrpUpdated())
                    MSUtils.setEnv(
                        'ActiveMntGrp', mg3, list(self._ms.ms.keys())[0])

                    # tmpcf1 =
                    json.loads(mgt[mg1].mntGrpConfiguration())
                    tmpcf2 = json.loads(mgt[mg2].mntGrpConfiguration())
                    tmpcf3 = json.loads(mgt[mg3].mntGrpConfiguration())
                    ltmpcf = json.loads(lmgt.mntGrpConfiguration())
#                    self.myAssertDict(tmpcf1, ltmpcf)
                    self.myAssertDict(tmpcf2, ltmpcf)
#                    self.myAssertDict(tmpcf3, ltmpcf)

                    lmgt.switchProfile(True)

                    # tmpcf1 =
                    json.loads(mgt[mg1].mntGrpConfiguration())
                    tmpcf2 = json.loads(mgt[mg2].mntGrpConfiguration())
                    tmpcf3 = json.loads(mgt[mg3].mntGrpConfiguration())
                    ltmpcf = json.loads(lmgt.mntGrpConfiguration())
                    self.myAssertDict(tmpcf3, ltmpcf)
#                    self.myAssertDict(tmpcf1, ltmpcf)
#                    self.myAssertDict(tmpcf2, ltmpcf)

                    self.compareToDumpJSON(
                        lse,
                        [
                            "DataSourceSelection",
                            "UnplottedComponents",
                            "PreselectingDataSources",
                            "Timer"],
                        name=mg3)
                    self.myAssertDict(json.loads(lse["DataSourceSelection"]),
                                      adss[mg3])
                    self.assertEqual(
                        set(json.loads(lse["PreselectingDataSources"])),
                        set(aadss[mg3]))

                    self.assertEqual(
                        set(json.loads(lse["UnplottedComponents"])),
                        mylhe)
                    self.assertEqual(json.loads(lse["OrderedChannels"]),
                                     pdss[mg3])
                    self.myAssertDict(json.loads(lse["UserData"]),
                                      records[mg3])
                    self.assertEqual(json.loads(lse["Timer"])[0],
                                     ltimers[mg3][0])
                    self.assertEqual(set(json.loads(lse["Timer"])),
                                     set(ltimers[mg3]))
                    self.assertEqual(lse["MntGrp"], mg3)

                    # try switch to unnamed active profile
                    # and then to selector mg3

#                    self.assertTrue(lmgt.isMntGrpUpdated())
#                    self.assertTrue(lmgt.isMntGrpUpdated())
                    wmg = ""
                    lse["MntGrp"] = mg3
                    MSUtils.setEnv(
                        'ActiveMntGrp', wmg, list(self._ms.ms.keys())[0])
                    lmgt.switchProfile()
                    self.assertEqual(
                        wmg,
                        MSUtils.getEnv(
                            'ActiveMntGrp', list(self._ms.ms.keys())[0]))

                    # tmpcf1 =
                    json.loads(mgt[mg1].mntGrpConfiguration())
                    tmpcf2 = json.loads(mgt[mg2].mntGrpConfiguration())
                    tmpcf3 = json.loads(mgt[mg3].mntGrpConfiguration())
                    ltmpcf = json.loads(lmgt.mntGrpConfiguration())
                    self.myAssertDict(tmpcf3, ltmpcf)
#                    self.myAssertDict(tmpcf1, ltmpcf)
#                    self.myAssertDict(tmpcf2, ltmpcf)

                    self.compareToDumpJSON(
                        lse,
                        [
                            "DataSourceSelection",
                            "UnplottedComponents",
                            "PreselectingDataSources",
                            "Timer"],
                        name=mg3)
                    self.myAssertDict(json.loads(lse["DataSourceSelection"]),
                                      adss[mg3])
                    self.assertEqual(
                        set(json.loads(lse["PreselectingDataSources"])),
                        set(aadss[mg3]))

                    self.assertEqual(
                        set(json.loads(lse["UnplottedComponents"])),
                        mylhe)
                    self.assertEqual(json.loads(lse["OrderedChannels"]),
                                     pdss[mg3])
                    self.myAssertDict(json.loads(lse["UserData"]),
                                      records[mg3])
                    self.assertEqual(json.loads(lse["Timer"])[0],
                                     ltimers[mg3][0])
                    self.assertEqual(set(json.loads(lse["Timer"])),
                                     set(ltimers[mg3]))
                    self.assertEqual(lse["MntGrp"], mg3)

                    # try switch to unnamed active profile
                    # and then to selector mg3

#                    self.assertTrue(lmgt.isMntGrpUpdated())
#                    self.assertTrue(lmgt.isMntGrpUpdated())
                    wmg = ""
                    lse["MntGrp"] = mg3
                    MSUtils.usetEnv(
                        'ActiveMntGrp', list(self._ms.ms.keys())[0])
                    lmgt.switchProfile()

                    # tmpcf1 =
                    json.loads(mgt[mg1].mntGrpConfiguration())
                    tmpcf2 = json.loads(mgt[mg2].mntGrpConfiguration())
                    tmpcf3 = json.loads(mgt[mg3].mntGrpConfiguration())
                    ltmpcf = json.loads(lmgt.mntGrpConfiguration())
                    self.myAssertDict(tmpcf3, ltmpcf)
#                    self.myAssertDict(tmpcf1, ltmpcf)
#                    self.myAssertDict(tmpcf2, ltmpcf)

                    self.compareToDumpJSON(
                        lse,
                        [
                            "DataSourceSelection",
                            "UnplottedComponents",
                            "PreselectingDataSources",
                            "Timer"],
                        name=mg3)
                    self.myAssertDict(json.loads(lse["DataSourceSelection"]),
                                      adss[mg3])
                    self.assertEqual(
                        set(json.loads(lse["PreselectingDataSources"])),
                        set(aadss[mg3]))

                    self.assertEqual(
                        set(json.loads(lse["UnplottedComponents"])),
                        mylhe)
                    self.assertEqual(json.loads(lse["OrderedChannels"]),
                                     pdss[mg3])
                    self.myAssertDict(json.loads(lse["UserData"]),
                                      records[mg3])
                    self.assertEqual(json.loads(lse["Timer"])[0],
                                     ltimers[mg3][0])
                    self.assertEqual(set(json.loads(lse["Timer"])),
                                     set(ltimers[mg3]))
                    self.assertEqual(lse["MntGrp"], mg3)

                    # fetch non-existing mg
                    wmg = "wrong_mg2"
                    lse["MntGrp"] = wmg
                    lmgt.fetchProfile()

                    # tmpcf1 =
                    json.loads(mgt[mg1].mntGrpConfiguration())
                    tmpcf2 = json.loads(mgt[mg2].mntGrpConfiguration())
                    tmpcf3 = json.loads(mgt[mg3].mntGrpConfiguration())
                    ltmpcf = json.loads(lmgt.mntGrpConfiguration())
#                    self.myAssertDict(tmpcf3, ltmpcf)
#                    self.myAssertDict(tmpcf1, ltmpcf)
#                    self.myAssertDict(tmpcf2, ltmpcf)

                    self.compareToDumpJSON(
                        lse,
                        [
                            "DataSourceSelection",
                            "UnplottedComponents",
                            "PreselectingDataSources",
                            "Timer", "MntGrp"],
                        name=mg3)
                    self.myAssertDict(json.loads(lse["DataSourceSelection"]),
                                      adss[mg3])
                    self.assertEqual(
                        set(json.loads(lse["PreselectingDataSources"])),
                        set(aadss[mg3]))

                    self.assertEqual(
                        set(json.loads(lse["UnplottedComponents"])),
                        mylhe)
                    self.assertEqual(json.loads(lse["OrderedChannels"]),
                                     pdss[mg3])
                    self.myAssertDict(json.loads(lse["UserData"]),
                                      records[mg3])
                    self.assertEqual(json.loads(lse["Timer"])[0],
                                     ltimers[mg3][0])
                    self.assertEqual(set(json.loads(lse["Timer"])),
                                     set(ltimers[mg3]))
                    self.assertEqual(lse["MntGrp"], wmg)
                    # print "MYLHE", mylhe
                    # fetch non-existing selection
                    self._cf.dp.deleteSelection(mg4)
                    lse["MntGrp"] = mg4
                    self.assertTrue(
                        mg4 not in self._cf.dp.availableSelections())
                    self.assertTrue(mg4 in lmgt.availableMntGrps())
                    if j % 2:
                        lmgt.defaultPreselectedComponents = \
                            list(json.loads(lse["ComponentPreselection"]
                                            ).keys())

                    lmgt.fetchProfile()
                    # tmpcf1 =
                    json.loads(mgt[mg1].mntGrpConfiguration())
                    tmpcf2 = json.loads(mgt[mg2].mntGrpConfiguration())
                    tmpcf3 = json.loads(mgt[mg3].mntGrpConfiguration())
                    tmpcf4 = json.loads(mgt[mg4].mntGrpConfiguration())
                    ltmpcf = json.loads(lmgt.mntGrpConfiguration())
                    self.myAssertDict(tmpcf4, ltmpcf)
#                    self.myAssertDict(tmpcf3, ltmpcf)
#                    self.myAssertDict(tmpcf1, ltmpcf)
#                    self.myAssertDict(tmpcf2, ltmpcf)

                    self.compareToDumpJSON(
                        lse,
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
                    self.assertEqual(
                        set(json.loads(lse["PreselectingDataSources"])),
                        set(aadss[mg3]))
                    self.assertEqual(
                        set(json.loads(lse["DataSourcePreselection"])),
                        set())

                    if j % 2:

                        cpgood = list(self.smycps.keys()) + \
                                 list(self.smycps2.keys())
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
                            json.loads(lse["ComponentPreselection"]),
                            myacps)
                    else:
                        self.myAssertDict(
                            json.loads(lse["ComponentPreselection"]),
                            {})

                    mycps = dict(cps[mg3])
                    for cp in mycps:
                        mycps[cp] = False
                    self.myAssertDict(
                        json.loads(lse["ComponentSelection"]), mycps)

                    self.assertEqual(json.loads(lse["OrderedChannels"]),
                                     pdss[mg3])
                    self.myAssertDict(json.loads(lse["UserData"]),
                                      records[mg3])
                    self.assertEqual(json.loads(lse["Timer"])[0],
                                     ltimers[mg4][0])
                    self.assertEqual(set(json.loads(lse["Timer"])),
                                     set(ltimers[mg4]))
                    self.assertEqual(lse["MntGrp"], mg4)

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

                    cpdss = mgt[mg3].componentDataSources()

                    for ds in json.loads(se[mg3]["UnplottedComponents"]):
                        if ds not in self.smychsXX.keys() \
                           and ds in self.smychs.keys() and ds in cpdss:
                            llhe.add(ds)
                    for ds in ladss.keys():
                        if ds in lhe2[mg4]:
                            llhe.add(ds)

                    for tm in json.loads(se[mg4]["Timer"]):
                        if tm in ladss:
                            if tm in llhe:
                                ladss[tm] = False
                                llhe.remove(tm)
                    for tm in json.loads(se[mg3]["Timer"]):
                        if tm in ladss:
                            if tm in json.loads(
                                    se[mg4]["UnplottedComponents"]):
                                ladss[tm] = False
                                if tm not in json.loads(se[mg4]["Timer"]):
                                    if tm in llhe:
                                        llhe.remove(tm)

                    for ds in self.smychs.keys():
                        if ds in llhe:
                            if ds in lhe2[mg3] and ds not in lhe2[mg4]:
                                llhe.remove(ds)

                    self.myAssertDict(json.loads(lse["DataSourceSelection"]),
                                      ladss)

                    mlhe = set(json.loads(lse["UnplottedComponents"]))
                    self.assertEqual(mlhe, llhe)

                finally:
                    for mg in mgt.keys():
                        try:
                            mgt[mg].deleteProfile(mgs[mg])
                        except Exception:
                            pass
                    for mg in tmg.keys():
                        try:
                            tmg[mg].tearDown()
                        except Exception:
                            pass
                    simp2.tearDown()
                    try:
                        self.tearDown()
                    except Exception:
                        pass
        finally:
            try:
                self.setUp()
            except Exception:
                pass


if __name__ == '__main__':
    unittest.main()
