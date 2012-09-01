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
# Scrapes meta.osqa.net for some test data calling the python script
# * Assumes OSQA tables have been setup using the scripts in the dir above
# * invokes export_osqa_pages.py to produce an data file which then imports into MYSQL

DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
source $DIR/../env.sh
DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"

QUERY_FILE="/tmp/$RANDOM.bgosqamysql"

echo "scraping..."
data=`$DIR/export_osqa_pages.py`
echo "exporting..."
echo "$data"> $QUERY_FILE
mysql osqa -u $MYSQL_USER -p$MYSQL_PASSWORD < $QUERY_FILE 



# rm -f $QUERY_FILE
echo "done"

