Copyright 2012 github.com/one10, Hellasec
http://www.apache.org/licenses/LICENSE-2.0
################################################################################

MediaWiki "realistic" traffic replay toolkit

Best setup is if the MW exp-import script is run on a target MediaWiki server
While the trace and traffic gen. scripts are run from the second, "attacking" server

* assumes MediaWiki has been installed using the scripts in the dir above

The flow and the files are as follows:

=====================
1. download the big pageview count file from, e.g.:
http://dumps.wikimedia.org/other/pagecounts-raw/2012/2012-03/
gunzip it into ./data

2. Script filters out garbage pages, generates pageview count json
Files:
./prepare_inputs.sh
Output example:
./data/pagecounts-20120301-040000.json

3. Trace gen .sh generates a trace from json (envetually using the new variates alg)
4. collapses the trace into a importable Wiki list
Files:
./trace_and_list_gen.sh
./trace_gen.py (invoked by .sh)
Output example:
./data/pagecounts-20120301-040000.trace
./data/pagecounts-20120301-040000.titles

5. Script to exp-import WP pages (import script+data must be run on the target MW server)
Files:
./export_wp_pages.sh 
(calls MW's importDump.php, so run with the input list from the prior step on MW server)
Output example:
./data/pagecounts-20120301-040000.0.wpimport.xml
./data/pagecounts-20120301-040000.15.wpimport.xml

6. Test or puzzle_solver: loops through trace, gets/posts MW page data according to trace
Files:
./test_run_trace.sh (calls postToMW.py)
(just to test the generated trace, may need to re-run all steps 1-6 after done testing)

For now, simply appends a few random chars to the old page body.

for the real trace runs, read documentation for doorman_test, e.g.:
nginx-overload-handler/doorman_test/puzzle_solver.py

Misc:
A script to erase all data from a Mediawiki instance for re-import (CLI php on MW server):
recreate_mw_db.sh

=====================
Notes/Todo/Limitations:
* Once a trace is generated, then some page export-import might fail. Such pages though
present in the trace, will not contribute to a realistic traffic pattern if ex-imp fails.

