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

import hashlib
import time
import os
import sys
import argparse
import threading
import Queue
import re
import urllib2
import random

DIRNAME = os.path.dirname(os.path.realpath(__file__))
sys.path.append(os.path.join(DIRNAME, '..', 'common'))

import log

class PuzzleSolver:
    '''Emulates JavaScript puzzle as closely as possible.
    Useful for automated testing of Doorman without needing to
    use a browser'''

    expected_vals = {"request" : str, "args" : str, "y" : str,
        "trunc_x" : str, "bits" : int, "expire" : str, "burst_len" : int,
        "sleep_time" : int}

    exclude_vals = ["func"]

    def __init__(self, logger, puzzle_html):
        self.logger = logger
        try:
            val = PuzzleSolver.get_val(puzzle_html)
        except Exception:
            self.logger.error("While trying to parse: %s", puzzle_html)
            raise

        self.__dict__.update(val)

        if self.args != "":
           self.request += "?" + self.args

        # convert from ms to sec
        self.sleep_time = self.sleep_time / 1000.0

    @staticmethod
    def get_val(puzzle_html):
        '''Parses puzzle_html extracting variable values
        needd to solve the puzzle. Very dependendent upon
        the exact format of the puzzle'''

        val = {}

        # Assumes:
        #   (1) Every line that begins with var declares a variable we're
        #   interested in
        #   (2) The part of the line after var (and before an optional semi colon)
        #   contains the value we care about
        #   (3) Values are either strings (single or double quoted) or ints

        lines = puzzle_html.split("\n")
        for line in lines:
            line = line.replace("=", " = ", 1)
            parts = line.split()
            if len(parts) > 0 and parts[0] == "var":
                assert(len(parts) >= 4)
                assert(parts[2] == "=" )
                var_name = parts[1]
                var_value = parts[3].rstrip(";")

                if var_name in PuzzleSolver.exclude_vals:
                    continue

                # If this is a string variable
                if ((var_value[0] == "'" and var_value[-1] == "'") or \
                    (var_value[0] == "\"" and var_value[-1] == "\"")) and \
                    len(var_value) >= 2:
                    val[var_name] = var_value[1:-1]
                # Otherwise better be an integer variable
                else:
                    val[var_name] = int(var_value)

        for val_name, val_type in PuzzleSolver.expected_vals.items():
            assert(val_name in val)
            assert(isinstance(val[val_name], val_type))

        return val

    @staticmethod
    def inc_digit(c):
        if c == "9":
            return "a"
        elif (c == "f"):
            return "0"
        else:
            return chr(ord(c) + 1)

    @staticmethod
    def increment(x):
        i = len(x) - 1
        new_x = list(x)
        while True:
            old_digit = x[i]
            new_digit = PuzzleSolver.inc_digit(old_digit)
            new_x[i] = new_digit

            if new_digit == "0":
                carry = True
                i -= 1
            else:
                carry = False

            if i < 0:
                carry = False

            if not carry:
                break
        return "".join(new_x)

    def compose(self, key):
        if self.args == "":
            url = self.request + "?"
        else:
            url = self.request + "&"
        return url + "key=" + key + "&expire=" + self.expire

    def solve(self):
        '''Returns url with solution'''
        x = self.trunc_x
        for attempt in xrange(0, 2 ** self.bits):
            hash_x = hashlib.md5(x).hexdigest()
            if hash_x == self.y:
                return self.compose(x)
            x = PuzzleSolver.increment(x)
            if attempt % self.burst_len == 0:
                time.sleep(self.sleep_time)

        raise ValueError("Bad puzzle; exhausted possibilities")


class ClientThread(threading.Thread):
    '''A thread that represents a web client'''

    def __init__(self, logger, queue, cpu, prefix, suffix, regex_target, \
        stall, thread_id, stall_after_puzzle, regex_puzzle = r"/puzzle_static/puzzle\.js"):
        self.queue = queue
        self.logger = logger
        self.cpu = cpu
        self.prefix = prefix
        self.suffix = suffix
        self.url = prefix + suffix
        self.regex_target = re.compile(regex_target)
        self.regex_puzzle = re.compile(regex_puzzle)
        self.stall = stall
        self.thread_id = thread_id
        self.stall_after_puzzle = stall_after_puzzle
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

        time.sleep(random.uniform(0.0, 2.0))

        while True:
            before = time.time()
            response = self.request(self.url)
            now = time.time()
            latency = now - before

            # If you are given a puzzle
            # Should really check for 502 at this place
            if response == None:
                self.queue.put(("web-app", now, latency))
            else:
                self.queue.put(("give-puzzle", now, latency))

                # You can only compute the puzzle if there aren't already max number of puzzle threads
                if self.cpu.acquire(blocking = False):
                    self.logger.info("%d, Solving puzzle", self.thread_id)

                    # You now have permssion to use the CPU
                    solver = PuzzleSolver(self.logger, response)

                    # cpu-intensive
                    before = time.time()
                    keyed_suffix = solver.solve()
                    now = time.time()
                    latency = now - before
                    self.queue.put(("solve-puzzle", now, latency))

                    self.logger.info("%d, done with puzzle: %s", self.thread_id, keyed_suffix)
                    self.cpu.release()

                    keyed_url = self.prefix + keyed_suffix

                    # Send the puzzle solution to the server to effect high-density work
                    before = time.time()
                    response = self.request(keyed_url)
                    now = time.time()
                    latency = now - before
                    self.queue.put(("web-app", now, latency))

                    # No need to sleep
                    if not self.stall_after_puzzle:
                        continue

            time.sleep(self.stall)

class Monitor:

    def __init__(self, logger, queue, history_len):
        self.queue = queue
        self.logger = logger
        self.records = {}
        self.history_len = history_len

    def run(self):
        while True:
            event, timestamp, latency = self.queue.get()
            if event not in self.records:
                self.records[event] = []
            self.records[event].append(latency)
            for event, latencies in self.records.items():
                trunc = latencies[-self.history_len:]
                avg = float(sum(trunc)) / float(len(trunc))
                self.logger.info("avg %s latency: %f", event, avg)

if __name__ == "__main__":
    cwd = os.getcwd()

    parser = argparse.ArgumentParser(description='Solves Doorman puzzles. Solves puzzle given by stdin. Example usage: curl -s "http://localhost/index.php" | ./puzzle_solver.py | xargs -I REQ curl -s "http://localhostREQ"')

    parser.add_argument("-s", "--sleep-time",  type=float, default=None,
                    help="If specified, overrides the puzzles sleep time (num secs to sleep between bursts)")
    parser.add_argument("-b", "--burst_len",  type=int, default=None,
                    help="If specified, overrides the puzzles burst_len")

    log.add_arguments(parser, "CRITICAL", "CRITICAL")
    args = parser.parse_args()
    logger = log.getLogger(args)
    logger.info("Command line arguments: %s" % str(args))

    solver = PuzzleSolver(logger, sys.stdin.read())
    solver.sleep_time = args.sleep_time or solver.sleep_time
    solver.burst_len = args.burst_len or solver.burst_len
    print solver.solve()

