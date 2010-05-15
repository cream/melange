from cream.contrib.melange import api

from lxml.etree import parse
from urllib import urlopen
from contextlib import closing

import re

@api.register('identica')
class Identica(api.API):

    def __init__(self):
    
        api.API.__init__(self)

        self.identica = 'https://identi.ca/api/statusnet/groups/timeline/{0}.xml'
        self.regex = 'http?://.*'

    @api.expose
    def get_data(self, group):
        url = self.identica.format(group)
        with closing(urlopen(url)) as xml:
            raw_data = parse(xml)

        data = []      
        posts = raw_data.findall('status')
   
        for post in posts:
            text = post.find('text').text
            # convert links to <a href>
            try:
                link = re.search(self.regex, text).group().strip()
                text = text.replace(link, '<a href="{0}">{0} </a>'.format(link))
            except:
                pass

            author = post.find('user').find('screen_name').text
            time = post.find('created_at').text.split()
            time = ' '.join(time[1:4])

            data.append({'text': text,
                         'author': author,
                         'time': time
            })

        return data


if __name__ == '__main__':
    test = Identica()
    data = test.get_data('cream')
    print data

