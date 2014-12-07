from __future__ import print_function

def chunk(gen, n=1):
    # not perfect unless n perfectly divides the lenght of gen
    while True:
        for i in xrange(n-1):
            next(gen)
        yield next(gen)

import itertools

def yielding_fromiter(gen, result):
    """
    fills the ND array ``result`` with values from the ``gen`` iterator,
    yielding after each insertion so that you can do something else
    (like incremental plotting).

    """
    dimensions = [xrange(n) for n in result.shape]
    coords = itertools.product(*dimensions)
    for loc,val in itertools.izip(coords,gen):
        result[loc] = val
        yield

from time import sleep
import numpy as n

def dumb_gen(X,Y):
    for y in Y:
        for x in X:
            sleep(.01)
            yield int(200000 * n.random.random())

from monitor import WorkerThread, EVT_RESULT

from ui import ImagePanel
from scan import ScanPanel
import wx

class MainWindow(wx.Frame):

    def __init__(self, parent, title):
        wx.Frame.__init__(self, parent, title=title, size=(500,400))

        #panels
        self.panel = ImagePanel(self)
        self.control = ScanPanel(self)
        self.control.start_scan = self.start_scan

        # menus
        filemenu = wx.Menu()

        menuExit = filemenu.Append(wx.ID_EXIT, "E&xit", " Stop program")

        menuBar = wx.MenuBar()
        menuBar.Append(filemenu, "&File")
        self.SetMenuBar(menuBar)

        self.Bind(wx.EVT_MENU, self.OnExit, menuExit)

        # sizers
        self.sizer = wx.BoxSizer(wx.HORIZONTAL)
        self.sizer.Add(self.panel, 1, wx.EXPAND)
        self.sizer.Add(self.control, 0, wx.EXPAND)

        self.SetSizer(self.sizer)
        self.SetAutoLayout(1)
        self.sizer.Fit(self)

    def __del__(self):
        # tell worker to finish
        self.worker.abort()
        self.worker.join()

    def OnExit(self, e):
        self.Close(True)

    def start_scan(self, X, Y, t):

        vector = n.ndarray(Y.shape + X.shape)
        vector[:] = n.nan

        self.panel.update_image(vector, X, Y)

        self.vector = vector
        gen = chunk(yielding_fromiter(dumb_gen(X, Y), vector),
                n = vector.shape[-1])
        self.datagen = gen

        self.start_worker()
        self.Bind(EVT_RESULT, self.on_result)

    def start_worker(self):
        self.worker = WorkerThread(self, self.datagen)
        self.worker.start()

    def on_result(self, event):
        self.panel.update_data(self.vector)


if __name__ == "__main__":
    app = wx.App(False)
    frame = MainWindow(None, 'Hello World')
    frame.Show(True)
    app.MainLoop()
