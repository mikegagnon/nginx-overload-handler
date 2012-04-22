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

import sys
import os
import subprocess

import time

dirname = os.path.dirname(os.path.realpath(__file__))

sys.path.append(os.path.join(dirname, '..', '..', 'bouncer'))

import bouncer_process_manager
from bouncer_process_manager import BouncerProcessManager

DUMMY_FASTCGI_APP_PATH = os.path.join(dirname, 'fcgi_worker_process.py')

class BouncerForDummyFcgi(BouncerProcessManager):

    def start_worker(self, addr, port):
        '''Must attempt to launch the specified worker. Should return the popen object for the new worker
           or None, if the worker couldn't be be launched for some reason.'''
        return subprocess.Popen([DUMMY_FASTCGI_APP_PATH, str(port)])

    def kill_worker(self, addr, port, popen_obj):
        '''Must attempt to kill the specified worker. Does not return anything'''
        # TODO: try terminate then graduate to kill if necessary
        # TODO: make sure to kill all children
        try:
            popen_obj.terminate()
        except OSError, e:
            print "Error while trying to kill '%s:%d': %s" % (addr, port, e)


bouncer_process_manager.main(BouncerForDummyFcgi)

