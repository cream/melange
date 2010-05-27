#! /usr/bin/env python
# -*- coding: utf-8 -*-

import gobject

from cream.contrib.melange import api

@api.register('appindicators')
class AppIndicators(api.API):

    def __init__(self):

        self.items = []

        # Intialize the DBus stuff here...


    def add_item(self, item):

        # Do some stuff here...

        self.items.append(item)

        self.emit('item-added', {
            'icon': '...',
            'id': 'the-items-id'
            })


    def remove_item(self, item):

        # Do some stuff here...

        self.items.remove(item)
        self.emit('item-removed', item.id)


    @api.expose
    def get_items(self):

        items = []

        for item in self.items:
            items.append({
                'icon': '...',
                'id': 'the-items-id'
                })

        return items


    @api.expose
    def show_menu(self, id):

        # Show the items menu...
        print id
