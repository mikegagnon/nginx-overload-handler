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
# ==== configures and compiles a vulnerable version of php5 ====
#
# USAGE:  ./install.sh
#

# $DIR is the absolute path for the directory containing this bash script
DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
source $DIR/../env.sh
DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"

sudo echo "Beginning install"

# install old autoconf
cd $AUTOCONF_LOCAL_PATH
./configure
make
sudo make install

# install php

cd $PHP_VULN_LOCAL_PATH

rm configure
./buildconf --force
# ./configure --help | grep apc # visually make sure apc is there
# also, to manually verify apc after php compilation:
# echo "<? echo phpinfo(); ?>" >> /home/fcgi_user/mediawiki-1.18.2/env.php
# browser http://localhost/env.php
# "Ctrl+F apc" in the browser

# Need to compile PHP twice, once for php-cgi and again for php-fpm
# See http://serverfault.com/questions/104605/how-to-compile-php-5-3-cgi
# First make php-cgi
./configure \
    --prefix=$PHP_VULN_INSTALL \
    --exec-prefix=$PHP_VULN_INSTALL \
    --with-mysql \
    --enable-apc \
    --enable-sockets
make

# Then make php-fpm
./configure \
    --prefix=$PHP_VULN_INSTALL \
    --exec-prefix=$PHP_VULN_INSTALL \
    --with-mysql \
    --enable-fpm \
    --with-fpm-user=$FCGI_USER \
    --with-fpm-group=$FCGI_USER \
    --enable-apc \
    --enable-sockets
make

cd $PHP_VULN_LOCAL_PATH

make install

cp $DIR/php.ini $PHP_VULN_INSTALL/lib/php.ini

