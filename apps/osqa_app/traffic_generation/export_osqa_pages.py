#!/usr/bin/python 
#
# Copyright 2012 github.com/one10, Hellasec
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
# http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
#
################################################################################
#
# export meta.osqa.net data, requires beautiful soup and what not
# assumes the local OSQA database has been purged
#

from BeautifulSoup import BeautifulSoup
import urllib
import urllib2
import time
from HTMLParser import HTMLParser
from urllib2 import HTTPError

TIMEOUT = 5
EXPORT_START_QUESTNUM = 1
EXPORT_LIMIT = 3
SERVER_NAME = 'meta.osqa.net'
OSQA_USER = 'beergarden'
OSQA_USERPASS_HASH = 'sha1$fdd5f$cdcd8f11b6113a3f42de2971d99a4df651f30552'

USER_QUERY1 = "insert into auth_user values (1 ,'" + OSQA_USER \
    + "','','','foo@localhost','" + OSQA_USERPASS_HASH \
    + "',1,1,1,'2012-08-26 21:21:59','2012-08-26 21:21:59');"
USER_QUERY2 = "insert into forum_user values (1, 0, 0, 1, 0, 0, 0, " \
    + "'2012-08-26 21:45:19', '', '', '', NULL, '');"
PAGE_Q_PART1 = "insert into forum_node values ('"
PAGE_Q_PART2 = "', '"
PAGE_Q_PART3 = "' , 'tag1', 1 , '"
PAGE_Q_PART4 = "', 'question', NULL, NULL, '2012-08-26 21:21:59', 0 , '', " \
    + " NULL, 1 ,'2012-08-26 21:21:59', "
PAGE_Q_PART5 = " , NULL, NULL, 1 , 0);"

# strip tags comes from here: 
# http://stackoverflow.com/questions/753052/strip-html-from-strings-in-python
class MLStripper(HTMLParser):
    def __init__(self):
        self.reset()
        self.fed = []
    def handle_data(self, d):
        self.fed.append(d)
    def get_data(self):
        return ''.join(self.fed)
def strip_tags(html):
    s = MLStripper()
    s.feed(html)
    return s.get_data()
# end strip tags

def readFromOsqaMeta(url, count):
    try:
        doc = urllib2.urlopen(url)
    except HTTPError, e:
        # if e.code == 404:
        return # just skip for now

    soup = BeautifulSoup(doc.read())
    #title = soup.find(attrs={'id':LASTMOD_ID})
    title = soup('h1')[0]
    assert(title != None and title != "")
    title = strip_tags(str(title))
    assert(title != None and title != "")
    title= title.replace("'", "\\'")

    body = soup.find(attrs={'class':'question-body'})
    # TODO: get rid of question-body div itself, possibly other technical tags
    assert(body != None and body!= "")
    body = str(body).replace("\n", " ")
    body = body.replace("'", "\\'")
    query = PAGE_Q_PART1 + str(count)  + PAGE_Q_PART2 + title + PAGE_Q_PART3 \
        + body + PAGE_Q_PART4 + str(count)  + PAGE_Q_PART5
    return query

### driver

# add user
print USER_QUERY1
print USER_QUERY2

# loop through pages
for i in range(EXPORT_LIMIT):
    url = "http://" + SERVER_NAME + "/questions/" + str(EXPORT_START_QUESTNUM + i)
    print readFromOsqaMeta(url, i + 1)
    time.sleep(TIMEOUT)
