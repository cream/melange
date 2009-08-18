import cream.ipc

import cream.contrib.melange
from cream.contrib.melange import widgets

OPACITY = '.6'

@cream.extensions.register
class PowerApplet(cream.contrib.melange.Applet):

    def __init__(self, *args):

        cream.contrib.melange.Applet.__init__(self, *args)

        self.system = cream.ipc.get_object('org.cream.system')

        self.widget._size = (266, 80)

        self.background = widgets.Background()
        self.widget.add(self.background)
        self.background.render()

        self.suspend = cream.gui.Image()
        self.suspend.connect('mouse-enter', self.mouse_enter_cb)
        self.suspend.connect('mouse-leave', self.mouse_leave_cb)
        self.suspend.connect('mouse-clicked', self.mouse_clicked_cb)
        self.suspend.set_attribute('path', 'images/system-suspend.svg')
        self.suspend.set_attribute('x', '4.51%')
        self.suspend.set_attribute('y', '15%')
        self.suspend.set_attribute('width', '21.05%')
        self.suspend.set_attribute('height', '70%')
        self.suspend.set_attribute('opacity', OPACITY)
        self.widget.add(self.suspend)
        self.suspend.render()

        self.hibernate = cream.gui.Image()
        self.hibernate.connect('mouse-enter', self.mouse_enter_cb)
        self.hibernate.connect('mouse-leave', self.mouse_leave_cb)
        self.hibernate.connect('mouse-clicked', self.mouse_clicked_cb)
        self.hibernate.set_attribute('path', 'images/system-hibernate.svg')
        self.hibernate.set_attribute('x', '27.81%')
        self.hibernate.set_attribute('y', '15%')
        self.hibernate.set_attribute('width', '21.05%')
        self.hibernate.set_attribute('height', '70%')
        self.hibernate.set_attribute('opacity', OPACITY)
        self.widget.add(self.hibernate)
        self.hibernate.render()

        self.shutdown = cream.gui.Image()
        self.shutdown.connect('mouse-enter', self.mouse_enter_cb)
        self.shutdown.connect('mouse-leave', self.mouse_leave_cb)
        self.shutdown.connect('mouse-clicked', self.mouse_clicked_cb)
        self.shutdown.set_attribute('path', 'images/system-halt.svg')
        self.shutdown.set_attribute('x', '51.11%')
        self.shutdown.set_attribute('y', '15%')
        self.shutdown.set_attribute('width', '21.05%')
        self.shutdown.set_attribute('height', '70%')
        self.shutdown.set_attribute('opacity', OPACITY)
        self.widget.add(self.shutdown)
        self.shutdown.render()

        self.reboot = cream.gui.Image()
        self.reboot.connect('mouse-enter', self.mouse_enter_cb)
        self.reboot.connect('mouse-leave', self.mouse_leave_cb)
        self.reboot.connect('mouse-clicked', self.mouse_clicked_cb)
        self.reboot.set_attribute('path', 'images/system-reboot.svg')
        self.reboot.set_attribute('x', '74.41%')
        self.reboot.set_attribute('y', '15%')
        self.reboot.set_attribute('width', '21.05%')
        self.reboot.set_attribute('height', '70%')
        self.reboot.set_attribute('opacity', OPACITY)
        self.widget.add(self.reboot)
        self.reboot.render()

        self.interface.add_widget(self.widget)


    def mouse_enter_cb(self, object):

        def fade_in(state):
            object.set_attribute('opacity', str(float(OPACITY) + (1 - float(OPACITY)) * state))
            object.render()
            

        curve = cream.gui.animation.Curve(800, cream.gui.animation.CURVE_SINE)
        curve.run(fade_in)


    def mouse_leave_cb(self, object):

        def fade_out(state):
            state = 1 - state
            object.set_attribute('opacity', str(float(OPACITY) + (1 - float(OPACITY)) * state))
            object.render()
            

        curve = cream.gui.animation.Curve(800, cream.gui.animation.CURVE_SINE)
        curve.run(fade_out)


    def mouse_clicked_cb(self, object):

        if object == self.suspend:
            self.system.suspend()
        elif object == self.hibernate:
            self.system.hibernate()
        elif object == self.shutdown:
            self.system.shudown()
        elif object == self.reboot:
            self.system.reboot()
