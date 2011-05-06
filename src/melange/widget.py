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

import sys
import os
import imp
import shutil
import weakref

import gobject
import gtk
import webkit
import javascriptcore as jscore
import webbrowser

import cream.base
import cream.gui
from cream.util import cached_property, random_hash, extend_querystring
from melange.api import APIS, PyToJSInterface

from cream.config import Configuration
from gpyconf.fields import MultiOptionField

from common import HTTPSERVER_BASE_URL, \
                   STATE_MOVE, STATE_NONE, STATE_VISIBLE, \
                   MOUSE_BUTTON_LEFT, MOUSE_BUTTON_MIDDLE, MOUSE_BUTTON_RIGHT, \
                   MOVE_TIMESTEP, OPACITY_MOVE

class WidgetAPI(object):
    pass


class WidgetConfiguration(Configuration):

    def __init__(self, scheme_path, path, skins, themes):

        Configuration.__init__(self, scheme_path, path, read=False)

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

        self.config = WidgetConfigurationProxy(self.widget_ref().config)

        self._size = (0, 0)
        self.state = STATE_NONE

        self.messages = cream.log.Messages()

        # Initializing the WebView...
        self.view = webkit.WebView()
        self.view.set_transparent(True)

        settings = self.view.get_settings()
        settings.set_property('enable-plugins', False)
        self.view.set_settings(settings)

        # Connecting to signals:
        self.view.connect('expose-event', self.resize_cb)
        self.view.connect('button-press-event', self.button_press_cb)
        self.view.connect('button-release-event', self.button_release_cb)
        self.view.connect('new-window-policy-decision-requested', self.navigation_request_cb)
        self.view.connect('navigation-policy-decision-requested', self.navigation_request_cb)
        self.view.connect('resource-request-starting', self.resource_request_cb)

        # Initialize drag and drop...
        self.view.drag_dest_set(0, [], 0)
        self.view.connect('drag_motion', self.drag_motion_cb)
        self.view.connect('drag_drop', self.drag_drop_cb)
        self.view.connect('drag_data_received', self.drag_data_cb)

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

        self.js_context.log = self.log

        # Set up JavaScript API...
        self.js_context._python = WidgetAPI()
        self.js_context._python.init = self.init_api
        self.js_context._python.init_config = self.init_config

        self.js_context.melange = WidgetAPI()
        self.js_context.melange.show_add_widget_dialog = self.widget_ref().__melange_ref__().add_widget
        self.js_context.melange.show_settings_dialog = self.widget_ref().__melange_ref__().config.show_dialog

        skin_url = HTTPSERVER_BASE_URL + '/widget/index.html'
        self.view.open(skin_url)

        gobject.timeout_add(250, self.apply_hack_to_avoid_problems_with_caching)


    def drag_motion_cb(self, widget, context, x, y, time):
        context.drag_status(gtk.gdk.ACTION_MOVE, time)
        return True


    def drag_drop_cb(self, widget, context, x, y, time):
        if 'text/uri-list' in context.targets:
            widget.drag_get_data(context, 'text/uri-list', time)
        return True


    def drag_data_cb(self, widget, context, x, y, data, info, time):

        def check_for_drop_handlers(e):
            if not isinstance(e.retrieve('events'), jscore.JSObject) or not 'drop' in e.retrieve('events'):
                return False
            return True

        e = self.js_context.document.elementFromPoint(x, y)

        while not check_for_drop_handlers(e):
            e = e.getParent()
            if isinstance(e, jscore.NullType):
                break
        else:
            e.fireEvent('drop', data.get_uris())
            context.finish(True, False, time)


    # evil black magic, but it fixes caching problems
    # adds some randomness to each link, style, script, whatsoever
    def apply_hack_to_avoid_problems_with_caching(self):
        if hasattr(self.js_context.document.head, 'childNodes'):
            for element in self.js_context.document.head.childNodes.values():
                if hasattr(element, 'src') and element.src:
                    url = extend_querystring(element.src, {'query_id': random_hash()[:5]})
                    element.src = url
                elif hasattr(element, 'href') and element.href:
                    url = extend_querystring(element.href, {'query_id': random_hash()[:5]})
                    element.href = url
            return False

    def log(self, msg):
        self.messages.debug(msg)


    def get_view(self):
        return self.view


    def init_config(self):
        # Register the JavaScript configuration event callback for *all*
        # configuration events. Further dispatching then *happens in JS*.
        self.js_context.widget.config._python_config = self.config
        self.config.connect('all', self.js_context.widget.config.on_config_event)


    def init_api(self):

        custom_api_file = os.path.join(self.widget_ref().context.get_path(), '__init__.py')
        if os.path.isfile(custom_api_file):
            sys.path.insert(0, self.widget_ref().context.get_path())
            imp.load_module(
                'custom_api_{0}'.format(self.widget_ref().instance_id),
                open(custom_api_file),
                custom_api_file,
                ('.py', 'r', imp.PY_SOURCE)
            )
            for name, value in APIS[custom_api_file].iteritems():
                c = value
                c._js_ctx = self.js_context
                c._data_path = self.widget_ref().get_data_path()
                c.context = self.widget_ref().context
                c.config = self.config.config_ref()
                c = c()
                i = PyToJSInterface(c)
                self.js_context.widget.api.__setattr__(name, i)
            del sys.path[0]


    def resource_request_cb(self, view, frame, resource, request, response):
        uri = request.get_property('uri')
        uri = extend_querystring(uri, {'instance': self.widget_ref().instance_id})
        request.set_property('uri', uri)


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
                                          skins=self.skins.by_id,
                                          themes=self.__melange_ref__().themes.by_id)
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
            os.path.dirname(self.skins.get_by_id(skin_id)._path)
        )

    def get_current_theme(self):
        theme_id = self.config.widget_theme
        if theme_id == 'use.the.fucking.global.settings.and.suck.my.Dick':
            theme_id = self.__melange_ref__().config.default_theme
        return self.__melange_ref__().themes.get_by_id(theme_id)


    def begin_move(self):

        self.emit('begin-move')

        self.state = STATE_MOVE
        self.move()


    def end_move(self):

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
        self.instance.connect('raise-request', lambda *args: self.emit('raise-request'))
        self.instance.connect('reload-request', lambda *args: self.reload())
        self.instance.connect('focus-request', self.focus_request_cb)
        self.instance.connect('begin-move-request', self.begin_move_request_cb)
        self.instance.connect('end-move-request', self.end_move_request_cb)


    def begin_move_request_cb(self, source):

        self.begin_move()


    def end_move_request_cb(self, source):

        self.end_move()


    def resize_request_cb(self, widget_instance, width, height):
        pass


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

        about_dialog = gtk.AboutDialog()
        about_dialog.connect('response', lambda *x: self.about_dialog.hide())
        about_dialog.connect('delete-event', lambda *x: True)

        about_dialog.set_name(self.context.manifest['name'])

        authors = ['{0} <{1}>'.format(author.get('name'),author.get('mail'))
                            for author in self.context.manifest['authors']]
        about_dialog.set_authors(authors)

        if self.context.manifest.get('icon'):
            icon = gtk.gdk.pixbuf_new_from_file(self.context.manifest['icon'])
            icon = icon.scale_simple(64, 64, gtk.gdk.INTERP_HYPER)
            about_dialog.set_logo(icon)
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
            'profile': self.config.profiles.active.name
        }
