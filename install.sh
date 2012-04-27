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
# ==== install.sh ====
#
# Compiles and installs nginx-overload-handler (and it's dependencies as well
# as a few demo web apps)
#
# Designed for and tested on Ubuntu 11.10 64-bit
#
# WARNING: This install.sh script does many things and assumes much about its 
# operating environment. You are probably better off to use this install script
# as a guide, and execute its commands by hand.
#
# TODO:
#    - Error checking, and abort when any cmd fails
#

set -e

# $DIR is the absolute path for the directory containing this bash script
DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"

cd $DIR

# Install binary dependencies
sudo ./dependencies/install_binary_dependencies.sh

# Download source dependencies
./dependencies/download.sh

# Compile and install thrift
sudo ./dependencies/thrift_compile/install_dependencies.sh
./dependencies/thrift_compile/compile.sh
sudo ./dependencies/thrift_compile/install.sh
./dependencies/thrift_compile/record_lib_location.sh

# Compile and install nginx with the upstream_overload module (together)
sudo ./nginx_upstream_overload/install_dependencies.sh
sudo ./nginx_upstream_overload/useradd.sh
sudo ./nginx_upstream_overload/install_named_pipe.sh
./nginx_upstream_overload/compile.sh
sudo ./nginx_upstream_overload/install.sh

# Compile the Bouncer process manager
./bouncer/compile.sh

# Create the fcgi_user; FastCGI workers will run as this user
sudo ./dependencies/useradd.sh

