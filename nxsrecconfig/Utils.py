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

"""  Tango Utilities """

import re
import PyTango
import time
import json
import pickle
import numpy
import fnmatch
import socket
import sys

if sys.version_info > (3,):
    unicode = str


#: (:obj:`bool`) PyTango bug #213 flag related to EncodedAttributes in python3
PYTG_BUG_213 = False
if sys.version_info > (3,):
    try:
        PYTGMAJOR, PYTGMINOR, PYTGPATCH = list(
            map(int, PyTango.__version__.split(".")[:3]))
        if PYTGMAJOR <= 9:
            if PYTGMAJOR == 9:
                if PYTGMINOR < 2:
                    PYTG_BUG_213 = True
                elif PYTGMINOR == 2 and PYTGPATCH <= 4:
                    PYTG_BUG_213 = True
            else:
                PYTG_BUG_213 = True
    except Exception:
        pass


class OldTangoError(Exception):

    """ Old Tango version Exception class
    """


class Utils(object):

    """  Miscellaneous Utilities """

    @classmethod
    def tostr(cls, text):
        """ convert bytestr or unicode to python str
        :param text: text to convert
        :type text: :obj:`bytes` or :obj:`unicode` or :obj:`str`
        :returns: converted text
        :rtype: :obj:`str`
        """
        if isinstance(text, str):
            return text
        else:
            if sys.version_info > (3,) and \
               (isinstance(text, bytes) or isinstance(text, unicode)):
                return str(text, "utf8")
            else:
                return str(text)

    @classmethod
    def pickleloads(cls, bytestr):
        """ loads pickle byte string
        :param bytestr: byte string to convert
        :type bytesstr: :obj:`bytes`
        :returns: loaded bytestring
        :rtype: :obj:`any`
        """
        if sys.version_info > (3,):
            return pickle.loads(bytestr, encoding='latin1')
        else:
            return pickle.loads(bytestr)

    @classmethod
    def compareDict(cls, dct, dct2):
        """ copares two dictionaries

        :param dct: first dictinary
        :type dct: :obj:`dict`
        :param dct2: second dictinary
        :type dct2: :obj:`dict`
        :returns: if dictionaries are the same
        :rtype: :obj:`bool`
        """
        if not isinstance(dct, dict):
            return False
        if not isinstance(dct2, dict):
            return False
        if len(list(dct.keys())) != len(list(dct2.keys())):

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

    @classmethod
    def getRecord(cls, node):
        """ provides datasource record from xml dom node

        :param node: xml DOM node
        :type node: :class:`lxml.etree.Element`
        :returns: datasource record
        :rtype: :obj:`str`
        """
        res = ''
        host = None
        port = None
        dname = None
        rname = None
        member = None
        device = node.findall("device")
        if device is not None and len(device) > 0:
            host = device[0].get("hostname")
            port = device[0].get("port")
            dname = device[0].get("name")
            member = device[0].get("member")

        surfix = ""
        prefix = ""
        if member or member != 'attribute':
            if member == 'property':
                prefix = '@'
            elif member == 'command':
                surfix = '()'

        record = node.findall("record")
        if record is not None and len(record) > 0:
            rname = record[0].get("name")
            if rname:
                if dname:
                    if host:
                        if not port:
                            port = '10000'
                        res = '%s:%s/%s/%s%s%s' % (
                            host, port, dname, prefix, rname, surfix)
                    else:
                        res = '%s/%s%s%s' % (dname, prefix, rname, surfix)
                else:
                    res = rname
        return res

    @classmethod
    def getText(cls, node):
        """ collects text from text child nodes

        :param node: parent node
        :type node: :obj:`xml.etree.ElementTree.Element`
        """
        if node is not None:
            tnodes = ([node.text] if node.text else []) \
                     + [child.tail for child in node if child.tail]
            return unicode("".join(tnodes)).strip()
        return ""

    @classmethod
    def stringToDictJson(cls, string, toBool=False):
        """ converts string to json dictionary

        :param string: string with list of item or json dictionary
        :type string: :obj:`str`
        :param toBool: if true convert dictionary values to bool
        :type toBool: :obj:`bool`
        :returns: json dictionary
        :rtype: :obj:`str`
        """
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

    @classmethod
    def stringToListJson(cls, string):
        """ converts string to json list

        :param string: with list of item or json list
        :type string: :obj:`str`
        :returns: json list
        :rtype: :obj:`str`
        """
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

    @classmethod
    def toString(cls, obj):
        """ converts list/dict/object of unicode/string to string object

        :param obj: given unicode/string object
        :type obj: `any`
        :returns: string object
        :rtype: :obj:`str`
        """
        if isinstance(obj, unicode) or isinstance(obj, bytes):
            return Utils.tostr(obj)
        elif isinstance(obj, list):
            return [cls.toString(el) for el in obj]
        elif isinstance(obj, dict):
            return dict([(cls.toString(key), cls.toString(value))
                         for key, value in obj.items()])
        else:
            return obj


class TangoUtils(object):

    """  Tango Utilities """

    #: (:obj:`dict` <:class:`PyTango.CmdArgType`, :obj:`str`>)
    #: map of Tango:Numpy types
    tTnp = {PyTango.DevLong64: "int64", PyTango.DevLong: "int32",
            PyTango.DevShort: "int16", PyTango.DevUChar: "uint8",
            PyTango.DevULong64: "uint64", PyTango.DevULong: "uint32",
            PyTango.DevUShort: "uint16", PyTango.DevDouble: "float64",
            PyTango.DevFloat: "float32", PyTango.DevString: "string",
            PyTango.DevBoolean: "bool", PyTango.DevEncoded: "encoded"}

    @classmethod
    def openProxy(cls, device, counter=1000):
        """ opens device proxy of the given device

        :param device: device name
        :type device: :obj:`str`
        :returns: DeviceProxy of device
        :rtype: :class:`PyTango.DeviceProxy`
        """
        found = False
        cnt = 0
        cnfServer = PyTango.DeviceProxy(Utils.tostr(device))

        while not found and cnt < counter:
            if cnt > 1:
                time.sleep(0.01)
            try:
                cnfServer.ping()
                found = True
            except PyTango.DevFailed:
                time.sleep(0.01)
                found = False
                if cnt == counter - 1:
                    raise
            cnt += 1
        cnfServer.set_source(PyTango.DevSource.DEV)
        return cnfServer

    @classmethod
    def wait(cls, proxy, counter=100, state="RUNNING"):
        """waits for device proxy not running

        :param proxy: device proxy
        :type proxy: :class:`PyTango.DeviceProxy`
        :returns: if proxy device ready
        :rtype: :obj:`str`
        """

        dstate = getattr(PyTango.DevState, state) if state else None
        found = False
        cnt = 0
        while not found and cnt < counter:
            if cnt > 1:
                time.sleep(0.01)
            try:
                pstate = proxy.state()
                if dstate:
                    if pstate != dstate:
                        found = True
                else:
                    found = True
            except PyTango.DevFailed:
                time.sleep(0.01)
                found = False
                if cnt == counter - 1:
                    raise
            cnt += 1
        return found

    @classmethod
    def getProxies(cls, names):
        """ provides proxies of given device names

        :param names: given device names
        :type names: :obj:`list` <:obj:`str`>
        :returns: list of device DeviceProxies
        :rtype: :obj:`list` <:class:`PyTango.DeviceProxy`>
        """
        dps = []
        for name in names:
            dp = PyTango.DeviceProxy(Utils.tostr(name))
            try:
                dp.ping()
                dps.append(dp)
            except PyTango.DevFailed:
                pass
        return dps

    @classmethod
    def getDeviceName(cls, db, cname):
        """ finds device of give class

        :param db: tango database
        :type db: :class:`PyTango.DeviceProxy`
        :param cname: device class name
        :type cname: :obj:`str`
        :returns: device name if exists
        :rtype: :obj:`bool`
        """
        servers = db.get_device_exported_for_class(
            cname).value_string
        device = ''
        for server in servers:
            try:
                dp = PyTango.DeviceProxy(Utils.tostr(server))
                dp.ping()
                device = server
                break
            except PyTango.DevFailed:
                pass
        return device

    @classmethod
    def getFullAttrName(cls, source, fqdn=False):
        """ provides tango device full name with host and port

        :param source: string with device name and its attribute
        :type source: :obj:`str`
        :param fqdn: if true adds fqdn host name
        :type fqdn: :obj:`bool`
        :returns: database host and port in url string
        :rtype: :obj:`str`
        """
        if ':' in source:
            if not fqdn:
                return "tango://%s" % source
            else:
                lsource = source.split(":")
                lsource[0] = socket.getfqdn(lsource[0])

                return "tango://%s" % ":".join(lsource)

        else:
            db = PyTango.Database()
            host, port = db.get_db_host(), db.get_db_port()
            if fqdn:
                host = socket.getfqdn(host)
            return "tango://%s:%s/%s" % (host, port, source)

    @classmethod
    def getShapeTypeUnit(cls, source):
        """ retrives shape type units for attribure

        :param source: string with device name and its attribute
        :type source: :obj:`str`
        :returns: (shape, data_type, units)
        :rtype: (:obj:`list` <:obj:`int`>, :obj:`str`, :obj:`str`)
        """
        vl = None
        shp = []
        dt = 'float64'
        ut = 'No unit'
        ap = PyTango.AttributeProxy(source)
        da = None
        ac = None

        try:
            ac = ap.get_config()
            if ac.data_format != PyTango.AttrDataFormat.SCALAR:
                da = ap.read()
                vl = da.value
        except PyTango.DevFailed:
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

    @classmethod
    def command(cls, server, command, *var):
        """ executes command on server on python package

        :param server: tango server name or package name
        :type server: :class:`PyTango.DeviceProxy` \
             or :class:`nxsconfigserver.XMLConfigurator.XMLConfigurator`
        :param command: command name
        :type command: :obj:`str`
        :param var: command variable list
        :type var: [ `any` ]
        :returns: command result
        :rtype: `any`
        """
        if not hasattr(server, "command_inout"):
            return getattr(server, command)(*var)
        elif var is None:
            return server.command_inout(command)
        else:
            return server.command_inout(command, *var)


class MSUtils(object):

    """  MacroServer Utilities """

    @classmethod
    def getEnv(cls, var, ms):
        """ provides environment variable value

        :param var: variable name
        :type var: :obj:`str`
        :param ms: macroserver
        :type ms: :obj:`str`
        :returns: environment variable value
        :rtype: `any`
        """
        active = ""
        dp = TangoUtils.openProxy(ms)
        if PYTG_BUG_213:
            raise OldTangoError(
                "Reading Encoded Attributes not supported in PyTango < 9.2.5")
        rec = dp.Environment
        if rec[0] == 'pickle':
            dc = Utils.pickleloads(rec[1])
            if 'new' in dc.keys() and \
                    var in dc['new'].keys():
                active = dc['new'][var]
        return active

    @classmethod
    def setEnv(cls, var, value, ms):
        """ sets environment variable value

        :param var: variable name
        :type var: :obj:`str`
        :param value: variable value
        :type value: `any`
        :param ms: macroserver
        :type ms: :obj:`str`
        """
        dp = TangoUtils.openProxy(ms)
        dc = {'new': {}}
        dc['new'][var] = value
        MSUtils.writeEnvAttr(dc, dp)

    @classmethod
    def setEnvs(cls, varvalues, ms):
        """ sets environment variable value

        :param varvalues: variable value dictionary
        :type varvalues: :obj:`dict` <:obj:`str` , `any`>
        :param ms: macroserver
        :type ms: :obj:`str`
        """
        dp = TangoUtils.openProxy(ms)
        dc = {'new': {}}
        for var, value in varvalues.items():
            dc['new'][var] = value
        MSUtils.writeEnvAttr(dc, dp)

    @classmethod
    def usetEnv(cls, var, ms):
        """ unsets environment variable

        :param var: variable name
        :type var: :obj:`str`
        :param ms: macroserver
        :type ms: :obj:`str`
        """
        dp = TangoUtils.openProxy(ms)
        dc = {'del': [var]}
        MSUtils.writeEnvAttr(dc, dp)

    @classmethod
    def getMacroServer(cls, db, door):
        """ provides macro server of given door

        :param db: tango database
        :type db: :class:`PyTango.Database`
        :param door: given door
        :type door: :obj:`str`
        :returns: first MacroServer of the given door
        :rtype: :obj:`str`
        """
        servers = db.get_device_exported_for_class(
            "MacroServer").value_string
        ms = ""
        sdoor = door.split("/")
        hostname = None
        if len(sdoor) > 1 and ":" in sdoor[0]:
            door = "/".join(sdoor[1:])
            hostname = sdoor[0]
        for server in servers:
            if hostname:
                mserver = "%s/%s" % (hostname, Utils.tostr(server))
            else:
                mserver = Utils.tostr(server)
            dp = PyTango.DeviceProxy(Utils.tostr(mserver))
            if hasattr(dp, "DoorList") and dp.DoorList:
                lst = [str(dr).lower() for dr in dp.DoorList]
                if lst and door.lower() in lst:
                    ms = mserver
                    break
        return ms

    @classmethod
    def writeEnvAttr(cls, value, dp):
        """ sets environment variable value

        :param value: variable value dictionary
        :type value: :obj:`dict` <:obj:`str` , `any`> or `any`
        :param dp: macroserver
        :type dp: :obj:`str`
        """
        if PYTG_BUG_213:
            raise OldTangoError(
                "Writing Encoded Attributes not supported in PyTango < 9.2.5")
        try:
            pk = pickle.dumps(value, protocol=2)
            dp.Environment = ['pickle', pk]
        except Exception:
            if sys.version_info < (3,):
                raise
            if isinstance(value, dict):
                newvalue = {}
                for key, vl in value.items():
                    if isinstance(vl, dict):
                        nvl = {}
                        for ky, it in vl.items():
                            nvl[bytes(ky, "utf8")
                                if isinstance(ky, unicode) else ky] = it
                        newvalue[bytes(key, "utf8")
                                 if isinstance(key, unicode) else key] = nvl
                    else:
                        newvalue[bytes(key, "utf8")
                                 if isinstance(key, unicode) else key] = vl
            else:
                newvalue = value
            pk = pickle.dumps(newvalue, protocol=2)
            dp.Environment = ['pickle', pk]


class PoolUtils(object):

    """  Pool Utilities """

    @classmethod
    def getDeviceControllers(cls, pools, devices=None):
        """ provides device controller full names

        :param pools: list of pool devices
        :type pools: :obj:`list` <:class:`PyTango.DeviceProxy`>
        :param devices: alias names
        :type devices: :obj:`list` <:obj:`str`>
        :returns: device controller full names
        :rtype: :obj:`dict` <:obj:`str`, :obj:`str`>
        """
        lst = []
        for pool in pools:
            if pool.ExpChannelList:
                lst += pool.ExpChannelList
        ctrls = {}
        for elm in lst:
            chan = json.loads(elm)
            if devices is None or chan['name'] in devices:
                ctrls[chan['name']] = chan['controller']
        return ctrls

    @classmethod
    def getChannelSources(cls, pools, devices):
        """ provides channel sources

        :param pools: list of pool devices
        :type pools: :obj:`list` <:class:`PyTango.DeviceProxy`>
        :param devices: alias names
        :type devices: :obj:`list` <:obj:`str`>
        :returns: device sources
        :rtype: :obj:`dict` <:obj:`str`, :obj:`str`>
        """
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

    @classmethod
    def getElementNames(cls, pools, listattr, typefilter=None):
        """ provides experimental Channels

        :param pools: list of pool devices
        :type pools: :obj:`list` <:class:`PyTango.DeviceProxy`>
        :param listattr: pool attribute with list
        :type listattr: :obj:`str`
        :param typefilter: pool attribute with list
        :type typefilter: :obj:`list` <:obj:`str`>
        :returns: names from given pool listattr
        :rtype: :obj:`list` <:obj:`str`>
        """
        lst = []
        elements = []
        for pool in pools:
            if hasattr(pool, listattr):
                ellist = getattr(pool, listattr)
                if ellist:
                    lst += ellist
        for elm in lst:
            if elm:
                chan = json.loads(elm)
                if chan and isinstance(chan, dict):
                    if typefilter:
                        if chan['type'] not in typefilter:
                            continue
                    elements.append(chan['name'])
        return elements

    @classmethod
    def getFullDeviceNames(cls, pools, names=None):
        """ find device names from aliases

        :param pools: list of pool devices
        :type pools: :obj:`list` <:class:`PyTango.DeviceProxy`>
        :param names: alias names if None returns name for all aliases
        :type names: :obj:`list` <:obj:`str`>
        :returns: full device name
        :rtype: :obj:`dict` <:obj:`str`, :obj:`str`>
        """
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

    @classmethod
    def getAliases(cls, pools, names=None):
        """ find aliases from fullnames

        :param pools: list of pool devices
        :type pools: :obj:`list` <:class:`PyTango.DeviceProxy`>
        :param names: fullnames if None returns all aliases
        :type names: :obj:`list` <:obj:`str`>
        :returns: full device name
        :rtype: :obj:`dict` <:obj:`str`, :obj:`str`>
        """
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

    @classmethod
    def getMntGrpName(cls, pools, alias):
        """ find measurement group name from alias

        :param pools: list of pool devices
        :type pools: :obj:`list` <:class:`PyTango.DeviceProxy`>
        :param alias: mntgrp alias
        :type alias: :obj:`str`
        :returns: full name of the measurement group alias
        :rtype: :obj:`str`
        """
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

    @classmethod
    def getTimers(cls, pools, filters=None):
        """ provides tiemrs of given pools

        :param pools: list of pool devices
        :type pools: :obj:`list` <:class:`PyTango.DeviceProxy`>
        :param filters: device name filter list
        :type filters: :obj:`list` <:obj:`str`>
        :returns: list of timer names
        :rtype: :obj:`list` <:obj:`str`>
        """
        lst = []
        res = []
        for pool in pools:
            if pool.ExpChannelList:
                lst += pool.ExpChannelList

        if not filters or not hasattr(filters, '__iter__'):
            filters = ["*dgg*", "*/timer/*", "*/ctctrl0*"]
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

    @classmethod
    def filterNames(cls, pools, filters=None, lst=None):
        """ provides channels of given pools

        :param pools: list of pool devices
        :type pools: :obj:`list` <:class:`PyTango.DeviceProxy`>
        :param filters: device name filter list
        :type filters: :obj:`list` <:obj:`str`>
        :returns: list of channel names
        :rtype: :obj:`list` <:obj:`str`>
        """
        res = []
        if lst is None:
            lst = []
            for pool in pools:
                if pool.AcqChannelList:
                    lst += pool.AcqChannelList

        if filters is None or not hasattr(filters, '__iter__'):
            filters = ["*"]
        for elm in lst:
            chan = json.loads(elm)
            fullname = chan['full_name']
            found = False
            for df in filters:
                found = fnmatch.filter([fullname], df)
                if found:
                    break
            if found:
                res.append(chan['name'])
        return res

    @classmethod
    def getSource(cls, name):
        """ provides datasource from pool device

        :param name: pool device name
        :type name:  :obj:`str`
        :returns: source of pool device
        :rtype:  :obj:`str`
        """
        source = None
        try:
            dp = PyTango.DeviceProxy(Utils.tostr(name))
            if hasattr(dp, 'DataSource'):
                ds = dp.DataSource
                sds = ds.split("://")
                ap = PyTango.AttributeProxy(sds[-1])
                if ap is None:
                    raise Exception("Empty proxy")
                source = sds[-1]
        except PyTango.DevFailed:
            pass
        return source
