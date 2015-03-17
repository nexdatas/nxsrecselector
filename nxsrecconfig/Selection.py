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
## \file state.py
# component describer

"""  Selection state """

import json
import PyTango
import Queue
import threading
import getpass
import pickle
from .Utils import Utils
from .Describer import Describer


ATTRIBUTESTOCHECK = ["Value", "Position", "Counts", "Data",
                     "Voltage", "Energy", "SampleTime"]


## NeXus Sardana Recorder settings
class Selection(object):
    """ selection state """

    ## constructor
    # \param configserver configuration server name
    def __init__(self, numberOfThreads):

        self.__numberOfThreads = numberOfThreads
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

        ## macro server instance
        self.__macroserver = ""
        ## pool instances
        self.__pools = []
        ## config server proxy
        self.__configProxy = None
        ## config server module
        self.__configModule = None
        ## black list of pools
        self.poolBlacklist = []

        self.__nxsenv = "NeXusConfiguration"

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
        ## init datasources
        self.__selection["InitDataSources"] = '[]'
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
            if key and key[0].upper() != key[0]:
                key = key[0].upper() + key[1:]
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
            if key and key[0].upper() != key[0]:
                key = key[0].upper() + key[1:]
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
                except (PyTango.DevFailed, PyTango.Except, PyTango.DevError):
                    self.__selection["ConfigDevice"] = ''

    ## get method for automaticDataSources attribute
    def __updateAutomaticDataSources(self):
        adsg = json.loads(self.__selection["AutomaticDataSources"])
        pmots = self.poolMotors()
        adsg = list(set(adsg if adsg else []) | set(pmots if pmots else []))
        self.__selection["AutomaticDataSources"] = json.dumps(adsg)

    ## update method for orderedChannels attribute
    def __updateOrderedChannels(self):
        pch = self.poolChannels()
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
        ads = self.configCommand("availableDataSources")
        ads = ads if ads else []
        pchs = self.poolChannels()
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
        except (PyTango.DevFailed, PyTango.Except, PyTango.DevError):
            self.__selection["Door"] = ''
        if "Door" not in self.__selection.keys() \
                or not self.__selection["Door"]:
            self.__selection["Door"] = Utils.getDeviceName(
                self.__db, "Door")
            self.updateMacroServer(self.__selection["Door"])

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

    def __toCheck(self, rcp, acps, ads, nonexisting):
        describer = Describer(self.setConfigInstance())
        toCheck = {}
        for acp in acps.keys():
            res = describer.components([acp], '', '')
            for cp, dss in res[1].items():
                if isinstance(dss, dict):
                    tgds = describer.dataSources(dss.keys(), 'TANGO')
                    for ds in dss.keys():
                        if ds in tgds.keys():
                            if cp not in toCheck.keys():
                                toCheck[cp] = [cp]
                            srec = tgds[ds][2].split("/")
                            attr = srec[-1]
                            toCheck[cp].append(
                                (str(ds), str("/".join(srec[:-1])), str(attr)))
                        elif ds in nonexisting:
                            rcp.add(cp)
                            if cp in toCheck.keys():
                                toCheck.pop(cp)
                            break
                        elif ds in ads:
                            if cp not in toCheck.keys():
                                toCheck[cp] = [cp]
                            toCheck[cp].append(str(ds))
        return toCheck

    def updateControllers(self, pools):
        ads = set(json.loads(self["AutomaticDataSources"]))
        nonexisting = []
        fnames = Utils.getFullDeviceNames(pools, ads)

        for dev in ads:
            if dev not in fnames.keys():
                nonexisting.append(dev)

        acps = json.loads(self["AutomaticComponentGroup"])

        rcp = set()
        toCheck = self.__toCheck(rcp, acps, ads, nonexisting)

        cqueue = Queue.Queue()
        for lds in toCheck.values():
            cqueue.put(lds)
        for _ in range(self.__numberOfThreads):
            thd = threading.Thread(target=checker, args=(cqueue,))
            thd.daemon = True
            thd.start()
        cqueue.join()

        for lds in toCheck.values():
            if lds and len(lds) > 0:
                rcp.add(lds[0])

        for acp in acps.keys():
            if acp in rcp:
                acps[acp] = False
            else:
                acps[acp] = True

        return json.dumps(acps)

    def getPools(self):
        if not self.__pools:
            self.updateMacroServer(self["Door"])
        return self.__pools

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

    def getMacroServer(self):
        if not self.__macroserver:
            self.updateMacroServer(self["Door"])
        return self.__macroserver

    ## sets config instances
    # \returns set config instance
    def setConfigInstance(self):
        if "ConfigDevice" not in self.__selection.keys() \
                or not self.__selection["ConfigDevice"]:
            self.__updateConfigDevice()

        if self.__selection["ConfigDevice"] and \
                self.__selection["ConfigDevice"].lower() != self.moduleLabel:
            self.__configProxy = Utils.openProxy(
                self.__selection["ConfigDevice"])
            self.__configProxy.open()
            self.__configModule = None
        else:
            from nxsconfigserver import XMLConfigurator
            from MySQLdb.connections import DatabaseError
            self.__configModule = XMLConfigurator.XMLConfigurator()
            self.getMacroServer()

            data = {}
            self.importEnv(['DBParams'], data)
            if 'DBParams' in data.keys():
                dbp = data['DBParams']
            else:
                dbp = '{}'

            try:
                self.__configModule.jsonsettings = dbp
                self.__configModule.open()
                self.__configModule.availableComponents()
            except DatabaseError:
                user = getpass.getuser()
                dbp = '{"host":"localhost","db":"nxsconfig",' \
                    + '"use_unicode":true,' \
                    + '"read_default_file":"/home/%s/.my.cnf"}' % user
                self.__configModule.jsonsettings = dbp
                self.__configModule.open()
                self.__configModule.availableComponents()
            self.__configProxy = None
        return self.__configProxy \
            if self.__configProxy else self.__configModule

    ## executes command on configuration server
    # \returns command result
    def configCommand(self, command, var=None):
        inst = self.setConfigInstance()
        if var is None:
            res = getattr(inst, command)()
        else:
            if self.__configProxy:
                res = inst.command_inout(command, var)
            else:
                res = getattr(inst, command)(var)
        return res

    ## available pool channels
    # \returns pool channels of the macroserver pools
    def poolChannels(self):
        res = []
        ms = self.getMacroServer()
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
    def poolMotors(self):
        res = []
        ms = self.getMacroServer()
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

    ## imports Enviroutment Data
    # \param names names of required variables
    # \param data dictionary with resulting data
    def importEnv(self, names=None, data=None):
        params = ["ScanDir",
                  "ScanFile"]

        if names is None:
            names = self.keys()
        if data is None:
            data = self

        dp = Utils.openProxy(self.getMacroServer())
        rec = dp.Environment
        nenv = {}
        if rec[0] == 'pickle':
            dc = pickle.loads(rec[1])
            if 'new' in dc.keys():
                if self.__nxsenv in dc['new'].keys():
                    nenv = dc['new'][self.__nxsenv]
                for var in names:
                    name = var if var in params else ("NeXus%s" % var)
                    if name in dc['new'].keys():
                        vl = dc['new'][name]
                        if type(vl) not in [str, bool, int, unicode]:
                            vl = json.dumps(vl)
                        data[var] = vl
                    elif var in nenv.keys():
                        vl = nenv[var]
                        if type(vl) not in [str, bool, int, unicode]:
                            vl = json.dumps(vl)
                        data[var] = vl

    ## exports all Enviroutment Data
    def exportEnv(self, data=None, cmddata=None):
        params = ["ScanDir",
                  "ScanFile"]

        if data is None:
            data = self

        ms = self.getMacroServer()
        msp = Utils.openProxy(ms)

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

    ## fetches Enviroutment Data
    # \returns JSON String with important variables
    def fetchEnvData(self):
        params = ["ScanDir",
                  "ScanFile",
                  "ScanID",
#                  "ActiveMntGrp",
                  "NeXusSelectorDevice"]
        res = {}
        dp = Utils.openProxy(self.getMacroServer())
        rec = dp.Environment
        if rec[0] == 'pickle':
            dc = pickle.loads(rec[1])
            if 'new' in dc.keys():
                for var in params:
                    if var in dc['new'].keys():
                        res[var] = dc['new'][var]
        return json.dumps(res)

    ## stores Enviroutment Data
    # \param jdata JSON String with important variables
    def storeEnvData(self, jdata):
        jdata = Utils.stringToDictJson(jdata)
        data = json.loads(jdata)
        scanID = -1
        ms = self.getMacroServer()
        msp = Utils.openProxy(ms)

        rec = msp.Environment
        if rec[0] == 'pickle':
            dc = pickle.loads(rec[1])
            if 'new' in dc.keys():
                for var in data.keys():
                    dc['new'][str(var)] = data[var]
                pk = pickle.dumps(dc)
                if 'ScanID' in dc['new'].keys():
                    scanID = int(dc['new']["ScanID"])
                msp.Environment = ['pickle', pk]
        return scanID


class WrongStateError(Exception):
    pass


## checkers if Tango devices are alive
# \params cqueue queue with task of the form ['comp','alias','alias', ...]
def checker(cqueue):
    while True:
        lds = cqueue.get()
        ok = True
        for ds in lds[1:]:
            if isinstance(ds, tuple) and len(ds) > 2:
                dname = str(ds[1])
                attr = str(ds[2])
            else:
                dname = str(ds)
                attr = None

            try:
                dp = PyTango.DeviceProxy(dname)
                if dp.state() in [
                    PyTango.DevState.FAULT,
                    PyTango.DevState.ALARM]:
                    raise WrongStateError("FAULT or ALARM STATE")
                dp.ping()
                if not attr:
                    for gattr in ATTRIBUTESTOCHECK:
                        if hasattr(dp, gattr):
                            _ = getattr(dp, gattr)
                else:
                    _ = getattr(dp, attr)
            except (PyTango.DevFailed, PyTango.Except, PyTango.DevError,
                    WrongStateError):
                ok = False
                break
        if ok:
            lds[:] = []
        cqueue.task_done()
