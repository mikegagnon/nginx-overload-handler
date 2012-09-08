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

==== README.txt for the solr_app ====
Instructions for installing and running the Solr web application using
a version of Java that is vulnerable to CVE-2010-4476. Useful for testing
nginx-overload-handler's ability to handle HashDoS attacks.

==== Prereq ====
(1) Install nginx-overload-handler via ../../install.sh
    WARNING: Read documentation in ../../install.sh before executing it.
(2) Install vulnerable Java. Read and follow the instructions in
    ../../dependencies/install_java.sh

==== Install solr ====
./install.sh

You can populate solr with some dummy data by doing:
./populate_solr.sh

==== Operation ====
Terminate solr:                 ./kill_solr.sh
Launch solr on port 9000:       ./launch_solr.sh

