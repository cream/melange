#!/usr/bin/env python

import urllib
from contextlib import closing
from lxml.etree import parse

class LyricsFetcher(object):

    def __init__(self):
        self.key = '9409c5a1f7bf7ecfd-temporary.API.access'
        self.lyricsfly = 'http://api.lyricsfly.com/api/api.php?i={0}&a={1}&t={2}'


    def get_lyrics(self, artist, title):
        url = self.lyricsfly.format(self.key, artist, title)
        with closing(urllib.urlopen(url)) as page:
            lyrics_data = parse(page)    
            if lyrics_data.find('status').text == '300':
                lyrics = lyrics_data.find('sg').find('tx').text.split('[br]')
                lyrics = ''.join(lyrics).replace('\n', '<br>')
                return lyrics
            else:
                return 'No lyrics available'
            
