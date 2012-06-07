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

    def __init__(self, puzzle_html):
        val = PuzzleSolver.get_val(puzzle_html)
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

    solver = PuzzleSolver(sys.stdin.read())
    solver.sleep_time = args.sleep_time or solver.sleep_time
    solver.burst_len = args.burst_len or solver.burst_len
    print solver.solve()

