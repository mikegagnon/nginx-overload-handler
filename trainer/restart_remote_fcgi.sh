#!/usr/bin/env bash
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
# ==== restart_remote_fcgi.sh ====
#
# executes restart_fcgi.sh on the remote server
#
# USAGE: ./restart_remote_fcgi.sh username server
#   where username is the username to log in as (via ssh)
#   and server is the address of the server to log in to
#
# PREREQs:
# (1) restart_fcgi.sh needs to be created and installed
# via the make_conf.sh and install_conf.sh commands for
# a given server configuration.
# (2) ssh needs to be setup so username can ssh in without
# a password
# (3) You do not want SUDO to prompt for the password
# when you execute restart_fcgi.sh. To accomplish this feat,
# edit the sudoers file (sudo EDITOR=/usr/bin/vim visudo) and
# add a line like:
#   username ALL=(ALL) NOPASSWD: /usr/local/bin/restart_fcgi.sh
#

ssh -f $1@$2 "nohup sudo -n restart_fcgi.sh &"
sleep 5
