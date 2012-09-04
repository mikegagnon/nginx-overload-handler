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
#
# A simple script to wipe out all Mediawiki data and start from a fresh install
#

DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
source $DIR/../env.sh

QUERY_FILE="/tmp/$RANDOM.bgmysql"

# DROP existing
echo "drop database my_wiki" > $QUERY_FILE

mysql -u $MYSQL_USER -p$MYSQL_PASSWORD < $QUERY_FILE > /dev/null 2>&1
#rm -f $QUERY_FILE

# replace with vanilla tables
sudo mv $INSTALL_MEDIA_WIKI_PATH/LocalSettings.php /tmp
sudo php $INSTALL_MEDIA_WIKI_PATH/maintenance/install.php \
    testname testadmin \
    --pass "$MEDIAWIKI_PASSWORD" \
    --scriptpath "" \
    --dbuser root \
    --dbpass "$MYSQL_PASSWORD" \
    --server "$MEDIAWIKI_ROOT_URL"

sudo mv /tmp/LocalSettings.php $INSTALL_MEDIA_WIKI_PATH/
