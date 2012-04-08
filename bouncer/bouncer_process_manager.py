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
# ==== Bouncer process manager ====
#
# Listens for alerts from AlertRouter, then kills (and restarts) the
# selected FastCGI worker
#
# ==== Build instructions ====
#
#

import sys
sys.path.append('gen-py')

import import_thrift_lib

from BouncerService import BouncerService
from BouncerService.ttypes import *

from thrift.transport import TSocket
from thrift.transport import TTransport
from thrift.protocol import TBinaryProtocol
from thrift.server import TServer

import socket

class BouncerProcessManager:

    def __init__(self):
        pass

    def alert(self, alert_message):
        print "Received alert '%s'" % alert_message

    def heartbeat(self):
        print "Received heartbeat request"
        return "OK"

bpm = BouncerProcessManager()
processor = BouncerService.Processor(bpm)
transport = TSocket.TServerSocket(port=3001)
tfactory = TTransport.TBufferedTransportFactory()
pfactory = TBinaryProtocol.TBinaryProtocolFactory()

server = TServer.TSimpleServer(processor, transport, tfactory, pfactory)

print "Starting Bouncer process manager "
server.serve()
print "finished"
