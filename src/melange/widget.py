import os
import urlparse

from gi.repository import Gtk as gtk, Gdk as gdk, GObject as gobject, WebKit as webkit

import cream
import cream.util
import cream.config
import cream.manifest

from gpyconf.fields import MultiOptionField


from melange.common import (STATE_NONE, STATE_MOVING, MOUSE_BUTTON_MIDDLE,
                            MOUSE_BUTTON_RIGHT, MOVE_TIMESTEP)


class WidgetConfiguration(cream.config.Configuration):

    def __init__(self, scheme_path, path, skins, themes):

        cream.config.Configuration.__init__(self, scheme_path, path, read=False)

        self._add_field(
            'skin',
            MultiOptionField('Skin',
                section='Appearance',
                options=((s['id'], s['name']) for s in skins.manifests.values())
            )
        )

        options = [('use.the.fucking.global.settings', 'Use global settings')]
        options += [(t['id'], t['name']) for t in themes.manifests.values()]
        self._add_field(
            'theme',
            MultiOptionField('Theme',
                section='Appearance',
                options=options
            )
        )

        self.read()



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
        self.state = STATE_NONE

        webkit.WebView.__init__(self)
        gobject.GObject.__init__(self)

        self.set_transparent(True)

        settings = self.get_settings()
        settings.set_property('enable-plugins', False)
        self.set_settings(settings)

        self.connect('button-press-event', self.button_press_cb)
        self.connect('button-release-event', self.button_release_cb)

        skin_url = self.widget_ref.get_skin_path()
        self.skin_url = os.path.join(skin_url, 'index.html')
        self.load_uri('file://' + self.skin_url)

        self.connect('resource-request-starting', self.dispatch_resource)
        self.connect('navigation-policy-decision-requested', self.navigation_request_cb)

    def dispatch_resource(self, view, frame, resource, request, response):

        scheme, _, path, _, query, _ = urlparse.urlparse(request.get_uri())

        class HandlerMissing(Exception): pass

        if path.startswith('/widget'):
            raise HandlerMissing()
        elif path.startswith('/theme'):
            path = path[7:] # remove /theme/
            path = os.path.join(self.widget_ref.get_theme_path(), path)
        elif path.startswith('/data'):
            raise HandlerMissing()
        elif path.startswith('/common'):
            path = path[8:] # remove /common/
            path = os.path.join(self.widget_ref.common_path, path)
        elif not os.path.exists(path):
            print 'Ignoring ' + path
            return

        request.set_uri('file://' + path)


    def navigation_request_cb(self, view, frame, request, action, decision):

        print 'nav'
        scheme, _, path, _, query, _ = urlparse.urlparse(request.get_uri())

        print scheme, path, query

        decision.ignore()
        return True




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

    def __init__(self, path, themes, theme, common_path):

        gobject.GObject.__init__(self)
        cream.Component.__init__(self, path=path)

        self.instance_id = cream.util.random_hash()[:10]

        self.themes = themes
        self.theme = theme
        self.common_path = common_path

        self.position = (0, 0)

        skin_dir = os.path.join(self.context.working_directory, 'data', 'skins')
        self.skins = cream.manifest.ManifestDB(skin_dir, 
            type='org.cream.melange.Skin'
        )

        scheme_path = os.path.join(self.context.get_path(), 
            'configuration/scheme.xml'
        )
        path = os.path.join(self.context.get_user_path(), 'configuration/')

        self.config = WidgetConfiguration(scheme_path, path, self.skins, self.themes)
        self.config.connect('field-value-changed', self.configuration_value_changed_cb)


        self.load()

    def load(self):

        self.view = WidgetView(self)
        self.view.connect('begin-move', lambda *x: self.view.move())
        self.view.connect('show-config-dialog-request', 
            lambda *x: self.config.show_dialog()
        )


    def get_position(self):
        return self.position

    def set_position(self, x, y):
        self.position = (x, y)


    def get_theme_path(self):

        theme_id = self.config.theme
        if theme_id == 'use.the.fucking.global.settings':
            theme_id = self.theme['id']

        return os.path.dirname(self.themes.get_by_id(theme_id)._path)


    def get_skin_path(self):

        return os.path.join(
            self.context.working_directory,
            'skins',
            os.path.dirname(self.skins.get_by_id(self.config.skin)._path)
        )


    def destroy(self):

        self.view.widget_ref = None
        self.view.destroy()

    def configuration_value_changed_cb(self, source, key, value):
        if key in ('theme', 'skin'):
            self.view.emit('reload-request')
