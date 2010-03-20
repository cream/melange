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
from cream.contrib.melange.api import APIS

from httpserver import HOST, PORT


class WidgetAPI(object):
    def __init__(self, widget):
        self.widget = widget

    def debug(self, message):
        print "DEBUG: %s: %s" % (self.widget.meta['name'], message)


class Widget(gobject.GObject, cream.Component):

    __gtype_name__ = 'Widget'
    __gsignals__ = {
        'position-changed': (gobject.SIGNAL_RUN_LAST, gobject.TYPE_NONE, (gobject.TYPE_INT, gobject.TYPE_INT)),
        'remove': (gobject.SIGNAL_RUN_LAST, gobject.TYPE_NONE, ()),
        'reload' : (gobject.SIGNAL_RUN_LAST, gobject.TYPE_NONE, ())
    }

    _widget_size = None
    _widget_element = None

    def __init__(self, meta):

        gobject.GObject.__init__(self)
        cream.base.Component.__init__(self)

        self.meta = meta

        self.instance = 'Cream_%s' % random_hash(bits=100)

        skin_dir = os.path.join(self.meta['path'], 'skins')
        self.skins = cream.meta.MetaDataDB(skin_dir, type='melange.widget.skin')

        self.build_ui()
        self.init_api()


    def build_ui(self):

        # Setting up the Widget's window...
        self.window = gtk.Window()
        self.window.stick()
        self.window.set_keep_below(True)
        self.window.set_type_hint(gtk.gdk.WINDOW_TYPE_HINT_UTILITY)
        self.window.set_skip_pager_hint(True)
        self.window.set_skip_taskbar_hint(True)
        self.window.set_decorated(False)
        self.window.set_app_paintable(True)
        self.window.set_resizable(False)
        self.window.set_default_size(10, 10)
        self.window.connect('expose-event', self.expose_cb)
        self.window.connect('configure-event', self._update_position)
        self.window.set_colormap(self.window.get_screen().get_rgba_colormap())

        # Initializing the WebView...
        self.view = webkit.WebView()
        self.view.set_transparent(True)

        # Creating container for receiving events:
        self.bin = gtk.EventBox()
        self.bin.add(self.view)

        # Connecting to signals:
        self.view.connect('expose-event', self.resize_cb)
        self.view.connect('button-press-event', self.clicked_cb)
        self.view.connect('new-window-policy-decision-requested', self.navigation_request_cb)
        self.view.connect('navigation-policy-decision-requested', self.navigation_request_cb)

        self.window.add(self.bin)

        # Building context menu:
        item_reload = gtk.ImageMenuItem(gtk.STOCK_REFRESH)
        item_reload.get_children()[0].set_label("Reload")
        item_reload.connect('activate', lambda *x: self.reload())

        item_remove = gtk.ImageMenuItem(gtk.STOCK_REMOVE)
        item_remove.connect('activate', lambda *x: self.close())

        item_about = gtk.ImageMenuItem(gtk.STOCK_ABOUT)
        item_about.connect('activate', lambda *x: self.about_dialog.show_all())

        self.menu = gtk.Menu()
        self.menu.append(item_reload)
        self.menu.append(item_remove)
        self.menu.append(item_about)
        self.menu.show_all()


    def init_api(self):

        # Creating JavaScript context...
        self.js_context = jscore.JSContext(self.view.get_main_frame().get_global_context()).globalObject

        # Setting up JavaScript API...
        self.js_context.widget = WidgetAPI(self)

        custom_api_file = os.path.join(self.meta['path'], '__init__.py')
        if os.path.isfile(custom_api_file):
            sys.path.insert(0, self.meta['path'])
            imp.load_module(
                'custom_api_{0}'.format(self.instance),
                open(custom_api_file),
                custom_api_file,
                ('.py', 'r', imp.PY_SOURCE)
            )
            for name, value in APIS[custom_api_file].iteritems():
                self.js_context.widget.__setattr__(name, value(self))
            del sys.path[0]


    def close(self):
        """ Close the widget window and emit 'remove' signal. """

        self.window.destroy()
        self.emit('remove')


    def show(self):
        """ Show the widget. """

        skin_url = urljoin_multi('http://{0}:{1}'.format(HOST, PORT), 'widgets',
                                 self.instance, 'Default', 'index.html')
        self.view.open(skin_url)
        self.window.show_all()


    def reload(self):
        """ Reload the widget. Really? Yeah. """

        self.emit('reload')


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

        return self.window.move(x, y)


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

        self.emit('position-changed', event.x, event.y)


    def clicked_cb(self, source, event):
        """ Handle clicking on the widget (e. g. by showing context menu). """

        if event.button == 3:
            self.menu.popup(None, None, None, event.button, event.get_time())
            return True


    def expose_cb(self, source, event):
        """ Clear the widgets background. """

        ctx = source.window.cairo_create()

        ctx.set_operator(cairo.OPERATOR_SOURCE)
        ctx.set_source_rgba(0, 0, 0, 0)
        ctx.paint()


    @cached_property
    def widget_element(self):
        # TODO: Can we eliminate that ugly inices-iterating-loop and use
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
    widget_element.non_none = True

    def resize_cb(self, widget, event, *args):
        """ Resize the widget properly... """
        if self.widget_element:
            width = int(self.widget_element.offsetWidth)
            height = int(self.widget_element.offsetHeight)
            if not self._widget_size == (width, height):
                self._widget_size = (width, height)
                self.window.set_size_request(width, height)
                self.window.resize(width, height)


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
