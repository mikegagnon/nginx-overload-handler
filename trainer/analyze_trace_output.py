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
# ==== analyze_trace_output.py ====
#
# USAGE: cat httperf_output.txt | ./analyze_trace_output.py test_size percentile
#

import sys
import re
import json
import math

from scipy import stats

class AnalyzeTraceOutput:

    def __init__(self, infile, test_size, debug = False):
        self.test_size = test_size

        # parse httperf_output
        request = {}
        reply = {}
        status = {}
        for line in infile:
            if re.match(r"REQUEST_TIME", line):
                n, timestamp = AnalyzeTraceOutput.getTimestamp(line, "REQUEST_TIME")
                if n in request:
                    raise ValueError("REQUEST_TIME%d already seen" % n)
                request[n] = timestamp
            elif re.match(r"REPLY_TIME", line):
                n, timestamp = AnalyzeTraceOutput.getTimestamp(line, "REPLY_TIME")
                if n in reply:
                    raise ValueError("REPLY_TIME%d already seen" % n)
                reply[n] = timestamp
            elif re.match(r"RH[0-9]+:HTTP/1.1 ", line):
                n, status_val = AnalyzeTraceOutput.getStatus(line)
                if n in status:
                    raise ValueError("Status code for %d already seen" % n)
                status[n] = status_val

        # build up the latency struct
        # latency[reqType][status_val][n] == latency for request n
        self.latency = {
            "legit" : {},
            "attack" : {}
        }
        for n, t1 in request.items():
          if self.isLegit(n):
            reqType = "legit"
          else:
            reqType = "attack"

          t2 = reply.get(n, float("inf"))
          latency_val = t2 - t1
          status_val = status.get(n, None)

          if status_val in self.latency[reqType]:
            self.latency[reqType][status_val][n] = latency_val
          else:
            self.latency[reqType][status_val] = {n : latency_val}

        if debug:
            print json.dumps(self.latency, indent=2, sort_keys=True)

        # legit_latencies is a list of latencies for legit requests
        # requests that have replies with status != 200 have latency = inf
        self.legit_latencies = []
        self.completed = 0
        for status_val in self.latency["legit"]:
            for _, latency_val in self.latency["legit"][status_val].items():
                if status_val == 200:
                    self.legit_latencies.append(latency_val)
                    self.completed += 1
                else:
                    self.legit_latencies.append(float("inf"))
        self.legit_latencies.sort()
        self.completion_rate = float(self.completed) / float(len(self.legit_latencies))

        if debug:
            print self.legit_latencies

    def throughput(self, period):
        '''Returns throughput, assuming the proportion of
        legit requests, L, is 1.0 (ie. 100%). To find
        the throughput for another value of L, where
        0 <= L <= 1.0, just do throughput * L'''
        return self.completion_rate * (1.0/period)

    def summary(self, period, quantiles):
        quantiles = set(quantiles)
        summary = {
            "completion_rate" : self.completion_rate,
            "quantile" : {},
            "throughput" : self.throughput(period)
        }
        quantiles.add(self.completion_rate)

        for q in quantiles:
            summary["quantile"][q] = self.legit_quantile(q)

        return summary

    def isLegit(self, n):
        return n % self.test_size == self.test_size - 1

    def legit_quantile(self, q):
        return AnalyzeTraceOutput.quantile(self.legit_latencies, q)

    @staticmethod
    def quantile(values, q):
        '''assumes values is sorted numbers (and each is >= 0), and 0.0 < p <= 1.0.
        returns x, where at least q * 100 percent of numbers (from values) are <= x'''
        index = int(q * len(values)) - 1
        if index >= 0:
            return values[index]
        else:
            return 0.0

    @staticmethod
    def getTimestamp(line, prefix):
        line = line.replace(prefix, "").strip()
        parts = line.split(":")
        n = int(parts[0])
        timestamp = float(parts[1])
        return (n, timestamp)

    @staticmethod
    def getStatus(line):
        line = line.replace("RH", "").strip()
        parts = line.split(":")
        n = int(parts[0])
        parts = line.split(" ")
        status_val = int(parts[1])
        return (n, status_val)

def load_results(filenames, test_size, quantiles):
    results = {}
    for filename in filenames:
        with open(filename, "r") as infile:
            line = infile.readline()
            parts = line.split()
            rate = float(filter(lambda x: x.startswith("--rate"), parts)[0].lstrip("--rate="))
            period = 1.0 / rate
            analysis = AnalyzeTraceOutput(infile, test_size)

        results[period] = analysis.summary(period, quantiles)
    return results

if __name__ == "__main__":
    quantiles = [0.25, 0.50, 0.75, 0.95, 0.99, 1.0]
    test_size = int(sys.argv[1])
    filenames = sys.argv[2:]
    results = load_results(filenames, test_size, quantiles)
    print json.dumps(results, indent=2, sort_keys=True)
    #analysis = AnalyzeTraceOutput(sys.stdin, test_size, True)
    #print json.dumps(analysis.summary(period, set([quantile])), indent=2, sort_keys=True)
