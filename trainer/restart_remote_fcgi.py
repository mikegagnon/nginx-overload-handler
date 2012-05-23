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
# ==== train.py ====
#
# USAGE: ./train.py completion period workers username server
#   where:
#       completion is the "minimal completion rate" (a number between 0 and 1)
#       period is the __initial__ interarrival period
#       workers is the numer of fastcgi workers on the server
#       usernaname is a user on server who has permission to restart the
#           the fcgi workers (see restart_remote_fcgi.sh)
#       server is the address of the server (or domain name)
#
# The goal is to run the web application under a variety of Beer Garden
# configurations, and recommend several configurations where at least
# 'completion' portion of legitimate requests complete. The trainer than
# reports the performance metrics from the trials, so you can choose the
# configuration with the "best" performance. "Best" is subjective; there is
# often a trade space between latency, throughput, and completion rate. The
# only setting the trainer modifies is 'period', interarrival time between
# requests.
#
# PREREQs:
#   (1) create a trace file
#
# ==== Design ====
#
# (1) Find M, the "minimal period." I.e., M is the smallest period that Beer
# Garden will recommend.
# (2) Find alternate periods by increasing M by 15% ten times.
# (3) Report the configurations, each configuration has 3 performance metrics
#     associated with its performance: throughput, completion rate, latency. Sort
#     configurations three different ways (according to each metric).
#

#TODO: make sure all file accesses are absolute and refer to the correct parent dir

import subprocess
import urllib2
import argparse
import os
import sys
import logging
import time

DIRNAME = os.path.dirname(os.path.realpath(__file__))
sys.path.append(os.path.join(DIRNAME, '..', 'common'))
RESTART_SCRIPT = os.path.join(DIRNAME, "restart_remote_fcgi.sh")

import log
import env

siteconfig = os.path.join(DIRNAME, "..", "siteconfig.sh")
var = env.env(siteconfig)
SERVER_NAME = var["SERVER_NAME"]

MAX_RETRIES = 30

class RestartWorkerError(Exception):
    pass

def restart_remote_fcgi(server, username, sshport, request_url, logger, max_retries=MAX_RETRIES):
    # ssh username@server -p sshport, then executes restart_fcgi.sh on server
    # after executing restart_fcgi.sh on server, keeps requesting request_url
    # until the request succeeds (up to max_retries)
    logger.debug("Restarting FCGI workers on %s", server)
    logger.debug("max_retries = %d", max_retries)
    cmd = [RESTART_SCRIPT,
        username,
        server,
        str(sshport)]
    logger.debug("running cmd = %s", cmd)
    p = subprocess.Popen(cmd, stderr=subprocess.PIPE, stdout=subprocess.PIPE)
    stdoutLogger = log.FileLoggerThread(logger, "restart_fcgi_workers stdout", logging.ERROR, p.stdout)
    stderrLogger = log.FileLoggerThread(logger, "restart_fcgi_workers stderr", logging.ERROR, p.stderr)
    stdoutLogger.start()
    stderrLogger.start()

    ret = p.wait()
    logger.debug("cmd done")
    if ret != 0:
        raise RestartWorkerError("restart_remote_fcgi.sh returned %d", ret)

    # Keep trying to access url until it succeeds (meeing restart_remote_fcgi.sh
    # has taken effect)
    success = False
    for i in range(0, max_retries - 1):
        time.sleep(1)
        logger.debug("Requesting %s, try number = %d", request_url, i + 1)
        try:
            response = urllib2.urlopen(request_url)
            success = True
            break
        except urllib2.URLError:
            logger.debug("Request try number = %d, failed", i + 1)
            pass

    if not success:
        time.sleep(1)
        logger.debug("Requesting %s, last try", request_url)
        try:
            response = urllib2.urlopen(request_url)
            success = True
        except urllib2.URLError:
            logger.critical("Error: Could not access %s. Perhaps restart_remote_fcgi.sh did not work." % request_url)
            raise
    logger.debug("Request succeeded afer %d requests", i + 1)
    logger.debug("Restart FCGI workers success")

if __name__ == "__main__":
    cwd = os.getcwd()

    default_trace_filename = os.path.join(cwd, "trace.txt")

    parser = argparse.ArgumentParser(description='Restarts FCGI workers on server.')
    parser.add_argument("-u", "--username", type=str, default="beergarden",
                    help="Default=%(default)s. The username on the server to log in as (via ssh).")
    parser.add_argument("-s", "--server", type=str, default=SERVER_NAME,
                    help="Default=%(default)s. The address of the server running Beer Garden.")
    parser.add_argument("--sshport", type=int, default=22,
                    help="Default=%(default)d. The port of the server listens for ssh.")
    parser.add_argument("--url", type=str, required=True,
                    help="REQUIRED. After attempting to restart the FCGI workers, request URL " \
                        "to make sure the restart worked.")
    parser.add_argument("-m", "--max-retries", type=int, default=MAX_RETRIES,
                    help="Default=%(default)d. After attempting to restart the FCGI workers, how many times to " \
                        "try requesting URL before giving up.")

    log.add_arguments(parser)
    args = parser.parse_args()
    logger = log.getLogger(args)
    logger.info("Command line arguments: %s" % str(args))

    restart_remote_fcgi( \
        args.server, \
        args.username, \
        args.sshport, \
        args.url, \
        logger, \
        args.max_retries)

