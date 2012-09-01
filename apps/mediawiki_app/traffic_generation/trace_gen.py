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
#
# usage: ./trace_gen.py NOUN_JSON_FILE VERB_JSON_FILE TRACE_SIZE
#
#!/usr/bin/python
import json
import sys
import random
from variate import Variate

NOUN_JSON_FILE = sys.argv[1]
VERB_JSON_FILE = sys.argv[2]
TRACE_SIZE = int(sys.argv[3])

SERVER_NAME="http://bg2.hellasec.com"

DEBUG_PRINTOUT_FREQ = 10000
ENABLE_DEBUG_OUT = True
# RUN_STATS_ONLY = True
RUN_STATS_ONLY = False
GENERATE_TITLES_FILE = True

if (ENABLE_DEBUG_OUT): sys.stderr.write("opening input json\n")
with open(NOUN_JSON_FILE) as f:    
    master_noun_counts = json.load(f)

# to track progress for large files
if (ENABLE_DEBUG_OUT): sys.stderr.write("opened input json\n")


if (GENERATE_TITLES_FILE):
    titles_file = open(NOUN_JSON_FILE + ".titles", "w"); 

# open verbs
with open(VERB_JSON_FILE) as f:    
    master_verb_counts = json.load(f)

# format verbs into a dict for variates
v_master_verb_counts = {}
needs_noun = []
master_verb_counts = master_verb_counts["verbs"]
for i in master_verb_counts:
    # given unicode floats, convert them into ints*1000
    v_master_verb_counts[i['urlPrefix']] = int(float(i['freq']) * 1000)
    if "needsNoun" in i:
        assert(i["needsNoun"] != "")
        needs_noun.append(i['urlPrefix'])

noun_counts = {}
verb_counts = {}

if (RUN_STATS_ONLY):
    trials = 100
else:
    trials = 1

trace_size = TRACE_SIZE
v_nouns = Variate(master_noun_counts)
v_verbs = Variate(v_master_verb_counts)

recorded_nouns = []
for j in range(0, trials):
    for i in range(0, trace_size):
        if (ENABLE_DEBUG_OUT):
            if ((i % DEBUG_PRINTOUT_FREQ == 0) and (j == 0) and (i != 0)):
                sys.stderr.write("picked %d\n" % (i))

        # pick verb
        verb = v_verbs.getRand()

        # pick noun
        noun = v_nouns.getRand()
        
        if (RUN_STATS_ONLY):
            if noun not in noun_counts:
                noun_counts[noun] = 0
            noun_counts[noun] += 1
            if verb not in verb_counts:
                verb_counts[verb] = 0
            verb_counts[verb] += 1

        # record noun as a title
        if (GENERATE_TITLES_FILE and noun not in recorded_nouns):
            titles_file.write(noun + "\n")
            recorded_nouns.append(noun)

        # main output:
        if not RUN_STATS_ONLY:
	        # print SERVER_NAME + verb + noun
	        if verb in needs_noun:
	            # print verb + " NEEDS A NOUN"
	            print SERVER_NAME + verb + noun
	        else:
	            # print verb + " DOES NOT NEED A  NOUN"
	            print SERVER_NAME + verb

if (RUN_STATS_ONLY):
#    sys.stderr.write(json.dumps(noun_counts, indent=2, sort_keys=True))
    print "************* v_master_verb_counts length: " + str(len(v_master_verb_counts))
    print v_master_verb_counts
    print "************* verb_counts length: " + str(len(verb_counts))
    sys.stderr.write(json.dumps(verb_counts, indent=2, sort_keys=True))
    print "************* master_noun_counts length: " + str(len(master_noun_counts))
    print master_noun_counts
    print "************* noun_counts length: " + str(len(noun_counts))
    sys.stderr.write(json.dumps(noun_counts, indent=2, sort_keys=True))

