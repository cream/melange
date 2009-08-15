#! /usr/bin/python
# -*- coding: utf-8 -*-

import gobject
import gtk
import cairo

import math
import os.path

import cream
import cream.ipc
import cream.extensions
import cream.gui
import cream.gui.animation
import cream.util

from cream.contrib.melange import themes

THEME = themes.ThemeManager()['Default']

gtk.gdk.threads_init()

class Melange(cream.Module):

    def __init__(self):

        cream.Module.__init__(self)

        self.widgets = []

        api = cream.extensions.ExtensionInterface({
            'add_widget': self.add_widget
            })

        self.extensions = cream.extensions.ExtensionManager([os.path.join(self._base_path, 'extensions')], api)

        #self.extensions.load('Test Widget')
        #self.extensions.load('Playground Widget')
        self.extensions.load('Power Applet')


    @cream.ipc.method('', 'as')
    def list_available_applets(self):

        return self.extensions.list()


    @cream.ipc.method('s')
    def load_applet(self, applet):

        self.extensions.load(applet)


    def add_widget(self, widget):

        widget.hide_timeout = None
        widget.resizing = False
        widget.frame = gtk.Window()
        widget.frame.set_colormap(widget.frame.get_screen().get_rgba_colormap())
        widget.frame.fullscreen()
        widget.frame.set_app_paintable(True)
        widget.frame.connect('expose-event', self.expose_cb)
        widget.frame.set_decorated(False)
        widget.frame.set_type_hint(gtk.gdk.WINDOW_TYPE_HINT_UTILITY)
        widget.frame.set_keep_below(True)
        widget.frame.set_property('skip-pager-hint', True)
        widget.frame.set_property('skip-taskbar-hint', True)
        widget.frame.stick()

        try:
            widget.frame.move(extension.config['melange.position.x'], extension.config['melange.position.y'])
        except:
            pass

        close = cream.gui.Image()
        close.set_attribute('width', '20px')
        close.set_attribute('height', '20px')
        close.set_attribute('x', '100% - 30px')
        close.set_attribute('y', '10px')
        close.set_attribute('path', THEME['applet.controls.close'])
        close.set_attribute('opacity', '0')
        close.connect('mouse-clicked', self.clicked_cb)

        #settings = cream.gui.Image()
        #settings.set_alpha(.8)
        #settings.set_size(.1, .1)
        #settings.set_position(0.85, 0.18)
        #settings.set_path('extensions/TestWidget/data/images/widget_settings.svg')
        #settings.connect('mouse-clicked', self.clicked_cb)

        move = cream.gui.Image()
        move.set_attribute('width', '20px')
        move.set_attribute('height', '20px')
        move.set_attribute('x', '100% - 30px')
        move.set_attribute('y', '100% - 30px')
        move.set_attribute('path', THEME['applet.controls.zoom'])
        move.set_attribute('opacity', '0')
        move.connect('mouse-press', self.pressed_cb)
        move.connect('mouse-release', self.released_cb)

        #widget.controls = {'close': close, 'settings': settings, 'move': move}
        widget.controls = {'close': close, 'move': move}

        self.widgets.append(widget)

        gtk.gdk.threads_enter()
        widget.connect('size-allocate', self.resize_cb)
        self.composite_bin = cream.gui.CompositeBin()
        self.composite_bin.add(widget)

        widget.frame.add(self.composite_bin)
        widget.frame.show_all()
        gtk.gdk.threads_leave()

        widget.connect('enter-notify-event', self.enter_notify_cb)
        widget.connect('leave-notify-event', self.leave_notify_cb)


    def enter_notify_cb(self, widget, event):

        if widget.hide_timeout:
            try:
                gobject.source_remove(widget.hide_timeout)
            except:
                pass
        if widget.controls['close'].get_attribute('opacity') != 1:
            self.show_controls(widget)
            widget.hide_timeout = None


    def leave_notify_cb(self, widget, event):

        widget.hide_timeout = gobject.timeout_add(1000, self.hide_controls, widget)


    def show_controls(self, widget):

        def anim(state):

            widget.controls['close'].set_attribute('opacity', start + (1 - start) * state)
            widget.controls['close'].render(False)
            widget.controls['move'].set_attribute('opacity', start + (1 - start) * state)
            widget.controls['move'].render(False)
            #widget.controls['settings'].set_alpha(start + (1 - start) * state)
            #widget.controls['settings'].render(False)
            widget.render()

        start = float(widget.controls['close'].get_attribute('opacity'))

        if start == 0:
            widget.add(widget.controls['close'])
            widget.controls['close'].set_attribute('opacity', start)
            widget.controls['close'].render()

            widget.add(widget.controls['move'])
            widget.controls['move'].set_attribute('opacity', start)
            widget.controls['move'].render()

            #widget.add(widget.controls['settings'])
            #widget.controls['settings'].set_alpha(start)
            #widget.controls['settings'].render()

        curve = cream.gui.animation.Curve(500, cream.gui.animation.CURVE_SINE)
        curve.run(anim)


    def hide_controls(self, widget):

        def anim(state):

            if widget.hide_timeout != None:
                state = 1 - state

                widget.controls['close'].set_attribute('opacity', state)
                widget.controls['close'].render(False)
                widget.controls['move'].set_attribute('opacity', state)
                widget.controls['move'].render(False)
                #widget.controls['settings'].set_alpha(state)
                #widget.controls['settings'].render(False)
                widget.render()

                if state == 0:
                    widget.stack.remove(widget.controls['close'])
                    widget.stack.remove(widget.controls['move'])
                    #widget.stack.remove(widget.controls['settings'])
                    widget.render()
                    widget.hide_timeout = None

        curve = cream.gui.animation.Curve(500, cream.gui.animation.CURVE_SINE)
        curve.run(anim)

        return False


    def resize(self, widget, x, y):

        new_x = widget.get_display().get_pointer()[1]
        new_y = widget.get_display().get_pointer()[2]

        x = new_x - x
        y = new_y - y

        if x > 0:
            factor = math.sqrt(x**2 + y**2) / math.sqrt(widget.zoom * float(widget.size[0])**2 + widget.zoom * float(widget.size[1])**2)
        else:
            factor = -math.sqrt(x**2 + y**2) / math.sqrt(widget.zoom * float(widget.size[0])**2 + widget.zoom * float(widget.size[1])**2)

        if widget.resizing == True:
            widget.zoom += widget.zoom * factor
            widget.render(force_render=True)
            widget.frame.set_size_request(int(widget.size[0]), int(widget.size[1]))
            gobject.timeout_add(50, self.resize, widget, new_x, new_y)


    def pressed_cb(self, object):

        object.parent.resizing = True
        gtk.gdk.pointer_grab(object.parent.window, event_mask = gtk.gdk.BUTTON_RELEASE_MASK)
        gobject.timeout_add(50, self.resize, object.parent, *object.parent.get_display().get_pointer()[1:-1])


    def released_cb(self, object):

        gtk.gdk.pointer_ungrab()
        object.parent.resizing = False
        object.parent.render(force_render=True)


    def clicked_cb(self, object):

        if object == object.parent.controls['close']:
            print "CLOSE"


    def resize_cb(self, widget, allocation):

        width = allocation.width
        height = allocation.height

        widget.frame.set_size_request(width, height)
        widget.frame.resize(width, height)


    def expose_cb(self, widget, event):

        ctx = widget.window.cairo_create()

        ctx.set_operator(cairo.OPERATOR_SOURCE)
        ctx.set_source_rgba(0, 0, 0, 0)
        ctx.paint()


melange = Melange()
melange.main()
