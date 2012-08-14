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
# Generates a page action trace and a plain unique titles list from the supplied JSON
# requires the bundled trace_gen.py
#
# Usage: ./trace_and_list_gen.sh <json-pageview-count-file> [<trace-size>]
#
# Output: .trace and .titles files
#

JSON_FILE=$1
if [ -z "$JSON_FILE" ]; then
    echo "Usage: ./trace_and_list_gen.sh <json-pageview-count-file> [<trace-size>]"
    # JSON_FILE="./data/sample-pagecounts-input00.json" # test only, remove
    exit
fi
OUTPUT_TRACE_FILE=`echo $JSON_FILE | sed s'/.json$//'`".trace"
OUTPUT_LIST_FILE=`echo $JSON_FILE | sed s'/.json$//'`".titles"

TRACE_SIZE=$2
if [ -z "$TRACE_SIZE" ]; then
    TRACE_SIZE=10 # default if not provided
fi

./trace_gen.py $JSON_FILE $TRACE_SIZE 1 > $OUTPUT_TRACE_FILE

data=`cat $OUTPUT_TRACE_FILE | sed s'/.*\?title\=//g'`
data=`echo "$data" | sort | uniq`
echo "$data" > $OUTPUT_LIST_FILE

