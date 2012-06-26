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
# ==== sim_test.py ====
#
#
import unittest
from sim import *

import os
import sys
DIRNAME = os.path.dirname(os.path.realpath(__file__))
sys.path.append(os.path.join(DIRNAME, '..', 'common'))
import log
import logging

class Test_sim(unittest.TestCase):

    def test_UpstreamCpu(self):
        self.logger = log.getLogger(stderr=logging.WARNING)
        config = {
            "time" : 1.0,
            "doorman_burst_len" : 1,
            "doorman_sleep_time" : 200,
            "doorman_expire_delta" : 60,
            "doorman_init_missing_bits" : 0,
            "num_server_cores" : 2,
            "num_total_backends" : 10,
            "num_spare_backends" : 3,
            "attack_hash_per_sec" : 1000.0,
            "attack_sleep" : True,
            "attack_jobs" : [-1.0],
            "attack_cores" : 1,
            "legit_hash_per_sec" : 1000.0,
            "legit_jobs" : [0.2],
            "legit_arrive" : { "exact" : 10.0 }
        }

        sim = Simulator(config, self.logger)
        cpuAgent = None
        cpu = UpstreamCpu(sim, cpuAgent).

if __name__ == '__main__':
    unittest.main()
