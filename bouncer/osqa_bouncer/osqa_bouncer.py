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
# ==== Bouncer process manager (for osqa) ====
#
# See ../bouncer/bouncer_process_manager.py for more information
#

import sys
import os
import subprocess
import time
from string import Template
import logging

DIRNAME = os.path.dirname(os.path.realpath(__file__))

sys.path.append(os.path.join(DIRNAME, '..'))
sys.path.append(os.path.join(DIRNAME, '..', '..', 'common'))

import log
import env
import bouncer_process_manager
from bouncer_process_manager import BouncerProcessManager

osqa_deps = os.path.join(DIRNAME, "..", "..", "apps", "osqa_app", "env.sh")
var = env.env(osqa_deps)

INSTALL_OSQA_PATH = var["INSTALL_OSQA_PATH"]

OSQA_CMD_TEMPLATE_STR = 'python %s/manage.py run_gunicorn 0.0.0.0:$port' % INSTALL_OSQA_PATH

class BouncerForOsqa(BouncerProcessManager):

    def start_worker(self, addr, port):
        '''Must attempt to launch the specified worker. Should return the popen object for the new worker
           or None, if the worker couldn't be be launched for some reason.'''
        cmd_str = Template(OSQA_CMD_TEMPLATE_STR).substitute( \
                addr = addr, \
                port = str(port) \
            )
        self.logger.debug("cmd_str='%s'" % cmd_str)
        cmd = cmd_str.split()
        process = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        stdoutLogger = log.FileLoggerThread(self.logger, "osqa stdout", logging.INFO, process.stdout)
        stderrLogger = log.FileLoggerThread(self.logger, "osqa stderr", logging.ERROR, process.stderr)
        stdoutLogger.start()
        stderrLogger.start()
        return process

    def kill_worker(self, addr, port, popen_obj):
        '''Must attempt to kill the specified worker. Does not return anything'''
        try:
            popen_obj.kill()
        except OSError, e:
            self.logger.error("Error while trying to kill '%s:%d': %s" % (addr, port, e))

bouncer_process_manager.main(BouncerForOsqa)

