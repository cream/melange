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

import gobject
gobject.threads_init()

import gtk
import cairo

import wnck

import cream
import cream.manifest
import cream.ipc
import cream.gui
import cream.util

from cream.contrib.melange.dialogs import AddWidgetDialog

from widget import Widget
from chrome import Background, Thingy
from httpserver import MelangeResponse, run as httpserver_run, \
                       HOST as HTTPSERVER_HOST, PORT as HTTPSERVER_PORT


EDIT_MODE_NONE = 0
EDIT_MODE_MOVE = 1
MOUSE_BUTTON_MIDDLE = 2

MODE_NORMAL = 0
MODE_EDIT = 1


class WidgetManager(gobject.GObject):

    __gtype_name__ = 'WidgetManager'
    __gsignals__ = {
        'window-added': (gobject.SIGNAL_RUN_LAST, gobject.TYPE_NONE, (gtk.Window,)),
        'window-removed': (gobject.SIGNAL_RUN_LAST, gobject.TYPE_NONE, (gtk.Window,)),
        }

    def __init__(self):

        gobject.GObject.__init__(self)

        self._widgets = {}


    def keys(self):
        return self._widgets.keys()


    def values(self):
        return self._widgets.values()


    def items(self):
        return self._widgets.items()


    def has_key(self, key):
        return self._widgets.has_key(key)


    def __getitem__(self, key):
        return self._widgets[key]


    def __setitem__(self, key, value):
        self._widgets[key] = value


    def __delitem__(self, key):
        del self._widgets[key]


    def add(self, widget, x=None, y=None):
        self[widget.instance_id] = widget

        widget.connect('move-request', self.move_request_cb)
        widget.connect('remove-request', self.remove_request_cb)

        if x and y:
            widget.set_position(x, y) # TODO: Use own moving algorithms.

        self.emit('window-added', widget.window)


    def move_request_cb(self, widget, x, y):

        old_x, old_y = widget.get_position()
        new_x = old_x + x
        new_y = old_y + y

        widget.set_position(new_x, new_y)


    def remove_request_cb(self, widget):

        self.emit('window-removed', widget.window)

        widget.remove()
        self.remove(widget)


    def remove(self, widget):
        del self[widget.instance_id]


class CommonWidgetManager(WidgetManager):

    def move_request_cb(self, widget, x, y):

        old_x, old_y = widget.get_position()
        new_x = old_x + x
        new_y = old_y + y

        widget.set_position(new_x, new_y)


class Melange(cream.Module, cream.ipc.Object):
    """ The main class of the Melange module. """

    mode = MODE_NORMAL

    def __init__(self):

        cream.Module.__init__(self)

        cream.ipc.Object.__init__(self,
            'org.cream.melange',
            '/org/cream/melange'
        )

        self.run_server()

        self.screen = wnck.screen_get_default()
        self.display = gtk.gdk.display_get_default()
        self._edit_mode = EDIT_MODE_NONE

        # Scan for themes...
        theme_dir = os.path.join(self.context.working_directory, 'themes')
        self.themes = cream.manifest.ManifestDB(theme_dir, type='org.cream.melange.Theme')

        # Scan for widgets...
        self.available_widgets = cream.manifest.ManifestDB('widgets', type='org.cream.melange.Widget')

        self.background = Background()
        self.background.initialize()

        self.widgets = CommonWidgetManager()
        self.widgets.connect('window-added', lambda widget_manager, window: window.set_transient_for(self.background.window))

        self.add_widget_dialog = AddWidgetDialog()

        self.thingy = Thingy()
        self.thingy.thingy_window.set_transient_for(self.background.window)
        self.thingy.control_window.set_transient_for(self.background.window)

        self.thingy.connect('toggle-overlay', lambda *args: self.toggle_overlay())
        self.thingy.connect('show-settings', lambda *args: self.config.show_dialog())
        self.thingy.connect('show-add-widgets', lambda *args: self.add_widget())

        # Load widgets stored in configuration.
        for widget in self.config.widgets:
            self.load_widget(**widget)

        widgets = sorted(self.available_widgets.by_id.itervalues(), key=itemgetter('name'))
        for widget in widgets:
            if widget.has_key('icon'):
                icon_path = os.path.join(widget['path'], widget['icon'])
                pixbuf = gtk.gdk.pixbuf_new_from_file(icon_path).scale_simple(28, 28, gtk.gdk.INTERP_HYPER)
            else:
                pixbuf = gtk.gdk.pixbuf_new_from_file(os.path.join(self.context.working_directory, 'melange.png')).scale_simple(28, 28, gtk.gdk.INTERP_HYPER)
            #label = "<b>{0}</b>\n{1}".format(w['name'], w['description'])
            label = "<b>{0}</b>\n{1}".format(widget['name'], '')
            #self.liststore.append((w['id'], w['id'], w['name'], w['description'], pb, label))
            self.add_widget_dialog.liststore.append((widget['id'], widget['id'], widget['name'], '', pixbuf, label))

        self.hotkeys.connect('hotkey-activated', self.hotkey_activated_cb)


    def run_server(self):
        class _MelangeResponse(MelangeResponse):
            _melange = self
        self._server_thread = thread.start_new_thread(
            httpserver_run,
            (HTTPSERVER_HOST, HTTPSERVER_PORT, _MelangeResponse)
        )


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

        widget = Widget(self.available_widgets.get_by_name(name)._path, backref=self)
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

        self.config.widgets = self.widgets.values()
        cream.Module.quit(self)


if __name__ == '__main__':
    cream.util.set_process_name('melange')
    melange = Melange()
    melange.main()

