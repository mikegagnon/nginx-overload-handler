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
# ==== train.py ====
#
# USAGE: ./train.py completion period workers username server
#   where:
#       completion is the "minimal completion rate" (a number between 0 and 1)
#       period is the __initial__ interarrival period
#       workers is the numer of fastcgi workers on the server
#       usernaname is a user on server who has permission to restart the
#           the fcgi workers (see restart_remote_fcgi.sh)
#       server is the address of the server (or domain name)
#
# The goal is to run the web application under a variety of Beer Garden
# configurations, and recommend several configurations where at least
# 'completion' portion of legitimate requests complete. The trainer than
# reports the performance metrics from the trials, so you can choose the
# configuration with the "best" performance. "Best" is subjective; there is
# often a trade space between latency, throughput, and completion rate. The
# only setting the trainer modifies is 'period', interarrival time between
# requests.
#
# PREREQs:
#   (1) create a trace file
#
# ==== Design ====
#
# (1) Find M, the "minimal period." I.e., M is the smallest period that Beer
# Garden will recommend.
# (2) Find alternate periods by increasing M by 15% ten times.
# (3) Report the configurations, each configuration has 3 performance metrics
#     associated with its performance: throughput, completion rate, latency. Sort
#     configurations three different ways (according to each metric).
#

#TODO: make sure all file accesses are absolute and refer to the correct parent dir

import json
import subprocess
from analyze_trace_output import AnalyzeTraceOutput

class TrainError(Exception):
    pass

class Train:

    def __init__(self,
            completion_rate,
            intial_period,
            trace_filename,
            username,
            server,
            num_tests,
            num_workers):
        self.completion_rate = completion_rate
        self.initial_period = intial_period
        self.trace_filename = trace_filename
        self.username = username
        self.server = server
        self.num_tests = num_tests
        self.num_workers = num_workers
        self.test_size = self.num_workers + 1
        # there should be self.num_requests sessions in self.trace_filename
        # TODO: assert this assumption
        self.num_requests = self.test_size * num_tests
        # TODO: come up with a principled timeout
        self.timeout = 5
        self.results = {}
        self.httperf_stdout_template = "httperf_stdout_%03d.txt"
        self.httperf_stderr_template = "httperf_stderr_%03d.txt"
        self.quantiles = set([0.25, 0.5, 0.75, 1.0, self.completion_rate])

    def restart_fcgi_workers(self, trial_num):
        #TODO: verify that the restart was successful.
        # idea: grab the first legit request from the trace, and do
        # a request for that. This has the added benefit in that
        # it will validate that the trainer is parsing the trace
        # correctly
        print "restart_fcgi_workers(trial_num=%d)" % (trial_num)
        cmd = ["/home/mgagnon/workspace/nginx-overload-handler/trainer/restart_remote_fcgi.sh",
            self.username,
            self.server]
        p = subprocess.Popen(cmd)
        ret = p.wait()
        if ret != 0:
            raise TrainError("restart_remote_fcgi.sh for trial %d returned %d" % (trial_num, ret))

    def run_httperf(self, period, trial_num):
        '''Executes httperf, adds the results to self.results, and
        returns the completion rate'''
        print "run_httperf(period=%f, trial_num=%d)" % (period, trial_num)
        cmd = ["httperf",
                "--hog",
                "--server=%s" % self.server,
                "--wsesslog=%d,1,%s" % (self.num_requests, self.trace_filename),
                "--period=%f" % period,
                "--timeout=%f" % self.timeout,
                "--print-reply=header",
                "--print-request=header"]

        print " ".join(cmd)
        #return

        httperf_stdout_filename = self.httperf_stdout_template % trial_num
        httperf_stderr_filename = self.httperf_stderr_template % trial_num
        with open(httperf_stdout_filename, "w") as stdout, \
             open(httperf_stderr_filename, "w") as stderr:
            p = subprocess.Popen(
                cmd,
                bufsize=1,
                stdout=stdout,
                stderr=stderr)
            ret = p.wait()
            if ret != 0:
                raise TrainError("httperf for trial %d returned %d" % (trial_num, ret))

        with open(httperf_stdout_filename, "r") as infile:
            analysis = AnalyzeTraceOutput(infile, self.test_size)

        self.results[period] = analysis.summary(period, self.quantiles)
        return self.results[period]["completion_rate"]

    def do_trial(self, period):
        self.restart_fcgi_workers(self.trial_num)
        completion_rate = self.run_httperf(period, self.trial_num)
        self.trial_num += 1
        return completion_rate

    def explore_initial_period(self):
        '''Do trials until completion_rate >= self.completion_rate. During each
        new trial, period is multiplied by 2 to get a new period. Returns
        (fail_period, success_period) where success_period is the period with
        the good completion_rate and fail_period was the immediately preceding
        period.'''
        period = self.initial_period
        completion_rate = self.do_trial(period)
        print "First trial with initial_period = %f --> %f" % (period, completion_rate)
        while completion_rate < self.completion_rate:
            period *= 2.0
            completion_rate = self.do_trial(period)
            print "explore trial with period = %f --> %f" % (period, completion_rate)
        if period == self.initial_period:
           raise TrainError("The first trial succeeded. Lower initial_period and try again")
        return (period/2.0, period)

    def find_minimal_period(self, precision=5):
        # Use explore_initial_period to find a pair of periods (fail, success).
        # Then iteratively refine (fail, success) using a binary search (until
        # we reach a desired level of precision).
        print "Finding minimal period"

        fail_period, success_period = self.explore_initial_period()

        for i in range(0, precision):
            trial_period = (fail_period + success_period) / 2.0
            completion_rate = self.do_trial(trial_period)
            print "(f=%f, try=%f, s=%f] --> %f" % (fail_period, trial_period, success_period, completion_rate)
            if completion_rate < self.completion_rate:
                fail_period = trial_period
            else:
                success_period = trial_period

        return success_period

    def explore_alternate_periods(self, period, num_trials=10, increase_rate=1.15):
        print "Finding alternate periods"

        completion_rate = self.results[period]["completion_rate"]

        # If the minimal_period leads to a completion rate of 100% then
        # there is not point in exploring alterante configurations, because
        # they should be strictly worse (because throughput will increase
        # while everything else stays the same).
        if completion_rate == 1.0:
            return

        for i in range(0, num_trials):
            period *= increase_rate
            completion_rate = self.do_trial(period)
            print "Period %f --> %f" % (period, completion_rate)
            if completion_rate == 1.0:
                return

    def output(self):
        pass

    def train(self):
        self.trial_num = 0
        minimal_period = self.find_minimal_period()
        self.explore_alternate_periods(minimal_period)
        self.output()

if __name__ == "__main__":
    completion_rate = 0.95
    intial_period = 0.1
    trace_filename = "trial_trace.txt"
    username = "beergarden"
    server = "172.16.209.198"
    num_tests = 10
    num_workers = 4

    period = 0.25
    trial_num = 0

    train = Train(
        completion_rate,
        intial_period,
        trace_filename,
        username,
        server,
        num_tests,
        num_workers)
    train.train()

    print json.dumps(train.results, indent=2, sort_keys=True)
