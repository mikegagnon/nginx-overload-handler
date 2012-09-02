#!/usr/bin/env python
#
# Copyright 2012 Mike Gagnon
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
################################################################################
#
# the Variate class allows you to efficiently generate random variates using
# an arbitrary distribution of tokens
#

import random

# Variate nodes form a binary tree
class Variate:

    # tokens is either a list or a dict of (token, count) pairs.
    # increasing max_node_size increases the runtime of the final step but
    # decreases total memory usage. I imagine 1000 should be good for most
    # environments.
    def __init__(self, tokens, max_node_size = 1000):
        if isinstance(tokens, dict):
            tokens = tokens.items()

        self.count = sum([pair[1] for pair in tokens])

        if len(tokens) <= max_node_size:
            self.tokens = tokens
            self.left = None
            self.right = None
        else:
            self.tokens = None
            length = len(tokens)
            self.left = Variate(tokens[:length/2], max_node_size)
            self.right = Variate(tokens[length/2:], max_node_size)

    # selects a random token according to the distribution of token counts
    # equivalent to creating a single list where each token appears token_count
    # times and then choosing a random uniformly at random
    def getRand(self):
        index = random.randint(0, self.count - 1)
        return self.get(index)

    def get(self, index):

        if self.tokens != None:
            if index >= self.count:
                raise ValueError("index out of boundsl index == %d > " \
                    "self.count == %d" % (index, self.count))
            current = 0
            i = 0
            while current <= index:
                pair = self.tokens[i]
                current += pair[1]
                i += 1
            return pair[0]
        else:
            if index < self.left.count:
                return self.left.get(index)
            else:
                return self.right.get(index - self.left.count)
