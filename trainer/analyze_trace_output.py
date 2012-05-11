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
import argparse
import glob
import os

import logging

DIRNAME = os.path.dirname(os.path.realpath(__file__))
sys.path.append(os.path.join(DIRNAME, '..', 'common'))

import log


class AnalyzeTraceOutput:
    '''Parses a single httperf output file'''

    def __init__(self, infile, test_size, logger):
        self.test_size = test_size
        self.logger = logger

        # parse httperf_output
        request = {}
        url = {}
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
            elif re.match(r"SH[0-9]+:GET .* HTTP/1.1", line):
                n, url_val = AnalyzeTraceOutput.getUrl(line)
                if n in url:
                    raise ValueError("Url for %d already seen in line '%s'" % (n, line))
                url[n] = url_val
            elif re.match(r"RH[0-9]+:HTTP/1.1 ", line):
                n, status_val = AnalyzeTraceOutput.getStatus(line)
                if n in status:
                    raise ValueError("Status code for %d already seen in line '%s'" % (n, line))
                if status_val == 404:
                    raise ValueError("404 encountered in line '%s'. The trainer run is flawed." % line)
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
          url_val = url[n]

          if status_val in self.latency[reqType]:
            self.latency[reqType][status_val][n] = (latency_val, url_val)
          else:
            self.latency[reqType][status_val] = {n : (latency_val, url_val)}

        self.logger.debug("latency = %s", json.dumps(self.latency, indent=2, sort_keys=True))

        # legit_latencies is a list of latencies for legit requests
        # requests that have replies with status != 200 have latency = inf
        self.legit_latencies = []
        self.completed = 0
        for status_val in self.latency["legit"]:
            for _, latency_val in self.latency["legit"][status_val].items():
                if status_val == 200:
                #    self.legit_latencies.append(latency_val)
                    self.completed += 1
                else:
                    latency_val = (float("inf"), latency_val[1])
                self.legit_latencies.append(latency_val)
        self.legit_latencies.sort()
        self.completion_rate = float(self.completed) / float(len(self.legit_latencies))

        self.logger.debug("legit_latencies = %s", self.legit_latencies)

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

    @staticmethod
    def getUrl(line):
        line = line.replace("SH", "").strip()
        parts = line.split(":")
        n = int(parts[0])
        parts = line.split(" ")
        url_val = parts[1]
        return (n, url_val)

class AnalyzeResults:
    '''Analyzes the many httperf output files and reports recommended configs'''

    def __init__(self, completion, quantiles, logger, results=None, filenames=None, test_size=None):
        self.logger = logger
        self.completion = completion
        quantiles = set(quantiles)
        quantiles.add(completion)
        self.quantiles = quantiles
        if results==None and filenames==None:
            raise ValueError("Either results must be given, or filenames, but not neither were given")
        if results!=None and filenames!=None:
            raise ValueError("Either results must be given, or filenames, but not both")
        if filenames != None:
            if test_size == None:
                raise ValueError("Missing test_size")
            if quantiles == None:
                raise ValueError("Missing quantiles")
            self.results = self.load_results(filenames, test_size)
        else:
            self.results = results

    def load_results(self, filenames, test_size):
        results = {}
        for filename in filenames:
            with open(filename, "r") as infile:
                line = infile.readline()
                parts = line.split()
                rate = float(filter(lambda x: x.startswith("--rate"), parts)[0].lstrip("--rate="))
                period = 1.0 / rate
                analysis = AnalyzeTraceOutput(infile, test_size, self.logger)

            results[period] = analysis.summary(period, self.quantiles)
        return results

    def print_csv(self, only_good=True, outfile=sys.stdout):
        '''Set only_good=True to print only the good configuration'''
        # print keys
        quantile_keys = ["quantile %f" % q for q in sorted(list(self.quantiles))]
        line = ["period", "completion rate", "throughput/legit_portion"] + quantile_keys
        line = ",".join(line) + "\n"
        outfile.write(line)

        for period in sorted(self.results.keys()):
            result = self.results[period]
            completion_rate = result["completion_rate"]
            if only_good and completion_rate < self.completion:
                continue
            line = [
                period,
                completion_rate,
                result["throughput"]
            ]

            for q in sorted(list(self.quantiles)):
                line.append(result["quantile"][q])
            line = [str(x) for x in line]
            line = ",".join(line) + "\n"
            outfile.write(line)

    def print_json(self, outfile=sys.stdout):
        '''Set only_good=True to print only the good configuration'''
        print json.dumps(self.results, indent=2, sort_keys=True)

if __name__ == "__main__":
    import os
    cwd = os.getcwd()

    default_glob = os.path.join(cwd, "httperf_stdout_*.txt")
    default_files = glob.glob(default_glob)

    parser = argparse.ArgumentParser(description='Analyzes output of trainer. See source for more info.')
    parser.add_argument("-c", "--completion", type=float, required=False, default=0.95,
                    help="Default=%(default)f. The minimal completion rate you're willing to accept")
    parser.add_argument('-q', "--quantiles", type=float, nargs='*', default=[0.25, 0.50, 0.75, 1.0],
                    help='Default=%(default)s. list of quantiles to measure (0.0 < QUANTILE <= 1.0)')
    parser.add_argument('-f', "--files", type=str, nargs='*', default=default_files,
                    help='Default=%s. list of httperf_stdout_*.txt files to read' % default_glob)
    parser.add_argument('-ts', "--test-size", type=int, required=True,
                    help="REQUIRED. The size of each test in the trace file (see --trace and make_trial_trace.py)")
    parser.add_argument('-o', "--output", type=str, nargs="+", default="csv", choices=["csv", "json"],
                    help="Default=%(default)s.")

    log.add_arguments(parser)
    args = parser.parse_args()
    logger = log.getLogger(args)
    logger.info("Command line arguments: %s" % str(args))

    if len (args.files) == 0:
        sys.stderr.write("Error: could not find any httperf_stdout_*.txt files. Did you run the trainer?\n")
        sys.exit(1)

    analysis = AnalyzeResults(
        args.completion,
        args.quantiles,
        logger,
        filenames=args.files,
        test_size=args.test_size)
    if "csv" in args.output:
        analysis.print_csv()
    if "json" in args.output:
        analysis.print_json()

