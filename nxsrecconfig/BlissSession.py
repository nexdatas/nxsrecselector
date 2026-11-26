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

""" BLISS session side of the ``bliss`` scan backend

It publishes channels, motors and measurement groups of a BLISS session
for the selector and applies the channels selected by the selector to
the BLISS measurement groups.  In a BLISS session::

    from nxsrecconfig.BlissSession import NXSBlissSession
    nxsbliss = NXSBlissSession()
    nxsbliss.sync()      # after changes in the selector or the session

The selector has to use the ``bliss`` backend with the session name
as its ``Door``.
"""

import json

from .BlissBackend import (
    BlissBackend, channelName, redisConnection, sessionKey)


class BlissAPI(object):

    """ access to the current BLISS session
    """

    def session(self):
        """ provides the session name

        :returns: session name
        :rtype: :obj:`str`
        """
        from bliss import current_session
        return current_session.name

    def counters(self):
        """ provides the counters of the session

        :returns: counters, i.e. dictionaries with ``fullname``,
                  ``controller``, ``shape`` and ``dtype``
        :rtype: :obj:`list` <:obj:`dict` <:obj:`str`, `any`>>
        """
        import numpy
        from bliss import global_map
        counters = []
        for cnt in global_map.get_counters_iter():
            try:
                dtype = numpy.dtype(cnt.dtype).name
            except Exception:
                dtype = "float64"
            ctrl = getattr(cnt, "_counter_controller", None)
            counters.append({
                "fullname": cnt.fullname,
                "controller": getattr(ctrl, "name", "") or "",
                "shape": list(getattr(cnt, "shape", None) or []),
                "dtype": dtype,
            })
        return counters

    def axes(self):
        """ provides the axis names of the session

        :returns: axis names
        :rtype: :obj:`list` <:obj:`str`>
        """
        from bliss import global_map
        return [axis.name for axis in global_map.get_axes_iter()]

    def mntgrps(self):
        """ provides the measurement groups of the session

        :returns: ``{name: {"available": [...], "enabled": [...]}}``
        :rtype: :obj:`dict` <:obj:`str`, :obj:`dict`>
        """
        from bliss.common import measurementgroup
        return {mg.name: {"available": list(mg.available),
                          "enabled": list(mg.enabled)}
                for mg in measurementgroup.get_all()}

    def activeMntGrp(self):
        """ provides the active measurement group name

        :returns: measurement group name
        :rtype: :obj:`str`
        """
        from bliss.common import measurementgroup
        return measurementgroup.get_active_name()

    def selectChannels(self, name, fullnames):
        """ enables only the given counters of a measurement group,
            the group is created if it does not exist

        :param name: measurement group name
        :type name: :obj:`str`
        :param fullnames: counter full names
        :type fullnames: :obj:`list` <:obj:`str`>
        """
        from bliss.common import measurementgroup
        mgs = {mg.name: mg for mg in measurementgroup.get_all()}
        if name not in mgs:
            measurementgroup.MeasurementGroup(
                name, {"counters": list(fullnames)})
            return
        mg = mgs[name]
        mg.disable_all()
        names = [fn for fn in fullnames if fn in mg.available]
        if names:
            mg.enable(*names)

    def setActiveMntGrp(self, name):
        """ activates a measurement group

        :param name: measurement group name
        :type name: :obj:`str`
        """
        from bliss.common import measurementgroup
        measurementgroup.set_active_name(name)


class NXSBlissSession(object):

    """ publishes a BLISS session for the selector
        and applies the selected channels
    """

    def __init__(self, session=None, redis=None, api=None):
        """ constructor

        :param session: session name, the current session if None
        :type session: :obj:`str`
        :param redis: Redis connection, see
                      :func:`nxsrecconfig.BlissBackend.redisConnection`
        :type redis: :class:`redis.Redis`
        :param api: BLISS session access
        :type api: :class:`BlissAPI`
        """
        #: (:class:`BlissAPI`) BLISS session access
        self.api = api or BlissAPI()
        #: (:obj:`str`) session name
        self.session = session or self.api.session()
        #: (:class:`redis.Redis`) Redis connection
        self.redis = redis if redis is not None else redisConnection()

    def elements(self):
        """ provides the session elements in the format of Sardana pools

        :returns: element lists
        :rtype: :obj:`dict` <:obj:`str`, :obj:`list` <:obj:`dict`>>
        """
        channels = []
        for cnt in self.api.counters():
            channels.append({
                "name": channelName(cnt["fullname"]),
                "full_name": cnt["fullname"],
                "source": cnt["fullname"],
                "controller": cnt.get("controller", ""),
                "type": "CounterTimer",
                "interfaces": ["Counter", "ExpChannel"],
                "shape": cnt.get("shape", []),
                "dtype": cnt.get("dtype", "float64"),
            })
        motors = [{
            "name": channelName(axis),
            "full_name": axis,
            "source": axis,
            "controller": "",
            "type": "Motor",
            "interfaces": ["Motor", "Moveable"],
        } for axis in self.api.axes()]
        mntgrps = [{
            "name": name,
            "full_name": name,
            "type": "MeasurementGroup",
            "channels": mg["enabled"],
        } for name, mg in self.api.mntgrps().items()]
        return {
            "AcqChannelList": channels,
            "ExpChannelList": channels,
            "MotorList": motors,
            "MeasurementGroupList": mntgrps,
        }

    def publish(self):
        """ publishes the session elements and its active measurement group
        """
        elements = self.elements()
        key = sessionKey(self.session, "elements")
        self.redis.delete(key)
        self.redis.hset(key, mapping={
            name: json.dumps(value) for name, value in elements.items()})
        active = self.api.activeMntGrp()
        if active:
            backend = BlissBackend(redis=self.redis)
            if backend.getEnv("ActiveMntGrp", self.session) is None:
                backend.setEnv("ActiveMntGrp", active, self.session)

    def apply(self):
        """ applies the selected channels to the measurement groups
            and activates the measurement group of the selector

        :returns: names of updated measurement groups
        :rtype: :obj:`list` <:obj:`str`>
        """
        key = sessionKey(self.session, "mntgrps")
        requests = self.redis.hgetall(key) or {}
        updated = []
        for name, value in requests.items():
            self.api.selectChannels(name, json.loads(value))
            updated.append(name)
        if requests:
            self.redis.hdel(key, *requests.keys())
        backend = BlissBackend(redis=self.redis)
        active = backend.getEnv("ActiveMntGrp", self.session)
        if active and active != self.api.activeMntGrp() and \
           active in self.api.mntgrps():
            self.api.setActiveMntGrp(active)
        return sorted(updated)

    def sync(self):
        """ applies the selection and publishes the session

        :returns: names of updated measurement groups
        :rtype: :obj:`list` <:obj:`str`>
        """
        updated = self.apply()
        self.publish()
        return updated
