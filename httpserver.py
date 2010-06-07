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
        return urlparse.parse_qs(urlparse.urlparse(self.environ['PATH_INFO']).query)

    def get_widget_instance(self):
        return self._melange.widgets[self.GET['instance']]


@bjoern.route(r'/thingy/(?P<file>.*)')
def thingy_files(env, response, file=None):
    path = os.path.join(response._melange.context.working_directory, 'data/thingy')
    return open(os.path.join(path, file))


@bjoern.route(r'/widget/(?P<file>.*)')
def widget_files(env, response, file=None):
    return open(os.path.join(response.get_widget_instance().get_skin_path(), file))


@bjoern.route(r'/common/(?P<file>.*)')
def common_files(env, response, file=None):
    try:
        widget_instance = response.get_widget_instance()
    except KeyError:
       theme = None
    else:
        theme = response._melange.widgets[instance].config.widget_theme
        if theme == 'use.the.fucking.global.settings.and.suck.my.Dick':
            theme = None

    if theme is None:
        theme = response._melange.config.default_theme

    path = os.path.dirname(response._melange.themes.get_by_id(theme)._path)
    return open(os.path.join(path, file))

@bjoern.route(r'/widget/tmp/(?P<file>.*)')
def tmp_files(env, response, file=None):
    path = response.get_widget_instance().get_tmp()
    return open(os.path.join(path, file))
