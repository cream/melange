import thread

from cream.contrib.melange import api

import pasty
import gtk

@api.register('paste')
class Paste(api.API):

    def __init__(self):

        api.API.__init__(self)

        self.language = 'text'
        self.clipboard = gtk.clipboard_get()


    def set_language(self, lang):
        self.language = lang


    def paste_clipboard(self, cb):

        text = self.clipboard.wait_for_text()

        t = api.Thread(self._paste, args=(text, self.language), callback=cb)
        t.start()


    def paste_file(self, cb):

        chooser = gtk.FileChooserDialog(buttons=(gtk.STOCK_CANCEL, gtk.RESPONSE_REJECT,
                    gtk.STOCK_OK, gtk.RESPONSE_ACCEPT))
        response = chooser.run()
        if response == gtk.RESPONSE_ACCEPT:
            fh = open(chooser.get_filename())
            text = fh.read()
            fh.close()
            response = chooser.destroy()
            t = api.Thread(self._paste, (text, self.language), callback=cb)
            t.start()
        elif response == gtk.RESPONSE_REJECT:
            response = chooser.destroy()


    def _paste(self, text, language):
        url = pasty.pocoo.do_paste(text, language)
        return url, text
