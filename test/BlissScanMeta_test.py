#!/usr/bin/env python
#   This file is part of nexdatas - Tango Server for NeXus data writer
#
#    Copyright (C) 2012-2026 DESY, Jan Kotanski <jkotan@mail.desy.de>
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
# \package test nexdatas
# \file BlissScanMeta_test.py
# unittests for the BLISS user scan metadata of selector profiles
#
import base64
import contextlib
import copy
import enum
import json
import sys
import types
import unittest

import numpy

from nxsrecconfig import BlissH5Map
from nxsrecconfig.BlissScanMeta import (
    NXSScanMeta, h5map_value, h5map_to_nxdict, entry_metadata)

try:
    from WriterConfiguration_test import FakeSelector, Log, source
except ImportError:
    from .WriterConfiguration_test import FakeSelector, Log, source

try:
    from nxswriter.TangoDataWriter import WRITERS
    # nxswriter >= 3.26.0 with nxstools >= 4.73.0
    WRITER = "h5map" in WRITERS
except Exception:
    WRITER = False

try:
    from bliss.scanning.scan_meta import ScanMeta, META_TIMING
    BLISS = True
except Exception:
    BLISS = False


XML = """<?xml version='1.0'?>
<definition>
  <group type="NXentry" name="scan_00012">
    <field name="title" type="NX_CHAR">
      <strategy mode="INIT"/>
      <datasource type="CLIENT" name="title">
        <record name="title"/>
      </datasource>
    </field>
    <field name="end_time" type="NX_DATE_TIME">
      <strategy mode="FINAL"/>
      <datasource type="CLIENT" name="end_time">
        <record name="end_time"/>
      </datasource>
    </field>
    <group type="NXinstrument" name="instrument">
      <group type="NXsource" name="source">
        <field name="name" type="NX_CHAR">PETRA III
          <attribute name="short_name" type="NX_CHAR">P3</attribute>
        </field>
        <field name="energy" type="NX_FLOAT64" units="GeV">
          <strategy mode="INIT"/>
          <datasource type="CLIENT" name="energy">
            <record name="energy"/>
          </datasource>
        </field>
      </group>
      <group type="NXdetector" name="detector">
        <field name="counts" type="NX_INT32">
          <strategy mode="STEP"/>
          <datasource type="CLIENT" name="exp_c01">
            <record name="exp_c01"/>
          </datasource>
        </field>
      </group>
    </group>
    <group type="NXdata" name="data">
      <link name="energy" target="/scan_00012/instrument/source/energy"/>
      <link name="end_time" target="/scan_00012/end_time"/>
      <link name="counts" target="/scan_00012/instrument/detector/counts"/>
    </group>
  </group>
</definition>
"""


class ProfileSelector(FakeSelector):
    """ selector stand-in with profiles """

    def __init__(self, profiles=None, xml=XML, **kwargs):
        FakeSelector.__init__(self, **kwargs)
        self.profiles = profiles or {}
        self.mntGrp = "default"
        self.profileConfiguration = "{}"
        self.xml = xml

    def availableProfiles(self):
        return list(self.profiles.keys())

    def fetchProfile(self):
        self.calls.append(("fetchProfile", self.mntGrp))
        self.profileConfiguration = json.dumps(self.profiles[self.mntGrp])

    def createWriterConfiguration(self, cps):
        FakeSelector.createWriterConfiguration(self, cps)
        return self.xml


class Scan(object):
    """ BLISS scan stand-in """

    def __init__(self, **scan_info):
        self.scan_info = scan_info


def profile(**kwargs):
    conf = {
        "ComponentsFromMntGrp": False,
        "DynamicComponents": True,
        "UserData": json.dumps({"energy": 6.0}),
        "ConfigVariables": json.dumps({"entryname": "scan"}),
    }
    conf.update(kwargs)
    return conf


@contextlib.contextmanager
def fake_scan_meta():
    """ bliss.scanning.scan_meta stand-in with the used API """

    class META_TIMING(enum.Flag):
        START = enum.auto()
        END = enum.auto()
        PREPARED = enum.auto()

    class Category(object):
        def __init__(self, name, metadata, timing):
            self.name = name
            self._metadata = metadata
            self._timing = timing

        @property
        def metadata(self):
            return self._metadata.setdefault(self.name, {})

        @property
        def timing(self):
            return self._timing.setdefault(self.name, META_TIMING.START)

        @timing.setter
        def timing(self, timing):
            self._timing[self.name] = timing

        def set(self, name, values):
            self.metadata[name] = values

        def remove(self, name):
            self.metadata.pop(name, None)

    class ScanMeta(object):
        _CATEGORIES = {"instrument", "positioners", "technique"}

        def __init__(self):
            self._metadata = {}
            self._timing = {}

        @classmethod
        def categories_names(cls):
            return sorted(cls._CATEGORIES)

        @classmethod
        def add_categories(cls, names):
            cls._CATEGORIES.update(s.lower() for s in names)

        @classmethod
        def remove_categories(cls, names):
            cls._CATEGORIES -= {s.lower() for s in names}

        def _scan_meta_category(self, category):
            if category in self._CATEGORIES:
                return Category(category, self._metadata, self._timing)

    module = types.ModuleType("bliss.scanning.scan_meta")
    module.ScanMeta = ScanMeta
    module.META_TIMING = META_TIMING
    module.get_user_scan_meta = ScanMeta
    names = ["bliss", "bliss.scanning", "bliss.scanning.scan_meta"]
    old = {name: sys.modules.get(name) for name in names}
    sys.modules["bliss"] = types.ModuleType("bliss")
    sys.modules["bliss.scanning"] = types.ModuleType("bliss.scanning")
    sys.modules["bliss.scanning.scan_meta"] = module
    try:
        yield module
    finally:
        for name, mod in old.items():
            if mod is None:
                sys.modules.pop(name, None)
            else:
                sys.modules[name] = mod


class BlissScanMetaTest(unittest.TestCase):

    def test_h5map_value(self):
        self.assertEqual(h5map_value("text"), "text")
        self.assertEqual(h5map_value(["a", "b"]), ["a", "b"])
        self.assertEqual(
            h5map_value({"type": "inline", "dtype": "int32",
                         "value": [1, 2]}), [1, 2])
        arr = numpy.array([[1.5, 2.5]], dtype="<f4")
        self.assertEqual(
            h5map_value({"type": "inline_b64", "dtype": "<f4",
                         "shape": [1, 2],
                         "value": base64.b64encode(
                             arr.tobytes()).decode()}),
            [[1.5, 2.5]])
        self.assertEqual(
            h5map_value({"type": "stream", "stream": "diode"}), None)

    def test_h5map_to_nxdict(self):
        h5map = {
            "type": "group",
            "attributes": {"NX_class": "NXsource"},
            "children": {
                "name": {"type": "dataset", "value": "PETRA III",
                         "attributes": {"short_name": "P3"}},
                "energy": {"type": "dataset", "value": {
                    "type": "inline", "dtype": "float64", "value": 6.0}},
                "counts": {"type": "dataset", "value": {
                    "type": "stream", "stream": "exp_c01"}},
                "sub": {"type": "group",
                        "attributes": {"NX_class": "NXcollection"}},
                "lnk": {"type": "soft_link", "target_path": "/a/b"},
                "ext": {"type": "external_link", "target_file": "f.h5",
                        "target_path": "/c"},
            },
        }
        self.assertEqual(h5map_to_nxdict(h5map), {
            "@NX_class": "NXsource",
            "name": "PETRA III",
            "name@short_name": "P3",
            "energy": 6.0,
            "sub": {"@NX_class": "NXcollection"},
            ">lnk": "/a/b",
            ">ext": "f.h5::/c",
        })

    def test_entry_metadata(self):
        def grp(nxclass, children):
            return {"type": "group", "attributes": {"NX_class": nxclass},
                    "children": children}

        def lnk(target):
            return {"type": "soft_link", "target_path": target}

        h5map = grp("NXroot", {
            "nexus_logs": grp("NXcollection", {
                "log": {"type": "dataset", "value": "log"}}),
            "scan_1": grp("NXentry", {
                "title": {"type": "dataset", "value": "ascan"},
                "empty": grp("NXcollection", {
                    "sub": grp("NXcollection", {})}),
                "instrument": grp("NXinstrument", {
                    "source": grp("NXsource", {
                        "energy": {"type": "dataset", "value": 6.0}}),
                    "rel": lnk("source/energy"),
                }),
                "data": grp("NXdata", {
                    "energy": lnk("/scan_1/instrument/source/energy"),
                    "counts": lnk("/scan_1/instrument/detector/counts"),
                    "ext": {"type": "external_link",
                            "target_file": "f.h5", "target_path": "/x"},
                    "other": lnk("/scan_2/title"),
                }),
                "onlydangling": grp("NXdata", {
                    "counts": lnk("/scan_1/instrument/detector/counts"),
                }),
            }),
        })
        self.assertEqual(entry_metadata(h5map), {
            "title": "ascan",
            "instrument": {
                "@NX_class": "NXinstrument",
                "source": {"@NX_class": "NXsource", "energy": 6.0},
                ">rel": "source/energy",
            },
            "data": {
                "@NX_class": "NXdata",
                ">energy": "../instrument/source/energy",
                ">ext": "f.h5::/x",
            },
        })

    @unittest.skipUnless(WRITER, "nxswriter or nxstools not available")
    def test_scan(self):
        selector = ProfileSelector(
            profiles={"mg1": profile()},
            components=["source"],
            cpsources={"source": [source("energy", "INIT"),
                                  source("exp_c01")]})
        log = Log()
        meta = NXSScanMeta(selector, profile="mg1",
                           userdata=lambda scan: {"sample": "water"},
                           log=log)
        scan = Scan(scan_nb=12, title="ascan roby 0 1 2 0.1",
                    filename="/tmp/nxsscanmeta_test.h5",
                    start_time="2026-11-26T10:00:00+01:00",
                    npoints=3, count_time=0.1,
                    channels={"axis:roby": {}, "diode:diode": {}})
        self.assertEqual(meta(None), None)

        init = meta(scan)
        self.assertEqual(selector.mntGrp, "mg1")
        self.assertTrue(("fetchProfile", "mg1") in selector.calls)
        self.assertEqual(init["title"], "ascan roby 0 1 2 0.1")
        self.assertTrue("end_time" not in init)
        source_ = init["instrument"]["source"]
        self.assertEqual(source_["@NX_class"], "NXsource")
        # scalars are stored as in the NXSDataWriter files
        self.assertEqual(source_["energy"], [6.0])
        self.assertEqual(source_["energy@units"], "GeV")
        self.assertEqual(source_["energy@nexdatas_strategy"], "INIT")
        self.assertEqual(source_["name"].strip(), "PETRA III")
        self.assertEqual(source_["name@short_name"], "P3")
        # STEP fields are written by BLISS
        self.assertTrue("detector" not in init["instrument"])
        self.assertEqual(init["data"], {
            "@NX_class": "NXdata",
            ">energy": "../instrument/source/energy"})
        json.dumps(init)

        # scan variables and channels in the writer configuration
        conf = selector.writerConfVars
        self.assertEqual(conf["serialno"], "_00012")
        self.assertEqual(conf["scan_id"], 12)
        self.assertEqual(conf["npoints"], 3)
        self.assertEqual(conf["measurement_group"], "mg1")
        self.assertEqual(conf["entryname"], "scan")
        dcp = [c for c in selector.calls
               if c[0] == "createDynamicComponent"][0][1]
        self.assertEqual(sorted(json.loads(dcp[0])),
                         ["axis:roby", "diode:diode"])
        names = sorted(ch["name"] for ch in json.loads(dcp[1]))
        self.assertEqual(names, ["axis:roby", "diode:diode", "sample"])
        self.assertTrue(("removeDynamicComponent", "__dynamic_component__1")
                        in selector.calls)

        scan.scan_info["end_time"] = "2026-11-26T10:01:00+01:00"
        final = meta(scan)
        self.assertEqual(final["end_time"], "2026-11-26T10:01:00+01:00")
        self.assertTrue("title" not in final)
        # INIT fields were provided at the scan start,
        # static fields without strategy come again
        source_ = final["instrument"]["source"]
        self.assertTrue("energy" not in source_)
        self.assertEqual(source_["name"].strip(), "PETRA III")
        self.assertEqual(final["data"][">end_time"], "../end_time")
        json.dumps(final)

        # a new scan opens a new entry
        init2 = meta(Scan(scan_nb=13, title="ct 1"))
        self.assertEqual(init2["title"], "ct 1")

    @unittest.skipUnless(WRITER, "nxswriter or nxstools not available")
    def test_session(self):
        class Session(object):
            def __init__(self):
                self.calls = []

            def scanStarted(self, scan_info):
                self.calls.append(("started", scan_info["scan_nb"]))

            def scanEnded(self, scan_info):
                self.calls.append(("ended", scan_info["scan_nb"]))
                raise RuntimeError("redis down")

        session = Session()
        log = Log()
        meta = NXSScanMeta(ProfileSelector(profiles={"mg1": profile()}),
                           profile="mg1", userdata={"energy": 7.0},
                           log=log, session=session)
        scan = Scan(scan_nb=5, title="ct")
        meta(scan)
        self.assertEqual(session.calls, [("started", 5)])
        final = meta(scan)
        self.assertEqual(session.calls, [("started", 5), ("ended", 5)])
        # errors of the session do not break the scan metadata
        self.assertTrue("end_time" in final)
        self.assertTrue(any("redis down" in w for w in log.warnings()))

    @unittest.skipUnless(WRITER, "nxswriter or nxstools not available")
    def test_missing_profile(self):
        selector = ProfileSelector(profiles={"mg1": profile()},
                                   components=["source"])
        log = Log()
        meta = NXSScanMeta(selector, profile="mg2",
                           userdata={"energy": 7.0}, log=log)
        init = meta.start(Scan(scan_nb=1, title="ct"))
        self.assertEqual(init["title"], "ct")
        self.assertEqual(init["instrument"]["source"]["energy"], [7.0])
        self.assertEqual(selector.mntGrp, "mg2")
        self.assertTrue(all(c[0] != "fetchProfile" for c in selector.calls
                            if isinstance(c, tuple)))
        self.assertTrue(any("mg2" in w for w in log.warnings()))
        # profile variables are not used
        self.assertTrue("entryname" not in selector.writerConfVars)

    @unittest.skipUnless(WRITER, "nxswriter or nxstools not available")
    def test_bad_configuration(self):
        selector = ProfileSelector(profiles={"mg1": profile()},
                                   xml="<definition><group></definition>")
        meta = NXSScanMeta(selector, profile="mg1", log=Log())
        scan = Scan(scan_nb=1, title="ct")
        self.assertRaises(Exception, meta, scan)
        # the scan has no open entry, i.e. the next call starts it
        selector.xml = XML
        init = meta(scan)
        self.assertEqual(init["title"], "ct")

    def test_register(self):
        if BLISS:
            self.check_register(ScanMeta, META_TIMING)
        else:
            with fake_scan_meta() as module:
                self.check_register(module.ScanMeta, module.META_TIMING)

    def check_register(self, scanmetaclass, timing):
        scanmeta = scanmetaclass()
        meta = NXSScanMeta(ProfileSelector(), profile="mg1")
        meta.register(scanmeta)
        self.assertTrue("" in scanmetaclass.categories_names())
        cat = scanmeta._scan_meta_category("")
        self.assertTrue(cat.metadata["nexdatas"] is meta)
        self.assertEqual(cat.timing, timing.START | timing.END)
        meta.unregister()
        self.assertTrue("nexdatas" not in cat.metadata)
        scanmetaclass.remove_categories([""])


class FakeScanModule(object):
    """ stand-in of bliss.scanning.scan with the h5map generator """

    def __init__(self, mapping):
        self.mapping = mapping
        self.scan_info_to_h5map = self.generate

    def generate(self, scan_info, configurable, flat,
                 multivalue_positioners):
        return {scan_info["filename"]: copy.deepcopy(self.mapping)}


def bliss_mapping():
    """ provides a BLISS-like h5map of a scan file """
    def grp(nxclass, children):
        return {"type": "group", "attributes": {"NX_class": nxclass},
                "children": children}

    def stream(name):
        return {"type": "dataset", "attributes": {},
                "value": {"type": "stream", "stream": name}}

    return {"type": "group", "attributes": {}, "children": {
        "12.1": grp("NXentry", {
            "title": {"type": "dataset", "attributes": {},
                      "value": "ascan"},
            "instrument": grp("NXinstrument", {
                "exp_c01": grp("NXdetector", {"data": stream(
                    "nxsds:exp_c01")}),
                "roby": grp("NXpositioner", {"value": stream("axis:roby")}),
                "nxsds": grp("NXcollection", {"label": {
                    "type": "dataset", "attributes": {},
                    "value": ["a", "b"]}}),
            }),
            "measurement": grp("NXcollection", {
                "exp_c01": {"type": "soft_link",
                            "target_path": "/12.1/instrument/exp_c01/data"},
            }),
        })}}


class FakeHookRegistry(object):
    """ stand-in of bliss.scanning.h5map_hooks """

    class META_TIMING(enum.Flag):
        START = enum.auto()
        END = enum.auto()

    def __init__(self):
        self.hooks = []

    def add_h5map_hook(self, hook):
        if hook not in self.hooks:
            self.hooks.append(hook)

    def remove_h5map_hook(self, hook):
        if hook in self.hooks:
            self.hooks.remove(hook)

    def apply_h5map_hooks(self, scan, mappings, timing):
        for hook in list(self.hooks):
            result = hook(scan, mappings, timing)
            if result is not None:
                mappings = result
        return mappings


class BlissH5MapTest(unittest.TestCase):

    def tearDown(self):
        BlissH5Map.uninstallHook()

    def test_stream_names(self):
        names = BlissH5Map.streamNames(
            ["axis:roby", "p201:ct1", "nxsds:exp_c01", "lima1:image:roi"])
        self.assertEqual(names["roby"], "axis:roby")
        self.assertEqual(names["p201_ct1"], "p201:ct1")
        self.assertEqual(names["exp_c01"], "nxsds:exp_c01")
        self.assertEqual(names["nxsds_exp_c01"], "nxsds:exp_c01")
        self.assertEqual(names["lima1_image_roi"], "lima1:image:roi")

    def test_apply(self):
        overlay = {"type": "group", "attributes": {}, "children": {
            "title": {"type": "step", "stream": "axis:roby"},
            "instrument": {"type": "group",
                           "attributes": {"NX_class": "NXinstrument"},
                           "children": {
                               "detector": {
                                   "type": "group",
                                   "attributes": {"NX_class": "NXdetector"},
                                   "children": {
                                       "counts": {"type": "step",
                                                  "stream": "nxsds:exp_c01"},
                                       "label": {"type": "step",
                                                 "stream": "nxsds:label"},
                                       "missing": {"type": "step",
                                                   "stream": "p201:ct9"}}},
                               "empty": {
                                   "type": "group", "attributes": {},
                                   "children": {"x": {"type": "step",
                                                      "stream": "no:x"}}}}}}}
        mapping = bliss_mapping()
        self.assertEqual(BlissH5Map.addProfileLinks(mapping, overlay), 2)
        entry = mapping["children"]["12.1"]
        # existing items are kept
        self.assertEqual(entry["children"]["title"]["value"], "ascan")
        detector = entry["children"]["instrument"]["children"]["detector"]
        self.assertEqual(detector["attributes"], {"NX_class": "NXdetector"})
        self.assertEqual(detector["children"], {
            "counts": {"type": "soft_link",
                       "target_path": "/12.1/instrument/exp_c01/data"},
            "label": {"type": "soft_link",
                      "target_path": "/12.1/instrument/nxsds/label"}})
        # groups without links are not created
        self.assertTrue(
            "empty" not in entry["children"]["instrument"]["children"])

    @unittest.skipUnless(WRITER, "nxswriter or nxstools not available")
    def test_registry_links(self):
        registry = FakeHookRegistry()
        timing = registry.META_TIMING
        hook = BlissH5Map.installHook(registry=registry)
        self.assertEqual(registry.hooks, [hook.blissHook])
        self.assertTrue(hook.module is None)
        # installed once
        self.assertTrue(BlissH5Map.installHook(registry=registry) is hook)
        self.assertEqual(len(registry.hooks), 1)

        selector = ProfileSelector(profiles={"mg1": profile()},
                                   components=["source"])
        meta = NXSScanMeta(selector, profile="mg1",
                           userdata={"energy": 7.0}, log=Log())
        if BLISS:
            scanmeta = ScanMeta()
        else:
            context = fake_scan_meta()
            fake = context.__enter__()
            scanmeta = fake.ScanMeta()
        try:
            meta.register(scanmeta, links=True)
            scan = Scan(scan_nb=12, title="ascan",
                        filename="/tmp/nxsscanmeta_links.h5",
                        channels={"axis:roby": {}, "nxsds:exp_c01": {}})
            meta(scan)
            fname = "/tmp/nxsscanmeta_links.h5"
            for tm in [timing.START, timing.END]:
                mappings = registry.apply_h5map_hooks(
                    scan, {fname: bliss_mapping()}, tm)
                entry = mappings[fname]["children"]["12.1"]
                self.assertEqual(
                    entry["children"]["instrument"]["children"][
                        "detector"]["children"]["counts"],
                    {"type": "soft_link",
                     "target_path": "/12.1/instrument/exp_c01/data"})
                self.assertEqual(
                    entry["children"]["data"]["children"]["counts"][
                        "target_path"], "/12.1/instrument/exp_c01/data")
            # the overlay is removed at the END timing
            self.assertEqual(hook.overlays, {})
            mappings = registry.apply_h5map_hooks(
                scan, {fname: bliss_mapping()}, timing.START)
            self.assertEqual(mappings[fname], bliss_mapping())
        finally:
            meta.unregister()
            if not BLISS:
                context.__exit__(None, None, None)
        # the hook is removed
        self.assertEqual(registry.hooks, [])

    def test_registry_failure(self):
        registry = FakeHookRegistry()
        log = Log()
        hook = BlissH5Map.installHook(registry=registry, log=log)
        scan = Scan(scan_nb=1, filename="/tmp/f.h5")
        hook.setOverlay(scan.scan_info, {"children": {
            "x": {"type": "step", "stream": "a:b"}}})

        class Broken(dict):
            def get(self, key, default=None):
                raise RuntimeError("broken mapping")

        # a wrong mapping is reported, the overlay removed at the end
        mappings = {"/tmp/f.h5": Broken()}
        self.assertEqual(registry.apply_h5map_hooks(
            scan, mappings, registry.META_TIMING.END), mappings)
        self.assertTrue(log.warnings())
        self.assertEqual(hook.overlays, {})

    @unittest.skipUnless(WRITER, "nxswriter or nxstools not available")
    def test_links(self):
        module = FakeScanModule(bliss_mapping())
        hook = BlissH5Map.installHook(module)
        self.assertTrue(module.scan_info_to_h5map is hook)
        selector = ProfileSelector(profiles={"mg1": profile()},
                                   components=["source"])
        meta = NXSScanMeta(selector, profile="mg1",
                           userdata={"energy": 7.0}, log=Log())
        if BLISS:
            scanmeta = ScanMeta()
        else:
            context = fake_scan_meta()
            fake = context.__enter__()
            scanmeta = fake.ScanMeta()
        try:
            meta.register(scanmeta, links=True)
            scan = Scan(scan_nb=12, title="ascan",
                        filename="/tmp/nxsscanmeta_links.h5",
                        channels={"axis:roby": {}, "nxsds:exp_c01": {}})
            init = meta(scan)
            # STEP fields are not in the metadata
            self.assertTrue("detector" not in init["instrument"])

            mappings = module.scan_info_to_h5map(
                scan.scan_info, True, True, False)
            entry = mappings["/tmp/nxsscanmeta_links.h5"]["children"]["12.1"]
            instrument = entry["children"]["instrument"]
            detector = instrument["children"]["detector"]
            self.assertEqual(detector["attributes"],
                             {"NX_class": "NXdetector"})
            self.assertEqual(detector["children"]["counts"], {
                "type": "soft_link",
                "target_path": "/12.1/instrument/exp_c01/data"})
            # links to STEP fields
            self.assertEqual(entry["children"]["data"], {
                "type": "group", "attributes": {"NX_class": "NXdata"},
                "children": {"counts": {
                    "type": "soft_link",
                    "target_path": "/12.1/instrument/exp_c01/data"}}})
            # other files and scans are not changed
            other = module.scan_info_to_h5map(
                {"filename": "/tmp/other.h5", "scan_nb": 12}, True, True,
                False)
            self.assertEqual(other["/tmp/other.h5"], bliss_mapping())

            scan.scan_info["end_time"] = "2026-11-27T10:00:00+01:00"
            meta(scan)
            scan.scan_info["end_reason"] = "SUCCESS"
            mappings = module.scan_info_to_h5map(
                scan.scan_info, True, True, False)
            entry = mappings["/tmp/nxsscanmeta_links.h5"]["children"]["12.1"]
            self.assertTrue("detector" in
                            entry["children"]["instrument"]["children"])
            # the scan is finished
            mappings = module.scan_info_to_h5map(
                scan.scan_info, True, True, False)
            self.assertEqual(mappings["/tmp/nxsscanmeta_links.h5"],
                             bliss_mapping())
        finally:
            meta.unregister()
            if not BLISS:
                context.__exit__(None, None, None)
        # the hook is removed
        self.assertEqual(module.scan_info_to_h5map, module.generate)


if __name__ == '__main__':
    unittest.main()
