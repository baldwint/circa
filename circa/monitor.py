from __future__ import division

import wx
import os

from matplotlib.backends.backend_wxagg import FigureCanvasWxAgg
from matplotlib.figure import Figure
from matplotlib import ticker as mticker
from matplotlib import transforms as mtransforms
import numpy as n
from time import sleep, time
import threading
from collections import deque
from .util import get_next_filename

class ScrollingLocator(mticker.MaxNLocator):

    def view_limits(self, vmin, vmax):
        """ Leave unchanged, for smooth scrolling """
        return mtransforms.nonsingular(vmin, vmax)


def silly_gen(inc=0.1):
    """
    a silly generator function producing 'data'
    (really just a sine wave plus noise)
    """
    pt = 0.
    while True:
        sleep(0.1)
        rl = n.sin(2 * n.pi * pt) + n.sin(2 * n.pi * pt / 50.)
        rl += 0.1* n.random.randn()
        yield pt, rl
        pt += inc

# threading code mostly stolen from http://wiki.wxpython.org/LongRunningTasks

# Define notification events
import wx.lib.newevent

# for new data available
ResultEvent, EVT_RESULT = wx.lib.newevent.NewEvent()

# for scan being finished
FinishedEvent, EVT_FINISHED = wx.lib.newevent.NewEvent()

# Thread class that executes processing
class WorkerThread(threading.Thread):
    """Worker Thread Class."""
    def __init__(self, notify_window, gen):
        """Init Worker Thread Class."""
        threading.Thread.__init__(self)
        self.gen = gen
        self._notify_window = notify_window
        self._want_abort = 0

    def run(self):
        """Run Worker Thread."""
        # This is the code executing in the new thread.
        start = time()
        # peek at the abort variable once in a while to see if we should stop
        for data in self.gen:
            if self._want_abort:
                break
            # Send data to the parent thread
            wx.PostEvent(self._notify_window, ResultEvent(data=data))
        # Signal that we are all done
        elapsed = time() - start
        wx.PostEvent(self._notify_window, FinishedEvent(elapsed=elapsed))

    def abort(self):
        """abort worker thread."""
        # Method for use by main thread to signal an abort
        self._want_abort = 1


class MonitorWindow(wx.Frame):

    def __init__(self, parent, title, datagen=None):
        wx.Frame.__init__(self, parent, title=title, size=(500,400))

        if datagen is None:
            datagen = silly_gen()

        self.statusbar = self.CreateStatusBar()
        self.panel = MonitorPanel(self, datagen)
        self.save_to_dir = os.path.expanduser('~')

        filemenu = wx.Menu()
        menuExit = filemenu.Append(wx.ID_EXIT, "E&xit", " Stop program")
        menuSave = filemenu.Append(wx.ID_SAVE, "&Save", " Save a file")

        menuBar = wx.MenuBar()
        menuBar.Append(filemenu, "&File")
        self.SetMenuBar(menuBar)

        self.Bind(wx.EVT_MENU, self.OnExit, menuExit)
        self.Bind(wx.EVT_MENU, self.OnSave, menuSave)

        # shortcuts
        shortcuts = wx.AcceleratorTable([
            (wx.ACCEL_CTRL, ord('S'), wx.ID_SAVE),
            ])
        self.SetAcceleratorTable(shortcuts)

    def OnExit(self, e):
        # Runs when the 'Exit' menu option is selected,
        # but not when the x is hit
        self.Close(True)

    def OnSave(self, e):
        xy = self.panel.get_data()
        dlg = wx.FileDialog(self,
                message="Save NPY file",
                defaultDir=self.save_to_dir,
                defaultFile=get_next_filename(self.save_to_dir,
                                              fmt="monitor%03d.npy"),
                wildcard="NPY files (*.npy)|*.npy",
                style=wx.FD_SAVE | wx.FD_OVERWRITE_PROMPT)
        if dlg.ShowModal() == wx.ID_OK:
            self.save_to_dir = dlg.GetDirectory()
            path = dlg.GetPath()
            n.save(path, xy)
            self.statusbar.SetStatusText('Saved %s' % path)


class MonitorPanel(wx.Panel):
    """
    Panel encompassing a line monitor graph.

    Pulls x,y data from the provided generator `datagen`
    and plots a live 2D graph.

    """

    def __init__(self, parent, datagen):

        wx.Panel.__init__(self, parent)

        self.datagen = datagen

        fig = Figure()
        self.ax = fig.add_subplot(111)

        self.ax.xaxis.set_major_locator(ScrollingLocator())

        # maintain x and y lists (we'll append to these as we go)
        self.setup_deques([], [])

        self.line, = self.ax.plot(self.x, self.y)

        self.canvas = FigureCanvasWxAgg(self, -1, fig)
        self.canvas.draw()

        self.checkbox = wx.CheckBox(self, label="Limit to")
        self.Bind(wx.EVT_CHECKBOX, self.impose_limit)
        self.spinbox = wx.SpinCtrlDouble(self,
                value='100', min=10, max=10000, inc=10)
        self.Bind(wx.EVT_SPINCTRLDOUBLE, self.impose_limit)
        self.clear_button = wx.Button(self, label="Clear")
        self.clear_button.Bind(wx.EVT_BUTTON, self.on_clear_button)
        self.start_button = wx.Button(self, label="Start")
        self.start_button.Bind(wx.EVT_BUTTON, self.on_start_button)

        self.subsizer = wx.BoxSizer(wx.HORIZONTAL)
        self.subsizer.Add(self.checkbox, 0, wx.EXPAND)
        self.subsizer.Add(self.spinbox, 1, wx.EXPAND)
        self.subsizer.Add(wx.StaticText(self, label='data points'),
                0, wx.ALIGN_CENTER)
        self.subsizer.Add(self.clear_button, 0, wx.EXPAND)
        self.subsizer.Add(self.start_button, 0, wx.EXPAND)

        self.box = wx.StaticBox(self, label="Monitor")
        self.sizer = wx.StaticBoxSizer(self.box, orient=wx.VERTICAL)
        self.sizer.Add(self.canvas, 1, wx.EXPAND)
        self.sizer.AddSpacer(5)
        self.sizer.Add(self.subsizer, 0, wx.EXPAND)

        self.SetSizer(self.sizer)
        self.SetAutoLayout(1)
        self.sizer.Fit(self)

        self.running = False
        self.Bind(EVT_RESULT, self.on_result)

    def on_start_button(self, event):
        if not self.running:
            self.start_worker()
            self.running = True
            self.start_button.SetLabel('Stop')
        else:
            self.abort_worker()
            self.running = False
            self.start_button.SetLabel('Resume')

    def on_clear_button(self, event):
        self.x.clear()
        self.y.clear()

    def __del__(self):
        # this doesn't seem to work
        self.abort_worker()

    def abort_worker(self):
        # tell worker to finish
        self.worker.abort()
        self.worker.join()

    def setup_deques(self, x, y, maxlen=None):
        self.x = deque(x, maxlen)
        self.y = deque(y, maxlen)

    def start_worker(self):
        self.worker = WorkerThread(self, self.datagen)
        self.worker.start()

    def on_result(self, event):
        if event.data is None:
            pass
        else:
            x,y = event.data

            self.x.append(x)
            self.y.append(y)

            self.line.set_data(self.x, self.y)
            self.ax.relim()
            self.ax.autoscale_view()
            self.canvas.draw()

    def impose_limit(self, event):
        if self.checkbox.IsChecked():
            maxlen = self.spinbox.GetValue()
        else:
            maxlen = None
        self.setup_deques(self.x, self.y, maxlen=maxlen)

    def get_data(self):
        return self.line.get_data()


if __name__ == "__main__":
    title = 'Monitor'

    from .config import load_config
    cfg = load_config()
    pulsechan = cfg.get('counting', 'pulsechan')
    countchan = cfg.get('counting', 'countchan')

    import sys
    fake = ('--fake' in sys.argv)

    try:
        import PyDAQmx as daq
    except NotImplementedError:
        fake = True

    if fake:
        gen = silly_gen()
        title += ' (fake)'
    elif '--gated' in sys.argv:
        from .expt import gen_gated_counts
        gen = gen_gated_counts(t=0.1)
        title += ' (gated)'
    else:
        from .expt import gen_count_rate
        gen = gen_count_rate(t=0.1, pulsechan=pulsechan, countchan=countchan)

    app = wx.App(False)
    frame = MonitorWindow(None, title, datagen=gen)
    frame.Show(True)
    app.MainLoop()
