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
# For testing only - the real legit+attack traffic gen should be done by puzzle_sover
# reads in a WP trace file, visits/posts MW pages according to it
#
# Usage example:
# ./test_run_trace.py ./data/pagecounts-20120301-040000.trace
#
# Update VIEW_URL_PREFIX with a proper MW server name
#

import httplib
import socket
import sys
import re
import postToMW
import time

SERVER = "localhost"
VIEW_URL_PREFIX = "http://"+ SERVER +"/index.php?title="
EDIT_STR = "EDIT"
VIEW_STR = "VIEW"
DELIM_STR = ", "
TIMEOUT = 20

with open(sys.argv[1], 'r') as f:
    trace = f.readlines()

for i in trace:
    i = i.strip()
    is_view = re.search(r'^' + VIEW_STR + DELIM_STR, i)

    time.sleep(1) # just in case - supposedly, we control the local MW anyway

    if is_view:
        print "VIEW:" + i
        title = i.replace(VIEW_STR + DELIM_STR, "", 1)
        url = VIEW_URL_PREFIX + title
        try:
            conn = httplib.HTTPConnection(SERVER, timeout=TIMEOUT)
            conn.request("GET", url)
            response = conn.getresponse()
            if response.status != 200:
                print ("error connecting: %s" % response.status, None)
            # text = response.read()
        except socket.timeout:
            print ("timeout connecting")
     
    # TODO: assuming if not view, then edit, may have more in the future
    else:
        title = i.replace(EDIT_STR + DELIM_STR, "", 1)
        print "EDIT:" + title
        postToMW.postToMW(title, "new test text " + time.asctime(time.localtime(time.time())))
