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
from ..utils.gnss_helpers import ecef_to_wgs84, ecef_velocity, gps_weeksecondstoutc


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

    # Convert ECEF velocities into horizontal speed and ascent rate (both in m/s)

    (ground_speed, ascent_rate, wind_u, wind_v, heading) = ecef_velocity(lat, lon, 
        output['ecef_vel_x_cms']/100.0 , 
        output['ecef_vel_y_cms']/100.0, 
        output['ecef_vel_z_cms']/100.0
        )
    
    # Add to the output dictionary
    output['latitude'] = lat
    output['longitude'] = lon
    output['altitude'] = alt
    output['ground_speed'] = ground_speed
    output['ascent_rate'] = ascent_rate
    output['wind_u'] = wind_u
    output['wind_v'] = wind_v
    output['heading'] = heading

    return output

def rs41_process_gps_info(block, **args):
    """ 
    Post-Process the GPS Information block from a RS41 Frame
    """

    output = block.copy()

    # Extract the timestamp information
    # The uBlox chipset on the RS41 provides an 'unwrapped' GPS week number.
    _timestamp = gps_weeksecondstoutc(output['week'], output['iTOW'])

    output['timestamp_dt'] = _timestamp
    output['timestamp_str'] = _timestamp.isoformat()

    # Extract GPS SV Quality Information
    _sv_quality = {}
    for _idx in range(len(output['sv_quality'])//2):
        _sv = output['sv_quality'][_idx*2]
        _qual = output['sv_quality'][_idx*2+1]

        _sv_quality[_sv] = _qual

    output['sv_quality'] = _sv_quality

    return output


def rs41_temp_calc(rf1, rf2, f, f1, f2, co, calT):
    """ Calculate a temperature based on provided measurement and calibration data """

        # static float get_T(gpx_t *gpx, ui32_t f, ui32_t f1, ui32_t f2, float *ptu_co, float *ptu_calT) {
        #     float *p = ptu_co;
        #     float *c = ptu_calT;
        #     float  g = (float)(f2-f1)/(gpx->ptu_Rf2-gpx->ptu_Rf1),       // gain
        #         Rb = (f1*gpx->ptu_Rf2-f2*gpx->ptu_Rf1)/(float)(f2-f1), // ofs
        #         Rc = f/g - Rb,
        #         R = Rc * c[0],
        #         T = (p[0] + p[1]*R + p[2]*R*R + c[1])*(1.0 + c[2]);
        #     return T; // [Celsius]
        # }
    
    p = co
    c = calT

    g = (f2 - f1)/(rf2 - rf1)
    Rb = (f1*rf2 - f2*rf1)/(f2-f1)
    Rc = f/g - Rb
    R = Rc * c[0]
    T = (p[0] + p[1]*R + p[2]*R*R + c[1])*(1.0 + c[2])

    return T

def rs41_process_measurements(block, subframe = None):

    output = block.copy()

    # No subframe data available, bomb out now.
    if subframe is None:
        output['measurements_valid'] = False
        return output
    
    if subframe.temperature_cal_available():
        #logging.debug(str(subframe.subframe_fields))
        # Temperature calibration data available!
        _rf1 = subframe.subframe_fields['rf1']
        _rf2 = subframe.subframe_fields['rf2']
        _co = subframe.subframe_fields['tempmeas_co1']
        _calT = subframe.subframe_fields['tempmeas_calT1']

        try:
            _temp = rs41_temp_calc(_rf1, _rf2, block['temp_meas_main'], block['temp_meas_ref1'], block['temp_meas_ref2'], _co, _calT)
            output['temperature'] = _temp
        except Exception as e:
            logging.exception("Error in temperature calculation: ", exc_info=e)
            #logging.info("")

    return output
