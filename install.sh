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
#    - Find where apt-get asks for yes's and automate it
#

set -e

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

# It is useful to test the the system against a vulnerable version of php
./dependencies/php_vuln/compile.sh
./dependencies/php_vuln/install.sh

# Create the php_fcgi user
sudo ./dependencies/useradd.sh

# NOTE: the install.sh script installs the vulnerable php version in the
# dependencies/php_vuln/install directory so you don't need root to install
# it and you don't need to worry about accidentally using the vulnerable
# version of php (since it doesn't touch /usr/bin and so on)

# Create a new user for the FastCGI workers to run as
sudo ./bouncer/php_bouncer/useradd.sh

# Install MediaWiki
sudo ./apps/mediawiki_app/install_dependencies.sh
sudo ./apps/mediawiki_app/install_mediawiki.sh

