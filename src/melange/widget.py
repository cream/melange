import os
import json
import urlparse
import webbrowser

from gi.repository import Gtk as gtk, Gdk as gdk, GObject as gobject, WebKit as webkit

import cream
import cream.util
import cream.config
import cream.manifest

from gpyconf.fields import MultiOptionField


from melange.api import import_api_file, Thread, APIS
from melange.dialogs import AboutDialog
from melange.common import (STATE_NONE, STATE_MOVING, MOUSE_BUTTON_MIDDLE,
                            MOUSE_BUTTON_RIGHT, MOVE_TIMESTEP)


USE_GLOBAL_SETTINGS = 'use.the.fucking.global.settings'


def register_scheme(scheme):
    for method in filter(lambda s: s.startswith('uses_'), dir(urlparse)):
        getattr(urlparse, method).append(scheme)

register_scheme('melange')
register_scheme('config')


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

        options = [(USE_GLOBAL_SETTINGS, 'Use global settings')]
        options += [(t['id'], t['name']) for t in themes.get_all_themes()]
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
        'show-request': (gobject.SignalFlags.RUN_LAST, None, ()),
        'move-request': (gobject.SignalFlags.RUN_LAST, None, (int, int)),
        'begin-move': (gobject.SignalFlags.RUN_LAST, None, ()),
        'show-config-dialog-request': (gobject.SignalFlags.RUN_LAST, None, ()),
        'reload-request': (gobject.SignalFlags.RUN_LAST, None, ()),
        'remove-request': (gobject.SignalFlags.RUN_LAST, None, ()),
        'show-about-dialog-request': (gobject.SignalFlags.RUN_LAST, None, ())
    }

    def __init__(self, widget):

        self.widget_ref = widget # XXX Circular reference
        self.state = STATE_NONE

        self.api = None

        webkit.WebView.__init__(self)
        gobject.GObject.__init__(self)

        self.set_transparent(True)

        settings = self.get_settings()
        settings.set_property('enable-plugins', False)
        self.set_settings(settings)

        self.connect('button-press-event', self.button_press_cb)
        self.connect('button-release-event', self.button_release_cb)

        # Initialize drag and drop...
        self.drag_dest_set(0, [], 0)
        self.connect('drag_motion', self.drag_motion_cb)
        self.connect('drag_drop', self.drag_drop_cb)
        self.connect('drag_data_received', self.drag_data_cb)

        skin_url = self.widget_ref.get_skin_path()
        self.skin_url = os.path.join(skin_url, 'index.html')
        self.load_uri('file://' + self.skin_url)

        self.connect('resource-request-starting', self.dispatch_resource)
        self.connect('navigation-policy-decision-requested', self.navigation_request_cb)
        self.connect('document-load-finished', self.document_load_finished_cb)


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

        scheme, action, path, _, query, _ = urlparse.urlparse(request.get_uri())
        query = dict(urlparse.parse_qsl(query))

        if scheme == 'melange':
            if action == 'init':
                self.init_api()
            elif action == 'call':
                method = path[1:]
                callback_id = query.pop('callback_id', None)

                arguments = []
                for key in sorted(query.keys()):
                    if key.startswith('argument_'):
                        arguments.append(query[key])

                self.handle_api_call(method, callback_id, arguments)

            decision.ignore()
        elif scheme == 'config':
            if action == 'get':
                callback_id, option = query['callback_id'], query['option']
                value = getattr(self.widget_ref.config, option)
                script = 'widget.config.invokeCallback({}, "{}");'.format(callback_id, value)
                self.execute_script(script)
            elif action == 'set':
                option, value = query['option'], query['value']
                setattr(self.widget_ref.config, option, value)
            decision.ignore()
        else:
            webbrowser.open(request.get_uri())

        return True


    def init_api(self):

        if not self.widget_ref.id in APIS:
            path = self.widget_ref.context.working_directory
            import_api_file(path, self.widget_ref.id)

        api_klass = APIS[self.widget_ref.id]
        api_klass.config = self.widget_ref.config
        api_klass.context = self.widget_ref.context
        self.api = api_klass()

        for method in self.api.get_exposed_methods():
            self.execute_script('widget.registerMethod("{}");'.format(method))
        self.execute_script('widget.main();')


    def handle_api_call(self, method_name, callback_id, arguments):

        def invoke_callback(thread, callback_id, result):
            result = json.dumps(result)
            script = 'widget.invokeCallback({}, {});'.format(callback_id, result)
            self.execute_script(script)

        method = getattr(self.api, method_name, None)
        if method is None:
            self.widget_ref.messages.error('API Method "{}" not found'.format(method_name))

        thread = Thread(method, callback_id, arguments)

        if callback_id is not None:
            thread.connect('finished', invoke_callback)

        thread.start()


    def document_load_finished_cb(self, view, frame):

        self.workaround_theme_caching()
        self.emit('show-request')

    def configuration_value_changed_cb(self, key, value):

        event = 'field-value-changed'
        script = 'widget.config.onConfigEvent("{}", "{}", "{}");'.format(event, key, value)
        self.execute_script(script)


    def button_press_cb(self, view, event):

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


    def drag_motion_cb(self, view, context, x, y, time):
        gdk.drag_status(context, gdk.DragAction.MOVE, time)
        return True


    def drag_drop_cb(self, view, context, x, y, time):

        for target in context.list_targets():
            if 'text/uri-list' in target.name():
                view.drag_get_data(context, target, time)
        return True


    def drag_data_cb(self, view, context, x, y, data, info, time):

        uris = json.dumps(data.get_uris())
        script = "widget.fireDrop({}, {}, '{}');".format(x, y, uris)
        self.execute_script(script)

        gdk.drop_finish(context, True, time)


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


    def workaround_theme_caching(self):
        """
        When we request our theme files via the /theme/ui url webkit caches
        the first file, but if we change theme, then this url points to a different
        location on disk and webkit instead loads the version from the cache.
        Solve this issue by appending a random querystring onto every link and
        script element that points to /themes/ui
        """

        self.execute_script('''
            var links = document.getElementsByTagName('link');
            for(i = 0; i < links.length; i++) {
                if(links[i].href.indexOf('/theme/ui') != -1)
                    links[i].href += '?random=' + (new Date()).getTime();
            }
            var scripts = document.getElementsByTagName('script');
            for(i = 0; i < scripts.length; i++) {
                if(scripts[i].src.indexOf('/theme/ui') != -1)
                    scripts[i].src += '?random=' + (new Date()).getTime();
            }
        ''')


class Widget(gobject.GObject, cream.Component):

    def __init__(self, widget_id, path, themes, common_path):

        gobject.GObject.__init__(self)
        cream.Component.__init__(self, path=path)

        self.id = widget_id

        self.themes = themes
        self.themes.connect('changed', self.theme_change_cb)

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
        self.view.connect('show-about-dialog-request',
            lambda *x: self.about_dialog.show()
        )


    def get_position(self):
        return self.position

    def set_position(self, x, y):
        self.position = (x, y)


    def get_theme_path(self):

        theme_id = self.config.theme
        if theme_id == USE_GLOBAL_SETTINGS:
            theme_id = self.themes.selected_theme_id

        return os.path.dirname(self.themes.get_theme(theme_id)._path)


    def get_skin_path(self):

        return os.path.join(
            self.context.working_directory,
            'skins',
            os.path.dirname(self.skins.get_by_id(self.config.skin)._path)
        )


    def destroy(self):

        if self.view.api is not None:
            self.view.api.config = None
            self.view.api = None
        self.view.widget_ref = None
        self.view.destroy()

    def configuration_value_changed_cb(self, source, key, value):
        if key in ('theme', 'skin'):
            self.view.emit('reload-request')
        else:
            self.view.configuration_value_changed_cb(key, value)


    def theme_change_cb(self, themes, theme_id):
        if self.config.theme == USE_GLOBAL_SETTINGS:
            self.view.emit('reload-request')


    @cream.util.cached_property
    def about_dialog(self):

        return AboutDialog(self.context.manifest)


