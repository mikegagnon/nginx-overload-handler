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

class NotEnoughDataException(Exception):
    pass

def splitTokens(string, regex_str="\s+", ngrams=1):
    '''
    splits string according to regex and returns set of n-gram tokens
    '''
    r = re.compile(regex_str)
    token_list = r.split(string)
    tokens = set()
    for i in xrange(len(token_list) - ngrams + 1):
        print i
        seq = str(token_list[i:i + ngrams])
        tokens.add(seq)
    return tokens

class Validate:

    def __init__(self, observations, model_size=5000, small_model=True):
        assert(len(observations.keys()) == 2)
        assert("good" in observations)
        assert("bad" in observations)

        self.observations = observations
        self.model_size = model_size
        self.small_model = small_model

    def test_fold(self, test, train):
        print "fold"
        print "test: %s" % test
        print "train: %s" % train
        classifier = Classifier(train, self.model_size)
        tp = 0
        fp = 0
        tn = 0
        fn = 0
        for good_example in test["good"]:
            result = classifier.classify(good_example, self.small_model)
            print "classified good_example %s as %s" % (good_example, result)
            if result == "good":
                tn += 1
            else:
                fp += 1
        for bad_example in test["bad"]:
            result = classifier.classify(bad_example, self.small_model)
            print "classified bad_example %s as %s" % (bad_example, result)
            if result == "bad":
                tp += 1
            else:
                fn += 1
        print "tp = %d" % tp
        print "fp = %d" % fp
        print "tn = %d" % tn
        print "fn = %d" % fn
        self.tp += tp
        self.fp += fp
        self.tn += tn
        self.fn += fn
        print

    def validate(self, num_folds=10):
        # do num_folds_times
        # train on 9/10ths of data
        # test on the other 10ths of data
        # for now to make life simple, use random sampling to produce folds
        self.tp = 0
        self.fp = 0
        self.tn = 0
        self.fn = 0
        num_test = {}
        for cat, exemplars in self.observations.items():
            num_exemplars = len(exemplars)
            num_test_cat = max(1, int(float(num_exemplars) / float(num_folds)))
            num_train_cat = num_exemplars - num_test_cat
            if num_test_cat < 1 or num_train_cat < 1:
                raise NotEnoughDataException(cat)
            num_test[cat] = num_test_cat

        for i in xrange(0, num_folds):
            test = {}
            train = {}
            for cat, exemplars in self.observations.items():
                random.shuffle(exemplars)
                test_list = exemplars[0:num_test[cat]]
                train_list = exemplars[num_test[cat]:]
                test[cat] = test_list
                train[cat] = train_list
            self.test_fold(test, train)

        sys.stderr.write("tp = %d\n" % self.tp)
        sys.stderr.write("fp = %d\n" % self.fp)
        sys.stderr.write("tn = %d\n" % self.tn)
        sys.stderr.write("fn = %d\n" % self.fn)

class Classifier:

    def __init__(self, observations, model_size=5000):
        '''
        obsevations is a dict that maps category names (e.g. "good" and "bad")
        to a list of exemplars. Each exemplar is a set of tokens.
        Example observations ==
        {
            "good" : [
               set("a", "b", "c"),
               set("c", "d")
            ],
            "bad" : [
               set("a"),
               set("b", "c", "d"),
               set("x", "y"),
            ]
        }
        '''

        self.observations = observations
        self.buildModels()
        self.buildFeatureRank()
        self.abridgeModel(model_size)

    def abridgeModel(self, model_size):
        '''
        remove all but the N most important tokens from the model
        (where N == model_size)
        '''

        tokens = self.tokenRank[:model_size]
        tokens = [pair[1] for pair in tokens]
        tokens = set(tokens)
        #print "tokens = %s" % tokens

        self.small_token_model = {}
        self.small_tokens = set()
        for (token, cat), prob in self.token_model.items():
            if token in tokens:
                self.small_token_model[(token, cat)] = prob
                self.small_tokens.add(token)

        #print "small_token_model"
        #for (token, category), prob in sorted(self.small_token_model.items()):
            #print "%s --> %f" % ((token, category), prob)


    def buildFeatureRank(self):
        '''
        builds an abridged version of self.token_model for only the most important
        features
        '''

        category_pairs = list(itertools.combinations(self.category_model.keys(), 2))

        # importance of a token t = abs(P(t | good) - P(t | bad))
        self.tokenRank = []
        for token, _ in self.token_freq.items():
            max_importance = 0.0
            for cat1, cat2 in category_pairs:
                p1 = self.token_model.get((token, cat1), 0.0)
                p2 = self.token_model.get((token, cat2), 0.0)
                importance = abs(p1 - p2)
                max_importance = max(max_importance, importance)
            self.tokenRank.append((max_importance, token))

        self.tokenRank.sort(reverse=True)
        #print "importance"
        #for importance, token in self.tokenRank:
            #print "token %s --> %f" % (token, importance)

    def buildModels(self):
        '''
        initializes self.token_model, self.category_model, and self.token_freq
        token_model maps (token, category) pairs to
        P(TOKEN == token | CATEGORY == category), i.e. the probability
        that you observe that token, given that the instance belongs to category
        category_model maps category to the probability that a given exemplar
        belongs to category
        token_freq maps each token the probability that token is observed (regardless
        of category)
        '''
        self.token_model = {}
        self.total_observations = 0.0
        self.token_freq = {}
        for category in self.observations:
            self.total_observations += float(len(self.observations[category]))
            for exemplar in self.observations[category]:
                for token in exemplar:
                    if token not in self.token_freq:
                        self.token_freq[token] = 0.0
                    self.token_freq[token] += 1.0
                    if (token, category) not in self.token_model:
                        self.token_model[(token, category)] = 0.0
                    self.token_model[(token, category)] += 1.0

        for token in self.token_freq:
            self.token_freq[token] /= self.total_observations
            #print "%s --> %f" % (token, self.token_freq[token])

        num_categories = float(len(self.observations.keys()))
        self.category_model = {}
        for category in self.observations:
            self.category_model[category] = float(len(self.observations[category])) / self.total_observations
            #print "%s --> %f" % (category, self.category_model[category])

        #print "token_model"
        min_prob = 1.0
        for (token, category), count in sorted(self.token_model.items()):
            self.token_model[(token, category)] = float(count) / float(len(self.observations[category]))
            prob = self.token_model[(token, category)]
            #print "%s --> %f" % ((token, category), prob)
            min_prob = min(min_prob, prob)

        self.default_prob = min_prob / 2.0
        #print "default_prob = %f" % self.default_prob

    def classify(self, tokens, small_model=True):
        '''
        for each cat:
            p(cat | features) = P(cat) * product[P(f_i|cat) ]
        '''
        if small_model:
            model = self.small_token_model
            model_tokens = self.small_tokens
        else:
            model = self.token_model
            model_tokens = self.token_freq.keys()

        #print "model"
        #print model

        products = {}
        for cat in self.category_model:
            products[cat] = self.category_model[cat]

        # wrong -- also need to take 1 - prob for tokens that don't exist
        # should probably just loop around tokens in the small model
        #for token in tokens:
        #    for cat in self.category_model:
        #print "classify(%s): " % tokens
        for token in model_tokens:
            for cat in self.category_model:
                # prob = probability that an exemplar from cat has this token
                prob = model.get((token, cat), self.default_prob)
                #present = "here"
                if token not in tokens:
                    # prob = probability that an exemplar from cat DOES NOT have this token
                    prob = 1.0 - prob
                    #present = "----"
                #print "%s %s, %s --> %f" % (present, token, cat, prob)
                products[cat] *= prob

        max_product = 0.0
        max_cat = None
        for cat, product in products.items():
            if product > max_product:
                max_product = product
                max_cat = cat

        #print "classify(%s) --> %s" % (tokens, max_cat)
        return max_cat

if __name__ == "__main__":
    import os
    d = "/home/beergarden/Desktop/trec05p-1/spam25"
    num_ham = 1000
    num_spam = 1000
    index_filename = os.path.join(d, "index")
    ham_filenames = set()
    spam_filenames = set()
    with open(index_filename) as f:
        for line in f:
            parts = line.split()
            assert(len(parts) == 2)
            assert(parts[0] == "spam" or parts[0] == "ham")
            filename = os.path.join(d, parts[1])
            if parts[0] == "spam":
                spam_filenames.add(filename)
            else:
                ham_filenames.add(filename)

    ham_filenames = list(ham_filenames)
    spam_filenames = list(spam_filenames)
    random.shuffle(ham_filenames)
    random.shuffle(spam_filenames)
    ham_filenames = ham_filenames[0:num_ham]
    spam_filenames = spam_filenames[0:num_spam]

    observations = {
        "good" : [],
        "bad" : []
    }

    for filename in ham_filenames:
        with open(filename) as f:
            tokens = splitTokens(f.read(), "\s+", 3)
            observations["good"].append(tokens)

    for filename in spam_filenames:
        with open(filename) as f:
            tokens = splitTokens(f.read(), "\s+", 3)
            observations["bad"].append(tokens)

    v = Validate(observations)
    v.validate()

