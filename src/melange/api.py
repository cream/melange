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



def in_main_thread(func):
    """ Decorator for functions that have to be called in the main thread. """

    def wrapper(*args, **kwargs):
        f = FunctionInMainThread(func)
        return f(*args, **kwargs)

    return wrapper


class API(object):

    @expose
    def log(self, msg):
        self.messages.info(msg)

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



class FunctionInMainThread(object):
    """ A wrapper for functions that have to be called in the main thread. """

    def __init__(self, func):

        self.func = func
        self.lock = threading.Event()
        self.ret = None


    def __call__(self, *args, **kwargs):

        self.lock.clear()
        gobject.timeout_add(0, self._func_wrapper, args, kwargs)
        self.lock.wait()
        return self.ret


    def _func_wrapper(self, args, kwargs):
        try:
            self.ret = self.func(*args, **kwargs)
        except Exception:
            import traceback
            traceback.print_exc()
        self.lock.set()
