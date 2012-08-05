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
# without using threads

import hashlib
import re
import argparse

# requires 1.03b or higher, because it contains a critical bug fix for timeouts
import gevent
from gevent import Greenlet
from gevent import monkey
from gevent import queue as Queue

# convert std libary methods to use greenlets
monkey.patch_all()

#from gevent import httplib
from gevent import socket
import urllib2
from urllib2 import HTTPError
import time

import os
import sys

DIRNAME = os.path.dirname(os.path.realpath(__file__))
sys.path.append(os.path.join(DIRNAME, '..', 'common'))

import log
import random

TIMEOUT=10

# when you call urllib2.urlopen above, it doesn't actually issue a request.
# rather gevent, queue's it up and issues the request later.
# if the queue delay is long that it takes longer than TIMEOUT then the system is clogged
class GeventBacklogged(Exception):
    pass

class PuzzleTimeout(Exception):
    pass

class PuzzleSolver:
    '''Emulates JavaScript puzzle as closely as possible.
    Useful for automated testing of Doorman without needing to
    use a browser'''

    expected_vals = {"request" : str, "args" : str, "y" : str,
        "trunc_x" : str, "bits" : int, "expire" : str, "burst_len" : int,
        "sleep_time" : int}

    exclude_vals = ["func"]

    def __init__(self, logger, puzzle_html, timeout):
        self.logger = logger
        self.timeout = timeout
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
        self.start_time = time.time()
        x = self.trunc_x
        for attempt in xrange(0, 2 ** self.bits):
            hash_x = hashlib.md5(x).hexdigest()
            if hash_x == self.y:
                return self.compose(x)
            x = PuzzleSolver.increment(x)
            if attempt % self.burst_len == 0:
                elapsed_time = time.time() - self.start_time
                if elapsed_time > self.timeout:
                    raise PuzzleTimeout("Timed out after %.2f seconds" % elapsed_time)
                #gevent.sleep(self.sleep_time)
                gevent.sleep(10)

        raise ValueError("Bad puzzle; exhausted possibilities")


class ClientGreenlet(Greenlet):

    def __init__(self, logger, queue, server, urls, timeout, regex_target, \
        greenlet_id, concurrent_puzzles, puzzles_being_solved, regex_puzzle = r"/puzzle_static/puzzle\.js"):

        Greenlet.__init__(self)
        self.queue = queue
        self.logger = logger
        self.server = server
        self.urls = urls
        self.timeout = timeout
        self.regex_target = re.compile(regex_target)
        self.regex_puzzle = re.compile(regex_puzzle)
        self.greenlet_id = greenlet_id
        self.concurrent_puzzles = concurrent_puzzles
        self.puzzles_being_solved = puzzles_being_solved

    def request(self, url):

        self.logger.debug("%d Requesting %s", self.greenlet_id, url)

        before = time.time()
        try:
            response = urllib2.urlopen("http://%s%s" % (self.server, url), timeout=self.timeout)
        except socket.timeout:
            latency = time.time() - before
            return("timeout", None, None, latency)
        except HTTPError, e:
            latency = time.time() - before
            return ("%s" % e.code, None, None, latency)


        text = response.read()
        latency = time.time() - before
        if (latency > self.timeout):
            raise GeventBacklogged("this machine can't send requests that fast")

        if self.regex_target.search(text):
            self.logger.debug("%d Received target response", self.greenlet_id)
            return ("200", "target", None, latency)
        elif self.regex_puzzle.search(text):
            self.logger.debug("%d, Received puzzle response", self.greenlet_id)
            return ("200", "puzzle", text, latency)
        else:
            self.logger.error("%d Did not recognize response: %s ...", self.greenlet_id, text[:100])
            return ("200", "other", text, latency)
            #raise ValueError("%d Did not recognize response: %s ..." % (self.greenlet_id, text[:100]))

    def run(self):

        url = random.choice(self.urls)
        self.logger.debug("requesting %s", url)
        (status, category, response, latency) = self.request(url)
        now = time.time()


        if status != "200":
            self.queue.put((status, None, now, latency, None))
            return
        # If the web-app served a page
        elif category == "target":
            self.queue.put((status, "web-app", now, latency, None))
            return

        # If the doorman served a puzzle
        elif category == "puzzle":
            solver = PuzzleSolver(self.logger, response, self.timeout)
            self.queue.put((status, "give-puzzle", now, latency, solver.bits))

            if self.concurrent_puzzles > 0 and self.puzzles_being_solved[0] >= self.concurrent_puzzles:
                self.logger.debug("%d, Received %d-bit puzzle, but puzzle concurrency is maxed out", \
                    self.greenlet_id, solver.bits)
                return

            self.puzzles_being_solved[0] += 1

            self.logger.info("%d, Solving %d-bit puzzle", self.greenlet_id, solver.bits)

            # cpu_intensive
            before = time.time()
            success = True
            keyed_url = None
            try:
                keyed_url = solver.solve()
            except PuzzleTimeout:
                success = False

            self.puzzles_being_solved[0] -= 1

            now = time.time()
            latency = now - before

            if success:
                self.queue.put((None, "solve-puzzle", now, latency, solver.bits))
                self.logger.info("%d, done with %d-bit puzzle: %s", self.greenlet_id, solver.bits, keyed_url)
            else:
                self.queue.put((None, "solve-puzzle-timeout", now, latency, solver.bits))
                self.logger.info("%d, failed with %d-bit puzzle: %s", self.greenlet_id, solver.bits, keyed_url)
                return

            # re-send the request, this time with puzzle solution
            (status, response, latency) = self.request(keyed_url)

            if status != "200":
                self.queue.put((status, None, now, latency, None))
            elif response == None:
                self.queue.put((status, "web-app", now, latency, None))
            else:
                self.logger.error("%d expecting web-app page but received something else", self.greenlet_id)

class Monitor(Greenlet):

    def __init__(self, logger, queue, history_len, trace_filename):
        Greenlet.__init__(self)
        self.queue = queue
        self.logger = logger
        self.tracefile = open(trace_filename, 'w')

        # indexed by response type
        self.rec_dict = {}

        self.history_len = history_len

    def run(self):
        first_timestamp = None
        num_fail = 0.0
        num_success = 0.0
        while True:
            status, event, timestamp, latency, num_bits = self.queue.get()
            if first_timestamp == None:
                first_timestamp = timestamp - latency
            delta = timestamp - first_timestamp
            self.logger.debug("received (%s, %s, %s, %s)", status, event, delta, latency)

            # There 4 types of events:
            #   * give-puzzle: a web response from the server delivering a puzzle
            #   * web-app: a web response from the server delivering an application page
            #   * solve-puzzle: the client solving a puzzle
            #   * solve-puzzle-timeout: the client giving up with a puzzle
            #   * None: a non-valid web response (e.g. 502)
            #
            # If the event is an HTTP response from the server, then status
            #   is a the status code from the response. Other possible values:
            #   * None -- e.g. solve-puzzle events
            #   * timeout -- when the request for the server times out
            trace_record = "%s,%s,%s,%s,%s\n" % (status, event, delta, latency, num_bits)
            self.tracefile.write(trace_record)
            self.tracefile.flush()

            if event not in self.rec_dict:
                self.rec_dict[(status, event)] = []

            if event == "web-app":
                num_success += 1.0
            elif event == None or event == "solve-puzzle-timeout" or status == "timeout":
                num_fail += 1.0

            total = num_success + num_fail
            if total > 0.0:
                success_rate = num_success / total
                self.logger.info("success rate: %f == %d/%d", success_rate, num_success, total)

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
    parser.add_argument("-u", "--url",  type=str, default=None,
                    help="Default=%(default)s. the rest of the url (not including SERVER); e.g. '/index.php'")
    parser.add_argument("-f", "--url-file",  type=str, default=None,
                    help="Default=%(default)s. filename contains urls, one per line (not including SERVER); e.g. '/index.php'")
    parser.add_argument("-to", "--timeout",  type=float, default=default_timeout,
                    help="Default=%(default)s. Connections timeout after TIMEOUT seconds.")
    parser.add_argument("-r", "--regex",  type=str, required=True,
                    help="regular expression that positively matches the target web-app page, NOT the puzzle page, and NOT 403 pages or anything else; e.g. MediaWiki")
    parser.add_argument("-e", "--rate",  type=int, default=10,
                    help="Default=%(default)s. Number of requests per second")
    parser.add_argument("-d", "--duration",  type=int, default=5,
                    help="Default=%(default)s. Duration of trial in seconds.")
    parser.add_argument("-z", "--concurrent-puzzles",  type=int, default=default_puzzle_threads,
                    help="Default=%(default)s. The maximum number of clients allowed to work on puzzles at the same time. If CONCURRENT_PUZZLES <= 0, then CONCURRENT_PUZZLES will be set to infinity.")
    parser.add_argument("-i", "--id",  type=str, default=1,
                    help="Default=%(default)s. An id to identify this process in the logs")
    parser.add_argument("-y", "--history",  type=int, default=20,
                    help="Default=%(default)s. When displaying averages, only use the last HISTORY measurements.")
    parser.add_argument("-p", "--poisson", action="store_true", default=False,
                    help="Set this flag to issue requests as poisson process. Else, issue requests as a non-random process.")
    parser.add_argument("-a", "--trace-filename",  type=str, default= name + ".csv",
                    help = '''Default=%(default)s. Name of output tracefile. The output tracefile is
                        a CSV with one row per event. Each row has 4 fields: (1) status, (2) event,
                        (3) latency, (4) num_bits. For further explanation, see the source.''')

    log.add_arguments(parser)
    args = parser.parse_args()

    logger = log.getLogger(args, name="%s.%s" % (name, args.id))
    logger.info("Command line arguments: %s" % str(args))

    queue = Queue.Queue()

    if args.url_file:
        urls = []
        with open(args.url_file) as f:
            for line in f:
                urls.append(line.strip())
    elif args.url:
        urls = [args.url]
    else:
        logger.error("Missing --url or --url-file arguments")
        sys.exit(1)

    logger.info("urls = %s", urls)

    monitor = Monitor.spawn(logger, queue, args.history, args.trace_filename)

    jobs = []

    period = 1.0 / args.rate
    requests = args.rate * args.duration

    # the total amount of time this greenlet should have spent sleeping
    expected_duration = 0.0

    puzzles_being_solved = [0]

    start_time = time.time()
    for i in range(0, requests):
        job = ClientGreenlet.spawn(logger, queue, args.server, urls, args.timeout, \
                    args.regex, i + 1, args.concurrent_puzzles, puzzles_being_solved)
        jobs.append(job)
        if args.poisson:
            sleep_time = random.expovariate(1.0/period)
        else:
            sleep_time = period
        actual_duration = time.time() - start_time
        # If you overslept last time, then reduce your sleeptime now in order to catch up
        overslept = max(0, actual_duration - expected_duration)
        requested_sleep_time = max(0, sleep_time - overslept)
        expected_duration += sleep_time
        logger.debug("sleeping for %f sec before next request", requested_sleep_time)
	if requested_sleep_time > 0.0:
	        gevent.sleep(requested_sleep_time)

    # if actual_duration significantly longer than duration, then this process is too CPU bound
    # need to slow down the rate
    actual_duration = time.time() - start_time
    if actual_duration > (expected_duration * 1.05):
        logger.error("Actual duration (%f) significantly longer then specified duration (%f). Could not send requests " \
            "fast enough" % (actual_duration, expected_duration))
    else:
        logger.debug("Actual duration (%f) NOT significantly longer then specified duration (%f). Sent requests " \
            "fast enough" % (actual_duration, expected_duration))

    # could not get joinall to work
    for i in range(0, int(args.timeout) + 1):
        # get rid of all jobs that have finished
        jobs = filter(lambda j: not j.ready(), jobs)
        if len(jobs) == 0:
            break
        gevent.sleep(1)

    jobs = filter(lambda j: not j.ready(), jobs)
    if len(jobs) > 0:
        for job in jobs:
            job.kill(block=True, timeout=1)    
    monitor.kill()


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




