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

        Configuration.__init__(self, scheme_path, path, read=False)

RESPONSE_TYPE_INIT = 'init'
RESPONSE_TYPE_CALL = 'call'

        self.read()


class WidgetConfigurationProxy(object):

    def __init__(self, config):
        self.config_ref = weakref.ref(config)

    def __getattribute__(self, key):

        try:
            return object.__getattribute__(self, key)
        except AttributeError:
            return getattr(self.config_ref(), key)



class WidgetInstance(gobject.GObject):

    __gtype_name__ = 'WidgetInstance'
    __gsignals__ = {
        'raise-request': (gobject.SIGNAL_RUN_LAST, gobject.TYPE_NONE, ()),
        'remove-request': (gobject.SIGNAL_RUN_LAST, gobject.TYPE_NONE, ()),
        'reload-request': (gobject.SIGNAL_RUN_LAST, gobject.TYPE_NONE, ()),
        'resize-request': (gobject.SIGNAL_RUN_LAST, gobject.TYPE_NONE, (gobject.TYPE_INT, gobject.TYPE_INT)),
        'focus-request': (gobject.SIGNAL_RUN_LAST, gobject.TYPE_NONE, ()),
        'begin-move-request': (gobject.SIGNAL_RUN_LAST, gobject.TYPE_NONE, ()),
        'end-move-request': (gobject.SIGNAL_RUN_LAST, gobject.TYPE_NONE, ()),
        'show-config-dialog-request' : (gobject.SIGNAL_RUN_LAST, gobject.TYPE_NONE, ()),
        'show-about-dialog-request' : (gobject.SIGNAL_RUN_LAST, gobject.TYPE_NONE, ()),
    }

    def __init__(self, widget):

        gobject.GObject.__init__(self)

        self.widget_ref = weakref.ref(widget)

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

        self.websocket_handler = None
        self.api = None

class Widget(gobject.GObject):

        self.js_context.melange = WidgetAPI()
        self.js_context.melange.show_add_widget_dialog = self.widget_ref().__melange_ref__().add_widget
        self.js_context.melange.show_settings_dialog = self.widget_ref().__melange_ref__().config.show_dialog

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
    def widget_element(self):
        if not self.js_context.document.body:
            # we don't have any body yet
            return

        for element in self.js_context.document.body.childNodes.values():
            if getattr(element, 'className', None) == 'widget':
                return element

    widget_element.not_none = True


    def resize_cb(self, widget, event, *args):

        """ Resize the widget properly... """
        if self.widget_element:
            width = int(self.widget_element.offsetWidth)
            height = int(self.widget_element.offsetHeight)
            if not self._size == (width, height):
                self._size = (width, height)
                self.emit('resize-request', width, height)


    def button_press_cb(self, source, event):
        """ Handle clicking on the widget (e. g. by showing context menu). """

        self.emit('focus-request')
        self.emit('raise-request')

        if event.button == MOUSE_BUTTON_RIGHT:
            self.menu.popup(None, None, None, event.button, event.get_time())
            return True
        elif event.button == MOUSE_BUTTON_MIDDLE:
            self.emit('begin-move-request')
            self.fade_out()
            return True
        elif event.button == MOUSE_BUTTON_LEFT and self.state == STATE_MOVE:
            self.emit('begin-move-request')
            return False


    def button_release_cb(self, source, event):

        if event.button == MOUSE_BUTTON_MIDDLE:
            self.emit('end-move-request')
            self.fade_in()
            return True
        if event.button == MOUSE_BUTTON_LEFT and self.state == STATE_MOVE:
            self.emit('end-move-request')
            return False


    def navigation_request_cb(self, view, frame, request, action, decision):
        """ Handle clicks on links, etc. """

        uri = request.get_uri()

        if not uri.startswith(HTTPSERVER_BASE_URL):
            # external URL, open in browser
            webbrowser.open(uri)
            return True


    def begin_move(self):

        self.state = STATE_MOVE

        self.fade_out()


    def end_move(self):

        self.emit('end-move-request')
        self.state = STATE_NONE

        self.fade_in()


    def fade_out(self):

        def fade(t, state):
            self.widget_element.style.opacity = 1 - (1-OPACITY_MOVE)*state

        t = cream.gui.Timeline(200, cream.gui.CURVE_SINE)
        t.connect('update', fade)
        t.run()


    def fade_in(self):

        def fade(t, state):
            self.widget_element.style.opacity = OPACITY_MOVE + (1-OPACITY_MOVE)*state

        t = cream.gui.Timeline(200, cream.gui.CURVE_SINE)
        t.connect('update', fade)
        t.run()



class Widget(gobject.GObject, cream.Component):

    __gtype_name__ = 'Widget'
    __gsignals__ = {
        'raise-request': (gobject.SIGNAL_RUN_LAST, gobject.TYPE_NONE, ()),
        'remove-request': (gobject.SIGNAL_RUN_LAST, gobject.TYPE_NONE, ()),
        'reload-request': (gobject.SIGNAL_RUN_LAST, gobject.TYPE_NONE, ()),
        'move-request': (gobject.SIGNAL_RUN_LAST, gobject.TYPE_NONE, (gobject.TYPE_INT, gobject.TYPE_INT)),
        'begin-move': (gobject.SIGNAL_RUN_LAST, gobject.TYPE_NONE, ()),
        'end-move': (gobject.SIGNAL_RUN_LAST, gobject.TYPE_NONE, ())
        }

    def __init__(self, path, backref):
        self.__melange_ref__ = weakref.ref(backref)
        exec_mode = self.__melange_ref__().context.execution_mode

        gobject.GObject.__init__(self)
        cream.base.Component.__init__(self, path=path, user_path_prefix='org.cream.Melange/data/widgets', exec_mode=exec_mode)

        self.state = STATE_NONE

        width = gtk.gdk.screen_width()
        height = gtk.gdk.screen_height()
        self._position = (int(width/2), int(height/2))

        self.display = gtk.gdk.display_get_default()

        self.instance_id = '%s' % random_hash(bits=100)[0:32]

        # TODO: User self.context.get(_user)_path()
        skin_dir = os.path.join(self.context.working_directory, 'data', 'skins')
        self.skins = cream.manifest.ManifestDB(skin_dir, type='org.cream.melange.Skin')

        scheme_path = os.path.join(self.context.get_path(), 'configuration/scheme.xml')
        path = os.path.join(self.context.get_user_path(), 'configuration/')

        self.config = WidgetConfiguration(scheme_path,
                                          path,
                                          skins=self.skins,
                                          themes=self.__melange_ref__().themes)
        self.config.connect('field-value-changed', self.configuration_value_changed_cb)

        self.load()


    def get_data_path(self):

        data_path = os.path.join(self.context.get_user_path(), 'data/shared')
        if not os.path.isdir(data_path):
            orig_data_path = os.path.join(self.context.get_path(), 'data/shared')

            if os.path.isdir(orig_data_path):
                shutil.copytree(orig_data_path, data_path)
            else:
                os.makedirs(data_path)

        return data_path


    def get_skin_path(self):
        return self.get_skin_path_by_id(self.config.widget_skin)


    def get_skin_path_by_id(self, skin_id):
        return os.path.join(
            self.context.working_directory,
            'skins',
            os.path.dirname(self.skins.get(id=skin_id).next()._path)
        )

    def get_current_theme(self):
        theme_id = self.config.widget_theme
        if theme_id == 'use.the.fucking.global.settings.and.suck.my.Dick':
            theme_id = self.__melange_ref__().config.default_theme
        return self.__melange_ref__().themes.get(id=theme_id).next()


    def begin_move(self):

        self.emit('begin-move')

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



    def end_move_request_cb(self, source):

        self.end_move()

    def resource_request_cb(self, view, frame, resource, request, response):

        uri = request.get_property('uri')
        uri = extend_querystring(uri, {'id': self.instance_id})
        request.set_property('uri', uri)



    def focus_request_cb(self, source):
        pass


    def reload(self):
        """ Reload the widget. Really? Yeah. """

        self.emit('reload-request')


    def remove(self):
        """ Close the widget window and emit 'remove' signal. """

        self.config.save()

        self.instance.get_view().destroy()
        del self


    def get_size(self):
        """
        Get the size of the widget.

        :return: Size.
        :rtype: `tuple`
        """

        return self.window.get_size()


    def get_position(self):
        """
        Get the position of the widget.

        :return: Position.
        :rtype: `tuple`
        """

        return self._position


    def set_position(self, x, y):
        """
        Set the position of the widget.

        :param x: The x-coordinate.
        :param y: The y-coordinate.

        :type x: `int`
        :type y: `int`
        """

        self._position = (x, y)


    def configuration_value_changed_cb(self, source, key, value):

        if key == 'widget_theme' or key == 'widget_skin':
            self.reload()


    @cached_property
    def about_dialog(self):
        """ Show the 'About' dialog. """

        return AboutDialog(self.context.manifest)


    def __xmlserialize__(self):
        """
        Return serialized data about widget.

        :return: Dict containing 'name', 'x' and 'y'.
        :rtype: `dict`
        """

        # TODO: Save hash rather than name here?
        return {
            'name' : self.context.manifest['name'],
            'x'    : self.get_position()[0],
            'y'    : self.get_position()[1],
            'profile': self.config.profiles.active.name
        }
