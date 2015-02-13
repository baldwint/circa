import numpy as n
import pylab as p

def sync(length, amp=16382):
    s = n.zeros((length,), dtype=n.uint16)
    s[1::2] = 1
    return s * amp

def zigzagify(A):
    """reshape a 2d array to have alternate rows going backward"""
    A[1::2] = A[1::2][:,::-1]

def pairify(a):
    """ return an array that's twice as long, with each value duplicated"""
    return n.asarray((a,a)).T.ravel()

def make_waveforms(X, Y, zigzag=False):

    x = pairify(n.array(X, dtype=n.uint16))
    y = n.array(Y, dtype=n.uint16)

    X,Y = n.meshgrid(x,y)

    assert X.size == Y.size <= 2**17

    if zigzag:
        zigzagify(X)

    return X.ravel(), Y.ravel(), sync(X.size)

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

# load it

def make_and_load_waveforms(X, Y, t, det_afg, rf_afg):
    det_arb = Arb(det_afg)
    rf_arb = Arb(rf_afg)

    s_ch = AFG_channel(det_afg, 1)
    y_ch = AFG_channel(det_afg, 2)
    x_ch = AFG_channel(rf_afg)

    X,Y,s = make_waveforms(X, Y)

    npts = len(s)     # number of waveform points
    naqs = npts // 2  # number of acquisitions (pixels)

    # load into the two AFGs
    det_arb.npts = npts
    det_arb.set_data(s)
    det_arb.copy_to('user3') # ch1 : user3
    det_arb.set_data(Y)      # ch2 : emem
    rf_arb.npts = npts
    rf_arb.set_data(X)

    # configure AFGs
    s_ch.set_mode('user3')
    y_ch.set_mode('emem')
    x_ch.set_mode('emem')

    total_time = naqs * t
    for ch in (x_ch, y_ch, s_ch):
        ch.freq = 1. / total_time

    return naqs

class AFGasDAC(object):

    def __init__(self, afg):
        self.arb = Arb(afg)

    def get_value(self):
        return self.arb.get_point(1)

    def set_value(self, value):
        return self.arb.set_point(1, value)


from PyDAQmx import *

def make_pulse(duration, pulsechan):
    pulse = Task()
    pulse.CreateCOPulseChanTime(
        pulsechan, "",           # physical channel, name to assign
        DAQmx_Val_Seconds,       # units:seconds
        DAQmx_Val_Low,           # idle state: low
        0.00, .0001, duration,  # initial delay, low time, high time
    )
    return pulse

def make_buffered_counter(samps, countchan, sampleclk):
    ctr = Task()
    ctr.CreateCICountEdgesChan(countchan, "",
                               DAQmx_Val_Rising,
                               0,  # initial count
                               DAQmx_Val_CountUp)

    # configure sample clock (http://www.ni.com/white-paper/5404/en/)
    ctr.CfgSampClkTiming(sampleclk,   # source of the sample clock
                         10000,  # rate of the sample clock.
                                 # not sure about units, lifted from white paper
                         DAQmx_Val_Rising,       # activeEdge
                         DAQmx_Val_FiniteSamps,  # sampleMode
                         samps)                    # sampsPerChanToAcquire

    return ctr

def many_samples(samps, timeout, pulsechan, countchan, sampleclk):
    ctr = make_buffered_counter(samps, countchan=countchan,
                                       sampleclk=sampleclk)
    # make a pulse to trigger the burst on AFGs
    co = make_pulse(.01, pulsechan=pulsechan)
    ctr.StartTask()  # start counting
    co.StartTask()   # send trigger
    # while that's going, allocate some memory
    spcr = c_long()
    data = n.zeros((samps,), dtype=numpy.uint32)
    ctr.WaitUntilTaskDone(timeout)
    # now read out the data
    ctr.ReadCounterU32(samps, # number of samples to read
                       10.0,  # timeout
                       data,  # readArray
                       samps, # arraySizeInSamps
                       spcr,  # sampsPerChanRead
                       None)  # reserved
    ctr.StopTask()
    co.StopTask()
    #print spcr.value
    assert spcr.value == samps
    return data

def decode_image(result, shape, zigzag=False):
    im = n.diff(n.insert(result,0,0))
    im = im.reshape(*shape)
    if zigzag:
        im[1::2] = im[1::2][:,::-1]  #zigzag
    return im

# generators for the GUI

def generate_frames(X, Y, t=.01, repeat=True,
                    pulsechan="Dev1/ctr2",
                    countchan="Dev1/ctr0",
                    sampleclk="PFI34",
                    det_afg=None, rf_afg=None):
    naqs = make_and_load_waveforms(X, Y, t, det_afg, rf_afg)
    outshape = Y.shape + X.shape
    timeout = 5. + naqs * t
    while True:
        try:
            result = many_samples(naqs, timeout,
                                  pulsechan=pulsechan,
                                  countchan=countchan,
                                  sampleclk=sampleclk)
        except DAQError as e:
            print(e)
            raise StopIteration
        yield decode_image(result, shape=outshape)/t
        if not repeat:
            break

def update_result(gen, resultarray):
    """
    plays the same role as yielding_fromiter,
    but expects gen to yield the whole result each time

    """
    for result in gen:
        resultarray[:] = result
        yield

def make_generator_factory(xgalvo, ygalvo,
                           pulsechan, countchan, sampleclk,
                           det_afg, rf_afg):
    # don't do anything with the galvos, they're fake

    def make_data_generator(X, Y, t, vector, repeat=True):
        gen = generate_frames(X, Y, t, repeat=repeat,
                              pulsechan=pulsechan,
                              countchan=countchan,
                              sampleclk=sampleclk,
                              det_afg=det_afg,
                              rf_afg=rf_afg,
                              )
        return update_result(gen, vector)

    return make_data_generator

def main():
    import wx
    from acquisition import FakeGalvoPixel, AcquisitionWindow

    from .config import load_config
    cfg = load_config()

    pulsechan = cfg.get('fast', 'pulsechan')
    countchan = cfg.get('fast', 'countchan')
    sampleclk = cfg.get('fast', 'sampleclk')

    import visa
    rm = visa.ResourceManager()

    det_afg = rm.get_instrument(cfg.get('fast', 'det_afg'))
    rf_afg = rm.get_instrument(cfg.get('fast', 'rf_afg'))

    ygalvo = AFGasDAC(det_afg)
    xgalvo = AFGasDAC(rf_afg)

    make_data_generator = make_generator_factory(xgalvo, ygalvo,
                                                 pulsechan, countchan,
                                                 sampleclk,
                                                 det_afg, rf_afg)

    # gui app
    app = wx.App(False)
    frame = AcquisitionWindow(None, xgalvo, ygalvo,
                              make_data_generator, nvals=16383,
                              repeat=True)
    frame.Show(True)
    app.MainLoop()

if __name__ == "__main__":
    main()
