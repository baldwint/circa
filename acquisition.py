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
        self.control = ScanPanel(self, self.scangen, abortable=True)

        self.control.Bind(EVT_RESULT, self.on_result)

        # menus
        filemenu = wx.Menu()

        menuExit = filemenu.Append(wx.ID_EXIT, "E&xit", " Stop program")
        menuOpen = filemenu.Append(wx.ID_OPEN, "&Open", " Open a file")
        menuSave = filemenu.Append(wx.ID_SAVE, "&Save", " Save a file")

        menuBar = wx.MenuBar()
        menuBar.Append(filemenu, "&File")
        self.SetMenuBar(menuBar)

        self.Bind(wx.EVT_MENU, self.OnExit, menuExit)
        self.Bind(wx.EVT_MENU, self.OnOpen, menuOpen)
        self.Bind(wx.EVT_MENU, self.OnSave, menuSave)

        # sizers
        self.sizer = wx.BoxSizer(wx.HORIZONTAL)
        self.sizer.Add(self.panel, 1, wx.EXPAND)
        self.sizer.Add(self.control, 0, wx.EXPAND)

        self.SetSizer(self.sizer)
        self.SetAutoLayout(1)
        self.sizer.Fit(self)

    def OnExit(self, e):
        self.Close(True)

    def OnOpen(self, e):
        dlg = wx.FileDialog(self,
                message="Choose a file",
                defaultDir='',
                defaultFile='',
                wildcard="NPZ files (*.npz)|*.npz",
                style=wx.FD_OPEN)
        if dlg.ShowModal() == wx.ID_OK:
            # load file
            path = dlg.GetPath()
            with n.load(path) as npz:
                self.vector = npz['image']
                self.X = npz['X']
                self.Y = npz['Y']
            # update image, and parameters on scan control
            self.panel.update_image(self.vector, self.X, self.Y)
            self.control.set_values_from_image(self.panel.im)

    def OnSave(self, e):
        dlg = wx.FileDialog(self,
                message="Save NPZ file",
                defaultDir='',
                defaultFile='',
                wildcard="NPZ files (*.npz)|*.npz",
                style=wx.FD_SAVE | wx.FD_OVERWRITE_PROMPT)
        if dlg.ShowModal() == wx.ID_OK:
            path = dlg.GetPath()
            n.savez(path, image=self.vector, X=self.X, Y=self.Y)

    def scangen(self, X, Y, t):

        vector = n.ndarray(Y.shape + X.shape)
        vector[:] = n.nan

        self.panel.update_image(vector, X, Y)

        # keep references to these (in case we save them)
        self.vector = vector
        self.X = X
        self.Y = Y

        gen = chunk(yielding_fromiter(dumb_gen(X, Y), vector),
                n = vector.shape[-1])

        return gen

    def on_result(self, event):
        self.panel.update_data(self.vector)


if __name__ == "__main__":
    app = wx.App(False)
    frame = MainWindow(None, 'Hello World')
    frame.Show(True)
    app.MainLoop()
