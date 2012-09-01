#!/usr/bin/env python
#
# Copyright 2012 github.com/one10, Hellasec
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
# http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
#
################################################################################
#
# Convert space-separated Wikipedia pageview count dump files into JSON
#
import sys
import json
import urllib2

output = {}
for line in sys.stdin:
    parts = line.split()
    assert(len(parts) == 4)
    page = parts[1]
    try:
        page_unicode = page.encode("utf8")
    except UnicodeDecodeError:
        page_unicode = page
    page = urllib2.quote(urllib2.unquote(page_unicode))
    output[page] = int(parts[2])

json.dump(output, sys.stdout, indent=2)

