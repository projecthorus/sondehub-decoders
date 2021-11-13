#!/usr/bin/env python
#
#   RS41 Decoder Library - RS41 SubFrame Data Handling
#
import logging
import struct

class RS41Subframe(object):

    SUBFRAME_IDXS = {
        # Variable Name     [index into subframe, data length, data type]
        # Refer function at line 502 of rs41mod
        'freq_lower':       [0x002, 1, 'B'],
        'freq_upper':       [0x003, 1, 'B'],
        'firmware_version': [0x015, 2, 'H'],
        'burstkill_status': [0x02B, 1, 'B'],
        'rf1':              [0x03D, 4, 'f'],
        'rf2':              [0x041, 4, 'f'],
        'tempmeas_co1_0':   [0x04D, 4, 'f'],
        'tempmeas_co1_1':   [0x051, 4, 'f'],
        'tempmeas_co1_2':   [0x055, 4, 'f'],
        'tempmeas_calT1_0': [0x059, 4, 'f'],
        'tempmeas_calT1_1': [0x05D, 4, 'f'],
        'tempmeas_calT1_2': [0x061, 4, 'f'],
        'humimeas_co2_0':   [0x125, 4, 'f'],
        'humimeas_co2_1':   [0x129, 4, 'f'],
        'humimeas_co2_2':   [0x12D, 4, 'f'],
        'humimeas_calT1_0': [0x131, 4, 'f'],
        'humimeas_calT1_1': [0x135, 4, 'f'],
        'humimeas_calT1_2': [0x139, 4, 'f'],
        'subtype':          [0x218, 10, 's'],
        'mainboard_type':   [0x222, 10, 's'],
        'mainboard_serial': [0x22C, 10, 's'],
        'pressure_serial':  [0x243, 10, 's'],
        'burstkill_timer':  [0x316, 2, 'H']
    }

    def __init__(self, max_subframe=50):
        """
        RS41 Subframe Storage and data extraction
        """

        self.subframe_raw_dict = {}
        self.subframe_length = max_subframe+1
        self.subframe_list = [0]*(self.subframe_length*16)
        self.subframe_fields = {}


    def index_available(self, index):
        """ Determine if a given index is available in the current set of subframe data """

        _block = index//16

        if _block in self.subframe_raw_dict:
            return True
        else:
            return False


    def extract_single_field(self, index, length, field_type):
        """ Attempt to extract a single field from the available subtype data """
        if self.index_available(index) and self.index_available(index+length-1):
            if field_type == 'B':
                # Don't use struct, just extract individual int.
                return self.subframe_list[index]
            elif field_type == 'H':
                #logging.debug(f"{index}: {str(bytes( self.subframe_list[index:index+2] ))}")
                _data = struct.unpack('<H', bytes( self.subframe_list[index:index+2] ) )[0]
                return _data
            elif field_type == 'f':
                _data = struct.unpack('<f', bytes( self.subframe_list[index:index+4] ) )[0]
                return _data
            elif field_type == 's':
                _str = struct.unpack(f'<{length}s', bytes(self.subframe_list[index:index+length]))[0]
                #logging.debug(f'Str: {str(_str)}')
                return _str.decode('ascii').rstrip('\x00')
        else:
            return None



    def update_fields(self):
        """ Work through all the known subframe fields and try and extract them from the available data """
        for _field_name in self.SUBFRAME_IDXS:
            _field_params = self.SUBFRAME_IDXS[_field_name]
            _field_data = self.extract_single_field(_field_params[0], _field_params[1], _field_params[2])

            if _field_data:
                self.subframe_fields[_field_name] = _field_data

        # Post-Process a few fields.
        if ('freq_lower' in self.subframe_fields) and ('freq_upper' in self.subframe_fields):
            # from rs41mod.c
            _f0 = ( (self.subframe_fields['freq_lower'] & 0xC0)*10) / 64
            _f1 = 40*self.subframe_fields['freq_upper']
            _freq = int(400000 + _f1+_f0)
            self.subframe_fields['tx_frequency_khz'] = _freq

        # Collate tempmeas_co1 if available
        if ('tempmeas_co1_0' in self.subframe_fields) and ('tempmeas_co1_1' in self.subframe_fields) and ('tempmeas_co1_2' in self.subframe_fields):
            self.subframe_fields['tempmeas_co1'] = [
                self.subframe_fields['tempmeas_co1_0'],
                self.subframe_fields['tempmeas_co1_1'],
                self.subframe_fields['tempmeas_co1_2'],
                ]
        # Collate tempmeas_calT1 if available
        if ('tempmeas_calT1_0' in self.subframe_fields) and ('tempmeas_calT1_1' in self.subframe_fields) and ('tempmeas_calT1_2' in self.subframe_fields):
            self.subframe_fields['tempmeas_calT1'] = [
                self.subframe_fields['tempmeas_calT1_0'],
                self.subframe_fields['tempmeas_calT1_1'],
                self.subframe_fields['tempmeas_calT1_2'],
                ]

        # Collate humimeas_co2 if available
        if ('humimeas_co2_0' in self.subframe_fields) and ('humimeas_co2_1' in self.subframe_fields) and ('humimeas_co2_2' in self.subframe_fields):
            self.subframe_fields['humimeas_co2'] = [
                self.subframe_fields['humimeas_co2_0'],
                self.subframe_fields['humimeas_co2_1'],
                self.subframe_fields['humimeas_co2_2'],
                ]
        # Collate tempmeas_calT1 if available
        if ('humimeas_calT1_0' in self.subframe_fields) and ('humimeas_calT1_1' in self.subframe_fields) and ('humimeas_calT1_2' in self.subframe_fields):
            self.subframe_fields['humimeas_calT1'] = [
                self.subframe_fields['humimeas_calT1_0'],
                self.subframe_fields['humimeas_calT1_1'],
                self.subframe_fields['humimeas_calT1_2'],
                ]

        return self.subframe_fields

    
    def add_segment(self, segment_num, segment_data):
        """ Add/update a subframe segment. """

        if (segment_num < self.subframe_length) and len(segment_data) == 16:
            # Add/update the raw dictionary
            self.subframe_raw_dict[segment_num] = segment_data
            logging.debug(f"Received subframe segment {segment_num}, ({len(list(self.subframe_raw_dict.keys()))}/{self.subframe_length})")

            # Update the bytes (actually a list of ints)
            self.subframe_list[16*segment_num : 16*(segment_num+1)] = list(segment_data)

            #logging.debug(str(bytes(self.subframe_list)))

            # Re-parse the subframe for available fields.
            self.update_fields()



            logging.debug(f"Subframe Fields: {str(self.subframe_fields)}")



    def temperature_cal_available(self):
        if ('rf1' in self.subframe_fields) and ('rf2' in self.subframe_fields) and ('tempmeas_co1' in self.subframe_fields) and ('tempmeas_calT1' in self.subframe_fields):
            return True
        else:
            return False

    def humidity_cal_available(self):
        return False

    def pressure_cal_available(self):
        return False

    def subframe_complete(self):
        """
        Indicate whether we have a complete set of subframe data.
        This is used to trigger re-processing of old telemetry data.
        """
        if len(list(self.subframe_raw_dict.keys())) == self.subframe_length:
            return True
        else:
            return False