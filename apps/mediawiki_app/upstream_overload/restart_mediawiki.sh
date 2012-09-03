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
# ==== restart_mediawiki.sh ====
#
# USAGE: sudo ./restart_mediawiki.sh
#

DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
source $DIR/../../../nginx_upstream_overload/env.sh
DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"

# create a ramdisk for the signature file
mkdir -p $NGINX_RAMDISK_DIR
umount $NGINX_RAMDISK_DIR
mount -t tmpfs none $NGINX_RAMDISK_DIR -o size=256M

$DIR/kill_mediawiki.sh
# TODO: actually verify that mediawiki is dead, instead of just
# sleeping for a second
sleep 1
$DIR/launch_mediawiki.sh

sleep 1
$DIR/../../../nginx_upstream_overload/launch_nginx.sh

