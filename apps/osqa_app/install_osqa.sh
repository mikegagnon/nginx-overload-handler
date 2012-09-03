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
# ==== install_osqa.sh for osqa ====
#
# USAGE: sudo ./install_osqa.sh
#

DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
source $DIR/env.sh
DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
source $DIR/../../dependencies/env.sh
DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"

$DIR/../../dependencies/django_vuln/install.sh
$DIR/../../dependencies/django_vuln/patch.sh

mkdir -p $INSTALL_OSQA_PATH
cp -r $OSQA_LOCAL_PATH/* $INSTALL_OSQA_PATH

cp $DIR/settings_local.py $INSTALL_OSQA_PATH/settings_local.py
cp $DIR/urls.py $INSTALL_OSQA_PATH/forum/urls.py

echo "CREATE DATABASE osqa DEFAULT CHARACTER SET UTF8 COLLATE utf8_general_ci;" > /tmp/query
mysql -u"$MYSQL_USER" -p"$MYSQL_PASSWORD" < /tmp/query
rm /tmp/query

# BUG FIX
cat $INSTALL_OSQA_PATH/forum/utils/html.py | sed s'/from django.template import mark_safe/from django.utils.safestring import mark_safe/g' > /tmp/html.py
mv /tmp/html.py $INSTALL_OSQA_PATH/forum/utils/html.py

chmod -R g+w $INSTALL_OSQA_PATH/forum/upfiles $INSTALL_OSQA_PATH/log

cd $INSTALL_OSQA_PATH
python manage.py syncdb --all --noinput
python manage.py migrate forum --fake

chown -R $FCGI_USER:$FCGI_USER $INSTALL_OSQA_PATH

# enable gunicorn in this app
echo "INSTALLED_APPS.append('gunicorn')" >> $INSTALL_OSQA_PATH/settings.py
