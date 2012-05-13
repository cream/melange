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
import sys
import cairo


from gi.repository import GtkClutter as gtkclutter
gtkclutter.init(sys.argv)

from gi.repository import (Gtk as gtk, Gdk as gdk, GObject as gobject, Gio as gio, GLib as glib,
                           Clutter as clutter)

import cream
import cream.path
from cream.util import cached_property

from melange.widget import WidgetManager
from melange.server import Server
from melange.utils import get_screen_size



class WidgetLayer(TransparentWindow):

    def __init__(self):

def yield_available_themes():

    for path in cream.path.CREAM_DIRS:
        path = os.path.join(path, 'org.cream.Melange/data/themes')
        if os.path.isdir(path):
            for name in os.listdir(path):
                yield name, os.path.join(path, name)

        self.mode = STATE_NONE

        self.connect('leave-notify-event', self.leave_notify_cb)
        self.connect('enter-notify-event', self.enter_notify_cb)

class MelangeTheme(object):

    def __init__(self, path, name):

        self.path = path
        self.name = name.capitalize()


    def __str__(self):
        return '<MelangeTheme {0}>'.format(self.name)

    def __repr__(self):
        return str(self)



class TransparentWindow(gtk.Window):

    def __init__(self):

        gtk.Window.__init__(self)

        self.alpha = 0

        self.set_app_paintable(True)
        self.set_decorated(False)
        self.set_type_hint(gdk.WindowTypeHint.DESKTOP)

        screen = gdk.Screen.get_default()
        self.set_visual(screen.get_rgba_visual())

        self.connect('draw', self.draw_cb)


    def draw_cb(self, source, ctx):
        """ Clear the widgets background. """

        ctx.set_operator(cairo.OPERATOR_SOURCE)
        ctx.set_source_rgba(0, 0, 0, self.alpha)
        ctx.paint()



class MelangeWindow(TransparentWindow):

    def __init__(self):

        TransparentWindow.__init__(self)

        self.set_default_size(*get_screen_size())

        self.embed = gtkclutter.Embed()
        self.add(self.embed)

        self.stage = self.embed.get_stage()
        self.stage.set_use_alpha(True)
        self.stage.set_opacity(0)


    def add_widget(self, widget):

        action = clutter.DragAction()
        action.set_drag_threshold(5, 5)
        action.connect('drag-end', self.on_drag_end, widget)
        widget.actor.add_action(action)

        widget.actor.show_all()

        self.stage.add_actor(widget.actor)


    def on_drag_end(self, action, actor, x, y, modifiers, widget):

        x, y = map(int, actor.get_position())
        widget.position = (x, y)


class Melange(cream.Module):

    def __init__(self):

        WidgetLayer.__init__(self)
        self.set_type_hint(gtk.gdk.WINDOW_TYPE_HINT_DESKTOP)

        self.background = WidgetLayerCanvas(self)


class WidgetManager(gobject.GObject):

    __gtype_name__ = 'WidgetManager'
    __gsignals__ = {
        'widget-added': (gobject.SIGNAL_RUN_LAST, gobject.TYPE_NONE, (Widget,)),
        'widget-removed': (gobject.SIGNAL_RUN_LAST, gobject.TYPE_NONE, (Widget,)),
        }

    def __init__(self):

        gobject.GObject.__init__(self)

        self.screen_width = gtk.gdk.screen_width()
        self.screen_height = gtk.gdk.screen_height()

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
        self.signal_handlers[widget]['reload-request'] = widget.connect('reload-request', self.reload_request_cb)

        if x and y:
            widget.set_position(x, y) # TODO: Use own moving algorithms.

        self.primary_widget_layer.add_widget(widget)

        self.emit('widget-added', widget)


    def raise_request_cb(self, widget):

        self.primary_widget_layer.raise_widget(widget)


        self.config = gio.Settings('org.cream.melange1', '/test/')

        self.widgets = WidgetManager()

        self.server = Server(self.widgets, self.common_path)
        self.server.start()

        self.window = MelangeWindow()
        self.window.connect('delete-event', lambda *x: self.quit())
        self.window.connect('button-release-event', self.show_menu)
        self.window.show_all()

    def remove_request_cb(self, widget):

        self.remove(widget)
        self.primary_widget_layer.remove_widget(widget)
        widget.remove()


    def reload_request_cb(self, widget):

        self.primary_widget_layer.remove_widget(widget)
        widget.load()
        self.primary_widget_layer.add_widget(widget)


    def remove(self, widget):

        del self[widget.instance_id]

        widget.disconnect(self.signal_handlers[widget]['raise-request'])
        widget.disconnect(self.signal_handlers[widget]['end-move'])
        widget.disconnect(self.signal_handlers[widget]['move-request'])
        widget.disconnect(self.signal_handlers[widget]['remove-request'])

        self.emit('widget-removed', widget)

    def show_menu(self, window, event):

        if event.button == MOUSE_BUTTON_RIGHT:
            self.menu.popup(None, None, None, None, event.button, event.get_time())



    @cream.util.cached_property
    def add_widget_dialog(self):

        widgets = sorted(self.available_widgets.get(),
                          key=itemgetter('name')
        )
        return AddWidgetDialog(widgets)


    @cached_property
    def menu(self):

        item_add = gtk.ImageMenuItem(gtk.STOCK_ADD)
        item_add.get_children()[0].set_label('Add widgets')
        item_add.connect('activate', lambda *x: self.show_dialog())

        menu = gtk.Menu()
        menu.append(item_add)
        menu.show_all()

        return menu


    @cached_property
    def themes(self):

        themes = []
        for name, path in yield_available_themes():
            themes.append(MelangeTheme(path, name))

        return themes


    @cached_property
    def common_path(self):

        for path in cream.path.CREAM_DIRS:
            path = os.path.join(path, 'org.cream.Melange/data/common')
            if os.path.isdir(path):
                return path


        # Add the widget to the list of currently active widgets:
        self.widgets.add(widget, x, y)


    @cream.ipc.method('', 'a{sa{ss}}')
    def list_widgets(self):
        """
        List all available widgets.

        :return: List of widgets.
        :rtype: `list`
        """

        res = {}

        for w in self.available_widgets.get():
            res[w['id']] = {
                'name': w['name'],
                'description': '',
                'path': '',
                'id': w['id'],
                }

        return res


    @cream.ipc.method('','')
    def toggle_overlay(self):

        layer = self.widgets.primary_widget_layer
        width, height = layer.get_size()[0],layer.get_size()[1]

        if layer.get_type_hint() == gtk.gdk.WINDOW_TYPE_HINT_DESKTOP:
            def fade_out_widgets(t, state):
                layer.set_opacity(1 - state)

            def fade_in_overlay(t):
                layer.hide()

                def fade_in(t, state):
                    layer.alpha = state * 0.8
                    layer.set_opacity(state)
                    layer.window.invalidate_rect(gtk.gdk.Rectangle(0, 0, width, height), True)

                t = cream.gui.Timeline(OVERLAY_FADE_DURATION, cream.gui.CURVE_SINE)
                t.connect('update', fade_in)
                t.run()

                layer.set_type_hint(gtk.gdk.WINDOW_TYPE_HINT_DOCK)
                layer.show_all()

            t = cream.gui.Timeline(OVERLAY_FADE_DURATION/2, cream.gui.CURVE_SINE)
            t.connect('update', fade_out_widgets)
            t.connect('completed', fade_in_overlay)
            t.run()


        else:
            def fade_out_overlay(t, state):
                layer.alpha = 0.8 - state * 0.8
                layer.set_opacity(1 - state)
                layer.window.invalidate_rect(gtk.gdk.Rectangle(0, 0, width, height), True)

            def fade_in_widgets(t):
                layer.hide()


                layer.set_type_hint(gtk.gdk.WINDOW_TYPE_HINT_DESKTOP)
                layer.show_all()

            t = cream.gui.Timeline(OVERLAY_FADE_DURATION, cream.gui.CURVE_SINE)
            t.connect('update', fade_out_overlay)
            t.connect('completed', fade_in_widgets)
            t.run()


    def quit(self):

        widgets = []
        for widget in self.widgets.get_all_widgets():
            x, y = map(str, widget.position)
            widgets.append([widget.id, widget.path, x, y])

        widgets = glib.Variant('aas', widgets)
        self.config.set_value('widgets', widgets)

        self.server.stop()
        cream.Module.quit(self)


if __name__ == '__main__':
    cream.util.set_process_name('melange')
    melange = Melange()
    melange.main()
