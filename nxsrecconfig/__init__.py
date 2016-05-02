#!/usr/bin/env python
#   This file is part of nxsrecconfig - NeXus Sardana Recorder Settings
#
#    Copyright (C) 2014-2016 DESY, Jan Kotanski <jkotan@mail.desy.de>
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
## \file __init__.py
# nxswriter runner

"""  NeXus Sardana Recorder Settings - Tango Server """

## package version
__version__ = "1.25.2"

import sys


## runs the TANGO server
# \param argv command-line arguments
def run(argv):
    import PyTango
    from .NXSConfig import NXSRecSelector as NXSRecConfig
    from .NXSConfig import NXSRecSelectorClass as NXSRecConfigClass
    try:
        py = PyTango.Util(argv)
        py.add_class(NXSRecConfigClass, NXSRecConfig)

        U = PyTango.Util.instance()
        U.server_init()
        U.server_run()

    except PyTango.DevFailed, e:
        print('-------> Received a DevFailed exception: %s' % e)
    except Exception, e:
        print('-------> An unforeseen exception occured.... %s' % e)
