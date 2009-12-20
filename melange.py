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

import gtk
import cairo

import os.path

import cream
import cream.ipc

import webkit

gtk.gdk.threads_init()

class SkinMetaData(cream.MetaData):
    def __init__(self, path):
        cream.MetaData.__init__(self, path)


class WidgetMetaData(cream.MetaData):
    def __init__(self, path):
        cream.MetaData.__init__(self, path)


class Widget:

    def __init__(self, meta):

        self.meta = meta

        skin_dir = os.path.join(os.path.dirname(self.meta['path']), 'skins')
        skns = SkinMetaData.scan(skin_dir, type='melange.widget.skin')
        self.skins = {}

        for s in skns:
            self.skins[s['name']] = s

        self.window = gtk.Window()
        self.window.stick()
        self.window.set_keep_below(True)
        self.window.set_type_hint(gtk.gdk.WINDOW_TYPE_HINT_UTILITY)
        self.window.set_skip_pager_hint(True)
        self.window.set_skip_taskbar_hint(True)
        self.window.set_decorated(False)
        self.window.set_app_paintable(True)
        self.window.connect('expose-event', self.expose_cb)
        self.window.set_colormap(self.window.get_screen().get_rgba_colormap())

        self.view = webkit.WebView()
        self.view.set_transparent(True)

        file = os.path.join(os.path.dirname(self.skins['Default']['path']), 'index.html')
        self.view.open(file)

        self.bin = gtk.EventBox()
        self.bin.add(self.view)

        self.view.connect('button-press-event', self.clicked_cb)

        self.window.add(self.bin)

        item_remove = gtk.ImageMenuItem(gtk.STOCK_REMOVE)
        item_remove.connect('activate', lambda *x: self.close())

        self.menu = gtk.Menu()
        self.menu.append(item_remove)
        self.menu.append(gtk.ImageMenuItem(gtk.STOCK_REFRESH))
        self.menu.append(gtk.SeparatorMenuItem())
        self.menu.append(gtk.ImageMenuItem(gtk.STOCK_ABOUT))
        self.menu.show_all()


    def close(self):

        self.window.destroy()
        del self


    def get_position(self):

        return self.window.get_position()


    def clicked_cb(self, source, event):

        if event.button == 3:
            self.menu.popup(None, None, None, event.button, event.get_time())
            return True


    def expose_cb(self, source, event):

        ctx = source.window.cairo_create()

        ctx.set_operator(cairo.OPERATOR_SOURCE)
        ctx.set_source_rgba(0, 0, 0, 0)
        ctx.paint()


    def show(self):
        self.window.show_all()


class Melange(cream.Module):

    __ipc_domain__ = 'org.cream.melange'

    def __init__(self):

        cream.Module.__init__(self)

        wdgs = WidgetMetaData.scan('widgets', type='melange.widget')
        self.widgets = {}

        for w in wdgs:
            self.widgets[w['hash']] = w


    @cream.ipc.method('s', '')
    def load_widget(self, name):

        self.messages.debug("Loading widget...")

        w = Widget(self.widgets[name])
        w.show()


    @cream.ipc.method('', 'a{sa{ss}}')
    def list_widgets(self):

        return self.widgets


melange = Melange()
melange.main()
