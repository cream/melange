import cream.contrib.melange
from cream.contrib.melange import widgets

@cream.extensions.register
class PlaygroundApplet(cream.contrib.melange.Applet):

    def __init__(self, *args):

        cream.contrib.melange.Applet.__init__(self, *args)

        self.widget._size = (160, 100)

        self.background = widgets.Background()
        self.widget.add(self.background)
        self.background.render()

        self.interface.add_widget(self.widget)
