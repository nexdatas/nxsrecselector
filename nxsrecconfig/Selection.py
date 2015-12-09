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
        self.__version = self["Version"] if "Version" in self else "1.0.0"
        self.reset()

    ## resets dictionary to default value
    def reset(self):
        self.clear()
        ## timer
        self["Timer"] = '[]'
        ## ordered channels
        self["OrderedChannels"] = '[]'
        ## group of electable components
        self["ComponentSelection"] = '{}'
        ## group of preselected components describing instrument state
        self["ComponentPreselection"] = '{}'
        ## preselected datasources
        self["PreselectedDataSources"] = '[]'
        ## selected datasources
        self["DataSourceSelection"] = '{}'
        ## init datasources
        self["InitDataSources"] = '[]'
        ## group of optional components available for preselected selqection
        self["OptionalComponents"] = '[]'
        ## appending new entries to existing file
        self["AppendEntry"] = False
        ## select components from the active measurement group
        self["ComponentsFromMntGrp"] = False
        ## Configuration Server variables
        self["ConfigVariables"] = '{}'
        ## JSON with Client Data Record
        self["UserData"] = '{}'
        ## JSON with channel properties
        self["ChannelProperties"] = '{}'
        ## JSON with NeXus paths for Label Paths
        self["UnplottedComponents"] = '[]'
        ## create dynamic components
        self["DynamicComponents"] = True
        ## create links for dynamic components
        self["DefaultDynamicLinks"] = True
        ## path for dynamic components
        self["DefaultDynamicPath"] = \
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
        ## version
        self["Version"] = self.__version

    ## deselects components and datasources
    def deselect(self):
        cps = json.loads(self["ComponentSelection"])
        ads = json.loads(self["DataSourceSelection"])
        for k in cps.keys():
            cps[k] = False
        for k in ads.keys():
            ads[k] = False
        self["InitDataSources"] = '[]'
        self["DataSourceSelection"] = json.dumps(ads)
        self["ComponentSelection"] = json.dumps(cps)

    ## update method for Preselected DataSources
    # \brief appends new datasources to Preselected DataSources
    # \param datasources
    def updatePreselectedDataSources(self, datasources):
        adsg = json.loads(self["PreselectedDataSources"])
        adsg = list(set(adsg or []) | set(datasources or []))
        self["PreselectedDataSources"] = json.dumps(adsg)

    ## update method for orderedChannels attribute
    # \brief sets pool channels in order defined by OrderedChannels
    # \param channels pool channels
    def updateOrderedChannels(self, channels):
        och = json.loads(self["OrderedChannels"])
        ordchannels = [ch for ch in och if ch in channels]
        uordchannels = list(set(channels) - set(och))
        ordchannels.extend(sorted(uordchannels))
        self["OrderedChannels"] = json.dumps(ordchannels)

    ## update method for componentGroup attribute
    # \brief It removes datasource components from component group
    def updateComponentSelection(self):
        cpg = json.loads(self["ComponentSelection"])
        dss = json.loads(self["DataSourceSelection"]).keys()
        for cp in set(cpg.keys()):
            if cp in dss:
                cpg.pop(cp)
        self["ComponentSelection"] = json.dumps(cpg)

    ## update method for dataSourceGroup attribute
    # \brief It removes datasources from DataSourceSelection if they are
    #        neither in poolchannels nor in avaiblable datasources
    #        It adds new channels to DataSourceSelection
    # \param channels pool channels
    # \param datasources available datasources
    def updateDataSourceSelection(self, channels, datasources):
        dsg = json.loads(self["DataSourceSelection"])
        datasources = datasources or []
        for ds in tuple(dsg.keys()):
            if ds not in channels and ds not in datasources:
                dsg.pop(ds)
        for pc in channels:
            if pc not in dsg.keys():
                dsg[pc] = False
        self["DataSourceSelection"] = json.dumps(dsg)

    ## reset method for mntGrp attribute
    # \brief If MntGrp not defined set it to default value
    def resetMntGrp(self):
        if "MntGrp" not in self.keys() or not self["MntGrp"]:
            self["MntGrp"] = self.__defaultmntgrp

    ## reset method for timeZone attribute
    # \brief If TimeZone not defined set it to default value
    def resetTimeZone(self):
        if "TimeZone" not in self.keys() or not self["TimeZone"]:
            self["TimeZone"] = self.__defaultzone

    ## resets Preselected Components with given components and set them
    #  to not active
    # \param components list of components to be set
    def resetPreselectedComponents(self, components):
        acps = {}
        for cp in components:
            acps[cp] = False
        self["ComponentPreselection"] = json.dumps(acps)
