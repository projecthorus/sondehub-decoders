#!/usr/bin/env python
#
#   RS41 Frame Post-Processing
#
#   Accepts a RS41 data frame as bytes, and extract its components.
#
#   This code makes use of information from the following resources:
#   - https://github.com/bazjo/RS41_Decoding
#
import logging
import struct
from ..utils.checksums import check_packet_crc
from ..utils.data_types import *
from ..utils.gnss_helpers import ecef_to_wgs84


def rs41_process_gps_position(block, **args):
    """ 
    Post-Process the GPS Position block from a RS41 Frame
    """

    output = block.copy()

    # Convert ECEF coordinates (in cm) to lat/lon/alt
    (lat, lon, alt) = ecef_to_wgs84(
        output['ecef_pos_x_cm']/100.0,
        output['ecef_pos_y_cm']/100.0,
        output['ecef_pos_z_cm']/100.0
        )
    
    output['latitude'] = lat
    output['longitude'] = lon
    output['altitude'] = alt

    # Convert ECEF velocities into horizontal speed and ascent rate (both in m/s)

    return output