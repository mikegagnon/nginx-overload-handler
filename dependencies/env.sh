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

FCGI_USER=fcgi_user
FCGI_USER_HOME="/home/$FCGI_USER"

# path to sudo command
SUDO="/usr/bin/sudo"

MYSQL_USER="root"
MYSQL_PASSWORD="dummyP@ssw0rd"
DOWNLOAD_DIR="$DIR/downloads"

NGINX_DL_REMOTE_PATH="http://nginx.org/download/nginx-1.0.12.tar.gz"
NGINX_DL_LOCAL_PATH="$DOWNLOAD_DIR/nginx-1.0.12.tar.gz"
NGINX_LOCAL_PATH="$DOWNLOAD_DIR/nginx-1.0.12"
NGINX_BIN=/usr/local/nginx/sbin/nginx
NGINX_CONF_DIR=/usr/local/nginx/conf
NGINX_CONF=$NGINX_CONF_DIR/nginx.conf

FLUP_DL_REMOTE_PATH="http://pypi.python.org/packages/source/f/flup/flup-1.0.2.tar.gz"
FLUP_DL_LOCAL_PATH="$DOWNLOAD_DIR/flup-1.0.2.tar.gz"
FLUP_LOCAL_PATH="$DOWNLOAD_DIR/flup-1.0.2"

THRIFT_DL_REMOTE_PATH="http://archive.apache.org/dist/thrift/0.8.0/thrift-0.8.0.tar.gz"
THRIFT_DL_LOCAL_PATH="$DOWNLOAD_DIR/thrift-0.8.0.tar.gz"
THRIFT_LOCAL_PATH="$DOWNLOAD_DIR/thrift-0.8.0"
THRIFT_PYTHON_LIB_INSTALL="$DIR/thrift_compile/python_thrift_lib"
THRIFT_PYTHON_LIB_INSTALL_PATH_FILE="$THRIFT_PYTHON_LIB_INSTALL/path.txt"

MEDIA_WIKI_DL_REMOTE_PATH="http://download.wikimedia.org/mediawiki/1.18/mediawiki-1.18.2.tar.gz"
MEDIA_WIKI_DL_LOCAL_PATH="$DOWNLOAD_DIR/mediawiki-1.18.2.tar.gz"
MEDIA_WIKI_LOCAL_PATH="$DOWNLOAD_DIR/mediawiki-1.18.2"

REDMINE_DL_REMOTE_PATH="http://rubyforge.org/frs/download.php/76017/redmine-1.4.0.tar.gz"
REDMINE_DL_LOCAL_PATH="$DOWNLOAD_DIR/redmine-1.4.0.tar.gz"
REDMINE_LOCAL_PATH="$DOWNLOAD_DIR/redmine-1.4.0"

FCGI_GEM_DL_REMOTE_PATH="https://rubyforge.org/frs/download.php/69127/fcgi-0.8.8.tgz"
FCGI_GEM_DL_LOCAL_PATH="$DOWNLOAD_DIR/fcgi-0.8.8.tgz"
FCGI_GEM_LOCAL_PATH="$DOWNLOAD_DIR/fcgi-0.8.8"

# This version of Ruby is vulnerable to HashDos (which is useful for testing purposes)
RUBY_VULN_DL_REMOTE_PATH="http://ftp.ruby-lang.org/pub/ruby/1.8/ruby-1.8.7-p352.tar.gz"
RUBY_VULN_DL_LOCAL_PATH="$DOWNLOAD_DIR/ruby-1.8.7-p352.tar.gz"
RUBY_VULN_LOCAL_PATH="$DOWNLOAD_DIR/ruby-1.8.7-p352"
RUBY_VULN_INSTALL="$DIR/ruby_vuln/install"
RUBY_VULN_BIN="$RUBY_VULN_INSTALL/bin/ruby"
export RUBY_VULN_BIN

GEM_HOME="$DIR/gems"
RUBY_LIB="$RUBY_VULN_INSTALL/lib/ruby"
RUBY_LIB_PATH="$RUBY_LIB:$RUBY_LIB/site_ruby/1.8"
export GEM_HOME
export RUBY_LIB
export RUBY_LIB_PATH

# This version of Ruby is vulnerable to HashDos (which is useful for testing purposes)
PHP_VULN_DL_REMOTE_PATH="http://us3.php.net/distributions/php-5.3.8.tar.gz"
PHP_VULN_DL_LOCAL_PATH="$DOWNLOAD_DIR/php-5.3.8"
PHP_VULN_LOCAL_PATH="$DOWNLOAD_DIR/php-5.3.8"
PHP_VULN_INSTALL="$DIR/php_vuln/install"
PHP_VULN_BIN="$PHP_VULN_INSTALL/bin/php"
PHP_CGI_VULN_BIN="$PHP_VULN_LOCAL_PATH/sapi/cgi/php-cgi"
PHP_FPM_VULN_BIN="$PHP_VULN_INSTALL/sbin/php-fpm"
export PHP_VULN_BIN
export PHP_CGI_VULN_BIN
export PHP_FPM_VULN_BIN

HTTPERF_DL_REMOTE_PATH="http://httperf.googlecode.com/files/httperf-0.9.0.tar.gz"
HTTPERF_DL_LOCAL_PATH="$DOWNLOAD_DIR/httperf-0.9.0.tar.gz"
HTTPERF_LOCAL_PATH="$DOWNLOAD_DIR/httperf-0.9.0"
HTTPERF_PATCHED_LOCAL_PATH="$DOWNLOAD_DIR/httperf-0.9.0-bg"

# Note you must manually download and install Java
# see install_java.sh
JAVA_DL_LOCAL_PATH="$DOWNLOAD_DIR/jdk-6u22-linux-x64.bin"
export JAVA_HOME="$DOWNLOAD_DIR/jdk1.6.0_22"

JETTY_DL_REMOTE_PATH="http://dist.codehaus.org/jetty/jetty-6.1.26/jetty-6.1.26.zip"
JETTY_DL_LOCAL_PATH="$DOWNLOAD_DIR/jetty-6.1.26.zip"
JETTY_LOCAL_PATH="$DOWNLOAD_DIR/jetty-6.1.26"

TOMCAT_DL_REMOTE_PATH="http://apache.osuosl.org/tomcat/tomcat-6/v6.0.35/bin/apache-tomcat-6.0.35.tar.gz"
TOMCAT_DL_LOCAL_PATH="$DOWNLOAD_DIR/apache-tomcat-6.0.35.tar.gz"
TOMCAT_LOCAL_PATH="$DOWNLOAD_DIR/apache-tomcat-6.0.35"
export CATALINA_HOME="$TOMCAT_LOCAL_PATH"

SOLR_DL_REMOTE_PATH="http://apache.mirrors.tds.net/lucene/solr/3.1.0/apache-solr-3.1.0.tgz"
SOLR_DL_LOCAL_PATH="$DOWNLOAD_DIR/apache-solr-3.1.0.tgz"
SOLR_LOCAL_PATH="$DOWNLOAD_DIR/apache-solr-3.1.0"
SOLR_LOCAL_PATH_JETTY="$SOLR_LOCAL_PATH-jetty"
SOLR_LOCAL_PATH_TOMCAT="$SOLR_LOCAL_PATH-tomcat"

DJANGO_DL_REMOTE_PATH="http://pypi.python.org/packages/source/D/Django/Django-1.3.1.tar.gz"
DJANGO_DL_LOCAL_PATH="$DOWNLOAD_DIR/Django-1.3.1.tar.gz"
DJANGO_LOCAL_PATH="$DOWNLOAD_DIR/Django-1.3.1"

OSQA_DL_REMOTE_PATH="http://www.osqa.net/releases/fantasy-island-0.9.0-beta3.tar.gz"
OSQA_DL_LOCAL_PATH="$DOWNLOAD_DIR/fantasy-island-0.9.0-beta3.tar.gz"
OSQA_LOCAL_PATH="$DOWNLOAD_DIR/fantasy-island-0.9.0-beta3"

