#!/usr/bin/env python
#   This file is part of nxsrecconfig - NeXus Sardana Recorder Settings
#
#    Copyright (C) 2014 DESY, Jan Kotanski <jkotan@mail.desy.de>
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
## \file Describer.py
# component describer

"""  Component Describer """

import re
import json
import xml.dom.minidom
from .Utils import Utils


## NeXus Sardana Recorder settings
class Describer(object):
    """ Lists datasources, strategy, dstype and record name
        of given component """

    ## constructor
    # \param configserver configuration server name
    def __init__(self, nexusconfig_device):
        self.__nexusconfig_device = nexusconfig_device
