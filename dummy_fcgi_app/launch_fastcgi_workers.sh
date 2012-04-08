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

# Kill any running workers
###############################################################################

pkill -f "fcgi_worker_process.py"

# Launch the workers
###############################################################################

python fcgi_worker_process.py 9000 &
python fcgi_worker_process.py 9001 &
python fcgi_worker_process.py 9002 &
python fcgi_worker_process.py 9003 &

