import thread

from cream.contrib.melange import api

import pasty
import gtk

@api.register('paste')
class Paste(api.API):

    def __init__(self, widget):

        self.widget = widget

        self.language = 'text'

        self.clipboard = gtk.clipboard_get()


    def set_language(self, lang):
        self.language = lang


    def paste_clipboard(self):

        text = self.clipboard.wait_for_text()
        thread.start_new_thread(self._paste, (text, self.language))


    def paste_file(self):

        chooser = gtk.FileChooserDialog(buttons=(gtk.STOCK_CANCEL, gtk.RESPONSE_REJECT,
                    gtk.STOCK_OK, gtk.RESPONSE_ACCEPT))
        response = chooser.run()
        if response == gtk.RESPONSE_ACCEPT:
            fh = open(chooser.get_filename())
            text = fh.read()
            fh.close()
            response = chooser.destroy()
            thread.start_new_thread(self._paste, (text, self.language))
        elif response == gtk.RESPONSE_REJECT:
            response = chooser.destroy()


    def _paste(self, text, language):
        url = pasty.pocoo.do_paste(text, language)
        self.emit_event('pasted', url)
