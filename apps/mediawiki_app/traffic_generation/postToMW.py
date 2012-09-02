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
# view, view edit form, post edit form for a Mediawiki page
#

from BeautifulSoup import BeautifulSoup
import urllib
import urllib2
import time # only for test

# SERVER_NAME = 'bg2.hellasec.com'
SERVER_NAME = 'localhost'

MW_EDIT_TOKEN_NAME = 'wpEdittime'
LASTMOD_ID = 't-permalink'
VIEW_URL = 'http://' + SERVER_NAME + '/index.php?title='
EDIT_URL = 'http://' + SERVER_NAME + '/index.php?action=edit&title='
EDIT_TARGET_URL = 'http://' + SERVER_NAME + '/index.php?action=submit&title='

# this function assumes a urlencoded page title
# it also taks a non-urlencode page replacement text
def postToMW(urlEncodedPageTitle, newPagePlainText):
    viewUrl = VIEW_URL + urlEncodedPageTitle
    editUrl = EDIT_URL + urlEncodedPageTitle
    editTargetUrl = EDIT_TARGET_URL + urlEncodedPageTitle
    
    # get the last mod string from a normal page view: footer-info-lastmod
    doc = urllib2.urlopen(viewUrl)
    soup = BeautifulSoup(doc.read())
    lastmod = soup.find(attrs={'id':LASTMOD_ID})
    # print "oldlastmod: " + str(lastmod)

    # fetch the edit token
    doc = urllib2.urlopen(editUrl)
    soup = BeautifulSoup(doc.read())
    token = soup.find(attrs={'name':MW_EDIT_TOKEN_NAME})
    # print "token: " + token["value"]

    # make a post
    values = {'wpEdittime' : token["value"],
             'wpEditToken' : '+\\',
             'wpTextbox1' : newPagePlainText,
             'wpSave' : 'Save page'}
    
    data = urllib.urlencode(values)
    req = urllib2.Request(editTargetUrl, data)

    # validate the response 
    response = urllib2.urlopen(req)
    soup = BeautifulSoup(response.read())
    newlastmod = soup.find(attrs={'id':LASTMOD_ID})
    # print "newlastmod: " + str(newlastmod.__class__)

    if lastmod == None or lastmod == "" or \
            newlastmod == None or newlastmod == "" or \
            lastmod == newlastmod:
        # print "error"
        # the page hasn't changed after post, or unable to determine = we have problems
        raise ValueError("post had problems and most likely didn't succeed")

################# a few test cases
# e.g.: S%CC%88%C3%B6m%CC%88%C3%AB_crazy_%C7%98mla%E1%B9%B3ts_%28and_some_%D0%A0%D1%83%D1%81%D1%81%D0%BA%D0%B8%D0%B9_text_for_a_good_measure%29
## pageTitle = 'S%CC%88%C3%B6m%CC%88%C3%AB_crazy_%C7%98mla%E1%B9%B3ts_%28and_some_%D0%A0%D1%83%D1%81%D1%81%D0%BA%D0%B8%D0%B9_text_for_a_good_measure%29'
#pageTitle = 'S%CC%88%C3%B6m%CC%88%C3%AB_crazy_%C7%98mla%E1%B9%B3ts_(and_some_%D0%A0%D1%83%D1%81%D1%81%D0%BA%D0%B8%D0%B9_text_for_a_good_measure)'
#pageTitle = "Test00"
##pageTitle = "Test00"
##pageText = time.asctime(time.localtime(time.time()))
##postToMW(pageTitle, pageText)

