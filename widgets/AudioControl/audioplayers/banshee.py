#!/usr/bin/env python

import dbus
BUS = dbus.SessionBus()

class Banshee(object):

    def __init__(self):
        self.player_engine = BUS.get_object('org.bansheeproject.Banshee',
                                '/org/bansheeproject/Banshee/PlayerEngine')
        self.playback_controller = BUS.get_object('org.bansheeproject.Banshee',
                            '/org/bansheeproject/Banshee/PlaybackController')
        

    def pause(self):
        self.player_engine.Pause()
    
    def play(self):
        self.player_engine.Play()
    
    def previous(self):
        self.playback_controller.Previous(True)
    
    def next(self):
        self.playback_controller.Next(True)


    def is_playing(self):
        if str(self.player_engine.GetCurrentState()) == 'playing':
            return True
        else:
            return False

    def get_track_data(self):
        data = dict()
        raw_data = self.player_engine.GetCurrentTrack()
        keys = { 'title':'name',
                 'artist':'artist',
                 'album':'album'}

        for key in keys.keys():
            try:
                data[key] = str(raw_data[keys[key]])
            except KeyError:
                data[key] = 'Unknown'

        return data

    def get_rating(self):
        return int(self.player_engine.GetRating())
    
    def set_rating(self, new_rating):
        self.player_engine.SetRating(dbus.Byte(int(new_rating)))

