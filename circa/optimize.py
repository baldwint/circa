import time
from .expt import do_count, configure_counter

def gen_count_rate(t=0.1):
    pc = configure_counter(duration=t)
    start = time.time()
    while True:
        y = do_count(*pc)/t
        yield time.time() - start, y

if __name__ == "__main__":
    import wx
    from .monitor import MonitorWindow

    app = wx.App(False)
    gen = gen_count_rate(t=0.1)
    frame = MonitorWindow(None, 'Monitor', datagen=gen)
    frame.Show(True)
    app.MainLoop()
