# auto generated. yay.
import ooxcb
from ooxcb.resource import get_internal
from ooxcb.types import SIZES, make_array, build_list
try:
    import cStringIO as StringIO
except ImportError:
    import StringIO
from struct import pack, unpack, calcsize

def unpack_from_stream(fmt, stream, offset=0):
    if offset:
        stream.seek(offset, 1)
    s = stream.read(calcsize(fmt))
    return unpack(fmt, s)


MAJOR_VERSION = 1
MINOR_VERSION = 13
key = ooxcb.ExtensionKey("RECORD")

class HType(object):
    FromServerTime = 1
    FromClientTime = 2
    FromClientSequence = 4

class CS(object):
    CurrentClients = 1
    FutureClients = 2
    AllClients = 3

class Category(object):
    FromServer = 0
    FromClient = 1
    ClientStarted = 2
    ClientDied = 3
    StartOfData = 4
    EndOfData = 5

class recordExtension(ooxcb.Extension):
    header = "record"
    def query_version(self, major_version, minor_version):
        buf = StringIO.StringIO()
        buf.write(pack("=xxxxHH", major_version, minor_version))
        return self.conn.record.send_request(ooxcb.Request(self.conn, buf.getvalue(), 0, False, True), \
            QueryVersionCookie(),
            QueryVersionReply)

    def query_version_unchecked(self, major_version, minor_version):
        buf = StringIO.StringIO()
        buf.write(pack("=xxxxHH", major_version, minor_version))
        return self.conn.record.send_request(ooxcb.Request(self.conn, buf.getvalue(), 0, False, False), \
            QueryVersionCookie(),
            QueryVersionReply)

    def create_context_checked(self, context, element_header, client_specs, ranges):
        num_client_specs = len(client_specs)
        num_ranges = len(ranges)
        context = get_internal(context)
        element_header = get_internal(element_header)
        buf = StringIO.StringIO()
        buf.write(pack("=xxxxIBxxxII", context, element_header, num_client_specs, num_ranges))
        buf.write(make_array(client_specs, "I"))
        for elt in ranges:
            elt.build(buf)
        return self.conn.record.send_request(ooxcb.Request(self.conn, buf.getvalue(), 1, True, True), \
            ooxcb.VoidCookie())

    def create_context(self, context, element_header, client_specs, ranges):
        num_client_specs = len(client_specs)
        num_ranges = len(ranges)
        context = get_internal(context)
        element_header = get_internal(element_header)
        buf = StringIO.StringIO()
        buf.write(pack("=xxxxIBxxxII", context, element_header, num_client_specs, num_ranges))
        buf.write(make_array(client_specs, "I"))
        for elt in ranges:
            elt.build(buf)
        return self.conn.record.send_request(ooxcb.Request(self.conn, buf.getvalue(), 1, True, False), \
            ooxcb.VoidCookie())

class ElementHeader(ooxcb.Resource):
    def __init__(self, conn, xid):
        ooxcb.Resource.__init__(self, conn, xid)

class ClientInfo(ooxcb.Struct):
    def __init__(self, conn):
        ooxcb.Struct.__init__(self, conn)
        self.client_resource = None
        self.num_ranges = None
        self.ranges = []

    def read(self, stream):
        self._address = stream.address
        root = stream.tell()
        _unpacked = unpack_from_stream("=II", stream)
        self.client_resource = Clientspec(self.conn, _unpacked[0])
        self.num_ranges = _unpacked[1]
        self.ranges = ooxcb.List(self.conn, stream, self.num_ranges, Range, 24)
        self.size = stream.tell() - root

    def build(self, stream):
        count = 0
        stream.write(pack("=II", get_internal(self.client_resource), self.num_ranges))
        count += 8
        build_list(self.conn, stream, self.ranges, Range)

class BadContext(ooxcb.ProtocolException):
    pass

class ContextError(ooxcb.Error):
    def __init__(self, conn):
        ooxcb.Error.__init__(self, conn)
        self.invalid_record = None

    def read(self, stream):
        self._address = stream.address
        _unpacked = unpack_from_stream("=xxxxI", stream)
        self.invalid_record = _unpacked[0]

    def build(self, stream):
        count = 0
        stream.write(pack("=xxxxI", self.invalid_record))

class EnableContextCookie(ooxcb.Cookie):
    pass

class QueryVersionCookie(ooxcb.Cookie):
    pass

class GetContextCookie(ooxcb.Cookie):
    pass

class GetContextReply(ooxcb.Reply):
    def __init__(self, conn):
        ooxcb.Reply.__init__(self, conn)
        self.enabled = None
        self.element_header = None
        self.num_intercepted_clients = None
        self.intercepted_clients = []

    def read(self, stream):
        self._address = stream.address
        _unpacked = unpack_from_stream("=xBxxxxxxBxxxIxxxxxxxxxxxxxxxx", stream)
        self.enabled = _unpacked[0]
        self.element_header = ElementHeader(self.conn, _unpacked[1])
        self.num_intercepted_clients = _unpacked[2]
        self.intercepted_clients = ooxcb.List(self.conn, stream, self.num_intercepted_clients, ClientInfo, -1)

    def build(self, stream):
        count = 0
        stream.write(pack("=xBxxxxxxBxxxIxxxxxxxxxxxxxxxx", self.enabled, get_internal(self.element_header), self.num_intercepted_clients))
        count += 32
        build_list(self.conn, stream, self.intercepted_clients, ClientInfo)

class Range16(ooxcb.Struct):
    def __init__(self, conn):
        ooxcb.Struct.__init__(self, conn)
        self.first = None
        self.last = None

    def read(self, stream):
        self._address = stream.address
        _unpacked = unpack_from_stream("=HH", stream)
        self.first = _unpacked[0]
        self.last = _unpacked[1]

    def build(self, stream):
        count = 0
        stream.write(pack("=HH", self.first, self.last))

    @classmethod
    def create(cls, conn, first, last):
        self = cls(conn)
        self.first = first
        self.last = last
        return self

class ExtRange(ooxcb.Struct):
    def __init__(self, conn):
        ooxcb.Struct.__init__(self, conn)
        self.major = None
        self.minor = None

    def read(self, stream):
        self._address = stream.address
        root = stream.tell()
        self.major = Range8.create_from_stream(self.conn, stream)
        stream.seek(ooxcb.type_pad(4, stream.tell() - root), 1)
        self.minor = Range16.create_from_stream(self.conn, stream)

    def build(self, stream):
        count = 0
        self.major.build(stream)
        self.minor.build(stream)

    @classmethod
    def create(cls, conn, major_first, major_last, minor_first, minor_last):
        self = cls(conn)
        self.major = Range8.create(conn, major_first, major_last)
        self.minor = Range16.create(conn, minor_first, minor_last)
        return self

class Range(ooxcb.Struct):
    def __init__(self, conn):
        ooxcb.Struct.__init__(self, conn)
        self.core_requests = None
        self.core_replies = None
        self.ext_requests = None
        self.ext_replies = None
        self.delivered_events = None
        self.device_events = None
        self.errors = None
        self.client_started = None
        self.client_died = None

    def read(self, stream):
        self._address = stream.address
        root = stream.tell()
        self.core_requests = Range8.create_from_stream(self.conn, stream)
        stream.seek(ooxcb.type_pad(2, stream.tell() - root), 1)
        self.core_replies = Range8.create_from_stream(self.conn, stream)
        stream.seek(ooxcb.type_pad(6, stream.tell() - root), 1)
        self.ext_requests = ExtRange.create_from_stream(self.conn, stream)
        stream.seek(ooxcb.type_pad(6, stream.tell() - root), 1)
        self.ext_replies = ExtRange.create_from_stream(self.conn, stream)
        stream.seek(ooxcb.type_pad(2, stream.tell() - root), 1)
        self.delivered_events = Range8.create_from_stream(self.conn, stream)
        stream.seek(ooxcb.type_pad(2, stream.tell() - root), 1)
        self.device_events = Range8.create_from_stream(self.conn, stream)
        stream.seek(ooxcb.type_pad(2, stream.tell() - root), 1)
        self.errors = Range8.create_from_stream(self.conn, stream)
        stream.seek(ooxcb.type_pad(4, stream.tell() - root), 1)
        _unpacked = unpack_from_stream("=BB", stream)
        self.client_started = _unpacked[0]
        self.client_died = _unpacked[1]

    def build(self, stream):
        count = 0
        self.core_requests.build(stream)
        self.core_replies.build(stream)
        self.ext_requests.build(stream)
        self.ext_replies.build(stream)
        self.delivered_events.build(stream)
        self.device_events.build(stream)
        self.errors.build(stream)
        stream.write(pack("=BB", self.client_started, self.client_died))

    @classmethod
    def create(cls, conn, core_requests, core_replies, ext_requests, ext_replies, delivered_events, device_events, errors, client_started, client_died):
        self = cls(conn)
        self.core_requests = Range8.create(conn, *core_requests)
        self.core_replies = Range8.create(conn, *core_replies)
        self.ext_requests = ExtRange.create(conn, *ext_requests)
        self.ext_replies = ExtRange.create(conn, *ext_replies)
        self.delivered_events = Range8.create(conn, *delivered_events)
        self.device_events = Range8.create(conn, *device_events)
        self.errors = Range8.create(conn, *errors)
        self.client_started = client_started
        self.client_died = client_died
        return self

class Context(ooxcb.Resource):
    def __init__(self, conn, xid):
        ooxcb.Resource.__init__(self, conn, xid)

    def register_clients_checked(self, element_header, client_specs, ranges):
        num_client_specs = len(client_specs)
        num_ranges = len(ranges)
        context = get_internal(self)
        element_header = get_internal(element_header)
        buf = StringIO.StringIO()
        buf.write(pack("=xxxxIBxxxII", context, element_header, num_client_specs, num_ranges))
        buf.write(make_array(client_specs, "I"))
        for elt in ranges:
            elt.build(buf)
        return self.conn.record.send_request(ooxcb.Request(self.conn, buf.getvalue(), 2, True, True), \
            ooxcb.VoidCookie())

    def register_clients(self, element_header, client_specs, ranges):
        num_client_specs = len(client_specs)
        num_ranges = len(ranges)
        context = get_internal(self)
        element_header = get_internal(element_header)
        buf = StringIO.StringIO()
        buf.write(pack("=xxxxIBxxxII", context, element_header, num_client_specs, num_ranges))
        buf.write(make_array(client_specs, "I"))
        for elt in ranges:
            elt.build(buf)
        return self.conn.record.send_request(ooxcb.Request(self.conn, buf.getvalue(), 2, True, False), \
            ooxcb.VoidCookie())

    def unregister_clients_checked(self, client_specs):
        num_client_specs = len(client_specs)
        context = get_internal(self)
        buf = StringIO.StringIO()
        buf.write(pack("=xxxxII", context, num_client_specs))
        buf.write(make_array(client_specs, "I"))
        return self.conn.record.send_request(ooxcb.Request(self.conn, buf.getvalue(), 3, True, True), \
            ooxcb.VoidCookie())

    def unregister_clients(self, client_specs):
        num_client_specs = len(client_specs)
        context = get_internal(self)
        buf = StringIO.StringIO()
        buf.write(pack("=xxxxII", context, num_client_specs))
        buf.write(make_array(client_specs, "I"))
        return self.conn.record.send_request(ooxcb.Request(self.conn, buf.getvalue(), 3, True, False), \
            ooxcb.VoidCookie())

    def get(self):
        context = get_internal(self)
        buf = StringIO.StringIO()
        buf.write(pack("=xxxxI", context))
        return self.conn.record.send_request(ooxcb.Request(self.conn, buf.getvalue(), 4, False, True), \
            GetContextCookie(),
            GetContextReply)

    def get_unchecked(self):
        context = get_internal(self)
        buf = StringIO.StringIO()
        buf.write(pack("=xxxxI", context))
        return self.conn.record.send_request(ooxcb.Request(self.conn, buf.getvalue(), 4, False, False), \
            GetContextCookie(),
            GetContextReply)

    def enable(self):
        context = get_internal(self)
        buf = StringIO.StringIO()
        buf.write(pack("=xxxxI", context))
        return self.conn.record.send_request(ooxcb.Request(self.conn, buf.getvalue(), 5, False, True), \
            EnableContextCookie(),
            EnableContextReply)

    def enable_unchecked(self):
        context = get_internal(self)
        buf = StringIO.StringIO()
        buf.write(pack("=xxxxI", context))
        return self.conn.record.send_request(ooxcb.Request(self.conn, buf.getvalue(), 5, False, False), \
            EnableContextCookie(),
            EnableContextReply)

    def disable_checked(self):
        context = get_internal(self)
        buf = StringIO.StringIO()
        buf.write(pack("=xxxxI", context))
        return self.conn.record.send_request(ooxcb.Request(self.conn, buf.getvalue(), 6, True, True), \
            ooxcb.VoidCookie())

    def disable(self):
        context = get_internal(self)
        buf = StringIO.StringIO()
        buf.write(pack("=xxxxI", context))
        return self.conn.record.send_request(ooxcb.Request(self.conn, buf.getvalue(), 6, True, False), \
            ooxcb.VoidCookie())

    def free_checked(self):
        context = get_internal(self)
        buf = StringIO.StringIO()
        buf.write(pack("=xxxxI", context))
        return self.conn.record.send_request(ooxcb.Request(self.conn, buf.getvalue(), 7, True, True), \
            ooxcb.VoidCookie())

    def free(self):
        context = get_internal(self)
        buf = StringIO.StringIO()
        buf.write(pack("=xxxxI", context))
        return self.conn.record.send_request(ooxcb.Request(self.conn, buf.getvalue(), 7, True, False), \
            ooxcb.VoidCookie())

    @classmethod
    def create(cls, conn, element_header, client_specs, ranges):
        xid = conn.generate_id()
        ctx = Context(conn, xid)
        conn.record.create_context_checked(ctx, element_header, client_specs, ranges).check()
        conn.add_to_cache(xid, ctx)
        return ctx

class Clientspec(ooxcb.Resource):
    def __init__(self, conn, xid):
        ooxcb.Resource.__init__(self, conn, xid)

class Range8(ooxcb.Struct):
    def __init__(self, conn):
        ooxcb.Struct.__init__(self, conn)
        self.first = None
        self.last = None

    def read(self, stream):
        self._address = stream.address
        _unpacked = unpack_from_stream("=BB", stream)
        self.first = _unpacked[0]
        self.last = _unpacked[1]

    def build(self, stream):
        count = 0
        stream.write(pack("=BB", self.first, self.last))

    @classmethod
    def create(cls, conn, first, last):
        self = cls(conn)
        self.first = first
        self.last = last
        return self

class EnableContextReply(ooxcb.Reply):
    def __init__(self, conn):
        ooxcb.Reply.__init__(self, conn)
        self.category = None
        self.element_header = None
        self.client_swapped = None
        self.xid_base = None
        self.server_time = None
        self.rec_sequence_num = None
        self.data = []

    def read(self, stream):
        self._address = stream.address
        _unpacked = unpack_from_stream("=xBxxxxxxBBxxIIIxxxxxxxx", stream)
        self.category = _unpacked[0]
        self.element_header = ElementHeader(self.conn, _unpacked[1])
        self.client_swapped = _unpacked[2]
        self.xid_base = _unpacked[3]
        self.server_time = _unpacked[4]
        self.rec_sequence_num = _unpacked[5]
        self.data = ooxcb.List(self.conn, stream, (self.length * 4), 'B', 1)

    def build(self, stream):
        count = 0
        stream.write(pack("=xBxxxxxxBBxxIIIxxxxxxxx", self.category, get_internal(self.element_header), self.client_swapped, self.xid_base, self.server_time, self.rec_sequence_num))
        count += 32
        build_list(self.conn, stream, self.data, 'B')

class QueryVersionReply(ooxcb.Reply):
    def __init__(self, conn):
        ooxcb.Reply.__init__(self, conn)
        self.major_version = None
        self.minor_version = None

    def read(self, stream):
        self._address = stream.address
        _unpacked = unpack_from_stream("=xxxxxxxxHH", stream)
        self.major_version = _unpacked[0]
        self.minor_version = _unpacked[1]

    def build(self, stream):
        count = 0
        stream.write(pack("=xxxxxxxxHH", self.major_version, self.minor_version))

_events = {
}

_errors = {
    0: (ContextError, BadContext),
}

for ev in _events.itervalues():
    if isinstance(ev.event_target_class, str):
        ev.event_target_class = globals()[ev.event_target_class]

ooxcb._add_ext(key, recordExtension, _events, _errors)
def mixin():
    pass
