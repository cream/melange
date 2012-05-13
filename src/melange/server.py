#! /usr/bin/env python
# -*- coding: utf-8 -*-

# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 2 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the Free Software
# Foundation, Inc., 51 Franklin Street, Fifth Floor, Boston,
# MA 02110-1301, USA.

import re
import os
import json
import urlparse
import threading

import tornado.web
import tornado.ioloop
import tornado.websocket
import tornado.httpserver


from melange.common import HTTP_HOST, HTTP_PORT


def parse_request(pattern, uri):

    result = urlparse.urlparse(uri)
    match = pattern.match(result.path)

    return match.groupdict()['file'], urlparse.parse_qs(result.query)


class WidgetHandler(tornado.web.RequestHandler):
    route = re.compile(r'/widget/(?P<file>.*)')

    def initialize(self, widgets):
        self.widgets = widgets

    def get(self):

        file_, query = parse_request(self.route, self.request.uri)
        widget = self.widgets.get_widget(query['id'][0])

        path = widget.selected_skin.path
        with open(os.path.join(path, file_), 'r') as file_handle:
            self.write(file_handle.read())

class ThemeHandler(tornado.web.RequestHandler):
    route = re.compile(r'/theme/(?P<file>.*)')

    def initialize(self, widgets):
        self.widgets = widgets

    def get(self):

        file_, query = parse_request(self.route, self.request.uri)
        widget = self.widgets.get_widget(query['id'][0])

        path = widget.selected_theme.path
        with open(os.path.join(path, file_), 'r') as file_handle:
            self.write(file_handle.read())

class CommonHandler(tornado.web.RequestHandler):
    route = re.compile(r'/common/(?P<file>.*)')

    def initialize(self, common_path):
        self.common_path = common_path

    def get(self):

        file_, qs = parse_request(self.route, self.request.uri)

        with open(os.path.join(self.common_path, file_), 'r') as file_handle:
            self.write(file_handle.read())


class WSHandler(tornado.websocket.WebSocketHandler):

    def initialize(self, widgets):
        self.widgets = widgets


    def send(self, message):
        """Send the message to the client. """

        self.write_message(json.dumps(message))

    def open(self):

    	widget_id = self.request.uri.replace('/ws/', '')
    	self.widgets.get_widget(widget_id).on_websocket_connected(self)


    def on_message(self, message):

    	message = json.loads(message)

    	widget = self.widgets.get_widget(message['id'])
    	if message['type'] == 'init':
    	    widget.on_websocket_init()
    	elif message['type'] == 'call':
    	    widget.on_api_method_called(message['method'],
    	       message['callback_id'],
    	       message['arguments']
    	   )



class DummyHandler(tornado.web.RequestHandler):

    def get(self):
        pass


class Server(threading.Thread):

    def __init__(self, widgets, common_path):

        threading.Thread.__init__(self)
        application = tornado.web.Application([
            (r'/widget/.*', WidgetHandler, {'widgets': widgets}),
            (r'/theme/.*', ThemeHandler, {'widgets': widgets}),
            (r'/common/.*', CommonHandler, {'common_path': common_path}),
            (r'/ws/.*', WSHandler, {'widgets': widgets}),
            (r'/favicon.ico.*', DummyHandler)
        ])

        self.server = tornado.httpserver.HTTPServer(application)


    def run(self):
        self.server.listen(HTTP_PORT)
        tornado.ioloop.IOLoop.instance().start()

    def stop(self):
        tornado.ioloop.IOLoop.instance().stop()
