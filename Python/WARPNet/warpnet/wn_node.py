# -*- coding: utf-8 -*-
"""
------------------------------------------------------------------------------
WARPNet Node
------------------------------------------------------------------------------
Authors:   Chris Hunter (chunter [at] mangocomm.com)
           Patrick Murphy (murphpo [at] mangocomm.com)
           Erik Welsh (welsh [at] mangocomm.com)
License:   Copyright 2014, Mango Communications. All rights reserved.
           Distributed under the WARP license (http://warpproject.org/license)
------------------------------------------------------------------------------
MODIFICATION HISTORY:

Ver   Who  Date     Changes
----- ---- -------- -----------------------------------------------------
1.00a ejw  1/23/14  Initial release

------------------------------------------------------------------------------

This module provides class definition for WARPNet Node.

Functions (see below for more information):
    WnNode() -- Base class for WARPNet node
    WnNodeFactory() -- Base class for creating WARPNet nodes

Integer constants:
    NODE_TYPE, NODE_ID, NODE_HW_GEN, NODE_DESIGN_VER, NODE_SERIAL_NUM, 
      NODE_FPGA_DNA -- Node hardware parameter constants 

If additional hardware parameters are needed for sub-classes of WnNode, please
make sure that the values of these hardware parameters are not reused.

"""

from . import wn_defaults
from . import wn_util
from . import wn_config
from . import wn_message
from . import wn_cmds
from . import wn_exception as ex
from . import wn_transport
from . import wn_transport_eth_udp_py
from . import wn_transport_eth_udp_py_bcast


__all__ = ['WnNode', 'WnNodeFactory']


# WARPNet Node Parameter Identifiers
#   NOTE:  The C counterparts are found in *_node.h
NODE_TYPE               = 0
NODE_ID                 = 1
NODE_HW_GEN             = 2
NODE_DESIGN_VER         = 3
NODE_SERIAL_NUM         = 4
NODE_FPGA_DNA           = 5



class WnNode(object):
    """Base Class for WARPNet node.
    
    The WARPNet node represents one node in a WARPNet network.  This class
    is the primary interface for interacting with nodes by providing methods
    for sending commands and checking status of nodes.
    
    By default, the base WARPNet node provides many useful node attributes
    as well as a transport component.
    
    Attributes:
        node_type -- Unique type of the WARPNet node
        node_id -- Unique identification for this node
        name -- User specified name for this node (supplied by user scripts)
        description -- String description of this node (auto-generated)
        serial_number -- Node's serial number, read from EEPROM on hardware
        fpga_dna -- Node's FPGA'a unique identification (on select hardware)
        hw_ver -- WARP hardware version of this node
        wn_ver_major -- WARPNet version running on this node
        wn_ver_minor
        wn_ver_revision
        
        transport -- Node's transport object
        transport_bcast -- Node's broadcast transport object
    """
    node_type       = None
    node_id         = None
    name            = None
    description     = None
    serial_number   = None
    fpga_dna        = None
    hw_ver          = None
    wn_ver_major    = None
    wn_ver_minor    = None
    wn_ver_revision = None

    transport       = None
    transport_bcast = None
    
    def __init__(self):
        (self.wn_ver_major, self.wn_ver_minor, self.wn_ver_revision) = wn_util.wn_ver(output=0)


    def __del__(self):
        """Clears the transport object to close any open socket connections
        in the event the node is deleted"""
        if self.transport:
            self.transport.wn_close()
            self.transport = None

        if self.transport_bcast:
            self.transport_bcast.wn_close()
            self.transport_bcast = None


    def set_init_configuration(self, serial_number,
                               node_id=wn_defaults.WN_NODE_DEFAULT_NODE_ID, 
                               node_name=wn_defaults.WN_NODE_DEFAULT_NAME, 
                               ip_address=wn_defaults.WN_NODE_DEFAULT_IP_ADDR, 
                               unicast_port=wn_defaults.WN_NODE_DEFAULT_UNICAST_PORT, 
                               bcast_port=wn_defaults.WN_NODE_DEFAULT_BCAST_PORT):
        """Set the initial configuration of the node."""
        config =  wn_config.WnConfiguration()
        
        if (config.get_param('network', 'transport_type') == 'python'):
            if self.transport is None:
                self.transport = wn_transport_eth_udp_py.WnTransportEthUdpPy()
            if self.transport_bcast is None:
                self.transport_bcast = wn_transport_eth_udp_py_bcast.WnTransportEthUdpPyBcast()
        else:
            print("Transport not defined\n")
        
        # Set Node information
        self.node_id = node_id
        self.name = node_name
        self.serial_number = serial_number

        # Set Node Unicast Transport information
        self.transport.wn_open(ip_address, unicast_port)
        self.transport.bcast_port = bcast_port
        self.transport.hdr.set_src_id(int(config.get_param('network', 'host_id')))
        self.transport.hdr.set_dest_id(node_id)

        # Set Node Broadcast Transport information
        self.transport_bcast.wn_open(ip_address, bcast_port)
        self.transport_bcast.unicast_port = unicast_port
        self.transport_bcast.hdr.set_src_id(int(config.get_param('network', 'host_id')))
        self.transport_bcast.hdr.set_dest_id(0xFFFF)


    def configure_node(self, jumbo_frame_support=False):
        """Get remaining information from the node and set remaining parameters."""
        
        self.transport.ping(self)
        self.transport.test_payload_size(self, jumbo_frame_support)        

        resp = self.get_node_info()
        self.process_parameters(resp)

        # Set description
        self.description = str("WARP v{} Node - ID {}".format(self.hw_ver, self.node_id))


    #-------------------------------------------------------------------------
    # WARPNet Commands for the Node
    #-------------------------------------------------------------------------
    def identify(self):
        """Have the node physically identify itself."""
        self.send_cmd(wn_cmds.WnCmdIdentify("W3-a-{0:05d}".format(self.serial_number)))

    def ping(self):
        """Ping the node."""
        self.transport.ping(self, output=True)

    def get_node_info(self):
        """Get the Hardware Information from the node."""
        return self.send_cmd(wn_cmds.WnCmdGetHwInfo())

    def setup_node_network_inf(self):
        """Setup the transport network information for the node."""
        self.send_cmd_bcast(wn_cmds.WnCmdNetworkSetup(self))
        
    def get_warpnet_node_type(self):
        """Get the WARPNet node type of the node."""
        if self.node_type is None:
            return self.send_cmd(wn_cmds.WnCmdGetWarpNetNodeType())
        else:
            return self.node_type

    #-------------------------------------------------------------------------
    # WARPNet Parameter Framework
    #   Allows for processing of hardware parameters
    #-------------------------------------------------------------------------
    def process_parameters(self, parameters):
        """Process all parameters.
        
        Each parameter is of the form:
                   | 31 ... 24 | 23 ... 16 | 15 ... 8 | 7 ... 0 |
            Word 0 | Reserved  | Group     | Length             |
            Word 1 | Parameter Identifier                       |
            Word 2 | Value 0 of Parameter                       |
            ...
            Word N | Value M of Parameter                       |
            
        where the number of parameters, M, is equal to the Length field
        """
        
        param_start = 0
        param_end   = len(parameters)
        
        while (param_start < param_end):
            param_group = (parameters[param_start] & 0x00FF0000) >> 16
            param_length = (parameters[param_start] & 0x0000FFFF)
            param_identifier = parameters[param_start+1]

            value_start = param_start + 2
            value_end = value_start + param_length
            
            param_values = parameters[value_start:value_end]
            
            # print(str("Param Start = " + str(param_start) + "\n" +
            #           "    param_group  = " + str(param_group) + "\n" + 
            #           "    param_length = " + str(param_length) + "\n" + 
            #           "    param_id     = " + str(param_identifier) + "\n"))
            
            self.process_parameter_group(param_group, param_identifier, 
                                         param_length, param_values)
            
            param_start = value_end


    def process_parameter_group(self, group, identifier, length, values):
        """Process the Parameter Group"""
        if   (group == wn_cmds.GRPID_NODE):
            self.process_parameter(identifier, length, values)
        elif (group == wn_cmds.GRPID_TRANS):
            self.transport.process_parameter(identifier, length, values)
        else:
            raise ex.WnParameterError("Group", "Unknown Group: {}".format(group))


    def process_parameter(self, identifier, length, values):
        """Extract values from the parameters"""
        if   (identifier == NODE_TYPE):
            if (length == 1):
                self.node_type = values[0]
            else:
                raise ex.WnParameterError("NODE_TYPE", "Incorrect length")

        elif (identifier == NODE_ID):
            if (length == 1):
                self.node_id = values[0]
            else:
                raise ex.WnParameterError("NODE_ID", "Incorrect length")

        elif (identifier == NODE_HW_GEN):
            if (length == 1):
                self.hw_ver = (values[0] & 0xFF)
            else:
                raise ex.WnParameterError("NODE_HW_GEN", "Incorrect length")

        elif (identifier == NODE_DESIGN_VER):
            if (length == 1):                
                self.wn_ver_major = (values[0] & 0x00FF0000) >> 16
                self.wn_ver_minor = (values[0] & 0x0000FF00) >> 8
                self.wn_ver_revision = (values[0] & 0x000000FF)                
                
                # Check to see if there is a version mismatch
                self.check_ver()
            else:
                raise ex.WnParameterError("NODE_DESIGN_VER", "Incorrect length")

        elif (identifier == NODE_SERIAL_NUM):
            if (length == 1):
                self.serial_number = values[0]
            else:
                raise ex.WnParameterError("NODE_SERIAL_NUM", "Incorrect length")

        elif (identifier == NODE_FPGA_DNA):
            if (length == 2):
                self.fpga_dna = (2**32 * values[1]) + values[0]
            else:
                raise ex.WnParameterError("NODE_FPGA_DNA", "Incorrect length")

        else:
            raise ex.WnParameterError(identifier, "Unknown node parameter")


    #-------------------------------------------------------------------------
    # Transmit / Receive methods for the Node
    #-------------------------------------------------------------------------
    def send_cmd(self, cmd, max_attempts=2):
        """Send the provided command.
        
        Attributes:
            cmd -- WnCommand to send
            max_attempts -- Maximum number of attempts to send a given command
        """
        resp_type = cmd.get_resp_type()
        payload = cmd.serialize()
        
        if  (resp_type == wn_transport.TRANSPORT_NO_RESP):
            self.transport.send(payload, robust=False)

        elif (resp_type == wn_transport.TRANSPORT_WN_RESP):
            resp = self._receive_resp(payload, max_attempts)
            return cmd.process_resp(resp)

        elif (resp_type == wn_transport.TRANSPORT_WN_BUFFER):
            resp = self._receive_buffer(cmd, payload, max_attempts)
            return cmd.process_resp(resp)

        else:
            raise ex.WnTransportError(self.transport, 
                                      "Unknown response type for command")


    def _receive_resp(self, payload, max_attempts):
        """Internal method to receive a response for a given command payload"""
        reply = b''
        curr_tx = 1
        done = False
        resp = wn_message.WnResp()

        self.transport.send(payload)

        while not done:
            try:
                reply = self.transport.receive()
            except ex.WnTransportError:
                if curr_tx == max_attempts:
                    raise ex.WnTransportError(self.transport, 
                                              "Max retransmissions without reply from node")

                self.transport.send(payload)
                curr_tx += 1
            else:
                resp.deserialize(reply)
                done = True
                
        return resp


    def _receive_buffer(self, cmd, payload, max_attempts):
        """Internal method to receive a buffer for a given command payload"""
        reply = b''
        curr_tx = 1
        resp = wn_message.WnBuffer(cmd.get_buffer_id(),
                                   cmd.get_buffer_flags(),
                                   cmd.get_buffer_size())

        self.transport.send(payload)

        while not resp.is_buffer_complete():
            try:
                reply = self.transport.receive()
            except ex.WnTransportError:
                # If there is a timeout, then request missing part of the buffer
                if curr_tx == max_attempts:
                    raise ex.WnTransportError(self.transport, 
                                              "Max retransmissions without reply from node")

                # TODO:  Currently, we are just requesting the entire buffer
                #   over.  This is not a good long term solution and should 
                #   eventually be changed to only request the missing piece
                #   of the buffer
                resp = wn_message.WnBuffer(cmd.get_buffer_id(),
                                           cmd.get_buffer_flags(),
                                           cmd.get_buffer_size())
                
                self.transport.send(payload)
                curr_tx += 1
            else:
                resp.add_data_to_buffer(reply)
                    
        return resp
        
    
    def send_cmd_bcast(self, cmd):
        """Send the provided command over the broadcast transport.

        NOTE:  Currently, broadcast commands cannot have a response.
        
        Attributes:
            cmd -- WnCommand to send
        """
        self.transport_bcast.send(cmd.serialize(), 'message')


    def receive_resp(self):
        """Return a list of responses that are sitting in the host's 
        receive queue.  It will empty the queue and return them all the 
        calling method."""
        
        output = []
        
        resp = self.transport.receive()
        
        if resp:
            # Create a list of response object if the list of bytes is a 
            # concatenation of many responses
            done = False
            
            while not done:
                wn_resp = wn_message.WnResp()
                wn_resp.deserialize(resp)
                resp_len = wn_resp.sizeof()

                if resp_len < len(resp):
                    resp = resp[(resp_len):]
                else:
                    done = True
                    
                output.append(wn_resp)
        
        return output


    #-------------------------------------------------------------------------
    # Misc methods for the Node
    #-------------------------------------------------------------------------
    def check_ver(self):
        """Check the WARPNet version of the node against the current WARPNet
        version."""
        (major, minor, revision) = wn_util.wn_ver(output=0)
        
        # Node %d with Serial # %d has version "%d.%d.%d" which does not match WARPNet v%d.%d.%d
        output_str = str("Node {0} ".format(self.node_id) +
                         "with serial # {0} ".format(self.serial_number) +
                         "has version {0:d}.{1:d}.{2:d} ".format(self.wn_ver_major,
                                                                 self.wn_ver_minor,
                                                                 self.wn_ver_revision) +
                         "which does not match WARPNet " +
                         "v{0:d}.{1:d}.{2:d}".format(major, minor, revision))
        
        if (major != self.wn_ver_major) or (minor != self.wn_ver_minor):
            raise ex.WnVersionError(output_str)
        else:
            if (revision != self.wn_ver_revision):
                print("WARNING: " + output_str)


    def __str__(self):
        """Pretty print WnNode object"""
        if not self.serial_number is None:
            print("Node '{0}' with ID {1}:".format(self.name, self.node_id))
            print("    Desc    :  {0}".format(self.description))
            print("    Serial #:  W3-a-{0}".format(self.serial_number))
        else:
            print("Node not initialized.")
        if not self.transport is None:
            print(self.transport)


    def __repr__(self):
        """Return node name and description"""
        return str("W3-a-{0:05d}: ID {1:5d} ({2})".format(self.serial_number,
                                                          self.node_id,
                                                          self.name))

# End Class WnNode



class WnNodeFactory(WnNode):
    """Sub-class of WARPNet node used to help with node configuration 
    and setup.
    
    This class will maintian the dictionary of WARPNet Node Types.  The 
    dictionary contains the 32-bit WARPNet Node Type as a key and the 
    corresponding class name as a value.
    
    To add new WARPNet Node Types, you can sub-class WnNodeConfig and 
    add your own WARPNet Node Types as part of your WnConfig file.
    
    Attributes:
        warpnet_dict -- Dictionary of WARPNet Node Types to class names
    """
    wn_dict             = None


    def __init__(self):
        super(WnNodeFactory, self).__init__()
 
        self.wn_dict = {}

        config = wn_config.WnConfiguration()
        section = config.get_wn_types()
        if section is None:
            print("Necessary informaton is not in wn_config.ini. ",
                  "Please run wn_setup.\n")
        else:
            for wn_node_type in section.keys():
                self.add_node_class(wn_node_type, section[wn_node_type])

    
    def setup(self, node_dict):
        self.set_init_configuration(serial_number=node_dict['serial_number'],
                                    node_id=node_dict['node_id'], 
                                    node_name=node_dict['node_name'], 
                                    ip_address=node_dict['ip_address'], 
                                    unicast_port=node_dict['unicast_port'], 
                                    bcast_port=node_dict['bcast_port'])


    def create_node(self):
        """Based on the WARPNet Node Type, dynamically create and return 
        the correct WARPNet node."""        
        node = None

        # Send broadcast command to initialize WARPNet node
        self.setup_node_network_inf()

        try:
            # Send unicast command to get the WARPNet type
            wn_node_type = self.get_warpnet_node_type()
            
            # Get the node class from the Factory dictionary
            node_class = self.get_node_class(wn_node_type)
        
            if not node_class is None:
                import warpnet
                node = eval(str(node_class + "()"))
                node.set_init_configuration(serial_number=self.serial_number,
                                            node_id=self.node_id,
                                            node_name=self.name,
                                            ip_address=self.transport.ip_address,
                                            unicast_port=self.transport.unicast_port,
                                            bcast_port=self.transport.bcast_port)
            else:
                print("ERROR:  Unknown WARPNet type: {0}".format(wn_node_type))
                print("    Unable to initialize node", 
                      "W3-a-{0:05d}".format(self.serial_number))

        except ex.WnTransportError:
            print("ERROR:  Node W3-a-{0:05d}".format(self.serial_number),
                  "is not responding.")
            print("    Please ensure the node is powered on and is properly",
                  "configured.")

        return node


    def add_node_class(self, wn_node_type, class_name):
        if (wn_node_type in self.wn_dict):
            print("WARNING: Changing definition of {0}".format(wn_node_type))
            
        self.wn_dict[wn_node_type] = class_name
 

    def get_node_class(self, wn_node_type):
        node_type = str(wn_node_type)
        
        if (node_type in self.wn_dict.keys()):
            return self.wn_dict[node_type]
        else:
            return None


    def print_wn_node_types(self):
        print("WARPNet Node Types:")
        for wn_node_type in self.wn_dict.keys():
            print("    {0:08x} = '{1}'".format(int(wn_node_type), 
                                               self.wn_dict[wn_node_type]))


# End Class WnNodeFactory

















