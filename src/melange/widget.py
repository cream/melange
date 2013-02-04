import os
import urlparse

from gi.repository import Gtk as gtk, Gdk as gdk, GObject as gobject, WebKit as webkit

import cream
import cream.util
import cream.manifest

from melange.common import (STATE_NONE, STATE_MOVING, MOUSE_BUTTON_MIDDLE,
                            MOUSE_BUTTON_RIGHT, MOVE_TIMESTEP)


class WidgetView(webkit.WebView, gobject.GObject):
    __gsignals__ = {
        'move-request': (gobject.SignalFlags.RUN_LAST, None, (int, int)),
        'begin-move': (gobject.SignalFlags.RUN_LAST, None, ()),
        'raise-request': (gobject.SignalFlags.RUN_LAST, None, ()),
        'show-config-dialog-request': (gobject.SignalFlags.RUN_LAST, None, ()),
        'reload-request': (gobject.SignalFlags.RUN_LAST, None, ()),
        'remove-request': (gobject.SignalFlags.RUN_LAST, None, ()),
        'show-about-dialog-request': (gobject.SignalFlags.RUN_LAST, None, ())
    }

    def __init__(self, widget):

        self.widget_ref = widget # XXX Circular reference
        self.position = (0, 0)
        self.state = STATE_NONE

        webkit.WebView.__init__(self)
        gobject.GObject.__init__(self)

        self.set_transparent(True)

        settings = self.get_settings()
        settings.set_property('enable-plugins', False)
        self.set_settings(settings)

        self.connect('resource-request-starting', self.dispatch_resource)
        self.connect('button-press-event', self.button_press_cb)
        self.connect('button-release-event', self.button_release_cb)

        skin_url = self.widget_ref.get_skin_path()
        self.skin_url = os.path.join(skin_url, 'index.html')
        self.open(self.skin_url)


    def dispatch_resource(self, view, frame, resource, request, response):

        scheme, _, path, _, query, _ = urlparse.urlparse(request.get_uri())

        if path.startswith('/widget'):
            print 'widget file'
        elif path.startswith('/theme'):
            path = path[7:] # remove /theme/
            path = os.path.join(self.widget_ref.theme_path, path)
        elif path.startswith('/data'):
            print 'data file'

        request.set_uri('file://' + path)


    def button_press_cb(self, view, event):

        self.emit('raise-request')

        if event.button == MOUSE_BUTTON_MIDDLE:
            self.state = STATE_MOVING
            self.emit('begin-move')
            return True
        elif event.button == MOUSE_BUTTON_RIGHT:
            self.menu.popup(None, None, None, None, event.button, event.get_time())
            return True


    def button_release_cb(self, view, event):
        if event.button == MOUSE_BUTTON_MIDDLE:
            self.state = STATE_NONE
            return True


    def move(self):
        display = gdk.Display.get_default()

        def move_cb(old_x, old_y):
            new_x, new_y = display.get_pointer()[1:3]

            move_x = new_x - old_x
            move_y = new_y - old_y

            if self.state == STATE_MOVING:
                self.emit('move-request', move_x, move_y)
                gobject.timeout_add(MOVE_TIMESTEP, move_cb, new_x, new_y)

        move_cb(*display.get_pointer()[1:3])



    def get_position(self):
        return self.position

    def set_position(self, x, y):
        self.position = (x, y)



    @cream.util.cached_property
    def menu(self):

        item_configure = gtk.ImageMenuItem(gtk.STOCK_PREFERENCES)
        item_configure.get_children()[0].set_label("Configure")
        item_configure.connect('activate', lambda *x: self.emit('show-config-dialog-request'))

        item_reload = gtk.ImageMenuItem(gtk.STOCK_REFRESH)
        item_reload.get_children()[0].set_label("Reload")
        item_reload.connect('activate', lambda *x: self.emit('reload-request'))

        item_remove = gtk.ImageMenuItem(gtk.STOCK_REMOVE)
        item_remove.get_children()[0].set_label("Remove")
        item_remove.connect('activate', lambda *x: self.emit('remove-request'))

        item_about = gtk.ImageMenuItem(gtk.STOCK_ABOUT)
        item_about.get_children()[0].set_label("About")
        item_about.connect('activate', lambda *x: self.emit('show-about-dialog-request'))

        menu = gtk.Menu()
        menu.append(item_configure)
        menu.append(item_reload)
        menu.append(item_remove)
        menu.append(item_about)
        menu.show_all()

        return menu




class Widget(gobject.GObject, cream.Component):

    def __init__(self, path, theme_path):

        gobject.GObject.__init__(self)
        cream.Component.__init__(self, path=path)

        self.instance_id = cream.util.random_hash(bits=100)[:10]

        self.size = (0, 0)
        self.theme_path = theme_path

        skin_dir = os.path.join(self.context.working_directory, 'data', 'skins')
        self.skins = cream.manifest.ManifestDB(skin_dir, 
            type='org.cream.melange.Skin'
        )

        self.view = WidgetView(self)

        self.view.connect('begin-move', lambda *x: self.view.move())



    def set_theme_path(self, theme_path):
        self.theme_path = theme_path
        # XXX reload



    def get_skin_path(self):

        # XXX Config

        return os.path.join(
            self.context.working_directory,
            'skins',
            os.path.dirname(self.skins.manifests.values()[0]._path)
        )


    def destroy(self):

        self.view.widget_ref = None
        self.view.destroy()

