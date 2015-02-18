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

import json
import PyTango
from .Utils import Utils


## NeXus Sardana Recorder settings
class Selection(object):
    """ selection state """

    ## constructor
    # \param configserver configuration server name
    def __init__(self, pfun):

        self.__pfun = pfun
        ## default zone
        self.__defaultzone = 'Europe/Berlin'

        ## default mntgrp
        self.__defaultmntgrp = 'nxsmntgrp'

        ##  dictionary with Settings
        self.__selection = {}

        ## tango database
        self.__db = PyTango.Database()

        ## module label
        self.moduleLabel = 'module'

        self.reset()

    def reset(self):
        self.__selection.clear()
        ## timer
        self.__selection["Timer"] = '[]'
        ## ordered channels
        self.__selection["OrderedChannels"] = '[]'
        ## group of electable components
        self.__selection["ComponentGroup"] = '{}'
        ## group of automatic components describing instrument state
        self.__selection["AutomaticComponentGroup"] = '{}'
        ## automatic datasources
        self.__selection["AutomaticDataSources"] = '[]'
        ## selected datasources
        self.__selection["DataSourceGroup"] = '{}'
        ## group of optional components available for automatic selqection
        self.__selection["OptionalComponents"] = '[]'
        ## appending new entries to existing file
        self.__selection["AppendEntry"] = False
        ## select components from the active measurement group
        self.__selection["ComponentsFromMntGrp"] = False
        ## Configuration Server variables
        self.__selection["ConfigVariables"] = '{}'
        ## JSON with Client Data Record
        self.__selection["DataRecord"] = '{}'
        ## JSON with Element Labels
        self.__selection["Labels"] = '{}'
        ## JSON with NeXus paths for Label Paths
        self.__selection["LabelPaths"] = '{}'
        ## JSON with NeXus paths for Label Links
        self.__selection["LabelLinks"] = '{}'
        ## JSON with NeXus paths for Label Displays
        self.__selection["HiddenElements"] = '[]'
        ## JSON with NeXus paths for Label Types
        self.__selection["LabelTypes"] = '{}'
        ## JSON with NeXus paths for Label Shapes
        self.__selection["LabelShapes"] = '{}'
        ## create dynamic components
        self.__selection["DynamicComponents"] = True
        ## create links for dynamic components
        self.__selection["DynamicLinks"] = True
        ## path for dynamic components
        self.__selection["DynamicPath"] = \
            '/entry$var.serialno:NXentry/NXinstrument/collection'
        ## timezone
        self.__selection["TimeZone"] = self.__defaultzone
        ## Configuration Server device name
        self.__selection["ConfigDevice"] = ''
        ## NeXus Data Writer device
        self.__selection["WriterDevice"] = ''
        ## Door device name
        self.__selection["Door"] = ''
        ## MntGrp
        self.__selection["MntGrp"] = ''

    def set(self, state):
        self.reset()
        for key in state.keys():
            self.__selection[key] = state[key]
            if hasattr(self, "_Selection__reset" + key):
                getattr(self, "_Selection__reset" + key)()

    ## provides names of variables
    def keys(self):
        return self.__selection.keys()

    def get(self):
        for key in self.keys():
            if hasattr(self, "_Selection__update" + key):
                getattr(self, "_Selection__update" + key)()
        return dict(self.__selection)

    def __getitem__(self, key):
        if key in self.keys():
            if hasattr(self, "_Selection__update" + key):
                getattr(self, "_Selection__update" + key)()
            return self.__selection[key]
        else:
            return None

    def __setitem__(self, key, value):
        self.__selection[key] = value
        if hasattr(self, "_Selection__reset" + key):
            getattr(self, "_Selection__reset" + key)()

    ## updates method for configDevice attribute
    def __updateConfigDevice(self):
        if "ConfigDevice" not in self.__selection.keys() \
                or not self.__selection["ConfigDevice"]:
            self.__selection["ConfigDevice"] = Utils.getDeviceName(
                self.__db, "NXSConfigServer")
        name = self.__selection["ConfigDevice"]
        if name:
            if name != self.moduleLabel:
                try:
                    dp = Utils.getProxies([name])
                    if not dp:
                        self.__selection["ConfigDevice"] = ''
                except:
                    self.__selection["ConfigDevice"] = ''
#            if self.__selection["ConfigDevice"]:
#                self.__pfun.storeConfiguration()

    ## get method for automaticDataSources attribute
    def __updateAutomaticDataSources(self):
        adsg = json.loads(self.__selection["AutomaticDataSources"])
        pmots = self.__pfun.poolMotors()
        adsg = list(set(adsg if adsg else []) | set(pmots if pmots else []))
        self.__selection["AutomaticDataSources"] = json.dumps(adsg)

    ## update method for orderedChannels attribute
    def __updateOrderedChannels(self):
        pch = self.__pfun.poolChannels()
        och = json.loads(self.__selection["OrderedChannels"])

        ordchannels = [ch for ch in och if ch in pch]
        uordchannels = list(set(pch) - set(och))
        ordchannels.extend(sorted(uordchannels))
        self.__selection["OrderedChannels"] = json.dumps(ordchannels)

    ## update method for mntGrp attribute
    def __updateMntGrp(self):
        if "MntGrp" not in self.keys() or not self.__selection["MntGrp"]:
            self.__selection["MntGrp"] = self.__defaultmntgrp

    ## update method for componentGroup attribute
    def __updateComponentGroup(self):
        cpg = json.loads(self.__selection["ComponentGroup"])
        dss = json.loads(self.__selection["DataSourceGroup"]).keys()
        for cp in set(cpg.keys()):
            if cp in dss:
                cpg.pop(cp)

        self.__selection["ComponentGroup"] = json.dumps(cpg)

    ## update method for dataSourceGroup attribute
    def __updateDataSourceGroup(self):
        dsg = json.loads(self.__selection["DataSourceGroup"])
        ads = self.__pfun.availableDataSources()
        pchs = self.__pfun.poolChannels()
        for ds in tuple(dsg.keys()):
            if ds not in pchs and ds not in ads:
                dsg.pop(ds)
        for pc in pchs:
            if pc not in dsg.keys():
                dsg[pc] = False
        self.__selection["DataSourceGroup"] = json.dumps(dsg)

    ## update method for door attribute
    def __updateDoor(self):
        try:
            if str(self.__selection["Door"]):
                dp = PyTango.DeviceProxy(str(self.__selection["Door"]))
                dp.ping()
        except:
            self.__selection["Door"] = ''
        if "Door" not in self.__selection.keys() \
                or not self.__selection["Door"]:
            self.__selection["Door"] = Utils.getDeviceName(
                self.__db, "Door")
            self.__pfun.updateMacroServer(self.__selection["Door"])

    ## update method for timeZone attribute
    def __updateTimeZone(self):
        if "TimeZone" not in self.keys() or not self.__selection["TimeZone"]:
            self.__selection["TimeZone"] = self.__defaultzone

    ## update method for writerDevice attribute
    # \returns name of writerDevice
    def __updateWriterDevice(self):
        if "WriterDevice" not in self.__selection.keys() \
                or not self.__selection["WriterDevice"]:
            self.__selection["WriterDevice"] = Utils.getDeviceName(
                self.__db, "NXSDataWriter")

    ## reset method for configDevice attribute
    def __resetConfigDevice(self):
        if not self.__selection["ConfigDevice"]:
            self.__selection["ConfigDevice"] = Utils.getDeviceName(
                self.__db, "NXSConfigServer")

    ## set method for mntGrp attribute
    def __resetMntGrp(self):
        if not self.__selection["MntGrp"]:
            self.__selection["MntGrp"] = self.__defaultmntgrp

    ## set method for timeZone attribute
    # \param name of timeZone
    def __resetTimeZone(self):
        if not self.__selection["TimeZone"]:
            self.__selection["TimeZone"] = self.__defaultzone

    ## set method for door attribute
    def __resetDoor(self):
        if not self.__selection["Door"]:
            self.__selection["Door"] = Utils.getDeviceName(
                self.__db, "Door")

    ## set method for writerDevice attribute
    def __resetWriterDevice(self):
        if not self.__selection["WriterDevice"]:
            self.__selection["WriterDevice"] = Utils.getDeviceName(
                self.__db, "NXSDataWriter")
