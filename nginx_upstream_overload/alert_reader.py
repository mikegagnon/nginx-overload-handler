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
# ==== alert_reader.py ====
#
# Continuously reads a named pipe, re-openeing the pipe as necessary.
#
# To read the upstream_overload alert_pipe:
#   ./alert_reader.py /home/nginx_user/alert_pipe
#

import sys
import time

def run(alert_pipe_path):

    while True:
        try:
            print "Waiting for pipe to open"
            with open(alert_pipe_path) as alert_pipe:
                print "Pipe opened"
                while True:
                    print "Waiting for message"
                    line = alert_pipe.readline()
                    if line == "":
                        print "Pipe closed"
                        break
                    else:
                        print '"%s"' % line.rstrip()
        except Exception as e:
            print e
            sys.stdout.flush()
            time.sleep(1)

if __name__ == "__main__":
    run(sys.argv[1])

