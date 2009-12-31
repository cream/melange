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

        self.config.active_profile = self.config.profiles[1]
        # TODO: weg damit

        for k, v in self.config.widgets.iteritems():
            self.load_widget(v['name'], v['x'], v['y'])
            w = self.config.widgets # TODO: *kotz*:D
            del w[k]
            self.config.widgets = w
            self.config.save()


    def widget_position_changed(self, widget, x, y):

        self.config.widgets[widget.instance]['x'] = x
        self.config.widgets[widget.instance]['y'] = y
        self.config.save()


    def widget_removed(self, widget):

        w = self.config.widgets # TODO: *kotz*:D
        del w[widget.instance]
        self.config.widgets = w
        self.config.save()


    @cream.ipc.method('svv', '')
    def load_widget(self, name, x=None, y=None):

        self.messages.debug("Loading widget '%s'..." % name)

        w = Widget(self.widgets.get_by_name(name))
        self.widget_instances[w.instance] = w

        w.connect('position-changed', self.widget_position_changed)
        w.connect('removed', self.widget_removed)

        self.config.widgets = dict(self.config.widgets, **{w.instance : { # TODO: *omg*
            'name': w.meta['name'],
            'x': int(x),
            'y': int(y)
            }})
        self.config.save()

        w.show()

        if x and y:
            w.set_position(x, y)


    @cream.ipc.method('', 'a{sa{ss}}')
    def list_widgets(self):

        return self.widgets.by_hash


if __name__ == '__main__':
    melange = Melange()
    melange.main()
