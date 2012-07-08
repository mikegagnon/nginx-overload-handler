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

import json

class Bayes:

    def __init__(self, observations):
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
        self.buildModel()

    def buildModel(self):
        '''
        initializes self.token_model, which maps (token, category) pairs to
        P(TOKEN == token | CATEGORY == category), i.e. the probability
        that you observe that token, given that the instance belongs to
        category
        '''
        self.token_model = {}
        self.total_observations = 0.0
        for category in self.observations:
            self.total_observations += float(len(self.observations[category]))
            for exemplar in self.observations[category]:
                for token in exemplar:
                    if (token, category) not in self.token_model:
                        self.token_model[(token, category)] = 0.0
                    self.token_model[(token, category)] += 1.0

        num_categories = float(len(self.observations.keys()))
        self.category_model = {}
        for category in self.observations:
            self.category_model[category] = float(len(self.observations[category])) / self.total_observations
            print "%s --> %f" % (category, self.category_model[category])

        for (token, category), count in sorted(self.token_model.items()):
            self.token_model[(token, category)] = float(count) / float(len(self.observations[category]))
            print "%s --> %f" % ((token, category), self.token_model[(token, category)])


x = {
    "good" : [
       set(["a", "b", "c"]),
       set(["c", "d"])
    ],
    "bad" : [
       set(["a"]),
       set(["b", "c", "d"]),
       set(["x", "y"]),
    ]
}

Bayes(x)
