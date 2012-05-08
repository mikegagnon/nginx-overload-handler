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
# ==== analyze_trace_output_test.py ====
#
#
import unittest
from analyze_trace_output import *

class Test_analyze_trace_output(unittest.TestCase):

    def test_quantile(self):
        values = [0.5, 1.0, 2.0, 3.0, 4.0, 5.0, 6.0, 7.0, 8.0, 9.0]
        self.assertEqual(AnalyzeTraceOutput.quantile(values, 1.0), 9.0)
        self.assertEqual(AnalyzeTraceOutput.quantile(values, 0.99), 8.0)
        self.assertEqual(AnalyzeTraceOutput.quantile(values, 0.901), 8.0)
        self.assertEqual(AnalyzeTraceOutput.quantile(values, 0.90), 8.0)
        self.assertEqual(AnalyzeTraceOutput.quantile(values, 0.89), 7.0)
        self.assertEqual(AnalyzeTraceOutput.quantile(values, 0.80), 7.0)
        self.assertEqual(AnalyzeTraceOutput.quantile(values, 0.21), 1.0)
        self.assertEqual(AnalyzeTraceOutput.quantile(values, 0.20), 1.0)
        self.assertEqual(AnalyzeTraceOutput.quantile(values, 0.19), 0.5)
        self.assertEqual(AnalyzeTraceOutput.quantile(values, 0.11), 0.5)
        self.assertEqual(AnalyzeTraceOutput.quantile(values, 0.10), 0.5)
        self.assertEqual(AnalyzeTraceOutput.quantile(values, 0.09), 0.0)

        values = [1.0, 2.0, 3.0]
        self.assertEqual(AnalyzeTraceOutput.quantile(values, 1.0), 3.0)
        self.assertEqual(AnalyzeTraceOutput.quantile(values, 0.99), 2.0)
        self.assertEqual(AnalyzeTraceOutput.quantile(values, 0.667), 2.0)
        self.assertEqual(AnalyzeTraceOutput.quantile(values, 0.666), 1.0)
        self.assertEqual(AnalyzeTraceOutput.quantile(values, 0.334), 1.0)
        self.assertEqual(AnalyzeTraceOutput.quantile(values, 0.333), 0.0)
        self.assertEqual(AnalyzeTraceOutput.quantile(values, 0.0), 0.0)

if __name__ == '__main__':
    unittest.main()
