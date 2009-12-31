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

from widget import Widget
from httpserver import HttpServer

class Melange(cream.Module):

    __ipc_domain__ = 'org.cream.melange'

    def __init__(self):

        cream.Module.__init__(self)

        self.server = HttpServer(self)
        self.server.run()

        self.widgets = cream.MetaDataDB('widgets', type='melange.widget')
        self.widget_instances = {}

        print self.config.widgets


    def _update_widget_position(self):
        pass


    @cream.ipc.method('svv', '')
    def load_widget(self, name, x=None, y=None):

        self.messages.debug("Loading widget '%s'..." % name)

        w = Widget(self.widgets.get_by_name(name))
        self.widget_instances[w.instance] = w

        self.config.widgets.append({
            'name': w.meta['name'],
            'x': 0,
            'y': 0
            })
        print self.config.widgets

        w.show()

        if x and y:
            w.set_position(x, y)


    @cream.ipc.method('', 'a{sa{ss}}')
    def list_widgets(self):

        return self.widgets.by_hash


if __name__ == '__main__':
    melange = Melange()
    melange.main()
