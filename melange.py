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

import os.path
import thread
from operator import itemgetter

import time
import math

import gobject
gobject.threads_init()

import gtk
import cairo

import cream
import cream.manifest
import cream.ipc
import cream.gui
import cream.util, cream.util.pywmctrl

from cream.contrib.melange.dialogs import AddWidgetDialog

from widget import Widget
from container import ContainerWindow
from httpserver import HttpServer
from common import HTTPSERVER_HOST, HTTPSERVER_PORT, \
                   ORIENTATION_HORIZONTAL, ORIENTATION_VERTICAL, \
                   MODE_NORMAL, MODE_EDIT, \
                   STATE_HIDDEN, STATE_MOVE, STATE_NONE, STATE_VISIBLE,\
                   MOVE_TIMESTEP

from container import ORIENTATION_TOP, ORIENTATION_BOTTOM, ORIENTATION_LEFT, ORIENTATION_RIGHT, ORIENTATION_CENTER


class TransparentWindow(gtk.Window):

    def __init__(self):

        gtk.Window.__init__(self)

        self.set_colormap(self.get_screen().get_rgba_colormap())
        self.set_app_paintable(True)
        self.connect('expose-event', self.expose_cb)


    def expose_cb(self, source, event):
        """ Clear the widgets background. """

        ctx = source.window.cairo_create()

        ctx.set_operator(cairo.OPERATOR_SOURCE)
        ctx.set_source_rgba(0, 0, 0, 0)
        ctx.paint()


class WidgetLayer(TransparentWindow):

    def __init__(self):

        TransparentWindow.__init__(self)

        self.widgets = []

        self.display = self.get_display()
        self.screen = self.display.get_default_screen()
        width, height = self.screen.get_width(), self.screen.get_height()
        self.resize(width, height)

        self.layout = cream.gui.CompositeBin()
        self.add(self.layout)


    def add_widget(self, widget):

        self.widgets.append(widget)

        view = widget.instance.get_view()
        self.layout.add(view, *widget.get_position())
        view.show_all()


    def remove_widget(self, widget):

        self.widgets.remove(widget)

        view = widget.instance.get_view()
        self.layout.remove(view)


    def raise_widget(self, widget):

        view = widget.instance.get_view()
        self.layout.raise_child(view)


    def move_widget(self, widget, x, y):

        view = widget.instance.get_view()
        self.layout.move(view, x, y)


class PrimaryWidgetLayer(WidgetLayer):

    def __init__(self):

        WidgetLayer.__init__(self)
        self.set_type_hint(gtk.gdk.WINDOW_TYPE_HINT_DESKTOP)


class WidgetManager(gobject.GObject):

    __gtype_name__ = 'WidgetManager'
    __gsignals__ = {
        'widget-added': (gobject.SIGNAL_RUN_LAST, gobject.TYPE_NONE, (Widget,)),
        'widget-removed': (gobject.SIGNAL_RUN_LAST, gobject.TYPE_NONE, (Widget,)),
        }

    def __init__(self):

        gobject.GObject.__init__(self)

        self.screen_width, self.screen_height = gtk.gdk.screen_width(), gtk.gdk.screen_height()

        self.signal_handlers = {}
        self.widgets = {}

        self.primary_widget_layer = PrimaryWidgetLayer()
        self.primary_widget_layer.show_all()


    def keys(self):
        return self.widgets.keys()


    def values(self):
        return self.widgets.values()


    def items(self):
        return self.widgets.items()


    def has_key(self, key):
        return self.widgets.has_key(key)


    def __getitem__(self, key):
        return self.widgets[key]


    def __setitem__(self, key, value):
        self.widgets[key] = value


    def __delitem__(self, key):
        del self.widgets[key]


    def add(self, widget, x=None, y=None):

        self[widget.instance_id] = widget

        self.signal_handlers[widget] = {}

        #self._signal_handlers[widget]['begin-move'] = widget.connect('move-request', self.begin_move_cb)
        self.signal_handlers[widget]['raise-request'] = widget.connect('raise-request', self.raise_request_cb)
        self.signal_handlers[widget]['end-move'] = widget.connect('end-move', self.end_move_cb)
        self.signal_handlers[widget]['move-request'] = widget.connect('move-request', self.move_request_cb)
        self.signal_handlers[widget]['remove-request'] = widget.connect('remove-request', self.remove_request_cb)

        if x and y:
            widget.set_position(x, y) # TODO: Use own moving algorithms.

        self.primary_widget_layer.add_widget(widget)

        self.emit('widget-added', widget)


    def raise_request_cb(self, widget):

        self.primary_widget_layer.raise_widget(widget)


    def end_move_cb(self, widget):
        pass


    def move_request_cb(self, widget, x, y):

        old_x, old_y = widget.get_position()
        new_x = max(0, min(old_x + x, self.screen_width - widget.instance.get_view().allocation.width))
        new_y = max(0, min(old_y + y, self.screen_height - widget.instance.get_view().allocation.height))

        self.primary_widget_layer.move_widget(widget, new_x, new_y)
        widget.set_position(new_x, new_y)


    def remove_request_cb(self, widget):

        widget.remove()
        self.remove(widget)


    def remove(self, widget):

        del self[widget.instance_id]

        widget.disconnect(self.signal_handlers[widget]['raise-request'])
        widget.disconnect(self.signal_handlers[widget]['end-move'])
        widget.disconnect(self.signal_handlers[widget]['move-request'])
        widget.disconnect(self.signal_handlers[widget]['remove-request'])

        self.emit('widget-removed', widget)


class Melange(cream.Module, cream.ipc.Object):
    """ The main class of the Melange module. """

    def __init__(self):

        cream.Module.__init__(self)

        cream.ipc.Object.__init__(self,
            'org.cream.Melange',
            '/org/cream/Melange'
        )

        self.run_server()

        self.screen = cream.util.pywmctrl.Screen()
        self.display = gtk.gdk.display_get_default()

        self.widgets = WidgetManager()

        # Scan for themes...
        theme_dir = os.path.join(self.context.working_directory, 'themes')
        self.themes = cream.manifest.ManifestDB(theme_dir, type='org.cream.melange.Theme')

        # Scan for widgets...
        self.available_widgets = cream.manifest.ManifestDB('widgets', type='org.cream.melange.Widget')

        self.add_widget_dialog = AddWidgetDialog()

        # Load widgets stored in configuration.
        for widget in self.config.widgets:
            self.load_widget(**widget)

        widgets = sorted(self.available_widgets.by_id.itervalues(), key=itemgetter('name'))
        for widget in widgets:
            self.add_widget_dialog.add(widget, self.context.working_directory)
        self.hotkeys.connect('hotkey-activated', self.hotkey_activated_cb)


    def run_server(self):
        server = HttpServer(self)
        thread.start_new_thread(server.run, (HTTPSERVER_HOST, HTTPSERVER_PORT))


    def add_widget(self):

        self.add_widget_dialog.dialog.show_all()

        if self.add_widget_dialog.dialog.run() == 1:
            selection = self.add_widget_dialog.treeview.get_selection()
            model, iter = selection.get_selected()

            id = model.get_value(iter, 2)
            self.load_widget(id, False, False)
        self.add_widget_dialog.dialog.hide()


    def hotkey_activated_cb(self, source, action):

        if action == 'toggle_overlay':
            pass


    @cream.ipc.method('', '')
    def debug_memory(self):

        from guppy import hpy
        h = hpy()
        print h.heap()


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

        # Initialize the widget...
        widget = Widget(self.available_widgets.get_by_name(name)._path, backref=self)

        widget.set_position(x, y)

        # Add the widget to the list of currently active widgets:
        self.widgets.add(widget, x, y)

        widget.show()


    @cream.ipc.method('', 'a{sa{ss}}')
    def list_widgets(self):
        """
        List all available widgets.

        :return: List of widgets.
        :rtype: `list`
        """

        res = {}

        for id, w in self.available_widgets.by_id.iteritems():
            res[id] = {
                'name': w['name'],
                'description': '',
                'path': '',
                'id': w['id'],
                }

        return res


    def quit(self):
        """ Quit the module. """

        self.config.widgets = self.widgets.values()
        cream.Module.quit(self)


if __name__ == '__main__':
    cream.util.set_process_name('melange')
    melange = Melange()
    melange.main()

