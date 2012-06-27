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
import greenlet

class MockSim:
    pass

def mockAgent():
    pass

class Test_sim(unittest.TestCase):

    def test_UpstreamCpu(self):
        self.logger = log.getLogger(stderr=logging.WARNING)
        sim = MockSim()
        sim.time = 0.0
        cpuAgent = greenlet.greenlet(mockAgent)
        num_cores = 4
        cpu = UpstreamCpu(num_cores, sim, cpuAgent)

        job_time1 = 1.0
        message = NewJobMessage(sim, job_time1)
        old_event1, new_event1, new_job1, finished_job1 = cpu.handleMessage(message)
        self.assertEquals(old_event1, None)
        self.assertIsInstance(new_event1.message, JobFinishMessage)
        self.assertAlmostEqual(new_event1.message.job, new_job1)
        self.assertAlmostEqual(new_event1.time, 1.0)
        self.assertEquals(finished_job1, None)
        self.assertAlmostEqual(new_job1.time, 1.0)

        sim.time += 0.1
        job_time2 = 1.0
        message = NewJobMessage(sim, job_time2)
        old_event2, new_event2, new_job2, finished_job2 = cpu.handleMessage(message)
        self.assertEquals(old_event2, new_event1)
        self.assertIsInstance(new_event2.message, JobFinishMessage)
        self.assertAlmostEqual(new_event2.message.job, new_job1)
        self.assertAlmostEqual(new_event2.time, 1.0)
        self.assertEquals(finished_job2, None)
        self.assertAlmostEqual(new_job1.time, 0.9)
        self.assertAlmostEqual(new_job2.time, 1.0)

        sim.time += 0.1
        job_time3 = 1.0
        message = NewJobMessage(sim, job_time3)
        old_event3, new_event3, new_job3, finished_job3 = cpu.handleMessage(message)
        self.assertEquals(old_event3, new_event2)
        self.assertIsInstance(new_event3.message, JobFinishMessage)
        self.assertAlmostEqual(new_event3.message.job, new_job1)
        self.assertAlmostEqual(new_event3.time, 1.0)
        self.assertEquals(finished_job3, None)
        self.assertAlmostEqual(new_job1.time, 0.8)
        self.assertAlmostEqual(new_job2.time, 0.9)
        self.assertAlmostEqual(new_job3.time, 1.0)

        sim.time += 0.1
        job_time4 = 1.0
        message = NewJobMessage(sim, job_time4)
        old_event4, new_event4, new_job4, finished_job4 = cpu.handleMessage(message)
        self.assertEquals(old_event4, new_event3)
        self.assertIsInstance(new_event4.message, JobFinishMessage)
        self.assertAlmostEqual(new_event4.message.job, new_job1)
        self.assertAlmostEqual(new_event4.time, 1.0)
        self.assertEquals(finished_job4, None)
        self.assertAlmostEqual(new_job1.time, 0.7)
        self.assertAlmostEqual(new_job2.time, 0.8)
        self.assertAlmostEqual(new_job3.time, 0.9)
        self.assertAlmostEqual(new_job4.time, 1.0)

        # After this job is added there are more jobs in the system
        # then there are cores. Therefore new_event5.time should
        # be set back. Job1 has 0.6 cpu-seconds left. Every one wall-clock second,
        # 4 cpu-seconds (from the 4 cores) get evenly distributed across the 5 jobs
        # --> each wall-clock second each job gets 4/5th of a CPU second.
        # Let W = number of wall-clock seconds needed for Job1 to finish.
        # 4/5 * W == 0.6 --> W == 0.75
        # current_time + W == 0.40 + 0.75 = 1.15
        sim.time += 0.1
        job_time5 = 1.0
        message = NewJobMessage(sim, job_time5)
        old_event5, new_event5, new_job5, finished_job5 = cpu.handleMessage(message)
        self.assertEquals(old_event5, new_event4)
        self.assertIsInstance(new_event5.message, JobFinishMessage)
        self.assertAlmostEqual(new_event5.message.job, new_job1)
        self.assertAlmostEqual(sim.time, 0.4)
        self.assertAlmostEqual(new_event5.time, 1.15)
        self.assertEquals(finished_job5, None)
        self.assertAlmostEqual(new_job1.time, 0.6)
        self.assertAlmostEqual(new_job2.time, 0.7)
        self.assertAlmostEqual(new_job3.time, 0.8)
        self.assertAlmostEqual(new_job4.time, 0.9)
        self.assertAlmostEqual(new_job5.time, 1.0)

        # Over the past 0.1 seconds each job has received 0.1 * 4/5 == 0.08 cpu seconds
        # Therefore job1 only needs 0.52 cpu seconds left
        # Job1 will finish in 6/4 * 0.52 seconds == 0.78 seconds
        # current_time + W == 0.5 + 0.78 = 1.28
        sim.time += 0.1
        job_time6 = 1.0
        message = NewJobMessage(sim, job_time6)
        old_event6, new_event6, new_job6, finished_job6 = cpu.handleMessage(message)
        self.assertEquals(old_event6, new_event5)
        self.assertIsInstance(new_event6.message, JobFinishMessage)
        self.assertAlmostEqual(new_event6.message.job, new_job1)
        self.assertAlmostEqual(sim.time, 0.5)
#        self.assertAlmostEqual(new_event5.time, 1.28)
        self.assertEquals(finished_job5, None)
        self.assertAlmostEqual(new_job1.time, 0.52)
        self.assertAlmostEqual(new_job2.time, 0.62)
        self.assertAlmostEqual(new_job3.time, 0.72)
        self.assertAlmostEqual(new_job4.time, 0.82)
        self.assertAlmostEqual(new_job5.time, 0.92)
        self.assertAlmostEqual(new_job6.time, 1.0)



if __name__ == '__main__':
    unittest.main()
