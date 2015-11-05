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
## \file Utils.py
# tango utilities

"""  Tango Utilities """

import re
import PyTango
import time
import json
import pickle
import numpy
import fnmatch


## Miscellaneous Utilities
class Utils(object):
    """  Miscellaneous Utilities """

    ## copares two dictionaries
    # \param dct first dictinary
    # \param dct2 second dictinary
    # \returns if dictionaries are the same
    @classmethod
    def compareDict(cls, dct, dct2):
        if not isinstance(dct, dict):
            return False
        if not isinstance(dct2, dict):
            return False
        if len(dct.keys()) != len(dct2.keys()):
            return False
        status = True
        for k, v in dct.items():
            if k not in dct2.keys():
                status = False
                break
            if isinstance(v, dict):
                status = Utils.compareDict(v, dct2[k])
                if not status:
                    break
            else:
                if v != dct2[k]:
                    status = False
                    break
        return status

    ## provides datasource record from xml dom node
    # \param node xml DOM node
    # \returns datasource record
    @classmethod
    def getRecord(cls, node):
        res = ''
        host = None
        port = None
        dname = None
        rname = None
        device = node.getElementsByTagName("device")
        if device and len(device) > 0:
            if device[0].hasAttribute("hostname"):
                host = device[0].attributes["hostname"].value
            if device[0].hasAttribute("port"):
                port = device[0].attributes["port"].value
            if device[0].hasAttribute("name"):
                dname = device[0].attributes["name"].value

        record = node.getElementsByTagName("record")
        if record and len(record) > 0:
            if record[0].hasAttribute("name"):
                rname = record[0].attributes["name"].value
                if dname:
                    if host:
                        if not port:
                            port = '10000'
                        res = '%s:%s/%s/%s' % (host, port, dname, rname)
                    else:
                        res = '%s/%s' % (dname, rname)
                else:
                    res = rname
        return res

    ## converts string to json dictionary
    # \param string with list of item or json dictionary
    # \param toBool if true convert dictionary values to bool
    # \returns json dictionary
    @classmethod
    def stringToDictJson(cls, string, toBool=False):
        try:
            if not string or string == "Not initialised":
                return "{}"
            acps = json.loads(string)
            if not isinstance(acps, dict):
                raise AssertionError()
            jstring = string
        except (ValueError, AssertionError):
            lst = re.sub("[:,;]", " ", string).split()
            if len(lst) % 2:
                lst.append("")
            dct = dict(zip(*[iter(lst)] * 2))
            if toBool:
                for k in dct.keys():
                    dct[k] = False \
                        if dct[k].lower() == 'false' else True
            jstring = json.dumps(dct)
        return jstring

    ## converts string to json list
    # \param string with list of item or json list
    # \returns json list
    @classmethod
    def stringToListJson(cls, string):
        if not string or string == "Not initialised":
            return "[]"
        try:
            acps = json.loads(string)
            if not isinstance(acps, (list, tuple)):
                raise AssertionError()
            jstring = string
        except (ValueError, AssertionError):
            lst = re.sub("[:,;]", "  ", string).split()
            jstring = json.dumps(lst)
        return jstring

    ## converts list/dict/object of unicode/string to string object
    # \param obj given unicode/string object
    # \returns string object
    @classmethod
    def toString(cls, obj):
        if isinstance(obj, unicode):
            return str(obj)
        elif isinstance(obj, list):
            return [cls.toString(el) for el in obj]
        elif isinstance(obj, dict):
            return dict([(cls.toString(key), cls.toString(value))
                         for key, value in obj.iteritems()])
        else:
            return obj


## Tango Utilities
class TangoUtils(object):
    """  Tango Utilities """

    ## map of Tango:Numpy types
    tTnp = {PyTango.DevLong64: "int64", PyTango.DevLong: "int32",
            PyTango.DevShort: "int16", PyTango.DevUChar: "uint8",
            PyTango.DevULong64: "uint64", PyTango.DevULong: "uint32",
            PyTango.DevUShort: "uint16", PyTango.DevDouble: "float64",
            PyTango.DevFloat: "float32", PyTango.DevString: "string",
            PyTango.DevBoolean: "bool", PyTango.DevEncoded: "encoded"}

    ## opens device proxy of the given device
    # \param cls class instance
    # \param device device name
    # \returns DeviceProxy of device
    @classmethod
    def openProxy(cls, device):
        found = False
        cnt = 0
        cnfServer = PyTango.DeviceProxy(str(device))

        while not found and cnt < 1000:
            if cnt > 1:
                time.sleep(0.01)
            try:
                cnfServer.ping()
                found = True
            except (PyTango.DevFailed, PyTango.Except, PyTango.DevError):
                time.sleep(0.01)
                found = False
                if cnt == 999:
                    raise
            cnt += 1

        return cnfServer

    ## provides proxies of given device names
    # \param cls class instance
    # \param names given device names
    # \returns list of device DeviceProxies
    @classmethod
    def getProxies(cls, names):
        dps = []
        for name in names:
            dp = PyTango.DeviceProxy(str(name))
            try:
                dp.ping()
                dps.append(dp)
            except (PyTango.DevFailed, PyTango.Except, PyTango.DevError):
                pass
        return dps

    ## find device of give class
    # \param cls class instance
    # \param db tango database
    # \param cname device class name
    # \returns device name if exists
    @classmethod
    def getDeviceName(cls, db, cname):
        servers = db.get_device_exported_for_class(
            cname).value_string
        device = ''
        for server in servers:
            try:
                dp = PyTango.DeviceProxy(str(server))
                dp.ping()
                device = server
                break
            except (PyTango.DevFailed, PyTango.Except, PyTango.DevError):
                pass
        return device

    ## retrives shape type value for attribure
    @classmethod
    def getShapeTypeUnit(cls, source):
        vl = None
        shp = []
        dt = 'float64'
        ut = 'No units'
        ap = PyTango.AttributeProxy(source)
        da = None
        ac = None

        try:
            ac = ap.get_config()
            if ac.data_format != PyTango.AttrDataFormat.SCALAR:
                da = ap.read()
                vl = da.value
        except (PyTango.DevFailed, PyTango.Except, PyTango.DevError):
            if ac and ac.data_format != PyTango.AttrDataFormat.SCALAR \
                    and (da is None or not hasattr(da, 'dim_x')):
                raise

        if vl is not None:
            shp = list(numpy.shape(vl))
        elif ac is not None:
            if ac.data_format != PyTango.AttrDataFormat.SCALAR:
                if da.dim_x and da.dim_x > 1:
                    shp = [da.dim_y, da.dim_x] \
                        if da.dim_y \
                        else [da.dim_x]
        if ac is not None:
            dt = cls.tTnp[ac.data_type]
            ut = ac.unit
        return (shp, dt, ut)

    ## executes command on server
    # \returns command result
    @classmethod
    def command(cls, server, command, *var):
        if not hasattr(server, "command_inout"):
            return getattr(server, command)(*var)
        elif var is None:
            return server.command_inout(command)
        else:
            return server.command_inout(command, *var)


## MacroServer Utilities
class MSUtils(object):
    """  MacroServer Utilities """

    ## provides environment variable value
    # \param cls class instance
    ## \param var variable name
    ## \param ms macroserver
    @classmethod
    def getEnv(cls, var, ms):
        active = ""
        dp = TangoUtils.openProxy(ms)
        rec = dp.Environment
        if rec[0] == 'pickle':
            dc = pickle.loads(rec[1])
            if 'new' in dc.keys() and \
                    var in dc['new'].keys():
                active = dc['new'][var]
        return active

    ## sets environment variable value
    # \param cls class instance
    ## \param var variable name
    ## \param value variable value
    ## \param ms macroserver
    @classmethod
    def setEnv(cls, var, value, ms):
        dp = TangoUtils.openProxy(ms)
        rec = dp.Environment
        if rec[0] == 'pickle':
            dc = pickle.loads(rec[1])
            if 'new' in dc.keys():
                dc['new'][var] = value
                pk = pickle.dumps(dc)
                dp.Environment = ['pickle', pk]

    ## unsets environment variable
    # \param cls class instance
    ## \param var variable name
    ## \param ms macroserver
    @classmethod
    def usetEnv(cls, var,  ms):
        dp = TangoUtils.openProxy(ms)
        rec = dp.Environment
        if rec[0] == 'pickle':
            dc = pickle.loads(rec[1])
            if 'new' in dc.keys():
                if var in dc['new']:
                    dc['new'].pop(var)
                pk = pickle.dumps(dc)
                dp.Environment = ['pickle', pk]

    ## provides macro server of given door
    # \param cls class instance
    # \param db tango database
    # \param door given door
    # \returns first macro server of given door
    @classmethod
    def getMacroServer(cls, db, door):
        servers = db.get_device_exported_for_class(
            "MacroServer").value_string
        ms = ""
        sdoor = door.split("/")
        if len(sdoor) > 1 and ":" in sdoor[0]:
            door = "/".join(sdoor[1:])
        for server in servers:
            dp = PyTango.DeviceProxy(str(server))
            if hasattr(dp, "DoorList"):
                lst = dp.DoorList
                if lst and door in lst:
                    ms = server
                    break
        return ms


## Pool Utilities
class PoolUtils(object):
    """  Pool Utilities """

    ## provides device controller full names
    # \param cls class instance
    # \param pools list of pool devices
    # \param devices alias names
    # \returns device controller full names
    @classmethod
    def getDeviceControllers(cls, pools, devices):
        lst = []
        for pool in pools:
            if pool.ExpChannelList:
                lst += pool.ExpChannelList
        ctrls = {}
        for elm in lst:
            chan = json.loads(elm)
            if chan['name'] in devices:
                ctrls[chan['name']] = chan['controller']
        return ctrls

    ## provides channel sources
    # \param cls class instance
    # \param pools list of pool devices
    # \param devices alias names
    # \returns device sources
    @classmethod
    def getChannelSources(cls, pools, devices):
        lst = []
        for pool in pools:
            if pool.ExpChannelList:
                lst += pool.ExpChannelList
        srs = {}
        for elm in lst:
            chan = json.loads(elm)
            if chan['name'] in devices:
                srs[chan['name']] = chan['source']
        return srs

    ## provides experimental Channels
    # \param cls class instance
    # \param pools list of pool devices
    # \returns experimental channel names
    @classmethod
    def getExperimentalChannels(cls, pools):
        lst = []
        channels = []
        for pool in pools:
            if pool.ExpChannelList:
                lst += pool.ExpChannelList
        for elm in lst:
            if elm:
                chan = json.loads(elm)
                if chan and isinstance(chan, dict):
                    channels.append(chan['name'])
        return channels

    ## provides motor names
    # \param cls class instance
    # \param pools list of pool devices
    # \returns motor names
    @classmethod
    def getMotorNames(cls, pools):
        lst = []
        motors = []
        for pool in pools:
            if pool.MotorList:
                lst += pool.MotorList
        for elm in lst:
            if elm:
                chan = json.loads(elm)
                if chan and isinstance(chan, dict):
                    motors.append(chan['name'])
        return motors

    ## find device names from aliases
    # \param cls class instance
    # \param pools list of pool devices
    # \param names alias names if None returns name for all aliases
    # \returns full device name
    @classmethod
    def getFullDeviceNames(cls, pools, names=None):
        lst = []
        for pool in pools:
            if pool.AcqChannelList:
                lst += pool.AcqChannelList
        argout = {}
        for elm in lst:
            chan = json.loads(elm)
            if names is None or chan['name'] in names:
                arr = chan['full_name'].split("/")
                argout[chan['name']] = "/".join(arr[0:-1])
        return argout

    ## find aliases from fullnames
    # \param cls class instance
    # \param pools list of pool devices
    # \param names fullnames if None returns all aliases
    # \returns full device name
    @classmethod
    def getAliases(cls, pools, names=None):
        lst = []
        for pool in pools:
            if pool.AcqChannelList:
                lst += pool.AcqChannelList
        argout = {}
        for elm in lst:
            chan = json.loads(elm)
            arr = chan['full_name'].split("/")
            fname = "/".join(arr[0:-1])
            if names is None or fname in names:
                argout[fname] = chan['name']
        return argout

    ## find measurement group from alias
    # \param cls class instance
    # \param pools list of pool devices
    # \returns name of measurement group
    @classmethod
    def getMntGrps(cls, pools):
        lst = []
        for pool in pools:
            if pool.MeasurementGroupList:
                lst += pool.MeasurementGroupList
        argout = []
        for elm in lst:
            chan = json.loads(elm)
            argout.append(chan['name'])
        return argout

    ## find measurement group from alias
    # \param cls class instance
    # \param pools list of pool devices
    # \param alias mntgrp alias
    # \returns full name of   measurement group
    @classmethod
    def getMntGrpName(cls, pools, alias):
        lst = []
        for pool in pools:
            if pool.MeasurementGroupList:
                lst += pool.MeasurementGroupList
        argout = ""
        for elm in lst:
            chan = json.loads(elm)
            if alias == chan['name']:
                argout = chan['full_name']
                break
        return argout

    ## provides tiemrs of given pools
    # \param cls class instance
    # \param pools list of pool devices
    # \param filters device name filter list
    # \returns list of timer names
    @classmethod
    def getTimers(cls, pools, filters=None):
        lst = []
        res = []
        for pool in pools:
            if pool.ExpChannelList:
                lst += pool.ExpChannelList

        if not filters or not hasattr(filters, '__iter__'):
            filters = ["*dgg*", "*/ctctrl0*"]
        for elm in lst:
            chan = json.loads(elm)
            inter = chan['interfaces']
            source = chan['source']
            if isinstance(inter, (list, tuple)):
                if 'CTExpChannel' in inter:
                    found = False
                    for df in filters:
                        found = fnmatch.filter([source], df)
                        if found:
                            break
                    if found:
                        res.append(chan['name'])
        return res

    ## provides datasource from pool device
    # \param name pool device name
    # \returns source of pool device
    @classmethod
    def getSource(cls, name):
        source = None
        try:
            dp = PyTango.DeviceProxy(str(name))
            if hasattr(dp, 'DataSource'):
                ds = dp.DataSource
                sds = ds.split("://")
                _ = PyTango.AttributeProxy(sds[-1])
                source = sds[-1]
        except (PyTango.DevFailed, PyTango.Except, PyTango.DevError):
            pass
        return source
