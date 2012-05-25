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
# ==== install_dependencies.sh for solr_app ====
#
# USAGE: ./install_dependencies.sh
#
# PREREQ:
#   Make sure to have already downloaded jdk-6u22-linux-x64.bin into
#   nginx-overload-handler/dependencies/downloads/jdk-6u22-linux-x64.bin
#   See README.txt for instructions on downloading
#

DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
source $DIR/env.sh
DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"

cd `dirname $JAVA_DL_LOCAL_PATH`
chmod a+x $JAVA_DL_LOCAL_PATH
$JAVA_DL_LOCAL_PATH

sudo ln -sf $JAVA_HOME/bin/java /usr/bin/java

