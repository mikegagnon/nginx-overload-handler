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
# ==== test for bayesian classifiers ====
#
# compiles to python stubs located in gen-py
#
# USAGE: ./test.sh
# On success emits no output
# On fail prints the diff between expected results and actual results

# $DIR is the absolute path for the directory containing this bash script
DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"

$DIR/../compile.sh

OUTPUT_FILE="$DIR/test_output/test_output.txt"
MODEL_FILE="$DIR/test_output/model.txt"
$DIR/../bayes.py -p $DIR/sample_positive_train.txt -n $DIR/sample_negative_train.txt -l -o model > $MODEL_FILE

rm -f $OUTPUT_FILE

while read line; do
    PY_RESULT=`$DIR/../bayes.py -p $DIR/sample_positive_train.txt -n $DIR/sample_negative_train.txt -l -o classify -c "$line"`
    C_RESULT=`$DIR/../bayes_test $MODEL_FILE "$line"`
    if [ "$PY_RESULT" == "$C_RESULT" ]
    then
        echo "match $PY_RESULT" >> $OUTPUT_FILE
    else
        echo "error: py=$PY_RESULT, c=$C_RESULT, for line='$line'" >> $OUTPUT_FILE
    fi
done < $DIR/sample_test.txt

diff -u $DIR/expected_results.txt $OUTPUT_FILE
