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
from string import Template

dirname = os.path.dirname(os.path.realpath(__file__))

sys.path.append(os.path.join(dirname, '..', 'bouncer'))

import bouncer_process_manager
from bouncer_process_manager import BouncerProcessManager

SPAWN_FCGI_ARGS = {
        'php_user' : "www-data",
        'php_group' : "www-data",
        'php_bin' : "/usr/bin/php5-cgi"
    }

PHP_FCGI_CMD_TEMPLATE_STR = Template('/usr/bin/spawn-fcgi -n -a $addr -p $port ' \
    '-u $php_user -g $php_group $php_bin').safe_substitute(SPAWN_FCGI_ARGS)

print "PHP_FCGI_CMD_TEMPLATE_STR='%s'" % PHP_FCGI_CMD_TEMPLATE_STR

class BouncerForPhp(BouncerProcessManager):

    def start_worker(self, addr, port):
        '''Must attempt to launch the specified worker. Should return the popen object for the new worker
           or None, if the worker couldn't be be launched for some reason.'''
        cmd_str = Template(PHP_FCGI_CMD_TEMPLATE_STR).substitute( \
                addr = addr, \
                port = str(port) \
            )
        print "cmd_str='%s'" % cmd_str
        cmd = cmd_str.split()
        return subprocess.Popen(cmd)

    def kill_worker(self, addr, port, popen_obj):
        '''Must attempt to kill the specified worker. Does not return anything'''
        #worker = "%s:%d" % (addr, port)
        try:
            popen_obj.terminate()
        except OSError, e:
            print "Error while trying to kill '%s:%d': %s" % (addr, port, e)
        #if port in self.worker_popen:
        #    p = self.worker_popen[port]
        #    # TODO: graduate to p.kill() if terminate doesn't work
        #    p.terminate()
        #    # Give terminate some time to take effect
        #    time.sleep(0.25)
        #else:
        #    raise ValueError("worker %s:%d isn't running" % (addr, port))


bouncer_process_manager.main(BouncerForPhp)

