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


ATTRIBUTESTOCHECK = ["Value", "Position", "Counts", "Data",
                     "Voltage", "Energy", "SampleTime"]


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
    def __check(cls, lds):
        erds = None
        message = None
        for ds in lds[1:]:
            if isinstance(ds, tuple) and len(ds) > 2:
                dname = str(ds[1])
                attr = str(ds[2])
            else:
                dname = str(ds)
                attr = None

            try:
                dp = PyTango.DeviceProxy(dname)
                if dp.command_inout("State") in [
                    PyTango.DevState.FAULT,
                    PyTango.DevState.ALARM]:
                    raise WrongStateError("FAULT or ALARM STATE")
                dp.ping()
                if not attr:
                    for gattr in ATTRIBUTESTOCHECK:
                        if hasattr(dp, gattr):
                            _ = getattr(dp, gattr)
                else:
                    _ = getattr(dp, attr)
            except Exception as e:
                message = str(e)
                erds = ds
                break
        if erds is None:
            lds[:] = []
        else:
            lds[:] = [lds[0], erds, message]


class WrongStateError(Exception):
    pass
