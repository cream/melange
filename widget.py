import os.path

import random
import hashlib

import gtk
import cairo
import webkit

import cream
import cream.config
from cream.util import urljoin_multi

class SkinMetaData(cream.MetaData):
    def __init__(self, path):
        cream.MetaData.__init__(self, path)


class WidgetMetaData(cream.MetaData):
    def __init__(self, path):
        cream.MetaData.__init__(self, path)


class WidgetConfiguration(cream.config.Configuration): # TODO: Move to cream.contrib.melange
    x_position = cream.config.fields.IntegerField(hidden=True, default=100)
    y_position = cream.config.fields.IntegerField(hidden=True, default=100)


class WidgetBase(cream.WithConfiguration): # TODO: Merge into Widget.
    def __init__(self):
        cream.WithConfiguration.__init__(self)

    def _load_config(self, base_path=None):
        if os.path.exists(os.path.join(self.meta['path'], 'config.py')):
            # we have a custom config.py module, so use it:
            return cream.WithConfiguration._load_config(self, self.meta['path'])
        else:
            # we don't have a custom configuration module, so we use the
            # standard melange configuration:
            return WidgetConfiguration(basedir=self.meta['path'])



class Widget(WidgetBase):

    def __init__(self, meta):

        WidgetBase.__init__(self)

        self.meta = meta

        self.instance = hashlib.sha256(str(random.getrandbits(100))).hexdigest()

        skin_dir = os.path.join(self.meta['path'], 'skins')
        skns = SkinMetaData.scan(skin_dir, type='melange.widget.skin')
        self.skins = {}

        for s in skns:
            self.skins[s['name']] = s


        self.about_dialog = gtk.AboutDialog()
        self.about_dialog.connect('response', lambda *x: self.about_dialog.hide())
        self.about_dialog.connect('delete-event', lambda *x: True)

        self.about_dialog.set_name(self.meta['name'])
        self.about_dialog.set_authors([self.meta['author']])
        if self.meta.has_key('icon'):
            icon_path = os.path.join(self.meta['path'], self.meta['icon'])
            icon_pb = gtk.gdk.pixbuf_new_from_file(icon_path).scale_simple(64, 64, gtk.gdk.INTERP_HYPER)
            self.about_dialog.set_logo(icon_pb)
        self.about_dialog.set_comments(self.meta['comment'])

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
        self.window.set_colormap(self.window.get_screen().get_rgba_colormap())

        self.view = webkit.WebView()
        self.view.set_transparent(True)

        self.bin = gtk.EventBox()
        self.bin.add(self.view)

        self.view.connect('button-press-event', self.clicked_cb)

        self.window.add(self.bin)

        item_remove = gtk.ImageMenuItem(gtk.STOCK_REMOVE)
        item_remove.connect('activate', lambda *x: self.close())

        item_about = gtk.ImageMenuItem(gtk.STOCK_ABOUT)
        item_about.connect('activate', lambda *x: self.about_dialog.show_all())

        self.menu = gtk.Menu()
        self.menu.append(item_remove)
        self.menu.append(item_about)
        self.menu.show_all()

        # TODO: Move position handling to Melange itself.
        self.set_position(self.config.x_position, self.config.y_position)


    def close(self):

        self.finalize()
        self.window.destroy()


    def __del__(self):
        raise ItWorks() # never called


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

        skin_url = urljoin_multi('http://127.0.0.1:8080', 'widgets', self.instance, 'Default', 'index.html')
        self.view.open(skin_url)
        self.window.show_all()


    def get_position(self):
        return self.window.get_position()

    def set_position(self, x, y):
        return self.window.move(x, y)

    def finalize(self):
        self.config.x_position, self.config.y_position = self.get_position()
