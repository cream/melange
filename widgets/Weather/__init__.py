#! /usr/bin/env python
# -*- coding: utf-8 -*-
 
import urllib
from xml.dom.minidom import parseString as parse_xml
 
from cream.contrib.melange import api
 
@api.register('weather')
class Weather(api.API): 

    @api.expose
    def get(self, location):

        handle = urllib.urlopen('http://api.wunderground.com/auto/wui/geo/WXCurrentObXML/index.xml?query={0}'.format(location))
        data = handle.read()
        handle.close()
        
        dom = parse_xml(data)

        return {
            'weather': dom.getElementsByTagName('weather')[0].childNodes[0].data,
            'temperature': dom.getElementsByTagName('temp_c')[0].childNodes[0].data,
            'humidity': dom.getElementsByTagName('relative_humidity')[0].childNodes[0].data.replace("%", ""),
            'wind_direction': dom.getElementsByTagName('wind_dir')[0].childNodes[0].data,
            'wind_speed': str(round(float(dom.getElementsByTagName('wind_mph')[0].childNodes[0].data) * 1.609, 1)),
            'pressure': dom.getElementsByTagName('pressure_mb')[0].childNodes[0].data,
            'visibility': dom.getElementsByTagName('visibility_km')[0].childNodes[0].data,
            'icon': dom.getElementsByTagName('icon')[0].childNodes[0].data
            }
