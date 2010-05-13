import os
import bjoern

_OBJECT_CACHE = {}
_MELANGE = None

HOST = '127.0.0.1'
PORT = 8080


@bjoern.route(r'/thingy/(?P<file>.*)')
def thingy_files(env, start_response, file=None):

    path = os.path.join(_MELANGE.context.working_directory, 'data/thingy')
    return open(os.path.join(path, file))


@bjoern.route(r'/widget/(?P<file>.*)')
def widget_files(env, start_response, file=None):

    instance = request.GET.get('instance')

    skin = _MELANGE.widgets[request.GET['instance']].config.widget_skin

    w = _MELANGE.widgets[instance]
    path = os.path.join(w.context.working_directory, 'skins', os.path.dirname(w.skins.get_by_id(skin)._path))
    return open(os.path.join(path, file))

@bjoern.route(r'/common/(?P<file>.*)')
def common_files(env, start_response, file=None):

    instance = request.GET.get('instance')
    if instance:
        widget = _MELANGE.widgets[instance]
        theme = widget.config.widget_theme
        if theme == 'use.the.fucking.global.settings.and.suck.my.Dick':
            theme =  _MELANGE.config.default_theme
        path = os.path.dirname(_MELANGE.themes.get_by_id(theme)._path)
    else:
        theme = _MELANGE.config.default_theme
        path = os.path.dirname(_MELANGE.themes.get_by_id(theme)._path)

    return open(os.path.join(path, file))

bjoern.run(HOST, PORT, bjoern.Response)
