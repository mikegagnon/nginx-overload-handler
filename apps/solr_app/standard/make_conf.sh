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
# ==== make_conf.sh ====
#
# Make config files by filling in values in .template files
#
# USAGE: ./make_conf.sh begin_port [end_port]
#   For example, ./make_conf.sh 9000 9008
#

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

DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
source $DIR/../env.sh
DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"

for PORT in `seq $PORT_BEGIN $PORT_END`;
do
    cat $JETTY_BASE_CONFIG \
        | sed "s@$JETTY_BASE_CONFIG_PORT@$PORT@g" \
        > $DIR/jetty_$PORT.xml
done

