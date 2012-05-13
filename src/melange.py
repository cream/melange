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
from melange.dialogs import AddWidgetDialog
from melange.common import MOUSE_BUTTON_RIGHT


def yield_available_widgets():

    for path in cream.path.CREAM_DIRS:
        path = os.path.join(path, 'org.cream.Melange/data/widgets')
        if os.path.isdir(path):
            for name in os.listdir(path):
                yield name, os.path.join(path, name)


def yield_available_themes():

    for path in cream.path.CREAM_DIRS:
        path = os.path.join(path, 'org.cream.Melange/data/themes')
        if os.path.isdir(path):
            for name in os.listdir(path):
                yield name, os.path.join(path, name)



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

        cream.Module.__init__(self, 'org.cream.Melange')

        self.config = gio.Settings('org.cream.melange1', '/test/')

        self.widgets = WidgetManager()

        self.server = Server(self.widgets, self.common_path)
        self.server.start()

        self.window = MelangeWindow()
        self.window.connect('delete-event', lambda *x: self.quit())
        self.window.connect('button-release-event', self.show_menu)
        self.window.show_all()

        # load widgets from last time
        widgets = list(self.config.get_value('widgets'))
        if widgets:
            for widget_id, path, x, y in widgets:
                self.load_widget(widget_id, path, int(x), int(y))


    def load_widget(self, widget_id, path=None, x=0, y=0):

        if path is None:
            path = self.available_widgets[widget_id]['path']

        widget = self.widgets.add_widget(widget_id, path, x, y, self.themes)
        widget.connect('remove', self.remove_widget_cb)
        widget.load()

        self.window.add_widget(widget)


    def show_dialog(self):

        self.add_widget_dialog.show()


    def show_menu(self, window, event):

        if event.button == MOUSE_BUTTON_RIGHT:
            self.menu.popup(None, None, None, None, event.button, event.get_time())


    @cached_property
    def available_widgets(self):

        widgets = {}
        for widget_id, path in yield_available_widgets():
            widgets[widget_id] = {'path': path}

        return widgets


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


    @cached_property
    def add_widget_dialog(self):

        w = []
        for widget_id, path in yield_available_widgets():
            w.append({'id': widget_id})

        dialog = AddWidgetDialog(w)
        dialog.connect('load-widget', lambda dialog, widget: self.load_widget(widget))

        return dialog


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
