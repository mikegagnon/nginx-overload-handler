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
# ==== install_dependencies.sh for redmine_app ====
#
# USAGE: sudo ./install_dependencies.sh
#

DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
# For $GEM_HOME and $RUBY_LIB
source $DIR/../../dependencies/env.sh
DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
source $DIR/env.sh
DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"

gem install bundler -v '1.1.3'
gem install mysql -v '2.8.1'

# "Make sure to install the C bindings for Ruby that dramatically
# improve performance. You can get them by running gem install mysql2"
# -- http://www.redmine.org/projects/redmine/wiki/RedmineInstall
gem install mysql2
gem install mongrel
