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
import weakref

import gobject
import gtk
import cairo
import webkit
import javascriptcore as jscore
import webbrowser

import cream.base
import cream.gui
from cream.util import urljoin_multi, cached_property, random_hash
from cream.contrib.melange.api import APIS, PyToJSInterface

from cream.config import Configuration, MissingConfigurationDefinitionFile
from cream.config.backend import CreamXMLBackend, CONFIGURATION_SCHEME_FILE
from gpyconf.fields import MultiOptionField

from common import HTTPSERVER_BASE_URL, \
                   STATE_HIDDEN, STATE_MOVE, STATE_NONE, STATE_VISIBLE, \
                   MOUSE_BUTTON_LEFT, MOUSE_BUTTON_MIDDLE, MOUSE_BUTTON_RIGHT, \
                   MOVE_TIMESTEP

class WidgetAPI(object):
    pass


class WidgetConfiguration(Configuration):

    def __init__(self, path, skins, themes):

        Configuration.__init__(self, path, read=False)

        self._add_field(
            'widget_skin',
            MultiOptionField('Skin',
                section='Appearance',
                options=((key, val['name']) for key, val in skins.iteritems())
            )
        )
        self._add_field(
            'widget_theme',
            MultiOptionField('Theme',
                section='Appearance',
                options=([('use.the.fucking.global.settings.and.suck.my.Dick', 'Use global settings')] + [(key, val['name']) for key, val in themes.iteritems()])
            )
        )

        self.read()


class WidgetConfigurationProxy(object):

    def __init__(self, config):
        self.config_ref = weakref.ref(config)

    def __getattribute__(self, key):

        try:
            return object.__getattribute__(self, key)
        except AttributeError:
            return getattr(self.config_ref(), key)


class MelangeWindow(gtk.Window):

    def __init__(self):

        gtk.Window.__init__(self)

        # Setting up the Widget's window...
        self.stick()
        self.set_type_hint(gtk.gdk.WINDOW_TYPE_HINT_DOCK)
        self.set_keep_below(True)
        self.set_skip_pager_hint(True)
        self.set_skip_taskbar_hint(True)
        self.set_decorated(False)
        self.set_app_paintable(True)
        self.set_resizable(False)
        self.set_default_size(10, 10)
        self.set_colormap(self.get_screen().get_rgba_colormap())


    def expose_cb(self, source, event):
        """ Clear the widgets background. """

        ctx = source.window.cairo_create()

        ctx.set_operator(cairo.OPERATOR_SOURCE)
        ctx.set_source_rgba(0, 0, 0, 0)
        ctx.paint()


class WidgetWindow(MelangeWindow):
    """
    The WidgetWindow class is being used for displaying Melange's widget in window mode.
    """

    def __init__(self):

        MelangeWindow.__init__(self)

        self.connect('expose-event', self.expose_cb)
        self.connect('focus-out-event', self.focus_cb)

        self.set_property('accept-focus', False)


    def focus_cb(self, source, event):
        self.set_property('accept-focus', False)


    def expose_cb(self, source, event):
        """ Clear the widgets background. """

        ctx = source.window.cairo_create()

        ctx.set_operator(cairo.OPERATOR_SOURCE)
        ctx.set_source_rgba(0, 0, 0, 0)
        ctx.paint()


class WidgetInstance(gobject.GObject):

    __gtype_name__ = 'WidgetInstance'
    __gsignals__ = {
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

        self.config = WidgetConfigurationProxy(self.widget_ref().config)

        self._size = (0, 0)
        self._position = (0, 0)
        self._tmp = None

        # Initializing the WebView...
        self.view = webkit.WebView()
        self.view.set_transparent(True)

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
        item_configure.connect('activate', lambda *x: self.emit('show-config-dialog-request'))

        item_reload = gtk.ImageMenuItem(gtk.STOCK_REFRESH)
        item_reload.get_children()[0].set_label("Reload")
        item_reload.connect('activate', lambda *x: self.emit('reload-request'))

        item_remove = gtk.ImageMenuItem(gtk.STOCK_REMOVE)
        item_remove.connect('activate', lambda *x: self.emit('remove-request'))

        item_about = gtk.ImageMenuItem(gtk.STOCK_ABOUT)
        item_about.connect('activate', lambda *x: self.emit('show-about-dialog-request'))

        self.menu = gtk.Menu()
        self.menu.append(item_configure)
        self.menu.append(item_reload)
        self.menu.append(item_remove)
        self.menu.append(item_about)
        self.menu.show_all()

        # Create JavaScript context...
        self.js_context = jscore.JSContext(self.view.get_main_frame().get_global_context()).globalObject

        # Set up JavaScript API...
        self.js_context._python = WidgetAPI()
        self.js_context._python.init = self.init_api
        self.js_context._python.init_config = self.init_config

        self.js_context.melange = WidgetAPI()
        self.js_context.melange.toggle_overlay = self.widget_ref().__melange_ref__()

        skin_url = HTTPSERVER_BASE_URL + '/widget/index.html'
        self.view.open(skin_url)


    def get_tmp(self):
        return self._tmp


    def get_view(self):
        return self.view


    def init_config(self):
        # Register the JavaScript configuration event callback for *all*
        # configuration events. Further dispatching then *happens in JS*.
        self.js_context.widget.config._python_config = self.config
        self.config.connect('all', self.js_context.widget.config.on_config_event)


    def init_api(self):
        custom_api_file = os.path.join(self.widget_ref().context.working_directory, '__init__.py')
        if os.path.isfile(custom_api_file):
            sys.path.insert(0, self.widget_ref().context.working_directory)
            imp.load_module(
                'custom_api_{0}'.format(self.widget_ref().instance_id),
                open(custom_api_file),
                custom_api_file,
                ('.py', 'r', imp.PY_SOURCE)
            )
            for name, value in APIS[custom_api_file].iteritems():
                c = value
                c._js_ctx = self.js_context
                c.context = self.widget_ref().context
                c = c()
                self._tmp = c.get_tmp()
                i = PyToJSInterface(c)
                self.js_context.widget.api.__setattr__(name, i)
            del sys.path[0]


    def resource_request_cb(self, view, frame, resource, request, response):
        uri = request.get_property('uri')
        request.set_property('uri', uri + '?instance={0}'.format(self.widget_ref().instance_id))


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
                self.emit('resize-request', width, height)


    def button_press_cb(self, source, event):
        """ Handle clicking on the widget (e. g. by showing context menu). """

        self.emit('focus-request')

        if event.button == MOUSE_BUTTON_RIGHT:
            self.menu.popup(None, None, None, event.button, event.get_time())
            return True
        elif event.button == MOUSE_BUTTON_MIDDLE:
            self.emit('begin-move-request')
            return True


    def button_release_cb(self, source, event):

        if event.button == MOUSE_BUTTON_MIDDLE:
            self.emit('end-move-request')
            return True


    def navigation_request_cb(self, view, frame, request, action, decision):
        """ Handle clicks on links, etc. """

        uri = request.get_uri()

        if not uri.startswith(HTTPSERVER_BASE_URL):
            # external URL, open in browser
            import webbrowser
            webbrowser.open(uri)
            return True


class Widget(gobject.GObject, cream.Component):

    __gtype_name__ = 'Widget'
    __gsignals__ = {
        'remove-request': (gobject.SIGNAL_RUN_LAST, gobject.TYPE_NONE, ()),
        'move-request': (gobject.SIGNAL_RUN_LAST, gobject.TYPE_NONE, (gobject.TYPE_INT, gobject.TYPE_INT)),
        'begin-move': (gobject.SIGNAL_RUN_LAST, gobject.TYPE_NONE, ()),
        'end-move': (gobject.SIGNAL_RUN_LAST, gobject.TYPE_NONE, ())
        }

    def __init__(self, path, backref):

        self.__melange_ref__ = weakref.ref(backref)

        gobject.GObject.__init__(self)
        cream.base.Component.__init__(self, path=path)

        self.state = STATE_NONE

        self.display = gtk.gdk.display_get_default()

        self.instance_id = '%s' % random_hash(bits=100)[0:32]

        skin_dir = os.path.join(self.context.working_directory, 'skins')
        self.skins = cream.manifest.ManifestDB(skin_dir, type='org.cream.melange.Skin')

        self.config = WidgetConfiguration(self.context.working_directory,
                                          skins=self.skins.by_id,
                                          themes=self.__melange_ref__().themes.by_id)
        self.config.connect('field-value-changed', self.configuration_value_changed_cb)

        self.window = WidgetWindow()

        self.load()

    def get_skin_path(self):
        return self.get_skin_path_by_id(self.config.widget_skin)

    def get_skin_path_by_id(self, skin_id):
        return os.path.join(
            self.context.working_directory,
            'skins',
            os.path.dirname(self.skins.get_by_id(skin_id)._path)
        )

    def get_current_theme(self):
        theme_id = self.config.widget_theme
        if theme_id == 'use.the.fucking.global.settings.and.suck.my.Dick':
            theme_id = self.__melange_ref__().config.default_theme
        return self.__melange_ref__().themes.get_by_id(theme_id)


    def get_tmp(self):
        return self.instance.get_tmp()


    def begin_move(self):

        def update(source, state):
            self.window.set_opacity(1 - state * .5)

        t = cream.gui.Timeline(500, cream.gui.CURVE_SINE)
        t.connect('update', update)
        t.run()

        self.emit('begin-move')

        self.state = STATE_MOVE
        self.move()


    def end_move(self):

        def update(source, state):
            self.window.set_opacity(.5 + state * .5)

        t = cream.gui.Timeline(500, cream.gui.CURVE_SINE)
        t.connect('update', update)
        t.run()

        self.emit('end-move')

        self.state = STATE_VISIBLE


    def move(self):

        def move_cb(old_x, old_y):
            new_x, new_y = self.display.get_pointer()[1:3]
            move_x = new_x - old_x
            move_y = new_y - old_y

            if self.state == STATE_MOVE:
                self.emit('move-request', move_x, move_y)
                gobject.timeout_add(MOVE_TIMESTEP, move_cb, new_x, new_y)

        move_cb(*self.display.get_pointer()[1:3])


    def load(self):

        self.instance = WidgetInstance(self)

        self.instance.connect('show-config-dialog-request', lambda *args: self.config.show_dialog())
        self.instance.connect('show-about-dialog-request', lambda *args: self.about_dialog.show_all())
        self.instance.connect('resize-request', self.resize_request_cb)
        self.instance.connect('remove-request', lambda *args: self.emit('remove-request'))
        self.instance.connect('reload-request', lambda *args: self.reload())
        self.instance.connect('focus-request', self.focus_request_cb)
        self.instance.connect('begin-move-request', self.begin_move_request_cb)
        self.instance.connect('end-move-request', self.end_move_request_cb)

        view = self.instance.get_view()
        self.window.add(view)


    def begin_move_request_cb(self, source):

        self.begin_move()


    def end_move_request_cb(self, source):

        self.end_move()


    def resize_request_cb(self, widget_instance, width, height):

        self.window.set_size_request(width, height)
        self.window.resize(width, height)


    def focus_request_cb(self, source):

        self.window.set_property('accept-focus', True)
        self.window.present()


    def reload(self):
        """ Reload the widget. Really? Yeah. """

        def go_on():
            view = self.instance.get_view()
            self.window.remove(view)

            del self.instance

            self.load()
            self.show()

        self.hide().connect('completed', lambda *args: go_on())


    def show(self):
        """ Show the widget. """

        self.window.set_opacity(0)
        self.window.show_all()

        def update(source, state):
            self.window.set_opacity(state)

        t = cream.gui.Timeline(500, cream.gui.CURVE_SINE)
        t.connect('update', update)
        t.run()

        return t


    def hide(self):
        """ Hide the widget. """

        def update(source, state):
            self.window.set_opacity(1 - state)
            if state == 1:
                self.window.hide()

        t = cream.gui.Timeline(500, cream.gui.CURVE_SINE)
        t.connect('update', update)
        t.run()

        return t


    def remove(self):
        """ Close the widget window and emit 'remove' signal. """

        self.hide()

        self.config.save()

        self.window.destroy()
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

        return self.window.get_position()


    def set_position(self, x, y):
        """
        Set the position of the widget.

        :param x: The x-coordinate.
        :param y: The y-coordinate.

        :type x: `int`
        :type y: `int`
        """

        self.window.move(x, y)


    def configuration_value_changed_cb(self, source, key, value):

        if key == 'widget_theme':
            self.reload()


    @cached_property
    def about_dialog(self):
        """ Show the 'About' dialog. """

        about_dialog = gtk.AboutDialog()
        about_dialog.connect('response', lambda *x: self.about_dialog.hide())
        about_dialog.connect('delete-event', lambda *x: True)

        about_dialog.set_name(self.context.manifest['name'])
        about_dialog.set_authors(self.context.manifest['authors'])
        if self.context.manifest.get('icon'):
            icon_path = os.path.join(self.context.working_directory, self.context.manifest['icon'])
            icon_pb = gtk.gdk.pixbuf_new_from_file(icon_path).scale_simple(64, 64, gtk.gdk.INTERP_HYPER)
            about_dialog.set_logo(icon_pb)
        about_dialog.set_comments(self.context.manifest['description'])

        return about_dialog


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
        }
