#!/usr/bin/env python
#   This file is part of nxsrecconfig - NeXus Sardana Recorder Settings
#
#    Copyright (C) 2014 DESY, Jan Kotanski <jkotan@mail.desy.de>
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
## \file MntGrpTools.py
# tango utilities

"""  MntGrp Tools """

import json

from .Utils import Utils
from .Describer import Describer

try:
    from nxstools.nxsxml import (XMLFile, NDSource)
    NXSTOOLS = True
except:
    NXSTOOLS = False


## MntGrp Tools
class MntGrpTools(object):
    """  MntGrp Tools """
    def __init__(self, selection, pfun):
        ## configuration selection
        self.__selection = selection
        ## parent functions
        self.__pfun = pfun
        ## default mntgrp
        self.__defaultmntgrp = 'nxsmntgrp'

        ## Record names set by sardana
        self.recorder_names = ['serialno', 'end_time', 'start_time',
                               'point_nb', 'timestamps', 'scan_title']

    ## deletes mntgrp
    # \param name mntgrp name
    def deleteMntGrp(self, name):
        pool = None
        ms = self.__pfun.getMacroServer()
        msp = Utils.openProxy(ms)
        pn = msp.get_property("PoolNames")["PoolNames"]
        fpool = None
        for pl in pn:
            pool = Utils.openProxy(pl)
            if not fpool:
                fpool = pool
        if fpool:
            fpool.DeleteElement(str(name))

    ## set active measurement group from components
    def createMntGrpConfiguration(self, pools):
#        pools = self.__getPools()
        cnf = {}
        cnf['controllers'] = {}
        cnf['description'] = "Measurement Group"
        cnf['label'] = ""

        dontdisplay = set(json.loads(self.__selection["HiddenElements"]))

        ltimers = set()
        timer = self.__prepareTimers(cnf, ltimers, pools)

        aliases = self.__fetchChannels(
            dontdisplay, set(ltimers) | set([timer]), pools)

        mfullname = self.__prepareMntGrp(cnf, timer, pools)

        index = 0
        fullnames = Utils.getFullDeviceNames(pools, aliases)
        for al in aliases:
            index = self.addDevice(
                al, dontdisplay, pools, cnf,
                al if al in ltimers else timer, index, fullnames)

        conf = json.dumps(cnf)
        self.__pfun.storeConfiguration()
        return conf, mfullname

    ## switch to active measurement
    def switchMntGrp(self, pools):
        ms = self.__pfun.getMacroServer()
        amntgrp = Utils.getEnv('ActiveMntGrp', ms)
        self.__selection["MntGrp"] = amntgrp
        self.__pfun.fetchConfiguration()
        self.importMntGrp(pools)

    ## provides configuration of mntgrp
    # \param proxy DeviceProxy of mntgrp
    # \returns string with mntgrp configuration
    def mntGrpConfiguration(self, pools, proxy=None):
        if not proxy:
            if not self.__selection["MntGrp"]:
                self.switchMntGrp(pools)
            mntGrpName = self.__selection["MntGrp"]
            fullname = str(Utils.getMntGrpName(pools, mntGrpName))
            if not fullname:
                return "{}"
            dpmg = Utils.openProxy(fullname)
        else:
            dpmg = proxy
        return str(dpmg.Configuration)

    ## import setting from active measurement
    def importMntGrp(self, pools):
        conf = json.loads(self.mntGrpConfiguration(pools))

        dsg = json.loads(self.__selection["DataSourceGroup"])
        hel = json.loads(self.__selection["HiddenElements"])
        channels = Utils.getExperimentalChannels(pools)
        for ch in channels:
            if ch in dsg.keys():
                dsg[ch] = False
            if ch in hel:
                hel.remove(ch)

        otimers = None
        timers = {}
        tangods = []
        if "timer" in conf.keys() and "controllers" in conf.keys():
            timers[conf["timer"]] = ''
            for ctrl in conf["controllers"].values():
                if 'units' in ctrl.keys() and \
                        '0' in ctrl['units'].keys():
                    if 'timer' in ctrl['units']['0'].keys():
                        timers[ctrl['units']['0']['timer']] = ''
                        if 'channels' in ctrl['units']['0'].keys():
                            for ch in ctrl['units']['0']['channels'].values():
                                dsg[ch['name']] = True

                                if not bool(ch['plot_type']):
                                    hel.append(ch['name'])
                    if 'channels' in ctrl['units']['0'].keys():
                        for ch in ctrl['units']['0']['channels'].values():
                            if '_controller_name' in ch.keys() and \
                                    ch['_controller_name'] == '__tango__':
                                tangods.append(
                                    [ch['name'], ch['label'], ch["source"]])

            if tangods and NXSTOOLS:
                jds = self.__createDataSources(tangods)
                for ctrl in conf["controllers"].values():
                    if 'units' in ctrl.keys() and \
                            '0' in ctrl['units'].keys():
                        if 'channels' in ctrl['units']['0'].keys():
                            for ch in ctrl['units']['0']['channels'].values():
                                if '_controller_name' in ch.keys() and \
                                        ch['_controller_name'] == '__tango__':
                                    if ch["source"] in jds.keys():
                                        name = jds[ch["source"]]
                                        dsg[name] = True
                                        if not bool(ch['plot_type']):
                                            hel.append(ch['name'])

            dtimers = Utils.getAliases(pools, timers)
            otimers = list(dtimers.values())
            otimers.remove(dtimers[conf["timer"]])
            otimers.insert(0, dtimers[conf["timer"]])

            tms = json.loads(self.__selection["Timer"])
            tms.extend(otimers)

            hel2 = json.loads(self.__selection["HiddenElements"])
            for tm in tms:
                if tm in hel2:
                    if tm in dsg.keys():
                        dsg[tm] = False
                    if tm in hel:
                        hel.remove(tm)

        changed = False
        jdsg = json.dumps(dsg)
        if self.__selection["DataSourceGroup"] != jdsg:
            self.__selection["DataSourceGroup"] = jdsg
            changed = True

        jhel = json.dumps(hel)
        if self.__selection["HiddenElements"] != jhel:
            self.__selection["HiddenElements"] = jhel
            changed = True

        if otimers is not None:
            jtimers = json.dumps(otimers)
            if self.__selection["Timer"] != jtimers:
                self.__selection["Timer"] = jtimers
                changed = True
        if changed:
            self.__pfun.storeConfiguration()

    ## available mntgrps
    # \returns list of available measurement groups
    def availableMeasurementGroups(self):
        mntgrps = None
        pool = None
        ms = self.__pfun.getMacroServer()
        msp = Utils.openProxy(ms)
        pn = msp.get_property("PoolNames")["PoolNames"]
        fpool = None
        for pl in pn:
            pool = Utils.openProxy(pl)
            if not fpool:
                fpool = pool
        if fpool:
            mntgrps = Utils.getMntGrps(fpool)
        mntgrps = mntgrps if mntgrps else []
        amntgrp = Utils.getEnv('ActiveMntGrp', ms)

        try:
            if mntgrps:
                ind = mntgrps.index(amntgrp)
                mntgrps[0], mntgrps[ind] = mntgrps[ind], mntgrps[0]
        except ValueError:
            pass
        return mntgrps

    ## checks client records
    def __checkClientRecords(self, datasources, pools):

        describer = Describer(self.__pfun.setConfigInstance())

        frecords = Utils.getFullDeviceNames(pools)
        dsres = describer.dataSources(
            set(datasources) - set(frecords.keys()), 'CLIENT')
        records = [str(dsr[2]) for dsr in dsres.values()]

        cpres = describer.components(
            list(set(self.__pfun.components) |
                 set(self.__pfun.automaticComponents) |
                 set(self.__pfun.mandatoryComponents())),
            '', 'CLIENT')
        for grp in cpres:
            for dss in grp.values():
                for dsrs in dss.values():
                    for dsr in dsrs:
                        records.append(str(dsr[2]))

        urecords = json.loads(self.__selection["DataRecord"]).keys()
        precords = frecords.values()
        missing = sorted(set(records)
                         - set(self.recorder_names)
                         - set(urecords)
                         - set(precords))
        if missing:
            raise Exception(
                "User Data not defined %s" % str(missing))

    @classmethod
    def __createMntGrp(cls, ms, mntGrpName, timer, pools):
        pool = None
        amntgrp = Utils.getEnv('ActiveMntGrp', ms)
        msp = Utils.openProxy(ms)
        pn = msp.get_property("PoolNames")["PoolNames"]
        apool = None
        lpool = [None, 0]
        fpool = None
        for pl in pn:
            pool = Utils.openProxy(pl)
            if not fpool:
                fpool = pool
            mntgrps = Utils.getMntGrps(pool)
            if amntgrp in mntgrps:
                apool = pool
            if lpool[1] < len(mntgrps):
                lpool = [pool, len(mntgrps)]

        if not apool:
            apool = lpool[0]
        lpool = None
        if not apool and fpool:
            apool = fpool
        fpool = None
        if not apool and len(pools) > 0:
            apool = pools[0]
        if apool:
            apool.CreateMeasurementGroup([mntGrpName, timer])
            mfullname = str(Utils.getMntGrpName(pools, mntGrpName))
        return mfullname

    ## prepares timers
    def __prepareTimers(self, cnf, ltimers, pools):
        mtimers = json.loads(self.__selection["Timer"])
        timer = mtimers[0] if mtimers else ''
        if not timer:
            raise Exception(
                "Timer or Monitor not defined")
        fullname = Utils.getFullDeviceNames(pools, [timer])[timer]
        if not fullname:
            raise Exception(
                "Timer or Monitor cannot be found amount the servers")
        cnf['monitor'] = fullname
        cnf['timer'] = fullname
        if len(mtimers) > 1:
            ltimers = set(mtimers[1:])
            if timer in ltimers:
                ltimers.remove(timer)
        return timer

    def __fetchChannels(self, dontdisplay, timers, pools):
        aliases = []
        datasources = self.__pfun.dataSources

        self.__checkClientRecords(datasources, pools)
        if isinstance(datasources, list):
            aliases = list(datasources)
        pchannels = json.loads(self.__selection["OrderedChannels"])
        aliases.extend(
            list(set(pchannels) & set(self.__pfun.disableDataSources)))

        res = self.__pfun.cpdescription('CLIENT')

        for grp in res:
            for cp, dss in grp.items():
                ndcp = cp in dontdisplay
                for ds in dss.keys():
                    aliases.append(str(ds))
                    if not ndcp and str(ds) in dontdisplay:
                        dontdisplay.remove(str(ds))

        self.__selection["HiddenElements"] = json.dumps(list(dontdisplay))
        aliases = list(set(aliases))

        for tm in timers:
            if tm not in aliases:
                aliases.append(tm)
                dontdisplay.add(tm)

        pchannels = [ch for ch in pchannels if ch in aliases]
        aliases = list(set(aliases) - set(pchannels))
        pchannels.extend(aliases)
        return pchannels

    ## sets mntgrp
    def __prepareMntGrp(self, cnf, timer, pools):
        if not self.__selection["MntGrp"]:
            self.__selection["MntGrp"] = self.__defaultmntgrp
        mntGrpName = self.__selection["MntGrp"]
        mfullname = str(Utils.getMntGrpName(pools, mntGrpName))
        ms = self.__pfun.getMacroServer()

        if not mfullname:
            mfullname = self.__createMntGrp(ms, mntGrpName, timer, pools)

        Utils.setEnv('ActiveMntGrp', mntGrpName, ms)
        cnf['label'] = mntGrpName
        return mfullname

    def __createDataSources(self, tangods):
        ads = self.__pfun.availableDataSources()
        sds = self.__pfun.getSourceDescription(ads)

        extangods = []
        exsource = {}
        for name, label, initsource in tangods:
            source = initsource if initsource[:8] != 'tango://' \
                else initsource[8:]
            msource = None
            csource = None
            spsource = source.split("/")
            if len(spsource) > 3 and ":" in spsource[0]:
                host, port = spsource[0].split(":")
                mhost = host.split(".")[0]
                csource = "/".join(spsource[1:])
                if mhost != host:
                    msource = "%s:%s/%s" % (mhost, port, csource)
                device = "/".join(spsource[1:-1])
                attribute = spsource[-1]
                exsource[source] = [host, port, device, attribute]
            extangods.append(
                [name, label, initsource, source, msource, csource])

        jds = {}
        for ds in sds:
            js = json.loads(ds)
            for name, label, initsource, source, msource, csource in extangods:
                if source == js["record"]:
                    jds[initsource] = js["dsname"]
                    break
                elif msource == js["record"]:
                    jds[initsource] = js["dsname"]
                    break

        for name, label, initsource, source, msource, csource in extangods:
            if initsource not in jds:
                jds[initsource] = None
                i = 0
                nname = name
                while nname in ads:
                    i += 1
                    nname = "%s_%s" % (name, i)
                name = nname

                if source in exsource:
                    host, port, device, attribute = exsource[source]
                    df = XMLFile("ds.xml")
                    sr = NDSource(df)
                    sr.initTango(
                        name, device, "attribute", attribute, host, port)

                    inst = self.__pfun.setConfigInstance()
                    xml = df.prettyPrint()
                    inst.xmlstring = str(xml)
                    inst.storeDataSource(str(name))
                    jds[initsource] = name
        return jds

    ## adds device into configuration dictionary
    # \param cls class instance
    # \param device device alias
    # \param dontdisplay list of devices disable for display
    # \param pools list of give pools
    # \param cnf configuration dictionary
    # \param timer device timer
    # \param index device index
    # \returns next device index
    @classmethod
    def addDevice(cls, device, dontdisplay, pools, cnf,
                  timer, index, fullnames=None):
        if not fullnames:
            fullnames = Utils.getFullDeviceNames(pools, [device, timer])

        ctrls = Utils.getDeviceControllers(pools, [device])
        ctrl = ctrls[device] if ctrls and device in ctrls.keys() else ""
        timers = Utils.getFullDeviceNames(pools, [timer])
        fulltimer = fullnames[timer] \
            if timers and timer in fullnames.keys() else ""
        if not ctrl:
            return index

        cls.__addController(cnf, ctrl, fulltimer)
        fullname = fullnames[device] \
            if fullnames and device in fullnames.keys() else ""
        index = cls.__addChannel(cnf, ctrl, device, fullname,
                                     dontdisplay, index)
        return index

    ## adds controller into configuration dictionary
    @classmethod
    def __addController(cls, cnf, ctrl, fulltimer):
        if 'controllers' not in cnf.keys():
            cnf['controllers'] = {}
        if not ctrl in cnf['controllers'].keys():
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

    ## adds channel into configuration dictionary
    @classmethod
    def __addChannel(cls, cnf, ctrl, device, fullname, dontdisplay, index):

        ctrlChannels = cnf['controllers'][ctrl]['units']['0'][
            u'channels']
        if not fullname in ctrlChannels.keys():
            source = Utils.getSource(fullname)
            shp, dt, _, ut = Utils.getShapeTypeValue(source)
            dct = {}
            dct['_controller_name'] = unicode(ctrl)
            dct['_unit_id'] = u'0'
            dct['conditioning'] = u''
            dct['data_type'] = dt
            dct['data_units'] = ut
            dct['enabled'] = True
            dct['full_name'] = fullname
            dct['index'] = index
            index += 1
            dct['instrument'] = None
            dct['label'] = unicode(device)
            dct['name'] = unicode(device)
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

            dct['source'] = source
            ctrlChannels[fullname] = dct

        return index
