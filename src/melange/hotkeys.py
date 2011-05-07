import gobject
import gtk
import ctypes

import ooxcb
from ooxcb.protocol import xproto
import record

class HotkeyRecorder(gobject.GObject):

    __gtype_name__ = 'HotkeyRecorder'
    __gsignals__ = {
        'key-press': (gobject.SIGNAL_RUN_LAST, gobject.TYPE_NONE, (gobject.TYPE_INT, gobject.TYPE_INT)),
        'key-release': (gobject.SIGNAL_RUN_LAST, gobject.TYPE_NONE, (gobject.TYPE_INT, gobject.TYPE_INT))
    }

    def __init__(self, hotkeys):

        gobject.GObject.__init__(self)

        self.hotkeys = hotkeys

        self.connection = ooxcb.connect()
        self.connection2 = ooxcb.connect()

        self.ctx = record.Context.create(self.connection, 0, [record.CS.AllClients],
            [record.Range.create(
                self.connection,
                (0, 0),
                (0, 0),
                (0, 0, 0, 0),
                (0, 0, 0, 0),
                (0, 0),
                (xproto.KeyPressEvent.opcode, xproto.KeyReleaseEvent.opcode),
                (0, 0),
                False,
                False
            )])

        self.cookie = self.ctx.enable()
        self.connection.flush()

        res = False
        res = gobject.io_add_watch(
            self.connection.get_file_descriptor(),
            gobject.IO_IN,
            self._ooxcb_callback)


    def _ooxcb_callback(self, source, condition):
        try:
            reply = self.cookie.reply()
        except ctypes.ArgumentError:
            return True
        if reply is not None and reply.category == record.Category.FromServer:
            opcode = reply.data[0]
            event_type = self.connection.events[opcode]
            buf = ctypes.create_string_buffer(''.join(map(chr, reply.data)))
            address = ctypes.addressof(buf)
            evt = event_type.create_from_address(self.connection, address)
            keysym = self.connection2.keysyms.get_keysym(evt.detail, 0)
            modifier_mask = evt.state
            if (keysym, modifier_mask) in self.hotkeys:
                if isinstance(evt, xproto.KeyPressEvent):
                    self.emit('key-press', keysym, modifier_mask)
                elif isinstance(evt, xproto.KeyReleaseEvent):
                    self.emit('key-release', keysym, modifier_mask)
        return True
