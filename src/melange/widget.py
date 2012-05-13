#! /usr/bin/env python
# -*- coding: utf-8 -*-

# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 2 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the Free Software
# Foundation, Inc., 51 Franklin Street, Fifth Floor, Boston,
# MA 02110-1301, USA.

import os
import cairo
import json

from gi.repository import GtkClutter as gtkclutter
from gi.repository import GObject as gobject, WebKit as webkit, Gtk as gtk, Gdk as gdk

from cream.util import cached_property, extend_querystring, random_hash
from cream.config import Configuration

from melange.common import HTTP_BASE_URL, MOUSE_BUTTON_RIGHT
from melange.api import import_api_file, APIS


RESPONSE_TYPE_INIT = 'init'
RESPONSE_TYPE_CALL = 'call'



class WidgetSkin(object):

    def __init__(self, skin_dir, name):

        self.path = os.path.join(skin_dir, name)
        self.name = name.capitalize()


    def __str__(self):
        return '<WidgetSkin {0}>'.format(self.name)

    def __repr__(self):
        return str(self)




class WidgetManager(object):

    def __init__(self):

        self.widgets = {}

    def add_widget(self, widget_id, path, x, y, themes):

        widget = Widget(widget_id, path, x, y, themes)
        self.widgets[widget.instance_id] = widget

        return widget

    def remove_widget(self, instance_id):

        del self.widgets[instance_id]


    def get_widget(self, instance_id):

        return self.widgets[instance_id]

    def get_all_widgets(self):

        return self.widgets.itervalues()


class Widget(gobject.GObject):

    __gtype_name__ = 'MelangeWidget'
    __gsignals__ = {
        'remove': (gobject.SignalFlags.RUN_LAST, None, ()),
    }

    def __init__(self, widget_id, path, x, y, themes):

        gobject.GObject.__init__(self)

        self.id = widget_id
        self.instance_id = random_hash()[:10]
        self.path = path
        self.themes = themes

        self.position = (x, y)

        self.websocket_handler = None
        self.api = None


    def load(self):

        self.view = webkit.WebView()
        self.view.set_transparent(True)

        settings = self.view.get_settings()
        settings.set_property('enable-plugins', False)
        settings.set_property('enable_default_context_menu', False)
        self.view.set_settings(settings)

        self.view.connect('draw', self.draw)
        self.view.connect('button-release-event', self.button_release_cb)
        self.view.connect('resource-request-starting', self.resource_request_cb)

        url = HTTP_BASE_URL + 'widget/index.html?id={id}'.format(id=self.instance_id)
        self.view.open(url)

        self.actor = gtkclutter.Actor.new_with_contents(self.view)
        self.actor.set_reactive(True)
        self.actor.set_position(*self.position)


    @cached_property
    def skins(self):

        skin_path = os.path.join(self.path, 'data/skins')
        return [WidgetSkin(skin_path, name) for name in os.listdir(skin_path)]

    @cached_property
    def menu(self):

        # Building context menu:
        item_configure = gtk.ImageMenuItem(gtk.STOCK_PREFERENCES)
        item_configure.get_children()[0].set_label("Configure")
        item_configure.connect('activate', self.show_config_dialog)

        #item_reload = gtk.ImageMenuItem(gtk.STOCK_REFRESH)
        #item_reload.get_children()[0].set_label("Reload")
        #item_reload.connect('activate', lambda *x: self.emit('reload-request'))

        item_remove = gtk.ImageMenuItem(gtk.STOCK_REMOVE)
        item_remove.get_children()[0].set_label("Remove")
        item_remove.connect('activate', self.remove_cb)

        item_about = gtk.ImageMenuItem(gtk.STOCK_ABOUT)
        item_about.get_children()[0].set_label("About")
        item_about.connect('activate', self.show_about_dialog)

        menu = gtk.Menu()
        menu.append(item_configure)
        #menu.append(item_reload)
        menu.append(item_remove)
        menu.append(item_about)
        menu.show_all()

        return menu

    @property
    def selected_skin(self):
        return self.skins[0] # TODO


    @property
    def selected_theme(self):
        return self.themes[1] # TODO


    def on_websocket_connected(self, websocket_handler):

        self.websocket_handler = websocket_handler

        if not self.id in APIS:
            import_api_file(self.path, self.id)

        self.api = APIS[self.id]()


    def on_websocket_init(self):

        response = {'type': RESPONSE_TYPE_INIT, 'methods': self.api.get_exposed_methods()}
        self.websocket_handler.send(response)


    def on_api_method_called(self, method, callback_id, arguments):

        result = getattr(self.api, method)(*arguments)
        response = {'type': RESPONSE_TYPE_CALL, 'callback_id': callback_id, 'arguments': result}
        self.websocket_handler.send(response)


    def draw(self, view, ctx):

        ctx = gdk.cairo_create(self.view.get_window())

        ctx.set_operator(cairo.OPERATOR_CLEAR)
        ctx.set_source_rgba(0, 0, 0, 0)
        ctx.paint()


    def button_release_cb(self, view, event):

        if event.button == MOUSE_BUTTON_RIGHT:
            self.menu.popup(None, None, None, None, event.button, event.get_time())
            return True


    def resource_request_cb(self, view, frame, resource, request, response):

        uri = request.get_property('uri')
        uri = extend_querystring(uri, {'id': self.instance_id})
        request.set_property('uri', uri)


    def show_config_dialog(self, *args):

        pass


    def show_about_dialog(self, *args):

        pass


    def remove_cb(self, menuitem):

        # Destroy the ui elements, which too closes the websocket connection
        self.view.destroy()
        self.actor.destroy()

        self.view = None
        self.actor = None

        self.emit('remove')
