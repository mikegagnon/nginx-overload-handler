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

# $DIR is the absolute path for the directory containing this bash script
DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
source $DIR/env.sh
DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"

cd $DOWNLOAD_DIR

wget --output-document=$NGINX_DL_LOCAL_PATH $NGINX_DL_REMOTE_PATH
tar -xvf $NGINX_DL_LOCAL_PATH

wget --output-document=$FLUP_DL_LOCAL_PATH $FLUP_DL_REMOTE_PATH
tar -xvf $FLUP_DL_LOCAL_PATH

wget --output-document=$THRIFT_DL_LOCAL_PATH $THRIFT_DL_REMOTE_PATH
tar -xvf $THRIFT_DL_LOCAL_PATH

wget --output-document=$MEDIA_WIKI_DL_LOCAL_PATH $MEDIA_WIKI_DL_REMOTE_PATH
tar -xvf $MEDIA_WIKI_DL_LOCAL_PATH

wget --output-document=$REDMINE_DL_LOCAL_PATH $REDMINE_DL_REMOTE_PATH
tar -xvf $REDMINE_DL_LOCAL_PATH

# gem install doesn't really work for this gem
wget --no-check-certificate --output-document=$FCGI_GEM_DL_LOCAL_PATH $FCGI_GEM_DL_REMOTE_PATH
tar -xvf $FCGI_GEM_DL_LOCAL_PATH

wget --output-document=$RUBY_VULN_DL_LOCAL_PATH $RUBY_VULN_DL_REMOTE_PATH
tar -xvf $RUBY_VULN_DL_LOCAL_PATH

wget --output-document=$PHP_VULN_DL_LOCAL_PATH $PHP_VULN_DL_REMOTE_PATH
tar -xvf $PHP_VULN_DL_LOCAL_PATH

wget --output-document=$JETTY_DL_LOCAL_PATH $JETTY_DL_REMOTE_PATH
unzip $JETTY_DL_LOCAL_PATH

wget --output-document=$TOMCAT_DL_LOCAL_PATH $TOMCAT_DL_REMOTE_PATH
tar -xvf $TOMCAT_DL_LOCAL_PATH

wget --output-document=$SOLR_DL_LOCAL_PATH $SOLR_DL_REMOTE_PATH
tar -xvf $SOLR_DL_LOCAL_PATH
mkdir -p $SOLR_LOCAL_PATH_TOMCAT
mkdir -p $SOLR_LOCAL_PATH_JETTY
cp -r $SOLR_LOCAL_PATH/* $SOLR_LOCAL_PATH_TOMCAT/
cp -r $SOLR_LOCAL_PATH/* $SOLR_LOCAL_PATH_JETTY/

