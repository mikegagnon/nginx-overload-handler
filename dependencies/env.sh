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

PHP_FCGI_USER=php_fcgi
PHP_FCGI_USER_HOME="/home/$PHP_FCGI_USER"

# path to sudo command
SUDO="/usr/bin/sudo"

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

# This version of Ruby is vulnerable to HashDos (which is useful for testing purposes)
RUBY_VULN_DL_REMOTE_PATH="http://ftp.ruby-lang.org/pub/ruby/1.8/ruby-1.8.7-p352.tar.gz"
RUBY_VULN_DL_LOCAL_PATH="$DOWNLOAD_DIR/ruby-1.8.7-p352.tar.gz"
RUBY_VULN_LOCAL_PATH="$DOWNLOAD_DIR/ruby-1.8.7-p352"
RUBY_VULN_INSTALL="$DIR/ruby_vuln/install"
RUBY_VULN_BIN="$RUBY_VULN_INSTALL/bin/ruby"
export RUBY_VULN_BIN

# This version of Ruby is vulnerable to HashDos (which is useful for testing purposes)
PHP_VULN_DL_REMOTE_PATH="http://us3.php.net/distributions/php-5.3.8.tar.gz"
PHP_VULN_DL_LOCAL_PATH="$DOWNLOAD_DIR/php-5.3.8"
PHP_VULN_LOCAL_PATH="$DOWNLOAD_DIR/php-5.3.8"
PHP_VULN_INSTALL="$DIR/php_vuln/install"
PHP_VULN_BIN="$PHP_VULN_INSTALL/bin/php"
PHP_FPM_VULN_BIN="$PHP_VULN_INSTALL/sbin/php-fpm"
export PHP_VULN_BIN
export PHP_FPM_VULN_BIN

