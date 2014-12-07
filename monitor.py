from __future__ import division

import wx
import os

from matplotlib.backends.backend_wxagg import FigureCanvasWxAgg
from matplotlib.figure import Figure
import numpy as n
from time import sleep
import threading
from collections import deque

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

# Define notification event for thread completion
import wx.lib.newevent
ResultEvent, EVT_RESULT = wx.lib.newevent.NewEvent()

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
        # peek at the abort variable once in a while to see if we should stop
        for data in self.gen:
            if self._want_abort:
                # Use a result of None to acknowledge the abort
                wx.PostEvent(self._notify_window, ResultEvent(data=None))
                return
            # Send data to the parent thread
            wx.PostEvent(self._notify_window, ResultEvent(data=data))

    def abort(self):
        """abort worker thread."""
        # Method for use by main thread to signal an abort
        self._want_abort = 1


class MonitorWindow(wx.Frame):

    def __init__(self, parent, title, datagen=None):
        wx.Frame.__init__(self, parent, title=title, size=(500,400))

        if datagen is None:
            datagen = silly_gen()

        self.panel = MonitorPanel(self, datagen)

        filemenu = wx.Menu()
        menuExit = filemenu.Append(wx.ID_EXIT, "E&xit", " Stop program")

        menuBar = wx.MenuBar()
        menuBar.Append(filemenu, "&File")
        self.SetMenuBar(menuBar)

        self.Bind(wx.EVT_MENU, self.OnExit, menuExit)

    def OnExit(self, e):
        # Runs when the 'Exit' menu option is selected,
        # but not when the x is hit
        self.Close(True)


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

        self.subsizer = wx.BoxSizer(wx.HORIZONTAL)
        self.subsizer.Add(self.checkbox, 0, wx.EXPAND)
        self.subsizer.Add(self.spinbox, 1, wx.EXPAND)
        self.subsizer.Add(wx.StaticText(self, label='data points'),
                0, wx.EXPAND)

        self.box = wx.StaticBox(self, label="Monitor")
        self.sizer = wx.StaticBoxSizer(self.box, orient=wx.VERTICAL)
        self.sizer.Add(self.canvas, 1, wx.EXPAND)
        self.sizer.AddSpacer(5)
        self.sizer.Add(self.subsizer, 0, wx.EXPAND)

        self.SetSizer(self.sizer)
        self.SetAutoLayout(1)
        self.sizer.Fit(self)

        self.start_worker()
        self.Bind(EVT_RESULT, self.on_result)

    def __del__(self):
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


if __name__ == "__main__":
    app = wx.App(False)
    frame = MonitorWindow(None, 'Monitor', datagen=silly_gen())
    frame.Show(True)
    app.MainLoop()
