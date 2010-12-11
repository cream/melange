#!/usr/bin/env python

# note: this is just a workaround until manifests are extended

from os.path import join, dirname

categories = {
    'org.cream.melange.CategoryInternet': {
        'name': 'Internet',
        'icon': join(dirname(__file__), 'images/internet.png'),
        'description': 'Interact with the web!'
    },
    'org.cream.melange.CategoryMultimedia': {
        'name': 'Multimedia',
        'icon': join(dirname(__file__), 'images/multimedia.png'),
        'description': 'Adds multimedia features to your desktop'
    },
    'org.cream.melange.CategoryTools': {
        'name': 'Tools',
        'icon': join(dirname(__file__), 'images/tools.png'),
        'description': 'Helping you to make your life easier'
    },
    'org.cream.melange.CategoryGames': {
        'name': 'Games',
        'icon': join(dirname(__file__), 'images/melange.png'),
        'description': 'Gaming for in between? Here you go!'
    },
    'org.cream.melange.CategoryMiscellaneous': {
        'name': 'Miscellaneous',
        'icon': join(dirname(__file__), 'images/melange.png'),
        'description': 'Various widgets i can\'t classify '
    }

}
