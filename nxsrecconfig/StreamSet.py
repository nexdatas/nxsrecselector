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
#

""" labels to Tango Streams """

import sys


class StreamSet(object):

    def __init__(self, streams):
        """ streamset constractor

        :param streams: tango-like steamset class
        :type streams: :class:`StreamSet` or :class:`PyTango.Device_4Impl`
        """

        #: (:class:`PyTango.log4tango.TangoStream`) Tango fatal log stream
        self.log_fatal = None
        #: (:class:`PyTango.log4tango.TangoStream`) Tango error log stream
        self.log_error = None
        #: (:class:`PyTango.log4tango.TangoStream`) Tango warn log stream
        self.log_warn = None
        #: (:class:`PyTango.log4tango.TangoStream`) Tango info log stream
        self.log_info = None
        #: (:class:`PyTango.log4tango.TangoStream`) Tango debug log stream
        self.log_debug = None
        #: (:obj:`set <:obj:`str` >`) if tango server
        if streams:
            if hasattr(streams, "log_fatal"):
                self.log_fatal = streams.log_fatal
            if hasattr(streams, "log_error"):
                self.log_error = streams.log_error
            if hasattr(streams, "log_warn"):
                self.log_warn = streams.log_warn
            if hasattr(streams, "log_info"):
                self.log_info = streams.log_info
            if hasattr(streams, "log_debug"):
                self.log_debug = streams.log_debug

    def fatal(self, message, std=True):
        """ writes fatal error message

        :param message: error message
        :type message: :obj:`str`
        :param std: True if it writes to sys stream
                    when log stream does not exist
        :type std: :obj:`bool`
        """
        if self.log_fatal:
            try:
                self.log_fatal.write(message + '\n')
            except:
                sys.stderr.write(message + '\n')
        elif std:
            sys.stderr.write(message + '\n')

    def error(self, message, std=True):
        """ writes error message

        :param message: error message
        :type message: :obj:`str`
        :param std: True if it writes to sys stream
                    when log stream does not exist
        :type std: :obj:`bool`
       """
        if self.log_error:
            try:
                self.log_error.write(message + '\n')
            except:
                sys.stderr.write(message + '\n')
        elif std:
            sys.stderr.write(message + '\n')

    def warn(self, message, std=True):
        """ writes warning message

        :param message: warning message
        :type message: :obj:`str`
        :param std: True if it writes to sys stream
                    when log stream does not exist
        :type std: :obj:`bool`
       """
        if self.log_warn:
            try:
                self.log_warn.write(message + '\n')
            except:
                sys.stderr.write(message + '\n')
        elif std:
            sys.stderr.write(message + '\n')

    def info(self, message, std=True):
        """ writes info message

        :param message: info message
        :type message: :obj:`str`
        :param std: True if it writes to sys stream
                    when log stream does not exist
        :type std: :obj:`bool`
        """
        if self.log_info:
            try:
                self.log_info.write(message + '\n')
            except:
                sys.stdout.write(message + '\n')
        elif std:
            sys.stdout.write(message + '\n')

    def debug(self, message, std=True):
        """ writes debug message

        :param message: debug message
        :type message: :obj:`str`
        :param std: True if it writes to sys stream
                    when log stream does not exist
        :type std: :obj:`bool`
       """
        if self.log_debug:
            try:
                self.log_debug.write(message + '\n')
            except:
                sys.stdout.write(message + '\n')
        elif std:
            sys.stdout.write(message + '\n')
