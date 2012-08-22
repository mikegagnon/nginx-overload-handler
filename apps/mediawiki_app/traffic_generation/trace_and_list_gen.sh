#!/bin/bash
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
# A very simple wrapper around trace_gen.py
#
# Usage: ./trace_and_list_gen.sh <json-pageview-count-file> [<trace-size>]
#
# Output: .trace and .titles files
#

NOUNS_JSON=$1
VERBS_JSON="./data/verbs.json" # use the default checked-in one

if [ -z "$NOUNS_JSON" ]; then
    echo "Usage: ./trace_and_list_gen.sh <json-pageview-count-file> [<trace-size>]"
    exit
fi
OUTPUT_TRACE_FILE=`echo $NOUNS_JSON | sed s'/.json$//'`".trace"

TRACE_SIZE=$2
if [ -z "$TRACE_SIZE" ]; then
    TRACE_SIZE=12000 # default if not provided
fi

./trace_gen.py $NOUNS_JSON $VERBS_JSON $TRACE_SIZE 1 > $OUTPUT_TRACE_FILE
