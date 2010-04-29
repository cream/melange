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

import os.path
import math

import wnck

import cream
import cream.manifest
import cream.ipc
import cream.gui
import cream.util

from cream.contrib.melange.dialogs import AddWidgetDialog

from widget import Widget
from thingy import Thingy
from httpserver import HttpServer

EDIT_MODE_NONE = 0
EDIT_MODE_MOVE = 1
MOUSE_BUTTON_MIDDLE = 2

MODE_NORMAL = 0
MODE_EDIT = 1

OVERLAY = False

class WidgetWindow(gtk.Window):
    """
    The WidgetWindow class is being used for displaying Melange's widget in window mode.
    """

    def __init__(self, widget):

        self.widget = widget
        self.widget.connect('remove', self.remove_cb)
        self.widget.connect('move', self.move_cb)
        self.widget.connect('resize', self.resize_cb)

        gtk.Window.__init__(self)

        # Setting up the Widget's window...
        self.stick()
        self.set_type_hint(gtk.gdk.WINDOW_TYPE_HINT_DOCK)
        #self.set_type_hint(gtk.gdk.WINDOW_TYPE_HINT_UTILITY)
        self.set_keep_below(True)
        self.set_skip_pager_hint(True)
        self.set_skip_taskbar_hint(True)
        self.set_decorated(False)
        self.set_app_paintable(True)
        self.set_resizable(False)
        self.set_default_size(10, 10)
        self.connect('expose-event', self.expose_cb)
        self.connect('focus-out-event', self.focus_cb)
        self.set_colormap(self.get_screen().get_rgba_colormap())

        self.set_property('accept-focus', False)

        # Creating container for receiving events:
        self.bin = gtk.EventBox()
        self.bin.add(self.widget.view)

        self.add(self.bin)

        self.move(*self.widget.get_position())


    def focus_cb(self, source, event):
        self.set_property('accept-focus', False)


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


class Melange(cream.Module, cream.ipc.Object):
    """ The main class of the Melange module. """

    mode = MODE_NORMAL

    def __init__(self):

        cream.Module.__init__(self)

        cream.ipc.Object.__init__(self,
            'org.cream.melange',
            '/org/cream/melange'
        )

        self.screen = wnck.screen_get_default()

        self.display = gtk.gdk.display_get_default()
        self._edit_mode = EDIT_MODE_NONE

        # Initialize the HTTP server providing the widget data.
        self.server = HttpServer(self)
        self.server.run()

        # Scan for widgets...
        self.widgets = cream.manifest.ManifestDB('widgets', type='org.cream.melange.Widget')
        self.widget_instances = {}

        self.background = Background()
        self.background.initialize()
        #self.widget_layer.window.window.input_shape_combine_region(gtk.gdk.Region(), 0, 0)

        self.add_widget_dialog = AddWidgetDialog()

        self.thingy = Thingy()
        self.thingy.thingy_window.set_transient_for(self.background.window)
        self.thingy.control_window.set_transient_for(self.background.window)

        self.thingy.connect('toggle-overlay', lambda *args: self.toggle_overlay())
        self.thingy.connect('show-settings', lambda *args: self.config.show_dialog())
        self.thingy.connect('show-settings', lambda *args: self.config.show_dialog())
        self.thingy.connect('show-add-widgets', lambda *args: self.add_widget())

        # Load widgets stored in configuration.
        for widget in self.config.widgets:
            self.load_widget(**widget)

        for w in self.widgets.by_id.itervalues():
            if w.has_key('icon'):
                p = os.path.join(w['path'], w['icon'])
                pb = gtk.gdk.pixbuf_new_from_file(p).scale_simple(28, 28, gtk.gdk.INTERP_HYPER)
            else:
                pb = gtk.gdk.pixbuf_new_from_file(os.path.join(self.context.working_directory, 'melange.png')).scale_simple(28, 28, gtk.gdk.INTERP_HYPER)
            #label = "<b>{0}</b>\n{1}".format(w['name'], w['description'])
            label = "<b>{0}</b>\n{1}".format(w['name'], '')
            #self.liststore.append((w['id'], w['id'], w['name'], w['description'], pb, label))
            self.add_widget_dialog.liststore.append((w['id'], w['id'], w['name'], '', pb, label))

        self.hotkeys.connect('hotkey-activated', self.hotkey_activated_cb)


    def add_widget(self):

        self.add_widget_dialog.show_all()

        if self.add_widget_dialog.run() == 1:
            selection = self.add_widget_dialog.treeview.get_selection()
            model, iter = selection.get_selected()
    
            id = model.get_value(iter, 2)
            self.load_widget(id, False, False)
        self.add_widget_dialog.hide()


    def hotkey_activated_cb(self, source, action):

        if action == 'toggle_overlay':
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

        widget = Widget(self.widgets.get_by_name(name)._path)
        self.widget_instances[widget.instance] = widget

        widget.connect('remove', self.widget_remove_cb)
        widget.connect('reload', self.widget_reload_cb)

        widget.view.connect('button-press-event', self.button_press_cb, widget)
        widget.view.connect('button-release-event', self.button_release_cb, widget)

        widget.set_position(x, y)

        widget.window = WidgetWindow(widget)
        widget.window.set_transient_for(self.background.window)
        widget.window.show_all()

        widget.show()
        widget.view.show()


    @cream.ipc.method('', 'a{sa{ss}}')
    def list_widgets(self):
        """
        List all available widgets.

        :return: List of widgets.
        :rtype: `list`
        """

        res = {}

        for id, w in self.widgets.by_id.iteritems():
            res[id] = {
                'name': w['name'],
                'description': '',
                'path': '',
                #'icon': '',
                'id': w['id'],
                }

        return res


    @cream.ipc.method('', '')
    def toggle_overlay(self):
        """ Show the overlay window. """

        if self.mode == MODE_NORMAL:
            self.mode = MODE_EDIT
            self.thingy.slide_in()
            self.screen.toggle_showing_desktop(True)
            self.background.show()
        else:
            self.mode = MODE_NORMAL
            self.thingy.slide_out()
            self.screen.toggle_showing_desktop(False)
            self.background.hide()


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

        widget.window.set_property('accept-focus', True)
        widget.window.present()

        if self.mode == MODE_EDIT and event.button == MOUSE_BUTTON_MIDDLE:
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
                widget.set_position(res_x, res_y)
                #self.overlay.bin.move(widget.clone, res_x, res_y)
                #self.widget_layer.bin.move(widget.view, res_x, res_y)

                width, height = widget.get_size()

                centers = {
                    'left': (res_x, res_y + height / 2),
                    'right': (res_x + width, res_y + height / 2),
                    'top': (res_x + width / 2, res_y),
                    'bottom': (res_x + width / 2, res_y + height)
                }

                for k, w in self.widget_instances.iteritems():
                    if not w == widget:
                        w_name = w.context.manifest['name']
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

                gobject.timeout_add(20, move_cb, new_x, new_y)

        move_cb(*self.display.get_pointer()[1:3])


if __name__ == '__main__':
    cream.util.set_process_name('melange')
    melange = Melange()
    melange.main()
