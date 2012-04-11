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

==== README.txt for the nginx_upstream_overload module ====

A load-balancing module for nginx with the following key features:
    (*) Keeps track of which backend servers are busy/idle.
    (*) Only sends requests to idle backend servers. Yields 502 error
        if there are no idle backends.
    (*) When the number of idle backends reaches num_spare_backends
        (or below), then sends an alert to a named pipe, which identifies
        the backend server that has been busy the longest. (The intent is
        that a daemon will listen on this pipe and then somehow abort the
        request being processed by the backend server.)

Current limitations:
    (*) There can only be one upstream configuration block, per nginx
        configuration file.
    (*) Cannot surive reloads (i.e. nginx -s reload). Instead of doing a
        reload, just do: nginx -s stop; nginx

==== Comparison to upstream_fair module ====

upstream_overload provides similar functionality to the upstream_fair
3rd-party module with weight_mode=peak and all servers have weight=1.
Except upstream_fair does not send overload alerts.

    See http://nginx.localdomain.pl/wiki/UpstreamFair

Also, upstream_overload is designed to be scalable w.r.t. (a) the number of
nginx worker processes and (b) the number of backend worker processes. Makes
most load-balancing operations in O(c) time, as opposed to upstream_fair, which
has most load-balancing decisions of O(N), where N is the number of backend
servers.

==== Comile ====

./compile.sh

==== Install ====

sudp ./install.sh

==== Configure and use module ====

see ../dummy_fcgi_app for an example of how to use this module.

There are three directives that upstream_overload accepts within the nginx
configuration file.
    (*) overload
    (*) num_spare_backends
    (*) alert_pipe

These directives are specified like this:

    http {

        [... abridged ...]

        num_spare_backends 1;
        alert_pipe /home/nginx_user/alert_pipe;

        upstream my_backend  {

            #activate the upstream_overload module
            overload;

            server    localhost:9007;
            server    localhost:9008;
            server    localhost:9009;
            server    localhost:9010;
        }
    }

This configuration specifies that:
    (*) The my_backend upstream block, uses the upstream_overload modules
        (via the inclusion of 'overload;')
    (*) Alert messages are sent the /home/nginx_user/alert_pipe named pipe
    (*) If 1 (or fewer) upstream servers (aka backend servers, aka peers)
        are idle, then the module will send an alert (via num_spare_backends).

==== Read alert messages ====

You can do something as simple as cat /home/nginx_user/alert_pipe. However,
there are nuances to the ordering of pipes opening, closing, etc.

For convenience there is a script alert_reader.py, which cats a pipe,
and continuously re-opens as needed. So you can you run alert_reader.py
once and restart nginx multiple times.

Note: nginx won't start unless there is a process reading the alert_pipe;
make sure to run alert_reader.py before launching nginx.

Usage:
    ./alert_reader.py /home/nginx_user/alert_pipe

==== TODO ====

To the extent possible, make the whole system resilient to crashes, erroneous messages,
etc.

