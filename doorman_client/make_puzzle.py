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
# ==== make_puzzle.py ====
#
# Use the client puzzle algorithm as described in "Client Puzzles: A
# Cryptographic Countermeasure Against Connection Depletion Attacks."
# http://www.rsa.com/rsalabs/node.asp?id=2050
#
# The general idea is as follows.
#   - Let x = hash(s, r), where s is a secret string (only known to the server)
#     and r is the text of the request
#   - Let y = hash(x)
#   - Let the puzzle be the tuple (r, y, truncate(x), b), where truncate(x) is the
#     "truncated "version of x, i.e. x but with b bits removed
#   - Give the puzzle to the client
#       - Note, the client does not know the value x
#   - The client solves the puzzle by guessing various values for the value x,
#     (i.e. a brute force search). We'll call a particular guess x'.
#   - The client knows they have found the solution when hash(x') = y
#   - The client re-sends the request, along with the solution x.
#   - The server can quickly check whether a solution is valid by calculating
#     hash(s,r); if it matches the given x then the server knows that the
#     client has spent the CPU time to brute-force the hash
#   - The protocol also uses nonces to prevent replay attacks
#

import sys
import hashlib

def truncate_hash(hexdigest, bits):
    '''bits is the number of bits to remove (least significant bits)'''
    val = int(hexdigest, 16)
    val = val >> bits
    val = val << bits
    return "%064x" % val

def gen_puzzle(puzzle_size, request, secret):
    x = hashlib.sha256(secret + request).hexdigest()
    y = hashlib.sha256(x).hexdigest()
    return (x, (request, y, truncate_hash(x, puzzle_size), puzzle_size))

puzzle_size = 5
secret = "foobar"
request = sys.stdin.read()

x, puzzle = gen_puzzle(puzzle_size, request, secret)
print x
print puzzle

