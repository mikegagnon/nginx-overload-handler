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
# ==== sigservice.py ====
#

import bayes
import sys
import os
import argparse

import logging
import Queue

DIRNAME = os.path.dirname(os.path.realpath(__file__))
sys.path.append(os.path.join(DIRNAME, 'gen-py'))
sys.path.append(os.path.join(DIRNAME, '..', 'common'))

import log

import import_thrift_lib

from thrift.transport import TSocket
from thrift.transport import TTransport
from thrift.protocol import TBinaryProtocol
from thrift.server import TServer
from thrift.Thrift import TException

import log

class LearnThread(threading.Thread):

    def __init__(self, queue, max_sample_size, update_requests, min_delay, max_delay, logger):
        '''
        creates a new signature whenever it receives at least update_requests requests
        or max_delay seconds have passed since that last signature.
        At leat min_delay seconds must pass between signature generations
        '''
        threading.Thread.__init__(self)
        self.queue = queue
        self.max_sample_size = max_sample_size
        self.update_requests = update_requests
        self.min_delay = min_delay
        self.max_delay = max_delay
        self.logger = logger

    def run(self):
        last_update = time.time()
        self.evicted = []
        self.completed = []

        while True:
            num_new_samples = 0
            # read in a bunch of request_str's until its time to create a new signature
            while not (num_new_samples >= self.update_requests and (time.time() - last_update >= self.min_delay)):
                try:
                    timeout = self.max_delay - (time.time() - last_update)
                    category, request_str = self.queue.get(timeout=timeout)
                    self.logger.debug("Received sample: %s --> %s", category, request_str)
                    num_new_samples += 1
                    if category == "evicted":
                        self.evicted.append(self.tokenize(request_str))
                    if category == "completed":
                        self.completed.append(self.tokenize(request_str))
                    else:
                        self.logger.error("Unexpected message from queue: (%s, %s)", category, request_str)
                except Queue.Empty:
                    self.logger.info("update_time expired; time to build a new signature")
                    break

            self.evicted = self.evicted[-self.max_sample_size:]
            self.completed = self.completed[-self.max_sample_size:]


class SignatureService:

    def __init__(self, port, logger, update_requests, update_time):
        self.port = port
        self.logger = logger
        self.update_requests = update_requests
        self.update_time = update_time
        self.queue = Queue.Queue()

    def evicted(self, request_str):
        self.queue.put(("evicted", request_str))

    def completed(self, request_str):
        self.queue.put(("completed", request_str))

    def run(self):
        processor = SignatureService.Processor(self)
        transport = TSocket.TServerSocket(port=self.port)
        tfactory = TTransport.TBufferedTransportFactory()
        pfactory = TBinaryProtocol.TBinaryProtocolFactory()

        server = TServer.TThreadPoolServer(processor, transport, tfactory, pfactory)

        self.logger.info("Starting Signature Service on port %d" % self.port)
        server.serve()
        self.logger.info("finished")


