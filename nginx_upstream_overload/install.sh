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
# ==== How to install ====
#
# - First make sure you have compiled with ./compile.sh
# - Then, sudo ./install.sh
#
###############################################################################


# Create the nginx user (and home dir) if it does not exist
###############################################################################

NGINX_USERNAME=nginx_user
HOME_DIR=/home/$NGINX_USERNAME

USER_EXISTS=`grep "^${NGINX_USERNAME}:" /etc/passwd`
if [ ! -n "$USER_EXISTS" ]
then
    useradd $NGINX_USERNAME
    USER_EXISTS=`grep "^${NGINX_USERNAME}:" /etc/passwd`
    if [ -n "$USER_EXISTS" ]
    then
        echo "Created user $NGINX_USERNAME"
        mkdir $HOME_DIR
        chown $NGINX_USERNAME:$NGINX_USERNAME $HOME_DIR
    else
        echo "Could not create user $NGINX_USERNAME. Your probably need to run this script as root."
        exit 1
    fi
fi

# Install nginx
###############################################################################

OVERLOAD_MODULE=`pwd`

cd ../nginx-1.0.12

make install

