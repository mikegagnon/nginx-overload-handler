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
# ==== bouncer_commony.py ====
#
# Functionality used by both alert_router.py and bouncer_process_manager.py,
# namely: reading configuration files (since they both have the same format)
#
# ==== Example config ====
#
# {
#    "alert_pipe" : "/home/nginx_user/alert_pipe",
#    "sigservice" : {
#       "addr" : "127.0.0.1",
#       "port" : 4001,
#       "sig_file" : "/home/nginx_user/sig_file",
#       "max_sample_size" : 100,
#       "update_requests" : 100,
#       "min_delay" : 1,
#       "max_delay" : 5
#    },
#    "bouncers" : [
#       {
#           "bouncer_addr" : "10.51.23.65",
#           "bouncer_port" : 10012,
#           "fcgi_workers" : [
#               "10.51.23.65:9000",
#               "10.51.23.65:9001",
#               "10.51.23.65:9002"
#               ]
#       },
#       {
#           "bouncer_addr" : "10.51.23.66",
#           "bouncer_port" : 10014,
#           "fcgi_workers" : [
#               "10.51.23.66:9010",
#               "10.51.23.66:9011"
#               ]
#       }
#    ]
# }
#
# In this configuration:
#   - the alert_router receives alerts by reading meassges from
#     /home/www/pipes/alert_pipe
#   - there are 5 FastCGI workers spread over two machines:
#       - 10.51.23.65
#       - 10.51.23.66.
#   - If the load balancer generates an alert for "10.51.23.65:9000",
#     "10.51.23.65:9001", or "10.51.23.65:9002" then alert_router will send an
#     alert to the bouncer daemon on 10.51.23.65, which is listening on port
#     10012.
#   - And so on for the bouncer on .66
#   - For description of sigservice config run sigservice.py -h
#       - the sigservice part of the config is optional

import sys
import json

class BadConfig(ValueError):
    pass

class BouncerAddress:

    def __init__(self, addr, port):
        self.addr = addr
        self.port = port

    def __str__(self):
        return "%s:%d" % (self.addr, self.port)

class Config:

    def __init__(self, fd):
        '''fd is an open file containing the config
        sets:
            self.sigservice to a dict
            self.alert_pipe to the path of alert_pipe.
            self.worker_map which is a dict that maps every FCGI worker string
                to a BouncerAddress object.
            self.bouncer_list which is a list of BouncerAddr objects
            self.bouncer_map which is a dict that maps every bouncer string (i.e str(bouncerAddr))
                to the FCGI workers (strings) that that bouncer is repsonsible for.'''

        try:
            json_config = json.load(fd)
        except Exception, e:
            raise e

        self.worker_map = {}
        self.bouncer_map = {}
        self.bouncer_list = []

        if "sigservice" not in json_config:
            self.sigservice = None
        else:
            self.sigservice = json_config["sigservice"]

            if "addr" not in self.sigservice:
                raise BadConfig("sigservice[addr] is not defined")
            if "port" not in self.sigservice:
                raise BadConfig("sigservice[port] is not defined")
            if "sig_file" not in self.sigservice:
                raise BadConfig("sigservice[sig_file] is not defined")
            if "max_sample_size" not in self.sigservice:
                raise BadConfig("sigservice[max_sample_size] is not defined")
            if "update_requests" not in self.sigservice:
                raise BadConfig("sigservice[update_requests] is not defined")
            if "min_delay" not in self.sigservice:
                raise BadConfig("sigservice[min_delay] is not defined")
            if "max_delay" not in self.sigservice:
                raise BadConfig("sigservice[max_delay] is not defined")

        if "alert_pipe" not in json_config:
            raise BadConfig("alert_pipe is not defined")
        self.alert_pipe = str(json_config["alert_pipe"])

        if "bouncers" not in json_config:
            raise BadConfig("bouncers is not defined")
        bouncers = json_config["bouncers"]

        for bouncer in bouncers:
            bouncer_addr = bouncer["bouncer_addr"]
            bouncer_port = int(bouncer["bouncer_port"])
            fcgi_workers = bouncer["fcgi_workers"]

            bouncer_obj = BouncerAddress(bouncer_addr, bouncer_port)
            self.bouncer_map[str(bouncer_obj)] = []
            self.bouncer_list.append(bouncer_obj)
            for worker in fcgi_workers:
                worker = str(worker)
                if worker in self.worker_map:
                    raise BadConfig("Same fcgi worker appears more than once")
                self.worker_map[worker] = bouncer_obj
                self.bouncer_map[str(bouncer_obj)].append(worker)

    def __str__(self):
        '''Just for debugging'''
        result = {}
        result['sigservice'] = self.sigservice
        result['alert_pipe'] = self.alert_pipe
        result['worker_map'] = self.worker_map
        result['bouncer_map'] = self.bouncer_map
        result['bouncer_list'] = self.bouncer_list
        return json.dumps(result, indent=4, sort_keys=True, default=str)

if __name__ == "__main__":
    with open(sys.argv[1]) as f:
        config = Config(f)
    print config
