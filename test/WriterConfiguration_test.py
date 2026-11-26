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
# \file WriterConfiguration_test.py
# unittests for the writer configuration of a selector profile
#
import json
import unittest

import numpy

from nxsrecconfig.WriterConfiguration import (
    WriterConfiguration, NumpyEncoder)


class Desc(object):
    """ sardana channel description stand-in """

    def __init__(self, name, shape=None, dtype="float64"):
        self.name = name
        self.shape = shape or []
        self.dtype = dtype


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


class FakeSelector(object):
    """ selector stand-in recording commands """

    def __init__(self, components=None, cpsources=None, selected=None,
                 mandatory=None, timers=None, available=None):
        self.components = list(components or [])
        self.cpsources = cpsources or {}
        self.selected = list(selected or [])
        self.mandatory = list(mandatory or [])
        self.timers = list(timers or [])
        self.available = list(available or self.cpsources.keys())
        self.configVariables = json.dumps({"keep": "me"})
        self.stepdatasources = '["old"]'
        self.linkdatasources = '[]'
        self.cachecomponent = ""
        self.calls = []
        self.writerConfVars = None
        self.writerStepDss = None

    def availableComponents(self):
        return list(self.available)

    def selectedDataSources(self):
        self.calls.append("selectedDataSources")
        return list(self.selected)

    def mandatoryComponents(self):
        return list(self.mandatory)

    def componentSources(self, cps):
        return json.dumps(self.cpsources.get(cps[0], []))

    def availableTimers(self):
        return list(self.timers)

    def createDynamicComponent(self, params):
        self.calls.append(("createDynamicComponent", params))
        return "__dynamic_component__1"

    def removeDynamicComponent(self, name):
        self.calls.append(("removeDynamicComponent", name))

    def updateConfigVariables(self):
        self.calls.append("updateConfigVariables")

    def createWriterConfiguration(self, cps):
        self.writerConfVars = json.loads(self.configVariables)
        self.writerStepDss = json.loads(self.stepdatasources)
        self.calls.append(("createWriterConfiguration", sorted(cps)))
        return "<definition/>"


def source(name, strategy="STEP", dstype="CLIENT", record=None):
    return {"dsname": name, "strategy": strategy, "dstype": dstype,
            "record": record or name, "parentobj": "field"}


ALIASES = {"tango://haso:10000/expchan/ctctrl01/1": "exp_c01",
           "expchan/ctctrl01/2": "exp_c02",
           "motor/motctrl01/1": "mot01"}


def getalias(name):
    """ alias lookup like tango: names without '/' are aliases """
    return name if "/" not in name else ALIASES.get(name)


class WriterConfigurationTest(unittest.TestCase):

    def profile(self, **kwargs):
        conf = {
            "ComponentsFromMntGrp": False,
            "DynamicComponents": True,
            "OptionalComponents": json.dumps([]),
            "DataSourcePreselection": json.dumps({"ds_init": True,
                                                  "ds_off": False}),
            "ConfigVariables": json.dumps({"entryname": "scan"}),
            "OrderedChannels": json.dumps(["exp_c02", "exp_c01", "mot01"]),
        }
        conf.update(kwargs)
        return conf

    def env(self):
        return {
            "ref_moveables": ["mot01"],
            "datadesc": [Desc("tango://haso:10000/expchan/ctctrl01/1"),
                         Desc("expchan/ctctrl01/2", [2], "int32"),
                         Desc("motor/motctrl01/1")],
        }

    def test_create(self):
        selector = FakeSelector(
            components=["slit1"],
            cpsources={"slit1": [source("exp_c01"),
                                 source("ds_init", "INIT", "TANGO")]},
            selected=["exp_c01", "exp_c02"],
            mandatory=["default"], timers=["exp_t01"])
        variables = {"serialno": "_00012"}
        log = Log()
        wc = WriterConfiguration(selector, self.profile(), variables, log,
                                 getalias=getalias)
        userdata = {"title": "my scan"}
        xml = wc.create(self.env(), userdata)
        self.assertEqual(xml, "<definition/>")

        # channels without components go to the dynamic component
        dcp = [c for c in selector.calls
               if c[0] == "createDynamicComponent"][0][1]
        stepdss = json.loads(dcp[0])
        self.assertEqual(sorted(stepdss), ["exp_c02", "mot01"])
        channels = json.loads(dcp[1])
        names = sorted(ch["name"] for ch in channels)
        self.assertEqual(names, ["expchan/ctctrl01/2", "motor/motctrl01/1",
                                 "title"])
        self.assertTrue({"name": "expchan/ctctrl01/2", "shape": [2],
                         "dtype": "int32", "strategy": "STEP"} in channels)
        self.assertTrue({"name": "title", "shape": [], "dtype": "str",
                         "strategy": "INIT"} in channels)
        self.assertEqual(json.loads(dcp[2]), ["ds_init"])

        # writer configuration of the selected and dynamic components
        self.assertEqual(
            selector.calls[-1],
            ("createWriterConfiguration",
             sorted(["slit1", "__dynamic_component__1"])))
        self.assertEqual(wc.dynamicCP, "__dynamic_component__1")
        self.assertEqual(selector.writerConfVars["entryname"], "scan")
        self.assertEqual(selector.writerConfVars["serialno"], "_00012")
        self.assertEqual(
            sorted(selector.writerConfVars["nexus_components"].split()),
            sorted(["slit1", "__dynamic_component__1"]))
        self.assertEqual(selector.writerConfVars["mgchannels"],
                         "exp_c02 exp_c01 mot01")
        self.assertEqual(selector.writerConfVars["timers"], "exp_t01")
        step = selector.writerConfVars["nexus_step_datasources"].split()
        self.assertEqual(step[0], "mot01")
        self.assertEqual(sorted(step), ["exp_c01", "exp_c02", "mot01"])
        self.assertEqual(selector.writerConfVars["nexus_init_datasources"],
                         "title ds_init")
        self.assertEqual(sorted(selector.writerStepDss),
                         ["exp_c01", "exp_c02", "mot01"])
        self.assertTrue("updateConfigVariables" in selector.calls)

        # selector variables are restored
        self.assertEqual(json.loads(selector.configVariables),
                         {"entryname": "scan"})
        self.assertEqual(selector.stepdatasources, '["old"]')
        self.assertEqual(variables["nexus_components"],
                         selector.writerConfVars["nexus_components"])
        self.assertEqual(userdata, {"title": "my scan"})
        self.assertEqual(wc.aliases, ["exp_c02", "exp_c01", "mot01"])

        wc.removeDynamicComponent()
        self.assertEqual(selector.calls[-1],
                         ("removeDynamicComponent",
                          "__dynamic_component__1"))

    def test_user_data_keys(self):
        selector = FakeSelector(
            components=["slit1"],
            cpsources={"slit1": [source("sample_name", "INIT")]})
        wc = WriterConfiguration(selector, self.profile(), {}, Log(),
                                 getalias=getalias)
        userdata = {"sample_name": "water", "beam energy": 7.5,
                    "beam energy@units": "keV"}
        wc.create({"datadesc": []}, userdata)
        dcp = [c for c in selector.calls
               if c[0] == "createDynamicComponent"][0][1]
        channels = json.loads(dcp[1])
        self.assertEqual(channels, [
            {"name": "beam_energy", "shape": [], "dtype": "float",
             "strategy": "INIT", "units": "keV"}])
        self.assertEqual(userdata["beam_energy"], 7.5)
        self.assertEqual(userdata["sample_name"], "water")

    def test_odd_mntgrp(self):
        selector = FakeSelector(
            components=["slit1"],
            cpsources={"slit1": [source("exp_c01")]},
            selected=["exp_c01"])
        log = Log()
        wc = WriterConfiguration(selector, {}, {}, log,
                                 getalias=getalias, oddmntgrp=True)
        wc.create(self.env(), {})
        self.assertTrue("selectedDataSources" not in selector.calls)
        # no user components, the channels go to the dynamic component
        dcp = [c for c in selector.calls
               if c[0] == "createDynamicComponent"][0][1]
        self.assertEqual(sorted(json.loads(dcp[0])),
                         ["exp_c01", "exp_c02", "mot01"])
        self.assertEqual(log.warnings(), ["ConfigVariables cannot be found"])

    def test_cache_component(self):
        selector = FakeSelector(
            components=["slit1"],
            cpsources={"__configuration_mg1": [source("exp_c01"),
                                               source("mot01")]},
            selected=["exp_c01"])
        selector.cachecomponent = "__configuration_mg1"
        wc = WriterConfiguration(selector, self.profile(), {}, Log(),
                                 getalias=getalias,
                                 moveables=lambda: ["mot01", "mot02"])
        wc.create(self.env(), {})
        self.assertEqual(wc.moveableDataSources, ["mot01"])
        dcp = [c for c in selector.calls
               if c[0] == "createDynamicComponent"][0][1]
        self.assertEqual(sorted(json.loads(dcp[2])), ["ds_init", "mot01"])
        self.assertEqual(
            selector.calls[-1],
            ("createWriterConfiguration",
             sorted(["__configuration_mg1", "__dynamic_component__1"])))

    def test_no_dynamic_components(self):
        selector = FakeSelector(
            components=["slit1"],
            cpsources={"slit1": [source("exp_c01")]},
            selected=["exp_c01"])
        log = Log()
        wc = WriterConfiguration(
            selector, self.profile(DynamicComponents=False), {}, log,
            getalias=getalias)
        wc.create(self.env(), {})
        dcp = [c for c in selector.calls
               if c[0] == "createDynamicComponent"][0][1]
        self.assertEqual(json.loads(dcp[0]), [])
        warnings = log.warnings()
        self.assertTrue(any("'exp_c02' will not be stored" in w
                            for w in warnings))
        self.assertTrue(any("'mot01' will not be stored" in w
                            for w in warnings))

    def test_dict_channels(self):
        selector = FakeSelector(components=[], cpsources={})
        wc = WriterConfiguration(
            selector, self.profile(), {}, Log(),
            getalias=lambda name: name.split(":")[-1])
        wc.create({"datadesc": [
            {"name": "diode:diode", "shape": [], "dtype": "float64"},
            {"name": "lima:image", "shape": [512, 512], "dtype": "uint16"}]},
            {})
        dcp = [c for c in selector.calls
               if c[0] == "createDynamicComponent"][0][1]
        self.assertEqual(sorted(json.loads(dcp[0])), ["diode", "image"])
        self.assertEqual(sorted(ch["name"] for ch in json.loads(dcp[1])),
                         ["diode:diode", "lima:image"])

    def test_vars_and_encoder(self):
        selector = FakeSelector()
        selector.profileConfiguration = "{"
        log = Log()
        wc = WriterConfiguration(selector, {"A": "{", "B": '{"x": 1}'},
                                 log=log)
        self.assertEqual(wc.confVar("A", 5, True), 5)
        self.assertEqual(wc.confVar("B", 5, True), {"x": 1})
        self.assertEqual(wc.confVar("B", 5), '{"x": 1}')
        self.assertEqual(wc.confVar("C", 6), 6)
        self.assertEqual(wc.confVar("B", 7, pass_default=True), 7)
        self.assertEqual(wc.serverVar("profileConfiguration", 8, True), 8)
        self.assertEqual(wc.serverVar("stepdatasources", 8, True), ["old"])
        self.assertEqual(log.warnings(), [
            "A = '{' cannot be decoded", "C cannot be found",
            "profileConfiguration = '{' cannot be decoded"])
        self.assertEqual(
            WriterConfiguration.shortName("tango://haso:10000/a/b/c"),
            "a/b/c")
        self.assertEqual(WriterConfiguration.shortName("exp_c01"),
                         "exp_c01")
        self.assertEqual(
            json.loads(json.dumps(
                [numpy.int16(3), numpy.float32(1.5), numpy.bool_(True),
                 numpy.array([1, 2])], cls=NumpyEncoder)),
            [3, 1.5, True, [1, 2]])


if __name__ == '__main__':
    unittest.main()
