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
# ==== env.sh ====
#
# defines some shell variables
#

# $DIR is the absolute path for the directory containing this bash script
DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
source $DIR/../../dependencies/env.sh
DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
source $DIR/../../bouncer/php_bouncer/env.sh
DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"

MEDIAWIKI_VERSION=`basename $MEDIA_WIKI_LOCAL_PATH`
INSTALL_MEDIA_WIKI_PATH="$FCGI_USER_HOME/$MEDIAWIKI_VERSION"

MEDIAWIKI_ROOT_URL="http://localhost"
export MEDIAWIKI_ROOT_URL

# A python regular expression. Any page titles that match this RE
# are considered "attack" pages, and will be excluded from a trace
# representing legitimate use
MEDIAWIKI_ATTACK_PAGES_RE="^Foo$"
export MEDIAWIKI_ATTACK_PAGES_RE

MEDIAWIKI_PASSWORD="dummyP@ssw0rd"

DUMMY_VULN_URL="/dummy_vuln.php"

