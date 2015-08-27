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
## \file CheckerThread.py
# thread with checks tango server attributes

"""  Component CheckerThread """

import Queue
import PyTango
import threading


## default attributes to check
ATTRIBUTESTOCHECK = ["Value", "Position", "Counts", "Data",
                     "Voltage", "Energy", "SampleTime"]


## Tango DataSource item
class TangoDSItem(object):
    __slots__ = 'name', 'device', 'attr'

    ## constructor
    # \param name datasource name
    # \param device datasource device
    # \param attr device attribute
    def __init__(self, name=None, device=None, attr=None):
        ## datasource name
        self.name = str(name) if name is not None else None
        ## datasource device
        self.device = str(device) if device is not None else None
        ## datasource device attribute
        self.attr = str(attr) if attr is not None else None


## Checker list Item
class CheckerItem(list):

    ## constructor
    # \param name checker item name
    def __init__(self, name):
        super(CheckerItem, self).__init__()
        ## checker name
        self.name = name
        ## datasource with first error
        self.errords = None
        ## first error message
        self.message = None
        ## enabled flag
        self.active = True


## Single CheckerThread
class CheckerThread(threading.Thread):
    ## constructor
    # \brief It creates ElementThread from the runnable element
    # \param index the current thread index
    # \param queue queue with tasks
    def __init__(self, index, queue):
        threading.Thread.__init__(self)
        ## thread index
        self.index = index
        ## queue with runnable elements
        self.__queue = queue

    ## runner
    # \brief It runs the defined thread
    def run(self):
        full = True
        while full:
            try:
                elem = self.__queue.get(block=False)
                self.__check(elem)

            except Queue.Empty:
                full = False

    @classmethod
    def __check(cls, checkeritem):
        for ds in checkeritem:
            try:
                dp = PyTango.DeviceProxy(ds.device)
                state = dp.command_inout("State")
                if state in [
                    PyTango.DevState.FAULT]:
                    raise FaultStateError("FAULT STATE")
                dp.ping()
                if not ds.attr:
                    for gattr in ATTRIBUTESTOCHECK:
                        if hasattr(dp, gattr):
                            _ = getattr(dp, gattr)
                else:
                    _ = getattr(dp, ds.attr)
                if state in [
                    PyTango.DevState.ALARM]:
                    raise AlarmStateError("ALARM STATE")
            except AlarmStateError as e:
                checkeritem.message = "ALARM_STATE"
                checkeritem.errords = ds.name
            except Exception as e:
                checkeritem.message = str(e)
                checkeritem.errords = ds.name
                checkeritem.active = False
                break


## Alarm State Exception class
class AlarmStateError(Exception):
    pass


## Fault State Exception class
class FaultStateError(Exception):
    pass
