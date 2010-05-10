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

class Background(gobject.GObject):

    __gtype_name__ = 'Background'
    __gsignals__ = {
        'close': (gobject.SIGNAL_RUN_LAST, gobject.TYPE_NONE, ())
        }

    def __init__(self):

        gobject.GObject.__init__(self)

        self.window = gtk.Window()
        self.window.set_type_hint(gtk.gdk.WINDOW_TYPE_HINT_DOCK)
        self.window.fullscreen()
        self.window.stick()
        self.window.set_keep_below(True)
        self.window.set_decorated(False)
        self.window.set_app_paintable(True)
        self.window.set_skip_pager_hint(True)
        self.window.set_skip_taskbar_hint(True)
        self.window.connect('expose-event', self.expose_cb)

        self.window.set_property('accept-focus', False)

        self.window.move(0, 0)

        self.screen = self.window.get_screen()
        self.root_window = gtk.gdk.get_default_root_window()
        self.window.resize(self.screen.get_width(), self.screen.get_height())
        self.window.set_colormap(self.screen.get_rgba_colormap())


    def expose_cb(self, source, event):

        self.draw()


    def draw(self):

        workarea = self.root_window.property_get('_NET_WORKAREA')
        if workarea:
            workarea = workarea[-1]
        else:
            workarea = (0, 0, self.screen.get_width(), self.screen.get_height())

        ctx = self.window.window.cairo_create()

        ctx.set_operator(cairo.OPERATOR_SOURCE)
        ctx.set_source_rgba(0, 0, 0, .7)
        ctx.paint()

        ctx.rectangle(workarea[0] - 1, workarea[1] - 1, workarea[2] + 2, workarea[3] + 2)

        ctx.set_source_rgba(0, 0, 0, .5)
        ctx.fill_preserve()

        ctx.set_line_width(1)
        ctx.set_source_rgba(1, 1, 1, .5)
        ctx.stroke()


    def initialize(self):
        """ Initialize the background window. """

        self.window.set_opacity(0)
        self.window.show_all()
        self.window.window.input_shape_combine_region(gtk.gdk.Region(), 0, 0)


    def show(self):
        """ Show the background window. """

        def update(source, state):
            self.window.set_opacity(state)

        t = cream.gui.Timeline(600, cream.gui.CURVE_SINE)
        t.connect('update', update)
        t.run()

        self.draw()

        region = gtk.gdk.Region()
        region.union_with_rect((0, 0, self.screen.get_width(), self.screen.get_height()))
        self.window.window.input_shape_combine_region(region, 0, 0)


    def hide(self):
        """ Hide the background window. """

        def update(source, state):
            self.window.set_opacity(1 - state)

        t = cream.gui.Timeline(600, cream.gui.CURVE_SINE)
        t.connect('update', update)
        t.run()

        self.window.window.input_shape_combine_region(gtk.gdk.Region(), 0, 0)


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
        self.set_property('accept-focus', False)
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
        self.control_window.set_title('aa')
        self.control_window.set_size_request(70, 35)

        self.screen = self.control_window.get_screen()
        self.control_window.move(self.screen.get_width() - 70 - 40, -35)

        self.control_window.load('http://{0}:{1}/thingy/control.html'.format(HOST, PORT))
        self.control_window.show_all()

        self.control_window.js_context.show_settings = self.show_settings
        self.control_window.js_context.show_add_widgets = self.show_add_widgets

        if self.thingy_window.get_position()[1] != 0:
            self.thingy_window.window.set_override_redirect(True)
        if self.control_window.get_position()[1] != -35:
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
