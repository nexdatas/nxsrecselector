#!/usr/bin/env python
#   This file is part of nexdatas - Tango Server for NeXus data writer
#
#    Copyright (C) 2014-2015 DESY, Jan Kotanski <jkotan@mail.desy.de>
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
## \file runtest.py
# the unittest runner
#

import os
import unittest

import logging
from optparse import OptionParser

#import TangoDataWriterTest
#import DescriberTest

import PyTango

## list of available databases
DB_AVAILABLE = []


import DSItemTest
import ExDSItemTest
import ExDSDictTest
import DescriberTest
import TangoDSItemTest
import CheckerItemTest
import CheckerThreadTest
import SelectionTest
import SelectorTest
import MacroServerPoolsTest
import DynamicComponentTest
import UtilsTest
import ProfileManagerTest
import SettingsTest
import NXSRecSelectorTest

#import TestServerSetUp


## main function
def main():
    levels = {'debug': logging.DEBUG,
              'info': logging.INFO,
              'warning': logging.WARNING,
              'error': logging.ERROR,
              'critical': logging.CRITICAL}

    usage = "usage:runtest.py [-l debug_level] "
    parser = OptionParser(usage=usage)

    parser.add_option(
        "-l", "--log", dest="log",
        help="logging level, i.e. debug, info, warning, error, critical")

    (options, _) = parser.parse_args()

    if options.log:
        level_name = options.log
        level = levels.get(level_name, logging.NOTSET)
        logging.basicConfig(level=level)

    ## test server
    ts = None

    ## test suit
    suite = unittest.TestSuite()

    suite.addTests(
        unittest.defaultTestLoader.loadTestsFromModule(SelectionTest))
    suite.addTests(
        unittest.defaultTestLoader.loadTestsFromModule(SelectorTest))
    suite.addTests(
        unittest.defaultTestLoader.loadTestsFromModule(ProfileManagerTest))

    suite.addTests(
        unittest.defaultTestLoader.loadTestsFromModule(TangoDSItemTest))
    suite.addTests(
        unittest.defaultTestLoader.loadTestsFromModule(CheckerItemTest))

    suite.addTests(
        unittest.defaultTestLoader.loadTestsFromModule(DSItemTest))

    suite.addTests(
        unittest.defaultTestLoader.loadTestsFromModule(ExDSItemTest))
    suite.addTests(
        unittest.defaultTestLoader.loadTestsFromModule(ExDSDictTest))

    suite.addTests(
        unittest.defaultTestLoader.loadTestsFromModule(DescriberTest))

    suite.addTests(
        unittest.defaultTestLoader.loadTestsFromModule(UtilsTest))

    suite.addTests(
        unittest.defaultTestLoader.loadTestsFromModule(CheckerThreadTest))

    suite.addTests(
        unittest.defaultTestLoader.loadTestsFromModule(MacroServerPoolsTest))

    suite.addTests(
        unittest.defaultTestLoader.loadTestsFromModule(DynamicComponentTest))

    suite.addTests(
        unittest.defaultTestLoader.loadTestsFromModule(SettingsTest))

    suite.addTests(
        unittest.defaultTestLoader.loadTestsFromModule(NXSRecSelectorTest))

    ## test runner
    runner = unittest.TextTestRunner()
    ## test result
    result = runner.run(suite)

    #   if ts:
    #       ts.tearDown()

if __name__ == "__main__":
    main()
