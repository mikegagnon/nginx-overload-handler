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
# ==== Bouncer process manager (for redmine) ====
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

remine_deps = os.path.join(DIRNAME, "..", "..", "apps", "redmine_app", "env.sh")
var = env.env(remine_deps)

INSTALL_REDMINE_PATH = var["INSTALL_REDMINE_PATH"]

# TODO: Is it possible to modify the configuration of mongrel such that it only
# handles one request at time? This would hopefully speed up the time it takes
# restart mongrel and lead to lower memory foot print.
REDMINE_CMD_TEMPLATE_STR = 'mongrel_rails start -p $port -e production -c %s -P /tmp/mongrel$port.pid' % INSTALL_REDMINE_PATH

class BouncerForRedmine(BouncerProcessManager):

    def start_worker(self, addr, port):
        '''Must attempt to launch the specified worker. Should return the popen object for the new worker
           or None, if the worker couldn't be be launched for some reason.'''
        cmd_str = Template(REDMINE_CMD_TEMPLATE_STR).substitute( \
                addr = addr, \
                port = str(port) \
            )
        self.logger.debug("cmd_str='%s'" % cmd_str)
        cmd = cmd_str.split()
        process = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        stdoutLogger = log.FileLoggerThread(self.logger, "redmine stdout", logging.INFO, process.stdout)
        stderrLogger = log.FileLoggerThread(self.logger, "redmine stderr", logging.ERROR, process.stderr)
        stdoutLogger.start()
        stderrLogger.start()
        return process

    def kill_worker(self, addr, port, popen_obj):
        '''Must attempt to kill the specified worker. Does not return anything'''
        try:
            popen_obj.kill()
        except OSError, e:
            self.logger.error("Error while trying to kill '%s:%d': %s" % (addr, port, e))

bouncer_process_manager.main(BouncerForRedmine)

