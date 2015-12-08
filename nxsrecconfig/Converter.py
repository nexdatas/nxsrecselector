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
## \file Converter.py
# selection converter

"""  Selection converter """


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
            "LabelPaths": "nexus_path",
            "LabelLinks": "link",
            "LabelTypes": "data_type",
            "LabelShapes": "shape",
        }


    def convert(self, selection):
        super(Converter1to2, self).convert(selection)
        props = {}
        for var, pn in pnames.items():
            if var in selection:
                self.addProperties(json.loads(selection.pop(var)), pn, props)
        selection["ChannelProperties"] = json.dumps(props)


## Selection converter from 2 to 1
class Converter2to1(ConverterXtoY):

    def __init__(self):
        super(Converter2to1, self).__init__()

        ## names of properties
        self.pnames = {
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
            self.addVariables(self.pnames, props, selection)
            selection["ChannelProperties"] = json.dumps(props)


## Selection converter
class Converter(object):
    """ selection converer """

    ## constructor
    # \param version the required selection version
    def __init__(self, version):

        ##  selection dictionary with Settings
        sver = version.split(".")
        self.majorversion = int(sver[0])
        self.minorversion = int(sver[1])
        self.patchversion = int(sver[2])

        self.__up = [Converter1to2()]
        self.__down = [Converter2to1()]
        self.__allkeys = set()
        for cv in self.__up:
            self.__allkeys.update(cv.names.keys())

    def allkeys(self, selection):
        ak = set(selection.keys())
        ak.update(self.__allkeys)
        return ak

    def convert(self, selection):
        major, _, _ = self.getVersion(selection)
        if major == self.majorversion:
            return

        if major < self.majorversion:
            for i in range(major - 1, self.majorversion - 1):
                self.__up[i].convert(selection)
        elif major > self.majorversion:
            for i in range(major - 2, self.majorversion - 2, -1):
                self.__down[i].convert(selection)

    @classmethod
    def getVersion(cls, selection):
        major = 1
        minor = 0
        patch = 0
        if 'Version' in selection:
            version = selection['Version']
            sver = version.split(".")
            major = int(sver[0])
            minor = int(sver[1])
            patch = int(sver[2])
        return major, minor, patch

    @classmethod    
    def addVariables(self, pnames, props, selection):
        for var, pn in pnames.items():
            svars = json.loads(selection[var]) if var in selection else {}
            for ch, prs in props.keys():
                if pn in prs:
                    svars[ch] = prs.pop(pn)
            selection[var] = json.dumps(svars)

    @classmethod    
    def removeProperties(cls, name, props):
        for ch, prs in props.items():
            if name in prs.keys():
                prs[ch].pop(name)
        
    @classmethod    
    def addProperties(cls, variables, name, props):
        for ch, value in variables.items():
            if ch not in props:
                props[ch] = {}
            props[ch][name] = value

    @classmethod    
    def updateProperties(cls, variables, name, props):
        cls.removeProperties(cls, name props)
        cls.addProperties(cls, variables, name props)
