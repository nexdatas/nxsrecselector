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

## 
class Utils(object):
    """  Tango Utilities """

    @classmethod
    def openProxy(cls, device):
        found = False
        cnt = 0
        cnfServer = PyTango.DeviceProxy(device)

        while not found and cnt < 1000:
            if cnt > 1:
                time.sleep(0.01)
            try:
                if cnfServer.state() != PyTango.DevState.RUNNING:
                    found = True
            except (PyTango.DevFailed, PyTango.Except,  PyTango.DevError):
                time.sleep(0.01)
                found = False
                if cnt == 999:
                    raise
            cnt += 1
        
        return cnfServer    

    @classmethod
    def getActiveMntGrp(cls, door):
        active = ""
        dp = cls.openProxy(door)
        dp.RunMacro(["lsmeas"])
        while dp.state() == PyTango.DevState.RUNNING:
            time.sleep(0.01)
        res = dp.Output
        if res and len(res)>2:
            for line in res[2:]:
                sline = line.split()
                if sline[0] == '*':
                    active = sline[1]
                    break
        return active


    @classmethod
    def setActiveMntGrp(cls, door, name):
        groups = set()
        dp = cls.openProxy(door)
        dp.RunMacro(["lsmeas"])
        while dp.state() == PyTango.DevState.RUNNING:
            time.sleep(0.01)
        res = dp.Output
        if res and len(res)>2:
            for line in res[2:]:
                sline = line.split()
                if sline[0] == '*':
                    groups.add(sline[1])
                else:
                    groups.add(sline[0])
        if name in groups:
            dp.RunMacro(['senv', 'ActiveMntGrp', '"%s"' % name])
            while dp.state() == PyTango.DevState.RUNNING:
                time.sleep(0.01)
        else:
            raise Exception("Unknown Measurement Group: %s" % name)
                    

    @classmethod
    def getDeviceNamesByClass(cls, db, className):
        srvs = cls.getServerNameByClass(db, className)
        argout = []
        for srv in srvs:
            lst = db.get_device_name(srv, className).value_string
            for i in range(0, len(lst)):
                argout.append(lst[i])
        return argout


    @classmethod
    def getServerNameByClass(cls, db, argin): 
        srvs = db.get_server_list("*").value_string
        argout = []
        for srv in srvs:
            classList = db.get_server_class_list(srv).value_string
            for clss in classList:
                if clss == argin:
                    argout.append(srv)
                    break
        return argout


    @classmethod
    def pools(cls, db):
        poolNames = cls.getDeviceNamesByClass(db, "Pool")
        pools = []
        for pool in poolNames:
            dp = PyTango.DeviceProxy(pool)
            try:
                dp.ping()
                pools.append(dp)    
            except:
                pass
        return pools    



    
    ## find device
    # \param name device class name
    @classmethod
    def findDevice(cls, db, name):        
        servers = db.get_device_exported_for_class(
            name).value_string
        if len(servers):
            return servers[0]                


    ## find device name from alias
    # \param name alias name
    # \param pools list of pool devices
    # \returns full device name    
    @classmethod
    def findFullDeviceName(cls, name, pools):
        lst = []
        for pool in pools:
            lst += pool.AcqChannelList
        argout = None
        for elm in lst:
            chan = json.loads(elm)
            if name == chan['name']:
                arr = chan['full_name'].split("/")
                argout = "/".join(arr[0:-1])
        return argout


    ## find device name from alias
    # \param name alias name
    # \param pools list of pool devices
    # \returns full device name    
    @classmethod
    def findMntGrpName(cls, name, pools):
        lst = []
        for pool in pools:
            lst += pool.MeasurementGroupList
        argout = None
        for elm in lst:
            chan = json.loads(elm)
            if name == chan['name']:
                argout = chan['full_name']
        return argout


    @classmethod
    def findDeviceController(cls, device, pools):
        lst = []
        for pool in pools:
            if not pool.ExpChannelList is None:
                lst += pool.ExpChannelList
        ctrl = None
        for elm in lst:
            chan = json.loads(elm)
            if device == chan['name']:
                ctrl = chan['controller']
                break
        return ctrl




    @classmethod
    def addDevice(cls, device, pools, hsh, timer, index):
        ctrl = cls.findDeviceController(device, pools)
        if not ctrl:
            return index
        if not ctrl in hsh['controllers'].keys():
            hsh['controllers'][ctrl] = {}
            hsh['controllers'][ctrl]['units'] = {}
            hsh['controllers'][ctrl]['units']['0'] = {}
            hsh['controllers'][ctrl]['units']['0'][
                u'channels'] = {}
            hsh['controllers'][ctrl]['units']['0']['id'] = 0
            hsh['controllers'][ctrl]['units']['0'][
                u'monitor'] = cls.findFullDeviceName(timer, pools)
            hsh['controllers'][ctrl]['units']['0'][
                u'timer'] = cls.findFullDeviceName(timer, pools)
            hsh['controllers'][ctrl]['units']['0'][
                u'trigger_type'] = 0

        ctrlChannels = hsh['controllers'][ctrl]['units']['0'][
            u'channels']
        
        full_name = cls.findFullDeviceName(device, pools) 
        if not full_name in ctrlChannels.keys():
            dp  = PyTango.DeviceProxy(full_name.encode())
            da =  dp.read_attribute('value')
            dct = {}
            dct['_controller_name'] = unicode(ctrl)
            dct['_unit_id'] = u'0'
            dct['conditioning'] = u''
            dct['data_type'] = u'float64'
            dct['data_units'] = u'No unit'
            dct['enabled'] = True
            dct['full_name'] = full_name
            dct['index'] = index
            index += 1
            dct['instrument'] = None
            dct['label'] = unicode(device)
            dct['name'] = unicode(device)
            dct['ndim'] = 0
            dct['nexus_path'] = u''
            dct['normalization'] = 0
            dct['output'] = True
            dct['plot_axes'] = []
            dct['plot_type'] = 0
            if da.dim_x and da.dim_x > 1 :
                dct['shape'] = [da.dim_y, da.dim_x] \
                    if da.dim_y \
                    else [da.dim_x]
            else:
                dct['shape'] = [] 
            dct['source'] = dct['full_name'] + "/value"
            ctrlChannels[full_name] = dct
        return index
