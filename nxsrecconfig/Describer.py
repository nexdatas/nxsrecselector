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

"""  Component Describer """

import re
import json
import PyTango
import xml.dom.minidom
from .Utils import Utils, TangoUtils


class DSItem(object):
    """ Basic DataSource item
    """
    __slots__ = 'name', 'dstype', 'record'

    ##
    def __init__(self, name=None, dstype=None, record=None, dsitem=None):
        """ constructor

        :param name: datasource name
        :param dstype: datasource type
        :param record: datasource record
        :param dsitem: datasource item
        """
        if dsitem:
            #: datasource name
            self.name = dsitem.name
            #: datasource type
            self.dstype = dsitem.dstype
            #: datasource record
            self.record = dsitem.record
        else:
            self.name = str(name) if name is not None else None
            self.dstype = str(dstype) if dstype is not None else None
            self.record = str(record) if record is not None else None


class ExDSItem(DSItem):
    """ Extended DataSource item
    """
    __slots__ = 'mode', 'nxtype', 'shape'

    ##
    def __init__(self, dsitem=None, mode=None, nxtype=None, shape=None):
        """ constructor

        :param dsitem: datasource item
        :param mode: writing mode
        :param nxtype: nexus type
        :param shape: datasource shape
        """
        DSItem.__init__(self, dsitem=dsitem)
        #: writing mode
        self.mode = str(mode) if mode is not None else None
        #: nexus type
        self.nxtype = str(nxtype) if nxtype is not None else None
        #: datasource shape
        self.shape = shape


class ExDSDict(dict):
    """ Extended DataSource Dictionary
    """

    def __init__(self, *args, **kw):
        """ constructor

        :param args: dict args
        :param kw: dict kw
        """
        super(ExDSDict, self).__init__(*args, **kw)
        self.__counter = 1
        self.__prefix = '__unnamed__'

    def appendDSList(self, dslist, mode, nxtype=None, shape=None):
        """ appends a list of ExDSItem

        :param dslist: DSItem list
        :param mode: startegy mode
        :param nxtype: NeXus type
        :param shape: data shape
        :returns: datasource name for first added datasource
              or None if not appended
        """
        fname = None
        for dsitem in dslist:
            name = dsitem.name
            if name:
                if name not in self.keys():
                    self[name] = []
                self[name].append(ExDSItem(dsitem, mode, nxtype, shape))
            elif dsitem.dstype:
                name = self.__prefix + str(self.__counter)
                while name in self.keys():
                    name = self.__prefix + str(self.__counter)
                    self.__counter = self.__counter + 1
                self[name] = []
                self[name].append(ExDSItem(dsitem, mode, nxtype, shape))
            if not fname:
                fname = name

        return fname


class Describer(object):
    """ Lists datasources, strategy, dstype and record name
        of given component """

    def __init__(self, nexusconfig_device, tree=False, pyevalfromscript=False):
        """ constructor

        :param nexusconfig_device: configserver configuration server name
        :param tree: output flag for dictionary tree
        :param tree: output flag for dictionary tree
        """
        self.__nexusconfig_device = nexusconfig_device
        self.__treeOutput = tree
        self.__pyevalfromscript = pyevalfromscript
        self.__availableComponents = TangoUtils.command(
            self.__nexusconfig_device,
            "availableComponents")
        self.__availableDataSources = TangoUtils.command(
            self.__nexusconfig_device,
            "availableDataSources")

    def components(self, components=None, strategy='', dstype='', cfvars=None):
        """ describes given components

        :param components: given components.
                           If None all available ones are taken
        :param strategy: list datasets only with given strategy.
                         If '' all available ones are taken
        :param dstype: list datasets only with given datasource type.
                       If '' all available ones are taken
        :param cfvars: configuration variables
        :returns: list of dictionary with description of components
        """
        result = []

        if components is not None:
            cps = [cp for cp in components if cp in self.__availableComponents]
        else:
            cps = list(self.__availableComponents)

        if self.__treeOutput:
            result = [{}]
            result[0] = self.__fillintree(cps, strategy, dstype)
        else:
            result = self.__fillinlist(cps, strategy, dstype, cfvars)

        return result

    def __fillinlist(self, cps, strategy, dstype, cfvars):
        """ fills in the list of output elements

        :param cps: component list
        :param strategy: required strategy or None
        :param dstype: required datasource type or None
        :param cfvars: dictionary with configuration variables
        :returns: list of output dictionary elements
        """
        result = []
        for cp in cps:
            dss = self.__getInstDataSourceAttributes(cp, cfvars)
            for ds in dss.keys():
                for vds in dss[ds]:
                    if (not strategy or vds.mode == strategy) and \
                       (not dstype or vds.dstype == dstype):
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
        """ fills in the dictionary of output elements

        :param cps: component list
        :param strategy: required strategy or None
        :param dstype: required datasource type or None
        :returns: dictionary of output dictionary elements
        """
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
        """ provides datasource item from XML node

        :param node: xml node
        :param dsl: list with datasource items (DSItem)
        """
        label = 'datasources'
        name = None
        dstype = None
        record = None
        dslist = dsl if dsl else []
        dsxmls = None

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
                if str(name) in self.__availableDataSources:
                    dsxmls = TangoUtils.command(self.__nexusconfig_device,
                                                "dataSources", [str(name)])
                else:
                    dsxmls = None
                    dsitem = DSItem(name, "__ERROR__", "__ERROR__")
                if dsxmls:
                    dsitem = self.__describeDataSource(name, dsxmls[0])
                    if dsitem.dstype:
                        dstype = dsitem.dstype
                        break
                else:
                    dsitem = DSItem(name, None, None)
                index = dstxt.find("$%s." % label, index + 1)
            dslist.append(dsitem)
        if name and str(dstype) == 'PYEVAL':
            if dsxmls and self.__pyevalfromscript:
                dslist.extend(self.__findsubdatasources(dsxmls[0]))
            else:
                for child in node.childNodes:
                    self.__getDSFromNode(child, dslist)

        return dslist

    def __findsubdatasources(self, dsxml):
        dslist = []
        result = ""
        label = 'datasources'
        indom = xml.dom.minidom.parseString(dsxml)
        cnode = indom.getElementsByTagName("datasource")[0]
        for child in cnode.childNodes:
            if child.nodeName == 'result':
                for content in child.childNodes:
                    if content.nodeType == content.TEXT_NODE:
                        result += str(content.data)

        index = dsxml.find("$%s." % label)
        while index != -1:
            try:
                subc = re.finditer(
                    r"[\w]+",
                    dsxml[(index + len(label) + 2):]).next().group(0)
            except (StopIteration, IndexError):
                subc = ''
            name = subc.strip() if subc else ""
            if name in result:
                chdsxml = TangoUtils.command(
                    self.__nexusconfig_device,
                    "dataSources", [str(name)])
                if chdsxml:
                    dsitem = self.__describeDataSource(name, chdsxml[0])
                    if dsitem.dstype:
                        dslist.append(dsitem)
                else:
                    dslist.append(DSItem(name, None, None))
            index = dsxml.find("$%s." % label, index + 1)
        return dslist

    @classmethod
    def __getShape(cls, node):
        """ provides shape from node

        :param node: xml node
        :returns: shape of node
        """
        rank = int(node.attributes["rank"].value)
        shape = [None] * rank
        dims = node.getElementsByTagName("dim")
        for dim in dims:
            index = int(dim.attributes["index"].value)
            if dim.hasAttribute("value"):
                try:
                    value = int(dim.attributes["value"].value)
                except ValueError:
                    value = str(dim.attributes["value"].value)
                shape[index - 1] = value
            else:
                dss = node.getElementsByTagName("datasource")
                if dss:
                    if dss[0].hasAttribute("name"):
                        value = dss[0].attributes["name"].value
                    else:
                        value = '__unnamed__'
                    shape[index - 1] = "$datasources.%s" % value
                else:
                    value = " ".join(t.nodeValue for t in dim.childNodes
                                     if t.nodeType == t.TEXT_NODE)
                    try:
                        value = int(value)
                    except:
                        value = value.strip()
                        if not value:
                            value = None
                    shape[index - 1] = value

        return shape

    def __getDataSourceAttributes(self, cp):
        """ provides datasource ExDSDict of given component

        :param cp : component name
        :returns: datasource ExDSDict
        """
        xmlc = TangoUtils.command(self.__nexusconfig_device,
                                  "components", [cp])
        if not len(xmlc) > 0:
            return ExDSDict()
        return self.__getDSFromXML(xmlc[0])

    def __getInstDataSourceAttributes(self, cp, cfvars=None):
        """ provides datasource ExDSDict of given instantiated component

        :param cp : component name
        :param cfvars : component variables
        :returns: datasource ExDSDict
        """
        if cfvars:
            cv = json.loads(self.__nexusconfig_device.variables)
            sv = json.loads(cfvars)
            if sv and isinstance(sv, dict):
                cv.update(sv)
            self.__nexusconfig_device.variables = json.dumps(cv)
        xmlc = TangoUtils.command(self.__nexusconfig_device,
                                  "instantiatedComponents", [cp])
        if not len(xmlc) > 0:
            return ExDSDict()
        return self.__getDSFromXML(xmlc[0])

    def __getDSFromXML(self, cpxml):
        """ provides datasource ExDSDict of given component xml

        :param cpxml : component xml
        :returns: datasource ExDSDict
        """
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

    def dataSources(self, names=None, dstype=''):
        """ describes given datasources

        :param names: given datasources.
                      If None all available ones are taken
        :param dstype: list datasources only with given type.
                       If '' all available ones are taken
        :returns: list of dictionary with description of datasources
        """
        ads = list(self.__availableDataSources)
        if names is not None:
            dss = [name for name in names if name in ads]
        else:
            dss = ads
        try:
            if dss:
                xmls = TangoUtils.command(self.__nexusconfig_device,
                                          "dataSources", dss)
            else:
                xmls = []
        except:
            xmls = None

        dslist = []
        dsres = {}
        for i, name in enumerate(dss):
            if name:
                if xmls:
                    dsxml = xmls[i]
                dsitem = self.__describeDataSource(name, dsxml)
                if dstype and dsitem.dstype != dstype:
                    continue
                dsres[name] = dsitem
                if dsxml and self.__pyevalfromscript:
                    dsitems = self.__findsubdatasources(dsxml)
                    for itm in dsitems:
                        dsres[itm.name] = itm

        if self.__treeOutput:
            dslist = [{}]
            dslist[0] = dsres
        else:
            dslist = []
            if isinstance(dsres, dict):
                for ds in dsres.values():
                    elem = {}
                    elem["dsname"] = ds.name
                    elem["dstype"] = ds.dstype
                    elem["record"] = ds.record
                    dslist.append(str(json.dumps(elem)))
        return dslist

    def __describeDataSource(self, name, dsxml=None):
        """
        """
        dstype = None
        record = None
        try:
            if not dsxml:
                dsource = TangoUtils.command(self.__nexusconfig_device,
                                             "dataSources", [str(name)])
            else:
                dsource = [dsxml]
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
