#!/usr/bin/env python
#
# Copyright 2012 HellaSec, LLC
#
#  Licensed under the Apache License, Version 2.0 (the "License");
#  you may not use this file except in compliance with the License.
#  You may obtain a copy of the License at
#
#      http://www.apache.org/licenses/LICENSE-2.0
#
#  Unless required by applicable law or agreed to in writing, software
#  distributed under the License is distributed on an "AS IS" BASIS,
#  WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
#  See the License for the specific language governing permissions and
#  limitations under the License.
#
# ==== log.py ====
#
# TODO: provide command-line arg parsing. Figure out if there's a way to generically
# catch all uncaught exceptions, and log them

import logging
import logging.handlers
import sys
import os

DIRNAME = os.path.dirname(os.path.realpath(__file__))
LOGDIR = os.path.join(DIRNAME, "..", "log")
LOGDIR = os.path.realpath(LOGDIR)

MAX_LOGFILE_BYTES = 1024 * 1024 * 1 # 1 MB
BACKUP_COUNT = 5

FORMATTER_LOGFILE = logging.Formatter("%(asctime)s - %(levelname)10s - %(process)d - %(filename)s:%(funcName)s - %(message)s")
FORMATTER_STDERR = logging.Formatter("%(levelname)s - %(filename)s:%(funcName)s - %(message)s")

def getLogger(stderr=None, logfile=None, name=None):
    '''to log to stderr set stderr = a level from logging
    to log to ../log/foo.log set logfile = a level from logging and
    set name = "foo"'''

    if name == None:
        # TODO: Get the filename of the caller
        name = "default"
    logger = logging.getLogger(name)
    if not (stderr != None or logfile != None):
        raise ValueError("You must set at least one of stderr or logfile to a logging level")
    handlers = []
    if stderr != None:
        handler = logging.StreamHandler(sys.stderr)
        handler.setLevel(stderr)
        handler.setFormatter(FORMATTER_STDERR)
        handlers.append(handler)
    if logfile != None:
        filename = os.path.join(LOGDIR, name) + ".log"
        handler = logging.handlers.RotatingFileHandler(
            filename,
            mode = 'a',
            maxBytes = MAX_LOGFILE_BYTES,
            backupCount = BACKUP_COUNT)
        handler.setLevel(logfile)
        handler.setFormatter(FORMATTER_LOGFILE)
        handlers.append(handler)
    min_level = min([handler.level for handler in handlers])
    for handler in handlers:
        logger.addHandler(handler)
    logger.setLevel(min_level)
    logger.debug("New logger instance")
    return logger

if __name__ == "__main__":
    log = getLogger(stderr=logging.INFO,logfile=logging.DEBUG)
    log.critical("test")
    log.error("test")
    log.warning("test")
    log.info("test")
    log.debug("test")

