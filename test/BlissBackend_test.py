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
from nxsrecconfig.BlissSession import NXSBlissSession
from nxsrecconfig.ProfileManager import ProfileManager
from nxsrecconfig.Utils import PoolUtils


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
        ]

    def axes(self):
        return ["roby", "robz"]

    def mntgrps(self):
        return self.mgs

    def activeMntGrp(self):
        return self.active

    def selectChannels(self, name, fullnames):
        self.calls.append(("selectChannels", name, list(fullnames)))
        if name in self.mgs:
            self.mgs[name]["enabled"] = [
                fn for fn in fullnames if fn in self.mgs[name]["available"]]
        else:
            self.mgs[name] = {"available": list(fullnames),
                              "enabled": list(fullnames)}

    def setActiveMntGrp(self, name):
        self.calls.append(("setActiveMntGrp", name))
        self.active = name


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
                                         None, None)]},
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

        session.sync()
        self.assertEqual(api.mgs["mg1"]["enabled"],
                         ["p201:ct2", "p201:ct1"])

        selector["MntGrp"] = "mg2"
        pm.updateProfile()
        session.sync()
        self.assertEqual(api.active, "mg2")
        self.assertEqual(pm.availableMntGrps(), ["mg2", "mg1"])

        pm.deleteProfile("mg1")
        self.assertEqual(selector.deleted, ["mg1"])
        # BLISS measurement groups are kept
        self.assertTrue("mg1" in api.mgs)


if __name__ == '__main__':
    unittest.main()
