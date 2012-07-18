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
# ==== bayes.py ====
#

import sys
import itertools
import random
import json
import re
import os
import argparse

import logging

DIRNAME = os.path.dirname(os.path.realpath(__file__))
sys.path.append(os.path.join(DIRNAME, '..', 'common'))

import log

class Validate:

    def __init__(self, positive, negative, logger, **kwargs):
        self.positive = positive
        self.negative = negative
        self.logger = logger
        self.kwargs = kwargs

    def test_fold(self, test_positive, test_negative, train_positive, train_negative, fold_num):
        classifier = Classifier(train_positive, train_negative, **self.kwargs)
        tp = 0
        fp = 0
        tn = 0
        fn = 0
        count = 0
        for positive_example in test_positive:
            count += 1
            result = classifier.classify(positive_example)
            if result == "positive":
                tp += 1
                self.logger.debug("(%d, %d) true positive", fold_num, count)
            else:
                fn += 1
                self.logger.debug("(%d, %d) false neative", fold_num, count)
        for negative_example in test_negative:
            count += 1
            result = classifier.classify(negative_example)
            if result == "negative":
                tn += 1
                self.logger.debug("(%d, %d) true negative", fold_num, count)
            else:
                fp += 1
                self.logger.debug("(%d, %d) false positive", fold_num, count)
        self.tp += tp
        self.fp += fp
        self.tn += tn
        self.fn += fn

    def validate(self, num_folds=10):
        # do num_folds_times
        # train on 9/10ths of data
        # test on the other 10ths of data
        # for now to make life simple, use random sampling to produce folds
        self.tp = 0
        self.fp = 0
        self.tn = 0
        self.fn = 0

        for i in xrange(0, num_folds):
            random.shuffle(self.positive)
            random.shuffle(self.negative)

            num_test_positive = max(1, int(len(self.positive) / float(num_folds)))
            num_test_negative = max(1, int(len(self.negative) / float(num_folds)))

            train_positive = self.positive[0:num_test_positive]
            test_positive = self.positive[num_test_positive:]
            train_negative = self.negative[0:num_test_negative]
            test_negative = self.negative[num_test_negative:]

            self.test_fold(test_positive, test_negative, train_positive, train_negative, i)

        sys.stderr.write("tp = %d\n" % self.tp)
        sys.stderr.write("fp = %d\n" % self.fp)
        sys.stderr.write("tn = %d\n" % self.tn)
        sys.stderr.write("fn = %d\n" % self.fn)

class Prob:

    def __init__(self):
        '''
        for a given token,
        positive_count = num occurences of token in positive dataset
        positive_prob = P(token | positive)
        similar definition for negative
        '''
        self.positive_count = 0.0
        self.negative_count = 0.0
        self.positive_prob = None
        self.negative_prob = None

    def inc(self, category):
        assert(category == "positive" or category == "negative")
        if category == "positive":
            self.positive_count += 1.0
        else:
            self.negative_count += 1.0

    def rank(self):
        return abs(self.positive_prob - self.negative_prob)

    def done(self, num_positive_messages, num_negative_messages):
        self.positive_count = max(self.positive_count, 0.5)
        self.negative_count = max(self.negative_count, 0.5)
        if num_positive_messages == 0:
            self.positive_prob = 1.0 / float(num_negative_messages + 1)
        else:
            self.positive_prob = self.positive_count / float(num_positive_messages)

        if num_negative_messages == 0:
            self.negative_prob = 1.0 / float(num_positive_messages + 1)
        else:
            self.negative_prob = self.negative_count / float(num_negative_messages)

    def __str__(self):
        return "rank=%f, pcount=%d, ncount=%d, pprob=%s, nprob=%s" % \
            (self.rank(),
            self.positive_count, self.negative_count, self.positive_prob, self.negative_prob)

class Classifier:

    def __init__(self, positive, negative, model_size=5000, rare_threshold=0.05):
        '''
        positive is a list of "positive" messages, where each message is a set of tokens
        And similarly for negative
        '''
        self.positive = positive
        self.negative = negative
        self.model_size = model_size
        self.rare_threshold = rare_threshold
        self.buildModel()

    def buildModel(self):
        '''
        sets self.model, which maps tokens to corresponding Prob objects
        sets self.positive_prior
        sets self.negative_prior
        '''

        num_positive_messages = len(self.positive)
        num_negative_messages = len(self.negative)
        total_messages = num_positive_messages + num_negative_messages
        self.positive_prior = 0.5
        self.negative_prior = 0.5

        model = {}

        # count tokens
        for category, messages in (("positive", self.positive), ("negative", self.negative)):
            for token in itertools.chain(*messages):
                if token not in model:
                    model[token] = Prob()
                model[token].inc(category)

        # calculate probabilities for tokens
        [token.done(num_positive_messages, num_negative_messages) for token in model.values()]

        # filter out rare tokens
        for token, prob in model.items():
            if max(prob.positive_prob, prob.negative_prob) < self.rare_threshold:
                del(model[token])

        # sort according to the information gain for each token, and take best N
        sorted_model = sorted(model.items(), reverse=True, cmp=lambda x,y: cmp(x[1].rank(), y[1].rank()))
        sorted_model = sorted_model[:self.model_size]

        self.model = dict(sorted_model)

    def __str__(self):
        items = sorted(self.model.items(), reverse=True, cmp=lambda x,y: cmp(x[1].rank(), y[1].rank()))
        lines = ["%s,%f,%f" % (token, prob.positive_prob, prob.negative_prob) for token, prob in items]
        return "\n".join(lines)


    def classify(self, message):

        positive_product = self.positive_prior
        negative_product = self.negative_prior

        for token in message:
            if token in self.model:
                positive_product *= self.model[token].positive_prob
                negative_product *= self.model[token].negative_prob

        if positive_product > negative_product:
            return "positive"
        else:
            return "negative"

def splitTokensNgrams(string, regex_str="\s+", ngrams=1):
    '''
    splits string according to regex and returns set of n-gram tokens
    '''
    r = re.compile(regex_str)
    token_list = r.split(string)
    token_list = filter(lambda t: t != '', token_list)
    tokens = set()
    for i in xrange(len(token_list) - ngrams + 1):
        seq = str(token_list[i:i + ngrams])
        tokens.add(seq)
    return tokens

def splitTokens(string, regex_str="\s+"):
    '''
    splits string according to regex and returns set of n-gram tokens
    '''
    r = re.compile(regex_str)
    tokens = r.split(string)
    tokens = filter(lambda t: t != '', tokens)
    return set(tokens)

invalid_url_char = re.compile("[^a-z0-9%]")
# TODO: urldecode?
def splitTokensUrl(string):
    return set(invalid_url_char.sub(' ', string.lower()).split())

def splitTokensMap(string, regex_str="\s+", map_func=str.lower):
    '''
    splits string according to regex and returns set of n-gram tokens
    '''
    tokens = splitTokens(string, regex_str)
    return set([map_func(t) for t in tokens])

def load_samples(filenames, do_lines=False, tokenize_func=splitTokensUrl):
    messages = []
    for filename in filenames:
        with open(filename, 'r') as f:
            if do_lines:
               temp_messages = f.readlines()
            else:
               temp_messages = [f.read()]
        temp_messages = [tokenize_func(m) for m in temp_messages]
        messages += temp_messages
    return messages

if __name__ == "__main__":
    cwd = os.getcwd()

    parser = argparse.ArgumentParser(description='Naive bayesian classifier')

    parser.add_argument("-o", "--output", choices=["validate", "model", "classify"], default="validate",
                    help="Default=%(default)s. Run a validation or output a model?")
    parser.add_argument("-p", "--positive", type=str, required=True, nargs="+",
                    help="REQUIRED. List of files containing positive samples")
    parser.add_argument("-n", "--negative", type=str, required=True, nargs="+",
                    help="REQUIRED. List of files containing negative samples")
    parser.add_argument("-c", "--classify", type=str, default=None,
                    help="REQUIRED iff OUTPUT = classify. String to classify.")
    parser.add_argument("-l", "--line", action='store_true',
                    help="If set then each line in sample files is considered a distinct sample. "
                    "(If not set then then each file is considered a different sample)")
    parser.add_argument("-m", "--model-size", type=int, default=5000,
                    help="Default=%(default)s. Number of features to include in model")
    parser.add_argument("-r", "--rare", type=float, default=0.05,
                    help="Default=%(default)s. A feature must occur in at least RARE proportion "
                    "of positive or negative samples for it to be part of the model")

    log.add_arguments(parser)
    args = parser.parse_args()
    logger = log.getLogger(args)

    positive = load_samples(args.positive, do_lines=args.line)
    negative = load_samples(args.negative, do_lines=args.line)

    if args.output == "validate":
        validate = Validate(positive, negative, logger, \
            model_size=args.model_size, rare_threshold=args.rare)
        validate.validate()
    elif args.output == "model":
        c = Classifier(positive, negative, model_size=args.model_size, rare_threshold=args.rare)
        print c
    elif args.output == "classify":
        if args.classify == None:
            raise ValueError()
        c = Classifier(positive, negative, model_size=args.model_size, rare_threshold=args.rare)
        print c.classify(splitTokensUrl(args.classify))
    else:
        raise ValueError()

