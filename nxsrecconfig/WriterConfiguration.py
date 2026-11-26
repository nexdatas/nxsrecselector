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

""" NXSDataWriter configuration of a selector profile and scan

It creates the XML configuration of NXSDataWriter for a scan from the
profile of NXSRecSelector, i.e. the selected components, datasources,
user data and configuration variables, and from the scan channels.
It is used by the Sardana NeXus recorder and can be used by other scan
systems, e.g. BLISS.
"""

import json
import logging
import re

import numpy

try:
    import tango
except Exception:
    import PyTango as tango


class NumpyEncoder(json.JSONEncoder):

    """ JSON encoder of numpy values """

    def default(self, obj):
        """ converts numpy values to python values

        :param obj: object to convert
        :type obj: `any`
        :returns: converted object
        :rtype: `any`
        """
        if isinstance(obj, numpy.integer):
            return int(obj)
        elif isinstance(obj, numpy.floating):
            return float(obj)
        elif isinstance(obj, numpy.ndarray):
            return obj.tolist()
        elif isinstance(obj, numpy.bool_):
            return bool(obj)
        return json.JSONEncoder.default(self, obj)


def _item(elm, key):
    """ provides an item of a channel description

    :param elm: channel description, an object or a dictionary
    :type elm: `any`
    :param key: item name, e.g. ``name``, ``shape`` or ``dtype``
    :type key: :obj:`str`
    :returns: item value
    :rtype: `any`
    """
    if isinstance(elm, dict):
        return elm[key]
    return getattr(elm, key)


class WriterConfiguration(object):

    """ NXSDataWriter configuration of a selector profile and scan """

    def __init__(self, selector, conf=None, variables=None, log=None,
                 getalias=None, moveables=None, oddmntgrp=False,
                 cacheprefix="__configuration_",
                 dynamiccp="__dynamic_component__"):
        """ constructor

        :param selector: NXSRecSelector device proxy or
                         :class:`nxsrecconfig.Settings.Settings`
        :type selector: :class:`tango.DeviceProxy` or `any`
        :param conf: profile configuration of the selector
        :type conf: :obj:`dict` <:obj:`str`, `any`>
        :param variables: configuration variables, extended by the created
                          configuration, e.g. ``nexus_components``
        :type variables: :obj:`dict` <:obj:`str`, `any`>
        :param log: logger with debug, info and warning methods
        :type log: :class:`logging.Logger` or `any`
        :param getalias: provides an alias of a channel or None,
                         tango aliases by default
        :type getalias: callable
        :param moveables: provides moveable names of the scan system,
                          used for cache components
        :type moveables: callable
        :param oddmntgrp: measurement group not defined by the selector,
                          i.e. profile variables are not used
        :type oddmntgrp: :obj:`bool`
        :param cacheprefix: prefix of cache components
        :type cacheprefix: :obj:`str`
        :param dynamiccp: initial dynamic component name
        :type dynamiccp: :obj:`str`
        """
        #: (:class:`tango.DeviceProxy` or `any`) selector
        self.selector = selector
        #: (:obj:`dict` <:obj:`str`, `any`>) profile configuration
        self.conf = conf if conf is not None else {}
        #: (:obj:`dict` <:obj:`str`, `any`>) configuration variables
        self.variables = variables if variables is not None else {}
        #: (:class:`logging.Logger` or `any`) logger
        self.log = log or logging.getLogger("nxsrecconfig")
        #: (callable) alias provider
        self.getalias = getalias or self.tangoAlias
        #: (callable) moveable name provider
        self.moveables = moveables
        #: (:obj:`bool`) measurement group not defined by the selector
        self.oddmntgrp = oddmntgrp
        #: (:obj:`str`) prefix of cache components
        self.cacheprefix = cacheprefix
        #: (:obj:`str`) dynamic component name
        self.dynamicCP = dynamiccp
        #: (:obj:`dict` <:obj:`str`, :obj:`str`>) device aliases
        self.deviceAliases = {}
        #: (:obj:`dict` <:obj:`str`, `None`>) dynamic datasources
        self.dynamicDataSources = {}
        #: (:obj:`list` <:obj:`str`>) moveable datasources
        self.moveableDataSources = []
        #: (:obj:`list` <:obj:`str`>) optional components
        self.availableComps = []
        #: (:obj:`list` <:obj:`str`>) ordered channel aliases
        self.aliases = []
        #: (:class:`tango.Database`) tango database
        self.__db = None

    def tangoAlias(self, name):
        """ provides a tango alias of a device name

        :param name: device name
        :type name: :obj:`str`
        :returns: alias or None
        :rtype: :obj:`str`
        """
        if name.startswith("tango://"):
            name = name[8:]
        if name.find('/') == -1:
            return name
        if name.find(':') >= 0:
            lst = name.split("/")
            name = "/".join(lst[1:])
        try:
            if self.__db is None:
                self.__db = tango.Database()
            alias = self.__db.get_alias(name)
        except Exception:
            alias = None
        return alias

    @classmethod
    def shortName(cls, name):
        """ provides a device name without the tango host

        :param name: device name
        :type name: :obj:`str`
        :returns: short device name
        :rtype: :obj:`str`
        """
        if name.startswith("tango://"):
            name = name[8:]
        if name.find('/') == -1:
            return name
        if name.find(':') >= 0:
            lst = name.split("/")
            name = "/".join(lst[1:])
        return name

    def command(self, command, *args):
        """ executes a selector command

        :param command: command name
        :type command: :obj:`str`
        :param args: command arguments
        :type args: :obj:`list` <`any`>
        :returns: command result
        :rtype: `any`
        """
        server = self.selector
        if server and command:
            if hasattr(server, 'command_inout'):
                if args:
                    return server.command_inout(command, args[0])
                else:
                    return server.command_inout(command)
            else:
                res = getattr(server, command)
                return res(*args)
        else:
            self.log.warning("%s.%s cannot be found" % (server, command))

    def confVar(self, var, default, decode=False, pass_default=False):
        """ provides a variable of the profile configuration

        :param var: variable name
        :type var: :obj:`str`
        :param default: default value
        :type default: `any`
        :param decode: True if the variable is a JSON string
        :type decode: :obj:`bool`
        :param pass_default: if True it returns the default value
        :type pass_default: :obj:`bool`
        :returns: variable value
        :rtype: `any`
        """
        if pass_default:
            return default
        if var in self.conf.keys():
            res = self.conf[var]
            if decode:
                try:
                    dec = json.loads(res)
                    return dec
                except Exception:
                    self.log.warning(
                        "%s = '%s' cannot be decoded" % (var, res))
                    return default
            else:
                return res
        else:
            self.log.warning("%s cannot be found" % (var))
            return default

    def serverVar(self, attr, default, decode=False, pass_default=False):
        """ provides a selector variable

        :param attr: variable name
        :type attr: :obj:`str`
        :param default: default value
        :type default: `any`
        :param decode: True if the variable is a JSON string
        :type decode: :obj:`bool`
        :param pass_default: if True it returns the default value
        :type pass_default: :obj:`bool`
        :returns: variable value
        :rtype: `any`
        """
        if pass_default:
            return default
        if self.selector and attr:
            res = getattr(self.selector, attr)
            if decode:
                try:
                    dec = json.loads(res)
                    return dec
                except Exception:
                    self.log.warning(
                        "%s = '%s' cannot be decoded" % (attr, res))
                    return default
            else:
                return res
        else:
            self.log.warning("%s cannot be found" % (attr))
            return default

    def collectAliases(self, envRec):
        """ collects aliases of the scan channels

        :param envRec: scan environment with ``counters``,
                       ``ref_moveables``, ``column_desc`` or ``datadesc``
        :type envRec: :obj:`dict` <:obj:`str`, `any`>
        """
        names = []
        if 'counters' in envRec:
            names.extend(str(elm) for elm in envRec['counters'])
        if 'ref_moveables' in envRec:
            names.extend(str(elm) for elm in envRec['ref_moveables'])
        if 'column_desc' in envRec:
            names.extend(str(elm['name']) for elm in envRec['column_desc']
                         if 'name' in elm.keys())
        if 'datadesc' in envRec:
            names.extend(str(_item(elm, "name"))
                         for elm in envRec['datadesc'])
        for name in names:
            alias = self.getalias(name)
            if alias:
                self.deviceAliases[alias] = name
            else:
                self.dynamicDataSources[name] = None

    def createDynamicComponent(self, envRec, dss, keys, udata,
                               nexuscomponents):
        """ creates a dynamic component

        :param envRec: scan environment with ``datadesc``
        :type envRec: :obj:`dict` <:obj:`str`, `any`>
        :param dss: datasource names
        :type dss: :obj:`list` <:obj:`str`>
        :param keys: INIT datasource names
        :type keys: :obj:`list` <:obj:`str`>
        :param udata: user data
        :type udata: :obj:`dict` <:obj:`str`, `any`>
        :param nexuscomponents: component names
        :type nexuscomponents: :obj:`list` <:obj:`str`>
        :returns: dynamic component name
        :rtype: :obj:`str`
        """
        self.log.debug('createDynamicComponent:  Step DSs: %s' % dss)
        self.log.debug('createDynamicComponent:  Init DSs: %s' % keys)
        self.log.debug('createDynamicComponent:  Init User Data: %s' % udata)
        lddict = []
        tdss = [ds for ds in dss if not ds.startswith("tango://")
                and ds not in nexuscomponents]
        tgdss = [self.shortName(ds) for ds in dss
                 if ds.startswith("tango://") and ds not in nexuscomponents]
        for dd in envRec.get('datadesc', []):
            alias = self.getalias(str(_item(dd, "name")))
            if alias in tdss and alias not in nexuscomponents:
                mdd = {}
                mdd["name"] = _item(dd, "name")
                mdd["shape"] = _item(dd, "shape")
                mdd["dtype"] = _item(dd, "dtype")
                mdd["strategy"] = 'STEP'
                lddict.append(mdd)
        fields = {}
        for ky, vl in udata.items():
            if "@" not in ky:
                mdd = {}
                mdd["name"] = ky
                mdd["shape"] = numpy.shape(vl)
                try:
                    if mdd["shape"]:
                        rank = len(mdd["shape"])
                        for _ in range(rank):
                            vl = vl[0]
                    mdd["dtype"] = str(type(vl).__name__)
                except Exception as e:
                    self.log.warning(
                        "Cannot find a type of user data %s %s"
                        % (ky, str(e)))
                    mdd["dtype"] = 'string'
                mdd["strategy"] = 'INIT'
                fields[ky] = mdd
        for ky, vl in udata.items():
            if "@" in ky:
                fld, att = ky.split("@")[:2]
                if fld and att:
                    if fld in fields.keys():
                        fields[fld][att] = vl
        for mdd in fields.values():
            lddict.append(mdd)
        tdss.extend(tgdss)
        jddict = json.dumps(lddict, cls=NumpyEncoder)
        jdss = json.dumps(tdss, cls=NumpyEncoder)
        jkeys = json.dumps(keys, cls=NumpyEncoder)
        self.log.debug(
            'createDynamicComponent:  tango STEP datasources: %s' % tdss)
        self.log.debug(
            'createDynamicComponent:  channel STEP datasources: %s' % jddict)
        self.log.debug(
            'createDynamicComponent:  INIT datasources: %s' % jkeys)
        self.dynamicCP = self.command(
            "createDynamicComponent", [jdss, jddict, jkeys])
        return self.dynamicCP

    def removeDynamicComponent(self):
        """ removes the dynamic component
        """
        self.command("removeDynamicComponent", str(self.dynamicCP))

    def availableComponents(self):
        """ provides available components

        :returns: available component names
        :rtype: :obj:`list` <:obj:`str`>
        """
        cmps = self.command("availableComponents")
        if self.availableComps:
            return list(set(cmps) & set(self.availableComps))
        else:
            return cmps

    def __moveableNames(self):
        """ provides moveable names of the scan system

        :returns: moveable names
        :rtype: :obj:`list` <:obj:`str`>
        """
        if self.moveables is None:
            return []
        return list(self.moveables())

    def searchDataSources(self, nexuscomponents, cfm, dyncp, userkeys):
        """ searches the datasources of the scan in the components

        :param nexuscomponents: component names
        :type nexuscomponents: :obj:`list` <:obj:`str`>
        :param cfm: components from measurement group flag
        :type cfm: :obj:`bool`
        :param dyncp: dynamic components flag
        :type dyncp: :obj:`bool`
        :param userkeys: user data keys
        :type userkeys: :obj:`list` <:obj:`str`>
        :returns: selected datasources, datasources not found,
                  components required by datasources,
                  missing user data keys and cache datasources
        :rtype: :obj:`tuple` <:obj:`list` <:obj:`str`>,
                :obj:`list` <:obj:`str`>,
                :obj:`dict` <:obj:`str`, :obj:`list` <:obj:`str`>>,
                :obj:`list` <:obj:`str`>, :obj:`list` <:obj:`str`>>
        """
        self.log.debug('searchDataSources: Init: %s' % str(
            [nexuscomponents, cfm, dyncp, userkeys]))
        dsFound = {}
        dsNotFound = []
        allcpdss = []
        cachedss = []
        cpReq = {}
        keyFound = set()
        if cfm:
            cmps = list(set(nexuscomponents) |
                        set(self.availableComponents()))
        else:
            cmps = list(set(nexuscomponents) &
                        set(self.availableComponents()))
        if self.oddmntgrp:
            nds = []
        else:
            nds = self.command("selectedDataSources")
        nds = nds if nds else []
        datasources = list(set(nds) | set(self.deviceAliases.keys()))
        hascpsrcs = hasattr(self.selector, 'componentSources')
        for cp in cmps:
            self.log.debug('searchDataSources:  component item: %s' % cp)
            try:
                if hascpsrcs:
                    cpdss = json.loads(
                        self.command("componentSources", [cp]))
                    adss = [ds["dsname"] for ds in cpdss
                            if 'parentobj' not in ds or
                            ds['parentobj'] in ['field', 'map', 'vds']]
                    allcpdss.extend(adss)
                    if cp.startswith(self.cacheprefix):
                        cachedss.extend(adss)
                        cldss = [ds["dsname"] for ds in cpdss
                                 if ('parentobj' not in ds or
                                     ds['parentobj'] in
                                     ['field', 'map', 'vds'])
                                 and ds["dstype"] == 'CLIENT']
                        self.moveableDataSources.extend(
                            list(set(cldss) & set(self.__moveableNames())))
                else:
                    cpdss = json.loads(
                        self.command("componentClientSources", [cp]))
                dss = [ds["dsname"] for ds in cpdss
                       if ds["strategy"] == 'STEP' and
                       ds["dstype"] == 'CLIENT']
                reckeys = [ds["record"] for ds in cpdss
                           if ds["dstype"] == 'CLIENT']
                keyFound.update(set(reckeys))
            except Exception as e:
                if cp in nexuscomponents:
                    self.log.warning(
                        "Component '%s' wrongly defined in DB!" % cp)
                    self.log.warning("Error: '%s'" % str(e))
                else:
                    self.log.debug(
                        "searchDataSources:  Component '%s' wrongly "
                        "defined in DB!" % cp)
                    self.log.debug("Error: '%s'" % str(e))
                dss = []
            if dss:
                cdss = list(set(dss) & set(datasources))
                for ds in cdss:
                    self.log.debug(
                        "searchDataSources:  '%s' found in '%s'"
                        % (ds, cp))
                    if ds not in dsFound.keys():
                        dsFound[ds] = []
                    dsFound[ds].append(cp)
                    if cp not in cpReq.keys():
                        cpReq[cp] = []
                    cpReq[cp].append(ds)
        missingKeys = set(userkeys) - keyFound
        datasources.extend(self.dynamicDataSources.keys())
        for ds in datasources:
            if ds not in dsFound.keys() and ds not in allcpdss:
                dsNotFound.append(ds)
                if not dyncp:
                    self.log.warning(
                        "Warning: '%s' will not be stored. "
                        "It was not found in Components!"
                        " Consider setting: NeXusDynamicComponents=True"
                        % ds)
            elif not cfm and ds not in allcpdss:
                if not set(dsFound[ds]) & set(nexuscomponents):
                    dsNotFound.append(ds)
                    if not dyncp:
                        self.log.warning(
                            "Warning: '%s' will not be stored. "
                            "It was not found in User Components!"
                            " Consider setting: "
                            "NeXusDynamicComponents=True" % ds)
        return (nds, dsNotFound, cpReq, list(missingKeys), cachedss)

    def create(self, envRec, userdata):
        """ creates the NXSDataWriter configuration

        The created dynamic component has to be removed with
        :meth:`removeDynamicComponent` when the scan ends.

        :param envRec: scan environment with ``datadesc``, and
                       ``ref_moveables``, ``counters`` or ``column_desc``
        :type envRec: :obj:`dict` <:obj:`str`, `any`>
        :param userdata: user data, extended by sanitized missing keys
        :type userdata: :obj:`dict` <:obj:`str`, `any`>
        :returns: XML configuration
        :rtype: :obj:`str`
        """
        odd = self.oddmntgrp
        cfm = self.confVar("ComponentsFromMntGrp", False, pass_default=odd)
        dyncp = self.confVar("DynamicComponents", True, pass_default=odd)
        self.collectAliases(envRec)
        mandatory = self.command("mandatoryComponents")
        self.log.info("Default Components %s" % str(mandatory))
        nexuscomponents = []
        lst = self.serverVar('components', None, False, pass_default=odd)
        if isinstance(lst, (tuple, list)):
            nexuscomponents.extend(lst)
        self.log.info("User Components %s" % str(nexuscomponents))
        allnexuscomponents = list(set(nexuscomponents) | set(mandatory))
        ccomp = None
        if hasattr(self.selector, "cachecomponent"):
            ccomp = self.selector.cachecomponent
        if ccomp:
            self.log.info("Cache Component %s" % str(ccomp))
            nexuscomponents = [ccomp]
            allnexuscomponents = [ccomp]
        self.availableComps = []
        lst = self.confVar("OptionalComponents", None, True,
                           pass_default=odd)
        if isinstance(lst, (tuple, list)):
            self.availableComps.extend(lst)
        self.availableComps = list(set(self.availableComps))
        self.log.info("Available Components %s" % str(
            self.availableComponents()))
        nds, dsNotFound, cpReq, missingKeys, cachedss = \
            self.searchDataSources(
                allnexuscomponents, cfm, dyncp, userdata.keys())
        self.log.debug("create:  DataSources Not Found : %s" % dsNotFound)
        self.log.debug("create:  Components required : %s" % cpReq)
        self.log.debug("create:  Missing User Data : %s" % missingKeys)
        if "InitDataSources" in self.conf.keys():
            ids = self.confVar("InitDataSources", None, True,
                               pass_default=odd)
        else:
            idsdct = self.confVar("DataSourcePreselection", None, True,
                                  pass_default=odd)
            ids = [k for (k, vl) in idsdct.items() if vl] \
                if idsdct else None
        self.variables["nexus_init_datasources"] = \
            " ".join(missingKeys + list(ids or []))
        udata = {str(re.sub(r"[^0-9a-zA-Z@_]+", "_", str(ky))): userdata[ky]
                 for ky in missingKeys}
        if userdata:
            userdata.update(udata)
        ids = list((set(ids or []) - set(cachedss)) |
                   set(self.moveableDataSources))
        self.createDynamicComponent(
            envRec, dsNotFound if dyncp else [], ids, udata, nexuscomponents)
        nexuscomponents.append(str(self.dynamicCP))
        if cfm:
            self.log.info("Sardana Components %s" % cpReq.keys())
            nexuscomponents.extend(cpReq.keys())
        nexuscomponents = list(set(nexuscomponents))
        nexusvariables = {}
        dct = self.confVar("ConfigVariables", None, True)
        if isinstance(dct, dict):
            nexusvariables = dct
        oldtoswitch = None
        try:
            self.log.info("Components %s" % list(
                set(nexuscomponents) | set(mandatory)))
            toswitch = set()
            for dd in envRec.get('datadesc', []):
                alias = self.getalias(str(_item(dd, "name")))
                if alias:
                    toswitch.add(alias)
            toswitch.update(set(nds))
            och = self.confVar("OrderedChannels", None, True,
                               pass_default=odd)
            allcp = list(nexuscomponents)
            allcp.extend(list(toswitch))
            och = och or []
            self.aliases = [ch for ch in och if ch in allcp]
            if self.aliases:
                self.variables["mgchannels"] = " ".join(self.aliases)
            timers = self.command("availableTimers")
            if timers:
                self.variables["timers"] = " ".join(timers)
            self.variables["nexus_components"] = " ".join(nexuscomponents)
            moveables = [str(ds) for ds in envRec.get('ref_moveables', [])]
            stepdss = [ds for ds in moveables if ds in toswitch]
            stepdss.extend([str(ds) for ds in toswitch
                            if ds not in moveables])
            self.variables["nexus_step_datasources"] = " ".join(stepdss)
            self.selector.configVariables = json.dumps(
                dict(nexusvariables, **self.variables), cls=NumpyEncoder)
            self.log.debug("VAR %s" % self.selector.configVariables)
            self.command("updateConfigVariables")
            self.log.debug("create:  Aliases: %s" % str(self.aliases))
            self.log.debug("create:  Switching to STEP mode: %s" % stepdss)
            oldtoswitch = self.serverVar('stepdatasources', '[]', False)
            stepdss = str(json.dumps(list(toswitch)))
            self.selector.stepdatasources = stepdss
            if hasattr(self.selector, 'linkdatasources'):
                self.selector.linkdatasources = stepdss
            cnfxml = self.command(
                "createWriterConfiguration", nexuscomponents)
        finally:
            self.selector.configVariables = json.dumps(nexusvariables)
            if oldtoswitch is not None:
                self.selector.stepdatasources = oldtoswitch
        return cnfxml
