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
import argparse

DIRNAME = os.path.dirname(os.path.realpath(__file__))

sys.path.append(os.path.join(DIRNAME, 'gen-py'))
sys.path.append(os.path.join(DIRNAME, '..', 'sig_service', 'gen-py'))
sys.path.append(os.path.join(DIRNAME, '..', 'common'))

import log
import import_thrift_lib
import logging

import time
import json
import traceback
from select import select

from BouncerService import BouncerService
from BouncerService.ttypes import *
from BouncerService.constants import *

from SignatureService import SignatureService
from SignatureService.ttypes import *
from SignatureService.constants import *


from thrift import Thrift
from thrift.transport import TSocket
from thrift.transport import TTransport
from thrift.protocol import TBinaryProtocol

import Queue
import threading
import time

from bouncer_common import *

# Request a heartbeat every HEART_BEAT_PERIOD seconds
HEART_BEAT_PERIOD=60

class GetBouncerException(ValueError):
    pass

class PipeReader(threading.Thread):

    def __init__(self, filename, queue, logger):
        threading.Thread.__init__(self)
        self.filename = filename
        self.queue = queue
        self.logger = logger

    def run(self):
        while True:
            try:
                self.logger.info("Waiting for pipe to open")
                with open(self.filename) as alert_pipe:
                    self.logger.debug("Pipe opened")
                    #self.requestHeartbeat()
                    while True:
                        self.logger.info("Waiting for message")
                        pipe_message = alert_pipe.readline()
                        if pipe_message == "":
                            self.logger.info("Pipe closed")
                            break
                        self.queue.put(pipe_message)


            except Exception as e:
                self.logger.exception("unexpected exception")
                time.sleep(1)


class AlertRouter:

    def __init__(self, config, logger):
        self.config = config
        self.logger = logger

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
                    self.logger.debug("Bouncer %s:%d heartbeat = OK" % (bouncer.addr, bouncer.port))
                elif result != self.config.bouncer_map[str(bouncer)]:
                    self.logger.error("Error: the bouncer's configuration == %s does not match the " \
                        "alert_router's configuration == %s" % (result, self.config.bouncer_map[str(bouncer)]))
                else:
                    self.logger.info("Good: the bouncer's configuration and the alert_router's configuration match")

            except Thrift.TException, exception:
                self.logger.error("Error while requesting heartbeat from Bouncer %s:%d --> %s" % (bouncer.addr, bouncer.port, exception))

    def sendAlert(self, bouncer, alert_message):
        try:
          transport = TSocket.TSocket(bouncer.addr, bouncer.port)
          transport = TTransport.TBufferedTransport(transport)
          protocol = TBinaryProtocol.TBinaryProtocol(transport)
          client = BouncerService.Client(protocol)

          transport.open()

          client.alert(alert_message)

          transport.close()

          self.logger.info("Successfully sent alert '%s' to Bouncer '%s:%d'" % \
            (alert_message, bouncer.addr, bouncer.port))

        except Thrift.TException, e:
            self.logger.error("Thrift exception: %s" % e)

    def sendNotice(self, category, request_str):
        if category != "evicted" and category != "completed":
            self.logger.error("Unsupported category: %s", category)
            return

        try:
          transport = TSocket.TSocket(self.config.sigservice["addr"], self.config.sigservice["port"])
          transport = TTransport.TBufferedTransport(transport)
          protocol = TBinaryProtocol.TBinaryProtocol(transport)
          client = SignatureService.Client(protocol)

          transport.open()

          if category == "evicted":
              client.evicted(request_str)
          elif category == "completed":
              client.completed(request_str)
          else:
              assert(False)

          transport.close()

          self.logger.info("Successfully sent %s notice '%s' to Signature service", category, request_str[:60])

        except Thrift.TException, e:
            self.logger.error("Thrift exception: %s" % e)

    def parseMessage(self, pipe_message):
        self.logger.debug("pipe_message=%s", pipe_message)
        if pipe_message == "init":
            self.logger.debug("Ignoring 'init' pipe_message")
            return "init", None
        elif pipe_message.startswith("evicted:"):
            return "evicted", pipe_message[8:]
        elif pipe_message.startswith("completed:"):
            return "completed", pipe_message[10:]
        else:
            if pipe_message in self.config.worker_map:
                return "bouncer", self.config.worker_map[pipe_message]
            else:
                raise GetBouncerException("Error: Received alert from pipe that I do not recognize '%s'" % pipe_message)

    def run(self):
        queue = Queue.Queue()
        pipereader = PipeReader(self.config.alert_pipe, queue, self.logger)
        pipereader.start()

        while True:
            try:
                pipe_message = queue.get(timeout=HEART_BEAT_PERIOD)
            except Queue.Empty:
                self.requestHeartbeat()
                continue

            pipe_message = pipe_message.rstrip()
            self.logger.debug('Received from pipe: "%s"' % pipe_message)
            try:
                self.logger.debug("Parsing message")
                message_type, message = self.parseMessage(pipe_message)
                self.logger.debug("Got message type = %s", message_type)
            except GetBouncerException, e:
                self.logger.error(e.message)
                message_type, message = None, None

            if message_type == "bouncer":
                bouncer = message
                self.logger.info("Sending alert")
                self.sendAlert(bouncer, pipe_message)
                self.logger.debug("Sent alert")
            elif message_type == "evicted" or message_type == "completed":
                if self.config.sigservice != None:
                    self.logger.info("Forwarding to sig service: %s", pipe_message[:40])
                    self.sendNotice(message_type, message)
                else:
                    self.logger.info("Ignoring sig-service notice: %s", pipe_message[:40])
            else:
                self.logger.debug("Ignoring message")

if __name__ == "__main__":

    cwd = os.getcwd()

    default_config = os.path.join(cwd, "bouncer_config.json")

    parser = argparse.ArgumentParser(description='Alert router')
    parser.add_argument("-c", "--config", type=str, default=default_config,
                        help="Default=%(default)s. The config file. See bouncer/bouncer_common.py for config-file format.")

    log.add_arguments(parser)
    args = parser.parse_args()
    logger = log.getLogger(args)
    logger.info("Command line arguments: %s" % str(args))

    try:
        with open(args.config, "r") as f:
            pass
    except:
        logger.critical("Error: could not open config file (%s)" % args.config)
        sys.exit(1)

    try:
        with open(args.config) as f:
            config = Config(f)
    except:
        print "Error while parsing config file. View %s for format of config." % sys.argv[0]
        print
        raise

    alert_router = AlertRouter(config, logger)
    alert_router.run()

