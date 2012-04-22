#!/usr/bin/env python
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
# ==== fcgi_worker_process.py ====
#
# A simple fastcgi worker for testing purposes
#
# Spawn: ./fcgi_worker_process.py [port_num]
#   where port_num is the port number the worker should listen on
#
# Three forms of web access:
#   (1) no parameters, i.e.:
#       curl -s http://localhost/test.py
#   (2) one sleep parameterl; i.e. url?sleep=5.0
#       which will cause the worker to sleep for 5.0 sec before responding. i.e.:
#       curl -s http://localhost/test.py?sleep=5.0
#   (3) one burn parameterl; i.e. url?burn=11
#       which will cause the worker to execute 11 slow for loops before responding. i.e.:
#       curl -s http://localhost/test.py?burn=11
#
# TODO: Deal with closed connections.
#     Found bug. Is it a bug in Flup? When you the client closes a long running request, the
#     request keeps running in the background (even though nginx closes the connection
#     to the backend worker).
#

from cgi import parse_qs, escape
import sys, os
import time

DIRNAME = os.path.dirname(os.path.realpath(__file__))

# FLUP_PATH must == FLUP_LOCAL_PATH as defined in ../dependencies/env.sh
FLUP_PATH  = os.path.join(DIRNAME, "..", "..", "dependencies", "downloads", "flup-1.0.2")

sys.path.append(FLUP_PATH)

from flup.server.fcgi_fork import WSGIServer

BURN_CONSTANT=10**4

def app(environ, start_response):
    try:
        start_response('200 OK', [('Content-Type', 'text/html')])
        response = []

        parameters = parse_qs(environ.get('QUERY_STRING', ''))
        if "sleep" in parameters:
            sec = float(escape(parameters['sleep'][0]))
            time.sleep(sec)
            response.append("Slept for %f sec. \n" % sec)
        if "burn" in parameters:
            burn = int(escape(parameters['burn'][0]))
            # perform computations on result, so that it can't
            # be compiled away.
            result = 1
            for i in range(1, burn + 1):
                result = (result + i) % (2**32)
                for j in range(1, BURN_CONSTANT + 1):
                    # keep the arithmetic in 32-bit ints
                    result = (result * j) % (2**32)
            response.append("Burned for %d loops, with result=%d. \n" % (burn, result))
        response.append('Oh hai! \n')
        return response
    except Exception as e:
        print "Unexpected error:", sys.exc_info()[0]
        print e
        raise

WSGIServer(app, bindAddress=("127.0.0.1", int(sys.argv[1])), maxSpare=1, maxChildren=1).run()
