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
# \file MacroServerPoolTest.py
# unittests for TangoDsItemTest running Tango Server
#
import unittest
import os
import sys
import random
import struct
import binascii
import PyTango
import time
import json
import pickle

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
    import TestConfigServerSetUp
except Exception:
    from . import TestConfigServerSetUp


from nxsrecconfig.MacroServerPools import MacroServerPools

import logging
logger = logging.getLogger()

if sys.version_info > (3,):
    long = int

# if 64-bit machione
IS64BIT = (struct.calcsize("P") == 8)


# test fixture
class MacroServerPoolsTest(unittest.TestCase):

    # constructor
    # \param methodName name of the test method

    def __init__(self, methodName):
        unittest.TestCase.__init__(self, methodName)

        self._bint = "int64" if IS64BIT else "int32"
        self._buint = "uint64" if IS64BIT else "uint32"
        self._bfloat = "float64" if IS64BIT else "float32"

        self._ms = TestMacroServerSetUp.TestMacroServerSetUp()
        self._cf = TestConfigServerSetUp.TestConfigServerSetUp()
        self._pool = TestPoolSetUp.TestPoolSetUp()
        self._simps = TestServerSetUp.TestServerSetUp()

        try:
            self.__seed = long(binascii.hexlify(os.urandom(16)), 16)
        except NotImplementedError:
            self.__seed = long(time.time() * 256)

        self.__rnd = random.Random(self.__seed)

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
            'smycppc1': (
                '<definition><group type="NXcollection" name="ddddntcp">'
                '<field name="long">'
                '$datasources.string_list<strategy mode="FINAL"/></field>'
                '<field name="short">'
                '$datasources.get_float<strategy mode="STEP"/></field>'
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
            's2mycppc1': (
                '<definition><group type="NXcollection" name="ddddntcp">'
                '<field name="long">'
                '$datasources.string2_list<strategy mode="FINAL"/></field>'
                '<field name="short">'
                '$datasources.get2_float<strategy mode="STEP"/></field>'
                '</group></definition>'),
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
            'image_long64': (
                '<definition><datasource type="TANGO" name="image_long64">'
                '<record name="ImageLong64"/>'
                '<device member="attribute" name="ttestp09/testts/t1r228"/>'
                '</datasource></definition>'),
            'image_ulong64': (
                '<definition><datasource type="TANGO" name="image_ulong64">'
                '<record name="ImageULong64"/>'
                '<device member="attribute" name="ttestp09/testts/t1r228"/>'
                '</datasource></definition>'),
            'image_float': (
                '<definition><datasource type="TANGO" name="image_float">'
                '<record name="ImageFloat"/>'
                '<device member="attribute" name="ttestp09/testts/t1r228"/>'
                '</datasource></definition>'),
            'image_double': (
                '<definition><datasource type="TANGO" name="image_double">'
                '<record name="ImageDouble"/>'
                '<device member="attribute" name="ttestp09/testts/t1r228"/>'
                '</datasource></definition>'),
            'image_string': (
                '<definition><datasource type="TANGO" name="image_string">'
                '<record name="ImageString"/>'
                '<device member="attribute" name="ttestp09/testts/t1r228"/>'
                '</datasource></definition>'),
            'image_Encoded': (
                '<definition><datasource type="TANGO" name="image_encoded">'
                '<record name="ImageEncoded"/>'
                '<device member="attribute" name="ttestp09/testts/t1r228"/>'
                '</datasource></definition>'),
            'image_uchar': (
                '<definition><datasource type="TANGO" name="image_uchar">'
                '<record name="ImageUChar"/>'
                '<device member="attribute" name="ttestp09/testts/t1r228"/>'
                '</datasource></definition>'),
            'client_long': (
                '<definition><datasource type="CLIENT" name="client_long">'
                '<record name="ClientLong"/>'
                '</datasource></definition>'),
            'client_short': (
                '<definition><datasource type="CLIENT" name="client_short">'
                '<record name="ClientShort"/>'
                '</datasource></definition>'),
            'string_list': (
                '<definition><datasource type="TANGO" name="string_list">'
                '<record name="StringList"/>'
                '<device member="property" name="ttestp09/testts/t1r228"/>'
                '</datasource></definition>'),
            'get_float': (
                '<definition><datasource type="TANGO" name="get_float">'
                '<record name="GetFloat"/>'
                '<device member="command" name="ttestp09/testts/t1r228"/>'
                '</datasource></definition>'),
        }

        self.smydss2 = {
            'scalar2_long': (
                '<definition><datasource type="TANGO" name="scalar2_long">'
                '<record name="ScalarLong"/>'
                '<device member="attribute" name="ttestp09/testts/t2r228"/>'
                '</datasource></definition>'),
            'scalar2_bool': (
                '<definition><datasource type="TANGO" name="scalar2_bool">'
                '<record name="ScalarBoolean"/>'
                '<device member="attribute" name="ttestp09/testts/t2r228"/>'
                '</datasource></definition>'),
            'scalar2_short': (
                '<definition><datasource type="TANGO" name="scalar2_short">'
                '<record name="ScalarShort"/>'
                '<device member="attribute" name="ttestp09/testts/t2r228"/>'
                '</datasource></definition>'),
            'scalar2_ushort': (
                '<definition><datasource type="TANGO" name="scalar2_ushort">'
                '<record name="ScalarUShort"/>'
                '<device member="attribute" name="ttestp09/testts/t2r228"/>'
                '</datasource></definition>'),
            'scalar2_ulong': (
                '<definition><datasource type="TANGO" name="scalar2_ulong">'
                '<record name="ScalarULong"/>'
                '<device member="attribute" name="ttestp09/testts/t2r228"/>'
                '</datasource></definition>'),
            'scalar2_long64': (
                '<definition><datasource type="TANGO" name="scalar2_long64">'
                '<record name="ScalarLong64"/>'
                '<device member="attribute" name="ttestp09/testts/t2r228"/>'
                '</datasource></definition>'),
            'scalar2_ulong64': (
                '<definition><datasource type="TANGO" name="scalar2_ulong64">'
                '<record name="ScalarULong64"/>'
                '<device member="attribute" name="ttestp09/testts/t2r228"/>'
                '</datasource></definition>'),
            'scalar2_float': (
                '<definition><datasource type="TANGO" name="scalar2_float">'
                '<record name="ScalarFloat"/>'
                '<device member="attribute" name="ttestp09/testts/t2r228"/>'
                '</datasource></definition>'),
            'scalar2_double': (
                '<definition><datasource type="TANGO" name="scalar2_double">'
                '<record name="ScalarDouble"/>'
                '<device member="attribute" name="ttestp09/testts/t2r228"/>'
                '</datasource></definition>'),
            'scalar2_string': (
                '<definition><datasource type="TANGO" name="scalar2_string">'
                '<record name="ScalarString"/>'
                '<device member="attribute" name="ttestp09/testts/t2r228"/>'
                '</datasource></definition>'),
            'scalar2_Encoded': (
                '<definition><datasource type="TANGO" name="scalar2_encoded">'
                '<record name="ScalarEncoded"/>'
                '<device member="attribute" name="ttestp09/testts/t2r228"/>'
                '</datasource></definition>'),
            'scalar2_uchar': (
                '<definition><datasource type="TANGO" name="scalar2_uchar">'
                '<record name="ScalarUChar"/>'
                '<device member="attribute" name="ttestp09/testts/t2r228"/>'
                '</datasource></definition>'),
            'spectrum2_long': (
                '<definition><datasource type="TANGO" name="spectrum2_long">'
                '<record name="SpectrumLong"/>'
                '<device member="attribute" name="ttestp09/testts/t2r228"/>'
                '</datasource></definition>'),
            'spectrum2_bool': (
                '<definition><datasource type="TANGO" name="spectrum2_bool">'
                '<record name="SpectrumBoolean"/>'
                '<device member="attribute" name="ttestp09/testts/t2r228"/>'
                '</datasource></definition>'),
            'spectrum2_short': (
                '<definition><datasource type="TANGO" name="spectrum2_short">'
                '<record name="SpectrumShort"/>'
                '<device member="attribute" name="ttestp09/testts/t2r228"/>'
                '</datasource></definition>'),
            'spectrum2_ushort': (
                '<definition><datasource type="TANGO" name="spectrum2_ushort">'
                '<record name="SpectrumUShort"/>'
                '<device member="attribute" name="ttestp09/testts/t2r228"/>'
                '</datasource></definition>'),
            'spectrum2_ulong': (
                '<definition><datasource type="TANGO" name="spectrum2_ulong">'
                '<record name="SpectrumULong"/>'
                '<device member="attribute" name="ttestp09/testts/t2r228"/>'
                '</datasource></definition>'),
            'spectrum2_long64': (
                '<definition><datasource type="TANGO" name="spectrum2_long64">'
                '<record name="SpectrumLong64"/>'
                '<device member="attribute" name="ttestp09/testts/t2r228"/>'
                '</datasource></definition>'),
            'spectrum2_ulong64': (
                '<definition>'
                '<datasource type="TANGO" name="spectrum2_ulong64">'
                '<record name="SpectrumULong64"/>'
                '<device member="attribute" name="ttestp09/testts/t2r228"/>'
                '</datasource></definition>'),
            'spectrum2_float': (
                '<definition><datasource type="TANGO" name="spectrum2_float">'
                '<record name="SpectrumFloat"/>'
                '<device member="attribute" name="ttestp09/testts/t2r228"/>'
                '</datasource></definition>'),
            'spectrum2_double': (
                '<definition><datasource type="TANGO" name="spectrum2_double">'
                '<record name="SpectrumDouble"/>'
                '<device member="attribute" name="ttestp09/testts/t2r228"/>'
                '</datasource></definition>'),
            'spectrum2_string': (
                '<definition><datasource type="TANGO" name="spectrum2_string">'
                '<record name="SpectrumString"/>'
                '<device member="attribute" name="ttestp09/testts/t2r228"/>'
                '</datasource></definition>'),
            'spectrum2_Encoded': (
                '<definition>'
                '<datasource type="TANGO" name="spectrum2_encoded">'
                '<record name="SpectrumEncoded"/>'
                '<device member="attribute" name="ttestp09/testts/t2r228"/>'
                '</datasource></definition>'),
            'spectrum2_uchar': (
                '<definition><datasource type="TANGO" name="spectrum2_uchar">'
                '<record name="SpectrumUChar"/>'
                '<device member="attribute" name="ttestp09/testts/t2r228"/>'
                '</datasource></definition>'),
            'image2_long': (
                '<definition><datasource type="TANGO" name="image2_long">'
                '<record name="ImageLong"/>'
                '<device member="attribute" name="ttestp09/testts/t2r228"/>'
                '</datasource></definition>'),
            'image2_bool': (
                '<definition><datasource type="TANGO" name="image2_bool">'
                '<record name="ImageBoolean"/>'
                '<device member="attribute" name="ttestp09/testts/t2r228"/>'
                '</datasource></definition>'),
            'image2_short': (
                '<definition><datasource type="TANGO" name="image2_short">'
                '<record name="ImageShort"/>'
                '<device member="attribute" name="ttestp09/testts/t2r228"/>'
                '</datasource></definition>'),
            'image2_ushort': (
                '<definition><datasource type="TANGO" name="image2_ushort">'
                '<record name="ImageUShort"/>'
                '<device member="attribute" name="ttestp09/testts/t2r228"/>'
                '</datasource></definition>'),
            'image2_ulong': (
                '<definition><datasource type="TANGO" name="image2_ulong">'
                '<record name="ImageULong"/>'
                '<device member="attribute" name="ttestp09/testts/t2r228"/>'
                '</datasource></definition>'),
            'image2_long64': (
                '<definition><datasource type="TANGO" name="image2_long64">'
                '<record name="ImageLong64"/>'
                '<device member="attribute" name="ttestp09/testts/t2r228"/>'
                '</datasource></definition>'),
            'image2_ulong64': (
                '<definition><datasource type="TANGO" name="image2_ulong64">'
                '<record name="ImageULong64"/>'
                '<device member="attribute" name="ttestp09/testts/t2r228"/>'
                '</datasource></definition>'),
            'image2_float': (
                '<definition><datasource type="TANGO" name="image2_float">'
                '<record name="ImageFloat"/>'
                '<device member="attribute" name="ttestp09/testts/t2r228"/>'
                '</datasource></definition>'),
            'image2_double': (
                '<definition><datasource type="TANGO" name="image2_double">'
                '<record name="ImageDouble"/>'
                '<device member="attribute" name="ttestp09/testts/t2r228"/>'
                '</datasource></definition>'),
            'image2_string': (
                '<definition><datasource type="TANGO" name="image2_string">'
                '<record name="ImageString"/>'
                '<device member="attribute" name="ttestp09/testts/t2r228"/>'
                '</datasource></definition>'),
            'image2_Encoded': (
                '<definition><datasource type="TANGO" name="image2_encoded">'
                '<record name="ImageEncoded"/>'
                '<device member="attribute" name="ttestp09/testts/t2r228"/>'
                '</datasource></definition>'),
            'image2_uchar': (
                '<definition><datasource type="TANGO" name="image2_uchar">'
                '<record name="ImageUChar"/>'
                '<device member="attribute" name="ttestp09/testts/t2r228"/>'
                '</datasource></definition>'),
            'client2_long': (
                '<definition><datasource type="CLIENT" name="client2_long">'
                '<record name="Client2Long"/>'
                '</datasource></definition>'),
            'client2_short': (
                '<definition><datasource type="CLIENT" name="client2_short">'
                '<record name="Client2Short"/>'
                '</datasource></definition>'),
            'string2_list': (
                '<definition><datasource type="TANGO" name="string2_list">'
                '<record name="StringList"/>'
                '<device member="property" name="ttestp09/testts/t2r228"/>'
                '</datasource></definition>'),
            'get2_float': (
                '<definition><datasource type="TANGO" name="get2_float">'
                '<record name="GetFloat"/>'
                '<device member="command" name="ttestp09/testts/t2r228"/>'
                '</datasource></definition>'),
        }

        self.mydss = {
            'nn': ('<?xml version=\'1.0\'?>'
                   '<definition><datasource type="TANGO">'
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

    # test starter
    # \brief Common set up
    def setUp(self):
        print("SEED = %s" % self.__seed)
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

    def myAssertDict(self, dct, dct2, excluded=None):
        exc = set(excluded or [])
        logger.debug('dict %s' % type(dct))
        logger.debug("\n%s\n%s" % (dct, dct2))
        self.assertTrue(isinstance(dct, dict))
        self.assertTrue(isinstance(dct2, dict))
        logger.debug("%s %s" % (len(list(dct.keys())), len(list(dct2.keys()))))
        self.assertEqual(len(list(dct.keys())), len(list(dct2.keys())))
        for k, v in dct.items():
            logger.debug("%s  in %s" % (str(k), str(dct2.keys())))
            self.assertTrue(k in dct2.keys())
            if k not in exc:
                if isinstance(v, dict):
                    self.myAssertDict(v, dct2[k])
                else:
                    logger.debug("%s , %s" % (str(v), str(dct2[k])))
                    self.assertEqual(v, dct2[k])

    # constructor test
    # \brief It tests default settings
    def test_constructor(self):
        fun = sys._getframe().f_code.co_name
        print("Run: %s.%s() " % (self.__class__.__name__, fun))
        # msp =
        MacroServerPools(0)
        # msp =
        MacroServerPools(10)

    # constructor test
    # \brief It tests default settings
    def test_getMacroServer(self):
        fun = sys._getframe().f_code.co_name
        print("Run: %s.%s() " % (self.__class__.__name__, fun))
        msp = MacroServerPools(0)
        msp = MacroServerPools(10)
        self.myAssertRaise(Exception, msp.updateMacroServer,
                           "sfdsTESTdfdf/sdfsdf/sdffsf")
        self.myAssertRaise(Exception, msp.updateMacroServer, "")
        self.myAssertRaise(Exception, msp.getMacroServer, "")
        self.myAssertRaise(Exception, msp.getPools, "")

        msp.updateMacroServer(list(self._ms.door.keys())[0])
        self.assertEqual(msp.getMacroServer(""), list(self._ms.ms.keys())[0])
        self.assertEqual(msp.getMacroServer(list(self._ms.door.keys())[0]),
                         list(self._ms.ms.keys())[0])
        self.assertEqual(msp.getPools(list(self._ms.door.keys())[0]), [])
        self.myAssertRaise(Exception, msp.getPools, "")

        self.myAssertRaise(Exception, msp.updateMacroServer,
                           "sfdsTESTdfdf/sdfsdf/sdffsf")
        self.myAssertRaise(Exception, msp.updateMacroServer, "")
        self.myAssertRaise(Exception, msp.getMacroServer, "")
        self.myAssertRaise(Exception, msp.getPools, "")

        self.assertEqual(msp.getPools(list(self._ms.door.keys())[0]), [])

        self._ms.dps[list(self._ms.ms.keys())[0]].DoorList = []
        self.myAssertRaise(Exception, msp.updateMacroServer,
                           list(self._ms.door.keys())[0])
        self.myAssertRaise(Exception, msp.getMacroServer, "")
        self.myAssertRaise(Exception,
                           msp.getPools, list(self._ms.door.keys())[0])

    # constructor test
    # \brief It tests default settings
    def test_getPool(self):
        fun = sys._getframe().f_code.co_name
        print("Run: %s.%s() " % (self.__class__.__name__, fun))
        msp = MacroServerPools(10)
        db = PyTango.Database()
        db.put_device_property(list(self._ms.ms.keys())[0],
                               {'PoolNames': self._pool.dp.name()})
        self._ms.dps[list(self._ms.ms.keys())[0]].Init()

        self.myAssertRaise(Exception, msp.updateMacroServer,
                           "sfdsTESTdfdf/sdfsdf/sdffsf")
        self.myAssertRaise(Exception, msp.updateMacroServer, "")
        self.myAssertRaise(Exception, msp.getMacroServer, "")
        self.myAssertRaise(Exception, msp.getPools, "")

        msp.updateMacroServer(list(self._ms.door.keys())[0])
        self.assertEqual(msp.getMacroServer(""), list(self._ms.ms.keys())[0])
        self.assertEqual(msp.getMacroServer(list(self._ms.door.keys())[0]),
                         list(self._ms.ms.keys())[0])
        pools = msp.getPools(list(self._ms.door.keys())[0])
        self.assertEqual(len(pools), 1)
        self.assertTrue(isinstance(pools[0], PyTango.DeviceProxy))
        self.assertEqual(pools[0].name(), self._pool.dp.name())

        pools = msp.getPools("sdfs")
        self.assertEqual(len(pools), 1)
        self.assertTrue(isinstance(pools[0], PyTango.DeviceProxy))
        self.assertEqual(pools[0].name(), self._pool.dp.name())

        self.myAssertRaise(Exception, msp.updateMacroServer,
                           "sfdsTESTdfdf/sdfsdf/sdffsf")
        self.myAssertRaise(Exception, msp.updateMacroServer, "")
        self.myAssertRaise(Exception, msp.getMacroServer, "")

        pools = msp.getPools(list(self._ms.door.keys())[0])
        self.assertEqual(len(pools), 1)
        self.assertTrue(isinstance(pools[0], PyTango.DeviceProxy))
        self.assertEqual(pools[0].name(), self._pool.dp.name())

        pools = msp.getPools("sdfs")
        self.assertEqual(len(pools), 1)
        self.assertTrue(isinstance(pools[0], PyTango.DeviceProxy))
        self.assertEqual(pools[0].name(), self._pool.dp.name())

        self._ms.dps[list(self._ms.ms.keys())[0]].DoorList = []
        self.myAssertRaise(Exception, msp.updateMacroServer,
                           list(self._ms.door.keys())[0])
        self.myAssertRaise(Exception, msp.getMacroServer, "")
        self.myAssertRaise(Exception, msp.getPools, "")

        self.myAssertRaise(Exception,
                           msp.getPools, list(self._ms.door.keys())[0])

    # constructor test
    # \brief It tests default settings
    def test_getPool_1to3(self):
        fun = sys._getframe().f_code.co_name
        print("Run: %s.%s() " % (self.__class__.__name__, fun))
        doors = ["door2testp09/testts/t1r228",
                 "door2testp09/testts/t2r228",
                 "door2testp09/testts/t3r228"]
        msname = "ms2testp09/testts/t1r228"
        try:

            ms2 = TestMacroServerSetUp.TestMacroServerSetUp(
                "MSTESTS1TO3", [msname], doors)
            ms2.setUp()

            msp = MacroServerPools(10)
            db = PyTango.Database()
            db.put_device_property(list(ms2.ms.keys())[0],
                                   {'PoolNames': self._pool.dp.name()})
            ms2.dps[list(ms2.ms.keys())[0]].Init()

            for i in range(3):
                ms2.dps[list(ms2.ms.keys())[0]].DoorList = doors
                # print "doors", doors[i]
                self.myAssertRaise(Exception, msp.updateMacroServer,
                                   "sfdsTESTdfdf/sdfsdf/sdffsf")
                self.myAssertRaise(Exception, msp.updateMacroServer, "")
                self.myAssertRaise(Exception, msp.getMacroServer, "")
                self.myAssertRaise(Exception, msp.getPools, "")
                # print doors[i]
                msp.updateMacroServer(doors[i])
                self.assertEqual(
                    msp.getMacroServer(""), list(ms2.ms.keys())[0])
                self.assertEqual(msp.getMacroServer(doors[i]),
                                 list(ms2.ms.keys())[0])
                pools = msp.getPools(doors[i])
                self.assertEqual(len(pools), 1)
                self.assertTrue(isinstance(pools[0], PyTango.DeviceProxy))
                self.assertEqual(pools[0].name(), self._pool.dp.name())

                pools = msp.getPools("sdfs")
                self.assertEqual(len(pools), 1)
                self.assertTrue(isinstance(pools[0], PyTango.DeviceProxy))
                self.assertEqual(pools[0].name(), self._pool.dp.name())

                self.myAssertRaise(Exception, msp.updateMacroServer,
                                   "sfdsTESTdfdf/sdfsdf/sdffsf")
                self.myAssertRaise(Exception, msp.updateMacroServer, "")
                self.myAssertRaise(Exception, msp.getMacroServer, "")

                pools = msp.getPools(doors[i])
                self.assertEqual(len(pools), 1)
                self.assertTrue(isinstance(pools[0], PyTango.DeviceProxy))
                self.assertEqual(pools[0].name(), self._pool.dp.name())

                pools = msp.getPools("sdfs")
                self.assertEqual(len(pools), 1)
                self.assertTrue(isinstance(pools[0], PyTango.DeviceProxy))
                self.assertEqual(pools[0].name(), self._pool.dp.name())

                ms2.dps[list(ms2.ms.keys())[0]].DoorList = []
                self.myAssertRaise(Exception, msp.updateMacroServer, doors[i])
                self.myAssertRaise(Exception, msp.getMacroServer, "")
                self.myAssertRaise(Exception, msp.getPools, "")

                self.myAssertRaise(Exception, msp.getPools, doors[i])
        finally:
            ms2.tearDown()

    # constructor test
    # \brief It tests default settings
    def test_getPool_3to3(self):
        fun = sys._getframe().f_code.co_name
        print("Run: %s.%s() " % (self.__class__.__name__, fun))
        doors = ["door3testp09/testts/t1r228",
                 "door3testp09/testts/t2r228",
                 "door3testp09/testts/t3r228"]
        mss = ["ms3testp09/testts/t1r228",
               "ms3testp09/testts/t2r228",
               "ms3testp09/testts/t3r228"]
        try:

            ms3 = TestMacroServerSetUp.TestMacroServerSetUp(
                "MSTESTS3TO3", mss, doors)
            ms3.setUp()

            msp = MacroServerPools(10)
            db = PyTango.Database()
            for j, ms in enumerate(mss):
                db.put_device_property(ms, {'PoolNames': self._pool.dp.name()})
                ms3.dps[ms].Init()

            for i, ms in enumerate(mss):
                ms3.dps[ms].DoorList = [doors[i]]
                # print "ms", ms, "doors", doors[i]
                self.myAssertRaise(Exception, msp.updateMacroServer,
                                   "sfdsTESTdfdf/sdfsdf/sdffsf")
                self.myAssertRaise(Exception, msp.updateMacroServer, "")
                self.myAssertRaise(Exception, msp.getMacroServer, "")
                self.myAssertRaise(Exception, msp.getPools, "")
                # print doors[i]
                msp.updateMacroServer(doors[i])
                self.assertEqual(msp.getMacroServer(""), ms)
                self.assertEqual(msp.getMacroServer(doors[i]), ms)
                pools = msp.getPools(doors[i])
                self.assertEqual(len(pools), 1)
                self.assertTrue(isinstance(pools[0], PyTango.DeviceProxy))
                self.assertEqual(pools[0].name(), self._pool.dp.name())

                pools = msp.getPools("sdfs")
                self.assertEqual(len(pools), 1)
                self.assertTrue(isinstance(pools[0], PyTango.DeviceProxy))
                self.assertEqual(pools[0].name(), self._pool.dp.name())

                self.myAssertRaise(Exception, msp.updateMacroServer,
                                   "sfdsTESTdfdf/sdfsdf/sdffsf")
                self.myAssertRaise(Exception, msp.updateMacroServer, "")
                self.myAssertRaise(Exception, msp.getMacroServer, "")

                pools = msp.getPools(doors[i])
                self.assertEqual(len(pools), 1)
                self.assertTrue(isinstance(pools[0], PyTango.DeviceProxy))
                self.assertEqual(pools[0].name(), self._pool.dp.name())

                pools = msp.getPools("sdfs")
                self.assertEqual(len(pools), 1)
                self.assertTrue(isinstance(pools[0], PyTango.DeviceProxy))
                self.assertEqual(pools[0].name(), self._pool.dp.name())

                ms3.dps[ms].DoorList = []
                self.myAssertRaise(Exception, msp.updateMacroServer, doors[i])
                self.myAssertRaise(Exception, msp.getMacroServer, "")
                self.myAssertRaise(Exception, msp.getPools, "")

                self.myAssertRaise(Exception, msp.getPools, doors[i])
        finally:
            ms3.tearDown()

    # constructor test
    # \brief It tests default settings
    def test_checkChannels_simple(self):
        fun = sys._getframe().f_code.co_name
        print("Run: %s.%s() " % (self.__class__.__name__, fun))
        msp = MacroServerPools(0)
        msp = MacroServerPools(10)
        channelerrors = []
        poolchannels = []
        componentgroup = {}
        datasourcegroup = {}
        self.myAssertRaise(Exception, msp.checkChannels,
                           None, None, None, None, None)
        res, res2 = msp.checkChannels(list(self._ms.door.keys())[0],
                                      self._cf.dp,
                                      poolchannels,
                                      componentgroup,
                                      datasourcegroup,
                                      channelerrors)
        self.assertEqual(res, '{}')
        self.assertEqual(res2, '{}')
        # print self._cf.dp.GetCommandVariable("COMMANDS")
        self.assertEqual(
            json.loads(self._cf.dp.GetCommandVariable("COMMANDS")),
            ['AvailableComponents', 'AvailableDataSources',
             'AvailableComponents', 'AvailableDataSources'])
        self.assertEqual(json.loads(
            self._cf.dp.GetCommandVariable("VARS")), [None, None, None, None])

    # constructor test
    # \brief It tests default settings
    def test_checkChannels_withcf(self):
        fun = sys._getframe().f_code.co_name
        print("Run: %s.%s() " % (self.__class__.__name__, fun))
        msp = MacroServerPools(0)
        msp = MacroServerPools(10)
        channelerrors = []
        poolchannels = []
        componentgroup = {}
        datasourcegroup = {}

        self._cf.dp.SetCommandVariable(["CPDICT", json.dumps(self.mycps)])
        self._cf.dp.SetCommandVariable(["DSDICT", json.dumps(self.mydss)])

        res, res2 = msp.checkChannels(list(self._ms.door.keys())[0],
                                      self._cf.dp,
                                      poolchannels,
                                      componentgroup,
                                      datasourcegroup,
                                      channelerrors)
        self.assertEqual(res, '{}')
        self.assertEqual(res2, '{}')
        self.assertEqual(componentgroup, {})
        self.assertEqual(datasourcegroup, {})
        self.assertEqual(channelerrors, [])
        # print self._cf.dp.GetCommandVariable("COMMANDS")
        self.assertEqual(
            json.loads(self._cf.dp.GetCommandVariable("COMMANDS")),
            ["AvailableComponents", "AvailableDataSources",
             "AvailableComponents", "AvailableDataSources"])
        self.assertEqual(
            json.loads(self._cf.dp.GetCommandVariable("VARS")),
            [None, None, None, None])
#        print self._cf.dp.availableComponents()

    # constructor test
    # \brief It tests default settings
    def test_checkChannels_withcf_cps(self):
        fun = sys._getframe().f_code.co_name
        print("Run: %s.%s() " % (self.__class__.__name__, fun))
        msp = MacroServerPools(0)
        msp = MacroServerPools(10)
        channelerrors = []
        poolchannels = ["mycp"]
        componentgroup = {"mycp": None}
        datasourcegroup = {"ann2": None}

        self._cf.dp.SetCommandVariable(["CPDICT", json.dumps(self.mycps)])
        self._cf.dp.SetCommandVariable(["DSDICT", json.dumps(self.mydss)])

        res, res2 = msp.checkChannels(list(self._ms.door.keys())[0],
                                      self._cf.dp,
                                      poolchannels,
                                      componentgroup,
                                      datasourcegroup,
                                      channelerrors)
        self.myAssertDict(json.loads(res), {"mycp": True})
        self.assertEqual(componentgroup, {"mycp": True})
        self.myAssertDict(json.loads(res2), {"ann2": True})
        self.assertEqual(datasourcegroup, {"ann2": True})
        self.assertEqual(channelerrors, [])

        # print self._cf.dp.GetCommandVariable("COMMANDS")
        self.assertEqual(
            json.loads(self._cf.dp.GetCommandVariable("COMMANDS")),
            ["AvailableComponents", "AvailableDataSources",
             "AvailableComponents", "AvailableDataSources",
             "DependentComponents",
             "Components",
             "DataSources", "DataSources"])
        self.assertEqual(
            json.loads(self._cf.dp.GetCommandVariable("VARS")),
            [None, None, None, None, ['mycp'], ['mycp'], ['ann2'], ['ann2']])

    # constructor test
    # \brief It tests default settings
    def test_checkChannels_withcf_cps_t(self):
        fun = sys._getframe().f_code.co_name
        print("Run: %s.%s() " % (self.__class__.__name__, fun))
        msp = MacroServerPools(0)
        msp = MacroServerPools(10)
        channelerrors = []
        poolchannels = ["mycp"]
        componentgroup = {"mycp": True}
        datasourcegroup = {"ann2": True}

        self._cf.dp.SetCommandVariable(["CPDICT", json.dumps(self.mycps)])
        self._cf.dp.SetCommandVariable(["DSDICT", json.dumps(self.mydss)])

        res, res2 = msp.checkChannels(list(self._ms.door.keys())[0],
                                      self._cf.dp,
                                      poolchannels,
                                      componentgroup,
                                      datasourcegroup,
                                      channelerrors)
        self.myAssertDict(json.loads(res), {"mycp": True})
        self.assertEqual(componentgroup, {"mycp": True})
        self.myAssertDict(json.loads(res2), {"ann2": True})
        self.assertEqual(datasourcegroup, {"ann2": True})
        self.assertEqual(channelerrors, [])

        print(self._cf.dp.GetCommandVariable("COMMANDS"))
        self.assertEqual(
            json.loads(self._cf.dp.GetCommandVariable("COMMANDS")),
            ["AvailableComponents", "AvailableDataSources",
             "AvailableComponents", "AvailableDataSources",
             "DependentComponents",
             "Components",
             "DataSources", "DataSources"])
        self.assertEqual(
            json.loads(self._cf.dp.GetCommandVariable("VARS")),
            [None, None, None, None, ['mycp'], ['mycp'], ['ann2'], ['ann2']])

    # constructor test
    # \brief It tests default settings
    def test_checkChannels_withcf_cps_False(self):
        fun = sys._getframe().f_code.co_name
        print("Run: %s.%s() " % (self.__class__.__name__, fun))
        msp = MacroServerPools(0)
        msp = MacroServerPools(10)
        channelerrors = []
        poolchannels = ["mycp"]
        componentgroup = {"mycp": False}
        datasourcegroup = {"ann2": False}

        self._cf.dp.SetCommandVariable(["CPDICT", json.dumps(self.mycps)])
        self._cf.dp.SetCommandVariable(["DSDICT", json.dumps(self.mydss)])

        res, res2 = msp.checkChannels(list(self._ms.door.keys())[0],
                                      self._cf.dp,
                                      poolchannels,
                                      componentgroup,
                                      datasourcegroup,
                                      channelerrors)
        self.myAssertDict(json.loads(res), {"mycp": False})
        self.assertEqual(componentgroup, {"mycp": False})
        self.myAssertDict(json.loads(res2), {"ann2": False})
        self.assertEqual(datasourcegroup, {"ann2": False})
        self.assertEqual(channelerrors, [])

        print(self._cf.dp.GetCommandVariable("COMMANDS"))
        self.assertEqual(
            json.loads(self._cf.dp.GetCommandVariable("COMMANDS")),
            ["AvailableComponents", "AvailableDataSources",
             "AvailableComponents", "AvailableDataSources"])
        self.assertEqual(
            json.loads(self._cf.dp.GetCommandVariable("VARS")),
            [None, None, None, None])
#        print self._cf.dp.availableComponents()

    # constructor test
    # \brief It tests default settings
    def test_checkChannels_withcf_nocps(self):
        fun = sys._getframe().f_code.co_name
        print("Run: %s.%s() " % (self.__class__.__name__, fun))
        msp = MacroServerPools(0)
        msp = MacroServerPools(10)
        channelerrors = []
        poolchannels = ["mycp"]
        componentgroup = {}
        datasourcegroup = {}

        self._cf.dp.SetCommandVariable(["CPDICT", json.dumps(self.mycps)])
        self._cf.dp.SetCommandVariable(["DSDICT", json.dumps(self.mydss)])

        res, res2 = msp.checkChannels(list(self._ms.door.keys())[0],
                                      self._cf.dp,
                                      poolchannels,
                                      datasourcegroup,
                                      componentgroup,
                                      channelerrors)
        self.myAssertDict(json.loads(res), {})
        self.assertEqual(componentgroup, {})
        self.myAssertDict(json.loads(res2), {})
        self.assertEqual(datasourcegroup, {})
        self.assertEqual(channelerrors, [])

        print(self._cf.dp.GetCommandVariable("COMMANDS"))
        self.assertEqual(
            json.loads(self._cf.dp.GetCommandVariable("COMMANDS")),
            ["AvailableComponents", "AvailableDataSources",
             "AvailableComponents", "AvailableDataSources"])
        self.assertEqual(
            json.loads(self._cf.dp.GetCommandVariable("VARS")),
            [None, None, None, None])

#        print self._cf.dp.availableComponents()
    # constructor test
    # \brief It tests default settings
    def test_checkChannels_withcf_nochnnel(self):
        fun = sys._getframe().f_code.co_name
        print("Run: %s.%s() " % (self.__class__.__name__, fun))
        msp = MacroServerPools(0)
        msp = MacroServerPools(10)
        channelerrors = []
        poolchannels = []
        componentgroup = {"mycp": None}
        datasourcegroup = {"ann2": None}

        self._cf.dp.SetCommandVariable(["CPDICT", json.dumps(self.mycps)])
        self._cf.dp.SetCommandVariable(["DSDICT", json.dumps(self.mydss)])

        res, res2 = msp.checkChannels(list(self._ms.door.keys())[0],
                                      self._cf.dp,
                                      poolchannels,
                                      componentgroup,
                                      datasourcegroup,
                                      channelerrors)
        self.myAssertDict(json.loads(res), {"mycp": True})
        self.assertEqual(componentgroup, {"mycp": True})
        self.myAssertDict(json.loads(res2), {"ann2": True})
        self.assertEqual(datasourcegroup, {"ann2": True})
        self.assertEqual(channelerrors, [])

        print(self._cf.dp.GetCommandVariable("COMMANDS"))
        self.assertEqual(
            json.loads(self._cf.dp.GetCommandVariable("COMMANDS")),
            ["AvailableComponents", "AvailableDataSources",
             "AvailableComponents", "AvailableDataSources",
             "DependentComponents",
             "Components",
             "DataSources", "DataSources"])
        self.assertEqual(json.loads(self._cf.dp.GetCommandVariable("VARS")),
                         [None, None, None, None,
                          ['mycp'], ['mycp'], ['ann2'], ['ann2']])

    # constructor test
    # \brief It tests default settings
    def test_checkChannels_withcf_nochnnel_t(self):
        fun = sys._getframe().f_code.co_name
        print("Run: %s.%s() " % (self.__class__.__name__, fun))
        msp = MacroServerPools(0)
        msp = MacroServerPools(10)
        channelerrors = []
        poolchannels = []
        componentgroup = {"mycp": True}
        datasourcegroup = {"ann2": True}

        self._cf.dp.SetCommandVariable(["CPDICT", json.dumps(self.mycps)])
        self._cf.dp.SetCommandVariable(["DSDICT", json.dumps(self.mydss)])

        res, res2 = msp.checkChannels(list(self._ms.door.keys())[0],
                                      self._cf.dp,
                                      poolchannels,
                                      componentgroup,
                                      datasourcegroup,
                                      channelerrors)
        self.myAssertDict(json.loads(res), {"mycp": True})
        self.assertEqual(componentgroup, {"mycp": True})
        self.myAssertDict(json.loads(res2), {"ann2": True})
        self.assertEqual(datasourcegroup, {"ann2": True})
        self.assertEqual(channelerrors, [])

        print(self._cf.dp.GetCommandVariable("COMMANDS"))
        self.assertEqual(
            json.loads(self._cf.dp.GetCommandVariable("COMMANDS")),
            ["AvailableComponents", "AvailableDataSources",
             "AvailableComponents", "AvailableDataSources",
             "DependentComponents",
             "Components",
             "DataSources", "DataSources"])
        self.assertEqual(json.loads(self._cf.dp.GetCommandVariable("VARS")),
                         [None, None, None, None,
                          ['mycp'], ['mycp'], ['ann2'], ['ann2']])

    # constructor test
    # \brief It tests default settings
    def test_checkChannels_withcf_nochnnel_False(self):
        fun = sys._getframe().f_code.co_name
        print("Run: %s.%s() " % (self.__class__.__name__, fun))
        msp = MacroServerPools(0)
        msp = MacroServerPools(10)
        channelerrors = []
        poolchannels = []
        componentgroup = {"mycp": False}
        datasourcegroup = {"ann2": False}

        self._cf.dp.SetCommandVariable(["CPDICT", json.dumps(self.mycps)])
        self._cf.dp.SetCommandVariable(["DSDICT", json.dumps(self.mydss)])

        res, res2 = msp.checkChannels(list(self._ms.door.keys())[0],
                                      self._cf.dp,
                                      poolchannels,
                                      componentgroup,
                                      datasourcegroup,
                                      channelerrors)
        self.myAssertDict(json.loads(res), {"mycp": False})
        self.assertEqual(componentgroup, {"mycp": False})
        self.myAssertDict(json.loads(res2), {"ann2": False})
        self.assertEqual(datasourcegroup, {"ann2": False})
        self.assertEqual(channelerrors, [])

        print(self._cf.dp.GetCommandVariable("COMMANDS"))
        self.assertEqual(
            json.loads(self._cf.dp.GetCommandVariable("COMMANDS")),
            ["AvailableComponents", "AvailableDataSources",
             "AvailableComponents",  "AvailableDataSources"])
        self.assertEqual(json.loads(self._cf.dp.GetCommandVariable("VARS")),
                         [None, None, None, None])

    # constructor test
    # \brief It tests default settings
    def test_checkChannels_wds(self):
        fun = sys._getframe().f_code.co_name
        print("Run: %s.%s() " % (self.__class__.__name__, fun))
        msp = MacroServerPools(0)
        msp = MacroServerPools(10)
        channelerrors = []
        poolchannels = []
        componentgroup = {"smycp": None}
        datasourcegroup = {"scalar_uchar": None}

        self._cf.dp.SetCommandVariable(["CPDICT", json.dumps(self.smycps)])
        self._cf.dp.SetCommandVariable(["DSDICT", json.dumps(self.smydss)])

        res, res2 = msp.checkChannels(list(self._ms.door.keys())[0],
                                      self._cf.dp,
                                      poolchannels,
                                      componentgroup,
                                      datasourcegroup,
                                      channelerrors)

        # print res
        self.myAssertDict(json.loads(res), {"smycp": True})
        self.assertEqual(componentgroup, {"smycp": True})
        self.myAssertDict(json.loads(res2), {"scalar_uchar": True})
        self.assertEqual(datasourcegroup, {"scalar_uchar": True})
        self.assertEqual(channelerrors, [])

        # print self._cf.dp.GetCommandVariable("COMMANDS")
        self.assertEqual(
            json.loads(self._cf.dp.GetCommandVariable("COMMANDS")),
            ["AvailableComponents", "AvailableDataSources",
             "AvailableComponents", "AvailableDataSources",
             "DependentComponents",
             "Components", "DataSources", "DataSources",
             "DataSources",
             "DataSources",
             "DataSources"])

    # constructor test
    # \brief It tests default settings
    def test_checkChannels_wds_cp_true(self):
        fun = sys._getframe().f_code.co_name
        print("Run: %s.%s() " % (self.__class__.__name__, fun))
        msp = MacroServerPools(0)
        msp = MacroServerPools(10)
        channelerrors = []
        poolchannels = []
        componentgroup = {"smycppc1": True}
        datasourcegroup = {"string_list": True, "get_float": True}

        self._cf.dp.SetCommandVariable(["CPDICT", json.dumps(self.smycps)])
        self._cf.dp.SetCommandVariable(["DSDICT", json.dumps(self.smydss)])

        res, res2 = msp.checkChannels(list(self._ms.door.keys())[0],
                                      self._cf.dp,
                                      poolchannels,
                                      componentgroup,
                                      datasourcegroup,
                                      channelerrors)

        # print res
        self.myAssertDict(json.loads(res), {"smycppc1": True})
        self.assertEqual(componentgroup, {"smycppc1": True})
        self.myAssertDict(
            json.loads(res2), {"string_list": True, "get_float": True})
        self.assertEqual(
            datasourcegroup, {"string_list": True, "get_float": True})
        self.assertEqual(channelerrors, [])

    # constructor test
    # \brief It tests default settings
    def test_checkChannels_wds_cp(self):
        fun = sys._getframe().f_code.co_name
        print("Run: %s.%s() " % (self.__class__.__name__, fun))
        msp = MacroServerPools(0)
        msp = MacroServerPools(10)
        channelerrors = []
        poolchannels = []
        componentgroup = {"smycppc1": None}
        datasourcegroup = {"string_list": None, "get_float": None}

        self._cf.dp.SetCommandVariable(["CPDICT", json.dumps(self.smycps)])
        self._cf.dp.SetCommandVariable(["DSDICT", json.dumps(self.smydss)])

        res, res2 = msp.checkChannels(list(self._ms.door.keys())[0],
                                      self._cf.dp,
                                      poolchannels,
                                      componentgroup,
                                      datasourcegroup,
                                      channelerrors)

        # print res
        self.myAssertDict(json.loads(res), {"smycppc1": True})
        self.assertEqual(componentgroup, {"smycppc1": True})
        self.myAssertDict(
            json.loads(res2), {"string_list": True, "get_float": True})
        self.assertEqual(
            datasourcegroup, {"string_list": True, "get_float": True})
        self.assertEqual(channelerrors, [])

    def test_checkChannels_wds_cp_false(self):
        fun = sys._getframe().f_code.co_name
        print("Run: %s.%s() " % (self.__class__.__name__, fun))
        msp = MacroServerPools(0)
        msp = MacroServerPools(10)
        channelerrors = []
        poolchannels = []
        componentgroup = {"smycppc1": False}
        datasourcegroup = {"string_list": False, "get_float": False}

        self._cf.dp.SetCommandVariable(["CPDICT", json.dumps(self.smycps)])
        self._cf.dp.SetCommandVariable(["DSDICT", json.dumps(self.smydss)])

        res, res2 = msp.checkChannels(list(self._ms.door.keys())[0],
                                      self._cf.dp,
                                      poolchannels,
                                      componentgroup,
                                      datasourcegroup,
                                      channelerrors)

        # print res
        self.myAssertDict(json.loads(res), {"smycppc1": False})
        self.assertEqual(componentgroup, {"smycppc1": False})
        self.myAssertDict(
            json.loads(res2), {"string_list": False, "get_float": False})
        self.assertEqual(
            datasourcegroup, {"string_list": False, "get_float": False})
        self.assertEqual(channelerrors, [])

    # constructor test
    # \brief It tests default settings
    def test_checkChannels_wds_cp2(self):
        fun = sys._getframe().f_code.co_name
        print("Run: %s.%s() " % (self.__class__.__name__, fun))
        simps2 = TestServerSetUp.TestServerSetUp(
            "ttestp09/testts/t2r228", "S2")
        try:
            simps2.add()
            msp = MacroServerPools(1)
            channelerrors = []
            poolchannels = []
            componentgroup = {"s2mycppc1": None}
            datasourcegroup = {"string2_list": None, "get2_float": None}

            self._cf.dp.SetCommandVariable(
                ["CPDICT", json.dumps(self.smycps2)])
            self._cf.dp.SetCommandVariable(
                ["DSDICT", json.dumps(self.smydss2)])

            res, res2 = msp.checkChannels(list(self._ms.door.keys())[0],
                                          self._cf.dp,
                                          poolchannels,
                                          componentgroup,
                                          datasourcegroup,
                                          channelerrors)

            # print res
            self.myAssertDict(json.loads(res), {"s2mycppc1": None})
            self.assertEqual(componentgroup, {"s2mycppc1": None})
            self.myAssertDict(
                json.loads(res2), {"string2_list": None, "get2_float": None})
            self.assertEqual(
                datasourcegroup, {"string2_list": None, "get2_float": None})
            self.assertEqual(len(channelerrors), 3)
        finally:
            simps2.delete()

    # constructor test
    # \brief It tests default settings
    def test_checkChannels_wds_t(self):
        fun = sys._getframe().f_code.co_name
        print("Run: %s.%s() " % (self.__class__.__name__, fun))
        msp = MacroServerPools(0)
        msp = MacroServerPools(10)
        channelerrors = []
        poolchannels = []
        componentgroup = {"smycp": True}
        datasourcegroup = {"scalar_uchar": True}

        self._cf.dp.SetCommandVariable(["CPDICT", json.dumps(self.smycps)])
        self._cf.dp.SetCommandVariable(["DSDICT", json.dumps(self.smydss)])

        res, res2 = msp.checkChannels(list(self._ms.door.keys())[0],
                                      self._cf.dp,
                                      poolchannels,
                                      componentgroup,
                                      datasourcegroup,
                                      channelerrors)

        # print res
        self.myAssertDict(json.loads(res), {"smycp": True})
        self.assertEqual(componentgroup, {"smycp": True})
        self.myAssertDict(json.loads(res2), {"scalar_uchar": True})
        self.assertEqual(datasourcegroup, {"scalar_uchar": True})
        self.assertEqual(channelerrors, [])

        print(self._cf.dp.GetCommandVariable("COMMANDS"))
        self.assertEqual(
            json.loads(self._cf.dp.GetCommandVariable("COMMANDS")),
            ["AvailableComponents", "AvailableDataSources",
             "AvailableComponents", "AvailableDataSources",
             "DependentComponents",
             "Components", "DataSources", "DataSources",
             "DataSources",
             "DataSources",
             "DataSources"])

    # constructor test
    # \brief It tests default settings
    def test_checkChannels_wds_false(self):
        fun = sys._getframe().f_code.co_name
        print("Run: %s.%s() " % (self.__class__.__name__, fun))
        msp = MacroServerPools(0)
        msp = MacroServerPools(10)
        channelerrors = []
        poolchannels = []
        componentgroup = {"smycp": False}
        datasourcegroup = {"scalar_uchar": False}

        self._cf.dp.SetCommandVariable(["CPDICT", json.dumps(self.smycps)])
        self._cf.dp.SetCommandVariable(["DSDICT", json.dumps(self.smydss)])

        res, res2 = msp.checkChannels(list(self._ms.door.keys())[0],
                                      self._cf.dp,
                                      poolchannels,
                                      componentgroup,
                                      datasourcegroup,
                                      channelerrors)

        # print res
        self.myAssertDict(json.loads(res), {"smycp": False})
        self.assertEqual(componentgroup, {"smycp": False})
        self.myAssertDict(json.loads(res2), {"scalar_uchar": False})
        self.assertEqual(datasourcegroup, {"scalar_uchar": False})
        self.assertEqual(channelerrors, [])

        # print self._cf.dp.GetCommandVariable("COMMANDS")
        self.assertEqual(
            json.loads(self._cf.dp.GetCommandVariable("COMMANDS")),
            ["AvailableComponents", "AvailableDataSources",
             "AvailableComponents", "AvailableDataSources"]
        )

    # constructor test
    # \brief It tests default settings
    def test_checkChannels_wds2(self):
        fun = sys._getframe().f_code.co_name
        print("Run: %s.%s() " % (self.__class__.__name__, fun))
        msp = MacroServerPools(0)
        msp = MacroServerPools(10)
        channelerrors = []
        poolchannels = []
        componentgroup = {"smycp": False, "smycp2": True, "smycp3": None}
        datasourcegroup = {"scalar_uchar": False, "scalar_string": True,
                           "scalar_ulong": None}

        self._cf.dp.SetCommandVariable(["CPDICT", json.dumps(self.smycps)])
        self._cf.dp.SetCommandVariable(["DSDICT", json.dumps(self.smydss)])

        res, res2 = msp.checkChannels(list(self._ms.door.keys())[0],
                                      self._cf.dp,
                                      poolchannels,
                                      componentgroup,
                                      datasourcegroup,
                                      channelerrors)

        self.myAssertDict(json.loads(res), {
            "smycp": False, "smycp2": True, "smycp3": True})
        self.assertEqual(componentgroup, {
            "smycp": False, "smycp2": True, "smycp3": True})
        self.myAssertDict(json.loads(res2),
                          {"scalar_uchar": False,
                           "scalar_string": True,
                           "scalar_ulong": True})
        self.assertEqual(datasourcegroup, json.loads(res2))
        self.assertEqual(channelerrors, [])

        # print(self._cf.dp.GetCommandVariable("COMMANDS"))
        self.assertEqual(
            json.loads(self._cf.dp.GetCommandVariable("COMMANDS")),
            ["AvailableComponents", "AvailableDataSources",
             "AvailableComponents", "AvailableDataSources",
             "DependentComponents", "Components",
             "DataSources", "DataSources", "DataSources",
             "DependentComponents", "Components",
             "DataSources", "DataSources", "DataSources",
             "DataSources", "DataSources", "DataSources", "DataSources"])
        res = json.loads(self._cf.dp.GetCommandVariable("VARS"))

    # constructor test
    # \brief It tests default settings
    def test_checkChannels_2wds(self):
        fun = sys._getframe().f_code.co_name
        print("Run: %s.%s() " % (self.__class__.__name__, fun))
        simps2 = TestServerSetUp.TestServerSetUp(
            "ttestp09/testts/t2r228", "S2")
        try:
            simps2.setUp()
            msp = MacroServerPools(1)
            channelerrors = []
            poolchannels = []
            componentgroup = {"smycp": None, "smycp2": None, "smycp3": None,
                              "s2mycp": None, "s2mycp2": None,
                              "s2mycp3": None}
            datasourcegroup = {
                "scalar_uchar": None, "scalar_string": None,
                "scalar_ulong": None,
                "scalar2_uchar": None, "scalar2_string": None,
                "scalar2_ulong": None
            }

            cps = dict(self.smycps)
            cps.update(self.smycps2)
            dss = dict(self.smydss)
            dss.update(self.smydss2)

            self._cf.dp.SetCommandVariable(["CPDICT", json.dumps(cps)])
            self._cf.dp.SetCommandVariable(["DSDICT", json.dumps(dss)])
    #        print "MDSS", self._cf.dp.availableDataSources()
    #        print "XDSS", self._cf.dp.dataSources(["scalar_long"])
            res, res2 = msp.checkChannels(list(self._ms.door.keys())[0],
                                          self._cf.dp,
                                          poolchannels,
                                          componentgroup,
                                          datasourcegroup,
                                          channelerrors)
    #        print res
    #        print channelerrors

            self.myAssertDict(json.loads(res), {
                "smycp": True, "smycp2": True, "smycp3": True,
                "s2mycp": True, "s2mycp2": True, "s2mycp3": True})
            self.myAssertDict(datasourcegroup, json.loads(res2))
            self.myAssertDict(json.loads(res2), {
                "scalar_uchar": True, "scalar_string": True,
                "scalar_ulong": True,
                "scalar2_uchar": True, "scalar2_string": True,
                "scalar2_ulong": True
            }
            )
            self.myAssertDict(componentgroup, json.loads(res))
            self.assertEqual(len(channelerrors), 0)

            # print self._cf.dp.GetCommandVariable("COMMANDS")
            self.assertEqual(
                json.loads(self._cf.dp.GetCommandVariable("COMMANDS")), [
                    "AvailableComponents", "AvailableDataSources",
                    "AvailableComponents", "AvailableDataSources",
                    "DependentComponents",
                    "Components", "DataSources", "DataSources", "DataSources",
                    "DependentComponents",
                    "Components", "DataSources", "DataSources", "DataSources",
                    "DependentComponents",
                    "Components", "DataSources", "DataSources", "DataSources",
                    "DependentComponents",
                    "Components", "DataSources", "DataSources", "DataSources",
                    "DependentComponents",
                    "Components", "DataSources", "DataSources", "DataSources",
                    "DependentComponents",
                    "Components", "DataSources", "DataSources", "DataSources",
                    "DataSources", "DataSources",
                    "DataSources", "DataSources",
                    "DataSources", "DataSources",
                    "DataSources", "DataSources",
                    "DataSources", "DataSources",
                    "DataSources", "DataSources",
                ])
        finally:
            simps2.tearDown()

    # constructor test
    # \brief It tests default settings
    def test_checkChannels_2wds_false(self):
        fun = sys._getframe().f_code.co_name
        print("Run: %s.%s() " % (self.__class__.__name__, fun))
        simps2 = TestServerSetUp.TestServerSetUp(
            "ttestp09/testts/t2r228", "S2")
        try:
            simps2.setUp()
            msp = MacroServerPools(1)
            channelerrors = []
            poolchannels = []
            componentgroup = {"smycp": False, "smycp2": False, "smycp3": False,
                              "s2mycp": False, "s2mycp2": False,
                              "s2mycp3": False}
            datasourcegroup = {
                "scalar_uchar": False, "scalar_string": False,
                "scalar_ulong": False,
                "scalar2_uchar": False, "scalar2_string": False,
                "scalar2_ulong": False
            }

            cps = dict(self.smycps)
            cps.update(self.smycps2)
            dss = dict(self.smydss)
            dss.update(self.smydss2)

            self._cf.dp.SetCommandVariable(["CPDICT", json.dumps(cps)])
            self._cf.dp.SetCommandVariable(["DSDICT", json.dumps(dss)])
    #        print "MDSS", self._cf.dp.availableDataSources()
    #        print "XDSS", self._cf.dp.dataSources(["scalar_long"])
            res, res2 = msp.checkChannels(list(self._ms.door.keys())[0],
                                          self._cf.dp,
                                          poolchannels,
                                          componentgroup,
                                          datasourcegroup,
                                          channelerrors)
    #        print res
    #        print channelerrors

            self.myAssertDict(json.loads(res), {
                "smycp": False, "smycp2": False, "smycp3": False,
                "s2mycp": False, "s2mycp2": False, "s2mycp3": False})
            self.myAssertDict(datasourcegroup, json.loads(res2))
            self.myAssertDict(json.loads(res2), {
                "scalar_uchar": False, "scalar_string": False,
                "scalar_ulong": False,
                "scalar2_uchar": False, "scalar2_string": False,
                "scalar2_ulong": False
            }
            )
            self.myAssertDict(componentgroup, json.loads(res))
            self.assertEqual(len(channelerrors), 0)

    #        print self._cf.dp.GetCommandVariable("COMMANDS")
            self.assertEqual(
                json.loads(self._cf.dp.GetCommandVariable("COMMANDS")), [
                    "AvailableComponents", "AvailableDataSources",
                    "AvailableComponents", "AvailableDataSources",
                ])
            res = json.loads(self._cf.dp.GetCommandVariable("VARS"))
        finally:
            simps2.tearDown()

    # constructor test
    # \brief It tests default settings
    def test_checkChannels_2wds_dvnorunning(self):
        fun = sys._getframe().f_code.co_name
        print("Run: %s.%s() " % (self.__class__.__name__, fun))
        simps2 = TestServerSetUp.TestServerSetUp(
            "ttestp09/testts/t2r228", "S2")
        try:
            simps2.add()
            msp = MacroServerPools(1)
            channelerrors = []
            poolchannels = []
            componentgroup = {
                "smycp": False, "smycp2": True, "smycp3": None,
                "s2mycp": False, "s2mycp2": True, "s2mycp3": None}
            datasourcegroup = {
                "scalar_uchar": False, "scalar_string": True,
                "scalar_ulong": None,
                "scalar2_uchar": False, "scalar2_string": True,
                "scalar2_ulong": None
            }

            cps = dict(self.smycps)
            cps.update(self.smycps2)
            dss = dict(self.smydss)
            dss.update(self.smydss2)

            self._cf.dp.SetCommandVariable(["CPDICT", json.dumps(cps)])
            self._cf.dp.SetCommandVariable(["DSDICT", json.dumps(dss)])
    #        print "MDSS", self._cf.dp.availableDataSources()
    #        print "XDSS", self._cf.dp.dataSources(["scalar_long"])
            res, res2 = msp.checkChannels(list(self._ms.door.keys())[0],
                                          self._cf.dp,
                                          poolchannels,
                                          componentgroup,
                                          datasourcegroup,
                                          channelerrors)
    #        print res
    #        print channelerrors

            self.myAssertDict(json.loads(res), {
                "smycp": False, "smycp2": True, "smycp3": True,
                "s2mycp": False, "s2mycp2": None, "s2mycp3": None})
            self.myAssertDict(datasourcegroup, json.loads(res2))
            self.myAssertDict(json.loads(res2), {
                "scalar_uchar": False, "scalar_string": True,
                "scalar_ulong": True,
                "scalar2_uchar": False, "scalar2_string": None,
                "scalar2_ulong": None
            })
            self.myAssertDict(componentgroup, json.loads(res))
            self.assertEqual(len(channelerrors), 4)

            # print(self._cf.dp.GetCommandVariable("COMMANDS"))
            self.assertEqual(
                json.loads(self._cf.dp.GetCommandVariable("COMMANDS")), [
                    "AvailableComponents", "AvailableDataSources",
                    "AvailableComponents", "AvailableDataSources",
                    "DependentComponents",
                    "Components", "DataSources", "DataSources", "DataSources",
                    "DependentComponents",
                    "Components", "DataSources", "DataSources", "DataSources",
                    "DependentComponents",
                    "Components", "DataSources", "DataSources", "DataSources",
                    "DependentComponents",
                    "Components", "DataSources", "DataSources", "DataSources",
                    "DataSources",
                    "DataSources", "DataSources",
                    "DataSources", "DataSources",
                    "DataSources", "DataSources",
                    "DataSources"])
            res = json.loads(self._cf.dp.GetCommandVariable("VARS"))
        finally:
            simps2.delete()

    # constructor test
    # \brief It tests default settings
    def test_checkChannels_2wds_dvnorunning_pe(self):
        fun = sys._getframe().f_code.co_name
        print("Run: %s.%s() " % (self.__class__.__name__, fun))
        simps2 = TestServerSetUp.TestServerSetUp(
            "ttestp09/testts/t2r228", "S2")
        try:
            simps2.add()
            msp = MacroServerPools(1)
            channelerrors = []
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
    #        print "MDSS", self._cf.dp.availableDataSources()
    #        print "XDSS", self._cf.dp.dataSources(["scalar_long"])
            res, res2 = msp.checkChannels(list(self._ms.door.keys())[0],
                                          self._cf.dp,
                                          poolchannels,
                                          componentgroup,
                                          datasourcegroup,
                                          channelerrors)
#            print json.loads(res)
#            print json.loads(res2)
#            print channelerrors

            self.myAssertDict(json.loads(res), {
                u'pyeval1a': True, u'pyeval2a': None, u'pyeval2c': None,
                u'pyeval2b': True, u'pyeval2': True, u'pyeval0': True,
                u'pyeval1': True})
            self.myAssertDict(datasourcegroup, json.loads(res2))
            self.myAssertDict(json.loads(res2), {
                u'pyeval1ads': True, u'pyeval2ads': None, u'pyeval2bds': True,
                u'pyeval2cds': None, u'pyeval0ds': True, u'pyeval1ds': True,
                u'pyeval2ds': True}
            )
            self.myAssertDict(componentgroup, json.loads(res))
            self.assertEqual(len(channelerrors), 4)

        finally:
            simps2.delete()

    # constructor test
    # \brief It tests default settings
    def test_checkChannels_2wds2_dvnorunning_pe(self):
        fun = sys._getframe().f_code.co_name
        print("Run: %s.%s() " % (self.__class__.__name__, fun))
        simps2 = TestServerSetUp.TestServerSetUp(
            "ttestp09/testts/t2r228", "S2")
        try:
            simps2.setUp()
            msp = MacroServerPools(1)
            channelerrors = []
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
    #        print "MDSS", self._cf.dp.availableDataSources()
    #        print "XDSS", self._cf.dp.dataSources(["scalar_long"])
            res, res2 = msp.checkChannels(list(self._ms.door.keys())[0],
                                          self._cf.dp,
                                          poolchannels,
                                          componentgroup,
                                          datasourcegroup,
                                          channelerrors)
#            print json.loads(res)
#            print json.loads(res2)
#            print channelerrors

            self.myAssertDict(json.loads(res), {
                u'pyeval1a': True, u'pyeval2a': True, u'pyeval2c': True,
                u'pyeval2b': True, u'pyeval2': True, u'pyeval0': True,
                u'pyeval1': True})
            self.myAssertDict(datasourcegroup, json.loads(res2))
            self.myAssertDict(json.loads(res2), {
                u'pyeval1ads': True, u'pyeval2ads': True, u'pyeval2bds': True,
                u'pyeval2cds': True, u'pyeval0ds': True, u'pyeval1ds': True,
                u'pyeval2ds': True}
            )
            self.myAssertDict(componentgroup, json.loads(res))
            self.assertEqual(len(channelerrors), 0)

        finally:
            simps2.tearDown()

    # constructor test
    # \brief It tests default settings
    def test_checkChannels_2wds2_dvnorunning_pe_true(self):
        fun = sys._getframe().f_code.co_name
        print("Run: %s.%s() " % (self.__class__.__name__, fun))
        simps2 = TestServerSetUp.TestServerSetUp(
            "ttestp09/testts/t2r228", "S2")
        try:
            simps2.setUp()
            msp = MacroServerPools(1)
            channelerrors = []
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
    #        print "MDSS", self._cf.dp.availableDataSources()
    #        print "XDSS", self._cf.dp.dataSources(["scalar_long"])
            res, res2 = msp.checkChannels(list(self._ms.door.keys())[0],
                                          self._cf.dp,
                                          poolchannels,
                                          componentgroup,
                                          datasourcegroup,
                                          channelerrors)
#            print json.loads(res)
#            print json.loads(res2)
#            print channelerrors

            self.myAssertDict(json.loads(res), {
                u'pyeval1a': True, u'pyeval2a': True, u'pyeval2c': True,
                u'pyeval2b': True, u'pyeval2': True, u'pyeval0': True,
                u'pyeval1': True})
            self.myAssertDict(datasourcegroup, json.loads(res2))
            self.myAssertDict(json.loads(res2), {
                u'pyeval1ads': True, u'pyeval2ads': True, u'pyeval2bds': True,
                u'pyeval2cds': True, u'pyeval0ds': True, u'pyeval1ds': True,
                u'pyeval2ds': True}
            )
            self.myAssertDict(componentgroup, json.loads(res))
            self.assertEqual(len(channelerrors), 0)

        finally:
            simps2.tearDown()

    # constructor test
    # \brief It tests default settings
    def test_checkChannels_2wds2_dvnorunning_pe_false(self):
        fun = sys._getframe().f_code.co_name
        print("Run: %s.%s() " % (self.__class__.__name__, fun))
        simps2 = TestServerSetUp.TestServerSetUp(
            "ttestp09/testts/t2r228", "S2")
        try:
            simps2.setUp()
            msp = MacroServerPools(1)
            channelerrors = []
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
    #        print "MDSS", self._cf.dp.availableDataSources()
    #        print "XDSS", self._cf.dp.dataSources(["scalar_long"])
            res, res2 = msp.checkChannels(list(self._ms.door.keys())[0],
                                          self._cf.dp,
                                          poolchannels,
                                          componentgroup,
                                          datasourcegroup,
                                          channelerrors)
#            print json.loads(res)
#            print json.loads(res2)
#            print channelerrors

            self.myAssertDict(json.loads(res), {
                u'pyeval1a': False, u'pyeval2a': False, u'pyeval2c': False,
                u'pyeval2b': False, u'pyeval2': False, u'pyeval0': False,
                u'pyeval1': False})
            self.myAssertDict(datasourcegroup, json.loads(res2))
            self.myAssertDict(json.loads(res2), {
                u'pyeval1ads': False, u'pyeval2ads': False,
                u'pyeval2bds': False,
                u'pyeval2cds': False, u'pyeval0ds': False, u'pyeval1ds': False,
                u'pyeval2ds': False}
            )
            self.myAssertDict(componentgroup, json.loads(res))
            self.assertEqual(len(channelerrors), 0)

        finally:
            simps2.tearDown()

    # constructor test
    # \brief It tests default settings
    def test_checkChannels_2wds_dvnorunning_pe_true(self):
        fun = sys._getframe().f_code.co_name
        print("Run: %s.%s() " % (self.__class__.__name__, fun))
        simps2 = TestServerSetUp.TestServerSetUp(
            "ttestp09/testts/t2r228", "S2")
        try:
            simps2.add()
            msp = MacroServerPools(1)
            channelerrors = []
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
    #        print "MDSS", self._cf.dp.availableDataSources()
    #        print "XDSS", self._cf.dp.dataSources(["scalar_long"])
            res, res2 = msp.checkChannels(list(self._ms.door.keys())[0],
                                          self._cf.dp,
                                          poolchannels,
                                          componentgroup,
                                          datasourcegroup,
                                          channelerrors)
#            print json.loads(res)
#            print json.loads(res2)
#            print channelerrors

            self.myAssertDict(json.loads(res), {
                u'pyeval1a': True, u'pyeval2a': None, u'pyeval2c': None,
                u'pyeval2b': True, u'pyeval2': True, u'pyeval0': True,
                u'pyeval1': True})
            self.myAssertDict(datasourcegroup, json.loads(res2))
            self.myAssertDict(json.loads(res2), {
                u'pyeval1ads': True, u'pyeval2ads': None, u'pyeval2bds': True,
                u'pyeval2cds': None, u'pyeval0ds': True, u'pyeval1ds': True,
                u'pyeval2ds': True}
            )
            self.myAssertDict(componentgroup, json.loads(res))
            self.assertEqual(len(channelerrors), 4)

        finally:
            simps2.delete()
    # constructor test
    # \brief It tests default settings

    def test_checkChannels_2wds_dvnorunning_pe_false(self):
        fun = sys._getframe().f_code.co_name
        print("Run: %s.%s() " % (self.__class__.__name__, fun))
        simps2 = TestServerSetUp.TestServerSetUp(
            "ttestp09/testts/t2r228", "S2")
        try:
            simps2.add()
            msp = MacroServerPools(1)
            channelerrors = []
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
    #        print "MDSS", self._cf.dp.availableDataSources()
    #        print "XDSS", self._cf.dp.dataSources(["scalar_long"])
            res, res2 = msp.checkChannels(list(self._ms.door.keys())[0],
                                          self._cf.dp,
                                          poolchannels,
                                          componentgroup,
                                          datasourcegroup,
                                          channelerrors)
#            print json.loads(res)
#            print json.loads(res2)
#            print channelerrors

            self.myAssertDict(json.loads(res), {
                u'pyeval1a': False, u'pyeval2a': False, u'pyeval2c': False,
                u'pyeval2b': False, u'pyeval2': False, u'pyeval0': False,
                u'pyeval1': False})
            self.myAssertDict(datasourcegroup, json.loads(res2))
            self.myAssertDict(json.loads(res2), {
                u'pyeval1ads': False, u'pyeval2ads': False,
                u'pyeval2bds': False,
                u'pyeval2cds': False, u'pyeval0ds': False, u'pyeval1ds': False,
                u'pyeval2ds': False}
            )
            self.myAssertDict(componentgroup, json.loads(res))
            self.assertEqual(len(channelerrors), 0)

        finally:
            simps2.delete()

    # constructor test
    # \brief It tests default settings
    def test_checkChannels_2wds_dvnodef(self):
        fun = sys._getframe().f_code.co_name
        print("Run: %s.%s() " % (self.__class__.__name__, fun))
        msp = MacroServerPools(1)
        channelerrors = []
        poolchannels = []
        componentgroup = {"smycp": False, "smycp2": True, "smycp3": None,
                          "s2mycp": False, "s2mycp2": True, "s2mycp3": None}
        datasourcegroup = {
            "scalar_uchar": False, "scalar_string": True,
            "scalar_ulong": None,
            "scalar2_uchar": False, "scalar2_string": True,
            "scalar2_ulong": None
        }

        cps = dict(self.smycps)
        cps.update(self.smycps2)
        dss = dict(self.smydss)
        dss.update(self.smydss2)

        self._cf.dp.SetCommandVariable(["CPDICT", json.dumps(cps)])
        self._cf.dp.SetCommandVariable(["DSDICT", json.dumps(dss)])
#        print "MDSS", self._cf.dp.availableDataSources()
#        print "XDSS", self._cf.dp.dataSources(["scalar_long"])
        res, res2 = msp.checkChannels(list(self._ms.door.keys())[0],
                                      self._cf.dp,
                                      poolchannels,
                                      componentgroup,
                                      datasourcegroup,
                                      channelerrors)
#        print res
#        print channelerrors

        self.myAssertDict(json.loads(res), {
            "smycp": False, "smycp2": True, "smycp3": True,
            "s2mycp": False, "s2mycp2": None, "s2mycp3": None})
        self.myAssertDict(componentgroup, json.loads(res))
        self.myAssertDict(datasourcegroup, json.loads(res2))
        self.myAssertDict(json.loads(res2), {
            "scalar_uchar": False, "scalar_string": True,
            "scalar_ulong": True,
            "scalar2_uchar": False, "scalar2_string": None,
            "scalar2_ulong": None
        })
        self.assertEqual(len(channelerrors), 4)

        # print(self._cf.dp.GetCommandVariable("COMMANDS"))
        self.assertEqual(
            json.loads(
                self._cf.dp.GetCommandVariable("COMMANDS")),
            ["AvailableComponents", "AvailableDataSources",
             "AvailableComponents",
             "AvailableDataSources", "DependentComponents", "Components",
             "DataSources", "DataSources", "DataSources",
             "DependentComponents",
             "Components", "DataSources", "DataSources", "DataSources",
             "DependentComponents", "Components", "DataSources", "DataSources",
             "DataSources", "DependentComponents", "Components", "DataSources",
             "DataSources", "DataSources", "DataSources", "DataSources",
             "DataSources", "DataSources", "DataSources", "DataSources",
             "DataSources", "DataSources"])
        res = json.loads(self._cf.dp.GetCommandVariable("VARS"))

    # constructor test
    # \brief It tests default settings
    def test_checkChannels_2wds_nods(self):
        fun = sys._getframe().f_code.co_name
        print("Run: %s.%s() " % (self.__class__.__name__, fun))
        simps2 = TestServerSetUp.TestServerSetUp(
            "ttestp09/testts/t2r228", "S2")
        try:
            simps2.setUp()
            msp = MacroServerPools(1)
            channelerrors = []
            poolchannels = []
            componentgroup = {
                "smycp": False, "smycp2": True, "smycp3": None,
                "s2mycp": False, "s2mycp2": True, "s2mycp3": None}
            datasourcegroup = {
                "scalar_uchar": False, "scalar_string": True,
                "scalar_ulong": None,
                "scalar2_uchar": False, "scalar2_string": True,
                "scalar2_ulong": None
            }

            cps = dict(self.smycps)
            cps.update(self.smycps2)
            dss = dict(self.smydss)
#            dss.update(self.smydss2)

            self._cf.dp.SetCommandVariable(["CPDICT", json.dumps(cps)])
            self._cf.dp.SetCommandVariable(["DSDICT", json.dumps(dss)])
    #        print "MDSS", self._cf.dp.availableDataSources()
    #        print "XDSS", self._cf.dp.dataSources(["scalar_long"])
            res, res2 = msp.checkChannels(list(self._ms.door.keys())[0],
                                          self._cf.dp,
                                          poolchannels,
                                          componentgroup,
                                          datasourcegroup,
                                          channelerrors)
    #        print res
    #        print channelerrors

            self.myAssertDict(json.loads(res), {
                "smycp": False, "smycp2": True, "smycp3": True,
                "s2mycp": False, "s2mycp2": None, "s2mycp3": None})
#                "smycp": False, "smycp2": True, "smycp3": True,
#                "s2mycp": False, "s2mycp2": True, "s2mycp3": True})
            self.myAssertDict(componentgroup, json.loads(res))
            self.myAssertDict(datasourcegroup, json.loads(res2))
            self.myAssertDict(json.loads(res2), {
                "scalar_uchar": False, "scalar_string": True,
                "scalar_ulong": True,
                "scalar2_uchar": False, "scalar2_string": None,
                "scalar2_ulong": None
            })
            self.assertEqual(len(channelerrors), 4)

    #        print self._cf.dp.GetCommandVariable("COMMANDS")
            res = json.loads(self._cf.dp.GetCommandVariable("VARS"))
        finally:
            simps2.tearDown()

    # constructor test
    # \brief It tests default settings
    def test_checkChannels_2wds_nodspool(self):
        fun = sys._getframe().f_code.co_name
        print("Run: %s.%s() " % (self.__class__.__name__, fun))
        simps2 = TestServerSetUp.TestServerSetUp(
            "ttestp09/testts/t2r228", "S2")
        try:
            simps2.setUp()
            msp = MacroServerPools(1)
            channelerrors = []
            poolchannels = ["scalar2_long", "spectrum2_short", "scalar2_uchar"]
            componentgroup = {
                "smycp": False, "smycp2": True, "smycp3": None,
                "s2mycp": False, "s2mycp2": True, "s2mycp3": None}
            datasourcegroup = {
                "scalar_uchar": False, "scalar_string": True,
                "scalar_ulong": None,
                "scalar2_uchar": False, "scalar2_string": True,
                "scalar2_ulong": None
            }

            cps = dict(self.smycps)
            cps.update(self.smycps2)
            dss = dict(self.smydss)
#            dss.update(self.smydss2)

            self._cf.dp.SetCommandVariable(["CPDICT", json.dumps(cps)])
            self._cf.dp.SetCommandVariable(["DSDICT", json.dumps(dss)])
            #        print "MDSS", self._cf.dp.availableDataSources()
            #        print "XDSS", self._cf.dp.dataSources(["scalar_long"])
            res, res2 = msp.checkChannels(list(self._ms.door.keys())[0],
                                          self._cf.dp,
                                          poolchannels,
                                          componentgroup,
                                          datasourcegroup,
                                          channelerrors)

    #        print res2
    #        print channelerrors

            self.myAssertDict(json.loads(res), {
                "smycp": False, "smycp2": True, "smycp3": True,
                "s2mycp": False, "s2mycp2": None, "s2mycp3": None})
            self.myAssertDict(componentgroup, json.loads(res))
            self.myAssertDict(datasourcegroup, json.loads(res2))
            self.myAssertDict(json.loads(res2), {
                "scalar_uchar": False, "scalar_string": True,
                "scalar_ulong": True,
                "scalar2_uchar": False, "scalar2_string": None,
                "scalar2_ulong": None
            })
            self.assertEqual(len(channelerrors), 4)

    #        print self._cf.dp.GetCommandVariable("COMMANDS")
            res = json.loads(self._cf.dp.GetCommandVariable("VARS"))
        finally:
            simps2.tearDown()

    # constructor test
    # \brief It tests default settings
    def test_checkChannels_2wds_notangods(self):
        fun = sys._getframe().f_code.co_name
        print("Run: %s.%s() " % (self.__class__.__name__, fun))
        simps2 = TestServerSetUp.TestServerSetUp(
            "ttestp09/testts/t2r228", "S2")
        try:
            simps2.setUp()
            msp = MacroServerPools(1)
            channelerrors = []
            poolchannels = ["scalar2_long", "spectrum2_short"]
            componentgroup = {"smycp": False, "smycp2": True,
                              "smycp3": None, "smycpnt1": None,
                              "s2mycp": False, "s2mycp2": True,
                              "s2mycp3": None}
            datasourcegroup = {
                "scalar_uchar": False, "scalar_string": True,
                "scalar_ulong": None,
                "scalar2_uchar": False, "scalar2_string": True,
                "scalar2_ulong": None,
                "ann3": None,
            }

            cps = dict(self.smycps)
            cps.update(self.smycps2)
            dss = dict(self.smydss)
            dss.update(self.smydss2)
            dss.update(self.mydss)

            self._cf.dp.SetCommandVariable(["CPDICT", json.dumps(cps)])
            self._cf.dp.SetCommandVariable(["DSDICT", json.dumps(dss)])
    #        print "MDSS", self._cf.dp.availableDataSources()
    #        print "XDSS", self._cf.dp.dataSources(["scalar_long"])
            res, res2 = msp.checkChannels(list(self._ms.door.keys())[0],
                                          self._cf.dp,
                                          poolchannels,
                                          componentgroup,
                                          datasourcegroup,
                                          channelerrors)
            # print res2
    #        print channelerrors

            self.myAssertDict(json.loads(res), {
                "smycp": False, "smycp2": True, "smycp3": True,
                "s2mycp": False, "s2mycp2": True, "s2mycp3": True,
                "smycpnt1": True})
            self.myAssertDict(componentgroup, json.loads(res))
            self.myAssertDict(datasourcegroup, json.loads(res2))
            self.myAssertDict(json.loads(res2), {
                "scalar_uchar": False, "scalar_string": True,
                "scalar_ulong": True,
                "scalar2_uchar": False, "scalar2_string": True,
                "scalar2_ulong": True,
                "ann3": True,
            })
            self.assertEqual(len(channelerrors), 0)

    #        print self._cf.dp.GetCommandVariable("COMMANDS")
            res = json.loads(self._cf.dp.GetCommandVariable("VARS"))
        finally:
            simps2.tearDown()

    # constructor test
    # \brief It tests default settings
    def test_checkChannels_2wds_notangodsnopool(self):
        fun = sys._getframe().f_code.co_name
        print("Run: %s.%s() " % (self.__class__.__name__, fun))
        simps2 = TestServerSetUp.TestServerSetUp(
            "ttestp09/testts/t2r228", "S2")
        try:
            simps2.setUp()
            msp = MacroServerPools(1)
            channelerrors = []
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
    #        print "MDSS", self._cf.dp.availableDataSources()
    #        print "XDSS", self._cf.dp.dataSources(["scalar_long"])
            res, res2 = msp.checkChannels(list(self._ms.door.keys())[0],
                                          self._cf.dp,
                                          poolchannels,
                                          componentgroup,
                                          datasourcegroup,
                                          channelerrors)
#            print res
    #        print channelerrors

            self.myAssertDict(json.loads(res), {
                "smycp": True, "smycp2": True, "smycp3": True,
                "s2mycp": True, "s2mycp2": True, "s2mycp3": False,
                "smycpnt1": None})
            self.myAssertDict(componentgroup, json.loads(res))
            self.myAssertDict(datasourcegroup, json.loads(res2))
            self.myAssertDict(json.loads(res2), {
                "scalar_uchar": True, "scalar_string": True,
                "scalar_ulong": False,
                "scalar2_uchar": True, "scalar2_string": True,
                "scalar2_ulong": False,
                "ann3": None,
            })
            self.assertEqual(len(channelerrors), 2)

    #        print self._cf.dp.GetCommandVariable("COMMANDS")
            res = json.loads(self._cf.dp.GetCommandVariable("VARS"))
        finally:
            simps2.tearDown()

    # constructor test
    # \brief It tests default settings
    def test_checkChannels_2wds_notangodsnopool_False(self):
        fun = sys._getframe().f_code.co_name
        print("Run: %s.%s() " % (self.__class__.__name__, fun))
        simps2 = TestServerSetUp.TestServerSetUp(
            "ttestp09/testts/t2r228", "S2")
        try:
            simps2.setUp()
            msp = MacroServerPools(1)
            channelerrors = []
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
    #        print "MDSS", self._cf.dp.availableDataSources()
    #        print "XDSS", self._cf.dp.dataSources(["scalar_long"])
            res, res2 = msp.checkChannels(list(self._ms.door.keys())[0],
                                          self._cf.dp,
                                          poolchannels,
                                          componentgroup,
                                          datasourcegroup,
                                          channelerrors)
#            print res
    #        print channelerrors

            self.myAssertDict(json.loads(res), {
                "smycp": True, "smycp2": True, "smycp3": True,
                "s2mycp": True, "s2mycp2": True, "s2mycp3": False,
                "smycpnt1": False})
            self.myAssertDict(componentgroup, json.loads(res))
            self.myAssertDict(datasourcegroup, json.loads(res2))
            self.myAssertDict(json.loads(res2), {
                "scalar_uchar": True, "scalar_string": True,
                "scalar_ulong": False,
                "scalar2_uchar": True, "scalar2_string": True,
                "scalar2_ulong": False,
                "ann3": False,
            })
            self.assertEqual(len(channelerrors), 0)

    #        print self._cf.dp.GetCommandVariable("COMMANDS")
            res = json.loads(self._cf.dp.GetCommandVariable("VARS"))
        finally:
            simps2.tearDown()

    # constructor test
    # \brief It tests default settings
    def test_checkChannels_2wds_notangodsnopool2(self):
        fun = sys._getframe().f_code.co_name
        print("Run: %s.%s() " % (self.__class__.__name__, fun))
        simps2 = TestServerSetUp.TestServerSetUp(
            "ttestp09/testts/t2r228", "S2")
        try:
            simps2.setUp()
            msp = MacroServerPools(10)
            db = PyTango.Database()
            db.put_device_property(list(self._ms.ms.keys())[0],
                                   {'PoolNames': self._pool.dp.name()})
            channelerrors = []
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
            msp.updateMacroServer(list(self._ms.door.keys())[0])
            # pools =
            msp.getPools(list(self._ms.door.keys())[0])
            # print "POOLS", pools

            res, res2 = msp.checkChannels(list(self._ms.door.keys())[0],
                                          self._cf.dp,
                                          poolchannels,
                                          componentgroup,
                                          datasourcegroup,
                                          channelerrors)
#            print res
    #        print channelerrors

            self.myAssertDict(json.loads(res), {
                "smycp": False, "smycp2": True, "smycp3": True,
                "s2mycp": True, "s2mycp2": True, "s2mycp3": False,
                "smycpnt1": None})
            self.myAssertDict(componentgroup, json.loads(res))
            self.myAssertDict(datasourcegroup, json.loads(res2))
            self.myAssertDict(json.loads(res2), {
                "scalar_uchar": True, "scalar_string": True,
                "scalar_ulong": False,
                "scalar2_uchar": True, "scalar2_string": True,
                "scalar2_ulong": False,
                "ann3": None,
            })
            self.assertEqual(len(channelerrors), 2)

    #        print self._cf.dp.GetCommandVariable("COMMANDS")
            res = json.loads(self._cf.dp.GetCommandVariable("VARS"))
        finally:
            simps2.tearDown()

    # constructor test
    # \brief It tests default settings
    def test_checkChannels_2wds_notangodsnopool2_False(self):
        fun = sys._getframe().f_code.co_name
        print("Run: %s.%s() " % (self.__class__.__name__, fun))
        simps2 = TestServerSetUp.TestServerSetUp(
            "ttestp09/testts/t2r228", "S2")
        try:
            simps2.setUp()
            msp = MacroServerPools(10)
            db = PyTango.Database()
            db.put_device_property(list(self._ms.ms.keys())[0],
                                   {'PoolNames': self._pool.dp.name()})
            channelerrors = []
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
            msp.updateMacroServer(list(self._ms.door.keys())[0])
            # pools =
            msp.getPools(list(self._ms.door.keys())[0])
            # print "POOLS", pools

            res, res2 = msp.checkChannels(list(self._ms.door.keys())[0],
                                          self._cf.dp,
                                          poolchannels,
                                          componentgroup,
                                          datasourcegroup,
                                          channelerrors)
#            print res
    #        print channelerrors

            self.myAssertDict(json.loads(res), {
                "smycp": False, "smycp2": True, "smycp3": True,
                "s2mycp": True, "s2mycp2": True, "s2mycp3": False,
                "smycpnt1": False})
            self.myAssertDict(componentgroup, json.loads(res))
            self.myAssertDict(datasourcegroup, json.loads(res2))
            self.myAssertDict(json.loads(res2), {
                "scalar_uchar": True, "scalar_string": True,
                "scalar_ulong": False,
                "scalar2_uchar": True, "scalar2_string": True,
                "scalar2_ulong": False,
                "ann3": False,
            })
            self.assertEqual(len(channelerrors), 0)

    #        print self._cf.dp.GetCommandVariable("COMMANDS")
            res = json.loads(self._cf.dp.GetCommandVariable("VARS"))
        finally:
            simps2.tearDown()

    # constructor test
    # \brief It tests default settings
    def test_checkChannels_2wds_notangods2(self):
        fun = sys._getframe().f_code.co_name
        print("Run: %s.%s() " % (self.__class__.__name__, fun))
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
            msp = MacroServerPools(10)
            db = PyTango.Database()
            db.put_device_property(list(self._ms.ms.keys())[0],
                                   {'PoolNames': self._pool.dp.name()})
            channelerrors = []
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
            msp.updateMacroServer(list(self._ms.door.keys())[0])
            pools = msp.getPools(list(self._ms.door.keys())[0])
            pools[0].AcqChannelList = [json.dumps(a) for a in arr]
            # print "POOLS", pools

            res, res2 = msp.checkChannels(list(self._ms.door.keys())[0],
                                          self._cf.dp,
                                          poolchannels,
                                          componentgroup,
                                          datasourcegroup,
                                          channelerrors)

            self.myAssertDict(json.loads(res), {
                "smycp": False, "smycp2": True, "smycp3": True,
                "s2mycp": True, "s2mycp2": False, "s2mycp3": True,
                "smycpnt1": True})
            self.myAssertDict(componentgroup, json.loads(res))
            self.myAssertDict(datasourcegroup, json.loads(res2))
            self.myAssertDict(json.loads(res2), {
                "scalar_uchar": True, "scalar_string": True,
                "scalar_ulong": False,
                "scalar2_uchar": True, "scalar2_string": True,
                "scalar2_ulong": False,
                "ann3": True,
            })
            self.assertEqual(len(channelerrors), 0)

    #        print self._cf.dp.GetCommandVariable("COMMANDS")
            res = json.loads(self._cf.dp.GetCommandVariable("VARS"))
        finally:
            simps2.tearDown()

    # constructor test
    # \brief It tests default settings
    def test_checkChannels_2wds_notangods2_false(self):
        fun = sys._getframe().f_code.co_name
        print("Run: %s.%s() " % (self.__class__.__name__, fun))
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
            msp = MacroServerPools(10)
            db = PyTango.Database()
            db.put_device_property(list(self._ms.ms.keys())[0],
                                   {'PoolNames': self._pool.dp.name()})
            channelerrors = []
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
            msp.updateMacroServer(list(self._ms.door.keys())[0])
            pools = msp.getPools(list(self._ms.door.keys())[0])
            pools[0].AcqChannelList = [json.dumps(a) for a in arr]
            # print "POOLS", pools

            res, res2 = msp.checkChannels(list(self._ms.door.keys())[0],
                                          self._cf.dp,
                                          poolchannels,
                                          componentgroup,
                                          datasourcegroup,
                                          channelerrors)

            self.myAssertDict(json.loads(res), {
                "smycp": False, "smycp2": True, "smycp3": True,
                "s2mycp": True, "s2mycp2": False, "s2mycp3": True,
                "smycpnt1": False})
            self.myAssertDict(componentgroup, json.loads(res))
            self.myAssertDict(datasourcegroup, json.loads(res2))
            self.myAssertDict(json.loads(res2), {
                "scalar_uchar": True, "scalar_string": True,
                "scalar_ulong": False,
                "scalar2_uchar": True, "scalar2_string": True,
                "scalar2_ulong": False,
                "ann3": False,
            })
            self.assertEqual(len(channelerrors), 0)

    #        print self._cf.dp.GetCommandVariable("COMMANDS")
            res = json.loads(self._cf.dp.GetCommandVariable("VARS"))
        finally:
            simps2.tearDown()

    # constructor test
    # \brief It tests default settings
    def test_checkChannels_2wds_notangodspool_error(self):
        fun = sys._getframe().f_code.co_name
        print("Run: %s.%s() " % (self.__class__.__name__, fun))
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
            msp = MacroServerPools(10)
            db = PyTango.Database()
            db.put_device_property(list(self._ms.ms.keys())[0],
                                   {'PoolNames': self._pool.dp.name()})
            channelerrors = []
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
    #        print "MDSS", self._cf.dp.availableDataSources()
    #        print "XDSS", self._cf.dp.dataSources(["scalar_long"])
            msp.updateMacroServer(list(self._ms.door.keys())[0])
            pools = msp.getPools(list(self._ms.door.keys())[0])
            pools[0].AcqChannelList = [json.dumps(a) for a in arr]
            # print "POOLS", pools

            res, res2 = msp.checkChannels(list(self._ms.door.keys())[0],
                                          self._cf.dp,
                                          poolchannels,
                                          componentgroup,
                                          datasourcegroup,
                                          channelerrors)
            # print res
    #        print channelerrors

            self.myAssertDict(json.loads(res), {
                "smycp": False, "smycp2": True, "smycp3": True,
                "s2mycp": False, "s2mycp2": True, "s2mycp3": True,
                "smycpnt1": None})
            self.myAssertDict(componentgroup, json.loads(res))
            self.myAssertDict(datasourcegroup, json.loads(res2))
            self.myAssertDict(json.loads(res2), {
                "scalar_uchar": True, "scalar_string": True,
                "scalar_ulong": False,
                "scalar2_uchar": True, "scalar2_string": True,
                "scalar2_ulong": False,
                "ann3": None,
            })
            self.assertEqual(len(channelerrors), 2)

    #        print self._cf.dp.GetCommandVariable("COMMANDS")
            res = json.loads(self._cf.dp.GetCommandVariable("VARS"))
        finally:
            simps2.tearDown()

    # constructor test
    # \brief It tests default settings
    def test_checkChannels_2wds_notangodspool_error_false(self):
        fun = sys._getframe().f_code.co_name
        print("Run: %s.%s() " % (self.__class__.__name__, fun))
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
            msp = MacroServerPools(10)
            db = PyTango.Database()
            db.put_device_property(list(self._ms.ms.keys())[0],
                                   {'PoolNames': self._pool.dp.name()})
            channelerrors = []
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
    #        print "MDSS", self._cf.dp.availableDataSources()
    #        print "XDSS", self._cf.dp.dataSources(["scalar_long"])
            msp.updateMacroServer(list(self._ms.door.keys())[0])
            pools = msp.getPools(list(self._ms.door.keys())[0])
            pools[0].AcqChannelList = [json.dumps(a) for a in arr]
            # print "POOLS", pools

            res, res2 = msp.checkChannels(list(self._ms.door.keys())[0],
                                          self._cf.dp,
                                          poolchannels,
                                          componentgroup,
                                          datasourcegroup,
                                          channelerrors)
            # print res
    #        print channelerrors

            self.myAssertDict(json.loads(res), {
                "smycp": False, "smycp2": True, "smycp3": True,
                "s2mycp": False, "s2mycp2": True, "s2mycp3": True,
                "smycpnt1": False})
            self.myAssertDict(componentgroup, json.loads(res))
            self.myAssertDict(datasourcegroup, json.loads(res2))
            self.myAssertDict(json.loads(res2), {
                "scalar_uchar": True, "scalar_string": True,
                "scalar_ulong": False,
                "scalar2_uchar": True, "scalar2_string": True,
                "scalar2_ulong": False,
                "ann3": False,
            })
            self.assertEqual(len(channelerrors), 0)

    #        print self._cf.dp.GetCommandVariable("COMMANDS")
            res = json.loads(self._cf.dp.GetCommandVariable("VARS"))
        finally:
            simps2.tearDown()

    # constructor test
    # \brief It tests default settings
    def test_checkChannels_2wds_notangodspool(self):
        fun = sys._getframe().f_code.co_name
        print("Run: %s.%s() " % (self.__class__.__name__, fun))
        simps2 = TestServerSetUp.TestServerSetUp(
            "ttestp09/testts/t2r228", "S2")

        arr = [
            {"name": "client_short", "full_name": "ttestp09/testts/t1r228"},
        ]
        try:
            simps2.setUp()
            msp = MacroServerPools(10)
            db = PyTango.Database()
            db.put_device_property(list(self._ms.ms.keys())[0],
                                   {'PoolNames': self._pool.dp.name()})
            channelerrors = []
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
    #        print "MDSS", self._cf.dp.availableDataSources()
    #        print "XDSS", self._cf.dp.dataSources(["scalar_long"])
            msp.updateMacroServer(list(self._ms.door.keys())[0])
            pools = msp.getPools(list(self._ms.door.keys())[0])
            pools[0].AcqChannelList = [json.dumps(a) for a in arr]
            # print "POOLS", pools
            self._simps.dp.ChangeValueType("ScalarShort")
            self._simps.dp.Value = 43
            res, res2 = msp.checkChannels(list(self._ms.door.keys())[0],
                                          self._cf.dp,
                                          poolchannels,
                                          componentgroup,
                                          datasourcegroup,
                                          channelerrors)
#            print res
    #        print channelerrors

            self.myAssertDict(json.loads(res), {
                "smycp": True, "smycp2": False, "smycp3": True,
                "s2mycp": False, "s2mycp2": True, "s2mycp3": True,
                "smycpnt1": None})
            self.myAssertDict(componentgroup, json.loads(res))
            self.myAssertDict(datasourcegroup, json.loads(res2))
            self.myAssertDict(json.loads(res2), {
                "scalar_uchar": True, "scalar_string": True,
                "scalar_ulong": False,
                "scalar2_uchar": True, "scalar2_string": True,
                "scalar2_ulong": False,
                "ann3": None,
            })
            self.assertEqual(len(channelerrors), 2)

    #        print self._cf.dp.GetCommandVariable("COMMANDS")
            res = json.loads(self._cf.dp.GetCommandVariable("VARS"))
        finally:
            simps2.tearDown()

    # constructor test
    # \brief It tests default settings
    def test_checkChannels_2wds_notangodspool_alias(self):
        fun = sys._getframe().f_code.co_name
        print("Run: %s.%s() " % (self.__class__.__name__, fun))
        simps2 = TestServerSetUp.TestServerSetUp(
            "ttestp09/testts/t2r228", "S2")
        db = PyTango.Database()

        arr = [
            {"name": "client_short", "full_name": "ttestp09/testts/t1r228"},
        ]
        try:
            simps2.setUp()
            msp = MacroServerPools(10)
            db.put_device_alias(arr[0]["full_name"], arr[0]["name"])
            db.put_device_property(list(self._ms.ms.keys())[0],
                                   {'PoolNames': self._pool.dp.name()})
            channelerrors = []
            poolchannels = ["scalar2_long", "spectrum2_short", "client_short"]
            componentgroup = {
                "smycp": None, "smycp2": None, "smycp3": None,
                "smycpnt1": None,
                "s2mycp": None, "s2mycp2": None, "s2mycp3": None
            }
            datasourcegroup = {}

            cps = dict(self.smycps)
            cps.update(self.smycps2)
            dss = dict(self.smydss)
            dss.update(self.smydss2)

            self._cf.dp.SetCommandVariable(["CPDICT", json.dumps(cps)])
            self._cf.dp.SetCommandVariable(["DSDICT", json.dumps(dss)])
            msp.updateMacroServer(list(self._ms.door.keys())[0])
            pools = msp.getPools(list(self._ms.door.keys())[0])
            pools[0].AcqChannelList = [json.dumps(a) for a in arr]
            # print "POOLS", pools
            self._simps.dp.ChangeValueType("ScalarShort")
            self._simps.dp.Value = 43
            res, res2 = msp.checkChannels(list(self._ms.door.keys())[0],
                                          self._cf.dp,
                                          poolchannels,
                                          componentgroup,
                                          datasourcegroup,
                                          channelerrors)
            # print res
    #        print channelerrors

            self.myAssertDict(json.loads(res), {
                "smycp": True, "smycp2": True, "smycp3": True,
                "s2mycp": True, "s2mycp2": True, "s2mycp3": True,
                "smycpnt1": True})
            self.myAssertDict(componentgroup, {
                "smycp": True, "smycp2": True, "smycp3": True,
                "s2mycp": True, "s2mycp2": True, "s2mycp3": True,
                "smycpnt1": True})
            self.assertEqual(len(channelerrors), 0)

    #        print self._cf.dp.GetCommandVariable("COMMANDS")
            res = json.loads(self._cf.dp.GetCommandVariable("VARS"))
        finally:
            db.delete_device_alias(arr[0]["name"])
            simps2.tearDown()

    # constructor test
    # \brief It tests default settings
    def test_checkChannels_2wds_notangodspool_alias_value(self):
        fun = sys._getframe().f_code.co_name
        print("Run: %s.%s() " % (self.__class__.__name__, fun))
        simps2 = TestServerSetUp.TestServerSetUp(
            "ttestp09/testts/t2r228", "S2")
        db = PyTango.Database()

        arr = [
            {"name": "client_short", "full_name": "ttestp09/testts/t1r228"},
        ]
        try:
            simps2.setUp()
            msp = MacroServerPools(10)
            db.put_device_alias(arr[0]["full_name"], arr[0]["name"])
            db.put_device_property(list(self._ms.ms.keys())[0],
                                   {'PoolNames': self._pool.dp.name()})
            channelerrors = []
            poolchannels = ["scalar2_long", "spectrum2_short", "client_short"]
            componentgroup = {
                "smycp": None, "smycp2": None, "smycp3": None,
                "smycpnt1": None,
                "s2mycp": None, "s2mycp2": None, "s2mycp3": None
            }
            datasourcegroup = {}

            cps = dict(self.smycps)
            cps.update(self.smycps2)
            dss = dict(self.smydss)
            dss.update(self.smydss2)

            self._cf.dp.SetCommandVariable(["CPDICT", json.dumps(cps)])
            self._cf.dp.SetCommandVariable(["DSDICT", json.dumps(dss)])
            msp.updateMacroServer(list(self._ms.door.keys())[0])
            pools = msp.getPools(list(self._ms.door.keys())[0])
            pools[0].AcqChannelList = [json.dumps(a) for a in arr]
            # print "POOLS", pools
#            self._simps.dp.ChangeValueType("ScalarShort")
#            self._simps.dp.Value = 43
            res, res2 = msp.checkChannels(list(self._ms.door.keys())[0],
                                          self._cf.dp,
                                          poolchannels,
                                          componentgroup,
                                          datasourcegroup,
                                          channelerrors)
#            print res
    #        print channelerrors

            self.myAssertDict(json.loads(res), {
                "smycp": True, "smycp2": True, "smycp3": True,
                "s2mycp": True, "s2mycp2": True, "s2mycp3": True,
                "smycpnt1": True})
            self.myAssertDict(componentgroup, {
                "smycp": True, "smycp2": True, "smycp3": True,
                "s2mycp": True, "s2mycp2": True, "s2mycp3": True,
                "smycpnt1": True})
            self.assertEqual(len(channelerrors), 0)

    #        print self._cf.dp.GetCommandVariable("COMMANDS")
            res = json.loads(self._cf.dp.GetCommandVariable("VARS"))
        finally:
            db.delete_device_alias(arr[0]["name"])
            simps2.tearDown()

    # constructor test
    # \brief It tests default settings
    def test_checkChannels_2wds_notangodspool_alias_novalue(self):
        fun = sys._getframe().f_code.co_name
        print("Run: %s.%s() " % (self.__class__.__name__, fun))
        simps2 = TestServerSetUp.TestServerSetUp(
            "ttestp09/testts/t2r228", "S2")
        db = PyTango.Database()

        arr = [
            {"name": "client2_short", "full_name": "ttestp09/testts/t2r228"},
        ]
        try:
            simps2.add()
            msp = MacroServerPools(10)
            db.put_device_alias(arr[0]["full_name"], arr[0]["name"])
            db.put_device_property(list(self._ms.ms.keys())[0],
                                   {'PoolNames': self._pool.dp.name()})
            channelerrors = []
            poolchannels = ["scalar2_long", "spectrum2_short", "client2_short"]
            componentgroup = {
                "smycp": None, "smycp2": None, "smycp3": None,
                "s2mycpnt1": None,
                # "s2mycp": False, "s2mycp2": False, "s2mycp3": False
            }
            datasourcegroup = {}

            cps = dict(self.smycps)
            cps.update(self.smycps2)
            dss = dict(self.smydss)
            dss.update(self.smydss2)

            self._cf.dp.SetCommandVariable(["CPDICT", json.dumps(cps)])
            self._cf.dp.SetCommandVariable(["DSDICT", json.dumps(dss)])
            msp.updateMacroServer(list(self._ms.door.keys())[0])
            pools = msp.getPools(list(self._ms.door.keys())[0])
            pools[0].AcqChannelList = [json.dumps(a) for a in arr]
            # print "POOLS", pools
            res, res2 = msp.checkChannels(list(self._ms.door.keys())[0],
                                          self._cf.dp,
                                          poolchannels,
                                          componentgroup,
                                          datasourcegroup,
                                          channelerrors)

            self.myAssertDict(json.loads(res), {
                "smycp": True, "smycp2": True, "smycp3": True,
                "s2mycpnt1": None})
            self.myAssertDict(componentgroup, {
                "smycp": True, "smycp2": True, "smycp3": True,
                "s2mycpnt1": None})
            self.assertEqual(len(channelerrors), 1)

    #        print self._cf.dp.GetCommandVariable("COMMANDS")
            res = json.loads(self._cf.dp.GetCommandVariable("VARS"))
        finally:
            db.delete_device_alias(arr[0]["name"])
            simps2.tearDown()

    # constructor test
    # \brief It tests default settings
    def test_checkChannels_2wds_nocomponents(self):
        fun = sys._getframe().f_code.co_name
        print("Run: %s.%s() " % (self.__class__.__name__, fun))
        simps2 = TestServerSetUp.TestServerSetUp(
            "ttestp09/testts/t2r228", "S2")
        try:
            simps2.setUp()
            msp = MacroServerPools(1)
            channelerrors = []
            poolchannels = []
            componentgroup = {
                "smycp": None, "smycp2": None, "smycp3": None,
                "s2mycp": None, "s2mycp2": None, "s2mycp3": None}
            datasourcegroup = {}

            cps = dict(self.smycps)
            dss = dict(self.smydss)

            self._cf.dp.SetCommandVariable(["CPDICT", json.dumps(cps)])
            self._cf.dp.SetCommandVariable(["DSDICT", json.dumps(dss)])
            res, res2 = msp.checkChannels(list(self._ms.door.keys())[0],
                                          self._cf.dp,
                                          poolchannels,
                                          componentgroup,
                                          datasourcegroup,
                                          channelerrors)

            self.myAssertDict(json.loads(res), {
                "smycp": True, "smycp2": True, "smycp3": True,
                "s2mycp": None, "s2mycp2": None, "s2mycp3": None})
            self.myAssertDict(componentgroup, {
                "smycp": True, "smycp2": True, "smycp3": True,
                "s2mycp": None, "s2mycp2": None, "s2mycp3": None})
            self.assertEqual(len(channelerrors), 3)

            res = json.loads(self._cf.dp.GetCommandVariable("VARS"))
        finally:
            simps2.tearDown()

    # constructor test
    # \brief It tests default settings
    def test_getSelectorEnv_noenv(self):
        fun = sys._getframe().f_code.co_name
        print("Run: %s.%s() " % (self.__class__.__name__, fun))

        envs = [
            pickle.dumps(
                {"new": {}}, protocol=2
            )
        ]
        enms = [
            [],
            ["ScanID"],
            ["ScanDir", "ScanFile"],
        ]

        edats = [
            {},
            {},
            {}
        ]

        msp = MacroServerPools(10)
        self.myAssertRaise(Exception, msp.getSelectorEnv, None, [], {})
        msp.getSelectorEnv(list(self._ms.door.keys())[0], [], {})
        dwt = msp.getScanEnv(list(self._ms.door.keys())[0])
        for i, dt in enumerate(edats):

            edl = list(json.loads(dwt).keys())
            data = {}
            self._ms.dps[list(self._ms.ms.keys())[0]].Environment = (
                'pickle', pickle.dumps({"del": edl}, protocol=2))
            self._ms.dps[list(self._ms.ms.keys())[0]].Environment = (
                'pickle', envs[0])
            msp.getSelectorEnv(list(self._ms.door.keys())[0], enms[i], data)
#            print "data",data
            dwt = msp.getScanEnv(list(self._ms.door.keys())[0])
            self.myAssertDict(data, dt)

    # constructor test
    # \brief It tests default settings
    def test_getSelectorEnv(self):
        fun = sys._getframe().f_code.co_name
        print("Run: %s.%s() " % (self.__class__.__name__, fun))

        envs = [
            pickle.dumps(
                {"new": {"ScanDir": "/tmp"}}, protocol=2
            ),
            pickle.dumps(
                {"new": {"ScanDir": "/tmp"}}, protocol=2
            ),
            pickle.dumps(
                {"new": {"ScanDir": "/tmp", "ScanFile": ["file.nxs"]}},
                protocol=2
            ),
            pickle.dumps(
                {
                    "new":
                    {
                        "ScanDir": "/tmp",
                        "ScanFile": ["file.nxs"],
                        "NeXusConfigServer": "ptr/ert/ert",
                    }
                }, protocol=2
            ),
            pickle.dumps(
                {
                    "new":
                    {
                        "ScanDir": "/tmp",
                        "ScanFile": ["file.nxs", "file2.nxs"],
                        "NeXusConfiguration": {"ConfigServer": "ptr/ert/ert2"},
                    }
                }, protocol=2
            ),
            pickle.dumps(
                {
                    "new":
                    {
                        "ScanDir": "/tmp",
                        "ScanFile": "file.nxs",
                        "NeXusConfigServer": "ptr/ert/ert",
                        "NeXusConfiguration": {"ConfigServer": "ptr/ert/ert2"},
                    }
                }, protocol=2
            ),
            pickle.dumps(
                {
                    "new":
                    {
                        "ScanDir": "/tmp",
                        "ScanFile": ["file.nxs"],
                        "NeXusConfigServer": u'ptr/ert/ert',
                        "NeXusBool": True,
                        "NeXusInt": 234,
                        "NeXusFloat": 123.123,
                        "NeXusSomething": ("dgfg",),
                        "NeXusDict": {"dgfg": 123, "sdf": "345"},
                    }
                }, protocol=2
            ),
            pickle.dumps(
                {
                    "new": {
                        "ScanDir": "/tmp",
                        "ScanFile": ["file.nxs"],
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
        enms = [
            ["ScanID"],
            ["ScanDir"],
            ["ScanDir", "ScanFile", "ConfigServer"],
            ["ScanDir", "ScanFile", "ConfigServer"],
            ["ScanDir", "ScanFile", "ConfigServer"],
            ["ScanDir", "ScanFile", "ConfigServer"],
            ["ScanDir", "ScanFile", "ConfigServer", "Bool", "Int", "Float",
             "Something", "Dict"],
            ["ScanDir", "ScanFile", "ConfigServer", "Bool", "Int", "Float",
             "Something", "Dict"],
        ]

        edats = [
            {},
            {"ScanDir": "/tmp"},
            {"ScanDir": "/tmp", "ScanFile": json.dumps(["file.nxs"])},
            {"ScanDir": "/tmp",
             "ScanFile": json.dumps(["file.nxs"]),
             "ConfigServer": "ptr/ert/ert"},
            {"ScanDir": "/tmp",
             "ScanFile": json.dumps(["file.nxs", "file2.nxs"]),
             "ConfigServer": "ptr/ert/ert"},
            {"ScanDir": "/tmp", "ScanFile": "file.nxs",
             "ConfigServer": "ptr/ert/ert"},
            {
                "ScanDir": "/tmp", "ScanFile": json.dumps(["file.nxs"]),
                "ConfigServer": "ptr/ert/ert",
                "Bool": True, "Int": 234, "Float": 123.123,
                "Something": json.dumps(["dgfg"]),
                "Dict": json.dumps({"dgfg": 123, "sdf": "345"}),
            },
            {
                "ScanDir": "/tmp", "ScanFile": json.dumps(["file.nxs"]),
                "ConfigServer": "ptr/ert/ert",
                "Bool": True, "Int": 234, "Float": 123.123,
                "Something": json.dumps(["dgfg"]),
                "Dict": json.dumps({"dgfg": 123, "sdf": "345"}),
            },
        ]

        msp = MacroServerPools(10)
        self.myAssertRaise(Exception, msp.getSelectorEnv, None, [], {})
        msp.getSelectorEnv(list(self._ms.door.keys())[0], [], {})
        for i, dt in enumerate(edats):
            data = {}
            self._ms.dps[list(self._ms.ms.keys())[0]].Environment = (
                'pickle', envs[i])
            msp.getSelectorEnv(list(self._ms.door.keys())[0], enms[i], data)
            self.myAssertDict(data, dt, ['Dict'])
            if 'Dict' in dt.keys():
                self.myAssertDict(
                    json.loads(data['Dict']), json.loads(dt['Dict']))

    # constructor test
    # \brief It tests default settings
    def test_setSelectorEnv(self):
        fun = sys._getframe().f_code.co_name
        print("Run: %s.%s() " % (self.__class__.__name__, fun))

        envs = [
            {
                "new": {'ScanID': 192,
                        'NeXusSelectorDevice': u'p09/nxsrecselector/1',
                        'ScanFile': [u'sar4r.nxs'],
                        'NeXusConfiguration': {},
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
                    'NeXusConfiguration': {},
                    'ActiveMntGrp': 'nxsmntgrp',
                    '_ViewOptions': {'ShowDial': True},
                    'DataCompressionRank': 0,
                    'ScanDir': '/tmp'}
            },
            {
                "new":
                {
                    'ScanID': 192,
                    'NeXusSelectorDevice': u'p09/nxsrecselector/1',
                    'NeXusConfiguration': {},
                    'ActiveMntGrp': 'nxsmntgrp',
                    '_ViewOptions': {'ShowDial': True},
                    'DataCompressionRank': 0,
                    "ScanDir": "/tmp",
                    "ScanFile": ["file.nxs"]
                }
            },
            {
                "new":
                {
                    "ScanDir": "/tmp",
                    'ScanID': 192,
                    'NeXusSelectorDevice': u'p09/nxsrecselector/1',
                    'NeXusConfiguration': {"ConfigServer": "ptr/ert/ert"},
                    'ActiveMntGrp': 'nxsmntgrp',
                    '_ViewOptions': {'ShowDial': True},
                    'DataCompressionRank': 0,
                    "ScanFile": ["file.nxs"],
                }
            },
            {
                "new":
                {
                    "ScanDir": "/tmp",
                    'ScanID': 192,
                    'NeXusSelectorDevice': u'p09/nxsrecselector/1',
                    'NeXusConfiguration': {"ConfigServer": "ptr/ert/ert2"},
                    'ActiveMntGrp': 'nxsmntgrp',
                    '_ViewOptions': {'ShowDial': True},
                    'DataCompressionRank': 0,
                    "ScanFile": ["file.nxs", "file2.nxs"],
                }
            },
            {
                "new":
                {
                    "ScanDir": "/tmp",
                    'ScanID': 192,
                    'NeXusSelectorDevice': u'p09/nxsrecselector/1',
                    'NeXusConfiguration': {"ConfigServer": "ptr/ert/ert"},
                    'ActiveMntGrp': 'nxsmntgrp',
                    '_ViewOptions': {'ShowDial': True},
                    'DataCompressionRank': 0,
                    "ScanFile": "file.nxs",
                }
            },
            {
                "new":
                {
                    "ScanDir": "/tmp",
                    'ScanID': 192,
                    'NeXusSelectorDevice': u'p09/nxsrecselector/1',
                    "NeXusConfiguration": {
                        "ConfigServer": 'ptr/ert/ert',
                        "Bool": True,
                        "Int": 234,
                        "Float": 123.123,
                        "Something": ["dgfg"],
                        "Dict": {"dgfg": 123, "sdf": "345"}},
                    'ActiveMntGrp': 'nxsmntgrp',
                    '_ViewOptions': {'ShowDial': True},
                    'DataCompressionRank': 0,
                    "ScanFile": ["file.nxs"],
                }
            },
            {
                "new":
                {
                    "ScanDir": "/tmp",
                    'ScanID': 192,
                    'NeXusSelectorDevice': u'p09/nxsrecselector/1',
                    "NeXusConfiguration": {
                        "ConfigServer": 'ptr/ert/ert',
                        "Bool": True,
                        "Int": 234,
                        "Float": 123.124,
                        "Something": ["dgfg"],
                        "Dict": {"dgfg": 123, "sdf": "345"}},
                    'ActiveMntGrp': 'nxsmntgrp',
                    '_ViewOptions': {'ShowDial': True},
                    'DataCompressionRank': 0,
                    "ScanFile": ["file.nxs"],
                }
            },
            {
                "new":
                {
                    "ScanDir": "/tmp",
                    'ScanID': 192,
                    'NeXusSelectorDevice': u'p09/nxsrecselector/1',
                    "NeXusConfiguration": {
                        "ConfigServer": 'ptr/ert/ert',
                        "Bool": True,
                        "Int": 234,
                        "Float": 123.124,
                        "Something": ["dgfg"],
                        "Dict": {"dgfg": 123, "sdf": "345"},
                        "CConfigServer": 'ptr/ert/ert',
                        "CBool": True,
                        "CInt": 234,
                        "CFloat": 123.124,
                        "CSomething": ["dgfg"],
                        "CDict": {"dgfg": 123, "sdf": "345"}
                    },
                    'ActiveMntGrp': 'nxsmntgrp',
                    '_ViewOptions': {'ShowDial': True},
                    'DataCompressionRank': 0,
                    "ScanFile": ["file.nxs"],
                }
            },
            {
                "new":
                {
                    "ScanDir": "/tmp",
                    'ScanID': 192,
                    'NeXusSelectorDevice': u'p09/nxsrecselector/1',
                    "NeXusConfiguration": {
                        "ConfigServer": 'ptr/ert/ert',
                        "Bool": True,
                        "Int": 234,
                        "Float": 123.124,
                        "Something": ["dgfg"],
                        "Dict": {"dgfg": 123, "sdf": "345"},
                        "CConfigServer": 'ptr/ert/ert',
                        "CBool": True,
                        "CInt": 234,
                        "CFloat": 123.124,
                        "CSomething": json.dumps(["dgfg"]),
                        "CDict": json.dumps({"dgfg": 123, "sdf": "345"})
                    },
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
            {"ScanDir": "/tmp", "ScanFile": json.dumps(["file.nxs"])},
            {"ScanDir": "/tmp", "ScanFile": json.dumps(["file.nxs"]),
             "ConfigServer": "ptr/ert/ert"},
            {"ScanDir": "/tmp",
             "ScanFile": json.dumps(["file.nxs", "file2.nxs"]),
             "ConfigServer": "ptr/ert/ert2"},
            {"ScanDir": "/tmp", "ScanFile": "file.nxs",
             "ConfigServer": "ptr/ert/ert"},
            {"ScanDir": "/tmp", "ScanFile": json.dumps(["file.nxs"]),
             "ConfigServer": "ptr/ert/ert",
             "Bool": True, "Int": 234, "Float": 123.123,
             "Something": json.dumps(["dgfg"]),
             "Dict": json.dumps({"dgfg": 123, "sdf": "345"}),
             },
            {"ScanDir": "/tmp", "ScanFile": ["file.nxs"],
             "ConfigServer": "ptr/ert/ert",
             "Bool": True, "Int": 234, "Float": 123.124, "Something": ["dgfg"],
             "Dict": {"dgfg": 123, "sdf": "345"},
             },
            {"ScanDir": "/tmp", "ScanFile": ["file.nxs"],
             "ConfigServer": "ptr/ert/ert",
             "Bool": True, "Int": 234, "Float": 123.124, "Something": ["dgfg"],
             "Dict": {"dgfg": 123, "sdf": "345"},
             },
            {"ScanDir": "/tmp", "ScanFile": ["file.nxs"],
             "ConfigServer": "ptr/ert/ert",
             "Bool": True, "Int": 234, "Float": 123.124, "Something": ["dgfg"],
             "Dict": {"dgfg": 123, "sdf": "345"},
             },
        ]

        cmds = [
            None, None, {}, None, None, None, None, None,
            {"CConfigServer": 'ptr/ert/ert',
             "CBool": True,
             "CInt": 234,
             "CFloat": 123.124,
             "CSomething": ["dgfg"],
             "CDict": {"dgfg": 123, "sdf": "345"}},
            {"CConfigServer": 'ptr/ert/ert',
             "CBool": True,
             "CInt": 234,
             "CFloat": 123.124,
             "CSomething": json.dumps(["dgfg"]),
             "CDict": json.dumps({"dgfg": 123, "sdf": "345"})},
        ]

        msp = MacroServerPools(10)
        self.myAssertRaise(Exception, msp.setSelectorEnv, None, {})
        self.myAssertRaise(Exception, msp.setSelectorEnv, None, {}, {})
        msp.setSelectorEnv(list(self._ms.door.keys())[0], {})
        msp.setSelectorEnv(list(self._ms.door.keys())[0], {}, {})
        for i, dt in enumerate(edats):
            msp.setSelectorEnv(list(self._ms.door.keys())[0], dt, cmds[i])
#            print "I = ",i
            # data = {}
            env = pickle.loads(
                self._ms.dps[list(self._ms.ms.keys())[0]].Environment[1])
#            print "env", env
#            print "ei", envs[i]
            self.myAssertDict(envs[i], env)

    # constructor test
    # \brief It tests default settings
    def test_getScanEnv(self):
        fun = sys._getframe().f_code.co_name
        print("Run: %s.%s() " % (self.__class__.__name__, fun))

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
                    "new":
                    {
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
                    "new":
                    {
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
                    "new":
                    {
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

        msp = MacroServerPools(10)
        self.myAssertRaise(Exception, msp.getScanEnv, None)
        data = {"ScanID": 192,
                "NeXusSelectorDevice": "p09/nxsrecselector/1",
                "ScanFile": ["sar4r.nxs"], "ScanDir": "/tmp/"}
        res = msp.getScanEnv(list(self._ms.door.keys())[0])
        self.myAssertDict(json.loads(res), data)
        dwt = msp.getScanEnv(list(self._ms.door.keys())[0])
        for i, dt in enumerate(edats):
            data = {}
            edl = list(json.loads(dwt).keys())
            self._ms.dps[list(self._ms.ms.keys())[0]].Environment = (
                'pickle', pickle.dumps({"del": edl}, protocol=2))
            self._ms.dps[list(self._ms.ms.keys())[0]].Environment = (
                'pickle', envs[i])
            dt = msp.getScanEnv(list(self._ms.door.keys())[0])
            dwt = msp.getScanEnv(list(self._ms.door.keys())[0])
            self.myAssertDict(edats[i], json.loads(dt))

    # constructor test
    # \brief It tests default settings
    def test_setScanEnv(self):
        fun = sys._getframe().f_code.co_name
        print("Run: %s.%s() " % (self.__class__.__name__, fun))

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
                "new":
                {
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
                "new":
                {
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
                "new":
                {
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
                "new":
                {
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
                "new":
                {
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
                "new":
                {
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
                "new":
                {
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
                "new":
                {
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

        msp = MacroServerPools(10)
        self.myAssertRaise(Exception, msp.setScanEnv, None, "{}")
        msp.setScanEnv(list(self._ms.door.keys())[0], "{}")
        for i, dt in enumerate(edats):
            sid = msp.setScanEnv(list(self._ms.door.keys())[0], json.dumps(dt))
            # print "I = ", i, sid
            self.assertEqual(sid, sids[i])
            # data = {}
            env = pickle.loads(
                self._ms.dps[list(self._ms.ms.keys())[0]].Environment[1])
#            print "env", env
#            print "ei", envs[i]
            self.myAssertDict(envs[i], env)

    # constructor test
    # \brief It tests default settings
    def test_setScanEnv_scanid(self):
        fun = sys._getframe().f_code.co_name
        print("Run: %s.%s() " % (self.__class__.__name__, fun))

        envs = [
            pickle.dumps(
                {"new": {}}, protocol=2
            ),
            pickle.dumps(
                {"new": {"ScanID": 12}}, protocol=2
            )
        ]

        msp = MacroServerPools(10)
        self.myAssertRaise(Exception, msp.setScanEnv, None, "{}")
        self.assertEqual(
            msp.setScanEnv(list(self._ms.door.keys())[0], "{}"), 192)
        self._ms.dps[
            list(self._ms.ms.keys())[0]].Environment = ('pickle', envs[0])
        self.assertEqual(
            msp.setScanEnv(list(self._ms.door.keys())[0], "{}"), 192)
        self._ms.dps[list(self._ms.ms.keys())[0]].Environment = (
            'pickle', pickle.dumps({"del": ["ScanID"]}, protocol=2))
        self._ms.dps[
            list(self._ms.ms.keys())[0]].Environment = ('pickle', envs[0])
        self.assertEqual(
            msp.setScanEnv(list(self._ms.door.keys())[0], "{}"), -1)
        self._ms.dps[
            list(self._ms.ms.keys())[0]].Environment = (
            'pickle', pickle.dumps({"del": ["ScanID"]}, protocol=2))
        self.assertEqual(
            msp.setScanEnv(list(self._ms.door.keys())[0], "{}"), -1)
        self._ms.dps[
            list(self._ms.ms.keys())[0]].Environment = ('pickle', envs[0])
        self.assertEqual(
            msp.setScanEnv(list(self._ms.door.keys())[0], "{}"), -1)
        self._ms.dps[
            list(self._ms.ms.keys())[0]].Environment = ('pickle', envs[1])
        self.assertEqual(
            msp.setScanEnv(list(self._ms.door.keys())[0], "{}"), 12)

    # constructor test
    # \brief It tests default settings
    def test_setScanEnv2(self):
        fun = sys._getframe().f_code.co_name
        print("Run: %s.%s() " % (self.__class__.__name__, fun))

        envs = [
            {
                "new": {
                    'ScanID': 192,
                    'NeXusSelectorDevice': u'p09/nxsrecselector/1',
                    'ScanFile': [u'sar4r.nxs'],
                    'ActiveMntGrp': 'nxsmntgrp',
                    '_ViewOptions': {'ShowDial': True},
                    'DataCompressionRank': 0,
                    'ScanDir': '/tmp/'
                }
            },
            {
                "new":
                {
                    'ScanID': 192,
                    'NeXusSelectorDevice': u'p09/nxsrecselector/1',
                    'ScanFile': [u'sar4r.nxs'],
                    'ActiveMntGrp': 'nxsmntgrp',
                    '_ViewOptions': {'ShowDial': True},
                    'DataCompressionRank': 0,
                    'ScanDir': '/tmp'
                }
            },
            {
                "new":
                {
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
                "new":
                {
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
                "new":
                {
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
                "new":
                {
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
                "new":
                {
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
                "new":
                {
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
                "new":
                {
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

        msp = MacroServerPools(10)
        self.myAssertRaise(Exception, msp.setScanEnv, None, "{}")
        msp.setScanEnv(list(self._ms.door.keys())[0], "{}")
        for i, dt in enumerate(edats):
            sid = msp.setScanEnv(list(self._ms.door.keys())[0], json.dumps(dt))
            # print "I = ", i, sid
            self.assertEqual(sid, sids[i])
            # data = {}
            env = pickle.loads(
                self._ms.dps[list(self._ms.ms.keys())[0]].Environment[1])
            self.myAssertDict(envs[i], env)

    # constructor test
    # \brief It tests default settings
    def test_setScanEnv_dtlist(self):
        fun = sys._getframe().f_code.co_name
        print("Run: %s.%s() " % (self.__class__.__name__, fun))

        envs = [
            {
                "new": {'ScanID': 192,
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
                    'ScanID': "11",
                    'NeXusSelectorDevice': u'p09/nxsrecselector/1',
                    'ActiveMntGrp': 'nxsmntgrp',
                    '_ViewOptions': {'ShowDial': True},
                    'DataCompressionRank': 0,
                    "ScanDir": "/tmp",
                    "ScanFile": "file.nxs"
                }
            },
            {
                "new": {
                    "ScanDir": "/tmp",
                    'ScanID': "11",
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
                    'ScanID': '13',
                    'NeXusSelectorDevice': u'p09/nxsrecselector/1',
                    "ConfigServer": "ptr/ert/ert2",
                    'ActiveMntGrp': 'nxsmntgrp',
                    '_ViewOptions': {'ShowDial': True},
                    'DataCompressionRank': 0,
                    "ScanFile": "file.nxs",
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
        ]

        edats = [
            "",
            "ScanDir /tmp",
            "ScanDir:/tmp, ScanFile:file.nxs, ScanID: 11",
            "ScanDir /tmp, ScanFile:file.nxs,ConfigServer ptr/ert/ert",
            "ScanDir:/tmp, ScanFile:file.nxs  ConfigServer:ptr/ert/ert2, "
            "ScanID: 13",
            {"ScanDir": "/tmp", "ScanFile": "file.nxs",
             "ConfigServer": "ptr/ert/ert", "ScanID": 13},
            {"ScanDir": "/tmp", "ScanFile": ["file.nxs"],
             "ConfigServer": "ptr/ert/ert", "ScanID": 15,
             "Bool": True, "Int": 234, "Float": 123.123, "Something": ["dgfg"],
             "Dict": {"dgfg": 123, "sdf": "345"},
             },
        ]

        sids = [192, 192, 11, 11, 13, 13, 15, 15, 17, 17]

        msp = MacroServerPools(10)
        self.myAssertRaise(Exception, msp.setScanEnv, None, "{}")
        msp.setScanEnv(list(self._ms.door.keys())[0], "{}")
        for i, dt in enumerate(edats):
            env = pickle.loads(
                self._ms.dps[list(self._ms.ms.keys())[0]].Environment[1])
            # print "env0", env
            sid = msp.setScanEnv(
                list(self._ms.door.keys())[0],
                dt if not isinstance(dt, dict) else json.dumps(dt))
            # print "I = ", i, sid
            self.assertEqual(sid, sids[i])
            # data = {}
            env = pickle.loads(
                self._ms.dps[list(self._ms.ms.keys())[0]].Environment[1])
            # print "env", env
            # print "ei", envs[i]
            self.myAssertDict(envs[i], env)


if __name__ == '__main__':
    unittest.main()
