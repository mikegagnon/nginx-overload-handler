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
# ==== download.sh downloads 3rd party software dependencies ====
#

source env.sh

cd $DOWNLOAD_DIR

wget --output-document=$NGINX_DL_LOCAL_PATH $NGINX_DL_REMOTE_PATH
tar -xvf $NGINX_DL_LOCAL_PATH

wget --output-document=$FLUP_DL_LOCAL_PATH $FLUP_DL_REMOTE_PATH
tar -xvf $FLUP_DL_LOCAL_PATH

wget --output-document=$THRIFT_DL_LOCAL_PATH $THRIFT_DL_REMOTE_PATH
tar -xvf $THRIFT_DL_LOCAL_PATH

wget --output-document=$MEDIA_WIKI_DL_LOCAL_PATH $MEDIA_WIKI_DL_REMOTE_PATH
tar -xvf $MEDIA_WIKI_DL_LOCAL_PATH

