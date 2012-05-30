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
# ==== env.sh ====
#
# defines some shell variables
#

# $DIR is the absolute path for the directory containing this bash script
DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
source $DIR/../../dependencies/env.sh
DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"

JAVA_DL_LOCAL_PATH="$DOWNLOAD_DIR/jdk-6u22-linux-x64.bin"
export JAVA_HOME="$DOWNLOAD_DIR/jdk1.6.0_22"

JETTY_BASE_CONFIG="$SOLR_LOCAL_PATH/example/etc/jetty.xml"
JETTY_BASE_CONFIG_PORT="8983"

START_SOLR_JAR="$SOLR_LOCAL_PATH/example/start.jar"

export JAVA_OPTIONS="$JAVA_OPTIONS -Dsolr.solr.home=$SOLR_LOCAL_PATH/example/solr"


