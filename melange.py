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

import random
import hashlib

import cream
import cream.ipc

import gtk.gdk
gtk.gdk.threads_init()

from widget import WidgetMetaData, Widget
from httpserver import HttpServer

W = [
    {
    'hash': '81c24aa464e36cd5a84e0a648deb24fd6024b2097499299caa9c113fd96ba045',
    'x': 600,
    'y': 50
    }
]

class Melange(cream.Module):

    __ipc_domain__ = 'org.cream.melange'

    def __init__(self):

        cream.Module.__init__(self)

        self.server = HttpServer(self)
        self.server.run()

        wdgs = WidgetMetaData.scan('widgets', type='melange.widget')
        self.widgets = {}
        self.widget_instances = {}

        for w in wdgs:
            self.widgets[w['hash']] = w

        for w in W:
            self.load_widget(w['hash'], w['x'], w['y'])


    @cream.ipc.method('svv', '')
    def load_widget(self, name, x=None, y=None):

        self.messages.debug("Loading widget '%s'..." % name)

        w = Widget(self.widgets[name])
        self.widget_instances[w.instance] = w

        w.show()

        if x and y:
            w.set_position(x, y)


    @cream.ipc.method('', 'a{sa{ss}}')
    def list_widgets(self):

        return self.widgets


if __name__ == '__main__':
    melange = Melange()
    melange.main()
