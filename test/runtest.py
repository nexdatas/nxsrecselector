#!/usr/bin/env python
#   This file is part of nexdatas - Tango Server for NeXus data writer
#
#    Copyright (C) 2014-2017 DESY, Jan Kotanski <jkotan@mail.desy.de>
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
import sys
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
import Selector2Test
import MacroServerPoolsTest
import MacroServerPools2Test
import DynamicComponentTest
import UtilsTest
import ProfileManagerTest
import ProfileManager2Test
import BasicSettingsTest
import BasicSettings2Test
import ExtraSettingsTest
import ExtraSettings2Test
import BasicNXSRecSelectorTest
import BasicNXSRecSelector2Test
import ExtraNXSRecSelectorTest
import ExtraNXSRecSelector2Test
import ConverterTest
import ConverterXtoYTest
import Converter1to2Test
import Converter2to1Test
import Converter3to2Test
import Converter2to3Test
import StreamsTest

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
    basicsuite = unittest.TestSuite()
    profilesuite = unittest.TestSuite()
    settingssuite1 = unittest.TestSuite()
    serversuite1 = unittest.TestSuite()
    settingssuite1b = unittest.TestSuite()
    serversuite1b = unittest.TestSuite()
    settingssuite2 = unittest.TestSuite()
    serversuite2 = unittest.TestSuite()
    settingssuite2b = unittest.TestSuite()
    serversuite2b = unittest.TestSuite()

    basicsuite.addTests(
        unittest.defaultTestLoader.loadTestsFromModule(SelectionTest))
    basicsuite.addTests(
        unittest.defaultTestLoader.loadTestsFromModule(Selector2Test))
    basicsuite.addTests(
        unittest.defaultTestLoader.loadTestsFromModule(SelectorTest))
    basicsuite.addTests(
        unittest.defaultTestLoader.loadTestsFromModule(TangoDSItemTest))
    basicsuite.addTests(
        unittest.defaultTestLoader.loadTestsFromModule(CheckerItemTest))
    basicsuite.addTests(
        unittest.defaultTestLoader.loadTestsFromModule(DSItemTest))
    basicsuite.addTests(
        unittest.defaultTestLoader.loadTestsFromModule(ExDSItemTest))
    basicsuite.addTests(
        unittest.defaultTestLoader.loadTestsFromModule(ExDSDictTest))
    basicsuite.addTests(
        unittest.defaultTestLoader.loadTestsFromModule(DescriberTest))
    basicsuite.addTests(
        unittest.defaultTestLoader.loadTestsFromModule(UtilsTest))
    basicsuite.addTests(
        unittest.defaultTestLoader.loadTestsFromModule(StreamsTest))
    basicsuite.addTests(
        unittest.defaultTestLoader.loadTestsFromModule(ConverterTest))
    basicsuite.addTests(
        unittest.defaultTestLoader.loadTestsFromModule(ConverterXtoYTest))
    basicsuite.addTests(
        unittest.defaultTestLoader.loadTestsFromModule(Converter1to2Test))
    basicsuite.addTests(
        unittest.defaultTestLoader.loadTestsFromModule(Converter2to1Test))
    basicsuite.addTests(
        unittest.defaultTestLoader.loadTestsFromModule(Converter3to2Test))
    basicsuite.addTests(
        unittest.defaultTestLoader.loadTestsFromModule(Converter2to3Test))
    basicsuite.addTests(
        unittest.defaultTestLoader.loadTestsFromModule(CheckerThreadTest))
    basicsuite.addTests(
        unittest.defaultTestLoader.loadTestsFromModule(MacroServerPoolsTest))
    basicsuite.addTests(
        unittest.defaultTestLoader.loadTestsFromModule(MacroServerPools2Test))
    basicsuite.addTests(
        unittest.defaultTestLoader.loadTestsFromModule(DynamicComponentTest))

    profilesuite.addTests(
        unittest.defaultTestLoader.loadTestsFromModule(ProfileManagerTest))

    profilesuite.addTests(
        unittest.defaultTestLoader.loadTestsFromModule(ProfileManager2Test))

    settingssuite1.addTests(
        unittest.defaultTestLoader.loadTestsFromModule(BasicSettingsTest))

    settingssuite1b.addTests(
        unittest.defaultTestLoader.loadTestsFromModule(BasicSettings2Test))

    settingssuite2.addTests(
        unittest.defaultTestLoader.loadTestsFromModule(ExtraSettingsTest))

    settingssuite2b.addTests(
        unittest.defaultTestLoader.loadTestsFromModule(ExtraSettings2Test))


    serversuite1.addTests(
        unittest.defaultTestLoader.loadTestsFromModule(BasicNXSRecSelectorTest))

    serversuite1b.addTests(
        unittest.defaultTestLoader.loadTestsFromModule(BasicNXSRecSelector2Test))

    serversuite2.addTests(
        unittest.defaultTestLoader.loadTestsFromModule(ExtraNXSRecSelectorTest))

    serversuite2b.addTests(
        unittest.defaultTestLoader.loadTestsFromModule(ExtraNXSRecSelector2Test))

    ## test runner
    runner = unittest.TextTestRunner()

    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument('args', metavar='name', type=str, nargs='*',
                        help='suite names: all, basic, profile, '
                        'basicsettings, basicserver, '
                        'basicsettings2, basicserver2, '
                        'extrasettings, extraserver, '
                        'extrasettings2, extraserver2',
                    )
    options = parser.parse_args()

    namesuite = {
        "basic": basicsuite,
        "profile": profilesuite,
        "basicsettings": settingssuite1,
        "basicserver": serversuite1,
        "basicsettings2": settingssuite1b,
        "basicserver2": serversuite1b,
        "extrasettings": settingssuite2,
        "extraserver": serversuite2,
        "extrasettings2": settingssuite2b,
        "extraserver2": serversuite2b,
    }
    
    print options.args
    if not options.args or 'all' in options.args:
        options.args = namesuite.keys()

    suite = unittest.TestSuite(
        [namesuite[nm] for nm in options.args if nm in namesuite.keys()])
    
    ## test result
    result = runner.run(suite).wasSuccessful()
    sys.exit(not result)
    
if __name__ == "__main__":
    main()
