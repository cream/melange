import os
import json
from bottle import route, send_file, abort, run, request
import thread

import bottle
bottle.debug(False)

MELANGE = None

class HttpServer(object):
    """
    HttpServer for serving static (HTML|JS|CSS) files and proxying DBus for
    javascript.

    Instantiated by the `melange.Melange` class.
    """
    def __init__(self, melange):

        global MELANGE
        MELANGE = melange


    @route(r'/widgets/:instance/:skin/(?P<file>.*)')
    def widget_files(instance, skin, file):

        w = MELANGE.instances[instance]
        path = os.path.join(w.meta['path'], 'skins', w.skins[skin]['path'])
        return send_file(file, path)


    @route(r'/common/(?P<file>.*)')
    def common_files(file):

        path = os.path.join(MELANGE._base_path, 'data')
        return send_file(file, path)


    @route('/ipc/:domain/:method', method='POST')
    def ipc_call(domain, method):

        parameters = json.loads(request.POST['data'])
        result = DBUS_CALL(request.POST['domain'], request.POST['method'], parameters)
        return TO_JSON(result)


    def run(self):
        thread.start_new_thread(run, (), dict(host='localhost', port=8080, quiet=True))
