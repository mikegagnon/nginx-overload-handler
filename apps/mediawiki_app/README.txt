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

==== README.txt for the mediawiki_app ====
Instructions for installing and running the MediaWiki web application using
a version of PHP that is vulnerable to CVE-2011-4885. Useful for testing
nginx-overload-handler's ability to handle HashDoS attacks. Attack code is not
included in this repository.

==== Prereq ====
Install nginx-overload-handler via ../../install.sh
WARNING: Read documentation in ../../install.sh before executing it.

==== Setup ====
Compile and install vulnerable version of PHP

    ../../dependencies/php_vuln/compile.sh
    ../../dependencies/php_vuln/install.sh

Compile and install MediaWiki

    sudo ./install_dependencies.sh
    sudo ./install_mediawiki.sh

==== Launch ====
You can launch MediaWiki in two configurations:
    (1) standard: Represents an industry-standard approach to running
        MediaWiki. Does not use the nginx-overload-handler system.
    (2) upstream_overload: Uses nginx-overload-handler.

==== Launch standard configuration ====

    ./standard/make_conf.sh
    sudo ./standard/install_conf.sh
    sudo ../../nginx_upstream_overload/launch_nginx.sh
    sudo ./standard/launch_mediawiki.sh

Point your browser to "http://localhost/index.php"

==== Launch upstream_overload configuration ====

    ./upstream_overload/make_conf.sh
    sudo ./upstream_overload/install_conf.sh

In separate terminals:

    sudo ./upstream_overload/run_bouncer.sh
    ./upstream_overload/run_alert_router.sh
    sudo ../../nginx_upstream_overload/launch_nginx.sh

Point your browser to "http://localhost/index.php"

