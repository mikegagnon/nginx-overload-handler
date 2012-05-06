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
Adds 12 pages to the local MediaWiki instance (including the history
of revisions for each page).

==== Source of pages ====
These pages were downloaded from Wikipedia from the "Beaches of Hawaii
(island)" category. You can access these pages from Wikipedia by visiting

    http://en.wikipedia.org/wiki/Special:Export

In the "Add pages from category" field enter "Beaches of Hawaii (island)",
click the add button. Then make sure the field "Include only the current
revision, not the full history" is checked, then click the "export button."

These pages are licensed under Creative Commons CC BY-SA 3.0.

    http://creativecommons.org/licenses/by-sa/3.0/

==== Importing pages into local MediaWiki instance ====
First, log in to MediaWiki as an administrator:

    Visit http://localhost/index.php?title=Special:UserLogin
    username: testadmin
    password: $MEDIAWIKI_PASSWORD taken from ../env.sh

Then, import the pages:

    Visit: http://localhost/index.php?title=Special:Import
    Upload the file wikipedia_sample_pages.xml

==== Getting list of pages ====
http://localhost/api.php?action=query&list=allpages&aplimit=500&format=json

==== Getting list of revisions for a page ====
Replace PAGE_TITLE with a page title in
http://localhost/api.php?action=query&prop=revisions&titles=PAGE_TITLE&rvlimit=500&rvprop=ids&format=json

