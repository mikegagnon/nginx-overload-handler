#!/bin/bash
#
# Copyright 2012 github.com/one10, Hellasec
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
# http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
#
################################################################################

DBUSER="root"
MYSQL_PASSWORD="dummyP@ssw0rd"
DBOSUSER="mysql"

INSTALL_MEDIA_WIKI_PATH="/home/fcgi_user/mediawiki-1.18.2"
MEDIAWIKI_PASSWORD="dummyP@ssw0rd"
SERVER_NAME="localhost"
MEDIAWIKI_ROOT_URL="http://$SERVER_NAME"

# assumes this was run somewhere in dependencies:
# sudo apt-get install mysql

