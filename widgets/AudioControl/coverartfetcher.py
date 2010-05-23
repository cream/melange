#!/usr/bin/env python

import urllib
from contextlib import closing
from lxml.etree import parse

import os

try:
    from PIL import Image
except ImportError:
    print 'Please install python imaging libary'

size = 130, 130

class CoverArtFetcher(object):

    def __init__(self):
        self.key = '0e3d952c596aaec8af228fea60f08b4a'
        self.lastfm_template = 'http://ws.audioscrobbler.com/2.0/?method=track.getinfo&api_key={0}&artist={1}&track={2}'
        self.path = 'skins/default/covers/{0}-{1}.jpg'

    def get_album_data(self, artist, track):
        url = self.lastfm_template.format(self.key, artist, track)
        with closing(urllib.urlopen(url)) as page:
            track_data = parse(page)    
            return track_data.find('track').find('album')
    
    def get_image_url(self, artist, track):
        album_data = self.get_album_data(artist, track)
        album_title = album_data.find('title').text
        images = album_data.findall('image')
        for image in images:
            if image.items()[0][1] == 'large':
                return (image.text, album_title)

    def resize_image(self, path):
        image = Image.open(path)
        image.thumbnail(size, Image.ANTIALIAS)
        image.save(path, image.format)

    def download_image(self, artist, track, album_title):
        if album_title != 'Unknown':
            path = self.path.format(artist, album_title)
            if os.path.exists(os.path.abspath(path)):
                return 'covers/{0}-{1}.jpg'.format(artist, album_title)

        image_url, album = self.get_image_url(artist, track)
        if album_title != 'Unknown':
            album = album_title
        path = self.path.format(artist, album)
        if os.path.exists(path):
            #return path
            #workaround until /data exists
            return 'covers/{0}-{1}.jpg'.format(artist, album)
        with open(path, 'w') as image_file:    
            with closing(urllib.urlopen(image_url)) as image:
                image_file.write(image.read())

        self.resize_image(path)
        return 'covers/{0}-{1}.jpg'.format(artist, album)
        #return path
        #workaround until /data exists

if __name__ == '__main__':
    test = CoverArtFetcher()
    print test.get_image_url('Dream Theater', 'pull me under')

