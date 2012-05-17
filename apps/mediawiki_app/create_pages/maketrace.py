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
# ==== maketrace.py ====
#
# Prints a list of URLs, which represents a stream of "legitimate" URL
# acccesses for MediaWiki.
#
# FOR USAGE: ./maketrace.py --help
#

import os
import sys
import json
import random
import argparse

DIRNAME = os.path.dirname(os.path.realpath(__file__))
sys.path.append(os.path.join(DIRNAME, '..', '..', '..', 'common'))

import log

class MakeTrace:

    def __init__(self, pages_file, diff, num_urls, logger):
        with open(pages_file, 'r') as f:
            self.pages = json.load(f)
        self.diff = diff
        self.num_urls = num_urls
        self.logger = logger

        # create more convenient data structures based off pages
        self.view_pages = [entry["view"] for _, entry in self.pages.items()]
        self.diff_pages = [entry["diff"] for _, entry in self.pages.items() if len(entry["diff"])]

    def make(self):
        for url_i in range(0, self.num_urls):
            if random.random() <= self.diff:
                page_list = random.choice(self.diff_pages)
                url = random.choice(page_list)
            else:
                url = random.choice(self.view_pages)

            print url
            print


if __name__ == "__main__":
    cwd = os.getcwd()

    default_pages_filename = os.path.join(cwd, "pages.json")

    parser = argparse.ArgumentParser(description='Trains Beer Garden. See source for more info.')
    parser.add_argument("-p", "--pages", type=str, default=default_pages_filename,
                    help="Default=%(default)s. The JSON file containing output from get_pages.py")
    parser.add_argument("-d", "--diff", type=float, default=0.0,
                    help="Default=%(default)f. The proportion of URL accesses that should be diffs")
    parser.add_argument("-n", "--num-urls", type=int, default=100,
                    help="Default=%(default)d. The number of URLs to generate")

    log.add_arguments(parser)
    args = parser.parse_args()
    logger = log.getLogger(args)
    logger.info("Command line arguments: %s" % str(args))

    try:
        with open(args.pages, "r") as f:
            pass
    except:
        logger.critical("Error: could not open pages file (%s)" % args.pages)
        sys.exit(1)

    mkTrace = MakeTrace( \
        args.pages, \
        args.diff, \
        args.num_urls, \
        logger)

    mkTrace.make()
