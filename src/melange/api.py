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
import threading

from gi.repository import GObject as gobject


APIS = {}


def import_api_file(path, widget_id):

    api_file = os.path.join(path, '__init__.py')
    if os.path.isfile(api_file):
        sys.path.insert(0, path)
        with open(api_file) as file_handle:
            imp.load_module(
                'widget_api',
                file_handle,
                api_file,
                ('.py', 'r', imp.PY_SOURCE)
            )
    else:
        APIS[widget_id] = API


def expose(func):
    func._exposed = True
    return func


def register(widget_id):

    def wrapper(api_cls):
        APIS[widget_id] = api_cls
        return api_cls
    return wrapper


class API(object):

    @expose
    def log(self, msg):
        print msg # XXX use cream.Messages

    def get_exposed_methods(self):
        methods = []
        for attr in dir(self):
            if hasattr(getattr(self, attr), '_exposed'):
                methods.append(attr)
        return methods



class Thread(threading.Thread, gobject.GObject):
    """An advanced threading class emitting a GObject signal after running."""

    __gtype_name__ = 'MelangeThread'
    __gsignals__ = {
        'finished': (gobject.SignalFlags.RUN_LAST, None, (str, object))
    }

    def __init__(self, func, callback_id, args=None):

        self.func = func
        self.callback_id = callback_id
        self.args = args if args is not None else []

        threading.Thread.__init__(self)
        gobject.GObject.__init__(self)


    def run(self):

        ret = self.func(*self.args)
        gobject.timeout_add(0, self._emit, ret)


    def _emit(self, ret):
        self.emit('finished', self.callback_id, ret)
