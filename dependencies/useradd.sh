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
# ==== useradd.sh ====
#
# Creates a new user to run FastCGI workers as (and home dir)
#
# USAGE: sudo ./useradd.sh
#

DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
source $DIR/env.sh
DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"

# Create the nginx user (and home dir) if it does not exist
###############################################################################

USER_EXISTS=`grep "^${FCGI_USER}:" /etc/passwd`
if [ ! -n "$USER_EXISTS" ]
then
    useradd $FCGI_USER
    USER_EXISTS=`grep "^${FCGI_USER}:" /etc/passwd`
    if [ -n "$USER_EXISTS" ]
    then
        echo "Created user $FCGI_USER"
        mkdir $FCGI_USER_HOME
        chown $FCGI_USER:$FCGI_USER $FCGI_USER_HOME
    else
        echo "Could not create user $FCGI_USER. Your probably need to run this script as root."
        exit 1
    fi
fi

