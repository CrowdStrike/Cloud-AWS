# logger.py
# python 3.7
# DCS 9/17/18
# JSH 11/15/20 modified

# logger.py opens a local logfile for write and writes logs to it

import time
import json
import logging
from logging.handlers import RotatingFileHandler


class Logger():
    def __init__(self, logfile, logger):
        """
        Creates a rotating output log
        """
        self.outputlog = logging.getLogger(logger)
        self.outputlog.setLevel(logging.INFO)
        # add a rotating handler
        handler = RotatingFileHandler(logfile, maxBytes=20971520, backupCount=5)
        self.outputlog.addHandler(handler)

    def statusWrite(self, log):
        # write will take as input an execution log and write it to the log along with the time
        # @params log: the log to write to the file
        ts = time.ctime()
        self.outputlog.info(ts + " %s\n" % log)

    def outputWrite(self, log):
        # write will take as input an output log and write it to the log along with the time
        # @params log: the log to write to the file
        ts = time.ctime()
        self.outputlog.info(ts + "\n ")
        self.outputlog.info(json.dumps(log, indent=4))

    def offsetWrite(self, offset_file, log):
        # write will take as input an offset log and write it to the log along with the time
        # @params log: the log to write to the file
        logfile = open(offset_file, "w")
        logfile.write(str(log))
        logfile.close()

    def offsetRead(self, offset_file):
        offset = 0
        try:
            logfile = open(offset_file, "r")
            offset = int(logfile.readline())
            logfile.close()
        except:
            pass

        return offset
