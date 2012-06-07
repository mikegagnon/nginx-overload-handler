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
# ==== Simulates web clients and solves Doorman puzzles ====
#

import re
import os
import sys
import argparse
import time
import puzzle_solver
import urllib
import urllib2
import threading
import Queue

DIRNAME = os.path.dirname(os.path.realpath(__file__))
sys.path.append(os.path.join(DIRNAME, '..', 'common'))

import log

class AttackerThread(threading.Thread):
    '''A web client that tests doorman by attacking web application.
    The general idea is to simulate an attacker with at least one CPU:
        (1) Whenever Doorman isn't active, then rapidly submit attack requests
        (2) When doorman is active, then solve puzzles. Each CPU should get
            its own process to solve puzzles. Since solving puzzles is CPU
            bound, this represents the attacker's best strategy.
    '''

    def __init__(self, logger, cpu, prefix, suffix, regex_target, \
        stall, thread_id, regex_puzzle = r"/puzzle_static/puzzle\.js"):

        self.logger = logger
        self.cpu = cpu
        self.prefix = prefix
        self.suffix = suffix
        self.url = args.prefix + args.suffix
        self.regex_target = re.compile(regex_target)
        self.regex_puzzle = re.compile(regex_puzzle)
        self.stall = stall
        self.thread_id = thread_id
        threading.Thread.__init__(self)

    def request(self, url):
        '''Requests URL. If the response is a puzzle page returns the response;
        if the response is the target page returns None; else throws exception.
        Throws an exception if it is neither.'''

        self.logger.debug("%d Requesting %s", self.thread_id, url)
        try:
            response = urllib2.urlopen(url).read()
        except urllib2.HTTPError, e:
            self.logger.warning("%d %s", self.thread_id, e)
            return None
        except urllib2.URLError:
            self.logger.critical("%d Error: Could not access %s. Perhaps the server is not running.", self.thread_id, url)
            raise

        if self.regex_target.search(response):
            self.logger.debug("%d Received target response", self.thread_id)
            return None
        elif self.regex_puzzle.search(response):
            self.logger.debug("%d, Received puzzle response", self.thread_id)
            return response
        else:
            raise ValueError("%d Did not recognize response: %s ...", self.thread_id, response[:100])

    def run(self):
        x = 0
        while True:
            response = self.request(self.url)

            # If you are given a puzzle
            if response != None:
                # You can only compute the puzzle if there aren't already max number of puzzle threads
                if self.cpu.acquire(blocking = False):
                    self.logger.info("%d, Solving puzzle", self.thread_id)

                    # You now have permssion to use the CPU
                    solver = puzzle_solver.PuzzleSolver(response)

                    # cpu-intensive
                    keyed_suffix = solver.solve()

                    self.logger.info("%d, done with puzzle: %s", self.thread_id, keyed_suffix)
                    self.cpu.release()

                    keyed_url = self.prefix + keyed_suffix

                    # Send the puzzle solution to the server to effect high-density work
                    response = self.request(keyed_url)

                    # No need to sleep
                    continue

            time.sleep(self.stall)

if __name__ == "__main__":
    cwd = os.getcwd()

    parser = argparse.ArgumentParser(description='Tool used to test Doorman by attacking web-app. WARNING: this ' \
        'script does not have an off switch. To stop, use: pkill -f "python.* doorman_attack.py"')

    parser.add_argument("-p", "--prefix",  type=str, required=True,
                    help="the domain part of the URL to submit requests to; e.g. 'http://localhost'")
    parser.add_argument("-s", "--suffix",  type=str, required=True,
                    help="the rest of the url; e.g. '/index.php'")
    parser.add_argument("-r", "--regex",  type=str, required=True,
                    help="regular expression that positively matches the target web-app page, NOT the puzzle page, and NOT 403 pages or anything else; e.g. MediaWiki")
    parser.add_argument("-t", "--threads",  type=int, default=10,
                    help="Default=%(default)s. The total number of threads to run")
    parser.add_argument("-z", "--puzzle-threads",  type=int, default=1,
                    help="Default=%(default)s. The maximum number of threads allowed to work on puzzles at the same time")
    parser.add_argument("-st", "--stall",  type=float, default=0.2,
                    help="Default=%(default)s. The number of seconds to stall when needed")
    parser.add_argument("-i", "--id",  type=int, default=1,
                    help="Default=%(default)s. An id to identify this attacker in the logs")

    log.add_arguments(parser)
    args = parser.parse_args()
    logger = log.getLogger(args, name="doorman_attack.py.%d" % args.id)
    logger.info("Command line arguments: %s" % str(args))

    cpu = threading.BoundedSemaphore(value=args.puzzle_threads)

    for i in xrange(0, args.threads):
        logger.debug("Launching %d/%d", i + 1, args.threads)
        attacker = AttackerThread(logger, cpu, args.prefix, args.suffix, args.regex, args.stall, i + 1)
        attacker.start()

