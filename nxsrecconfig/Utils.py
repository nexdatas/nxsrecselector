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
        srvs = db.get_server_list( "*").value_string
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
            dp = cls.openProxy(pool)
            try:
                dp.ping()
                pools.append(dp)    
            except:
                pass
        return pools    


    @classmethod
    def findDeviceController(cls, pools, device):
        """
        returns the controller that belongs to a device
        """
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

    
    ## find device
    # \param name device class name
    @classmethod
    def findDevice(cls, db, name):        
        servers = db.get_device_exported_for_class(
            name).value_string
        if len(servers):
            return servers[0]                

