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

"""  ProfileManager """

import json
import sys
import PyTango

from .Utils import TangoUtils, PoolUtils, MSUtils, Utils
from .Describer import Describer

try:
    from nxstools.nxsxml import (XMLFile, NDSource)
    #: (:obj:`bool`) flag for nxstools installed
    NXSTOOLS = True
except ImportError:
    NXSTOOLS = False

if sys.version_info > (3,):
    unicode = str


#: (:obj:`list` <:obj:`str`>) default data names
DEFAULT_RECORD_KEYS = ['serialno', 'end_time', 'start_time',
                       'point_nb', 'timestamps', 'scan_title',
                       'filename']


class ProfileManager(object):

    """  Manages Measurement Group and Profile from Selector"""

    def __init__(self, selector, syncsnapshot=False):
        """ constructor

        :param selector: selector object
        :type selector: :class:`nxsrecconfig.Selector.Selector`
        :param syncsnapshot: preselection merges current ScanSnapshot
        :type syncsnapshot: :obj:`bool`
        """
        #: (:class:`nxsrecconfig.Selector.Selector`) configuration selector
        self.__selector = selector

        #: (:obj:`str`) macro server name
        self.__macroServerName = None
        #: (:class:`PyTango.DeviceProxy` \
        #: or :class:`nxsconfigserver.XMLConfigurator.XMLConfigurator`) \
        #:     configuration server proxy
        self.__configServer = None
        #: (:obj:`list` <:obj:`PyTango.DeviceProxy`>) pool server proxies
        self.__pools = None

        #: (:obj:`list` <:obj:`str`>) default preselectedComponents
        self.defaultPreselectedComponents = []

        #: (:obj:`list` <:obj:`str`>) client record keys
        self.clientRecordKeys = []

        #: (:obj:`list` <:obj:`str`>) timer filters
        self.timerFilters = ["*dgg*", "*/timer/*", "*/ctctrl0*"]

        #: (:obj:`bool`) mntgrp with synchronization
        self.__withsynch = True

        #: (:obj:`bool`) preselection merges current ScanSnapshot
        self.__syncsnapshot = syncsnapshot

    def __updateMacroServer(self):
        """ updatas MacroServer name
        """
        self.__macroServerName = self.__selector.getMacroServer()
        self.__withsynch = self.__hassynch()

    def __updateConfigServer(self):
        """ update configuration server device proxy
        """
        self.__configServer = self.__selector.setConfigInstance()

    def __updatePools(self):
        """ update device pool proxy list
        """
        self.__pools = self.__selector.getPools()
        self.__withsynch = self.__hassynch()

    def __hassynch(self):
        """ check if pool devices has TriggerGateList

        :returns: if pool devices has TriggerGateList
        :rtype: :obj:`bool`
        """
        if self.__pools:
            return hasattr(self.__pools[0], "TriggerGateList")
        return True

    def availableMntGrps(self):
        """ available mntgrps

        :returns: list of available measurement groups
        :rtype: :obj:`list` <:obj:`str`>
        """
        self.__updateMacroServer()
        self.__updatePools()
        mntgrps = None
        amntgrp = MSUtils.getEnv('ActiveMntGrp', self.__macroServerName)
        fpool = self.__getActivePool(amntgrp)
        if fpool:
            mntgrps = PoolUtils.getElementNames(
                [fpool], 'MeasurementGroupList')
        mntgrps = mntgrps if mntgrps else []

        try:
            if mntgrps:
                ind = mntgrps.index(amntgrp)
                mntgrps[0], mntgrps[ind] = mntgrps[ind], mntgrps[0]
        except ValueError:
            pass
        return mntgrps

    def components(self):
        """ provides selected components

        :returns: list of available selected components
        :rtype: :obj:`list` <:obj:`str`>
        """
        cps = json.loads(self.__selector["ComponentSelection"])
        ads = json.loads(self.__selector["DataSourceSelection"])
        dss = [ds for ds in ads if ads[ds]]
        acp = self.__selector.configCommand("availableComponents") or []
        res = []
        if isinstance(cps, dict):
            res = [cp for cp in cps.keys() if cps[cp]]
            for ds in dss:
                if ds in acp:
                    res.append(ds)
        return res

    def preselectedComponents(self):
        """ provides preselected components

        :returns: list of available preselected components
        :rtype: :obj:`list` <:obj:`str`>
        """
        cps = json.loads(self.__selector["ComponentPreselection"])
        if isinstance(cps, dict):
            return [cp for cp in cps.keys() if cps[cp]]
        else:
            return []

    def preselectedDataSources(self):
        """ provides preselected datasources

        :returns: list of available preselected components
        :rtype: :obj:`list` <:obj:`str`>
        """
        cps = json.loads(self.__selector["DataSourcePreselection"])
        if isinstance(cps, dict):
            return [cp for cp in cps.keys() if cps[cp]]
        else:
            return []

    def cpdescription(self, full=False):
        """ provides description of components

        :param full: if True describes all available ones are taken
                     otherwise selectect, preselected and mandatory
        :type full: :obj:`bool`
        :returns: description of required components
        :rtype: [:obj:`dict` <:obj:`str`, :obj:`dict` <:obj:`str`, \
                 :obj:`list` <(:obj:`str`, :obj:`str`, :obj:`str`, \
                      :obj:`str`, :obj:`list` <:obj:`int`>)> > > ] or \
                [{"dsname": :obj:`str`, "strategy": :obj:`str`, \
                  "dstype": :obj:`str`, "record": :obj:`str`, \
                  "nxstype": :obj:`str`, "shape": :obj:`list` <:obj:`int`> , \
          "cpname": :obj:`str`}, ...]
        """
        self.__updateConfigServer()
        describer = Describer(self.__configServer, True)
        cp = None
        if not full:
            mcp = self.__selector.configCommand("mandatoryComponents") or []
            cp = list(
                set(self.components()) | set(self.preselectedComponents()) |
                set(mcp))
            res = describer.components(cp, 'STEP', '')
        else:
            res = describer.components(cp, '', '')
        return res

    def componentDataSources(self):
        """ provides a list of Component DataSources

        :returns: list of component datasources
        :rtype: :obj:`list` <:obj:`str`>
        """
        return self.__componentDataSources(self.cpdescription())

    def __componentDataSources(self, description=None):
        """ provides a list of Component DataSources

        :param description: component description
        :type description: :obj:`bool`
        :returns: list of component datasources
        :rtype: :obj:`list` <:obj:`str`>
        """
        if description is None:
            description = self.cpdescription()

        dds = set()

        for dss in description[0].values():
            if isinstance(dss, dict):
                for ds, params in dss.items():
                    for param in params:
                        if param and len(param) > 2:
                            if param[0] == 'STEP':
                                dds.add(ds)
        return list(dds)

    def __dataSources(self, compdatasources=None):
        """ provides selected datasources

        :param componentdatasources: component datasources
        :type componentdatasources: :obj:`list` <:obj:`str`>
        :returns: list of available selected datasources
        :rtype: :obj:`list` <:obj:`str`>
        """
        if compdatasources is None:
            compdatasources = self.__componentDataSources()
        if not isinstance(compdatasources, list):
            compdatasources = []
        dss = json.loads(self.__selector["DataSourceSelection"])
        if isinstance(dss, dict):
            return [ds for ds in dss.keys()
                    if dss[ds] and ds not in compdatasources]
        else:
            return []

    def dataSources(self):
        """ provides selected datasources

        :returns: list of available selected datasources
        :rtype: :obj:`list` <:obj:`str`>
        """
        return self.__dataSources()

    def deleteProfile(self, name):
        """ deletes mntgrp

        :param name: mntgrp name
        :type name: :obj:`str`
        """
        self.__updatePools()
        for pool in self.__pools:
            mntgrps = PoolUtils.getElementNames([pool], 'MeasurementGroupList')
            if name in mntgrps:
                TangoUtils.command(
                    pool, "DeleteElement", Utils.tostr(name))
        if MSUtils.getEnv('ActiveMntGrp', self.__macroServerName) == name:
            MSUtils.usetEnv("ActiveMntGrp", self.__macroServerName)
        inst = self.__selector.setConfigInstance()
        if name in inst.AvailableSelections():
            inst.deleteSelection(name)

    def updateProfile(self, sync=False):
        """ sets active measurement group from components and
        import setting from active measurement


        :param sync: make profile and mntgrp synchronization
        :type sync: :obj:`bool`
        :returns: json dictionary with mntgrp configuration information
        :rtype: :obj:`str`
        """
        mcp = self.__selector.configCommand("mandatoryComponents") or []
        components = list(
            set(self.components()) | set(self.preselectedComponents()) |
            set(mcp))

        self.__updateConfigServer()
        describer = Describer(self.__configServer, True)
        description = describer.components(components, '', '')
        componentdatasources = self.__componentDataSources(description)
        datasources = self.__dataSources(componentdatasources)
#        conf, mntgrp
        mginfo = self.__createMntGrpConf(
            datasources, componentdatasources, description)
        conf = mginfo['configuration']
        dpmg = TangoUtils.openProxy(Utils.tostr(mginfo['device']))
        dpmg.Configuration = conf
        conf = Utils.tostr(dpmg.configuration)
        self.__selector['MntGrpConfiguration'] = conf
        mginfo['configuration'] = conf
        if sync:
            self.__setFromMntGrpConf(conf, componentdatasources)
        self.__selector.storeSelection()
        MSUtils.setEnvs(
            {'PreScanSnapshot': mginfo['snapshot'],
             'ActiveMntGrp': mginfo['alias']},
            self.__macroServerName
        )
        return conf

    def switchProfile(self, toActive=True):
        """ switchProfile to active measurement

        :param toActive: if False update the current profile
        :type toActive: :obj:`bool`
        """
        if toActive:
            ms = self.__selector.getMacroServer()
            amntgrp = MSUtils.getEnv('ActiveMntGrp', ms)
            if not toActive or amntgrp:
                self.__selector["MntGrp"] = amntgrp
        self.fetchProfile()
        jconf = self.mntGrpConfiguration()
        self.__updateConfigServer()
        if self.__setFromMntGrpConf(jconf):
            self.__selector.storeSelection()

    def mntGrpConfiguration(self):
        """ provides configuration of mntgrp

        :returns: string with mntgrp configuration
        :rtype: :obj:`str`
        """
        self.__updatePools()
        self.__updateMacroServer()
        mntGrpName = self.__selector["MntGrp"]
        fullname = Utils.tostr(PoolUtils.getMntGrpName(
            self.__pools, mntGrpName))
        dpmg = TangoUtils.openProxy(fullname) if fullname else None
        if not dpmg:
            return "{}"
        return Utils.tostr(dpmg.Configuration)

    def isMntGrpUpdated(self):
        """ check if active measurement group was changed

        :returns: True if it is different to the current setting
        :rtype: :obj:`bool`
        """
        mcp = self.__selector.configCommand("mandatoryComponents") or []
        components = list(
            set(self.components()) | set(self.preselectedComponents()) |
            set(mcp))

        self.__updateConfigServer()
        describer = Describer(self.__configServer, True)
        description = describer.components(components, '', '')
        componentdatasources = self.__componentDataSources(description)
        datasources = self.__dataSources(componentdatasources)
        mgconf = json.loads(self.mntGrpConfiguration())

        state = self.__selector.get()
        amg = MSUtils.getEnv('ActiveMntGrp', self.__macroServerName)

        mginfo = self.__createMntGrpConf(
            datasources, componentdatasources, description)
        llconf = mginfo["configuration"]

        dpmg = TangoUtils.openProxy(Utils.tostr(mginfo['device']))
        oldconf = Utils.tostr(dpmg.configuration)
        dpmg.Configuration = llconf
        llconf = Utils.tostr(dpmg.configuration)
        dpmg.Configuration = oldconf

        amg2 = MSUtils.getEnv('ActiveMntGrp', self.__macroServerName)
        if amg != amg2:
            MSUtils.setEnv(
                'ActiveMntGrp', Utils.tostr(amg), self.__macroServerName)
        state2 = self.__selector.get()
        if json.dumps(state) != json.dumps(state2):
            self.__selector.set(state)

        lsconf = json.loads(llconf)
        return Utils.compareDict(mgconf, lsconf)

    def importMntGrp(self):
        """ import setting from active measurement
        """
        self.__updateMacroServer()
        self.__updateConfigServer()
        jconf = self.mntGrpConfiguration()
        if self.__setFromMntGrpConf(jconf):
            self.__selector.storeSelection()

    def __addPreselectedComponents(self, components):
        """ add preselected components to set of given components

        :param components: new selection preselected components
        :type components: :obj:`list` <:obj:`str`>
        """
        if not self.__macroServerName:
            self.__updateMacroServer()
        snapshot = MSUtils.getEnv(
            'PreScanSnapshot', self.__macroServerName)
        tangods = [[ds[1], ds[1], ds[0]] for ds in snapshot]
        snpds = dict([(ds[1], False) for ds in snapshot])
        mydsg = {}
        self.createDataSources(tangods, mydsg)
        jpcps = json.loads(self.__selector["ComponentPreselection"])
        jpdss = json.loads(self.__selector["DataSourcePreselection"])
        predss = set(json.loads(self.__selector["PreselectingDataSources"]))
        changed = False
        for cp in components:
            if cp not in jpcps.keys():
                jpcps[cp] = False
        cps = set(self.__selector.configCommand("mandatoryComponents")
                  or []) | set(list(jpcps.keys()))

        describer = Describer(self.__configServer, True)
        description = describer.components(list(cps), '', '')
        for cp, dss in description[0].items():
            if isinstance(dss, dict):
                cpdss = set()
                fdss = set()
                for ds, params in dss.items():
                    for param in params:
                        if param and len(param) > 2:
                            if param[0] in ['INIT', 'FINAL']:
                                if param[1] == 'TANGO' or ds in predss:
                                    cpdss.add(ds)
                                    if ds in snpds.keys():
                                        fdss.add(ds)

                if fdss:
                    if not (cpdss - fdss):
                        if cp in jpcps.keys() and jpcps[cp] is False:
                            jpcps[cp] = None
                        for ds in fdss:
                            snpds[ds] = True
        for ds, val in snpds.items():
            if val is not True:
                jpdss[ds] = None
        pcps = json.dumps(jpcps)
        pdss = json.dumps(jpdss)
        if pcps != self.__selector["ComponentPreselection"]:
            self.__selector["ComponentPreselection"] = pcps
            changed = True
        if pdss != self.__selector["DataSourcePreselection"]:
            self.__selector["DataSourcePreselection"] = pdss
            changed = True
        # print(changed)
        return changed

    def fetchProfile(self):
        """ fetches the profile configuration
        """
        self.__updateConfigServer()
        if self.__selector.fetchSelection() is False:
            avmg = self.availableMntGrps()
            if self.__selector["MntGrp"] in avmg:
                self.__selector.deselect()
                self.importMntGrp()
                if self.__syncsnapshot:
                    # print("FETCH")
                    self.__addPreselectedComponents(
                        self.defaultPreselectedComponents)
                self.__selector.resetPreselectedComponents(
                    self.defaultPreselectedComponents)
                self.__selector.preselect()
        elif self.__syncsnapshot:
            # print("FETCH 2")
            changed = self.__addPreselectedComponents(
                self.defaultPreselectedComponents)
            if changed:
                self.__selector.preselect()

    def __createMntGrpConf(self, datasources,
                           componentdatasources, description):
        """ sets active measurement group from components

        :param components:  component list
        :type components: :obj:`list` <:obj:`int`>
        :param datasources: datasource list
        :type datasources: :obj:`list` <:obj:`int`>
        :param componentdatasources: component datasource list
        :type componentdatasources: :obj:`list` <:obj:`int`>
        :param description: component description
        :type description: [:obj:`dict` <:obj:`str`, :obj:`dict` <:obj:`str`, \
            :obj:`list` <(:obj:`str`, :obj:`str`, :obj:`str`, \
            :obj:`str`, :obj:`list` <:obj:`int`>)> > > ]
        :returns: dictionary of MntGrp configuration and MntGrp Device name
        :rtype: {"alias": :obj:`str` , "device": :obj:`str` , \
            "configuration": :obj:`str` ,  \
            "snapshot": :obj:`list` <(:obj:`str` , :obj:`str` )>}
        """
        self.__updatePools()
        self.__updateMacroServer()
        cnf = {}
        cnf['controllers'] = {}
        cnf['description'] = "Measurement Group"
        cnf['label'] = ""

        dontdisplay = set(json.loads(self.__selector["UnplottedComponents"]))

        ltimers = set()
        timer = self.__prepareTimers(cnf, ltimers)

        aliases, snapshot = self.__fetchChannels(
            datasources, componentdatasources,
            dontdisplay, set(ltimers) | set([timer]), description)
        mfullname = self.__prepareMntGrp(cnf, timer)

        index = 0
        fullnames = PoolUtils.getFullDeviceNames(self.__pools, aliases)
        sources = PoolUtils.getChannelSources(self.__pools, aliases)
        props = json.loads(self.__selector["ChannelProperties"])
        synchronizer = props["synchronizer"] \
            if "synchronizer" in props.keys() else {}
        synchronization = props["synchronization"] \
            if "synchronization" in props.keys() else {}
        tchannels = set(PoolUtils.getElementNames(
            self.__pools, 'ExpChannelList',
            ['CTExpChannel', 'OneDExpChannel', 'TwoDExpChannel']))
        tchannels = tchannels | ltimers

        for al in aliases:
            index = self.__addDevice(
                al, dontdisplay, cnf,
                al if al in tchannels else timer, index, fullnames, sources,
                synchronizer[al] if al in synchronizer.keys() else None,
                int(synchronization[al]) if al in synchronization.keys()
                else None
            )
        conf = json.dumps(cnf)

        mginfo = {
            "alias": Utils.tostr(cnf['label']),
            "device": mfullname,
            "configuration": Utils.tostr(conf),
            "snapshot": snapshot
        }
        return mginfo

    def __setFromMntGrpConf(self, jconf, compdatasources=None):
        """ import setting from active measurement

        :param jconf: json with mntgrp configuration
        :type jconf: :obj:`str`
        :param componentdatasources: component datasources
        :type componentdatasources: :obj:`list` <:obj:`int`>
        :returns: if profile has been changed
        :rtype: :obj:`bool`
        """
        self.__updatePools()
        conf = json.loads(jconf)
        otimers = None
        timers = {}

        dsg = json.loads(self.__selector["DataSourceSelection"])
        hel = set(json.loads(self.__selector["UnplottedComponents"]))
        props = json.loads(self.__selector["ChannelProperties"])
        # synchronizer = props["synchronizer"] \
        #     if "synchronizer" in props.keys() else {}
        synchronizer = {}
        # synchronization = props["synchronization"] \
        #     if "synchronization" in props.keys() else {}
        synchronization = {}
        self.__clearChannels(dsg, hel, compdatasources)

        # fill in dsg, timers hel
        if "timer" in conf.keys() and "controllers" in conf.keys():
            avtimers = PoolUtils.getTimers(self.__pools, self.timerFilters)
            tangods = self.__readChannels(
                conf, timers, dsg, hel, synchronizer, synchronization)
            self.__readTangoChannels(
                conf, tangods, dsg, hel, synchronizer, synchronization)
            otimers = self.__reorderTimers(conf, timers, dsg, hel, avtimers)

        props["synchronizer"] = synchronizer
        props["synchronization"] = synchronization

        changed = False
        jdsg = json.dumps(dsg)
        if self.__selector["DataSourceSelection"] != jdsg:
            self.__selector["DataSourceSelection"] = jdsg
            changed = True

        jprops = json.dumps(props)
        if self.__selector["ChannelProperties"] != jprops:
            self.__selector["ChannelProperties"] = jprops
            changed = True

        if set(json.loads(self.__selector["UnplottedComponents"])) != hel:
            self.__selector["UnplottedComponents"] = json.dumps(list(hel))
            changed = True

        if otimers is not None:
            jtimers = json.dumps(otimers)
            if self.__selector["Timer"] != jtimers:
                self.__selector["Timer"] = jtimers
                changed = True
        if self.__selector["MntGrp"] not in \
           self.__configServer.availableSelections():
            changed = True
        return changed

    def __clearChannels(self, dsg, hel, compdatasources=None):
        """ clears profile channels

        :param dsg: datasource selection dictionary
        :type dsg: :obj:`dict` <:obj:`str`, :obj:`bool` or `None`>
        :param hel: list of hidden elements
        :type hel: :obj:`list` <:obj:`str`>
        :param componentdatasources: component datasources
        :type componentdatasources: :obj:`list` <:obj:`int`>
        """
        if compdatasources is None:
            compdatasources = self.componentDataSources()
        describer = Describer(self.__configServer, True)
        ads = TangoUtils.command(self.__configServer, "availableDataSources")
        dsres = describer.dataSources(ads, 'TANGO')[0]
        tangods = [Utils.tostr(dsr.name) for dsr in dsres.values()
                   if dsr.name not in compdatasources]
        channels = set(
            PoolUtils.getElementNames(self.__pools, 'ExpChannelList') or [])
        channels.update(set(tangods))

        for ch in channels:
            if ch in dsg.keys():
                dsg[ch] = False
            if ch in hel:
                hel.remove(ch)

    @classmethod
    def __readChannels(cls, conf, timers, dsg, hel, synchronizer,
                       synchronization):
        """ reads channels from mntgrp configutation

        :param conf: mntgrp configuration
        :type jconf: :obj:`str`
        :param timers: timer dictionary
        :type timers: :obj:`dict` <:obj:`str`, :obj:`str`>
        :param dsg: datasource selection dictionary
        :type dsg: :obj:`dict` <:obj:`str`, :obj:`bool` or `None`>
        :param hel: list of hidden elements
        :type hel: :obj:`list` <:obj:`str`>
        :param synchronizer: channel synchronizer, default = 'software'
        :type synchronizer: :obj:`dict` <:obj:`str`, :obj:`str`>
        :param synchronization: channel synchronization,
                i.e. Trigger=0, Gate=1, Start=2
        :type synchronization: :obj:`dict` <:obj:`str`, :obj:`int`>
        :returns: tango datasources list with elements (name, label, source)
        :rtype: :obj:`list` < [:obj:`str` , :obj:`str` , :obj:`str` ] >
        """
        tangods = []
        timers[conf["timer"]] = ''
        for ctrlname, ctrl in conf["controllers"].items():
            if 'units' in ctrl.keys() and \
                    '0' in ctrl['units'].keys():
                uctrl = ctrl['units']['0']
            else:
                uctrl = ctrl
            if 'timer' in uctrl.keys():
                timers[uctrl['timer']] = ''
            if 'channels' in uctrl.keys():
                for ch in uctrl['channels'].values():
                    if ctrlname == "__tango__" or \
                      ('_controller_name' in ch.keys() and
                       ch['_controller_name'] == '__tango__'):
                        tangods.append(
                            [ch['name'], ch['label'], ch["source"]])
                    else:
                        dsg[ch['name']] = True
                        if not bool(ch['plot_type']):
                            hel.add(ch['name'])
                        elif ch['name'] in hel:
                            hel.remove(ch['name'])
                        if 'synchronizer' in ctrl \
                           and ctrl['synchronizer'].lower() != 'software':
                            synchronizer[ch['name']] = ctrl['synchronizer']
                        if 'synchronization' in ctrl \
                           and ctrl['synchronization'] != 0:
                            synchronization[ch['name']] = \
                                ctrl['synchronization']
        return tangods

    def __readTangoChannels(self, conf, tangods, dsg, hel, synchronizer,
                            synchronization):
        """ reads Tango channels from mntgrp configutation

        :param conf: mntgrp configuration
        :type conf: :obj:`dict` <:obj:`str`, `any`>
        :param tangods: tango datasources list
                        with elements (name, label, source)
        :type tangods: :obj:`list` < [:obj:`str` , :obj:`str` , :obj:`str` ] >
        :param dsg: datasource selection dictionary
        :type dsg: :obj:`dict` <:obj:`str`, :obj:`bool` or `None`>
        :param synchronizer: channel synchronizer, default = 'software'
        :type synchronizer: :obj:`dict` <:obj:`str`, :obj:`str`>
        :param synchronization: channel synchronization, i.e. Trigger=0, Gate=1
        :type synchronization: :obj:`dict` <:obj:`str`, :obj:`int`>
        :param hel: list of hidden elements
        :type hel: :obj:`list` <:obj:`str`>
        """
        if tangods and NXSTOOLS:
            jds = self.createDataSources(tangods, dsg)
            for ctrlname, ctrl in conf["controllers"].items():
                if 'units' in ctrl.keys() and \
                        '0' in ctrl['units'].keys():
                    uctrl = ctrl['units']['0']
                else:
                    uctrl = ctrl
                if 'channels' in uctrl.keys():
                    for ch in uctrl['channels'].values():
                        if ctrlname == "__tango__" or \
                          ('_controller_name' in ch.keys() and
                           ch['_controller_name'] == '__tango__'):
                            if ch["source"] in jds.keys():
                                name = jds[ch["source"]]
                                dsg[name] = True
                                if not bool(ch['plot_type']):
                                    hel.add(name)
                                elif ch['name'] in hel:
                                    hel.remove(name)
                                if 'synchronizer' in ctrl and \
                                   ctrl['synchronizer'].lower() != 'software':
                                    synchronizer[name] = \
                                        ctrl['synchronizer']
                                if 'synchronization' in ctrl and \
                                   ctrl['synchronization'] != 0:
                                    synchronization[name] = \
                                        ctrl['synchronization']

    def __reorderTimers(self, conf, timers, dsg, hel, avtimers=None):
        """ reads timer aliases and reoder it according to mntgrp

        :param conf: mntgrp configuration
        :type conf: :obj:`dict` <:obj:`str`, `any`>
        :param timers: timer device name list
        :type timers: :obj:`list` <:obj:`str`>
        :param dsg: datasource selection dictionary
        :type dsg: :obj:`dict` <:obj:`str`, :obj:`bool` or `None`>
        :param hel: list of hidden elements
        :type hel: :obj:`list` <:obj:`str`>
        :param avtimers: available timers
        :type avtimers :obj:`list` <:obj:`str`>
        :returns: timer alias list
        :rtype: :obj:`list` <:obj:`str`>
        """
        dtimers = PoolUtils.getAliases(self.__pools, timers)
        avtimers = avtimers or []
        otimers = [tm for tm in dtimers.values() if tm in avtimers]
        if dtimers[conf["timer"]] in otimers:
            otimers.remove(dtimers[conf["timer"]])
            otimers.insert(0, dtimers[conf["timer"]])
        elif not otimers:
            otimers.insert(0, dtimers[conf["timer"]])

        tms = json.loads(self.__selector["Timer"])
        tms.extend(otimers)

        for tm in tms:
            if tm in hel:
                if tm in dsg.keys():
                    dsg[tm] = False
                    hel.remove(tm)
        return otimers

    def __checkClientRecords(self, datasources, description):
        """ checks client records

        :param datasources: datasource list
        :type datasources: :obj:`list` <:obj:`str`>
        :param description: component description
        :type description: [:obj:`dict` <:obj:`str`, :obj:`dict` <:obj:`str`, \
            :obj:`list` <(:obj:`str`, :obj:`str`, :obj:`str`, \
            :obj:`str`, :obj:`list` <:obj:`int`>)> > > ]
        """

        describer = Describer(self.__configServer, True)
        frecords = PoolUtils.getFullDeviceNames(self.__pools)
        dsres = describer.dataSources(
            set(datasources) - set(frecords.keys()), 'CLIENT')[0]
        records = [Utils.tostr(dsr.record) for dsr in dsres.values()]

        for grp in description:
            for dss in grp.values():
                for dsrs in dss.values():
                    for dsr in dsrs:
                        if dsr[1] == 'CLIENT':
                            records.append(Utils.tostr(dsr[2]))

        urecords = list(json.loads(self.__selector["UserData"]).keys())
        precords = list(frecords.values())
        missing = sorted(set(records)
                         - set(DEFAULT_RECORD_KEYS)
                         - set(self.clientRecordKeys)
                         - set(urecords)
                         - set(precords))
        if missing:
            raise Exception(
                "User Data not defined %s" % Utils.tostr(missing))

    def __getActivePool(self, mntgrp=None):
        """ get the active pool

        :param mntgrp: current mntgrp
        :type mntgrp: :obj:`str`
        :returns: active pool proxy
        :rtype: :obj:`PyTango.DeviceProxy`:
        """
        apool = []
        lpool = [None, 0]
        fpool = None
        for pool in self.__pools:
            if not fpool:
                fpool = pool
            mntgrps = PoolUtils.getElementNames([pool], 'MeasurementGroupList')
            if mntgrp in mntgrps:
                if not apool:
                    fpool = pool
                apool.append(pool)
            if lpool[1] < len(mntgrps):
                lpool = [pool, len(mntgrps)]

        if fpool is None:
            fpool = lpool[0]
        return fpool

    def __createMntGrpDevice(self, mntGrpName, timer):
        """ creates mntgrp devices

        :param mntgrpName: measurement group name
        :type mntgrpName: :obj:`str`
        :param timer: master timer name
        :type time: :obj:`str`
        :returns: measurement group full name
        :rtype: :obj:`str`
        """
        amntgrp = MSUtils.getEnv('ActiveMntGrp', self.__macroServerName)
        apool = self.__getActivePool(amntgrp)
        if apool:
            try:
                TangoUtils.command(apool, "CreateMeasurementGroup",
                                   [mntGrpName, timer])
            except PyTango.CommunicationFailed as cf:
                if len(cf.args) >= 2 and \
                   cf.args[1].reason == "API_DeviceTimedOut":
                    TangoUtils.wait(apool)
                else:
                    raise
            mfullname = Utils.tostr(PoolUtils.getMntGrpName(
                self.__pools, mntGrpName))
        return mfullname

    def __prepareTimers(self, cnf, ltimers):
        """ prepares timers

        :param cnf: mntgrp configuration
        :type cnf: :obj:`dict` <:obj:`str`, `any`>
        :param ltimers: slave timer list
        :type ltimers: :obj:`list` <:obj:`str`>
        :returns: master timer
        :rtype: :obj:`str`
        """
        mtimers = json.loads(self.__selector["Timer"])
        #   avtimers = PoolUtils.getTimers(self.__pools, self.timerFilters)
        #   mtimers = mtimers or []
        #   mtimers = [tm for tm in mtimers if tm in avtimers]

        timer = mtimers[0] if mtimers else ''
        if not timer:
            raise Exception(
                "Timer or Monitor not defined")
        fullname = PoolUtils.getFullDeviceNames(
            self.__pools, [timer])[timer]
        if not fullname:
            raise Exception(
                "Timer or Monitor cannot be found amount the servers")
        cnf['monitor'] = fullname
        cnf['timer'] = fullname
        if len(mtimers) > 1:
            ltimers.clear()
            ltimers.update(set(mtimers[1:]))
            if timer in ltimers:
                ltimers.remove(timer)
        return timer

    def __fetchChannels(self, datasources, componentdatasources,
                        dontdisplay, timers, description):
        """ fetches component channels from config server
            and preselect datasources

        :param datasources: datasource list
        :type datasources: :obj:`list` <:obj:`int`>
        :param componentdatasources: component datasources
        :param componentdatasources: component datasource list
        :param dontdisplay: hidden channel list
        :type dontdisplay: :obj:`list` <:obj:`str`>
        :param timers: timers list
        :type timers: :obj:`list` <:obj:`str`>
        :param description: component description
        :type description: [:obj:`dict` <:obj:`str`, :obj:`dict` <:obj:`str`, \
            :obj:`list` <(:obj:`str`, :obj:`str`, :obj:`str`, \
            :obj:`str`, :obj:`list` <:obj:`int`>)> > > ]
        :returns:  (ordered pool channels, snapshot tuple list)
        :rtype: (:obj:`list` <:obj:`str`> ,  \
            :obj:`list` <(:obj:`str` , :obj:`str` )>)
        """
        aliases = []
        initsources = {}

        self.__checkClientRecords(datasources, description)
        if isinstance(datasources, list):
            aliases = list(datasources)
        pchannels = json.loads(self.__selector["OrderedChannels"])
        dsg = json.loads(self.__selector["DataSourceSelection"])
        aliases.extend(
            list(set(pchannels) & set(componentdatasources)))

        describer = Describer(self.__configServer, True)
        for grp in description:
            for cp, dss in grp.items():
                ndcp = cp in dontdisplay
                for ds, params in dss.items():
                    for param in params:
                        if param and len(param) > 2:
                            if param[0] == 'STEP' \
                               and param[1] in ['TANGO', 'CLIENT']:
                                aliases.append(Utils.tostr(ds))
                                dsg[Utils.tostr(ds)] = True
                                if not ndcp and Utils.tostr(ds) in dontdisplay:
                                    dontdisplay.remove(Utils.tostr(ds))
                            elif param[0] in ['FINAL', 'INIT'] and \
                                    param[1] in ['TANGO']:
                                initsources[Utils.tostr(ds)] = \
                                    TangoUtils.getFullAttrName(
                                        param[2], self.__withsynch)

        devices = self.preselectedDataSources()
        if devices:
            sds = describer.dataSources(devices)
            if sds:
                for ds in sds[0].values():
                    if ds.dstype == 'TANGO':
                        initsources[ds.name] = \
                            TangoUtils.getFullAttrName(
                                ds.record, self.__withsynch)
        snapshot = [(initsources[dsname], dsname)
                    for dsname in sorted(initsources.keys())
                    if ('@' not in initsources[dsname] and
                        '()' not in initsources[dsname])]

        for tm in timers:
            if tm in dontdisplay:
                if tm in dsg.keys():
                    dsg[Utils.tostr(tm)] = False

        self.__selector["DataSourceSelection"] = json.dumps(dsg)
        self.__selector["UnplottedComponents"] = json.dumps(
            list(dontdisplay))
        aliases = list(set(aliases))

        for tm in timers:
            if tm not in aliases:
                aliases.append(tm)
                dontdisplay.add(tm)

        pchannels = [ch for ch in pchannels if ch in aliases]
        aliases = sorted(list(set(aliases) - set(pchannels)))
        pchannels.extend(aliases)
        return pchannels, snapshot

    def __prepareMntGrp(self, cnf, timer):
        """ creates mntgrp if does not exists

        :param cnf: mntgrp configuration
        :type cnf: :obj:`dict` <:obj:`str`, `any`>
        :param timer: master timer
        :type timer: :obj:`str`
        :returns: full mntgrp name
        :rtype: :obj:`str`
        """
        mntGrpName = self.__selector["MntGrp"]
        mfullname = Utils.tostr(PoolUtils.getMntGrpName(
            self.__pools, mntGrpName))

        if not mfullname:
            mfullname = self.__createMntGrpDevice(mntGrpName, timer)

        cnf['label'] = mntGrpName
        return mfullname

    @classmethod
    def __findSources(cls, tangods, extangods, exsource):
        """ finds sources of tango datasources

        :param tangods: tango datasources list
                        with elements (name, label, source)
        :type tangods: :obj:`list` < [:obj:`str` , :obj:`str` , :obj:`str` ] >
        :param extangods: tango datasources list
                        with elements
                        (ds name, input source,
                         source without 'tango://',
                         sources with host)
        :type extangods: :obj:`list` < [:obj:`str` , :obj:`str` , \
               :obj:`str` ,:obj:`str` ,:obj:`str` ] >
        """
        for name, _, initsource in tangods:
            source = initsource if initsource[:8] != 'tango://' \
                else initsource[8:]
            msource = None
            spsource = source.split("/")
            if len(spsource) > 3 and ":" in spsource[0]:
                host, port = spsource[0].split(":")
                mhost = host.split(".")[0]
                msource = "/".join(spsource[1:])
                if mhost != host:
                    msource = "%s:%s/%s" % (mhost, port, msource)
                device = "/".join(spsource[1:-1])
                attribute = spsource[-1]
                exsource[source] = [host, port, device, attribute]
            extangods.append(
                [name, initsource, source, msource])

    @classmethod
    def __addKnownSources(cls, extangods, sds, existing=None):
        """ adds known sources

        :param extangods: tango datasources list
                        with elements
                        (ds name, input source,
                         source without 'tango://',
                         sources with host)
        :type extangods: :obj:`list` < [:obj:`str` , :obj:`str` , \
               :obj:`str` ,:obj:`str` ,:obj:`str` ] >
        :param sds: list of json datasource descriptions
        :type sds: :obj:`list` <:obj:`str`>
        :param existing: list of existing datasources
        :type existing: :obj:`list` <:obj:`str`>
        :returns: dictionary with known sources
        :rtype: :obj:`dict` <:obj:`str`, :obj:`str`>
        """
        jds = {}
        found = set()
        if not existing:
            existing = []
        for ds in sds:
            js = json.loads(ds)
            if js["dsname"] in existing:
                for _, initsource, source, msource in extangods:
                    if source == js["record"]:
                        jds[initsource] = js["dsname"]
                        found.add(Utils.tostr(js["record"]))
                        break
                    elif msource == js["record"]:
                        jds[initsource] = js["dsname"]
                        found.add(Utils.tostr(js["record"]))
                        break
        for ds in sds:
            js = json.loads(ds)
            if js["dsname"] not in existing and \
                    js["record"] not in found:
                for _, initsource, source, msource in extangods:
                    if source == js["record"]:
                        jds[initsource] = js["dsname"]
                        found.add(Utils.tostr(js["dsname"]))
                        break
                    elif msource == js["record"]:
                        jds[initsource] = js["dsname"]
                        found.add(Utils.tostr(js["dsname"]))
                        break
        return jds

    @classmethod
    def __createXMLSource(cls, name, source, exsource):
        """ creates datasource XML for sources

        :param name: datasource name
        :type name: :obj:`str`
        :param source: datasource source string
        :type source: :obj:`str`
        :param exsource: dictioanry of source attributes \
           with value (host, port, device, attribute)
        :type exsource: :obj:`dict` <:obj:`str` , \
         (:obj:`str` , :obj:`str` , :obj:`str` , :obj:`str` )>
        :returns: xml string
        :rtype :obj:`str`
        """
        host, port, device, attribute = exsource[source]
        df = XMLFile("ds.xml")
        sr = NDSource(df)
        sr.initTango(
            name, device, "attribute", attribute, host, port,
            group='__CLIENT__')
        return df.prettyPrint()

    def __createUnknownSources(self, extangods, exsource, ads, jds):
        """ creates datasource XMLs for unknown datasources

        :param extangods: tango datasources list
                        with elements
                        (ds name, input source,
                         source without 'tango://',
                         sources with host)
        :type extangods: :obj:`list` < [:obj:`str` , :obj:`str` , \
               :obj:`str` ,:obj:`str` ,:obj:`str` ] >
        :param exsource: dictioanry of source attributes \
         with value (host, port, device, attribute)
        :type exsource: :obj:`dict` <:obj:`str` , \
         (:obj:`str` , :obj:`str` , :obj:`str` , :obj:`str` )>
        :param ads: availaible datasources
        :type ads: :obj:`list` <:obj:`str`>
        :param jds: dictionary with of source alias names
        :type jds: :obj:`dict` <:obj:`str` ,  :obj:`str` >
        """
        for name, initsource, source, _ in extangods:
            if initsource not in jds:
                jds[initsource] = None
                i = 0
                nname = name
                while nname in ads:
                    i += 1
                    nname = "%s_%s" % (name, i)
                name = nname
                if source in exsource:
                    xml = self.__createXMLSource(name, source, exsource)
                    self.__configServer.xmlstring = Utils.tostr(xml)
                    TangoUtils.command(self.__configServer, "storeDataSource",
                                       Utils.tostr(name))
                    jds[initsource] = name

    def createDataSources(self, tangods, dsg=None):
        """adds known and creates unknown datasources

        :param tangods: tango datasources list
                        with elements (name, label, source)
        :type tangods: :obj:`list` < [:obj:`str` , :obj:`str` , :obj:`str` ] >
        :param dsg: datasource selection dictionary
        :type dsg: :obj:`dict` <:obj:`str`, :obj:`bool` or `None`>
        :returns: dictionary with of source alias names
        :rtype:  :obj:`dict` <:obj:`str` ,  :obj:`str` >
        """
        extangods = []
        exsource = {}
        dsg = dsg or {}

        ads = TangoUtils.command(self.__configServer, "availableDataSources")
        if not ads:
            ads = []
        describer = Describer(self.__configServer)
        sds = describer.dataSources(ads)
        self.__findSources(tangods, extangods, exsource)
        jds = self.__addKnownSources(extangods, sds, list(dsg.keys()))
        self.__createUnknownSources(extangods, exsource, ads, jds)
        return jds

    def __addDevice(self, device, dontdisplay, cnf,
                    timer, index, fullnames=None, sources=None,
                    synchronizer=None, synchronization=None):
        """ adds device into configuration dictionary

        :param device: device alias
        :type device: :obj:`str`
        :param dontdisplay: list of devices component for display
        :type dontdisplay: :obj:`list` <:obj:`str`>
        :param cnf: mntgrp configuration dictionary
        :type cnf: :obj:`dict` <:obj:`str`, `any`>
        :param timer: device timer
        :type timer: :obj:`str`
        :param index: device index
        :type index: :obj:`int`
        :param fullnames: dictionary with full names
        :type fullnames: :obj:`dict` <:obj:`str`, :obj:`str`>
        :param sources: dictionary with source names
        :type sources: :obj:`dict` <:obj:`str`, :obj:`str`>
        :param synchronizer: name of trigger or gate device
        :type synchronizer: :obj:`str`
        :param synchronization: trigger:0 or gate:1
        :type synchronization: :obj:`int`
        :returns: next device index
        :rtype: :obj:`int`
        """
        if not fullnames:
            fullnames = PoolUtils.getFullDeviceNames(
                self.__pools, [device, timer])

        ctrls = PoolUtils.getDeviceControllers(self.__pools, [device])
        ctrl = ctrls[device] if ctrls and device in ctrls.keys() else ""
        timers = PoolUtils.getFullDeviceNames(self.__pools, [timer])
        fulltimer = fullnames[timer] \
            if timers and timer in fullnames.keys() else ""
        if ctrl:
            self.__addController(cnf, ctrl, fulltimer)
            fullname = fullnames[device] \
                if fullnames and device in fullnames.keys() else ""
            source = sources[device] \
                if sources and device in sources.keys() else ""
            index = self.__addChannel(cnf, ctrl, device, fullname,
                                      dontdisplay, index, source)
        else:
            describer = Describer(self.__configServer)
            sds = describer.dataSources([device])
            if sds:
                js = json.loads(sds[0])
                if js["dstype"] == 'TANGO':
                    ctrl = "__tango__"
                    self.__addController(cnf, ctrl, fulltimer)
                    index = self.__addTangoChannel(
                        cnf, ctrl, device, Utils.tostr(js["record"]),
                        dontdisplay, index)
        synchronization = synchronization or None
        synchronizer = synchronizer or None
        if synchronization is not None:
            cnf['controllers'][ctrl][u'synchronization'] = \
                int(synchronization)
        if synchronizer is not None:
            cnf['controllers'][ctrl][u'synchronizer'] = synchronizer
        return index

    def __addController(self, cnf, ctrl, fulltimer):
        """ adds controller into mntgrp configuration dictionary

        :param cnf: mntgrp configuration dictionary
        :type cnf: :obj:`dict` <:obj:`str`, `any`>
        :param ctrl: controller device name
        :type ctrl: :obj:`str`
        :param fulltimer: full timer name
        :rtype: :obj:`str`
        """
        if not self.__withsynch:
            self.__addController1(cnf, ctrl, fulltimer)
        else:
            self.__addController2(cnf, ctrl, fulltimer)

    @classmethod
    def __addController1(cls, cnf, ctrl, fulltimer):
        """ adds controller into mntgrp configuration dictionary

        :param cnf: mntgrp configuration dictionary
        :type cnf: :obj:`dict` <:obj:`str`, `any`>
        :param ctrl: controller device name
        :type ctrl: :obj:`str`
        :param fulltimer: full timer name
        :rtype: :obj:`str`
        """
        if 'controllers' not in cnf.keys():
            cnf['controllers'] = {}
        if ctrl not in cnf['controllers'].keys():
            cnf['controllers'][ctrl] = {}
            cnf['controllers'][ctrl]['units'] = {}
            cnf['controllers'][ctrl]['units']['0'] = {}
            cnf['controllers'][ctrl]['units']['0'][
                u'channels'] = {}
            cnf['controllers'][ctrl]['units']['0']['id'] = 0
            cnf['controllers'][ctrl]['units']['0'][
                u'monitor'] = fulltimer
            cnf['controllers'][ctrl]['units']['0'][
                u'timer'] = fulltimer
            cnf['controllers'][ctrl]['units']['0'][
                u'trigger_type'] = 0

    @classmethod
    def __addController2(cls, cnf, ctrl, fulltimer):
        """ adds controller into mntgrp configuration dictionary

        :param cnf: mntgrp configuration dictionary
        :type cnf: :obj:`dict` <:obj:`str`, `any`>
        :param ctrl: controller device name
        :type ctrl: :obj:`str`
        :param fulltimer: full timer name
        :rtype: :obj:`str`
        """
        if 'controllers' not in cnf.keys():
            cnf['controllers'] = {}
        if ctrl not in cnf['controllers'].keys():
            cnf['controllers'][ctrl] = {}
            cnf['controllers'][ctrl][u'channels'] = {}
            cnf['controllers'][ctrl][u'monitor'] = fulltimer
            cnf['controllers'][ctrl][u'timer'] = fulltimer
            # 0 old trigger_type
            cnf['controllers'][ctrl][u'synchronization'] = 0
            cnf['controllers'][ctrl][u'synchronizer'] = 'software'

    @classmethod
    def __addChannel(cls, cnf, ctrl, device, fullname, dontdisplay, index,
                     source):
        """ adds channel into mngrp configuration dictionary

        :param cnf: mntgrp configuration dictionary
        :type cnf: :obj:`dict` <:obj:`str`, `any`>
        :param ctrl: controller device name
        :type ctrl: :obj:`str`
        :param device: alias device name
        :type device: :obj:`str`
        :param fullname: full device name
        :type fullname: :obj:`str`
        :param dontdisplay: hidden channels
        :type dontdisplay: :obj:`list` <:obj:`str`>
        :param index: channel index
        :type index: :obj:`int`
        :param source: channel source
        :type source: :obj:`str`
        :returns: next index
        :rtype: :obj:`int`
        """
        if 'units' in cnf['controllers'][ctrl].keys():
            ctrlChannels = cnf['controllers'][ctrl]['units']['0'][
                u'channels']
        else:
            ctrlChannels = cnf['controllers'][ctrl][u'channels']
        if fullname not in ctrlChannels.keys():
            dsource = source.encode() or PoolUtils.getSource(fullname)
            if not dsource:
                dsource = '%s/%s' % (fullname.encode(), 'Value')
            shp, dt, ut = TangoUtils.getShapeTypeUnit(dsource)
            dct = {}
            dct['_controller_name'] = Utils.tostr(ctrl)
            dct['_unit_id'] = u'0'
            dct['conditioning'] = u''
            dct['data_type'] = dt
            dct['data_units'] = ut
            dct['enabled'] = True
            dct['full_name'] = fullname
            dct['index'] = index
            index += 1
            dct['instrument'] = None
            dct['label'] = Utils.tostr(device)
            dct['name'] = Utils.tostr(device)
            dct['ndim'] = 0
            dct['nexus_path'] = u''
            dct['normalization'] = 0
            dct['output'] = True
            dct['shape'] = shp

            if device in dontdisplay:
                dct['plot_axes'] = []
                dct['plot_type'] = 0
            elif dct['shape'] and len(dct['shape']) == 1:
                dct['plot_axes'] = ['<idx>']
                dct['plot_type'] = 1
            elif dct['shape'] and len(dct['shape']) == 2:
                dct['plot_axes'] = ['<idx>', '<idx>']
                dct['plot_type'] = 2
            else:
                dct['plot_axes'] = ['<mov>']
                dct['plot_type'] = 1

            dct['source'] = Utils.tostr(dsource)
            ctrlChannels[fullname] = dct

        return index

    @classmethod
    def __addTangoChannel(cls, cnf, ctrl, device, record, dontdisplay, index):
        """ adds tango channel into mntgrp configuration dictionary

        :param cnf: mntgrp configuration dictionary
        :type cnf: :obj:`dict` <:obj:`str`, `any`>
        :param ctrl: controller device name
        :type ctrl: :obj:`str`
        :param device: alias device name
        :type device: :obj:`str`
        :param record: tango channel sources
        :type record: :obj:`str`
        :param dontdisplay: hidden channels
        :type dontdisplay: :obj:`list` <:obj:`str`>
        :param index: channel index
        :type index: :obj:`int`
        :returns: next index
        :rtype: :obj:`int`
        """

        if 'units' in cnf['controllers'][ctrl].keys():
            ctrlChannels = cnf['controllers'][ctrl]['units']['0'][
                u'channels']
        else:
            ctrlChannels = cnf['controllers'][ctrl][u'channels']
        fullname = "tango://%s" % record
        srecord = record.split("/")
        if srecord and len(srecord) > 1 and ":" in srecord[0]:
            label = "/".join(srecord[1:])
        else:
            label = record
        if fullname not in ctrlChannels.keys():
            source = record
            shp, dt, ut = TangoUtils.getShapeTypeUnit(source)
            dct = {}
            dct['_controller_name'] = Utils.tostr(ctrl)
            dct['_unit_id'] = u'0'
            dct['conditioning'] = u''
            dct['data_type'] = dt
            dct['data_units'] = ut
            dct['enabled'] = True
            dct['full_name'] = fullname
            dct['index'] = index
            index += 1
            dct['instrument'] = None
            dct['label'] = Utils.tostr(label)
            dct['name'] = Utils.tostr(device)
            dct['ndim'] = 0
            dct['nexus_path'] = u''
            dct['normalization'] = 0
            dct['output'] = True
            dct['shape'] = shp

            if device in dontdisplay:
                dct['plot_axes'] = []
                dct['plot_type'] = 0
            elif dct['shape'] and len(dct['shape']) == 1:
                dct['plot_axes'] = ['<idx>']
                dct['plot_type'] = 1
            elif dct['shape'] and len(dct['shape']) == 2:
                dct['plot_axes'] = ['<idx>', '<idx>']
                dct['plot_type'] = 2
            else:
                dct['plot_axes'] = ['<mov>']
                dct['plot_type'] = 1

            dct['source'] = Utils.tostr(source)
            ctrlChannels[fullname] = dct

        return index
