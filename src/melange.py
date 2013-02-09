#!/usr/bin/env python

import os
import cairo
from gi.repository import (Gtk as gtk, Gdk as gdk, GObject as gobject,
                           WebKit as webkit)

import cream
import cream.ipc

from gpyconf.fields import MultiOptionField

from melange.widget import Widget
from melange.gui import CompositeBin
from melange.dialogs import AddWidgetDialog
from melange.common import MOUSE_BUTTON_RIGHT


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



class WidgetLayer(TransparentWindow):

    def __init__(self):

        TransparentWindow.__init__(self)

        self.set_events(gdk.EventMask.BUTTON_RELEASE_MASK)
        self.set_type_hint(gdk.WindowTypeHint.DESKTOP)

        self.widgets = {}
        self.signal_handlers = {}

        screen = gdk.Screen.get_default()
        self.width = screen.get_width()
        self.height = screen.get_height()

        self.layout = CompositeBin()
        self.add(self.layout)


    def add_widget(self, widget):

        self.widgets[widget.instance_id] = widget
        handler_ids = []
        self.signal_handlers[widget.instance_id] = handler_ids

        handler_ids.append(widget.view.connect('move-request', self.move_request_cb))
        handler_ids.append(widget.view.connect('raise-request', self.raise_request_cb))
        handler_ids.append(widget.view.connect('remove-request', self.remove_request_cb))
        handler_ids.append(widget.view.connect('reload-request', self.reload_request_cb))


        self.layout.add(widget.view, *widget.get_position())
        widget.view.show_all()


    def remove_widget(self, widget):

        del self.widgets[widget.instance_id]

        for id in self.signal_handlers[widget.instance_id]:
            widget.view.disconnect(id)

        self.layout.remove(widget.view)
        widget.destroy()


    def reload(self, widget):
        self.remove_widget(widget)
        widget.load()
        self.add_widget(widget)


    def reload_all(self):

        for widget in self.widgets.itervalues():
            self.reload(widget)


    def move_request_cb(self, view, x, y):

        old_x, old_y = view.widget_ref.get_position()
        allocation = view.get_allocation()
        new_x = max(0, min(old_x + x, self.width - allocation.width))
        new_y = max(0, min(old_y + y, self.height - allocation.height))

        self.layout.move(view, new_x, new_y)
        view.widget_ref.set_position(new_x, new_y)


    def raise_request_cb(self, view):

        self.layout.raise_child(view)


    def remove_request_cb(self, view):

        self.remove_widget(view.widget_ref)


    def reload_request_cb(self, view):

        widget = view.widget_ref
        self.reload(widget)


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
        self.themes = cream.manifest.ManifestDB(theme_dirs, 
            type='org.cream.melange.Theme'
        )

        widget_dirs = [
            os.path.join(self.context.get_path(), 'data/widgets'),
            os.path.join(self.context.get_user_path(), 'data/widgets')
        ]
        self.available_widgets = cream.manifest.ManifestDB(widget_dirs,
            type='org.cream.melange.Widget'
        )


        self.config._add_field(
            'theme',
            MultiOptionField('Theme',
                options=((k, v['name']) for k,v in self.themes.manifests.items())
            )
        )

        self.config.read()
        self.config.connect('field-value-changed', self.configuration_value_changed_cb)

        self.layer = WidgetLayer()
        self.layer.connect('button-release-event', self.button_release_cb)
        self.layer.show_all()


        self.load_widget('org.cream.melange.CalculatorWidget')


    @cream.util.cached_property
    def add_widget_dialog(self):

        widgets = sorted(
            self.available_widgets.manifests.itervalues(), 
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
        return self.themes.get_by_id(self.config.theme)


    def add_widget(self):

        widget_id = self.add_widget_dialog.run()
        if widget_id is not None:
            self.load_widget(widget_id)


    def button_release_cb(self, layer, event):

        if event.button == MOUSE_BUTTON_RIGHT:
            self.menu.popup(None, None, None, None, event.button, event.get_time())


    def configuration_value_changed_cb(self, source, key, value):
        if key == 'theme':
            theme = self.themes.get_by_id(value)
            for widget in self.layer.widgets.itervalues():
                widget.theme = theme
            self.layer.reload_all()

    @cream.ipc.method('svv', '')
    def load_widget(self, id, x=None, y=None):

        self.messages.debug("Loading widget '%s'..." % id)

        path = self.available_widgets.get_by_id(id)._path
        widget = Widget(path, self.themes, self.selected_theme, self.common_path)

        if x and y:
            x, y = int(x), int(y)
            widget.set_position(x, y)
        else:
            x, y = widget.get_position()


        self.layer.add_widget(widget)


if __name__ == '__main__':
    melange = Melange()
    melange.main()

