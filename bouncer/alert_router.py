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
# ==== Alert Router ====
#
# For overview of functionality, see README.txt
#
# This daemon should probably run at a higher priority than web server,
# because the alerts need to get to the bouncers ASAP.
#
# ==== TODO ====
#   - Logging
#   - Timeouts on RPC calls
#   - To the extent possible, ensure that bouncers, alert_router, and nginx can be
#     started in any order (and at least give intelligent errors when an error
#     results from out-of-order startup)
#   - Consider keeping connections alive. Right now sendAlert creates, opens, and closes
#     a connection every time an alert needs to be sent, which will have higher
#     overhead than keeping the connections alive. If if alert_router.py doesn't acutally
#     keep the connections alive there are probably still ways to improve sendAlert

import sys
import os

dirname = os.path.dirname(os.path.realpath(__file__))

sys.path.append(os.path.join(dirname, 'gen-py'))

import import_thrift_lib

import time
import json
import traceback
from select import select

from BouncerService import BouncerService
from BouncerService.ttypes import *
from BouncerService.constants import *

from thrift import Thrift
from thrift.transport import TSocket
from thrift.transport import TTransport
from thrift.protocol import TBinaryProtocol

from bouncer_common import *

# Request a heartbeat every HEART_BEAT_PERIOD seconds
HEART_BEAT_PERIOD=60

class GetBouncerException(ValueError):
    pass

class AlertRouter:

    def __init__(self, config):
        self.config = config

    def requestHeartbeat(self):
        for bouncer in self.config.bouncer_list:
            try:
                transport = TSocket.TSocket(bouncer.addr, bouncer.port)
                transport = TTransport.TBufferedTransport(transport)
                protocol = TBinaryProtocol.TBinaryProtocol(transport)
                client = BouncerService.Client(protocol)

                transport.open()

                result = client.heartbeat()

                transport.close()

                if result == []:
                    print "Bouncer %s:%d heartbeat = OK" % (bouncer.addr, bouncer.port)
                elif result != self.config.bouncer_map[str(bouncer)]:
                    print "Error: the bouncer's configuration == %s does not match the " \
                        "alert_router's configuration == %s" % (result, self.config.bouncer_map[str(bouncer)])
                else:
                    print "Good: the bouncer's configuration and the alert_router's configuration match"

            except Thrift.TException, exception:
                print "ERROR while requesting heartbeat from Bouncer %s:%d --> %s" % (bouncer.addr, bouncer.port, exception)

    def sendAlert(self, bouncer, alert_message):
        # TODO catch remote exception

        try:
          transport = TSocket.TSocket(bouncer.addr, bouncer.port)
          transport = TTransport.TBufferedTransport(transport)
          protocol = TBinaryProtocol.TBinaryProtocol(transport)
          client = BouncerService.Client(protocol)

          transport.open()

          client.alert(alert_message)

          transport.close()

          print "Successfully sent alert '%s' to Bouncer '%s:%d'" % \
            (alert_message, bouncer.addr, bouncer.port)

        except BouncerException, e:
            print "Bouncer ERROR: %s" % e
            sys.stdout.flush()
        except Thrift.TException, e:
            print "Thrift exception: %s" % e
            sys.stdout.flush()


    def getBouncer(self, pipe_message):
        '''Returns a BoucerAddress object for bouncer that should receive the alert.
        Returns None if the pipe_message should be ignored.
        Throws a GetBouncerException exception if there is a problem.'''
        if pipe_message == "init":
            print "Ignoring 'init' pipe_message"
            return None
        else:
            if pipe_message in self.config.worker_map:
                return self.config.worker_map[pipe_message]
            else:
                raise GetBouncerException("Error: Received alert from pipe that I do not recognize '%s'" % pipe_message)

    def run(self):

        while True:
            try:
                print "Waiting for pipe to open"
                with open(self.config.alert_pipe) as alert_pipe:
                    print "Pipe opened"
                    self.requestHeartbeat()
                    while True:
                        print "Waiting for message"
                        rfds, _, _ = select( [alert_pipe], [], [], HEART_BEAT_PERIOD)
                        # if reading alert_pipe timed out
                        if len(rfds) == 0:
                            self.requestHeartbeat()
                        else:
                            print "Received message (or pipe closed)"
                            pipe_message = alert_pipe.readline()
                            if pipe_message == "":
                                print "Pipe closed"
                                break
                            else:
                                pipe_message = pipe_message.rstrip()
                                print 'Received from pipe: "%s"' % pipe_message
                                try:
                                    print "Getting bouncer"
                                    bouncer = self.getBouncer(pipe_message)
                                    print "Got bouncer"
                                except GetBouncerException, e:
                                    print "ERROR: %s" % e.message
                                    bouncer = None

                                if bouncer:
                                    print "Sending alert"
                                    self.sendAlert(bouncer, pipe_message)
                                    print "Sent alert"
                                else:
                                    print "Not sending alert"

            except Exception as e:
                traceback.print_exc()
                sys.stdout.flush()

def print_usage():
    print "Usage: %s [config_filename]" % sys.argv[0]
    print "View bouncer/bouncer_common.py for config-file format."
    print ""

if __name__ == "__main__":

    if len(sys.argv) == 2:
        config_filename = sys.argv[1]
        try:
            with open(config_filename) as f:
                config = Config(f)
        except IOError:
            print "Could not open config file %s" % config_filename
            sys.exit(1)
        except:
            print "Error while parsing config file. View %s for format of config." % sys.argv[0]
            print
            raise

        alert_router = AlertRouter(config)
        alert_router.run()

    else:
        print_usage()
        sys.exit(1)



