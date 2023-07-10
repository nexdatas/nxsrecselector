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
#
import unittest
import sys
import struct

try:
    import tango
except Exception:
    import PyTango as tango

try:
    import Settings_test
except Exception:
    from . import Settings_test


try:
    import TestPool2SetUp
except Exception:
    from . import TestPool2SetUp


import logging
logger = logging.getLogger()

# if 64-bit machione
IS64BIT = (struct.calcsize("P") == 8)

# list of available databases
DB_AVAILABLE = []

#: tango version
TGVER = tango.__version_info__[0]

if sys.version_info > (3,):
    long = int


class NotEqualException(Exception):
    pass


try:
    import MySQLdb
    # connection arguments to MYSQL DB
    mydb = MySQLdb.connect({})
    mydb.close()
    DB_AVAILABLE.append("MYSQL")
except Exception:
    try:
        import MySQLdb
    # connection arguments to MYSQL DB
        args = {'db': 'nxsconfig',
                'read_default_file': '/etc/my.cnf', 'use_unicode': True}
    # inscance of MySQLdb
        mydb = MySQLdb.connect(**args)
        mydb.close()
        DB_AVAILABLE.append("MYSQL")
    except Exception:
        try:
            import MySQLdb
            from os.path import expanduser
            home = expanduser("~")
        # connection arguments to MYSQL DB
            args2 = {'db': 'nxsconfig',
                     'read_default_file': '%s/.my.cnf' % home,
                     'use_unicode': True}
        # inscance of MySQLdb
            mydb = MySQLdb.connect(**args2)
            mydb.close()
            DB_AVAILABLE.append("MYSQL")

        except ImportError as e:
            print("MYSQL not available: %s" % e)
        except Exception as e:
            print("MYSQL not available: %s" % e)
        except Exception:
            print("MYSQL not available")


# test fixture
class Settings2Test(Settings_test.SettingsTest):

    # constructor
    # \param methodName name of the test method

    def __init__(self, methodName):
        Settings_test.SettingsTest.__init__(self, methodName)
        self._pool = TestPool2SetUp.TestPool2SetUp()


if __name__ == '__main__':
    unittest.main()
