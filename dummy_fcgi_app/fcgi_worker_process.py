#!/usr/bin/env python
#
# A simple fastcgi worker for testing purposes
#
# Spawn: ./fcgi_worker_process.py [port_num]
#   where port_num is the port number the worker should listen on
#
# Two forms of web access:
#   (1) no parameters, i.e.:
#       curl -s http://localhost/test.py
#   (2) one sleep parameterl; i.e. url?sleep=5
#       which will cause the worker to sleep for 5 sec before responding. i.e.:
#       curl -s http://localhost/test.py?sleep=5
#

from cgi import parse_qs, escape
import sys, os
import time

dirname = os.path.dirname(os.path.realpath(__file__))
sys.path.append(os.path.join(dirname, "..", "flup-1.0.2"))

from flup.server.fcgi_fork import WSGIServer


def app(environ, start_response):
    try:
        start_response('200 OK', [('Content-Type', 'text/html')])
        response = []

        parameters = parse_qs(environ.get('QUERY_STRING', ''))
        if "sleep" in parameters:
            sec = float(escape(parameters['sleep'][0]))
            time.sleep(sec)
            response.append("Slept for %f sec. \n" % sec)
        response.append('Oh hai! \n')
        return response
    except Exception as e:
        print "Unexpected error:", sys.exc_info()[0]
        print e
        raise

WSGIServer(app, bindAddress=("127.0.0.1", int(sys.argv[1])), maxSpare=1, maxChildren=1).run()
