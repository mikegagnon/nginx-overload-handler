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
# Given a wikidump input file from this site:
# http://dumps.wikimedia.org/other/pagecounts-raw/
# this script  produces a JSON pageview count file 
# using the bundled ./page_counts_to_json.py
#

DUMPS_FILE=$1
if [ -z "$DUMPS_FILE" ]; then
    echo "Usage: ./prepare_inputs.sh <wikidump-pagecount-file>"
    # DUMPS_FILE="sample-pagecounts-input00" # test only, remove
    exit
fi
SPECIAL_PREFIXES="Category
Category_talk
File
File_talk
Help
Http
Image
Image_talk
Portal
Portal_talk
Special
Special_talk
Talk
Template
Template_talk
User
User_talk
Wikipedia
Wikipedia_talk
WP"
# TODO: need to get an exhaustive updated list of special WP namespaces

# only en
data=`grep "^en .*" $DUMPS_FILE`

# remove special etc. pages
for i in `echo $SPECIAL_PREFIXES`; do
    echo "removing special '$i'"
    data=`echo "$data" | egrep -vi "^en $i:"`
    data=`echo "$data" | egrep -vi "^en $i%3A"`
done
data=`echo "$data" | shuf`
echo "$data" > $DUMPS_FILE".filtered"
./page_counts_to_json.py < $DUMPS_FILE".filtered" \
    > $DUMPS_FILE".json"

rm $DUMPS_FILE".filtered"  
