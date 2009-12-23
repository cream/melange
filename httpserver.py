import os
import json
from bottle import route, send_file, abort, run, request
import thread
import json

import cream.ipc

import gtk

import bottle
bottle.debug(False)

MELANGE = None
OBJECT_CACHE = {}

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
        print send_file(file, path)
        return send_file(file, path)


    @route('/ipc/call', method='POST')
    def ipc_call():

        if OBJECT_CACHE.has_key(':'.join([request.POST['bus'], request.POST['object']])):
            obj = OBJECT_CACHE[':'.join([request.POST['bus'], request.POST['object']])]
        else:
            obj = cream.ipc.get_object(request.POST['bus'], request.POST['object'], 'org.cream.collector')
            OBJECT_CACHE[':'.join([request.POST['bus'], request.POST['object']])] = obj

        met = getattr(obj, request.POST['method'])
        ret = met(*json.loads(request.POST['arguments']))

        return json.dumps(ret)


    def run(self):
        thread.start_new_thread(run, (), dict(host='localhost', port=8080, quiet=True))
