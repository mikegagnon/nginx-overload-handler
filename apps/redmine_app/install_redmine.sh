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
# ==== install_redmine.sh ====
#
# Installs MediaWiki
#
# PREREQs:
#   (1) ./compile_dependencies.sh
#   (1) sudo ./install_dependencies.sh
#
# USAGE: sudo ./install_redmine.sh
#
# TODO: replace PHP_FCGI_USER with FCGI_USER
#

DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
source $DIR/../../nginx_upstream_overload/env.sh
DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
source $DIR/../../dependencies/env.sh
DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
source $DIR/env.sh
DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"

# Copy redmine files into installation location
mkdir -p $INSTALL_REDMINE_PATH
cp -r $REDMINE_LOCAL_PATH/* $INSTALL_REDMINE_PATH

# Run installation scripts
cd $INSTALL_REDMINE_PATH
bundle install --without development test postgresql sqlite rmagick

cat config/database.yml.example \
    | sed "s/password:/password: $REDMINE_PASSWORD/g" \
    > config/database.yml

rake generate_session_store

RAILS_ENV=production rake db:migrate
RAILS_ENV=production rake redmine:load_default_data

cp public/dispatch.fcgi.example public/dispatch.fcgi

# nginx will serve static file, hence:
mkdir -p files log tmp public/plugin_assets
touch log/production.log
chmod -R 755 files log tmp public/plugin_assets
chmod 0666 log/production.log
chown -R $PHP_FCGI_USER:$PHP_FCGI_USER $INSTALL_REDMINE_PATH

