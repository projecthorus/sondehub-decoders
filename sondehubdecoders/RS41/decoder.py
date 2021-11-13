#!/usr/bin/env python
#
#   RS41 Frame Decoder
#
#   This code makes use of information from the following resources:
#   - https://github.com/bazjo/RS41_Decoding
#   - https://github.com/rs1729/RS/
#
import logging
import struct
from ..utils.checksums import check_packet_crc
from ..utils.data_types import *
from .postprocess import *

# Frame Header - common to all frames.
RS41_FRAME_HEADER = b"\x86\x35\xf4\x40\x93\xdf\x1a\x60"

# RS41 XOR Scrambling Sequence. Not currently using this
RS41_XOR_SCRAMBLE = b'\x96\x83>Q\xb1I\x08\x982\x05Y\x0e\xf9D\xc6&!`\xc2\xeay]m\xa1TiG\x0c\xdc\xe8\\\xf1\xf7v\x82\x7f\x07\x99\xa2,\x93|0c\xf5\x10.a\xd0\xbc\xb4\xb6\x06\xaa\xf4#xn;\xae\xbf{L\xc1'

# Frame Types
RS41_FRAME_TYPE_REGULAR = 0x0F
RS41_FRAME_TYPE_EXTENDED = 0xF0

# Block Types
RS41_BLOCK_STATUS = 0x79
RS41_BLOCK_MEAS = 0x7A
RS41_BLOCK_GPSINFO = 0x7C
RS41_BLOCK_GPSRAW = 0x7D
RS41_BLOCK_GPSPOS = 0x7B
RS41_BLOCK_XDATA = 0x7E
RS41_BLOCK_EMPTY = 0x76
RS41_BLOCK_ENCRYPTED = 0x80

# Expected block lengths
RS41_FRAME_HEADER_LEN = 8
RS41_ECC_LEN = 48
RS41_FRAME_TYPE_LEN = 1

# Positions for some data
RS41_HEADER_POS = 0
RS41_ECC_POS = RS41_FRAME_HEADER_LEN
RS41_FRAME_TYPE_POS = RS41_FRAME_HEADER_LEN + RS41_ECC_LEN
RS41_BLOCK_START_POS = RS41_FRAME_HEADER_LEN + RS41_ECC_LEN + RS41_FRAME_TYPE_LEN

# Block Decoding Information
RS41_BLOCK_DECODERS = {
    RS41_BLOCK_STATUS: {
        "block_name": "Status",
        "expected_len": 40,
        "struct": "<H8sBHHBBHHBBB16s",
        "fields": [
            "frame_count",
            "serial",
            "battery",
            "unknown1",
            "bitfield1",
            "unknown2",
            "ref_area_temp",
            "bitfield2",
            "humidity_sensor_heating_pwm",
            "tx_power",
            "max_subframe",
            "subframe_count",
            "subframe_data",
        ],
        "field_decoders": {
            "serial": lambda s: s.decode(),
            "battery": lambda v_in: v_in / 10.0,
        },
        "block_post_process": None,
    },
    RS41_BLOCK_MEAS: {
        "block_name": "Measurements",
        "expected_len": 42,
        # Note - As struct does not have a type for 24-bit uints, we use a helper function to decode these fields.
        "struct": "<3s3s3s3s3s3s3s3s3s3s3s3sHhH",
        "fields": [
            "temp_meas_main",
            "temp_meas_ref1",
            "temp_meas_ref2",
            "humidity_main",
            "humidity_ref1",
            "humidity_ref2",
            "humidity_temp_main",
            "humidity_temp_ref1",
            "humidity_temp_ref2",
            "pressure_main",
            "pressure_ref1",
            "pressure_ref1",
            "unknown",
            "pressure_temp",
            "unknown2",
        ],
        "field_decoders": {
            "temp_meas_main": uint24_le,
            "temp_meas_ref1": uint24_le,
            "temp_meas_ref2": uint24_le,
            "humidity_main": uint24_le,
            "humidity_ref1": uint24_le,
            "humidity_ref2": uint24_le,
            "humidity_temp_main": uint24_le,
            "humidity_temp_ref1": uint24_le,
            "humidity_temp_ref2": uint24_le,
            "pressure_main": uint24_le,
            "pressure_ref1": uint24_le,
            "pressure_ref2": uint24_le,
            "pressure_temp": lambda t_in: t_in / 100.0,
        },
        "block_post_process": None,
    },
    RS41_BLOCK_GPSPOS: {
        "block_name": "GPS Position",
        "expected_len": 21,
        "struct": "<iiihhhBBB",
        "fields": [
            'ecef_pos_x_cm',
            'ecef_pos_y_cm',
            'ecef_pos_z_cm',
            'ecef_vel_x_cms',
            'ecef_vel_y_cms',
            'ecef_vel_z_cms',
            'numSV',
            'sAcc',
            'pDOP'
            ],
        "field_decoders": {
            "sAcc": lambda sAcc: sAcc*10.0,
            "pDOP": lambda pDOP: pDOP/10.0
        },
        "block_post_process": rs41_process_gps_position,
    },
}


def decode(frame, ignore_crc=False, subframe=None):
    """
    Attempt to decode a RS41 frame, provided as bytes, after de-scrambling has been performed.

    Args:
    frame (bytes): Data frame provided as bytes
    ignore_crc (bool): If set, ignore any CRC failures
    subframe (dict): Optional subframe dataset, structured as {1: bytes, 2: bytes, etc...}

    Returns a dictionary, structured as follows:



    By default this function only returns information 

    """

    # Basic length check.
    if len(frame) < (RS41_FRAME_HEADER_LEN + RS41_ECC_LEN + RS41_FRAME_TYPE_LEN):
        raise ValueError(f"Supplied RS41 frame too small.")

    # Check for header.
    if frame[:RS41_FRAME_HEADER_LEN] != RS41_FRAME_HEADER:
        raise ValueError(f"Frame Header Mismatch")

    # Now we can start breaking apart the frame.
    output = {"blocks": {}}

    # ECC data is always present. For now we don't make use of this (maybe we should?)
    output["ecc_data"] = frame[RS41_ECC_POS : RS41_ECC_POS + RS41_ECC_LEN]

    # Decode the frame type field
    if frame[RS41_FRAME_TYPE_POS] == RS41_FRAME_TYPE_REGULAR:
        output["frame_type"] = "Regular"
    elif frame[RS41_FRAME_TYPE_POS] == RS41_FRAME_TYPE_EXTENDED:
        output["frame_type"] = "Extended"
    else:
        raise ValueError(f"Unknown Frame Type {hex(frame[RS41_FRAME_TYPE_POS])}")

    # Now we start decoding the different sub-blocks in the frame
    _idx = RS41_BLOCK_START_POS

    while _idx < len(frame):
        try:
            _block_type = frame[_idx]
            _block_len = frame[_idx + 1]
            _block_data = frame[_idx + 2 : _idx + 2 + _block_len]

            _crc_ok = check_packet_crc(frame[_idx + 2 : _idx + 2 + _block_len + 2])

            logging.debug(
                f"Block Type: {hex(_block_type)}, Len: {_block_len}, CRC OK: {_crc_ok}"
            )

            if _crc_ok:
                if _block_type in RS41_BLOCK_DECODERS:
                    if _block_len == RS41_BLOCK_DECODERS[_block_type]["expected_len"]:
                        # Decode fields
                        _block_field_data = struct.unpack(
                            RS41_BLOCK_DECODERS[_block_type]["struct"], _block_data
                        )
                        _block_dict = dict(
                            zip(
                                RS41_BLOCK_DECODERS[_block_type]["fields"],
                                _block_field_data,
                            )
                        )

                        # Post-process any individual fields that require it
                        # These are usually simple unit or type conversions.
                        for _field in _block_dict:
                            if (
                                _field
                                in RS41_BLOCK_DECODERS[_block_type]["field_decoders"]
                            ):
                                _temp = RS41_BLOCK_DECODERS[_block_type][
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
                        if RS41_BLOCK_DECODERS[_block_type]["block_post_process"]:
                            output["blocks"][
                                RS41_BLOCK_DECODERS[_block_type]["block_name"]
                            ] = RS41_BLOCK_DECODERS[_block_type]["block_post_process"](
                                _block_dict, subframe=subframe
                            )
                        else:
                            # Add the resultant block data to our output dictionary as-is
                            output["blocks"][
                                RS41_BLOCK_DECODERS[_block_type]["block_name"]
                            ] = _block_dict

                    else:
                        logging.error(
                            f"Block Type {hex(_block_type)} has unexpected length {_block_len} (expected {RS41_BLOCK_DECODERS[_block_type]['expected_len']})"
                        )
                else:
                    logging.error(f"Unknown Block Type: {hex(_block_type)}, Length: {_block_len}")

            else:
                logging.error("Block CRC failure")

            # Increment our pointer to the start of the next block.
            _idx += 2 + _block_len + 2

        except Exception as e:
            logging.error(f"Error extracting block. (Index: {_idx}): {str(e)}")
            break

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
    _line += "timestamp,"

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
    _line += "temp,humidity,pressure,"

    # The rest TODO...


    return _line



if __name__ == "__main__":
    import argparse
    import codecs
    import pprint

    # Command line arguments.
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "hexstring", help="RS41 Frame in Hexadecimal",
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
