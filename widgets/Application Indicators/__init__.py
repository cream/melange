#! /usr/bin/env python
# -*- coding: utf-8 -*-

import gobject

from cream.contrib.melange import api

from cream_indicator.host import StatusNotifierHost

def construct_js_item(item):
    return {
        'icon': '...',
        'id': item.id,
    }

@api.register('appindicators')
class AppIndicators(api.API):

    def __init__(self):

        # Intialize the DBus stuff here...
        self.host = StatusNotifierHost()
        self.host.connect('item-added', self.sig_item_added)
        self.host.connect('item-removed', self.sig_item_removed)

        self.add_initially()

    def sig_item_added(self, host, item):
        self.emit('item-added', construct_js_item(item))

    def sig_item_removed(self, host, item):
        self.emit('item-removed', item.id)

    def add_initially(self):
        for item in self.host.items:
            self.sig_item_added(self.host, item)

    @api.expose
    def get_items(self):

        items = []

        for item in self.host.items:
            items.append(construct_js_item(item))

        return items


    @api.expose
    def show_menu(self, id):
        item = self.host.get_item_by_id(id)
        # Show the menu.
        item.show_menu()
