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
# This script takes a list of WP page titles and exports them
# in batches of <20 files at a time into multiple local files
# then it also attempts to import these local files into a local Mediawiki
#
# Usage: ./export_wp_pages.sh <title-list-file> [import-only]
#
# Specify below a proper LOCAL_MW_INSTALL_DIR for successful import
#
# Note: No guarantees how many of the supplied title list will be actually successfully
# downloaded from Wikipedia, many pages fail (deleted since, or special, or error, etc),
# so watch the "verified downloaded" stats at the end of this script

PAGES_PER_CURBATCH=20
SLEEP=3
TITLE_LIST_FILE=$1
if [ -z "$TITLE_LIST_FILE" ]; then
    echo "Usage: ./export_wp_pages.sh <title-list-file>"
    echo "Also, don't forget to update path to local Mediawiki path for proper import"
    # TITLE_LIST_FILE="data/sample-pagecounts-input00.titles" # test only, remove
    exit
fi
EXP_SERVER="http://en.wikipedia.org"
EXP_URL="/w/index.php?title=Special:Export&action=submit&curonly=1&wpDownload=1&pages="
LOCAL_MW_INSTALL_DIR="/home/fcgi_user/mediawiki-1.18.2/"

# if we wish to import an existing bunch of files only...
IMPORT_ONLY=$2
if [ -n "$IMPORT_ONLY" ]; then
    # pagecounts-20120301-210000.json.
    for i in `ls $TITLE_LIST_FILE.*.xml`
    do
        echo "exporting $i..."
        php ${LOCAL_MW_INSTALL_DIR}/maintenance/importDump.php $i    
    done
    exit
fi

data=`cat $TITLE_LIST_FILE`
datasize=`echo "$data" | wc -l`

actual_downloaded=0
count=0

# after done preparing titles, export them from the Wikipedia
for i in `echo "$data"`
do
    # TODO: for early termination before some limit N for whatever reason...
    # if [[ (( "$count" -ge "$N" )) || (( "$actual_downloaded" -ge "$N" )) ]]; then
    #    break
    # fi 
    count=`expr $count + 1`
    if [[ (( $[$count % $PAGES_PER_CURBATCH] -eq "0" )) || (( $count -eq $datasize )) ]]; then
        # append 20 from data to curdata
        # download curdata to ./datafolder
        postval=$curbatch
        #postval=$(python -c "import urllib; print urllib.quote('''$postval''')")
        echo $postval
        out_file=`echo $TITLE_LIST_FILE | sed s'/.titles$//'`".$actual_downloaded.wpimport.xml"
        curl -o $out_file ${EXP_SERVER}${EXP_URL}${postval}
        sleep $SLEEP
        verify_num_pages=`grep -o "text.*bytes=[^>]*" $out_file | wc -l`
        actual_downloaded=`expr $actual_downloaded + $verify_num_pages`
        echo "number of pages downloaded: $verify_num_pages, total: $actual_downloaded"
        
        # import this batch into local MW
        php ${LOCAL_MW_INSTALL_DIR}/maintenance/importDump.php $out_file
        curbatch=""
    fi
    curbatch=$curbatch"%0D%0A"$i
done

echo "Totals: input list size: $datasize, verified downloaded: $actual_downloaded"
