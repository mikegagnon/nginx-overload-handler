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

CONFIG_INSTALLED=/usr/local/nginx/conf/nginx.conf
CONFIG_INSTALLED_BACKUP=/usr/local/nginx/conf/nginx.conf.bak
CONFIG_LOCAL=nginx.conf
NAMED_PIPE=/home/nginx_user/alert_pipe
NGINX_USER=nginx_user

# First, install the configuration file
###############################################################################

# Crete a backup of the current config if it doesn't already exist
if [ -e "$CONFIG_INSTALLED" ]
then
    if [ ! -e "$CONFIG_INSTALLED_BACKUP" ]
    then
        cp $CONFIG_INSTALLED $CONFIG_INSTALLED_BACKUP
        chmod -w $CONFIG_INSTALLED_BACKUP
    fi
fi

cp $CONFIG_LOCAL $CONFIG_INSTALLED

# Second, create the named pipe if necessary
###############################################################################

if [ ! -e "$NAMED_PIPE" ]
then
    mkfifo $NAMED_PIPE
    chown $NGINX_USER:$NGINX_USER $NAMED_PIPE
    chmod 644 $NAMED_PIPE
fi
