#!/usr/bin/env python
#   This file is part of nexdatas - Tango Server for NeXus data writer
#
#    Copyright (C) 2012-2016 DESY, Jan Kotanski <jkotan@mail.desy.de>
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

#: Tango fatal log stream
log_fatal = None
#: Tango error log stream
log_error = None
#: Tango warn log stream
log_warn = None
#: Tango info log stream
log_info = None
#: Tango debug log stream
log_debug = None


def fatal(message, std=True):
    """ writes fatal error message

    :param message: error message
    :param std: it writes to sys stream
                when log stream does not exist
    """
    if log_fatal:
        try:
            log_fatal.write(message + '\n')
        except:
            # workaround for PyTango bug: #740
            sys.stderr.write(message + '\n')
    elif std:
        sys.stderr.write(message + '\n')


def error(message, std=True):
    """ writes error message

    :param message: error message
    :param std: it writes to sys stream
                when log stream does not exist
   """
    if log_error:
        try:
            log_error.write(message + '\n')
        except:
            # workaround for PyTango bug: #740
            sys.stderr.write(message + '\n')
    elif std:
        sys.stderr.write(message + '\n')


def warn(message, std=True):
    """ writes warning message

    :param message: warning message
    :param std: it writes to sys stream
                when log stream does not exist
   """
    if log_warn:
        try:
            log_warn.write(message + '\n')
        except:
            # workaround for PyTango bug: #740
            sys.stderr.write(message + '\n')
    elif std:
        sys.stderr.write(message + '\n')


def info(message, std=True):
    """ writes info message

    :param message: info message
    :param std: it writes to sys stream
                when log stream does not exist
    """
    if log_info:
        try:
            log_info.write(message + '\n')
        except:
            # workaround for PyTango bug: #740
            sys.stdout.write(message + '\n')
    elif std:
        sys.stdout.write(message + '\n')


def debug(message, std=True):
    """ writes debug message

    :param message: debug message
    :param std: it writes to sys stream
                when log stream does not exist
   """
    if log_debug:
        try:
            log_debug.write(message + '\n')
        except:
            # workaround for PyTango bug: #740
            sys.stdout.write(message + '\n')
    elif std:
        sys.stdout.write(message + '\n')
