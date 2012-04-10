Copyright 2012 HellaSec, LLC

  Licensed under the Apache License, Version 2.0 (the "License");
  you may not use this file except in compliance with the License.
  You may obtain a copy of the License at

      http://www.apache.org/licenses/LICENSE-2.0

  Unless required by applicable law or agreed to in writing, software
  distributed under the License is distributed on an "AS IS" BASIS,
  WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
  See the License for the specific language governing permissions and
  limitations under the License.

==== README.txt for bouncer ====

Contents:

bouncer_commony.py
    used by alert_router.py and bouncer_process_manager.py

bouncer_process_manager.py,
    the super class for bouncers. Each web application implements a subclass
    of bouncer_process_manager.py (which defines how start and kill FastCGI
    workers). For example, see ../dummy_fcgi_app/bouncer_for_dummy_app.py. Each
    pool of FastCGI workers runs its own instance of bouncer, which does the
    following:
        (a) Restarts its FastCGI workers if they crash
        (b) Listens for overload alerts from the alert_router. When it receives
            an alert, bouncer_process_manager.py restarts the FastGI worker
            that is specified in the alert.

alert_router.py
    listens for alerts from the upstream_overload nginx module (via a named
    pipe), then forwards those alerts to the appropriate Bouncer instance
    using thrift RPC.

BouncerService.thrift
    specifies the thrift RPC interface between bouncer_process_manager.py and
    alert_router.py

compile.sh
    script to compile the thrift file into Python stub code

example_config.json
    Alert Routers and Bouncers read the same config file. This is an example.

import_thrift_lib.py
    a hack that imports thrift's python library

==== Build instructions ====

PREREQUSIITE:
    Install thrift per the instructions in ../thrift_compile/README.txt

./compile.sh

==== Example usage ====

See ../dummy_fcgi_app/README.txt

