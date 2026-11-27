#!/usr/bin/env python
#   This file is part of nxsrecconfig - NeXus Sardana Recorder Settings
#
#    Copyright (C) 2014-2026 DESY, Jan Kotanski <jkotan@mail.desy.de>
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

""" scan backend interface, i.e. the control system of the scans

The selector settings access the control system running the scans, e.g.
Sardana, only via a scan backend: its scan environment, its channels
(given by pools in Sardana), its measurement groups and its targets
(doors in Sardana).
"""

import json

from .Utils import Utils, TangoUtils
from .Describer import Describer
from .CheckerThread import CheckerThread, TangoDSItem, CheckerItem

import queue as Queue


class ScanBackend(object):

    """ scan backend interface """

    #: (:obj:`str`) backend name
    name = None

    #: (:obj:`bool`) the backend provides measurement group devices
    supportsMntGrps = False

    #: (:obj:`bool`) the backend selects channels of its measurement groups
    #:   by :meth:`selectChannels` for backends without measurement
    #:   group devices
    selectsChannels = False

    #: (:obj:`list` <:obj:`str`>) types of STEP datasources without
    #:   channels which are read by the scan system
    #:   via :meth:`selectDataSources`
    dataSourceTypes = []

    def __init__(self, numberOfThreads=None):
        """ constructor

        :param numberOfThreads: number of threads
        :type numberOfThreads: :obj:`str`
        """
        self._numberOfThreads = numberOfThreads or 0

        #: (:obj:`str`) nexus configuration variable name in environment
        self._nxsenv = "NeXusConfiguration"

        #: (:obj:`list` <:obj:`str`>) black list of pools
        self.poolBlacklist = []

        #: (:obj:`list` <:obj:`str`>) pure variables
        self._pureVar = [
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

        #: (:obj:`list` <:obj:`str`>) tango datasources off states
        self.tangoSourceErrorStates = [
            "OFF", "INIT", "INSERT", "CLOSE", "UNKNOWN", "FAULT"]

        #: (:obj:`list` <:obj:`str`>) tango datasources warning states
        self.tangoSourceWarningStates = ["ALARM", "DISABLE"]

    # targets, i.e. doors in sardana

    def defaultDoor(self, db):
        """ provides the default target of the scans

        :param db: tango database
        :type db: :class:`tango.Database`
        :returns: target name, e.g. door device name
        :rtype: :obj:`str`
        """
        raise NotImplementedError()

    def isDoorValid(self, door):
        """ checks if the target of the scans is valid

        :param door: target name, e.g. door device name
        :type door: :obj:`str`
        :returns: True if valid
        :rtype: :obj:`bool`
        """
        raise NotImplementedError()

    def updateMacroServer(self, door):
        """ updates the scan server and its channel sources for given target

        :param door: target name, e.g. door device name
        :type door: :obj:`str`
        :returns: scan server name, e.g. macroserver device name
        :rtype: :obj:`str`
        """
        raise NotImplementedError()

    def getMacroServer(self, door):
        """ provides the scan server name for given target

        :param door: target name, e.g. door device name
        :type door: :obj:`str`
        :returns: scan server name, e.g. macroserver device name
        :rtype: :obj:`str`
        """
        raise NotImplementedError()

    def getPools(self, door):
        """ provides channel sources, i.e. sardana pool proxies

        :param door: target name, e.g. door device name
        :type door: :obj:`str`
        :returns: pool proxies, an empty list without pools
        :rtype: :obj:`list` <:class:`tango.DeviceProxy`>
        """
        raise NotImplementedError()

    def isDoorRunning(self, ms):
        """ checks if a scan is running

        :param ms: scan server name, e.g. macroserver device name
        :type ms: :obj:`str`
        :returns: True if a scan is running
        :rtype: :obj:`bool`
        """
        raise NotImplementedError()

    # channels

    def nonExistingChannels(self, door, channels):
        """ provides the channels which are not known to the backend

        :param door: target name, e.g. door device name
        :type door: :obj:`str`
        :param channels: channel names
        :type channels: :obj:`list` <:obj:`str`>
        :returns: channels not provided by the backend
        :rtype: :obj:`list` <:obj:`str`>
        """
        raise NotImplementedError()

    def channelSource(self, name):
        """ provides the tango source of a channel

        :param name: channel name
        :type name: :obj:`str`
        :returns: tango attribute name or None
        :rtype: :obj:`str`
        """
        raise NotImplementedError()

    # scan environment

    def getEnv(self, var, ms):
        """ provides a scan environment variable

        :param var: variable name
        :type var: :obj:`str`
        :param ms: scan server name, e.g. macroserver device name
        :type ms: :obj:`str`
        :returns: variable value
        :rtype: `any`
        """
        raise NotImplementedError()

    def setEnv(self, var, value, ms):
        """ sets a scan environment variable

        :param var: variable name
        :type var: :obj:`str`
        :param value: variable value
        :type value: `any`
        :param ms: scan server name, e.g. macroserver device name
        :type ms: :obj:`str`
        """
        raise NotImplementedError()

    def setEnvs(self, varvalues, ms):
        """ sets scan environment variables

        :param varvalues: variable names and values
        :type varvalues: :obj:`dict` <:obj:`str`, `any`>
        :param ms: scan server name, e.g. macroserver device name
        :type ms: :obj:`str`
        """
        raise NotImplementedError()

    def usetEnv(self, var, ms):
        """ unsets a scan environment variable

        :param var: variable name
        :type var: :obj:`str`
        :param ms: scan server name, e.g. macroserver device name
        :type ms: :obj:`str`
        """
        raise NotImplementedError()

    def getSelectorEnv(self, door, names, data):
        """ provides selector variables from the scan environment

        :param door: target name, e.g. door device name
        :type door: :obj:`str`
        :param names: names of variables
        :type names: :obj:`list` <:obj:`str`>
        :param data: dictionary to be filled with the variables
        :type data: :obj:`dict` <:obj:`str`, `any`>
        """
        raise NotImplementedError()

    def setSelectorEnv(self, door, data, cmddata=None):
        """ stores selector variables in the scan environment

        :param door: target name, e.g. door device name
        :type door: :obj:`str`
        :param data: variables
        :type data: :obj:`dict` <:obj:`str`, `any`>
        :param cmddata: command variables
        :type cmddata: :obj:`dict` <:obj:`str`, `any`>
        """
        raise NotImplementedError()

    def getScanEnv(self, door):
        """ provides scan file variables of the scan environment

        :param door: target name, e.g. door device name
        :type door: :obj:`str`
        :returns: JSON string with the variables
        :rtype: :obj:`str`
        """
        raise NotImplementedError()

    def setScanEnv(self, door, jdata):
        """ sets scan file variables of the scan environment

        :param door: target name, e.g. door device name
        :type door: :obj:`str`
        :param jdata: JSON string with the variables
        :type jdata: :obj:`str`
        :returns: scan id
        :rtype: :obj:`int`
        """
        raise NotImplementedError()

    # measurement groups, see supportsMntGrps

    def createMntGrp(self, pool, name, timer):
        """ creates a measurement group

        :param pool: pool proxy
        :type pool: :class:`tango.DeviceProxy`
        :param name: measurement group name
        :type name: :obj:`str`
        :param timer: timer name
        :type timer: :obj:`str`
        """
        raise NotImplementedError()

    def deleteMntGrp(self, pool, name):
        """ deletes a measurement group

        :param pool: pool proxy
        :type pool: :class:`tango.DeviceProxy`
        :param name: measurement group name
        :type name: :obj:`str`
        """
        raise NotImplementedError()

    def mntGrpConfiguration(self, device):
        """ provides the measurement group configuration

        :param device: measurement group device name
        :type device: :obj:`str`
        :returns: JSON configuration
        :rtype: :obj:`str`
        """
        raise NotImplementedError()

    def setMntGrpConfiguration(self, device, conf):
        """ sets the measurement group configuration

        :param device: measurement group device name
        :type device: :obj:`str`
        :param conf: JSON configuration
        :type conf: :obj:`str`
        :returns: the configuration read back from the device
        :rtype: :obj:`str`
        """
        raise NotImplementedError()

    def testMntGrpConfiguration(self, device, conf):
        """ provides the configuration the measurement group makes of conf
            and restores its current configuration

        :param device: measurement group device name
        :type device: :obj:`str`
        :param conf: JSON configuration
        :type conf: :obj:`str`
        :returns: the configuration read back from the device
        :rtype: :obj:`str`
        """
        raise NotImplementedError()

    def selectChannels(self, ms, mntgrp, channels):
        """ selects channels of a measurement group of the scan system

        It is used by backends without measurement group devices
        and with :attr:`selectsChannels`

        :param ms: scan server name
        :type ms: :obj:`str`
        :param mntgrp: measurement group name
        :type mntgrp: :obj:`str`
        :param channels: ordered channel names
        :type channels: :obj:`list` <:obj:`str`>
        """

    def selectDataSources(self, ms, mntgrp, datasources):
        """ selects STEP datasources without channels of the scan system
            to be read in scans of a measurement group

        It is used by backends with :attr:`dataSourceTypes`

        :param ms: scan server name
        :type ms: :obj:`str`
        :param mntgrp: measurement group name
        :type mntgrp: :obj:`str`
        :param datasources: datasource descriptions by datasource names,
                            i.e. dictionaries with ``xml`` definitions,
                            ``nxtype`` NeXus types and ``rank``
        :type datasources: :obj:`dict` <:obj:`str`, :obj:`dict`>
        """

    # helpers for the environment variables

    def _readSelectorEnv(self, env, names, data):
        """ reads selector variables from environment variables

        :param env: environment variables
        :type env: :obj:`dict` <:obj:`str`, `any`>
        :param names: names of variables
        :type names: :obj:`list` <:obj:`str`>
        :param data: dictionary to be filled with the variables
        :type data: :obj:`dict` <:obj:`str`, `any`>
        """
        params = ["ScanDir",
                  "ScanFile"]
        nenv = {}
        vl = None
        if self._nxsenv in env.keys():
            nenv = env[self._nxsenv]
        for var in names:
            name = var if var in params else ("NeXus%s" % var)
            if name in env.keys():
                vl = env[name]
            elif var in nenv.keys():
                vl = nenv[var]
            else:
                continue
            if type(vl) not in [str, bool, int, str, float]:
                vl = json.dumps(vl)
            data[var] = vl

    def _selectorEnvUpdate(self, data, cmddata=None):
        """ provides environment variables of selector variables

        :param data: variables
        :type data: :obj:`dict` <:obj:`str`, `any`>
        :param cmddata: command variables
        :type cmddata: :obj:`dict` <:obj:`str`, `any`>
        :returns: environment variables to be set
        :rtype: :obj:`dict` <:obj:`str`, `any`>
        """
        params = ["ScanDir",
                  "ScanFile"]
        env = {self._nxsenv: {}}
        nenv = env[self._nxsenv]
        for var in data.keys():
            if var in self._pureVar:
                vl = data[var]
            else:
                try:
                    vl = json.loads(data[var])
                except (ValueError, TypeError):
                    vl = data[var]
            if var in params:
                env[Utils.tostr(var)] = vl
            else:
                nenv["%s" % var] = vl
        if cmddata:
            for name, value in cmddata.items():
                nenv[Utils.tostr(name)] = value
        return env

    @classmethod
    def _readScanEnv(cls, env):
        """ reads scan file variables from environment variables

        :param env: environment variables
        :type env: :obj:`dict` <:obj:`str`, `any`>
        :returns: scan file variables
        :rtype: :obj:`dict` <:obj:`str`, `any`>
        """
        params = ["ScanDir",
                  "ScanFile",
                  "ScanID",
                  "NeXusSelectorDevice"]
        return dict((var, env[var]) for var in params if var in env.keys())

    @classmethod
    def _scanEnvUpdate(cls, data):
        """ provides environment variables of scan file variables

        :param data: scan file variables
        :type data: :obj:`dict` <:obj:`str`, `any`>
        :returns: environment variables to be set
        :rtype: :obj:`dict` <:obj:`str`, `any`>
        """
        return dict((Utils.tostr(var), Utils.toString(data[var]))
                    for var in data.keys())

    # channel checks

    @classmethod
    def __toCheck(cls, configdevice, discomponentgroup, components,
                  datasources, channels, nonexisting):
        """ prepares list of channels to check

        :param configdevice: configuration device proxy
        :type configdevice: :class:`tango.DeviceProxy` \
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
                "%s not defined in Configuration Server" % k
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
        :type configdevice: :class:`tango.DeviceProxy` \
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
        nonexisting = self.nonExistingChannels(door, channels)

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
        if self._numberOfThreads < 1:
            self._numberOfThreads = len(toCheck)

        for i in range(min(self._numberOfThreads, len(toCheck))):
            thd = CheckerThread(i, cqueue)
            thd.tangoSourceErrorStates = self.tangoSourceErrorStates
            thd.tangoSourceWarningStates = self.tangoSourceWarningStates
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
