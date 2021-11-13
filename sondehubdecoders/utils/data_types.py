#!/usr/bin/env python
#
#   Data Type Converters
#   (Mainly ones that 'struct' doesn't handle nicely)
#
import struct

def uint24_le(data):
    """
    Decode a 24-bit little-endian unsigned integer.
    """
    if len(data) != 3:
        raise ValueError("Input does not have length of 3 bytes!")
    else:
        return struct.unpack('<I', data+b'\x00')[0]

