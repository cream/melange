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

import gtk
import cairo

import time
import math

import cream
import cream.meta
import cream.ipc
import cream.gui
import cream.util

from widget import Widget
from thingy import MelangeThingy
from httpserver import HttpServer

EDIT_MODE_NONE = 0
EDIT_MODE_MOVE = 1
MOUSE_BUTTON_MIDDLE = 2

OVERLAY = False

import ctypes

cgdk = ctypes.CDLL("libgdk-x11-2.0.so")

class GdkCursor(ctypes.Structure):
        _fields_ = [('type', ctypes.c_int)]


def gdk_window_get_cursor(window):

    cr = cgdk.gdk_window_get_cursor(hash(window))
    if cr == 0:
        return None
    else:
        return GdkCursor.from_address(cr)


class Clone(gtk.DrawingArea):

    __gtype_name__ = 'Clone'

    def __init__(self, widget):

        gtk.DrawingArea.__init__(self)

        self.set_events(gtk.gdk.ALL_EVENTS_MASK)

        self.widget = widget

        self.connect('event', self.dispatch_event)


    def do_realize(self):

        gtk.DrawingArea.do_realize(self)

        self.widget.connect('expose-event', lambda source, event: self.window.invalidate_rect(event.area, True))
        self.widget.connect('size-allocate', lambda source, allocation: self.do_size_allocate(allocation))


    def focus_cb(self, *args):

        self.widget.grab_focus()

        toplevel = self.widget.get_toplevel()

        if toplevel:
            toplevel.present()


    def do_unrealize(self):
        self.window.destroy()


    def do_size_request(self, requisition):

        #widget_size = self.widget.get_size()
        widget_size = (100, 100)

        requisition.width = widget_size[0]
        requisition.height = widget_size[1]


    def do_size_allocate(self, allocation):
        if self.flags() & gtk.REALIZED:
            widget_size = self.widget.allocation
            allocation.width = widget_size.width
            allocation.height = widget_size.height
            self.allocation = allocation
            self.window.move_resize(*allocation)


    def dispatch_event(self, source, event):

        if event.type in [gtk.gdk.EXPOSE]:
            return

        if event.type == gtk.gdk.BUTTON_PRESS:
            self.focus_cb()

        event.copy()
        event.window = self.widget.window
        event.put()

        cr = gdk_window_get_cursor(self.widget.window)
        if cr:
            self.window.set_cursor(gtk.gdk.Cursor(cr.type))

        return True


    def do_expose_event(self, event):

        ctx = self.window.cairo_create()

        region = gtk.gdk.region_rectangle(self.widget.allocation)
        r = gtk.gdk.region_rectangle(event.area)
        region.intersect(r)
        ctx.region (region)
        ctx.clip()

        ctx.set_operator(cairo.OPERATOR_SOURCE)
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

        self.resize(width, height)
        self.set_size_request(width, height)


    def move_cb(self, widget, x, y):

        self.move(x, y)


class Overlay(gobject.GObject):

    __gtype_name__ = 'MelangeOverlay'
    __gsignals__ = {
        'close': (gobject.SIGNAL_RUN_LAST, gobject.TYPE_NONE, ())
        }

    def __init__(self):

        gobject.GObject.__init__(self)

        self.window = gtk.Window()
        self.window.fullscreen()
        self.window.stick()
        self.window.set_keep_above(True)
        self.window.set_app_paintable(True)
        self.window.set_skip_pager_hint(True)
        self.window.set_skip_taskbar_hint(True)
        self.window.set_events(self.window.get_events() | gtk.gdk.BUTTON_RELEASE_MASK)
        self.window.connect('expose-event', self.expose_cb)
        self.window.connect('button-release-event', self.button_release_cb)
        self.window.set_colormap(self.window.get_screen().get_rgba_colormap())

        self.bin = cream.gui.CompositeBin()
        self.window.add(self.bin)


    def initialize(self):

        self.window.set_opacity(0)
        self.window.show_all()
        self.window.window.input_shape_combine_region(gtk.gdk.Region(), 0, 0)


    def show(self):

        self.window.set_opacity(1)
        region = gtk.gdk.Region()
        region.union_with_rect((0, 0, 1280, 800))
        self.window.window.input_shape_combine_region(region, 0, 0)


    def hide(self):

        self.window.set_opacity(0)
        self.window.window.input_shape_combine_region(gtk.gdk.Region(), 0, 0)


    def expose_cb(self, source, event):

        ctx = self.window.window.cairo_create()

        ctx.set_operator(cairo.OPERATOR_SOURCE)
        ctx.set_source_rgba(0, 0, 0, .8)
        ctx.paint()

        ctx.set_operator(cairo.OPERATOR_OVER)


    def button_release_cb(self, source, event):
        self.emit('close')


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

        self.overlay = Overlay()
        self.overlay.connect('close', lambda *args: self.toggle_overlay())
        self.thingy = MelangeThingy()

        self.thingy.connect('toggle-overlay', lambda *args: self.toggle_overlay())
        self.thingy.connect('show-settings', lambda *args: self.config.show_window())

        # Load widgets stored in configuration.
        for widget in self.config.widgets:
            self.load_widget(**widget)

        self.config.connect('field-value-changed', self.configuration_changed_cb)

        try:
            self.hotkey_manager = cream.ipc.get_object('org.cream.hotkeys', '/org/cream/hotkeys')

            self.hotkey_manager.register_hotkey(self.config.hotkey_overlay)
            self.hotkey_manager.connect_to_signal('activate', self.hotkey_activate_cb)
        except:
            self.hotkey_manager = None
            self.messages.debug("Not able to register hotkey.")


    def configuration_changed_cb(self, source, field, value):

        if field == 'hotkey_overlay':
            if self.hotkey_manager:
                self.hotkey_manager.register_hotkey(self.config.hotkey_overlay)


    def hotkey_activate_cb(self, keyval, modifier_mask):

        if (keyval, modifier_mask) == gtk.accelerator_parse(self.config.hotkey_overlay):
            self.toggle_overlay()


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

        widget.window = WidgetWindow(widget)
        widget.window.show_all()

        widget.clone = Clone(widget.view)

        self.overlay.bin.add(widget.clone, x, y)
        widget.clone.show()


    @cream.ipc.method('', 'a{sa{ss}}')
    def list_widgets(self):
        """
        List all available widgets.

        :return: List of widgets.
        :rtype: `list`
        """

        return self.widgets.by_hash


    @cream.ipc.method('', '')
    def toggle_overlay(self):
        """ Show the overlay window. """

        global OVERLAY

        if OVERLAY:
            OVERLAY = False
            self.overlay.hide()

            for k, w in self.widget_instances.iteritems():
                w.window.set_opacity(1)
        else:
            OVERLAY = True
            self.overlay.initialize()
            self.overlay.show()

            for k, w in self.widget_instances.iteritems():
                w.window.set_opacity(0)


    def quit(self):
        """ Quit the module. """

        self.config.widgets = self.widget_instances.values()
        cream.Module.quit(self)


    def widget_remove_cb(self, widget):
        """ Callback being called when a widget has been removed. """

        self.overlay.bin.remove(widget.clone)
        del self.widget_instances[widget.instance]


    def widget_reload_cb(self, widget):
        """ Callback function that is called when the user clicks on the "Reload" menu entry. """

        info_dict = widget.__xmlserialize__()
        self.messages.debug("Reloading widget '%(name)s'" % info_dict)
        widget.close()
        self.load_widget(**info_dict)


    def button_press_cb(self, source, event, widget):
        """ Handle clicking on the widget (e. g. by showing context menu). """

        if event.button == MOUSE_BUTTON_MIDDLE:
            self._edit_mode = EDIT_MODE_MOVE
            self.start_move(widget)
            return True


    def button_release_cb(self, source, event, widget):

        if event.button == MOUSE_BUTTON_MIDDLE:
            self._edit_mode = EDIT_MODE_NONE
            return True


    def start_move(self, widget):

        # WTF. Maybe put some comments in here. :)
        def move_cb(old_x, old_y):
            if self._edit_mode == EDIT_MODE_MOVE:
                new_x, new_y = self.display.get_pointer()[1:3]
                mov_x = new_x - old_x
                mov_y = new_y - old_y

                res_x = widget.get_position()[0] + mov_x
                res_y = widget.get_position()[1] + mov_y
                #widget.set_position(res_x, res_y)
                widget.set_position(res_x, res_y)
                self.overlay.bin.move(widget.clone, res_x, res_y)

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
    cream.util.set_process_name('melange')
    melange = Melange()
    melange.main()
