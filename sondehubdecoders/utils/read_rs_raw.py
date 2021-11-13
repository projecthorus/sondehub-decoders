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








if __name__ == "__main__":
    import argparse
    import pprint
    import sys
    from ..RS41.decoder import decode as rs41_decode
    from ..RS41.decoder import to_autorx_log as rs41_log

    # Command line arguments.
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "filename", help="Filename to Open",
    )
    parser.add_argument(
        "-t", "--type", help="Radiosonde type (RS41, ...)", default="RS41"
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
    else:
        logging.critical("Unknown Radiosonde Type!")
        sys.exit(1)

    # Read file
    frames = read_raw_rs41(args.filename)
    
    #print(frames)
    #pprint.pprint(decode(_hex))

    for _raw_frame in frames:
        try:
            _frame = decode_func(_raw_frame)


            if args.csv:
                print(log_func(_frame))
            else:
                pprint.pprint(_frame)

        except:
            continue

