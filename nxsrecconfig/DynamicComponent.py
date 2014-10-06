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
## \file DynamicComponent.py
# dynamic component creator

"""  Dynamic Component """

import xml.dom.minidom
import json
import PyTango


## NeXus Sardana Recorder settings
class DynamicComponent(object):
    """ Creates dynamic component
        of given component """

    ## constructor
    # \param configserver configuration server name
    def __init__(self, nexusconfig_device):
        self.__nexusconfig_device = nexusconfig_device

        self.__dictDSources = []
        self.__dsources = []
        ## dynamic components
        self.__defaultCP = "__dynamic_component__"
        self.__dynamicCP = ""
        self.__nexuslabels = {}
        self.__nexuspaths = {}
        self.__nexuslinks = {}
        self.__nexustypes = {}
        self.__nexusshapes = {}

        self.__db = PyTango.Database()

        self.__ldefaultpath = \
            "/entry$var.serialno:NXentry/NXinstrument/collection"
        self.__defaultpath = self.__ldefaultpath
        self.__links = True

        ## map of numpy types : NEXUS
        self.__npTn = {"float32": "NX_FLOAT32", "float64": "NX_FLOAT64",
                       "float": "NX_FLOAT32", "double": "NX_FLOAT64",
                       "int": "NX_INT", "int64": "NX_INT64",
                       "int32": "NX_INT32", "int16": "NX_INT16",
                       "int8": "NX_INT8", "uint64": "NX_UINT64",
                       "uint32": "NX_UINT32", "uint16": "NX_UINT16",
                       "uint8": "NX_UINT8", "uint": "NX_UINT64",
                       "string": "NX_CHAR", "bool": "NX_BOOLEAN"}

    ## provides a device alias
    # \param name device name
    # \return device alias
    def __get_alias(self, name):
        # if name does not contain a "/" it's probably an alias
        if name.find("/") == -1:
            return name

        # haso107klx:10000/expchan/hasysis3820ctrl/1
        if name.find(':') >= 0:
            lst = name.split("/")
            name = "/".join(lst[1:])
        return self.__db.get_alias(name)

    ## sets user datasource parameters
    # \params dct list of parameter dictionaries
    def setDictDSources(self, dct):
        self.__dictDSources = []
        jdct = json.loads(dct)

        if isinstance(jdct, list):
            for dd in jdct:
                if "name" not in dd.keys():
                    continue
                self.__dictDSources.append(dd)
                if "dtype" not in dd.keys():
                    self.__dictDSources[-1]["dtype"] = "string"
                if "shape" not in dd.keys():
                    self.__dictDSources[-1]["shape"] = []

    def setDataSources(self, dsources):
        self.__dsources = list(dsources)
        if not isinstance(self.__dsources, list):
            self.__dsources = []

    def setLabelParams(self, labels, paths, links, types, shapes):
        self.__nexuslabels = json.loads(labels)
        if not isinstance(self.__nexuslabels, dict):
            self.__nexuslabels = {}
        self.__nexuspaths = json.loads(paths)
        if not isinstance(self.__nexuspaths, dict):
            self.__nexuspaths = {}
        self.__nexuslinks = json.loads(links)
        if not isinstance(self.__nexuslinks, dict):
            self.__nexuslinks = {}
        self.__nexustypes = json.loads(types)
        if not isinstance(self.__nexustypes, dict):
            self.__nexustypes = {}
        self.__nexusshapes = json.loads(shapes)
        if not isinstance(self.__nexusshapes, dict):
            self.__nexusshapes = {}

    def setLinkParams(self, dynamicLinks, dynamicPath):
        self.__links = dynamicLinks
        self.__defaultpath = dynamicPath
        if not self.__defaultpath:
            self.__defaultpath = self.__ldefaultpath

    ## creates dynamic component
    def create(self):
        cps = self.__nexusconfig_device.availableComponents()
        name = self.__defaultCP
        while name in cps:
            name = name + "x"
        self.__dynamicCP = name

        root = xml.dom.minidom.Document()
        definition = root.createElement("definition")
        root.appendChild(definition)
        avds = self.__nexusconfig_device.availableDataSources()

        created = []
        for dd in self.__dictDSources:
            alias = self.__get_alias(str(dd["name"]))
            path, field = self.__getFieldPath(
                self.__nexuspaths, self.__nexuslabels,
                alias, self.__defaultpath)
            link = self.__getProp(self.__nexuslinks, self.__nexuslabels,
                                      alias, self.__links)
            (parent, nxdata) = self.__createGroupTree(
                root, definition, path, link)
            created.append(alias)
            nxtype = self.__npTn[dd["dtype"]] \
                if dd["dtype"] in self.__npTn.keys() else 'NX_CHAR'
            self.__createField(
                root, parent, field, nxtype, alias,
                dd["name"], dd["shape"])
            if link:
                self.__createLink(root, nxdata, path, field)

        for ds in self.__dsources:
            if ds not in created:
                path, field = self.__getFieldPath(
                    self.__nexuspaths, self.__nexuslabels,
                    ds, self.__defaultpath)
                link = self.__getProp(
                    self.__nexuslinks, self.__nexuslabels, ds, self.__links)
                (parent, nxdata) = self.__createGroupTree(
                    root, definition, path, link)

                nxtype = self.__getProp(
                    self.__nexustypes, self.__nexuslabels, ds, 'NX_CHAR')
                shape = self.__getProp(
                    self.__nexusshapes, self.__nexuslabels, ds, None)
                if ds in avds:
                    dsource = self.__nexusconfig_device.dataSources([str(ds)])
                    indom = xml.dom.minidom.parseString(dsource[0])
                    dss = indom.getElementsByTagName("datasource")
                    self.__createField(root, parent, field, nxtype, ds,
                                       dsnode=dss[0], shape=shape)
                else:
                    self.__createField(root, parent, field, nxtype, ds,
                                       ds, shape)
                if link:
                    self.__createLink(root, nxdata, path, field)

        self.__nexusconfig_device.xmlstring = str(root.toprettyxml(indent=""))
        self.__nexusconfig_device.storeComponent(str(self.__dynamicCP))
#        print("Dynamic Component:\n%s" % root.toprettyxml(indent="  "))

        return self.__dynamicCP

    @classmethod
    def __getProp(cls, nexusprop, nexuslabels, name, default):
        prop = nexusprop.get(nexuslabels.get(name, ""), None)
        if prop is None:
            prop = nexusprop.get(name, default)
        return prop

    @classmethod
    def __getFieldPath(cls, nexuspaths, nexuslabels, alias, defaultpath):
        path = nexuspaths.get(nexuslabels.get(alias, ""), "")
        if not path:
            path = nexuspaths.get(alias, "")
        if path:
            spath = path.split('/')
            field = spath[-1]
            path = '/'.join(spath[:-1]) if len(spath) > 1 else defaultpath
        else:
            path = defaultpath
            field = alias
        return (path, field)

    @classmethod
    def __createLink(cls, root, entry, path, name):
        if name and entry:
            link = root.createElement("link")
            entry.appendChild(link)
            link.setAttribute("target", "%s/%s" % (path, name))
            link.setAttribute("name", name)

    @classmethod
    def __createField(cls, root, parent, fname, nxtype, sname,
                      record=None, shape=None, dsnode=None):
        field = root.createElement("field")
        parent.appendChild(field)
        field.setAttribute("type", nxtype)
        field.setAttribute("name", fname)

        strategy = root.createElement("strategy")
        field.appendChild(strategy)
        strategy.setAttribute("mode", "STEP")

        if dsnode:
            dsource = root.importNode(dsnode, True)
        else:
            dsource = root.createElement("datasource")
            dsource.setAttribute("name", sname)
            dsource.setAttribute("type", "CLIENT")
            rec = root.createElement("record")
            dsource.appendChild(rec)
            rec.setAttribute("name", record)

        field.appendChild(dsource)
        if shape:
            dm = root.createElement("dimensions")
            dm.setAttribute("rank", str(len(shape)))
            field.appendChild(dm)
            for i in range(len(shape)):
                dim = root.createElement("dim")
                dm.appendChild(dim)
                dim.setAttribute("index", str(i + 1))
                dim.setAttribute("value", str(shape[i]))

    def removeDynamicComponent(self, name):
        if self.__defaultCP not in name:
            raise Exception(
                "Dynamic component name should contain: %s" % self.__defaultCP)
        cps = self.__nexusconfig_device.availableComponents()
        if name in cps:
            self.__nexusconfig_device.deleteComponent(str(name))

    @classmethod
    def __createGroupTree(cls, root, definition, path, links=False):
        # create group tree

        spath = path.split('/')
        entry = None
        parent = definition
        nxdata = None
        for dr in spath:
            if dr.strip():
                node = root.createElement("group")
                parent.appendChild(node)
                if not entry:
                    entry = node

                w = dr.split(':')
                if len(w) == 1:
                    if len(w[0]) > 2 and w[0][:2] == 'NX':
                        w.insert(0, w[0][2:])
                    else:
                        w.append("NX" + w[0])
                node.setAttribute("type", w[1])
                node.setAttribute("name", w[0])
                parent = node
        if links:
            nxdata = root.createElement("group")
            entry.appendChild(nxdata)
            nxdata.setAttribute("type", "NXdata")
            nxdata.setAttribute("name", "data")

        return parent, nxdata
