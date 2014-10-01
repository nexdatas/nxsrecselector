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
## \file Describer.py
# component describer

"""  Component Describer """

import re
import xml.dom.minidom


## NeXus Sardana Recorder settings
class Describer(object):
    """ Lists datasources, strategy, dstype and record name
        of given component """

    ## constructor
    # \param configserver configuration server name
    def __init__(self, nexusconfig_device):
        self.__nexusconfig_device = nexusconfig_device

    ## describes given components
    # \param components given components.
    #        If None all available ones are taken
    # \param strategy list datasets only with given strategy.
    #        If '' all available ones are taken
    # \param dstype list datasets only with given datasource type.
    #        If '' all available ones are taken
    def components(self, components=None, strategy='', dstype=''):
        result = [{}, {}]

        if components is not None:
            cpp = self.__nexusconfig_device.availableComponents()
            cps = [cp for cp in components if cp in cpp]
        else:
            cps = self.__nexusconfig_device.availableComponents()
        if components is None:
            mand = self.__nexusconfig_device.mandatoryComponents()
            cps = list(set(cps) - set(mand))

        if components is None:
            for cp in mand:
                dss = self.__getDataSourceAttributes(cp)
                tr = {}
                for ds in dss.keys():
                    for vds in dss[ds]:
                        if (not strategy or vds[0] == strategy) and \
                                (not dstype or vds[1] == dstype):
                            if ds not in tr:
                                tr[ds] = []
                            tr[ds].append(vds)
                result[0][cp] = tr

        for cp in cps:
            dss = self.__getDataSourceAttributes(cp)
            tr = {}
            for ds in dss.keys():
                for vds in dss[ds]:
                    if (not strategy or vds[0] == strategy) and \
                            (not dstype or vds[1] == dstype):
                        if ds not in tr:
                            tr[ds] = []
                        tr[ds].append(vds)
            result[1][cp] = tr
        return result

    ## describes given components after configuration creation
    # \param components given components.
    #        If None all available ones are taken
    # \param strategy list datasets only with given strategy.
    #        If '' all available ones are taken
    # \param dstype list datasets only with given datasource type.
    #        If '' all available ones are taken
    # \param cfvars configuration variables
    def final(self, components=None, strategy='', dstype='', cfvars=None):

        if components is not None:
            cpp = self.__nexusconfig_device.availableComponents()
            cps = [cp for cp in components if cp in cpp]
        else:
            cps = self.__nexusconfig_device.availableComponents()

        dss = self.__getDataSetAttributes(cps, cfvars)
        tr = []
        for ds in dss.keys():
            for vds in dss[ds]:
                if (not strategy or vds[0] == strategy) and \
                        (not dstype or vds[1] == dstype):
                    elem = {}
                    elem["dsname"] = ds
                    elem["strategy"] = vds[0]
                    elem["dstype"] = vds[1]
                    elem["record"] = vds[2]
                    elem["nxtype"] = vds[3]
                    elem["shape"] = vds[4]
                    tr.append(elem)
        return tr

    @classmethod
    def __getRecord(cls, node):
        res = ''
        host = None
        port = None
        dname = None
        rname = None
        device = node.getElementsByTagName("device")
        if device and len(device) > 0:
            if device[0].hasAttribute("host"):
                host = device[0].attributes["host"].value
            if device[0].hasAttribute("port"):
                port = device[0].attributes["port"].value
            if device[0].hasAttribute("name"):
                dname = device[0].attributes["name"].value

        record = node.getElementsByTagName("record")
        if record and len(record) > 0:
            if record[0].hasAttribute("name"):
                rname = record[0].attributes["name"].value
                if dname:
                    if host:
                        if not port:
                            port = '10000'
                        res = '%s:%s/%s/%s' % (host, port, dname, rname)
                    else:
                        res = '%s/%s' % (dname, rname)
                else:
                    res = rname
        return res

    def __checkNode(self, node, dsl=None):
        label = 'datasources'
        dstype = None
        name = None
        record = None
        dslist = dsl if dsl else []

        if node.nodeName == 'datasource':
            if node.hasAttribute("type"):
                dstype = node.attributes["type"].value
            if node.hasAttribute("name"):
                name = node.attributes["name"].value
            record = self.__getRecord(node)
            dslist.append((name, dstype, record))

        elif node.nodeType == node.TEXT_NODE:
            dstxt = node.data
            index = dstxt.find("$%s." % label)
            while index != -1 and not dstype:
                try:
                    subc = re.finditer(
                        r"[\w]+",
                        dstxt[(index + len(label) + 2):]).next().group(0)
                except Exception:
                    subc = ''
                name = subc.strip() if subc else ""
                name, dstype, record = self.__describeDataSource(name)
                index = dstxt.find("$%s." % label, index + 1)
            dslist.append((name, dstype, record))
        if name and str(dstype) == 'PYEVAL':
            for child in node.childNodes:
                self.__checkNode(child, dslist)
        return dslist

    ## describes given components
    # \param names given datasources.
    #        If None all available ones are taken
    # \param dstype list datasourcesonly with given type.
    #        If '' all available ones are taken
    def dataSources(self, names=None, dstype=''):
        ads = self.__nexusconfig_device.availableDataSources()
        if names is not None:
            dss = [name for name in names if name in ads]
        else:
            dss = ads

        result = {}
        for name in dss:
            if name:
                rec = self.__describeDataSource(name)
                if dstype and rec[1] != dstype:
                    continue
                result[name] = rec
        return result

    def __describeDataSource(self, name):
        dstype = None
        record = None
        try:
            dsource = self.__nexusconfig_device.dataSources([str(name)])
        except:
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
                    record = self.__getRecord(ds)
        return name, dstype, record

    def __appendNode(self, node, dss, mode, counter, nxtype=None, shape=None):
        prefix = '__unnamed__'
        dslist = self.__checkNode(node)
        fname = None
        for (name, dstype, record) in dslist:
            if name:
                if name not in dss:
                    dss[name] = []
                dss[name].append((str(mode), str(dstype) if dstype else None,
                                  str(record) if record else None, nxtype,
                                  shape))
            elif node.nodeName == 'datasource':
                name = prefix + str(counter)
                while name in dss.keys():
                    name = prefix + str(counter)
                    counter = counter + 1
                dss[name] = []
                dss[name].append((str(mode), str(dstype) if dstype else None,
                                  str(record) if record else None, nxtype,
                                  shape))
            if not fname:
                fname = name

        return (fname, counter)

    @classmethod
    def __getShape(cls, node):
        shape = None
        rank = int(node.attributes["rank"].value)
        shape = [None] * rank
        dims = node.getElementsByTagName("dim")
        for dim in dims:
            index = int(dim.attributes["index"].value)
            try:
                value = int(dim.attributes["value"].value)
            except:
                value = dim.attributes["value"].value
            shape[index - 1] = value
        return shape

    def __getDataSourceAttributes(self, cp):
        xmlc = self.__nexusconfig_device.components([cp])
        names = []
        if not len(xmlc) > 0:
            return names
        return self.__getXMLAttributes(xmlc[0])

    def __getDataSetAttributes(self, cps, cfvars=None):
        if cfvars:
            self.__nexusconfig_device.variables = cfvars
        self.__nexusconfig_device.createConfiguration(cps)
        cpxml = str(self.__nexusconfig_device.xmlstring)
        names = []
        if not len(cpxml) > 0:
            return names
        return self.__getXMLAttributes(cpxml)

    def __getXMLAttributes(self, cpxml):
        indom = xml.dom.minidom.parseString(cpxml)
        strategy = indom.getElementsByTagName("strategy")
        counter = 1
        dss = {}

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
                    name, counter = self.__appendNode(
                        nxt, dss, mode, counter, nxtype, shape)
                    nxt = nxt.nextSibling

                prev = sg.previousSibling
                while prev and not name:
                    name, counter = self.__appendNode(
                        prev, dss, mode, counter, nxtype, shape)
                    prev = prev.previousSibling

        return dss
