from __future__ import print_function
import sys
import time
import PyDAQmx as daq
from PyDAQmx import uInt32, int32, int16, byref
from contextlib import contextmanager

# --------------
# COUNTING STUFF
# --------------

def make_counter(countchan, trig=None):
    """
    Configure the given counter to count, maybe with a pause trigger.
    """
    ctr = daq.Task()
    ctr.CreateCICountEdgesChan(countchan, "",
                               daq.DAQmx_Val_Rising,
                               0,  # initial count
                               daq.DAQmx_Val_CountUp)

    if trig is not None:
        # configure pause trigger
        ctr.SetPauseTrigType(daq.DAQmx_Val_DigLvl)
        ctr.SetDigLvlPauseTrigSrc(trig)
        ctr.SetDigLvlPauseTrigWhen(daq.DAQmx_Val_Low)

    return ctr

def make_pulse(duration, pulsechan):
    """
    Configure the counter `pulsechan` to output
    a pulse of the given `duration` (in seconds).
    """
    pulse = daq.Task()
    pulse.CreateCOPulseChanTime(
        pulsechan, "",            # physical channel, name to assign
        daq.DAQmx_Val_Seconds,   # units:seconds
        daq.DAQmx_Val_Low,       # idle state: low
        0.00, .0001, duration,   # initial delay, low time, high time
    )
    return pulse

def configure_counter(duration=.1,
                      pulsechan="Dev1/ctr1",
                      countchan="Dev1/ctr0"):
    """
    Configure the card to count edges on `countchan`, for the specified
    `duration` of time (seconds). This is a hardware-timed thing,
    using the paired counter `pulsechan` to gate the detection
    """

    # configure pulse (for hardware timing)
    pulse = make_pulse(duration, pulsechan)

    # if these are paired counters, we can use the internal output
    # of the pulsing channel to trigger the counting channel
    trigchan = "/%sInternalOutput" % pulsechan.replace('ctr', 'Ctr')

    # configure counter
    ctr = make_counter(countchan, trig=trigchan)

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
            print("stopped counter")
        except daq.DAQError:
            print("no need to stop counter")
        try:
            pulse.StopTask()
            print("stopped timer")
        except daq.DAQError:
            print("no need to stop timer")
        raise

def scan(gen, t=0.1, **kwargs):
    """threaded version"""
    p,c = configure_counter(duration=t, **kwargs)
    with counting(p,c):
        next(gen)
        try:
            last = do_count(p,c)/t
        except daq.DAQError as e:
            print(str(e), file=sys.stderr)
            raise StopIteration
        for step in gen:
            start_count(p, c)
            yield last
            last = finish_count(p, c)/t
        yield last

def gen_count_rate(t=0.1, **kwargs):
    p,c = configure_counter(duration=t, **kwargs)
    start = time.time()
    while True:
        y = do_count(p,c)/t
        yield time.time() - start, y

# ---------------
# PULSED COUNTING
# ---------------

def get_counts(ctr):
    """ this stops ``ctr`` and returns its result """
    count = daq.uInt32()
    ctr.ReadCounterScalarU32(10., daq.byref(count), None)
    ctr.StopTask()
    return count.value

def gen_gated_counts(t=0.1):
    """
    equivalent of gen_count_rate when something else (e.g. a spincore
    sequence) is gating the detection, not a pulse we generate
    ourselves.

    This counts both photons and gate edges, and returns the rate as
    photons collected per gated detection period. Divide by the width
    of the window to get counts per second.
    """
    # photon counter
    pc = make_counter("Dev2/ctr2", trig="/Dev2/PFI5")
    # and the gate counter:
    gc = make_counter("Dev2/ctr3")
    # the paths here are for andrew's setup, hardcoded for now (sorry)

    start = time.time()
    while True:
        gc.StartTask() # start both counters. this isn't
        pc.StartTask() # exactly synchronous (error source)
        time.sleep(t)
        photons = get_counts(pc)
        pulses  = get_counts(gc)
        if pulses:
            rate = photons / float(pulses)
        else:
            rate = 0.
        yield time.time() - start, rate

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
