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

""" NeXus metadata of selector profiles for BLISS scans

The descriptive part of the NeXus configuration selected by NXSRecSelector,
i.e. its INIT and FINAL fields, is added to BLISS scans as user scan
metadata, so the BLISS writer stores it in the scan entry.  STEP fields
are not written, the scan data are stored by BLISS itself.

In a BLISS session::

    from nxsrecconfig.BlissScanMeta import NXSScanMeta
    nxsmeta = NXSScanMeta()     # the selector module with the null backend
    nxsmeta.register()

The profile of the active BLISS measurement group is used by default.

The INIT fields are evaluated when the scan starts and the FINAL fields
when the scan ends, by NXSDataWriter (:mod:`nxswriter`) with the ``h5map``
writer of :mod:`nxstools`, which builds the NeXus tree in memory.
Links to the written fields are kept, links to STEP fields are dropped.
"""

import base64
import datetime
import json
import logging
import posixpath

import numpy

from .WriterConfiguration import WriterConfiguration, NumpyEncoder


#: (:obj:`list` <:obj:`str`>) fields exported at the start of the scan
START_SKIP = ["STEP", "FINAL"]

#: (:obj:`list` <:obj:`str`>) fields exported at the end of the scan
END_SKIP = ["STEP", "INIT"]


def h5map_value(value):
    """ converts an h5map data item to a value of the BLISS metadata

    :param value: h5map data item
    :type value: `any`
    :returns: value or None for streams and virtual datasets
    :rtype: `any`
    """
    if not isinstance(value, dict):
        return value
    tp = value.get("type")
    if tp == "inline":
        return value.get("value")
    if tp == "inline_b64":
        array = numpy.frombuffer(
            base64.b64decode(value.get("value", "")),
            dtype=numpy.dtype(value["dtype"]))
        return array.reshape(value.get("shape", [])).tolist()
    return None


def h5map_to_nxdict(group):
    """ converts an h5map group to a silx-like NeXus dictionary

    Group attributes are stored as ``@name`` keys, dataset attributes as
    ``dataset@name`` keys and links as ``>name`` keys.

    :param group: h5map group
    :type group: :obj:`dict` <:obj:`str`, `any`>
    :returns: NeXus dictionary
    :rtype: :obj:`dict` <:obj:`str`, `any`>
    """
    nxdict = {}
    for name, value in (group.get("attributes") or {}).items():
        nxdict["@%s" % name] = h5map_value(value)
    for name, child in (group.get("children") or {}).items():
        tp = child.get("type")
        if tp == "group":
            nxdict[name] = h5map_to_nxdict(child)
        elif tp == "dataset":
            value = h5map_value(child.get("value"))
            if value is None:
                continue
            nxdict[name] = value
            for aname, avalue in (child.get("attributes") or {}).items():
                nxdict["%s@%s" % (name, aname)] = h5map_value(avalue)
        elif tp == "soft_link":
            nxdict[">%s" % name] = child["target_path"]
        elif tp == "external_link":
            nxdict[">%s" % name] = "%s::%s" % (
                child["target_file"], child["target_path"])
    return nxdict


def _has(nxdict, path):
    """ checks if a dictionary has an item

    :param nxdict: NeXus dictionary
    :type nxdict: :obj:`dict` <:obj:`str`, `any`>
    :param path: item path relative to the dictionary
    :type path: :obj:`str`
    :returns: True if the item exists
    :rtype: :obj:`bool`
    """
    item = nxdict
    for name in [nm for nm in path.split("/") if nm]:
        if not isinstance(item, dict) or (
                name not in item and ">%s" % name not in item):
            return False
        item = item.get(name, {})
    return True


def _relink(nxdict, entry, root, parents=()):
    """ makes entry links relative and removes dangling links

    The BLISS writer names the scan entry itself, so links to the entry
    of the NeXus configuration become relative.

    :param nxdict: NeXus dictionary of a group in the entry
    :type nxdict: :obj:`dict` <:obj:`str`, `any`>
    :param entry: absolute path of the configuration entry
    :type entry: :obj:`str`
    :param root: NeXus dictionary of the entry
    :type root: :obj:`dict` <:obj:`str`, `any`>
    :param parents: names of the group and its parents in the entry
    :type parents: :obj:`tuple` <:obj:`str`>
    """
    for key in list(nxdict.keys()):
        value = nxdict[key]
        if isinstance(value, dict):
            _relink(value, entry, root, parents + (key,))
        elif key.startswith(">") and "::" not in str(value):
            target = posixpath.normpath(
                posixpath.join("/", *parents, str(value)))
            prefix = entry.rstrip("/") + "/"
            if target.startswith(prefix):
                target = target[len(prefix):]
                if _has(root, target):
                    nxdict[key] = posixpath.relpath(
                        target, posixpath.join(".", *parents))
                    continue
            elif not str(value).startswith("/"):
                if _has(root, target.lstrip("/")):
                    continue
            nxdict.pop(key)


def _prune(nxdict):
    """ removes groups without fields and links

    :param nxdict: NeXus dictionary
    :type nxdict: :obj:`dict` <:obj:`str`, `any`>
    :returns: True if the group has no fields and links
    :rtype: :obj:`bool`
    """
    for key in list(nxdict.keys()):
        if isinstance(nxdict[key], dict) and _prune(nxdict[key]):
            nxdict.pop(key)
    return not any(not key.startswith("@") for key in nxdict.keys())


def entry_metadata(h5map):
    """ provides the content of the NXentry groups of an h5map

    :param h5map: h5map of the file root
    :type h5map: :obj:`dict` <:obj:`str`, `any`>
    :returns: NeXus dictionary with the content of the entries
    :rtype: :obj:`dict` <:obj:`str`, `any`>
    """
    metadata = {}
    for name, child in (h5map.get("children") or {}).items():
        if child.get("type") != "group":
            continue
        nxclass = h5map_value(
            (child.get("attributes") or {}).get("NX_class"))
        if nxclass != "NXentry":
            continue
        content = h5map_to_nxdict(child)
        for key in [ky for ky in content if ky.startswith("@")]:
            content.pop(key)
        _relink(content, "/%s" % name, content)
        _prune(content)
        metadata.update(content)
    return metadata


class NXSScanMeta(object):

    """ BLISS user scan metadata of NXSRecSelector profiles
    """

    def __init__(self, selector=None, profile=None, userdata=None,
                 writerproperties=None, log=None):
        """ constructor

        :param selector: NXSRecSelector device name or proxy,
                         or :class:`nxsrecconfig.Settings.Settings`,
                         the selector module with the null backend if None
        :type selector: :obj:`str` or `any`
        :param profile: profile name or a function of a scan returning it,
                        the active BLISS measurement group if None
        :type profile: :obj:`str` or callable
        :param userdata: user data or a function of a scan returning them,
                         added to the ``UserData`` of the profile
        :type userdata: :obj:`dict` <:obj:`str`, `any`> or callable
        :param writerproperties: properties of NXSDataWriter,
                                 e.g. ``{"addingLogs": False}``
        :type writerproperties: :obj:`dict` <:obj:`str`, `any`>
        :param log: logger with debug, info and warning methods
        :type log: :class:`logging.Logger` or `any`
        """
        #: (:obj:`str` or `any`) selector
        self.__selector = selector
        #: (:obj:`str` or callable) profile name
        self.profile = profile
        #: (:obj:`dict` or callable) user data
        self.userdata = userdata
        #: (:obj:`dict` <:obj:`str`, `any`>) NXSDataWriter properties
        self.writerproperties = dict(writerproperties or {})
        #: (:class:`logging.Logger` or `any`) logger
        self.log = log or logging.getLogger("nxsrecconfig")
        #: (:obj:`dict` <:obj:`int`, `any`>) writers of running scans
        self.__writers = {}
        #: (:class:`bliss.scanning.scan_meta.ScanMeta`) registered scan meta
        self.__scanmeta = None
        #: (:obj:`str`) registered category
        self.__category = None
        #: (:obj:`str`) registered metadata name
        self.__name = None

    @property
    def selector(self):
        """ NXSRecSelector device or module

        :returns: selector
        :rtype: :class:`tango.DeviceProxy` or
                :class:`nxsrecconfig.Settings.Settings`
        """
        if self.__selector is None:
            from .Settings import Settings
            self.__selector = Settings(backend="null")
        elif isinstance(self.__selector, str):
            import tango
            self.__selector = tango.DeviceProxy(self.__selector)
        return self.__selector

    def register(self, scanmeta=None, category="", name="nexdatas"):
        """ registers the metadata in the BLISS user scan metadata

        The empty category merges the metadata into the scan entry.

        :param scanmeta: scan metadata, the user scan metadata if None
        :type scanmeta: :class:`bliss.scanning.scan_meta.ScanMeta`
        :param category: metadata category
        :type category: :obj:`str`
        :param name: metadata name in the category
        :type name: :obj:`str`
        """
        from bliss.scanning.scan_meta import META_TIMING, get_user_scan_meta
        if scanmeta is None:
            scanmeta = get_user_scan_meta()
        self.unregister()
        scanmeta.add_categories([category])
        meta = scanmeta._scan_meta_category(category.lower())
        meta.set(name, self)
        meta.timing = META_TIMING.START | META_TIMING.END
        self.__scanmeta = scanmeta
        self.__category = category.lower()
        self.__name = name

    def unregister(self):
        """ removes the metadata from the BLISS user scan metadata
        """
        if self.__scanmeta is not None:
            meta = self.__scanmeta._scan_meta_category(self.__category)
            if meta is not None:
                meta.remove(self.__name)
        self.__scanmeta = None
        self.__closeAll()

    def __call__(self, scan):
        """ provides the metadata of a scan, called by BLISS

        The first call of a scan opens the entry, i.e. provides INIT fields,
        the second one closes it, i.e. provides FINAL fields.

        :param scan: BLISS scan
        :type scan: :class:`bliss.scanning.scan.Scan`
        :returns: NeXus dictionary
        :rtype: :obj:`dict` <:obj:`str`, `any`>
        """
        if scan is None:
            return None
        if id(scan) in self.__writers:
            return self.end(scan)
        return self.start(scan)

    def __profileName(self, scan):
        """ provides the profile name of a scan

        :param scan: BLISS scan
        :type scan: :class:`bliss.scanning.scan.Scan`
        :returns: profile name or None
        :rtype: :obj:`str`
        """
        if callable(self.profile):
            return self.profile(scan)
        if self.profile:
            return self.profile
        try:
            from bliss.common.measurementgroup import get_active_name
            return get_active_name()
        except Exception:
            return None

    def __userData(self, scan):
        """ provides user data of a scan

        :param scan: BLISS scan
        :type scan: :class:`bliss.scanning.scan.Scan`
        :returns: user data
        :rtype: :obj:`dict` <:obj:`str`, `any`>
        """
        if callable(self.userdata):
            return dict(self.userdata(scan) or {})
        return dict(self.userdata or {})

    def configuration(self, scan_info, profile=None, userdata=None):
        """ creates the NXSDataWriter configuration and its INIT record

        :param scan_info: scan info
        :type scan_info: :obj:`dict` <:obj:`str`, `any`>
        :param profile: profile name, the current profile if None
        :type profile: :obj:`str`
        :param userdata: user data
        :type userdata: :obj:`dict` <:obj:`str`, `any`>
        :returns: XML configuration and the INIT record
        :rtype: (:obj:`str`, :obj:`dict` <:obj:`str`, `any`>)
        """
        selector = self.selector
        wc = WriterConfiguration(selector, log=self.log)
        odd = False
        if profile and str(selector.mntGrp) != profile:
            selector.mntGrp = profile
        if profile and profile not in (
                wc.command("availableProfiles") or []):
            self.log.warning(
                "NXSScanMeta: a profile for '%s' does not exist, "
                "the mandatory components are used" % profile)
            odd = True
        else:
            wc.command("fetchProfile")
        wc.conf = wc.serverVar("profileConfiguration", {}, True)
        wc.oddmntgrp = odd

        serialno = scan_info.get("scan_nb", 0) or 0
        title = scan_info.get("title", "")
        filename = scan_info.get("filename", "") or ""
        variables = wc.variables
        variables["serialno"] = "_%05i" % int(serialno)
        variables["scan_id"] = serialno
        variables["scan_title"] = title
        variables["filename"] = filename
        variables["measurement_group"] = profile or ""
        data = {
            "serialno": serialno,
            "scan_title": title,
            "title": title,
            "filename": filename,
            "start_time": scan_info.get("start_time", ""),
        }
        for key in ["npoints", "count_time"]:
            if scan_info.get(key) is not None:
                variables[key] = scan_info[key]
                data[key] = scan_info[key]

        udata = wc.confVar("UserData", None, True)
        udata = dict(udata) if isinstance(udata, dict) else {}
        udata.update(userdata or {})
        envRec = {
            "datadesc": [{"name": str(name), "shape": [], "dtype": "float64"}
                         for name in (scan_info.get("channels") or {})],
        }
        try:
            xml = wc.create(envRec, udata)
        finally:
            try:
                wc.removeDynamicComponent()
            except Exception as e:
                self.log.warning("NXSScanMeta: %s" % str(e))
        data.update(udata)
        return xml, {"data": data}

    def __writer(self, filename, xml, record):
        """ opens an NXSDataWriter entry in memory

        :param filename: file name
        :type filename: :obj:`str`
        :param xml: XML configuration
        :type xml: :obj:`str`
        :param record: INIT record
        :type record: :obj:`dict` <:obj:`str`, `any`>
        :returns: NXSDataWriter
        :rtype: :class:`nxswriter.TangoDataWriter.TangoDataWriter`
        """
        from nxswriter.TangoDataWriter import TangoDataWriter
        writer = TangoDataWriter()
        writer.addingLogs = False
        for key, value in self.writerproperties.items():
            if hasattr(writer, key):
                setattr(writer, key, value)
        writer.writer = "h5map"
        writer.fileName = filename or "nxsscanmeta.nxs"
        writer.openFile()
        try:
            writer.xmlsettings = xml
            writer.jsonrecord = json.dumps(record, cls=NumpyEncoder)
            writer.openEntry()
        except Exception:
            writer.closeFile()
            raise
        return writer

    def start(self, scan):
        """ opens the entry and provides its INIT fields

        :param scan: BLISS scan
        :type scan: :class:`bliss.scanning.scan.Scan`
        :returns: NeXus dictionary
        :rtype: :obj:`dict` <:obj:`str`, `any`>
        """
        # entries of scans which have not ended
        self.__closeAll()
        scan_info = dict(scan.scan_info)
        xml, record = self.configuration(
            scan_info, self.__profileName(scan), self.__userData(scan))
        writer = self.__writer(scan_info.get("filename"), xml, record)
        self.__writers[id(scan)] = (writer, record)
        return entry_metadata(writer.getFile().h5map(skip=START_SKIP))

    def end(self, scan):
        """ closes the entry and provides its FINAL fields

        :param scan: BLISS scan
        :type scan: :class:`bliss.scanning.scan.Scan`
        :returns: NeXus dictionary
        :rtype: :obj:`dict` <:obj:`str`, `any`>
        """
        writer, record = self.__writers.pop(id(scan))
        try:
            data = record["data"]
            data["end_time"] = scan.scan_info.get("end_time") or \
                datetime.datetime.now().astimezone().isoformat()
            writer.jsonrecord = json.dumps(record, cls=NumpyEncoder)
            writer.closeEntry()
            return entry_metadata(writer.getFile().h5map(skip=END_SKIP))
        finally:
            writer.closeFile()

    def __closeAll(self):
        """ closes writers of all scans
        """
        writers = self.__writers
        self.__writers = {}
        for writer, _ in writers.values():
            try:
                writer.closeFile()
            except Exception as e:
                self.log.warning("NXSScanMeta: %s" % str(e))
