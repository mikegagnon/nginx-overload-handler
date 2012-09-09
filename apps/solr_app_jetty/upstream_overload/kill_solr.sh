#!/usr/bin/env bash
#
# Copyright 2012 HellaSec, LLC
#
#  Licensed under the Apache License, Version 2.0 (the "License");
#  you may not use this file except in compliance with the License.
#  You may obCONFIG_INSTALLED_BACKUPtain a copy of the License at
#
#      http://www.apache.org/licenses/LICENSE-2.0
#
#  Unless required by applicable law or agreed to in writing, software
#  distributed under the License is distributed on an "AS IS" BASIS,
#  WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
#  See the License for the specific language governing permissions and
#  limitations under the License.
#
# ==== kill_solr.sh ====
#
# USAGE: sudo ./kill_solr.sh
#

DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
source $DIR/../env.sh
DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"

echo "Killing solr politely..."
pkill -f "$START_SOLR_JAR"
sleep 5
echo "Killing solr brutally (just in case)... "
pkill -9 -f "$START_SOLR_JAR"
sleep 1

pkill -f "solr_bouncer.py"
pkill -f "java"
pkill -f "alert_router.py"
sleep 2
pkill -9 -f "solr_bouncer.py"
pkill -9 -f "java"
pkill -9 -f "alert_router.py"
