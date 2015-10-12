#!/usr/bin/env python
#   This file is part of nexdatas - Tango Server for NeXus data writer
#
#    Copyright (C) 2012-2015 DESY, Jan Kotanski <jkotan@mail.desy.de>
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
## \file StreamsTest.py
# unittests for field Tags running Tango Server
#
import unittest
import os
import sys
import subprocess
import random
import struct
import binascii
import string
from cStringIO import StringIO

from nxswriter import Streams

## if 64-bit machione
IS64BIT = (struct.calcsize("P") == 8)


## test fixture
class StreamsTest(unittest.TestCase):

    ## constructor
    # \param methodName name of the test method
    def __init__(self, methodName):
        unittest.TestCase.__init__(self, methodName)
        try:
            self.__seed = long(binascii.hexlify(os.urandom(16)), 16)
        except NotImplementedError:
            self.__seed = long(time.time() * 256)

        self.__rnd = random.Random(self.__seed)

        self.old_stdout = sys.stdout
        self.old_stderr = sys.stderr
        self.mystdout = StringIO()
        self.mystderr = StringIO()
        self.mystd1 = StringIO()
        self.mystd2 = StringIO()
        self.mystd3 = StringIO()
        self.mystd4 = StringIO()
        self.mystd5 = StringIO()

    def getRandomString(self, maxsize):
        letters = [chr(i) for i in range(256)]
        size = self.__rnd.randint(1, maxsize)
        return ''.join(self.__rnd.choice(letters) for _ in range(size))

    ## test starter
    # \brief Common set up
    def setUp(self):
        print "SEED =", self.__seed
        print "\nsetting up..."
        hasattr(Streams, "log_fatal")
        hasattr(Streams, "log_error")
        hasattr(Streams, "log_warn")
        hasattr(Streams, "log_info")
        hasattr(Streams, "log_debug")
        Streams.log_fatal = None
        Streams.log_error = None
        Streams.log_warn = None
        Streams.log_info = None
        Streams.log_debug = None

    ## test closer
    # \brief Common tear down
    def tearDown(self):
        sys.stdout = self.old_stdout
        sys.stderr = self.old_stderr
        print "tearing down ..."

    def test_fatal(self):
        fun = sys._getframe().f_code.co_name
        print "Run: %s.%s() " % (self.__class__.__name__, fun)
        for i in range(20):
            name = self.getRandomString(100)
            sys.stdout = self.mystdout = StringIO()
            sys.stderr = self.mystderr = StringIO()
            if i % 2:
                Streams.fatal(name)
            else:
                Streams.fatal(name, std=True)
            self.assertEqual(Streams.log_fatal, None)
            self.assertEqual(Streams.log_error, None)
            self.assertEqual(Streams.log_warn, None)
            self.assertEqual(Streams.log_info, None)
            self.assertEqual(Streams.log_debug, None)
            self.assertEqual(self.mystdout.getvalue(), "")
            self.assertEqual(self.mystderr.getvalue(), name + '\n')
            sys.stdout = self.old_stdout
            sys.stderr = self.old_stderr

    def test_fatal_nostd(self):
        fun = sys._getframe().f_code.co_name
        print "Run: %s.%s() " % (self.__class__.__name__, fun)
        for i in range(20):
            name = self.getRandomString(100)
            sys.stdout = self.mystdout = StringIO()
            sys.stderr = self.mystderr = StringIO()
            Streams.fatal(name, std=False)
            self.assertEqual(Streams.log_fatal, None)
            self.assertEqual(Streams.log_error, None)
            self.assertEqual(Streams.log_warn, None)
            self.assertEqual(Streams.log_info, None)
            self.assertEqual(Streams.log_debug, None)
            self.assertEqual(self.mystdout.getvalue(), "")
            self.assertEqual(self.mystderr.getvalue(), "")
            sys.stdout = self.old_stdout
            sys.stderr = self.old_stderr

    def test_fatal_log(self):
        fun = sys._getframe().f_code.co_name
        print "Run: %s.%s() " % (self.__class__.__name__, fun)
        for i in range(20):
            name = self.getRandomString(100)
            sys.stdout = self.mystdout = StringIO()
            sys.stderr = self.mystderr = StringIO()
            Streams.log_fatal = self.mystd1 = StringIO()
            Streams.log_error = self.mystd2 = StringIO()
            Streams.log_warn = self.mystd3 = StringIO()
            Streams.log_info = self.mystd4 = StringIO()
            Streams.log_debug = self.mystd5 = StringIO()
            if i % 3 == 0:
                Streams.fatal(name)
            elif i % 3 == 1:
                Streams.fatal(name, std=False)
            elif i % 3 == 2:
                Streams.fatal(name, std=True)
            self.assertEqual(Streams.log_fatal.getvalue(), name + '\n')
            self.assertEqual(Streams.log_error.getvalue(), "")
            self.assertEqual(Streams.log_warn.getvalue(), "")
            self.assertEqual(Streams.log_info.getvalue(), "")
            self.assertEqual(Streams.log_debug.getvalue(), "")
            self.assertEqual(self.mystdout.getvalue(), "")
            self.assertEqual(self.mystderr.getvalue(), "")
            sys.stdout = self.old_stdout
            sys.stderr = self.old_stderr

    def test_error(self):
        fun = sys._getframe().f_code.co_name
        print "Run: %s.%s() " % (self.__class__.__name__, fun)
        for i in range(20):
            name = self.getRandomString(100)
            sys.stdout = self.mystdout = StringIO()
            sys.stderr = self.mystderr = StringIO()
            if i % 2:
                Streams.error(name)
            else:
                Streams.error(name, std=True)
            self.assertEqual(Streams.log_fatal, None)
            self.assertEqual(Streams.log_error, None)
            self.assertEqual(Streams.log_warn, None)
            self.assertEqual(Streams.log_info, None)
            self.assertEqual(Streams.log_debug, None)
            self.assertEqual(self.mystdout.getvalue(), "")
            self.assertEqual(self.mystderr.getvalue(), name + '\n')
            sys.stdout = self.old_stdout
            sys.stderr = self.old_stderr

    def test_error_nostd(self):
        fun = sys._getframe().f_code.co_name
        print "Run: %s.%s() " % (self.__class__.__name__, fun)
        for i in range(20):
            name = self.getRandomString(100)
            sys.stdout = self.mystdout = StringIO()
            sys.stderr = self.mystderr = StringIO()
            Streams.error(name, std=False)
            self.assertEqual(Streams.log_fatal, None)
            self.assertEqual(Streams.log_error, None)
            self.assertEqual(Streams.log_warn, None)
            self.assertEqual(Streams.log_info, None)
            self.assertEqual(Streams.log_debug, None)
            self.assertEqual(self.mystdout.getvalue(), "")
            self.assertEqual(self.mystderr.getvalue(), "")
            sys.stdout = self.old_stdout
            sys.stderr = self.old_stderr

    ## constructor test
    # \brief It tests default settings
    def test_error_log(self):
        fun = sys._getframe().f_code.co_name
        print "Run: %s.%s() " % (self.__class__.__name__, fun)
        for i in range(20):
            name = self.getRandomString(100)
            sys.stdout = self.mystdout = StringIO()
            sys.stderr = self.mystderr = StringIO()
            Streams.log_fatal = self.mystd1 = StringIO()
            Streams.log_error = self.mystd2 = StringIO()
            Streams.log_warn = self.mystd3 = StringIO()
            Streams.log_info = self.mystd4 = StringIO()
            Streams.log_debug = self.mystd5 = StringIO()
            if i % 3 == 0:
                Streams.error(name)
            elif i % 3 == 1:
                Streams.error(name, std=False)
            elif i % 3 == 2:
                Streams.error(name, std=True)
            self.assertEqual(Streams.log_fatal.getvalue(), "")
            self.assertEqual(Streams.log_error.getvalue(), name + '\n')
            self.assertEqual(Streams.log_warn.getvalue(), "")
            self.assertEqual(Streams.log_info.getvalue(), "")
            self.assertEqual(Streams.log_debug.getvalue(), "")
            self.assertEqual(self.mystdout.getvalue(), "")
            self.assertEqual(self.mystderr.getvalue(), "")
            sys.stdout = self.old_stdout
            sys.stderr = self.old_stderr

    def test_warn(self):
        fun = sys._getframe().f_code.co_name
        print "Run: %s.%s() " % (self.__class__.__name__, fun)
        for i in range(20):
            name = self.getRandomString(100)
            sys.stdout = self.mystdout = StringIO()
            sys.stderr = self.mystderr = StringIO()
            if i % 2:
                Streams.warn(name)
            else:
                Streams.warn(name, std=True)
            self.assertEqual(Streams.log_fatal, None)
            self.assertEqual(Streams.log_error, None)
            self.assertEqual(Streams.log_warn, None)
            self.assertEqual(Streams.log_info, None)
            self.assertEqual(Streams.log_debug, None)
            self.assertEqual(self.mystdout.getvalue(), "")
            self.assertEqual(self.mystderr.getvalue(), name + '\n')
            sys.stdout = self.old_stdout
            sys.stderr = self.old_stderr

    def test_warn_nostd(self):
        fun = sys._getframe().f_code.co_name
        print "Run: %s.%s() " % (self.__class__.__name__, fun)
        for i in range(20):
            name = self.getRandomString(100)
            sys.stdout = self.mystdout = StringIO()
            sys.stderr = self.mystderr = StringIO()
            Streams.warn(name, std=False)
            self.assertEqual(Streams.log_fatal, None)
            self.assertEqual(Streams.log_error, None)
            self.assertEqual(Streams.log_warn, None)
            self.assertEqual(Streams.log_info, None)
            self.assertEqual(Streams.log_debug, None)
            self.assertEqual(self.mystdout.getvalue(), "")
            self.assertEqual(self.mystderr.getvalue(), "")
            sys.stdout = self.old_stdout
            sys.stderr = self.old_stderr

    def test_warn_log(self):
        fun = sys._getframe().f_code.co_name
        print "Run: %s.%s() " % (self.__class__.__name__, fun)
        for i in range(20):
            name = self.getRandomString(100)
            sys.stdout = self.mystdout = StringIO()
            sys.stderr = self.mystderr = StringIO()
            Streams.log_fatal = self.mystd1 = StringIO()
            Streams.log_error = self.mystd2 = StringIO()
            Streams.log_warn = self.mystd3 = StringIO()
            Streams.log_info = self.mystd4 = StringIO()
            Streams.log_debug = self.mystd5 = StringIO()
            if i % 3 == 0:
                Streams.warn(name)
            elif i % 3 == 1:
                Streams.warn(name, std=False)
            elif i % 3 == 2:
                Streams.warn(name, std=True)
            self.assertEqual(Streams.log_fatal.getvalue(), "")
            self.assertEqual(Streams.log_error.getvalue(), "")
            self.assertEqual(Streams.log_warn.getvalue(), name + '\n')
            self.assertEqual(Streams.log_info.getvalue(), "")
            self.assertEqual(Streams.log_debug.getvalue(), "")
            self.assertEqual(self.mystdout.getvalue(), "")
            self.assertEqual(self.mystderr.getvalue(), "")
            sys.stdout = self.old_stdout
            sys.stderr = self.old_stderr

    def test_info(self):
        fun = sys._getframe().f_code.co_name
        print "Run: %s.%s() " % (self.__class__.__name__, fun)
        for i in range(20):
            name = self.getRandomString(100)
            sys.stdout = self.mystdout = StringIO()
            sys.stderr = self.mystderr = StringIO()
            if i % 2:
                Streams.info(name)
            else:
                Streams.info(name, std=True)
            self.assertEqual(Streams.log_fatal, None)
            self.assertEqual(Streams.log_error, None)
            self.assertEqual(Streams.log_warn, None)
            self.assertEqual(Streams.log_info, None)
            self.assertEqual(Streams.log_debug, None)
            self.assertEqual(self.mystdout.getvalue(), name + '\n')
            self.assertEqual(self.mystderr.getvalue(), "")
            sys.stdout = self.old_stdout
            sys.stderr = self.old_stderr

    def test_info_nostd(self):
        fun = sys._getframe().f_code.co_name
        print "Run: %s.%s() " % (self.__class__.__name__, fun)
        for i in range(20):
            name = self.getRandomString(100)
            sys.stdout = self.mystdout = StringIO()
            sys.stderr = self.mystderr = StringIO()
            Streams.info(name, std=False)
            self.assertEqual(Streams.log_fatal, None)
            self.assertEqual(Streams.log_error, None)
            self.assertEqual(Streams.log_warn, None)
            self.assertEqual(Streams.log_info, None)
            self.assertEqual(Streams.log_debug, None)
            self.assertEqual(self.mystdout.getvalue(), "")
            self.assertEqual(self.mystderr.getvalue(), "")
            sys.stdout = self.old_stdout
            sys.stderr = self.old_stderr

    ## constructor test
    # \brief It tests default settings
    def test_info_log(self):
        fun = sys._getframe().f_code.co_name
        print "Run: %s.%s() " % (self.__class__.__name__, fun)
        for i in range(20):
            name = self.getRandomString(100)
            sys.stdout = self.mystdout = StringIO()
            sys.stderr = self.mystderr = StringIO()
            Streams.log_fatal = self.mystd1 = StringIO()
            Streams.log_error = self.mystd2 = StringIO()
            Streams.log_warn = self.mystd3 = StringIO()
            Streams.log_info = self.mystd4 = StringIO()
            Streams.log_debug = self.mystd5 = StringIO()
            if i % 3 == 0:
                Streams.info(name)
            elif i % 3 == 1:
                Streams.info(name, std=False)
            elif i % 3 == 2:
                Streams.info(name, std=True)
            self.assertEqual(Streams.log_fatal.getvalue(), "")
            self.assertEqual(Streams.log_error.getvalue(), "")
            self.assertEqual(Streams.log_warn.getvalue(), "")
            self.assertEqual(Streams.log_info.getvalue(), name + '\n')
            self.assertEqual(Streams.log_debug.getvalue(), "")
            self.assertEqual(self.mystdout.getvalue(), "")
            self.assertEqual(self.mystderr.getvalue(), "")
            sys.stdout = self.old_stdout
            sys.stderr = self.old_stderr

    def test_debug(self):
        fun = sys._getframe().f_code.co_name
        print "Run: %s.%s() " % (self.__class__.__name__, fun)
        for i in range(20):
            name = self.getRandomString(100)
            sys.stdout = self.mystdout = StringIO()
            sys.stderr = self.mystderr = StringIO()
            if i % 2:
                Streams.debug(name)
            else:
                Streams.debug(name, std=True)
            self.assertEqual(Streams.log_fatal, None)
            self.assertEqual(Streams.log_error, None)
            self.assertEqual(Streams.log_warn, None)
            self.assertEqual(Streams.log_info, None)
            self.assertEqual(Streams.log_debug, None)
            self.assertEqual(self.mystdout.getvalue(), name + '\n')
            self.assertEqual(self.mystderr.getvalue(), "")
            sys.stdout = self.old_stdout
            sys.stderr = self.old_stderr

    def test_debug_nostd(self):
        fun = sys._getframe().f_code.co_name
        print "Run: %s.%s() " % (self.__class__.__name__, fun)
        for i in range(20):
            name = self.getRandomString(100)
            sys.stdout = self.mystdout = StringIO()
            sys.stderr = self.mystderr = StringIO()
            Streams.debug(name, std=False)
            self.assertEqual(Streams.log_fatal, None)
            self.assertEqual(Streams.log_error, None)
            self.assertEqual(Streams.log_warn, None)
            self.assertEqual(Streams.log_info, None)
            self.assertEqual(Streams.log_debug, None)
            self.assertEqual(self.mystdout.getvalue(), "")
            self.assertEqual(self.mystderr.getvalue(), "")
            sys.stdout = self.old_stdout
            sys.stderr = self.old_stderr

    ## constructor test
    # \brief It tests default settings
    def test_debug_log(self):
        fun = sys._getframe().f_code.co_name
        print "Run: %s.%s() " % (self.__class__.__name__, fun)
        for i in range(20):
            name = self.getRandomString(100)
            sys.stdout = self.mystdout = StringIO()
            sys.stderr = self.mystderr = StringIO()
            Streams.log_fatal = self.mystd1 = StringIO()
            Streams.log_error = self.mystd2 = StringIO()
            Streams.log_warn = self.mystd3 = StringIO()
            Streams.log_info = self.mystd4 = StringIO()
            Streams.log_debug = self.mystd5 = StringIO()
            if i % 3 == 0:
                Streams.debug(name)
            elif i % 3 == 1:
                Streams.debug(name, std=False)
            elif i % 3 == 2:
                Streams.debug(name, std=True)
            self.assertEqual(Streams.log_fatal.getvalue(), "")
            self.assertEqual(Streams.log_error.getvalue(), "")
            self.assertEqual(Streams.log_warn.getvalue(), "")
            self.assertEqual(Streams.log_info.getvalue(), "")
            self.assertEqual(Streams.log_debug.getvalue(), name + '\n')
            self.assertEqual(self.mystdout.getvalue(), "")
            self.assertEqual(self.mystderr.getvalue(), "")
            sys.stdout = self.old_stdout
            sys.stderr = self.old_stderr


if __name__ == '__main__':
    unittest.main()
