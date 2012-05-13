#!/usr/bin/env python

from gi.repository import GObject as gobject, Gtk as gtk, Gdk as gdk, GdkPixbuf as pixbuf

from os.path import join, dirname

ICON_SIZE_SMALL = 24
ICON_SIZE_MEDIUM = 48
ICON_SIZE_BIG = 64

AUTHOR = '{0} <{1}>'


categories = {
    'org.cream.melange.CategoryInternet': {
        'name': 'Internet',
        'icon': 'applications-internet',
        'description': 'Interact with the web!'
    },
    'org.cream.melange.CategoryMultimedia': {
        'name': 'Multimedia',
        'icon': 'applications-multimedia',
        'description': 'Adds multimedia features to your desktop.'
    },
    'org.cream.melange.CategoryTools': {
        'name': 'Tools',
        'icon': 'applications-accessories',
        'description': 'Helping you to make your life easier.'
    },
    'org.cream.melange.CategoryGames': {
        'name': 'Games',
        'icon': 'applications-games',
        'description': 'Gaming for in between? Here you go!'
    },
    'org.cream.melange.CategoryMiscellaneous': {
        'name': 'Miscellaneous',
        'icon': 'applications-other',
        'description': 'Various widgets.'
    }

}

class AddWidgetDialog(gobject.GObject):

    __gtype_name__ = 'AddWidgetDialog'
    __gsignals__ = {
        'load-widget': (gobject.SIGNAL_RUN_LAST, None, (gobject.TYPE_PYOBJECT,))
    }

    def __init__(self, widgets):

        gobject.GObject.__init__(self)

        self.widgets = widgets
        self.widgets_cat = {}

        interface = gtk.Builder()
        interface.add_from_file(join(dirname(__file__), 'add_dialog.glade'))

        self.dialog =  interface.get_object('dialog')
        self.category_liststore =  interface.get_object('categories')
        self.category_view =  interface.get_object('category_view')
        self.widget_liststore =  interface.get_object('widgets')
        self.widget_view =  interface.get_object('widget_view')
        self.category_image =  interface.get_object('category_image')
        self.category_description =  interface.get_object('category_description')
        self.add_button = interface.get_object('add')

        # connect signals
        self.dialog.connect('delete_event', lambda *x: self.dialog.hide())
        self.category_view.connect('cursor-changed',
                                    lambda *x: self.on_category_change()
        )
        self.add_button.connect('clicked', self.on_widget_added)

        # add the categories to the liststore alphabetically
        categories_ = sorted(categories.iteritems(),
                             key=lambda c: c[1]['name']
        )

        theme = gtk.IconTheme.get_default()
        for id, category in categories_:
            icon_info = theme.lookup_icon(category['icon'], ICON_SIZE_SMALL, 0)
            icon = pixbuf.Pixbuf.new_from_file_at_size(icon_info.get_filename(),
                                                        ICON_SIZE_SMALL, ICON_SIZE_SMALL)

            self.category_liststore.append((category['name'], id, icon))

        for widget in widgets:
            self._add_to_category('org.cream.melange.CategoryMiscellaneous', widget)

        self.category_view.set_cursor(0)


    def show(self):

        self.dialog.show_all()
        self.dialog.run()
        self.dialog.hide()


    def _add_to_category(self, category, widget):
        if category in self.widgets_cat:
            self.widgets_cat[category].append(widget)
        else:
            self.widgets_cat[category] = [widget]

    def update_info_bar(self):
        """
        Update the description of a category which is displayed above
        the widget listview
        """

        category = categories[self.selected_category]
        theme = gtk.IconTheme.get_default()
        icon_info = theme.lookup_icon(category['icon'], ICON_SIZE_MEDIUM, 0)
        icon = pixbuf.Pixbuf.new_from_file_at_size(icon_info.get_filename(),
                                                    ICON_SIZE_MEDIUM, ICON_SIZE_MEDIUM)

        self.category_image.set_from_pixbuf(icon)

        description = category['description']
        self.category_description.set_text(description)

    def on_category_change(self):
        """
        Whenever a new category is selected, clear the liststore and add the
        widgets corresponding to the category to it
        """

        self.widget_liststore.clear()
        self.update_info_bar()
        category = self.selected_category
        if not category in self.widgets_cat:
            return

        for widget in sorted(self.widgets_cat[category], key=lambda w: w['id']):
            path = '/home/kris/projects/cream/src/src/modules/melange/src/melange.png'

            icon = pixbuf.Pixbuf.new_from_file_at_size(path, 35, 35)
            name = widget['id'].replace('org.cream.melange.widget.', '')
            label = '<b>{0}</b>\n{1}'.format(name, 'description')
            self.widget_liststore.append((icon, label, widget['id']))


    def on_widget_added(self, *args):

        self.emit('load-widget', self.selected_widget)


    @property
    def selected_widget(self):
        selection = self.widget_view.get_selection()
        model, iter = selection.get_selected()
        if iter:
            return model.get_value(iter, 2)

    @property
    def selected_category(self):
        selection = self.category_view.get_selection()
        model, iter = selection.get_selected()
        return model.get_value(iter, 1)
