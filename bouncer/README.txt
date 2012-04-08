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
(1) bouncer_process_manager.py, the Bouncer process manager. Each
    pool of FastCGI workers runs and instance of bouncer_process_manager.py,
    which does the following:
        (a) Restarts its FastCGI workers if they crash
        (b) Listens for overload alerts from the alert_router. When it receives
            an alert, bouncer_process_manager.py restarts the FastGI worker
            that is specified in the alert.
(2) alert_router.py, which listens for alerts from the upstream_overload nginx
    module (via a named pipe), then forwards those alerts to the appropriate
    Bouncer instance using thrift RPC.
(3) BouncerService.thrift, which specifies the thrift RPC interface between
    bouncer_process_manager.py and alert_router.py

==== Build instructions ====

PREREQUSIITE:
    Install thrift per the instructions in ../thrift_compile/README.txt

./compile.sh
