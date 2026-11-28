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

""" NeXus structure of selector profiles in BLISS HDF5 mappings

BLISS describes its scan files by h5maps of :mod:`blissdata`, generated
by ``scan_info_to_h5map`` of :mod:`blisswriter` at the start and at the
end of each scan.  The hook of this module adds the STEP fields of the
NeXus configuration, at their NeXus paths, to the scan entry as soft
links to the datasets written by BLISS, i.e. the scan file has the NeXus
structure of the profile as with NXSDataWriter, and the BLISS one.

The hook is added by ``add_h5map_hook`` of :mod:`bliss.scanning.h5map_hooks`
if BLISS provides it.  Otherwise ``scan_info_to_h5map`` of
:mod:`bliss.scanning.scan` is wrapped by the hook.

The STEP fields are provided by
:class:`nxsrecconfig.BlissScanMeta.NXSScanMeta` registered with
``links=True``, which also provides INIT and FINAL fields::

    from nxsrecconfig.BlissScanMeta import NXSScanMeta
    nxsmeta = NXSScanMeta("p09/nxsrecselector/1")
    nxsmeta.register(links=True)

Overlays are trees of h5map-like dictionaries with groups and
``{"type": "step", "stream": <stream name>}`` items.
"""

import logging
import posixpath

import numpy

from .BlissBackend import channelName
from .BlissDataSources import CONTROLLER


#: (:obj:`list` <:class:`NXSH5MapHook`>) installed hook
_HOOK = []


#: (:obj:`set` <:obj:`str`>) types of h5map items which are not datasets
#:   given by their values
H5TYPES = {"group", "dataset", "external_binary_dataset", "soft_link",
           "external_link", "virtual_dataset"}


def _get(item, key, default=None):
    """ provides a field of an h5map item, i.e. a dictionary or a model

    :param item: h5map item
    :type item: :obj:`dict` or :class:`pydantic.BaseModel`
    :param key: field name
    :type key: :obj:`str`
    :param default: default value
    :type default: `any`
    :returns: field value
    :rtype: `any`
    """
    if isinstance(item, dict):
        return item.get(key, default)
    return getattr(item, key, default)


def itemType(item):
    """ provides the type of an h5map item

    Datasets without attributes can be given by their values.

    :param item: h5map item
    :type item: :obj:`dict` or :class:`pydantic.BaseModel` or `any`
    :returns: item type, e.g. ``group``, ``dataset`` or ``soft_link``
    :rtype: :obj:`str`
    """
    tp = _get(item, "type") if isinstance(item, dict) or \
        hasattr(item, "type") else None
    return tp if tp in H5TYPES else "dataset"


def attributeValue(value):
    """ provides a plain value of an h5map attribute

    :param value: h5map attribute value
    :type value: `any`
    :returns: plain value
    :rtype: `any`
    """
    if hasattr(value, "root"):
        value = value.root
    elif hasattr(value, "value") and not isinstance(value, dict):
        value = value.value
    if isinstance(value, dict):
        value = value.get("value")
    if isinstance(value, numpy.ndarray):
        value = value.item() if value.size == 1 else value.tolist()
    if isinstance(value, list) and len(value) == 1:
        value = value[0]
    if isinstance(value, bytes):
        value = value.decode()
    return value


def streamNames(channels, controller=CONTROLLER):
    """ provides stream names of selector channels and datasources

    :param channels: full names of BLISS scan channels
    :type channels: :obj:`list` <:obj:`str`>
    :param controller: name of the datasource counter controller
    :type controller: :obj:`str`
    :returns: stream names by selector names
    :rtype: :obj:`dict` <:obj:`str`, :obj:`str`>
    """
    names = {}
    for fullname in channels or []:
        fullname = str(fullname)
        names.setdefault(channelName(fullname), fullname)
    for fullname in channels or []:
        fullname = str(fullname)
        prefix, _, short = fullname.rpartition(":")
        if prefix in ("axis", controller) and short:
            # motors and datasource counters keep their names
            names[channelName(short)] = fullname
    return names


def stepOverlay(h5map):
    """ provides the overlay of STEP stream fields of NXentry groups

    Links to STEP fields are STEP fields of the same streams.

    :param h5map: h5map of a file root exported by the nxstools
                  h5map writer with stream names of STEP fields
    :type h5map: :obj:`dict` <:obj:`str`, `any`>
    :returns: overlay of the entry content, None without STEP fields
    :rtype: :obj:`dict` <:obj:`str`, `any`>
    """
    overlay = None
    for name, child in (h5map.get("children") or {}).items():
        if child.get("type") != "group" or attributeValue(
                (child.get("attributes") or {}).get("NX_class")) \
                != "NXentry":
            continue
        streams = {}
        _streamFields(child, "", streams)
        if not streams:
            continue
        tree = _streamTree(child, "/%s" % name, "", streams)
        if tree is not None:
            if overlay is None:
                overlay = {"type": "group", "attributes": {},
                           "children": {}}
            overlay["children"].update(tree["children"])
    return overlay


def _streamValue(item):
    """ provides the stream name of an h5map item

    :param item: h5map item
    :type item: :obj:`dict` or :class:`pydantic.BaseModel` or `any`
    :returns: stream name or None
    :rtype: :obj:`str`
    """
    if itemType(item) != "dataset":
        return None
    value = item
    if _get(item, "type") == "dataset":
        value = _get(item, "value")
    if (isinstance(value, dict) or hasattr(value, "type")) and \
       _get(value, "type") == "stream":
        return _get(value, "stream")
    return None


def _streamFields(group, path, streams):
    """ collects stream fields of a group

    :param group: h5map group
    :type group: :obj:`dict` <:obj:`str`, `any`>
    :param path: group path relative to the entry
    :type path: :obj:`str`
    :param streams: stream names by field paths relative to the entry
    :type streams: :obj:`dict` <:obj:`str`, :obj:`str`>
    """
    for name, child in (group.get("children") or {}).items():
        cpath = "%s/%s" % (path, name) if path else name
        if child.get("type") == "group":
            _streamFields(child, cpath, streams)
        else:
            stream = _streamValue(child)
            if stream:
                streams[cpath] = stream


def _streamTree(group, entry, path, streams):
    """ provides groups, stream fields and links to them of a group

    :param group: h5map group
    :type group: :obj:`dict` <:obj:`str`, `any`>
    :param entry: absolute entry path
    :type entry: :obj:`str`
    :param path: group path relative to the entry
    :type path: :obj:`str`
    :param streams: stream names by field paths relative to the entry
    :type streams: :obj:`dict` <:obj:`str`, :obj:`str`>
    :returns: overlay group or None without stream fields
    :rtype: :obj:`dict` <:obj:`str`, `any`>
    """
    children = {}
    for name, child in (group.get("children") or {}).items():
        cpath = "%s/%s" % (path, name) if path else name
        tp = child.get("type")
        if tp == "group":
            tree = _streamTree(child, entry, cpath, streams)
            if tree is not None:
                children[name] = tree
        elif tp == "soft_link":
            target = posixpath.normpath(posixpath.join(
                entry, path, str(child.get("target_path"))))
            prefix = entry.rstrip("/") + "/"
            if target.startswith(prefix) and \
               target[len(prefix):] in streams:
                children[name] = {"type": "step",
                                  "stream": streams[target[len(prefix):]]}
        elif cpath in streams:
            children[name] = {"type": "step", "stream": streams[cpath]}
    if not children:
        return None
    attributes = {}
    nxclass = attributeValue(
        (group.get("attributes") or {}).get("NX_class"))
    if nxclass:
        attributes["NX_class"] = str(nxclass)
    return {"type": "group", "attributes": attributes, "children": children}


def itemPaths(group, path=""):
    """ provides paths of streams and of other datasets of an h5map group

    :param group: h5map group
    :type group: :obj:`dict` or :class:`pydantic.BaseModel`
    :param path: group path
    :type path: :obj:`str`
    :returns: dataset paths by stream names, paths of other datasets
    :rtype: (:obj:`dict` <:obj:`str`, :obj:`str`>,
             :obj:`list` <:obj:`str`>)
    """
    streams = {}
    datasets = []

    def add(stream, spath):
        if stream not in streams or \
           len(spath.split("/")) < len(streams[stream].split("/")):
            streams[stream] = spath

    for name, child in (_get(group, "children") or {}).items():
        cpath = "%s/%s" % (path, name)
        tp = itemType(child)
        if tp == "group":
            cstreams, cdatasets = itemPaths(child, cpath)
            for stream, spath in cstreams.items():
                add(stream, spath)
            datasets.extend(cdatasets)
        elif tp in ("dataset", "virtual_dataset", "external_binary_dataset"):
            stream = _streamValue(child)
            if stream:
                add(stream, cpath)
            else:
                datasets.append(cpath)
    return streams, datasets


def targetPath(stream, streams, datasets):
    """ provides the path of a BLISS dataset of a stream

    Datasets of streams are looked for first, then datasets of the
    stream controller with the stream short name, e.g. string datasource
    values stored as scan metadata of the datasource counter controller.

    :param stream: stream name
    :type stream: :obj:`str`
    :param streams: dataset paths by stream names
    :type streams: :obj:`dict` <:obj:`str`, :obj:`str`>
    :param datasets: paths of other datasets
    :type datasets: :obj:`list` <:obj:`str`>
    :returns: dataset path or None
    :rtype: :obj:`str`
    """
    if stream in streams:
        return streams[stream]
    controller, _, short = stream.rpartition(":")
    if controller and short:
        suffix = "/%s/%s" % (controller.split(":")[-1], short)
        found = sorted((path for path in datasets if path.endswith(suffix)),
                       key=lambda path: len(path.split("/")))
        if found:
            return found[0]
    return None


class DictItems(object):

    """ creates h5map items as dictionaries
    """

    def group(self, attributes):
        """ creates a group

        :param attributes: group attributes
        :type attributes: :obj:`dict` <:obj:`str`, `any`>
        :returns: h5map group
        :rtype: :obj:`dict` <:obj:`str`, `any`>
        """
        return {"type": "group", "attributes": dict(attributes),
                "children": {}}

    def link(self, target):
        """ creates a soft link

        :param target: target path
        :type target: :obj:`str`
        :returns: h5map soft link
        :rtype: :obj:`dict` <:obj:`str`, `any`>
        """
        return {"type": "soft_link", "target_path": target}


class ModelItems(object):

    """ creates h5map items as :mod:`blissdata.h5map` models
    """

    def __init__(self, module=None):
        """ constructor

        :param module: h5map model module, :mod:`blissdata.h5map` if None
        :type module: :obj:`module`
        """
        if module is None:
            from blissdata import h5map as module
        #: (:obj:`module`) h5map model module
        self.module = module

    def group(self, attributes):
        """ creates a group

        :param attributes: group attributes
        :type attributes: :obj:`dict` <:obj:`str`, `any`>
        :returns: h5map group
        :rtype: :class:`blissdata.h5map.Group`
        """
        return self.module.Group(
            attributes={key: self.module.InlineRaw(value)
                        for key, value in attributes.items()},
            children={})

    def link(self, target):
        """ creates a soft link

        :param target: target path
        :type target: :obj:`str`
        :returns: h5map soft link
        :rtype: :class:`blissdata.h5map.SoftLink`
        """
        return self.module.SoftLink(target_path=target)


def applyOverlay(group, overlay, streams, datasets, path="", log=None,
                 items=None):
    """ adds overlay fields as soft links to an h5map group

    Existing items of the group are kept.

    :param group: h5map group
    :type group: :obj:`dict` or :class:`blissdata.h5map.Group`
    :param overlay: overlay group
    :type overlay: :obj:`dict` <:obj:`str`, `any`>
    :param streams: dataset paths by stream names
    :type streams: :obj:`dict` <:obj:`str`, :obj:`str`>
    :param datasets: paths of other datasets
    :type datasets: :obj:`list` <:obj:`str`>
    :param path: group path
    :type path: :obj:`str`
    :param log: logger
    :type log: :class:`logging.Logger`
    :param items: item factory, :class:`DictItems` if None
    :type items: :class:`DictItems` or :class:`ModelItems`
    :returns: number of added links
    :rtype: :obj:`int`
    """
    items = items or DictItems()
    added = 0
    children = _get(group, "children")
    for name, item in overlay.get("children", {}).items():
        cpath = "%s/%s" % (path, name)
        if item.get("type") == "group":
            child = children.get(name)
            if child is None:
                child = items.group(item.get("attributes") or {})
                nadded = applyOverlay(
                    child, item, streams, datasets, cpath, log, items)
                if nadded:
                    children[name] = child
                added += nadded
            elif itemType(child) == "group":
                added += applyOverlay(
                    child, item, streams, datasets, cpath, log, items)
            elif log:
                log.debug("nxsrecconfig: %s exists, skipped" % cpath)
        elif name not in children:
            target = targetPath(item["stream"], streams, datasets)
            if target and target != cpath:
                children[name] = items.link(target)
                added += 1
    return added


def addProfileLinks(mapping, overlay, log=None, items=None):
    """ adds STEP fields of a profile to NXentry groups of an h5map

    :param mapping: h5map of a file root
    :type mapping: :obj:`dict` or :class:`blissdata.h5map.Group`
    :param overlay: overlay of the entry content
    :type overlay: :obj:`dict` <:obj:`str`, `any`>
    :param log: logger
    :type log: :class:`logging.Logger`
    :param items: item factory, :class:`DictItems` if None
    :type items: :class:`DictItems` or :class:`ModelItems`
    :returns: number of added links
    :rtype: :obj:`int`
    """
    added = 0
    for name, child in (_get(mapping, "children") or {}).items():
        if itemType(child) != "group" or attributeValue(
                (_get(child, "attributes") or {}).get("NX_class")) \
                != "NXentry":
            continue
        entry = "/%s" % name
        streams, datasets = itemPaths(child, entry)
        added += applyOverlay(
            child, overlay, streams, datasets, entry, log, items)
    return added


def scanKey(scan_info):
    """ provides the key of a scan

    :param scan_info: scan info
    :type scan_info: :obj:`dict` <:obj:`str`, `any`>
    :returns: file name and scan number
    :rtype: (:obj:`str`, :obj:`int`)
    """
    return (posixpath.normpath(str(scan_info.get("filename") or "")),
            scan_info.get("scan_nb"))


class NXSH5MapHook(object):

    """ hook of the BLISS h5map generation
    """

    def __init__(self, log=None):
        """ constructor

        :param log: logger
        :type log: :class:`logging.Logger`
        """
        #: (:class:`logging.Logger`) logger
        self.log = log or logging.getLogger("nxsrecconfig")
        #: (:obj:`dict` <:obj:`tuple`, :obj:`dict`>) overlays by scans
        self.overlays = {}
        #: (callable) the original h5map generator
        self.original = None
        #: (:obj:`module`) module of the h5map generator
        self.module = None
        #: (:obj:`module`) module of the BLISS h5map hooks, i.e.
        #:     :mod:`bliss.scanning.h5map_hooks`
        self.registry = None

    def setOverlay(self, scan_info, overlay):
        """ sets the overlay of a scan

        :param scan_info: scan info
        :type scan_info: :obj:`dict` <:obj:`str`, `any`>
        :param overlay: overlay of the entry content or None
        :type overlay: :obj:`dict` <:obj:`str`, `any`>
        """
        key = scanKey(scan_info)
        if overlay:
            self.overlays[key] = overlay
        else:
            self.overlays.pop(key, None)

    def apply(self, scan_info, mappings, end=None):
        """ adds profile links to the h5maps of a scan

        :param scan_info: scan info
        :type scan_info: :obj:`dict` <:obj:`str`, `any`>
        :param mappings: h5map models or dictionaries by file names,
                         updated in place
        :type mappings: :obj:`dict` <:obj:`str`, `any`>
        :param end: the last h5maps of the scan,
                    the scan info with ``end_reason`` if None
        :type end: :obj:`bool`
        :returns: updated mappings
        :rtype: :obj:`dict` <:obj:`str`, `any`>
        """
        key = scanKey(scan_info)
        overlay = self.overlays.get(key)
        if end is None:
            end = "end_reason" in scan_info
        if end:
            # the last h5map of the scan
            self.overlays.pop(key, None)
        if not overlay:
            return mappings
        for filename in list(mappings.keys()):
            if posixpath.normpath(str(filename)) != key[0]:
                continue
            mapping = mappings[filename]
            items = DictItems() if isinstance(mapping, dict) \
                else ModelItems()
            addProfileLinks(mapping, overlay, self.log, items)
        return mappings

    def blissHook(self, scan, mappings, timing):
        """ adds profile links to the h5maps of a scan,
            called by :mod:`bliss.scanning.h5map_hooks`

        :param scan: BLISS scan
        :type scan: :class:`bliss.scanning.scan.Scan`
        :param mappings: h5maps by file names, updated in place
        :type mappings: :obj:`dict` <:obj:`str`,
                        :class:`blissdata.h5map.Group`>
        :param timing: ``META_TIMING.START`` or ``META_TIMING.END``
        :type timing: :class:`bliss.scanning.scan_meta.META_TIMING`
        :returns: updated mappings
        :rtype: :obj:`dict` <:obj:`str`, :class:`blissdata.h5map.Group`>
        """
        scan_info = scan.scan_info
        end = getattr(timing, "name", str(timing)) == "END"
        try:
            return self.apply(scan_info, mappings, end)
        except Exception as e:
            self.log.warning(
                "nxsrecconfig: profile links cannot be added: %s" % e)
            if end:
                self.overlays.pop(scanKey(scan_info), None)
            return mappings

    def __call__(self, scan_info, *args, **kwargs):
        """ generates h5maps with profile links

        :param scan_info: scan info
        :type scan_info: :obj:`dict` <:obj:`str`, `any`>
        :returns: h5maps by file names
        :rtype: :obj:`dict` <:obj:`str`, `any`>
        """
        mappings = self.original(scan_info, *args, **kwargs)
        try:
            return self.apply(scan_info, mappings)
        except Exception as e:
            self.log.warning(
                "nxsrecconfig: profile links cannot be added: %s" % e)
            return mappings


def installHook(module=None, log=None, registry=None):
    """ installs the h5map hook in BLISS

    The hook is added to the BLISS h5map hooks if BLISS provides them,
    otherwise ``scan_info_to_h5map`` of the BLISS scan module is wrapped.

    :param module: module with ``scan_info_to_h5map`` to be wrapped,
                   :mod:`bliss.scanning.scan` if None
    :type module: :obj:`module`
    :param log: logger
    :type log: :class:`logging.Logger`
    :param registry: module with ``add_h5map_hook`` and
                     ``remove_h5map_hook``,
                     :mod:`bliss.scanning.h5map_hooks` if available
                     and *module* is None
    :type registry: :obj:`module`
    :returns: the installed hook
    :rtype: :class:`NXSH5MapHook`
    """
    if _HOOK:
        return _HOOK[0]
    hook = NXSH5MapHook(log)
    if registry is None and module is None:
        try:
            from bliss.scanning import h5map_hooks as registry
        except ImportError:
            registry = None
    if registry is not None:
        hook.registry = registry
        registry.add_h5map_hook(hook.blissHook)
    else:
        if module is None:
            import bliss.scanning.scan as module
        hook.module = module
        hook.original = module.scan_info_to_h5map
        module.scan_info_to_h5map = hook
    _HOOK.append(hook)
    return hook


def uninstallHook():
    """ removes the h5map hook from BLISS
    """
    while _HOOK:
        hook = _HOOK.pop()
        if hook.registry is not None:
            hook.registry.remove_h5map_hook(hook.blissHook)
        elif hook.module is not None and \
                hook.module.scan_info_to_h5map is hook:
            hook.module.scan_info_to_h5map = hook.original
