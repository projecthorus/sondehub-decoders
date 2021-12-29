#!/usr/bin/env python
#
#   Helper script to read and process raw hex output from a RS decoder.
#
import codecs
import logging


def read_raw_rs41(filename):
    """
    Attempt to read a file containing lines of hexadecimal data, suffixed with CRC information (e.g. [OK] or [NO])
    
    Returns a list of bytes.
    """

    # Read in entire file contents
    _f = open(filename, 'r')
    _data = _f.read()
    _f.close()

    output = []

    # Work through each line
    for _line in _data.split('\n'):

        if '[OK]' in _line:
            _hex = _line.split(' ')[0]
            _bytes = codecs.decode(_hex, 'hex')

            output.append(_bytes)

    return output


def read_raw_lms6_403(filename):
    """
    Attempt to read a file containing lines of hexadecimal data, suffixed with CRC information (e.g. [OK] or [NO])
    
    Returns a list of bytes.
    """

    # Read in entire file contents
    _f = open(filename, 'r')
    _data = _f.read()
    _f.close()

    output = []

    # Work through each line
    for _line in _data.split('\n'):

        if '[OK]' in _line:
            _hex = _line.split('  [OK]')[0]
            _hex = _hex.replace(' ','')
            try:
                _bytes = codecs.decode(_hex, 'hex')
            except:
                continue

            output.append(_bytes)

    return output



if __name__ == "__main__":
    import argparse
    import pprint
    import sys
    from ..RS41.decoder import decode as rs41_decode
    from ..RS41.decoder import to_autorx_log as rs41_log
    from ..RS41 import RS41
    from ..LMS6_403.decoder import decode as lms6_403_decode

    # Command line arguments.
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "filename", help="Filename to Open",
    )
    parser.add_argument(
        "-t", "--type", help="Radiosonde type (RS41, LMS6_403, DFM, etc...)", default="RS41"
    )
    parser.add_argument(
        "-v", "--verbose", help="Enable debug output.", action="store_true"
    )
    parser.add_argument(
        "-c", "--csv", help="Output as CSV", action="store_true", default=False
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

    
    if args.type == "RS41":
        decode_func = rs41_decode
        log_func = rs41_log
        frames = read_raw_rs41(args.filename)
    # Other types here
    elif args.type == "LMS6_403":
        log_func = lambda x: print(x)
        decode_func = lms6_403_decode
        frames = read_raw_lms6_403(args.filename)
    else:
        logging.critical("Unknown Radiosonde Type!")
        sys.exit(1)

    # Read file

    
    #print(frames)
    #pprint.pprint(decode(_hex))

    _rs41 = RS41()

    for _raw_frame in frames:
        try:
            if args.type == "RS41":
                _frame = _rs41.add_frame(_raw_frame)
                #_frame = decode_func(_raw_frame)
            elif args.type == "LMS6_403":
                #_frame = _raw_frame
                _frame = decode_func(_raw_frame)

            if args.csv:
                print(log_func(_frame))
            else:
                pprint.pprint(_frame)

        except Exception as e:
            logging.exception("Issue parsing frame", exc_info=e)
            continue

