#!/usr/bin/env bash
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
# ==== doorman_legit.sh for mediawiki ====
#
# For usage see: ./doorman_legit.sh -h
#
# Example usage: ./doorman_legit.sh -s localhost -to 5 -t 20
#

# $DIR is the absolute path for the directory containing this bash script
DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
source $DIR/../env.sh
DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
source $DIR/env.sh
DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"

FILENAME_BASE=`echo "legit_$*" | sed 's/\s/_/g'`
TRACE_FILENAME="$DIR/results/$FILENAME_BASE.csv"
SUMMARY_FILENAME="$DIR/results/$FILENAME_BASE.json"
echo $TRACE_FILENAME

$DOORMAN_LEGIT --stderr off --trace-filename $TRACE_FILENAME --url "/index.php?title=Main_Page" --regex MediaWiki $* &
sleep $TEST_TIME
kill $!
cat $TRACE_FILENAME | $DOORMAN_ANALYZE > $SUMMARY_FILENAME

echo "done"

