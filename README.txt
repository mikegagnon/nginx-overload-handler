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

==== README.txt for nginx-overload-handler ====
How does the Nginx webserver handle web-application overloads? It doesn't.
Instead, Nginx just keeps piping requests to the web application and lets
them deal with overloads. How do web applications handle overloads? They
usually don't.

That's a problem.

nginx-overload-handler is an attempt to solve this problem by (1) having nginx
detect overloads, (2) alerting web applications of overloads, and (3) implementing
generic, default behavior for web applications that enables them to survive
overloads.

==== How is it implemented? ====
Several moving parts:
    (1) A new load balancing module for nginx, upstream_overload.
        See nginx_upstream_overload/README.txt
    (2) An Alert Router receives alerts from upstream_overload (via
        a named pipe) and forwards these alerts to the appropriate
        Bouncer (via Thrift RPC).
        See bouncer/README.txt
    (3) Each Bouncer manages a group of FastCGI worker process that
        implements the web application. When one of those workers, dies
        the Boucner restarts it. When it receives an alert from the Alert
        Router, it kills one of the workers to help deal with the overload.
        See bouncer/README.txt

==== Requirements ====
Designed and tested on Linux (specifically Ubuntu 11.10 32-bit and 64-bit),
but should be portable to other *nix's with minimal effort.

==== WARNING ====
Some of these files (particularly the ones that need to be run as sudo)
might do things you don't want, such as overwriting nginx configuration
files without backuping up your old ones. If you are concerned about this
sort of thing I recommend viewing the files that require sudo before you
execute them. It's probably best to test nginx-overload-handler in its
own VM.

==== Is this code ready for production? ====
Definintely not. It is highly experimental.

==== Installing nginx-overload-handler on localhost ====
If you're brave, just run:
    ./install.sh

If you're patient, read install.sh and run the commands one at at a time.

==== Testing with MediaWiki ====
Make and install the config files
    ./apps/mediawiki_app/upstream_overload/make_conf.sh
    sudo ./apps/mediawiki_app/upstream_overload/install_conf.sh

Start bouncer, alert router, and nginx (in separate terminals)
    sudo ./apps/mediawiki_app/upstream_overload/run_bouncer.sh
    ./apps/mediawiki_app/upstream_overload/run_alert_router.sh
    sudo ./nginx_upstream_overload/launch_nginx.sh

==== Testing with MediaWiki, without our overload handler ====
For the sake of comparison, we also include instructions
for running MediaWiki without the overload-handler system.

Make and install the config files
    ./apps/mediawiki_app/standard/make_conf.sh
    sudo ./apps/mediawiki_app/standard/install_conf.sh

Start the php FastCGI server and launch nginx (in separate terminals)
    sudo ./apps/mediawiki_app/standard/run_php.sh
    sudo ./nginx_upstream_overload/launch_nginx.sh

Point your browser to http://localhost/index.php?title=Main_Page

==== Testing with dummy_py_app ====
TODO: Update this section

Install the nginx.conf for the dummy py app
    sudo ./dummy_py_app/install.sh

Launch the Bouncer process managers
    ./dummy_py_app/bouncer_for_dummy_app.py dummy_py_app/bouncer_config.json 127.0.0.1 3001
    ./dummy_py_app/bouncer_for_dummy_app.py dummy_py_app/bouncer_config.json 127.0.0.1 3002

Launch the Alert Router
    ./bouncer/alert_router.py dummy_py_app/bouncer_config.json

Launch nginx
    sudo ./nginx_upstream_overload/launch_nginx.sh

Try a fast request (should print "Oh hai!")
    curl -s http://localhost/test.py

Try a slow request (should hang 5 sec then print "Slept for 5.000000 sec.\n Oh hai!"
    curl -s http://localhost/test.py?sleep=5

Run a mix of fast and slow requests. Observe the fast requests being serviced,
while the slow requests are evicted by the bouncer.
    ./dummy_py_app/send_loop.sh

