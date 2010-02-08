import os.path
import imp

import gobject
import gtk
import webkit
import javascriptcore as jscore

import cream
import cream.meta
from cream.util import urljoin_multi, cached_property, random_hash

from httpserver import HOST, PORT

import webbrowser

from cream.contrib.melange.api import APIS


class SkinMetaData(cream.meta.MetaData):
    pass

class WidgetMetaData(cream.meta.MetaData):
    pass


class WidgetAPI(object):

    def debug(self, message):
        print message


class Widget(gobject.GObject, cream.Configurable):

    __gtype_name__ = 'Widget'
    __gsignals__ = {
        'position-changed': (gobject.SIGNAL_RUN_LAST, gobject.TYPE_NONE, (gobject.TYPE_INT, gobject.TYPE_INT)),
        'removed': (gobject.SIGNAL_RUN_LAST, gobject.TYPE_NONE, ()),
        'reload' : (gobject.SIGNAL_RUN_LAST, gobject.TYPE_NONE, ())
        }

    def __init__(self, meta):

        gobject.GObject.__init__(self)
        cream.Configurable.__init__(self)

        self.meta = meta

        self.instance = 'Cream_%s' % random_hash(bits=100)

        skin_dir = os.path.join(self.meta['path'], 'skins')
        self.skins = dict((skin['name'], skin) for skin in
                          SkinMetaData.scan(skin_dir, type='melange.widget.skin'))

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
        self.js_context.widget = WidgetAPI()

        custom_api_file = os.path.join(self.meta['path'], '__init__.py')
        if os.path.isfile(custom_api_file):
            imp.load_module('custom_api', open(custom_api_file), custom_api_file, ('.py', 'rb', imp.PY_SOURCE))
            for a in APIS[custom_api_file].iteritems():
                self.js_context.widget.__setattr__(a[0], a[1](self))


    def navigation_request_cb(self, view, frame, request, action, decision):

        uri = request.get_uri()

        if not uri.startswith('http://{0}:{1}/'.format(HOST, PORT)):
            webbrowser.open(uri)
            return True


    @cached_property
    def about_dialog(self):
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
        self.emit('position-changed', event.x, event.y)


    def close(self):
        self.window.destroy()
        self.emit('removed')

    def clicked_cb(self, source, event):

        if event.button == 3:
            self.menu.popup(None, None, None, event.button, event.get_time())
            return True

    def expose_cb(self, source, event):
        ctx = source.window.cairo_create()

        ctx.set_operator(0x1) # 0x1 = cairo.OPERATOR_SOURCE
        ctx.set_source_rgba(0, 0, 0, 0)
        ctx.paint()


    def show(self):
        skin_url = urljoin_multi('http://{0}:{1}'.format(HOST, PORT), 'widgets',
                                 self.instance, 'Default', 'index.html')
        self.view.open(skin_url)
        self.window.show_all()


    def reload(self):
        self.emit('reload')


    def get_position(self):
        return self.window.get_position()

    def set_position(self, x, y):
        return self.window.move(x, y)

    def __xmlserialize__(self):
        # TODO: Save hash rather than name here?
        return {
            'name' : self.meta['name'],
            'x'    : self.get_position()[0],
            'y'    : self.get_position()[1],
        }
