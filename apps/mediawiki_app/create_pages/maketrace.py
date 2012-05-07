#
# Copyright 2012 HellaSec, LLC
#
#  Licensed under the Apache License, Version 2.0 (the "License");
#  you may not use this file except in compliance with the License.
#  You may obtain a copy of the License at
#
#      http://www.apache.org/licenses/LICENSE-2.0
#
#  Unless required by applicable law or agreed to in writing, software
#  distributed under the License is distributed on an "AS IS" BASIS,
#  WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
#  See the License for the specific language governing permissions and
#  limitations under the License.
#
# ==== maketrace.py ====
#
# Prints a list of URLs, which represents a stream of "legitimate" URL
# acccesses for MediaWiki.
#
# USAGE:
#   - Make sure that MediaWiki is running
#   > ./maketrace.sh  root_url num_urls > legit_trace.txt
# NOTE that you invoke the .sh file, not the .py file
#

import os
import sys
import urllib
import urllib2
import json
import re
import random
import httplib


# the percentage of MediaWiki requests that are for diffs
# (the other requests are just for page views)
diff_percent = 0.0

root_url = sys.argv[1]
domain = root_url.replace("http://", "")

# the number of urls to output
num_urls = int(sys.argv[2])

def getenv(key):
    try:
        val = os.environ[key]
    except KeyError:
        sys.stderr.write("Error: the environment variable %s is not defined. Make sure you invoke the .sh file (not the .py file)\n\n" % key)
        sys.exit(1)
    return val

def getjson(url):
    try:
        response = urllib2.urlopen(url)
    except urllib2.URLError:
        sys.stderr.write("Error: Could not access %s. Perhaps you MediaWiki is not running.\n\n" % root_url)
        sys.exit(1)
    return json.loads(response.read())

attack_re_str = getenv("MEDIAWIKI_ATTACK_PAGES_RE")
attack_re = re.compile(attack_re_str)

sys.stderr.write("Getting list of pages\n")
url = "%s/api.php?action=query&list=allpages&aplimit=500&format=json&apfilterredir=nonredirects" % root_url
response = getjson(url)
pages = response['query']['allpages']
unescaped_titles = [page['title'] for page in pages]
sys.stderr.write("%d pages found\n" % len(unescaped_titles))

# note this titles look like this, for example, "Hapuna BeachState Recreation Area"
# they need to be escaped, MediaWiki style "Hapuna_Beach_State_Recreation_Area".
# If you simply do a url ecnoding, then MediaWiki will returns with a 301 redirect
# with the actual title, which is what we want
def mwEscape(title):
    url = "/index.php?title=%s" % urllib.quote(title)
    conn = httplib.HTTPConnection(domain)
    conn.request("GET", url)
    response = conn.getresponse()
    if response.status == 301:
        location = response.getheader("Location")
        escaped_title = location.split("=")[-1]
        sys.stderr.write("Escaped title to '%s'\n" % escaped_title)
        url = "/index.php?title=%s" % urllib.quote(escaped_title)
        conn = httplib.HTTPConnection(domain)
        conn.request("GET", url)
        response = conn.getresponse()
        if response.status != 200:
            raise ValueError("Escaped title does not lead to status == 200, for '%s'" % escaped_title)
    elif response.status == 200:
        escaped_title = title
        sys.stderr.write("Did not escape title '%s'\n" % escaped_title)
    else:
        raise ValueError("Got status %d while requesting '%s'" % title)

    return escaped_title

titles = [mwEscape(title) for title in unescaped_titles]

# for each title included in the trace, page_version[title]
# maps a list of sorted page ids (ints)
page_version = {}
page_titles = []
for title in titles:
    if not attack_re.search(title):
        page_version[title] = set()
        page_titles.append(title)

sys.stderr.write("Ignoring %d page(s)\n" % (len(titles) - len(page_version)))
for title in page_version.keys():
    sys.stderr.write("Getting revisions for %s pages --> " % title)
    url = "%s/api.php?action=query&prop=revisions&titles=%s&rvlimit=500&rvprop=ids&format=json" % \
        (root_url, urllib.quote(title))
    response = getjson(url)
    revisions = response["query"]["pages"].popitem()[1]["revisions"]
    page_version[title] = sorted([rev["revid"] for rev in revisions])
    sys.stderr.write("%d revisions\n" % len(page_version[title]))
    if len(page_version[title]) < 2:
        sys.stderr.write("    ignoring %s\n" % title)
        del(page_version[title])

page_version_titles = page_version.keys()
for url_i in range(0, num_urls):
    if random.random() <= diff_percent:
        title = random.choice(page_version_titles)
        revids = page_version[title]
        first_rev_i = random.randint(0, len(revids) - 2)
        first_rev = revids[first_rev_i]
        second_rev = revids[first_rev_i + 1]
        url = "/index.php?title=%s&action=historysubmit&diff=%d&oldid=%d" % \
            (urllib.quote(title), second_rev, first_rev)
    else:
        title = random.choice(page_titles)
        url = "/index.php?title=%s" % urllib.quote(title)

    print url
    print
