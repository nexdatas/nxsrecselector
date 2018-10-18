#!/usr/bin/env python
#   This file is part of nxsrecconfig - NeXus Sardana Recorder Settings
#
#    Copyright (C) 2014-2017 DESY, Jan Kotanski <jkotan@mail.desy.de>
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

"""  Selection version converter """

import json


class ConverterXtoY(object):

    """ virtual selection version converter
    """

    def __init__(self):
        """ constructor
        """
        #: (:obj:`dict` <:obj:`str`, :obj:`str`>) names to convert
        self.names = {}

    def convert(self, selection):
        """ converts selection to the current selector version

        :param selection: selection dictionary object
        :type selection: :obj:`dict` <:obj:`str`, `any`>
        """
        for old, new in self.names.items():
            if old in list(selection.keys()):
                selection[new] = selection.pop(old)


class Converter2to3(ConverterXtoY):

    """ Selection converter from version 2 to 3
    """

    def __init__(self):
        """ converter
        """
        super(Converter2to3, self).__init__()

        #: (:obj:`dict` <:obj:`str`, :obj:`str`>) names to convert
        self.names = {
            "PreselectedDataSources": "PreselectingDataSources",
            "InitDataSources": "DataSourcePreselection",
        }

    def seltoint(self, jselelem):
        """ converters list/dict of elements to dictionary with logical values

        :param jselelem: json list or dict selection element
        :type jselelem: :obj:`str`
        :returns: json dictionary
        :rtype: :obj:`str`
        """
        sel = json.loads(jselelem)
        if isinstance(sel, dict):
            return json.dumps(
                dict((key, True if vl else None) for key, vl in sel.items()))
        elif isinstance(sel, (list, tuple)):
            return json.dumps(dict((key, True) for key in sel))

    def convert(self, selection):
        """ converts selection from version 2 to 3

        :param selection: selection dictionary object
        :type selection: :obj:`dict` <:obj:`str`, `any`>
        """
        super(Converter2to3, self).convert(selection)

        if 'ComponentPreselection' in selection.keys():
            selection["ComponentPreselection"] = self.seltoint(
                selection["ComponentPreselection"])
        if 'DataSourcePreselection' in selection.keys():
            selection["DataSourcePreselection"] = self.seltoint(
                selection["DataSourcePreselection"])
        if 'MntGrpConfiguration' not in selection.keys():
            selection['MntGrpConfiguration'] = ''


class Converter3to2(ConverterXtoY):

    """ Selection converter from version 3 to 2
    """

    def __init__(self):
        """ constructor
        """
        super(Converter3to2, self).__init__()

        #: (:obj:`dict` <:obj:`str`, :obj:`str`>) names to convert
        self.names = {
            "PreselectingDataSources": "PreselectedDataSources",
            "DataSourcePreselection": "InitDataSources",
        }

    def seltobool(self, jselelem):
        """ converters dictioanry with None/True/False values
            to dictionary with True/False values

        :param jselelem: json dictionary selection element
        :type jselelem: :obj:`str`
        :returns: converter json dictionary
        :rtype: :obj:`str`
        """
        sel = json.loads(jselelem)
        return json.dumps(
            dict((key, vl is not None) for key, vl in sel.items()))

    def seltolist(self, jselelem):
        """ converters dictioanry with None/True/False values
            to list of elementes with walue True

        :param jselelem: json dictionary selection element
        :type jselelem: :obj:`str`
        :returns: converter json dictionary
        :rtype: :obj:`str`
        """
        sel = json.loads(jselelem)
        return json.dumps([key for key, vl in sel.items() if vl])

    def convert(self, selection):
        """ converts selection from version 3 to 2

        :param selection: selection dictionary object
        :type selection: :obj:`dict` <:obj:`str`, `any`>
        """
        super(Converter3to2, self).convert(selection)
        if 'ComponentPreselection' in selection.keys():
            selection["ComponentPreselection"] = self.seltobool(
                selection["ComponentPreselection"])
        if 'InitDataSources' in selection.keys():
            selection['InitDataSources'] = self.seltolist(
                selection['InitDataSources'])
        if 'MntGrpConfiguration' in selection.keys():
            selection.pop('MntGrpConfiguration')


class Converter1to2(ConverterXtoY):

    """ Selection converter from version 1 to 2
    """

    def __init__(self):
        """ constructor
        """
        super(Converter1to2, self).__init__()

        #: (:obj:`dict` <:obj:`str`, :obj:`str`>) names to convert
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

        #: (:obj:`dict` <:obj:`str`, :obj:`str`>) names of properties
        self.pnames = {
            "Labels": "label",
            "LabelPaths": "nexus_path",
            "LabelLinks": "link",
            "LabelTypes": "data_type",
            "LabelShapes": "shape",
        }

    def convert(self, selection):
        """ converts selection from version 1 to 2

        :param selection: selection dictionary object
        :type selection: :obj:`dict` <:obj:`str`, `any`>
        """
        super(Converter1to2, self).convert(selection)
        props = {}
        for var, pn in self.pnames.items():
            if var in list(selection.keys()):
                props[pn] = json.loads(selection.pop(var))
        selection["ChannelProperties"] = json.dumps(props)


class Converter2to1(ConverterXtoY):

    """ Selection converter from version 2 to 1
    """

    def __init__(self):
        """ constructor
        """
        super(Converter2to1, self).__init__()

        #: (:obj:`dict` <:obj:`str`, :obj:`str`>) names of properties
        self.pnames = {
            "Labels": "label",
            "LabelPaths": "nexus_path",
            "LabelLinks": "link",
            "LabelTypes": "data_type",
            "LabelShapes": "shape",
        }

        #: (:obj:`dict` <:obj:`str`, :obj:`str`>) names to convert
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
        """ converts selection from version 2 to 1

        :param selection: selection dictionary object
        :type selection: :obj:`dict` <:obj:`str`, `any`>
        """
        super(Converter2to1, self).convert(selection)
        if "ChannelProperties" in selection:
            props = json.loads(selection["ChannelProperties"])
            for var, pn in self.pnames.items():
                if pn in props:
                    selection[var] = json.dumps(props.pop(pn))
            selection.pop("ChannelProperties")
        if "Version" in selection:
            selection.pop("Version")


class Converter(object):

    """ selection version converter """

    def __init__(self, ver):
        """ contstructor

        :param ver: the required selection version
        :type ver: :obj:`str`
        """

        sver = ver.split(".")
        #: (:obj:`int`) major selection version
        self.majorversion = int(sver[0])
        #: (:obj:`int`) minor selection version
        self.minorversion = int(sver[1])
        #: (:obj:`int`) patch selection version
        self.patchversion = int(sver[2])

        #: (:obj:`list` <:class:`ConverterXtoY`>) converter up sequence
        self.up = [Converter1to2(), Converter2to3()]
        #: (:obj:`list` <:class:`ConverterXtoY`>) converter down sequence
        self.down = [Converter2to1(), Converter3to2()]

    def allkeys(self, selection):
        """

        :param selection: selection dictionary object
        :type selection: nxsrecconfig.Selection.Selection
        :returns: selection keys
        :rtype: :obj:`set`
        """
        lkeys = set()
        for cv in self.up:
            lkeys.update(set(cv.names.keys()))
            lkeys.update(set(cv.names.values()))
        ak = set(selection.keys())
        ak.update(lkeys)
        return ak

    def convert(self, selection):
        """ converts selection from any version to any other

        :param selection: selection dictionary object
        :type selection: :obj:`dict` <:obj:`str`, `any`>
        """
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
        """ fetches selection version and converts it
            into (major, minor, patch)

        :param selection: selection dictionary object
        :type selection: nxsrecconfig.Selection.Selection
        :returns: (major, minor, patch) tuple with integers
        :rtype: (:obj:`int` , :obj:`int` , :obj:`int`)
        """
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
