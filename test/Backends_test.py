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
# \file Backends_test.py
# unittests for scan backends
#
import json
import random
import unittest

from nxsrecconfig.Utils import Utils
from nxsrecconfig.ScanBackend import ScanBackend
from nxsrecconfig.Backends import (
    NullBackend, SardanaBackend, BACKENDS, DEFAULTBACKEND, createBackend)
from nxsrecconfig.MacroServerPools import MacroServerPools
from nxsrecconfig.DynamicComponent import DynamicComponent
from nxsrecconfig.ProfileManager import ProfileManager

try:
    from nxsrecconfig.Selector import Selector
    import tango
    tango.Database()
    TANGODB = True
except Exception:
    TANGODB = False


NXSENV = "NeXusConfiguration"
PUREVAR = ["AppendEntry", "ComponentsFromMntGrp", "DynamicComponents",
           "DefaultDynamicLinks", "DefaultDynamicPath", "TimeZone",
           "ConfigDevice", "WriterDevice", "Door", "MntGrp", "ScanDir"]


# reference implementations: the environment code of MacroServerPools
# before the backend refactoring, working on the macroserver dictionary

def ref_getSelectorEnv(dc, names, data):
    params = ["ScanDir", "ScanFile"]
    nenv = {}
    vl = None
    if 'new' in dc.keys():
        if NXSENV in dc['new'].keys():
            nenv = dc['new'][NXSENV]
        for var in names:
            name = var if var in params else ("NeXus%s" % var)
            if name in dc['new'].keys():
                vl = dc['new'][name]
            elif var in nenv.keys():
                vl = nenv[var]
            else:
                continue
            if type(vl) not in [str, bool, int, str, float]:
                vl = json.dumps(vl)
            data[var] = vl


def ref_setSelectorEnv(dc, data, cmddata=None):
    params = ["ScanDir", "ScanFile"]
    if 'new' in dc.keys():
        dc = {'new': {}}
        if NXSENV not in dc['new'].keys() \
                or not isinstance(dc['new'][NXSENV], dict):
            dc = {'new': {NXSENV: {}}}
        else:
            dc = {'new': {NXSENV: dc['new'][NXSENV]}}
        nenv = dc['new'][NXSENV]
        for var in data.keys():
            if var in PUREVAR:
                vl = data[var]
            else:
                try:
                    vl = json.loads(data[var])
                except (ValueError, TypeError):
                    vl = data[var]
            if var in params:
                dc['new'][Utils.tostr(var)] = vl
            else:
                nenv[("%s" % var)] = vl
        if cmddata:
            for name, value in cmddata.items():
                nenv[Utils.tostr(name)] = value
        return dc


def ref_getScanEnv(dc):
    params = ["ScanDir", "ScanFile", "ScanID", "NeXusSelectorDevice"]
    res = {}
    if 'new' in dc.keys():
        for var in params:
            if var in dc['new'].keys():
                res[var] = dc['new'][var]
    return json.dumps(res)


def ref_setScanEnv(dc, jdata):
    jdata = Utils.stringToDictJson(jdata)
    data = json.loads(jdata)
    scanID = -1
    if 'new' in dc.keys():
        if 'ScanID' in dc['new'].keys():
            scanID = int(dc['new']["ScanID"])
    dc = {'new': {}}
    for var in data.keys():
        dc['new'][Utils.tostr(var)] = Utils.toString(data[var])
    if 'ScanID' in dc['new'].keys():
        scanID = int(dc['new']["ScanID"])
    return dc, scanID


class FakeConfigServer(object):
    """ configuration server stand-in """

    def __init__(self, components=None, datasources=None):
        self.components = components or []
        self.datasources = datasources or []

    def availableComponents(self):
        return list(self.components)

    def availableDataSources(self):
        return list(self.datasources)


class FakeChannelBackend(NullBackend):
    """ null backend with a known channel source """

    def channelSource(self, name):
        return {"exp_c01": "haso:10000/p09/vmexecutor/exp.01/Counts"}.get(
            name)


class FakeSelector(object):
    """ selector stand-in for profile managing without mntgrps """

    def __init__(self, backend):
        self.backend = backend
        self.items = {"MntGrp": "mymg", "Door": "", "ComponentSelection": "{}",
                      "DataSourceSelection": "{}"}
        self.stored = 0
        self.selections = ["mymg"]
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

    def setConfigInstance(self):
        selector = self

        class Config(object):
            def AvailableSelections(self):
                return list(selector.selections)

            def deleteSelection(self, name):
                selector.deleted.append(name)
                selector.selections.remove(name)
        return Config()


def random_value(rnd):
    return rnd.choice([
        rnd.randint(-5, 100), rnd.random(), "text%s" % rnd.randint(0, 9),
        True, False, [1, 2, "a"], {"a": [1, 2], "b": {"c": "d"}},
        json.dumps({"x": rnd.randint(0, 9)}), json.dumps([1, 2]), "{",
        None])


class ScanBackendTest(unittest.TestCase):

    def test_interface(self):
        sb = ScanBackend(3)
        self.assertEqual(sb.name, None)
        self.assertFalse(sb.supportsMntGrps)
        self.assertEqual(sb.poolBlacklist, [])
        self.assertEqual(
            sb.tangoSourceErrorStates,
            ["OFF", "INIT", "INSERT", "CLOSE", "UNKNOWN", "FAULT"])
        self.assertEqual(sb.tangoSourceWarningStates, ["ALARM", "DISABLE"])
        calls = [
            ("defaultDoor", (None,)), ("isDoorValid", ("d",)),
            ("updateMacroServer", ("d",)), ("getMacroServer", ("d",)),
            ("getPools", ("d",)), ("isDoorRunning", ("ms",)),
            ("nonExistingChannels", ("d", [])), ("channelSource", ("c",)),
            ("getEnv", ("v", "ms")), ("setEnv", ("v", 1, "ms")),
            ("setEnvs", ({}, "ms")), ("usetEnv", ("v", "ms")),
            ("getSelectorEnv", ("d", [], {})),
            ("setSelectorEnv", ("d", {})),
            ("getScanEnv", ("d",)), ("setScanEnv", ("d", "{}")),
            ("createMntGrp", (None, "mg", "t")),
            ("deleteMntGrp", (None, "mg")),
            ("mntGrpConfiguration", ("dev",)),
            ("setMntGrpConfiguration", ("dev", "{}")),
            ("testMntGrpConfiguration", ("dev", "{}")),
        ]
        for name, args in calls:
            with self.assertRaises(NotImplementedError, msg=name):
                getattr(sb, name)(*args)

    def test_selector_env_like_macroserverpools(self):
        rnd = random.Random(12345)
        sb = ScanBackend()
        names = PUREVAR + ["ScanFile", "ComponentSelection", "UserData",
                           "Timer", "OrderedChannels", "Other"]
        for _ in range(300):
            new = {}
            for name in rnd.sample(names, rnd.randint(0, len(names))):
                key = name if name in ["ScanDir", "ScanFile"] \
                    else rnd.choice(["NeXus%s" % name, name])
                if key == name and name not in ["ScanDir", "ScanFile"]:
                    new.setdefault(NXSENV, {})[name] = random_value(rnd)
                else:
                    new[key] = random_value(rnd)
            dc = {'new': new}
            qnames = rnd.sample(names, rnd.randint(0, len(names)))
            expected = {}
            ref_getSelectorEnv(dc, qnames, expected)
            got = {}
            sb._readSelectorEnv(new, qnames, got)
            self.assertEqual(got, expected)

            data = dict((name, random_value(rnd)) for name in rnd.sample(
                names, rnd.randint(0, len(names))))
            cmddata = dict(("cmd%s" % i, random_value(rnd))
                           for i in range(rnd.randint(0, 3))) or None
            self.assertEqual(
                {'new': sb._selectorEnvUpdate(data, cmddata)},
                ref_setSelectorEnv({'new': {}}, data, cmddata))

    def test_scan_env_like_macroserverpools(self):
        rnd = random.Random(54321)
        sb = ScanBackend()
        params = ["ScanDir", "ScanFile", "ScanID", "NeXusSelectorDevice",
                  "ActiveMntGrp", "Other"]
        for _ in range(300):
            new = dict((p, rnd.choice([rnd.randint(0, 99), "f_%05d.nxs",
                                       ["a.nxs", "b.fio"], "/tmp"]))
                       for p in rnd.sample(params, rnd.randint(0, 6)))
            self.assertEqual(json.dumps(sb._readScanEnv(new)),
                             ref_getScanEnv({'new': new}))
            data = dict((p, rnd.choice([rnd.randint(0, 99), "x",
                                        ["a.nxs", "b.fio"], "/tmp"]))
                        for p in rnd.sample(params, rnd.randint(0, 6)))
            if "ScanID" in data:
                data["ScanID"] = rnd.randint(0, 99)
            refdc, _ = ref_setScanEnv({'new': {}}, json.dumps(data))
            self.assertEqual({'new': sb._scanEnvUpdate(data)}, refdc)

    def test_check_channels(self):
        backend = NullBackend(2)
        config = FakeConfigServer(components=["cp1"], datasources=["ds1"])
        errors = ["old"]
        # describing existing components needs a real configuration server,
        # so only missing components and datasources are checked here
        jcp, jds = backend.checkChannels(
            "", config, [], {"cp2": True, "cp3": False},
            {"ds2": True}, errors)
        self.assertEqual(json.loads(jcp), {"cp2": None, "cp3": False})
        self.assertEqual(json.loads(jds), {"ds2": None})
        self.assertEqual(len(errors), 2)
        messages = sorted(json.loads(er)["message"] for er in errors)
        self.assertTrue("cp2 not defined in Configuration Server"
                        in messages)


class BackendFactoryTest(unittest.TestCase):

    def test_backends(self):
        self.assertEqual(sorted(BACKENDS), ["bliss", "null", "sardana"])
        self.assertEqual(DEFAULTBACKEND, "sardana")
        self.assertTrue(issubclass(SardanaBackend, MacroServerPools))
        self.assertTrue(issubclass(MacroServerPools, ScanBackend))
        self.assertTrue(issubclass(NullBackend, ScanBackend))
        self.assertEqual(SardanaBackend.name, "sardana")
        self.assertTrue(SardanaBackend.supportsMntGrps)

    def test_create_null(self):
        for name in ["null", "NULL", "Null"]:
            backend = createBackend(name, 5)
            self.assertTrue(isinstance(backend, NullBackend))
            self.assertEqual(backend.name, "null")

    def test_create_wrong(self):
        with self.assertRaises(ValueError):
            createBackend("tine")

    @unittest.skipUnless(TANGODB, "tango database is not available")
    def test_create_default(self):
        for name in [None, "", "sardana", "Sardana"]:
            backend = createBackend(name, 5)
            self.assertTrue(isinstance(backend, SardanaBackend))


class NullBackendTest(unittest.TestCase):

    def test_targets(self):
        nb = NullBackend()
        self.assertFalse(nb.supportsMntGrps)
        self.assertEqual(nb.defaultDoor(None), "")
        self.assertTrue(nb.isDoorValid(""))
        self.assertTrue(nb.isDoorValid("p09/door/haso.01"))
        self.assertEqual(nb.updateMacroServer("p09/door/haso.01"), "")
        self.assertEqual(nb.getMacroServer(""), "")
        self.assertEqual(nb.getPools(""), [])
        self.assertFalse(nb.isDoorRunning(""))
        self.assertEqual(nb.nonExistingChannels("", ["a", "b"]), [])
        self.assertEqual(nb.channelSource("exp_c01"), None)

    def test_no_mntgrps(self):
        nb = NullBackend()
        for name, args in [("createMntGrp", (None, "mg", "t")),
                           ("deleteMntGrp", (None, "mg")),
                           ("mntGrpConfiguration", ("dev",)),
                           ("setMntGrpConfiguration", ("dev", "{}")),
                           ("testMntGrpConfiguration", ("dev", "{}"))]:
            with self.assertRaises(NotImplementedError):
                getattr(nb, name)(*args)

    def test_env(self):
        nb = NullBackend()
        self.assertEqual(nb.getEnv("ActiveMntGrp", ""), None)
        value = {"a": [1, 2]}
        nb.setEnv("Var", value, "")
        value["a"].append(3)
        self.assertEqual(nb.getEnv("Var", ""), {"a": [1, 2]})
        got = nb.getEnv("Var")
        got["a"].append(4)
        self.assertEqual(nb.getEnv("Var"), {"a": [1, 2]})
        nb.setEnvs({"ActiveMntGrp": "mg1", "ScanID": 3}, "")
        self.assertEqual(nb.getEnv("ActiveMntGrp"), "mg1")
        nb.usetEnv("ActiveMntGrp", "")
        nb.usetEnv("NotThere", "")
        self.assertEqual(nb.getEnv("ActiveMntGrp"), None)
        self.assertEqual(nb.environment,
                         {"Var": {"a": [1, 2]}, "ScanID": 3})

    def test_selector_env(self):
        nb = NullBackend()
        data = {"MntGrp": "mg1", "ScanDir": "/tmp/scans",
                "ScanFile": '["a.nxs"]', "UserData": '{"sample": "water"}',
                "ComponentSelection": '{"slit1": true}', "Timer": "[1"}
        nb.setSelectorEnv("", data, {"Cmd": 5})
        env = nb.environment
        self.assertEqual(env["ScanDir"], "/tmp/scans")
        self.assertEqual(env["ScanFile"], ["a.nxs"])
        self.assertEqual(env[NXSENV], {
            "MntGrp": "mg1", "UserData": {"sample": "water"},
            "ComponentSelection": {"slit1": True}, "Timer": "[1",
            "Cmd": 5})
        got = {}
        nb.getSelectorEnv("", list(data.keys()) + ["Cmd", "Missing"], got)
        self.assertEqual(got, {
            "MntGrp": "mg1", "ScanDir": "/tmp/scans",
            "ScanFile": '["a.nxs"]', "UserData": '{"sample": "water"}',
            "ComponentSelection": '{"slit1": true}', "Timer": "[1",
            "Cmd": 5})
        # NeXus<name> variables take precedence like in sardana
        nb.setEnv("NeXusMntGrp", "mg2")
        got = {}
        nb.getSelectorEnv("", ["MntGrp"], got)
        self.assertEqual(got, {"MntGrp": "mg2"})

    def test_scan_env(self):
        nb = NullBackend()
        self.assertEqual(json.loads(nb.getScanEnv("")), {})
        self.assertEqual(nb.setScanEnv("", json.dumps(
            {"ScanDir": "/tmp", "ScanFile": ["a.nxs", "b.fio"]})), -1)
        self.assertEqual(nb.setScanEnv("", json.dumps({"ScanID": 12})), 12)
        self.assertEqual(nb.setScanEnv("", json.dumps({"ScanDir": "/d"})),
                         12)
        self.assertEqual(json.loads(nb.getScanEnv("")), {
            "ScanDir": "/d", "ScanFile": ["a.nxs", "b.fio"], "ScanID": 12})


class DynamicComponentBackendTest(unittest.TestCase):

    def test_channel_source(self):
        dc = DynamicComponent(None, backend=FakeChannelBackend())
        find = dc._DynamicComponent__findDataSource
        self.assertEqual(
            find("exp_c01"),
            ("Counts", "p09/vmexecutor/exp.01", "haso", "10000"))
        self.assertEqual(find("unknown"), (None, None, None, None))
        dc = DynamicComponent(None, backend=NullBackend())
        find = dc._DynamicComponent__findDataSource
        self.assertEqual(find("exp_c01"), (None, None, None, None))
        self.assertEqual(
            find("tango://haso:10000/p09/vmexecutor/exp.01/Counts"),
            ("Counts", "p09/vmexecutor/exp.01", "haso", "10000"))


class ProfileManagerNullBackendTest(unittest.TestCase):

    def test_profile_without_mntgrps(self):
        nb = NullBackend()
        selector = FakeSelector(nb)
        pm = ProfileManager(selector)
        self.assertEqual(pm.availableMntGrps(), [])
        self.assertEqual(pm.getPoolMotors(), [])
        self.assertEqual(pm.mntGrpConfiguration(), "{}")
        self.assertTrue(pm.isMntGrpUpdated())

        self.assertEqual(pm.updateProfile(), "{}")
        self.assertEqual(selector.stored, 1)
        self.assertEqual(nb.getEnv("ActiveMntGrp"), "mymg")

        selector["Door"] = "somedoor"
        self.assertEqual(pm.updateProfile(resetDoor=True), "{}")
        self.assertEqual(selector["Door"], "")
        self.assertEqual(selector.stored, 2)

        pm.deleteProfile("mymg")
        self.assertEqual(selector.deleted, ["mymg"])
        self.assertEqual(nb.getEnv("ActiveMntGrp"), None)


@unittest.skipUnless(TANGODB, "tango database is not available")
class SelectorNullBackendTest(unittest.TestCase):

    def test_selector(self):
        nb = NullBackend()
        selector = Selector(nb, "4.14.0")
        self.assertTrue(selector.backend is nb)
        self.assertEqual(selector["Door"], "")
        self.assertTrue(selector.isDoorValid())
        self.assertEqual(selector.getPools(), [])
        self.assertEqual(selector.getMacroServer(), "")
        self.assertEqual(selector.poolElementNames("ExpChannelList"), [])

        selector["MntGrp"] = "mymg"
        selector["UserData"] = json.dumps({"sample": "water"})
        selector.exportEnv(cmddata={"Cmd": 1})
        self.assertEqual(nb.environment[NXSENV]["MntGrp"], "mymg")
        data = {}
        selector.importEnv(["MntGrp", "UserData"], data)
        self.assertEqual(data["MntGrp"], "mymg")
        self.assertEqual(json.loads(data["UserData"]), {"sample": "water"})

        selector.setScanEnvVariables(json.dumps({"ScanID": 7}))
        self.assertEqual(
            json.loads(selector.getScanEnvVariables()), {"ScanID": 7})


class MntGrpRuntimeKeysTest(unittest.TestCase):

    def conf(self, runtime=True):
        ch1 = {"name": "exp_c01", "index": 0, "enabled": True}
        ch2 = {"name": "lima", "index": 1, "enabled": True,
               "value_ref_enabled": True}
        if runtime:
            ch1["value_stream_ref"] = {}
            ch2["value_stream_ref"] = {"backend": "blissdata",
                                       "scan_key": "esrf:scan:1"}
        ctrl1 = {"synchronization": 0, "channels": {"expchan/c/1": ch1}}
        ctrl2 = {"units": {"0": {"channels": {"expchan/l/1": ch2}}}}
        if runtime:
            ctrl1["streamable"] = True
            ctrl2["units"]["0"]["streamable"] = True
        return {"label": "mg1", "timer": "exp_t01",
                "controllers": {"ctrl1": ctrl1, "ctrl2": ctrl2}}

    def test_strip(self):
        conf = self.conf()
        stripped = Utils.stripMntGrpRuntimeKeys(conf)
        self.assertEqual(stripped, self.conf(False))
        # the given configuration is not changed
        self.assertEqual(conf, self.conf())
        jconf = Utils.stripMntGrpRuntimeKeys(json.dumps(conf))
        self.assertEqual(json.loads(jconf), self.conf(False))
        # configurations of older Sardana versions stay the same
        self.assertEqual(Utils.stripMntGrpRuntimeKeys(self.conf(False)),
                         self.conf(False))
        self.assertTrue(Utils.compareDict(
            Utils.stripMntGrpRuntimeKeys(self.conf()),
            Utils.stripMntGrpRuntimeKeys(self.conf(False))))
        for value in ["{}", "", "[1]", "{wrong", "{\"controllers\": 3}"]:
            self.assertEqual(Utils.stripMntGrpRuntimeKeys(value),
                             value if value[:1] != "{" or value == "{wrong"
                             else json.dumps(json.loads(value)))


if __name__ == '__main__':
    unittest.main()
