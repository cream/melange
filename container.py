import gobject
import cairo
import gtk
import webkit
import javascriptcore as jscore

from widget import MelangeWindow
from common import HTTPSERVER_BASE_URL, \
                   MOUSE_BUTTON_LEFT, MOUSE_BUTTON_MIDDLE, MOUSE_BUTTON_RIGHT

class ContainerWindow(MelangeWindow):

    __gsignals__ = {
        'begin-move': (gobject.SIGNAL_RUN_LAST, gobject.TYPE_NONE, ()),
        'end-move': (gobject.SIGNAL_RUN_LAST, gobject.TYPE_NONE, ()),
    }

    def __init__(self):

        MelangeWindow.__init__(self)

        self.set_property('accept-focus', False)
        self.set_type_hint(gtk.gdk.WINDOW_TYPE_HINT_DOCK)
        self.set_keep_below(True)

        self.view = webkit.WebView()
        self.view.set_transparent(True)

        self.view.connect('button-press-event', self.button_press_cb)
        self.view.connect('button-release-event', self.button_release_cb)

        self.add(self.view)

        self.js_context = jscore.JSContext(self.view.get_main_frame().get_global_context()).globalObject

        url = HTTPSERVER_BASE_URL + '/chrome/container.html'
        self.view.open(url)


    def button_press_cb(self, source, event):
        """ Handle clicking on the widget (e. g. by showing context menu). """

        if event.button == MOUSE_BUTTON_RIGHT:
            pass
            return True
        elif event.button == MOUSE_BUTTON_MIDDLE:
            self.emit('begin-move')
            return True


    def button_release_cb(self, source, event):

        if event.button == MOUSE_BUTTON_MIDDLE:
            self.emit('end-move')
            return True
