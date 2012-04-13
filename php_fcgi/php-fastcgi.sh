#!/bin/bash

FASTCGI_USER=www-data
FASTCGI_GROUP=www-data
ADDRESS=127.0.0.1
PORT=9000
PIDFILE=/var/run/php-fastcgi/php-fastcgi.pid
CHILDREN=0
PHP5=/usr/bin/php5-cgi

exec /usr/bin/spawn-fcgi -n -a $ADDRESS -p $PORT -C $CHILDREN $PHP5
