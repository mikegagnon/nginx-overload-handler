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
        sim.time = Fraction(0.0)
        cpuAgent = greenlet.greenlet(mockAgent)
        num_cores = 4
        cpu = UpstreamCpu(num_cores, sim, cpuAgent)

        job_time1 = Fraction(1.0)
        message = NewJobMessage(sim, job_time1)
        old_event1, new_event1, new_job1, finished_job1 = cpu.handleMessage(message)
        self.assertEquals(old_event1, None)
        self.assertIsInstance(new_event1.message, JobFinishMessage)
        self.assertEquals(new_event1.message.job, new_job1)
        self.assertEquals(finished_job1, None)
        self.assertEquals(new_job1.time, Fraction(1.0))
        self.assertEquals(new_event1.time, Fraction(1.0))

        sim.time += Fraction(0.1)
        job_time2 = Fraction(1.0)
        message = NewJobMessage(sim, job_time2)
        old_event2, new_event2, new_job2, finished_job2 = cpu.handleMessage(message)
        self.assertEquals(old_event2, new_event1)
        self.assertIsInstance(new_event2.message, JobFinishMessage)
        self.assertEquals(new_event2.message.job, new_job1)
        self.assertEquals(finished_job2, None)
        self.assertEquals(new_job1.time, Fraction(1.0) - Fraction(0.1))
        self.assertEquals(new_job2.time, Fraction(1.0))
        self.assertEquals(new_event2.time, Fraction(1.0))

        sim.time += Fraction(0.1)
        job_time3 = Fraction(1.0)
        message = NewJobMessage(sim, job_time3)
        old_event3, new_event3, new_job3, finished_job3 = cpu.handleMessage(message)
        self.assertEquals(old_event3, new_event2)
        self.assertIsInstance(new_event3.message, JobFinishMessage)
        self.assertEquals(new_event3.message.job, new_job1)
        self.assertEquals(finished_job3, None)
        self.assertEquals(new_job1.time, Fraction(1.0) - Fraction(0.2))
        self.assertEquals(new_job2.time, Fraction(1.0) - Fraction(0.1))
        self.assertEquals(new_job3.time, Fraction(1.0))
        self.assertEquals(new_event3.time, Fraction(1.0))

        sim.time += Fraction(0.1)
        job_time4 = Fraction(1.0)
        message = NewJobMessage(sim, job_time4)
        old_event4, new_event4, new_job4, finished_job4 = cpu.handleMessage(message)
        self.assertEquals(old_event4, new_event3)
        self.assertIsInstance(new_event4.message, JobFinishMessage)
        self.assertEquals(new_event4.message.job, new_job1)
        self.assertEquals(finished_job4, None)
        self.assertEquals(new_job1.time, Fraction(1.0) - Fraction(0.2) - Fraction(0.1))
        self.assertEquals(new_job2.time, Fraction(1.0) - Fraction(0.2))
        self.assertEquals(new_job3.time, Fraction(1.0) - Fraction(0.1))
        self.assertEquals(new_job4.time, Fraction(1.0))
        self.assertEquals(new_event4.time, Fraction(1.0))

        # After this job is added there are more jobs in the system
        # then there are cores. Therefore new_event5.time should
        # be set back. Job1 has 0.6 cpu-seconds left. Every one wall-clock second,
        # 4 cpu-seconds (from the 4 cores) get evenly distributed across the 5 jobs
        # --> each wall-clock second each job gets 4/5th of a CPU second.
        # Let W = number of wall-clock seconds needed for Job1 to finish.
        # 4/5 * W == 0.6 --> W == 0.75
        # current_time + W == 0.40 + 0.75 = 1.15
        sim.time += Fraction(0.1)
        job_time5 = Fraction(1.0)
        message = NewJobMessage(sim, job_time5)
        old_event5, new_event5, new_job5, finished_job5 = cpu.handleMessage(message)
        self.assertEquals(old_event5, new_event4)
        self.assertIsInstance(new_event5.message, JobFinishMessage)
        self.assertEquals(new_event5.message.job, new_job1)
        self.assertEquals(sim.time, Fraction(0.4))
        self.assertEquals(finished_job5, None)
        self.assertEquals(new_job1.time, Fraction(0.6))
        self.assertEquals(new_job2.time, Fraction(1.0) - Fraction(0.2) - Fraction(0.1))
        self.assertEquals(new_job3.time, Fraction(1.0) - Fraction(0.2))
        self.assertEquals(new_job4.time, Fraction(1.0) - Fraction(0.1))
        self.assertEquals(new_job5.time, Fraction(1.0))
        self.assertEquals(new_event5.time, Fraction(0.4) + Fraction(0.6) * Fraction(5, 4))

        # Over the past 0.1 seconds each job has received 0.1 * 4/5 == 0.08 cpu seconds
        # Therefore job1 only needs 0.52 cpu seconds left
        # Job1 will finish in 6/4 * 0.52 seconds == 0.78 seconds
        # current_time + W == 0.5 + 0.78 = 1.28
        sim.time += Fraction(0.1)
        job_time6 = Fraction(1.0)
        message = NewJobMessage(sim, job_time6)
        old_event6, new_event6, new_job6, finished_job6 = cpu.handleMessage(message)
        self.assertEquals(old_event6, new_event5)
        self.assertIsInstance(new_event6.message, JobFinishMessage)
        self.assertEquals(new_event6.message.job, new_job1)
        self.assertEquals(sim.time, Fraction(0.4) + Fraction(0.1))
        self.assertEquals(finished_job6, None)
        self.assertEquals(new_job1.time, Fraction(0.6) - Fraction(0.1) * Fraction(4,5))
        self.assertEquals(new_job2.time, (Fraction(1.0) - Fraction(0.2) - Fraction(0.1)) - Fraction(0.1) * Fraction(4,5))
        self.assertEquals(new_job3.time, 0.72)
        self.assertEquals(new_job4.time, 0.82)
        self.assertEquals(new_job5.time, 0.92)
        self.assertEquals(new_job6.time, 1.0)
        self.assertEquals(new_event6.time, 1.28)

        return
        # Fast forward until it is time for job1 to finish.
        # Over the past 0.78 seconds each job has received 0.78 * 4/6 == 0.52 cpu seconds
        # Job1 will finish in 5/4 * 0.10 seconds == 0.125 seconds
        # current_time + W == 1.28 + 0.125 = 1.405
        sim.time = new_event6.time
        old_event7, new_event7, new_job7, finished_job7 = cpu.handleMessage(new_event6.message)
        self.assertEquals(old_event7, new_event6)
        self.assertIsInstance(new_event7.message, JobFinishMessage)
        self.assertAlmostEqual(new_event7.message.job, new_job2)
        self.assertAlmostEqual(sim.time, 1.28)
        self.assertEquals(finished_job7, new_job1)
        self.assertAlmostEqual(new_job1.time, 0.00)
        self.assertAlmostEqual(new_job2.time, 0.10)
        self.assertAlmostEqual(new_job3.time, 0.20)
        self.assertAlmostEqual(new_job4.time, 0.30)
        self.assertAlmostEqual(new_job5.time, 0.40)
        self.assertAlmostEqual(new_job6.time, 0.48)
        self.assertEquals(new_job7, None)
        self.assertAlmostEqual(new_event7.time, 1.405)

        return
        # Zero time passes and a job arrives that will become first in line
        # Job8 will finish in 6/4 * 0.05 seconds == 0.075 seconds
        # current_time + W == 1.28 + 0.075 = 1.355
        sim.time = new_event6.time
        job_time8 = 0.05
        message = NewJobMessage(sim, job_time8)
        old_event8, new_event8, new_job8, finished_job8 = cpu.handleMessage(message)
        self.assertEquals(old_event8, new_event7)
        self.assertIsInstance(new_event8.message, JobFinishMessage)
        self.assertAlmostEqual(new_event8.message.job, new_job8)
        self.assertAlmostEqual(sim.time, 1.28)
        self.assertEquals(finished_job8, None)
        self.assertAlmostEqual(new_job1.time, 0.00)
        self.assertAlmostEqual(new_job2.time, 0.10)
        self.assertAlmostEqual(new_job3.time, 0.20)
        self.assertAlmostEqual(new_job4.time, 0.30)
        self.assertAlmostEqual(new_job5.time, 0.40)
        self.assertAlmostEqual(new_job6.time, 0.48)
        self.assertEquals(new_job7, None)
        self.assertAlmostEqual(new_job8.time, 0.05)
        self.assertAlmostEqual(new_event8.time, 1.355)

        # Zero time passes and another job arrives that is identical to previous job
        # Job8 will finish in 7/4 * 0.05 seconds == 0.0875 seconds
        # current_time + W == 1.28 + 0.0875 = 1.355
        sim.time = new_event6.time
        job_time9 = 0.05
        message = NewJobMessage(sim, job_time9)
        old_event9, new_event9, new_job9, finished_job9 = cpu.handleMessage(message)
        self.assertEquals(old_event9, new_event8)
        self.assertIsInstance(new_event9.message, JobFinishMessage)
        self.assertAlmostEqual(new_event9.message.job, new_job8)
        self.assertAlmostEqual(sim.time, 1.28)
        self.assertEquals(finished_job9, None)
        self.assertAlmostEqual(new_job1.time, 0.00)
        self.assertAlmostEqual(new_job2.time, 0.10)
        self.assertAlmostEqual(new_job3.time, 0.20)
        self.assertAlmostEqual(new_job4.time, 0.30)
        self.assertAlmostEqual(new_job5.time, 0.40)
        self.assertAlmostEqual(new_job6.time, 0.48)
        self.assertEquals(new_job7, None)
        self.assertAlmostEqual(new_job8.time, 0.05)
        self.assertAlmostEqual(new_job9.time, 0.05)
        self.assertAlmostEqual(new_event9.time, 1.3675)

        # Before the next job can finish, job2 is killed
        # Over the past 0.025 seconds each job has received 0.025 * 4/7 == 0.014285714285714287 cpu seconds
        # Job8 will finish in 6/4 * 0.03571428571428571 seconds == 0.05357142857142857 seconds
        # current_time + W == 1.305 + 0.05357142857142857 = 1.3585714285714285
        sim.time += 0.025
        message = KillJobMessage(sim, new_job2)
        old_event10, new_event10, new_job10, finished_job10 = cpu.handleMessage(message)
        self.assertEquals(old_event10, new_event9)
        self.assertIsInstance(new_event10.message, JobFinishMessage)
        self.assertAlmostEqual(new_event10.message.job, new_job8)
        self.assertAlmostEqual(sim.time, 1.305)
        self.assertEquals(finished_job10, None)
        self.assertAlmostEqual(new_job1.time, 0.00)
        self.assertAlmostEqual(new_job2.time, 0.08571428571428572)
        self.assertAlmostEqual(new_job3.time, 0.18571428571428572)
        self.assertAlmostEqual(new_job4.time, 0.28571428571428572)
        self.assertAlmostEqual(new_job5.time, 0.38571428571428572)
        self.assertAlmostEqual(new_job6.time, 0.46571428571428570)
        self.assertEquals(new_job7, None)
        self.assertAlmostEqual(new_job8.time, 0.03571428571428571)
        self.assertAlmostEqual(new_job9.time, 0.03571428571428571)
        self.assertEquals(new_job10, None)
        self.assertAlmostEqual(new_event10.time, 1.3585714285714285)

        # Fast forward until it is time for job8 to finish.
        # Over the past 0.05357142857142857 seconds each job has received
        #       0.05357142857142857 * 4/6 == 0.03571428571428571 cpu seconds
        # Job1 will finish in 5/4 * 0.10 seconds == 0.125 seconds
        # current_time + W == 1.28 + 0.125 = 1.405
        sim.time = new_event10.time,
        old_event11, new_event11, new_job11, finished_job11 = cpu.handleMessage(new_event10.message)
        self.assertEquals(old_event11, new_event10)
        self.assertIsInstance(new_event11.message, JobFinishMessage)
        self.assertEquals(new_event11.message.job, finished_job11)
        self.assertEquals(finished_job11, new_job8)
        self.assertAlmostEqual(new_job1.time, 0.00)
        self.assertAlmostEqual(new_job2.time, 0.08571428571428572)

        # BOOKMARK
        self.assertAlmostEqual(new_job3.time, 0.20)
        self.assertAlmostEqual(new_job4.time, 0.30)
        self.assertAlmostEqual(new_job5.time, 0.40)
        self.assertAlmostEqual(new_job6.time, 0.48)
        self.assertEquals(new_job7, None)
        self.assertAlmostEqual(new_event7.time, 1.405)


if __name__ == '__main__':
    unittest.main()
