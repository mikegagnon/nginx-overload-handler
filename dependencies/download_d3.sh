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
# ==== download_d3.sh downloads 3rd party software dependencies ====
#

# $DIR is the absolute path for the directory containing this bash script
DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
source $DIR/env.sh
DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"

cd $DOWNLOAD_DIR

wget --output-document=$TOMCAT_DL_LOCAL_PATH $TOMCAT_DL_REMOTE_PATH
tar -xvf $TOMCAT_DL_LOCAL_PATH

wget --output-document=$SOLR_DL_LOCAL_PATH $SOLR_DL_REMOTE_PATH
tar -xvf $SOLR_DL_LOCAL_PATH
mkdir -p $SOLR_LOCAL_PATH_TOMCAT
cp -r $SOLR_LOCAL_PATH/* $SOLR_LOCAL_PATH_TOMCAT/

wget --output-document=$DJANGO_DL_LOCAL_PATH $DJANGO_DL_REMOTE_PATH
tar -xvf $DJANGO_DL_LOCAL_PATH

wget --output-document=$OSQA_DL_LOCAL_PATH $OSQA_DL_REMOTE_PATH
tar -xvf $OSQA_DL_LOCAL_PATH

