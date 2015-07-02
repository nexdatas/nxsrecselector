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
## \file DescriberTest.py
# unittests for field Tags running Tango Server
#
import unittest
import os
import sys
import subprocess
import random
import struct

from nxsrecconfig.Describer import Describer


## if 64-bit machione
IS64BIT = (struct.calcsize("P") == 8)


class NoServer(object):

    def __init__(self, value=None):
        self.reset(value)

    def reset(self, value=None):
        self.value = value
        self.commands = []
        self.vars = []
        self.dsdict = {}
        self.cpdict = {}
        self.icpdict = {}
        self.mcplist = []
        self.checkvariables = ""
        self.variables = ""

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

    def instantiatedComponents(self, names):
        if self.checkvariables != self.variables:
            raise Exception("Variables not set")
        self.vars.append(names)
        self.commands.append("components")
        return [self.icpdict[nm] for nm in names if nm in self.icpdict.keys()]

    def availableComponents(self):
        self.vars.append(None)
        self.commands.append("availableComponents")
        return list(self.cpdict.keys())

    def mandatoryComponents(self):
        self.vars.append(None)
        self.commands.append("mandatoryComponents")
        return list(self.mcplist)


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


## test fixture
class DescriberTest(unittest.TestCase):

    ## constructor
    # \param methodName name of the test method
    def __init__(self, methodName):
        unittest.TestCase.__init__(self, methodName)

        self._bint = "int64" if IS64BIT else "int32"
        self._buint = "uint64" if IS64BIT else "uint32"
        self._bfloat = "float64" if IS64BIT else "float32"

        self.mycps = {
            'mycp' : ('<?xml version=\'1.0\'?>'
                      '<definition>'
                      '<group type="NXcollection" name="dddd"/>'
                      '</definition>'),
            }

        self.mydss = {
            'nn': ('<definition><datasource type="TANGO">'
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
        print "\nsetting up..."

    ## test closer
    # \brief Common tear down
    def tearDown(self):
        print "tearing down ..."

    def checkDS(self, rv, cv):
        self.assertEqual(sorted(rv.keys()), sorted(cv))
        for vl in cv:
            self.assertEqual(self.resdss[vl][0], rv[vl].name)
            self.assertEqual(self.resdss[vl][1], rv[vl].dstype)
            self.assertEqual(self.resdss[vl][2], rv[vl].record)

    ## constructor test
    # \brief It tests default settings
    def test_constructor(self):
        fun = sys._getframe().f_code.co_name
        print "Run: %s.%s() " % (self.__class__.__name__, fun)
        el = Describer(None, None)
#        self.assertEqual(el.tagName, self._tfname)
#        self.assertEqual(el._tagAttrs, self._fattrs)
#        self.assertEqual(el.content, [])
#        self.assertEqual(el.doc, "")
#        self.assertEqual(el.last, None)
        el = Describer(None, False)
        el = Describer(None, True)

    ## constructor test
    # \brief It tests default settings
    def test_datasources(self):
        fun = sys._getframe().f_code.co_name
        print "Run: %s.%s() " % (self.__class__.__name__, fun)
        dsdict = {
            "ann": self.mydss["ann"]
            }
        server = NoServer()
        server.dsdict = dsdict
        des = Describer(server)
        self.assertEqual(des.dataSources(["myds2"]), {})

        des = Describer(server)
        res = des.dataSources(["ann"])
        self.checkDS(res, ["ann"])

        des = Describer(server)
        res = des.dataSources(["ann", "myds2"])
        self.checkDS(res, ["ann"])

        des = Describer(server)
        res = des.dataSources(["ann"], "TANGO")
        self.checkDS(res, ["ann"])

        des = Describer(server)
        res = des.dataSources(["ann"], "CLIENT")
        self.checkDS(res, [])

    ## constructor test
    # \brief It tests default settings
    def test_datasources_server(self):
        fun = sys._getframe().f_code.co_name
        print "Run: %s.%s() " % (self.__class__.__name__, fun)
        dsdict = {
            "ann": self.mydss["ann"]
            }
        server = Server()
        server.dsdict = dsdict
        des = Describer(server)
        self.assertEqual(des.dataSources(["myds2"]), {})

        des = Describer(server)
        res = des.dataSources(["ann"])
        self.checkDS(res, ["ann"])

        des = Describer(server)
        res = des.dataSources(["ann", "myds2"])
        self.checkDS(res, ["ann"])

        des = Describer(server)
        res = des.dataSources(["ann"], "TANGO")
        self.checkDS(res, ["ann"])

        des = Describer(server)
        res = des.dataSources(["ann"], "CLIENT")
        self.checkDS(res, [])

    ## constructor test
    # \brief It tests default settings
    def test_datasources_noargs(self):
        fun = sys._getframe().f_code.co_name
        print "Run: %s.%s() " % (self.__class__.__name__, fun)

        server = NoServer()
        server.dsdict = self.mydss

        des = Describer(server)
        res = des.dataSources()
        self.checkDS(res, self.resdss.keys())

    ## constructor test
    # \brief It tests default settings
    def test_datasources_noargs_server(self):
        fun = sys._getframe().f_code.co_name
        print "Run: %s.%s() " % (self.__class__.__name__, fun)

        server = Server()
        server.dsdict = self.mydss

        des = Describer(server)
        res = des.dataSources()
        self.checkDS(res, self.resdss.keys())

    ## constructor test
    # \brief It tests default settings
    def test_datasources_dstype(self):
        fun = sys._getframe().f_code.co_name
        print "Run: %s.%s() " % (self.__class__.__name__, fun)

        server = NoServer()
        server.dsdict = self.mydss

        des = Describer(server)
        res = des.dataSources(dstype="TANGO")
        self.checkDS(
            res,
            [k for k in self.resdss.keys() if self.resdss[k][1] == 'TANGO'])

        des = Describer(server)
        res = des.dataSources(dstype="CLIENT")
        self.checkDS(
            res,
            [k for k in self.resdss.keys() if self.resdss[k][1] == 'CLIENT'])

        des = Describer(server)
        res = des.dataSources(dstype="DB")
        self.checkDS(
            res,
            [k for k in self.resdss.keys() if self.resdss[k][1] == 'DB'])

        des = Describer(server)
        res = des.dataSources(dstype="PYEVAL")
        self.checkDS(
            res,
            [k for k in self.resdss.keys() if self.resdss[k][1] == 'PYEVAL'])

        des = Describer(server)
        res = des.dataSources(dstype="NEW")
        self.checkDS(
            res,
            [k for k in self.resdss.keys() if self.resdss[k][1] == 'NEW'])

        des = Describer(server)
        res = des.dataSources(dstype="UNKNOWN")
        self.checkDS(
            res,
            [k for k in self.resdss.keys() if self.resdss[k][1] == 'UNKNOWN'])

    ## constructor test
    # \brief It tests default settings
    def test_datasources_dstype_server(self):
        fun = sys._getframe().f_code.co_name
        print "Run: %s.%s() " % (self.__class__.__name__, fun)

        server = Server()
        server.dsdict = self.mydss

        des = Describer(server)
        res = des.dataSources(dstype="TANGO")
        self.checkDS(
            res,
            [k for k in self.resdss.keys() if self.resdss[k][1] == 'TANGO'])

        des = Describer(server)
        res = des.dataSources(dstype="CLIENT")
        self.checkDS(
            res,
            [k for k in self.resdss.keys() if self.resdss[k][1] == 'CLIENT'])

        des = Describer(server)
        res = des.dataSources(dstype="DB")
        self.checkDS(
            res,
            [k for k in self.resdss.keys() if self.resdss[k][1] == 'DB'])

        des = Describer(server)
        res = des.dataSources(dstype="PYEVAL")
        self.checkDS(
            res,
            [k for k in self.resdss.keys() if self.resdss[k][1] == 'PYEVAL'])

        des = Describer(server)
        res = des.dataSources(dstype="NEW")
        self.checkDS(
            res,
            [k for k in self.resdss.keys() if self.resdss[k][1] == 'NEW'])

        des = Describer(server)
        res = des.dataSources(dstype="UNKNOWN")
        self.checkDS(
            res,
            [k for k in self.resdss.keys() if self.resdss[k][1] == 'UNKNOWN'])

    ## constructor test
    # \brief It tests default settings
    def test_datasources_names(self):
        fun = sys._getframe().f_code.co_name
        print "Run: %s.%s() " % (self.__class__.__name__, fun)

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
            self.checkDS(res, names)

    ## constructor test
    # \brief It tests default settings
    def test_datasources_names_server(self):
        fun = sys._getframe().f_code.co_name
        print "Run: %s.%s() " % (self.__class__.__name__, fun)

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
            self.checkDS(res, names)

    ## constructor test
    # \brief It tests default settings
    def test_components_unknown(self):
        fun = sys._getframe().f_code.co_name
        print "Run: %s.%s() " % (self.__class__.__name__, fun)
        dsdict = {
            "ann": self.mydss["ann"]
            }

        server = NoServer()
        server.dsdict = dsdict
        des = Describer(server)
        self.assertEqual(des.components(), [])
        self.assertEqual(des.components(["unknown"]), [])

        des = Describer(server, True)
        self.assertEqual(des.components(), [{}, {}])
        self.assertEqual(des.components(["unknown"]), [{}, {}])

        server = Server()
        server.dsdict = dsdict
        des = Describer(server)
        self.assertEqual(des.components(), [])
        self.assertEqual(des.components(["unknown"]), [])

        des = Describer(server, True)
        self.assertEqual(des.components(), [{}, {}])
        self.assertEqual(des.components(["unknown"]), [{}, {}])


    ## constructor test
    # \brief It tests default settings
    def test_components_noarg(self):
        server = NoServer()
        server.dsdict = self.mydss
        server.cpdict = self.mycps
        des = Describer(server)
        self.assertEqual(des.components(), [])

if __name__ == '__main__':
    unittest.main()
