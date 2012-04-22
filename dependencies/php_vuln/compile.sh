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
# USAGE: ./compile.sh
#

# $DIR is the absolute path for the directory containing this bash script
DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
source $DIR/../env.sh
DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"

cd $PHP_VULN_LOCAL_PATH

./configure \
    --prefix=$PHP_VULN_INSTALL \
    --exec-prefix=$PHP_VULN_INSTALL \
    --with-mysql \
    --enable-fpm \
    --with-fpm-user=$PHP_FCGI_USER \
    --with-fpm-group=$PHP_FCGI_USER

make

