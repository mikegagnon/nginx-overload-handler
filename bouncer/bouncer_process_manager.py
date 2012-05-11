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
#

import sys
import os
import inspect
import logging

DIRNAME = os.path.dirname(os.path.realpath(__file__))

sys.path.append(os.path.join(DIRNAME, 'gen-py'))
sys.path.append(os.path.join(DIRNAME, '..', 'common'))

import log

import import_thrift_lib

from BouncerService import BouncerService
from BouncerService.ttypes import *

from thrift.transport import TSocket
from thrift.transport import TTransport
from thrift.protocol import TBinaryProtocol
from thrift.server import TServer
from thrift.Thrift import TException

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

    def __init__(self, popen_obj, bouncerAddr, worker, logger):
        '''popen_obj is an instance of subprocess.Popen for the worker to be monitored.
        bouncerAddr is the BouncerAddress objcect for this bouncer.
        worker is a string like "127.0.0.1:9001".'''
        self.popen_obj = popen_obj
        self.bouncerAddr = bouncerAddr
        self.worker = worker
        self.logger = logger
        super(WorkerMonitor, self).__init__()

    def sendMessage(self):
        self.logger.info("Sending worker-terminated message for worker '%s' to bouncer" % self.worker)
        try:
            transport = TSocket.TSocket(self.bouncerAddr.addr, self.bouncerAddr.port)
            transport = TTransport.TBufferedTransport(transport)
            protocol = TBinaryProtocol.TBinaryProtocol(transport)
            client = BouncerService.Client(protocol)

            transport.open()

            client.workerTerminated(self.worker)

            transport.close()

        except TException, exception:
            self.logger.error("Error while sending workerTerminated to Bouncer %s:%d --> %s" % (self.bouncerAddr.addr, self.bouncerAddr.port, exception))

    def run(self):
        self.logger.debug("Monitor launched for worker '%s'" % self.worker)
        self.popen_obj.wait()
        self.logger.info("Monitor for worker '%s': worker terminated" % self.worker)
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

    def __init__(self, config, addr, port, logger):
        self.logger = logger
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

            self.logger.info("Starting worker: %s" % worker)
            popen_obj = self.start_worker(addr, port)
            if (popen_obj == None):
                raise StartWorkerFailed("Could not start worker '%s' for unknown reason" % worker)

            self.worker_popen_map[worker] = popen_obj

            # Launch the WorkerMonitor thread for this worker
            WorkerMonitor(popen_obj, self.bouncerAddr, worker, self.logger).start()

    def start_worker(self, addr, port):
        '''Must attempt to launch the specified worker. Should return the popen object for the new worker
        or None, if the worker couldn't be be launched for some reason.'''
        return None

    def kill_worker(self, addr, port, popen_obj):
        '''Must attempt to kill the specified worker. Does not return anything'''
        pass

    def alert(self, alert_message):
        self.logger.info("Received alert '%s'" % alert_message)
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

        self.logger.info("Killing worker '%s'" % worker)
        self.kill_worker(addr, port, popen_obj)

        # No need to start worker manually; the WorkerMonitor thread for that worker
        # will detect that the worker was killed and will call workerTerminated, which
        # will then restart the worker

    def heartbeat(self):

        if self.receivedFirstHeartbeat:
            self.logger.debug("Received heartbeat")
            return []
        else:
            self.logger.info("Received first heartbeat")
            self.receivedFirstHeartbeat = True
            return self.workers

    def workerTerminated(self, worker):
        self.logger.info("Received workerCrashed(%s) message" % worker)
        try:
            addr, port = BouncerProcessManager.parse_worker(worker)
        except ValueError, e:
            self.logger.error("Could not handle message because worker '%s' is malformed" % worker)
            return
        self.logger.debug("Trying to start the worker")
        popen_obj = self.start_worker(addr, port)
        self.worker_popen_map[worker] = popen_obj
        if popen_obj != None:
            # Launch the WorkerMonitor thread for this worker
            WorkerMonitor(popen_obj, self.bouncerAddr, worker).start()
        else:
            self.logger.error("Could not start the worker")

    def run(self):
        processor = BouncerService.Processor(self)
        transport = TSocket.TServerSocket(port=self.bouncerAddr.port)
        tfactory = TTransport.TBufferedTransportFactory()
        pfactory = TBinaryProtocol.TBinaryProtocolFactory()

        server = TServer.TSimpleServer(processor, transport, tfactory, pfactory)

        self.logger.info("Starting Bouncer process manager on port %d" % self.bouncerAddr.port)
        server.serve()
        self.logger.info("finished")

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

    _,filename,_,_,_,_ = inspect.getouterframes(inspect.currentframe())[1]
    logname = os.path.basename(filename)

    logger = log.getLogger(stderr=logging.INFO, logfile=logging.INFO, name=logname)

    if not issubclass(BouncerSubclass, BouncerProcessManager):
        raise ValueError("The given class, %s, is not a subclass of BouncerProcessManager" % bouncerClass)

    if len(sys.argv) == 4:
        config_filename = sys.argv[1]
        addr = sys.argv[2]
        port = int(sys.argv[3])
        try:
            with open(config_filename) as f:
                config = Config(f)
            bpm = BouncerSubclass(config, addr, port, logger)
        except IOError:
            logger.critical("Could not open config file %s" % config_filename)
            sys.exit(1)
        except:
            logger.critical("Error while parsing config file. View bouncer/bouncer_common.py for format of config.")
            raise
        bpm.run()

    else:
        print_usage()
        sys.exit(1)

