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
Install nginx-overload-handler via ../../install.sh
WARNING: Read documentation in ../../install.sh before executing it.

==== Install vulnerable Java ====
Manually download and install Java SE Development Kit 6u22 oracle.com.
Browse to

    http://www.oracle.com/technetwork/java/javasebusiness/downloads/java-archive-downloads-javase6-419409.html#jdk-6u22-oth-JPR

and click the link for "jdk-6u22-linux-x64.bin" (make sure to check
"Accept License Agreement").

Copy jdk-6u22-linux-x64.bin to:

    nginx-overload-handler/dependencies/downloads/

Unless you have previously downloaded Java from Oracle before, Oracle
will likely prompt you to create an account.

==== Install solr ====
Running ../../dependencies/download.sh unzips solr, which is all that is
needed to install it.

You can populate solr with some dummy data by doing:
./standard/populate_solr.sh

==== Operation ====
Terminate solr:                 ./standard/kill_solr.sh
Launch solr on port 8983:       ./standard/launch_solr.sh 8983
Launch solr on ports 9000 9006: ./standard/launch_solr.sh 9000 9006

