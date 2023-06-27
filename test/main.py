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
# \package test nexdatas
# \file runtest.py
# the unittest runner
#

import sys
import unittest

import logging
from optparse import OptionParser

# import TangoDataWriter_test
# import Describer_test

import DSItem_test
import ExDSItem_test
import ExDSDict_test
import Describer_test
import TangoDSItem_test
import CheckerItem_test
import CheckerThread_test
import Selection_test
import Selector_test
import Selector2_test
import MacroServerPools_test
import MacroServerPools2_test
import DynamicComponent_test
import Utils_test
import ProfileManager_test
import ProfileManager2_test
import ProfileManager3_test
import BasicSettings_test
import BasicSettings2_test
import BasicSettings3_test
import ExtraSettings_test
import ExtraSettings2_test
import ExtraSettings3_test
import BasicNXSRecSelector_test
import BasicNXSRecSelector2_test
import BasicNXSRecSelector3_test
import ExtraNXSRecSelector_test
import ExtraNXSRecSelector2_test
import ExtraNXSRecSelector3_test
import Converter_test
import ConverterXtoY_test
import Converter1to2_test
import Converter2to1_test
import Converter3to2_test
import Converter2to3_test
import StreamSet_test

# list of available databases
DB_AVAILABLE = []


# import TestServerSetUp


# main function
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

    # test server
    ts = None

    # test suit
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
        unittest.defaultTestLoader.loadTestsFromModule(Selection_test))
    basicsuite.addTests(
        unittest.defaultTestLoader.loadTestsFromModule(Selector2_test))
    basicsuite.addTests(
        unittest.defaultTestLoader.loadTestsFromModule(Selector_test))
    basicsuite.addTests(
        unittest.defaultTestLoader.loadTestsFromModule(TangoDSItem_test))
    basicsuite.addTests(
        unittest.defaultTestLoader.loadTestsFromModule(CheckerItem_test))
    basicsuite.addTests(
        unittest.defaultTestLoader.loadTestsFromModule(DSItem_test))
    basicsuite.addTests(
        unittest.defaultTestLoader.loadTestsFromModule(ExDSItem_test))
    basicsuite.addTests(
        unittest.defaultTestLoader.loadTestsFromModule(ExDSDict_test))
    basicsuite.addTests(
        unittest.defaultTestLoader.loadTestsFromModule(Describer_test))
    basicsuite.addTests(
        unittest.defaultTestLoader.loadTestsFromModule(Utils_test))
    basicsuite.addTests(
        unittest.defaultTestLoader.loadTestsFromModule(StreamSet_test))
    basicsuite.addTests(
        unittest.defaultTestLoader.loadTestsFromModule(Converter_test))
    basicsuite.addTests(
        unittest.defaultTestLoader.loadTestsFromModule(ConverterXtoY_test))
    basicsuite.addTests(
        unittest.defaultTestLoader.loadTestsFromModule(Converter1to2_test))
    basicsuite.addTests(
        unittest.defaultTestLoader.loadTestsFromModule(Converter2to1_test))
    basicsuite.addTests(
        unittest.defaultTestLoader.loadTestsFromModule(Converter3to2_test))
    basicsuite.addTests(
        unittest.defaultTestLoader.loadTestsFromModule(Converter2to3_test))
    basicsuite.addTests(
        unittest.defaultTestLoader.loadTestsFromModule(CheckerThread_test))
    basicsuite.addTests(
        unittest.defaultTestLoader.loadTestsFromModule(MacroServerPools_test))
    basicsuite.addTests(
        unittest.defaultTestLoader.loadTestsFromModule(MacroServerPools2_test))
    basicsuite.addTests(
        unittest.defaultTestLoader.loadTestsFromModule(DynamicComponent_test))

    profilesuite.addTests(
        unittest.defaultTestLoader.loadTestsFromModule(ProfileManager_test))

    profilesuite.addTests(
        unittest.defaultTestLoader.loadTestsFromModule(ProfileManager2_test))

    profilesuite.addTests(
        unittest.defaultTestLoader.loadTestsFromModule(ProfileManager3_test))

    settingssuite1.addTests(
        unittest.defaultTestLoader.loadTestsFromModule(BasicSettings_test))

    settingssuite1b.addTests(
        unittest.defaultTestLoader.loadTestsFromModule(BasicSettings2_test))

    settingssuite1b.addTests(
        unittest.defaultTestLoader.loadTestsFromModule(BasicSettings3_test))

    settingssuite2.addTests(
        unittest.defaultTestLoader.loadTestsFromModule(ExtraSettings_test))

    settingssuite2b.addTests(
        unittest.defaultTestLoader.loadTestsFromModule(ExtraSettings2_test))

    settingssuite2b.addTests(
        unittest.defaultTestLoader.loadTestsFromModule(ExtraSettings3_test))

    serversuite1.addTests(
        unittest.defaultTestLoader.loadTestsFromModule(
            BasicNXSRecSelector_test))

    serversuite1b.addTests(
        unittest.defaultTestLoader.loadTestsFromModule(
            BasicNXSRecSelector2_test))

    serversuite1b.addTests(
        unittest.defaultTestLoader.loadTestsFromModule(
            BasicNXSRecSelector3_test))

    serversuite2.addTests(
        unittest.defaultTestLoader.loadTestsFromModule(
            ExtraNXSRecSelector_test))

    serversuite2b.addTests(
        unittest.defaultTestLoader.loadTestsFromModule(
            ExtraNXSRecSelector2_test))

    serversuite2b.addTests(
        unittest.defaultTestLoader.loadTestsFromModule(
            ExtraNXSRecSelector3_test))

    # test runner
    runner = unittest.TextTestRunner()

    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument('args', metavar='name', type=str, nargs='*',
                        help='suite names: all, basic, '
                        'basicsettings, basicserver, '
                        'extrasettings, extraserver '
                        )
    options = parser.parse_args()

    namesuite = {
        "basic": [basicsuite, profilesuite],
        "basicsettings": [settingssuite1, settingssuite1b],
        "basicserver": [serversuite1, serversuite1b],
        "extrasettings": [settingssuite2, settingssuite2b],
        "extraserver": [serversuite2, serversuite2b],
    }

    print(options.args)
    if not options.args or 'all' in options.args:
        options.args = list(namesuite.keys())

    ts = []
    for nm in options.args:
        if nm in namesuite.keys():
            ts.extend(namesuite[nm])

    suite = unittest.TestSuite(ts)

    # test result
    result = runner.run(suite).wasSuccessful()
    sys.exit(not result)


if __name__ == "__main__":
    main()
