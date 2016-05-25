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
#

"""  Selection state """

import json
import PyTango
import Queue
import pickle
from .Utils import Utils, TangoUtils, MSUtils, PoolUtils
from .Describer import Describer
from .CheckerThread import CheckerThread, TangoDSItem, CheckerItem


class MacroServerPools(object):
    """ sardanamacro server and pools """

    ##
    def __init__(self, numberOfThreads):
        """ constructor

        :param numberOfThreads: number of threads
        """
        self.__numberOfThreads = numberOfThreads

        #: tango database
        self.__db = PyTango.Database()

        #: nexus configuration variable name in ms
        self.__nxsenv = "NeXusConfiguration"

        #: macro server instance
        self.__macroserver = ""
        #: pool instances
        self.__pools = []
        #: black list of pools
        self.poolBlacklist = []

        #: pure variables
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
        """
        self.__macroserver = ""
        self.__pools = []
        if not door:
            raise Exception("Door '%s' cannot be found" % door)
        macroserver = MSUtils.getMacroServer(self.__db, door)
        msp = TangoUtils.openProxy(macroserver)
        pnames = msp.get_property("PoolNames")["PoolNames"]
        if not pnames:
            pnames = []
        poolNames = list(
            set(pnames) - set(self.poolBlacklist))
        self.__pools = TangoUtils.getProxies(poolNames)
        self.__macroserver = macroserver

    def getMacroServer(self, door):
        """ door macro server device name

        :param door: door device name
        :returns: macroserver device name
        """
        if not self.__macroserver:
            self.updateMacroServer(door)
        return self.__macroserver

    def getPools(self, door):
        """ door pool device proxies
        :param door: door device name
        :returns: pool device proxies
        """
        if not self.__pools:
            self.updateMacroServer(door)
        return self.__pools

    @classmethod
    def __toCheck(cls, configdevice, discomponentgroup, components,
                  datasources, channels, nonexisting):
        """ prepares list of channels to check

        :param configdevice: configuration device proxy
        :param discomponentgroup: name dictionary of checker items
        :param components: component list
        :param datasources: datasource list
        :param channel: pool channel list
        :param nonexisting: non-exising pool channels
        :returns: list of CheckerItems
        """
        describer = Describer(configdevice, True, pyevalfromscript=True)
        availablecomponents = TangoUtils.command(
            configdevice, "availableComponents")

        for k in set(components) - set(availablecomponents):
            discomponentgroup[str(k)] = CheckerItem(str(k))
            discomponentgroup[str(k)].errords = "..."
            discomponentgroup[str(k)].active = False
            discomponentgroup[str(k)].message = \
                "%s not defined in Configuration Server" % k
        toCheck = {}
        for acp in components:
            res = describer.components([acp], '', '')
            for cp, dss in res[0].items():
                cls.__createCheckItem(cp, dss, toCheck, nonexisting,
                                      discomponentgroup, channels, describer)

        for ads in datasources:
            cls.__createCheckItem(ads, {ads: None}, toCheck, nonexisting,
                                  discomponentgroup, channels, describer)

        return toCheck.values()

    @classmethod
    def __createCheckItem(cls, name, dss, toCheck, nonexisting,
                          discomponentgroup, channels, describer):
        """ creates Checker Item

        :param name: item name
        :param dss: datasource dictionary
        :param toCheck: dictionary with checker items
        :param nonexisting: non-exising pool channels
        :param discomponentgroup: name dictionary of checker items
        :param channel: pool channel list
        :param describer: describer instance
        """
        if isinstance(dss, dict):
            tgds = describer.dataSources(dss.keys(), 'TANGO')[0]
            for ds in dss.keys():
                if ds in tgds.keys():
                    if name not in toCheck.keys():
                        toCheck[name] = CheckerItem(name)
                    srec = tgds[ds].record.split("/")
                    attr = srec[-1]
                    toCheck[name].append(
                        TangoDSItem(str(ds),
                                    str("/".join(srec[:-1])),
                                    str(attr)))
                elif ds in nonexisting:
                    discomponentgroup[name] = CheckerItem(name)
                    discomponentgroup[name].errords = ds
                    discomponentgroup[name].active = False
                    discomponentgroup[name].message = \
                        "%s not defined in Pool" % ds

                    if name in toCheck.keys():
                        toCheck.pop(name)
                    break
                elif ds in channels:
                    if name not in toCheck.keys():
                        toCheck[name] = CheckerItem(name)
                    toCheck[name].append(TangoDSItem(str(ds)))

    def checkChannels(self, door, configdevice, channels,
                      componentgroup, datasourcegroup,
                      channelerrors):
        """ checks component channels

        :param door: door device name
        :param configdevice: configuration server
        :param channels: pool channels
        :param componentgroup: preselected component group
        :param channelerrors: deactivated component errors
        :returns: json dictionary with selected active components
        """
        channelerrors[:] = []
        discomponentgroup = {}
        threads = []
        pools = self.getPools(door)
        fnames = PoolUtils.getFullDeviceNames(pools, channels)
        nonexisting = [dev for dev in channels if dev not in fnames.keys()]

        toCheck = self.__toCheck(configdevice, discomponentgroup,
                                 componentgroup.keys(),
                                 datasourcegroup.keys(),
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
        :param disgroup: dictionary with checker items
        :param channelerrors: list with channel errors
        """
        for acp in group.keys():
            if acp in disgroup.keys():
                checkeritem = disgroup[acp]
                channelerrors.append(json.dumps(
                    {"component": str(acp),
                     "datasource": str(checkeritem.errords),
                     "message": str(checkeritem.message)}
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
        :param names: names of required variables
        :param data: dictionary with resulting data
        """
        params = ["ScanDir",
                  "ScanFile"]

        msp = TangoUtils.openProxy(self.getMacroServer(door))
        rec = msp.Environment
        nenv = {}
        vl = None
        if rec[0] == 'pickle':
            dc = pickle.loads(rec[1])
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
        :param data: data dictionary
        :param cmddata: command data dictionary
        """
        params = ["ScanDir",
                  "ScanFile"]

        msp = TangoUtils.openProxy(self.getMacroServer(door))
        rec = msp.Environment
        if rec[0] == 'pickle':
            dc = pickle.loads(rec[1])
            if 'new' in dc.keys():
                if self.__nxsenv not in dc['new'].keys() \
                        or not isinstance(dc['new'][self.__nxsenv], dict):
                    dc['new'][self.__nxsenv] = {}
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
                        dc['new'][str(var)] = vl
                    else:
                        nenv[("%s" % var)] = vl

                if cmddata:
                    for name, value in cmddata.items():
                        nenv[str(name)] = value
                pk = pickle.dumps(dc)
                msp.Environment = ['pickle', pk]

    def getScanEnv(self, door):
        """ fetches Scan Environment Data

        :param door: door device
        :returns: JSON String with important variables
        """
        params = ["ScanDir",
                  "ScanFile",
                  "ScanID",
                  # "ActiveMntGrp",
                  "NeXusSelectorDevice"]
        res = {}
        msp = TangoUtils.openProxy(self.getMacroServer(door))
        rec = msp.Environment
        if rec[0] == 'pickle':
            dc = pickle.loads(rec[1])
            if 'new' in dc.keys():
                for var in params:
                    if var in dc['new'].keys():
                        res[var] = dc['new'][var]
        return json.dumps(res)

    def setScanEnv(self, door, jdata):
        """ stores Scan Environment Data

        :param door: door device
        :param jdata: JSON String with important variables
        """
        jdata = Utils.stringToDictJson(jdata)
        data = json.loads(jdata)
        scanID = -1
        msp = TangoUtils.openProxy(self.getMacroServer(door))
        rec = msp.Environment
        if rec[0] == 'pickle':
            dc = pickle.loads(rec[1])
            if 'new' in dc.keys():
                for var in data.keys():
                    dc['new'][str(var)] = Utils.toString(data[var])
                pk = pickle.dumps(dc)
                if 'ScanID' in dc['new'].keys():
                    scanID = int(dc['new']["ScanID"])
                msp.Environment = ['pickle', pk]
        return scanID
