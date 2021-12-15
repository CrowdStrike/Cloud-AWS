"""Log handler for Security Hub integration"""
# DCS 9/17/18
# JSH 11/15/20 modified

import time
import json
import logging
from logging.handlers import RotatingFileHandler


class Logger():
    """Class to handle all logging operations."""
    def __init__(self, logfile, logger):
        """Create a rotating output log."""
        self.outputlog = logging.getLogger(logger)
        self.outputlog.setLevel(logging.INFO)
        # add a rotating handler
        handler = RotatingFileHandler(logfile, maxBytes=20971520, backupCount=5)
        self.outputlog.addHandler(handler)

    def status_write(self, log):
        """Write a status message to the log."""
        # write will take as input an execution log and write it to the log along with the time
        # @params log: the log to write to the file
        timestamp = time.ctime()
        self.outputlog.info(timestamp + " %s\n" % log)

    def output_write(self, log):
        """Write a log to the log."""
        # write will take as input an output log and write it to the log along with the time
        # @params log: the log to write to the file
        timestamp = time.ctime()
        self.outputlog.info("%s\n ", timestamp)
        self.outputlog.info(json.dumps(log, indent=4))

    @staticmethod
    def offset_write(offset_file, log):
        """Log the offset."""
        # write will take as input an offset log and write it to the log along with the time
        # @params log: the log to write to the file
        with open(offset_file, "w", encoding="utf-8") as logfile:
            logfile.write(str(log))

    @staticmethod
    def offset_read(offset_file):
        """Read the offset."""
        offset = 0
        try:
            with open(offset_file, "r", encoding="utf-8") as logfile:
                offset = int(logfile.readline())
        except (FileNotFoundError, OSError, ValueError):
            # Skip if we can't find the file or read it, we'll start at zero.
            pass

        return offset
