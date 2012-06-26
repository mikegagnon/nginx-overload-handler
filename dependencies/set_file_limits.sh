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
# ==== set_file_limits.sh ====
#
# USAGE: sudo ./set_file_limits.sh
#
# Modifies Linux kernel settings to allow more than 1024 files to be open
# at once. Sadly you must logout and log back in for settings to take effect.
# A reboot will do.
#

LIMITS_CONF=/etc/security/limits.conf
grep "*       soft    nofile  65535" $LIMITS_CONF > /dev/null
if [ $? -ne 0 ] ;
then
cat >> $LIMITS_CONF <<InputComesFromHERE
*       soft    nofile  65535
*       hard    nofile  65535
InputComesFromHERE
echo "Updated $LIMITS_CONF"
else
echo "No need to update $LIMITS_CONF"
fi

SYSCTL_CONF=/etc/sysctl.conf
grep "fs.file-max = 65535" $SYSCTL_CONF > /dev/null
if [ $? -ne 0 ] ;
then
echo "fs.file-max = 65535" >> /etc/sysctl.conf
echo "Updated $SYSCTL_CONF"
else
echo "No need to update $SYSCTL_CONF"
fi

echo "Open file limit: `ulimit -Sn`"
if [ `ulimit -Sn` -ne "65535" ]
then
echo "You need to reboot the machine"
fi
