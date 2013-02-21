#!/usr/bin/env python

import os
import cairo
from gi.repository import Gtk as gtk, Gdk as gdk, GObject as gobject

import cream
import cream.ipc

from gpyconf.fields import MultiOptionField

from melange.widget import Widget
from melange.dialogs import AddWidgetDialog
from melange.common import MOUSE_BUTTON_LEFT, MOUSE_BUTTON_RIGHT


class TransparentWindow(gtk.Window):

    def __init__(self):

        gtk.Window.__init__(self)

        screen = self.get_display().get_default_screen()
        self.set_default_size(screen.get_width(), screen.get_height())

        self.set_events(gdk.EventMask.BUTTON_RELEASE_MASK)
        self.set_type_hint(gdk.WindowTypeHint.DESKTOP)

        self.set_app_paintable(True)
        self.set_visual(self.get_screen().get_rgba_visual())
        self.connect('draw', self.draw_cb)


    def draw_cb(self, window, ctx):

        ctx.set_operator(cairo.OPERATOR_SOURCE)
        ctx.set_source_rgba(0, 0, 0, 0)
        ctx.paint()



class WidgetWindow(gtk.Window, gobject.GObject):
    __gsignals__ = {
        'remove-request': (gobject.SignalFlags.RUN_LAST, None, ())
    }

    def __init__(self):

        gtk.Window.__init__(self)
        gobject.GObject.__init__(self)

        self.ctrl_pressed = False

        self.set_events(gdk.EventMask.BUTTON_RELEASE_MASK)
        self.set_type_hint(gdk.WindowTypeHint.DESKTOP)

        self.set_app_paintable(True)
        self.set_visual(self.get_screen().get_rgba_visual())

        self.connect('draw', self.draw_cb)
        self.connect('key-press-event', self.key_press_cb)
        self.connect('key-release-event', self.key_release_cb)
        self.connect('button-press-event', self.button_press_cb)
        self.connect('button-release-event', self.button_release_cb)

        screen = gdk.Screen.get_default()
        self.screen_width = screen.get_width()
        self.screen_height = screen.get_height()


    def load_widget(self, widget):

        self._widget = widget
        self.handlers = []

        self.handlers.append(widget.view.connect('show-request', self.show_request_cb))
        self.handlers.append(widget.view.connect('move-request', self.move_request_cb))
        self.handlers.append(widget.view.connect('begin-move', self.fade_out))
        self.handlers.append(widget.view.connect('end-move', self.fade_in))
        self.handlers.append(widget.view.connect('remove-request', self.remove_request_cb))
        self.handlers.append(widget.view.connect('reload-request', self.reload_request_cb))

        self.add(widget.view)


    def reload(self):

        for id in self.handlers:
            self._widget.view.disconnect(id)

        self.remove(self._widget.view)
        self._widget.destroy()
        self._widget.load()
        self.load_widget(self._widget)


    def fade_in(self, view):
        self.set_opacity(1)


    def fade_out(self, view):
        self.set_opacity(0.8)


    def show_request_cb(self, view):

        self.show_all()
        self.move(*self._widget.get_position())


    def move_request_cb(self, view, x, y):

        old_x, old_y = self._widget.get_position()
        allocation = view.get_allocation()

        new_x = max(0, min(old_x + x, self.screen_width - allocation.width))
        new_y = max(0, min(old_y + y, self.screen_height - allocation.height))

        self.move(new_x, new_y)
        self._widget.set_position(new_x, new_y)


    def remove_request_cb(self, view):

        for id in self.handlers:
            self._widget.view.disconnect(id)

        self.remove(view)
        self._widget.destroy()

        self.emit('remove-request')

    def reload_request_cb(self, view):

        self.reload()


    def key_press_cb(self, window, event):

        if event.keyval in (gdk.KEY_Control_L, gdk.KEY_Control_R):
            self.ctrl_pressed = True


    def key_release_cb(self, window, event):

        if event.keyval in (gdk.KEY_Control_L, gdk.KEY_Control_R):
            self.ctrl_pressed = False
            self._widget.view.end_move()


    def button_press_cb(self, window, event):

        if self.ctrl_pressed and event.button == MOUSE_BUTTON_LEFT:
            self._widget.view.begin_move()


    def button_release_cb(self, window, event):

        if self.ctrl_pressed and event.button == MOUSE_BUTTON_LEFT:
            self._widget.view.end_move()


    def draw_cb(self, window, ctx):

        ctx.set_operator(cairo.OPERATOR_SOURCE)
        ctx.set_source_rgba(0, 0, 0, 0)
        ctx.paint()


class Themes(gobject.GObject):
    __gsignals__ = {
        'changed': (gobject.SignalFlags.RUN_LAST, None, (str,))
    }

    def __init__(self, theme_dirs):

        gobject.GObject.__init__(self)

        self._themes = cream.manifest.ManifestDB(theme_dirs,
            type='org.cream.melange.Theme'
        )

        self.selected_theme_id = None


    def change_theme(self, theme_id):

        self.selected_theme_id = theme_id
        self.emit('changed', theme_id)

    def get_theme(self, theme_id):

        return self._themes.get(id=theme_id)

    def get_all_themes(self):

        return self._themes.get_all()


class Melange(cream.Module, cream.ipc.Object):

    def __init__(self):

        cream.Module.__init__(self, 'org.cream.Melange')
        cream.ipc.Object.__init__(self,
            'org.cream.Melange',
            '/org/cream/Melange'
        )

        self.common_path = os.path.join(self.context.working_directory,
            'data/common'
        )

        theme_dirs = [
            os.path.join(self.context.get_path(), 'data/themes'),
            os.path.join(self.context.get_user_path(), 'data/themes')
        ]
        self.themes = Themes(theme_dirs)

        widget_dirs = [
            os.path.join(self.context.get_user_path(), 'data/widgets')
        ]
        self.available_widgets = cream.manifest.ManifestDB(widget_dirs,
            type='org.cream.melange.Widget'
        )

        self.config._add_field(
            'theme',
            MultiOptionField('Theme',
                options=((t['id'], t['name']) for t in self.themes.get_all_themes())
            )
        )

        self.config.read()
        self.config.connect('field-value-changed', self.configuration_value_changed_cb)

        self.themes.change_theme(self.config.theme)

        self.event_layer = TransparentWindow()
        self.event_layer.connect('button-release-event', self.button_release_cb)
        self.event_layer.show_all()

        self.windows = []

        gobject.timeout_add(20, self.load_widgets_from_config)

    @cream.util.cached_property
    def add_widget_dialog(self):

        widgets = sorted(
            self.available_widgets.get_all(),
            key=lambda w: w['name']
        )
        return AddWidgetDialog(widgets)


    @cream.util.cached_property
    def menu(self):

        item_add = gtk.ImageMenuItem(gtk.STOCK_ADD)
        item_add.get_children()[0].set_label('Add widgets')
        item_add.connect('activate', lambda *x: self.add_widget())

        item_settings = gtk.ImageMenuItem(gtk.STOCK_PREFERENCES)
        item_settings.get_children()[0].set_label('Settings')
        item_settings.connect('activate', lambda *x: self.config.show_dialog())

        menu = gtk.Menu()
        menu.append(item_add)
        menu.append(item_settings)
        menu.show_all()

        return menu


    @property
    def selected_theme(self):
        return self.themes.get_theme(self.config.theme)


    def add_widget(self):

        widget_id = self.add_widget_dialog.run()
        if widget_id is not None:
            self.load_widget(widget_id)


    def button_release_cb(self, layer, event):

        if event.button == MOUSE_BUTTON_RIGHT:
            self.menu.popup(None, None, None, None, event.button, event.get_time())

        # Raise all widgets to be on top of the event_layer again
        for window in self.windows:
            window.present()



    def configuration_value_changed_cb(self, source, key, value):

        if key == 'theme':
            self.themes.change_theme(value)

    def remove_request_cb(self, window):

        self.windows.remove(window)
        window.destroy()


    def load_widgets_from_config(self):

        for widget in self.config.widgets:
            self.load_widget(**widget)

    @cream.ipc.method('svv', '')
    def load_widget(self, id, x=None, y=None):

        self.messages.debug("Loading widget '%s'..." % id)

        path = self.available_widgets.get(id=id)._path
        widget = Widget(id, path, self.themes, self.common_path)

        if x and y:
            x, y = int(x), int(y)
            widget.set_position(x, y)
        else:
            x, y = widget.get_position()

        window = WidgetWindow()
        window.connect('remove-request', self.remove_request_cb)
        window.load_widget(widget)

        self.windows.append(window)


    def quit(self):

        widgets = []
        for window in self.windows:
            widget = window._widget
            widgets.append({
                'id': widget.id, 
                'x': widget.get_position()[0],
                'y': widget.get_position()[1]
            })

        self.config.widgets = widgets
        cream.Module.quit(self)



if __name__ == '__main__':
    melange = Melange()
    melange.main()

