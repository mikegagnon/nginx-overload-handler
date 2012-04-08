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
# ==== Bouncer process manager (for dummy FastCGI app) ====
#
# See ../bouncer/bouncer_process_manager.py for more information
#
# ==== TODO ====
# - When the bouncer kills a flup worker, flup sends debug information as a response.
#   It needs to return a 502, or something else, or nothing.
#

import sys
import os
import subprocess

import time

dirname = os.path.dirname(os.path.realpath(__file__))

sys.path.append(os.path.join(dirname, '..', 'bouncer'))

import bouncer_process_manager
from bouncer_process_manager import BouncerProcessManager

DUMMY_FASTCGI_APP_PATH = os.path.join(dirname, 'fcgi_worker_process.py')

class BouncerForDummyFcgi(BouncerProcessManager):

    def __init__(self, config, addr, port):
        #BouncerProcessManager.init(self, config, addr, port)

        # TODO: kill any workers laying around for this bouncer
        #indexed by port of the worker
        self.worker_popen = {}
        super(BouncerForDummyFcgi, self).__init__(config, addr, port)

    def start_worker(self, addr, port):
        '''Must attempt to launch the specified worker. Does not return anything'''
        if port not in self.worker_popen:
            p = subprocess.Popen([DUMMY_FASTCGI_APP_PATH, str(port)])
            self.worker_popen[port] = p
        elif not self.is_worker_alive(addr, port):
            p = subprocess.Popen([DUMMY_FASTCGI_APP_PATH, str(port)])
            self.worker_popen[port] = p
        else:
            raise ValueError("worker %s:%d is already running" % (addr, port))

    def kill_worker(self, addr, port):
        '''Must attempt to kill the specified worker. Does not return anything'''
        if port in self.worker_popen:
            p = self.worker_popen[port]
            # TODO: graduate to p.kill() if terminate doesn't work
            p.terminate()
            # Give terminate some time to take effect
            time.sleep(0.25)
        else:
            raise ValueError("worker %s:%d isn't running" % (addr, port))

    def is_worker_alive(self, addr, port):
        '''Returns True if the worker is alive, and False otherwise'''
        if port in self.worker_popen:
            p = self.worker_popen[port]
            return_code = p.poll()
            if return_code == None:
                return True
            else:
                return False
        else:
            return False

bouncer_process_manager.main(BouncerForDummyFcgi)

