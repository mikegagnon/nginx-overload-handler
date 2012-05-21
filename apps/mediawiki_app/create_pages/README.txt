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

==== README.txt for create_pages ====
Adds several Wikipedia pages to the local MediaWiki instance. Some pages
include the history of revisions (which is useful for testing MediaWiki's
diff feature).

==== Source of pages ====
These pages were downloaded from Wikipedia from the categories:

    - "Beaches of Hawaii (island)" in wikipedia_hawaiian_beaches.xml
    - "Beer styles" in wikipedia_beer_styles.xml

If you want to download these Wikipedia pages yourself, visit:

    http://en.wikipedia.org/wiki/Special:Export

In the "Add pages from category" field enter the name of the category and
click the add button. These pages are licensed under Creative Commons CC BY-SA
3.0. http://creativecommons.org/licenses/by-sa/3.0/

==== Importing pages into local MediaWiki instance ====
First, log in to MediaWiki as an administrator:

    Visit http://$SERVER_NAME/index.php?title=Special:UserLogin
    username: testadmin
    password: $MEDIAWIKI_PASSWORD taken from ../env.sh

NOTE: $SERVER_NAME is defined in nginx-overload-handler/siteconfig.sh

Then, import the pages:

    Visit: http://$SERVER_NAME/index.php?title=Special:Import
    Upload one of the wikipedia_*.xml files from this directory

==== Troubleshooting ====
MediaWiki can take a long time to import large archive files (such as
wikipedia_hawaiian_beaches.xml). It is possible that it will timeout
and the import will have only partially completed. That is OK.

For some of the wikipedia_*.xml archive file
http://$SERVER_NAME/index.php?title=Special:AllPages

