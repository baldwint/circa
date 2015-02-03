import time
#from wanglib.pylab_extensions.live_plot import plotgen
#from wanglib.util import notraceback
from .expt import do_count, configure_counter

def gen_count_rate(pc, t=0.1):
    start = time.time()
    while True:
        y = do_count(*pc)/t
        yield time.time() - start, y

def monitor_countrate(t=.1, ax=None, **kwargs):
    with notraceback():
        pc = configure_counter(duration=t)
        with counting(*pc):
            plotgen(gen_count_rate(pc, t), ax, **kwargs)

if __name__ == "__main__":
    import wx
    from .monitor import MonitorWindow

    app = wx.App(False)
    t = 0.1
    pc = configure_counter(duration=t)
    gen = gen_count_rate(pc, t)
    frame = MonitorWindow(None, 'Monitor', datagen=gen)
    frame.Show(True)
    app.MainLoop()
