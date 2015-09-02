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
## \file MacroServerPoolTest.py
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

import logging
logger = logging.getLogger()

import TestMacroServerSetUp
import TestPoolSetUp
import TestServerSetUp
import TestConfigServerSetUp


from nxsrecconfig.MacroServerPools import MacroServerPools


## if 64-bit machione
IS64BIT = (struct.calcsize("P") == 8)




## test fixture
class MacroServerPoolTest(unittest.TestCase):

    ## constructor
    # \param methodName name of the test method
    def __init__(self, methodName):
        unittest.TestCase.__init__(self, methodName)


        self._bint = "int64" if IS64BIT else "int32"
        self._buint = "uint64" if IS64BIT else "uint32"
        self._bfloat = "float64" if IS64BIT else "float32"

        self._ms = TestMacroServerSetUp.TestMacroServerSetUp()
        self._cf = TestConfigServerSetUp.TestConfigServerSetUp()
        self._pool = TestPoolSetUp.TestPoolSetUp()
#        self._ms2 = TestMacroServerSetUp.TestMacroServerSetUp("mstestp09/testts/t2r228", "MSTESTS2")
        self._simps = TestServerSetUp.TestServerSetUp()
#        self._simps2 = TestServerSetUp.TestServerSetUp( "ttestp09/testts/t2r228", "S2")
 #       self._simps3 = TestServerSetUp.TestServerSetUp( "ttestp09/testts/t3r228", "S3") 
 #       self._simps4 = TestServerSetUp.TestServerSetUp( "ttestp09/testts/t4r228", "S4")
 #       self._simpsoff = TestServerSetUp.TestServerSetUp( "ttestp09/testts/t5r228", "OFF")


        try:
            self.__seed  = long(binascii.hexlify(os.urandom(16)), 16)
        except NotImplementedError:
            self.__seed  = long(time.time() * 256) 
         
        self.__rnd = random.Random(self.__seed)


        self.mycps = {
            'mycp' : (
                '<?xml version=\'1.0\'?>'
                '<definition>'
                '<group type="NXcollection" name="dddd"/>'
                '</definition>'),
            'mycp2' : (
                '<definition><group type="NXcollection" name="dddd">'
                '<field><datasource type="TANGO" name="ann" /></field>'
                '</group></definition>'),
            'mycp3' : (
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

        self.smycps ={
            'smycp' : (
                '<definition><group type="NXcollection" name="dddd">'
                '<field name="long">$datasources.scalar_long<strategy mode="STEP"/></field>'
                '<field name="short">$datasources.scalar_short<strategy mode="STEP"/></field>'
                '</group></definition>'),
            'smycp2' : (
                '<definition><group type="NXcollection" name="dddd">'
                '<field name="long">$datasources.spectrum_long<strategy mode="INIT"/></field>'
                '<field name="short">$datasources.spectrum_short<strategy mode="STEP"/></field>'
                '</group></definition>'),
            'smycp3' : (
                '<definition><group type="NXcollection" name="dddd">'
                '<field name="long">$datasources.image_long<strategy mode="FINAL"/></field>'
                '<field name="short">$datasources.image_short<strategy mode="STEP"/></field>'
                '</group></definition>'),
            'smycpnt1' : (
                '<definition><group type="NXcollection" name="ddddnt">'
                '<field name="long">$datasources.client_long<strategy mode="FINAL"/></field>'
                '<field name="short">$datasources.client_short<strategy mode="STEP"/></field>'
                '</group></definition>'),
            }

        self.smycps2 ={
            's2mycp' : (
                '<definition><group type="NXcollection" name="dddd2">'
                '<field name="long">$datasources.scalar2_long<strategy mode="STEP"/></field>'
                '<field name="short">$datasources.scalar2_short<strategy mode="STEP"/></field>'
                '</group></definition>'),
            's2mycp2' : (
                '<definition><group type="NXcollection" name="dddd2">'
                '<field name="long">$datasources.spectrum2_long<strategy mode="STEP"/></field>'
                '<field name="short">$datasources.spectrum2_short<strategy mode="FINAL"/></field>'
                '</group></definition>'),
            's2mycp3' : (
                '<definition><group type="NXcollection" name="dddd2">'
                '<field name="long">$datasources.image2_long<strategy mode="STEP"/></field>'
                '<field name="short">$datasources.image2_short<strategy mode="INIT"/></field>'
                '</group></definition>'),
            's2mycpnt1' : (
                '<definition><group type="NXcollection" name="dddd2nt">'
                '<field name="long">$datasources.client2_long<strategy mode="FINAL"/></field>'
                '<field name="short">$datasources.client2_short<strategy mode="STEP"/></field>'
                '</group></definition>'),
            }
            
        self.smydss = {
            'scalar_long': ('<definition><datasource type="TANGO" name="scalar_long">'
                     '<record name="ScalarLong"/>'
                     '<device member="attribute" name="ttestp09/testts/t1r228"/>'
                     '</datasource></definition>'),
            'scalar_bool': ('<definition><datasource type="TANGO" name="scalar_bool">'
                     '<record name="ScalarBoolean"/>'
                     '<device member="attribute" name="ttestp09/testts/t1r228"/>'
                     '</datasource></definition>'),
            'scalar_short': ('<definition><datasource type="TANGO" name="scalar_short">'
                     '<record name="ScalarShort"/>'
                     '<device member="attribute" name="ttestp09/testts/t1r228"/>'
                     '</datasource></definition>'),
            'scalar_ushort': ('<definition><datasource type="TANGO" name="scalar_ushort">'
                     '<record name="ScalarUShort"/>'
                     '<device member="attribute" name="ttestp09/testts/t1r228"/>'
                     '</datasource></definition>'),
            'scalar_ulong': ('<definition><datasource type="TANGO" name="scalar_ulong">'
                     '<record name="ScalarULong"/>'
                     '<device member="attribute" name="ttestp09/testts/t1r228"/>'
                     '</datasource></definition>'),
            'scalar_long64': ('<definition><datasource type="TANGO" name="scalar_long64">'
                     '<record name="ScalarLong64"/>'
                     '<device member="attribute" name="ttestp09/testts/t1r228"/>'
                     '</datasource></definition>'),
            'scalar_ulong64': ('<definition><datasource type="TANGO" name="scalar_ulong64">'
                     '<record name="ScalarULong64"/>'
                     '<device member="attribute" name="ttestp09/testts/t1r228"/>'
                     '</datasource></definition>'),
            'scalar_float': ('<definition><datasource type="TANGO" name="scalar_float">'
                     '<record name="ScalarFloat"/>'
                     '<device member="attribute" name="ttestp09/testts/t1r228"/>'
                     '</datasource></definition>'),
            'scalar_double': ('<definition><datasource type="TANGO" name="scalar_double">'
                     '<record name="ScalarDouble"/>'
                     '<device member="attribute" name="ttestp09/testts/t1r228"/>'
                     '</datasource></definition>'),
            'scalar_string': ('<definition><datasource type="TANGO" name="scalar_string">'
                     '<record name="ScalarString"/>'
                     '<device member="attribute" name="ttestp09/testts/t1r228"/>'
                     '</datasource></definition>'),
            'scalar_Encoded': ('<definition><datasource type="TANGO" name="scalar_encoded">'
                     '<record name="ScalarEncoded"/>'
                     '<device member="attribute" name="ttestp09/testts/t1r228"/>'
                     '</datasource></definition>'),
            'scalar_uchar': ('<definition><datasource type="TANGO" name="scalar_uchar">'
                     '<record name="ScalarUChar"/>'
                     '<device member="attribute" name="ttestp09/testts/t1r228"/>'
                     '</datasource></definition>'),
            'spectrum_long': ('<definition><datasource type="TANGO" name="spectrum_long">'
                     '<record name="SpectrumLong"/>'
                     '<device member="attribute" name="ttestp09/testts/t1r228"/>'
                     '</datasource></definition>'),
            'spectrum_bool': ('<definition><datasource type="TANGO" name="spectrum_bool">'
                     '<record name="SpectrumBoolean"/>'
                     '<device member="attribute" name="ttestp09/testts/t1r228"/>'
                     '</datasource></definition>'),
            'spectrum_short': ('<definition><datasource type="TANGO" name="spectrum_short">'
                     '<record name="SpectrumShort"/>'
                     '<device member="attribute" name="ttestp09/testts/t1r228"/>'
                     '</datasource></definition>'),
            'spectrum_ushort': ('<definition><datasource type="TANGO" name="spectrum_ushort">'
                     '<record name="SpectrumUShort"/>'
                     '<device member="attribute" name="ttestp09/testts/t1r228"/>'
                     '</datasource></definition>'),
            'spectrum_ulong': ('<definition><datasource type="TANGO" name="spectrum_ulong">'
                     '<record name="SpectrumULong"/>'
                     '<device member="attribute" name="ttestp09/testts/t1r228"/>'
                     '</datasource></definition>'),
            'spectrum_long64': ('<definition><datasource type="TANGO" name="spectrum_long64">'
                     '<record name="SpectrumLong64"/>'
                     '<device member="attribute" name="ttestp09/testts/t1r228"/>'
                     '</datasource></definition>'),
            'spectrum_ulong64': ('<definition><datasource type="TANGO" name="spectrum_ulong64">'
                     '<record name="SpectrumULong64"/>'
                     '<device member="attribute" name="ttestp09/testts/t1r228"/>'
                     '</datasource></definition>'),
            'spectrum_float': ('<definition><datasource type="TANGO" name="spectrum_float">'
                     '<record name="SpectrumFloat"/>'
                     '<device member="attribute" name="ttestp09/testts/t1r228"/>'
                     '</datasource></definition>'),
            'spectrum_double': ('<definition><datasource type="TANGO" name="spectrum_double">'
                     '<record name="SpectrumDouble"/>'
                     '<device member="attribute" name="ttestp09/testts/t1r228"/>'
                     '</datasource></definition>'),
            'spectrum_string': ('<definition><datasource type="TANGO" name="spectrum_string">'
                     '<record name="SpectrumString"/>'
                     '<device member="attribute" name="ttestp09/testts/t1r228"/>'
                     '</datasource></definition>'),
            'spectrum_Encoded': ('<definition><datasource type="TANGO" name="spectrum_encoded">'
                     '<record name="SpectrumEncoded"/>'
                     '<device member="attribute" name="ttestp09/testts/t1r228"/>'
                     '</datasource></definition>'),
            'spectrum_uchar': ('<definition><datasource type="TANGO" name="spectrum_uchar">'
                     '<record name="SpectrumUChar"/>'
                     '<device member="attribute" name="ttestp09/testts/t1r228"/>'
                     '</datasource></definition>'),
            'image_long': ('<definition><datasource type="TANGO" name="image_long">'
                     '<record name="ImageLong"/>'
                     '<device member="attribute" name="ttestp09/testts/t1r228"/>'
                     '</datasource></definition>'),
            'image_bool': ('<definition><datasource type="TANGO" name="image_bool">'
                     '<record name="ImageBoolean"/>'
                     '<device member="attribute" name="ttestp09/testts/t1r228"/>'
                     '</datasource></definition>'),
            'image_short': ('<definition><datasource type="TANGO" name="image_short">'
                     '<record name="ImageShort"/>'
                     '<device member="attribute" name="ttestp09/testts/t1r228"/>'
                     '</datasource></definition>'),
            'image_ushort': ('<definition><datasource type="TANGO" name="image_ushort">'
                     '<record name="ImageUShort"/>'
                     '<device member="attribute" name="ttestp09/testts/t1r228"/>'
                     '</datasource></definition>'),
            'image_ulong': ('<definition><datasource type="TANGO" name="image_ulong">'
                     '<record name="ImageULong"/>'
                     '<device member="attribute" name="ttestp09/testts/t1r228"/>'
                     '</datasource></definition>'),
            'image_long64': ('<definition><datasource type="TANGO" name="image_long64">'
                     '<record name="ImageLong64"/>'
                     '<device member="attribute" name="ttestp09/testts/t1r228"/>'
                     '</datasource></definition>'),
            'image_ulong64': ('<definition><datasource type="TANGO" name="image_ulong64">'
                     '<record name="ImageULong64"/>'
                     '<device member="attribute" name="ttestp09/testts/t1r228"/>'
                     '</datasource></definition>'),
            'image_float': ('<definition><datasource type="TANGO" name="image_float">'
                     '<record name="ImageFloat"/>'
                     '<device member="attribute" name="ttestp09/testts/t1r228"/>'
                     '</datasource></definition>'),
            'image_double': ('<definition><datasource type="TANGO" name="image_double">'
                     '<record name="ImageDouble"/>'
                     '<device member="attribute" name="ttestp09/testts/t1r228"/>'
                     '</datasource></definition>'),
            'image_string': ('<definition><datasource type="TANGO" name="image_string">'
                     '<record name="ImageString"/>'
                     '<device member="attribute" name="ttestp09/testts/t1r228"/>'
                     '</datasource></definition>'),
            'image_Encoded': ('<definition><datasource type="TANGO" name="image_encoded">'
                     '<record name="ImageEncoded"/>'
                     '<device member="attribute" name="ttestp09/testts/t1r228"/>'
                     '</datasource></definition>'),
            'image_uchar': ('<definition><datasource type="TANGO" name="image_uchar">'
                     '<record name="ImageUChar"/>'
                     '<device member="attribute" name="ttestp09/testts/t1r228"/>'
                     '</datasource></definition>'),
            'client_long': ('<definition><datasource type="CLIENT" name="client_long">'
                     '<record name="ClientLong"/>'
                     '</datasource></definition>'),
            'client_short': ('<definition><datasource type="CLIENT" name="client_short">'
                     '<record name="ClientShort"/>'
                     '</datasource></definition>'),
            }


        self.smydss2 = {
            'scalar2_long': ('<definition><datasource type="TANGO" name="scalar2_long">'
                     '<record name="ScalarLong"/>'
                     '<device member="attribute" name="ttestp09/testts/t2r228"/>'
                     '</datasource></definition>'),
            'scalar2_bool': ('<definition><datasource type="TANGO" name="scalar2_bool">'
                     '<record name="ScalarBoolean"/>'
                     '<device member="attribute" name="ttestp09/testts/t2r228"/>'
                     '</datasource></definition>'),
            'scalar2_short': ('<definition><datasource type="TANGO" name="scalar2_short">'
                     '<record name="ScalarShort"/>'
                     '<device member="attribute" name="ttestp09/testts/t2r228"/>'
                     '</datasource></definition>'),
            'scalar2_ushort': ('<definition><datasource type="TANGO" name="scalar2_ushort">'
                     '<record name="ScalarUShort"/>'
                     '<device member="attribute" name="ttestp09/testts/t2r228"/>'
                     '</datasource></definition>'),
            'scalar2_ulong': ('<definition><datasource type="TANGO" name="scalar2_ulong">'
                     '<record name="ScalarULong"/>'
                     '<device member="attribute" name="ttestp09/testts/t2r228"/>'
                     '</datasource></definition>'),
            'scalar2_long64': ('<definition><datasource type="TANGO" name="scalar2_long64">'
                     '<record name="ScalarLong64"/>'
                     '<device member="attribute" name="ttestp09/testts/t2r228"/>'
                     '</datasource></definition>'),
            'scalar2_ulong64': ('<definition><datasource type="TANGO" name="scalar2_ulong64">'
                     '<record name="ScalarULong64"/>'
                     '<device member="attribute" name="ttestp09/testts/t2r228"/>'
                     '</datasource></definition>'),
            'scalar2_float': ('<definition><datasource type="TANGO" name="scalar2_float">'
                     '<record name="ScalarFloat"/>'
                     '<device member="attribute" name="ttestp09/testts/t2r228"/>'
                     '</datasource></definition>'),
            'scalar2_double': ('<definition><datasource type="TANGO" name="scalar2_double">'
                     '<record name="ScalarDouble"/>'
                     '<device member="attribute" name="ttestp09/testts/t2r228"/>'
                     '</datasource></definition>'),
            'scalar2_string': ('<definition><datasource type="TANGO" name="scalar2_string">'
                     '<record name="ScalarString"/>'
                     '<device member="attribute" name="ttestp09/testts/t2r228"/>'
                     '</datasource></definition>'),
            'scalar2_Encoded': ('<definition><datasource type="TANGO" name="scalar2_encoded">'
                     '<record name="ScalarEncoded"/>'
                     '<device member="attribute" name="ttestp09/testts/t2r228"/>'
                     '</datasource></definition>'),
            'scalar2_uchar': ('<definition><datasource type="TANGO" name="scalar2_uchar">'
                     '<record name="ScalarUChar"/>'
                     '<device member="attribute" name="ttestp09/testts/t2r228"/>'
                     '</datasource></definition>'),
            'spectrum2_long': ('<definition><datasource type="TANGO" name="spectrum2_long">'
                     '<record name="SpectrumLong"/>'
                     '<device member="attribute" name="ttestp09/testts/t2r228"/>'
                     '</datasource></definition>'),
            'spectrum2_bool': ('<definition><datasource type="TANGO" name="spectrum2_bool">'
                     '<record name="SpectrumBoolean"/>'
                     '<device member="attribute" name="ttestp09/testts/t2r228"/>'
                     '</datasource></definition>'),
            'spectrum2_short': ('<definition><datasource type="TANGO" name="spectrum2_short">'
                     '<record name="SpectrumShort"/>'
                     '<device member="attribute" name="ttestp09/testts/t2r228"/>'
                     '</datasource></definition>'),
            'spectrum2_ushort': ('<definition><datasource type="TANGO" name="spectrum2_ushort">'
                     '<record name="SpectrumUShort"/>'
                     '<device member="attribute" name="ttestp09/testts/t2r228"/>'
                     '</datasource></definition>'),
            'spectrum2_ulong': ('<definition><datasource type="TANGO" name="spectrum2_ulong">'
                     '<record name="SpectrumULong"/>'
                     '<device member="attribute" name="ttestp09/testts/t2r228"/>'
                     '</datasource></definition>'),
            'spectrum2_long64': ('<definition><datasource type="TANGO" name="spectrum2_long64">'
                     '<record name="SpectrumLong64"/>'
                     '<device member="attribute" name="ttestp09/testts/t2r228"/>'
                     '</datasource></definition>'),
            'spectrum2_ulong64': ('<definition><datasource type="TANGO" name="spectrum2_ulong64">'
                     '<record name="SpectrumULong64"/>'
                     '<device member="attribute" name="ttestp09/testts/t2r228"/>'
                     '</datasource></definition>'),
            'spectrum2_float': ('<definition><datasource type="TANGO" name="spectrum2_float">'
                     '<record name="SpectrumFloat"/>'
                     '<device member="attribute" name="ttestp09/testts/t2r228"/>'
                     '</datasource></definition>'),
            'spectrum2_double': ('<definition><datasource type="TANGO" name="spectrum2_double">'
                     '<record name="SpectrumDouble"/>'
                     '<device member="attribute" name="ttestp09/testts/t2r228"/>'
                     '</datasource></definition>'),
            'spectrum2_string': ('<definition><datasource type="TANGO" name="spectrum2_string">'
                     '<record name="SpectrumString"/>'
                     '<device member="attribute" name="ttestp09/testts/t2r228"/>'
                     '</datasource></definition>'),
            'spectrum2_Encoded': ('<definition><datasource type="TANGO" name="spectrum2_encoded">'
                     '<record name="SpectrumEncoded"/>'
                     '<device member="attribute" name="ttestp09/testts/t2r228"/>'
                     '</datasource></definition>'),
            'spectrum2_uchar': ('<definition><datasource type="TANGO" name="spectrum2_uchar">'
                     '<record name="SpectrumUChar"/>'
                     '<device member="attribute" name="ttestp09/testts/t2r228"/>'
                     '</datasource></definition>'),
            'image2_long': ('<definition><datasource type="TANGO" name="image2_long">'
                     '<record name="ImageLong"/>'
                     '<device member="attribute" name="ttestp09/testts/t2r228"/>'
                     '</datasource></definition>'),
            'image2_bool': ('<definition><datasource type="TANGO" name="image2_bool">'
                     '<record name="ImageBoolean"/>'
                     '<device member="attribute" name="ttestp09/testts/t2r228"/>'
                     '</datasource></definition>'),
            'image2_short': ('<definition><datasource type="TANGO" name="image2_short">'
                     '<record name="ImageShort"/>'
                     '<device member="attribute" name="ttestp09/testts/t2r228"/>'
                     '</datasource></definition>'),
            'image2_ushort': ('<definition><datasource type="TANGO" name="image2_ushort">'
                     '<record name="ImageUShort"/>'
                     '<device member="attribute" name="ttestp09/testts/t2r228"/>'
                     '</datasource></definition>'),
            'image2_ulong': ('<definition><datasource type="TANGO" name="image2_ulong">'
                     '<record name="ImageULong"/>'
                     '<device member="attribute" name="ttestp09/testts/t2r228"/>'
                     '</datasource></definition>'),
            'image2_long64': ('<definition><datasource type="TANGO" name="image2_long64">'
                     '<record name="ImageLong64"/>'
                     '<device member="attribute" name="ttestp09/testts/t2r228"/>'
                     '</datasource></definition>'),
            'image2_ulong64': ('<definition><datasource type="TANGO" name="image2_ulong64">'
                     '<record name="ImageULong64"/>'
                     '<device member="attribute" name="ttestp09/testts/t2r228"/>'
                     '</datasource></definition>'),
            'image2_float': ('<definition><datasource type="TANGO" name="image2_float">'
                     '<record name="ImageFloat"/>'
                     '<device member="attribute" name="ttestp09/testts/t2r228"/>'
                     '</datasource></definition>'),
            'image2_double': ('<definition><datasource type="TANGO" name="image2_double">'
                     '<record name="ImageDouble"/>'
                     '<device member="attribute" name="ttestp09/testts/t2r228"/>'
                     '</datasource></definition>'),
            'image2_string': ('<definition><datasource type="TANGO" name="image2_string">'
                     '<record name="ImageString"/>'
                     '<device member="attribute" name="ttestp09/testts/t2r228"/>'
                     '</datasource></definition>'),
            'image2_Encoded': ('<definition><datasource type="TANGO" name="image2_encoded">'
                     '<record name="ImageEncoded"/>'
                     '<device member="attribute" name="ttestp09/testts/t2r228"/>'
                     '</datasource></definition>'),
            'image2_uchar': ('<definition><datasource type="TANGO" name="image2_uchar">'
                     '<record name="ImageUChar"/>'
                     '<device member="attribute" name="ttestp09/testts/t2r228"/>'
                     '</datasource></definition>'),
            'client2_long': ('<definition><datasource type="CLIENT" name="client2_long">'
                     '<record name="Client2Long"/>'
                     '</datasource></definition>'),
            'client2_short': ('<definition><datasource type="CLIENT" name="client2_short">'
                     '<record name="Client2Short"/>'
                     '</datasource></definition>'),
            }

        self.mydss = {
            'nn': ('<?xml version=\'1.0\'?><definition><datasource type="TANGO">'
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
 
    ## Exception tester
    # \param exception expected exception
    # \param method called method      
    # \param args list with method arguments
    # \param kwargs dictionary with method arguments
    def myAssertRaise(self, exception, method, *args, **kwargs):
        err = None
        try:
            error =  False
            method(*args, **kwargs)
        except exception, e:
            error = True
            err = e
        self.assertEqual(error, True)
        return err


    def myAssertDict(self, dct, dct2):
        logger.debug('dict %s' % type(dct))
        logger.debug("\n%s\n%s" % ( dct, dct2))
        self.assertTrue(isinstance(dct, dict))
        self.assertTrue(isinstance(dct2, dict))
        logger.debug("%s %s" %(len(dct.keys()), len(dct2.keys())))
        self.assertEqual(len(dct.keys()), len(dct2.keys()))
        for k,v in dct.items():
            logger.debug("%s  in %s" %(str(k), str(dct2.keys())))
            self.assertTrue(k in dct2.keys())
            if isinstance(v, dict):
                self.myAssertDict(v, dct2[k])
            else:
                logger.debug("%s , %s" %(str(v), str(dct2[k])))
                self.assertEqual(v, dct2[k])


    ## constructor test
    # \brief It tests default settings
    def ttest_constructor(self):
        fun = sys._getframe().f_code.co_name
        print "Run: %s.%s() " % (self.__class__.__name__, fun)
        msp = MacroServerPools(0)
        msp = MacroServerPools(10)

    ## constructor test
    # \brief It tests default settings
    def ttest_getMacroServer(self):
        fun = sys._getframe().f_code.co_name
        print "Run: %s.%s() " % (self.__class__.__name__, fun)
        msp = MacroServerPools(0)
        msp = MacroServerPools(10)
        self.myAssertRaise(Exception, msp.updateMacroServer, "sfdsTESTdfdf/sdfsdf/sdffsf")
        self.myAssertRaise(Exception, msp.updateMacroServer, "")
        self.myAssertRaise(Exception, msp.getMacroServer, "")
        self.myAssertRaise(Exception, msp.getPools, "")

        msp.updateMacroServer(self._ms.door.keys()[0])
        self.assertEqual(msp.getMacroServer(""),self._ms.ms.keys()[0])
        self.assertEqual(msp.getMacroServer(self._ms.door.keys()[0]),self._ms.ms.keys()[0])
        self.assertEqual(msp.getPools(self._ms.door.keys()[0]), [])
        self.myAssertRaise(Exception, msp.getPools, "")

        self.myAssertRaise(Exception, msp.updateMacroServer, "sfdsTESTdfdf/sdfsdf/sdffsf")
        self.myAssertRaise(Exception, msp.updateMacroServer, "")
        self.myAssertRaise(Exception, msp.getMacroServer, "")
        self.myAssertRaise(Exception, msp.getPools, "")

        self.assertEqual(msp.getPools(self._ms.door.keys()[0]), [])

        self._ms.dps[self._ms.ms.keys()[0]].DoorList = []
        self.myAssertRaise(Exception, msp.updateMacroServer, self._ms.door.keys()[0])
        self.myAssertRaise(Exception, msp.getMacroServer, "")
        self.myAssertRaise(Exception, msp.getPools, self._ms.door.keys()[0])


    ## constructor test
    # \brief It tests default settings
    def ttest_getPool(self):
        fun = sys._getframe().f_code.co_name
        print "Run: %s.%s() " % (self.__class__.__name__, fun)
        msp = MacroServerPools(10)
        db = PyTango.Database()
        db.put_device_property(self._ms.ms.keys()[0], {'PoolNames':self._pool.dp.name()})
        self._ms.dps[self._ms.ms.keys()[0]].Init()

        self.myAssertRaise(Exception, msp.updateMacroServer, "sfdsTESTdfdf/sdfsdf/sdffsf")
        self.myAssertRaise(Exception, msp.updateMacroServer, "")
        self.myAssertRaise(Exception, msp.getMacroServer, "")
        self.myAssertRaise(Exception, msp.getPools, "")

        msp.updateMacroServer(self._ms.door.keys()[0])
        self.assertEqual(msp.getMacroServer(""), self._ms.ms.keys()[0])
        self.assertEqual(msp.getMacroServer(self._ms.door.keys()[0]),self._ms.ms.keys()[0])
        pools = msp.getPools(self._ms.door.keys()[0])
        self.assertEqual(len(pools), 1)
        self.assertTrue(isinstance(pools[0], PyTango.DeviceProxy))
        self.assertEqual(pools[0].name(), self._pool.dp.name())
        
        pools = msp.getPools("sdfs")
        self.assertEqual(len(pools), 1)
        self.assertTrue(isinstance(pools[0], PyTango.DeviceProxy))
        self.assertEqual(pools[0].name(), self._pool.dp.name())

        self.myAssertRaise(Exception, msp.updateMacroServer, "sfdsTESTdfdf/sdfsdf/sdffsf")
        self.myAssertRaise(Exception, msp.updateMacroServer, "")
        self.myAssertRaise(Exception, msp.getMacroServer, "")

        pools = msp.getPools(self._ms.door.keys()[0])
        self.assertEqual(len(pools), 1)
        self.assertTrue(isinstance(pools[0], PyTango.DeviceProxy))
        self.assertEqual(pools[0].name(), self._pool.dp.name())

        pools = msp.getPools("sdfs")
        self.assertEqual(len(pools), 1)
        self.assertTrue(isinstance(pools[0], PyTango.DeviceProxy))
        self.assertEqual(pools[0].name(), self._pool.dp.name())

        self._ms.dps[self._ms.ms.keys()[0]].DoorList = []
        self.myAssertRaise(Exception, msp.updateMacroServer, self._ms.door.keys()[0])
        self.myAssertRaise(Exception, msp.getMacroServer, "")
        self.myAssertRaise(Exception, msp.getPools, "")
        
        self.myAssertRaise(Exception, msp.getPools, self._ms.door.keys()[0])



    ## constructor test
    # \brief It tests default settings
    def ttest_getPool_1to3(self):
        fun = sys._getframe().f_code.co_name
        print "Run: %s.%s() " % (self.__class__.__name__, fun)
        doors = ["door2testp09/testts/t1r228","door2testp09/testts/t2r228","door2testp09/testts/t3r228"]
        msname = "ms2testp09/testts/t1r228"
        try:
            
            ms2 = TestMacroServerSetUp.TestMacroServerSetUp("MSTESTS1TO3", [msname], doors)
            ms2.setUp()

            msp = MacroServerPools(10)
            db = PyTango.Database()
            db.put_device_property(ms2.ms.keys()[0], {'PoolNames':self._pool.dp.name()})
            ms2.dps[ms2.ms.keys()[0]].Init()

            
            for i in range(3):
                ms2.dps[ms2.ms.keys()[0]].DoorList = doors
                print "doors", doors[i]
                self.myAssertRaise(Exception, msp.updateMacroServer, "sfdsTESTdfdf/sdfsdf/sdffsf")
                self.myAssertRaise(Exception, msp.updateMacroServer, "")
                self.myAssertRaise(Exception, msp.getMacroServer, "")
                self.myAssertRaise(Exception, msp.getPools, "")
                print doors[i]
                msp.updateMacroServer(doors[i])
                self.assertEqual(msp.getMacroServer(""), ms2.ms.keys()[0])
                self.assertEqual(msp.getMacroServer(doors[i]),ms2.ms.keys()[0])
                pools = msp.getPools(doors[i])
                self.assertEqual(len(pools), 1)
                self.assertTrue(isinstance(pools[0], PyTango.DeviceProxy))
                self.assertEqual(pools[0].name(), self._pool.dp.name())

                pools = msp.getPools("sdfs")
                self.assertEqual(len(pools), 1)
                self.assertTrue(isinstance(pools[0], PyTango.DeviceProxy))
                self.assertEqual(pools[0].name(), self._pool.dp.name())

                self.myAssertRaise(Exception, msp.updateMacroServer, "sfdsTESTdfdf/sdfsdf/sdffsf")
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

                ms2.dps[ms2.ms.keys()[0]].DoorList = []
                self.myAssertRaise(Exception, msp.updateMacroServer, doors[i])
                self.myAssertRaise(Exception, msp.getMacroServer, "")
                self.myAssertRaise(Exception, msp.getPools, "")

                self.myAssertRaise(Exception, msp.getPools, doors[i])
        finally:
            ms2.tearDown()


    ## constructor test
    # \brief It tests default settings
    def ttest_getPool_3to3(self):
        fun = sys._getframe().f_code.co_name
        print "Run: %s.%s() " % (self.__class__.__name__, fun)
        doors = ["door3testp09/testts/t1r228","door3testp09/testts/t2r228","door3testp09/testts/t3r228"]
        mss =  ["ms3testp09/testts/t1r228", "ms3testp09/testts/t2r228", "ms3testp09/testts/t3r228"]
        try:
            
            ms3 = TestMacroServerSetUp.TestMacroServerSetUp("MSTESTS3TO3", mss, doors)
            ms3.setUp()

            msp = MacroServerPools(10)
            db = PyTango.Database()
            for j, ms in enumerate(mss):
                db.put_device_property(ms, {'PoolNames':self._pool.dp.name()})
                ms3.dps[ms].Init()
            

            for i, ms in enumerate(mss):
                ms3.dps[ms].DoorList = [doors[i]]
                print "ms", ms, "doors", doors[i]
                self.myAssertRaise(Exception, msp.updateMacroServer, "sfdsTESTdfdf/sdfsdf/sdffsf")
                self.myAssertRaise(Exception, msp.updateMacroServer, "")
                self.myAssertRaise(Exception, msp.getMacroServer, "")
                self.myAssertRaise(Exception, msp.getPools, "")
                print doors[i]
                msp.updateMacroServer(doors[i])
                self.assertEqual(msp.getMacroServer(""), ms)
                self.assertEqual(msp.getMacroServer(doors[i]),ms)
                pools = msp.getPools(doors[i])
                self.assertEqual(len(pools), 1)
                self.assertTrue(isinstance(pools[0], PyTango.DeviceProxy))
                self.assertEqual(pools[0].name(), self._pool.dp.name())

                pools = msp.getPools("sdfs")
                self.assertEqual(len(pools), 1)
                self.assertTrue(isinstance(pools[0], PyTango.DeviceProxy))
                self.assertEqual(pools[0].name(), self._pool.dp.name())

                self.myAssertRaise(Exception, msp.updateMacroServer, "sfdsTESTdfdf/sdfsdf/sdffsf")
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
                        

    ## constructor test
    # \brief It tests default settings
    def ttest_checkComponentChannels_simple(self):
        fun = sys._getframe().f_code.co_name
        print "Run: %s.%s() " % (self.__class__.__name__, fun)
        msp = MacroServerPools(0)
        msp = MacroServerPools(10)
        channelerrors = []
        poolchannels = []
        componentgroup = {}
        self.myAssertRaise(Exception, msp.checkComponentChannels, None, None, None, None, None)
        res = msp.checkComponentChannels(self._ms.door.keys()[0],
                                   self._cf.dp, 
                                   poolchannels,
                                   componentgroup,
                                   channelerrors)
        self.assertEqual(res, '{}')
        print self._cf.dp.GetCommandVariable("COMMANDS")
        self.assertEqual(json.loads(self._cf.dp.GetCommandVariable("COMMANDS")), 
                         ['AvailableComponents','AvailableDataSources','AvailableComponents'])
        self.assertEqual(json.loads(self._cf.dp.GetCommandVariable("VARS")), [None, None, None])

    ## constructor test
    # \brief It tests default settings
    def ttest_checkComponentChannels_withcf(self):
        fun = sys._getframe().f_code.co_name
        print "Run: %s.%s() " % (self.__class__.__name__, fun)
        msp = MacroServerPools(0)
        msp = MacroServerPools(10)
        channelerrors = []
        poolchannels = []
        componentgroup = {}

        self._cf.dp.SetCommandVariable(["CPDICT", json.dumps(self.mycps)])
        self._cf.dp.SetCommandVariable(["DSDICT", json.dumps(self.mydss)])

        res = msp.checkComponentChannels(self._ms.door.keys()[0],
                                   self._cf.dp, 
                                   poolchannels,
                                   componentgroup,
                                   channelerrors)
        self.assertEqual(res, '{}')
        self.assertEqual(componentgroup, {})
        self.assertEqual(channelerrors, [])
        print self._cf.dp.GetCommandVariable("COMMANDS")
        self.assertEqual(json.loads(self._cf.dp.GetCommandVariable("COMMANDS")), 
                         ["AvailableComponents", "AvailableDataSources", "AvailableComponents"])
        self.assertEqual(json.loads(self._cf.dp.GetCommandVariable("VARS")), [None, None, None])
#        print self._cf.dp.availableComponents()


    ## constructor test
    # \brief It tests default settings
    def ttest_checkComponentChannels_withcf_cps(self):
        fun = sys._getframe().f_code.co_name
        print "Run: %s.%s() " % (self.__class__.__name__, fun)
        msp = MacroServerPools(0)
        msp = MacroServerPools(10)
        channelerrors = []
        poolchannels = ["mycp"]
        componentgroup = {"mycp":False}

        self._cf.dp.SetCommandVariable(["CPDICT", json.dumps(self.mycps)])
        self._cf.dp.SetCommandVariable(["DSDICT", json.dumps(self.mydss)])

        res = msp.checkComponentChannels(self._ms.door.keys()[0],
                                   self._cf.dp, 
                                   poolchannels,
                                   componentgroup,
                                   channelerrors)
        self.myAssertDict(json.loads(res), {"mycp":True})
        self.assertEqual(componentgroup, {"mycp":True})
        self.assertEqual(channelerrors, [])

        print self._cf.dp.GetCommandVariable("COMMANDS")
        self.assertEqual(json.loads(self._cf.dp.GetCommandVariable("COMMANDS")), 
                         ["AvailableComponents", "AvailableDataSources", "AvailableComponents", "Components"])
        self.assertEqual(json.loads(self._cf.dp.GetCommandVariable("VARS")),[None, None, None, ['mycp']] )
#        print self._cf.dp.availableComponents()



    ## constructor test
    # \brief It tests default settings
    def ttest_checkComponentChannels_withcf_nocps(self):
        fun = sys._getframe().f_code.co_name
        print "Run: %s.%s() " % (self.__class__.__name__, fun)
        msp = MacroServerPools(0)
        msp = MacroServerPools(10)
        channelerrors = []
        poolchannels = ["mycp"]
        componentgroup = {}

        self._cf.dp.SetCommandVariable(["CPDICT", json.dumps(self.mycps)])
        self._cf.dp.SetCommandVariable(["DSDICT", json.dumps(self.mydss)])

        res = msp.checkComponentChannels(self._ms.door.keys()[0],
                                   self._cf.dp, 
                                   poolchannels,
                                   componentgroup,
                                   channelerrors)
        self.myAssertDict(json.loads(res), {})
        self.assertEqual(componentgroup, {})
        self.assertEqual(channelerrors, [])

        print self._cf.dp.GetCommandVariable("COMMANDS")
        self.assertEqual(json.loads(self._cf.dp.GetCommandVariable("COMMANDS")), 
                         ["AvailableComponents", "AvailableDataSources", "AvailableComponents"])
        self.assertEqual(json.loads(self._cf.dp.GetCommandVariable("VARS")),[None, None, None] )

#        print self._cf.dp.availableComponents()
    ## constructor test
    # \brief It tests default settings
    def ttest_checkComponentChannels_withcf_nochnnel(self):
        fun = sys._getframe().f_code.co_name
        print "Run: %s.%s() " % (self.__class__.__name__, fun)
        msp = MacroServerPools(0)
        msp = MacroServerPools(10)
        channelerrors = []
        poolchannels = []
        componentgroup = {"mycp":True}

        self._cf.dp.SetCommandVariable(["CPDICT", json.dumps(self.mycps)])
        self._cf.dp.SetCommandVariable(["DSDICT", json.dumps(self.mydss)])

        res = msp.checkComponentChannels(self._ms.door.keys()[0],
                                   self._cf.dp, 
                                   poolchannels,
                                   componentgroup,
                                   channelerrors)
        self.myAssertDict(json.loads(res), {"mycp":True})
        self.assertEqual(componentgroup, {"mycp":True})
        self.assertEqual(channelerrors, [])

        print self._cf.dp.GetCommandVariable("COMMANDS")
        self.assertEqual(json.loads(self._cf.dp.GetCommandVariable("COMMANDS")), 
                         ["AvailableComponents", "AvailableDataSources", "AvailableComponents", "Components"])
        self.assertEqual(json.loads(self._cf.dp.GetCommandVariable("VARS")),[None, None, None, ['mycp']] )
#        print self._cf.dp.availableComponents()


    ## constructor test
    # \brief It tests default settings
    def ttest_checkComponentChannels_wds(self):
        fun = sys._getframe().f_code.co_name
        print "Run: %s.%s() " % (self.__class__.__name__, fun)
        msp = MacroServerPools(0)
        msp = MacroServerPools(10)
        channelerrors = []
        poolchannels = []
        componentgroup = {"smycp":True}

        self._cf.dp.SetCommandVariable(["CPDICT", json.dumps(self.smycps)])
        self._cf.dp.SetCommandVariable(["DSDICT", json.dumps(self.smydss)])

        res = msp.checkComponentChannels(self._ms.door.keys()[0],
                                   self._cf.dp, 
                                   poolchannels,
                                   componentgroup,
                                   channelerrors)
        
        print res
        self.myAssertDict(json.loads(res), {"smycp":True})
        self.assertEqual(componentgroup, {"smycp":True})
        self.assertEqual(channelerrors, [])

        print self._cf.dp.GetCommandVariable("COMMANDS")
        self.assertEqual(json.loads(self._cf.dp.GetCommandVariable("COMMANDS")), 
                         ["AvailableComponents", "AvailableDataSources", "AvailableComponents", 
                          "Components", "DataSources",  "DataSources", "DataSources",  "DataSources"])
#        self.assertEqual(json.loads(self._cf.dp.GetCommandVariable("VARS")),[None, None, None, ['smycp']] )


    ## constructor test
    # \brief It tests default settings
    def ttest_checkComponentChannels_wds2(self):
        fun = sys._getframe().f_code.co_name
        print "Run: %s.%s() " % (self.__class__.__name__, fun)
        msp = MacroServerPools(0)
        msp = MacroServerPools(10)
        channelerrors = []
        poolchannels = []
        componentgroup = {"smycp":False,"smycp2":False,"smycp3":False}

        self._cf.dp.SetCommandVariable(["CPDICT", json.dumps(self.smycps)])
        self._cf.dp.SetCommandVariable(["DSDICT", json.dumps(self.smydss)])

        res = msp.checkComponentChannels(self._ms.door.keys()[0],
                                   self._cf.dp, 
                                   poolchannels,
                                   componentgroup,
                                   channelerrors)
        
        self.myAssertDict(json.loads(res), {"smycp":True,"smycp2":True,"smycp3":True})
        self.assertEqual(componentgroup, {"smycp":True,"smycp2":True,"smycp3":True})
        self.assertEqual(channelerrors, [])

        print self._cf.dp.GetCommandVariable("COMMANDS")
        self.assertEqual(json.loads(self._cf.dp.GetCommandVariable("COMMANDS")), 
                         ["AvailableComponents", "AvailableDataSources", "AvailableComponents", 
                          "Components", "DataSources",  "DataSources",  "DataSources",  "DataSources", 
                          "Components", "DataSources",  "DataSources", "DataSources",  "DataSources", 
                          "Components", "DataSources",  "DataSources", "DataSources",  "DataSources" ])
        res = json.loads(self._cf.dp.GetCommandVariable("VARS"))
#        self.assertEqual(sorted(componentgroup.keys()),sorted([res[3][0], res[4][0], res[5][0]]) )


    ## constructor test
    # \brief It tests default settings
    def ttest_checkComponentChannels_2wds(self):
        fun = sys._getframe().f_code.co_name
        print "Run: %s.%s() " % (self.__class__.__name__, fun)
        simps2 = TestServerSetUp.TestServerSetUp( "ttestp09/testts/t2r228", "S2")
        try:
            simps2.setUp()
            msp = MacroServerPools(1)
            channelerrors = []
            poolchannels = []
            componentgroup = {"smycp":False,"smycp2":False,"smycp3":False,
                              "s2mycp":False,"s2mycp2":False,"s2mycp3":False}

            cps = dict(self.smycps)
            cps.update(self.smycps2)
            dss = dict(self.smydss)
            dss.update(self.smydss2)

            self._cf.dp.SetCommandVariable(["CPDICT", json.dumps(cps)])
            self._cf.dp.SetCommandVariable(["DSDICT", json.dumps(dss)])
    #        print "MDSS", self._cf.dp.availableDataSources()
    #        print "XDSS", self._cf.dp.dataSources(["scalar_long"])
            res = msp.checkComponentChannels(self._ms.door.keys()[0],
                                       self._cf.dp, 
                                       poolchannels,
                                       componentgroup,
                                       channelerrors)
    #        print res 
    #        print channelerrors

            self.myAssertDict(json.loads(res), {
                    "smycp":True,"smycp2":True,"smycp3":True,
                    "s2mycp":True,"s2mycp2":True,"s2mycp3":True})
            self.myAssertDict(componentgroup, {
                    "smycp":True,"smycp2":True,"smycp3":True,
                    "s2mycp":True,"s2mycp2":True,"s2mycp3":True})
            self.assertEqual(len(channelerrors), 0)

    #        print self._cf.dp.GetCommandVariable("COMMANDS")
            self.assertEqual(json.loads(self._cf.dp.GetCommandVariable("COMMANDS")), 
                             ["AvailableComponents", "AvailableDataSources", "AvailableComponents", 
                              "Components", "DataSources","DataSources", "DataSources", "DataSources",
                              "Components", "DataSources","DataSources", "DataSources","DataSources",
                              "Components", "DataSources","DataSources", "DataSources","DataSources",
                              "Components", "DataSources","DataSources", "DataSources","DataSources",
                              "Components", "DataSources","DataSources", "DataSources","DataSources",
                              "Components", "DataSources","DataSources", "DataSources","DataSources"])
            res = json.loads(self._cf.dp.GetCommandVariable("VARS"))
        finally:
            simps2.tearDown()
            

    ## constructor test
    # \brief It tests default settings
    def ttest_checkComponentChannels_2wds_dvnorunning(self):
        fun = sys._getframe().f_code.co_name
        print "Run: %s.%s() " % (self.__class__.__name__, fun)
        simps2 = TestServerSetUp.TestServerSetUp( "ttestp09/testts/t2r228", "S2")
        try:
            simps2.add()
            msp = MacroServerPools(1)
            channelerrors = []
            poolchannels = []
            componentgroup = {"smycp":False,"smycp2":False,"smycp3":False,
                              "s2mycp":False,"s2mycp2":False,"s2mycp3":False}

            cps = dict(self.smycps)
            cps.update(self.smycps2)
            dss = dict(self.smydss)
            dss.update(self.smydss2)

            self._cf.dp.SetCommandVariable(["CPDICT", json.dumps(cps)])
            self._cf.dp.SetCommandVariable(["DSDICT", json.dumps(dss)])
    #        print "MDSS", self._cf.dp.availableDataSources()
    #        print "XDSS", self._cf.dp.dataSources(["scalar_long"])
            res = msp.checkComponentChannels(self._ms.door.keys()[0],
                                       self._cf.dp, 
                                       poolchannels,
                                       componentgroup,
                                       channelerrors)
    #        print res 
    #        print channelerrors

            self.myAssertDict(json.loads(res), {
                    "smycp":True,"smycp2":True,"smycp3":True,
                    "s2mycp":False,"s2mycp2":False,"s2mycp3":False})
            self.myAssertDict(componentgroup, {
                    "smycp":True,"smycp2":True,"smycp3":True,
                    "s2mycp":False,"s2mycp2":False,"s2mycp3":False})
            self.assertEqual(len(channelerrors), 3)

    #        print self._cf.dp.GetCommandVariable("COMMANDS")
            self.assertEqual(json.loads(self._cf.dp.GetCommandVariable("COMMANDS")), 
                             ["AvailableComponents", "AvailableDataSources", "AvailableComponents", 
                              "Components", "DataSources","DataSources", "DataSources", "DataSources",
                              "Components", "DataSources","DataSources", "DataSources","DataSources",
                              "Components", "DataSources","DataSources", "DataSources","DataSources",
                              "Components", "DataSources","DataSources", "DataSources","DataSources",
                              "Components", "DataSources","DataSources", "DataSources","DataSources",
                              "Components", "DataSources","DataSources", "DataSources","DataSources"])
            res = json.loads(self._cf.dp.GetCommandVariable("VARS"))
        finally:
            simps2.delete()
            

    ## constructor test
    # \brief It tests default settings
    def ttest_checkComponentChannels_2wds_dvnodef(self):
        fun = sys._getframe().f_code.co_name
        print "Run: %s.%s() " % (self.__class__.__name__, fun)
        msp = MacroServerPools(1)
        channelerrors = []
        poolchannels = []
        componentgroup = {"smycp":False,"smycp2":False,"smycp3":False,
                          "s2mycp":False,"s2mycp2":False,"s2mycp3":False}

        cps = dict(self.smycps)
        cps.update(self.smycps2)
        dss = dict(self.smydss)
        dss.update(self.smydss2)

        self._cf.dp.SetCommandVariable(["CPDICT", json.dumps(cps)])
        self._cf.dp.SetCommandVariable(["DSDICT", json.dumps(dss)])
#        print "MDSS", self._cf.dp.availableDataSources()
#        print "XDSS", self._cf.dp.dataSources(["scalar_long"])
        res = msp.checkComponentChannels(self._ms.door.keys()[0],
                                   self._cf.dp, 
                                   poolchannels,
                                   componentgroup,
                                   channelerrors)
#        print res 
#        print channelerrors

        self.myAssertDict(json.loads(res), {
                "smycp":True,"smycp2":True,"smycp3":True,
                "s2mycp":False,"s2mycp2":False,"s2mycp3":False})
        self.myAssertDict(componentgroup, {
                "smycp":True,"smycp2":True,"smycp3":True,
                "s2mycp":False,"s2mycp2":False,"s2mycp3":False})
        self.assertEqual(len(channelerrors), 3)

#        print self._cf.dp.GetCommandVariable("COMMANDS")
        self.assertEqual(json.loads(self._cf.dp.GetCommandVariable("COMMANDS")), 
                         ["AvailableComponents", "AvailableDataSources", "AvailableComponents", 
                          "Components", "DataSources","DataSources", "DataSources", "DataSources",
                          "Components", "DataSources","DataSources", "DataSources","DataSources",
                          "Components", "DataSources","DataSources", "DataSources","DataSources",
                          "Components", "DataSources","DataSources", "DataSources","DataSources",
                          "Components", "DataSources","DataSources", "DataSources","DataSources",
                          "Components", "DataSources","DataSources", "DataSources","DataSources"])
        res = json.loads(self._cf.dp.GetCommandVariable("VARS"))
#        print res
#        self.assertEqual(sorted(componentgroup.keys()),sorted([res[3][0], res[4][0], res[5][0]]) )


    ## constructor test
    # \brief It tests default settings
    def ttest_checkComponentChannels_2wds_nods(self):
        fun = sys._getframe().f_code.co_name
        print "Run: %s.%s() " % (self.__class__.__name__, fun)
        simps2 = TestServerSetUp.TestServerSetUp( "ttestp09/testts/t2r228", "S2")
        try:
            simps2.setUp()
            msp = MacroServerPools(1)
            channelerrors = []
            poolchannels = []
            componentgroup = {"smycp":False,"smycp2":False,"smycp3":False,
                              "s2mycp":False,"s2mycp2":False,"s2mycp3":False}

            cps = dict(self.smycps)
            cps.update(self.smycps2)
            dss = dict(self.smydss)
#            dss.update(self.smydss2)

            self._cf.dp.SetCommandVariable(["CPDICT", json.dumps(cps)])
            self._cf.dp.SetCommandVariable(["DSDICT", json.dumps(dss)])
    #        print "MDSS", self._cf.dp.availableDataSources()
    #        print "XDSS", self._cf.dp.dataSources(["scalar_long"])
            res = msp.checkComponentChannels(self._ms.door.keys()[0],
                                       self._cf.dp, 
                                       poolchannels,
                                       componentgroup,
                                       channelerrors)
    #        print res 
    #        print channelerrors

            self.myAssertDict(json.loads(res), {
                    "smycp":True,"smycp2":True,"smycp3":True,
                    "s2mycp":True,"s2mycp2":True,"s2mycp3":True})
            self.myAssertDict(componentgroup, {
                    "smycp":True,"smycp2":True,"smycp3":True,
                    "s2mycp":True,"s2mycp2":True,"s2mycp3":True})
            self.assertEqual(len(channelerrors), 0)

    #        print self._cf.dp.GetCommandVariable("COMMANDS")
            res = json.loads(self._cf.dp.GetCommandVariable("VARS"))
        finally:
            simps2.tearDown()
            


    ## constructor test
    # \brief It tests default settings
    def ttest_checkComponentChannels_2wds_nodspool(self):
        fun = sys._getframe().f_code.co_name
        print "Run: %s.%s() " % (self.__class__.__name__, fun)
        simps2 = TestServerSetUp.TestServerSetUp( "ttestp09/testts/t2r228", "S2")
        try:
            simps2.setUp()
            msp = MacroServerPools(1)
            channelerrors = []
            poolchannels = ["scalar2_long", "spectrum2_short"]
            componentgroup = {"smycp":False,"smycp2":False,"smycp3":False,
                              "s2mycp":False,"s2mycp2":False,"s2mycp3":False}

            cps = dict(self.smycps)
            cps.update(self.smycps2)
            dss = dict(self.smydss)
#            dss.update(self.smydss2)

            self._cf.dp.SetCommandVariable(["CPDICT", json.dumps(cps)])
            self._cf.dp.SetCommandVariable(["DSDICT", json.dumps(dss)])
    #        print "MDSS", self._cf.dp.availableDataSources()
    #        print "XDSS", self._cf.dp.dataSources(["scalar_long"])
            res = msp.checkComponentChannels(self._ms.door.keys()[0],
                                       self._cf.dp, 
                                       poolchannels,
                                       componentgroup,
                                       channelerrors)
    #        print res 
    #        print channelerrors

            self.myAssertDict(json.loads(res), {
                    "smycp":True,"smycp2":True,"smycp3":True,
                    "s2mycp":False,"s2mycp2":False,"s2mycp3":True})
            self.myAssertDict(componentgroup, {
                    "smycp":True,"smycp2":True,"smycp3":True,
                    "s2mycp":False,"s2mycp2":False,"s2mycp3":True})
            self.assertEqual(len(channelerrors), 2)

    #        print self._cf.dp.GetCommandVariable("COMMANDS")
            res = json.loads(self._cf.dp.GetCommandVariable("VARS"))
        finally:
            simps2.tearDown()

    ## constructor test
    # \brief It tests default settings
    def ttest_checkComponentChannels_2wds_notangods(self):
        fun = sys._getframe().f_code.co_name
        print "Run: %s.%s() " % (self.__class__.__name__, fun)
        simps2 = TestServerSetUp.TestServerSetUp( "ttestp09/testts/t2r228", "S2")
        try:
            simps2.setUp()
            msp = MacroServerPools(1)
            channelerrors = []
            poolchannels = ["scalar2_long", "spectrum2_short"]
            componentgroup = {"smycp":False,"smycp2":False,"smycp3":False,"smycpnt1":False,
                              "s2mycp":False,"s2mycp2":False,"s2mycp3":False}

            cps = dict(self.smycps)
            cps.update(self.smycps2)
            dss = dict(self.smydss)
            dss.update(self.smydss2)

            self._cf.dp.SetCommandVariable(["CPDICT", json.dumps(cps)])
            self._cf.dp.SetCommandVariable(["DSDICT", json.dumps(dss)])
    #        print "MDSS", self._cf.dp.availableDataSources()
    #        print "XDSS", self._cf.dp.dataSources(["scalar_long"])
            res = msp.checkComponentChannels(self._ms.door.keys()[0],
                                       self._cf.dp, 
                                       poolchannels,
                                       componentgroup,
                                       channelerrors)
#            print res 
    #        print channelerrors

            self.myAssertDict(json.loads(res), {
                    "smycp":True,"smycp2":True,"smycp3":True,
                    "s2mycp":True,"s2mycp2":True,"s2mycp3":True,"smycpnt1":True})
            self.myAssertDict(componentgroup, {
                    "smycp":True,"smycp2":True,"smycp3":True,
                    "s2mycp":True,"s2mycp2":True,"s2mycp3":True,"smycpnt1":True})
            self.assertEqual(len(channelerrors), 0)

    #        print self._cf.dp.GetCommandVariable("COMMANDS")
            res = json.loads(self._cf.dp.GetCommandVariable("VARS"))
        finally:
            simps2.tearDown()

    ## constructor test
    # \brief It tests default settings
    def ttest_checkComponentChannels_2wds_notangodsnopool(self):
        fun = sys._getframe().f_code.co_name
        print "Run: %s.%s() " % (self.__class__.__name__, fun)
        simps2 = TestServerSetUp.TestServerSetUp( "ttestp09/testts/t2r228", "S2")
        try:
            simps2.setUp()
            msp = MacroServerPools(1)
            channelerrors = []
            poolchannels = ["scalar2_long", "spectrum2_short", "client_long"]
            componentgroup = {"smycp":False,"smycp2":False,"smycp3":False,"smycpnt1":False,
                              "s2mycp":False,"s2mycp2":False,"s2mycp3":False}

            cps = dict(self.smycps)
            cps.update(self.smycps2)
            dss = dict(self.smydss)
            dss.update(self.smydss2)

            self._cf.dp.SetCommandVariable(["CPDICT", json.dumps(cps)])
            self._cf.dp.SetCommandVariable(["DSDICT", json.dumps(dss)])
    #        print "MDSS", self._cf.dp.availableDataSources()
    #        print "XDSS", self._cf.dp.dataSources(["scalar_long"])
            res = msp.checkComponentChannels(self._ms.door.keys()[0],
                                       self._cf.dp, 
                                       poolchannels,
                                       componentgroup,
                                       channelerrors)
#            print res 
    #        print channelerrors

            self.myAssertDict(json.loads(res), {
                    "smycp":True,"smycp2":True,"smycp3":True,
                    "s2mycp":True,"s2mycp2":True,"s2mycp3":True,"smycpnt1":False})
            self.myAssertDict(componentgroup, {
                    "smycp":True,"smycp2":True,"smycp3":True,
                    "s2mycp":True,"s2mycp2":True,"s2mycp3":True,"smycpnt1":False})
            self.assertEqual(len(channelerrors), 1)

    #        print self._cf.dp.GetCommandVariable("COMMANDS")
            res = json.loads(self._cf.dp.GetCommandVariable("VARS"))
        finally:
            simps2.tearDown()
            

    ## constructor test
    # \brief It tests default settings
    def ttest_checkComponentChannels_2wds_notangodsnopool2(self):
        fun = sys._getframe().f_code.co_name
        print "Run: %s.%s() " % (self.__class__.__name__, fun)
        simps2 = TestServerSetUp.TestServerSetUp( "ttestp09/testts/t2r228", "S2")
        try:
            simps2.setUp()
            msp = MacroServerPools(10)
            db = PyTango.Database()
            db.put_device_property(self._ms.ms.keys()[0], {'PoolNames':self._pool.dp.name()})
            channelerrors = []
            poolchannels = ["scalar2_long", "spectrum2_short", "client_long"]
            componentgroup = {"smycp":False,"smycp2":False,"smycp3":False,"smycpnt1":False,
                              "s2mycp":False,"s2mycp2":False,"s2mycp3":False}

            cps = dict(self.smycps)
            cps.update(self.smycps2)
            dss = dict(self.smydss)
            dss.update(self.smydss2)

            self._cf.dp.SetCommandVariable(["CPDICT", json.dumps(cps)])
            self._cf.dp.SetCommandVariable(["DSDICT", json.dumps(dss)])
    #        print "MDSS", self._cf.dp.availableDataSources()
    #        print "XDSS", self._cf.dp.dataSources(["scalar_long"])
            msp.updateMacroServer(self._ms.door.keys()[0])
            pools = msp.getPools(self._ms.door.keys()[0])
            print "POOLS", pools

            res = msp.checkComponentChannels(self._ms.door.keys()[0],
                                       self._cf.dp, 
                                       poolchannels,
                                       componentgroup,
                                       channelerrors)
#            print res 
    #        print channelerrors

            self.myAssertDict(json.loads(res), {
                    "smycp":True,"smycp2":True,"smycp3":True,
                    "s2mycp":True,"s2mycp2":True,"s2mycp3":True,"smycpnt1":False})
            self.myAssertDict(componentgroup, {
                    "smycp":True,"smycp2":True,"smycp3":True,
                    "s2mycp":True,"s2mycp2":True,"s2mycp3":True,"smycpnt1":False})
            self.assertEqual(len(channelerrors), 1)

    #        print self._cf.dp.GetCommandVariable("COMMANDS")
            res = json.loads(self._cf.dp.GetCommandVariable("VARS"))
        finally:
            simps2.tearDown()
            
    ## constructor test
    # \brief It tests default settings
    def ttest_checkComponentChannels_2wds_notangods2(self):
        fun = sys._getframe().f_code.co_name
        print "Run: %s.%s() " % (self.__class__.__name__, fun)
        simps2 = TestServerSetUp.TestServerSetUp( "ttestp09/testts/t2r228", "S2")

        arr = [
            {"name":"client_long", "full_name":"ttestp09/testts/t1r228/Value"} ,
            {"name":"client_short", "full_name":"ttestp09/testts/t1r228/Value"} ,
            ]
        try:
            simps2.setUp()
            msp = MacroServerPools(10)
            db = PyTango.Database()
            db.put_device_property(self._ms.ms.keys()[0], {'PoolNames':self._pool.dp.name()})
            channelerrors = []
            poolchannels = []
            componentgroup = {"smycp":False,"smycp2":False,"smycp3":False,"smycpnt1":False,
                              "s2mycp":False,"s2mycp2":False,"s2mycp3":False}

            cps = dict(self.smycps)
            cps.update(self.smycps2)
            dss = dict(self.smydss)
            dss.update(self.smydss2)

            self._cf.dp.SetCommandVariable(["CPDICT", json.dumps(cps)])
            self._cf.dp.SetCommandVariable(["DSDICT", json.dumps(dss)])
    #        print "MDSS", self._cf.dp.availableDataSources()
    #        print "XDSS", self._cf.dp.dataSources(["scalar_long"])
            msp.updateMacroServer(self._ms.door.keys()[0])
            pools = msp.getPools(self._ms.door.keys()[0])
            pools[0].AcqChannelList = [json.dumps(a) for a in arr]
            print "POOLS", pools

            res = msp.checkComponentChannels(self._ms.door.keys()[0],
                                       self._cf.dp, 
                                       poolchannels,
                                       componentgroup,
                                       channelerrors)
#            print res 
    #        print channelerrors

            self.myAssertDict(json.loads(res), {
                    "smycp":True,"smycp2":True,"smycp3":True,
                    "s2mycp":True,"s2mycp2":True,"s2mycp3":True,"smycpnt1":True})
            self.myAssertDict(componentgroup, {
                    "smycp":True,"smycp2":True,"smycp3":True,
                    "s2mycp":True,"s2mycp2":True,"s2mycp3":True,"smycpnt1":True})
            self.assertEqual(len(channelerrors), 0)

    #        print self._cf.dp.GetCommandVariable("COMMANDS")
            res = json.loads(self._cf.dp.GetCommandVariable("VARS"))
        finally:
            simps2.tearDown()
            


    ## constructor test
    # \brief It tests default settings
    def ttest_checkComponentChannels_2wds_notangodspool_error(self):
        fun = sys._getframe().f_code.co_name
        print "Run: %s.%s() " % (self.__class__.__name__, fun)
        simps2 = TestServerSetUp.TestServerSetUp( "ttestp09/testts/t2r228", "S2")

        arr = [
            {"name":"client_long", "full_name":"ttestp09/testts/t1r228/Value"} ,
            {"name":"client_short", "full_name":"ttestp09/testts/t1r228/Value"} ,
            ]
        try:
            simps2.setUp()
            msp = MacroServerPools(10)
            db = PyTango.Database()
            db.put_device_property(self._ms.ms.keys()[0], {'PoolNames':self._pool.dp.name()})
            channelerrors = []
            poolchannels = ["scalar2_long", "spectrum2_short", "client_long", "client_short"]
            componentgroup = {
                "smycp":False,"smycp2":False,"smycp3":False,
                "smycpnt1":False,
                "s2mycp":False,"s2mycp2":False,"s2mycp3":False
                }

            cps = dict(self.smycps)
            cps.update(self.smycps2)
            dss = dict(self.smydss)
            dss.update(self.smydss2)

            self._cf.dp.SetCommandVariable(["CPDICT", json.dumps(cps)])
            self._cf.dp.SetCommandVariable(["DSDICT", json.dumps(dss)])
    #        print "MDSS", self._cf.dp.availableDataSources()
    #        print "XDSS", self._cf.dp.dataSources(["scalar_long"])
            msp.updateMacroServer(self._ms.door.keys()[0])
            pools = msp.getPools(self._ms.door.keys()[0])
            pools[0].AcqChannelList = [json.dumps(a) for a in arr]
            print "POOLS", pools

            res = msp.checkComponentChannels(self._ms.door.keys()[0],
                                       self._cf.dp, 
                                       poolchannels,
                                       componentgroup,
                                       channelerrors)
            print res 
    #        print channelerrors

            self.myAssertDict(json.loads(res), {
                    "smycp":True,"smycp2":True,"smycp3":True,
                    "s2mycp":True,"s2mycp2":True,"s2mycp3":True,"smycpnt1":False})
            self.myAssertDict(componentgroup, {
                    "smycp":True,"smycp2":True,"smycp3":True,
                    "s2mycp":True,"s2mycp2":True,"s2mycp3":True,"smycpnt1":False})
            self.assertEqual(len(channelerrors), 1)

    #        print self._cf.dp.GetCommandVariable("COMMANDS")
            res = json.loads(self._cf.dp.GetCommandVariable("VARS"))
        finally:
            simps2.tearDown()

    ## constructor test
    # \brief It tests default settings
    def ttest_checkComponentChannels_2wds_notangodspool(self):
        fun = sys._getframe().f_code.co_name
        print "Run: %s.%s() " % (self.__class__.__name__, fun)
        simps2 = TestServerSetUp.TestServerSetUp( "ttestp09/testts/t2r228", "S2")

        arr = [
            {"name":"client_short", "full_name":"ttestp09/testts/t1r228"} ,
            ]
        try:
            simps2.setUp()
            msp = MacroServerPools(10)
            db = PyTango.Database()
            db.put_device_property(self._ms.ms.keys()[0], {'PoolNames':self._pool.dp.name()})
            channelerrors = []
            poolchannels = ["scalar2_long", "spectrum2_short",  "client_short"]
            componentgroup = {
                "smycp":False,"smycp2":False,"smycp3":False,
                "smycpnt1":False,
                "s2mycp":False,"s2mycp2":False,"s2mycp3":False
                }

            cps = dict(self.smycps)
            cps.update(self.smycps2)
            dss = dict(self.smydss)
            dss.update(self.smydss2)

            self._cf.dp.SetCommandVariable(["CPDICT", json.dumps(cps)])
            self._cf.dp.SetCommandVariable(["DSDICT", json.dumps(dss)])
    #        print "MDSS", self._cf.dp.availableDataSources()
    #        print "XDSS", self._cf.dp.dataSources(["scalar_long"])
            msp.updateMacroServer(self._ms.door.keys()[0])
            pools = msp.getPools(self._ms.door.keys()[0])
            pools[0].AcqChannelList = [json.dumps(a) for a in arr]
            print "POOLS", pools
            self._simps.dp.ChangeValueType("ScalarShort")
            self._simps.dp.Value = 43
            res = msp.checkComponentChannels(self._ms.door.keys()[0],
                                       self._cf.dp, 
                                       poolchannels,
                                       componentgroup,
                                       channelerrors)
#            print res 
    #        print channelerrors

            self.myAssertDict(json.loads(res), {
                    "smycp":True,"smycp2":True,"smycp3":True,
                    "s2mycp":True,"s2mycp2":True,"s2mycp3":True,"smycpnt1":False})
            self.myAssertDict(componentgroup, {
                    "smycp":True,"smycp2":True,"smycp3":True,
                    "s2mycp":True,"s2mycp2":True,"s2mycp3":True,"smycpnt1":False})
            self.assertEqual(len(channelerrors), 1)

    #        print self._cf.dp.GetCommandVariable("COMMANDS")
            res = json.loads(self._cf.dp.GetCommandVariable("VARS"))
        finally:
            simps2.tearDown()
            


   ## constructor test
    # \brief It tests default settings
    def ttest_checkComponentChannels_2wds_notangodspool_alias(self):
        fun = sys._getframe().f_code.co_name
        print "Run: %s.%s() " % (self.__class__.__name__, fun)
        simps2 = TestServerSetUp.TestServerSetUp( "ttestp09/testts/t2r228", "S2")
        db = PyTango.Database()

        arr = [
            {"name":"client_short", "full_name":"ttestp09/testts/t1r228"} ,
            ]
        try:
            simps2.setUp()
            msp = MacroServerPools(10)
            db.put_device_alias(arr[0]["full_name"],arr[0]["name"])
            db.put_device_property(self._ms.ms.keys()[0], {'PoolNames':self._pool.dp.name()})
            channelerrors = []
            poolchannels = ["scalar2_long", "spectrum2_short", "client_short"]
            componentgroup = {
                "smycp":False,"smycp2":False,"smycp3":False,
                "smycpnt1":False,
                "s2mycp":False,"s2mycp2":False,"s2mycp3":False
                }

            cps = dict(self.smycps)
            cps.update(self.smycps2)
            dss = dict(self.smydss)
            dss.update(self.smydss2)

            self._cf.dp.SetCommandVariable(["CPDICT", json.dumps(cps)])
            self._cf.dp.SetCommandVariable(["DSDICT", json.dumps(dss)])
            msp.updateMacroServer(self._ms.door.keys()[0])
            pools = msp.getPools(self._ms.door.keys()[0])
            pools[0].AcqChannelList = [json.dumps(a) for a in arr]
            print "POOLS", pools
            self._simps.dp.ChangeValueType("ScalarShort")
            self._simps.dp.Value = 43
            res = msp.checkComponentChannels(self._ms.door.keys()[0],
                                       self._cf.dp, 
                                       poolchannels,
                                       componentgroup,
                                       channelerrors)
#            print res 
    #        print channelerrors

            self.myAssertDict(json.loads(res), {
                    "smycp":True,"smycp2":True,"smycp3":True,
                    "s2mycp":True,"s2mycp2":True,"s2mycp3":True,"smycpnt1":True})
            self.myAssertDict(componentgroup, {
                    "smycp":True,"smycp2":True,"smycp3":True,
                    "s2mycp":True,"s2mycp2":True,"s2mycp3":True,"smycpnt1":True})
            self.assertEqual(len(channelerrors), 0)

    #        print self._cf.dp.GetCommandVariable("COMMANDS")
            res = json.loads(self._cf.dp.GetCommandVariable("VARS"))
        finally:
            db.delete_device_alias(arr[0]["name"])
            simps2.tearDown()
            
   ## constructor test
    # \brief It tests default settings
    def ttest_checkComponentChannels_2wds_notangodspool_alias_value(self):
        fun = sys._getframe().f_code.co_name
        print "Run: %s.%s() " % (self.__class__.__name__, fun)
        simps2 = TestServerSetUp.TestServerSetUp( "ttestp09/testts/t2r228", "S2")
        db = PyTango.Database()

        arr = [
            {"name":"client_short", "full_name":"ttestp09/testts/t1r228"} ,
            ]
        try:
            simps2.setUp()
            msp = MacroServerPools(10)
            db.put_device_alias(arr[0]["full_name"],arr[0]["name"])
            db.put_device_property(self._ms.ms.keys()[0], {'PoolNames':self._pool.dp.name()})
            channelerrors = []
            poolchannels = ["scalar2_long", "spectrum2_short", "client_short"]
            componentgroup = {
                "smycp":False,"smycp2":False,"smycp3":False,
                "smycpnt1":False,
                "s2mycp":False,"s2mycp2":False,"s2mycp3":False
                }

            cps = dict(self.smycps)
            cps.update(self.smycps2)
            dss = dict(self.smydss)
            dss.update(self.smydss2)

            self._cf.dp.SetCommandVariable(["CPDICT", json.dumps(cps)])
            self._cf.dp.SetCommandVariable(["DSDICT", json.dumps(dss)])
            msp.updateMacroServer(self._ms.door.keys()[0])
            pools = msp.getPools(self._ms.door.keys()[0])
            pools[0].AcqChannelList = [json.dumps(a) for a in arr]
            print "POOLS", pools
#            self._simps.dp.ChangeValueType("ScalarShort")
#            self._simps.dp.Value = 43
            res = msp.checkComponentChannels(self._ms.door.keys()[0],
                                       self._cf.dp, 
                                       poolchannels,
                                       componentgroup,
                                       channelerrors)
#            print res 
    #        print channelerrors

            self.myAssertDict(json.loads(res), {
                    "smycp":True,"smycp2":True,"smycp3":True,
                    "s2mycp":True,"s2mycp2":True,"s2mycp3":True,"smycpnt1":True})
            self.myAssertDict(componentgroup, {
                    "smycp":True,"smycp2":True,"smycp3":True,
                    "s2mycp":True,"s2mycp2":True,"s2mycp3":True,"smycpnt1":True})
            self.assertEqual(len(channelerrors), 0)

    #        print self._cf.dp.GetCommandVariable("COMMANDS")
            res = json.loads(self._cf.dp.GetCommandVariable("VARS"))
        finally:
            db.delete_device_alias(arr[0]["name"])
            simps2.tearDown()
            
  ## constructor test
    # \brief It tests default settings
    def ttest_checkComponentChannels_2wds_notangodspool_alias_novalue(self):
        fun = sys._getframe().f_code.co_name
        print "Run: %s.%s() " % (self.__class__.__name__, fun)
        simps2 = TestServerSetUp.TestServerSetUp( "ttestp09/testts/t2r228", "S2")
        db = PyTango.Database()

        arr = [
            {"name":"client2_short", "full_name":"ttestp09/testts/t2r228"} ,
            ]
        try:
            simps2.add()
            msp = MacroServerPools(10)
            db.put_device_alias(arr[0]["full_name"],arr[0]["name"])
            db.put_device_property(self._ms.ms.keys()[0], {'PoolNames':self._pool.dp.name()})
            channelerrors = []
            poolchannels = ["scalar2_long", "spectrum2_short", "client2_short"]
            componentgroup = {
                "smycp":False,"smycp2":False,"smycp3":False,
                "s2mycpnt1":False,
#                "s2mycp":False,"s2mycp2":False,"s2mycp3":False
                }

            cps = dict(self.smycps)
            cps.update(self.smycps2)
            dss = dict(self.smydss)
            dss.update(self.smydss2)

            self._cf.dp.SetCommandVariable(["CPDICT", json.dumps(cps)])
            self._cf.dp.SetCommandVariable(["DSDICT", json.dumps(dss)])
            msp.updateMacroServer(self._ms.door.keys()[0])
            pools = msp.getPools(self._ms.door.keys()[0])
            pools[0].AcqChannelList = [json.dumps(a) for a in arr]
            print "POOLS", pools
            res = msp.checkComponentChannels(self._ms.door.keys()[0],
                                       self._cf.dp, 
                                       poolchannels,
                                       componentgroup,
                                       channelerrors)
#            print res 
#            print channelerrors

            self.myAssertDict(json.loads(res), {
                    "smycp":True,"smycp2":True,"smycp3":True,
                    "s2mycpnt1":False})
            self.myAssertDict(componentgroup, {
                    "smycp":True,"smycp2":True,"smycp3":True,
                    "s2mycpnt1":False})
            self.assertEqual(len(channelerrors), 1)

    #        print self._cf.dp.GetCommandVariable("COMMANDS")
            res = json.loads(self._cf.dp.GetCommandVariable("VARS"))
        finally:
            db.delete_device_alias(arr[0]["name"])
            simps2.tearDown()
            
    ## constructor test
    # \brief It tests default settings
    def ttest_checkComponentChannels_2wds_nocomponents(self):
        fun = sys._getframe().f_code.co_name
        print "Run: %s.%s() " % (self.__class__.__name__, fun)
        simps2 = TestServerSetUp.TestServerSetUp( "ttestp09/testts/t2r228", "S2")
        try:
            simps2.setUp()
            msp = MacroServerPools(1)
            channelerrors = []
            poolchannels = []
            componentgroup = {"smycp":False,"smycp2":False,"smycp3":False,
                              "s2mycp":False,"s2mycp2":False,"s2mycp3":False}

            cps = dict(self.smycps)
#            cps.update(self.smycps2)
            dss = dict(self.smydss)
#            dss.update(self.smydss2)

            self._cf.dp.SetCommandVariable(["CPDICT", json.dumps(cps)])
            self._cf.dp.SetCommandVariable(["DSDICT", json.dumps(dss)])
    #        print "MDSS", self._cf.dp.availableDataSources()
    #        print "XDSS", self._cf.dp.dataSources(["scalar_long"])
            res = msp.checkComponentChannels(self._ms.door.keys()[0],
                                       self._cf.dp, 
                                       poolchannels,
                                       componentgroup,
                                       channelerrors)
    #        print res 
    #        print channelerrors

            self.myAssertDict(json.loads(res), {
                    "smycp":True,"smycp2":True,"smycp3":True,
                    "s2mycp":False,"s2mycp2":False,"s2mycp3":False})
            self.myAssertDict(componentgroup, {
                    "smycp":True,"smycp2":True,"smycp3":True,
                    "s2mycp":False,"s2mycp2":False,"s2mycp3":False})
            self.assertEqual(len(channelerrors), 3)

    #        print self._cf.dp.GetCommandVariable("COMMANDS")
            res = json.loads(self._cf.dp.GetCommandVariable("VARS"))
        finally:
            simps2.tearDown()
            


    ## constructor test
    # \brief It tests default settings
    def ttest_getSelectorEnv_noenv(self):
        fun = sys._getframe().f_code.co_name
        print "Run: %s.%s() " % (self.__class__.__name__, fun)
            
        envs = [
            pickle.dumps(
                {"new":{}
                     }
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
        msp.getSelectorEnv(self._ms.door.keys()[0], [], {})
        for i, dt in enumerate(edats):
            
            data = {}
            self._ms.dps[self._ms.ms.keys()[0]].Environment = ('pickle', envs[0])
            msp.getSelectorEnv(self._ms.door.keys()[0],enms[i], data)
#            print "data",data
            self.myAssertDict(data, dt)



    ## constructor test
    # \brief It tests default settings
    def ttest_getSelectorEnv(self):
        fun = sys._getframe().f_code.co_name
        print "Run: %s.%s() " % (self.__class__.__name__, fun)
            
        envs = [
            pickle.dumps(
                {"new":{"ScanDir":"/tmp"}
                 }
                ),
            pickle.dumps(
                {"new":{"ScanDir":"/tmp"}
                 }
                ),
            pickle.dumps(
                {"new":{"ScanDir":"/tmp", "ScanFile":["file.nxs"]}
                 }
                ),
            pickle.dumps(
                {"new":{"ScanDir":"/tmp", 
                        "ScanFile":["file.nxs"], 
                        "NeXusConfigServer":"ptr/ert/ert",
                        }
                 }
                ),
            pickle.dumps(
                {"new":{"ScanDir":"/tmp", 
                        "ScanFile":["file.nxs","file2.nxs"], 
                        "NeXusConfiguration":{"ConfigServer":"ptr/ert/ert2"},
                        }
                 }
                ),
            pickle.dumps(
                {"new":{"ScanDir":"/tmp", 
                        "ScanFile":"file.nxs", 
                        "NeXusConfigServer":"ptr/ert/ert",
                        "NeXusConfiguration":{"ConfigServer":"ptr/ert/ert2"},
                        }
                 }
                ),
            pickle.dumps(
                {"new":{"ScanDir":"/tmp", 
                        "ScanFile":["file.nxs"], 
                        "NeXusConfigServer":u'ptr/ert/ert',
                        "NeXusBool":True,
                        "NeXusInt":234,
                        "NeXusFloat":123.123,
                        "NeXusSomething":("dgfg",),
                        "NeXusDict":{"dgfg":123,"sdf":"345"},
                        }
                 }
                ),
            pickle.dumps(
                {"new":{"ScanDir":"/tmp", 
                        "ScanFile":["file.nxs"], 
                        "NeXusConfiguration":{"ConfigServer":u'ptr/ert/ert',
                        "Bool":True,
                        "Int":234,
                        "Float":123.123,
                        "Something":("dgfg",),
                        "Dict":{"dgfg":123,"sdf":"345"}}
                        }
                 }
                ),
            ]
        enms = [
            ["ScanID"], 
            ["ScanDir"],
            ["ScanDir", "ScanFile", "ConfigServer"],
            ["ScanDir", "ScanFile", "ConfigServer"],
            ["ScanDir", "ScanFile", "ConfigServer"],
            ["ScanDir", "ScanFile", "ConfigServer"],
            ["ScanDir", "ScanFile", "ConfigServer", "Bool", "Int","Float", "Something", "Dict"],
            ["ScanDir", "ScanFile", "ConfigServer", "Bool", "Int","Float", "Something", "Dict"],
            ]

        edats = [
            {},
            {"ScanDir":"/tmp"},
            {"ScanDir":"/tmp", "ScanFile":json.dumps(["file.nxs"])},
            {"ScanDir":"/tmp", "ScanFile":json.dumps(["file.nxs"]),"ConfigServer":"ptr/ert/ert"},
            {"ScanDir":"/tmp", "ScanFile":json.dumps(["file.nxs","file2.nxs"]),"ConfigServer":"ptr/ert/ert2"},
            {"ScanDir":"/tmp", "ScanFile":"file.nxs", "ConfigServer":"ptr/ert/ert"},
            {"ScanDir":"/tmp", "ScanFile":json.dumps(["file.nxs"]),"ConfigServer":"ptr/ert/ert",
             "Bool":True, "Int":234,"Float":123.123, "Something":json.dumps(["dgfg"]),
             "Dict":json.dumps({"dgfg":123,"sdf":"345"}),
             },
            {"ScanDir":"/tmp", "ScanFile":json.dumps(["file.nxs"]),"ConfigServer":"ptr/ert/ert",
             "Bool":True, "Int":234,"Float":123.123, "Something":json.dumps(["dgfg"]),
             "Dict":json.dumps({"dgfg":123,"sdf":"345"}),             
             },
            ] 

        msp = MacroServerPools(10)
        self.myAssertRaise(Exception, msp.getSelectorEnv, None, [], {})
        msp.getSelectorEnv(self._ms.door.keys()[0], [], {})
        for i, dt in enumerate(edats):
#            print "I = ",i
            data = {}
            self._ms.dps[self._ms.ms.keys()[0]].Environment = ('pickle', envs[i])
            msp.getSelectorEnv(self._ms.door.keys()[0],enms[i], data)
#            print pickle.loads(self._ms.dps[self._ms.ms.keys()[0]].Environment[1])
#            print "data",data
            self.myAssertDict(data, dt)



    ## constructor test
    # \brief It tests default settings
    def test_setSelectorEnv(self):
        fun = sys._getframe().f_code.co_name
        print "Run: %s.%s() " % (self.__class__.__name__, fun)
            
        envs = [
            {"new":{'ScanID': 192, 
                    'NeXusSelectorDevice': u'p09/nxsrecselector/1', 
                    'ScanFile': [u'sar4r.nxs'], 
                    'NeXusConfiguration': {}, 
                    'ActiveMntGrp': 'nxsmntgrp', 
                    '_ViewOptions': {'ShowDial': True}, 
                    'DataCompressionRank': 0, 
                    'ScanDir': '/tmp/'}
             },
            {"new":{
                    'ScanID': 192, 
                    'NeXusSelectorDevice': u'p09/nxsrecselector/1', 
                    'ScanFile': [u'sar4r.nxs'], 
                    'NeXusConfiguration': {}, 
                    'ActiveMntGrp': 'nxsmntgrp', 
                    '_ViewOptions': {'ShowDial': True}, 
                    'DataCompressionRank': 0, 
                    'ScanDir': '/tmp'}
             },
            {"new":{
                    'ScanID': 192, 
                    'NeXusSelectorDevice': u'p09/nxsrecselector/1', 
                    'NeXusConfiguration': {}, 
                    'ActiveMntGrp': 'nxsmntgrp', 
                    '_ViewOptions': {'ShowDial': True}, 
                    'DataCompressionRank': 0, 
                    "ScanDir":"/tmp", 
                    "ScanFile":["file.nxs"]
                    }
             },
            {"new":{"ScanDir":"/tmp", 
                    'ScanID': 192, 
                    'NeXusSelectorDevice': u'p09/nxsrecselector/1', 
                    'NeXusConfiguration': {"ConfigServer":"ptr/ert/ert"}, 
                    'ActiveMntGrp': 'nxsmntgrp', 
                    '_ViewOptions': {'ShowDial': True}, 
                    'DataCompressionRank': 0, 
                    "ScanFile":["file.nxs"], 
                    }
             },
            {"new":{"ScanDir":"/tmp", 
                    'ScanID': 192, 
                    'NeXusSelectorDevice': u'p09/nxsrecselector/1', 
                    'NeXusConfiguration': {"ConfigServer":"ptr/ert/ert2"}, 
                    'ActiveMntGrp': 'nxsmntgrp', 
                    '_ViewOptions': {'ShowDial': True}, 
                    'DataCompressionRank': 0, 
                    "ScanFile":["file.nxs","file2.nxs"], 
                    }
             },
            {"new":{"ScanDir":"/tmp", 
                    'ScanID': 192, 
                    'NeXusSelectorDevice': u'p09/nxsrecselector/1', 
                    'NeXusConfiguration': {"ConfigServer":"ptr/ert/ert"}, 
                    'ActiveMntGrp': 'nxsmntgrp', 
                    '_ViewOptions': {'ShowDial': True}, 
                    'DataCompressionRank': 0, 
                    "ScanFile":"file.nxs", 
                    }
             },
            {"new":{"ScanDir":"/tmp", 
                    'ScanID': 192, 
                    'NeXusSelectorDevice': u'p09/nxsrecselector/1', 
                    "NeXusConfiguration":{"ConfigServer":'ptr/ert/ert',
                                          "Bool":True,
                                          "Int":234,
                                          "Float":123.123,
                                          "Something":["dgfg"],
                                          "Dict":{"dgfg":123,"sdf":"345"}},
                    'ActiveMntGrp': 'nxsmntgrp', 
                    '_ViewOptions': {'ShowDial': True}, 
                    'DataCompressionRank': 0, 
                    "ScanFile":["file.nxs"], 
                    }
             }, 
            {"new":{"ScanDir":"/tmp", 
                    'ScanID': 192, 
                    'NeXusSelectorDevice': u'p09/nxsrecselector/1', 
                    "NeXusConfiguration":{"ConfigServer":'ptr/ert/ert',
                                          "Bool":True,
                                          "Int":234,
                                          "Float":123.124,
                                          "Something":["dgfg"],
                                          "Dict":{"dgfg":123,"sdf":"345"}},
                    'ActiveMntGrp': 'nxsmntgrp', 
                    '_ViewOptions': {'ShowDial': True}, 
                    'DataCompressionRank': 0, 
                    "ScanFile":["file.nxs"], 
                    }
             },
           ]

        edats = [
            {},
            {"ScanDir":"/tmp"},
            {"ScanDir":"/tmp", "ScanFile":json.dumps(["file.nxs"])},
            {"ScanDir":"/tmp", "ScanFile":json.dumps(["file.nxs"]),"ConfigServer":"ptr/ert/ert"},
            {"ScanDir":"/tmp", "ScanFile":json.dumps(["file.nxs","file2.nxs"]),"ConfigServer":"ptr/ert/ert2"},
            {"ScanDir":"/tmp", "ScanFile":"file.nxs", "ConfigServer":"ptr/ert/ert"},
            {"ScanDir":"/tmp", "ScanFile":json.dumps(["file.nxs"]),"ConfigServer":"ptr/ert/ert",
             "Bool":True, "Int":234,"Float":123.123, "Something":json.dumps(["dgfg"]),
             "Dict":json.dumps({"dgfg":123,"sdf":"345"}),
             },
            {"ScanDir":"/tmp", "ScanFile":["file.nxs"],"ConfigServer":"ptr/ert/ert",
             "Bool":True, "Int":234,"Float":123.124, "Something":["dgfg"],
             "Dict":{"dgfg":123,"sdf":"345"},
             },
            ] 

        msp = MacroServerPools(10)
        self.myAssertRaise(Exception, msp.setSelectorEnv, None, {})
        self.myAssertRaise(Exception, msp.setSelectorEnv, None, {}, {})
        msp.setSelectorEnv(self._ms.door.keys()[0], {})
        msp.setSelectorEnv(self._ms.door.keys()[0], {}, {})
        for i, dt in enumerate(edats):
            msp.setSelectorEnv(self._ms.door.keys()[0], dt)
#            print "I = ",i
            data = {}
            env = pickle.loads(self._ms.dps[self._ms.ms.keys()[0]].Environment[1])
#            print "env", env
#            print "ei", envs[i]
            self.myAssertDict(envs[i], env)


if __name__ == '__main__':
    unittest.main()
