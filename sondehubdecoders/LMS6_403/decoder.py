#!/usr/bin/env python
#
#   LMS6_403 Frame Decoder
#
#   This code makes use of information from the following resources:
#   - https://github.com/rs1729/RS/
#
import logging
import struct
from ..utils.checksums import check_packet_crc
from ..utils.data_types import *
#from .postprocess import *

# 24 54 00 00 00 7c 4a 9e 0b 19 1c 54 46 02 ff e6 e1 e2 1d bb b4 b3 c0 1f ec 8f 00 b2 51 b4 00 9e 26 00 25 30 00 14 18 00 38 0d 29 1f 84 2c a8 ac 1c f9 6f 99 0f 28 1f 7a ef 59 ea 1c f5 33 d1 12 2a 1f 7b ca 3c dc 1c f0 ae 04 1d 29 1f 8b 96 0f 81 1c fe 13 91 17 2b 1f 82 75 27 61 1c ee fa 7c 18 20 1f 91 fc 8f 68 1c e9 bf 50 05 25 1f 8c e3 f2 5f 1c fb 58 2b 0a 28 1f 92 9a 06 63 1c ec 93 7a 1b 24 1f 96 70 ff fa 1c eb a3 00 10 00 84 00 00 00 00 00 00 00 00 8a 2a 80 00 00 00 00 00 00 00 00 06 00 80 00 00 00 00 00 00 00 00 03 c1 72 00 00 00 03 3e 1b 09 dd 7f 00 00 00 00 00 00 1b e4 73 0f c1 a0 03 c1 95 03 c1 8a 03 c1 96 03 c1 94 00 00 00 00 1b 00 00 00 00 6f 9a 07 e4 3e  [OK]


# Frame Header - common to all frames.
LMS6_403_FRAME_HEADER = b"\x24\x54\x00\x00"


# Expected block lengths
LMS6_403_FRAME_HEADER_LEN = 4


# Positions for some data
LMS6_403_HEADER_POS = 0

# Block Decoding Information
LMS6_403_DECODERS = {
    "block_name": "Overall",
    "expected_len": 40,
    "struct": ">4sIHI4siii3s3s3sH132s3s3s3s3s3s3s3s3s3s3s3s3s",
    "fields": [
        "header",
        "serial",
        "frame_count",
        "iTOW",
        "unknown1",
        "latitude",
        "longitude",
        "altitude",
        "east_west_vel_mms",
        "north_south_vel_mms",
        "up_down_vel_mms",
        "unknown2",
        "gps_status",
        "sensor_chan1",
        "sensor_chan2",
        "sensor_chan3",
        "sensor_chan4",
        "sensor_chan5",
        "sensor_chan6",
        "sensor_chan7",
        "sensor_chan8",
        "sensor_chan9",
        "sensor_chan10",
        "sensor_chan11",
        "sensor_chan12"
    ],
    "field_decoders": {
        "altitude": lambda alt: alt/1000,
        "up_down_vel_mms": lambda val: int24_be(val)/1000,
        "east_west_vel_mms": lambda val: int24_be(val)/1000,
        "north_south_vel_mms": lambda val: int24_be(val)/1000,
        "latitude": lambda val: (val/(2**32-1))/360.0,
        "longitude": lambda val: (val/(2**32-1))/360.0,
        "sensor_chan1": lms6_24bit,
        "sensor_chan2": lms6_24bit,
        "sensor_chan3": lms6_24bit,
        "sensor_chan4": lms6_24bit,
        "sensor_chan5": lms6_24bit,
        "sensor_chan6": lms6_24bit,
        "sensor_chan7": lms6_24bit,
        "sensor_chan8": lms6_24bit,
        "sensor_chan9": lms6_24bit,
        "sensor_chan10": lms6_24bit,
        "sensor_chan11": lms6_24bit,
        "sensor_chan12": lms6_24bit,
    },
    "block_post_process": None
}

LMS6_403_FRAME_LEN = struct.calcsize(LMS6_403_DECODERS['struct'])
LMS6_403_DECODERS['expected_len'] = LMS6_403_FRAME_LEN


def decode(frame, ignore_crc=False, subframe=None):
    """
    Attempt to decode a LMS6_403 frame, provided as bytes, after de-scrambling has been performed.

    Args:
    frame (bytes): Data frame provided as bytes
    ignore_crc (bool): If set, ignore any CRC failures
    subframe (dict): Optional subframe Object, for use in processing measurement data.

    """

    # Basic length check.
    if len(frame) < LMS6_403_FRAME_LEN:
        raise ValueError(f"Supplied LMS6_403 frame too small.")

    # Check for header.
    if frame[:LMS6_403_FRAME_HEADER_LEN] != LMS6_403_FRAME_HEADER:
        raise ValueError(f"Frame Header Mismatch")

    # Now we can start breaking apart the frame.
    output = {}

    # TODO - CRC Check
    _crc_ok = True

    if _crc_ok:

        try:
            if len(frame) > LMS6_403_DECODERS["expected_len"]:
                # Clip frame
                frame = frame[:LMS6_403_DECODERS["expected_len"]]

            # Decode fields
            _block_field_data = struct.unpack(
                LMS6_403_DECODERS["struct"], frame
            )
            _block_dict = dict(
                zip(
                    LMS6_403_DECODERS["fields"],
                    _block_field_data,
                )
            )

            # Post-process any individual fields that require it
            # These are usually simple unit or type conversions.
            for _field in _block_dict:
                if (
                    _field
                    in LMS6_403_DECODERS["field_decoders"]
                ):
                    _temp = LMS6_403_DECODERS[
                        "field_decoders"
                    ][_field](_block_dict[_field])

                    if type(_temp) == dict:
                        # If the field processor returned a dictionary, add those keys into our block dict.
                        _block_dict.update(_temp)
                    else:
                        # Otherwise, we got a single value.
                        _block_dict[_field] = _temp

            # Apply any further post-processing to the block before storing it into the output dictionary
            # This may include converting coordinates to a more user-friendly format, or calculating
            # sensor values.

            # TODO

            output = _block_dict

        except Exception as e:
            logging.error(f"Error extracting frame data: {str(e)}")
            return None

    else:
        logging.error("Block CRC failure")



    # Pull out the commonly required telemetry fields, for use in SondeHub
    output['common'] = {
        'type': 'LMS6-403'
    }

    return output


def descramble(frame):
    """
    De-Scramble a RS41 data frame by bitwise-XORing it with the known XOR scramble mask
    """
    # TODO
    return frame


def to_autorx_log(frame):
    """
    Convert a frame dictionary into a line matching the auto_rx log format.
    """
    # timestamp,serial,frame,lat,lon,alt,vel_v,vel_h,heading,temp,humidity,pressure,type,freq_mhz,snr,f_error_hz,sats,batt_v,burst_timer,aux_data
    # 2021-11-12T22:53:38.000Z,S4610487,313,-34.95245,138.52045,10.5,-0.3,0.3,180.9,-273.0,-1.0,-1.0,RS41,401.500,13.5,937,6,2.9,-1,-1
    _line = ""

    # Timestamp
    _line += f"{frame['blocks']['GPS Fix Information']['timestamp_str']},"

    # Serial
    _line += frame['blocks']['Status']['serial'] + ","

    # Frame Number
    _line += f"{frame['blocks']['Status']['frame_count']},"

    # Latitude
    _line += f"{frame['blocks']['GPS Position']['latitude']:0.5f},"

    # Longitude
    _line += f"{frame['blocks']['GPS Position']['longitude']:0.5f},"

    # Altitude
    _line += f"{frame['blocks']['GPS Position']['altitude']:0.1f},"

    # Ascent Rate
    _line += f"{frame['blocks']['GPS Position']['ascent_rate']:0.1f},"

    # Ground Speed
    _line += f"{frame['blocks']['GPS Position']['ground_speed']:0.1f},"

    # Heading
    _line += f"{frame['blocks']['GPS Position']['heading']:0.1f},"

    # Temp, Humidity, Pressure
    if 'temperature' in frame['blocks']['Measurements']:
        _line += f"{frame['blocks']['Measurements']['temperature']:.1f},"
    else:
        _line += "-273.0,"
    
    _line += "humidity,pressure,"

    # The rest TODO...


    return _line



if __name__ == "__main__":
    import argparse
    import codecs
    import pprint

    # Command line arguments.
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "hexstring", help="LMS6_403 Frame in Hexadecimal",
    )
    parser.add_argument(
        "-v", "--verbose", help="Enable debug output.", action="store_true"
    )
    args = parser.parse_args()

    if args.verbose:
        _log_level = logging.DEBUG
    else:
        _log_level = logging.INFO

    # Setup Logging
    logging.basicConfig(
        format="%(asctime)s %(levelname)s: %(message)s", level=_log_level
    )

    _hex = codecs.decode(args.hexstring, "hex")

    pprint.pprint(decode(_hex))
