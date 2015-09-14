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
## \file DynamicComponent.py
# dynamic component creator

"""  Dynamic Component """

import xml.dom.minidom
import json
import PyTango

from .Utils import Utils, TangoUtils, PoolUtils


## NeXus Sardana Recorder settings
class DynamicComponent(object):
    """ Creates dynamic component
        of given component """

    ## constructor
    # \param nexusconfig_device configserver configuration server name
    def __init__(self, nexusconfig_device):
        self.__nexusconfig_device = nexusconfig_device

        self.__stepdsourcesDict = []
        self.__stepdsources = []
        self.__initdsources = []
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

    ## sets user datasources with type and shape
    # \param dctlist json list of parameter dictionaries
    #        [{"name": <dsname>, "dtype": <num_type>, "shape":<list>}, ...]
    def setStepDictDSources(self, dctlist):
        self.__stepdsourcesDict = []
        if isinstance(dctlist, list):
            for dct in dctlist:
                if "name" not in dct.keys():
                    continue
                self.__stepdsourcesDict.append(dct)
                if "dtype" not in dct.keys():
                    self.__stepdsourcesDict[-1]["dtype"] = "string"
                if "shape" not in dct.keys():
                    self.__stepdsourcesDict[-1]["shape"] = []

    ## sets step datasources
    # \param dsources list of step datasources
    def setStepDSources(self, dsources):
        self.__stepdsources = list(dsources)
        if not isinstance(self.__stepdsources, list):
            self.__stepdsources = []

    ## sets init datasources
    # \param dsources list of init datasources
    def setInitDSources(self, dsources):
        self.__initdsources = list(dsources)
        if not isinstance(self.__initdsources, list):
            self.__initdsources = []

    ## sets label parameters for specific dynamic components
    # \param labels label dictionaries
    # \param paths nexus path dictionaries
    # \param links link dictionaries
    # \param types nexus type dictionaries
    # \param shapes data shape dictionaries
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

    ## sets default nexus path and link flag for dynamic components
    # \brief if dynamicPath is None or "" it is reset to default one
    # \param dynamicPath nexus default path
    # \param dynamicLinks default link flag
    def setDefaultLinkPath(self, dynamicLinks, dynamicPath):
        self.__links = dynamicLinks
        self.__defaultpath = dynamicPath
        if not self.__defaultpath:
            self.__defaultpath = self.__ldefaultpath

    def __shapeFromTango(self, ds):
        nxtype = None
        dstype = None
        shape = None
        if ds.hasAttribute("type"):
            dstype = ds.attributes["type"].value
        if dstype == 'TANGO':
            source = str(Utils.getRecord(ds))
            shape, dt, _ = TangoUtils.getShapeTypeUnit(source)
            nxtype = self.__npTn[dt] \
                if dt in self.__npTn.keys() else nxtype
        return shape, nxtype

    def __createSardanaNodes(self, created, root, definition):
        for dd in self.__stepdsourcesDict:
            alias = self.__get_alias(str(dd["name"]))
            path, field = self.__getPathField(
                self.__nexuspaths, self.__nexuslabels,
                alias, self.__defaultpath)
            link = self.__getProp(
                self.__nexuslinks, self.__nexuslabels,
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

    def __createNonSardanaNodes(self, created, avds, root, definition,
                                strategy="STEP"):
        dsources = self.__initdsources \
            if strategy == 'INIT' else self.__stepdsources
        for ds in dsources:
            if ds not in created:
                path, field = self.__getPathField(
                    self.__nexuspaths, self.__nexuslabels,
                    ds, self.__defaultpath)

                link = self.__getProp(
                    self.__nexuslinks, self.__nexuslabels, ds,
                    self.__links)
                (parent, nxdata) = self.__createGroupTree(
                    root, definition, path, link)

                shape, nxtype = None, 'NX_CHAR'
                if ds in avds:
                    dsource = TangoUtils.command(
                        self.__nexusconfig_device, "dataSources",
                        [str(ds)])
                    indom = xml.dom.minidom.parseString(dsource[0])
                    dss = indom.getElementsByTagName("datasource")
                    if dss and shape is None:
                        shape, nxtype = self.__shapeFromTango(dss[0])
                        if not nxtype:
                            nxtype = 'NX_CHAR'

                nxtype = self.__getProp(
                    self.__nexustypes, self.__nexuslabels, ds, nxtype)
                shape = self.__getProp(
                    self.__nexusshapes, self.__nexuslabels, ds, shape)

                if ds in avds:
                    self.__createField(
                        root, parent, field, nxtype, ds,
                        dsnode=dss[0], shape=shape, strategy=strategy)
                else:
                    self.__createField(root, parent, field, nxtype, ds,
                                       ds, shape, strategy=strategy)
                if link:
                    self.__createLink(root, nxdata, path, field)

    ## creates dynamic component
    def create(self):
        cps = TangoUtils.command(self.__nexusconfig_device,
                                 "availableComponents")
        name = self.__defaultCP
        while name in cps:
            name = name + "x"
        self.__dynamicCP = name

        root = xml.dom.minidom.Document()
        definition = root.createElement("definition")
        root.appendChild(definition)
        avds = TangoUtils.command(self.__nexusconfig_device,
                                  "availableDataSources")

        created = []
        self.__createSardanaNodes(created, root, definition)
        self.__createNonSardanaNodes(created, avds, root, definition, 'STEP')
        self.__createNonSardanaNodes(created, avds, root, definition, 'INIT')

        self.__nexusconfig_device.xmlstring = str(root.toprettyxml(indent=""))
        TangoUtils.command(self.__nexusconfig_device, "storeComponent",
                      str(self.__dynamicCP))
#        print("Dynamic Component:\n%s" % root.toprettyxml(indent="  "))

        return self.__dynamicCP

    @classmethod
    def __getProp(cls, nexusprop, nexuslabels, name, default):
        prop = nexusprop.get(nexuslabels.get(name, ""), None)
        if prop is None:
            prop = nexusprop.get(name, default)
        return prop

    @classmethod
    def __getPathField(cls, nexuspaths, nexuslabels, alias, defaultpath):
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
        if len(field) > 12 and field[:8] == 'tango://':
            field = field[8:]
        return (path,
                field.replace(" ", "_").replace("/", "_").replace(
                ":", "_").replace(".", "_").replace("\\", "_").replace(
                ";", "_").lower())

    @classmethod
    def __createLink(cls, root, entry, path, name):
        if name and entry:
            link = root.createElement("link")
            entry.appendChild(link)
            link.setAttribute("target", "%s/%s" % (path, name))
            link.setAttribute("name", name)

    @classmethod
    def __findDataSource(cls, name):
        attr = None
        device = None
        host = None
        port = None
        source = None

        sname = name.split("://")
        if name and sname[0] == 'tango' and sname[-1].count('/') > 2:
            source = sname[-1]
        else:
            source = PoolUtils.getSource(name)
        if source:
            arr = source.split("/")
            if len(arr) > 4 and ":" in arr[0]:
                device = "/".join(arr[1:-1])
                attr = arr[-1]
                hat = arr[0].split(":")
                if hat > 1:
                    host = hat[0]
                    port = hat[1]
            elif len(arr) > 3:
                device = "/".join(arr[:-1])
                attr = arr[-1]
        return (attr, device, host, port)

    @classmethod
    def __createField(cls, root, parent, fname, nxtype, sname,
                      record=None, shape=None, dsnode=None,
                      strategy='STEP'):
        field = root.createElement("field")
        parent.appendChild(field)
        field.setAttribute("type", nxtype)
        field.setAttribute("name", fname)

        strategynode = root.createElement("strategy")
        field.appendChild(strategynode)
        strategynode.setAttribute("mode", strategy)

        if dsnode:
            dsource = root.importNode(dsnode, True)
        else:
            (attr, device, host, port) = cls.__findDataSource(sname)
            if device and attr:
                dsource = root.createElement("datasource")
                dsource.setAttribute("name", sname)
                dsource.setAttribute("type", "TANGO")
                dev = root.createElement("device")
                dsource.appendChild(dev)
                dev.setAttribute("member", "attribute")
                dev.setAttribute("name", device)
                if host and port:
                    dev.setAttribute("hostname", host)
                    dev.setAttribute("port", port)
                rec = root.createElement("record")
                dsource.appendChild(rec)
                rec.setAttribute("name", attr)
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

    ## removes dynamic component
    # \param name dynamic component name
    def remove(self, name):
        if self.__defaultCP not in name:
            raise Exception(
                "Dynamic component name should contain: %s" % self.__defaultCP)
        cps = TangoUtils.command(self.__nexusconfig_device,
                            "availableComponents")
        if name in cps:
            TangoUtils.command(self.__nexusconfig_device,
                          "deleteComponent", str(name))

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
        if links and entry:
            nxdata = root.createElement("group")
            entry.appendChild(nxdata)
            nxdata.setAttribute("type", "NXdata")
            nxdata.setAttribute("name", "data")

        return parent, nxdata
