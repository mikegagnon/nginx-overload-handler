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
source $DIR/../../dependencies/env.sh
DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
source $DIR/env.sh
DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"

export RAILS_ENV=production
umask 22

exec spawn-fcgi -n -a 127.0.0.1 -p 9000 -u $PHP_FCGI_USER -f "$INSTALL_REDMINE_PATH/public/dispatch.fcgi"
# works
#exec spawn-fcgi -n -a 127.0.0.1 -p 9000 -u $PHP_FCGI_USER -f "$INSTALL_REDMINE_PATH/public/dispatch.fcgi"

# doesn't work
#exec spawn-fcgi -n -a 127.0.0.1 -p 9000 -u $PHP_FCGI_USER "/home/beergarden/nginx-overload-handler/apps/redmine_app/launch.sh"

