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
import PyTango
import sys

from .Utils import (
    Utils, TangoUtils, MSUtils, PoolUtils, OldTangoError, PYTG_BUG_213)
from .Describer import Describer
from .CheckerThread import CheckerThread, TangoDSItem, CheckerItem

if sys.version_info > (3,):
    import queue as Queue
else:
    import Queue

if sys.version_info > (3,):
    unicode = str


class MacroServerPools(object):

    """ sardanamacro server and pools """

    #

    def __init__(self, numberOfThreads):
        """ constructor

        :param numberOfThreads: number of threads
        :type numberOfThreads: :obj:`str`
        """
        self.__numberOfThreads = numberOfThreads

        #: (:class:`PyTango.Database`) tango database
        self.__db = PyTango.Database()

        #: (:obj:`str`) nexus configuration variable name in ms
        self.__nxsenv = "NeXusConfiguration"

        #: (:obj:`str`) macro server device name
        self.__macroserver = ""
        #: (:obj:`list` <:obj:`PyTango.DeviceProxy`>) pool instances
        self.__pools = []
        #: (:obj:`list` <:obj:`str`>) black list of pools
        self.poolBlacklist = []

        #: (:obj:`list` <:obj:`str`>) pure variables
        self.__pureVar = [
            "AppendEntry",
            "ComponentsFromMntGrp",
            "DynamicComponents",
            "DefaultDynamicLinks",
            "DefaultDynamicPath",
            "TimeZone",
            "ConfigDevice",
            "WriterDevice",
            "Door",
            "MntGrp",
            "ScanDir"
        ]

    def updateMacroServer(self, door):
        """ updates MacroServer and sardana pools for given door

        :param door: door device name
        :type door: :obj:`str`
        """
        self.__macroserver = ""
        self.__pools = []
        host = None
        port = None
        if not door:
            raise Exception("Door '%s' cannot be found" % door)
        if ":" in door.split("/")[0] and len(door.split("/")) > 1:
            host, port = door.split("/")[0].split(":")
            db = PyTango.Database(host, int(port))
            macroserver = MSUtils.getMacroServer(db, door)
        else:
            macroserver = MSUtils.getMacroServer(self.__db, door)
        msp = TangoUtils.openProxy(macroserver)
        pnames = msp.get_property("PoolNames")["PoolNames"]
        if not pnames:
            pnames = []
        poolNames = list(
            set(pnames) - set(self.poolBlacklist))
        poolNames = ["%s/%s" % (door.split("/")[0], pn)
                     if (host and ":" not in pn)
                     else pn
                     for pn in poolNames]
        self.__pools = TangoUtils.getProxies(poolNames)
        self.__macroserver = macroserver

    def getMacroServer(self, door):
        """ door macro server device name

        :param door: door device name
        :type door: :obj:`str`
        :returns: macroserver device name
        :rtype: :obj:`str`
        """
        if not self.__macroserver:
            self.updateMacroServer(door)
        return self.__macroserver

    def getPools(self, door):
        """ door pool device proxies

        :param door: door device name
        :type door: :obj:`str`
        :returns: pool device proxies
        :rtype: :obj:`list` <:obj:`PyTango.DeviceProxy`>
        """
        if not self.__pools:
            self.updateMacroServer(door)
        return self.__pools

    @classmethod
    def __toCheck(cls, configdevice, discomponentgroup, components,
                  datasources, channels, nonexisting):
        """ prepares list of channels to check

        :param configdevice: configuration device proxy
        :type configdevice: :class:`PyTango.DeviceProxy` \
             or :class:`nxsconfigserver.XMLConfigurator.XMLConfigurator`
        :param discomponentgroup: name dictionary of checker items
        :type discomponentgroup: :obj:`dict` <:obj:`str` ,
            :class:`nxsrecconfig.CheckerThread.CheckerItem`>
        :param components: component list
        :type components: :obj:`list` <:obj:`str`>
        :param datasources: datasource list
        :type datasources: :obj:`list` <:obj:`str`>
        :param channels: pool channel list
        :type channels: :obj:`list` <:obj:`str`>
        :param nonexisting: non-exising pool channels
        :type nonexisting: :obj:`list` <:obj:`str`>
        :returns: list of CheckerItems
        :rtype: :obj:`list` <:class:`nxsrecconfig.CheckerThread.CheckerItem`>
        """
        describer = Describer(configdevice, True, pyevalfromscript=True)
        availablecomponents = TangoUtils.command(
            configdevice, "availableComponents")
        availabledatasouces = TangoUtils.command(
            configdevice, "availableDataSources")

        for k in set(components) - set(availablecomponents):
            discomponentgroup[Utils.tostr(k)] = CheckerItem(Utils.tostr(k))
            discomponentgroup[Utils.tostr(k)].errords = "..."
            discomponentgroup[Utils.tostr(k)].active = False
            discomponentgroup[Utils.tostr(k)].message = \
                "%s not defined in Configuration Server" % k
        for k in set(datasources) - set(availabledatasouces):
            discomponentgroup[Utils.tostr(k)] = CheckerItem(Utils.tostr(k))
            discomponentgroup[Utils.tostr(k)].errords = k
            discomponentgroup[Utils.tostr(k)].active = False
            discomponentgroup[Utils.tostr(k)].message = \
                "%s not defined i<n Configuration Server" % k
        toCheck = {}
        cps = set(components) & set(availablecomponents)
        for acp in cps:
            res = describer.components([acp], '', '')
            for cp, dss in res[0].items():
                for ds in dss.keys():
                    if ds not in availabledatasouces:
                        discomponentgroup[Utils.tostr(cp)] = CheckerItem(
                            Utils.tostr(cp))
                        discomponentgroup[Utils.tostr(cp)].errords = ds
                        discomponentgroup[Utils.tostr(cp)].active = False
                        discomponentgroup[Utils.tostr(cp)].message = \
                            "%s of %s not defined in Configuration Server" \
                            % (ds, cp)
                        break
                cls.__createCheckItem(cp, dss, toCheck, nonexisting,
                                      discomponentgroup, channels, describer)
        adss = set(datasources) & set(availabledatasouces)
        for ads in adss:
            res = describer.dataSources([ads])
            if ads not in res[0].keys():
                res[0][ads] = None
            cls.__createCheckItem(ads, res[0], toCheck, nonexisting,
                                  discomponentgroup, channels, describer)
        return list(toCheck.values())

    @classmethod
    def __createCheckItem(cls, name, dss, toCheck, nonexisting,
                          discomponentgroup, channels, describer):
        """ creates Checker Item

        :param name: item name
        :type name: :obj:`str`
        :param dss: datasource dictionary
        :type dss: :obj:`dict` <:obj:`str`, `any`>
        :param toCheck: dictionary with checker items
        :type toCheck: :obj:`dict` <:obj:`str` ,
            :class:`nxsrecconfig.CheckerThread.CheckerItem`>
        :param nonexisting: non-exising pool channels
        :type nonexisting: :obj:`list` <:obj:`str`>
        :param discomponentgroup: name dictionary of checker items
        :type discomponentgroup: :obj:`dict` <:obj:`str` ,
            :class:`nxsrecconfig.CheckerThread.CheckerItem`>
        :param channels: pool channel list
        :type channels: :obj:`list` <:obj:`str`>
        :param describer: describer instance
        :type describer: :class:`nxsrecconfig.Describer.Describer`
        """
        if isinstance(dss, dict):
            tgds = describer.dataSources(list(dss.keys()), 'TANGO')[0]
            for ds in dss.keys():
                if ds in tgds.keys():
                    if name not in toCheck.keys():
                        toCheck[name] = CheckerItem(name)
                    srec = tgds[ds].record.split("/")
                    attr = srec[-1]
                    toCheck[name].append(
                        TangoDSItem(Utils.tostr(ds),
                                    Utils.tostr("/".join(srec[:-1])),
                                    Utils.tostr(attr)))
                elif ds in nonexisting:
                    discomponentgroup[name] = CheckerItem(name)
                    discomponentgroup[name].errords = ds
                    discomponentgroup[name].active = False
                    discomponentgroup[name].message = \
                        "%s not defined in Pool" % ds

                    if name in list(toCheck.keys()):
                        toCheck.pop(name)
                    break
                elif ds in channels:
                    if name not in toCheck.keys():
                        toCheck[name] = CheckerItem(name)
                    toCheck[name].append(TangoDSItem(Utils.tostr(ds)))

    def checkChannels(self, door, configdevice, channels,
                      componentgroup, datasourcegroup,
                      channelerrors):
        """ checks component channels

        :param door: door device name
        :type door: :obj:`str`
        :param configdevice: configuration server
        :type configdevice: :class:`PyTango.DeviceProxy` \
             or :class:`nxsconfigserver.XMLConfigurator.XMLConfigurator`
        :param channels: pool channels
        :type channels: :obj:`list` <:obj:`str`>
        :param componentgroup: preselected component group
        :type componentgroup: :obj:`dict` <:obj:`str` , :obj:`bool`>
        :param channelerrors: list of deactivated component errors
        :type channelerrors: :obj:`list` <:obj:`str`>
        :returns: json dictionary with selected active components
        :rtype: :obj:`str`
        """
        channelerrors[:] = []
        discomponentgroup = {}
        threads = []
        pools = self.getPools(door)
        fnames = PoolUtils.getFullDeviceNames(pools, channels)
        nonexisting = [dev for dev in channels if dev not in fnames.keys()]

        toCheck = self.__toCheck(
            configdevice, discomponentgroup,
            [cp for cp in componentgroup.keys()
             if componentgroup[cp] is not False],
            [ds for ds in datasourcegroup.keys()
             if datasourcegroup[ds] is not False],
            channels, nonexisting)

        cqueue = Queue.Queue()
        for checkeritem in toCheck:
            cqueue.put(checkeritem)
        if self.__numberOfThreads < 1:
            self.__numberOfThreads = len(toCheck)

        for i in range(min(self.__numberOfThreads, len(toCheck))):
            thd = CheckerThread(i, cqueue)
            threads.append(thd)
            thd.start()

        for th in threads:
            th.join()

        for checkeritem in toCheck:
            if checkeritem.errords is not None:
                discomponentgroup[checkeritem.name] = checkeritem

        self.__updategroup(componentgroup, discomponentgroup,
                           channelerrors)
        self.__updategroup(datasourcegroup, discomponentgroup,
                           channelerrors)

        return (json.dumps(componentgroup), json.dumps(datasourcegroup))

    @classmethod
    def __updategroup(cls, group, disgroup, channelerrors):
        """ updates selection dictionary

        :param group: selection dictionary
        :type group: :obj:`dict` <:obj:`str` , :obj:`bool`>
        :param disgroup: dictionary with checker items
        :type disgroup: :obj:`dict` <:obj:`str` ,
            :class:`nxsrecconfig.CheckerThread.CheckerItem`>
        :param channelerrors: list with channel errors
        :type channelerrors: :obj:`list` <:obj:`str`>
        """
        for acp in group.keys():
            if acp in disgroup.keys():
                checkeritem = disgroup[acp]
                channelerrors.append(json.dumps(
                    {"component": Utils.tostr(acp),
                     "datasource": Utils.tostr(checkeritem.errords),
                     "message": Utils.tostr(checkeritem.message)}
                ))
                if checkeritem.active is False:
                    group[acp] = None
                elif group[acp] is not False:
                    group[acp] = True
            else:
                if group[acp] is not False:
                    group[acp] = True

    def getSelectorEnv(self, door, names, data):
        """ imports Environment Data

        :param door: door device
        :type door: :obj:`str`
        :param names: names of required variables
        :type names: :obj:`list` <:obj:`str`>
        :param data: dictionary with resulting data
        :type data: :obj:`dict` <:obj:`str` , `any`>
        """
        params = ["ScanDir",
                  "ScanFile"]

        msp = TangoUtils.openProxy(self.getMacroServer(door))
        if PYTG_BUG_213:
            raise OldTangoError(
                "Reading Encoded Attributes not supported in PyTango < 9.2.5")
        rec = msp.Environment
        nenv = {}
        vl = None
        if rec[0] == 'pickle':
            dc = Utils.pickleloads(rec[1])
            if 'new' in dc.keys():
                if self.__nxsenv in dc['new'].keys():
                    nenv = dc['new'][self.__nxsenv]
                for var in names:
                    name = var if var in params else ("NeXus%s" % var)
                    if name in dc['new'].keys():
                        vl = dc['new'][name]
                    elif var in nenv.keys():
                        vl = nenv[var]
                    else:
                        continue
                    if type(vl) not in [str, bool, int, unicode, float]:
                        vl = json.dumps(vl)
                    data[var] = vl

    def setSelectorEnv(self, door, data, cmddata=None):
        """ exports all Environment Data

        :param door: door device
        :type door: :obj:`str`
        :param data: data dictionary
        :type data: :obj:`dict` <:obj:`str` , `any`>
        :param cmddata: command data dictionary
        :type cmddata: :obj:`dict` <:obj:`str` , `any`>
        """
        params = ["ScanDir",
                  "ScanFile"]

        msp = TangoUtils.openProxy(self.getMacroServer(door))
        if PYTG_BUG_213:
            raise OldTangoError(
                "Reading Encoded Attributes not supported in PyTango < 9.2.5")
        rec = msp.Environment
        if rec[0] == 'pickle':
            dc = Utils.pickleloads(rec[1])
            if 'new' in dc.keys():
                dc = {'new': {}}
                if self.__nxsenv not in dc['new'].keys() \
                        or not isinstance(dc['new'][self.__nxsenv], dict):
                    dc = {'new': {self.__nxsenv: {}}}
                else:
                    dc = {'new': {self.__nxsenv: dc['new'][self.__nxsenv]}}

                nenv = dc['new'][self.__nxsenv]
                for var in data.keys():
                    if var in self.__pureVar:
                        vl = data[var]
                    else:
                        try:
                            vl = json.loads(data[var])
                        except (ValueError, TypeError):
                            vl = data[var]
                    if var in params:
                        dc['new'][Utils.tostr(var)] = vl
                    else:
                        nenv[("%s" % var)] = vl

                if cmddata:
                    for name, value in cmddata.items():
                        nenv[Utils.tostr(name)] = value
                MSUtils.writeEnvAttr(dc, msp)

    def getScanEnv(self, door):
        """ fetches Scan Environment Data

        :param door: door device
        :type door: :obj:`str`
        :returns: JSON String with important variables
        :rtype: :obj:`str`
        """
        params = ["ScanDir",
                  "ScanFile",
                  "ScanID",
                  # "ActiveMntGrp",
                  "NeXusSelectorDevice"]
        res = {}
        msp = TangoUtils.openProxy(self.getMacroServer(door))
        if PYTG_BUG_213:
            raise OldTangoError(
                "Reading Encoded Attributes not supported in "
                "PyTango < 9.2.5")
        rec = msp.Environment
        if rec[0] == 'pickle':
            dc = Utils.pickleloads(rec[1])
            if 'new' in dc.keys():
                for var in params:
                    if var in dc['new'].keys():
                        res[var] = dc['new'][var]
        return json.dumps(res)

    def setScanEnv(self, door, jdata):
        """ stores Scan Environment Data

        :param door: door device
        :type door: :obj:`str`
        :param jdata: JSON String with important variables
        :type jdata: :obj:`str`
        """
        jdata = Utils.stringToDictJson(jdata)
        data = json.loads(jdata)
        scanID = -1
        msp = TangoUtils.openProxy(self.getMacroServer(door))
        if PYTG_BUG_213:
            raise OldTangoError(
                "Reading Encoded Attributes not supported in "
                "PyTango < 9.2.5")
        rec = msp.Environment
        if rec[0] == 'pickle':
            dc = Utils.pickleloads(rec[1])
            if 'new' in dc.keys():
                if 'ScanID' in dc['new'].keys():
                    scanID = int(dc['new']["ScanID"])
            dc = {'new': {}}
            for var in data.keys():
                dc['new'][Utils.tostr(var)] = Utils.toString(data[var])
            if 'ScanID' in dc['new'].keys():
                scanID = int(dc['new']["ScanID"])
            MSUtils.writeEnvAttr(dc, msp)
        return scanID
