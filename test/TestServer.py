#    "$Name:  $";
#    "$Header:  $";
#=============================================================================
#
# file :        TestServer.py
#
# description : Python source for the TestServer and its commands. 
#                The class is derived from Device. It represents the
#                CORBA servant object which will be accessed from the
#                network. All commands which can be executed on the
#                TestServer are implemented in this file.
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
#=============================================================================
#          This file is generated by POGO
#    (Program Obviously used to Generate tango Object)
#
#         (c) - Software Engineering Group - ESRF
#=============================================================================
#


import PyTango
import sys
import numpy
import struct
import pickle

#==================================================================
#   TestServer Class Description:
#
#         My Simple Server
#
#==================================================================
#     Device States Description:
#
#   DevState.ON :  Server On
#==================================================================


class TestServer(PyTango.Device_4Impl):

#--------- Add you global variables here --------------------------

#------------------------------------------------------------------
#    Device constructor
#------------------------------------------------------------------
    def __init__(self,cl, name):
        PyTango.Device_4Impl.__init__(self,cl,name)
        TestServer.init_device(self)

#------------------------------------------------------------------
#    Device destructor
#------------------------------------------------------------------
    def delete_device(self):
        print "[Device delete_device method] for device",self.get_name()


#------------------------------------------------------------------
#    Device initialization
#------------------------------------------------------------------
    def init_device(self):
        print "In ", self.get_name(), "::init_device()"
        self.set_state(PyTango.DevState.ON)
        self.get_device_properties(self.get_device_class())
        env = {'new': {'ActiveMntGrp': 'nxsmntgrp',
                       'DataCompressionRank': 0,
                       'NeXusSelectorDevice': u'p09/nxsrecselector/1',
                       'ScanDir': u'/tmp/',
                       'ScanFile': [u'sar4r.nxs'],
                       'ScanID': 192,
                       '_ViewOptions': {'ShowDial': True}}}

        self.attr_Environment = ("pickle", pickle.dumps(env))
        self.attr_DoorList = ['test/door/1', 'test/door/2']

#------------------------------------------------------------------
#    Always excuted hook method
#------------------------------------------------------------------
    def always_executed_hook(self):
        print "In ", self.get_name(), "::always_excuted_hook()"



#==================================================================
#
#    TestServer read/write attribute methods
#
#==================================================================

#------------------------------------------------------------------
#    Read DoorList attribute
#------------------------------------------------------------------
    def read_DoorList(self, attr):
        print "In ", self.get_name(), "::read_DoorList()"
        
        #    Add your own code here
        
        attr.set_value(self.attr_DoorList)


#------------------------------------------------------------------
#    Write DoorList attribute
#------------------------------------------------------------------
    def write_DoorList(self, attr):
        print "In ", self.get_name(), "::write_DoorList()"

        #    Add your own code here

        self.attr_DoorList = attr.get_write_value()
        print "Attribute value = ", self.attr_DoorList



#------------------------------------------------------------------
#    Read Environment attribute
#------------------------------------------------------------------
    def read_Environment(self, attr):
        print "In ", self.get_name(), "::read_Environment()"
        
        #    Add your own code here
        
        attr.set_value(self.attr_Environment[0], self.attr_Environment[1])


#------------------------------------------------------------------
#    Write Environment attribute
#------------------------------------------------------------------
    def write_Environment(self, attr):
        print "In ", self.get_name(), "::write_Environment()"

        #    Add your own code here

        self.attr_Environment = attr.get_write_value()
        print "Attribute value = ", self.attr_Environment



#==================================================================
#
#    TestServer command methods
#
#==================================================================


#------------------------------------------------------------------
#    SetState command:
#
#    Description: Set state of tango device
#                
#    argin: DevString     tango state
#------------------------------------------------------------------
    def SetState(self, state):
        print "In ", self.get_name(), "::SetState()"
        if state == "RUNNING":
            self.set_state(PyTango.DevState.RUNNING)
        elif state == "FAULT":
            self.set_state(PyTango.DevState.FAULT)
        else:
            self.set_state(PyTango.DevState.ON)
    


#==================================================================
#
#    TestServerClass class definition
#
#==================================================================
class TestServerClass(PyTango.DeviceClass):

    #    Class Properties
    class_property_list = {
        }


    #    Device Properties
    device_property_list = {
        }


    #    Command definitions
    cmd_list = {
        'SetState':
            [[PyTango.DevString, "ScalarString"],
            [PyTango.DevVoid, ""]],
        }


    #    Attribute definitions
    attr_list = {
        'Environment':
            [[PyTango.DevEncoded,
              PyTango.SCALAR,
              PyTango.READ_WRITE],
            {
                'description':"Environment attribute",
            } ],
        'DoorList':
            [[PyTango.DevString,
              PyTango.SPECTRUM,
              PyTango.READ_WRITE,
              256],
            {
                'description':"Environment attribute",
            } ],
        }


#------------------------------------------------------------------
#    TestServerClass Constructor
#------------------------------------------------------------------
    def __init__(self, name):
        PyTango.DeviceClass.__init__(self, name)
        self.set_type(name);
        print "In TestServerClass  constructor"

#==================================================================
#
#    TestServer class main method
#
#==================================================================
if __name__ == '__main__':
    try:
        py = PyTango.Util(sys.argv)
        py.add_TgClass(TestServerClass,TestServer,'TestServer')

        U = PyTango.Util.instance()
        U.server_init()
        U.server_run()

    except PyTango.DevFailed,e:
        print '-------> Received a DevFailed exception:',e
    except Exception,e:
        print '-------> An unforeseen exception occured....',e