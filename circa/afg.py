import numpy as n

# AFG controls

class AFG_channel(object):
    """
    Class encapsulating a AFG channel
    """

    def __init__(self, bus, channel=None):
        self.bus = bus
        self.channel = channel

    def cmd(self, command):
        if self.channel is not None:
            prefix = 'source%d:' % self.channel
        else:
            prefix = ''
        return prefix + command

    def get_mode(self):
        return self.bus.ask(self.cmd('func?'))

    def set_mode(self, val):
        self.bus.write(self.cmd('func ' + val))

    mode = property(get_mode, set_mode)

    def get_freq(self):
        return float(self.bus.ask(self.cmd('freq?')))

    def set_freq(self, val):
        self.bus.write(self.cmd('freq ' + str(val)))

    freq = property(get_freq, set_freq)

from io import BytesIO

def decode_array(data):
    b = BytesIO(data)
    assert b.read(1) == b'#'
    meta_len = int(b.read(1))
    data_len = int(b.read(meta_len))
    result = b.read(data_len)
    array = n.fromstring(result, dtype='>u2')
    return array

def encode_array(array):
    #assert array.dtype == n.dtype('>u2')
    data = array.astype('>u2').tostring()
    data_len = str(len(data))
    meta_len = str(len(data_len))
    assert len(meta_len) == 1
    return b'#' + meta_len + data_len + data

class Arb(object):
    """
    Class encapsulating the AFG's arbitrary edit memory
    """

    YMAX = 16382

    def __init__(self, bus):
        self.bus = bus

    def get_selected(self):
        return 'EMEM' in self.bus.ask('func?').upper()

    def set_selected(self, val):
        if val:
            self.bus.write('func emem')

    selected = property(get_selected, set_selected)

    def initialize(self, npts, val=None):
        """
        Wipe the edit meory register.

        Sets the register to be `npts` points long,
        where npts is between 2 and 131072 points.

        Optionally, provide `val` to initialize
        all points to a given value of y. Y can be a value
        between 0 and 16382. The default is 8191
        """
        self.bus.write('data:define emem,%d' % npts)
        if val is not None:
            self.add_line(1,npts,int(val))

    def add_line(self, x0, x1, y0, y1=None):
        # 1-based indexing because nothing is sacred
        if y1 is None:
            y1 = y0
        self.bus.write('data:line emem,%d,%d,%d,%d' % (x0, y0, x1, y1))

    def get_npts(self):
        return int(self.bus.ask('data:points? emem'))

    def set_npts(self, val):
        self.bus.write('data:points emem,%d' % val)

    npts = property(get_npts, set_npts)

    def get_data(self):
        self.bus.write('data:data? emem')
        data = self.bus.read_raw()
        return decode_array(data)

    def set_data(self, array):
        block = encode_array(array)
        self.bus.write_raw(b'data:data emem,' + block)

    def get_point(self, index):
        self.bus.write('data:value? emem,%d' % index)

    def set_point(self, index, value):
        self.bus.write('data:value emem,%d,%d' % (index, value))

    def copy_to(self, register):
        #register is either USER1, USER2, etc.
        self.bus.write('data:copy %s,emem' % register)

    def copy_from(self, register):
        #register is either USER1, USER2, etc.
        self.bus.write('data:copy emem,%s' % register)

