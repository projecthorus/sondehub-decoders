#!/usr/bin/env python
#
#   LMS6_403 Decoder Library
#
import logging
import time
import traceback
from .decoder import decode

class LMS6_403(object):
    """
    Stateful LMS6_403 Decoder Class
    """

    LMS6_403_CAL_PER_FRAME = 4
    LMS6_403_TOTAL_CAL = 28

    def __init__(
        self,
        archive_postprocess_callback = None):
        """
        
        """

        # Serial number store. Once set, all future frames must match this serial number
        self.serial = None
        # Store of raw frames which we will post-process once a full sub-frame is available.
        self.raw_frames = []
        # Calibration data
        self.cal_data = None

        # Last frame arrival time, which allows us to close out this object after some timeout.
        self.last_frame_time = time.time()

        self.archive_postprocess_callback = archive_postprocess_callback

    
    def add_frame(self, raw):
        """ Add and process a frame """

        try:
            _frame = decode(raw, cal_data = self.cal_data)

            self.last_frame_time = time.time()

            if self.serial is None:
                self.serial = _frame['serial']
            else:
                if _frame['serial'] != self.serial:
                    # Serial mismatch!
                    raise ValueError(f"Telemetry is from a different radiosonde! ({_frame['serial']}, should be {self.serial}.")

            # If measurements could not be calculated, add the frame to self.raw_frames for later re-processing
            # TODO - May not be worth it for the LMS6

            # Create a new subframe object if none exists yet
            if self.cal_data is None:
                self.cal_data = [None]*self.LMS6_403_TOTAL_CAL

            # Calibration data is split across multiple frames.
            _cal_base_idx = (_frame['frame_count']%(self.LMS6_403_TOTAL_CAL//self.LMS6_403_CAL_PER_FRAME))*self.LMS6_403_CAL_PER_FRAME
            self.cal_data[_cal_base_idx] = _frame['cal1']
            self.cal_data[_cal_base_idx+1] = _frame['cal2']
            self.cal_data[_cal_base_idx+2] = _frame['cal3']
            self.cal_data[_cal_base_idx+3] = _frame['cal4']

            _frame['cal_data'] = self.cal_data

            if not (None in self.cal_data):
                # TODO - Reprocess anything in self.raw_frames and send to a callback.
                pass

            return _frame
            


        except Exception as e:
            logging.exception(f"Error processing frame",exc_info=e)
            return

