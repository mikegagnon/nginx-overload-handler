#!/usr/bin/env python
#
# Copyright 2012 github.com/one10, Hellasec
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
# http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
#
################################################################################
#
# Generates a trace to simulate realistic Wikipedia traffic
# given input file with pageview counts/hour from wpdumps server in JSON format
#
# usage: ./trace_gen.py <wp-pageviewcount-json> <trace-size>
#

import json
import sys
import random
from variate import Variate

JSON_FILE = sys.argv[1]
TRACE_SIZE = int(sys.argv[2])

PROB_EDIT = 0.2
PROB_VIEW = 1 - 0.2
EDIT_STR = "EDIT"
VIEW_STR = "VIEW"
DELIM_STR = ", "
WP_PREFIX_URL = "http://bg2.hellasec.com/index.php?title="
DEBUG_PRINTOUT_FREQ = 10000
ENABLE_DEBUG_OUT = True
ENABLE_STATS = True

# def pick_rand(counts, sum_counts):
#    i = random.randint(0, sum_counts - 1)
#    for item, count in counts.items():
#        i -= count
#        if i < 0:
#            return item

if (ENABLE_DEBUG_OUT): sys.stderr.write("opening input json\n")
with open(JSON_FILE) as f:    
    master_counts = json.load(f)
# to track progress for large files
if (ENABLE_DEBUG_OUT): sys.stderr.write("opened input json\n")

# sum_counts = sum(master_counts.values())
counts = {}

trials = 1
trace_size = TRACE_SIZE
v = Variate(master_counts)

for j in range(0, trials):
    for i in range(0, trace_size):
        if (ENABLE_DEBUG_OUT):
            if (i % DEBUG_PRINTOUT_FREQ == 0): sys.stderr.write("picked %d\n" % (i))
        # item = pick_rand(master_counts, sum_counts)
        item = v.getRand()
        
        if (ENABLE_STATS):
            if item not in counts:
                counts[item] = 0
            counts[item] += 1

        if random.random() <= PROB_EDIT:
            print EDIT_STR + DELIM_STR + WP_PREFIX_URL + item
        else:
            print VIEW_STR + DELIM_STR + WP_PREFIX_URL + item

if (ENABLE_STATS):
    sys.stderr.write(json.dumps(counts, indent=2, sort_keys=True))

