#!/usr/bin/env python
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
# ==== get_pages.py ====
#
# Asks the MediaWiki instance for a list of its pages and outputs
# a JSON structure with links to those pages.
#
# USAGE:
#   - Make sure that MediaWiki is running
#   > ./get_pages.py > pages.json
#
# OUTPUT FORMAT:
# output[pagetitle]["view"] = url to view that wiki page
# output[pagetitle]["diff"] = list of urls that ask for diffs on that page
#
# Example:
# {
#  "India_Pale_Ale": {
#    "diff": [],
#    "view": "/index.php?title=India_Pale_Ale"
#  },
#  "Isaac_Hale_Beach_Park": {
#    "diff": [
#      "/index.php?title=Isaac_Hale_Beach_Park&action=historysubmit&diff=523&oldid=522",
#      "/index.php?title=Isaac_Hale_Beach_Park&action=historysubmit&diff=524&oldid=523",
#      "/index.php?title=Isaac_Hale_Beach_Park&action=historysubmit&diff=525&oldid=524",
#      "/index.php?title=Isaac_Hale_Beach_Park&action=historysubmit&diff=526&oldid=525",
#      "/index.php?title=Isaac_Hale_Beach_Park&action=historysubmit&diff=527&oldid=526",
#      "/index.php?title=Isaac_Hale_Beach_Park&action=historysubmit&diff=528&oldid=527",
#      "/index.php?title=Isaac_Hale_Beach_Park&action=historysubmit&diff=529&oldid=528",
#      "/index.php?title=Isaac_Hale_Beach_Park&action=historysubmit&diff=530&oldid=529"
#    ],
#    "view": "/index.php?title=Isaac_Hale_Beach_Park"
#  },
#  ...
# }
#


import os
import sys
import urllib
import urllib2
import json
import re
import random
import httplib


DIRNAME = os.path.dirname(os.path.realpath(__file__))

sys.path.append(os.path.join(DIRNAME, '..', '..', '..', 'common'))

import log
import env

mediawiki_app = os.path.join(DIRNAME, "..", "env.sh")
var = env.env(mediawiki_app)
MEDIAWIKI_ATTACK_PAGES_RE = var["MEDIAWIKI_ATTACK_PAGES_RE"]
attack_re = re.compile(MEDIAWIKI_ATTACK_PAGES_RE)

siteconfig = os.path.join(DIRNAME, "..", "..", "..", "siteconfig.sh")
var = env.env(siteconfig)
SERVER_NAME = var["SERVER_NAME"]

def getjson(url):
    try:
        response = urllib2.urlopen(url)
    except urllib2.URLError:
        sys.stderr.write("Error: Could not access %s. Perhaps MediaWiki is not running.\n\n" % SERVER_NAME)
        sys.exit(1)
    return json.loads(response.read())


sys.stderr.write("Getting list of pages\n")
url = "http://%s/api.php?action=query&list=allpages&aplimit=500&format=json&apfilterredir=nonredirects" % SERVER_NAME
response = getjson(url)
pages = response['query']['allpages']
unescaped_titles = [page['title'] for page in pages]
sys.stderr.write("%d pages found\n" % len(unescaped_titles))

# note this titles look like this, for example, "Hapuna BeachState Recreation Area"
# they need to be escaped, MediaWiki style "Hapuna_Beach_State_Recreation_Area".
# If you simply do a url ecnoding, then MediaWiki will returns with a 301 redirect
# with the actual title, which is what we want
def mwEscape(title):
    try:
        url = "/index.php?title=%s" % urllib.quote(title)
    except KeyError:
        # Happens with non-ascii titles, which we ignore for now (by returning None)
        # TODO: Handle non-ascii titles
        return None
    conn = httplib.HTTPConnection(SERVER_NAME)
    conn.request("GET", url)
    response = conn.getresponse()
    if response.status == 301:
        location = response.getheader("Location")
        escaped_title = location.split("=")[-1]
        sys.stderr.write("Escaped title to '%s'\n" % escaped_title)
        url = "/index.php?title=%s" % urllib.quote(escaped_title)
        conn = httplib.HTTPConnection(SERVER_NAME)
        conn.request("GET", url)
        response = conn.getresponse()
        if response.status != 200:
            raise ValueError("Escaped title does not lead to status == 200, for '%s' --> status = %d, %s" % (escaped_title, response.status, url))
    elif response.status == 200:
        escaped_title = title
        sys.stderr.write("Did not escape title '%s'\n" % escaped_title)
    else:
        raise ValueError("Got status %d while requesting '%s'" % (response.status, title))

    return escaped_title

titles = [mwEscape(title) for title in unescaped_titles]
# Get rid of non-ascii titles
titles = filter(lambda x: x != None, titles)

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
    url = "http://%s/api.php?action=query&prop=revisions&titles=%s&rvlimit=500&rvprop=ids&format=json" % \
        (SERVER_NAME, urllib.quote(title))
    response = getjson(url)
    revisions = response["query"]["pages"].popitem()[1]["revisions"]
    page_version[title] = sorted([rev["revid"] for rev in revisions])
    sys.stderr.write("%d revisions\n" % len(page_version[title]))
    if len(page_version[title]) < 2:
        sys.stderr.write("    ignoring %s\n" % title)
        del(page_version[title])

urls = {}

for title in page_titles:
    url = "/index.php?title=%s" % urllib.quote(title)
    urls[title] = {"view":url, "diff" : []}

page_version_titles = page_version.keys()
for title in page_version_titles:
    revids = page_version[title]
    first_rev = revids[0]
    for second_rev in revids[1:]:
        url = "/index.php?title=%s&action=historysubmit&diff=%d&oldid=%d" % \
            (urllib.quote(title), second_rev, first_rev)
        first_rev = second_rev
        urls[title]["diff"].append(url)

print json.dumps(urls, sort_keys=True, indent=2)

