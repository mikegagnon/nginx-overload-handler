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
# ==== install_java.sh installs vulnerable version of Java (CVE-2010-4476) ====
#
# PREREQ:
# Browse to
#
#   http://www.oracle.com/technetwork/java/javasebusiness/downloads/java-archive-downloads-javase6-419409.html#jdk-6u22-oth-JPR
#
# and click the link for "jdk-6u22-linux-x64.bin" (make sure to check
# "Accept License Agreement"). Copy jdk-6u22-linux-x64.bin to:
#
#   nginx-overload-handler/dependencies/downloads/
#
# Unless you have previously downloaded Java from Oracle before, Oracle
# will likely prompt you to create an account.
#
#

# $DIR is the absolute path for the directory containing this bash script
DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
source $DIR/env.sh
DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"

cd `dirname $JAVA_DL_LOCAL_PATH`
chmod a+x $JAVA_DL_LOCAL_PATH
$JAVA_DL_LOCAL_PATH

sudo ln -sf $JAVA_HOME/bin/java /usr/bin/java

