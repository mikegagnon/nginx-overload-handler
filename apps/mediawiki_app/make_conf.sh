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
# USAGE: sudo ./make_conf.sh
#

DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
source $DIR/../../nginx_upstream_overload/env.sh
DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
source $DIR/env.sh
DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"

cat $DIR/nginx.conf.template \
    | sed "s@TEMPLATE_ALERT_PIPE_PATH@$ALERT_PIPE_PATH@g" \
    | sed "s@TEMPLATE_MEDIAWIKI_PATH@$INSTALL_MEDIA_WIKI_PATH@g" \
    > $DIR/nginx.conf

cat $DIR/nginx_no_overload.conf.template \
    | sed "s@TEMPLATE_ALERT_PIPE_PATH@$ALERT_PIPE_PATH@g" \
    | sed "s@TEMPLATE_MEDIAWIKI_PATH@$INSTALL_MEDIA_WIKI_PATH@g" \
    > $DIR/nginx_no_overload.conf

cat $DIR/bouncer_config.json.template \
    | sed "s@TEMPLATE_ALERT_PIPE_PATH@$ALERT_PIPE_PATH@g" \
    > $DIR/bouncer_config.json

