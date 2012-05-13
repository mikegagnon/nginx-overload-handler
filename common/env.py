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
# ==== env.py ====
#
# Executes a bash script and imports its environment variables. Kind of like
# the "source" command for bash.
#

import subprocess

def env(filename):
    cmd = ['/bin/bash', '-c', 'source %s && env' % filename]
    p = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    stdout, _ = p.communicate()
    if p.returncode != 0:
        raise ValueError("returncode != 0 == %d" % p.returncode)
    result = {}
    for line in stdout.split("\n")[:-1]:
        try:
            index = line.index("=")
        except ValueError:
            raise ValueError("Missing '=' in %s" % line)
        key = line[0:index]
        val = line[index + 1:]
        result[key] = val
    if len(result) == 0:
        raise ValueError("No environment variables found")
    return result

if __name__ == "__main__":
    import json
    import sys
    print json.dumps(env(sys.argv[1]), sort_keys=True, indent=2)

