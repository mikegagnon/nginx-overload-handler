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
# ==== install.sh for dummy_php_app ====
#
# USAGE: sudo ./install.sh

source ../dependencies/env.sh
source env.sh

# Create the nginx user (and home dir) if it does not exist
###############################################################################

USER_EXISTS=`grep "^${PHP_FCGI_USER}:" /etc/passwd`
if [ ! -n "$USER_EXISTS" ]
then
    useradd $PHP_FCGI_USER
    USER_EXISTS=`grep "^${PHP_FCGI_USER}:" /etc/passwd`
    if [ -n "$USER_EXISTS" ]
    then
        echo "Created user $PHP_FCGI_USER"
        mkdir $PHP_FCGI_USER_HOME
        chown $PHP_FCGI_USER:$PHP_FCGI_USER $PHP_FCGI_USER_HOME
    else
        echo "Could not create user $PHP_FCGI_USER. Your probably need to run this script as root."
        exit 1
    fi
fi

# Copy the php code into the public_html directory
###############################################################################

mkdir -p $APP_DIR
cp $DIR/*.php $APP_DIR/
chown -R $PHP_FCGI_USER:$PHP_FCGI_USER $APP_DIR

# Copy the nginx config
###############################################################################
cp nginx.conf $NGINX_CONF

