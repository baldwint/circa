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
        rl = n.sin(2 * n.pi * pt) + 6
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
    def __init__(self, notify_window, func):
        """Init Worker Thread Class."""
        threading.Thread.__init__(self)
        self.func = func
        self._notify_window = notify_window
        self._want_abort = 0

    def run(self):
        """Run Worker Thread."""
        # This is the code executing in the new thread.
        # peek at the abort variable once in a while to see if we should stop
        while True:
            if self._want_abort:
                # Use a result of None to acknowledge the abort
                wx.PostEvent(self._notify_window, ResultEvent(data=None))
                return
            # Send data to the parent thread
            data = self.func()
            wx.PostEvent(self._notify_window, ResultEvent(data=data))

    def abort(self):
        """abort worker thread."""
        # Method for use by main thread to signal an abort
        self._want_abort = 1


class MainWindow(wx.Frame):

    def __init__(self, parent, title):
        wx.Frame.__init__(self, parent, title=title, size=(500,400))

        self.panel = GraphPanel(self)

        #self.CreateStatusBar()

        filemenu = wx.Menu()

        menuAbout = filemenu.Append(wx.ID_ABOUT, "&About", " Info plz")
        #filemenu.AppendSeparator()
        menuExit = filemenu.Append(wx.ID_EXIT, "E&xit", " Stop program")
        menuOpen = filemenu.Append(wx.ID_OPEN, "&Open", " open a file")

        menuBar = wx.MenuBar()
        menuBar.Append(filemenu, "&File")
        self.SetMenuBar(menuBar)

        self.Bind(wx.EVT_MENU, self.OnAbout, menuAbout)
        self.Bind(wx.EVT_MENU, self.OnExit, menuExit)

        #self.Show(True)

    def OnAbout(self, e):
        dlg = wx.MessageDialog(self, "small text editior",
                'about this prog', wx.OK)
        dlg.ShowModal()
        dlg.Destroy()

    def OnExit(self, e):
        self.Close(True)

class GraphPanel(wx.Panel):

    def __init__(self, parent):

        wx.Panel.__init__(self, parent)

        self.datagen = silly_gen()

        fig = Figure()
        self.ax = fig.add_subplot(111)

        # maintain x and y lists (we'll append to these as we go)
        maxlen = None
        self.x = deque([], maxlen)
        self.y = deque([], maxlen)

        self.line, = self.ax.plot(self.x, self.y)

        self.canvas = FigureCanvasWxAgg(self, -1, fig)
        self.canvas.draw()

        self.box = wx.StaticBox(self, label="Monitor")
        self.sizer = wx.StaticBoxSizer(self.box)
        self.sizer.Add(self.canvas, 1, wx.EXPAND)

        self.SetSizer(self.sizer)
        self.SetAutoLayout(1)
        self.sizer.Fit(self)

        self.start_worker()
        self.Bind(EVT_RESULT, self.on_result)

    def start_worker(self):
        def getnext():
            return next(self.datagen)

        self.worker = WorkerThread(self, getnext)
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

if __name__ == "__main__":
    app = wx.App(False)
    frame = MainWindow(None, 'Hello World')
    frame.Show(True)
    app.MainLoop()
