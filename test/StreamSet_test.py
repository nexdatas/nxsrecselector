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
# \file StreamSetTest.py
# unittests for field Tags running Tango Server
#
import unittest
import os
import sys
# import subprocess
import random
import struct
import binascii
import time

from nxsrecconfig import StreamSet

# import string
if sys.version_info > (3,):
    from io import StringIO
else:
    from StringIO import StringIO


if sys.version_info > (3,):
    long = int


# if 64-bit machione
IS64BIT = (struct.calcsize("P") == 8)


# test fixture
class StreamSetTest(unittest.TestCase):

    # constructor
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
        self.streams = None

    def getRandomString(self, maxsize):
        letters = [chr(i) for i in range(32, 126)]
        size = self.__rnd.randint(1, maxsize)
        return ''.join(self.__rnd.choice(letters) for _ in range(size))

    # test starter
    # \brief Common set up
    def setUp(self):
        print("SEED =%s" % self.__seed)
        print("\nsetting up...")
        self.streams = StreamSet.StreamSet(None)
        hasattr(self.streams, "log_fatal")
        hasattr(self.streams, "log_error")
        hasattr(self.streams, "log_warn")
        hasattr(self.streams, "log_info")
        hasattr(self.streams, "log_debug")
        self.streams.log_fatal = None
        self.streams.log_error = None
        self.streams.log_warn = None
        self.streams.log_info = None
        self.streams.log_debug = None

    # test closer
    # \brief Common tear down
    def tearDown(self):
        sys.stdout = self.old_stdout
        sys.stderr = self.old_stderr
        print("tearing down ...")

    def test_constructor(self):
        fun = sys._getframe().f_code.co_name
        print("Run: %s.%s() " % (self.__class__.__name__, fun))
        streams = StreamSet.StreamSet(None)
        self.assertEqual(streams.log_fatal, None)
        self.assertEqual(streams.log_error, None)
        self.assertEqual(streams.log_warn, None)
        self.assertEqual(streams.log_info, None)
        self.assertEqual(streams.log_debug, None)
        for i in range(6):
            self.streams.log_fatal = self.mystd1 = self.getRandomString(100)
            self.streams.log_error = self.mystd2 = self.getRandomString(100)
            self.streams.log_warn = self.mystd3 = self.getRandomString(100)
            self.streams.log_info = self.mystd4 = self.getRandomString(100)
            self.streams.log_debug = self.mystd5 = self.getRandomString(100)
            streams = StreamSet.StreamSet(self.streams)
            self.assertEqual(streams.log_fatal, self.mystd1)
            self.assertEqual(streams.log_error, self.mystd2)
            self.assertEqual(streams.log_warn, self.mystd3)
            self.assertEqual(streams.log_info, self.mystd4)
            self.assertEqual(streams.log_debug, self.mystd5)

    def test_fatal(self):
        fun = sys._getframe().f_code.co_name
        print("Run: %s.%s() " % (self.__class__.__name__, fun))
        for i in range(6):
            name = self.getRandomString(100)
            sys.stdout = self.mystdout = StringIO()
            sys.stderr = self.mystderr = StringIO()
            if i % 2:
                self.streams.fatal(name)
            else:
                self.streams.fatal(name, std=True)
            self.assertEqual(self.streams.log_fatal, None)
            self.assertEqual(self.streams.log_error, None)
            self.assertEqual(self.streams.log_warn, None)
            self.assertEqual(self.streams.log_info, None)
            self.assertEqual(self.streams.log_debug, None)
            self.assertEqual(self.mystdout.getvalue(), "")
            self.assertEqual(
                self.mystderr.getvalue().split(" ", 2)[-1],
                "FATAL: " + name + '\n')
            sys.stdout = self.old_stdout
            sys.stderr = self.old_stderr

    def test_fatal_nostd(self):
        fun = sys._getframe().f_code.co_name
        print("Run: %s.%s() " % (self.__class__.__name__, fun))
        for i in range(6):
            name = self.getRandomString(100)
            sys.stdout = self.mystdout = StringIO()
            sys.stderr = self.mystderr = StringIO()
            self.streams.fatal(name, std=False)
            self.assertEqual(self.streams.log_fatal, None)
            self.assertEqual(self.streams.log_error, None)
            self.assertEqual(self.streams.log_warn, None)
            self.assertEqual(self.streams.log_info, None)
            self.assertEqual(self.streams.log_debug, None)
            self.assertEqual(self.mystdout.getvalue(), "")
            self.assertEqual(self.mystderr.getvalue(), "")
            sys.stdout = self.old_stdout
            sys.stderr = self.old_stderr

    def test_fatal_log(self):
        fun = sys._getframe().f_code.co_name
        print("Run: %s.%s() " % (self.__class__.__name__, fun))
        for i in range(6):
            name = self.getRandomString(100)
            sys.stdout = self.mystdout = StringIO()
            sys.stderr = self.mystderr = StringIO()
            self.streams.log_fatal = self.mystd1 = StringIO()
            self.streams.log_error = self.mystd2 = StringIO()
            self.streams.log_warn = self.mystd3 = StringIO()
            self.streams.log_info = self.mystd4 = StringIO()
            self.streams.log_debug = self.mystd5 = StringIO()
            if i % 3 == 0:
                self.streams.fatal(name)
            elif i % 3 == 1:
                self.streams.fatal(name, std=False)
            elif i % 3 == 2:
                self.streams.fatal(name, std=True)
            self.assertEqual(self.streams.log_fatal.getvalue(), name + '\n')
            self.assertEqual(self.streams.log_error.getvalue(), "")
            self.assertEqual(self.streams.log_warn.getvalue(), "")
            self.assertEqual(self.streams.log_info.getvalue(), "")
            self.assertEqual(self.streams.log_debug.getvalue(), "")
            self.assertEqual(self.mystdout.getvalue(), "")
            if i % 3 == 0:
                self.assertEqual(
                    self.mystderr.getvalue().split(" ", 2)[-1],
                    "FATAL: " + name + '\n')
            elif i % 3 == 1:
                self.assertEqual(self.mystderr.getvalue(), '')
            elif i % 3 == 2:
                self.assertEqual(
                    self.mystderr.getvalue().split(" ", 2)[-1],
                    "FATAL: " + name + '\n')
            sys.stdout = self.old_stdout
            sys.stderr = self.old_stderr

    def test_error(self):
        fun = sys._getframe().f_code.co_name
        print("Run: %s.%s() " % (self.__class__.__name__, fun))
        for i in range(6):
            name = self.getRandomString(100)
            sys.stdout = self.mystdout = StringIO()
            sys.stderr = self.mystderr = StringIO()
            if i % 2:
                self.streams.error(name)
            else:
                self.streams.error(name, std=True)
            self.assertEqual(self.streams.log_fatal, None)
            self.assertEqual(self.streams.log_error, None)
            self.assertEqual(self.streams.log_warn, None)
            self.assertEqual(self.streams.log_info, None)
            self.assertEqual(self.streams.log_debug, None)
            self.assertEqual(self.mystdout.getvalue(), "")
            self.assertEqual(
                self.mystderr.getvalue().split(" ", 2)[-1],
                "ERROR: " + name + '\n')
            sys.stdout = self.old_stdout
            sys.stderr = self.old_stderr

    def test_error_nostd(self):
        fun = sys._getframe().f_code.co_name
        print("Run: %s.%s() " % (self.__class__.__name__, fun))
        for i in range(6):
            name = self.getRandomString(100)
            sys.stdout = self.mystdout = StringIO()
            sys.stderr = self.mystderr = StringIO()
            self.streams.error(name, std=False)
            self.assertEqual(self.streams.log_fatal, None)
            self.assertEqual(self.streams.log_error, None)
            self.assertEqual(self.streams.log_warn, None)
            self.assertEqual(self.streams.log_info, None)
            self.assertEqual(self.streams.log_debug, None)
            self.assertEqual(self.mystdout.getvalue(), "")
            self.assertEqual(self.mystderr.getvalue(), "")
            sys.stdout = self.old_stdout
            sys.stderr = self.old_stderr

    # constructor test
    # \brief It tests default settings
    def test_error_log(self):
        fun = sys._getframe().f_code.co_name
        print("Run: %s.%s() " % (self.__class__.__name__, fun))
        for i in range(6):
            name = self.getRandomString(100)
            sys.stdout = self.mystdout = StringIO()
            sys.stderr = self.mystderr = StringIO()
            self.streams.log_fatal = self.mystd1 = StringIO()
            self.streams.log_error = self.mystd2 = StringIO()
            self.streams.log_warn = self.mystd3 = StringIO()
            self.streams.log_info = self.mystd4 = StringIO()
            self.streams.log_debug = self.mystd5 = StringIO()
            if i % 3 == 0:
                self.streams.error(name)
            elif i % 3 == 1:
                self.streams.error(name, std=False)
            elif i % 3 == 2:
                self.streams.error(name, std=True)
            self.assertEqual(self.streams.log_fatal.getvalue(), "")
            self.assertEqual(self.streams.log_error.getvalue(), name + '\n')
            self.assertEqual(self.streams.log_warn.getvalue(), "")
            self.assertEqual(self.streams.log_info.getvalue(), "")
            self.assertEqual(self.streams.log_debug.getvalue(), "")
            self.assertEqual(self.mystdout.getvalue(), "")
            if i % 3 == 0:
                self.assertEqual(
                    self.mystderr.getvalue().split(" ", 2)[-1],
                    "ERROR: " + name + '\n')
            elif i % 3 == 1:
                self.assertEqual(self.mystderr.getvalue(), '')
            elif i % 3 == 2:
                self.assertEqual(
                    self.mystderr.getvalue().split(" ", 2)[-1],
                    "ERROR: " + name + '\n')
            sys.stdout = self.old_stdout
            sys.stderr = self.old_stderr

    def test_warn(self):
        fun = sys._getframe().f_code.co_name
        print("Run: %s.%s() " % (self.__class__.__name__, fun))
        for i in range(6):
            name = self.getRandomString(100)
            sys.stdout = self.mystdout = StringIO()
            sys.stderr = self.mystderr = StringIO()
            if i % 2:
                self.streams.warn(name)
            else:
                self.streams.warn(name, std=True)
            self.assertEqual(self.streams.log_fatal, None)
            self.assertEqual(self.streams.log_error, None)
            self.assertEqual(self.streams.log_warn, None)
            self.assertEqual(self.streams.log_info, None)
            self.assertEqual(self.streams.log_debug, None)
            self.assertEqual(self.mystdout.getvalue(), "")
            self.assertEqual(
                self.mystderr.getvalue().split(" ", 2)[-1],
                "WARNING: " + name + '\n')
            sys.stdout = self.old_stdout
            sys.stderr = self.old_stderr

    def test_warn_nostd(self):
        fun = sys._getframe().f_code.co_name
        print("Run: %s.%s() " % (self.__class__.__name__, fun))
        for i in range(6):
            name = self.getRandomString(100)
            sys.stdout = self.mystdout = StringIO()
            sys.stderr = self.mystderr = StringIO()
            self.streams.warn(name, std=False)
            self.assertEqual(self.streams.log_fatal, None)
            self.assertEqual(self.streams.log_error, None)
            self.assertEqual(self.streams.log_warn, None)
            self.assertEqual(self.streams.log_info, None)
            self.assertEqual(self.streams.log_debug, None)
            self.assertEqual(self.mystdout.getvalue(), "")
            self.assertEqual(self.mystderr.getvalue(), "")
            sys.stdout = self.old_stdout
            sys.stderr = self.old_stderr

    def test_warn_log(self):
        fun = sys._getframe().f_code.co_name
        print("Run: %s.%s() " % (self.__class__.__name__, fun))
        for i in range(6):
            name = self.getRandomString(100)
            sys.stdout = self.mystdout = StringIO()
            sys.stderr = self.mystderr = StringIO()
            self.streams.log_fatal = self.mystd1 = StringIO()
            self.streams.log_error = self.mystd2 = StringIO()
            self.streams.log_warn = self.mystd3 = StringIO()
            self.streams.log_info = self.mystd4 = StringIO()
            self.streams.log_debug = self.mystd5 = StringIO()
            if i % 3 == 0:
                self.streams.warn(name)
            elif i % 3 == 1:
                self.streams.warn(name, std=False)
            elif i % 3 == 2:
                self.streams.warn(name, std=True)
            self.assertEqual(self.streams.log_fatal.getvalue(), "")
            self.assertEqual(self.streams.log_error.getvalue(), "")
            self.assertEqual(self.streams.log_warn.getvalue(), name + '\n')
            self.assertEqual(self.streams.log_info.getvalue(), "")
            self.assertEqual(self.streams.log_debug.getvalue(), "")
            self.assertEqual(self.mystdout.getvalue(), "")
            if i % 3 == 0:
                self.assertEqual(
                    self.mystderr.getvalue().split(" ", 2)[-1],
                    "WARNING: " + name + '\n')
            elif i % 3 == 1:
                self.assertEqual(self.mystderr.getvalue(), '')
            elif i % 3 == 2:
                self.assertEqual(
                    self.mystderr.getvalue().split(" ", 2)[-1],
                    "WARNING: " + name + '\n')
            sys.stdout = self.old_stdout
            sys.stderr = self.old_stderr

    def test_info(self):
        fun = sys._getframe().f_code.co_name
        print("Run: %s.%s() " % (self.__class__.__name__, fun))
        for i in range(6):
            name = self.getRandomString(100)
            sys.stdout = self.mystdout = StringIO()
            sys.stderr = self.mystderr = StringIO()
            self.streams.info(name, std=True)
            self.assertEqual(self.streams.log_fatal, None)
            self.assertEqual(self.streams.log_error, None)
            self.assertEqual(self.streams.log_warn, None)
            self.assertEqual(self.streams.log_info, None)
            self.assertEqual(self.streams.log_debug, None)
            self.assertEqual(
                self.mystdout.getvalue().split(" ", 2)[-1],
                "INFO: " + name + '\n')
            self.assertEqual(self.mystderr.getvalue(), "")
            sys.stdout = self.old_stdout
            sys.stderr = self.old_stderr

    def test_info_nostd(self):
        fun = sys._getframe().f_code.co_name
        print("Run: %s.%s() " % (self.__class__.__name__, fun))
        for i in range(6):
            name = self.getRandomString(100)
            sys.stdout = self.mystdout = StringIO()
            sys.stderr = self.mystderr = StringIO()
            if i % 2 == 0:
                self.streams.info(name)
            else:
                self.streams.info(name, std=False)
            self.assertEqual(self.streams.log_fatal, None)
            self.assertEqual(self.streams.log_error, None)
            self.assertEqual(self.streams.log_warn, None)
            self.assertEqual(self.streams.log_info, None)
            self.assertEqual(self.streams.log_debug, None)
            self.assertEqual(self.mystdout.getvalue(), "")
            self.assertEqual(self.mystderr.getvalue(), "")
            sys.stdout = self.old_stdout
            sys.stderr = self.old_stderr

    # constructor test
    # \brief It tests default settings
    def test_info_log(self):
        fun = sys._getframe().f_code.co_name
        print("Run: %s.%s() " % (self.__class__.__name__, fun))
        for i in range(6):
            name = self.getRandomString(100)
            sys.stdout = self.mystdout = StringIO()
            sys.stderr = self.mystderr = StringIO()
            self.streams.log_fatal = self.mystd1 = StringIO()
            self.streams.log_error = self.mystd2 = StringIO()
            self.streams.log_warn = self.mystd3 = StringIO()
            self.streams.log_info = self.mystd4 = StringIO()
            self.streams.log_debug = self.mystd5 = StringIO()
            if i % 3 == 0:
                self.streams.info(name)
            elif i % 3 == 1:
                self.streams.info(name, std=False)
            elif i % 3 == 2:
                self.streams.info(name, std=True)
            self.assertEqual(self.streams.log_fatal.getvalue(), "")
            self.assertEqual(self.streams.log_error.getvalue(), "")
            self.assertEqual(self.streams.log_warn.getvalue(), "")
            self.assertEqual(self.streams.log_info.getvalue(), name + '\n')
            self.assertEqual(self.streams.log_debug.getvalue(), "")
            self.assertEqual(self.mystdout.getvalue(), "")
            self.assertEqual(self.mystderr.getvalue(), "")
            sys.stdout = self.old_stdout
            sys.stderr = self.old_stderr

    def test_debug(self):
        fun = sys._getframe().f_code.co_name
        print("Run: %s.%s() " % (self.__class__.__name__, fun))
        for i in range(6):
            name = self.getRandomString(100)
            sys.stdout = self.mystdout = StringIO()
            sys.stderr = self.mystderr = StringIO()
            self.streams.debug(name, std=True)
            self.assertEqual(self.streams.log_fatal, None)
            self.assertEqual(self.streams.log_error, None)
            self.assertEqual(self.streams.log_warn, None)
            self.assertEqual(self.streams.log_info, None)
            self.assertEqual(self.streams.log_debug, None)
            self.assertEqual(
                self.mystdout.getvalue().split(" ", 2)[-1],
                "DEBUG: " + name + '\n')
            self.assertEqual(self.mystderr.getvalue(), "")
            sys.stdout = self.old_stdout
            sys.stderr = self.old_stderr

    def test_debug_nostd(self):
        fun = sys._getframe().f_code.co_name
        print("Run: %s.%s() " % (self.__class__.__name__, fun))
        for i in range(6):
            name = self.getRandomString(100)
            sys.stdout = self.mystdout = StringIO()
            sys.stderr = self.mystderr = StringIO()
            if i % 2:
                self.streams.debug(name)
            else:
                self.streams.debug(name, std=False)
            self.assertEqual(self.streams.log_fatal, None)
            self.assertEqual(self.streams.log_error, None)
            self.assertEqual(self.streams.log_warn, None)
            self.assertEqual(self.streams.log_info, None)
            self.assertEqual(self.streams.log_debug, None)
            self.assertEqual(self.mystdout.getvalue(), "")
            self.assertEqual(self.mystderr.getvalue(), "")
            sys.stdout = self.old_stdout
            sys.stderr = self.old_stderr

    # constructor test
    # \brief It tests default settings
    def test_debug_log(self):
        fun = sys._getframe().f_code.co_name
        print("Run: %s.%s() " % (self.__class__.__name__, fun))
        for i in range(6):
            name = self.getRandomString(100)
            sys.stdout = self.mystdout = StringIO()
            sys.stderr = self.mystderr = StringIO()
            self.streams.log_fatal = self.mystd1 = StringIO()
            self.streams.log_error = self.mystd2 = StringIO()
            self.streams.log_warn = self.mystd3 = StringIO()
            self.streams.log_info = self.mystd4 = StringIO()
            self.streams.log_debug = self.mystd5 = StringIO()
            if i % 3 == 0:
                self.streams.debug(name)
            elif i % 3 == 1:
                self.streams.debug(name, std=False)
            elif i % 3 == 2:
                self.streams.debug(name, std=True)
            self.assertEqual(self.streams.log_fatal.getvalue(), "")
            self.assertEqual(self.streams.log_error.getvalue(), "")
            self.assertEqual(self.streams.log_warn.getvalue(), "")
            self.assertEqual(self.streams.log_info.getvalue(), "")
            self.assertEqual(self.streams.log_debug.getvalue(), name + '\n')
            self.assertEqual(self.mystdout.getvalue(), "")
            self.assertEqual(self.mystderr.getvalue(), "")
            sys.stdout = self.old_stdout
            sys.stderr = self.old_stderr


if __name__ == '__main__':
    unittest.main()
