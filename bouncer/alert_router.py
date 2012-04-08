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
# ==== Example config ====
#
# {
#    "alert_pipe" : "/home/nginx_user/alert_pipe"
#    "bouncers" : [
#       {
#           "bouncer_addr" : "10.51.23.65",
#           "bouncer_port" : 10012,
#           "fcgi_workers" : [
#               "10.51.23.65:9000",
#               "10.51.23.65:9001",
#               "10.51.23.65:9002"
#               ]
#       },
#       {
#           "bouncer_addr" : "10.51.23.66",
#           "bouncer_port" : 10014,
#           "fcgi_workers" : [
#               "10.51.23.66:9010",
#               "10.51.23.66:9011"
#               ]
#       }
#    ]
# }
#
# In this configuration:
#   - the alert_router receives alerts by reading meassges from
#     /home/www/pipes/alert_pipe
#   - there are 5 FastCGI workers spread over two machines:
#       - 10.51.23.65
#       - 10.51.23.66.
#   - If the load balancer generates an alert for "10.51.23.65:9000",
#     "10.51.23.65:9001", or "10.51.23.65:9002" then alert_router will send an
#     alert to the bouncer daemon on 10.51.23.65, which is listening on port
#     10012.
#   - And so on for the bouncer on .66
#
# ==== TODO ====
#   - Logging
#   - Consider keeping connections alive. Right now sendAlert creates, opens, and closes
#     a connection every time an alert needs to be sent, which will have higher
#     overhead than keeping the connections alive. If if alert_router.py doesn't acutally
#     keep the connections alive there are probably still ways to improve sendAlert

import sys
sys.path.append('gen-py')

import import_thrift_lib

import time
import json
from select import select

from BouncerService import BouncerService
from BouncerService.ttypes import *
from BouncerService.constants import *

from thrift import Thrift
from thrift.transport import TSocket
from thrift.transport import TTransport
from thrift.protocol import TBinaryProtocol

# Request a heartbeat every HEART_BEAT_PERIOD seconds
HEART_BEAT_PERIOD=60

class BadConfig(ValueError):
    pass

class BouncerAddress:

    def __init__(self, addr, port):
        self.addr = addr
        self.port = port

    def __str__(self):
        return "%s:%d" % (self.addr, self.port)

class Config:

    def __init__(self, json_config):
        '''sets:
        self.alert_pipe to the path of alert_pipe.
        self.worker_map which is a dict that maps every FCGI worker string.
        self.bouncer_list which is a list of all BouncerAddress objects.'''

        self.worker_map = {}
        self.bouncer_list = []

        if "alert_pipe" not in json_config:
            raise BadConfig("alert_pipe is not defined")
        self.alert_pipe = str(json_config["alert_pipe"])

        if "bouncers" not in json_config:
            raise BadConfig("bouncers is not defined")
        bouncers = json_config["bouncers"]

        for bouncer in bouncers:
            bouncer_addr = bouncer["bouncer_addr"]
            bouncer_port = int(bouncer["bouncer_port"])
            fcgi_workers = bouncer["fcgi_workers"]

            bouncer_obj = BouncerAddress(bouncer_addr, bouncer_port)
            self.bouncer_list.append(bouncer_obj)
            for worker in fcgi_workers:
                worker = str(worker)
                if worker in self.worker_map:
                    raise BadConfig("Same fcgi worker appears more than once")
                self.worker_map[worker] = bouncer_obj

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

                print "Bouncer %s:%d heartbeat = %s" % \
                    (bouncer.addr, bouncer.port, result)

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

        except Thrift.TException, exception:
          print exception.message


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
                    while True:
                        print "Waiting for message"
                        rfds, _, _ = select( [alert_pipe], [], [], HEART_BEAT_PERIOD)
                        # if reading alert_pipe timed out
                        if len(rfds) == 0:
                            self.requestHeartbeat()
                        else:
                            print "Something else"
                            pipe_message = alert_pipe.readline()
                            if pipe_message == "":
                                print "Pipe closed"
                                break
                            else:
                                pipe_message = pipe_message.rstrip()
                                print 'Received from pipe: "%s"' % pipe_message
                                try:
                                    bouncer = self.getBouncer(pipe_message)
                                except GetBouncerException, e:
                                    print e.message
                                    bouncer = None

                                if bouncer:
                                    self.sendAlert(bouncer, pipe_message)

            except Exception as e:
                print e
                sys.stdout.flush()
                time.sleep(1)

def print_usage():
    print "Usage: %s [config_filename]" % sys.argv[0]
    print "View %s for config-file format." % sys.argv[0]
    print ""

if __name__ == "__main__":

    if len(sys.argv) == 2:
        config_filename = sys.argv[1]
        try:
            with open(config_filename) as f:
                json_config = json.load(f)
            config = Config(json_config)
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



