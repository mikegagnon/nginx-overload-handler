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
# ==== install.sh ====
#
# Based off of http://wiki.apache.org/solr/SolrTomcat
#

DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
source $DIR/env.sh
DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"

SOLR_WAR="$SOLR_HOME/solr.war"

cp $DIR/tomcat-users.xml $CATALINA_HOME/conf/tomcat-users.xml

$CATALINA_HOME/bin/catalina.sh run &
sleep 10
./kill_solr.sh

cp $SOLR_LOCAL_PATH/dist/apache-solr-*.war $SOLR_WAR

cat $DIR/solrconfig.xml.template \
    | sed "s@TEMPLATE_SOLR_DATA_DIR@$SOLR_DATA_DIR@g" \
    > $DIR/solrconfig.xml
cp $DIR/solrconfig.xml $SOLR_HOME/conf/solrconfig.xml

cat $DIR/solr.xml.template \
    | sed "s@TEMPLATE_SOLR_HOME@$SOLR_HOME@g" \
    | sed "s@TEMPLATE_SOLR_WAR@$SOLR_WAR@g" \
    > $DIR/solr.xml
cp $DIR/solr.xml $CATALINA_HOME/conf/Catalina/localhost/solr.xml

cat $DIR/server.xml.template \
    | sed "s@TEMPLATE_TOMCAT_PORT@9000@g" \
    > $DIR/server.xml
cp $DIR/server.xml $CATALINA_HOME/conf/server.xml

