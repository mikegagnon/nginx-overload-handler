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

DOWNLOAD_DIR="$DIR/downloads"

NGINX_DL_REMOTE_PATH="http://nginx.org/download/nginx-1.0.12.tar.gz"
NGINX_DL_LOCAL_PATH="$DOWNLOAD_DIR/nginx-1.0.12.tar.gz"
NGINX_LOCAL_PATH="$DOWNLOAD_DIR/nginx-1.0.12"

MEDIA_WIKI_DL_REMOTE_PATH="http://download.wikimedia.org/mediawiki/1.18/mediawiki-1.18.2.tar.gz"
MEDIA_WIKI_DL_LOCAL_PATH="$DOWNLOAD_DIR/mediawiki-1.18.2.tar.gz"
MEDIA_WIKI_LOCAL_PATH="$DOWNLOAD_DIR/mediawiki-1.18.2"

FLUP_DL_REMOTE_PATH="http://pypi.python.org/packages/source/f/flup/flup-1.0.2.tar.gz"
FLUP_DL_LOCAL_PATH="$DOWNLOAD_DIR/flup-1.0.2.tar.gz"
FLUP_LOCAL_PATH="$DOWNLOAD_DIR/flup-1.0.2"

THRIFT_DL_REMOTE_PATH="http://archive.apache.org/dist/thrift/0.8.0/thrift-0.8.0.tar.gz"
THRIFT_DL_LOCAL_PATH="$DOWNLOAD_DIR/thrift-0.8.0.tar.gz"
THRIFT_LOCAL_PATH="$DOWNLOAD_DIR/thrift-0.8.0"
THRIFT_PYTHON_LIB_INSTALL="$DIR/thrift_compile/python_thrift_lib"
THRIFT_PYTHON_LIB_INSTALL_PATH_FILE="$THRIFT_PYTHON_LIB_INSTALL/path.txt"

