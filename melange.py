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

import cream
import cream.ipc

import gtk.gdk
gtk.gdk.threads_init()

from widget import WidgetMetaData, Widget
from httpserver import HttpServer


class Melange(cream.Module):

    __ipc_domain__ = 'org.cream.melange'

    def __init__(self):

        cream.Module.__init__(self)

        wdgs = WidgetMetaData.scan('widgets', type='melange.widget')
        self.widgets = {}

        for w in wdgs:
            self.widgets[w['hash']] = w


    @cream.ipc.method('s', '')
    def load_widget(self, name):

        self.messages.debug("Loading widget '%s'..." % name)

        Widget(self.widgets[name]).show()


    @cream.ipc.method('', 'a{sa{ss}}')
    def list_widgets(self):

        return self.widgets


melange = Melange()
melange.main()
