import os.path

import gtk
import cairo
import webkit

import cream
import cream.config

class SkinMetaData(cream.MetaData):
    def __init__(self, path):
        cream.MetaData.__init__(self, path)


class WidgetMetaData(cream.MetaData):
    def __init__(self, path):
        cream.MetaData.__init__(self, path)


class WidgetConfiguration(cream.config.Configuration):
    x_position = cream.config.fields.IntegerField(hidden=True)
    y_position = cream.config.fields.IntegerField(hidden=True)


class Widget(object):

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

    def get_position(self):
        return self.window.get_position()
