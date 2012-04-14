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
# ==== install_named_pipe.sh ====
#
# The upstream_overload module sends alerts to a named pipe.
# This script creates that named pipe (if it doesn't already exist)
#
# USAGE: sudo ./install_named_pipe.sh
#

# $DIR is the absolute path for the directory containing this bash script
DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
source $DIR/env.sh
DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"

if [ ! -e "$ALERT_PIPE_PATH" ]
then
    echo "Creating named pipe: $ALERT_PIPE_PATH"
    mkfifo $ALERT_PIPE_PATH
    chown $NGINX_USER:$NGINX_GROUP $ALERT_PIPE_PATH
    chmod 644 $ALERT_PIPE_PATH
else
    echo "Named pipe already exists: $ALERT_PIPE_PATH" 
fi

