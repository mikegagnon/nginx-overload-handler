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

==== README.txt for trainer ====

For a given web app, the trainer tests nginx-overload-handler under various
configurations and reports on the security guarantees that can be obtained
from the tested configurations. The only variable that the trainer experiments
with is I, the inter-arrival time between admitted requests.

==== Running a trial ====

A trial trial consists of one run of httperf. Parts:
    (1) Setup trial
        (a) ./maketrace.sh "http://MediaWikiInstance" 1000 > legit_trace.txt
        (b) ./make_trial_trace.py 4 25 legit_trace.txt attack_trace.txt > trial_trace.txt
    (2) Execute trial
        (a) restart the web application to an idle state
        (c) httperf
        (d) analyze output

httperf --hog --server=172.16.206.129 --wsesslog=4,1,foo.txt --period=0.25 --print-reply=header --print-request=header
