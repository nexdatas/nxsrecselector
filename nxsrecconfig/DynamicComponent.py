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

"""  Dynamic Component """

import json
import sys
import PyTango
import lxml.etree
import xml.etree.ElementTree as et
from lxml.etree import XMLParser

from .Utils import Utils, TangoUtils, PoolUtils


class DynamicComponent(object):

    """ Creates dynamic component
        of given component """

    def __init__(self, nexusconfig_device,
                 defaultpath="/$var.entryname#'scan'$var.serialno:NXentry/"
                 "NXinstrument/collection"):
        """ constructor

        :param nexusconfig_device: configserver configuration server
        :type  nexusconfig_device: :obj:`PyTango.DeviceProxy` \
             or :class:`nxsconfigserver.XMLConfigurator.XMLConfigurator`
        :param defaultpath:  default dynamic component path
        :type defaultpath: :obj:`str`
        """
        #: (:class:`PyTango.DeviceProxy` \
        #: or :class:`nxsconfigserver.XMLConfigurator.XMLConfigurator`) \
        #:    configuration server
        self.__nexusconfig_device = nexusconfig_device

        #: (:obj:`list` <:obj:`dict` <:obj:`str` , `any`> >) \
        #:    step datasources
        self.__stepdsourcesDict = []
        #: (:obj:`list` <:obj:`str`>) step datasources
        self.__stepdsources = []
        #: (:obj:`list` <:obj:`str`>) init datasources
        self.__initdsources = []
        #: (:obj:`str`) default dynamic component name
        self.__defaultCP = "__dynamic_component__"
        #: (:obj:`str`) dynamic component name
        self.__dynamicCP = ""
        #: (:obj:`dict` <:obj:`str` , :obj:`str`> ) \
        #:       alias label dictionary
        self.__nexuslabels = {}
        #: (:obj:`dict` <:obj:`str` , :obj:`str`> ) \
        #:       alias path dictionary
        self.__nexuspaths = {}
        #: (:obj:`dict` <:obj:`str` , :obj:`bool`> ) \
        #:       alias link dictionary
        self.__nexuslinks = {}
        #: (:obj:`dict` <:obj:`str` , :obj:`str`> ) \
        #:       alias nexus types dictionary
        self.__nexustypes = {}
        #: (:obj:`dict` <:obj:`str` , :obj:`list` <:obj:`int`> > ) \
        #:       alias nexus types dictionary
        self.__nexusshapes = {}

        #: (:class:`PyTango.Database` ) pytango database server
        self.__db = PyTango.Database()

        #: (:obj:`str`) default dynamic component path
        self.__ldefaultpath = defaultpath
        #: (:obj:`str`) standard dynamic component path
        self.__defaultpath = defaultpath
        #: (:obj:`bool`) standard dynamic link flag
        self.__links = True
        #: (:obj:`bool`) standard dynamic link flag for INIT strategy
        self.__ilinks = False

        #: (:obj:`dict` <:obj:`str` , :obj:`str`> ) \
        #:    map of numpy types : NEXUS
        self.__npTn = {"float32": "NX_FLOAT32", "float64": "NX_FLOAT64",
                       "float": "NX_FLOAT32", "double": "NX_FLOAT64",
                       "int": "NX_INT", "int64": "NX_INT64",
                       "int32": "NX_INT32", "int16": "NX_INT16",
                       "int8": "NX_INT8", "uint64": "NX_UINT64",
                       "uint32": "NX_UINT32", "uint16": "NX_UINT16",
                       "uint8": "NX_UINT8", "uint": "NX_UINT64",
                       "string": "NX_CHAR", "bool": "NX_BOOLEAN"}

    def __get_alias(self, name):
        """ provides a device alias

        :param name: device name
        :type name: :obj:`str`
        :returns: device alias
        :rtype: :obj:`str`
        """
        if name.startswith("tango://"):
            name = name[8:]
        # if name does not contain a "/" it's probably an alias
        if name.find("/") == -1:
            return name

        # haso107klx:10000/expchan/hasysis3820ctrl/1
        if name.find(':') >= 0:
            lst = name.split("/")
            name = "/".join(lst[1:])
        return self.__db.get_alias(name)

    def setStepDictDSources(self, dctlist):
        """ sets user datasources with type and shape

        :param dctlist: json list of parameter dictionaries
               [{"name": <dsname>, "dtype": <num_type>, "shape":<list>}, ...]
        :type dctlist: :obj:`str`
        """
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

    def setStepDSources(self, dsources):
        """ sets step datasources

        :param dsources: list of step datasources
        :type dsources: :obj:`list` <:obj:`str`>
        """
        self.__stepdsources = list(dsources)
        if not isinstance(self.__stepdsources, list):
            self.__stepdsources = []

    #
    def setInitDSources(self, dsources):
        """ sets init datasources

        :param dsources: list of init datasources
        :type dsources: :obj:`list` <:obj:`str`>
        """
        self.__initdsources = list(dsources)
        if not isinstance(self.__initdsources, list):
            self.__initdsources = []

    #
    def setLabelParams(self, labels, paths, links, types, shapes):
        """ sets label parameters for specific dynamic components

        :param labels: label dictionaries
        :type labels: :obj:`dict` <:obj:`str` , :obj:`str`>
        :param paths: nexus path dictionaries
        :type paths: :obj:`dict` <:obj:`str` , :obj:`str`>
        :param links: link dictionaries
        :type links: :obj:`dict` <:obj:`str` , :obj:`bool`>
        :param types: nexus type dictionaries
        :type types: :obj:`dict` <:obj:`str` , :obj:`str`>
        :param shapes: data shape dictionaries
        :type shapes: :obj:`dict` <:obj:`str` , :obj:`list` <:obj:`int`> >
        """
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

    def setDefaultLinkPath(self, dynamicLinks, dynamicPath,
                           dynamicInitLinks=None):
        """ sets default nexus path and link flag for dynamic components

        :brief: if dynamicPath is None or "" it is reset to default one
        :param dynamicPath: nexus default path
        :type dynamicPath: :obj:`str`
        :param dynamicLinks: default link flag
        :type dynamicLinks: :obj:`bool`
        :param dynamicInitLinks: default link flag
        :type dynamicInitLinks: :obj:`bool`
        """
        self.__links = dynamicLinks
        self.__ilinks = dynamicInitLinks
        self.__defaultpath = dynamicPath
        if not self.__defaultpath:
            self.__defaultpath = self.__ldefaultpath

    def __shapeFromTango(self, ds):
        """ provices datasource shape and NeXus type from Tango device

        :param ds: datasource name
        :type ds: :obj:`str`
        :returns: (shape, NeXus type) tuple
        :returns: (:obj:`list` <:obj:`int`>, :obj:`str`) tuple
        """
        nxtype = None
        shape = None
        dstype = ds.get("type")
        if dstype == 'TANGO':
            source = Utils.tostr(Utils.getRecord(ds))
            shape, dt, _ = TangoUtils.getShapeTypeUnit(source)
            nxtype = self.__npTn[dt] \
                if dt in self.__npTn.keys() else nxtype
        return shape, nxtype

    def __createSardanaNodes(self, created, definition):
        """ creates XML nodes for sardana devices

        :param created: list of created devices
        :type created: :obj:`list` <:obj:`str`>
        :param definition: definition node
        :type definition: :class:`lxml.etree.Element`
        """
        for dd in self.__stepdsourcesDict:
            alias = self.__get_alias(Utils.tostr(dd["name"]))
            path, field = self.__getPathField(
                self.__nexuspaths, self.__nexuslabels,
                alias, self.__defaultpath)
            link = self.__getProp(
                self.__nexuslinks, self.__nexuslabels,
                alias, self.__links)
            (parent, nxdata) = self.__createGroupTree(
                definition, path, link)
            created.append(alias)
            nxtype = self.__npTn[dd["dtype"]] \
                if dd["dtype"] in self.__npTn.keys() else 'NX_CHAR'
            self.__createField(
                parent, field, nxtype, alias,
                dd["name"], dd["shape"], dstype='CLIENT')
            if link:
                self.__createLink(nxdata, path, field)

    def __createNonSardanaNodes(self, created, avds, definition,
                                strategy="STEP"):
        """ creates XML nodes for non sardana devices

        :param created: list of created devices
        :type created: :obj:`list` <:obj:`str`>
        :param avds: available datasources
        :type avds: :obj:`list` <:obj:`str`>
        :param definition: definition node
        :type definition: :class:`lxml.etree.Element`
        """
        dsources = self.__initdsources \
            if strategy == 'INIT' else self.__stepdsources
        for ds in dsources:
            if ds not in created:
                path, field = self.__getPathField(
                    self.__nexuspaths, self.__nexuslabels,
                    ds, self.__defaultpath)

                link = self.__getProp(
                    self.__nexuslinks, self.__nexuslabels, ds,
                    self.__ilinks if strategy == 'INIT'
                    else self.__links)
                (parent, nxdata) = self.__createGroupTree(
                    definition, path, link)
                created.append(ds)

                shape, nxtype = None, 'NX_CHAR'
                if ds in avds:
                    dsource = TangoUtils.command(
                        self.__nexusconfig_device, "dataSources",
                        [Utils.tostr(ds)])
                    if sys.version_info > (3,):
                        root = et.fromstring(
                            bytes(dsource[0], "UTF-8"),
                            parser=XMLParser(collect_ids=False))
                    else:
                        root = et.fromstring(
                            dsource[0],
                            parser=XMLParser(collect_ids=False))
                    dss = root.findall(".//datasource")
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
                        parent, field, nxtype, ds,
                        dsnode=dss[0], shape=shape, strategy=strategy)
                else:
                    self.__createField(parent, field, nxtype, ds,
                                       ds, shape, strategy=strategy)
                if link:
                    self.__createLink(nxdata, path, field)

    def create(self):
        """ creates dynamic component

        :returns: dynanic component name
        :rtype: :obj:`str`
        """
        cps = TangoUtils.command(self.__nexusconfig_device,
                                 "availableComponents")
        name = self.__defaultCP
        while name in cps:
            name = name + "x"
        self.__dynamicCP = name

        definition = lxml.etree.Element("definition")
        avds = TangoUtils.command(self.__nexusconfig_device,
                                  "availableDataSources")

        created = []
        self.__createSardanaNodes(created, definition)
        self.__createNonSardanaNodes(created, avds, definition, 'STEP')
        self.__createNonSardanaNodes(created, avds, definition, 'INIT')

        xmls = Utils.tostr(
            lxml.etree.tostring(
                definition, encoding='utf8',
                method='xml', pretty_print=True))
        if xmls.startswith("<?xml"):
            self.__nexusconfig_device.xmlstring = xmls
        else:
            self.__nexusconfig_device.xmlstring = \
                "<?xml version='1.0' encoding='utf8'?>\n" + xmls

        TangoUtils.command(self.__nexusconfig_device, "storeComponent",
                           Utils.tostr(self.__dynamicCP))
#        print("Dynamic Component:\n%s" % root.toprettyxml(indent="  "))

        return self.__dynamicCP

    @classmethod
    def __getProp(cls, nexusprop, nexuslabels, name, default):
        """ gets the property value for the given datasource

        :param nexusprop: nexus property dictionary
        :type nexusprop: :obj:`dict` <:obj:`str` , :`any`>
        :param nexuslabel: nexus label dictionary
        :type nexuslabels: :obj:`dict` <:obj:`str` , :obj:`str`>
        :param default: default value if property is not defined
        :type default: `any`
        :returns: propery value
        :rtype: `any`
        """
        prop = nexusprop.get(nexuslabels.get(name, ""), None)
        if prop is None:
            prop = nexusprop.get(name, default)
        return prop

    @classmethod
    def __getPathField(cls, nexuspaths, nexuslabels, alias, defaultpath):
        """ gets the Nexus path and for the given datasource

        :param nexuspaths: nexus property path dictionary
        :type nexuspaths: :obj:`dict` <:obj:`str` , :obj:`str`>
        :param nexuslabels: nexus label dictionary
        :type nexuslabels: :obj:`dict` <:obj:`str` , :obj:`str`>
        :param alias : datasource alias
        :type alias : :obj:`str`
        :param defaultpath: default path if path is not defined
        :type defaultpath: :obj:`str`
        :returns: (path, fieldname)
        :rtype: (:obj:`str` , :obj:`str`)
        """
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
    def __createLink(cls, entry, path, name):
        """ creates XML node for nexus link

        :param root: root node
        :type root: :class:`lxml.etree.Element`
        :param entry: entry node
        :type entry: :class:`lxml.etree.Element`
        :param path: nexus path
        :type path: :obj:`str`
        :param name: link name
        :type name: :obj:`str`
        """
        if name is not None and entry is not None:
            link = lxml.etree.Element("link")
            entry.append(link)
            link.attrib["target"] = "%s/%s" % (path, name)
            link.attrib["name"] = name

    @classmethod
    def __findDataSource(cls, name):
        """ finds datasource details:
        (attribute name, device name, host, port) tuple

        :param name: datasource name
        :type name: :obj:`str`
        :returns: (attribute name, device name, host, port) tuple
        :rtype: (:obj:`str`, :obj:`str`, :obj:`str`)
        """
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
    def __createField(cls, parent, fname, nxtype, sname,
                      record=None, shape=None, dsnode=None,
                      strategy='STEP', dstype=None):
        """ creates XML node for NeXus field

        :param parent: parent node
        :type parent: :class:`lxml.etree.Element`
        :param fname: field name
        :type fname: :obj:`str`
        :param nxtype: field NeXus type
        :type nxtype: :obj:`str`
        :param sname: data source name
        :type sname: :obj:`str`
        :param record: record attribute
        :type record: :obj:`str`
        :param shape: field shape
        :type shape: :obj:`list`< :obj:`int`>:
        :param dsnode: datasource node
        :type dsnode: :obj:`str`
        :param strategy: strategy mode
        :type strategy: :obj:`str`
        :param dstype: datasource type
        :type dstyp: :obj:`str`
        """
        field = lxml.etree.Element("field")
        parent.append(field)
        field.attrib["type"] = nxtype
        field.attrib["name"] = fname

        strategynode = lxml.etree.Element("strategy")
        field.append(strategynode)
        strategynode.attrib["mode"] = strategy

        if dsnode is not None:
            dsource = dsnode
        else:
            if dstype == 'CLIENT' and record:
                device = None
                attr = None
            else:
                (attr, device, host, port) = cls.__findDataSource(sname)
            if device and attr:
                dsource = lxml.etree.Element("datasource")
                dsource.attrib["name"] = sname
                dsource.attrib["type"] = "TANGO"
                dev = lxml.etree.Element("device")
                dsource.append(dev)
                dev.attrib["member"] = "attribute"
                dev.attrib["name"] = device
                if host and port:
                    dev.attrib["hostname"] = host
                    dev.attrib["port"] = port
                rec = lxml.etree.Element("record")
                dsource.append(rec)
                rec.attrib["name"] = attr
            else:
                dsource = lxml.etree.Element("datasource")
                dsource.attrib["name"] = sname
                dsource.attrib["type"] = "CLIENT"
                rec = lxml.etree.Element("record")
                dsource.append(rec)
                rec.attrib["name"] = record

        field.append(dsource)
        if shape:
            dm = lxml.etree.Element("dimensions")
            dm.attrib["rank"] = Utils.tostr(len(shape))
            field.append(dm)
            for i in range(len(shape)):
                dim = lxml.etree.Element("dim")
                dm.append(dim)
                dim.attrib["index"] = Utils.tostr(i + 1)
                dim.attrib["value"] = Utils.tostr(shape[i])

    def remove(self, name):
        """ removes dynamic component

        :param name: dynamic component name
        :type name: :obj:`str`
        """
        if self.__defaultCP not in name:
            raise Exception(
                "Dynamic component name should contain: %s" % self.__defaultCP)
        cps = TangoUtils.command(self.__nexusconfig_device,
                                 "availableComponents")
        if name in cps:
            TangoUtils.command(self.__nexusconfig_device,
                               "deleteComponent", Utils.tostr(name))

    @classmethod
    def __createGroupTree(cls, definition, path, links=False):
        """ creates group tree

        :param definition: definition node
        :type definition: :class:`lxml.etree.Element`
        :param path: NeXus path
        :type path: :obj:`str`
        :param links: if NXdata should be created
        :type links: :obj:`bool`
        :returns (last group node, nxdata group node) tuple
        :rtype (:class:`lxml.etree.Element`, :class:`lxml.etree.Element`)
        """
        spath = path.split('/')
        entry = None
        parent = definition
        nxdata = None
        for dr in spath:
            if dr.strip():
                node = lxml.etree.Element("group")
                parent.append(node)
                if entry is None:
                    entry = node

                w = dr.split(':')
                if len(w) == 1:
                    if len(w[0]) > 2 and w[0][:2] == 'NX':
                        w.insert(0, w[0][2:])
                    else:
                        w.append("NX" + w[0])
                node.attrib["type"] = w[1]
                node.attrib["name"] = w[0]
                parent = node
        if links and entry is not None:
            nxdata = lxml.etree.Element("group")
            entry.append(nxdata)
            nxdata.attrib["type"] = "NXdata"
            nxdata.attrib["name"] = "data"

        return parent, nxdata
