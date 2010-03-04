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
gobject.threads_init()

import dbus.service

import gtk
import cairo

import math

import cream
import cream.meta
import cream.ipc
import cream.gui

from widget import Widget
from httpserver import HttpServer

EDIT_MODE_NONE = 0
EDIT_MODE_MOVE = 1

class Clone:

    def __init__(self, widget):

        self.widget = widget

        self.window = gtk.Window()
        self.window.set_keep_above(True)
        self.window.set_app_paintable(True)
        self.window.connect('expose-event', self.expose_cb)
        self.window.set_colormap(self.window.get_screen().get_rgba_colormap())
        self.window.show()

        self.widget.connect('expose-event', lambda source, event: self.window.window.invalidate_rect(event.area, True))


    def expose_cb(self, source, event):

        ctx = self.window.window.cairo_create()

        ctx.set_operator(cairo.OPERATOR_SOURCE)
        ctx.set_source_rgba(0, 0, 0, .8)
        ctx.paint()

        ctx.set_operator(cairo.OPERATOR_OVER)

        ctx.set_source_pixmap(self.widget.window, 0, 0)
        ctx.paint()


class WidgetWindow(gtk.Window):

    def __init__(self, widget):

        self.widget = widget
        self.widget.connect('remove', self.remove_cb)
        self.widget.connect('move', self.move_cb)
        self.widget.connect('resize', self.resize_cb)

        gtk.Window.__init__(self)

        # Setting up the Widget's window...
        self.stick()
        self.set_keep_below(True)
        self.set_type_hint(gtk.gdk.WINDOW_TYPE_HINT_DOCK)
        self.set_skip_pager_hint(True)
        self.set_skip_taskbar_hint(True)
        self.set_decorated(False)
        self.set_app_paintable(True)
        self.set_resizable(False)
        self.set_default_size(10, 10)
        self.connect('expose-event', self.expose_cb)
        self.set_colormap(self.get_screen().get_rgba_colormap())

        # Creating container for receiving events:
        self.bin = gtk.EventBox()
        self.bin.add(self.widget.view)

        self.add(self.bin)

        self.move(*self.widget.get_position())


    def expose_cb(self, source, event):
        """ Clear the widgets background. """

        ctx = source.window.cairo_create()

        ctx.set_operator(cairo.OPERATOR_SOURCE)
        ctx.set_source_rgba(0, 0, 0, 0)
        ctx.paint()


    def remove_cb(self, widget):

        self.destroy()


    def resize_cb(self, widget, width, height):

        self.set_size_request(width, height)
        self.resize(width, height)


    def move_cb(self, widget, x, y):

        self.move(x, y)


class Overlay:

    def __init__(self, foo):

        self.foo = foo

        self.window = gtk.Window()
        self.window.fullscreen()
        self.window.set_keep_above(True)
        self.window.set_app_paintable(True)
        self.window.connect('expose-event', self.expose_cb)
        self.window.set_colormap(self.window.get_screen().get_rgba_colormap())

        self.bin = cream.gui.CompositeBin()
        self.window.add(self.bin)

        self.window.show_all()

        gobject.timeout_add(2000, self.show)


    def show(self):

        for k, v in self.foo.widget_instances.iteritems():
            x, y = v.get_position()
            v.bin.remove(v.view)
            self.bin.add(v.view, x, y)


    def expose_cb(self, source, event):

        ctx = self.window.window.cairo_create()

        ctx.set_operator(cairo.OPERATOR_SOURCE)
        ctx.set_source_rgba(0, 0, 0, .8)
        ctx.paint()

        ctx.set_operator(cairo.OPERATOR_OVER)


class Melange(cream.Module, cream.ipc.Object):
    """ The main class of the Melange module. """

    def __init__(self):

        cream.Module.__init__(self)

        cream.ipc.Object.__init__(self,
            'org.cream.melange',
            '/org/cream/melange'
        )

        self.display = gtk.gdk.display_get_default()
        self._edit_mode = EDIT_MODE_NONE

        # Initialize the HTTP server providing the widget data.
        self.server = HttpServer(self)
        self.server.run()

        # Scan for widgets...
        self.widgets = cream.meta.MetaDataDB('widgets', type='melange.widget')
        self.widget_instances = {}

        # Load widgets stored in configuration.
        for widget in self.config.widgets:
            self.load_widget(**widget)


        #self.overlay = Overlay(self)


    @cream.ipc.method('svv', '')
    def load_widget(self, name, x=None, y=None):
        """
        Load a widget with the given name at the specified coordinates (optional).

        :param name: The name of the widget.
        :param x: The x-coordinate.
        :param y: The y-coordinate.

        :type name: `str`
        :type x: `int`
        :type y: `int`
        """

        x, y = int(x), int(y)

        self.messages.debug("Loading widget '%s'..." % name)

        widget = Widget(self.widgets.get_by_name(name))
        self.widget_instances[widget.instance] = widget

        widget.connect('remove', self.widget_remove_cb)
        widget.connect('reload', self.widget_reload_cb)

        widget.view.connect('button-press-event', self.button_press_cb, widget)
        widget.view.connect('button-release-event', self.button_release_cb, widget)

        widget.set_position(x, y)

        widget.show()

        window = WidgetWindow(widget)
        window.show_all()

        #widget.window.get_group().remove_window(widget.window)

        #c = Clone(widget.view)

        #if x is not None and y is not None:
        #    widget.set_position(x, y)


    @cream.ipc.method('', 'a{sa{ss}}')
    def list_widgets(self):
        """
        List all available widgets.

        :return: List of widgets.
        :rtype: `list`
        """

        return self.widgets.by_hash


    def quit(self):
        """ Quit the module. """

        self.config.widgets = self.widget_instances.values()
        cream.Module.quit(self)


    def widget_remove_cb(self, widget):
        """ Callback being called when a widget has been removed. """

        del self.widget_instances[widget.instance]


    def widget_reload_cb(self, widget):
        """ Callback function that is called when the user clicks on the "Reload" menu entry. """

        info_dict = widget.__xmlserialize__()
        self.messages.debug("Reloading widget '%(name)s'" % info_dict)
        widget.close()
        self.load_widget(**info_dict)


    def button_press_cb(self, source, event, widget):
        """ Handle clicking on the widget (e. g. by showing context menu). """

        if event.button == 2:
            self._edit_mode = EDIT_MODE_MOVE
            self.start_move(widget)
            return True


    def button_release_cb(self, source, event, widget):

        if event.button == 2:
            self._edit_mode = EDIT_MODE_NONE
            return True


    def start_move(self, widget):

        def move_cb(old_x, old_y):
            if self._edit_mode == EDIT_MODE_MOVE:
                new_x, new_y = self.display.get_pointer()[1:3]
                mov_x = new_x - old_x
                mov_y = new_y - old_y

                res_x = widget.get_position()[0] + mov_x
                res_y = widget.get_position()[1] + mov_y
                #widget.set_position(res_x, res_y)
                widget.set_position(res_x, res_y)

                width, height = widget.get_size()

                centers = {
                    'left': (res_x, res_y + height / 2),
                    'right': (res_x + width, res_y + height / 2),
                    'top': (res_x + width / 2, res_y),
                    'bottom': (res_x + width / 2, res_y + height)
                }

                for k, w in self.widget_instances.iteritems():
                    if not w == widget:
                        w_name = w.meta['name']
                        w_x, w_y = w.get_position()
                        w_width, w_height = w.get_size()

                        w_centers = {
                            'left': (w_x, w_y + w_height / 2),
                            'right': (w_x + w_width, w_y + w_height / 2),
                            'top': (w_x + w_width / 2, w_y),
                            'bottom': (w_x + w_width / 2, w_y + w_height)
                        }

                        w_distances = [
                            ('left', int(math.sqrt(abs(w_centers['left'][0] - centers['right'][0]) ** 2 + abs(w_centers['left'][1] - centers['right'][1]) ** 2))),
                            ('right', int(math.sqrt(abs(w_centers['right'][0] - centers['left'][0]) ** 2 + abs(w_centers['right'][1] - centers['left'][1]) ** 2))),
                            ('top', int(math.sqrt(abs(w_centers['top'][0] - centers['bottom'][0]) ** 2 + abs(w_centers['top'][1] - centers['bottom'][1]) ** 2))),
                            ('bottom', int(math.sqrt(abs(w_centers['bottom'][0] - centers['top'][0]) ** 2 + abs(w_centers['bottom'][1] - centers['top'][1]) ** 2)))
                        ]

                        w_distances.sort(key=lambda x:(x[1], x[0]))
                        #print w_name, w_distances[0]

                gobject.timeout_add(30, move_cb, new_x, new_y)

        move_cb(*self.display.get_pointer()[1:3])


if __name__ == '__main__':
    melange = Melange()
    melange.main()
