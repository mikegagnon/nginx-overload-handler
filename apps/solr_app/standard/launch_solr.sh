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
# ==== launch_solr.sh ====
#
# USAGE: ./launch_solr.sh jetty_9000.xml jetty_9001.xml ...
#

DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
source $DIR/../env.sh
DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"

CONFIG_DIR=$DIR

if [ "$1" == "" ]
then
    echo "Error: You need to specify a begin port"
    exit 1
fi
PORT_BEGIN=$1

if [ "$2" == "" ]
then
    PORT_END=$PORT_BEGIN
else
    PORT_END=$2
fi

DIR=`dirname $START_SOLR_JAR`
cd $DIR

for PORT in `seq $PORT_BEGIN $PORT_END`;
do
    CONFIG_FILE="$CONFIG_DIR/jetty_$PORT.xml"

    cat $JETTY_BASE_CONFIG \
        | sed "s@$JETTY_BASE_CONFIG_PORT@$PORT@g" \
        > $CONFIG_FILE

    BASE=`basename $CONFIG_FILE`
    NOHUP_OUT="$CONFIG_DIR/nohup.$BASE.out"
    rm -f $NOHUP_OUT
    echo "Launching solr with config $CONFIG_FILE"
    nohup java -jar $START_SOLR_JAR $CONFIG_FILE &> $NOHUP_OUT &
    sleep 1
    grep -l "Started SocketConnector" $NOHUP_OUT > /dev/null
    sleep 1
    echo "Launch successful"
done

