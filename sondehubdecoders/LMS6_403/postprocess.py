#!/usr/bin/env python
#
#   LMS6_403 Frame Post-Processing
#
import logging
import math
import struct


# LMS6_403 Calibration data Information
#
# 28 calibration values are sent, with 4 per frame, at byte offsets 212 through 220, as big-endian uint16's.
# Cal values repeat every 7 frames.
# As there is no calibration 'subframe' number in the telemetry like on the RS41, we make use of the
# frame count to assign each calibration value a number.
#
# (frame_count%7)==0 -> Cal 0 through Cal 3
# (frame_count%7)==1 -> Cal 4 through Cal 7
# ... etc
# (frame_count%7)==6 -> Cal 24 through Cal 27
#
# An example set of calibration values:
# (0-3) 37292, 14726, 1697, 13846, 
# (4-7) 28307, 13209, 53398, 8226,
# (8-11) 9984, 21534, 1729, 8371,
# (12-15) 9966, 14726, 1697, 13846,
# (16-19) 28305, 13209, 53398, 190,
# (20-23) 6, 1000, 30, 0,
# (24-27) 27, 0, 0, 20727
#
# The meaning of each calibration parameter is still uncertain at this point.
# Values that match up with values written on the sonde box:
# Cal 7 = Temp Sensor Thermistor Lock-In (e.g. 8226) - possibly at 30 degrees C
# Cal 8 = Temp Sensor Thermistor TRC * 10000  (e.g. 9984 = 0.9984)

# A few guesses:
# Cal 11 = Humidity Temperature Sensor Thermistor Lock-In Value
# Cal 12 = Humidity Temperature Sensor Thermistor TRC * 10000
# Cal 1 = Temp Sensor R0 ???
# Cal 2 = Temp Sensor B ???


# Indexes to calibration values we would want to use.
LMS6_TEMP_R0_CAL_IDX = 1
LMS6_TEMP_B_CAL_IDX = 2
LMS6_TEMP_LOCKIN_IDX = 7
LMS6_TEMP_TRC_IDX = 8


def lms6_403_calculate_temperature(frame, cal_data):

    # The following calculation is not particularly accurate at higher temperatures,
    # and is really only good to  +/- 5 degrees C across the range.

    R0 = cal_data[LMS6_TEMP_R0_CAL_IDX]
    T0 = 273.15
    B = cal_data[LMS6_TEMP_B_CAL_IDX]
    C = 0

    temp_raw = frame['sensor_chan3']

    temp = -273.15 + 1 / (1.0/T0 + 1.0/B * math.log(temp_raw / R0)) + C

    return temp


def lms6_403_process_measurements(frame, cal_data = None):

    output = frame.copy()


    # No cal data available, bomb out now.
    if cal_data is None:
        return output
    
    # TODO - Check for particular calibration values.
    if None in cal_data:
        return output
    
    output['temperature'] = lms6_403_calculate_temperature(frame, cal_data)

    return output