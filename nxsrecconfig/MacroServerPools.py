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
#import getpass
#import pickle
from .Utils import Utils
from .Describer import Describer
from .CheckerThread import CheckerThread


## NeXus Sardana Recorder settings
class MacroServerPools(object):
    """ sardanamacro server and pools """

    ## constructor
    # \param configserver configuration server name
    def __init__(self, numberOfThreads):

        self.__numberOfThreads = numberOfThreads

        ## tango database
        self.__db = PyTango.Database()

        ## macro server instance
        self.__macroserver = ""
        ## pool instances
        self.__pools = []
        ## black list of pools
        self.poolBlacklist = []

    ## updates MacroServer and sardana pools for given door
    # \param door door device
    def updateMacroServer(self, door):
        if not door:
            raise Exception("Door '%s' cannot be found" % door)
        self.__macroserver = Utils.getMacroServer(self.__db, door)
        msp = Utils.openProxy(self.__macroserver)
        pnames = msp.get_property("PoolNames")["PoolNames"]
        if not pnames:
            pnames = []
        poolNames = list(
            set(pnames) - set(self.poolBlacklist))
        self.__pools = Utils.getProxies(poolNames)

    ## available pool channels
    # \param door door device
    # \returns pool channels of the macroserver pools
    def poolChannels(self, door):
        res = []
        ms = self.getMacroServer(door)
        msp = Utils.openProxy(ms)
        pn = msp.get_property("PoolNames")["PoolNames"]
        if pn:
            for pl in pn:
                pool = Utils.openProxy(pl)
                exps = pool.ExpChannelList
                if exps:
                    for jexp in exps:
                        if jexp:
                            exp = json.loads(jexp)
                            if exp and isinstance(exp, dict):
                                res.append(exp['name'])
        return res

    ## available pool motors
    # \returns pool motors of the macroserver pools
    def poolMotors(self, door):
        res = []
        ms = self.getMacroServer(door)
        msp = Utils.openProxy(ms)
        pn = msp.get_property("PoolNames")["PoolNames"]
        if pn:
            for pl in pn:
                pool = Utils.openProxy(pl)
                exps = pool.MotorList
                if exps:
                    for jexp in exps:
                        if jexp:
                            exp = json.loads(jexp)
                            if exp and isinstance(exp, dict):
                                res.append(exp['name'])
        return res

    def getMacroServer(self, door):
        if not self.__macroserver:
            self.updateMacroServer(door)
        return self.__macroserver

    def getPools(self, door):
        if not self.__pools:
            self.updateMacroServer(door)
        return self.__pools

    @classmethod
    def __toCheck(cls, inst, rcp, acps, ads, nonexisting):
        describer = Describer(inst, True)
        avcp = Utils.command(inst, "availableComponents")

        rcp.update(dict(
                [str(k), ("...", "%s not defined in Configuration Server" % k)]
                for k in set(acps) - set(avcp)))
        toCheck = {}
        for acp in acps.keys():
            res = describer.components([acp], '', '')
            for cp, dss in res[0].items():
                if isinstance(dss, dict):
                    tgds = describer.dataSources(dss.keys(), 'TANGO')
                    for ds in dss.keys():
                        if ds in tgds.keys():
                            if cp not in toCheck.keys():
                                toCheck[cp] = [cp]
                            srec = tgds[ds].record.split("/")
                            attr = srec[-1]
                            toCheck[cp].append(
                                (str(ds), str("/".join(srec[:-1])), str(attr)))
                        elif ds in nonexisting:
                            rcp[cp] = (ds, "%s not defined in Pool" % ds)
                            if cp in toCheck.keys():
                                toCheck.pop(cp)
                            break
                        elif ds in ads:
                            if cp not in toCheck.keys():
                                toCheck[cp] = [cp]
                            toCheck[cp].append(str(ds))
        return toCheck

    def updateControllers(self, inst, ads, acps, door, descErrors):
        descErrors[:] = []
        rcp = {}
        threads = []
        pools = self.getPools(door)
        fnames = Utils.getFullDeviceNames(pools, ads)
        nonexisting = [dev for dev in ads if dev not in fnames.keys()]
        toCheck = self.__toCheck(inst, rcp, acps, ads, nonexisting)

        cqueue = Queue.Queue()
        for lds in toCheck.values():
            cqueue.put(lds)
        if self.__numberOfThreads < 1:
            self.__numberOfThreads = len(toCheck.values())

        for i in range(min(self.__numberOfThreads, len(toCheck.values()))):
            thd = CheckerThread(i, cqueue)
            threads.append(thd)
            thd.start()

        for th in threads:
            th.join()

        for lds in toCheck.values():
            if lds and len(lds) > 0:
                rcp[lds[0]] = (lds[1], lds[2])

        for acp in acps.keys():
            if acp in rcp.keys():
                value = rcp[acp]
                descErrors.append(json.dumps(
                        {"component": str(acp),
                         "datasource": str(value[0]),
                         "message": str(value[1])}))
                if str(value[1]) != "ALARM_STATE":
                    acps[acp] = False
                else:
                    acps[acp] = True
            else:
                acps[acp] = True

        return json.dumps(acps)
