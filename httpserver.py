#! /usr/bin/env python
# -*- coding: utf-8 -*-

# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 2 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the Free Software
# Foundation, Inc., 51 Franklin Street, Fifth Floor, Boston,
# MA 02110-1301, USA.

import os
import sys
import urlparse
from bjoern import run
from cream.util import cached_property

def route(url_regex):
    def decorator(func):
        if not hasattr(func, '__bjoern_routes__'):
            func.__bjoern_routes__ = list()
        func.__bjoern_routes__.append(url_regex)
        return func
    return decorator

def query_string_to_dict(query_string):
    return dict((header_name, header_values[0]) for header_name, header_values in
                urlparse.parse_qs(query_string).iteritems())

class SmallWebFramework(object):
    def __init__(self):
        self.routed_methods = self._get_routed()

    def _get_routed(self):
        routed = []
        for attr in dir(self):
            func = getattr(self, attr)
            if hasattr(func, '__bjoern__routes__'):
                routed.append(func)
        return routed

    def run(self, host, port):
        run(self, host, port)

    def __call__(self, environ, start_response):
        """ The WSGI application called by bjoern """
        GET = query_string_to_dict(environ.get('QUERY_STRING', ''))
        func, kwargs = self.dispatch(environ)
        if func is None:
            start_response('404 Not Found', [('Content-Length', '13')])
            return 'Not Found'
        try:
            response = func(GET, **kwargs)
        except:
            start_response('500 Python Error :(', [('Content-Length', '21')], sys.exc_info())
            return 'Internal Server Error'
        else:
            if isinstance(response, file):
                headers = [('Content-Length', str(os.path.getsize(file.name)))]
            else:
                headers = []
            start_response('200 Alles in Butter', headers)
            return response

    def dispatch(self, environ):
        path = environ.get('PATH_INFO', '')
        for func in self.routed:
            for route in func.__bjoern_routes__:
                match = route.match(path)
                if match is not None:
                    return func, match.groupdict()
        return None, None


class HttpServer(SmallWebFramework):
    def __init__(self, melange):
        SmallWebFramework.__init__(self)
        self._melange = melange

    def _get_widget_theme(self, GET):
        widget_id = GET.get('instance')
        if widget_id:
            return self._melange.widgets[widget_id].get_current_theme()
        else:
            return self._melange.themes.get_by_id(self._melange.config.default_theme)

    @route(r'/thingy/(?P<file>.*)')
    def thingy_files(self, GET, file):
        path = os.path.join(self._melange.context.working_directory, 'data/thingy')
        return open(os.path.join(path, file))

    @route(r'/widget/(?P<file>.*)')
    def widget_files(self, GET, file):
        return open(os.path.join(self._melange.widgets[GET['instance']].get_skin_path(), file))

    @route(r'/common/(?P<file>.*)')
    def common_files(self, GET, file):
        widget_theme = self._get_widget_theme(GET)
        return open(os.path.join(widget_theme['path'], file))

    @route(r'/widget/tmp/(?P<file>.*)')
    def tmp_files(self, GET, file):
        path = self._melange.widgets[GET['instance']].get_tmp()
        return open(os.path.join(path, file))

    @route(r'/chrome/(?P<file>.*)')
    def chrome_files(self, GET, file):
        widget_theme = self._get_widget_theme(GET)
        return open(os.path.join(widget_theme['path'], 'chrome', file))
