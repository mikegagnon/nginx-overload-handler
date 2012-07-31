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
# ==== sigservice.py ====
#
# Note: calculating/estimating the a prior probability of high-density is tricky
# because we classify before admittance, but we only train on samples after they're
# admitted. So the a priori probability of high-density might truly be 0.99
# but the SigService might see twice as many low-density requests as high density
# requests.
#
# So really, the Doorman is the only component that can estimate this probability.
#
# TODO: the classification might work better if it takes into account missing features
#

import bayes
import sys
import os
import argparse

import threading
import logging
import Queue
import time

DIRNAME = os.path.dirname(os.path.realpath(__file__))
sys.path.append(os.path.join(DIRNAME, 'gen-py'))
sys.path.append(os.path.join(DIRNAME, '..', 'common'))
sys.path.append(os.path.join(DIRNAME, '..', 'bouncer'))

import log

import import_thrift_lib

from thrift.transport import TSocket
from thrift.transport import TTransport
from thrift.protocol import TBinaryProtocol
from thrift.server import TServer
from thrift.Thrift import TException

from SignatureService import SignatureService
from SignatureService.ttypes import *

from bouncer_common import Config

class LearnThread(threading.Thread):

    def __init__(self, queue, sig_file, max_sample_size, update_requests, \
        min_delay, max_delay, bayes_classifier, logger):
        '''
        creates a new signature whenever it receives at least update_requests requests
        or max_delay seconds have passed since that last signature.
        At leat min_delay seconds must pass between signature generations
        '''
        threading.Thread.__init__(self)
        self.queue = queue
        self.bayes_classifier = bayes_classifier

        # make sure bayes_classifier is valid
        test = bayes.Classifier( [], [], **self.bayes_classifier)

        self.sig_file = sig_file
        self.max_sample_size = max_sample_size
        self.update_requests = update_requests
        self.min_delay = min_delay
        self.max_delay = max_delay
        self.logger = logger

    def tokenize(self, request_str):
        return bayes.splitTokensUrl(request_str)

    def run(self):
        self.evicted = []
        self.completed = []

        while True:
            last_update = time.time()
            num_new_samples = 0
            # read in a bunch of request_str's until its time to create a new signature
            while not (num_new_samples >= self.update_requests and (time.time() - last_update >= self.min_delay)):
                try:
                    timeout = self.max_delay - (time.time() - last_update)
                    if timeout <= 0.0:
                        raise Queue.Empty()
                    self.logger.debug("waiting for %fs before next update", timeout)
                    category, request_str = self.queue.get(timeout=timeout)
                    self.logger.debug("Received sample: %s --> %s", category, request_str)
                    num_new_samples += 1
                    if category == "evicted":
                        self.evicted.append(self.tokenize(request_str))
                    elif category == "completed":
                        self.completed.append(self.tokenize(request_str))
                    else:
                        self.logger.error("Unexpected message from queue: (%s, %s)", category, request_str)
                except Queue.Empty:
                    self.logger.info("update_time expired; time to build a new signature")
                    break

            elapsed = time.time() - last_update
            self.logger.info("Time since last update: %fs", elapsed)
            self.logger.info("Samples since last update: %d", num_new_samples)

            self.logger.info("Evaluating signature accuracy")
            validate = bayes.Validate(self.evicted, self.completed, self.logger)
            tp, fp, tn, fn = validate.validate()
            self.logger.info("tp = %d", self.tp)
            self.logger.info("fp = %d", self.fp)
            self.logger.info("tn = %d", self.tn)
            self.logger.info("fn = %d", self.fn)
            self.logger.info("fp-rate = %f", float(self.fp) / (self.fp + self.tn))
            self.logger.info("fn-rate = %f", float(self.fn) / (self.fn + self.tp))

            self.logger.info("Building new signature")
            self.evicted = self.evicted[-self.max_sample_size:]
            self.completed = self.completed[-self.max_sample_size:]
            for i, sample in enumerate(self.evicted):
                self.logger.info("evicted-%d: %s", i, sample)
            for i, sample in enumerate(self.completed):
                self.logger.info("completed-%d: %s", i, sample)
            classifier = bayes.Classifier(self.evicted, self.completed, **self.bayes_classifier)
            with open(self.sig_file, 'w') as f:
                f.write(str(classifier) + "\n")



class SigServer:

    def __init__(self, sig_file, addr, port, max_sample_size, update_requests, \
        min_delay, max_delay, bayes_classifier, logger):

        self.sig_file = sig_file
        self.bayes_classifier = bayes_classifier

        classifier = bayes.Classifier( [], [], **self.bayes_classifier)
        with open(self.sig_file, 'w') as f:
            f.write(str(classifier) + "\n")

        self.addr = addr
        self.port = port
        self.queue = Queue.Queue()
        self.max_sample_size = max_sample_size
        self.update_requests = update_requests
        self.min_delay = min_delay
        self.max_delay = max_delay
        self.logger = logger

    def evicted(self, request_str):
        self.queue.put(("evicted", request_str))

    def completed(self, request_str):
        self.queue.put(("completed", request_str))

    def run(self):

        # launch learn thread
        lt = LearnThread(self.queue, self.sig_file, self.max_sample_size, self.update_requests, self.min_delay, self.max_delay, self.bayes_classifier, self.logger)
        lt.start()

        # Launch thrift service
        processor = SignatureService.Processor(self)
        transport = TSocket.TServerSocket(port=self.port)
        tfactory = TTransport.TBufferedTransportFactory()
        pfactory = TBinaryProtocol.TBinaryProtocolFactory()

        server = TServer.TThreadPoolServer(processor, transport, tfactory, pfactory)

        self.logger.info("Starting Signature Service on port %d" % self.port)
        server.serve()
        self.logger.info("finished")

if __name__ == "__main__":

    parser = argparse.ArgumentParser(description='Signature service')
    parser.add_argument("-c", "--config", type=str, default=None,
                        help="Default=%(default)s. Config filename. If given, then overrides all other command line args.")
    parser.add_argument("-f", "--sig-file", type=str, default="signature.txt",
                        help="Default=%(default)s. Signature file that sigservice produces. Should be mounted "
                        "on ramdisk for maximum performance.")
    parser.add_argument("-bm", "--bayes-model-size", type=int, default=5000,
                        help="Default=%(default)d. Size of Bayes model; see bayes.py")
    parser.add_argument("-br", "--bayes-rare-threshold", type=float, default=0.01,
                        help="Default=%(default)f. Rarity threshold for Bayes model; see bayes.py")
    parser.add_argument("-a", "--addr", type=str, default="127.0.0.1",
                        help="Default=%(default)s. Alert router will send notifcations to SigService at ADDR")
    parser.add_argument("-p", "--port", type=int, default=4001,
                        help="Default=%(default)d. Port to listen from")
    parser.add_argument("-m", "--max-sample-size", type=int, default=100,
                        help="Default=%(default)d. Maximium number of samples to use (from each category) when developing a signature")
    parser.add_argument("-u", "--update-requests", type=int, default=100,
                        help="Default=%(default)d. If UPDATE-REQUESTS samples come in (and at least MIN-DELAY seconds have elapsed since "
                        "the last signature) then develop a new signature")
    parser.add_argument("-n", "--min-delay", type=float, default=1.0,
                        help="Default=%(default)f. Minimum number of seconds that must pass between successive signature updates")
    parser.add_argument("-x", "--max-delay", type=float, default=5.0,
                        help="Default=%(default)f. Maximum number of seconds that may pass before a new signature is generated")


    log.add_arguments(parser)
    args = parser.parse_args()
    logger = log.getLogger(args)

    if args.config != None:
        logger.info("Config file: %s", args.config)
        try:
            with open(args.config) as f:
                config = Config(f)
        except:
            logger.critical("Error while parsing config file. View bouncer/bouncer_common.py for format of config.")
            raise
        logger.info("config: %s", config)
        s = SigServer(logger=logger, **config.sigservice)
    else:
        logger.info("Command line arguments: %s" % str(args))
        s = SigServer(
            args.sig_file,
            args.addr,
            args.port,
            args.max_sample_size,
            args.update_requests,
            args.min_delay,
            args.max_delay,
            {
                "model_size" : args.bayes_model_size,
                "rare_threshold" : args.bayes_rare_threshold,
            },
            logger)

    s.run()

