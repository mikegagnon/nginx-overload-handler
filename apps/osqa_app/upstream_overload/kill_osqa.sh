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
# ==== launch_osqa.sh ====
#
# USAGE: ./launch_osqa.sh

# $DIR is the absolute path for the directory containing this bash script
DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
source $DIR/../env.sh
DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"

pkill -f "osqa_bouncer.py"
pkill -f INSTALL_OSQA_PATH/manage.py
pkill -f "alert_router.py"
pkill -f ".*run_gunicorn.*"
sleep 2
pkill -9 -f "osqa_bouncer.py"
pkill -9 -f INSTALL_OSQA_PATH/manage.py
pkill -9 -f "alert_router.py"
pkill -9 -f ".*run_gunicorn.*"
