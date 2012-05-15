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
# ==== simclient.py ====
# Simulates http requests (legit and attack) being funneled through a doorman.
#
# DESIGN:
#   - Fill up a queue of requests (legit and attack requests)
#   - For each fcgi worker in the backend, launch a thread, which does the
#     following:
#       (1) pulls a request from the queue and issues it to the server
#       (2) sets a timeout on the request
#       (3) If timeout expires, then acccount the request as a failure. Do not
#         actually abort the request, but go ahead and go back to step 1.
# NOTE:
#   The implemention suffers many deficiencies that will likely result in poor
#   timing precision when timeouts are short. For an explanation see
#   http://www.hpl.hp.com/research/linux/httperf/httperf-man-0.9.pdf
#   We can imporve the implementation later if we need to. Also, I would just
#   use httperf, but it doesn't provide this functionality.
#
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
import restart_remote_fcgi

siteconfig = os.path.join(DIRNAME, "..", "siteconfig.sh")
var = env.env(siteconfig)
SERVER_NAME = var["SERVER_NAME"]

class SimClient:

    def __init__(self, \
        server, \
        username, \
        sshport, \
        legit_trace, \
        attack_trace, \
        attack_probability, \
        timeout, \
        num_fcgi_workers, \
        max_threads, \
        num_requests, \
        logger):
        '''to restart workers does ssh username@server -p sshport, then executes restart script.
        gets list of legit urls from legit_trace filename
        gets list of legit urls from attack_trace filename
        when generating requests, the probability that a request is an attack is attack_probability
        timeout is the amount of time to give a request before it's written off as a failure
        num_fcgi_workers
        max_threads is the maximum number to run, which is also the maximum number of connections
        to keep open'''
        self.server = server
        self.username = username
        self.sshport = sshport
        self.legit_trace = legit_trace
        self.attack_trace = attack_trace
        self.attack_probability = attack_probability
        self.timeout = timeout
        self.num_fcgi_workers = num_fcgi_workers
        self.max_threads = max_threads
        self.num_requests = num_requests
        self.logger = logger

    def restart_remote_fcgi(self, trial_num):
        self.logger.info("trial_num=%d", trial_num)
        restart_remote_fcgi.restart_remote_fcgi( \
            self.server, \
            self.username, \
            self.sshport, \
            self.legit_url, \
            self.logger)


if __name__ == "__main__":
    cwd = os.getcwd()

    default_trace_filename = os.path.join(cwd, "trace.txt")
        attack_probability, \
        num_fcgi_workers, \
        max_threads, \

    parser = argparse.ArgumentParser(description='Simulates http requests (legit and attack) being funneled through a doorman')
    parser.add_argument("-to", "--timeout", type=float, default=0.5,
                    help="Default=%(default)f. The amount of time to give a task before it is considered a failure.")
    parser.add_argument("-lt", "--legit-trace", type=str, default=default_legit_trace,
                    help="Default=%(default)s. The legit trace file (produced by TODO)")
    parser.add_argument("-at", "--attack-trace", type=str, default=default_attack_trace,
                    help="Default=%(default)s. The attack trace file (produced by TODO)")
    parser.add_argument("-u", "--username", type=str, default="beergarden",
                    help="Default=%(default)s. The username on the server. Used when "\
                    "invoking restart_remote_fcgi.sh (see its source for PREREQs for username)")
    parser.add_argument("-s", "--server", type=str, default=SERVER_NAME,
                    help="Default=%(default)s. The address of the server running Beer Garden.")
    parser.add_argument("--sshport", type=int, default=22,
                    help="Default=%(default)s. The port of the server listens for ssh.")
    parser.add_argument("-r", "--num-requests", type=int, default=default_num_requests,
                    help="Default=%(default)d. The number of requests to issue")
    parser.add_argument("-a", "--attack", type=float, default=0.20,
                    help="Default=%(default)f. The probably that a request is an attack")
    parser.add_argument("-w", "--workers", type=int, required=True,
                    help="REQUIRED. The number of FCGI workers on the server")
    parser.add_argument("-th", "--threads", type=int, default=None,
                    help="Default=3*WORKERS. The max number of threads")

    log.add_arguments(parser)
    args = parser.parse_args()
    logger = log.getLogger(args)
    logger.info("Command line arguments: %s" % str(args))

    if args.threads == None:
        args.threads = 3 * args.workers

    try:
        with open(args.legit_trace, "r") as f:
            pass
    except:
        logger.critical("Error: could not open trace file (%s)" % args.legit_trace)
        sys.exit(1)

    try:
        with open(args.attack_trace, "r") as f:
            pass
    except:
        logger.critical("Error: could not open trace file (%s)" % args.l_trace)
        sys.exit(1)

    train = Train(
        args.completion,
        args.period,
        args.trace,
        args.username,
        args.server,
        args.sshport,
        args.num_tests,
        args.test_size,
        logger)
    train.train()

