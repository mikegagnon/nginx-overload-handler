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
# TODO: Re-direct output to stdout / stderr to logger
#

import logging
import logging.handlers
import sys
import os
import traceback
import inspect
import argparse

DIRNAME = os.path.dirname(os.path.realpath(__file__))
LOGDIR = os.path.join(DIRNAME, "..", "log")
LOGDIR = os.path.realpath(LOGDIR)

MAX_LOGFILE_BYTES = 1024 * 1024 * 1 # 1 MB
BACKUP_COUNT = 5

FORMATTER_LOGFILE = logging.Formatter("%(asctime)s - %(levelname)10s - %(process)d - %(filename)20s : %(funcName)30s - %(message)s")
FORMATTER_STDERR = logging.Formatter("%(levelname)10s - %(filename)20s : %(funcName)30s - %(message)s")

def uncaughtException(logger, typ, value, tb):
    exception_lines = traceback.format_exception(typ, value, tb)
    for line in exception_lines:
        logger.critical(line.strip())

def getLogger(args=None, stderr=None, logfile=None, name=None):
    '''to log to stderr set stderr = a level from logging
    to log to ../log/foo.log set logfile = a level from logging and
    set name = "foo"'''

    if name == None:
        # Get the filename of the caller
        _,filename,_,_,_,_ = inspect.getouterframes(inspect.currentframe())[1]
        name = os.path.basename(filename)

    logger = logging.getLogger(name)
    # for some readon the expression 'args == None' causes a TypeError (motivating isinstance)
    if stderr == None and logfile == None and not isinstance(args, argparse.Namespace):
        raise ValueError("You must set at least one of stderr or logfile to a logging level (or args)")
    if (stderr != None or logfile != None) and isinstance(args, argparse.Namespace):
        raise ValueError("You must set (stderr and/or logfile) or args, but not both")
    if isinstance(args, argparse.Namespace):
        stderr = loggingMap[args.stderr]
        logfile = loggingMap[args.logfile]

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
    if logfile != None:
        logger.debug("Recording logs in %s" % filename)
    func = lambda typ, value, traceback: uncaughtException(logger, typ, value, traceback)
    sys.excepthook = func

    return logger

loggingChoices = ["CRITICAL", "ERROR", "WARNING", "INFO", "DEBUG", "off"]
loggingMap = {
    "CRITICAL" : logging.CRITICAL,
    "ERROR" : logging.ERROR,
    "WARNING" : logging.WARNING,
    "INFO" : logging.INFO,
    "DEBUG" : logging.DEBUG,
    "off" : None}

# USAGE:
#    parser = argparse.ArgumentParser()
#    log.add_arguments(parser)
#    args = parser.parse_args()
#    logger = log.getLogger(args)
#    logger.info("Command line arguments: %s" % str(args))
def add_arguments(parser):
    # TODO: use Action class top convert string to logging level
    parser.add_argument("--stderr", type=str, default="INFO", choices=loggingChoices,
                    help="Default=%(default)s. Logging level for stderr.")
    parser.add_argument("--logfile", type=str, default="INFO", choices=loggingChoices,
                    help="Default=%(default)s. Logging level for log file.")

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    add_arguments(parser)
    args = parser.parse_args()
    logger = getLogger(args)

    logger.critical("test")
    logger.error("test")
    logger.warning("test")
    logger.info("test")
    logger.debug("test")
    raise ValueError("foo")

