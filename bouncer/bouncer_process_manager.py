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
#       I think the best way to do this is to spawn threads that wait on popen
#       on objects, then issue thrift RPC calls when the wait finishes
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
import threading

from bouncer_common import *

class StartWorkerFailed(Exception):
    pass

# TODO: Determine if popen objects are thread safe. As in, is it OK
# for one thread to do popen_obj.wait() while another does popen_obj.terminate() ?
class WorkerMonitor(threading.Thread):
    '''A thread that watches a worker process and sends workerTerminated
    message when the worker terminates.'''

    def __init__(self, popen_obj, bouncerAddr, worker):
        '''popen_obj is an instance of subprocess.Popen for the worker to be monitored.
        bouncerAddr is the BouncerAddress objcect for this bouncer.
        worker is a string like "127.0.0.1:9001".'''
        self.popen_obj = popen_obj
        self.bouncerAddr = bouncerAddr
        self.worker = worker
        super(WorkerMonitor, self).__init__()

    def sendMessage(self):
        print "Sending worker-terminated message for worker '%s' to bouncer" % self.worker
        try:
            transport = TSocket.TSocket(self.bouncerAddr.addr, self.bouncerAddr.port)
            transport = TTransport.TBufferedTransport(transport)
            protocol = TBinaryProtocol.TBinaryProtocol(transport)
            client = BouncerService.Client(protocol)

            transport.open()

            client.workerTerminated(self.worker)

            transport.close()

        except Thrift.TException, exception:
            print "ERROR while sending workerTerminated to Bouncer %s:%d --> %s" % (bouncer.addr, bouncer.port, exception)

    def run(self):
        print "Monitor launched for worker '%s'" % self.worker
        self.popen_obj.wait()
        print "Monitor for worker '%s': worker terminated" % self.worker
        self.sendMessage()

class BouncerProcessManager(object):
    '''The super class for bouncer process managers. Each web application requires its
    own logic for starting, killing, and checking the status of workers. Therefore
    each web application requires its own subclass of BouncerProcessManager
    that overrides the following methods:
        start_worker
        kill_worker
    Each of these methods accepts one parameter, worker, which is a string identifying
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

        # maps each worker string to the popen object for that worker process
        self.worker_popen_map = {}

        for worker in self.workers:
            try:
                addr, port = BouncerProcessManager.parse_worker(worker)
            except ValueError, e:
                raise StartWorkerFailed("Could not start worker '%s' because it is malformed" % worker)

            print "Trying to start worker: %s" % worker
            popen_obj = self.start_worker(addr, port)
            if (popen_obj == None):
                raise StartWorkerFailed("Could not start worker '%s' for unknown reason" % worker)

            self.worker_popen_map[worker] = popen_obj

            # Launch the WorkerMonitor thread for this worker
            WorkerMonitor(popen_obj, self.bouncerAddr, worker).start()

    def start_worker(self, addr, port):
        '''Must attempt to launch the specified worker. Should return the popen object for the new worker
        or None, if the worker couldn't be be launched for some reason.'''
        return None

    def kill_worker(self, addr, port, popen_obj):
        '''Must attempt to kill the specified worker. Does not return anything'''
        pass

    def alert(self, alert_message):
        print "Received alert '%s'" % alert_message
        worker = alert_message

        if worker not in self.workers:
            raise BouncerException("This bouncer is not configured to restart worker '%s'" % worker)
        try:
            addr, port = BouncerProcessManager.parse_worker(worker)
        except ValueError, e:
            raise BouncerException("Worker '%s' because is malformed" % worker)

        if worker not in self.worker_popen_map:
            raise BouncerException("Worker '%s' does not seem to be running (it's not in worker_popen_map)" % worker)

        popen_obj = self.worker_popen_map[worker]
        if popen_obj == None:
            raise BouncerException("Worker '%s' does not seem to be running (its popen_obj == None)" % worker)

        print "Killing worker '%s'" % worker
        self.kill_worker(addr, port, popen_obj)

        # No need to start worker manually; the WorkerMonitor thread for that worker
        # will detect that the worker was killed and will call workerTerminated, which
        # will then restart the worker

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

    def workerTerminated(self, worker):
        print "Received workerCrashed(%s) message" % worker
        try:
            addr, port = BouncerProcessManager.parse_worker(worker)
        except ValueError, e:
            print "Could not handle message because worker '%s' is malformed" % worker
            return
        print "Trying to start the worker"
        popen_obj = self.start_worker(addr, port)
        self.worker_popen_map[worker] = popen_obj
        if popen_obj != None:
            # Launch the WorkerMonitor thread for this worker
            WorkerMonitor(popen_obj, self.bouncerAddr, worker).start()
        else:
            print "Could not start the worker"

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

