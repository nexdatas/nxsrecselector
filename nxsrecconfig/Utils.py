#!/usr/bin/env python
#   This file is part of nxsrecconfig - NeXus Sardana Recorder Settings
#
#    Copyright (C) 2014 DESY, Jan Kotanski <jkotan@mail.desy.de>
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

import PyTango
import time
import json
import pickle
import numpy


## Tango Utilities
class Utils(object):
    """  Tango Utilities """

    ## map of Tango:Numpy types
    tTnp = {PyTango.DevLong64: "int64", PyTango.DevLong: "int32",
            PyTango.DevShort: "int16", PyTango.DevUChar: "uint8",
            PyTango.DevULong64: "uint64", PyTango.DevULong: "uint32",
            PyTango.DevUShort: "uint16", PyTango.DevDouble: "float64",
            PyTango.DevFloat: "float32", PyTango.DevString: "string",
            PyTango.DevBoolean: "bool"}

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

    ## provides environment variable value
    # \param cls class instance
    ## \param var variable name
    ## \param ms macroserver
    @classmethod
    def getEnv(cls, var, ms):
        active = ""
        dp = cls.openProxy(ms)
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
        dp = cls.openProxy(ms)
        rec = dp.Environment
        if rec[0] == 'pickle':
            dc = pickle.loads(rec[1])
            if 'new' in dc.keys():
                dc['new'][var] = value
                pk = pickle.dumps(dc)
                dp.Environment = ['pickle', pk]

    ## provides proxies of given device names
    # \param cls class instance
    # \param names given device names
    # \returns list of device DeviceProxies
    @classmethod
    def getProxies(cls, names):
        dps = []
        for name in names:
            dp = PyTango.DeviceProxy(name)
            try:
                dp.ping()
                dps.append(dp)
            except:
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
                dp = PyTango.DeviceProxy(server)
                dp.ping()
                device = server
                break
            except:
                pass
        return device

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
            dp = PyTango.DeviceProxy(server)
            if hasattr(dp, "DoorList"):
                lst = dp.DoorList
                if door in lst:
                    ms = server
                    break
        return ms

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
    # \param name alias name
    # \returns full name of   measurement group
    @classmethod
    def getMntGrpName(cls, pools, name):
        lst = []
        for pool in pools:
            if pool.MeasurementGroupList:
                lst += pool.MeasurementGroupList
        argout = ""
        for elm in lst:
            chan = json.loads(elm)
            if name == chan['name']:
                argout = chan['full_name']
                break
        return argout

    ## find measurement group from alias
    # \param cls class instance
    # \param pool pool device
    # \returns name of measurement group
    @classmethod
    def getMntGrps(cls, pool):
        lst = []
        if pool.MeasurementGroupList:
            lst += pool.MeasurementGroupList
        argout = []
        for elm in lst:
            chan = json.loads(elm)
            argout.append(chan['name'])
        return argout

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

    ## provides tiemrs of given pools
    # \param cls class instance
    # \param pools list of pool devices
    # \returns list of timer names
    @classmethod
    def getTimers(cls, pools):
        lst = []
        res = []
        for pool in pools:
            if pool.ExpChannelList:
                lst += pool.ExpChannelList
        for elm in lst:
            chan = json.loads(elm)
            inter = chan['interfaces']
            if isinstance(inter, (list, tuple)):
                if 'CTExpChannel' in inter:
                    res.append(chan['name'])
        return res

    ## adds controller into configuration dictionary
    @classmethod
    def __addController(cls, cnf, ctrl, fulltimer):
        if 'controllers' not in cnf.keys():
            cnf['controllers'] = {}
        if not ctrl in cnf['controllers'].keys():
            cnf['controllers'][ctrl] = {}
            cnf['controllers'][ctrl]['units'] = {}
            cnf['controllers'][ctrl]['units']['0'] = {}
            cnf['controllers'][ctrl]['units']['0'][
                u'channels'] = {}
            cnf['controllers'][ctrl]['units']['0']['id'] = 0
            cnf['controllers'][ctrl]['units']['0'][
                u'monitor'] = fulltimer
            cnf['controllers'][ctrl]['units']['0'][
                u'timer'] = fulltimer
            cnf['controllers'][ctrl]['units']['0'][
                u'trigger_type'] = 0

    ## retrives shape type value for attribure
    @classmethod
    def __getShapeTypeValue(cls, source):
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
        except Exception:
            if ac and ac.data_format != PyTango.AttrDataFormat.SCALAR \
                    and da is None:
                raise

        if vl is not None:
            shp = list(numpy.shape(vl))
            dt = getattr(vl, 'dtype', numpy.dtype(type(vl))).name
        elif ac is not None:
            if ac.data_format != PyTango.AttrDataFormat.SCALAR:
                if da.dim_x and da.dim_x > 1:
                    shp = [da.dim_y, da.dim_x] \
                        if da.dim_y \
                        else [da.dim_x]
            dt = cls.tTnp[ac.data_type]
        if ac is not None:
            ut = ac.unit
        return (shp, dt, vl, ut)

    ## adds channel into configuration dictionary
    @classmethod
    def __addChannel(cls, cnf, ctrl, device, fullname, dontdisplay, index):

        ctrlChannels = cnf['controllers'][ctrl]['units']['0'][
            u'channels']
        if not fullname in ctrlChannels.keys():
            source = '%s/%s' % (fullname.encode(), 'value')

            shp, dt, _, ut = cls.__getShapeTypeValue(source)
            dct = {}
            dct['_controller_name'] = unicode(ctrl)
            dct['_unit_id'] = u'0'
            dct['conditioning'] = u''
            dct['data_type'] = dt
            dct['data_units'] = ut
            dct['enabled'] = True
            dct['full_name'] = fullname
            dct['index'] = index
            index += 1
            dct['instrument'] = None
            dct['label'] = unicode(device)
            dct['name'] = unicode(device)
            dct['ndim'] = 0
            dct['nexus_path'] = u''
            dct['normalization'] = 0
            dct['output'] = True
            dct['shape'] = shp

            if device in dontdisplay:
                dct['plot_axes'] = []
                dct['plot_type'] = 0
            elif dct['shape'] and len(dct['shape']) == 1:
                dct['plot_axes'] = ['<idx>']
                dct['plot_type'] = 1
            elif dct['shape'] and len(dct['shape']) == 2:
                dct['plot_axes'] = ['<idx>', '<idx>']
                dct['plot_type'] = 2
            else:
                dct['plot_axes'] = ['<mov>']
                dct['plot_type'] = 1

            dct['source'] = source
            ctrlChannels[fullname] = dct

        return index

    ## adds device into configuration dictionary
    # \param cls class instance
    # \param device device alias
    # \param dontdisplay list of devices disable for display
    # \param pools list of give pools
    # \param cnf configuration dictionary
    # \param timer device timer
    # \param index device index
    # \returns next device index
    @classmethod
    def addDevice(cls, device, dontdisplay, pools, cnf, timer, index):
        ctrls = cls.getDeviceControllers(pools, [device])
        ctrl = ctrls[device] if ctrls and device in ctrls.keys() else ""
        timers = cls.getFullDeviceNames(pools, [timer])
        fulltimer = timers[timer] if timers and timer in timers.keys() else ""
        if not ctrl:
            return index

        cls.__addController(cnf, ctrl, fulltimer)
        fullnames = cls.getFullDeviceNames(pools, [device])
        fullname = fullnames[device] \
            if fullnames and device in fullnames.keys() else ""
        index = cls.__addChannel(cnf, ctrl, device, fullname,
                                     dontdisplay, index)

        return index

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

    ## adds device into configuration dictionary
    # \param cls class instance
    # \param devices device aliases
    # \param dontdisplay list of devices disable for display
    # \param pools list of give pools
    # \param cnf configuration dictionary
    # \param timer device timer
    # \param index device index
    # \returns next device index
    @classmethod
    def addDevices(cls, devices, dontdisplay, pools, cnf, timer, index):
        ctrls = cls.getDeviceControllers(pools, devices)
        fullnames = cls.getFullDeviceNames(pools, devices)
        for device, ctrl in ctrls.items():
            cls.__addController(cnf, ctrl, timer)
            fullname = fullnames[device]
            index = cls.__addChannel(cnf, ctrl, device, fullname,
                                     dontdisplay, index)

        return index
