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

import os
import sys
import imp

APIS = {}


def import_api_file(path, widget_id):

    api_file = os.path.join(path, '__init__.py')
    if os.path.isfile(api_file):
        sys.path.insert(0, path)
        with open(api_file) as file_handle:
            imp.load_module(
                widget_id,
                file_handle,
                api_file,
                ('.py', 'r', imp.PY_SOURCE)
            )


class API(object):

    def get_exposed_methods(self):
        methods = []
        for attr in dir(self):
            if hasattr(getattr(self, attr), '_exposed'):
                methods.append(attr)
        return methods


def expose(func):

    func._exposed = True
    return func


def register(widget_id):

    def wrapper(api_cls):
        APIS[widget_id] = api_cls
        return api_cls
    return wrapper
