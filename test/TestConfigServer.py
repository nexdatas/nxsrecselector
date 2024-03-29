#    "$Name:  $";
#    "$Header:  $";
# ============================================================================
#
# file :        TestConfigServer.py
#
# description : Python source for the TestConfigServer and its commands.
#                The class is derived from Device. It represents the
#                CORBA servant object which will be accessed from the
#                network. All commands which can be executed on the
#                TestConfigServer are implemented in this file.
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
import json
import re

try:
    import tango
except Exception:
    import PyTango as tango

# =================================================================
#   TestConfigServer Class Description:
#
#         My Simple Server
#
# =================================================================
#     Device States Description:
#
#   DevState.ON :  Server On
# =================================================================


class NXSConfigServer(tango.LatestDeviceImpl):

    # -------- Add you global variables here --------------------------

    # -----------------------------------------------------------------
    #    Device constructor
    # -----------------------------------------------------------------

    def __init__(self, cl, name):
        tango.LatestDeviceImpl.__init__(self, cl, name)

        self.attr_value = ""
        NXSConfigServer.init_device(self)

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

        self.attr_XMLString = ""
        self.attr_Version = "2.0.0"
        self.attr_Selection = ""
        self.attr_JSONSettings = ""
        self.attr_STEPDataSources = ""
        self.attr_CanFailDataSources = ""
        self.attr_LinkDataSources = ""
        self.attr_Variables = "{}"

        self.cmd = {}
        self.cmd["CPDICT"] = {}
        self.cmd["DSDICT"] = {}
        self.cmd["SELDICT"] = {}
        self.cmd["VARS"] = []
        self.cmd["COMMANDS"] = []
        self.cmd["MCPLIST"] = []
        self.cmd["VALUE"] = None
        self.cmd["CHECKVARIABLES"] = "{}"

        self.get_device_properties(self.get_device_class())

    # -----------------------------------------------------------------
    #    Always excuted hook method
    # -----------------------------------------------------------------
    def always_executed_hook(self):
        pass

    # -----------------------------------------------------------------
    #    Read Version attribute
    # -----------------------------------------------------------------
    def read_Version(self, attr):
        attr.set_value(self.attr_Version)

    # -----------------------------------------------------------------
    #    Read XMLString attribute
    # -----------------------------------------------------------------
    def read_XMLString(self, attr):
        attr.set_value(self.attr_XMLString)

    # -----------------------------------------------------------------
    #    Write XMLString attribute
    # -----------------------------------------------------------------
    def write_XMLString(self, attr):
        self.attr_XMLString = attr.get_write_value()

    # -----------------------------------------------------------------
    #    Read Selection attribute
    # -----------------------------------------------------------------
    def read_Selection(self, attr):
        attr.set_value(self.attr_Selection)

    # -----------------------------------------------------------------
    #    Write Selection attribute
    # -----------------------------------------------------------------
    def write_Selection(self, attr):
        self.attr_Selection = attr.get_write_value()

    # -----------------------------------------------------------------
    #    Read JSONSettings attribute
    # -----------------------------------------------------------------
    def read_JSONSettings(self, attr):
        attr.set_value(self.attr_JSONSettings)

    # -----------------------------------------------------------------
    #    Write JSONSettings attribute
    # -----------------------------------------------------------------
    def write_JSONSettings(self, attr):
        self.attr_JSONSettings = attr.get_write_value()

    # -----------------------------------------------------------------
    #    Read STEPDataSources attribute
    # -----------------------------------------------------------------
    def read_STEPDataSources(self, attr):
        attr.set_value(self.attr_STEPDataSources)

    # -----------------------------------------------------------------
    #    Write STEPDataSources attribute
    # -----------------------------------------------------------------
    def write_STEPDataSources(self, attr):
        self.attr_STEPDataSources = attr.get_write_value()

    # -----------------------------------------------------------------
    #    Read CanFailDataSources attribute
    # -----------------------------------------------------------------
    def read_CanFailDataSources(self, attr):
        attr.set_value(self.attr_CanFailDataSources)

    # -----------------------------------------------------------------
    #    Write CanFailDataSources attribute
    # -----------------------------------------------------------------
    def write_CanFailDataSources(self, attr):
        self.attr_CanFailDataSources = attr.get_write_value()

    # -----------------------------------------------------------------
    #    Read LinkDataSources attribute
    # -----------------------------------------------------------------
    def read_LinkDataSources(self, attr):
        attr.set_value(self.attr_LinkDataSources)

    # -----------------------------------------------------------------
    #    Write LinkDataSources attribute
    # -----------------------------------------------------------------
    def write_LinkDataSources(self, attr):
        self.attr_LinkDataSources = attr.get_write_value()

    # -----------------------------------------------------------------
    def read_Variables(self, attr):
        attr.set_value(self.attr_Variables)

    # -----------------------------------------------------------------
    #    Write Variables attribute
    # -----------------------------------------------------------------
    def write_Variables(self, attr):
        self.attr_Variables = attr.get_write_value()

    #
    # =================================================================
    #
    #    NXSConfigServer command methods
    #
    # =================================================================
    #
    # -----------------------------------------------------------------
    #    Open command:
    #
    #    Description: Opens connection to the database
    #
    # -----------------------------------------------------------------
    def Open(self):
        """ """

    # -----------------------------------------------------------------
    #    Close command:
    #
    #    Description: Closes connection into the database
    #
    # -----------------------------------------------------------------

    def Close(self):
        """ """

    # -----------------------------------------------------------------
    #    Components command:
    #
    #    Description: Returns a list of required components
    #
    #    argin:  DevVarStringArray    list of component names
    #    argout: DevVarStringArray    list of required components
    # -----------------------------------------------------------------

    def Components(self, names):
        self.cmd["VARS"].append(names)
        self.cmd["COMMANDS"].append("Components")
        return [self.cmd["CPDICT"][nm] for nm in names
                if nm in self.cmd["CPDICT"].keys()]

    # -----------------------------------------------------------------
    #    ComponentVariables command:
    #
    #    Description: Returns a list of required componentVariables
    #
    #    argin:  DevString    list of component names
    #    argout: DevVarStringArray    list of required componentVariables
    # -----------------------------------------------------------------
    def ComponentVariables(self, name):
        self.cmd["VARS"].append(name)
        self.cmd["COMMANDS"].append("ComponentVariables")
        cp = self.cmd["CPDICT"][name]
        return self.__findText(cp, "$var.")

    def __findText(self, text, label):
        variables = []
        index = text.find(label)
        while index != -1:
            try:
                if sys.version_info > (3,):
                    subc = re.finditer(
                        r"[\w]+",
                        text[(index + len(label)):]
                    ).__next__().group(0)
                else:
                    subc = re.finditer(
                        r"[\w]+",
                        text[(index + len(label)):]
                    ).next().group(0)
            except Exception as e:
                print("Error: %s" % str(e))
                subc = ""
            name = subc.strip() if subc else ""
            if name:
                variables.append(name)
            index = text.find(label, index + 1)
        return variables

    def DependentComponents(self, argin):
        """ DependentComponents command

        :brief: returns a list of dependent component names
            for a given components

        :param argin:  DevVarStringArray    component names
        :type argin: :obj:`list` <:obj:`str`>
        :returns: DevVarStringArray    list of component names
        :rtype: :obj:`list` <:obj:`str`>
        """
        self.debug_stream("In DependentComponents()")
        self.cmd["VARS"].append(argin)
        self.cmd["COMMANDS"].append("DependentComponents")
        res = []
        for name in argin:
            res.append(name)
            cp = self.cmd["CPDICT"][name]
            res.extend(self.__findText(cp, "$components."))
        return res

    # -----------------------------------------------------------------
    #    Selections command:
    #
    #    Description: Returns a list of required selections
    #
    #    argin:  DevVarStringArray    list of selection names
    #    argout: DevVarStringArray    list of required selections
    # -----------------------------------------------------------------
    def Selections(self, names):
        self.cmd["VARS"].append(names)
        self.cmd["COMMANDS"].append("Selections")
        return [self.cmd["SELDICT"][nm] for nm in names
                if nm in self.cmd["SELDICT"].keys()]

    # -----------------------------------------------------------------
    #    InstantiatedComponents command:
    #
    #    Description: Returns a list of required components
    #
    #    argin:  DevVarStringArray    list of component names
    #    argout: DevVarStringArray    list of instantiated components
    # -----------------------------------------------------------------
    def InstantiatedComponents(self, names):
        if self.attr_Variables and self.cmd["CHECKVARIABLES"]:
            d1 = json.loads(self.cmd["CHECKVARIABLES"])
            d2 = json.loads(self.attr_Variables)
            if len(d1) != len(d2):
                raise Exception("Variables not set")
            for ky, vl in d1.items():
                if ky not in d2.keys():
                    raise Exception("Variables not set")
                if d1[ky] != d2[ky]:
                    raise Exception("Variables not set")

        elif self.cmd["CHECKVARIABLES"] != self.attr_Variables:
            raise Exception("Variables not set")
        self.cmd["VARS"].append(names)
        self.cmd["COMMANDS"].append("InstantiatedComponents")
        return [self.cmd["CPDICT"][nm] for nm in names
                if nm in self.cmd["CPDICT"].keys()]

    # -----------------------------------------------------------------
    #    DataSources command:
    #
    #    Description: Return a list of required DataSources
    #
    #    argin:  DevVarStringArray    list of DataSource names
    #    argout: DevVarStringArray    list of required DataSources
    # -----------------------------------------------------------------
    def DataSources(self, names):
        self.cmd["VARS"].append(names)
        self.cmd["COMMANDS"].append("DataSources")
        return [self.cmd["DSDICT"][nm] for nm in names
                if nm in self.cmd["DSDICT"].keys()]

    # -----------------------------------------------------------------
    #    AvailableComponents command:
    #
    #    Description: Returns a list of available component names
    #
    #    argout: DevVarStringArray    list of available component names
    # -----------------------------------------------------------------
    def AvailableComponents(self):
        self.cmd["VARS"].append(None)
        self.cmd["COMMANDS"].append("AvailableComponents")
        return list(self.cmd["CPDICT"].keys())

    # -----------------------------------------------------------------
    #    AvailableSelections command:
    #
    #    Description: Returns a list of available selection names
    #
    #    argout: DevVarStringArray    list of available selection names
    # -----------------------------------------------------------------
    def AvailableSelections(self):
        self.cmd["VARS"].append(None)
        self.cmd["COMMANDS"].append("AvailableSelections")
        return list(self.cmd["SELDICT"].keys())

    # -----------------------------------------------------------------
    #    AvailableDataSources command:
    #
    #    Description: Returns a list of available DataSource names
    #
    #    argout: DevVarStringArray    list of available DataSource names
    # -----------------------------------------------------------------
    def AvailableDataSources(self):
        self.cmd["VARS"].append(None)
        self.cmd["COMMANDS"].append("AvailableDataSources")
        return list(self.cmd["DSDICT"].keys())

    # -----------------------------------------------------------------
    #    MandatoryComponents command:
    #
    #    Description: Sets the mandatory components
    #
    #    argout: DevVarStringArray    component names
    # -----------------------------------------------------------------
    def MandatoryComponents(self):
        #    Add your own code here

        self.cmd["VARS"].append(None)
        self.cmd["COMMANDS"].append("MandatoryComponents")
        return list(self.cmd["MCPLIST"])

    # -----------------------------------------------------------------
    #    StoreSelection command:
    #
    #    Description: Stores the selection from XMLString
    #
    #    argin:  DevString    selection name
    # -----------------------------------------------------------------
    def StoreSelection(self, argin):
        self.cmd["VARS"].append(argin)
        self.cmd["COMMANDS"].append("StoreSelection")
        self.cmd["SELDICT"][str(argin)] = self.attr_Selection

    # -----------------------------------------------------------------
    #    StoreDataSource command:
    #
    #    Description: Stores the selection from XMLString
    #
    #    argin:  DevString    selection name
    # -----------------------------------------------------------------
    def StoreDataSource(self, argin):
        self.cmd["VARS"].append(argin)
        self.cmd["COMMANDS"].append("StoreDataSource")
        self.cmd["DSDICT"][str(argin)] = self.attr_XMLString

    # -----------------------------------------------------------------
    #    StoreComponent command:
    #
    #    Description: Stores the component from XMLString
    #
    #    argin:  DevString    component name
    # -----------------------------------------------------------------
    def StoreComponent(self, argin):
        self.cmd["VARS"].append(argin)
        self.cmd["COMMANDS"].append("StoreComponent")
        self.cmd["CPDICT"][str(argin)] = self.attr_XMLString

    # -----------------------------------------------------------------
    #    DeleteComponent command:
    #
    #    Description: Deletes the component from XMLString
    #
    #    argin:  DevString    component name
    # -----------------------------------------------------------------
    def DeleteComponent(self, argin):
        self.cmd["VARS"].append(argin)
        self.cmd["COMMANDS"].append("DeleteComponent")
        self.cmd["CPDICT"].pop(str(argin))

    # -----------------------------------------------------------------
    #    DeleteSelection command:
    #
    #    Description: Deletes the selection from XMLString
    #
    #    argin:  DevString    selection name
    # -----------------------------------------------------------------
    def DeleteSelection(self, argin):
        self.cmd["VARS"].append(argin)
        self.cmd["COMMANDS"].append("DeleteSelection")
        self.cmd["SELDICT"].pop(str(argin))

    # -----------------------------------------------------------------
    #    DeleteDataSource command:
    #
    #    Description: Deletes the datasource from XMLString
    #
    #    argin:  DevString    datasource name
    # -----------------------------------------------------------------
    def DeleteDataSource(self, argin):
        self.cmd["VARS"].append(argin)
        self.cmd["COMMANDS"].append("DeleteDataSource")
        self.cmd["DSDICT"].pop(str(argin))

    # -----------------------------------------------------------------
    #    CreateConfiguration command:
    #
    #    Description: Creates the NDTS configuration script from the
    #                 given components. The result is strored in XMLString
    #
    #    argin:  DevVarStringArray    list of component names
    # -----------------------------------------------------------------
    def CreateConfiguration(self, argin):
        self.cmd["VARS"].append(argin)
        self.cmd["COMMANDS"].append("CreateConfiguration")

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

    # -----------------------------------------------------------------
    #    GetCommandVariable command:
    #
    #    Description: Get command variable
    #
    #    argin: DevString     variable
    # -----------------------------------------------------------------
    def GetCommandVariable(self, variable):
        return json.dumps(self.cmd[variable])

    # -----------------------------------------------------------------
    #    SetCommandVariable command:
    #
    #    Description: Set command variable
    #
    #    argin: DevVarStringArray     variable
    # -----------------------------------------------------------------
    def SetCommandVariable(self, record):
        self.cmd[record[0]] = json.loads(record[1])


# =================================================================
#
#    NXSConfigServerClass class definition
#
# =================================================================
class NXSConfigServerClass(tango.DeviceClass):

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
        'Open':
            [[tango.DevVoid, ""],
             [tango.DevVoid, ""]],
        'Close':
            [[tango.DevVoid, ""],
             [tango.DevVoid, ""]],
        'Components':
            [[tango.DevVarStringArray, "list of component names"],
             [tango.DevVarStringArray, "list of required components"]],
        'Selections':
            [[tango.DevVarStringArray, "list of selection names"],
             [tango.DevVarStringArray, "list of required selections"]],
        'InstantiatedComponents':
            [[tango.DevVarStringArray, "list of component names"],
             [tango.DevVarStringArray, "list of instantiated components"]],
        'DataSources':
            [[tango.DevVarStringArray, "list of DataSource names"],
             [tango.DevVarStringArray, "list of required DataSources"]],
        'AvailableComponents':
            [[tango.DevVoid, ""],
             [tango.DevVarStringArray, "list of available component names"]],
        'AvailableSelections':
            [[tango.DevVoid, ""],
             [tango.DevVarStringArray, "list of available selection names"]],
        'AvailableDataSources':
            [[tango.DevVoid, ""],
             [tango.DevVarStringArray,
              "list of available DataSource names"]],
        'StoreSelection':
            [[tango.DevString, "selection name"],
             [tango.DevVoid, ""]],
        'CreateConfiguration':
            [[tango.DevVarStringArray, "list of component names"],
             [tango.DevVoid, ""]],
        'MandatoryComponents':
            [[tango.DevVoid, ""],
             [tango.DevVarStringArray, "component names"]],
        'StoreComponent':
            [[tango.DevString, "component name"],
             [tango.DevVoid, ""]],
        'StoreDataSource':
            [[tango.DevString, "datasource name"],
             [tango.DevVoid, ""]],
        'DeleteComponent':
            [[tango.DevString, "component name"],
             [tango.DevVoid, ""]],
        'DeleteSelection':
            [[tango.DevString, "selection name"],
             [tango.DevVoid, ""]],
        'DeleteDataSource':
            [[tango.DevString, "datasource name"],
             [tango.DevVoid, ""]],
        'SetCommandVariable':
            [[tango.DevVarStringArray, "(name,jsonstring)"],
             [tango.DevVoid, ""]],
        'GetCommandVariable':
            [[tango.DevString, "name"],
             [tango.DevString, "jsonstring"]],
        'ComponentVariables':
            [[tango.DevString, "component name"],
             [tango.DevVarStringArray, "list of variable names"]],
        'DependentComponents':
            [[tango.DevVarStringArray, "component names"],
             [tango.DevVarStringArray, "list of component names"]],
    }

    #    Attribute definitions
    attr_list = {
        'XMLString':
            [[tango.DevString,
              tango.SCALAR,
              tango.READ_WRITE],
             {
                 'label': "XML configuration",
                 'description':
                 "It allows to pass XML strings into database during "
                 "performing StoreComponent and StoreDataSource."
                 "\nMoreover, after performing CreateConfiguration "
                 "it contains the resulting XML configuration.",
                 'Display level': tango.DispLevel.EXPERT,
            }],
        'Selection':
            [[tango.DevString,
              tango.SCALAR,
              tango.READ_WRITE],
             {
                 'label': "Selected Component",
                 'description':
                 "It allows to pass JSON strings into database during "
                 "performing StoreSelection.",
                 'Display level': tango.DispLevel.EXPERT,
            }],
        'JSONSettings':
            [[tango.DevString,
              tango.SCALAR,
              tango.READ_WRITE],
             {
                 'label': "Arguments of MySQLdb.connect(...)",
                 'description': "The JSON string with parameters of "
                 "MySQLdb.connect(...).",
                 'Memorized': "true",
                 'Display level': tango.DispLevel.EXPERT,
            }],
        'Variables':
            [[tango.DevString,
              tango.SCALAR,
              tango.READ_WRITE],
             {
                 'label': "XML configuration variables",
                 'description': "The JSON string with "
                 "XML configuration variables",
            }],
        'STEPDataSources':
            [[tango.DevString,
              tango.SCALAR,
              tango.READ_WRITE],
             {
                 'label': "datasources to be switched into STEP mode",
                 'description': "datasources to be switched "
                 "into STEP mode during creating configuration process",
            }],
        'CanFailDataSources':
            [[tango.DevString,
              tango.SCALAR,
              tango.READ_WRITE],
             {
                 'label': "datasources to be switched into CanFail mode",
                 'description': "datasources to be switched "
                 "into CanFail mode during creating configuration process",
            }],
        'LinkDataSources':
            [[tango.DevString,
              tango.SCALAR,
              tango.READ_WRITE],
             {
                 'label': "datasources to be switched into Link mode",
                 'description': "datasources to be switched "
                 "into Link mode during creating configuration process",
            }],
        'Version':
            [[tango.DevString,
              tango.SCALAR,
              tango.READ],
             {
                 'label': "Configuration Version",
                 'description': "Configuration version",
            }],
    }

# -----------------------------------------------------------------
#    NXSConfigServerClass Constructor
# -----------------------------------------------------------------
    def __init__(self, name):
        tango.DeviceClass.__init__(self, name)
        self.set_type(name)
        # print "In TestConfigServerClass  constructor"


# =================================================================
#
#    NXSConfigServer class main method
#
# =================================================================
if __name__ == '__main__':
    try:
        argv = list(sys.argv)
        argv[0] = "NXSConfigServer"
        py = tango.Util(argv)
        py.add_class(NXSConfigServerClass, NXSConfigServer)

        U = tango.Util.instance()
        U.server_init()
        U.server_run()

    except tango.DevFailed as e:
        print('-------> Received a DevFailed exception: %s' % e)
    except Exception as e:
        print('-------> An unforeseen exception occured.... %s' % e)
