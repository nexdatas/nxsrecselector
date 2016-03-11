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
## \file DynamicComponentTest.py
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
import xml.dom.minidom

import logging
logger = logging.getLogger()

import TestMacroServerSetUp
import TestPoolSetUp
import TestServerSetUp
import TestConfigServerSetUp
import TestWriterSetUp


from nxsrecconfig.MacroServerPools import MacroServerPools
from nxsrecconfig.DynamicComponent import DynamicComponent
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
        args = {'host': u'localhost', 'db': u'nxsconfig',
                'read_default_file': u'/etc/my.cnf', 'use_unicode': True}
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
            args2 = {'host': u'localhost', 'db': u'nxsconfig',
                     'read_default_file': u'%s/.my.cnf' % home,
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
class DynamicComponentTest(unittest.TestCase):

    ## constructor
    # \param methodName name of the test method
    def __init__(self, methodName):
        unittest.TestCase.__init__(self, methodName)

        self._bint = "int64" if IS64BIT else "int32"
        self._buint = "uint64" if IS64BIT else "uint32"
        self._bfloat = "float64" if IS64BIT else "float32"

#        self._ms = TestMacroServerSetUp.TestMacroServerSetUp()
        self._cf = TestConfigServerSetUp.TestConfigServerSetUp()
#        self._wr = TestWriterSetUp.TestWriterSetUp()
#        self._pool = TestPoolSetUp.TestPoolSetUp()
        self._simps = TestServerSetUp.TestServerSetUp()

        try:
            self.__seed = long(binascii.hexlify(os.urandom(16)), 16)
        except NotImplementedError:
            self.__seed = long(time.time() * 256)

        self.__rnd = random.Random(self.__seed)

        self.__dump = {}

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
            ("Labels", '{}'),
            ("LabelPaths", '{}'),
            ("LabelLinks", '{}'),
            ("UnplottedComponents", '[]'),
            ("LabelTypes", '{}'),
            ("LabelShapes", '{}'),
            ("DynamicComponents", True),
            ("DefaultDynamicLinks", True),
            ("DefaultDynamicPath", self.__defaultpath),
            ("TimeZone", self.__defaultzone),
            ("ConfigDevice", ''),
            ("WriterDevice", ''),
            ("Door", ''),
            ("MntGrpConfiguration", ''),
            ("MntGrp", '')
        ]

        self.mysel = {
            'mysl': (
                '{}'),
            'mysl2': (
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
                 '<record name="ttestp09/testts/t1r228/ScalarLong"/>'
                 '</datasource></definition>'),
            'client_short':
                ('<definition><datasource type="CLIENT" name="client_short">'
                 '<record name="ttestp09/testts/t1r228/ScalarShort"/>'
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
            'scalar_Encoded': ([]),
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
            'spectrum_Encoded': ([]),
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
            'image_Encoded':
                ([]),
            'image_uchar':
                ([2, 2]),
            'client_long':
                ([]),
            'client_short':
                ([]),
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

    ## test starter
    # \brief Common set up
    def setUp(self):
        print "SEED =", self.__seed
#        self._wr.setUp()
#        self._ms.setUp()
        self._cf.setUp()
#        self._pool.setUp()
        self._simps.setUp()
        print "\nsetting up..."

    ## test closer
    # \brief Common tear down
    def tearDown(self):
        print "tearing down ..."
        self._simps.tearDown()
#        self._pool.tearDown()
        self._cf.tearDown()
#        self._ms.tearDown()
#        self._wr.tearDown()

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
        self.assertTrue(isinstance(dct2, dict))
        logger.debug("%s %s" % (len(dct.keys()), len(dct2.keys())))
        self.assertEqual(len(dct.keys()), len(dct2.keys()))
        for k, v in dct.items():
            logger.debug("%s  in %s" % (str(k), str(dct2.keys())))
            self.assertTrue(k in dct2.keys())
            if isinstance(v, dict):
                self.myAssertDict(v, dct2[k])
            else:
                logger.debug("%s , %s" % (str(v), str(dct2[k])))
                self.assertEqual(v, dct2[k])

    ## constructor test
    # \brief It tests default settings
    def test_create_remove(self):
        fun = sys._getframe().f_code.co_name
        print "Run: %s.%s() " % (self.__class__.__name__, fun)
        cps = {"empty":
               '<?xml version="1.0" ?>\n<definition/>\n'}
        dname = "__dynamic_component__"
        dc = DynamicComponent(None)
        dc = DynamicComponent(self._cf.dp)

        cpname = dc.create()
        self.assertEqual(cpname, dname)
        self._cf.dp.Components([cpname])
        self.assertEqual(cps["empty"], self._cf.dp.Components([cpname])[0])

        cpname = dc.create()
        self.assertEqual(cpname, dname + "x")
        self._cf.dp.Components([cpname])
        self.assertEqual(cps["empty"], self._cf.dp.Components([cpname])[0])

        cpname = dc.create()
        self.assertEqual(cpname, dname + "xx")
        self._cf.dp.Components([cpname])
        self.assertEqual(cps["empty"], self._cf.dp.Components([cpname])[0])

        cpname = dc.create()
        self.assertEqual(cpname, dname + "xxx")
        self._cf.dp.Components([cpname])
        self.assertEqual(cps["empty"], self._cf.dp.Components([cpname])[0])

        dc.remove(dname + "xx")
        self.assertEqual(self._cf.dp.Components([dname + "xx"]), [])

        cpname = dc.create()
        self.assertEqual(cpname, dname + "xx")
        self._cf.dp.Components([cpname])
        self.assertEqual(cps["empty"], self._cf.dp.Components([cpname])[0])

        dc.remove(dname + "x")
        self.assertEqual(self._cf.dp.Components([dname + "x"]), [])

        dc.remove(dname + "xxx")
        self.assertEqual(self._cf.dp.Components([dname + "xxx"]), [])

        dc.remove(dname + "xx")
        self.assertEqual(self._cf.dp.Components([dname + "xx"]), [])

        dc.remove(dname + "xx")
        self.assertEqual(self._cf.dp.Components([dname + "xx"]), [])

        dc.remove(dname)
        self.assertEqual(self._cf.dp.Components([dname]), [])

        self.myAssertRaise(Exception, dc.remove, "sdfsdf")

    ## constructor test
    # \brief It tests default settings
    def test_create_dict(self):
        fun = sys._getframe().f_code.co_name
        print "Run: %s.%s() " % (self.__class__.__name__, fun)
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
        dc = DynamicComponent(self._cf.dp)
        for lb, ds in dsdict.items():
            dc.setStepDictDSources(ds)
            cpname = dc.create()
            comp = self._cf.dp.Components([cpname])[0]
            self.assertEqual(cps[lb], comp)

    ## constructor test
    # \brief It tests default settings
    def test_create_dict_type(self):
        fun = sys._getframe().f_code.co_name
        print "Run: %s.%s() " % (self.__class__.__name__, fun)
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
        dc = DynamicComponent(self._cf.dp)
        for tp, nxstp in self.__npTn.items():
            dc.setStepDictDSources([{"name": "ds1", "dtype": tp}])
            cpname = dc.create()
            comp = self._cf.dp.Components([cpname])[0]
            self.assertEqual(cps["type"] % nxstp, comp)

    ## constructor test
    # \brief It tests default settings
    def test_create_dict_shape(self):
        fun = sys._getframe().f_code.co_name
        print "Run: %s.%s() " % (self.__class__.__name__, fun)
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
        dc = DynamicComponent(self._cf.dp)
        for i in range(50):
            ms = [self.__rnd.randint(0, 3000)
                  for _ in range(self.__rnd.randint(0, 3))]
            dc.setStepDictDSources([{"name": "ds2", "shape": ms}])
            cpname = dc.create()
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

            dc = DynamicComponent(self._cf.dp)
            for i, ar in enumerate(arr):
                if '/' in ar["full_name"]:
                    db.put_device_alias(ar["full_name"], ar["name"])
#                print "I = ", i
                for tp, nxstp in self.__npTn.items():
                    lbl = self.getRandomName(20)
                    dc = DynamicComponent(self._cf.dp)
#                    print "TP = ", tp
                    ms = [self.__rnd.randint(0, 3000)
                          for _ in range(self.__rnd.randint(0, 3))]
                    ms2 = [self.__rnd.randint(0, 3000)
                           for _ in range(self.__rnd.randint(0, 3))]
                    tmptp = self.__rnd.choice(self.__npTn.keys())
                    if i == 0:
                        pass
                        dc.setDefaultLinkPath(False, self.__defaultpath)
                    elif i == 1:
                        dc.setDefaultLinkPath(True, self.__defaultpath)
                    elif i == 2:
                        dc.setLabelParams("{}", "{}",
                                          json.dumps({ar["name"]: False}),
                                          "{}", "{}")
                    elif i == 3:
                        dc.setLabelParams("{}", "{}",
                                          json.dumps({ar["name"]: True}),
                                          "{}", "{}")
                    elif i == 4:
                        dc.setDefaultLinkPath(True, self.__defaultpath)
                        dc.setLabelParams("{}", "{}",
                                          json.dumps({ar["name"]: False}),
                                          "{}", "{}")
                    elif i == 5:
                        dc.setDefaultLinkPath(False, self.__defaultpath)
                        dc.setLabelParams("{}", "{}",
                                          json.dumps({ar["name"]: True}),
                                          "{}", "{}")
                    elif i == 6:
                        dc.setDefaultLinkPath(False, self.__defaultpath)
                        dc.setLabelParams("{}", "{}",
                                          json.dumps({ar["full_name"]: True}),
                                          "{}",
                                          json.dumps({ar["name"]: ms2}))
                    elif i == 7:
                        dc.setLabelParams("{}", "{}", "{}",
                                          json.dumps({ar["name"]: tmptp}),
                                          "{}")
                    elif i == 8:
                        dc.setDefaultLinkPath(True, self.__defaultpath)
                        dc.setLabelParams(json.dumps({ar["name"]: lbl}),
                                          "{}",
                                          json.dumps({lbl: False}),
                                          "{}", "{}")
                    elif i == 9:
                        dc.setDefaultLinkPath(False, self.__defaultpath)
                        dc.setLabelParams(json.dumps({ar["name"]: lbl}),
                                          "{}",
                                          json.dumps({lbl: True}),
                                          "{}", "{}")
                    elif i == 10:
                        dc.setDefaultLinkPath(False, self.__defaultpath)
                        dc.setLabelParams(json.dumps({ar["name"]: lbl}),
                                          "{}",
                                          json.dumps({ar["full_name"]: True}),
                                          "{}",
                                          json.dumps({lbl: ms2}))
                    elif i == 11:
                        dc.setLabelParams(json.dumps({ar["name"]: lbl}),
                                          "{}", "{}",
                                          json.dumps({lbl: tmptp}),
                                          "{}")
                    dc.setStepDictDSources([{"name": ar["full_name"],
                                             "shape": ms,
                                             "dtype": tp}])
                    cpname = dc.create()
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
                    dc = DynamicComponent(self._cf.dp)

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
                        dc.setDefaultLinkPath(False, mypath)
                    elif i == 1:
                        dc.setDefaultLinkPath(True, mypath)
                    elif i == 2:
                        dc.setLabelParams(
                            "{}",
                            json.dumps({ar["name"]: mypath + "/" + fieldname}),
                            json.dumps({ar["name"]: False}),
                            "{}", "{}")
                    elif i == 3:
                        dc.setLabelParams(
                            "{}",
                            json.dumps({ar["name"]: mypath + "/" + fieldname}),
                            json.dumps({ar["name"]: True}),
                            "{}", "{}")
                    elif i == 4:
                        dc.setDefaultLinkPath(False, mypath)
                        dc.setLabelParams(
                            json.dumps({ar["name"]: lbl}),
                            "{}", "{}", "{}", "{}")
                    elif i == 5:
                        dc.setDefaultLinkPath(True, mypath)
                        dc.setLabelParams(
                            json.dumps({ar["name"]: lbl}),
                            "{}", "{}", "{}", "{}")
                    elif i == 6:
                        dc.setLabelParams(
                            json.dumps({ar["name"]: lbl}),
                            json.dumps({lbl: mypath + "/" + fieldname}),
                            json.dumps({lbl: False}),
                            "{}", "{}")
                    elif i == 7:
                        dc.setLabelParams(
                            json.dumps({ar["name"]: lbl}),
                            json.dumps({lbl: mypath + "/" + fieldname}),
                            json.dumps({lbl: True}),
                            "{}", "{}")
                    dc.setStepDictDSources([{"name": ar["full_name"],
                                             "shape": ms,
                                             "dtype": tp}])
                    cpname = dc.create()
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

                dc = DynamicComponent(self._cf.dp)
                dc.setStepDictDSources([{"name": ar["full_name"]}])
                cpname = dc.create()
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
        dc = DynamicComponent(self._cf.dp)
        for lb, ds in dsdict.items():
            dc.setStepDSources(ds)
            cpname = dc.create()
            comp = self._cf.dp.Components([cpname])[0]
#            print "COMP", comp
            self.assertEqual(cps[lb], comp)

    ## constructor test
    # \brief It tests default settings
    def test_create_step_init(self):
        fun = sys._getframe().f_code.co_name
        print "Run: %s.%s() " % (self.__class__.__name__, fun)
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
        dc = DynamicComponent(self._cf.dp)
        for lb, ds in dsdict.items():
            dc.setStepDSources(ds)
            dc.setInitDSources(ds)
            cpname = dc.create()
            comp = self._cf.dp.Components([cpname])[0]
#            print "COMP", comp
            self.assertEqual(cps[lb], comp)

    ## constructor test
    # \brief It tests default settings
    def test_create_step_no_type(self):
        fun = sys._getframe().f_code.co_name
        print "Run: %s.%s() " % (self.__class__.__name__, fun)
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
        dc = DynamicComponent(self._cf.dp)
        for tp, nxstp in self.__npTn.items():
            dc.setStepDSources(["ds1"])
#            dc.setStepDSources([{"name": "ds1", "dtype": tp}])
            cpname = dc.create()
            comp = self._cf.dp.Components([cpname])[0]
#            self.assertEqual(cps["type"] % nxstp, comp)
            self.assertEqual(cps["type"] % "NX_CHAR", comp)

    ## constructor test
    # \brief It tests default settings
    def test_create_init_no_type(self):
        fun = sys._getframe().f_code.co_name
        print "Run: %s.%s() " % (self.__class__.__name__, fun)
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
        dc = DynamicComponent(self._cf.dp)
        for tp, nxstp in self.__npTn.items():
            dc.setInitDSources(["ds1"])
#            dc.setStepDSources([{"name": "ds1", "dtype": tp}])
            cpname = dc.create()
            comp = self._cf.dp.Components([cpname])[0]
#            self.assertEqual(cps["type"] % nxstp, comp)
            self.assertEqual(cps["type"] % "NX_CHAR", comp)

    ## constructor test
    # \brief It tests default settings
    def test_create_step_type_param(self):
        fun = sys._getframe().f_code.co_name
        print "Run: %s.%s() " % (self.__class__.__name__, fun)
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
        dc = DynamicComponent(self._cf.dp)
        for tp, nxstp in self.__npTn.items():
            dc.setStepDSources(["ds1"])
            dc.setLabelParams("{}", "{}", "{}",
                              json.dumps({"ds1": nxstp}),
                              "{}")
            cpname = dc.create()
            comp = self._cf.dp.Components([cpname])[0]
            self.assertEqual(cps["type"] % nxstp, comp)

    ## constructor test
    # \brief It tests default settings
    def test_create_init_type_param(self):
        fun = sys._getframe().f_code.co_name
        print "Run: %s.%s() " % (self.__class__.__name__, fun)
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
        dc = DynamicComponent(self._cf.dp)
        for tp, nxstp in self.__npTn.items():
            dc.setInitDSources(["ds1"])
            dc.setLabelParams("{}", "{}", "{}",
                              json.dumps({"ds1": nxstp}),
                              "{}")
            cpname = dc.create()
            comp = self._cf.dp.Components([cpname])[0]
            self.assertEqual(cps["type"] % nxstp, comp)

    ## constructor test
    # \brief It tests default settings
    def test_create_step_shape(self):
        fun = sys._getframe().f_code.co_name
        print "Run: %s.%s() " % (self.__class__.__name__, fun)
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
        dc = DynamicComponent(self._cf.dp)
        for i in range(50):
            ms = [self.__rnd.randint(0, 3000)
                  for _ in range(self.__rnd.randint(0, 3))]
            dc.setLabelParams("{}", "{}", "{}",
                              "{}",
                              json.dumps({"ds2": ms}))
            dc.setStepDSources(["ds2"])
            cpname = dc.create()
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
        dc = DynamicComponent(self._cf.dp)
        for i in range(50):
            ms = [self.__rnd.randint(0, 3000)
                  for _ in range(self.__rnd.randint(0, 3))]
            dc.setLabelParams("{}", "{}", "{}",
                              "{}",
                              json.dumps({"ds2": ms}))
            dc.setInitDSources(["ds2"])
            cpname = dc.create()
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
            dc = DynamicComponent(self._cf.dp)
            for i, ar in enumerate(arr):
                for tp, nxstp in self.__npTn.items():
                    lbl = self.getRandomName(20)
                    dc = DynamicComponent(self._cf.dp)
                    ms = [self.__rnd.randint(0, 3000)
                          for _ in range(self.__rnd.randint(0, 3))]
                    ms2 = [self.__rnd.randint(0, 3000)
                           for _ in range(self.__rnd.randint(0, 3))]
                    tmptp = self.__rnd.choice(self.__npTn.keys())
                    if i == 0:
                        dc.setDefaultLinkPath(False, self.__defaultpath)
                        dc.setLabelParams("{}", "{}", "{}",
                                          json.dumps({ar["name"]: nxstp}),
                                          json.dumps({ar["name"]: ms}))
                    elif i == 1:
                        dc.setDefaultLinkPath(True, self.__defaultpath)
                        dc.setLabelParams("{}", "{}", "{}",
                                          json.dumps({ar["name"]: nxstp}),
                                          json.dumps({ar["name"]: ms}))
                    elif i == 2:
                        dc.setLabelParams("{}", "{}",
                                          json.dumps({ar["name"]: False}),
                                          json.dumps({ar["name"]: nxstp}),
                                          json.dumps({ar["name"]: ms}))
                    elif i == 3:
                        dc.setLabelParams("{}", "{}",
                                          json.dumps({ar["name"]: True}),
                                          json.dumps({ar["name"]: nxstp}),
                                          json.dumps({ar["name"]: ms}))
                    elif i == 4:
                        dc.setDefaultLinkPath(True, self.__defaultpath)
                        dc.setLabelParams("{}", "{}",
                                          json.dumps({ar["name"]: False}),
                                          json.dumps({ar["name"]: nxstp}),
                                          json.dumps({ar["name"]: ms}))
                    elif i == 5:
                        dc.setDefaultLinkPath(False, self.__defaultpath)
                        dc.setLabelParams("{}", "{}",
                                          json.dumps({ar["name"]: True}),
                                          json.dumps({ar["name"]: nxstp}),
                                          json.dumps({ar["name"]: ms}))
                    elif i == 6:
                        dc.setDefaultLinkPath(False, self.__defaultpath)
                        dc.setLabelParams("{}", "{}",
                                          json.dumps({"dssd": True}),
                                          json.dumps({ar["name"]: nxstp}),
                                          json.dumps({ar["name"]: ms}))
                    elif i == 7:
                        dc.setLabelParams(json.dumps({ar["name"]: lbl}),
                                          "{}", "{}",
                                          json.dumps({ar["name"]: nxstp}),
                                          json.dumps({ar["name"]: ms}))
                    elif i == 8:
                        pass
                        dc.setDefaultLinkPath(False, self.__defaultpath)
                        dc.setLabelParams(json.dumps({ar["name"]: lbl}),
                                          "{}", "{}",
                                          json.dumps({lbl: nxstp}),
                                          json.dumps({lbl: ms}))
                    elif i == 9:
                        dc.setDefaultLinkPath(True, self.__defaultpath)
                        dc.setLabelParams(json.dumps({ar["name"]: lbl}),
                                          "{}", "{}",
                                          json.dumps({lbl: nxstp}),
                                          json.dumps({lbl: ms}))
                    elif i == 10:
                        dc.setLabelParams(json.dumps({ar["name"]: lbl}),
                                          "{}",
                                          json.dumps({lbl: False}),
                                          json.dumps({lbl: nxstp}),
                                          json.dumps({lbl: ms}))
                    elif i == 11:
                        dc.setLabelParams(json.dumps({ar["name"]: lbl}),
                                          "{}",
                                          json.dumps({lbl: True}),
                                          json.dumps({lbl: nxstp}),
                                          json.dumps({lbl: ms}))
                    elif i == 12:
                        dc.setDefaultLinkPath(True, self.__defaultpath)
                        dc.setLabelParams(json.dumps({ar["name"]: lbl}),
                                          "{}",
                                          json.dumps({lbl: False}),
                                          json.dumps({lbl: nxstp}),
                                          json.dumps({lbl: ms}))
                    elif i == 13:
                        dc.setDefaultLinkPath(False, self.__defaultpath)
                        dc.setLabelParams(json.dumps({ar["name"]: lbl}),
                                          "{}",
                                          json.dumps({lbl: True}),
                                          json.dumps({lbl: nxstp}),
                                          json.dumps({lbl: ms}))
                    elif i == 14:
                        dc.setDefaultLinkPath(False, self.__defaultpath)
                        dc.setLabelParams(json.dumps({ar["name"]: lbl}),
                                          "{}",
                                          json.dumps({"dssd": True}),
                                          json.dumps({lbl: nxstp}),
                                          json.dumps({lbl: ms}))
                    elif i == 15:
                        dc.setLabelParams(json.dumps({ar["name"]: lbl}),
                                          "{}", "{}",
                                          json.dumps({lbl: nxstp}),
                                          json.dumps({ar["name"]: ms}))

                    dc.setStepDSources([ar["name"]])
                    cpname = dc.create()
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
            dc = DynamicComponent(self._cf.dp)
            for i, ar in enumerate(arr):
                for tp, nxstp in self.__npTn.items():
                    lbl = self.getRandomName(20)
                    dc = DynamicComponent(self._cf.dp)
#                    print "TP = ", tp, i
                    ms = [self.__rnd.randint(0, 3000)
                          for _ in range(self.__rnd.randint(0, 3))]
                    ms2 = [self.__rnd.randint(0, 3000)
                           for _ in range(self.__rnd.randint(0, 3))]
                    tmptp = self.__rnd.choice(self.__npTn.keys())
                    if i == 0:
                        dc.setDefaultLinkPath(False, self.__defaultpath)
                        dc.setLabelParams("{}", "{}", "{}",
                                          json.dumps({ar["name"]: nxstp}),
                                          json.dumps({ar["name"]: ms}))
                    elif i == 1:
                        dc.setDefaultLinkPath(True, self.__defaultpath)
                        dc.setLabelParams("{}", "{}", "{}",
                                          json.dumps({ar["name"]: nxstp}),
                                          json.dumps({ar["name"]: ms}))
                    elif i == 2:
                        dc.setLabelParams("{}", "{}",
                                          json.dumps({ar["name"]: False}),
                                          json.dumps({ar["name"]: nxstp}),
                                          json.dumps({ar["name"]: ms}))
                    elif i == 3:
                        dc.setLabelParams("{}", "{}",
                                          json.dumps({ar["name"]: True}),
                                          json.dumps({ar["name"]: nxstp}),
                                          json.dumps({ar["name"]: ms}))
                    elif i == 4:
                        dc.setDefaultLinkPath(True, self.__defaultpath)
                        dc.setLabelParams("{}", "{}",
                                          json.dumps({ar["name"]: False}),
                                          json.dumps({ar["name"]: nxstp}),
                                          json.dumps({ar["name"]: ms}))
                    elif i == 5:
                        dc.setDefaultLinkPath(False, self.__defaultpath)
                        dc.setLabelParams("{}", "{}",
                                          json.dumps({ar["name"]: True}),
                                          json.dumps({ar["name"]: nxstp}),
                                          json.dumps({ar["name"]: ms}))
                    elif i == 6:
                        dc.setDefaultLinkPath(False, self.__defaultpath)
                        dc.setLabelParams("{}", "{}",
                                          json.dumps({"dssd": True}),
                                          json.dumps({ar["name"]: nxstp}),
                                          json.dumps({ar["name"]: ms}))
                    elif i == 7:
                        dc.setLabelParams(json.dumps({ar["name"]: lbl}),
                                          "{}", "{}",
                                          json.dumps({ar["name"]: nxstp}),
                                          json.dumps({ar["name"]: ms}))
                    elif i == 8:
                        pass
                        dc.setDefaultLinkPath(False, self.__defaultpath)
                        dc.setLabelParams(json.dumps({ar["name"]: lbl}),
                                          "{}", "{}",
                                          json.dumps({lbl: nxstp}),
                                          json.dumps({lbl: ms}))
                    elif i == 9:
                        dc.setDefaultLinkPath(True, self.__defaultpath)
                        dc.setLabelParams(json.dumps({ar["name"]: lbl}),
                                          "{}", "{}",
                                          json.dumps({lbl: nxstp}),
                                          json.dumps({lbl: ms}))
                    elif i == 10:
                        dc.setLabelParams(json.dumps({ar["name"]: lbl}),
                                          "{}",
                                          json.dumps({lbl: False}),
                                          json.dumps({lbl: nxstp}),
                                          json.dumps({lbl: ms}))
                    elif i == 11:
                        dc.setLabelParams(json.dumps({ar["name"]: lbl}),
                                          "{}",
                                          json.dumps({lbl: True}),
                                          json.dumps({lbl: nxstp}),
                                          json.dumps({lbl: ms}))
                    elif i == 12:
                        dc.setDefaultLinkPath(True, self.__defaultpath)
                        dc.setLabelParams(json.dumps({ar["name"]: lbl}),
                                          "{}",
                                          json.dumps({lbl: False}),
                                          json.dumps({lbl: nxstp}),
                                          json.dumps({lbl: ms}))
                    elif i == 13:
                        dc.setDefaultLinkPath(False, self.__defaultpath)
                        dc.setLabelParams(json.dumps({ar["name"]: lbl}),
                                          "{}",
                                          json.dumps({lbl: True}),
                                          json.dumps({lbl: nxstp}),
                                          json.dumps({lbl: ms}))
                    elif i == 14:
                        dc.setDefaultLinkPath(False, self.__defaultpath)
                        dc.setLabelParams(json.dumps({ar["name"]: lbl}),
                                          "{}",
                                          json.dumps({"dssd": True}),
                                          json.dumps({lbl: nxstp}),
                                          json.dumps({lbl: ms}))
                    elif i == 15:
                        dc.setLabelParams(json.dumps({ar["name"]: lbl}),
                                          "{}", "{}",
                                          json.dumps({lbl: nxstp}),
                                          json.dumps({ar["name"]: ms}))

                    dc.setInitDSources([ar["name"]])
                    cpname = dc.create()
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
        dc = DynamicComponent(self._cf.dp)
        for i in range(4):
            for ds, dsxml in self.smydss.items():
                ms = self.smydsspar[ds]
                sds = ds.split("_")
                tp = sds[1]
                dc.setStepDSources([ds])

                if i == 0:
                    dc.setDefaultLinkPath(False, self.__defaultpath)
                    dc.setLabelParams("{}", "{}", "{}", "{}", "{}")
                elif i == 1:
                    dc.setDefaultLinkPath(True, self.__defaultpath)
                    dc.setLabelParams("{}", "{}", "{}", "{}", "{}")
                elif i == 2:
                    dc.setLabelParams("{}", "{}",
                                      json.dumps({ds: False}), "{}", "{}")
                elif i == 3:
                    dc.setLabelParams("{}", "{}",
                                      json.dumps({ds: True}), "{}", "{}")

                cpname = dc.create()
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

                dc = DynamicComponent(self._cf.dp)
                for ds, dsxml in self.smydss.items():
                    dc.setStepDSources([ar["name"]])
                cpname = dc.create()
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

                dc = DynamicComponent(self._cf.dp)
                for ds, dsxml in self.smydss.items():
                    dc.setInitDSources([ar["name"]])
                cpname = dc.create()
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

#        self._cf.dp.SetCommandVariable(["DSDICT", json.dumps(self.smydss)])
        dc = DynamicComponent(self._cf.dp)
        for i in range(4):
            for ds, dsxml in self.smydss.items():
                ms = self.smydsspar[ds]
                sds = ds.split("_")
                tp = sds[1]
                dc.setInitDSources([ds])

                if i == 0:
                    dc.setDefaultLinkPath(False, self.__defaultpath)
                    dc.setLabelParams("{}", "{}", "{}", "{}", "{}")
                elif i == 1:
                    dc.setDefaultLinkPath(True, self.__defaultpath)
                    dc.setLabelParams("{}", "{}", "{}", "{}", "{}")
                elif i == 2:
                    dc.setLabelParams("{}", "{}",
                                      json.dumps({ds: False}), "{}", "{}")
                elif i == 3:
                    dc.setLabelParams("{}", "{}",
                                      json.dumps({ds: True}), "{}", "{}")

                cpname = dc.create()
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
    def test_create_step_typeshape_tango(self):
        fun = sys._getframe().f_code.co_name
        print "Run: %s.%s() " % (self.__class__.__name__, fun)

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
        dc = DynamicComponent(self._cf.dp)
        for i in range(4):
            for ds, dsxml in self.smydss.items():
                ms = self.smydsspar[ds]
                sds = ds.split("_")
                tp = sds[1]
                dc.setStepDSources([ds])

                if i == 0:
                    dc.setDefaultLinkPath(False, self.__defaultpath)
                    dc.setLabelParams("{}", "{}", "{}", "{}", "{}")
                elif i == 1:
                    dc.setDefaultLinkPath(True, self.__defaultpath)
                    dc.setLabelParams("{}", "{}", "{}", "{}", "{}")
                elif i == 2:
                    dc.setLabelParams("{}", "{}",
                                      json.dumps({ds: False}), "{}", "{}")
                elif i == 3:
                    dc.setLabelParams("{}", "{}",
                                      json.dumps({ds: True}), "{}", "{}")

                cpname = dc.create()
                comp = self._cf.dp.Components([cpname])[0]

                indom = xml.dom.minidom.parseString(dsxml)
                dss = indom.getElementsByTagName("datasource")
                if not ds.startswith("client_") and sds[1] != 'Encoded':
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
        dc = DynamicComponent(self._cf.dp)
        for i in range(4):
            for ds, dsxml in self.smydss.items():
                ms = self.smydsspar[ds]
                sds = ds.split("_")
                tp = sds[1]
                dc.setInitDSources([ds])

                if i == 0:
                    dc.setDefaultLinkPath(False, self.__defaultpath)
                    dc.setLabelParams("{}", "{}", "{}", "{}", "{}")
                elif i == 1:
                    dc.setDefaultLinkPath(True, self.__defaultpath)
                    dc.setLabelParams("{}", "{}", "{}", "{}", "{}")
                elif i == 2:
                    dc.setLabelParams("{}", "{}",
                                      json.dumps({ds: False}), "{}", "{}")
                elif i == 3:
                    dc.setLabelParams("{}", "{}",
                                      json.dumps({ds: True}), "{}", "{}")

                cpname = dc.create()
                comp = self._cf.dp.Components([cpname])[0]

                indom = xml.dom.minidom.parseString(dsxml)
                dss = indom.getElementsByTagName("datasource")
                if not ds.startswith("client_") and sds[1] != 'Encoded':
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
                dc = DynamicComponent(self._cf.dp)
                ms = self.smydsspar[ds]
                ms2 = [self.__rnd.randint(0, 3000)
                       for _ in range(self.__rnd.randint(0, 3))]
                lbl = self.getRandomName(20)
                sds = ds.split("_")
                tp = sds[1]
                dc.setStepDSources([ds])

                if i == 0:
                    dc.setDefaultLinkPath(False, self.__defaultpath)
                    dc.setLabelParams("{}", "{}", "{}",
                                      json.dumps({ds: nxstp}),
                                      json.dumps({ds: ms2}))
                elif i == 1:
                    dc.setDefaultLinkPath(True, self.__defaultpath)
                    dc.setLabelParams("{}", "{}", "{}",
                                      json.dumps({ds: nxstp}),
                                      json.dumps({ds: ms2}))
                elif i == 2:
                    dc.setLabelParams("{}", "{}",
                                      json.dumps({ds: False}),
                                      json.dumps({ds: nxstp}),
                                      json.dumps({ds: ms2}))
                elif i == 3:
                    dc.setLabelParams("{}", "{}",
                                      json.dumps({ds: True}),
                                      json.dumps({ds: nxstp}),
                                      json.dumps({ds: ms2}))
                elif i == 4:
                    dc.setDefaultLinkPath(True, self.__defaultpath)
                    dc.setLabelParams("{}", "{}",
                                      json.dumps({ds: False}),
                                      json.dumps({ds: nxstp}),
                                      json.dumps({ds: ms2}))
                elif i == 5:
                    dc.setDefaultLinkPath(False, self.__defaultpath)
                    dc.setLabelParams("{}", "{}",
                                      json.dumps({ds: True}),
                                      json.dumps({ds: nxstp}),
                                      json.dumps({ds: ms2}))
                elif i == 6:
                    dc.setDefaultLinkPath(False, self.__defaultpath)
                    dc.setLabelParams("{}", "{}",
                                      json.dumps({"dssd": True}),
                                      json.dumps({ds: nxstp}),
                                      json.dumps({ds: ms2}))
                elif i == 7:
                    dc.setLabelParams(json.dumps({ds: lbl}),
                                      "{}", "{}",
                                      json.dumps({ds: nxstp}),
                                      json.dumps({ds: ms2}))
                elif i == 8:
                    pass
                    dc.setDefaultLinkPath(False, self.__defaultpath)
                    dc.setLabelParams(json.dumps({ds: lbl}),
                                      "{}", "{}",
                                      json.dumps({lbl: nxstp}),
                                      json.dumps({lbl: ms2}))
                elif i == 9:
                    dc.setDefaultLinkPath(True, self.__defaultpath)
                    dc.setLabelParams(json.dumps({ds: lbl}),
                                      "{}", "{}",
                                      json.dumps({lbl: nxstp}),
                                      json.dumps({lbl: ms2}))
                elif i == 10:
                    dc.setLabelParams(json.dumps({ds: lbl}),
                                      "{}",
                                      json.dumps({lbl: False}),
                                      json.dumps({lbl: nxstp}),
                                      json.dumps({lbl: ms2}))
                elif i == 11:
                    dc.setLabelParams(json.dumps({ds: lbl}),
                                      "{}",
                                      json.dumps({lbl: True}),
                                      json.dumps({lbl: nxstp}),
                                      json.dumps({lbl: ms2}))
                elif i == 12:
                    dc.setDefaultLinkPath(True, self.__defaultpath)
                    dc.setLabelParams(json.dumps({ds: lbl}),
                                      "{}",
                                      json.dumps({lbl: False}),
                                      json.dumps({lbl: nxstp}),
                                      json.dumps({lbl: ms2}))
                elif i == 13:
                    dc.setDefaultLinkPath(False, self.__defaultpath)
                    dc.setLabelParams(json.dumps({ds: lbl}),
                                      "{}",
                                      json.dumps({lbl: True}),
                                      json.dumps({lbl: nxstp}),
                                      json.dumps({lbl: ms2}))
                elif i == 14:
                    dc.setDefaultLinkPath(False, self.__defaultpath)
                    dc.setLabelParams(json.dumps({ds: lbl}),
                                      "{}",
                                      json.dumps({"dssd": True}),
                                      json.dumps({lbl: nxstp}),
                                      json.dumps({lbl: ms2}))
                elif i == 15:
                    dc.setLabelParams(json.dumps({ds: lbl}),
                                      "{}", "{}",
                                      json.dumps({lbl: nxstp}),
                                      json.dumps({ds: ms2}))

                cpname = dc.create()
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
                dc = DynamicComponent(self._cf.dp)
                ms = self.smydsspar[ds]
                ms2 = [self.__rnd.randint(0, 3000)
                       for _ in range(self.__rnd.randint(0, 3))]
                lbl = self.getRandomName(20)
                sds = ds.split("_")
                tp = sds[1]
                dc.setInitDSources([ds])

                if i == 0:
                    dc.setDefaultLinkPath(False, self.__defaultpath)
                    dc.setLabelParams("{}", "{}", "{}",
                                      json.dumps({ds: nxstp}),
                                      json.dumps({ds: ms2}))
                elif i == 1:
                    dc.setDefaultLinkPath(True, self.__defaultpath)
                    dc.setLabelParams("{}", "{}", "{}",
                                      json.dumps({ds: nxstp}),
                                      json.dumps({ds: ms2}))
                elif i == 2:
                    dc.setLabelParams("{}", "{}",
                                      json.dumps({ds: False}),
                                      json.dumps({ds: nxstp}),
                                      json.dumps({ds: ms2}))
                elif i == 3:
                    dc.setLabelParams("{}", "{}",
                                      json.dumps({ds: True}),
                                      json.dumps({ds: nxstp}),
                                      json.dumps({ds: ms2}))
                elif i == 4:
                    dc.setDefaultLinkPath(True, self.__defaultpath)
                    dc.setLabelParams("{}", "{}",
                                      json.dumps({ds: False}),
                                      json.dumps({ds: nxstp}),
                                      json.dumps({ds: ms2}))
                elif i == 5:
                    dc.setDefaultLinkPath(False, self.__defaultpath)
                    dc.setLabelParams("{}", "{}",
                                      json.dumps({ds: True}),
                                      json.dumps({ds: nxstp}),
                                      json.dumps({ds: ms2}))
                elif i == 6:
                    dc.setDefaultLinkPath(False, self.__defaultpath)
                    dc.setLabelParams("{}", "{}",
                                      json.dumps({"dssd": True}),
                                      json.dumps({ds: nxstp}),
                                      json.dumps({ds: ms2}))
                elif i == 7:
                    dc.setLabelParams(json.dumps({ds: lbl}),
                                      "{}", "{}",
                                      json.dumps({ds: nxstp}),
                                      json.dumps({ds: ms2}))
                elif i == 8:
                    pass
                    dc.setDefaultLinkPath(False, self.__defaultpath)
                    dc.setLabelParams(json.dumps({ds: lbl}),
                                      "{}", "{}",
                                      json.dumps({lbl: nxstp}),
                                      json.dumps({lbl: ms2}))
                elif i == 9:
                    dc.setDefaultLinkPath(True, self.__defaultpath)
                    dc.setLabelParams(json.dumps({ds: lbl}),
                                      "{}", "{}",
                                      json.dumps({lbl: nxstp}),
                                      json.dumps({lbl: ms2}))
                elif i == 10:
                    dc.setLabelParams(json.dumps({ds: lbl}),
                                      "{}",
                                      json.dumps({lbl: False}),
                                      json.dumps({lbl: nxstp}),
                                      json.dumps({lbl: ms2}))
                elif i == 11:
                    dc.setLabelParams(json.dumps({ds: lbl}),
                                      "{}",
                                      json.dumps({lbl: True}),
                                      json.dumps({lbl: nxstp}),
                                      json.dumps({lbl: ms2}))
                elif i == 12:
                    dc.setDefaultLinkPath(True, self.__defaultpath)
                    dc.setLabelParams(json.dumps({ds: lbl}),
                                      "{}",
                                      json.dumps({lbl: False}),
                                      json.dumps({lbl: nxstp}),
                                      json.dumps({lbl: ms2}))
                elif i == 13:
                    dc.setDefaultLinkPath(False, self.__defaultpath)
                    dc.setLabelParams(json.dumps({ds: lbl}),
                                      "{}",
                                      json.dumps({lbl: True}),
                                      json.dumps({lbl: nxstp}),
                                      json.dumps({lbl: ms2}))
                elif i == 14:
                    dc.setDefaultLinkPath(False, self.__defaultpath)
                    dc.setLabelParams(json.dumps({ds: lbl}),
                                      "{}",
                                      json.dumps({"dssd": True}),
                                      json.dumps({lbl: nxstp}),
                                      json.dumps({lbl: ms2}))
                elif i == 15:
                    dc.setLabelParams(json.dumps({ds: lbl}),
                                      "{}", "{}",
                                      json.dumps({lbl: nxstp}),
                                      json.dumps({ds: ms2}))

                cpname = dc.create()
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
                    if not ds.startswith("client_") and sds[1] != 'Encoded':
                        nxstp = self.__npTn2[tp]
                    else:
                        nxstp = 'NX_CHAR'
                    dc = DynamicComponent(self._cf.dp)

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
                    if i == 0:
                        dc.setDefaultLinkPath(False, mypath)
                    elif i == 1:
                        dc.setDefaultLinkPath(True, mypath)
                    elif i == 2:
                        dc.setLabelParams(
                            "{}",
                            json.dumps({ds: mypath + "/" + fieldname}),
                            json.dumps({ds: False}),
                            "{}", "{}")
                    elif i == 3:
                        dc.setLabelParams(
                            "{}",
                            json.dumps({ds: mypath + "/" + fieldname}),
                            json.dumps({ds: True}),
                            "{}", "{}")
                    elif i == 4:
                        dc.setDefaultLinkPath(False, mypath)
                        dc.setLabelParams(
                            json.dumps({ds: lbl}),
                            "{}", "{}", "{}", "{}")
                    elif i == 5:
                        dc.setDefaultLinkPath(True, mypath)
                        dc.setLabelParams(
                            json.dumps({ds: lbl}),
                            "{}", "{}", "{}", "{}")
                    elif i == 6:
                        dc.setLabelParams(
                            json.dumps({ds: lbl}),
                            json.dumps({lbl: mypath + "/" + fieldname}),
                            json.dumps({lbl: False}),
                            "{}", "{}")
                    elif i == 7:
                        dc.setLabelParams(
                            json.dumps({ds: lbl}),
                            json.dumps({lbl: mypath + "/" + fieldname}),
                            json.dumps({lbl: True}),
                            "{}", "{}")
#@                    dc.setStepDSources([{"name": ar["full_name"],
#                                             "shape": ms,
#                                             "dtype": tp}])
                    dc.setStepDSources([ds])
                    cpname = dc.create()
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
                    if not ds.startswith("client_") and sds[1] != 'Encoded':
                        nxstp = self.__npTn2[tp]
                    else:
                        nxstp = 'NX_CHAR'
                    dc = DynamicComponent(self._cf.dp)

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
                    if i == 0:
                        dc.setDefaultLinkPath(False, mypath)
                    elif i == 1:
                        dc.setDefaultLinkPath(True, mypath)
                    elif i == 2:
                        dc.setLabelParams(
                            "{}",
                            json.dumps({ds: mypath + "/" + fieldname}),
                            json.dumps({ds: False}),
                            "{}", "{}")
                    elif i == 3:
                        dc.setLabelParams(
                            "{}",
                            json.dumps({ds: mypath + "/" + fieldname}),
                            json.dumps({ds: True}),
                            "{}", "{}")
                    elif i == 4:
                        dc.setDefaultLinkPath(False, mypath)
                        dc.setLabelParams(
                            json.dumps({ds: lbl}),
                            "{}", "{}", "{}", "{}")
                    elif i == 5:
                        dc.setDefaultLinkPath(True, mypath)
                        dc.setLabelParams(
                            json.dumps({ds: lbl}),
                            "{}", "{}", "{}", "{}")
                    elif i == 6:
                        dc.setLabelParams(
                            json.dumps({ds: lbl}),
                            json.dumps({lbl: mypath + "/" + fieldname}),
                            json.dumps({lbl: False}),
                            "{}", "{}")
                    elif i == 7:
                        dc.setLabelParams(
                            json.dumps({ds: lbl}),
                            json.dumps({lbl: mypath + "/" + fieldname}),
                            json.dumps({lbl: True}),
                            "{}", "{}")
#@                    dc.setInitDSources([{"name": ar["full_name"],
#                                             "shape": ms,
#                                             "dtype": tp}])
                    dc.setInitDSources([ds])
                    cpname = dc.create()
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

if __name__ == '__main__':
    unittest.main()
