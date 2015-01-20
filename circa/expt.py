import PyDAQmx as daq
from PyDAQmx import uInt32, int32, int16, byref
from contextlib import contextmanager

# --------------
# COUNTING STUFF
# --------------

def configure_counter(duration=.1):

    # configure pulse (for hardware timing)
    pulse = daq.Task()
    pulse.CreateCOPulseChanTime(
        "Dev1/ctr1", "",         # physical channel, name to assign
        daq.DAQmx_Val_Seconds,   # units:seconds
        daq.DAQmx_Val_Low,       # idle state: low
        0.00, .0001, duration,   # initial delay, low time, high time
    )

    # configure counter
    ctr = daq.Task()
    ctr.CreateCICountEdgesChan("Dev1/ctr0", "",
                               daq.DAQmx_Val_Rising,
                               0,  # initial count
                               daq.DAQmx_Val_CountUp)

    # pause trigger
    ctr.SetPauseTrigType(daq.DAQmx_Val_DigLvl)
    ctr.SetDigLvlPauseTrigWhen(daq.DAQmx_Val_Low)
    ctr.SetDigLvlPauseTrigSrc("/Dev1/Ctr1InternalOutput")

    return pulse, ctr

def start_count(pulse, ctr):
    """ start counting events. """
    # start counter
    ctr.StartTask()
    # fire pulse
    pulse.StartTask()
    return

def finish_count(pulse, ctr):
    """ finish counting events and return the result. """
    # initialize memory for readout
    count = uInt32()
    # wait for pulse to be done
    pulse.WaitUntilTaskDone(10.)
    # timeout, ref to output value, reserved
    ctr.ReadCounterScalarU32(10., byref(count), None)
    pulse.StopTask()
    ctr.StopTask()
    return count.value

def do_count(pulse, ctr):
    """
    simple counting in a synchronous mode
    """
    start_count(pulse, ctr)
    return finish_count(pulse, ctr)

@contextmanager
def counting(pulse, ctr):
    try:
        yield
    except KeyboardInterrupt:
        # stop the counters
        try:
            ctr.StopTask()
            print "stopped counter"
        except DAQError:
            print "no need to stop counter"
        try:
            pulse.StopTask()
            print "stopped timer"
        except DAQError:
            print "no need to stop timer"
        raise

def scan(gen, t=0.1):
    """threaded version"""
    p,c = configure_counter(duration=t)
    with counting(p,c):
        next(gen)
        last = do_count(p,c)/t
        for step in gen:
            start_count(p, c)
            yield last
            last = finish_count(p, c)/t
        yield last


# ---------------
# SCANNING MIRROR
# ---------------

def set_DAC_bits(num, channel_name="Dev2/ao0"):
    """
    Set the DAC bits to the given value (provide an integer between 0 and 2**12)
    """
    dc = DACChannel(channel_name)
    dc.set_value(num)

class DACChannel(object):
    """ encapsulates a DAC channel"""
    def __init__(self, name="Dev2/ao0"):
        self.ao = daq.Task()
        self.ao.CreateAOVoltageChan(
            name, "",                     # physical channel, name to assign
            0., 5., daq.DAQmx_Val_Volts,  # max, min, in units: Volts
            None)                         # not using custom scale

        # no timing (seems to be 1ms per sample)
        self.name = name
        self._value = None

    def get_value(self):
        return self._value

    def set_value(self, val):
        written = int32()
        samples = int16(val)
        self.ao.WriteRaw(
            1, True, 10.0,            # no of samples, autostart, timeout
            byref(samples),           # data to actually write!
            byref(written),           # output: the number of things written
            None)                     # reserved

        # verify that we wrote all the samples
        assert written.value == 1

        self._value = int(val)

    value = property(get_value, set_value)


class GalvoPixel(object):
    """ encapsulates a Galvonometer at a given DAC channel"""
    def __init__(self, name="Dev2/ao0", bits=12, reverse=False):
        self.dc = DACChannel(name)
        self._value = None
        self.max_value = 2**bits
        self.factor = -1 if reverse else 1

    def get_value(self):
        return self._value

    def set_value(self, val):
        realval = (self.factor * int(val)) % self.max_value
        self.dc.set_value(realval)
        self._value = int(val) % self.max_value

    value = property(get_value, set_value)
