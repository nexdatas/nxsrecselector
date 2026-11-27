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
# \file BlissBackend_test.py
# unittests for the bliss scan backend and the bliss session publisher
#
import fnmatch
import json
import unittest

from nxsrecconfig import ProfileManager as PMModule
from nxsrecconfig.Backends import BACKENDS, createBackend
from nxsrecconfig.BlissBackend import (
    BlissBackend, BlissPool, channelName, sessionKey)
import importlib
import sys
import types

import numpy

from nxsrecconfig import BlissDataSources as BDModule
from nxsrecconfig.BlissDataSources import (
    DataSourceReader, convert, description, fillValue, numpyType)
from nxsrecconfig.BlissSession import (
    NXSBlissSession, NXSBlissWatcher, NXSNexDatas, setup_nexdatas)
from nxsrecconfig.ProfileManager import ProfileManager
from nxsrecconfig.Utils import PoolUtils, Utils

try:
    import nxswriter.DataSourcePool  # noqa: F401
    NXSWRITER = True
except Exception:
    NXSWRITER = False


def dsxml(name, dstype, body=""):
    """ provides a datasource XML definition of the configuration server """
    return ('<?xml version="1.0" ?><definition>'
            '<datasource name="%s" type="%s">%s</datasource></definition>'
            % (name, dstype, body))


DATASOURCES = {
    "robz": dsxml("robz", "TANGO",
                  '<device member="attribute" name="a/b/c"/>'
                  '<record name="pos"/>'),
    "mypyeval": dsxml("mypyeval", "PYEVAL",
                      '<result name="result">ds.result = 2</result>'),
    "myclient": dsxml("myclient", "CLIENT", '<record name="myclient"/>'),
    "myspectrum": dsxml("myspectrum", "TANGO",
                        '<device member="attribute" name="a/b/c"/>'
                        '<record name="spectrum"/>'),
    "slit_gap": dsxml("slit_gap", "TANGO",
                      '<device member="attribute" name="a/b/c"/>'
                      '<record name="gap"/>'),
}


class FakeRedis(object):
    """ in-memory Redis stand-in with the used hash commands """

    def __init__(self):
        self.data = {}

    def scan_iter(self, pattern):
        return [key for key in list(self.data)
                if fnmatch.fnmatchcase(key, pattern)]

    def exists(self, key):
        return int(key in self.data)

    def delete(self, *keys):
        for key in keys:
            self.data.pop(key, None)

    def hget(self, key, field):
        return self.data.get(key, {}).get(field)

    def hgetall(self, key):
        return dict(self.data.get(key, {}))

    def hset(self, key, field=None, value=None, mapping=None):
        hsh = self.data.setdefault(key, {})
        if field is not None:
            hsh[field] = value
        hsh.update(mapping or {})

    def hdel(self, key, *fields):
        hsh = self.data.get(key, {})
        for field in fields:
            hsh.pop(field, None)
        if not hsh:
            self.data.pop(key, None)

    def publish(self, channel, message):
        subscribers = [sub for sub in getattr(self, "subscribers", [])
                       if channel in sub.channels]
        for sub in subscribers:
            sub.queue.append(
                {"type": "message", "channel": channel, "data": message})
        return len(subscribers)

    def pubsub(self, ignore_subscribe_messages=False):
        return FakePubSub(self)


class FakePubSub(object):
    """ Redis subscription stand-in """

    def __init__(self, redis):
        self.redis = redis
        self.channels = []
        self.queue = []
        self.closed = False

    def subscribe(self, *channels):
        self.channels.extend(channels)
        if not hasattr(self.redis, "subscribers"):
            self.redis.subscribers = []
        self.redis.subscribers.append(self)

    def unsubscribe(self):
        self.channels = []
        if self in getattr(self.redis, "subscribers", []):
            self.redis.subscribers.remove(self)

    def close(self):
        self.closed = True

    def get_message(self, timeout=0):
        return self.queue.pop(0) if self.queue else None


class FakeDataStore(object):
    """ blissdata data store stand-in """

    def __init__(self, scans=None):
        self.scans = scans or {}
        self.queries = []

    def search_existing_scans(self, **kwargs):
        self.queries.append(kwargs)
        if "fail" in self.scans:
            raise RuntimeError("no redis search")
        keys = [key for key, (session, number, _) in self.scans.items()
                if session == kwargs.get("session") and
                number == kwargs.get("number")]
        return "0-0", keys

    def get_scans_state(self, keys):
        return {key: self.scans[key][2] for key in keys}


class FakeBlissAPI(object):
    """ BLISS session stand-in """

    def __init__(self):
        self.mgs = {
            "mg1": {"available": ["diode:diode", "p201:ct1", "p201:ct2"],
                    "enabled": ["diode:diode"]},
            "mg2": {"available": ["p201:ct1"], "enabled": ["p201:ct1"]},
        }
        self.active = "mg1"
        self.calls = []
        self.controller = "nxsds"
        self.datasources = {}
        self.saving = {}
        self.extra = []

    def session(self):
        return "demo"

    def counters(self):
        return [
            {"fullname": "diode:diode", "controller": "diode",
             "shape": [], "dtype": "float64"},
            {"fullname": "p201:ct1", "controller": "p201",
             "shape": [], "dtype": "uint32"},
            {"fullname": "p201:ct2", "controller": "p201",
             "shape": [], "dtype": "uint32"},
            {"fullname": "lima1:image", "controller": "lima1",
             "shape": [-1, -1], "dtype": "uint16"},
        ] + list(self.extra) + [
            {"fullname": "nxsds:%s" % ds, "controller": "nxsds",
             "shape": [], "dtype": "float64"}
            for ds in sorted(self.datasources)]

    def setDataSources(self, datasources):
        self.calls.append(("setDataSources", sorted(datasources)))
        self.datasources = dict(datasources)
        return {ds: "nxsds:%s" % ds for ds in datasources}

    def axes(self):
        return ["roby", "robz"]

    def mntgrps(self):
        return self.mgs

    def activeMntGrp(self):
        return self.active

    def selectChannels(self, name, fullnames):
        self.calls.append(("selectChannels", name, list(fullnames)))
        if name in self.mgs:
            # mg.add() of counters missing in the measurement group
            known = [cnt["fullname"] for cnt in self.counters()]
            self.mgs[name]["available"].extend(
                fn for fn in fullnames
                if fn in known and fn not in self.mgs[name]["available"])
            self.mgs[name]["enabled"] = [
                fn for fn in fullnames if fn in self.mgs[name]["available"]]
        else:
            self.mgs[name] = {"available": list(fullnames),
                              "enabled": list(fullnames)}

    def setActiveMntGrp(self, name):
        self.calls.append(("setActiveMntGrp", name))
        self.active = name

    def scanSaving(self):
        return {"ScanDir": self.saving.get("dir", "/data/demo"),
                "ScanFile": [self.saving.get("file", "data.h5")],
                "data_policy": self.saving.get("policy", "None")}

    def setScanSaving(self, scandir=None, scanfile=None):
        if self.saving.get("policy") == "ESRF":
            raise PermissionError("ESRF data policy")
        self.calls.append(("setScanSaving", scandir, scanfile))
        if scandir:
            self.saving["dir"] = scandir
        if scanfile:
            self.saving["file"] = scanfile.split(".")[0] + ".h5"


class FakeDescriber(object):
    """ describer stand-in """

    description = [{}]

    def __init__(self, server, tree=False):
        pass

    def components(self, components, strategy, dstype):
        return [{cp: dss for cp, dss in self.description[0].items()
                 if cp in components}]


class FakeSelector(object):
    """ selector stand-in for profiles without mntgrps """

    def __init__(self, backend, door="demo"):
        self.backend = backend
        self.items = {
            "MntGrp": "mg1", "Door": door,
            "ComponentSelection": json.dumps({"slits": True}),
            "ComponentPreselection": "{}",
            "DataSourceSelection": json.dumps(
                {"p201_ct2": True, "diode_diode": False, "roby": True,
                 "unknown": True}),
            "OrderedChannels": json.dumps(["p201_ct2", "lima1_image"]),
        }
        self.stored = 0
        self.selections = ["mg1"]
        self.deleted = []

    def __getitem__(self, key):
        return self.items.get(key)

    def __setitem__(self, key, value):
        self.items[key] = value

    def getMacroServer(self):
        return self.backend.getMacroServer(self.items["Door"])

    def getPools(self):
        return self.backend.getPools(self.items["Door"])

    def storeSelection(self):
        self.stored += 1

    def configCommand(self, name, *args):
        return {"mandatoryComponents": ["default"],
                "availableComponents": ["slits", "default"]}.get(name)

    def setConfigInstance(self):
        selector = self

        class Config(object):
            def AvailableSelections(self):
                return list(selector.selections)

            def deleteSelection(self, name):
                selector.deleted.append(name)
                selector.selections.remove(name)

            def availableDataSources(self):
                return sorted(DATASOURCES)

            def dataSources(self, names):
                return [DATASOURCES[name] for name in names]
        return Config()


def published():
    """ provides a redis with a published session """
    redis = FakeRedis()
    api = FakeBlissAPI()
    session = NXSBlissSession(redis=redis, api=api)
    session.publish()
    return redis, api, session


class BlissBackendTest(unittest.TestCase):

    def test_factory(self):
        self.assertTrue("bliss" in BACKENDS)
        backend = createBackend("bliss")
        self.assertTrue(isinstance(backend, BlissBackend))
        self.assertEqual(backend.name, "bliss")
        self.assertFalse(backend.supportsMntGrps)
        self.assertTrue(backend.selectsChannels)

    def test_channel_name(self):
        self.assertEqual(channelName("diode:diode"), "diode_diode")
        self.assertEqual(channelName("lima1:roi.sum"), "lima1_roi_sum")
        self.assertEqual(channelName("roby"), "roby")
        self.assertEqual(sessionKey("demo", "env"), "nxsselector:demo:env")

    def test_sessions(self):
        redis, _, _ = published()
        backend = BlissBackend(redis=redis)
        self.assertEqual(backend.sessions(), ["demo"])
        self.assertEqual(backend.defaultDoor(None), "demo")
        self.assertTrue(backend.isDoorValid("demo"))
        self.assertFalse(backend.isDoorValid("other"))
        self.assertFalse(backend.isDoorValid(""))
        self.assertEqual(backend.getMacroServer("demo"), "demo")
        self.assertEqual(backend.updateMacroServer("demo"), "demo")
        self.assertEqual(BlissBackend(redis=FakeRedis()).defaultDoor(None),
                         "")
        self.assertEqual(backend.getPools("other"), [])

    def test_pool_utils(self):
        redis, _, _ = published()
        backend = BlissBackend(redis=redis)
        pools = backend.getPools("demo")
        self.assertEqual(len(pools), 1)
        self.assertTrue(isinstance(pools[0], BlissPool))
        self.assertEqual(pools[0].name(), "demo")
        self.assertEqual(
            PoolUtils.getElementNames(pools, "AcqChannelList"),
            ["diode_diode", "p201_ct1", "p201_ct2", "lima1_image"])
        self.assertEqual(
            PoolUtils.getElementNames(pools, "MotorList"), ["roby", "robz"])
        self.assertEqual(
            PoolUtils.getElementNames(pools, "MeasurementGroupList"),
            ["mg1", "mg2"])
        self.assertEqual(
            PoolUtils.getDeviceControllers(pools, ["p201_ct1"]),
            {"p201_ct1": "p201"})
        self.assertEqual(
            PoolUtils.getChannelSources(pools, ["diode_diode"]),
            {"diode_diode": "diode:diode"})
        self.assertEqual(PoolUtils.getMntGrpName(pools, "mg2"), "mg2")
        self.assertEqual(
            [m[0] for m in PoolUtils.getMotorPositionAttributes(pools)],
            ["roby", "robz"])
        self.assertEqual(PoolUtils.getTimers(pools), [])

    def test_channels(self):
        redis, _, _ = published()
        backend = BlissBackend(redis=redis)
        self.assertEqual(
            backend.nonExistingChannels(
                "demo", ["diode_diode", "roby", "exp_c01", "diode:diode"]),
            ["exp_c01", "diode:diode"])
        # BLISS channels are CLIENT datasources
        self.assertEqual(backend.channelSource("diode_diode"), None)

    def test_env(self):
        redis = FakeRedis()
        backend = BlissBackend(redis=redis)
        self.assertEqual(backend.getEnv("ScanDir", "demo"), None)
        backend.setEnv("ScanDir", "/tmp", "demo")
        backend.setEnvs({"ScanID": 12, "ScanFile": ["a.nxs", "a.fio"],
                         "NeXusConfiguration": {"a": {"b": 1}}}, "demo")
        self.assertEqual(backend.getEnv("ScanDir", "demo"), "/tmp")
        self.assertEqual(backend.getEnv("ScanID", "demo"), 12)
        self.assertEqual(backend.getEnv("ScanFile", "demo"),
                         ["a.nxs", "a.fio"])
        self.assertEqual(backend.getEnv("NeXusConfiguration", "demo"),
                         {"a": {"b": 1}})
        # sessions have separate environments
        self.assertEqual(backend.getEnv("ScanDir", "other"), None)
        backend.usetEnv("ScanDir", "demo")
        self.assertEqual(backend.getEnv("ScanDir", "demo"), None)
        # without target
        backend.setEnv("ScanDir", "/tmp", "")
        self.assertEqual(backend.getEnv("ScanDir", ""), None)
        self.assertFalse(backend.isDoorRunning("demo"))
        backend.setEnv("ScanRunning", True, "demo")
        self.assertTrue(backend.isDoorRunning("demo"))

    def test_selector_env(self):
        backend = BlissBackend(redis=FakeRedis())
        backend.setSelectorEnv("demo", {"Timer": '["t1"]', "ScanDir": "/x"},
                               {"ConfigDevice": "cs"})
        data = {}
        backend.getSelectorEnv("demo", ["Timer", "ConfigDevice"], data)
        self.assertEqual(data["Timer"], '["t1"]')
        self.assertEqual(data["ConfigDevice"], "cs")
        self.assertEqual(backend.getEnv("ScanDir", "demo"), "/x")

    def test_scan_env(self):
        backend = BlissBackend(redis=FakeRedis())
        self.assertEqual(backend.setScanEnv("demo", json.dumps(
            {"ScanDir": "/tmp", "ScanFile": ["s.nxs"], "ScanID": 7})), 7)
        res = json.loads(backend.getScanEnv("demo"))
        self.assertEqual(res["ScanDir"], "/tmp")
        self.assertEqual(res["ScanFile"], ["s.nxs"])
        self.assertEqual(res["ScanID"], 7)
        self.assertEqual(backend.setScanEnv(
            "demo", json.dumps({"ScanDir": "/tmp2"})), 7)

    def test_no_mntgrp_devices(self):
        backend = BlissBackend(redis=FakeRedis())
        for method in [backend.createMntGrp, backend.deleteMntGrp,
                       backend.mntGrpConfiguration,
                       backend.setMntGrpConfiguration,
                       backend.testMntGrpConfiguration]:
            self.assertRaises(NotImplementedError, method, "a", "b")

    def test_select_channels(self):
        redis, api, session = published()
        backend = BlissBackend(redis=redis)
        backend.selectChannels(
            "demo", "mg1", ["p201_ct2", "unknown", "diode_diode"])
        self.assertEqual(
            json.loads(redis.hget(sessionKey("demo", "mntgrps"), "mg1")),
            ["p201:ct2", "diode:diode"])
        # nothing without session or measurement group
        backend.selectChannels("", "mg1", ["p201_ct2"])
        backend.selectChannels("demo", "", ["p201_ct2"])
        self.assertEqual(
            list(redis.hgetall(sessionKey("demo", "mntgrps"))), ["mg1"])


class BlissSessionTest(unittest.TestCase):

    def test_publish(self):
        redis, api, session = published()
        self.assertEqual(session.session, "demo")
        elements = {
            key: json.loads(value) for key, value in
            redis.hgetall(sessionKey("demo", "elements")).items()}
        self.assertEqual(sorted(elements), [
            "AcqChannelList", "ExpChannelList", "MeasurementGroupList",
            "MotorList"])
        lima = elements["AcqChannelList"][3]
        self.assertEqual(lima["name"], "lima1_image")
        self.assertEqual(lima["full_name"], "lima1:image")
        self.assertEqual(lima["controller"], "lima1")
        self.assertEqual(lima["shape"], [-1, -1])
        self.assertEqual(lima["dtype"], "uint16")
        self.assertEqual(elements["MeasurementGroupList"][0]["channels"],
                         ["diode:diode"])
        # the active measurement group is the initial selector one
        backend = BlissBackend(redis=redis)
        self.assertEqual(backend.getEnv("ActiveMntGrp", "demo"), "mg1")
        backend.setEnv("ActiveMntGrp", "mg2", "demo")
        session.publish()
        self.assertEqual(backend.getEnv("ActiveMntGrp", "demo"), "mg2")

    def test_apply(self):
        redis, api, session = published()
        backend = BlissBackend(redis=redis)
        self.assertEqual(session.apply(), [])
        self.assertEqual(api.calls, [])

        backend.selectChannels("demo", "mg1", ["p201_ct1", "p201_ct2"])
        backend.selectChannels("demo", "new", ["roby", "diode_diode"])
        self.assertEqual(
            json.loads(redis.hget(sessionKey("demo", "mntgrps"), "new")),
            ["diode:diode"])
        backend.setEnv("ActiveMntGrp", "new", "demo")
        self.assertEqual(session.sync(), ["mg1", "new"])
        self.assertEqual(api.mgs["mg1"]["enabled"], ["p201:ct1", "p201:ct2"])
        self.assertEqual(api.mgs["new"]["enabled"], ["diode:diode"])
        self.assertEqual(api.active, "new")
        # requests are applied once
        self.assertEqual(redis.hgetall(sessionKey("demo", "mntgrps")), {})
        self.assertEqual(session.apply(), [])
        # published again
        mgs = json.loads(redis.hget(sessionKey("demo", "elements"),
                                    "MeasurementGroupList"))
        self.assertEqual([mg["name"] for mg in mgs], ["mg1", "mg2", "new"])

    def test_unknown_active_mntgrp(self):
        redis, api, session = published()
        BlissBackend(redis=redis).setEnv("ActiveMntGrp", "nomg", "demo")
        session.apply()
        self.assertEqual(api.active, "mg1")
        self.assertEqual(api.calls, [])


class ProfileManagerBlissTest(unittest.TestCase):

    def setUp(self):
        self.describer = PMModule.Describer
        PMModule.Describer = FakeDescriber
        FakeDescriber.description = [{
            "slits": {"p201_ct1": [("STEP", "CLIENT", "p201_ct1", None,
                                    None)],
                      "slit_gap": [("INIT", "TANGO", "a/b/c/gap", None,
                                    None)]},
            "default": {"robz": [("STEP", "TANGO", "a/b/c/pos", None,
                                  None)],
                        "lima1_image": [("STEP", "CLIENT", "lima1_image",
                                         None, None)],
                        "mypyeval": [("STEP", "PYEVAL", None, "NX_INT32",
                                      None)],
                        "myclient": [("STEP", "CLIENT", "myclient",
                                      "NX_CHAR", None)],
                        "myspectrum": [("STEP", "TANGO", "a/b/c/spectrum",
                                        "NX_FLOAT", [10])]},
        }]

    def tearDown(self):
        PMModule.Describer = self.describer

    def test_update_profile(self):
        redis, api, session = published()
        backend = BlissBackend(redis=redis)
        selector = FakeSelector(backend)
        pm = ProfileManager(selector)
        self.assertEqual(pm.availableMntGrps(), ["mg1", "mg2"])
        self.assertEqual(pm.mntGrpConfiguration(), "{}")
        self.assertTrue(pm.isMntGrpUpdated())

        self.assertEqual(pm.updateProfile(), "{}")
        self.assertEqual(selector.stored, 1)
        self.assertEqual(backend.getEnv("ActiveMntGrp", "demo"), "mg1")
        # ordered channels first, then the other ones sorted,
        # without motors and unknown channels
        self.assertEqual(
            json.loads(redis.hget(sessionKey("demo", "mntgrps"), "mg1")),
            ["p201:ct2", "lima1:image", "p201:ct1"])

        # TANGO, DB, PYEVAL and CLIENT STEP datasources without counters
        dss = json.loads(
            redis.hget(sessionKey("demo", "datasources"), "mg1"))
        self.assertEqual(sorted(dss),
                         ["myclient", "mypyeval", "myspectrum", "robz"])
        self.assertEqual(dss["robz"], {"xml": DATASOURCES["robz"],
                                       "nxtype": None, "rank": 0})
        self.assertEqual(dss["mypyeval"]["nxtype"], "NX_INT32")
        self.assertEqual(dss["myclient"]["nxtype"], "NX_CHAR")
        self.assertEqual(dss["myspectrum"]["nxtype"], "NX_FLOAT")
        self.assertEqual(dss["myspectrum"]["rank"], 1)

        session.sync()
        self.assertEqual(api.datasources, dss)
        self.assertEqual(api.mgs["mg1"]["enabled"],
                         ["p201:ct2", "lima1:image", "p201:ct1",
                          "nxsds:myclient", "nxsds:mypyeval",
                          "nxsds:myspectrum", "nxsds:robz"])
        # datasource counters are not published as channels
        names = PoolUtils.getElementNames(
            backend.getPools("demo"), "AcqChannelList")
        self.assertTrue("nxsds_robz" not in names)
        self.assertTrue("robz" not in names)
        # the same selection again
        pm.updateProfile()
        self.assertEqual(sorted(json.loads(
            redis.hget(sessionKey("demo", "datasources"), "mg1"))),
            ["myclient", "mypyeval", "myspectrum", "robz"])

        selector["MntGrp"] = "mg2"
        pm.updateProfile()
        session.sync()
        self.assertEqual(api.active, "mg2")
        self.assertEqual(api.mgs["mg2"]["enabled"],
                         ["p201:ct2", "lima1:image", "p201:ct1",
                          "nxsds:myclient", "nxsds:mypyeval",
                          "nxsds:myspectrum", "nxsds:robz"])

        # deselected datasources are removed from the measurement group,
        # the counters are kept for the other measurement groups
        FakeDescriber.description[0]["default"].pop("robz")
        pm.updateProfile()
        session.sync()
        self.assertEqual(sorted(api.datasources),
                         ["myclient", "mypyeval", "myspectrum", "robz"])
        self.assertEqual(api.mgs["mg2"]["enabled"],
                         ["p201:ct2", "lima1:image", "p201:ct1",
                          "nxsds:myclient", "nxsds:mypyeval",
                          "nxsds:myspectrum"])
        selector["MntGrp"] = "mg1"
        pm.updateProfile()
        session.sync()
        self.assertEqual(sorted(api.datasources),
                         ["myclient", "mypyeval", "myspectrum"])
        self.assertEqual(api.active, "mg1")
        selector["MntGrp"] = "mg2"
        pm.updateProfile()
        session.sync()
        self.assertEqual(pm.availableMntGrps(), ["mg2", "mg1"])

        pm.deleteProfile("mg1")
        self.assertEqual(selector.deleted, ["mg1"])
        # BLISS measurement groups are kept
        self.assertTrue("mg1" in api.mgs)


class DataSourceHelpersTest(unittest.TestCase):

    def test_description(self):
        self.assertEqual(description("<xml/>"),
                         {"xml": "<xml/>", "nxtype": None, "rank": 0})
        self.assertEqual(
            description({"xml": "<xml/>", "nxtype": "NX_INT", "rank": 2}),
            {"xml": "<xml/>", "nxtype": "NX_INT", "rank": 2})

    def test_types(self):
        self.assertEqual(numpyType("NX_INT32"), "int32")
        self.assertEqual(numpyType("NX_CHAR"), "str")
        self.assertEqual(numpyType("NX_BOOLEAN"), "bool")
        self.assertEqual(numpyType(None), "float64")
        self.assertEqual(numpyType("NX_WRONG"), "float64")
        self.assertTrue(numpy.isnan(fillValue("float32")))
        self.assertEqual(fillValue("int16"), 32767)
        self.assertEqual(fillValue("uint8"), 255)
        self.assertEqual(fillValue("bool"), False)
        self.assertEqual(fillValue("str"), "")

    def test_convert(self):
        self.assertEqual(convert(3, "int32", 0).dtype, numpy.int32)
        self.assertEqual(convert([4.5], "float64", 0), 4.5)
        self.assertEqual(convert([1, 2], "float32", 1).tolist(), [1., 2.])
        self.assertEqual(convert(5, "int64", 1).tolist(), [5])
        self.assertEqual(convert([[1, 2]], "uint8", 2).shape, (1, 2))
        self.assertEqual(convert(b"abc", "str", 0), "abc")
        self.assertEqual(convert(["a", "b"], "str", 1), ["a", "b"])
        for args in [([1, 2], "float64", 0), ([[1]], "int32", 1),
                     ("abc", "float64", 0), (["a", "b"], "str", 0)]:
            self.assertRaises(ValueError, convert, *args)


@unittest.skipIf(not NXSWRITER, "nxswriter is not available")
class DataSourceReaderTest(unittest.TestCase):

    def test_datasource_type(self):
        self.assertEqual(Utils.dataSourceType(DATASOURCES["robz"]), "TANGO")
        self.assertEqual(
            Utils.dataSourceType('<datasource type="DB" name="d"/>'), "DB")
        self.assertEqual(Utils.dataSourceType("<definition/>"), None)
        self.assertEqual(Utils.dataSourceType("<wrong"), None)
        self.assertEqual(Utils.dataSourceType(None), None)

    def test_read(self):
        userdata = {"energy": 7.5, "names": ["a", "b"]}
        reader = DataSourceReader(userdata=lambda: userdata)
        reader.setDataSources({
            "pe": dsxml("pe", "PYEVAL",
                        '<result name="result">ds.result = 2.5 * 2'
                        '</result>'),
            "pe2": {"xml": dsxml(
                "pe2", "PYEVAL",
                '<datasource type="CLIENT" name="energy">'
                '<record name="energy"/></datasource>'
                '<result name="result">'
                'ds.result = [ds.energy + 1, ds.energy]</result>'),
                "nxtype": "NX_FLOAT", "rank": 1},
            "cl": dsxml("cl", "CLIENT", '<record name="energy"/>'),
            "cl2": dsxml("cl2", "CLIENT", '<record name="names"/>'),
            "nocl": dsxml("nocl", "CLIENT", '<record name="nodata"/>'),
            "bad": dsxml("bad", "UNKNOWN"),
            "wrong": "<datasource",
        })
        # CLIENT datasources without user data are skipped
        self.assertEqual(reader.names(), ["cl", "cl2", "pe", "pe2"])
        self.assertEqual(reader.description("pe2")["rank"], 1)
        self.assertEqual(reader.description("pe")["rank"], 0)
        values = reader.read(["pe", "pe2", "cl", "cl2", "missing"])
        self.assertEqual(values[:4], [5.0, [8.5, 7.5], 7.5, ["a", "b"]])
        self.assertEqual(values[4], None)
        self.assertEqual(list(reader.errors), ["missing"])
        userdata["energy"] = 8.0
        self.assertEqual(reader.read(["pe2", "cl"]), [[9.0, 8.0], 8.0])
        userdata.pop("energy")
        self.assertEqual(reader.read(["cl"]), [None])
        self.assertEqual(list(reader.errors), ["cl"])

        reader.setDataSources({"pe": dsxml(
            "pe", "PYEVAL", '<result name="result">ds.result = 1</result>')})
        self.assertEqual(reader.names(), ["pe"])
        self.assertEqual(reader.read(["pe"]), [1])


try:
    import bliss.common.counter  # noqa: F401
    BLISS = True
except Exception:
    BLISS = False


class StubCounter(object):
    """ stand-in of bliss.common.counter.Counter """

    def __init__(self, name, controller=None, dtype=None):
        self.name = name
        self.dtype = dtype
        self._counter_controller = controller
        controller._counters[name] = self

    @property
    def fullname(self):
        return "%s:%s" % (self._counter_controller.name, self.name)


class StubController(object):
    """ stand-in of bliss.controllers.counter.CounterController """

    def __init__(self, name):
        self.name = name
        self._counters = {}

    @property
    def counters(self):
        return list(self._counters.values())

    def remove(self, cnt):
        del self._counters[cnt.name]


class StubChannel(object):
    """ stand-in of bliss.scanning.channel.AcquisitionChannel """

    def __init__(self, name, shape):
        self.name = name
        self.shape = shape
        self.data = []

    def emit(self, value):
        value = numpy.asarray(value)
        assert value.ndim == len(self.shape)
        self.data.append(value)


class StubSlave(object):
    """ stand-in of BaseCounterAcquisitionSlave """

    def __init__(self, device, count_time=None, npoints=1,
                 prepare_once=False, start_once=False, ctrl_params=None):
        import collections
        self.device = device
        self.npoints = npoints
        self._counters = collections.defaultdict(list)
        self._stop_flag = False
        self.channels = []

    def _do_add_counter(self, counter):
        self.channels.append(StubChannel(counter.fullname, counter.shape))
        self._counters[counter].append(self.channels[-1])

    def add_counter(self, counter):
        self._do_add_counter(counter)

    def prepare_device(self):
        pass

    def start_device(self):
        pass

    def stop_device(self):
        pass

    def get_acquisition_metadata(self, timing=None):
        return "base"


class StubTiming(object):
    PREPARED = 1
    END = 2


@unittest.skipIf(BLISS or not NXSWRITER,
                 "BLISS is available or nxswriter is not available")
class DataSourceControllerTest(unittest.TestCase):

    def setUp(self):
        self.modules = {}
        stubs = {
            "bliss": {}, "bliss.common": {}, "bliss.controllers": {},
            "bliss.scanning": {}, "bliss.scanning.acquisition": {},
            "bliss.common.counter": {"Counter": StubCounter},
            "bliss.controllers.counter": {
                "CounterController": StubController},
            "bliss.scanning.acquisition.counter": {
                "BaseCounterAcquisitionSlave": StubSlave},
            "bliss.scanning.scan_meta": {"META_TIMING": StubTiming},
        }
        for name, attrs in stubs.items():
            self.modules[name] = sys.modules.get(name)
            module = types.ModuleType(name)
            for key, value in attrs.items():
                setattr(module, key, value)
            sys.modules[name] = module
        importlib.reload(BDModule)

    def tearDown(self):
        for name, module in self.modules.items():
            if module is None:
                sys.modules.pop(name, None)
            else:
                sys.modules[name] = module
        importlib.reload(BDModule)

    def controller(self, userdata, canfail=True):
        ctrl = BDModule.NXSDataSourceController(
            "nxsds", BDModule.DataSourceReader(lambda: userdata), canfail)
        fullnames = ctrl.setDataSources({
            "energy": {"xml": dsxml("energy", "CLIENT",
                                    '<record name="energy"/>'),
                       "nxtype": "NX_FLOAT32", "rank": 0},
            "counts": {"xml": dsxml("counts", "CLIENT",
                                    '<record name="counts"/>'),
                       "nxtype": "NX_INT32", "rank": 1},
            "title": {"xml": dsxml("title", "CLIENT",
                                   '<record name="title"/>'),
                      "nxtype": "NX_CHAR", "rank": 0},
            "pe": dsxml("pe", "PYEVAL",
                        '<result name="result">ds.result = 3</result>'),
        })
        self.assertEqual(sorted(fullnames), [
            "nxsds:counts", "nxsds:energy", "nxsds:pe", "nxsds:title"])
        return ctrl

    def scan(self, ctrl, npoints=2):
        slave = ctrl.get_acquisition_object(
            {"count_time": 0.1, "npoints": npoints}, {}, {})
        for cnt in sorted(ctrl.counters, key=lambda c: c.name):
            slave.add_counter(cnt)
        slave.prepare()
        slave.start()
        return slave

    def test_scan(self):
        userdata = {"energy": 7.5, "counts": [1, 2, 3], "title": "abc"}
        ctrl = self.controller(userdata)
        counters = {cnt.name: cnt for cnt in ctrl.counters}
        self.assertEqual(counters["counts"].shape, (-1,))
        self.assertEqual(counters["energy"].shape, ())
        self.assertTrue(counters["title"].isstring)
        self.assertEqual(ctrl.get_default_chain_parameters(
            {"count_time": 0.5, "npoints": 4}, {}),
            {"count_time": 0.5, "npoints": 4})

        slave = self.scan(ctrl)
        slave.trigger()
        userdata.update({"energy": 8.0, "counts": [4, 5], "title": "def"})
        slave.trigger()
        slave.stop()
        # string datasources have no channels
        channels = {ch.name: ch for ch in slave.channels}
        self.assertEqual(sorted(channels),
                         ["nxsds:counts", "nxsds:energy", "nxsds:pe"])
        self.assertEqual([v.tolist() for v in channels["nxsds:counts"].data],
                         [[1, 2, 3], [4, 5]])
        self.assertEqual(channels["nxsds:counts"].data[0].dtype, numpy.int32)
        self.assertEqual([v.item() for v in channels["nxsds:energy"].data],
                         [7.5, 8.0])
        self.assertEqual(channels["nxsds:energy"].data[0].dtype,
                         numpy.float32)
        self.assertEqual([v.item() for v in channels["nxsds:pe"].data],
                         [3.0, 3.0])
        self.assertEqual(
            slave.get_acquisition_metadata(StubTiming.END),
            {"title": ["abc", "def"]})
        self.assertEqual(
            slave.get_acquisition_metadata(StubTiming.PREPARED), "base")

        # a new scan
        slave.prepare()
        self.assertEqual(slave.get_acquisition_metadata(StubTiming.END),
                         {"title": []})

    def test_canfail(self):
        userdata = {"energy": 7.5, "counts": [1, 2], "title": "abc"}
        ctrl = self.controller(userdata)
        slave = self.scan(ctrl)
        userdata.clear()
        slave.trigger()
        channels = {ch.name: ch for ch in slave.channels}
        self.assertTrue(numpy.isnan(channels["nxsds:energy"].data[0]))
        self.assertEqual(channels["nxsds:counts"].data[0].tolist(),
                         [2147483647])
        self.assertEqual(slave.get_acquisition_metadata(StubTiming.END),
                         {"title": [""]})

        ctrl.canfail = False
        self.assertRaises(RuntimeError, slave.trigger)

    def test_update(self):
        ctrl = self.controller({"energy": 1, "counts": [1], "title": "a"})
        old = {cnt.name: cnt for cnt in ctrl.counters}
        fullnames = ctrl.setDataSources({
            "energy": {"xml": dsxml("energy", "CLIENT",
                                    '<record name="energy"/>'),
                       "nxtype": "NX_FLOAT64", "rank": 0},
            "pe": dsxml("pe", "PYEVAL",
                        '<result name="result">ds.result = 3</result>'),
        })
        self.assertEqual(sorted(fullnames), ["nxsds:energy", "nxsds:pe"])
        new = {cnt.name: cnt for cnt in ctrl.counters}
        # the counter of the same datasource is kept
        self.assertTrue(new["pe"] is old["pe"])
        # the counter with a new type is recreated
        self.assertTrue(new["energy"] is not old["energy"])
        self.assertEqual(new["energy"].typename, "float64")


class Log(object):
    """ logger collecting messages """

    def __init__(self):
        self.messages = []

    def debug(self, msg):
        self.messages.append(("debug", msg))

    def info(self, msg):
        self.messages.append(("info", msg))

    def warning(self, msg):
        self.messages.append(("warning", msg))

    def warnings(self):
        return [m for (k, m) in self.messages if k == "warning"]


class BlissAutomationTest(unittest.TestCase):

    def session(self):
        redis = FakeRedis()
        api = FakeBlissAPI()
        log = Log()
        return redis, api, NXSBlissSession(redis=redis, api=api, log=log), log

    def test_notify(self):
        redis, api, session, _ = self.session()
        sub = redis.pubsub()
        sub.subscribe(sessionKey("demo", "changed"))
        backend = BlissBackend(redis=redis)
        backend.setEnv("ScanDir", "/tmp", "demo")
        backend.usetEnv("ScanDir", "demo")
        backend.selectChannels("demo", "mg1", [])
        backend.selectDataSources("demo", "mg1", {})
        self.assertEqual([m["data"] for m in sub.queue],
                         ["env", "env", "mntgrps", "datasources"])
        # the session does not notify itself
        sub.queue = []
        session.sync()
        session.scanStarted({"scan_nb": 3})
        session.scanEnded()
        self.assertEqual(sub.queue, [])

    def test_is_door_running(self):
        redis = FakeRedis()
        store = FakeDataStore({"k1": ("demo", 3, 2), "k2": ("demo", 4, 4)})
        backend = BlissBackend(redis=redis, datastore=store)
        self.assertFalse(backend.isDoorRunning("demo"))
        backend.setEnv("ScanRunning", {"session": "demo", "number": 3},
                       "demo")
        self.assertTrue(backend.isDoorRunning("demo"))
        self.assertEqual(store.queries[-1], {"session": "demo", "number": 3})
        # closed scans are not running, e.g. after a session crash
        backend.setEnv("ScanRunning", {"session": "demo", "number": 4},
                       "demo")
        self.assertFalse(backend.isDoorRunning("demo"))
        # scans which are not created yet are running
        backend.setEnv("ScanRunning", {"session": "demo", "number": 5},
                       "demo")
        self.assertTrue(backend.isDoorRunning("demo"))
        # without blissdata the published flag is used
        store.scans["fail"] = None
        backend.setEnv("ScanRunning", {"session": "demo", "number": 4},
                       "demo")
        self.assertTrue(backend.isDoorRunning("demo"))
        backend.setEnv("ScanRunning", True, "demo")
        self.assertTrue(backend.isDoorRunning("demo"))

    def test_scan_paths(self):
        redis, api, session, log = self.session()
        session.publish()
        backend = BlissBackend(redis=redis)
        self.assertEqual(backend.getEnv("ScanDir", "demo"), "/data/demo")
        self.assertEqual(backend.getEnv("ScanFile", "demo"), ["data.h5"])
        self.assertEqual(json.loads(backend.getScanEnv("demo"))["ScanDir"],
                         "/data/demo")
        # unchanged paths are not applied
        session.sync()
        self.assertTrue(all(c[0] != "setScanSaving" for c in api.calls))
        # paths changed by the selector
        backend.setScanEnv("demo", json.dumps(
            {"ScanDir": "/data/new", "ScanFile": ["scan.nxs"]}))
        session.sync()
        self.assertEqual(api.calls[-1],
                         ("setScanSaving", "/data/new", "scan.nxs"))
        # the BLISS paths are published
        self.assertEqual(backend.getEnv("ScanDir", "demo"), "/data/new")
        self.assertEqual(backend.getEnv("ScanFile", "demo"), ["scan.h5"])
        backend.setEnv("ScanFile", "other.h5", "demo")
        session.sync()
        self.assertEqual(api.calls[-1], ("setScanSaving", None, "other.h5"))

    def test_esrf_data_policy(self):
        redis, api, session, log = self.session()
        api.saving["policy"] = "ESRF"
        session.publish()
        backend = BlissBackend(redis=redis)
        backend.setEnv("ScanDir", "/data/new", "demo")
        session.sync()
        self.assertTrue(any("ESRF" in w for w in log.warnings()))
        # the BLISS paths are published again
        self.assertEqual(backend.getEnv("ScanDir", "demo"), "/data/demo")

    def test_scan_state(self):
        redis, api, session, log = self.session()
        session.publish()
        self.assertFalse(session.scanRunning)
        session.scanStarted({"scan_nb": 12})
        backend = BlissBackend(redis=redis)
        running = backend.getEnv("ScanRunning", "demo")
        self.assertEqual(running["session"], "demo")
        self.assertEqual(running["number"], 12)
        self.assertTrue(running["since"])
        self.assertEqual(backend.getEnv("ScanID", "demo"), 12)
        self.assertTrue(session.scanRunning)
        self.assertEqual(log.warnings(), [])
        session.scanEnded({"scan_nb": 12})
        self.assertFalse(session.scanRunning)
        # selections changed after the scan creation
        backend.selectChannels("demo", "mg1", ["p201_ct1"])
        self.assertEqual(session.pending(), ["mg1"])
        session.scanStarted({"scan_nb": 13})
        self.assertTrue(any("mg1" in w for w in log.warnings()))

    def test_watcher(self):
        redis, api, session, log = self.session()
        session.sync()
        watcher = NXSBlissWatcher(session, interval=0.01)
        watcher.signature = session.signature()
        self.assertFalse(watcher.poll())
        backend = BlissBackend(redis=redis)
        backend.selectChannels("demo", "mg1", ["p201_ct1"])
        # changes are applied after the scan
        session.scanStarted({"scan_nb": 1})
        self.assertFalse(watcher.poll())
        self.assertEqual(api.mgs["mg1"]["enabled"], ["diode:diode"])
        session.scanEnded()
        self.assertTrue(watcher.poll())
        self.assertEqual(api.mgs["mg1"]["enabled"], ["p201:ct1"])
        self.assertEqual(session.pending(), [])
        self.assertFalse(watcher.poll())
        # new counters of the session are published
        api.extra.append({"fullname": "new:ct", "controller": "new",
                          "shape": [], "dtype": "float64"})
        self.assertFalse(watcher.poll())
        names = PoolUtils.getElementNames(
            backend.getPools("demo"), "AcqChannelList")
        self.assertTrue("new_ct" in names)
        watcher.stop()

    def test_watcher_start_stop(self):
        redis, api, session, log = self.session()
        watcher = NXSBlissWatcher(session, interval=0.01)
        watcher.start()
        watcher.start()
        self.assertEqual(len(redis.subscribers), 1)
        watcher.stop()
        self.assertEqual(redis.subscribers, [])

    def test_setup_nexdatas(self):
        redis = FakeRedis()
        api = FakeBlissAPI()
        nexdatas = setup_nexdatas(redis=redis, api=api, watch=False,
                                  scanmeta=False)
        self.assertTrue(isinstance(nexdatas, NXSNexDatas))
        self.assertEqual(nexdatas.session.session, "demo")
        backend = BlissBackend(redis=redis)
        self.assertEqual(backend.getEnv("ScanDir", "demo"), "/data/demo")
        self.assertEqual(nexdatas.meta, None)
        self.assertEqual(nexdatas.watcher, None)
        nexdatas.stop()

        nexdatas = setup_nexdatas(redis=redis, api=api, scanmeta=False,
                                  interval=0.01)
        self.assertTrue(isinstance(nexdatas.watcher, NXSBlissWatcher))
        self.assertEqual(nexdatas.watcher.signature,
                         nexdatas.session.signature())
        nexdatas.stop()
        self.assertEqual(redis.subscribers, [])


if __name__ == '__main__':
    unittest.main()
