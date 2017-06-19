#!/usr/bin/env python
#   This file is part of nexdatas - Tango Server for NeXus data writer
#
#    Copyright (C) 2012-2017 DESY, Jan Kotanski <jkotan@mail.desy.de>
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
# \file MacroServerPools2Test.py
# unittests for field Tags running Tango Server
#
import unittest

import TestPool2SetUp
import MacroServerPoolsTest


# test fixture
class MacroServerPools2Test(MacroServerPoolsTest.MacroServerPoolsTest):

    # constructor
    # \param methodName name of the test method

    def __init__(self, methodName):
        MacroServerPoolsTest.MacroServerPoolsTest.__init__(self, methodName)

        self._pool = TestPool2SetUp.TestPool2SetUp()


if __name__ == '__main__':
    unittest.main()
