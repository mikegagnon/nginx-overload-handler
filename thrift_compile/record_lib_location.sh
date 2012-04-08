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
# ==== Record the location of thrift's python library ====
#

CWD=`pwd`

PYTHON_LIB_INSTALL=$CWD/python_thrift_lib

# the make script installs the python thrift library somewhere
# in PYTHON_LIB_INSTALL. Find it, and save it in path.txt
# so that way the python scripts (that use thrift) can know
# where to import the thrift scripts from
PYTHON_THRIFT_LIB=`find $PYTHON_LIB_INSTALL -name site-packages`
echo $PYTHON_THRIFT_LIB > $PYTHON_LIB_INSTALL/path.txt

