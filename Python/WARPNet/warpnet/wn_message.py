# -*- coding: utf-8 -*-
"""
------------------------------------------------------------------------------
WARPNet Messages
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

This module provides class definitions for all WARPNet over-the-wire 
messages.

Functions (see below for more information):
    WnTransportHeader() -- WARPNet Transport Header
    WnCmd() -- Base class for WARPNet Commands the require WnResp responses
    WnBufferCmd() -- Base class for WARPNet Commands that require WnBuffer responses
    WnResp() -- WARPNet responses (single packet)
    WnBuffer() -- WARPNet responses (multiple packets)

Integer constants:
    PKTTYPE_TRIGGER, PKTTYPE_HTON_MSG, PKTTYPE_NTOH_MSG, PKTTYPE_NTOH_MSG_ASYNC
      - Transport Header Packet Types

"""

import struct

from . import wn_transport

__all__ = ['WnTransportHeader', 'WnCmd', 'WnBufferCmd', 'WnResp', 'WnBuffer']

# Transport Header defines
PKTTYPE_TRIGGER              = 0
PKTTYPE_HTON_MSG             = 1
PKTTYPE_NTOH_MSG             = 2
PKTTYPE_NTOH_MSG_ASYNC       = 3


class WnMessage(object):
    """Base class for WARPNet messages."""
    def serialize(self,): raise NotImplementedError
    def deserialize(self,): raise NotImplementedError
    def sizeof(self,): raise NotImplementedError

# End Class WnMessage


class WnTransportHeader(WnMessage):
    """Class for WARPNet transport header.
    
    Attributes:
        dest_id -- (uint16) Destination ID of the message
        src_id -- (uint16) Source ID of the message
        reserved -- (uint8) Reserved field in the header
        pkt_type -- (uint8) Packet Type
        length -- (uint16) Length of the payload in bytes
        seq_num -- (uint16) Sequence number of the message
        flags -- (uint16) Flags of the message
    """
    
    def __init__(self, dest_id=0, src_id=0, reserved=0, 
                 pkt_type=PKTTYPE_HTON_MSG, length=0, seq_num=0, flags=0):
        self.dest_id = dest_id
        self.src_id = src_id
        self.reserved = reserved
        self.pkt_type = pkt_type
        self.length = length
        self.seq_num = seq_num
        self.flags = flags

    def serialize(self):
        """Return a bytes object of a packed transport header."""
        return struct.pack('!2H 2B 3H',
                           self.dest_id, self.src_id,
                           self.reserved, self.pkt_type, self.length, 
                           self.seq_num, self.flags)

    def deserialize(self, buffer):
        """Not used for Transport headers"""
        pass
    
    def sizeof(self):
        """Return the size of the transport header."""
        return struct.calcsize('!2H 2B 3H')
    
    def increment(self, step=1):
        """Increment the sequence number of the header by a given step."""
        self.seq_num = (self.seq_num + step) % 0xFFFF
        
    def set_type(self, pkt_type):
        """Sets the pkt_type field of the transport header.
        
        Attributes:
            pkt_type -- String of the packet type:
                "trigger" = PKTTYPE_TRIGGER
                "message" = PKTTYPE_HTON_MSG
        """
        pkt_type = pkt_type.lower()

        if   (pkt_type == 'trigger'):
            self.pkt_type = PKTTYPE_TRIGGER
        elif (pkt_type == 'message'):
            self.pkt_type = PKTTYPE_HTON_MSG
        else:
            print("Uknown packet type: {}".format(pkt_type))

    def set_length(self, length):
        """Sets the length field of the transport header."""
        self.length = length
        
    def set_src_id(self, src_id):
        """Sets the source id field of the transport header."""
        self.src_id = src_id
        
    def set_dest_id(self, dest_id):
        """Sets the destination id field of the transport header."""
        self.dest_id = dest_id
        
    def response_required(self):
        """Sets bit 0 of the flags since a response is required."""
        self.flags = self.flags | 0x1
            
    def response_not_required(self):
        """Clears bit 0 of the flags since a response is not required."""
        self.flags = self.flags & 0xFFFE

    def reset(self):
        """Reset the sequence number of the transport header."""
        self.seq_num = 1
    
    def is_reply(self, input_data):
        """Checks input_data to see if it is a valid reply to the last
        outgoing packet.
        
        Checks:
            input_data.dest_id == self.src_id
            input_data.src_id  == self.dest_id
            input_data.seq_num == self.seq_num
            
        Raises a TypeError excpetion if input data is not the correct size.
        """
        if len(input_data) == self.sizeof():
            dataTuple = struct.unpack('!2H 2B 3H', input_data[0:12])
            
            if ((self.dest_id != dataTuple[1]) or
                    (self.src_id  != dataTuple[0]) or
                    (self.seq_num != dataTuple[5])):
                print("WARNING:  transport header mismatch:",
                      "[{0:d} {1:d}]".format(self.dest_id, dataTuple[1]),
                      "[{0:d} {1:d}]".format(self.src_id, dataTuple[0]),
                      "[{0:d} {1:d}]".format(self.seq_num, dataTuple[5]))
                return False
            else:
                return True
        else:
            raise TypeError(str("WnTransportHeader:  length of header " +
                                "did not match size of transport header"))

# End Class WnTransportHeader


class WnCmdMessage(WnMessage):
    """Base class for WARPNet command / response messages.
    
    Attributes:
        command -- (uint32) WARPNet command / response
        length -- (uint16) Length of the cmd / resp args in bytes
        num_args -- (uint16) Number of uint32 arguments
        args -- (list of uint32) Arguments of the command / reponse
    """
    
    def __init__(self, command=0, length=0, num_args=0, args=None):
        self.command = command
        self.length = length
        self.num_args = num_args
        self.args = args or []

    def serialize(self):
        """Return a bytes object of a packed command / response."""
        # self.print()              # For Debug
        
        if self.num_args == 0:
            return struct.pack('!I 2H',
                               self.command,
                               self.length,
                               self.num_args)
        else:
            return struct.pack('!I 2H %dI' % self.num_args,
                               self.command,
                               self.length,
                               self.num_args,
                               *self.args)

    def deserialize(self, buffer):
        """Populate the fields of a WnCmdResp from a buffer."""
        try:
            dataTuple = struct.unpack('!I 2H', buffer[0:8])
            self.command = dataTuple[0]
            self.length = dataTuple[1]
            self.num_args = dataTuple[2]
            self.args = list(struct.unpack_from('!%dI' % self.num_args, 
                                                buffer, offset=8))
        except struct.error as err:
            # Reset Cmd/Resp.  We want predictable behavior on error
            self.reset()
            print("Error unpacking WARPNet cmd/resp: {0}".format(err))
    
    def sizeof(self):
        """Return the size of the cmd/resp including all attributes."""
        if self.num_args == 0:
            return struct.calcsize('!I 2H')
        else:        
            return struct.calcsize('!I 2H %dI' % self.num_args)

    def reset(self):
        """Reset the WnCmdResp object to a default state (all zeros)"""
        self.command = 0
        self.length = 0
        self.num_args = 0
        self.args = []
        
# End Class WnCmdResp


class WnCmd(WnCmdMessage):
    """Base Class for WARPNet commands.

    Attributes:
        resp_type -- Response type of the command.  See WARPNet transport
            for defined response types.  By default, a WnCmd will require
            a WnResp.

    See documentation of WnCmdResp for additional attributes
    """
    resp_type = None
    
    def __init__(self, command=0, length=0, num_args=0, 
                 args=None, resp_type=None):
        super(WnCmd, self).__init__(command, length, num_args, args)
        self.resp_type = resp_type or wn_transport.TRANSPORT_WN_RESP
    
    def set_args(self, *args):
        """Set the command arguments."""
        self.args = args
        self.num_args = len(args)
        self.length = self.num_args * 4
    
    def add_args(self, *args):
        """Append arguments to current command argument list."""
        self.args.append(*args)
        self.num_args += len(args)
        self.length += len(args) * 4

    def get_resp_type(self):
        return self.resp_type

    def process_resp(self, resp):
        """Process the response of the WARPNet command."""
        raise NotImplementedError

    def __str__(self):
        """Pretty print the WnCommand"""
        print("WARPNet Command [{0:d}] ({1:d} bytes): ".format(self.command, 
                                                               self.length))
        print("    Args [0:{0:d}]  : ".format(self.num_args))
        for i in range(len(self.args)):
            print("        0x%08x " % self.args[i])
        print("")

# End Class WnCommand


class WnBufferCmd(WnCmdMessage):
    """Base Class for WARPNet Buffer commands.

    Arguments:
        buffer_id -- (uint32) ID of buffer for this message.
        flags -- (uint32) Flags associated with this message.
        start_byte -- (uint32) Starting address of the buffer for this message.
        size -- (uint32) Size of the buffer in bytes

    Attributes:
        resp_type -- Response type of the command.  See WARPNet transport
            for defined response types.  By default, a WnCmd will require
            a WnResp.

    See documentation of WnCmdResp for additional attributes
    """
    resp_type  = None
    buffer_id  = None
    flags      = None
    start_byte = None
    size       = None
    
    def __init__(self, command=0, buffer_id=0, flags=0, start_byte=0, size=0):
        super(WnBufferCmd, self).__init__(command=command,
                                          length=16,
                                          num_args=4,
                                          args=[buffer_id, flags, start_byte, size])

        self.resp_type = wn_transport.TRANSPORT_WN_BUFFER
        self.buffer_id = buffer_id
        self.flags = flags
        self.start_byte = start_byte
        self.size = size
    
    def get_resp_type(self): return self.resp_type        
    def get_buffer_size(self): return self.size    
    def get_buffer_id(self): return self.buffer_id
    def get_buffer_flags(self): return self.flags

    def process_resp(self, resp):
        """Process the response of the WARPNet command."""
        raise NotImplementedError

    def __str__(self):
        """Pretty print the WnCommand"""
        print("WARPNet Buffer Command [{0:d}]".format(self.command),
              "({0:d} bytes): ".format(self.length))
        print("    Args [0:{0:d}]  : ".format(self.num_args))
        for i in range(len(self.args)):
            print("        0x%08x " % self.args[i])
        print("")

# End Class WnCommand


class WnResp(WnCmdMessage):
    """Class for WARPNet responses.
    
    See documentation of WnCmdResp for attributes
    """
    
    def get_args(self):
        """Return the response arguments."""
        return self.args

    def __str__(self):
        """Pretty print the WnResponse"""
        print("WARPNet Response [{0:d}] ({1:d} bytes): ".format(self.command, 
                                                                self.length))
        print("    Args [0:{0:d}]  : ".format(self.num_args))
        for i in range(len(self.args)):
            print("        0x%08x " % self.args[i])
        print("")

# End Class WnResp


class WnBuffer(WnMessage):
    """Class for WARPNet buffer for transferring generic information.
    
    This object provides a container to transfer information that will be
    decoded by higher level functions.

    Attributes:
        complete -- Flag to indicate if buffer contains all of the bytes
                      indicated by the size parameter
        num_bytes -- Number of bytes currently contained within the buffer

    Wire Data Format:
        command -- (uint32) WARPNet command / response
        length -- (uint16) Length of the cmd / resp args in bytes
        num_args -- (uint16) Number of uint32 arguments
        buffer_id -- (uint32) ID of buffer for this message.
        flags -- (uint32) Flags associated with this message.
        size -- (uint32) Size of the buffer in bytes
        buffer -- (list of uint8) Content of the buffer 
    """
    complete    = None
    num_bytes   = None
    buffer_id   = None
    flags       = None
    size        = None
    buffer      = None


    def __init__(self, buffer_id=0, flags=0, size=0, buffer=None):
        self.buffer_id = buffer_id
        self.flags = flags
        self.size = size

        if buffer is None:
            # Create an empty buffer of the specified size
            self.complete = False
            self.num_bytes = 0
            self.buffer = bytearray(self.size)
        else:
            self._add_buffer_data(0, buffer)

    def serialize(self, command=0, start_byte=0):
        """Return a bytes object of a packed buffer."""
        return struct.pack('!I 2H 4I %ds' % self.size, 
                           command, 16, 4,  # length = Num_args * 4 bytes / arg; Num_args = 4; 
                           self.buffer_id, self.flags, start_byte,
                           self.size, self.buffer)

    def deserialize(self, raw_data):
        """Populate the fields of a WnBuffer with a message raw_data."""
        try:
            # Interpret the raw_data
            dataTuple = struct.unpack('!I 2H 4I', raw_data[0:24])
            self.buffer_id = dataTuple[3]
            self.flags = dataTuple[4]
            start_byte = dataTuple[5]
            size = dataTuple[6]
            buffer = struct.unpack_from('!%dB' % size, raw_data, offset=24)
            
            self._update_size(start_byte + size)
            self._add_buffer_data(start_byte, buffer)
            self._set_buffer_complete()            
        except struct.error as err:
            # Ignore the data.  We want predictable behavior on error
            print("Error unpacking WARPNet buffer: {0}\n".format(err),
                  "    Ignorning data.")

    def add_data_to_buffer(self, raw_data):
        """Add the raw data (with the format of a WnBuffer) to the current
        WnBuffer.
        
        Note:  This will check to make sure that data is for the given buffer
        as well as place it in the appropriate place indicated by the
        start_byte.        
        """
        try:
            # Interpret the raw_data
            dataTuple = struct.unpack('!I 2H 4I', raw_data[0:24])
            buffer_id = dataTuple[3]
            flags = dataTuple[4]
            start_byte = dataTuple[5]
            size = dataTuple[6]
            buffer = struct.unpack_from('!%dB' % size, raw_data, offset=24)
        except struct.error as err:
            # Ignore the data.  We want predictable behavior on error
            print("Error unpacking WARPNet buffer: {0}\n".format(err),
                  "    Ignorning data.")

        if (buffer_id == self.buffer_id):
            self._update_size(start_byte + size)
            self._add_buffer_data(start_byte, buffer)
            self._set_buffer_complete()            
 
            self.set_flags(flags)
        else:
            print("Data not intended for given WARPNet buffer.  Ignoring.")

    def append(self, wn_buffer):
        """Append the contents of the provided WnBuffer to the current
        WnBuffer."""
        curr_size = self.size
        new_size = curr_size + wn_buffer.get_buffer_size()
        
        self._update_size(new_size, force=1)
        self._add_buffer_data(curr_size, wn_buffer.get_bytes())
        self._set_buffer_complete()

    def sizeof(self):
        """Return the size of the buffer including all attributes."""
        return struct.calcsize('!4I %dB' % self.size)

    def get_buffer_id(self): return self.buffer_id
    def get_buffer_size(self): return self.size
    def get_flags(self): return self.flags

    def set_flags(self, flags):
        """Set the bits in the flags field based on the value provided."""
        self.flags = self.flags | flags

    def clear_flags(self,flags):
        """Clear the bits in the flags field based on the value provided."""
        self.flags = self.flags & ~flags

    def set_bytes(self, buffer):
        """Set the message bytes of the buffer."""
        self._update_size(len(buffer), force=1)
        self._add_buffer_data(0, buffer)
        self._set_buffer_complete()

    def get_bytes(self):
        """Return the message bytes of the buffer."""
        return self.buffer

    def is_buffer_complete(self):
        """Return if the buffer is complete."""
        return self.complete

    def reset(self):
        """Reset the WnBuffer object to a default state (all zeros)"""
        self.buffer_id = 0
        self.flags = 0
        self.size = 0
        self.buffer = bytearray(self.size)

    def __str__(self):
        """Pretty print the WnBuffer"""
        print("WARPNet Buffer [{0:d}] ({1:d} bytes): ".format(self.buffer_id, 
                                                              self.size))
        print("    Flags    : 0x{0:08x}".format(self.flags))
        print("    Num bytes: {0:d}".format(self.num_bytes))
        print("    Complete : {0}".format(self.complete))
        print("    Data     : ")
        for i in range(len(self.buffer)):
            if (i % 16) == 0:
                print("\n        %02x " % self.buffer[i])
            else:
                print("%02x " % self.buffer[i])
        print("")


    #-------------------------------------------------------------------------
    # Internal helper methods
    #-------------------------------------------------------------------------
    def _update_size(self, size, force=0):
        if ((self.size == 0) or (force == 1)):
            self.size = size

    def _add_buffer_data(self, start_byte, buffer):
        """Internal method to add data to the buffer
        
        NOTE:  If the provided buffer data is greater than specified buffer
            size, then the data will be truncated.
        """
        buffer_size = len(buffer)
        num_bytes = self._num_bytes_to_add(buffer_size)        
        end_byte = num_bytes + start_byte

        if (num_bytes > 0):
            self.buffer[start_byte:end_byte] = buffer[:num_bytes]
            
        self._set_buffer_complete()

    def _num_bytes_to_add(self, buffer_size):
        """Internal function to determine how many bytes we can add to the 
        buffer.
        
        NOTE:  If the provided buffer data is greater than specified buffer
            size, then the data will be truncated.
        """
        num_bytes = buffer_size
        end_byte = self.num_bytes + buffer_size
        
        if (end_byte <= self.size):
            self.num_bytes = end_byte
        else:
            num_bytes = self.size - self.num_bytes
            self.num_bytes = self.size

        return num_bytes

    def _set_buffer_complete(self):
        """Internal method to set the complete flag on the buffer."""
        if   (self.num_bytes == self.size):
            self.complete = True
        elif (self.num_bytes < self.size):
            self.complete = False
        else:
            print("WARNING: WnBuffer out of sync.  Should never reach here.")
        

# End Class WnBuffer