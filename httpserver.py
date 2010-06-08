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
import urlparse
import bjoern
from bjoern import run
from cream.util import cached_property

# no file support in bjoern yet
_open = open
def open(*a, **k):
    return _open(*a, **k).read()

class MelangeResponse(bjoern.Response):
    response_headers = ()
    response_status = '200 Alles super'

    @cached_property
    def GET(self):
        return dict((header_name, header_values[0]) for header_name, header_values in
                    urlparse.parse_qs(self.environ['QUERY_STRING']).iteritems())


def route(url_regex):
    def decorator(func):
        if not hasattr(func, '__bjoern_routes__'):
            func.__bjoern_routes__ = list()
        func.__bjoern_routes__.append(url_regex)
        return func
    return decorator


class HttpServer(object):
    def __init__(self, melange):
        self._melange = melange
        self._setup_routes()

    def _setup_routes(self):
        for name, attr in ((name, getattr(self, name)) for name in dir(self)):
            if hasattr(attr, '__bjoern_routes__'):
                for route in attr.__bjoern_routes__:
                    bjoern.route(route)(attr)

    def run(self, host, port):
        bjoern.run(host, port, MelangeResponse)

    def _get_widget_theme(self, request):
        widget_id = request.GET.get('instance')
        if widget_id:
            return self._melange.widgets[widget_id].get_current_theme()
        else:
            return self._melange.themes.get_by_id(self._melange.config.default_theme)


    @route(r'/thingy/(?P<file>.*)')
    def thingy_files(self, env, request, file):
        path = os.path.join(self._melange.context.working_directory, 'data/thingy')
        return open(os.path.join(path, file))

    @route(r'/widget/(?P<file>.*)')
    def widget_files(self, env, request, file):
        return open(os.path.join(self._melange.widgets[request.GET['instance']].get_skin_path(), file))

    @route(r'/common/(?P<file>.*)')
    def common_files(self, env, request, file):
        widget_theme = self._get_widget_theme(request)
        return open(os.path.join(widget_theme['path'], file))

    @route(r'/widget/tmp/(?P<file>.*)')
    def tmp_files(self, env, request, file):
        path = self._melange.widgets[request.GET['instance']].get_tmp()
        return open(os.path.join(path, file))

    @route(r'/chrome/(?P<file>.*)')
    def chrome_files(self, env, request, file):
        widget_theme = self._get_widget_theme(request)
        return open(os.path.join(widget_theme['path'], file))
