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
# \file DescriberTest.py
# unittests for field Tags running Tango Server
#
import unittest
import time
import os
import sys
import json
import random
import struct
import binascii
import re
# import subprocess

from nxsrecconfig.Describer import Describer


# if 64-bit machione
IS64BIT = (struct.calcsize("P") == 8)

if sys.version_info > (3,):
    long = int


class NoServer(object):

    def __init__(self, value=None):
        self.reset(value)

    def reset(self, value=None):
        self.value = value
        self.commands = []
        self.vars = []
        self.dsdict = {}
        self.cpdict = {}
        self.mcplist = []
        self.checkvariables = None
        self.variables = None

    def dataSources(self, names):
        self.vars.append(names)
        self.commands.append("dataSources")
        return [self.dsdict[nm] for nm in names if nm in self.dsdict.keys()]

    def availableDataSources(self):
        self.vars.append(None)
        self.commands.append("availableDataSources")
        return list(self.dsdict.keys())

    def components(self, names):
        self.vars.append(names)
        self.commands.append("components")
        return [self.cpdict[nm] for nm in names if nm in self.cpdict.keys()]

    def dependentComponents(self, names):
        self.vars.append(names)
        self.commands.append("dependentComponents")
        res = []
        for name in names:
            res.append(name)
            cp = self.cpdict[name]
            res.extend(self.__findText(cp, "$components."))
        return res

    def instantiatedComponents(self, names):
        if self.checkvariables != self.variables:
            raise Exception("Variables not set")
        self.vars.append(names)
        self.commands.append("components")
        return [self.cpdict[nm] for nm in names if nm in self.cpdict.keys()]

    def availableComponents(self):
        self.vars.append(None)
        self.commands.append("availableComponents")
        return list(self.cpdict.keys())

    def mandatoryComponents(self):
        self.vars.append(None)
        self.commands.append("mandatoryComponents")
        return list(self.mcplist)

    def __findText(self, text, label):
        variables = []
        index = text.find(label)
        while index != -1:
            try:
                if sys.version_info > (3,):
                    subc = re.finditer(
                        r"[\w]+",
                        text[(index + len(label)):]
                    ).__next__().group(0)
                else:
                    subc = re.finditer(
                        r"[\w]+",
                        text[(index + len(label)):]
                    ).next().group(0)

            except Exception as e:
                print("Error: %s" % str(e))
                subc = ""
            name = subc.strip() if subc else ""
            if name:
                variables.append(name)
            index = text.find(label, index + 1)
        return variables


class Server(NoServer):

    def __init__(self, value=None):
        NoServer.__init__(self, value)

    def command_inout(self, command, var=None):
        if hasattr(self, command):
            cmd = getattr(self, command)
            if var is not None:
                self.value = cmd(var)
            else:
                self.value = cmd()
        else:

            self.vars.append(var)
            self.commands.append(command)
        return self.value


# test fixture
class DescriberTest(unittest.TestCase):

    # constructor
    # \param methodName name of the test method

    def __init__(self, methodName):
        unittest.TestCase.__init__(self, methodName)

        self._bint = "int64" if IS64BIT else "int32"
        self._buint = "uint64" if IS64BIT else "uint32"
        self._bfloat = "float64" if IS64BIT else "float32"

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
                '<field type="NX_FLOAT64" name="field2">'
                '$datasources.pyeval2bds'
                '<strategy mode="FINAL"/>'
                '</field></group>'
                '</definition>'
            ),
            'pyeval2b2': (
                '<definition>$components.pyeval2b'
                '</definition>'
            ),
            'pyeval2b3': (
                '<definition>$components.pyeval2b\n$components.pyeval2a'
                '</definition>'
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
            'pyeval0': {
                'pyeval0ds': [
                    ('INIT', 'PYEVAL', '', 'NX_INT8', None, "field")],
            },
            'pyeval1': {
                'pyeval1ds': [
                    ('STEP', 'PYEVAL', '', 'NX_INT32', None, "field")],
            },
            'pyeval1a': {
                'pyeval1ads': [
                    ('STEP', 'PYEVAL', '', 'NX_INT32', None, "field")],
            },
            'pyeval2': {
                'pyeval2ds': [
                    ('STEP', 'PYEVAL', '', 'NX_FLOAT', None, "field")],
            },
            'pyeval2a': {
                'pyeval2ads': [
                    ('STEP', 'PYEVAL', '', 'NX_FLOAT', None, "field")],
            },
            'pyeval2b': {
                'pyeval2bds': [
                    ('FINAL', 'PYEVAL', '', 'NX_FLOAT64', None, "field")],
            },
            'pyeval2b2': {
                'pyeval2bds': [
                    ('FINAL', 'PYEVAL', '', 'NX_FLOAT64', None, "field")],
            },
            'pyeval2b3': {
                'pyeval2ads': [
                    ('STEP', 'PYEVAL', '', 'NX_FLOAT', None, "field")],
                'pyeval2bds': [
                    ('FINAL', 'PYEVAL', '', 'NX_FLOAT64', None, "field")],
            }
        }

        self.rescps_pfs = {
            'pyeval1a': {
                'pyeval1ads': [
                    ('STEP', 'PYEVAL', '', 'NX_INT32', None, "field")],
                'tann1c': [
                    ('STEP', 'TANGO', 'dsf/sd/we/myattr2', 'NX_INT32',
                     None, "datasource")],
            },
            'pyeval2a': {
                'pyeval2ads': [
                    ('STEP', 'PYEVAL', '', 'NX_FLOAT', None, "field")],
                'tann1c': [
                    ('STEP', 'TANGO', 'dsf/sd/we/myattr2', 'NX_FLOAT',
                     None, "datasource")],
                'tann0': [
                    ('STEP', 'TANGO', 'sf:12345/dsff/myattr', 'NX_FLOAT',
                     None, "datasource")],
            },
            'pyeval2b': {
                'pyeval2bds': [
                    ('FINAL', 'PYEVAL', '', 'NX_FLOAT64', None, "field")],
                'tann0': [
                    ('FINAL', 'TANGO', 'sf:12345/dsff/myattr', 'NX_FLOAT64',
                     None, "datasource")],
            },
            'pyeval2b2': {
                'pyeval2bds': [
                    ('FINAL', 'PYEVAL', '', 'NX_FLOAT64', None, "field")],
                'tann0': [
                    ('FINAL', 'TANGO', 'sf:12345/dsff/myattr', 'NX_FLOAT64',
                     None, "datasource")],
            },
            'pyeval2b3': {
                'pyeval2bds': [
                    ('FINAL', 'PYEVAL', '', 'NX_FLOAT64', None, "field")],
                'tann0': [
                    ('FINAL', 'TANGO', 'sf:12345/dsff/myattr', 'NX_FLOAT64',
                     None, "datasource"),
                    ('STEP', 'TANGO', 'sf:12345/dsff/myattr', 'NX_FLOAT',
                     None, "datasource")],
                'pyeval2ads': [
                    ('STEP', 'PYEVAL', '', 'NX_FLOAT', None, "field")],
                'tann1c': [
                    ('STEP', 'TANGO', 'dsf/sd/we/myattr2', 'NX_FLOAT',
                     None, "datasource")],
            },
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
                '$datasources.tann0'
                '<result name="myattr2">'
                'ds.myattr2 = "SomeThing"'
                '</result>'
                '</datasource>'
                '</definition>'
            ),
            'pyeval1ads': (
                '<definition>'
                '<datasource type="PYEVAL" name="pyeval1ads">'
                '$datasources.tann1c'
                '<result name="myattr2">'
                'ds.myattr2 = ds.tann1c'
                '</result>'
                '</datasource>'
                '</definition>'
            ),
            'pyeval2ds': (
                '<definition>'
                '<datasource type="PYEVAL" name="pyeval2ds">'
                '$datasources.tann1c'
                '$datasources.tann0'
                '<result name="myattr2">'
                'ds.myattr2 = "OMSS"'
                '</result>'
                '</datasource>'
                '</definition>'
            ),
            'pyeval2ads': (
                '<definition>'
                '<datasource type="PYEVAL" name="pyeval2ads">'
                '$datasources.tann1c'
                '$datasources.tann0'
                '<result name="myattr2">'
                'ds.myattr2 = ds.tann0 + ds.tann1c'
                '</result>'
                '</datasource>'
                '</definition>'
            ),
            'pyeval2bds': (
                '<definition>'
                '<datasource type="PYEVAL" name="pyeval2bds">'
                '$datasources.tann1c'
                '$datasources.tann0'
                '<result name="myattr2">'
                'ds.myattr2 = ds.tann0'
                '</result>'
                '</datasource>'
                '</definition>'
            ),
        }

        self.resdss_pfs = {
            'P1M_fileStartNum': ("P1M_fileStartNum", None, None),
            'P1M_fileDir': ("P1M_fileDir", None, None),
            'P1M_filePostfix': ("P1M_filePostfix", None, None),
            'P1M_filePrefix': ("P1M_filePrefix", None, None),
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
            'pyeval0ds': ('pyeval0ds', "PYEVAL", ""),
            'pyeval1ds': ('pyeval1ds', "PYEVAL", ""),
            'pyeval1ads': ('pyeval1ads', "PYEVAL", ""),
            'pyeval2ds': ('pyeval2ds', "PYEVAL", ""),
            'pyeval2ads': ('pyeval2ads', "PYEVAL", ""),
            'pyeval2bds': ('pyeval2bds', "PYEVAL", ""),
        }

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

    # test starter
    # \brief Common set up
    def setUp(self):
        print("\nsetting up...")
        print("SEED = %s" % self.__seed)

    # test closer
    # \brief Common tear down
    def tearDown(self):
        print("tearing down ...")

    def checkDS(self, rv, cv, dct=None):
        resdss = dct or self.resdss
        self.assertEqual(sorted(rv.keys()), sorted(cv))
        for vl in cv:
            self.assertEqual(resdss[vl][0], rv[vl].name)
            self.assertEqual(resdss[vl][1], rv[vl].dstype)
            self.assertEqual(resdss[vl][2], rv[vl].record)

    def checkDSList(self, rv, cv, dct=None):

        resdss = dct or self.resdss
        mset = set()
        for jr in rv:
            rr = json.loads(jr)
            vl = rr["dsname"]
            mset.add(vl)
            if not vl:
                vl = 'nn2'
            self.assertEqual(resdss[vl][0], rr["dsname"])
            self.assertEqual(resdss[vl][1], rr["dstype"])
            self.assertEqual(resdss[vl][2], rr["record"])
        self.assertEqual(len(rv), len(cv))
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
                res.append(ds)
        return res

    def checkCP(self, rv, cv, strategy=None, dstype=None, dct=None):
        rescps = dct or self.rescps
        self.assertEqual(sorted(set(rv[0].keys())), sorted(cv))
        for i in range(1):
            for cp, vl in rv[i].items():
                cres = rescps[cp]
                cresk = [ds for ds in cres.keys()
                         if self.dsfilter(cres[ds], strategy, dstype)]

                self.assertEqual(sorted(vl.keys()), sorted(cresk))
                for ds in cresk:
                    # print("EL", ds, cres[ds])
                    # print("VDS", vl[ds])
                    self.assertEqual(
                        sorted(self.dsfilter(cres[ds], strategy, dstype)),
                        sorted(vl[ds]))

    @classmethod
    def findElement(cls, cp, ds, vds, rv):
        found = False
        for el in rv:
            if el["cpname"] == cp and el["dsname"] == ds \
                    and el["strategy"] == vds[0] \
                    and el["dstype"] == vds[1] \
                    and el["record"] == vds[2] \
                    and el["nxtype"] == vds[3] \
                    and el["shape"] == vds[4] \
                    and el["parentobj"] == vds[5]:
                found = True
                break
        if not found:
            print("NOT FOUND %s %s %s %s" % (cp, ds, vds, rv))
        return found

    def checkICP(self, rv, cv, strategy=None, dstype=None, dct=None):
        rescps = dct or self.rescps
        dscnt = 0
        tcv = [k for k in cv if rescps[k]]
        for cp in tcv:
            print(cp)
            for ds, dss in rescps[cp].items():
                print("DS %s" % ds)
                for vds in dss:
                    print(vds)
                    if strategy is not None:
                        if vds[0] != strategy:
                            continue
                    if dstype is not None:
                        if vds[1] != dstype:
                            continue
                    self.assertTrue(self.findElement(cp, ds, vds, rv))
                    dscnt += 1
        print(len(rescps))
        print(rv)
        self.assertEqual(dscnt, len(rv))

    # constructor test
    # \brief It tests default settings
    def test_constructor(self):
        fun = sys._getframe().f_code.co_name
        print("Run: %s.%s() " % (self.__class__.__name__, fun))
        self.myAssertRaise(Exception, Describer, None, None)
        self.myAssertRaise(Exception, Describer, None, False)
        self.myAssertRaise(Exception, Describer, None, True)
        self.myAssertRaise(Exception, Describer, None, True, True)
        self.myAssertRaise(Exception, Describer, None, True, False)

    # constructor test
    # \brief It tests default settings
    def test_datasources(self):
        fun = sys._getframe().f_code.co_name
        print("Run: %s.%s() " % (self.__class__.__name__, fun))
        dsdict = {
            "ann": self.mydss["ann"]
        }
        server = NoServer()
        server.dsdict = dsdict
        des = Describer(server)
        self.assertEqual(des.dataSources(["myds2"]), [])

        des = Describer(server)
        res = des.dataSources(["ann"])
        self.checkDSList(res, ["ann"])

        des = Describer(server)
        res = des.dataSources(["ann", "myds2"])
        self.checkDSList(res, ["ann"])

        des = Describer(server)
        res = des.dataSources(["ann"], "TANGO")
        self.checkDSList(res, ["ann"])

        des = Describer(server)
        res = des.dataSources(["ann"], "CLIENT")
        self.checkDSList(res, [])

    # constructor test
    # \brief It tests default settings
    def test_datasources_server(self):
        fun = sys._getframe().f_code.co_name
        print("Run: %s.%s() " % (self.__class__.__name__, fun))
        dsdict = {
            "ann": self.mydss["ann"]
        }
        server = Server()
        server.dsdict = dsdict
        des = Describer(server)
        self.assertEqual(des.dataSources(["myds2"]), [])

        des = Describer(server)
        res = des.dataSources(["ann"])
        self.checkDSList(res, ["ann"])

        des = Describer(server)
        res = des.dataSources(["ann", "myds2"])
        self.checkDSList(res, ["ann"])

        des = Describer(server)
        res = des.dataSources(["ann"], "TANGO")
        self.checkDSList(res, ["ann"])

        des = Describer(server)
        res = des.dataSources(["ann"], "CLIENT")
        self.checkDSList(res, [])

    # constructor test
    # \brief It tests default settings
    def test_datasources_noargs(self):
        fun = sys._getframe().f_code.co_name
        print("Run: %s.%s() " % (self.__class__.__name__, fun))

        server = NoServer()
        server.dsdict = self.mydss

        des = Describer(server)
        res = des.dataSources()
        self.checkDSList(res, list(self.resdss.keys()))

    # constructor test
    # \brief It tests default settings
    def test_datasources_noargs_pfs(self):
        fun = sys._getframe().f_code.co_name
        print("Run: %s.%s() " % (self.__class__.__name__, fun))

        server = NoServer()
        server.dsdict = self.mydss

        des = Describer(server, pyevalfromscript=True)
        res = des.dataSources()
        res2 = dict(self.resdss)
        res2.update(self.resdss_pfs)
        self.checkDSList(res, list(res2.keys()), dct=res2)

    # constructor test
    # \brief It tests default settings
    def test_datasources_noargs_server_pfs(self):
        fun = sys._getframe().f_code.co_name
        print("Run: %s.%s() " % (self.__class__.__name__, fun))

        server = Server()
        server.dsdict = self.mydss

        des = Describer(server, pyevalfromscript=True)
        res = des.dataSources()
        res2 = dict(self.resdss)
        res2.update(self.resdss_pfs)
        self.checkDSList(res, list(res2.keys()), dct=res2)

    # constructor test
    # \brief It tests default settings
    def test_datasources_noargs_server(self):
        fun = sys._getframe().f_code.co_name
        print("Run: %s.%s() " % (self.__class__.__name__, fun))

        server = Server()
        server.dsdict = self.mydss

        des = Describer(server)
        res = des.dataSources()
        self.checkDSList(res, list(self.resdss.keys()))

    # constructor test
    # \brief It tests default settings
    def test_datasources_dstype(self):
        fun = sys._getframe().f_code.co_name
        print("Run: %s.%s() " % (self.__class__.__name__, fun))

        server = NoServer()
        server.dsdict = self.mydss

        des = Describer(server)
        res = des.dataSources(dstype="TANGO")
        self.checkDSList(
            res,
            [k for k in self.resdss.keys() if self.resdss[k][1] == 'TANGO'])

        des = Describer(server)
        res = des.dataSources(dstype="CLIENT")
        self.checkDSList(
            res,
            [k for k in self.resdss.keys() if self.resdss[k][1] == 'CLIENT'])

        des = Describer(server)
        res = des.dataSources(dstype="DB")
        self.checkDSList(
            res,
            [k for k in self.resdss.keys() if self.resdss[k][1] == 'DB'])

        des = Describer(server)
        res = des.dataSources(dstype="PYEVAL")
        self.checkDSList(
            res,
            [k for k in self.resdss.keys() if self.resdss[k][1] == 'PYEVAL'])

        des = Describer(server)
        res = des.dataSources(dstype="NEW")
        self.checkDSList(
            res,
            [k for k in self.resdss.keys() if self.resdss[k][1] == 'NEW'])

        des = Describer(server)
        res = des.dataSources(dstype="UNKNOWN")
        self.checkDSList(
            res,
            [k for k in self.resdss.keys() if self.resdss[k][1] == 'UNKNOWN'])

    # constructor test
    # \brief It tests default settings
    def test_datasources_dstype_server(self):
        fun = sys._getframe().f_code.co_name
        print("Run: %s.%s() " % (self.__class__.__name__, fun))

        server = Server()
        server.dsdict = self.mydss

        des = Describer(server)
        res = des.dataSources(dstype="TANGO")
        self.checkDSList(
            res,
            [k for k in self.resdss.keys() if self.resdss[k][1] == 'TANGO'])

        des = Describer(server)
        res = des.dataSources(dstype="CLIENT")
        self.checkDSList(
            res,
            [k for k in self.resdss.keys() if self.resdss[k][1] == 'CLIENT'])

        des = Describer(server)
        res = des.dataSources(dstype="DB")
        self.checkDSList(
            res,
            [k for k in self.resdss.keys() if self.resdss[k][1] == 'DB'])

        des = Describer(server)
        res = des.dataSources(dstype="PYEVAL")
        self.checkDSList(
            res,
            [k for k in self.resdss.keys() if self.resdss[k][1] == 'PYEVAL'])

        des = Describer(server)
        res = des.dataSources(dstype="NEW")
        self.checkDSList(
            res,
            [k for k in self.resdss.keys() if self.resdss[k][1] == 'NEW'])

        des = Describer(server)
        res = des.dataSources(dstype="UNKNOWN")
        self.checkDSList(
            res,
            [k for k in self.resdss.keys() if self.resdss[k][1] == 'UNKNOWN'])

    # constructor test
    # \brief It tests default settings
    def test_datasources_names(self):
        fun = sys._getframe().f_code.co_name
        print("Run: %s.%s() " % (self.__class__.__name__, fun))

        server = NoServer()
        server.dsdict = self.mydss

        names_list = [
            [],
            ["ann3"],
            ["ann", "nn2", "tann0", "dbtest", "slt1vgap"],
            ['nn', 'nn2', 'ann', 'ann2', 'ann3', 'ann4', 'ann5',
             'tann0', 'tann1', 'tann1b', 'tann1c', 'P1M_postrun',
             'dbtest', 'dbds', 'slt1vgap']
        ]

        for names in names_list:
            des = Describer(server)
            res = des.dataSources(names)
            self.checkDSList(res, names)

    # constructor test
    # \brief It tests default settings
    def test_datasources_names_server(self):
        fun = sys._getframe().f_code.co_name
        print("Run: %s.%s() " % (self.__class__.__name__, fun))

        server = Server()
        server.dsdict = self.mydss

        names_list = [
            [],
            ["ann3"],
            ["ann", "nn2", "tann0", "dbtest", "slt1vgap"],
            ['nn', 'nn2', 'ann', 'ann2', 'ann3', 'ann4',
             'ann5', 'tann0', 'tann1', 'tann1b', 'tann1c',
             'P1M_postrun', 'dbtest', 'dbds', 'slt1vgap']
        ]

        for names in names_list:
            des = Describer(server)
            res = des.dataSources(names)
            self.checkDSList(res, names)

    # constructor test
    # \brief It tests default settings
    def test_datasources_tree(self):
        fun = sys._getframe().f_code.co_name
        print("Run: %s.%s() " % (self.__class__.__name__, fun))
        dsdict = {
            "ann": self.mydss["ann"]
        }
        server = NoServer()
        server.dsdict = dsdict
        des = Describer(server, True)
        self.assertEqual(des.dataSources(["myds2"])[0], {})

        des = Describer(server, True)
        res = des.dataSources(["ann"])[0]
        self.checkDS(res, ["ann"])

        des = Describer(server, True)
        res = des.dataSources(["ann", "myds2"])[0]
        self.checkDS(res, ["ann"])

        des = Describer(server, True)
        res = des.dataSources(["ann"], "TANGO")[0]
        self.checkDS(res, ["ann"])

        des = Describer(server, True)
        res = des.dataSources(["ann"], "CLIENT")[0]
        self.checkDS(res, [])

    # constructor test
    # \brief It tests default settings
    def test_datasources_server_tree(self):
        fun = sys._getframe().f_code.co_name
        print("Run: %s.%s() " % (self.__class__.__name__, fun))
        dsdict = {
            "ann": self.mydss["ann"]
        }
        server = Server()
        server.dsdict = dsdict
        des = Describer(server, True)
        self.assertEqual(des.dataSources(["myds2"])[0], {})

        des = Describer(server, True)
        res = des.dataSources(["ann"])[0]
        self.checkDS(res, ["ann"])

        des = Describer(server, True)
        res = des.dataSources(["ann", "myds2"])[0]
        self.checkDS(res, ["ann"])

        des = Describer(server, True)
        res = des.dataSources(["ann"], "TANGO")[0]
        self.checkDS(res, ["ann"])

        des = Describer(server, True)
        res = des.dataSources(["ann"], "CLIENT")[0]
        self.checkDS(res, [])

    # constructor test
    # \brief It tests default settings
    def test_datasources_noargs_tree(self):
        fun = sys._getframe().f_code.co_name
        print("Run: %s.%s() " % (self.__class__.__name__, fun))

        server = NoServer()
        server.dsdict = self.mydss

        des = Describer(server, True)
        res = des.dataSources()[0]
        self.checkDS(res, list(self.resdss.keys()))

    # constructor test
    # \brief It tests default settings
    def test_datasources_noargs_tree_pfs(self):
        fun = sys._getframe().f_code.co_name
        print("Run: %s.%s() " % (self.__class__.__name__, fun))

        server = NoServer()
        server.dsdict = self.mydss

        des = Describer(server, True, pyevalfromscript=True)
        res = des.dataSources()[0]
        res2 = dict(self.resdss)
        res2.update(self.resdss_pfs)
        self.checkDS(res, list(res2.keys()), dct=res2)

    # constructor test
    # \brief It tests default settings
    def test_datasources_noargs_server_tree(self):
        fun = sys._getframe().f_code.co_name
        print("Run: %s.%s() " % (self.__class__.__name__, fun))

        server = Server()
        server.dsdict = self.mydss

        des = Describer(server, True)
        res = des.dataSources()[0]
        self.checkDS(res, list(self.resdss.keys()))

    # constructor test
    # \brief It tests default settings
    def test_datasources_noargs_server_tree_pfs(self):
        fun = sys._getframe().f_code.co_name
        print("Run: %s.%s() " % (self.__class__.__name__, fun))

        server = Server()
        server.dsdict = self.mydss

        des = Describer(server, True, pyevalfromscript=True)
        res = des.dataSources()[0]
        res2 = dict(self.resdss)
        res2.update(self.resdss_pfs)
        self.checkDS(res, list(res2.keys()), dct=res2)

    # constructor test
    # \brief It tests default settings
    def test_datasources_dstype_tree(self):
        fun = sys._getframe().f_code.co_name
        print("Run: %s.%s() " % (self.__class__.__name__, fun))

        server = NoServer()
        server.dsdict = self.mydss

        des = Describer(server, True)
        res = des.dataSources(dstype="TANGO")[0]
        self.checkDS(
            res,
            [k for k in self.resdss.keys() if self.resdss[k][1] == 'TANGO'])

        des = Describer(server, True)
        res = des.dataSources(dstype="CLIENT")[0]
        self.checkDS(
            res,
            [k for k in self.resdss.keys() if self.resdss[k][1] == 'CLIENT'])

        des = Describer(server, True)
        res = des.dataSources(dstype="DB")[0]
        self.checkDS(
            res,
            [k for k in self.resdss.keys() if self.resdss[k][1] == 'DB'])

        des = Describer(server, True)
        res = des.dataSources(dstype="PYEVAL")[0]
        self.checkDS(
            res,
            [k for k in self.resdss.keys() if self.resdss[k][1] == 'PYEVAL'])

        des = Describer(server, True)
        res = des.dataSources(dstype="NEW")[0]
        self.checkDS(
            res,
            [k for k in self.resdss.keys() if self.resdss[k][1] == 'NEW'])

        des = Describer(server, True)
        res = des.dataSources(dstype="UNKNOWN")[0]
        self.checkDS(
            res,
            [k for k in self.resdss.keys() if self.resdss[k][1] == 'UNKNOWN'])

    # constructor test
    # \brief It tests default settings
    def test_datasources_dstype_server_tree(self):
        fun = sys._getframe().f_code.co_name
        print("Run: %s.%s() " % (self.__class__.__name__, fun))

        server = Server()
        server.dsdict = self.mydss

        des = Describer(server, True)
        res = des.dataSources(dstype="TANGO")[0]
        self.checkDS(
            res,
            [k for k in self.resdss.keys() if self.resdss[k][1] == 'TANGO'])

        des = Describer(server, True)
        res = des.dataSources(dstype="CLIENT")[0]
        self.checkDS(
            res,
            [k for k in self.resdss.keys() if self.resdss[k][1] == 'CLIENT'])

        des = Describer(server, True)
        res = des.dataSources(dstype="DB")[0]
        self.checkDS(
            res,
            [k for k in self.resdss.keys() if self.resdss[k][1] == 'DB'])

        des = Describer(server, True)
        res = des.dataSources(dstype="PYEVAL")[0]
        self.checkDS(
            res,
            [k for k in self.resdss.keys() if self.resdss[k][1] == 'PYEVAL'])

        des = Describer(server, True)
        res = des.dataSources(dstype="NEW")[0]
        self.checkDS(
            res,
            [k for k in self.resdss.keys() if self.resdss[k][1] == 'NEW'])

        des = Describer(server, True)
        res = des.dataSources(dstype="UNKNOWN")[0]
        self.checkDS(
            res,
            [k for k in self.resdss.keys() if self.resdss[k][1] == 'UNKNOWN'])

    # constructor test
    # \brief It tests default settings
    def test_datasources_names_tree(self):
        fun = sys._getframe().f_code.co_name
        print("Run: %s.%s() " % (self.__class__.__name__, fun))

        server = NoServer()
        server.dsdict = self.mydss

        names_list = [
            [],
            ["ann3"],
            ["ann", "nn2", "tann0", "dbtest", "slt1vgap"],
            ['nn', 'nn2', 'ann', 'ann2', 'ann3', 'ann4', 'ann5',
             'tann0', 'tann1', 'tann1b', 'tann1c', 'P1M_postrun',
             'dbtest', 'dbds', 'slt1vgap']
        ]

        for names in names_list:
            des = Describer(server, True)
            res = des.dataSources(names)[0]
            self.checkDS(res, names)

    # constructor test
    # \brief It tests default settings
    def test_datasources_names_server_tree(self):
        fun = sys._getframe().f_code.co_name
        print("Run: %s.%s() " % (self.__class__.__name__, fun))

        server = Server()
        server.dsdict = self.mydss

        names_list = [
            [],
            ["ann3"],
            ["ann", "nn2", "tann0", "dbtest", "slt1vgap"],
            ['nn', 'nn2', 'ann', 'ann2', 'ann3', 'ann4',
             'ann5', 'tann0', 'tann1', 'tann1b', 'tann1c',
             'P1M_postrun', 'dbtest', 'dbds', 'slt1vgap']
        ]

        for names in names_list:
            des = Describer(server, True)
            res = des.dataSources(names)[0]
            self.checkDS(res, names)

    # constructor test
    # \brief It tests default settings
    def test_components_unknown(self):
        fun = sys._getframe().f_code.co_name
        print("Run: %s.%s() " % (self.__class__.__name__, fun))
        dsdict = {
            "ann": self.mydss["ann"]
        }

        server = NoServer()
        server.dsdict = dsdict
        des = Describer(server)
        self.assertEqual(des.components(), [])
        self.assertEqual(des.components(["unknown"]), [])

        des = Describer(server, True)
        self.assertEqual(des.components(), [{}])
        self.assertEqual(des.components(["unknown"]), [{}])

        server = Server()
        server.dsdict = dsdict
        des = Describer(server)
        self.assertEqual(des.components(), [])
        self.assertEqual(des.components(["unknown"]), [])

        des = Describer(server, True)
        self.assertEqual(des.components(), [{}])
        self.assertEqual(des.components(["unknown"]), [{}])

        des = Describer(server, True, True)
        self.assertEqual(des.components(), [{}])
        self.assertEqual(des.components(["unknown"]), [{}])

        des = Describer(server, True, False)
        self.assertEqual(des.components(), [{}])
        self.assertEqual(des.components(["unknown"]), [{}])

        des = Describer(server, False, True)
        self.assertEqual(des.components(), [])
        self.assertEqual(des.components(["unknown"]), [])

        des = Describer(server, False, False)
        self.assertEqual(des.components(), [])
        self.assertEqual(des.components(["unknown"]), [])

    # constructor test
    # \brief It tests default settings
    def test_components_noarg(self):
        server = NoServer()
        server.dsdict = self.mydss
        server.cpdict = self.mycps
        des = Describer(server)
        res = des.components()
        self.checkICP(res, list(self.rescps.keys()))

    # constructor test
    # \brief It tests default settings
    def test_components_noarg_pfs(self):
        server = NoServer()
        server.dsdict = self.mydss
        server.cpdict = self.mycps
        des = Describer(server, pyevalfromscript=True)
        res = des.components()
        res2 = dict(self.rescps)
        res2.update(self.rescps_pfs)
        self.checkICP(res, list(res2.keys()), dct=res2)

    # constructor test
    # \brief It tests default settings
    def test_components_noarg_tree(self):
        server = NoServer()
        server.dsdict = self.mydss
        server.cpdict = self.mycps
        des = Describer(server, True)
        res = des.components()
        self.checkCP(res, list(self.rescps.keys()))

    # constructor test
    # \brief It tests default settings
    def test_components_noarg_tree_pfs(self):
        server = NoServer()
        server.dsdict = self.mydss
        server.cpdict = self.mycps
        des = Describer(server, True, True)
        res = des.components()
        res2 = dict(self.rescps)
        res2.update(self.rescps_pfs)
        self.checkCP(res, list(self.rescps.keys()), dct=res2)

    # constructor test
    # \brief It tests default settings
    def test_components_noarg_server(self):
        server = Server()
        server.dsdict = self.mydss
        server.cpdict = self.mycps
        des = Describer(server)
        res = des.components()
        self.checkICP(res, list(self.rescps.keys()))

    # constructor test
    # \brief It tests default settings
    def test_components_noarg_server_pfs(self):
        server = Server()
        server.dsdict = self.mydss
        server.cpdict = self.mycps
        des = Describer(server, pyevalfromscript=True)
        res = des.components()
        res2 = dict(self.rescps)
        res2.update(self.rescps_pfs)
        self.checkICP(res, list(self.rescps.keys()), dct=res2)

    # constructor test
    # \brief It tests default settings
    def test_components_noarg_tree_server(self):
        server = Server()
        server.dsdict = self.mydss
        server.cpdict = self.mycps
        des = Describer(server, True)
        res = des.components()
        self.checkCP(res, list(self.rescps.keys()))

    # constructor test
    # \brief It tests default settings
    def test_components_noarg_tree_server_pfs(self):
        server = Server()
        server.dsdict = self.mydss
        server.cpdict = self.mycps
        des = Describer(server, True, True)
        res = des.components()
        res2 = dict(self.rescps)
        res2.update(self.rescps_pfs)
        self.checkCP(res, list(self.rescps.keys()), dct=res2)

    # constructor test
    # \brief It tests default settings
    def test_components_strategy_dstype(self):
        server = NoServer()
        server.dsdict = self.mydss
        server.cpdict = self.mycps

        dstypes = [None, 'CLIENT', 'TANGO', 'PYEVAL', 'NEW', 'UNKNOWN']
        strategies = [None, 'CONFIG', 'INIT', 'STEP', 'FINAL']

        for dst in dstypes:
            for st in strategies:
                des = Describer(server)
                res = des.components(strategy=st, dstype=dst)
                self.checkICP(res, list(self.rescps.keys()),
                              strategy=st, dstype=dst)

    # constructor test
    # \brief It tests default settings
    def test_components_strategy_dstype_pfs(self):
        server = NoServer()
        server.dsdict = self.mydss
        server.cpdict = self.mycps

        dstypes = [None, 'CLIENT', 'TANGO', 'PYEVAL', 'NEW', 'UNKNOWN']
        strategies = [None, 'CONFIG', 'INIT', 'STEP', 'FINAL']

        for dst in dstypes:
            for st in strategies:
                des = Describer(server, pyevalfromscript=True)
                res = des.components(strategy=st, dstype=dst)
                res2 = dict(self.rescps)
                res2.update(self.rescps_pfs)
                self.checkICP(res, list(self.rescps.keys()),
                              strategy=st, dstype=dst, dct=res2)

    # constructor test
    # \brief It tests default settings
    def test_components_strategy_dstype_server(self):
        server = Server()
        server.dsdict = self.mydss
        server.cpdict = self.mycps

        dstypes = [None, 'CLIENT', 'TANGO', 'PYEVAL', 'NEW', 'UNKNOWN']
        strategies = [None, 'CONFIG', 'INIT', 'STEP', 'FINAL']

        for dst in dstypes:
            for st in strategies:
                des = Describer(server)
                res = des.components(strategy=st, dstype=dst)
                self.checkICP(res, list(self.rescps.keys()),
                              strategy=st, dstype=dst)

    # constructor test
    # \brief It tests default settings
    def test_components_strategy_dstype_server_pfs(self):
        server = Server()
        server.dsdict = self.mydss
        server.cpdict = self.mycps

        dstypes = [None, 'CLIENT', 'TANGO', 'PYEVAL', 'NEW', 'UNKNOWN']
        strategies = [None, 'CONFIG', 'INIT', 'STEP', 'FINAL']

        for dst in dstypes:
            for st in strategies:
                des = Describer(server, pyevalfromscript=True)
                res = des.components(strategy=st, dstype=dst)
                res2 = dict(self.rescps)
                res2.update(self.rescps_pfs)
                self.checkICP(res, list(self.rescps.keys()),
                              strategy=st, dstype=dst, dct=res2)

    # constructor test
    # \brief It tests default settings
    def test_components_strategy_dstype_tree_pfs(self):
        server = NoServer()
        server.dsdict = self.mydss
        server.cpdict = self.mycps

        dstypes = [None, 'CLIENT', 'TANGO', 'PYEVAL', 'NEW', 'UNKNOWN']
        strategies = [None, 'CONFIG', 'INIT', 'STEP', 'FINAL']

        for dst in dstypes:
            for st in strategies:
                des = Describer(server, True, pyevalfromscript=True)
                res = des.components(strategy=st, dstype=dst)
                res2 = dict(self.rescps)
                res2.update(self.rescps_pfs)
                # print("RES", res)
                self.checkCP(res, list(self.rescps.keys()),
                             strategy=st, dstype=dst, dct=res2)

    # constructor test
    # \brief It tests default settings
    def test_components_strategy_dstype_tree(self):
        server = NoServer()
        server.dsdict = self.mydss
        server.cpdict = self.mycps

        dstypes = [None, 'CLIENT', 'TANGO', 'PYEVAL', 'NEW', 'UNKNOWN']
        strategies = [None, 'CONFIG', 'INIT', 'STEP', 'FINAL']

        for dst in dstypes:
            for st in strategies:
                des = Describer(server, True)
                res = des.components(strategy=st, dstype=dst)
                self.checkCP(res, list(self.rescps.keys()),
                             strategy=st, dstype=dst)

    # constructor test
    # \brief It tests default settings
    def test_components_strategy_dstype_server_tree(self):
        server = Server()
        server.dsdict = self.mydss
        server.cpdict = self.mycps

        dstypes = [None, 'CLIENT', 'TANGO', 'PYEVAL', 'NEW', 'UNKNOWN']
        strategies = [None, 'CONFIG', 'INIT', 'STEP', 'FINAL']

        for dst in dstypes:
            for st in strategies:
                des = Describer(server, True)
                res = des.components(strategy=st, dstype=dst)
                self.checkCP(res, list(self.rescps.keys()),
                             strategy=st, dstype=dst)

    # constructor test
    # \brief It tests default settings
    def test_components_strategy_dstype_server_tree_pfs(self):
        server = Server()
        server.dsdict = self.mydss
        server.cpdict = self.mycps

        dstypes = [None, 'CLIENT', 'TANGO', 'PYEVAL', 'NEW', 'UNKNOWN']
        strategies = [None, 'CONFIG', 'INIT', 'STEP', 'FINAL']

        for dst in dstypes:
            for st in strategies:
                des = Describer(server, True, True)
                res = des.components(strategy=st, dstype=dst)
                res2 = dict(self.rescps)
                res2.update(self.rescps_pfs)
                self.checkCP(res, list(self.rescps.keys()),
                             strategy=st, dstype=dst, dct=res2)

    # constructor test
    # \brief It tests default settings
    def test_components_noarg_mem(self):
        dstypes = [None, 'CLIENT', 'TANGO', 'PYEVAL', 'NEW', 'UNKNOWN']
        strategies = [None, 'CONFIG', 'INIT', 'STEP', 'FINAL']

        for dst in dstypes:
            for st in strategies:

                nmem = self.__rnd.randint(1, len(list(self.mycps.keys())) - 1)
                mem = self.__rnd.sample(list(self.mycps.keys()), nmem)

                server = NoServer()
                server.dsdict = self.mydss
                server.cpdict = self.mycps
                server.mcplist = list(mem)
                des = Describer(server)
                res = des.components(strategy=st, dstype=dst)
                self.checkICP(res, list(self.rescps.keys()),
                              strategy=st, dstype=dst)

    # constructor test
    # \brief It tests default settings
    def test_components_noarg_mem_tree(self):

        dstypes = [None, 'CLIENT', 'TANGO', 'PYEVAL', 'NEW', 'UNKNOWN']
        strategies = [None, 'CONFIG', 'INIT', 'STEP', 'FINAL']

        for dst in dstypes:
            for st in strategies:
                nmem = self.__rnd.randint(1, len(list(self.mycps.keys())) - 1)
                mem = self.__rnd.sample(list(self.mycps.keys()), nmem)

                server = NoServer()
                server.dsdict = self.mydss
                server.cpdict = self.mycps
                server.mcplist = list(mem)
                des = Describer(server, True)
                res = des.components(strategy=st, dstype=dst)
                self.checkCP(res, list(self.rescps.keys()),
                             strategy=st, dstype=dst)

    # constructor test
    # \brief It tests default settings
    def test_components_noarg_mem_server(self):
        dstypes = [None, 'CLIENT', 'TANGO', 'PYEVAL', 'NEW', 'UNKNOWN']
        strategies = [None, 'CONFIG', 'INIT', 'STEP', 'FINAL']

        for dst in dstypes:
            for st in strategies:

                nmem = self.__rnd.randint(
                    1, len(list(self.mydss.keys())) - 1)
                mem = self.__rnd.sample(list(self.mydss.keys()), nmem)

                server = Server()
                server.dsdict = self.mydss
                server.cpdict = self.mycps
                server.mcplist = list(mem)
                des = Describer(server)
                res = des.components(strategy=st, dstype=dst)
                self.checkICP(res, list(self.rescps.keys()),
                              strategy=st, dstype=dst)

    # constructor test
    # \brief It tests default settings
    def test_components_noarg_mem_tree_server(self):

        dstypes = [None, 'CLIENT', 'TANGO', 'PYEVAL', 'NEW', 'UNKNOWN']
        strategies = [None, 'CONFIG', 'INIT', 'STEP', 'FINAL']

        for dst in dstypes:
            for st in strategies:
                nmem = self.__rnd.randint(1, len(list(self.mycps.keys())) - 1)
                mem = self.__rnd.sample(list(self.mycps.keys()), nmem)

                server = Server()
                server.dsdict = self.mydss
                server.cpdict = self.mycps
                server.mcplist = list(mem)
                des = Describer(server, True)
                res = des.components(strategy=st, dstype=dst)
                self.checkCP(res, list(self.rescps.keys()),
                             strategy=st, dstype=dst)

    # constructor test
    # \brief It tests default settings
    def test_components_noarg_comp(self):
        dstypes = [None, 'CLIENT', 'TANGO', 'PYEVAL', 'NEW', 'UNKNOWN']
        strategies = [None, 'CONFIG', 'INIT', 'STEP', 'FINAL']

        for dst in dstypes:
            for st in strategies:

                ncps = self.__rnd.randint(1, len(list(self.mycps.keys())) - 1)
                cps = self.__rnd.sample(list(self.mycps.keys()), ncps)

                server = NoServer()
                server.dsdict = self.mydss
                server.cpdict = self.mycps
                des = Describer(server)
                res = des.components(cps, strategy=st, dstype=dst)
                self.checkICP(res, cps,
                              strategy=st, dstype=dst)

    # constructor test
    # \brief It tests default settings
    def test_components_noarg_comp_pfs(self):
        dstypes = [None, 'CLIENT', 'TANGO', 'PYEVAL', 'NEW', 'UNKNOWN']
        strategies = [None, 'CONFIG', 'INIT', 'STEP', 'FINAL']

        for dst in dstypes:
            for st in strategies:

                ncps = self.__rnd.randint(1, len(list(self.mycps.keys())) - 1)
                cps = self.__rnd.sample(list(self.mycps.keys()), ncps)

                server = NoServer()
                server.dsdict = self.mydss
                server.cpdict = self.mycps
                des = Describer(server, pyevalfromscript=True)
                res = des.components(cps, strategy=st, dstype=dst)
                res2 = dict(self.rescps)
                res2.update(self.rescps_pfs)
                self.checkICP(res, cps,
                              strategy=st, dstype=dst, dct=res2)

    # constructor test
    # \brief It tests default settings
    def test_components_noarg_tree_comp(self):

        dstypes = [None, 'CLIENT', 'TANGO', 'PYEVAL', 'NEW', 'UNKNOWN']
        strategies = [None, 'CONFIG', 'INIT', 'STEP', 'FINAL']

        for dst in dstypes:
            for st in strategies:
                ncps = self.__rnd.randint(1, len(list(self.mycps.keys())) - 1)
                cps = self.__rnd.sample(list(self.mycps.keys()), ncps)

                server = NoServer()
                server.dsdict = self.mydss
                server.cpdict = self.mycps
                des = Describer(server, True)
                res = des.components(cps, strategy=st, dstype=dst)
                self.checkCP(res, cps,
                             strategy=st, dstype=dst)

    # constructor test
    # \brief It tests default settings
    def test_components_noarg_tree_comp_pfs(self):

        dstypes = [None, 'CLIENT', 'TANGO', 'PYEVAL', 'NEW', 'UNKNOWN']
        strategies = [None, 'CONFIG', 'INIT', 'STEP', 'FINAL']

        for dst in dstypes:
            for st in strategies:
                ncps = self.__rnd.randint(1, len(list(self.mycps.keys())) - 1)
                cps = self.__rnd.sample(list(self.mycps.keys()), ncps)

                server = NoServer()
                server.dsdict = self.mydss
                server.cpdict = self.mycps
                des = Describer(server, True, pyevalfromscript=True)
                res = des.components(cps, strategy=st, dstype=dst)
                res2 = dict(self.rescps)
                res2.update(self.rescps_pfs)
                self.checkCP(res, cps,
                             strategy=st, dstype=dst, dct=res2)

    # constructor test
    # \brief It tests default settings
    def test_components_noarg_comp_server(self):
        dstypes = [None, 'CLIENT', 'TANGO', 'PYEVAL', 'NEW', 'UNKNOWN']
        strategies = [None, 'CONFIG', 'INIT', 'STEP', 'FINAL']

        for dst in dstypes:
            for st in strategies:

                ncps = self.__rnd.randint(1, len(list(self.mycps.keys())) - 1)
                cps = self.__rnd.sample(list(self.mycps.keys()), ncps)

                server = Server()
                server.dsdict = self.mydss
                server.cpdict = self.mycps
                des = Describer(server)
                res = des.components(cps, strategy=st, dstype=dst)
                self.checkICP(res, cps,
                              strategy=st, dstype=dst)

    # constructor test
    # \brief It tests default settings
    def test_components_noarg_comp_server_pfs(self):
        dstypes = [None, 'CLIENT', 'TANGO', 'PYEVAL', 'NEW', 'UNKNOWN']
        strategies = [None, 'CONFIG', 'INIT', 'STEP', 'FINAL']

        for dst in dstypes:
            for st in strategies:

                ncps = self.__rnd.randint(1, len(list(self.mycps.keys())) - 1)
                cps = self.__rnd.sample(list(self.mycps.keys()), ncps)

                server = Server()
                server.dsdict = self.mydss
                server.cpdict = self.mycps
                des = Describer(server, pyevalfromscript=True)
                res = des.components(cps, strategy=st, dstype=dst)
                res2 = dict(self.rescps)
                res2.update(self.rescps_pfs)
                self.checkICP(res, cps,
                              strategy=st, dstype=dst, dct=res2)

    # constructor test
    # \brief It tests default settings
    def test_components_noarg_tree_comp_server(self):

        dstypes = [None, 'CLIENT', 'TANGO', 'PYEVAL', 'NEW', 'UNKNOWN']
        strategies = [None, 'CONFIG', 'INIT', 'STEP', 'FINAL']

        for dst in dstypes:
            for st in strategies:
                ncps = self.__rnd.randint(1, len(list(self.mycps.keys())) - 1)
                cps = self.__rnd.sample(list(self.mycps.keys()), ncps)

                server = Server()
                server.dsdict = self.mydss
                server.cpdict = self.mycps
                des = Describer(server, True)
                res = des.components(cps, strategy=st, dstype=dst)
                self.checkCP(res, cps,
                             strategy=st, dstype=dst)

    # constructor test
    # \brief It tests default settings
    def test_components_noarg_tree_comp_server_pfs(self):

        dstypes = [None, 'CLIENT', 'TANGO', 'PYEVAL', 'NEW', 'UNKNOWN']
        strategies = [None, 'CONFIG', 'INIT', 'STEP', 'FINAL']

        for dst in dstypes:
            for st in strategies:
                ncps = self.__rnd.randint(1, len(list(self.mycps.keys())) - 1)
                cps = self.__rnd.sample(list(self.mycps.keys()), ncps)

                server = Server()
                server.dsdict = self.mydss
                server.cpdict = self.mycps
                des = Describer(server, True, True)
                res = des.components(cps, strategy=st, dstype=dst)
                res2 = dict(self.rescps)
                res2.update(self.rescps_pfs)
                self.checkCP(res, cps,
                             strategy=st, dstype=dst, dct=res2)

    # constructor test
    # \brief It tests default settings
    def test_components_noarg_mem_comp(self):
        dstypes = [None, 'CLIENT', 'TANGO', 'PYEVAL', 'NEW', 'UNKNOWN']
        strategies = [None, 'CONFIG', 'INIT', 'STEP', 'FINAL']

        for dst in dstypes:
            for st in strategies:

                ncps = self.__rnd.randint(1, len(list(self.mycps.keys())) - 1)
                cps = self.__rnd.sample(list(self.mycps.keys()), ncps)

                nmem = self.__rnd.randint(1, len(list(self.mycps.keys())) - 1)
                mem = self.__rnd.sample(list(self.mycps.keys()), nmem)
                server = NoServer()
                server.dsdict = self.mydss
                server.cpdict = self.mycps
                server.mcplist = list(mem)
                des = Describer(server)
                res = des.components(cps, strategy=st, dstype=dst)
                self.checkICP(res, cps,
                              strategy=st, dstype=dst)

    # constructor test
    # \brief It tests default settings
    def test_components_noarg_mem_tree_comp(self):

        dstypes = [None, 'CLIENT', 'TANGO', 'PYEVAL', 'NEW', 'UNKNOWN']
        strategies = [None, 'CONFIG', 'INIT', 'STEP', 'FINAL']

        for dst in dstypes:
            for st in strategies:
                ncps = self.__rnd.randint(1, len(list(self.mycps.keys())) - 1)
                cps = self.__rnd.sample(list(self.mycps.keys()), ncps)

                nmem = self.__rnd.randint(1, len(list(self.mycps.keys())) - 1)
                mem = self.__rnd.sample(list(self.mycps.keys()), nmem)
                server = NoServer()
                server.dsdict = self.mydss
                server.cpdict = self.mycps
                server.mcplist = list(mem)
                des = Describer(server, True)
                res = des.components(cps, strategy=st, dstype=dst)
                self.checkCP(res, cps,
                             strategy=st, dstype=dst)


if __name__ == '__main__':
    unittest.main()
