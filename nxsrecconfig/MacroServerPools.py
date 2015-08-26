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
## \file MacroServerPools.py
# sardana macro server and pools

"""  Selection state """

import json
import PyTango
import Queue
import pickle
from .Utils import Utils, TangoUtils, MSUtils, PoolUtils
from .Describer import Describer
from .CheckerThread import CheckerThread, TangoDSItem, CheckerItem


## NeXus Sardana Recorder settings
class MacroServerPools(object):
    """ sardanamacro server and pools """

    ## constructor
    # \param configserver configuration server name
    def __init__(self, numberOfThreads):

        self.__numberOfThreads = numberOfThreads

        ## tango database
        self.__db = PyTango.Database()

        self.__nxsenv = "NeXusConfiguration"

        ## macro server instance
        self.__macroserver = ""
        ## pool instances
        self.__pools = []
        ## black list of pools
        self.poolBlacklist = []

        self.__pureVar = [
            "AppendEntry",
            "ComponentsFromMntGrp",
            "DynamicComponents",
            "DynamicLinks",
            "DynamicPath",
            "TimeZone",
            "ConfigDevice",
            "WriterDevice",
            "Door",
            "MntGrp",
            "ScanDir"
            ]

    ## updates MacroServer and sardana pools for given door
    # \param door door device
    def updateMacroServer(self, door):
        if not door:
            raise Exception("Door '%s' cannot be found" % door)
        self.__macroserver = MSUtils.getMacroServer(self.__db, door)
        msp = TangoUtils.openProxy(self.__macroserver)
        pnames = msp.get_property("PoolNames")["PoolNames"]
        if not pnames:
            pnames = []
        poolNames = list(
            set(pnames) - set(self.poolBlacklist))
        self.__pools = TangoUtils.getProxies(poolNames)

    ## door macro server device name
    # \param door door device
    # \returns macroserver device name
    def getMacroServer(self, door):
        if not self.__macroserver:
            self.updateMacroServer(door)
        return self.__macroserver

    ## door pool device proxies
    # \param door door device
    # \returns pool device proxies
    def getPools(self, door):
        if not self.__pools:
            self.updateMacroServer(door)
        return self.__pools

    @classmethod
    def __toCheck(cls, configdevice, discomponentgroup, components, channels,
                  nonexisting):
        describer = Describer(configdevice, True)
        availablecomponents = TangoUtils.command(configdevice,
                                                 "availableComponents")

        discomponentgroup.update(dict(
                [str(k), ("...", "%s not defined in Configuration Server" % k)]
                for k in set(components) - set(availablecomponents)))
        toCheck = {}
        for acp in components:
            res = describer.components([acp], '', '')
            for cp, dss in res[0].items():
                if isinstance(dss, dict):
                    tgds = describer.dataSources(dss.keys(), 'TANGO')
                    for ds in dss.keys():
                        if ds in tgds.keys():
                            if cp not in toCheck.keys():
                                toCheck[cp] = CheckerItem(cp)
                            srec = tgds[ds].record.split("/")
                            attr = srec[-1]
                            toCheck[cp].append(
                                TangoDSItem(str(ds),
                                            str("/".join(srec[:-1])),
                                            str(attr)))
                        elif ds in nonexisting:
                            discomponentgroup[cp] = \
                                (ds, "%s not defined in Pool" % ds)
                            if cp in toCheck.keys():
                                toCheck.pop(cp)
                            break
                        elif ds in channels:
                            if cp not in toCheck.keys():
                                toCheck[cp] = CheckerItem(cp)
                            toCheck[cp].append(TangoDSItem(str(ds)))
        return toCheck.values()

    def checkComponentChannels(self, door, configdevice, channels,
                               componentgroup, channelerrors):
        channelerrors[:] = []
        discomponentgroup = {}
        threads = []
        pools = self.getPools(door)
        fnames = PoolUtils.getFullDeviceNames(pools, channels)
        nonexisting = [dev for dev in channels if dev not in fnames.keys()]
        toCheck = self.__toCheck(configdevice, discomponentgroup,
                                 componentgroup.keys(),
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

        for acp in componentgroup.keys():
            if acp in discomponentgroup.keys():
                checkeritem = discomponentgroup[acp]
                channelerrors.append(json.dumps(
                        {"component": str(acp),
                         "datasource": str(checkeritem.errords),
                         "message": str(checkeritem.message)}))
                componentgroup[acp] = checkeritem.enabled
            else:
                componentgroup[acp] = True

        return json.dumps(componentgroup)

    ## imports Environment Data
    # \param door door device
    # \param names names of required variables
    # \param data dictionary with resulting data
    def getSelectorEnv(self, door, names, data):
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
                    if type(vl) not in [str, bool, int, unicode]:
                        vl = json.dumps(vl)
                    data[var] = vl

    ## exports all Environment Data
    # \param door door device
    def setSelectorEnv(self, door, data, cmddata=None):
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
                        except ValueError:
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

    ## fetches Scan Environment Data
    # \param door door device
    # \returns JSON String with important variables
    def getScanEnv(self, door):
        params = ["ScanDir",
                  "ScanFile",
                  "ScanID",
#                  "ActiveMntGrp",
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

    ## stores Scan Environment Data
    # \param door door device
    # \param jdata JSON String with important variables
    def setScanEnv(self, door, jdata):
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
