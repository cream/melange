#!/usr/bin/env python

from gi.repository import Gtk as gtk, GdkPixbuf as gdkpixbuf
from os.path import join, dirname

from categories import categories

ICON_SIZE_SMALL = 24
ICON_SIZE_BIG = 48

AUTHOR = u'{0} <{1}>'
class AddWidgetDialog(object):

    def __init__(self, widgets):
        self.widgets = {}

        interface = gtk.Builder()
        interface.add_from_file(join(dirname(__file__), 'add_dialog.glade'))

        self.dialog =  interface.get_object('dialog')
        self.category_liststore =  interface.get_object('categories')
        self.category_view =  interface.get_object('category_view')
        self.widget_liststore =  interface.get_object('widgets')
        self.widget_view =  interface.get_object('widget_view')
        self.category_image =  interface.get_object('category_image')
        self.category_description =  interface.get_object('category_description')

        # connect signals
        self.dialog.connect('delete_event', lambda *x: self.dialog.hide())
        self.category_view.connect('cursor-changed',
            lambda *x: self.on_category_change()
        )

        # add the categories to the liststore alphabetically
        categories_ = sorted(categories.iteritems(), key=lambda c: c[1]['name'])

        theme = gtk.IconTheme.get_default()
        for id, category in categories_:
            icon_info = theme.lookup_icon(category['icon'], ICON_SIZE_SMALL, 0)
            icon = gdkpixbuf.Pixbuf.new_from_file_at_size(
                icon_info.get_filename(),
                ICON_SIZE_SMALL,
                ICON_SIZE_SMALL
            )

            self.category_liststore.append((category['name'], id, icon))

        # group widgets into categories
        for widget in widgets:
            if not widget.get('categories'):
                category = 'org.cream.melange.CategoryMiscellaneous'
                self._add_to_category(category, widget)
            for category in widget['categories']:
                self._add_to_category(category['id'], widget)

        self.category_view.set_cursor(0)

    def _add_to_category(self, category, widget):
        if category in self.widgets:
            self.widgets[category].append(widget)
        else:
            self.widgets[category] = [widget]

    def update_info_bar(self):
        """
        Update the description of a category which is displayed above
        the widget listview
        """

        category = categories[self.selected_category]
        theme = gtk.IconTheme.get_default()
        icon_info = theme.lookup_icon(category['icon'], ICON_SIZE_BIG, 0)
        icon = gdkpixbuf.Pixbuf.new_from_file_at_size(
            icon_info.get_filename(),
            ICON_SIZE_BIG,
            ICON_SIZE_BIG
        )

        self.category_image.set_from_pixbuf(icon)

        description = split_string(category['description'])
        self.category_description.set_text(description)

    def on_category_change(self):
        """
        Whenever a new category is selected, clear the liststore and add the
        widgets corresponding to the category to it
        """

        self.widget_liststore.clear()
        self.update_info_bar()
        category = self.selected_category
        if not category in self.widgets:
            return

        for widget in self.widgets[category]:
            if 'icon' in widget:
                path = widget['icon']
            else:
                path = join(dirname(__file__), 'images/melange.png')

            icon = gdkpixbuf.Pixbuf.new_from_file_at_size(path, 35, 35)
            label = u'<b>{0}</b>\n{1}'.format(
                widget['name'],
                split_string(widget['description'])
            )
            self.widget_liststore.append((icon, label, widget['id']))

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

    def run(self):

        self.dialog.show_all()

        widget = None
        if self.dialog.run() == 1:
            widget = self.selected_widget

        self.dialog.hide()

        return widget


class AboutDialog(gtk.AboutDialog):

    def __init__(self, manifest):

        gtk.AboutDialog.__init__(self)

        self.connect('response', lambda *x: self.hide())
        self.connect('delete-event', lambda *x: True)

        self.set_program_name(manifest['name'])

        developers, designers = [], []

        for author in manifest['authors']:
            author_info = AUTHOR.format(author.get('name'), author.get('mail'))
            if author.get('type') == 'developer':
                developers.append(author_info)
            elif author.get('type') == 'designer':
                designers.append(author_info)

        self.set_authors(developers)
        self.set_artists(designers)

        if manifest.get('icon', None):
            icon = gdkpixbuf.Pixbuf.new_from_file_at_size(
                manifest['icon'],
                ICON_SIZE_BIG,
                ICON_SIZE_BIG
            )
            self.set_logo(icon)

        self.set_comments(manifest['description'])


def split_string(description):
    """split a long string into multiple lines"""
    lst = []
    chars = 0
    for word in description.split():
        if chars > 30:
            lst.append(u'\n')
            chars = 0
        lst.append(word)
        chars += len(word)

    return u' '.join(lst)
