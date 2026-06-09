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

"""  Component CheckerThread - thread which checks tango server attributes"""

import multiprocessing as mp
import sys

if sys.version_info > (3,):
    import queue as Queue
else:
    import Queue

try:
    import tango
except Exception:
    import PyTango as tango

from .Checker import check


class CheckerProcess(mp.Process):

    """ Single CheckerThread
    """

    def __init__(self, index, queue, rqueue):
        """ constructor

        :brief: It creates ElementThread from the runnable element
        :param index: the current thread index
        :type index: :obj:`int`
        :param queue: queue with tasks
        :type queue: :class:`Queue.Queue`
        :param rqueue: queue with results
        :type rqueue: :class:`Queue.Queue`
        """
        mp.Process.__init__(self)
        #: (:obj:`int`) process index
        self.index = index
        #: (:class:`Queue.Queue`) queue with runnable elements
        self.__queue = queue
        #: (:class:`Queue.Queue`) queue with runnable elements
        self.__rqueue = rqueue

        #: (:obj:`list` <:obj:`str`>) tango datasources error states
        self.tangoSourceErrorStates = [
            "OFF", "INIT", "INSERT", "CLOSE", "UNKNOWN", "FAULT"]

        #: (:obj:`list` <:obj:`str`>) tango datasources warning states
        self.tangoSourceWarningStates = ["ALARM", "DISABLE"]

    def run(self):
        """ runner

        :brief: It runs the defined thread
        """
        if hasattr(tango.ApiUtil, 'cleanup'):
            tango.ApiUtil.cleanup()
        import time
        time.sleep(self.index/10.)
        while not self.__queue.empty():
            elem = None
            try:
                elem = self.__queue.get(block=False)
                check(elem, self.tangoSourceErrorStates,
                      self.tangoSourceWarningStates)
                self.__rqueue.put(elem)
            except Queue.Empty:
                break
            except Exception as e:
                print("Error:", str(e))
