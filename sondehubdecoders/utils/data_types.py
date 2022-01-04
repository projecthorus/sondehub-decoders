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

def int24_be(data):
    """
    Decode a 24-bit big-endian unsigned integer.
    """
    if len(data) != 3:
        raise ValueError("Input does not have length of 3 bytes!")
    else:
        return struct.unpack('>i', data+b'\x00')[0]>>8

def lms6_24bit(data):
    """
    Decode the LMS6 7/17-bit format.
    """

    if len(data) != 3:
        raise ValueError("Input does not have length of 3 bytes!")
    else:
        # Interpret data as a uint32 to start with.
        _temp = struct.unpack('>I', b'\x00'+ data)[0]
        _numerator = _temp & 0x1FFFF
        _denominator = _temp >> 17
        try:
            _val = _numerator / _denominator
            return _val
        except:
            return 0