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
## \package nxswriter nexdatas
## \file Streams.py

""" labels to Tango Streams """

import sys

## Tango fatal log
log_fatal = None
## Tango error log
log_error = None
## Tango warn log
log_warn = None
## Tango info log
log_info = None
## Tango debug log
log_debug = None


## writer fatal error message
# \param message error message
# \param std if writes to sys stream
#        when log stream does not exist
def fatal(message, std=True):
    if log_fatal:
        log_fatal.write(message + '\n')
    elif std:
        sys.stderr.write(message + '\n')


## writer fatal error message
# \param message error message
# \param std if writes to sys stream
#        when log stream does not exist
def error(message, std=True):
    if log_error:
        log_error.write(message + '\n')
    elif std:
        sys.stderr.write(message + '\n')


## writer fatal error message
# \param message error message
# \param std if writes to sys stream
#        when log stream does not exist
def warn(message, std=True):
    if log_warn:
        log_warn.write(message + '\n')
    elif std:
        sys.stderr.write(message + '\n')


## writer fatal error message
# \param message error message
# \param std if writes to sys stream
#        when log stream does not exist
def info(message, std=True):
    if log_info:
        log_info.write(message + '\n')
    elif std:
        sys.stdout.write(message + '\n')


## writer fatal error message
# \param message error message
# \param std if writes to sys stream
#        when log stream does not exist
def debug(message, std=True):
    if log_debug:
        log_debug.write(message + '\n')
    elif std:
        sys.stdout.write(message + '\n')
