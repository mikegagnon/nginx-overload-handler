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
# ==== Simulator for Beer Garden ====
# Objective:
#   Simulate Beer Garden at sufficient fidelity that we can explore
#   adaptive behaviors Doorman. Behavior of simualted Beer Garden
#   should generally be predictive of real-world Beer Garden performance &
#   behavior
#.
#   Note: Not trying to simulate every type of effect. For example,
#   this simulator will not accurately simulate the effects of the Doorman
#   being overloaded.
#
#   Also useful as a specification for Beer Garden
#
# Design:
#   Event driven simulation using greenlets.
#   Each agent in the system is implemented as a greenlet. Agents:
#       * visitors
#       * attackers
#       * upstream_workers
#       * doorman
#       * load balancer
#       * bouncer
#       * signature_service
#       * event_loop
#
# TODO: ensure all exceptions get propagated to critical and break execution
#

import os
import sys
import argparse
import json
import greenlet
from random import choice
import heapq
import logging
DIRNAME = os.path.dirname(os.path.realpath(__file__))

sys.path.append(os.path.join(DIRNAME, '..', 'common'))
sys.path.append(os.path.join(DIRNAME, '..', 'bouncer'))

import log
log.FORMATTER_LOGFILE = logging.Formatter("%(asctime)s - %(levelname)10s - %(process)d - %(filename)20s : %(funcName)30s - %(message)s")
log.FORMATTER_STDERR = logging.Formatter("%(levelname)10s - %(message)s")

import bouncer_common

def isInt(x):
    return isinstance(x, int)

def isFloat(x):
    return isinstance(x, float)

def isBool(x):
    return isinstance(x, bool)

def isListFloat(x):
    return isinstance(x, list) and all([isFloat(item) for item in x])

def isArrive(x):
    if not isinstance(x, dict):
        return False
    if "exponential" in x and isFloat(x["exponential"]):
        return True
    if "exact" in x and isFloat(x["exact"]):
        return True
    return False

config_keys = {
       "time" : isFloat,
       "doorman_burst_len" : isInt,
       "doorman_sleep_time" : isInt,
       "doorman_expire_delta" : isInt,
       "doorman_init_missing_bits" : isInt,
       "num_server_cores" : isInt,
       "num_total_backends" : isInt,
       "num_spare_backends" : isInt,
       "attack_hash_per_sec" : isFloat,
       "attack_sleep" : isBool,
       "attack_jobs" : isListFloat,
       "attack_cores" : isInt,
       "legit_hash_per_sec" : isFloat,
       "legit_jobs" : isListFloat,
       "legit_arrive" : isArrive
    }

def validateConfig(config):
    '''fd is an open file containing the config
    returns a map with the following keys and values:

    Simulation control:
        time : float, number of simulated minutes

    Doorman:
        doorman_burst_len : int
        doorman_sleep_time : int, milliseconds
        doorman_expire_delta : int seconds
        doorman_init_missing_bits : 0 <= int <= 128

    Server:
        num_server_cores : int

    Bouncer:
        num_total_backends : int
        num_spare_backends : int

    Attacker:
        attack_hash_per_sec : float
        attack_sleep : boolean (does the attacker sleep when instructed)
        attack_jobs : list of floats, where each value represents the cpu-time
            requirement of a randomly selected attack job
        attack_cores : int

    Legit visitor:
        legit_hash_per_sec : float
        legit_jobs : list of floats, where each value represents the cpu-time
            requirement of a randomly selected legit job
        legit_arrive : can be either
            { "exponential" : mean } where mean is the average amount of
                time elapsed between adjacent legit requests, OR
            {"exact" : delay} where delay is the exact amount of time
                between adjacent legit requests
    '''

    for key, valid_func in config_keys.items():
        if key not in config:
            raise ValueError("Config is missing value for '%s'" % key)
        value = config[key]
        if not valid_func(value):
            raise ValueError("The value for '%s' is invalid: %s" % (key, value))

# Events
###############################################################################

class Event:
    def __init__(self, sim, delay):
        '''Fire the event in delta seconds'''
        self.time = sim.time + delay
        self.sim = sim

class GameOverEvent(Event):
    def __str__(self):
        return "GameOverEvent()"

class ReceiveMessageEvent(Event):
    def __init__(self, sim, delay, dest, message):
        Event.__init__(self, sim, delay)

        assert(isinstance(dest, greenlet.greenlet))
        self.dest = dest

        assert(isinstance(message, Message))
        self.message = message

    def execute(self):
        self.dest.switch(self.message)

    def __str__(self):
        return "ReceiveMessageEvent(dest=%s, message=%s)" % \
            (self.sim.greenlets[self.dest], self.message)

class NewVisitorEvent(Event):

    def getArriveDelay(self):
        '''Returns number of seconds until next new VisitorEvent'''
        if ("exact" in self.sim.config.legit_arrive):
            return self.sim.config.legit_arrive["exact"]
        else:
            raise ValueError("Unsupported legit_arrive value: %s" % self.sim.config.legit_arrive)

    def execute(self):
        # (1) schedule the next NewVisitorEvent
        delay = self.getArriveDelay()
        nextNewVisitorEvent = NewVisitorEvent(self.sim, delay)
        self.sim.schedule(nextNewVisitorEvent)

        # (2) Create a visitor agent and switch to it
        name = "visitor_%d" % self.sim.next_visitor_id
        self.sim.next_visitor_id += 1
        visitorAgent = self.sim.greenlet(VisitorAgent, name)
        visitorAgent.switch(self.sim)

    def __str__(self):
        return "NewVisitorEvent()"

# Messages
###############################################################################

class Message:
    def __init__(self, sim):
        self.sender = greenlet.getcurrent()
        self.sim = sim

class ForwardedMessage(Message):
    def __init__(self, sim, message):
        Message.__init__(self, sim)
        assert(isinstance(message, Message))
        self.message = message

    def __str__(self):
        return "ForwardedMessage(sender=%s, message=%s)" % \
            (self.sim.greenlets[self.sender], self.message)

class WebRequestMessage(Message):
    def __init__(self, sim, job_time, key, expire):
        Message.__init__(self, sim)
        self.job_time = job_time
        self.key = key
        self.expire = expire

    def __str__(self):
        return "WebRequestMessage(sender=%s, job_time=%f, key=%s, expire=%s)" % \
            (self.sim.greenlets[self.sender], self.job_time, self.key, self.expire)

class WebResponseMessage(Message):
    def __init__(self, sim, status_code, content, puzzle, expire):
        Message.__init__(self, sim)

        # 200, 502, etc.
        self.status_code = status_code

        assert(content == "puzzle" or content == "requested_page")
        self.content = content

        #the number of hashes required to solve the puzzle
        if (content == "requested_page"):
            assert(puzzle == None)
        self.puzzle = puzzle

        # None or the number of seconds until the puzzle expires
        if (content == "requested_page"):
            assert(expire == None)
        self.expire = expire

    def __str__(self):
        return "WebResponseMessage(sender=%s, status_code=%d, content=%s, puzzle=%s, expire=%s)" % \
            (self.sim.greenlets[self.sender], self.status_code, self.content, self.puzzle, self.expire)

# Agents (instantiated as greenlets)
###############################################################################
# agent definitions follows UpperCamelCase convention because they are really
# more like class definitions than normal functions

def VisitorAgent(sim):
    job_time = choice(sim.config.legit_jobs)

    # Send request to Doorman
    request = WebRequestMessage(
        sim,
        job_time,
        key=False,
        expire=None)
    sim.logger.info("%s sending request: %s", sim.logprefix(), request)
    sim.sendMessage(sim.doorman, request, 0.1)

    # Wait for response
    response = sim.event_loop.switch()
    assert(isinstance(response, WebResponseMessage))
    assert(greenlet.getcurrent().parent == sim.event_loop)
    sim.logger.info("%s received response: %s", sim.logprefix(), response)

def DoormanAgent(sim):
    assert(greenlet.getcurrent().parent == sim.event_loop)

    while True:

        # Wait for request
        request = sim.event_loop.switch()
        assert(isinstance(request, WebRequestMessage))
        assert(greenlet.getcurrent().parent == sim.event_loop)
        sim.logger.info("%s received request: %s", sim.logprefix(), request)

        # Forward request to load balancer
        forward = ForwardedMessage(sim, request)
        sim.sendMessage(sim.load_balancer, forward, 0.1)
        sim.logger.info("%s forwarding request to load balancer: %s", sim.logprefix(), forward)

def LoadBalancerAgent(sim):
    assert(greenlet.getcurrent().parent == sim.event_loop)

    while True:

        # Wait for request
        fwd_request = sim.event_loop.switch()
        assert(isinstance(fwd_request, ForwardedMessage))
        request = fwd_request.message
        assert(isinstance(request, WebRequestMessage))
        assert(greenlet.getcurrent().parent == sim.event_loop)
        sim.logger.info("%s received forwarded request: %s", sim.logprefix(), request)

        response = WebResponseMessage(
            sim,
            status_code = 200,
            content = "requested_page",
            puzzle = None,
            expire = None)
        sim.logger.info("%s sending response: %s", sim.logprefix(), response)
        sim.sendMessage(request.sender, response, request.job_time)

def EventLoopAgent(sim):

    # Launch the doorman
    sim.doorman = sim.greenlet(DoormanAgent, "doorman")
    sim.doorman.switch(sim)

    # Launch the load balancer
    sim.load_balancer = sim.greenlet(LoadBalancerAgent, "load_balancer")
    sim.load_balancer.switch(sim)

    # Schedule the game_over event
    game_over = GameOverEvent(sim, delay=sim.config.time * 60.0)
    sim.schedule(game_over)

    # Schedule the first visitor
    new_visitor = NewVisitorEvent(sim, delay=0.0)
    sim.schedule(new_visitor)

    while True:
        event = sim.nextEvent()
        sim.time = event.time
        sim.logger.debug("%s %s", sim.logprefix(), event)
        if event == game_over:
            break
        event.execute()

# The simulator and supportign classses
###############################################################################

class PriorityQueue:

    def __init__(self):
        self.q = []
        self.count = 0

    def push(self, event):
        '''event must have time field'''
        self.count += 1
        entry = (event.time, self.count, event)
        heapq.heappush(self.q, entry)

    def pop(self):
        if len(self.q) == 0:
            raise ValueError("Tried pop an empty queue")
        _, _, event = heapq.heappop(self.q)
        return event

class Config:
    def __init__(self, config_dict):
        self.__dict__.update(config_dict)

class Simulator:

    def __init__(self, config_file, logger, **kwargs):
        self.logger = logger
        with open(config_file) as f:
            config_dict = json.load(f)

        self.logger.debug("config_file = %s", json.dumps(config_dict, sort_keys=True, indent=4))
        self.logger.debug("kwargs = %s", json.dumps(kwargs, sort_keys=True, indent=4))
        config_dict.update(kwargs)
        self.logger.info("config = %s", json.dumps(config_dict, sort_keys=True, indent=4))
        validateConfig(config_dict)
        self.config = Config(config_dict)

        # maps greenlet objects to name-strings
        self.greenlets = {}

    def greenlet(self, func, name):
        agent = greenlet.greenlet(func)
        self.greenlets[agent] = name
        return agent

    def logprefix(self):
        return "%6.3f - %15s -" % (self.time, self.greenlets[greenlet.getcurrent()])

    def schedule(self, event):
        self.events.push(event)

    def nextEvent(self):
        return self.events.pop()

    def sendMessage(self, dest, message, delay):
        event = ReceiveMessageEvent(self, delay, dest, message)
        self.schedule(event)

    def run(self):
        self.time = 0
        self.next_visitor_id = 1
        self.events = PriorityQueue()
        self.event_loop = sim.greenlet(EventLoopAgent, "event_loop")
        self.event_loop.switch(self)

if __name__ == "__main__":

    default_config_filename = os.path.join(DIRNAME, "configs", "default.json")

    parser = argparse.ArgumentParser(description='Simulates Beer Garden')
    parser.add_argument("-c", "--config", type=str, default=default_config_filename,
                    help="Default=%(default)s. The configuration for the simulation. See source " \
                    "for documentation on file format.")

    log.add_arguments(parser)
    args = parser.parse_args()
    args.config = os.path.abspath(args.config)
    logger = log.getLogger(args)
    logger.info("Command line arguments: %s" % str(args))

    sim = Simulator(args.config, logger)
    sim.run()

