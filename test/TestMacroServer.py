#    "$Name:  $";
#    "$Header:  $";
# ============================================================================
#
# file :        TestMacroServer.py
#
# description : Python source for the TestMacroServer and its commands.
#                The class is derived from Device. It represents the
#                CORBA servant object which will be accessed from the
#                network. All commands which can be executed on the
#                TestMacroServer are implemented in this file.
#
# project :     TANGO Device Server
#
# $Author:  $
#
# $Revision:  $
#
# $Log:  $
#
# copyleft :    European Synchrotron Radiation Facility
#               BP 220, Grenoble 38043
#               FRANCE
#
# ============================================================================
#          This file is generated by POGO
#    (Program Obviously used to Generate tango Object)
#
#         (c) - Software Engineering Group - ESRF
# ============================================================================
#

import sys
import pickle

try:
    import tango
except Exception:
    import PyTango as tango

# # workaround for problems when pytango locally compiled
# if sys.version_info[0] == 2:
#     sys.path = [pth for pth in sys.path if 'python3' not in pth]
# else:
#     sys.path = [pth for pth in sys.path if 'python2' not in pth]
# tango = __import__("tango")


def pickleloads(bytestr):
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

# =================================================================
#   TestMacroServer Class Description:
#
#         My Simple Server
#
# =================================================================
#     Device States Description:
#
#   DevState.ON :  Server On
# =================================================================


class MacroServer(tango.Device_4Impl):

    # -------- Add you global variables here --------------------------

    # -----------------------------------------------------------------
    #    Device constructor
    # -----------------------------------------------------------------

    def __init__(self, cl, name):
        tango.Device_4Impl.__init__(self, cl, name)

        self.attr_value = ""
        MacroServer.init_device(self)
        self.attr_DoorList = ['doortestp09/testts/t1r228']

    # -----------------------------------------------------------------
    #    Device destructor
    # -----------------------------------------------------------------
    def delete_device(self):
        """ """

    # -----------------------------------------------------------------
    #    Device initialization
    # -----------------------------------------------------------------

    def init_device(self):
        self.set_state(tango.DevState.ON)
        self.get_device_properties(self.get_device_class())
        env = {'new': {'ActiveMntGrp': 'nxsmntgrp',
                       'DataCompressionRank': 0,
                       'NeXusSelectorDevice': u'p09/nxsrecselector/1',
                       'ScanDir': u'/tmp/',
                       'ScanFile': [u'sar4r.nxs'],
                       'ScanID': 192,
                       '_ViewOptions': {'ShowDial': True}}}

        self.attr_Environment = ("pickle", pickle.dumps(env, protocol=2))
        self.attr_DoorList = ['doortestp09/testts/t1r228']

    # -----------------------------------------------------------------
    #    Always excuted hook method
    # -----------------------------------------------------------------
    def always_executed_hook(self):
        pass

    # =================================================================
    #
    #    TestMacroServer read/write attribute methods
    #
    # =================================================================
    #
    # -----------------------------------------------------------------
    #    Read DoorList attribute
    # -----------------------------------------------------------------
    def read_DoorList(self, attr):
        #    Add your own code here

        attr.set_value(self.attr_DoorList or [])

    # -----------------------------------------------------------------
    #    Write DoorList attribute
    # -----------------------------------------------------------------
    def write_DoorList(self, attr):
        #    Add your own code here

        self.attr_DoorList = attr.get_write_value()

    # -----------------------------------------------------------------
    #    Read Environment attribute
    # -----------------------------------------------------------------
    def read_Environment(self, attr):
        #    Add your own code here

        attr.set_value(self.attr_Environment[0], self.attr_Environment[1])

    # -----------------------------------------------------------------
    #    Write Environment attribute
    # -----------------------------------------------------------------
    def write_Environment(self, attr):
        #    Add your own code here

        env = attr.get_write_value()
        envnew = {}
        envchange = {}
        envdel = []
        if env[0] == 'pickle':
            edict = pickleloads(env[1])
            if 'new' in edict.keys():
                envnew = edict['new']
            if 'change' in edict.keys():
                envchange = edict['change']
            if 'del' in edict.keys():
                envdel = edict['del']
            envdict = pickleloads(self.attr_Environment[1])
            if 'new' not in envdict.keys():
                envdict['new'] = {}
            newdict = envdict['new']
            newdict.update(envnew)
            newdict.update(envchange)
            for ed in envdel:
                if ed in newdict.keys():
                    newdict.pop(ed)
            self.attr_Environment = (
                "pickle",
                pickle.dumps(envdict, protocol=2))

    #
    # =================================================================
    #
    #    TestMacroServer command methods
    #
    # =================================================================
    #
    # -----------------------------------------------------------------
    #    SetState command:
    #
    #    Description: Set state of tango device
    #
    #    argin: DevString     tango state
    # -----------------------------------------------------------------
    def SetState(self, state):
        if state == "RUNNING":
            self.set_state(tango.DevState.RUNNING)
        elif state == "FAULT":
            self.set_state(tango.DevState.FAULT)
        elif state == "ALARM":
            self.set_state(tango.DevState.ALARM)
        else:
            self.set_state(tango.DevState.ON)


# =================================================================
#
#    MacroServerClass class definition
#
# =================================================================
class MacroServerClass(tango.DeviceClass):

    #    Class Properties
    class_property_list = {
    }

    #    Device Properties
    device_property_list = {
        'PoolNames':
            [tango.DevVarStringArray,
             "pool names",
             []],
    }

    #    Command definitions
    cmd_list = {
        'SetState':
            [[tango.DevString, "ScalarString"],
             [tango.DevVoid, ""]],
    }

    #    Attribute definitions
    attr_list = {
        'Environment':
            [[tango.DevEncoded,
              tango.SCALAR,
              tango.READ_WRITE],
             {
                 'description': "Environment attribute",
            }],
        'DoorList':
            [[tango.DevString,
              tango.SPECTRUM,
              tango.READ_WRITE,
              256],
             {
                 'description': "Environment attribute",
            }],
    }

# -----------------------------------------------------------------
#    MacroServerClass Constructor
# -----------------------------------------------------------------
    def __init__(self, name):
        tango.DeviceClass.__init__(self, name)
        self.set_type(name)


# =================================================================
#   TestDoor Class Description:
#
#         My Simple Server
#
# =================================================================
#     Device States Description:
#
#   DevState.ON :  Server On
# =================================================================

class Door(tango.Device_4Impl):

    # -------- Add you global variables here --------------------------

    # -----------------------------------------------------------------
    #    Device constructor
    # -----------------------------------------------------------------

    def __init__(self, cl, name):
        tango.Device_4Impl.__init__(self, cl, name)

        self.attr_value = ""
        Door.init_device(self)

    # -----------------------------------------------------------------
    #    Device destructor
    # -----------------------------------------------------------------
    def delete_device(self):
        self.get_name()

    # -----------------------------------------------------------------
    #    Device initialization
    # -----------------------------------------------------------------
    def init_device(self):
        self.set_state(tango.DevState.ON)
        self.get_device_properties(self.get_device_class())

    # -----------------------------------------------------------------
    #    Always excuted hook method
    # -----------------------------------------------------------------
    def always_executed_hook(self):
        pass

    # =================================================================
    #
    #    TestDoor read/write attribute methods
    #
    # =================================================================
    #
    # =================================================================
    #
    #    TestDoor command methods
    #
    # =================================================================
    #
    # -----------------------------------------------------------------
    #    SetState command:
    #
    #    Description: Set state of tango device
    #
    #    argin: DevString     tango state
    # -----------------------------------------------------------------
    def SetState(self, state):
        if state == "RUNNING":
            self.set_state(tango.DevState.RUNNING)
        elif state == "FAULT":
            self.set_state(tango.DevState.FAULT)
        elif state == "ALARM":
            self.set_state(tango.DevState.ALARM)
        else:
            self.set_state(tango.DevState.ON)


# =================================================================
#
#    DoorClass class definition
#
# =================================================================
class DoorClass(tango.DeviceClass):

    #    Class Properties
    class_property_list = {
    }

    #    Device Properties
    device_property_list = {
    }

    #    Command definitions
    cmd_list = {
        'SetState':
            [[tango.DevString, "ScalarString"],
             [tango.DevVoid, ""]],
    }

    #    Attribute definitions
    attr_list = {
    }

# -----------------------------------------------------------------
#    DoorClass Constructor
# -----------------------------------------------------------------
    def __init__(self, name):
        tango.DeviceClass.__init__(self, name)
        self.set_type(name)


# =================================================================
#
#    MacroServer class main method
#
# =================================================================
if __name__ == '__main__':
    try:
        argv = list(sys.argv)
        argv[0] = "MacroServer"
        py = tango.Util(argv)
        py.add_class(MacroServerClass, MacroServer)
        py.add_class(DoorClass, Door)

        U = tango.Util.instance()
        U.server_init()
        U.server_run()

    except tango.DevFailed as e:
        print('-------> Received a DevFailed exception: %s' % e)
    except Exception as e:
        print('-------> An unforeseen exception occured.... %s' % e)
