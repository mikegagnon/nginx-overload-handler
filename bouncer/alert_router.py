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
# ==== Build instructions ====
#

import sys
sys.path.append('gen-py')
sys.path.append('/usr/lib/python2.7/site-packages/')

from BouncerService import BouncerService
from BouncerService.ttypes import *
from BouncerService.constants import *

from thrift import Thrift
from thrift.transport import TSocket
from thrift.transport import TTransport
from thrift.protocol import TBinaryProtocol

try:
  transport = TSocket.TSocket('localhost', 3001)
  transport = TTransport.TBufferedTransport(transport)
  protocol = TBinaryProtocol.TBinaryProtocol(transport)
  client = BouncerService.Client(protocol)

  transport.open()

  print client.heartbeat()
  client.alert("test alert 1")
  print client.heartbeat()
  client.alert("test alert 2")

  transport.close()

except Thrift.TException, exception:
  print exception.message

