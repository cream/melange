import cream.contrib.melange
from cream.contrib.melange import widgets
from pprint import pprint
from math import log
from time import localtime
import gobject

class BinaryClock(object):

    def __init__(self, kind='digit'):
        self.kind = kind


    def get_lights(self, number, dividor = 8):

        lights = []
        while dividor >= 1:
            if number >= dividor:
                lights.append(True)
                number -= dividor

            else:
                lights.append(False)

            dividor /= 2

        return lights


    def get_digit_lights(self, digits):

        lights = []
        for digit in digits:
            lights.append(self.get_lights(digit))

        return lights


    def get_grouped_lights(self, numbers):

        lights = []
        for number in numbers:
            lights.append(self.get_lights(number, 32))

        return lights


    def clock(self):

        t = localtime()
        hour = t[3]
        minute = t[4]
        second = t[5]

        if self.kind == 'digit':

            hour1 = hour // 10
            hour2 = hour % 10

            minute1 = minute // 10
            minute2 = minute % 10

            second1 = second // 10
            second2 = second % 10

            digits = (hour1, hour2, minute1, minute2, second1, second2)

            lights = self.get_digit_lights(digits)

        else:
            lights = self.get_grouped_lights((hour, minute, second))

        return lights


@cream.extensions.register
class BinaryClockApplet(cream.contrib.melange.Applet):

    def __init__(self, *args):

        cream.contrib.melange.Applet.__init__(self, *args)

        self.clock = BinaryClock()

        self.widget._size = (160, 100)

        self.background = widgets.Background()
        self.widget.add(self.background)
        self.background.render()

        self.dots = []

        c_x = 0
        c_y = 0
        for i in xrange(0, 6):
            l = []
            self.dots.append(l)
            for i in xrange(0, 4):
                img = cream.gui.Image()
                img.set_attribute('path', 'images/dot-inactive.svg')
                img.set_attribute('width', '12%')
                img.set_attribute('height', '19.2%')
                img.set_attribute('x', str(c_x * 12 + (c_x // 2) * 7 + 7) + '%')
                img.set_attribute('y', str(c_y * 19.2 + 10) + '%')
                self.widget.add(img)
                img.render()
                l.append(img)
                c_y += 1
            c_y = 0
            c_x += 1

        self.interface.add_widget(self.widget)
        gobject.timeout_add(1000, self.update_clock)
        self.update_clock()


    def update_clock(self):

        for c_x, l in enumerate(self.clock.clock()):
            for c_y, i in enumerate(l):
                d = self.dots[c_x][c_y]
                if i and not d.get_attribute('path') == 'images/dot-active.svg':
                    d.set_attribute('path', 'images/dot-active.svg')
                    d.render(False)
                elif not i and d.get_attribute('path') == 'images/dot-active.svg':
                    d.set_attribute('path', 'images/dot-inactive.svg')
                    d.render(False)
        self.widget.render()
        return True
