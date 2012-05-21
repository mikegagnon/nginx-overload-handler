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
# ==== make_trial_trace.py ====
#
# Creates a an httperf-formated trace by interleaving a legit_trace.txt file
# (containing only "legitimate" requests) with attack attack_trace.txt file
#
# USAGE: ./make_trial_trace.py test_size num_tests legit_trace.txt attack_trace.txt
#
# creates a trace containing test_size * num_tests requests.
#   Requests are grouped by "tests". In each test there are
#   test_size-1 requests drawn from attack_trace.txt, followed by a request
#   drawn from attack_trace.txt
#

import sys

def make_trial_trace(test_size, num_tests, legit_filename, attack_filename,
    outfile):

    with open(legit_filename) as f:
        contents = f.read()
        legit = contents.split("\n\n")
        # get rid of empty strings
        legit = filter(None, legit)

    with open(attack_filename) as f:
        contents = f.read()
        attack = contents.split("\n\n")
        # get rid of empty strings
        attack = filter(None, attack)

    def itemgen(items):
        numitems = len(items)
        i = 0
        while True:
            yield items[i]
            i = (i + 1) % numitems

    legit_items = itemgen(legit)
    attack_items = itemgen(attack)

    for test_i in range(0, num_tests):
        for test_j in range(0, test_size - 1):
            outfile.write("%s\n\n" % attack_items.next())

        outfile.write("%s\n\n" % legit_items.next())

    for test_j in range(0, test_size - 1):
        outfile.write("%s\n\n" % attack_items.next())

if __name__ == "__main__":
    test_size = int(sys.argv[1])
    num_tests = int(sys.argv[2])
    legit_filename = sys.argv[3]
    attack_filename = sys.argv[4]
    outfile = sys.stdout
    make_trial_trace(test_size, num_tests, legit_filename, attack_filename, outfile)

