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
# ==== Bouncer process manager (superclass) ====
#
# Listens for alerts from the Alert Router, then kills (and restarts) the
# selected FastCGI worker.
#
# Bouncer process managers are necessarily application specific, somewhat.
#
# This module provides BouncerProcessManager, a super class which acts
# as the basis for application-specific bouncers. See the documentation for
# BouncerProcessManager for an explanation of what the subclass should do.
#
# This module also provides a helper function main(...) which takes
# a single argument, a specific subclass of BouncerProcessManager. This method
# parses the command line arguments, instantiates the subclass, and runs the
# server. See the documentation for main(...) for more details.
#
# ==== TODO ====
#   - The sublcass methods raise exceptions, the superclass should handle them
#   - Consider event handling models: threaded, event based, ...?
#   - monitor workers for unexpected crashes. Perhaps run a thread for each popen
#     object that waits on the popen and when an unxepcted crash occurs, enqueues
#     a message for the main event loop to handle.
#
import sys
import os

dirname = os.path.dirname(os.path.realpath(__file__))

sys.path.append(os.path.join(dirname, 'gen-py'))

import import_thrift_lib

from BouncerService import BouncerService
from BouncerService.ttypes import *

from thrift.transport import TSocket
from thrift.transport import TTransport
from thrift.protocol import TBinaryProtocol
from thrift.server import TServer

import socket

from bouncer_common import *

class StartWorkerFailed(Exception):
    pass

class BouncerProcessManager(object):
    '''The super class for bouncer process managers. Each web application requires its
    own logic for starting, killing, and checking the status of workers. Therefore
    each web application requires its own subclass of BouncerProcessManager
    that overrides the following methods:
        start_worker
        kill_worker
        is_worker_alive
    Each of these methods accepts one paramter, worker, which is a string identifying
    the worker to kill. The worker string is of the form '127.0.0.1:9001', i.e.
    'ip_addr:port'.

    The documentation for those methods, specifies they contract that implementations
    must fulfill.'''

    @staticmethod
    def parse_worker(worker):
        '''Takes a string such as 'ipaddr:port' and returns a 2-tuple (ipaddr, port)
        where ipaddr is a str and port is an int. Raises ValueError if parse fails'''
        parts = worker.split(':')
        if len(parts) != 2:
            raise ValueError("There should be exactly one : in '%s'" % worker)
        return (parts[0], int(parts[1]))

    def __init__(self, config, addr, port):
        self.config = config
        self.bouncerAddr = BouncerAddress(addr, port)
        if str(self.bouncerAddr) not in self.config.bouncer_map:
            raise BadConfig("This bouncer '%s' is not in the configuration" % str(self.bouncerAddr))
        self.workers = self.config.bouncer_map[str(self.bouncerAddr)]
        self.receivedFirstHeartbeat = False

        for worker in self.workers:
            try:
                addr, port = BouncerProcessManager.parse_worker(worker)
            except ValueError, e:
                raise StartWorkerFailed("Could not start worker '%s' because it is malformed" % worker)

            print "Starting worker: %s" % worker
            self.start_worker(addr, port)
            if not self.is_worker_alive(addr, port):
                raise StartWorkerFailed("Could not start worker '%s' for unknown reason" % worker)

    def start_worker(self, addr, port):
        '''Must attempt to launch the specified worker. Does not return anything'''
        pass

    def kill_worker(self, addr, port):
        '''Must attempt to kill the specified worker. Does not return anything'''
        pass

    def is_worker_alive(self, addr, port):
        '''Returns True if the worker is alive, and False otherwise'''
        return False

    def alert(self, alert_message):
        print "Received alert '%s'" % alert_message
        worker = alert_message

        if worker not in self.workers:
            raise BouncerException("This bouncer is not configured to restart worker '%s'" % worker)
        try:
            addr, port = BouncerProcessManager.parse_worker(worker)
        except ValueError, e:
            raise BouncerException("Worker '%s' because is malformed" % worker)

        print "Killing worker: %s" % worker
        self.kill_worker(addr, port)
        if self.is_worker_alive(addr, port):
            raise BouncerException("Tried to kill worker '%s', but could not kill worker" % worker)

        print "Restarting worker: %s" % worker
        self.start_worker(addr, port)
        if not self.is_worker_alive(addr, port):
            raise BouncerException("Killed worker '%s', but could not start worker" % worker)

        print "Restart successful for worker: %s" % worker

    def heartbeat(self):
        # TODO: modify heartbeat so that it returns a list of strings
        # The first heartbeat a Bouncer receives it sends its list
        # of workers, so the alert_router can veryify their configs
        # are in sync. Thereafter it just returns an empty list.

        if self.receivedFirstHeartbeat:
            print "Received heartbeat"
            return []
        else:
            print "Received first heartbeat"
            self.receivedFirstHeartbeat = True
            return self.workers

    def run(self):
        processor = BouncerService.Processor(self)
        transport = TSocket.TServerSocket(port=self.bouncerAddr.port)
        tfactory = TTransport.TBufferedTransportFactory()
        pfactory = TBinaryProtocol.TBinaryProtocolFactory()

        server = TServer.TSimpleServer(processor, transport, tfactory, pfactory)

        print "Starting Bouncer process manager on port %d" % self.bouncerAddr.port
        server.serve()
        print "finished"

def print_usage():
    print "Usage: %s [config_filename] [bouncer_ip_address] [bouncer_port]" % sys.argv[0]
    print "View bouncer/bouncer_common.py for config-file format."
    print ""

def main(BouncerSubclass):
    '''Within a module that defines a subclass for BouncerProcessManager, say FooSubclass,
    you can do this:
        if __init__ == "__main__":
            main(FooSubclass)
    which parses command line arguments, instantiates your sublcass, and runs its server.'''

    if not issubclass(BouncerSubclass, BouncerProcessManager):
        raise ValueError("The given class, %s, is not a subclass of BouncerProcessManager" % bouncerClass)

    if len(sys.argv) == 4:
        config_filename = sys.argv[1]
        addr = sys.argv[2]
        port = int(sys.argv[3])
        try:
            with open(config_filename) as f:
                config = Config(f)
            bpm = BouncerSubclass(config, addr, port)
        except IOError:
            print "Could not open config file %s" % config_filename
            sys.exit(1)
        except:
            print "Error while parsing config file. View bouncer/bouncer_common.py for format of config."
            print
            raise
        bpm.run()

    else:
        print_usage()
        sys.exit(1)

