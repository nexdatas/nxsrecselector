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
# \file SettingsTest.py
# unittests for TangoDsItemTest running Tango Server

import unittest

try:
    import Settings2_test
except Exception:
    from . import Settings2_test


# test fixture
class Settings3Test(Settings2_test.Settings2Test):

    # constructor
    # \param methodName name of the test method

    def __init__(self, methodName):
        Settings2_test.Settings2Test.__init__(self, methodName)
        self._masterTimerFirst = True

    def openRecSelector(self):
        st = Settings2_test.Settings2Test.openRecSelector(self)
        st.masterTimer = False
        st.masterTimerFirst = True
        return st

    def openRecSelector2(self):
        st = Settings2_test.Settings2Test.openRecSelector(self)
        st.masterTimer = False
        st.masterTimerFirst = True
        return st


if __name__ == '__main__':
    unittest.main()
