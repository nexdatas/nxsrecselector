#!/usr/bin/env python
#   This file is part of nxsrecconfig - NeXus Sardana Recorder Settings
#
#    Copyright (C) 2014-2015 DESY, Jan Kotanski <jkotan@mail.desy.de>
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
## \file Selection.py
# component describer

"""  Selection state """

import json


## Selection dictionary
class Selection(dict):
    """ Selection Dictionary """

    ## constructor
    # \param args dictionary args
    # \param kw dictionary kw
    def __init__(self, *args, **kw):
        super(Selection, self).__init__(*args, **kw)

        ## default zone
        self.__defaultzone = 'Europe/Berlin'

        ## default mntgrp
        self.__defaultmntgrp = 'nxsmntgrp'
        self.reset()

    ## resets dictionary to default value
    def reset(self):
        self.clear()
        ## timer
        self["Timer"] = '[]'
        ## ordered channels
        self["OrderedChannels"] = '[]'
        ## group of electable components
        self["ComponentGroup"] = '{}'
        ## group of automatic components describing instrument state
        self["AutomaticComponentGroup"] = '{}'
        ## automatic datasources
        self["AutomaticDataSources"] = '[]'
        ## selected datasources
        self["DataSourceGroup"] = '{}'
        ## init datasources
        self["InitDataSources"] = '[]'
        ## group of optional components available for automatic selqection
        self["OptionalComponents"] = '[]'
        ## appending new entries to existing file
        self["AppendEntry"] = False
        ## select components from the active measurement group
        self["ComponentsFromMntGrp"] = False
        ## Configuration Server variables
        self["ConfigVariables"] = '{}'
        ## JSON with Client Data Record
        self["DataRecord"] = '{}'
        ## JSON with Element Labels
        self["Labels"] = '{}'
        ## JSON with NeXus paths for Label Paths
        self["LabelPaths"] = '{}'
        ## JSON with NeXus paths for Label Links
        self["LabelLinks"] = '{}'
        ## JSON with NeXus paths for Label Displays
        self["HiddenElements"] = '[]'
        ## JSON with NeXus paths for Label Types
        self["LabelTypes"] = '{}'
        ## JSON with NeXus paths for Label Shapes
        self["LabelShapes"] = '{}'
        ## create dynamic components
        self["DynamicComponents"] = True
        ## create links for dynamic components
        self["DynamicLinks"] = True
        ## path for dynamic components
        self["DynamicPath"] = \
            '/entry$var.serialno:NXentry/NXinstrument/collection'
        ## timezone
        self["TimeZone"] = self.__defaultzone
        ## Configuration Server device name
        self["ConfigDevice"] = ''
        ## NeXus Data Writer device
        self["WriterDevice"] = ''
        ## Door device name
        self["Door"] = ''
        ## MntGrp
        self["MntGrp"] = ''

    ## deselects components and datasources
    def deselect(self):
        cps = json.loads(self["ComponentGroup"])
        ads = json.loads(self["DataSourceGroup"])
        for k in cps.keys():
            cps[k] = False
        for k in ads.keys():
            ads[k] = False
        self["InitDataSources"] = '[]'
        self["DataSourceGroup"] = json.dumps(ads)
        self["ComponentGroup"] = json.dumps(cps)

    ## update method for Automatic DataSources
    # \brief appends new datasources to Automatic DataSources
    # \param datasources
    def updateAutomaticDataSources(self, datasources):
        adsg = json.loads(self["AutomaticDataSources"])
        adsg = list(set(adsg or []) | set(datasources or []))
        self["AutomaticDataSources"] = json.dumps(adsg)

    ## update method for orderedChannels attribute
    # \param channels pool channels
    def updateOrderedChannels(self, channels):
        och = json.loads(self["OrderedChannels"])
        ordchannels = [ch for ch in och if ch in channels]
        uordchannels = list(set(channels) - set(och))
        ordchannels.extend(sorted(uordchannels))
        self["OrderedChannels"] = json.dumps(ordchannels)

    ## update method for componentGroup attribute
    def updateComponentGroup(self):
        cpg = json.loads(self["ComponentGroup"])
        dss = json.loads(self["DataSourceGroup"]).keys()
        for cp in set(cpg.keys()):
            if cp in dss:
                cpg.pop(cp)
        self["ComponentGroup"] = json.dumps(cpg)

    ## update method for dataSourceGroup attribute
    def updateDataSourceGroup(self, channels, datasources):
        dsg = json.loads(self["DataSourceGroup"])
        datasources = datasources or []
        for ds in tuple(dsg.keys()):
            if ds not in channels and ds not in datasources:
                dsg.pop(ds)
        for pc in channels:
            if pc not in dsg.keys():
                dsg[pc] = False
        self["DataSourceGroup"] = json.dumps(dsg)

    ## update method for mntGrp attribute
    def updateMntGrp(self):
        if "MntGrp" not in self.keys() or not self["MntGrp"]:
            self["MntGrp"] = self.__defaultmntgrp

    ## update method for timeZone attribute
    def updateTimeZone(self):
        if "TimeZone" not in self.keys() or not self["TimeZone"]:
            self["TimeZone"] = self.__defaultzone

    ## set method for mntGrp attribute
    def resetMntGrp(self):
        if not self["MntGrp"]:
            self["MntGrp"] = self.__defaultmntgrp

    ## set method for timeZone attribute
    def resetTimeZone(self):
        if not self["TimeZone"]:
            self["TimeZone"] = self.__defaultzone

    ## resets Automatic Components with given components and set them
    #  to not active
    # \param components list of components to be set
    def resetAutomaticComponents(self, components):
        acps = {}
        for cp in components:
            acps[cp] = False
        self["AutomaticComponentGroup"] = json.dumps(acps)
