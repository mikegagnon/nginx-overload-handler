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

import log
log.FORMATTER_LOGFILE = logging.Formatter("%(asctime)s - %(levelname)10s - %(process)d - %(filename)20s : %(funcName)30s - %(message)s")
log.FORMATTER_STDERR = logging.Formatter("%(levelname)10s - %(message)s")

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

class UpstreamCpuEvent(ReceiveMessageEvent):
    pass

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

# Sent to an upstream worker when its job finishes successfully
class JobFinishMessage(Message):
    def __init__(self, sim, job):
        Message.__init__(self, sim)
        self.job = job

    def __str__(self):
        return "JobFinishMessage(sender=%s, job=%s)" % \
            (self.sim.greenlets[self.sender], self.job)

class KillJobMessage(Message):
    def __init__(self, sim, job):
        Message.__init__(self, sim)
        self.job = job

    def __str__(self):
        return "KillJobMessage(sender=%s, job=%s)" % \
            (self.sim.greenlets[self.sender], self.job)

class NewJobMessage(Message):
    def __init__(self, sim, job_time):
        Message.__init__(self, sim)
        self.job_time = job_time

    def __str__(self):
        return "NewJobMessage(sender=%s, job_time=%f)" % \
            (self.sim.greenlets[self.sender], self.job_time)

# Agents (instantiated as greenlets)
###############################################################################
# agent definitions follows UpperCamelCase convention because they are really
# more like class definitions than normal functions

def VisitorAgent(sim):
    assert(greenlet.getcurrent().parent == sim.event_loop)
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
        assert(fwd_request.sender == sim.doorman)
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

def UpstreamWorkerAgent(sim):
    assert(greenlet.getcurrent().parent == sim.event_loop)

    while True:

        # Wait for request
        fwd_request = sim.event_loop.switch()
        assert(isinstance(fwd_request, ForwardedMessage))
        assert(fwd_request.sender == sim.load_balancer)
        request = fwd_request.message
        assert(isinstance(request, WebRequestMessage))
        assert(greenlet.getcurrent().parent == sim.event_loop)
        sim.logger.info("%s received forwarded request: %s", sim.logprefix(), request)

        # add this job to the set of jobs burning the CPU on the upstream server
        sim.burnCpu(request.job_time)
        fwd_request = sim.event_loop.switch()

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

# TODO: unit tests
class PriorityQueue:

    class RemovedEvent:
        pass

    removedEvent = RemovedEvent()

    def __init__(self):
        self.q = []
        self.count = 0
        self.entries = {}
        self.num_items = 0

    # Does not actually remove the entry from the heap (because
    # that would require re-heapifying). Instead, just marks
    # it removed in the heap, that when this entry is popped
    # it will be skipped over. Profiling will tell if this is
    # a good algorithm for our workload
    def remove(self, event):
        self.num_items -= 1
        entry = self.entries.pop(event)
        entry[2] = PriorityQueue.removedEvent

    def push(self, event):
        '''event must have time field'''
        self.num_items += 1
        entry = [event.time, self.count, event]
        self.entries[event] = entry
        heapq.heappush(self.q, entry)

    def head(self):
        '''Returns the head of the queue without popping it'''
        while self.q:
            _, _, event = self.q[0]
            if event != PriorityQueue.removedEvent:
                return event
            else:
                heapq.heappop(self.q)
        raise ValueError("Tried pop an empty queue")

    def pop(self):
        self.num_items -= 1
        while self.q:
            _, _, event = heapq.heappop(self.q)
            if event != PriorityQueue.removedEvent:
                del self.entries[event]
                return event
        raise ValueError("Tried pop an empty queue")

class UpstreamJob:
    def __init__(self, message, job_time, job_id):
        assert(isinstance(message, NewJobMessage))
        self.message = message
        self.time = job_time
        self.job_id = job_id

    def __str__(self):
        return "UpstreamJob(job_id=%d, job_time=%f, message=%s)" % \
            (self.job_id, self.job_time, self.message)

# Perhaps implement this as an Agent, since it's essentially an event handler
class UpstreamCpu:
    '''Logic to figure out which upstream-worker jobs get how much CPU and when.
    Each upstream machine gets exactly one UpstreamCpu instance.'''

    # Design:
    # Each job's time field specifies how much cpu-time is needed to complet the job
    # Whenever an event occurs, update every jobs time field
    # How does it figure out what to update the time fields to?
    #   (1) Figure out how much wallclock time has elapsed since the previous event
    #   (2) Figure out how much cpu-time is allocatd to each job during that
    #       wallclock time
    #   Step (2) is greatly simplified by guarantee that the only time jobs enter
    #   and leave the system only happen at events. Thus cpu-time is function
    #   of number of jobs, number of cores, and wall clock time
    #

    def __init__(self, num_cores, sim, cpuAgent):
        ''' sim and cpuAgent are mostly treated like opaque objects and are
        only used to to pass along to Event objects when they're created, etc.
        The only value used from sim is sim.time
        '''
        self.sim = sim
        self.num_cores = num_cores
        self.jobs = set()
        self.nextJobId = 0

        self.cpuAgent = cpuAgent

        self.current_job_finish_event = None

        # the wallclock timestamp from the last event; used for measuring
        # elapsed wallclock time between successive events
        self.last_event_time = None

    def newJobFinishEvent(self, job):
        '''Assumes the state of the CPU has already been changed
        for the event currently being handled'''
        delay = dest = message = None
        return JobFinishEvent(self.sim, delay, dest, message)

    def getCpuSecPerWallSec(self):
        if len(self.jobs) <= self.num_cores:
            # If there are more cores than jobs, then each
            # job gets it's own CPU; therefore each job
            # will get 1.0 cpu-second per wallclock second
            return 1.0
        else:
            # Otherwise all jobs share all cpus precisely evenly
            return float(self.num_cores) / float(len(self.jobs))

    def getCpuSec(self, wall_clock_sec):
        '''Returns the number of CPU seconds each job will get over the next
        wall-clock seconds'''
        return wall_clock_sec * self.getCpuSecPerWallSec()

    def getWallSec(self, cpu_sec):
        '''Returns the number of wall-clock seconds needed execute cpu_sec CPU seconds'''
        return cpu_sec * (1.0 / self.getCpuSecPerWallSec())

    def updateJobs(self, time):
        '''
        Preconditions:
            during the time between self.last_clock and time,
            the number of jobs in the system did not change
        Postconditions:
            each job has made equal progress during the elapsed time.
            updates the time field for each job to reflect that status.
            Returns None, or a single job that has finished (and removes
            that job from the CPU). If multiple jobs have job.time == 0
            (i.e. multiple jobs should finish) then the job that finishes
            is the job that was added to the system first. An event should
            fire within the same time unit that will remove the next job.
        '''

        finished_jobs = set()

        if self.last_event_time != None:
            elapsed_sec = time - self.last_event_time
        else:
            elapsed_sec = 0.0

        cpu_sec = self.getCpuSec(elapsed_sec)

        # update job.time for all jobs
        for job in self.jobs:
            job.time -= cpu_sec
            assert(job.time >= 0.0)
            if job.time == 0.0:
                finished_jobs.add(job)

        if len(finished_jobs) == 0:
            return None

        finished_job = sorted(self.jobs, key=lambda job: job.job_id)[0]
        self.jobs.remove(finished_job)
        return finished_job

    def newJob(self, message, job_time):
        '''Adds a new job to the list of jobs being processed by the CPU.'''
        job = UpstreamJob(message, job_time, self.nextJobId)
        self.nextJobId += 1
        self.jobs.add(job)

        return job

    def killJob(self, job):
        '''Removes a job from the list of jobs being processed by the CPU.'''
        self.jobs.remove(job)

    def getNextFinishEvent(self):
        '''Create a new event that will fire when the next job finishes.
        The validity of the this new event assumes the UpstreamCpu will not
        receive any events between this time and the next. If this assumption
        is invalididate, then the event becomes invalid and should be replaced
        by a new event'''

        if len(self.jobs) == 0:
            return None

        min_job = sorted(self.jobs, key=lambda job: (job.time, job.job_id))[0]

        # when will min_job finish?
        delay = self.getWallSec(min_job.time)

        # Create and return event
        message = JobFinishMessage(self.sim, min_job)
        event = ReceiveMessageEvent(self.sim, delay, self.cpuAgent, message)
        return event

    def handleMessage(self, message):
        '''finishes a job, kills a job, or creates a new job.
        determines how much time has elapsed since the last event
        and makes progress on each job based on the elapsed time since
        the last event.
        Returns a 4-tuple (old_event, new_event, new_job, finished_job).
        The old_event is the previous finish_job_event that is now obsolete
        (supplanated by new_event). The caller should remove old_event
        from the event queue (if not None) and add new_event to the event_queue
        (if not None).
        new_job is a reference to the newly created job (or None no job created)
        finished_job is a reference to the successfully finished job (or None if no job
            successfully finished)
        '''
        time = self.sim.time

        # Each job has made progress on the CPU since the last
        # event, so update the jobs accordingly
        finished_job = self.updateJobs(time)
        new_job = None

        if isinstance(message, JobFinishMessage):
            assert(finished_job == message.job)
        elif isinstance(message, KillJobMessage):
            self.killJob(message.job)
        elif isinstance(message, NewJobMessage):
            new_job = self.newJob(message, message.job_time)
        else:
            raise ValueError("Unexpected message type")

        next_event = self.getNextFinishEvent()

        old_event = self.current_job_finish_event
        self.current_job_finish_event = next_event
        self.last_event_time = time
        return (old_event, self.current_job_finish_event, new_job, finished_job)

class Config:
    def __init__(self, config_dict):
        self.__dict__.update(config_dict)

class Simulator:

    def __init__(self, config_dict, logger, **kwargs):
        self.logger = logger

        self.logger.debug("config_file = %s", json.dumps(config_dict, sort_keys=True, indent=4))
        self.logger.debug("kwargs = %s", json.dumps(kwargs, sort_keys=True, indent=4))
        config_dict.update(kwargs)
        self.logger.info("config = %s", json.dumps(config_dict, sort_keys=True, indent=4))
        validateConfig(config_dict)
        self.config = Config(config_dict)

        # map from greenlet objects to name-strings
        self.greenlets = {}

        # map from upstream_worker geenlet objects to floating point numbers,
        # representing the CPU-time needed to complete the task on that work
        self.upstream_tasks = []

    def greenlet(self, func, name):
        agent = greenlet.greenlet(func)
        self.greenlets[agent] = name
        return agent

    # kind of a hack
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

    with open(args.config) as f:
        config_dict = json.load(f)

    sim = Simulator(config_dict, logger)
    sim.run()

