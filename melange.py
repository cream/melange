#! /usr/bin/python
# -*- coding: utf-8 -*-

import gobject
import gtk
import cairo

import math
import os.path

import cream
import cream.ipc
import cream.util
from cream.gui import CompositeBin

import webkit

gtk.gdk.threads_init()

WIDGETS = [
    [
        "Clock Widget",
        "A simple clock for your desktop...",
        '/home/stein/clock.png',
        'file:///home/stein/Labs/Cream/dev/src/modules/melange/test/test.html'
    ],
    [
        "Test Widget",
        "Test widget for Melange...",
        '/home/stein/clock.png',
        'file:///home/stein/Labs/Cream/dev/src/modules/melange/test/test2.html'
    ]
    ]


class Widget:

    def __init__(self, path):

        self.path = path

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

        self.view.open(self.path)

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

    def __init__(self):

        cream.Module.__init__(self)

        #self.load_widget('file:///home/stein/Tests/dock.html')
        self.load_widget('file:///home/stein/Labs/Cream/dev/src/modules/melange/test/test.html')


    @cream.ipc.method('s', '')
    def load_widget(self, path):

        self.messages.debug("Loading widget...")

        w = Widget(path)
        w.show()


    @cream.ipc.method('', 'aas')
    def list_widgets(self):

        return WIDGETS


melange = Melange()
melange.main()
