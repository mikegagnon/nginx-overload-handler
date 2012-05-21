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
# FOR USAGE: ./maketrace.py --help
#
# PREREQ: run get_pages.py first to get a list of MediaWiki pages (saved in pages.json)
#
# Creates several trace files for cross-validation training of Beer Garden. Gets a list
# of MediaWiki pages from pages.json, partitions these pages into non-overlapping subsets.
# From there, generates a random trace of URL accesses for each partition.
#
# What's the point? Cross validation of Beer Garden.
#   - Train Beer Garden on one partition
#   - Test Beer Garden on the other partitions
#
# NOTE: Cross validation would be even better if we trained on one type of page (say list
# of Beers) and tested on a other type of page (say Hawaiian Beaches). But this version
# doesn't support that feature.
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

    def part(self, items):
        part = {}
        for i in range(0, self.partitions):
            part[i] = []

        for i, item in enumerate(items):
            part[i % self.partitions].append(item)
        return part

    def __init__(self, pages_file, diff, num_urls, partitions, filename, logger):
        with open(pages_file, 'r') as f:
            self.pages = json.load(f)
        self.diff = diff
        self.num_urls = num_urls
        self.partitions = partitions
        self.filename = filename
        self.logger = logger

        # create more convenient data structures based off pages
        view_pages = [entry["view"] for _, entry in self.pages.items()]
        diff_pages = [entry["diff"] for _, entry in self.pages.items() if len(entry["diff"])]

        random.shuffle(view_pages)
        random.shuffle(diff_pages)

        self.view_pages = self.part(view_pages)
        self.diff_pages = self.part(diff_pages)

    def make(self):
        for i in range(0, self.partitions):
            view_pages = self.view_pages[i]
            diff_pages = self.diff_pages[i]
            filename = self.filename % i
            self.logger.info("Created %s", filename)
            with open(filename, "w") as f:
                for url_i in range(0, self.num_urls):
                    if random.random() <= self.diff:
                        page_list = random.choice(diff_pages)
                        url = random.choice(page_list)
                    else:
                        url = random.choice(view_pages)

                    f.write("%s\n\n" % url)


if __name__ == "__main__":
    cwd = os.getcwd()

    default_pages_filename = os.path.join(cwd, "pages.json")
    default_output_filename = os.path.join(cwd, "legit_trace_%d.txt")

    parser = argparse.ArgumentParser(description='Creates trace files for cross-validation training of Beer Garden. " \
        "Outputs several files with filename template given by OUTPUT_FILENAME (default = %s).' % default_output_filename)
    parser.add_argument("-p", "--pages", type=str, default=default_pages_filename,
                    help="Default=%(default)s. The JSON file containing output from get_pages.py")
    parser.add_argument("-d", "--diff", type=float, default=0.0,
                    help="Default=%(default)f. The proportion of URL accesses that should be diffs")
    parser.add_argument("-n", "--num-urls", type=int, default=100,
                    help="Default=%(default)d. The number of URLs to generate")
    parser.add_argument("-r", "--partitions", type=int, default=2,
                    help="Default=%(default)d. The number of ways to partitions to produce for cross validation.")
    parser.add_argument("-o", "--output_filename", type=str, default=default_output_filename,
                    help="Default=%(default)s. The filename template for output files (must contain %%d).")

    log.add_arguments(parser)
    args = parser.parse_args()
    logger = log.getLogger(args)
    logger.info("Command line arguments: %s" % str(args))

    args.output_filename = os.path.realpath(args.output_filename)
    try:
        test_filename = args.output_filename % 1
    except TypeError:
        logger.critical("output filename must contain exactly one %d")
        sys.exit(1)

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
        args.partitions, \
        args.output_filename, \
        logger)

    mkTrace.make()

