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

"""  Selection state """

import json


class Selection(dict):

    """ Selection Dictionary which contains the following records:
    {
    "Timer":  '[]',
    "OrderedChannels":  '[]',
    "ComponentSelection":  '{}',
    "DataSourceSelection":  '{}',
    "DataSourcePreselection":  '{}',
    "ComponentPreselection":  '{}',
    "PreselectingDataSources":  '[]',
    "OptionalComponents":  '[]',
    "AppendEntry":  False,
    "ComponentsFromMntGrp":  False,
    "ConfigVariables":  '{}',
    "UserData":  '{}',
    "ChannelProperties":  '{}',
    "UnplottedComponents":  '[]',
    "DynamicComponents":  True,
    "DefaultDynamicLinks":  True,
    "DefaultDynamicPath":  \
    '/$var.entryname#'scan'$var.serialno:NXentry/NXinstrument/collection',
    "TimeZone":  self.__defaultzone,
    "ConfigDevice":  '',
    "WriterDevice":  '',
    "Door":  '',
    "MntGrp":  '',
    "Version":  self.__version,
    "MntGrpConfiguration":  ''
    }

    """

    def __init__(self, *args, **kw):
        """ constructor

        :param args: dictionary args
        :type args: :obj:`list` <`any`>
        :param kw: dictionary kw
        :type kw: :obj:`dict` <:obj:`str`, `any`>
        """
        super(Selection, self).__init__(*args, **kw)

        #: (:obj:`str`) default zone
        self.__defaultzone = self['TimeZone'] \
            if 'TimeZone' in self else 'Europe/Berlin'

        #: (:obj:`str`) default mntgrp
        self.__defaultmntgrp = self['MntGrp'] \
            if 'MntGrp' in self else 'nxsmntgrp'
        #: (:obj:`str`) version string
        self.__version = self["Version"] \
            if "Version" in self else "1.0.0"
        self.reset()

    def reset(self):
        """ resets dictionary to default value
        """
        self.clear()
        # timer
        self["Timer"] = '[]'
        # ordered channels
        self["OrderedChannels"] = '[]'
        # group of electable components
        self["ComponentSelection"] = '{}'
        # step selected datasources
        self["DataSourceSelection"] = '{}'
        # init preselected datasources
        self["DataSourcePreselection"] = '{}'
        # group of preselected components describing instrument state
        self["ComponentPreselection"] = '{}'
        # preselected datasources
        self["PreselectingDataSources"] = '[]'
        # group of optional components available for preselected selqection
        self["OptionalComponents"] = '[]'
        # appending new entries to existing file
        self["AppendEntry"] = False
        # select components from the active measurement group
        self["ComponentsFromMntGrp"] = False
        # Configuration Server variables
        self["ConfigVariables"] = '{}'
        # JSON with Client Data Record
        self["UserData"] = '{}'
        # JSON with channel properties
        self["ChannelProperties"] = '{}'
        # JSON with NeXus paths for Label Paths
        self["UnplottedComponents"] = '[]'
        # create dynamic components
        self["DynamicComponents"] = True
        # create links for dynamic components
        self["DefaultDynamicLinks"] = True
        # path for dynamic components
        self["DefaultDynamicPath"] = \
            "/$var.entryname#'scan'$var.serialno:NXentry" \
            "/NXinstrument/collection"
        # timezone
        self["TimeZone"] = self.__defaultzone
        # Configuration Server device name
        self["ConfigDevice"] = ''
        # NeXus Data Writer device
        self["WriterDevice"] = ''
        # Door device name
        self["Door"] = ''
        # MntGrp
        self["MntGrp"] = ''
        # version
        self["Version"] = self.__version
        # MntGrp configuration
        self["MntGrpConfiguration"] = ''

    def deselect(self):
        """ deselects components and datasources
        """
        cps = json.loads(self["ComponentSelection"])
        ads = json.loads(self["DataSourceSelection"])
        for k in cps.keys():
            cps[k] = False
        for k in ads.keys():
            ads[k] = False
        self["DataSourcePreselection"] = '{}'
        self["DataSourceSelection"] = json.dumps(ads)
        self["ComponentSelection"] = json.dumps(cps)
        self["UnplottedComponents"] = '[]'

    def updatePreselectingDataSources(self, datasources):
        """ update method for Preselected DataSources

        :brief: appends new datasources to Preselected DataSources
        :param datasources: list of datasources
        :type datasources: :obj:`list` <:obj:`str`>
        """
        adsg = json.loads(self["PreselectingDataSources"])
        adsg = list(set(adsg or []) | set(datasources or []))
        self["PreselectingDataSources"] = json.dumps(adsg)

    def updateOrderedChannels(self, channels):
        """ update method for orderedChannels attribute

        :brief: sets pool channels in order defined by OrderedChannels
        :param channels: pool channels
        :type channels: :obj:`list` <:obj:`str`>
        """
        och = json.loads(self["OrderedChannels"])
        ordchannels = [ch for ch in och if ch in channels]
        uordchannels = list(set(channels) - set(och))
        ordchannels.extend(sorted(uordchannels))
        self["OrderedChannels"] = json.dumps(ordchannels)

    def updateChannelProperties(self, devicecontrollers, triggergate):
        """ update method for orderedChannels attribute

        :brief: sets pool channels in order defined by OrderedChannels
        :param devicecontrollers: device controller dictionary
        :type devicecontrollers: :obj:`dict` <:obj:`str`, :obj:`str`>
        :param triggergate: trigger gate list
        :type triggergate: :obj:`list` <:obj:`str`>
        """
        props = json.loads(self["ChannelProperties"])
        if devicecontrollers:
            props["__controllers__"] = devicecontrollers
        if triggergate:
            props["__triggergatelist__"] = triggergate
        self["ChannelProperties"] = json.dumps(props)

    def updateComponentSelection(self):
        """ update method for componentGroup attribute

        :brief: It removes datasource components from component group
        """
        cpg = json.loads(self["ComponentSelection"])
        dss = list(json.loads(self["DataSourceSelection"]).keys())
        for cp in set(cpg.keys()):
            if cp in dss:
                cpg.pop(cp)
        self["ComponentSelection"] = json.dumps(cpg)

    def updateDataSourceSelection(self, channels, datasources):
        """ update method for dataSourceGroup attribute

        :brief: It removes datasources from DataSourceSelection if they are
                neither in poolchannels nor in avaiblable datasources
                It adds new channels to DataSourceSelection
        :param channels: pool channels
        :type channels: :obj:`list` <:obj:`str`>
        :param datasources: available datasources
        :type datasources: :obj:`list` <:obj:`str`>
        """
        dsg = json.loads(self["DataSourceSelection"])
        datasources = datasources or []
        for ds in tuple(dsg.keys()):
            if ds not in channels and ds not in datasources:
                dsg.pop(ds)
        for pc in channels:
            if pc not in dsg.keys():
                dsg[pc] = False
        self["DataSourceSelection"] = json.dumps(dsg)

    def resetMntGrp(self):
        """ reset method for mntGrp attribute

        :brief: If MntGrp not defined set it to default value
        """
        if "MntGrp" not in self.keys() or not self["MntGrp"]:
            self["MntGrp"] = self.__defaultmntgrp

    def resetTimeZone(self):
        """ reset method for timeZone attribute

        :brief: If TimeZone not defined set it to default value
        """
        if "TimeZone" not in self.keys() or not self["TimeZone"]:
            self["TimeZone"] = self.__defaultzone

    def resetPreselectedComponents(self, components):
        """ resets Preselected Components with given components and set them
        to not active
        :param components: list of components to be set
        :type components: :obj:`list` <:obj:`str`>
        """
        acps = {}
        for cp in components:
            acps[cp] = None
        self["ComponentPreselection"] = json.dumps(acps)
