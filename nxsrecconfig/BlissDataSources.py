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
i.e. TANGO, DB, PYEVAL or CLIENT datasources of the configuration server,
are read in BLISS scans by counters of :class:`NXSDataSourceController`.
The datasources are evaluated by :mod:`nxswriter` datasources,
i.e. in the same way as by NXSDataWriter.

* numeric and boolean datasources of any rank are BLISS channels
  with the type of their NeXus fields and free dimensions,
* string datasources are collected at each scan point and stored
  as scan metadata of the controller at the end of the scan,
* CLIENT datasources are read from user data, they are skipped
  if their records are not in the user data,
* datasources which cannot be read are filled with NaN for floats,
  the maximal value for integers, False for booleans or an empty string,
  or the scan is stopped if ``canfail`` is False.

The controller is created and updated by
:class:`nxsrecconfig.BlissSession.NXSBlissSession`.
"""

import logging

import lxml.etree
import numpy

from .Utils import Utils

try:
    from bliss.common.counter import Counter
    from bliss.controllers.counter import CounterController
    from bliss.scanning.acquisition.counter import \
        BaseCounterAcquisitionSlave
    from bliss.scanning.scan_meta import META_TIMING
    #: (:obj:`bool`) BLISS is available
    BLISS_AVAILABLE = True
except Exception:
    Counter = object
    CounterController = object
    BaseCounterAcquisitionSlave = object
    META_TIMING = None
    BLISS_AVAILABLE = False


#: (:obj:`str`) default name of the datasource counter controller
CONTROLLER = "nxsds"

#: (:obj:`dict` <:obj:`str`, :obj:`str`>) numpy types of NeXus types
NXTYPES = {
    "NX_FLOAT32": "float32", "NX_FLOAT64": "float64",
    "NX_FLOAT": "float64", "NX_NUMBER": "float64",
    "NX_INT": "int64", "NX_INT64": "int64",
    "NX_INT32": "int32", "NX_INT16": "int16", "NX_INT8": "int8",
    "NX_UINT64": "uint64", "NX_UINT32": "uint32",
    "NX_UINT16": "uint16", "NX_UINT8": "uint8",
    "NX_UINT": "uint64", "NX_POSINT": "uint64",
    "NX_DATE_TIME": "str", "ISO8601": "str", "NX_CHAR": "str",
    "NX_BOOLEAN": "bool",
}


def description(value):
    """ provides a datasource description

    :param value: datasource description or its XML definition
    :type value: :obj:`dict` <:obj:`str`, `any`> or :obj:`str`
    :returns: datasource description with ``xml``, ``nxtype`` and ``rank``
    :rtype: :obj:`dict` <:obj:`str`, `any`>
    """
    if isinstance(value, dict):
        return {"xml": value.get("xml"), "nxtype": value.get("nxtype"),
                "rank": int(value.get("rank") or 0)}
    return {"xml": value, "nxtype": None, "rank": 0}


def numpyType(nxtype):
    """ provides the numpy type of a NeXus type

    :param nxtype: NeXus type, e.g. ``NX_INT32``
    :type nxtype: :obj:`str`
    :returns: numpy type name, ``float64`` for unknown types
    :rtype: :obj:`str`
    """
    return NXTYPES.get(nxtype or "", "float64")


def fillValue(dtype):
    """ provides the fill value of data which cannot be read

    :param dtype: numpy type name
    :type dtype: :obj:`str`
    :returns: NaN for floats, the maximal value for integers,
              False for booleans and an empty string for strings
    :rtype: `any`
    """
    if dtype == "str":
        return ""
    if dtype == "bool":
        return False
    npdtype = numpy.dtype(dtype)
    if npdtype.kind in "iu":
        return numpy.iinfo(npdtype).max
    return numpy.nan


def convert(value, dtype, rank):
    """ converts a datasource value to the type and rank of its field

    :param value: datasource value
    :type value: `any`
    :param dtype: numpy type name
    :type dtype: :obj:`str`
    :param rank: field rank
    :type rank: :obj:`int`
    :returns: converted value
    :rtype: :class:`numpy.ndarray` or :obj:`str`
    :raises: :exc:`ValueError` if the value cannot be converted
    """
    if dtype == "str":
        if isinstance(value, bytes):
            value = value.decode()
        if rank == 0:
            arr = numpy.asarray(value)
            if arr.size != 1:
                raise ValueError("a scalar value is expected")
            return str(arr.reshape(-1)[0])
        return numpy.asarray(value).astype(str).tolist()
    arr = numpy.asarray(value, dtype=dtype)
    if arr.ndim != rank:
        if arr.size == 1 and rank == 0:
            arr = arr.reshape(())
        elif arr.ndim < rank:
            arr = arr.reshape((1,) * (rank - arr.ndim) + arr.shape)
        else:
            raise ValueError(
                "rank %s is expected, got shape %s" % (rank, arr.shape))
    return arr


class DataSourceReader(object):

    """ reads NeXus configuration datasources by nxswriter datasources
    """

    def __init__(self, userdata=None, log=None):
        """ constructor

        :param userdata: user data of CLIENT datasources
                         or a function returning them
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
        #: (:obj:`dict` <:obj:`str`, :obj:`str`>) errors of the last reading
        self.errors = {}
        #: (:class:`nxswriter.DataSourcePool.DataSourcePool`) pool
        self.__pool = DataSourcePool()
        #: (:class:`nxswriter.DecoderPool.DecoderPool`) decoders
        self.__decoders = DecoderPool()
        #: (:obj:`dict` <:obj:`str`, `any`>) datasources by names
        self.__sources = {}
        #: (:obj:`dict` <:obj:`str`, :obj:`dict`>) descriptions by names
        self.__descriptions = {}

    def names(self):
        """ provides names of the datasources

        :returns: datasource names
        :rtype: :obj:`list` <:obj:`str`>
        """
        return sorted(self.__sources.keys())

    def description(self, name):
        """ provides a datasource description

        :param name: datasource name
        :type name: :obj:`str`
        :returns: datasource description with ``xml``, ``nxtype``
                  and ``rank``
        :rtype: :obj:`dict` <:obj:`str`, `any`>
        """
        return dict(self.__descriptions[name])

    def setDataSources(self, datasources):
        """ sets the datasources

        Datasources which cannot be set up and CLIENT datasources
        without user data are skipped.

        :param datasources: datasource descriptions or XML definitions
                            by datasource names
        :type datasources: :obj:`dict` <:obj:`str`, :obj:`dict`>
        """
        datasources = {name: description(value)
                       for name, value in (datasources or {}).items()}
        for name in list(self.__sources.keys()):
            if name not in datasources:
                self.__sources.pop(name)
                self.__descriptions.pop(name)
        for name, desc in datasources.items():
            if name in self.__sources and \
               self.__descriptions[name] == desc:
                continue
            self.__sources.pop(name, None)
            self.__descriptions.pop(name, None)
            try:
                source = self.__create(name, desc["xml"])
            except Exception as e:
                self.log.warning(
                    "nxsrecconfig: datasource %s cannot be set up: %s"
                    % (name, e))
                continue
            if source is not None:
                self.__sources[name] = source
                self.__descriptions[name] = desc

    def __userdata(self):
        """ provides the user data

        :returns: user data
        :rtype: :obj:`dict` <:obj:`str`, `any`>
        """
        userdata = self.userdata() if callable(self.userdata) \
            else self.userdata
        return dict(userdata or {})

    def __create(self, name, xml):
        """ creates a nxswriter datasource

        :param name: datasource name
        :type name: :obj:`str`
        :param xml: datasource XML definition
        :type xml: :obj:`str`
        :returns: nxswriter datasource or None for CLIENT datasources
                  without user data
        :rtype: :class:`nxswriter.DataSources.DataSource`
        """
        node = Utils.dataSourceNode(xml)
        if node is None:
            raise ValueError("wrong XML definition")
        dstype = node.get("type")
        if not self.__pool.hasDataSource(dstype):
            raise ValueError("unknown datasource type %s" % dstype)
        if dstype == "CLIENT":
            record = node.find("record")
            rname = record.get("name") if record is not None else None
            if rname not in self.__userdata():
                self.log.info(
                    "nxsrecconfig: CLIENT datasource %s skipped: "
                    "no user data of %s" % (name, rname))
                return None
        source = self.__pool.get(dstype)(name=name)
        source.setup(lxml.etree.tostring(node, encoding="unicode"))
        if hasattr(source, "setJSON"):
            source.setJSON({"data": self.__userdata()})
        if hasattr(source, "setDataSources"):
            source.setDataSources(self.__pool)
        if hasattr(source, "setDecoders"):
            source.setDecoders(self.__decoders)
        return source

    def read(self, names):
        """ reads datasource values

        :param names: datasource names
        :type names: :obj:`list` <:obj:`str`>
        :returns: values, None for datasources which cannot be read,
                  their errors are in :attr:`errors`
        :rtype: :obj:`list` `any`
        """
        # new reading of tango groups
        self.__pool.counter += 1
        gjson = {"data": self.__userdata()}
        self.errors = {}
        values = []
        for name in names:
            source = self.__sources.get(name)
            value = None
            if source is None:
                self.errors[name] = "unknown datasource"
            else:
                try:
                    if hasattr(source, "setJSON"):
                        source.setJSON(gjson)
                    data = source.getData()
                    value = data.get("value") \
                        if isinstance(data, dict) else data
                    if value is None:
                        self.errors[name] = "no data"
                except Exception as e:
                    self.errors[name] = str(e)
                    value = None
            values.append(value)
        return values


class NXSDataSourceCounter(Counter):

    """ BLISS counter of a NeXus configuration datasource
    """

    def __init__(self, name, controller, dtype="float64", rank=0):
        """ constructor

        :param name: datasource name
        :type name: :obj:`str`
        :param controller: counter controller
        :type controller: :class:`NXSDataSourceController`
        :param dtype: numpy type name, ``str`` for strings
        :type dtype: :obj:`str`
        :param rank: field rank
        :type rank: :obj:`int`
        """
        Counter.__init__(
            self, name, controller,
            dtype=(str if dtype == "str" else numpy.dtype(dtype)))
        #: (:obj:`str`) numpy type name
        self.typename = dtype
        #: (:obj:`int`) field rank
        self.rank = rank

    @property
    def shape(self):
        """ data shape with free dimensions

        :returns: shape
        :rtype: :obj:`tuple` <:obj:`int`>
        """
        return (-1,) * self.rank

    @property
    def isstring(self):
        """ string datasource flag

        :returns: True for string datasources stored as scan metadata
        :rtype: :obj:`bool`
        """
        return self.typename == "str"


class NXSDataSourceAcquisitionSlave(BaseCounterAcquisitionSlave):

    """ BLISS acquisition object of datasource counters,
        it reads all datasources once per scan point
    """

    def __init__(self, *counters, ctrl_params=None, count_time=None,
                 npoints=1):
        """ constructor

        :param counters: counter controller and counters
        :type counters: :obj:`list`
        :param ctrl_params: controller parameters
        :type ctrl_params: :obj:`dict`
        :param count_time: count time
        :type count_time: :obj:`float`
        :param npoints: number of points, 0 for endless acquisition
        :type npoints: :obj:`int`
        """
        BaseCounterAcquisitionSlave.__init__(
            self, *counters, count_time=count_time,
            npoints=max(1, npoints), prepare_once=True,
            start_once=npoints > 0, ctrl_params=ctrl_params)
        #: (:obj:`dict` <:obj:`str`, :obj:`list`>) string values
        self.strings = {}

    def _do_add_counter(self, counter):
        """ adds a counter, string counters have no channels

        :param counter: counter
        :type counter: :class:`NXSDataSourceCounter`
        """
        if getattr(counter, "isstring", False):
            self._counters[counter] = []
            self.strings[counter.name] = []
        else:
            BaseCounterAcquisitionSlave._do_add_counter(self, counter)

    def prepare(self):
        """ prepares the acquisition
        """
        self._nb_acq_points = 0
        for name in self.strings:
            self.strings[name] = []
        self.device.startScan()
        self.prepare_device()

    def start(self):
        """ starts the acquisition
        """
        self._stop_flag = False
        self.start_device()

    def stop(self):
        """ stops the acquisition
        """
        self._stop_flag = True
        self.stop_device()

    def trigger(self):
        """ reads the datasources of one scan point
        """
        if self._stop_flag:
            return
        counters = list(self._counters.keys())
        values = self.device.read_all(*counters)
        for counter, value in zip(counters, values):
            channels = self._counters[counter]
            if channels:
                for channel in channels:
                    channel.emit(value)
            elif counter.name in self.strings:
                self.strings[counter.name].append(value)
        self._nb_acq_points += 1

    def reading(self):
        """ the datasources are read by :meth:`trigger`
        """

    def get_acquisition_metadata(self, timing=None):
        """ provides string datasource values at the end of the scan

        :param timing: metadata timing
        :type timing: :class:`bliss.scanning.scan_meta.META_TIMING`
        :returns: metadata
        :rtype: :obj:`dict`
        """
        if META_TIMING is not None and timing == META_TIMING.END:
            if self.strings:
                return {name: list(values)
                        for name, values in self.strings.items()}
            return None
        return BaseCounterAcquisitionSlave.get_acquisition_metadata(
            self, timing=timing)


class NXSDataSourceController(CounterController):

    """ BLISS counter controller of NeXus configuration datasources
    """

    def __init__(self, name=CONTROLLER, reader=None, canfail=True):
        """ constructor

        :param name: controller name
        :type name: :obj:`str`
        :param reader: datasource reader
        :type reader: :class:`DataSourceReader`
        :param canfail: fill values of datasources which cannot be read,
                        stop the scan otherwise
        :type canfail: :obj:`bool`
        """
        if not BLISS_AVAILABLE:
            raise ImportError("BLISS is not available")
        CounterController.__init__(self, name)
        #: (:class:`DataSourceReader`) datasource reader
        self.reader = reader or DataSourceReader()
        #: (:obj:`bool`) fill values of datasources which cannot be read
        self.canfail = canfail
        #: (:obj:`set` <:obj:`str`>) datasources with reported errors
        self.__reported = set()

    def get_acquisition_object(self, acq_params, ctrl_params,
                               parent_acq_params):
        """ provides the acquisition object

        :param acq_params: acquisition parameters
        :type acq_params: :obj:`dict`
        :param ctrl_params: controller parameters
        :type ctrl_params: :obj:`dict`
        :param parent_acq_params: parent acquisition parameters
        :type parent_acq_params: :obj:`dict`
        :returns: acquisition object
        :rtype: :class:`NXSDataSourceAcquisitionSlave`
        """
        return NXSDataSourceAcquisitionSlave(
            self, ctrl_params=ctrl_params, **acq_params)

    def get_default_chain_parameters(self, scan_params, acq_params):
        """ provides default acquisition parameters

        :param scan_params: scan parameters
        :type scan_params: :obj:`dict`
        :param acq_params: acquisition parameters
        :type acq_params: :obj:`dict`
        :returns: acquisition parameters
        :rtype: :obj:`dict`
        """
        return {
            "count_time": acq_params.get(
                "count_time", scan_params.get("count_time")),
            "npoints": acq_params.get(
                "npoints", scan_params.get("npoints", 1)),
        }

    def setDataSources(self, datasources):
        """ sets the datasources and creates their counters

        :param datasources: datasource descriptions or XML definitions
                            by datasource names
        :type datasources: :obj:`dict` <:obj:`str`, :obj:`dict`>
        :returns: full names of the counters
        :rtype: :obj:`list` <:obj:`str`>
        """
        self.reader.setDataSources(datasources)
        names = self.reader.names()
        for cnt in list(self.counters):
            desc = self.reader.description(cnt.name) \
                if cnt.name in names else None
            if desc is None or \
               cnt.typename != numpyType(desc["nxtype"]) or \
               cnt.rank != desc["rank"]:
                self.remove(cnt)
        existing = set(cnt.name for cnt in self.counters)
        for name in names:
            if name not in existing:
                desc = self.reader.description(name)
                NXSDataSourceCounter(
                    name, self, numpyType(desc["nxtype"]), desc["rank"])
        return [cnt.fullname for cnt in self.counters]

    def startScan(self):
        """ resets error reports at the scan start
        """
        self.__reported = set()

    def read_all(self, *counters):
        """ reads the datasources of the counters

        :param counters: counters
        :type counters: :obj:`list` <:class:`NXSDataSourceCounter`>
        :returns: values converted to the counter types and ranks
        :rtype: :obj:`list` `any`
        :raises: :exc:`RuntimeError` if a datasource cannot be read
                 and :attr:`canfail` is False
        """
        values = self.reader.read([cnt.name for cnt in counters])
        errors = dict(self.reader.errors)
        result = []
        for cnt, value in zip(counters, values):
            if cnt.name not in errors:
                try:
                    result.append(convert(value, cnt.typename, cnt.rank))
                    continue
                except Exception as e:
                    errors[cnt.name] = str(e)
            if not self.canfail:
                raise RuntimeError(
                    "nxsrecconfig: datasource %s cannot be read: %s"
                    % (cnt.name, errors[cnt.name]))
            if cnt.name not in self.__reported:
                self.__reported.add(cnt.name)
                self.reader.log.warning(
                    "nxsrecconfig: datasource %s cannot be read: %s"
                    % (cnt.name, errors[cnt.name]))
            fill = fillValue(cnt.typename)
            if cnt.rank and cnt.typename != "str":
                fill = numpy.full((1,) * cnt.rank, fill,
                                  dtype=cnt.typename)
            elif cnt.rank:
                fill = numpy.full((1,) * cnt.rank, fill).tolist()
            result.append(fill)
        return result
