#! /usr/bin/env python
# -*- coding: utf-8 -*-

# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 2 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the Free Software
# Foundation, Inc., 51 Franklin Street, Fifth Floor, Boston,
# MA 02110-1301, USA.

import gobject
gobject.threads_init()

import dbus.service

import cream
import cream.meta
import cream.ipc

from widget import Widget
from httpserver import HttpServer

class Melange(cream.Module, cream.ipc.Object):
    """ The main class of the Melange module. """

    __ipc_domain__ = 'org.cream.melange'

    def __init__(self):

        cream.Module.__init__(self)

        self._bus_name = '.'.join(self.__ipc_domain__.split('.')[:3])
        self._dbus_bus_name = dbus.service.BusName(self._bus_name, cream.ipc.SESSION_BUS)

        cream.ipc.Object.__init__(self,
            cream.ipc.SESSION_BUS,
            self._bus_name,
            cream.ipc.bus_name_to_path(self.__ipc_domain__)
        )

        # Initialize the HTTP server providing the widget data.
        self.server = HttpServer(self)
        self.server.run()

        # Scan for widgets...
        self.widgets = cream.meta.MetaDataDB('widgets', type='melange.widget')
        self.widget_instances = {}

        # Load widgets stored in configuration.
        for widget in self.config.widgets:
            self.load_widget(**widget)


    @cream.ipc.method('svv', '')
    def load_widget(self, name, x=None, y=None):
        """
        Load a widget with the given name at the specified coordinates (optional).

        :param name: The name of the widget.
        :param x: The x-coordinate.
        :param y: The y-coordinate.

        :type name: `str`
        :type x: `int`
        :type y: `int`
        """

        x, y = int(x), int(y)

        self.messages.debug("Loading widget '%s'..." % name)

        widget = Widget(self.widgets.get_by_name(name))
        self.widget_instances[widget.instance] = widget

        widget.connect('position-changed', self.widget_position_changed_cb)
        widget.connect('remove', self.widget_remove_cb)
        widget.connect('reload', self.widget_reload_cb)

        widget.show()

        if x is not None and y is not None:
            widget.set_position(x, y)


    @cream.ipc.method('', 'a{sa{ss}}')
    def list_widgets(self):
        """
        List all available widgets.

        :return: List of widgets.
        :rtype: `list`
        """

        return self.widgets.by_hash


    def quit(self):
        """ Quit the module. """

        self.config.widgets = self.widget_instances.values()
        cream.Module.quit(self)


    def widget_position_changed_cb(self, widget, x, y):
        """ Callback function being called when a widget was moved. """

        pass


    def widget_remove_cb(self, widget):
        """ Callback being called when a widget has been removed. """

        del self.widget_instances[widget.instance]


    def widget_reload_cb(self, widget):
        """ Callback function that is called when the user clicks on the "Reload" menu entry. """

        info_dict = widget.__xmlserialize__()
        self.messages.debug("Reloading widget '%(name)s'" % info_dict)
        widget.close()
        self.load_widget(**info_dict)


if __name__ == '__main__':
    melange = Melange()
    melange.main()
