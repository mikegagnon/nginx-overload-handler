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
# ==== install_mediawiki.sh ====
#
# Installs MediaWiki
#
# PREREQs:
#   (1) ./install_dependencies.sh
#   (2) ../../bouncer/php_bouncer/install.sh
#
# USAGE: sudo ./install_mediawiki.sh
#

DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
source $DIR/../../dependencies/env.sh
DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
source $DIR/../../bouncer/php_bouncer/env.sh
DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
source $DIR/env.sh
DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"

# Copy mediawiki files into installation location
mkdir -p $INSTALL_MEDIA_WIKI_PATH
cp -r $MEDIA_WIKI_LOCAL_PATH/* $INSTALL_MEDIA_WIKI_PATH
chown -R $FCGI_USER:$FCGI_USER $INSTALL_MEDIA_WIKI_PATH

# Run installation script
php $INSTALL_MEDIA_WIKI_PATH/maintenance/install.php \
    testname testadmin \
    --pass "$MEDIAWIKI_PASSWORD" \
    --scriptpath "" \
    --dbuser root \
    --dbpass "$MYSQL_PASSWORD"
    --server "$MEDIAWIKI_ROOT_URL"

echo -e '$wgMaxUploadSize = 1024 * 1024 * 100;\n' >> $INSTALL_MEDIA_WIKI_PATH/LocalSettings.php

