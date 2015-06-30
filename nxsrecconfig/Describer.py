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
## \file Describer.py
# component describer

"""  Component Describer """

import re
import json
import PyTango
import xml.dom.minidom
from .Utils import Utils

## Basic DataSource item
class DSItem(object):
    __slots__ = 'name', 'dstype', 'record'
    
    ## constructor
    # \param name datasource name
    # \param dstype datasource type
    # \param record datasource record
    def __init__(self, name=None, dstype=None, record=None, dsitem=None):
        if dsitem:
            ## datasource name
            self.name = dsitem.name
            ## datasource type
            self.dstype = dsitem.dstype
            ## datasource record
            self.record = dsitem.record
        else:
            self.name = str(name) if name else None
            self.dstype = str(dstype) if dstype else None
            self.record = str(record) if record else None
        

## Extended DataSource item
class ExDSItem(DSItem):
    __slots__ = 'mode', 'nxtype', 'shape'

    ## constructor
    # \param dsitem datasource item
    # \param mode writing mode
    # \param nxtype nexus type
    # \param shape datasource shape
    def __init__(self, dsitem, mode, nxtype, shape):
        DSItem.__init__(self, dsitem=dsitem)
        ## writing mode
        self.mode = str(mode) if mode else None
        ## nexus type
        self.nxtype = str(nxtype) if nxtype else None
        ## datasource shape
        self.shape = shape


class ExDSDict(dict):

    def __init__(self, *args, **kw):
        super(ExDSDict, self).__init__(*args, **kw)
        self.counter = 1
        self.prefix = '__unnamed__'
 
    def appendDSList(self, dslist, mode, nxtype=None, shape=None):
        fname = None
        for dsitem in dslist:
            name = dsitem.name
            if name:
                if name not in self.keys():
                    self[name] = []
                self[name].append(ExDSItem(dsitem, mode, nxtype, shape))
            elif dsitem.dstype:
                name = self.prefix + str(self.counter)
                while name in self.keys():
                    name = self.prefix + str(self.counter)
                    self.counter = self.counter + 1
                self[name] = []
                self[name].append(ExDSItem(dsitem, mode, nxtype, shape))
            if not fname:
                fname = name

        return fname



## NeXus Sardana Recorder settings
class Describer(object):
    """ Lists datasources, strategy, dstype and record name
        of given component """

    ## constructor
    # \param configserver configuration server name
    def __init__(self, nexusconfig_device, tree=False):
        self.__nexusconfig_device = nexusconfig_device
        self.treeOutput = tree

    ## describes given components
    # \param components given components.
    #        If None all available ones are taken
    # \param strategy list datasets only with given strategy.
    #        If '' all available ones are taken
    # \param dstype list datasets only with given datasource type.
    #        If '' all available ones are taken
    # \param cfvars configuration variables
    def components(self, components=None, strategy='', dstype='', cfvars=None):
        result = []

        if components is not None:
            cpp = Utils.command(self.__nexusconfig_device,
                                "availableComponents")
            cps = [cp for cp in components if cp in cpp]
        else:
            cps = Utils.command(self.__nexusconfig_device,
                                "availableComponents")
        if components is None:
            mand = Utils.command(self.__nexusconfig_device,
                                 "mandatoryComponents")
            if self.treeOutput:
                cps = list(set(cps) - set(mand))
            else:
                cps = list(set(cps) | set(mand))
                
        if self.treeOutput:
            result = [{}, {}]
            if components is None:
                result[0] = self.__fillintree(mand, strategy, dstype)
            result[1] = self.__fillintree(cps, strategy, dstype)
        else:
            result = self.__fillinlist(cps, strategy, dstype, cfvars)
            
        return result

    def __fillinlist(self, cps, strategy, dstype, cfvars):
        result = []
        for cp in cps:
            dss = self.__getInstDataSourceAttributes(cp, cfvars)
            for ds in dss.keys():
                for vds in dss[ds]:
                    if (not strategy or vds[0] == strategy) and \
                        (not dstype or vds[1] == dstype):
                        elem = {}
                        elem["dsname"] = ds
                        elem["strategy"] = vds.mode
                        elem["dstype"] = vds.dstype
                        elem["record"] = vds.record
                        elem["nxtype"] = vds.nxtype
                        elem["shape"] = vds.shape
                        elem["cpname"] = cp
                        result.append(elem)
        return result

    def __fillintree(self, cps, strategy, dstype):
        result = {}
        for cp in cps:
            dss = self.__getDataSourceAttributes(cp)
            tr = {}
            for ds in dss.keys():
                for vds in dss[ds]:
                    if (not strategy or vds.mode == strategy) and \
                            (not dstype or vds.dstype == dstype):
                        if ds not in tr:
                            tr[ds] = []
                        tr[ds].append((vds.mode, vds.dstype, vds.record,
                                       vds.nxtype, vds.shape))
            result[cp] = tr
        return result

    def __getDSFromNode(self, node, dsl=None):
        label = 'datasources'
        name = None
        dstype = None
        record = None
        dslist = dsl if dsl else []

        if node.nodeName == 'datasource':
            if node.hasAttribute("type"):
                dstype = node.attributes["type"].value
            if node.hasAttribute("name"):
                name = node.attributes["name"].value
            record = Utils.getRecord(node)
            dslist.append(DSItem(name, dstype, record))

        elif node.nodeType == node.TEXT_NODE:
            dsitem = DSItem()
            dstxt = node.data
            index = dstxt.find("$%s." % label)
            while index != -1:
                try:
                    subc = re.finditer(
                        r"[\w]+",
                        dstxt[(index + len(label) + 2):]).next().group(0)
                except (StopIteration, IndexError):
                    subc = ''
                name = subc.strip() if subc else ""
                dsitem = self.__describeDataSource(name)
                if dsitem.dstype:
                    break
                index = dstxt.find("$%s." % label, index + 1)
            dslist.append(dsitem)

        if name and str(dstype) == 'PYEVAL':
            for child in node.childNodes:
                self.__getDSFromNode(child, dslist)

        return dslist

    ## describes given datasources
    # \param names given datasources.
    #        If None all available ones are taken
    # \param dstype list datasources only with given type.
    #        If '' all available ones are taken
    def dataSources(self, names=None, dstype=''):
        ads = Utils.command(self.__nexusconfig_device,
                            "availableDataSources")
        if names is not None:
            dss = [name for name in names if name in ads]
        else:
            dss = ads

        result = {}
        for name in dss:
            if name:
                dsitem = self.__describeDataSource(name)
                if dstype and dsitem.dstype != dstype:
                    continue
                result[name] = dsitem
        return result

    def __describeDataSource(self, name):
        dstype = None
        record = None
        try:
            dsource = Utils.command(self.__nexusconfig_device,
                                    "dataSources", [str(name)])
        except (PyTango.DevFailed, PyTango.Except, PyTango.DevError):
            dsource = []
        if len(dsource) > 0:
            indom = xml.dom.minidom.parseString(dsource[0])
            dss = indom.getElementsByTagName("datasource")
            for ds in dss:
                if ds.nodeName == 'datasource':
                    if ds.hasAttribute("type"):
                        dstype = ds.attributes["type"].value
                    if ds.hasAttribute("name"):
                        name = ds.attributes["name"].value
                    record = Utils.getRecord(ds)
        return DSItem(name, dstype, record)

    @classmethod
    def __getShape(cls, node):
        shape = None
        rank = int(node.attributes["rank"].value)
        shape = [None] * rank
        dims = node.getElementsByTagName("dim")
        for dim in dims:
            index = int(dim.attributes["index"].value)
            if dim.hasAttribute("value"):
                try:
                    value = int(dim.attributes["value"].value)
                except ValueError:
                    value = dim.attributes["value"].value
                shape[index - 1] = value
        return shape

    def __getDataSourceAttributes(self, cp):
        xmlc = Utils.command(self.__nexusconfig_device,
                             "components", [cp])
        names = []
        if not len(xmlc) > 0:
            return names
        return self.__getDSFromXML(xmlc[0])

    def __getInstDataSourceAttributes(self, cp, cfvars=None):
        if cfvars:
            cv = json.loads(self.__nexusconfig_device.variables)
            sv = json.loads(cfvars)
            if sv and isinstance(sv, dict):
                cv.update(sv)
            self.__nexusconfig_device.variables = json.dumps(cv)
        xmlc = Utils.command(self.__nexusconfig_device,
                             "instantiatedComponents", [cp])
        names = []
        if not len(xmlc) > 0:
            return names
        return self.__getDSFromXML(xmlc[0])

    def __getDSFromXML(self, cpxml):
        indom = xml.dom.minidom.parseString(cpxml)
        strategy = indom.getElementsByTagName("strategy")

        dss = ExDSDict()
        for sg in strategy:
            if sg.hasAttribute("mode"):
                mode = sg.attributes["mode"].value
                name = None
                nxtype = None
                dset = sg.parentNode
                if dset.hasAttribute("type"):
                    nxtype = dset.attributes["type"].value

                nxt = sg.nextSibling
                loop = True
                shape = None
                while nxt and loop:
                    if nxt.nodeName == 'dimensions':
                        shape = self.__getShape(nxt)
                        loop = False
                    nxt = nxt.nextSibling

                prev = sg.previousSibling
                while prev and loop:
                    if prev.nodeName == 'dimensions':
                        shape = self.__getShape(prev)
                        loop = False
                    prev = prev.previousSibling

                nxt = sg.nextSibling
                while nxt and not name:
                    name = dss.appendDSList(self.__getDSFromNode(nxt), 
                                            mode, nxtype, shape)
                    nxt = nxt.nextSibling

                prev = sg.previousSibling
                while prev and not name:
                    name = dss.appendDSList(self.__getDSFromNode(prev), 
                                            mode, nxtype, shape)
                    prev = prev.previousSibling

        return dss
