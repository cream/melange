#!/usr/bin/env python

import dbus
BUS = dbus.SessionBus()

class Rhythmbox(object):

    def __init__(self):
        self.player = BUS.get_object('org.gnome.Rhythmbox',
                                '/org/gnome/Rhythmbox/Player')
        self.shell = BUS.get_object('org.gnome.Rhythmbox',
                                '/org/gnome/Rhythmbox/Shell')

    def pause(self):
        self.player.playPause(False)

    def play(self):
        self.player.playPause(True)
    
    def previous(self):
        self.player.previous()

    def next(self):
        self.player.next()


    def is_playing(self):
        if self.player.getPlaying():
            return True
        else:
            return False

    def get_track_data(self):
        uri = self.player.getPlayingUri()
        raw_data = self.shell.getSongProperties(uri)
        data = dict()
        keys = ['artist', 'album', 'title']
        for key in keys:
            try:
                data[key] = str(raw_data[key])
            except KeyError:
                data[key] = 'Unknown'
        return data

    def get_rating(self):
        uri = self.player.getPlayingUri()
        raw_data = self.shell.getSongProperties(uri)
        return int(raw_data['rating'])

    def set_rating(self, new_rating):
        uri = self.player.getPlayingUri()
        self.shell.setSongProperty(uri, 'rating',  dbus.Double(new_rating, variant_level=1))



if __name__ == '__main__':
    test = Rhythmbox()
    test.set_rating(5)

