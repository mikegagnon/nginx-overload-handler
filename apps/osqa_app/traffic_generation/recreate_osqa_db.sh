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
# A simple script to wipe out all osqa data and start from a fresh install
# needs sudo

DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
source $DIR/../env.sh
DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"

# sudo /etc/init.d/mysql restart
QUERY_FILE="/tmp/$RANDOM.bgosqamysql"

# DROP existing
echo "drop database osqa;" > $QUERY_FILE
echo "CREATE DATABASE osqa DEFAULT CHARACTER SET UTF8 COLLATE utf8_general_ci;" >> $QUERY_FILE

mysql -u $MYSQL_USER -p$MYSQL_PASSWORD < $QUERY_FILE > /dev/null 2>&1
rm -f $QUERY_FILE

cd $INSTALL_OSQA_PATH
python manage.py syncdb --all --noinput
python manage.py migrate forum --fake
rm -rf ./cache/*

# sudo /etc/init.d/mysql restart
