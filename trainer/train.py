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
# ==== train.py (the Trainer) ====
# The goal of the Trainer is to help Beer Garden administrators choose a
# value for the TIMEOUT configuration parameter.
#
# The trainer accomplishes this goal by running Beer Garden under various
# configurations (specifcally, different values for PERIOD). For each config,
# the Trainer measures Beer Garden's ability to protect the web application
# from worst-cast high-density attacks. Each configuration test is a different
# "trial."
#
# ==== What is TIMEOUT configuration parameter?====
# Beer Garden evicts the oldest request in the system when (a) there is a new
# request waiting for admission AND (b) there are no idle upstream workers AND
# (c) the oldest request has been in the system for at least TIMEOUT seconds.
#
# ==== Attack workload generation and definition of PERIOD ====
# To emulate a worst-case attack, the trainer sends a series of request bursts.
# Each burst contains N attack requests, followed by one legitimate request,
# followed by N attack requests, where N = WORKERS = the number of non-spare
# upstream workers. Each request is separated by PERIOD seconds, where
# PERIOD = WORKERS / TIMEOUT.
#
# Why this workload? The first N attack requests fill up every upstream worker
# so that there are no longer any idle workers. Then when the legit request
# arrives Beer Garden must evict an attack request to make room for the legit
# request. The following N requests fill up the workers again. When the very
# last request arrives, then at this point the legit request is the oldest
# request in the system, so Beer Garden evicts it in order to admit the new
# attack request.
#
# But why define PERIOD as WORKERS / TIMEOUT? When requests are separated
# by PERIOD seconds, then it guarantees that there exists a request that has
# been in the system for approximately TIMEOUT seconds, which implies that
# every time a request arrives there is a request that has just become
# eligible for eviction.
#
# This workload is therefore "worst case" because it creates maximimum
# contention for CPU and evicts legitimate requests as soon as they become
# eligible for eviction.
#
# ==== What vulnerability does the trainer exploit? ====
# To send attack requests there must be a vulnerablity in the web application.
# You must manually install a vulnerability in the web application. An attack
# request should exploit this vulnerability to put the upstream_worker in an
# infinite loop.
#
# You should create an attack_trace.txt file that contains at least one URL
# (following the httperf wsesslog format), that when requested exploits the
# vulnerability and triggers an infinite loop. Each URL should be followed
# by two newlines.
#
# ==== Concrete example of attack_trace.txt ====
# Vulnerable code: nginx-overload-handler/apps/mediawiki_app/dummy_vuln.php
#
#   <?php while(true); ?>
#
# Copy dummy_vuln.php into the MediaWiki installation by using
# nginx-overload-handler/apps/mediawiki_app/install_dummy_vuln.sh
#
# You can trigger an infinite loop in MediaWiki by requesting
# http://$SERVER_NAME/dummy_vuln.php
#
# The attack_trace.txt file (nginx-overload-handler/apps/mediawiki_app/
# attack_trace.txt) therefore contains:
#
#   /dummy_vuln.php\n\n
#
# ==== What legit requests does the Trainer use? ====
# You must create a legit_trace.txt file that contains a series of
# legitimate URLs (each separated by two newlines). For running the
# Trainer against a MediaWiki instance you can use the script
#
#   nginx-overload-handler/apps/mediawiki_app/create_pages/get_pages.py
#
# to get a list of MediaWiki pages, then use the script
#
#   nginx-overload-handler/apps/mediawiki_app/create_pages/maketrace.py
#
# to generate a number of mutually exclusive legit_trace_*.txt files.
# The resulting legit_trace.txt are mutually exclusive in the sense that
# any legit URL that appears in one legit_trace_*.txt file, will not
# appear in any other legit_trace_*.txt files. This mutual exclusivity
# is useful for cross-validation testing. I.e. train Beer Garden on one
# legit trace, then test it the other traces.
#
# ==== Operation of Trainer ====
# See ./train.py --help for complete command-line usage. There are four
# required arguments to train.py:
#
#  -l LEGIT_TRACE, --legit-trace LEGIT_TRACE
#                        REQUIRED. The trace file containing legit URLs
#  -a ATTACK_TRACE, --attack-trace ATTACK_TRACE
#                        REQUIRED. The trace file containing attack URLs
#  -t TRIAL_SIZE, --trial-size TRIAL_SIZE
#                        REQUIRED. The number of legit requests per trial
#  -w WORKERS, --workers WORKERS
#                        REQUIRED. The number of upstream worker processes.
#
# The trainer loads the LEGIT_TRACE and ATTACK_TRACE files and merges
# them into trace.txt, by taking TRIAL_SIZE requests from LEGIT_TRACE
# and inserting WORKERS attack requests (taken from ATTACK_TRACE) before
# and after each legit request URL (two newlines separating each URL). The
# trace.txt should therefore contain (WORKERS+1) * TRIAL_SIZE + WORKERS
# requests, and twice as many lines.
#
# Each trial, will use the same trace.txt file.
#
# There are three phases:
#   [Phase 1/3] Start off with a period that is sufficiently small such that
#       it leads to an "unsuccessful" trial. An unsuccessful trial is a trial
#       where the proportion of legit request that complete is less than
#       COMPLETION. Then, keep tring new trials (each time doubling period)
#       until there is a successful trial. The trainer now has a lower and
#       upper bound for the "minimal period" --- i.e. the smallest period with
#       that leads to a 'successful' trial.
#   [Phase 2/3] Find the minimal period by trying periods inbetween the lower
#       and upper bounds established in Phase 1.
#   [Phase 3/3] Once you know the minimal period, explore alternative periods
#       that are bigger than the minimal period. Do 10 more trials, each time
#       increasing period by 15%.
#
# For each trial, the trainer produces an output file httperf_stdout_*.txt.
# Use ./analyze_trace_output.py to analyze these output files and make
# configuration recommendations.

#

import json
import subprocess
import urllib2
import argparse
from analyze_trace_output import AnalyzeTraceOutput
import os
import sys
import logging
import time

DIRNAME = os.path.dirname(os.path.realpath(__file__))
sys.path.append(os.path.join(DIRNAME, '..', 'common'))
RESTART_SCRIPT = os.path.join(DIRNAME, "restart_remote_fcgi.sh")

import log
import env
import restart_remote_fcgi
import make_trial_trace

siteconfig = os.path.join(DIRNAME, "..", "siteconfig.sh")
var = env.env(siteconfig)
SERVER_NAME = var["SERVER_NAME"]

class TrainError(Exception):
    pass

class Train:

    def __init__(self,
            completion_rate,
            intial_period,
            trace_filename,
            username,
            server,
            sshport,
            trial_size,
            workers,
            logger):
        self.logger = logger
        self.completion_rate = completion_rate
        self.initial_period = intial_period
        self.trace_filename = trace_filename
        self.username = username
        self.server = server
        self.sshport = sshport
        self.trial_size = trial_size
        self.workers = workers
        self.test_size = workers + 1
        # there should be self.num_requests sessions in self.trace_filename
        # TODO: assert this assumption
        self.num_requests = self.test_size * trial_size + self.workers
        # TODO: come up with a principled timeout
        self.timeout = 5
        self.results = {}
        self.httperf_stdout_template = "httperf_stdout_%03d.txt"
        self.httperf_stderr_template = "httperf_stderr_%03d.txt"
        self.quantiles = set([0.25, 0.5, 0.75, 1.0, self.completion_rate])

        # Find the url that represents a legitimate request
        with open(self.trace_filename) as f:
            lines = f.readlines()
            page = lines[self.workers * 2].strip()
            self.legit_url = "http://%s%s" % (self.server, page)

    def restart_remote_fcgi(self, trial_num):
        self.logger.info("Restarting FCGI workers on server")
        restart_remote_fcgi.restart_remote_fcgi( \
            self.server, \
            self.username, \
            self.sshport, \
            self.legit_url, \
            self.logger)
        self.logger.info("Finished restarting workers")

    def run_httperf(self, period, trial_num):
        '''Executes httperf, adds the results to self.results, and
        returns the completion rate'''
        self.logger.info("Running httperf")
        self.logger.debug("period=%f, trial_num=%d" % (period, trial_num))
        cmd = ["httperf",
                "--hog",
                "--server=%s" % self.server,
                "--wsesslog=%d,1,%s" % (self.num_requests, self.trace_filename),
                "--period=%f" % period,
                "--timeout=%f" % self.timeout,
                "--print-reply=header",
                "--print-request=header"]

        self.logger.debug(" ".join(cmd))
        #return

        httperf_stdout_filename = self.httperf_stdout_template % trial_num
        #httperf_stderr_filename = self.httperf_stderr_template % trial_num
        with open(httperf_stdout_filename, "w") as stdout:#, \
             #open(httperf_stderr_filename, "w") as stderr:
            p = subprocess.Popen(
                cmd,
                bufsize=1,
                stdout=stdout,
                stderr=subprocess.PIPE)
            stderrLogger = log.FileLoggerThread(self.logger, "httperf stderr", logging.WARNING, p.stderr)
            stderrLogger.start()
            ret = p.wait()
            if ret != 0:
                raise TrainError("httperf for trial %d returned %d" % (trial_num, ret))

        with open(httperf_stdout_filename, "r") as infile:
            analysis = AnalyzeTraceOutput(infile, workers=self.workers, logger=self.logger)

        self.results[period] = analysis.summary(period, self.quantiles)
        self.logger.debug("results[period=%f] = %s", period, json.dumps(self.results[period], indent=2, sort_keys=True))
        return self.results[period]["completion_rate"]

    def do_trial(self, period):
        self.restart_remote_fcgi(self.trial_num)
        completion_rate = self.run_httperf(period, self.trial_num)
        self.trial_num += 1
        return completion_rate

    def explore_initial_period(self):
        '''Do trials until completion_rate >= self.completion_rate. During each
        new trial, period is multiplied by 2 to get a new period. Returns
        (fail_period, success_period) where success_period is the period with
        the good completion_rate and fail_period was the immediately preceding
        period.'''
        self.logger.info("[Phase 1/3] Phase begin. Exploring different periods until there is a 'successful' trial")
        period = self.initial_period
        self.logger.info("[Phase 1/3] Running first trial with period = %f", period)
        completion_rate = self.do_trial(period)
        self.logger.info("[Phase 1/3] First trial completion rate = %f", completion_rate)
        while completion_rate < self.completion_rate:
            period *= 2.0
            self.logger.info("[Phase 1/3] Trial #%d beginning. Doubling period to %f", self.trial_num, period)
            completion_rate = self.do_trial(period)
            self.logger.info("[Phase 1/3] Trial #%d finished. Completion rate = %f", self.trial_num - 1, completion_rate)
        if period == self.initial_period:
           raise TrainError("[Phase 1/3] Aborting because the first trial succeeded. Re-run trainer with a shorter initial period")

        self.logger.info("[Phase 1/3] Phase finished")
        lower = period / 2.0
        upper = period
        self.logger.info("[Phase 1/3] Period lower bound = %f, upper bound = %f", lower, upper)

        return (lower, upper)

    def find_minimal_period(self, precision=6):
        # Use explore_initial_period to find a pair of periods (fail, success).
        # Then iteratively refine (fail, success) using a binary search (until
        # we reach a desired level of precision).

        fail_period, success_period = self.explore_initial_period()

        self.logger.info("[Phase 2/3] Finding 'minimal period,' i.e. the smallest period with a 'successful' trial")
        for i in range(0, precision):
            trial_period = (fail_period + success_period) / 2.0
            self.logger.info("[Phase 2/3] Trial #%d, testing with period = %f", self.trial_num, trial_period)
            completion_rate = self.do_trial(trial_period)
            self.logger.info("[Phase 2/3] Trial #%d finished. Completion rate = %f", self.trial_num - 1, completion_rate)
            self.logger.debug("(f=%f, try=%f, s=%f] --> %f" % (fail_period, trial_period, success_period, completion_rate))
            if completion_rate < self.completion_rate:
                self.logger.info("[Phase 2/3] Trial #%d was unsuccessful, increasing period next Phase-2 trial", self.trial_num)
                fail_period = trial_period
            else:
                self.logger.info("[Phase 2/3] Trial #%d was successful, decreasing period next Phase-2 trial", self.trial_num)
                success_period = trial_period

        self.logger.info("[Phase 2/3] Phase finished.")
        self.logger.info("[Phase 2/3] minimal period = %f", success_period)
        return success_period

    def explore_alternate_periods(self, period, num_trials=10, increase_rate=1.15):

        completion_rate = self.results[period]["completion_rate"]

        # If the minimal_period leads to a completion rate of 100% then
        # there is not point in exploring alterante configurations, because
        # they should be strictly worse (because throughput will increase
        # while everything else stays the same).
        if completion_rate == 1.0:
            self.logger.info("[Phase 3/3] No need for Phase 3 since minimal period leads to completion rate of 1.0.")
        else:
            self.logger.info("[Phase 3/3] Exploring alternate period bigger than the minimal period. These trials should all be successful.")
            for i in range(0, num_trials):
                period *= increase_rate
                self.logger.info("[Phase 3/3] Trial #%d, testing with period = %f", self.trial_num, period)
                completion_rate = self.do_trial(period)
                self.logger.info("[Phase 3/3] Trial #%d finished. Completion rate = %f", self.trial_num - 1, completion_rate)
                if completion_rate == 1.0:
                    self.logger.info("[Phase 3/3] No need to explore further since, this period leads to completion rate of 1.0.")
                    break
        self.logger.info("[Phase 3/3] Phase finished.")

    def train(self):
        self.trial_num = 1
        minimal_period = self.find_minimal_period()
        self.explore_alternate_periods(minimal_period)
        self.logger.debug(json.dumps(train.results, indent=2, sort_keys=True))

if __name__ == "__main__":
    cwd = os.getcwd()

    #default_trace_filename = os.path.join(cwd, "trace.txt")

    parser = argparse.ArgumentParser(description='Trains Beer Garden. See source for more info.')

    parser.add_argument("-l", "--legit-trace", type=str, required=True,
                    help="REQUIRED. The trace file containing legit URLs")
    parser.add_argument("-a", "--attack-trace", type=str, required=True,
                    help="REQUIRED. The trace file containing attack URLs")
    parser.add_argument("-t", "--trial-size", type=int, required=True,
                    help="REQUIRED. The number of legit requests per trial")
    parser.add_argument("-w", "--workers", type=int, required=True,
                    help="REQUIRED. The number of non-spare upstream worker processes.")
    parser.add_argument("--single", type=int, default=None,
                    help="Default=%(default)s. If you specify SINGLE, then trainer will "
                    "test a single value for PERIOD (without exploring alternates) SINGLE "
                    "number of times. Useful for testing how reliable results are for a given "
                    "value for PERIOD.")
    parser.add_argument("-c", "--completion", type=float, default=0.95,
                    help="Default=%(default)f. The minimal completion rate you're willing to accept")
    parser.add_argument("-p", "--period", type=float, default=0.01,
                    help="Default=%(default)f. The initial inter-arrival period. Beer Garden should not " \
                    "reach COMPLETION rate when running with PERIOD.")
    parser.add_argument("-u", "--username", type=str, default="beergarden",
                    help="Default=%(default)s. The username on the server. Used when "\
                    "invoking restart_remote_fcgi.sh (see its source for PREREQs for username)")
    parser.add_argument("-s", "--server", type=str, default=SERVER_NAME,
                    help="Default=%(default)s. The address of the server running Beer Garden.")
    parser.add_argument("--sshport", type=int, default=22,
                    help="Default=%(default)s. The port of the server listens for ssh.")

    log.add_arguments(parser)
    args = parser.parse_args()
    logger = log.getLogger(args)
    logger.info("Command line arguments: %s" % str(args))

    try:
        with open(args.legit_trace, "r") as f:
            pass
    except:
        logger.critical("Error: could not open trace file (%s)" % args.legit_trace)
        sys.exit(1)

    try:
        with open(args.attack_trace, "r") as f:
            pass
    except:
        logger.critical("Error: could not open trace file (%s)" % args.attack_trace)
        sys.exit(1)

    trace_filename = os.path.join(cwd, "trace.txt")

    with open(trace_filename, "w") as trace_file:
        make_trial_trace.make_trial_trace( \
            args.workers + 1, \
            args.trial_size, \
            args.legit_trace, \
            args.attack_trace, \
            trace_file)

    train = Train(
        args.completion,
        args.period,
        trace_filename,
        args.username,
        args.server,
        args.sshport,
        args.trial_size,
        args.workers,
        logger)

    if args.single != None:
        train.logger.info("Executing %d trial(s) with period = %f", args.single, args.period)
        train.trial_num = 1
        for i in range(0, args.single):
            train.do_trial(args.period)
            train.logger.info("Trial #%d, testing with period = %f", train.trial_num, period)
            completion_rate = train.do_trial(args.period)
            train.logger.info("Trial #%d finished. Completion rate = %f", train.trial_num - 1, completion_rate)
    else:
        try:
            train.train()
        except TrainError, e:
            train.logger.critical(e.message)
            train.logger.critical("Aborting training")

