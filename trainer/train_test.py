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
# ==== train_test.py ====
#
#
import unittest
from train import *

class TrainDummy(Train):
    def do_trial(self, period):
        completion_rate = 1.0
        for p, cr in self.crs:
            if period < p:
                completion_rate = cr
                break
        self.results[period] ={ "completion_rate":completion_rate }
        return completion_rate

class Test_train(unittest.TestCase):

    def test_train_period(self):
        #TODO more tests
        username = "foo"
        server = "bar"
        workers = 1

        intial_period = 0.01
        completion_rate = 0.95
        precision = 7
        td = TrainDummy(completion_rate, intial_period, workers, username, server)
        td.crs = [(0.25, 0.30), (0.30, .40), (0.406, .45), (0.41, 0.95), (0.45, 0.96), (1.0, 0.99),(3.0, 0.999)]

        true_min_period = 0.406
        min_period = td.find_minimal_period(precision)
        delta = 2 ** -precision
        self.assertTrue(min_period - delta <= true_min_period and min_period + delta >= true_min_period)

        td.explore_alternate_periods(min_period)


if __name__ == '__main__':
    unittest.main()
