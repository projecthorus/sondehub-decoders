#!/usr/bin/env python
#
#   RS41 Decoder Library
#
import logging
import time
import traceback
from .decoder import decode
from .subframe import *

class RS41(object):
    """
    Stateful RS41 Decoder Class
    """

    def __init__(
        self,
        archive_postprocess_callback = None):
        """
        
        """

        # Serial number store. Once set, all future frames must match this serial number
        self.serial = None
        # Store of raw frames which we will post-process once a full sub-frame is available.
        self.raw_frames = []
        # Subframe data store, as a dictionary with each sub-frame entry.
        self.subframe = None
        self.max_subframe = None

        # Last frame arrival time, which allows us to close out this object after some timeout.
        self.last_frame_time = time.time()

        self.archive_postprocess_callback = archive_postprocess_callback

    
    def add_frame(self, raw):
        """ Add and process a frame """

        try:
            _frame = decode(raw, subframe=self.subframe)

            self.last_frame_time = time.time()

            if self.serial is None:
                self.serial = _frame['blocks']['Status']['serial']
            else:
                if _frame['blocks']['Status']['serial'] != self.serial:
                    # Serial mismatch!
                    raise ValueError(f"Telemetry is from a different radiosonde! ({_frame['blocks']['Status']['serial']}, should be {self.serial}.")

            # If measurements could not be calculated, add the frame to self.raw_frames for later re-processing

            # Create a new subframe object if none exists yet
            if self.subframe is None:
                self.subframe = RS41Subframe(max_subframe=_frame['blocks']['Status']['max_subframe'])

            # Add the current subframe data
            self.subframe.add_segment(_frame['blocks']['Status']['subframe_count'], _frame['blocks']['Status']['subframe_data'])

            _frame['subframe'] = self.subframe.subframe_fields

            if self.subframe.subframe_complete():
                # TODO - Reprocess anything in self.raw_frames and send to a callback.
                pass

            return _frame
            


        except Exception as e:
            logging.exception(f"Error processing frame",exc_info=e)
            return


