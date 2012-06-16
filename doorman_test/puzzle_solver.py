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
import socket
import time
import os
import sys
import argparse
import threading
import Queue
import re
#import urllib2
import httplib
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

    def __init__(self, logger, queue, cpu, server, url, timeout, regex_target, \
        stall, thread_id, stall_after_puzzle, regex_puzzle = r"/puzzle_static/puzzle\.js"):
        self.queue = queue
        self.logger = logger
        self.cpu = cpu
        self.server = server
        self.url = url
        self.timeout = timeout
        self.regex_target = re.compile(regex_target)
        self.regex_puzzle = re.compile(regex_puzzle)
        self.stall = stall
        self.thread_id = thread_id
        self.stall_after_puzzle = stall_after_puzzle
        threading.Thread.__init__(self)

    def request(self, url):

        self.logger.debug("%d Requesting %s", self.thread_id, url)
        conn = httplib.HTTPConnection(self.server, timeout=self.timeout)
        conn.request("GET", url)
        try:
            response = conn.getresponse()
        except socket.timeout:
            return("timeout", None)

        if response.status != 200:
            return ("%s" % response.status, None)
        text = response.read()

        if self.regex_target.search(text):
            self.logger.debug("%d Received target response", self.thread_id)
            return ("200", None)
        elif self.regex_puzzle.search(text):
            self.logger.debug("%d, Received puzzle response", self.thread_id)
            return ("200", text)
        else:
            raise ValueError("%d Did not recognize response: %s ...", self.thread_id, text[:100])

    def run(self):

        time.sleep(random.uniform(0.0, 2.0))

        while True:
            before = time.time()
            (status, response) = self.request(self.url)
            now = time.time()
            latency = now - before

            if status != "200":
                self.queue.put((status, None, now, latency, None))

            # If the web-app served a page
            elif response == None:
                self.queue.put((status, "web-app", now, latency, None))
            # If the doorman served a puzzle
            else:
                solver = PuzzleSolver(self.logger, response)
                self.queue.put((status, "give-puzzle", now, latency, solver.bits))

                # You can only compute the puzzle if there aren't already max number of puzzle threads
                if self.cpu.acquire(blocking = False):
                    # You now have permssion to use the CPU

                    self.logger.info("%d, Solving %d-bit puzzle", self.thread_id, solver.bits)

                    # cpu-intensive
                    before = time.time()
                    keyed_url = solver.solve()
                    now = time.time()
                    latency = now - before
                    self.queue.put((None, "solve-puzzle", now, latency, solver.bits))

                    self.logger.info("%d, done with %d-bit puzzle: %s", self.thread_id, solver.bits, keyed_url)
                    self.cpu.release()

                    # Send the puzzle solution to the server to effect high-density work
                    before = time.time()
                    (status, response) = self.request(keyed_url)
                    now = time.time()
                    latency = now - before
                    #self.queue.put((status, "web-app", now, latency, None))

                    if status != "200":
                        self.queue.put((status, None, now, latency, None))
                    elif response == None:
                        self.queue.put((status, "web-app", now, latency, None))
                    else:
                        self.logger.error("%d expecting web-app page but received something else", self.thread_id)
                        self.queue.put((status, "error", now, latency, None))

                    # No need to sleep
                    if not self.stall_after_puzzle:
                        continue

            time.sleep(self.stall)

class Monitor(threading.Thread):

    def __init__(self, logger, queue, history_len, trace_filename):
        self.queue = queue
        self.logger = logger
        self.tracefile = open(trace_filename, 'w')

        # indexed by response type
        self.rec_dict = {}

        # List of events excluding puzzle events
        self.web_app_events = []

        self.history_len = history_len
        threading.Thread.__init__(self)

    def run(self):
        first_timestamp = None
        while True:
            status, event, timestamp, latency, num_bits = self.queue.get()
            if first_timestamp == None:
                first_timestamp = timestamp - latency
            delta = timestamp - first_timestamp
            self.logger.debug("received (%s, %s, %s, %s)", status, event, delta, latency)

            trace_record = "%s,%s,%s,%s,%s," % (status, event, delta, latency, num_bits)
            if status != None and (status != "200" or event == "web-app"):
                self.web_app_events.append((status, event))
                trace_record += "web-app,"
            else:
                trace_record += "%s," % None


            if event not in self.rec_dict:
                self.rec_dict[(status, event)] = []

            recent_events = self.web_app_events[-self.history_len:]
            if len(recent_events) > 0:
                success_events = filter(lambda x: x[0] == "200", recent_events)
                num_events = len(recent_events)
                num_success = len(success_events)
                success_rate = float(num_success) / float(num_events)
                self.logger.info("success rate: %f == %d/%d", success_rate, num_success, num_events)
                trace_record += "%f\n" % success_rate
                self.tracefile.write(trace_record)
                self.tracefile.flush()


            self.rec_dict[(status, event)].append(latency)
            for (status, event), latencies in self.rec_dict.items():
                trunc = latencies[-self.history_len:]
                avg = float(sum(trunc)) / float(len(trunc))
                self.logger.info("avg (%s, %s) latency: %f", status, event, avg)

def run_client(name, desc, default_puzzle_threads, default_timeout, stall_after_puzzle):

    desc += " WARNING: this script does not have an off switch. You must forcefully kill it with someting like " + \
        "pkill -f 'python.*%s'" % name

    cwd = os.getcwd()

    parser = argparse.ArgumentParser(description=desc)

    parser.add_argument("-s", "--server",  type=str, required=True,
                    help="the domain part of the URL to submit requests to; e.g. 'localhost'")
    parser.add_argument("-u", "--url",  type=str, required=True,
                    help="the rest of the url (not including SERVER); e.g. '/index.php'")
    parser.add_argument("-to", "--timeout",  type=float, default=default_timeout,
                    help="Default=%(default)s. Connections timeout after TIMEOUT seconds.")
    parser.add_argument("-r", "--regex",  type=str, required=True,
                    help="regular expression that positively matches the target web-app page, NOT the puzzle page, and NOT 403 pages or anything else; e.g. MediaWiki")
    parser.add_argument("-t", "--threads",  type=int, default=10,
                    help="Default=%(default)s. The total number of threads to run")
    parser.add_argument("-z", "--puzzle-threads",  type=int, default=default_puzzle_threads,
                    help="Default=%(default)s. The maximum number of threads allowed to work on puzzles at the same time. If PUZZLE_THREADS <= 0, then PUZZLE_THREADS will be set to THREADS.")
    parser.add_argument("-st", "--stall",  type=float, default=0.2,
                    help="Default=%(default)s. The number of seconds to stall when needed")
    parser.add_argument("-i", "--id",  type=int, default=1,
                    help="Default=%(default)s. An id to identify this attacker in the logs")
    parser.add_argument("-y", "--history",  type=int, default=20,
                    help="Default=%(default)s. When displaying averages, only use the last HISTORY measurements.")
    parser.add_argument("-a", "--trace-filename",  type=str, default= name + ".csv",
                    help="Default=%(default)s. Name of output tracefile")

    log.add_arguments(parser)
    args = parser.parse_args()

    if args.puzzle_threads <= 0:
        args.puzzle_threads = args.threads

    logger = log.getLogger(args, name="%s.%d" % (name, args.id))
    logger.info("Command line arguments: %s" % str(args))

    # By settings bounded-value == #threads, it means every thread can work on puzzles
    # at the same time. This only makes sense when the puzzles aren't CPU bound
    cpu = threading.BoundedSemaphore(value=args.puzzle_threads)

    queue = Queue.Queue()

    for i in xrange(0, args.threads):
        logger.debug("Launching %d/%d", i + 1, args.threads)
        legit = ClientThread(logger, queue, cpu, args.server, args.url, args.timeout, \
            args.regex, args.stall, i + 1, stall_after_puzzle)
        legit.start()

    monitor = Monitor(logger, queue, args.history, args.trace_filename)
    monitor.start()

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

