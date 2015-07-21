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
import getpass
import pickle
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
