#!/usr/bin/env python

import cairo
from gi.repository import (Gtk as gtk, Gdk as gdk, GObject as gobject,
                           WebKit as webkit)

from melange.gui import CompositeBin


class TransparentWindow(gtk.Window):

    def __init__(self):

        gtk.Window.__init__(self)

        display = self.get_display()
        screen = display.get_default_screen()
        width, height = screen.get_width(), screen.get_height()
        self.set_default_size(width, height)

        self.set_app_paintable(True)
        self.set_visual(self.get_screen().get_rgba_visual())
        self.connect('draw', self.draw_cb)


    def draw_cb(self, window, ctx):

        ctx.set_operator(cairo.OPERATOR_SOURCE)
        ctx.set_source_rgba(0, 0, 0, 0)
        ctx.paint()


a
class WidgetLayer(TransparentWindow):

    def __init__(self):

        TransparentWindow.__init__(self)

        self.set_events(gdk.EventMask.BUTTON_RELEASE_MASK)
        self.set_type_hint(gdk.WindowTypeHint.DESKTOP)


        self.layout = CompositeBin()
        self.add(self.layout)


        view = webkit.WebView()
        view.set_transparent(True)
        view.load_uri('file:///tmp/test.html')

        self.layout.add(view, 50, 50)




class Melange(object):

    def __init__(self):


        self.window = WidgetLayer()
        self.window.show_all()



if __name__ == '__main__':
    melange = Melange()

    mainloop = gobject.MainLoop()
    try:
        mainloop.run()
    except (KeyboardInterrupt, SystemError):
        mainloop.quit()
