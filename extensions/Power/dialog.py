#! /usr/bin/python
# -*- coding: utf-8 -*-

import gtk
import cairo

import cream.gui
import cream.gui.animation


class CompositeBin(gtk.Fixed):

    def __init__(self):

        self.alpha = 1

        gtk.Fixed.__init__(self)

        self.connect('realize', self.realize_cb)


    def realize_cb(self, widget):

        self.parent.connect_after('expose-event', self.expose_cb)


    def expose_cb(self, widget, event):

        if self.child.window:
            ctx = widget.window.cairo_create()
            ctx.set_operator(cairo.OPERATOR_OVER)

            ctx.set_source_pixmap(self.child.window, 0, 0)
            ctx.paint_with_alpha(self.alpha)

        return False


    def add(self, child):

        self.child = child
        self.child.connect('realize', self.child_realize_cb)
        self.put(child, 0, 0)


    def child_realize_cb(self, widget):

        widget.window.set_composited(True)


class LogoutDialog:

    def __init__(self):

        self.options = [
            ('system-halt.svg', 'Shutdown', "Shut down your computer and switch it off..."),
            ('system-reboot.svg', 'Reboot', "Reboot your computer..."),
            ('system-suspend.svg', 'Suspend', "In this mode, your computer will draw a very little amount off current. Your session will be restored within just a few seconds."),
            ('system-hibernate.svg', 'Hibernate', "In this mode, your computer will draw no current. Your session will be saved on disk. Restoring your session will take some moments."),
            ('system-logout.svg', 'Logout', "Quit this session and bring you back to the login-screen.")
            ]

        self.window = gtk.Window()
        self.window.stick()
        self.window.set_keep_above(True)
        self.window.set_type_hint(gtk.gdk.WINDOW_TYPE_HINT_SPLASHSCREEN)
        self.window.set_position(gtk.WIN_POS_CENTER_ALWAYS)
        self.window.set_colormap(self.window.get_screen().get_rgba_colormap())
        self.window.set_app_paintable(True)
        self.window.connect('expose-event', self.expose_cb)
        self.window.set_decorated(False)

        self.widget = cream.gui.Widget()

        self.widget._size = (360, 180)

        self.background = cream.gui.Image()
        self.background.set_attribute('path', 'data/images/background.svg')
        self.background.set_attribute('opacity', .9)
        self.background.set_attribute('x', '0%')
        self.background.set_attribute('y', '0%')
        self.background.set_attribute('width', '100%')
        self.background.set_attribute('height', '100%')
        self.widget.add(self.background)
        self.background.render()

        self.logo = cream.gui.Image()
        self.logo.set_attribute('path', 'data/images/logo.svg')
        self.logo.set_attribute('opacity', .15)
        self.background.set_attribute('x', '40%')
        self.background.set_attribute('y', '10%')
        self.background.set_attribute('width', '80%')
        self.background.set_attribute('height', '160%')
        self.widget.add(self.logo)
        self.logo.render()

        self.line = cream.gui.Image()
        self.line.set_attribute('path', 'data/images/line.svg')
        self.logo.set_attribute('opacity', 1)
        self.background.set_attribute('x', '0%')
        self.background.set_attribute('y', '40%')
        self.background.set_attribute('width', '100%')
        self.background.set_attribute('height', '0.7%')
        self.widget.add(self.line)
        self.line.render()

        c = 1

        for i in self.options:

            description = cream.gui.Text()
            description.set_attribute('text', "j")
            description.set_attribute('font-family', 'Sans')
            description.set_attribute('font-color', (0.96, 0.95, 0.88, 0))
            description.set_attribute('font-size', 1)
            description.set_attribute('x', '5%')
            description.set_attribute('y', '5%')
            description.set_attribute('width', '80%')
            description.set_attribute('height', '40%')
            self.widget.add(description)
            description.render()

            item = cream.gui.Image()
            item.description = description
            item.set_attribute('path', 'data/images/%s' % i[0])
            item.connect('mouse-enter', self.item_mouse_enter_cb)
            item.connect('mouse-leave', self.item_mouse_leave_cb)
            item.connect('mouse-clicked', self.item_mouse_clicked)
            item.set_attribute('opacity', .5)
            x = 5.833333 * c + 13 * (c - 1)
            item.set_attribute('x', '{0}%'.format(x))
            item.set_attribute('y', '7%')
            item.set_attribute('width', '13%')
            item.set_attribute('height', '26%')
            self.widget.add(item)
            item.render()

            c += 1


        self.composite_bin = CompositeBin()
        self.composite_bin.add(self.widget)

        self.window.add(self.composite_bin)
        self.window.show_all()


    def expose_cb(self, widget, event):

        ctx = widget.window.cairo_create()

        ctx.set_operator(cairo.OPERATOR_SOURCE)
        ctx.set_source_rgba(0, 0, 0, 0)
        ctx.paint()


    def item_mouse_clicked(self, item):

        print "CLICKED: %s" % item


    def item_mouse_enter_cb(self, item):

        def anim(state):

            item.description.set_font_color((0.96, 0.95, 0.88, state))
            item.set_alpha(0.5 + state * .5)
            item.render()
            item.description.render()


        curve = cream.gui.animation.Curve(400, cream.gui.animation.CURVE_SINE)
        curve.run(anim)


    def item_mouse_leave_cb(self, item):

        def anim(state):

            item.description.set_font_color((0.96, 0.95, 0.88, 1 - state))
            item.set_alpha(1 - state * .5)
            item.render()
            item.description.render()


        curve = cream.gui.animation.Curve(400, cream.gui.animation.CURVE_SINE)
        curve.run(anim)
