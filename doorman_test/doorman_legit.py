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
# ==== Tests doorman by sending attacks and solving puzzles fast ====
#

import re
import os
import sys
import argparse
import time
import puzzle_solver
import urllib
import threading
import Queue

DIRNAME = os.path.dirname(os.path.realpath(__file__))
sys.path.append(os.path.join(DIRNAME, '..', 'common'))

import log

if __name__ == "__main__":
    cwd = os.getcwd()

    parser = argparse.ArgumentParser(description='Tool used to test Doorman with legit clients. WARNING: this ' \
        'script does not have an off switch. To stop, use: pkill -f "python.* doorman_legit.py"')

    parser.add_argument("-p", "--prefix",  type=str, required=True,
                    help="the domain part of the URL to submit requests to; e.g. 'http://localhost'")
    parser.add_argument("-s", "--suffix",  type=str, required=True,
                    help="the rest of the url; e.g. '/index.php'")
    parser.add_argument("-r", "--regex",  type=str, required=True,
                    help="regular expression that positively matches the target web-app page, NOT the puzzle page, and NOT 403 pages or anything else; e.g. MediaWiki")
    parser.add_argument("-t", "--threads",  type=int, default=10,
                    help="Default=%(default)s. The total number of threads to run")
    parser.add_argument("-st", "--stall",  type=float, default=0.2,
                    help="Default=%(default)s. The number of seconds to stall when needed")
    parser.add_argument("-i", "--id",  type=int, default=1,
                    help="Default=%(default)s. An id to identify this attacker in the logs")
    parser.add_argument("-y", "--history",  type=int, default=20,
                    help="Default=%(default)s. When displaying averages, only use the last HISTORY measurements.")

    log.add_arguments(parser)
    args = parser.parse_args()
    logger = log.getLogger(args, name="doorman_attack.py.%d" % args.id)
    logger.info("Command line arguments: %s" % str(args))

    # By settings bounded-value == #threads, it means every thread can work on puzzles
    # at the same time. This only makes sense when the puzzles aren't CPU bound
    cpu = threading.BoundedSemaphore(value=args.threads)

    stall_after_puzzle = True
    queue = Queue.Queue()

    for i in xrange(0, args.threads):
        logger.debug("Launching %d/%d", i + 1, args.threads)
        legit = puzzle_solver.ClientThread(logger, queue, cpu, args.prefix, args.suffix, args.regex, \
            args.stall, i + 1, stall_after_puzzle)
        legit.start()

    monitor = puzzle_solver.Monitor(logger, queue, args.history)
    monitor.run()

