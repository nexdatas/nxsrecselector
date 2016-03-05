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
## \file Converter.py
# selection converter

"""  Selection converter """

import json

## virtual selection converter
class ConverterXtoY(object):

    ## constructor
    def __init__(self):

        ## names to convert
        self.names = {}

    def convert(self, selection):
        for old, new in self.names.items():
            if old in selection.keys():
                selection[new] = selection.pop(old)


## Selection converter from 2 to 3
class Converter2to3(ConverterXtoY):

    def __init__(self):
        super(Converter2to3, self).__init__()

        ## names to convert
        self.names = {
            "PreselectedDataSources":"PreselectingDataSources",
            "InitDataSources": "DataSourcePreselection",
        }

    def seltoint(self, jselection):
        sel = json.loads(jselection)
        if isinstance(sel, dict):
            return json.dumps(
                dict((key, True if vl else None) for key, vl in sel.items()))
        elif isinstance(sel, (list, tuple)):
            return json.dumps(dict((key, True) for key in sel))


    def convert(self, selection):
        super(Converter2to3, self).convert(selection)

        if 'ComponentPreselection' in selection.keys():
            selection["ComponentPreselection"] = self.seltoint(
                selection["ComponentPreselection"])
        if 'DataSourcesPreselection' in selection.keys():
            selection["DataSourcePreselection"] = self.seltoint(
                selection["DataSourcePreselection"])

## Selection converter from 3 to 2
class Converter3to2(ConverterXtoY):

    def __init__(self):
        super(Converter3to2, self).__init__()

        ## names to convert
        self.names = {
            "PreselectingDataSources":"PreselectedDataSources",
            "DataSourcePreselection":"InitDataSources",
        }

    def seltobool(self, jselection):
        sel = json.loads(jselection)
        return json.dumps(
            dict((key, vl is not None) for key, vl in sel.items()))

    def seltolist(self, jselection):
        sel = json.loads(jselection)
        return json.dumps([key for key, vl in sel.items() if vl])


    def convert(self, selection):
        super(Converter3to2, self).convert(selection)
        if 'ComponentPreselection' in selection.keys():
            selection["ComponentPreselection"] = self.seltobool(
                selection["ComponentPreselection"])
        if 'InitDataSources' in selection.keys():
            selection['InitDataSources'] = self.seltolist(
                selection['InitDataSources'])

## Selection converter from 1 to 2
class Converter1to2(ConverterXtoY):

    def __init__(self):
        super(Converter1to2, self).__init__()

        ## names to convert
        self.names = {
            "AutomaticComponentGroup": "ComponentPreselection",
            "AutomaticDataSources": "PreselectedDataSources",
            "ComponentGroup": "ComponentSelection",
            "DataSourceGroup": "DataSourceSelection",
            "DataRecord": "UserData",
            "HiddenElements": "UnplottedComponents",
            "DynamicLinks": "DefaultDynamicLinks",
            "DynamicPath": "DefaultDynamicPath"

        }

        ## names of properties
        self.pnames = {
            "Labels": "label",
            "LabelPaths": "nexus_path",
            "LabelLinks": "link",
            "LabelTypes": "data_type",
            "LabelShapes": "shape",
        }

    def convert(self, selection):
        super(Converter1to2, self).convert(selection)
        props = {}
        for var, pn in self.pnames.items():
            if var in selection:
                props[pn] = json.loads(selection.pop(var))
        selection["ChannelProperties"] = json.dumps(props)


## Selection converter from 2 to 1
class Converter2to1(ConverterXtoY):

    def __init__(self):
        super(Converter2to1, self).__init__()

        ## names of properties
        self.pnames = {
            "Labels": "label",
            "LabelPaths": "nexus_path",
            "LabelLinks": "link",
            "LabelTypes": "data_type",
            "LabelShapes": "shape",
        }

        ## names to convert
        self.names = {
            "ComponentSelection": "ComponentGroup",
            "ComponentPreselection": "AutomaticComponentGroup",
            "PreselectedDataSources": "AutomaticDataSources",
            "DataSourceSelection": "DataSourceGroup",
            "UserData": "DataRecord",
            "UnplottedComponents": "HiddenElements",
            "DefaultDynamicLinks": "DynamicLinks",
            "DefaultDynamicPath": "DynamicPath"
        }

    def convert(self, selection):
        super(Converter2to1, self).convert(selection)
        if "ChannelProperties" in selection:
            props = json.loads(selection["ChannelProperties"])
            for var, pn in self.pnames.items():
                if pn in props:
                    selection[var] = json.dumps(props.pop(pn))
            selection.pop("ChannelProperties")
        if "Version" in selection:
            selection.pop("Version")


## Selection converter
class Converter(object):
    """ selection converer """

    ## constructor
    # \param ver the required selection version
    def __init__(self, ver):

        ##  selection dictionary with Settings
        sver = ver.split(".")
        self.majorversion = int(sver[0])
        self.minorversion = int(sver[1])
        self.patchversion = int(sver[2])

        self.up = [Converter1to2(), Converter2to3()]
        self.down = [Converter3to2(), Converter2to1()]

    def allkeys(self, selection):
        lkeys = set()
        for cv in self.up:
            lkeys.update(cv.names.keys())
        ak = set(selection.keys())
        ak.update(lkeys)
        return ak

    def convert(self, selection):
        major, _, _ = self.version(selection)
        if major == self.majorversion:
            return

        if major < self.majorversion:
            for i in range(major - 1, self.majorversion - 1):
                self.up[i].convert(selection)
        elif major > self.majorversion:
            for i in range(major - 2, self.majorversion - 2, -1):
                self.down[i].convert(selection)
        selection["Version"] = "%s.%s.%s" % (
            self.majorversion, self.minorversion, self.patchversion)

    @classmethod
    def version(cls, selection):
        major = 1
        minor = 0
        patch = 0
        if 'Version' in selection:
            ver = selection['Version']
            sver = ver.split(".")
            major = int(sver[0])
            minor = int(sver[1])
            patch = int(sver[2])
        return major, minor, patch
