from gi.repository import Gdk as gdk


def get_screen_size():

    display = gdk.Display.get_default()
    screen = display.get_default_screen()
    return screen.get_width(), screen.get_height()
