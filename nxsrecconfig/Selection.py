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
## \file state.py
# component describer

"""  Selection state """

import re
import json
import xml.dom.minidom
from .Utils import Utils


## NeXus Sardana Recorder settings
class Selection(object):
    """ selection state """

    ## constructor
    # \param configserver configuration server name
    def __init__(self, state=None):

        ## default zone
        self.__defaultzone = 'Europe/Berlin'

        ##  dictionary with Settings
        self.__state = {}
        self.reset()

        if state:
            self.set(state)

    def reset(self):
        self.__state.clear()
        ## timer
        self.__state["Timer"] = '[]'
        ## ordered channels
        self.__state["OrderedChannels"] = '[]'
        ## group of electable components
        self.__state["ComponentGroup"] = '{}'
        ## group of automatic components describing instrument state
        self.__state["AutomaticComponentGroup"] = '{}'
        ## automatic datasources
        self.__state["AutomaticDataSources"] = '[]'
        ## selected datasources
        self.__state["DataSourceGroup"] = '{}'
        ## group of optional components available for automatic selqection
        self.__state["OptionalComponents"] = '[]'
        ## appending new entries to existing file
        self.__state["AppendEntry"] = False
        ## select components from the active measurement group
        self.__state["ComponentsFromMntGrp"] = False
        ## Configuration Server variables
        self.__state["ConfigVariables"] = '{}'
        ## JSON with Client Data Record
        self.__state["DataRecord"] = '{}'
        ## JSON with Element Labels
        self.__state["Labels"] = '{}'
        ## JSON with NeXus paths for Label Paths
        self.__state["LabelPaths"] = '{}'
        ## JSON with NeXus paths for Label Links
        self.__state["LabelLinks"] = '{}'
        ## JSON with NeXus paths for Label Displays
        self.__state["HiddenElements"] = '[]'
        ## JSON with NeXus paths for Label Types
        self.__state["LabelTypes"] = '{}'
        ## JSON with NeXus paths for Label Shapes
        self.__state["LabelShapes"] = '{}'
        ## create dynamic components
        self.__state["DynamicComponents"] = True
        ## create links for dynamic components
        self.__state["DynamicLinks"] = True
        ## path for dynamic components
        self.__state["DynamicPath"] = \
            '/entry$var.serialno:NXentry/NXinstrument/collection'
        ## timezone
        self.__state["TimeZone"] = self.__defaultzone
        ## Configuration Server device name
        self.__state["ConfigDevice"] = ''
        ## NeXus Data Writer device
        self.__state["WriterDevice"] = ''
        ## Door device name
        self.__state["Door"] = ''
        ## MntGrp
        self.__state["MntGrp"] = ''
        

    def set(self, state):
        self.reset()
        for key in state.keys():
            self.__state[key] = state[key]

    ## provides names of variables
    def keys(self):
        return self.__state.keys()

    def get(self):
        return dict(self.__state)

    def __getitem__(self, key):
        if key in self.keys():
            return self.__state[key]
        else:
            return None

    def __setitem__(self, key, value):
        self.__state[key] = value
