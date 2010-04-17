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

import sys
import os.path
import imp

import gobject
import gtk
import cairo
import webkit
import javascriptcore as jscore
import webbrowser

import cream.base
import cream.meta
from cream.util import urljoin_multi, cached_property, random_hash
from cream.contrib.melange.api import APIS, PyToJSInterface
from cream.config import NoConfigurationFileError, Configuration
from cream.config.backend import CreamXMLBackend, CONFIGURATION_SCHEME_FILE

from httpserver import HOST, PORT


MOUSE_BUTTON_RIGHT = 3

class WidgetAPI(object):
    pass


class WidgetConfiguration(Configuration):

    @classmethod
    def fromxml(cls, directory='.', classname=None):

        if CreamXMLBackend.configuration_file_exists(directory):
            from gpyconf.mvc import ComponentFactory
            from gpyconf.fields import MultiOptionField

            backend = CreamXMLBackend(directory)
            class_dict = backend.read_scheme()
            class_dict['widget_skin'] = MultiOptionField(
                label = "Skin",
                section = "Appearance",
                options=(
                    (u'foo', u'Default'),
                    (u'bar', u'Small'),
                ))
            class_dict['widget_theme'] = MultiOptionField(
                label = "Theme",
                section = "Appearance",
                options=(
                    (u'foo', u'Dark'),
                    (u'bar', u'Light'),
                ))

            klass = type(classname or cls.__name__, (cls,), class_dict)
            return klass(backend_instance=backend)
        else:
            raise NoConfigurationFileError("Could not find %s." % CONFIGURATION_SCHEME_FILE)


class Widget(gobject.GObject, cream.Component):

    __gtype_name__ = 'Widget'
    __gsignals__ = {
        'move': (gobject.SIGNAL_RUN_LAST, gobject.TYPE_NONE, (gobject.TYPE_INT, gobject.TYPE_INT)),
        'resize': (gobject.SIGNAL_RUN_LAST, gobject.TYPE_NONE, (gobject.TYPE_INT, gobject.TYPE_INT)),
        'remove': (gobject.SIGNAL_RUN_LAST, gobject.TYPE_NONE, ()),
        'reload' : (gobject.SIGNAL_RUN_LAST, gobject.TYPE_NONE, ())
    }

    def __init__(self, meta):

        gobject.GObject.__init__(self)
        cream.base.Component.__init__(self)

        self._size = (0, 0)
        self._position = (0, 0)

        self.meta = meta

        self.instance = 'widget_%s' % random_hash(bits=100)

        skin_dir = os.path.join(self.meta['path'], 'skins')
        self.skins = cream.meta.MetaDataDB(skin_dir, type='melange.widget.skin')


        try:
            self.uses_config = self.config and True
        except NoConfigurationFileError:
            self.uses_config = False

        self.build_ui()

        # Create JavaScript context...
        self.js_context = jscore.JSContext(self.view.get_main_frame().get_global_context()).globalObject

        # Set up JavaScript API...
        self.js_context._python = WidgetAPI()
        self.js_context._python.init = self.init_api
        self.js_context._python.init_config = self.init_config


    def _load_config(self, base_path=None):

        self.config = WidgetConfiguration.fromxml(base_path or self.meta['path'])
        self.config_loaded = True


    def init_config(self):
        # Register the JavaScript configuration event callback for *all*
        # configuration events. Further dispatching then *happens in JS*.
        if self.uses_config:
            self.js_context.widget.config._python_config = self.config
            self.config.connect('all', self.js_context.widget.config.on_config_event)

    def init_api(self):

        custom_api_file = os.path.join(self.meta['path'], '__init__.py')
        print self.meta['name']
        if os.path.isfile(custom_api_file):
            sys.path.insert(0, self.meta['path'])
            imp.load_module(
                'custom_api_{0}'.format(self.instance),
                open(custom_api_file),
                custom_api_file,
                ('.py', 'r', imp.PY_SOURCE)
            )
            for name, value in APIS[custom_api_file].iteritems():
                c = value()
                i = PyToJSInterface(c)
                c._js_ctx = self.js_context
                self.js_context.widget.api.__setattr__(name, i)
            del sys.path[0]


    def build_ui(self):

        # Initializing the WebView...
        self.view = webkit.WebView()
        self.view.set_transparent(True)

        settings = self.view.get_settings()
        settings.set_property('user-agent', self.instance)
        self.view.set_settings(settings)

        # Connecting to signals:
        self.view.connect('expose-event', self.resize_cb)
        self.view.connect('button-press-event', self.button_press_cb)
        self.view.connect('button-release-event', self.button_release_cb)
        self.view.connect('new-window-policy-decision-requested', self.navigation_request_cb)
        self.view.connect('navigation-policy-decision-requested', self.navigation_request_cb)
        self.view.connect('resource-request-starting', self.resource_request_cb)

        # Building context menu:
        item_configure = gtk.ImageMenuItem(gtk.STOCK_PREFERENCES)
        item_configure.get_children()[0].set_label("Configure")
        if self.uses_config:
            item_configure.connect('activate', lambda *x: self.config.show_dialog())
        else:
            item_configure.set_sensitive(False)

        item_reload = gtk.ImageMenuItem(gtk.STOCK_REFRESH)
        item_reload.get_children()[0].set_label("Reload")
        item_reload.connect('activate', lambda *x: self.reload())

        item_remove = gtk.ImageMenuItem(gtk.STOCK_REMOVE)
        item_remove.connect('activate', lambda *x: self.close())

        item_about = gtk.ImageMenuItem(gtk.STOCK_ABOUT)
        item_about.connect('activate', lambda *x: self.about_dialog.show_all())

        self.menu = gtk.Menu()
        self.menu.append(item_configure)
        self.menu.append(item_reload)
        self.menu.append(item_remove)
        self.menu.append(item_about)
        self.menu.show_all()


    def resource_request_cb(self, view, frame, resource, request, response):
        uri = request.get_property('uri')
        #request.set_property('uri', uri + '?id=aa')


    def close(self):
        """ Close the widget window and emit 'remove' signal. """

        self.emit('remove')


    def show(self):
        """ Show the widget. """

        skin_url = urljoin_multi('http://{0}:{1}'.format(HOST, PORT), 'widgets',
                                 self.instance, 'Default', 'index.html')
        self.view.open(skin_url)


    def reload(self):
        """ Reload the widget. Really? Yeah. """

        self.emit('reload')


    def get_size(self):
        """
        Get the size of the widget.

        :return: Size.
        :rtype: `tuple`
        """

        return self._size


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
        self.emit('move', *self._position)


    @cached_property
    def about_dialog(self):
        """ Show the 'About' dialog. """

        about_dialog = gtk.AboutDialog()
        about_dialog.connect('response', lambda *x: self.about_dialog.hide())
        about_dialog.connect('delete-event', lambda *x: True)

        about_dialog.set_name(self.meta['name'])
        about_dialog.set_authors([self.meta['author']])
        if self.meta.has_key('icon'):
            icon_path = os.path.join(self.meta['path'], self.meta['icon'])
            icon_pb = gtk.gdk.pixbuf_new_from_file(icon_path).scale_simple(64, 64, gtk.gdk.INTERP_HYPER)
            about_dialog.set_logo(icon_pb)
        about_dialog.set_comments(self.meta['comment'])

        return about_dialog


    def _update_position(self, window, event):
        """ Emit the 'position-changed' signal when the widget was moved. """

        self.emit('move', event.x, event.y)


    def button_press_cb(self, source, event):
        """ Handle clicking on the widget (e. g. by showing context menu). """

        if event.button == MOUSE_BUTTON_RIGHT:
            self.menu.popup(None, None, None, event.button, event.get_time())
            return True


    def button_release_cb(self, source, event):
        pass


    @cached_property
    def widget_element(self):
        # TODO: Can we eliminate that ugly indices-iterating-loop and use
        #       something similar to Javascript's `for each`?
        if not self.js_context.document.body:
            # we don't have any body yet
            return

        for i in xrange(0, int(self.js_context.document.body.childNodes.length)):
            try:
                element = self.js_context.document.body.childNodes[i]
                if element.className == 'widget':
                    return element
            except:
                pass
    widget_element.not_none = True

    def resize_cb(self, widget, event, *args):
        """ Resize the widget properly... """
        if self.widget_element:
            width = int(self.widget_element.offsetWidth)
            height = int(self.widget_element.offsetHeight)
            if not self._size == (width, height):
                self._size = (width, height)
                self.emit('resize', width, height)


    def navigation_request_cb(self, view, frame, request, action, decision):
        """ Handle clicks on links, etc. """

        uri = request.get_uri()

        if not uri.startswith('http://{0}:{1}/'.format(HOST, PORT)):
            import webbrowser
            webbrowser.open(uri)
            return True


    def __xmlserialize__(self):
        """
        Return serialized data about widget.

        :return: Dict containing 'name', 'x' and 'y'.
        :rtype: `dict`
        """

        # TODO: Save hash rather than name here?
        return {
            'name' : self.meta['name'],
            'x'    : self.get_position()[0],
            'y'    : self.get_position()[1],
        }
