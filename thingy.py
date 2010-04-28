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
import webkit
import javascriptcore as jscore
import cream.gui
from httpserver import HOST, PORT

class ThingyWindow(gtk.Window):

    def __init__(self):

        gtk.Window.__init__(self)

        self.stick()
        self.set_type_hint(gtk.gdk.WINDOW_TYPE_HINT_DOCK)
        self.set_keep_below(True)
        self.set_skip_pager_hint(True)
        self.set_skip_taskbar_hint(True)
        self.set_decorated(False)
        self.set_app_paintable(True)
        self.set_resizable(False)
        self.connect('expose-event', self.expose_cb)

        self.screen = self.get_screen()
        self.set_colormap(self.screen.get_rgba_colormap())

        self.view = webkit.WebView()
        self.view.set_transparent(True)

        self.js_context = jscore.JSContext(self.view.get_main_frame().get_global_context()).globalObject

        self.add(self.view)


    def load(self, uri):
        self.view.open(uri)


    def expose_cb(self, source, event):
        """ Clear the widgets background. """

        ctx = source.window.cairo_create()

        ctx.set_operator(cairo.OPERATOR_SOURCE)
        ctx.set_source_rgba(0, 0, 0, 0)
        ctx.paint()


class Thingy(gobject.GObject):

    __gtype_name__ = 'MelangeThingy'
    __gsignals__ = {
        'toggle-overlay': (gobject.SIGNAL_RUN_LAST, gobject.TYPE_NONE, ()),
        'show-settings': (gobject.SIGNAL_RUN_LAST, gobject.TYPE_NONE, ()),
        'show-add-widgets': (gobject.SIGNAL_RUN_LAST, gobject.TYPE_NONE, ())
        }

    def __init__(self):

        gobject.GObject.__init__(self)

        self.thingy_window = ThingyWindow()
        self.thingy_window.set_size_request(35, 35)

        self.screen = self.thingy_window.get_screen()
        self.thingy_window.move(self.screen.get_width() - 35, 0)

        self.thingy_window.load('http://{0}:{1}/thingy/thingy.html'.format(HOST, PORT))
        self.thingy_window.show_all()

        self.thingy_window.js_context.toggle_overlay = self.toggle_overlay


        self.control_window = ThingyWindow()
        self.control_window.set_size_request(70, 35)

        self.screen = self.control_window.get_screen()
        self.control_window.move(self.screen.get_width() - 70 - 40, -35)

        self.control_window.load('http://{0}:{1}/thingy/control.html'.format(HOST, PORT))
        self.control_window.show_all()

        self.control_window.js_context.show_settings = self.show_settings
        self.control_window.js_context.show_add_widgets = self.show_add_widgets


        self.thingy_window.window.set_override_redirect(True)
        self.control_window.window.set_override_redirect(True)


    def toggle_overlay(self):
        self.emit('toggle-overlay')


    def show_settings(self):
        self.emit('show-settings')


    def show_add_widgets(self):
        self.emit('show-add-widgets')


    def slide_in(self):

        def update(source, state):
            self.control_window.move(self.screen.get_width() - 70 - 40, -35 + state*35)

        t = cream.gui.Timeline(600, cream.gui.CURVE_SINE)
        t.connect('update', update)
        t.run()


    def slide_out(self):

        def update(source, state):
            self.control_window.move(self.screen.get_width() - 70 - 40, -state*35)

        t = cream.gui.Timeline(600, cream.gui.CURVE_SINE)
        t.connect('update', update)
        t.run()
