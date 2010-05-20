import os
import urlparse
import bjoern
from bjoern import run
from cream.util import cached_property

HOST = '127.0.0.1'
PORT = 8765


class MelangeResponse(bjoern.Response):
    @cached_property
    def GET(self):
        return urlparse.parse_qs(urlparse.urlparse(self['PATH_INFO']))


@bjoern.route(r'/thingy/(?P<file>.*)')
def thingy_files(env, start_response, file=None):
    path = os.path.join(env._melange.context.working_directory, 'data/thingy')
    return open(os.path.join(path, file))


@bjoern.route(r'/widget/(?P<file>.*)')
def widget_files(env, start_response, file=None):
    widget = env._melange.widgets[env.GET['instance']]
    return open(os.path.join(widget.get_skin_path(), file))


@bjoern.route(r'/common/(?P<file>.*)')
def common_files(env, start_response, file=None):
    theme = env._melange.config.default_theme

    instance = env.GET.get('instance')
    if instance:
        theme_ = env._melange.widgets[instance].config.widget_theme
        if theme != 'use.the.fucking.global.settings.and.suck.my.Dick':
            theme = theme_

    path = os.path.dirname(env._melange.themes.get_by_id(theme)._path)
    return open(os.path.join(path, file))
