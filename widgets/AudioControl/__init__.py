#!/usr/bin/env python

from cream.contrib.melange import api

from audioplayers.banshee import Banshee
from audioplayers.rhythmbox import Rhythmbox

from coverartfetcher import CoverArtFetcher
from lyricsfetcher import LyricsFetcher

@api.register('audiocontrol')
class AudioControl(api.API):

    def __init__(self):
    
        api.API.__init__(self)
        
        self.player = Banshee()
        self.coverartfetcher = CoverArtFetcher()
        self.lyricsfetcher = LyricsFetcher()
        
        self.cur_track = None
    
    @api.expose
    def pause(self):
        @api.in_main_thread
        def pause():
            self.player.pause()

        pause()
    
    @api.expose
    def play(self):
        @api.in_main_thread
        def play():
            self.player.play()

        play()

    @api.expose
    def previous_track(self):
        @api.in_main_thread
        def previous_track():
            self.player.previous()

        previous_track()

    @api.expose
    def next_track(self):
        @api.in_main_thread
        def next_track():
            self.player.next()

        next_track()

    @api.expose
    def is_playing(self):
        @api.in_main_thread
        def is_playing():
            return self.player.is_playing()

        return is_playing()

    @api.expose
    def get_track_data(self):
        @api.in_main_thread
        def get_track_data():
            return self.player.get_track_data()
        return get_track_data()



    @api.expose
    def get_cover_art(self, artist, title, album):
        path = self.coverartfetcher.download_image(artist, title, album)
        return path


    @api.expose
    def get_rating(self):
        @api.in_main_thread
        def get_rating():
            return self.player.get_rating()

        return get_rating()

    @api.expose
    def set_rating(self, new_rating):
        @api.in_main_thread
        def set_rating():
            self.player.set_rating(new_rating)

        set_rating()

    @api.expose
    def get_lyrics(self, artist, title):
        return self.lyricsfetcher.get_lyrics(artist, title)

    @api.expose
    def song_changed(self):
        @api.in_main_thread
        def song_changed():
            track = self.player.get_track_data()['title']
            if track != self.cur_track:
                self.cur_track = track
                return True
            else:
                return False

        return song_changed()

        
