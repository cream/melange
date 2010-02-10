import thread
import gobject

from cream.contrib.melange import api

import facebook

import gtk.gdk
import javascriptcore as jscore


API_KEY = 'd9dc0a6d7099624b7a8a551ae77be974'
SECRET_KEY = 'c324e15be447b70eefc404aaf5835412'

@api.register
class API(api.WidgetAPI):

    def __init__(self, widget):

        def call_callback(event, arguments=()):
            #print self.widget.js_context.blubb([1, 'aa']) # This works.
            if event == 'authenticated':
                self.callbacks[event]()
            else:
                self.callbacks[event](*arguments) # SIGSEGV

        self.callbacks = {}

        self.widget = widget

        self._facebook = Facebook()
        self._facebook.connect('authenticated', lambda *x: gobject.timeout_add(0, call_callback, ('authenticated')))
        self._facebook.connect('update-friends', lambda source, friends: gobject.timeout_add(0, call_callback, 'update-friends', (friends,)))


    def authenticate(self):
        thread.start_new_thread(self._facebook.authenticate, ())


    def add_callback(self, event, cb):
        """ Registering a callback function... """

        self.callbacks[event] = cb


    def request_friends(self):
        """ Request friends from Facebook... """

        thread.start_new_thread(self._facebook.list_friends, ())


class Facebook(gobject.GObject):

    __gtype_name__ = 'Facebook'
    __gsignals__ = {
        'authenticated': (gobject.SIGNAL_RUN_LAST, gobject.TYPE_NONE, ()),
        'update-friends': (gobject.SIGNAL_RUN_LAST, gobject.TYPE_NONE, (gobject.TYPE_PYOBJECT,))
        }

    def __init__(self):

        gobject.GObject.__init__(self)

        self.api = facebook.Facebook(API_KEY, SECRET_KEY)


    def authenticate(self):

        print "AUTHENTICATING..."

        """
        self.api.auth.createToken()
        self.api.login(True)
        res = self.api.auth.getSession()
        """

        gobject.timeout_add(0, lambda: self.emit('authenticated'))


    def list_friends(self):

        print "RETRIEVING FRIEND LIST..."

        """
        friends = self.api.friends.get()
        #infos = self.api.users.getInfo(friends, ['first_name', 'last_name', 'name'])
        #print infos
        """

        friends = [1, 2, 3, 4, 5]
        
        gobject.timeout_add(0, lambda: self.emit('update-friends', friends))

        print "RETRIEVED FRIEND LIST"


    def get_notifications(self):

        return self.api.notifications.get()
