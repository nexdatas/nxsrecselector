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

""" BLISS counters of NeXus configuration datasources

STEP datasources selected in NXSRecSelector which are not BLISS counters,
e.g. TANGO, DB or PYEVAL datasources of the configuration server,
are read in BLISS scans by counters of :class:`NXSDataSourceController`.
The datasources are evaluated by :mod:`nxswriter` datasources,
i.e. in the same way as by NXSDataWriter.

The controller is created and updated by
:class:`nxsrecconfig.BlissSession.NXSBlissSession`.
Only scalar datasources are supported,
the values are stored as ``float64``.
"""

import logging

import lxml.etree
import numpy

from .Utils import Utils

try:
    from bliss.controllers.counter import SamplingCounterController
    from bliss.common.counter import SamplingCounter, SamplingMode
    #: (:obj:`bool`) BLISS is available
    BLISS_AVAILABLE = True
except Exception:
    SamplingCounterController = object
    SamplingCounter = None
    SamplingMode = None
    BLISS_AVAILABLE = False


#: (:obj:`str`) default name of the datasource counter controller
CONTROLLER = "nxsds"


def scalarValue(data):
    """ converts data of a nxswriter datasource into a scalar value

    :param data: datasource data, i.e. a dictionary with ``value``
    :type data: :obj:`dict` <:obj:`str`, `any`>
    :returns: scalar value, NaN if not available
    :rtype: :obj:`float`
    """
    value = data.get("value") if isinstance(data, dict) else data
    try:
        arr = numpy.asarray(value, dtype=numpy.float64)
        if arr.size == 1:
            return float(arr.reshape(-1)[0])
    except Exception:
        pass
    return numpy.nan


class DataSourceReader(object):

    """ reads NeXus configuration datasources by nxswriter datasources
    """

    def __init__(self, userdata=None, log=None):
        """ constructor

        :param userdata: user data of CLIENT datasources used e.g. by
                         PYEVAL datasources or a function returning them
        :type userdata: :obj:`dict` <:obj:`str`, `any`> or callable
        :param log: logger with debug, info and warning methods
        :type log: :class:`logging.Logger` or `any`
        """
        from nxswriter.DataSourcePool import DataSourcePool
        from nxswriter.DecoderPool import DecoderPool

        #: (:obj:`dict` or callable) user data
        self.userdata = userdata
        #: (:class:`logging.Logger` or `any`) logger
        self.log = log or logging.getLogger("nxsrecconfig")
        #: (:class:`nxswriter.DataSourcePool.DataSourcePool`) pool
        self.__pool = DataSourcePool()
        #: (:class:`nxswriter.DecoderPool.DecoderPool`) decoders
        self.__decoders = DecoderPool()
        #: (:obj:`dict` <:obj:`str`, `any`>) datasources by names
        self.__sources = {}
        #: (:obj:`dict` <:obj:`str`, :obj:`str`>) XML definitions by names
        self.__xmls = {}

    def names(self):
        """ provides names of the datasources

        :returns: datasource names
        :rtype: :obj:`list` <:obj:`str`>
        """
        return sorted(self.__sources.keys())

    def setDataSources(self, datasources):
        """ sets the datasources

        Datasources which cannot be set up are skipped.

        :param datasources: datasource XML definitions by datasource names
        :type datasources: :obj:`dict` <:obj:`str`, :obj:`str`>
        """
        datasources = dict(datasources or {})
        for name in list(self.__sources.keys()):
            if name not in datasources:
                self.__sources.pop(name)
                self.__xmls.pop(name)
        for name, xml in datasources.items():
            if name in self.__sources and self.__xmls[name] == xml:
                continue
            try:
                self.__sources[name] = self.__create(name, xml)
                self.__xmls[name] = xml
            except Exception as e:
                self.__sources.pop(name, None)
                self.__xmls.pop(name, None)
                self.log.warning(
                    "nxsrecconfig: datasource %s cannot be set up: %s"
                    % (name, e))

    def __globalJSON(self):
        """ provides global JSON data of the datasources

        :returns: global JSON data
        :rtype: :obj:`dict` <:obj:`str`, `any`>
        """
        userdata = self.userdata() if callable(self.userdata) \
            else self.userdata
        return {"data": dict(userdata or {})}

    def __create(self, name, xml):
        """ creates a nxswriter datasource

        :param name: datasource name
        :type name: :obj:`str`
        :param xml: datasource XML definition
        :type xml: :obj:`str`
        :returns: nxswriter datasource
        :rtype: :class:`nxswriter.DataSources.DataSource`
        """
        node = Utils.dataSourceNode(xml)
        if node is None:
            raise ValueError("wrong XML definition")
        dstype = node.get("type")
        if not self.__pool.hasDataSource(dstype):
            raise ValueError("unknown datasource type %s" % dstype)
        source = self.__pool.get(dstype)(name=name)
        source.setup(lxml.etree.tostring(node, encoding="unicode"))
        if hasattr(source, "setJSON"):
            source.setJSON(self.__globalJSON())
        if hasattr(source, "setDataSources"):
            source.setDataSources(self.__pool)
        if hasattr(source, "setDecoders"):
            source.setDecoders(self.__decoders)
        return source

    def read(self, names):
        """ reads datasource values

        :param names: datasource names
        :type names: :obj:`list` <:obj:`str`>
        :returns: values, NaN for datasources which cannot be read
        :rtype: :obj:`list` <:obj:`float`>
        """
        # new reading of tango groups
        self.__pool.counter += 1
        gjson = self.__globalJSON()
        values = []
        for name in names:
            source = self.__sources.get(name)
            value = numpy.nan
            if source is not None:
                try:
                    if hasattr(source, "setJSON"):
                        source.setJSON(gjson)
                    value = scalarValue(source.getData())
                except Exception as e:
                    self.log.warning(
                        "nxsrecconfig: datasource %s cannot be read: %s"
                        % (name, e))
            values.append(value)
        return values


class NXSDataSourceController(SamplingCounterController):

    """ BLISS counter controller of NeXus configuration datasources
    """

    def __init__(self, name=CONTROLLER, reader=None):
        """ constructor

        :param name: controller name
        :type name: :obj:`str`
        :param reader: datasource reader
        :type reader: :class:`DataSourceReader`
        """
        if not BLISS_AVAILABLE:
            raise ImportError("BLISS is not available")
        SamplingCounterController.__init__(self, name)
        #: (:class:`DataSourceReader`) datasource reader
        self.reader = reader or DataSourceReader()
        self.max_sampling_frequency = None

    def setDataSources(self, datasources):
        """ sets the datasources and creates their counters

        :param datasources: datasource XML definitions by datasource names
        :type datasources: :obj:`dict` <:obj:`str`, :obj:`str`>
        :returns: full names of the counters
        :rtype: :obj:`list` <:obj:`str`>
        """
        self.reader.setDataSources(datasources)
        names = self.reader.names()
        for cnt in list(self.counters):
            if cnt.name not in names:
                self.remove(cnt)
        existing = set(cnt.name for cnt in self.counters)
        for name in names:
            if name not in existing:
                SamplingCounter(name, self, mode=SamplingMode.SINGLE)
        return [cnt.fullname for cnt in self.counters]

    def read_all(self, *counters):
        """ reads the datasources of the counters

        :param counters: counters
        :type counters: :obj:`list` <:class:`bliss.common.counter.Counter`>
        :returns: values
        :rtype: :obj:`list` <:obj:`float`>
        """
        return self.reader.read([cnt.name for cnt in counters])
