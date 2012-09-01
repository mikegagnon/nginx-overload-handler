#!/usr/bin/env bash
#
# Copyright 2012 HellaSec, LLC
#
#  Licensed under the Apache License, Version 2.0 (the "License");
#  you may not use this file except in compliance with the License.
#  You may obCONFIG_INSTALLED_BACKUPtain a copy of the License at
#
#      http://www.apache.org/licenses/LICENSE-2.0
#
#  Unless required by applicable law or agreed to in writing, software
#  distributed under the License is distributed on an "AS IS" BASIS,
#  WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
#  See the License for the specific language governing permissions and
#  limitations under the License.
#
# ==== dissect Wikipedia trace ====
# First download a trace from http://www.wikibench.eu/wiki/2008-01/
# It's just a timestamped list of url accesses for Wikipedia.
# 
# In our tests we used wiki.1199203018
#
# Usage: ./dissect_wiki_trace.sh trace_file
#
# Outputs partitions the trace into files, grouping by URL features. Useful
# for synthesizing MediaWiki traces.
#

ROOT=$1

ENGLISH=$ROOT.english

echo $ENGLISH

#cat $ROOT \
#	| awk '{print $3}' \
#	| grep "http://en.wikipedia.org" \
#	> $ENGLISH

STATIC=$ENGLISH.static
DYNAMIC=$ENGLISH.dynamic
echo $STATIC
echo $DYNAMIC
STATIC_REGEX='\.(css|jpg|png|js|gif|ico|txt)\??'
grep    -E "$STATIC_REGEX" $ENGLISH > $STATIC
grep -v -E "$STATIC_REGEX" $ENGLISH > $DYNAMIC

# 21% of dynamic urls have "Special:"
SPECIAL=$DYNAMIC.special
NON_SPECIAL=$DYNAMIC.non_special
echo $SPECIAL
echo $NON_SPECIAL
SPECIAL_REGEX='Special(:|%3(A|a))'
grep    -E "$SPECIAL_REGEX" $DYNAMIC > $SPECIAL
grep -v -E "$SPECIAL_REGEX" $DYNAMIC > $NON_SPECIAL

# proportion of special:
# 44% Special:NoticeLocal
# 26% Special:Search
# 14% Special:Random
# 11% Special:Recentchanges
# 2% Special%3ASearch
# 1% Special:Export
# 3% other
SPECIAL_ACTIONS=$SPECIAL.actions
echo $SPECIAL_ACTIONS
SPECIAL_ACTIONS_REGEX='Special(:|%3(A|a))[^&/?]*'
grep -E -o "$SPECIAL_ACTIONS_REGEX" $SPECIAL | sort | uniq -c | sort -rn \
	> $SPECIAL_ACTIONS

#########

# 51% of dynamic
WIKI_SINGLE=$NON_SPECIAL.wiki_single
WIKI_SINGLE_REGEX='^http://en.wikipedia.org/wiki/[^/]*$'
echo $WIKI_SINGLE
grep    "$WIKI_SINGLE_REGEX" $NON_SPECIAL > $WIKI_SINGLE

# 0.3% of dynamic
WIKI_MULTIPLE=$NON_SPECIAL.wiki_multiple
WIKI_MULTIPLE_REGEX='^http://en.wikipedia.org/wiki/.*/'
echo $WIKI_MULTIPLE
grep    "$WIKI_MULTIPLE_REGEX" $NON_SPECIAL > $WIKI_MULTIPLE

# 0.7% of dynamic
STYLE=$NON_SPECIAL.style
STYLE_REGEX='^http://en.wikipedia.org/style/'
echo $STYLE
grep    "$STYLE_REGEX" $NON_SPECIAL > $STYLE

# 7% of dynamic
OPENSEARCH=$NON_SPECIAL.opensearch
OPENSEARCH_REGEX='^http://en.wikipedia.org/w/opensearch_desc.php'
echo $OPENSEARCH
grep    "$OPENSEARCH_REGEX" $NON_SPECIAL > $OPENSEARCH

# 20% of dynamic (mostly gen, see below)
OTHER=$NON_SPECIAL.other
echo $OTHER
grep -E -v "($WIKI_SINGLE_REGEX)|($WIKI_MULTIPLE_REGEX)|($STYLE_REGEX)|($OPENSEARCH_REGEX)" \
	$NON_SPECIAL > $OTHER

#########

# 81% of other == 16% of dynamic
GEN=$OTHER.gen
# 20% of other == 4% of dynamic (safe to ignore)
NON_GEN=$OTHER.non_gen

GEN_REGEX='&gen=(js|css)'
echo $GEN
echo $NON_GEN
grep    -E "$GEN_REGEX" $OTHER > $GEN
grep -v -E "$GEN_REGEX" $OTHER > $NON_GEN

# 58% urls in NON_GEN have an action=param; the most popular actions are
# edit, query, raw, history, submit
NON_GEN_ACTIONS=$NON_GEN.actions
echo $NON_GEN_ACTIONS
grep -o "action=[^&]*" $NON_GEN | sort | uniq -c | sort -rn > $NON_GEN_ACTIONS
