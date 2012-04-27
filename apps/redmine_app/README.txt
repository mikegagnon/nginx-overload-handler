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

==== README.txt for the redmine_app ====
Instructions for installing and running the Redmine web application using
a version of Ruby that is vulnerable to CVE-2011-481. Useful for testing
nginx-overload-handler's ability to handle HashDoS attacks. Attack code is not
included in this repository.

==== Prereq ====
Install nginx-overload-handler via ../../install.sh
WARNING: Read documentation in ../../install.sh before executing it.

==== Setup ====
Install binary dependencies

    sudo ./install_binary_dependencies.sh

Compile and install vulnerable ruby

    ../../dependencies/ruby_vuln/compile.sh
    sudo ../../dependencies/ruby_vuln/install.sh

Compile and install 3rd-party libraries needed by Redmine

    ./compile_dependencies.sh
    sudo ./install_dependencies.sh

Download and install gems needed by Redmine

    sudo ./install_gems.sh

Set up database for Redmine.

    ./create_db.sh

Install Redmine. It will prompt you for some input. The default values are fine.

    sudo ./install_redmine.sh

==== Launch ====
In time, there will be multiple configurations for redmine stored in different
subdirectories. For now, there is just a "standard" configuration, which
does not use the nginx-overload-handler.

Make and install standard configuration
    ./standard/make_conf.sh
    sudo ./standard/install_conf.sh

Launch redmine in standard configuration

    sudo ./standard/launch_redmine.sh

Use Redmine

    - Point your browser to http://localhost
    - Log in as username "admin", password "admin"

==== To do ====
The current "standard" installation here does not currently represent an
industry-standard redmine configuration. This configuration of Redmine can only
handle one request at a time.

TODO: Use mongrel to host Redmine, which will allow Redmine to handle
concurrent requests.

