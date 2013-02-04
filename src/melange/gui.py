import cairo
from gi.repository import Gtk as gtk, Gdk as gdk



class CompositeBin(gtk.Fixed):

    def __init__(self):

        self.alpha = 1
        self.children = []

        gtk.Fixed.__init__(self)

        self.connect('realize', self.realize_cb)


    def realize_cb(self, widget):
        self.get_parent().connect_after('draw', self.draw_cb)


    def draw_cb(self, widget, ctx):

        ctx.set_operator(cairo.OPERATOR_OVER)
        x, y = widget.get_position()
        width, height = widget.get_allocated_width(), widget.get_allocated_height()
        #widget.get_window().invalidate_rect(widget.get_allocation(), True)
        ctx.rectangle(x, y, width, height)
        ctx.clip()

        for child in self.children:
            alloc = child.get_allocation()
            ctx.move_to(alloc.x, alloc.y)
            gdk.cairo_set_source_window(ctx, child.get_window(), alloc.x, alloc.y)
            ctx.paint()

        return True


    def add(self, child, x, y):
        """
        Add a widget.

        :param child: A `GtkWidget` to add to the `CompositedBin`.
        """

        self.children.append(child)
        child.connect('realize', self.child_realize_cb)
        self.put(child, x, y)


    def remove(self, child):

        gtk.Fixed.remove(self, child)
        self.children.remove(child)


    def child_realize_cb(self, widget):
        try:
            widget.get_window().set_composited(True)
        except:
            pass


    def raise_child(self, child):

        child.get_window().raise_()
        self.children.remove(child)
        self.children.insert(len(self.children), child)
        self.window.invalidate_rect(child.allocation, True)
