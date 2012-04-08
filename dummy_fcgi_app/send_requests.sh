#!/usr/bin/env bash
#
# Copyright 2012 HellaSec, LLC
#
#  Licensed under the Apache License, Version 2.0 (the "License");
#  you may not use this file except in compliance with the License.
#  You may obCONFIG_INSTALLED_BACKUPtain a copy of the License at
#
#      http://www.apache.org/licenses/LICENSE-2.0
#
#  Unless required by applicable law or agreed to in writing, software
#  distributed under the License is distributed on an "AS IS" BASIS,
#  WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
#  See the License for the specific language governing permissions and
#  limitations under the License.
#

function big_request {
    curl -s http://localhost/test.py?sleep=5 > /dev/null &
}

function quick_request {
    curl -s http://localhost/test.py > /dev/null &
}

echo "Big request goes to 9000"
big_request

echo "Big request goes to 9001"
big_request

echo "Big request goes to 9002, AND an alert is sent out for 127.0.0.1:9000"
big_request

echo "Big request goes to 9003, AND an alert is sent out for 127.0.0.1:9000"
big_request

echo "Big request is rejected, AND an alert is sent out for 127.0.0.1:9000"
big_request

echo "Give big requests some time to finish (sleep for 6 seconds)"
sleep 6

echo "Quick request goes to 9000 (finishes quickly)"
quick_request

echo "Quick request goes to 9001 (finishes quickly)"
quick_request

echo "Give quick requests some time to finish (sleep for 6 seconds)"
sleep 1

echo "Big request goes to 9002"
big_request

echo "Big request goes to 9003"
big_request

echo "Big request goes to 9000, AND an alert is sent out for 127.0.0.1:9002"
big_request

echo "Big request goes to 9001, AND an alert is sent out for 127.0.0.1:9002"
big_request

echo "Big request is rejected, AND an alert is sent out for 127.0.0.1:9002"
big_request

