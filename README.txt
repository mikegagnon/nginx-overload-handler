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

==== Want to see it in action? ====

See dummy_fcgi_app/README.txt


