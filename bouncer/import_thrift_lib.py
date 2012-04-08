#!/usr/bin/env python
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
# ==== import_thrift_lib.py (a hack) ====
#
# When I installed thrift via the default configuration, it put the python
# library in place that wasn't in sys.path. Which means importing the thrift
# library failed.
#
# To hack around this:
#   (1) the ./thrift_compile/compile.sh script specifies to put the python
#       lib in a particular directory.
#   (2) the ../thrift_compile/record_lib_location.sh script determines the final
#       location of the python lib, and records it in the text file
#       ../thrift_compile/python_thrift_lib/path.txt/
#
# So now we can import the python thrift lib by updating the path
#

import sys
import os

path_filename = os.path.join("..", "thrift_compile", "python_thrift_lib", "path.txt")

with open(path_filename) as f:
    python_thrift_lib_path = f.readline().rstrip()
    sys.path.append(python_thrift_lib_path)

