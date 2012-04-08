#!/usr/bin/env python
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
# ==== Bouncer service ====
#
# Listens for alerts from AlertRouter, then kills (and restarts) the
# selected FastCGI worker
#
# ==== Build instructions ====
#
#

import sys
sys.path.append('gen-py')

# Thrift installed it's python library in this dir;
# however, this dir is not in python's path by default.
# TODO: Come up with a more principled way of getting the
# thrift library in the path
sys.path.append('/usr/lib/python2.7/site-packages/')

from BouncerService import BouncerService
from BouncerService.ttypes import *

from thrift.transport import TSocket
from thrift.transport import TTransport
from thrift.protocol import TBinaryProtocol
from thrift.server import TServer

import socket

class BouncerHandler:

    def __init__(self):
        self.log = {}

    def alert(self, alert_message):
        print "Received '%s'" % alert_message

  #def sayHello(self):
  #  print "sayHello()"
  #  return "say hello from " + socket.gethostbyname(socket.gethostname())
  #
  #def sayMsg(self, msg):
  #  print "sayMsg(" + msg + ")"
  #  return "say " + msg + " from " + socket.gethostbyname(socket.gethostname())

handler = BouncerHandler()
processor = BouncerService.Processor(handler)
transport = TSocket.TServerSocket(port=3001)
tfactory = TTransport.TBufferedTransportFactory()
pfactory = TBinaryProtocol.TBinaryProtocolFactory()

server = TServer.TSimpleServer(processor, transport, tfactory, pfactory)

print "Starting BouncerService server..."
server.serve()
print "finished"
