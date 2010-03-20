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

import gobject
import gtk
import cairo

class MelangeThingy(gobject.GObject):

    __gtype_name__ = 'MelangeThingy'
    __gsignals__ = {
        'toggle-overlay': (gobject.SIGNAL_RUN_LAST, gobject.TYPE_NONE, ()),
        'show-settings': (gobject.SIGNAL_RUN_LAST, gobject.TYPE_NONE, ())
        }

    def __init__(self):

        gobject.GObject.__init__(self)

        self.window = gtk.Window()
        self.window.stick()
        self.window.set_keep_below(True)
        self.window.set_type_hint(gtk.gdk.WINDOW_TYPE_HINT_DOCK)
        self.window.set_skip_pager_hint(True)
        self.window.set_skip_taskbar_hint(True)
        self.window.set_decorated(False)
        self.window.set_app_paintable(True)
        self.window.set_resizable(False)
        self.window.set_events(self.window.get_events() | gtk.gdk.BUTTON_RELEASE_MASK)
        self.window.connect('expose-event', self.expose_cb)
        self.window.connect('button-release-event', self.click_cb)

        self.screen = self.window.get_screen()
        self.window.set_colormap(self.screen.get_rgba_colormap())

        self.window.show()
        self.window.set_size_request(50, 50)

        self.window.move(self.screen.get_width() - 50, 0)

        self.pixbuf = gtk.gdk.pixbuf_new_from_file('thingy.png')

        # Building context menu:
        item_settings = gtk.ImageMenuItem(gtk.STOCK_PREFERENCES)
        item_settings.connect('activate', lambda *x: self.emit('show-settings'))

        self.menu = gtk.Menu()
        self.menu.append(item_settings)
        self.menu.show_all()


    def click_cb(self, source, event):

        if event.button == 1:
            self.emit('toggle-overlay')
        elif event.button == 3:
            self.menu.popup(None, None, None, event.button, event.get_time())


    def expose_cb(self, source, event):
        """ Clear the widgets background. """

        ctx = source.window.cairo_create()

        ctx.set_operator(cairo.OPERATOR_SOURCE)
        ctx.set_source_rgba(0, 0, 0, 0)
        ctx.paint()
        ctx.set_source_pixbuf(self.pixbuf, 0, 0)
        ctx.paint()
