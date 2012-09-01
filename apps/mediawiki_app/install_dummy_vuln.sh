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
# ==== install_dummy_vuln.sh for MediaWiki====
#
# Installs a dummy high-density vulnerability into the MediaWiki installation.
# This is necessary to conduct high-density attacks while training.
#
# USAGE: sudo ./install_dummy_vuln.sh
#

DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
source $DIR/../../dependencies/env.sh
DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
source $DIR/env.sh
DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"

cp $DIR/dummy_vuln.php $INSTALL_MEDIA_WIKI_PATH/dummy_vuln.php
cp $DIR/dummy_vuln_sql.php $INSTALL_MEDIA_WIKI_PATH/dummy_vuln_sql.php
chown -R $FCGI_USER:$FCGI_USER $INSTALL_MEDIA_WIKI_PATH/dummy_vuln_*.php

