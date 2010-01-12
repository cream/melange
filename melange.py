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
import cream.meta
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

        self.widgets = cream.meta.MetaDataDB('widgets', type='melange.widget')
        self.widget_instances = {}

        for widget in self.config.widgets:
            self.load_widget(**widget)

    def quit(self):
        # Okay, we're going to perish right now, quickly save the current
        # configuration and then let happen what can't be inhibited.
        self.config.widgets = self.widget_instances.values()
        cream.Module.quit(self)


    def widget_position_changed(self, widget, x, y):
        pass

    def widget_removed(self, widget):
        del self.widget_instances[widget.instance]


    @cream.ipc.method('svv', '')
    def load_widget(self, name, x=None, y=None):
        x, y = int(x), int(y)

        self.messages.debug("Loading widget '%s'..." % name)

        w = Widget(self.widgets.get_by_name(name))
        self.widget_instances[w.instance] = w

        w.connect('position-changed', self.widget_position_changed)
        w.connect('removed', self.widget_removed)

        w.show()

        if x is not None and y is not None:
            w.set_position(x, y)


    @cream.ipc.method('', 'a{sa{ss}}')
    def list_widgets(self):
        return self.widgets.by_hash


if __name__ == '__main__':
    melange = Melange()
    melange.main()
