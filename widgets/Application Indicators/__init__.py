#! /usr/bin/env python
# -*- coding: utf-8 -*-

import gobject

from cream.contrib.melange import api

from cream_indicator.host import StatusNotifierHost, Status

def construct_js_item(item):
    return {
        'icon': item.cached_icon_filename,
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
        item.connect('status-new', self.sig_status_new)

    def sig_status_new(self, item, status):
        if status == Status.NeedsAttention:
            print 'Attention icon'
            # TODO: Show attention icon and BLING BLING
        else:
            # TODO: Show normal icon without BLING BLING.
            pass

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
