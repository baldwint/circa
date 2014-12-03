from __future__ import division

import wx
import os


from matplotlib.backends.backend_wxagg import FigureCanvasWxAgg
from matplotlib.figure import Figure
import numpy as n

class MainWindow(wx.Frame):

    def __init__(self, parent, title):
        wx.Frame.__init__(self, parent, title=title, size=(500,400))

        self.panel = GraphPanel(self)
        #self.panel = MainPanel(self)

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
        self.Bind(wx.EVT_MENU, self.OnOpen, menuOpen)

        #self.Show(True)

    def OnAbout(self, e):
        dlg = wx.MessageDialog(self, "small text editior",
                'about this prog', wx.OK)
        dlg.ShowModal()
        dlg.Destroy()

    def OnExit(self, e):
        print self.panel.cbar.vmax
        self.Close(True)

    def OnOpen(self, e):
        self.dirname = ''
        dlg = wx.FileDialog(self, "Choose a file",
                self.dirname, '', '*.*', wx.OPEN)
        if dlg.ShowModal() == wx.ID_OK:
            self.filename = dlg.GetFilename()
            self.dirname = dlg.GetDirectory()
            self.panel.open(self.dirname, self.filename)
        dlg.Destroy()

class MainPanel(wx.Panel):

    def __init__(self, parent):

        wx.Panel.__init__(self, parent)

        self.control = wx.TextCtrl(self, style=wx.TE_MULTILINE)

        self.subsizer = wx.BoxSizer(wx.HORIZONTAL)
        self.buttons = []
        for i in range(3):
            self.buttons.append(wx.Button(self, -1, "Button &%d" % i))
            self.subsizer.Add(self.buttons[i], 1, wx.EXPAND)

        self.sizer = wx.BoxSizer(wx.VERTICAL)
        self.sizer.Add(self.control, 1, wx.EXPAND)
        self.sizer.Add(self.subsizer, 0, wx.EXPAND)

        self.SetSizer(self.sizer)
        self.SetAutoLayout(1)
        self.sizer.Fit(self)

    def open(self, dirname, filename):
        with open(os.path.join(dirname, filename), 'r') as f:
            self.control.SetValue(f.read())

from imaging import show_image, add_hist_to_cbar

class GraphPanel(wx.Panel):

    def __init__(self, parent):

        wx.Panel.__init__(self, parent)

        fig = Figure()
        self.ax = fig.add_subplot(111)
        self.im = self.ax.imshow(n.zeros((2048,2048)))

        self.cbar = fig.colorbar(self.im, aspect=8)

        #self.hist = fig.add_subplot(121)

        self.canvas = FigureCanvasWxAgg(self, -1, fig)
        self.canvas.draw()

        def relimcolor(state):
            im = self.im
            if not state.mousedown.inaxes == state.mouseup.inaxes:
                # drag was not contained in one axes
                return
            elif state.mousedown.inaxes is None:
                # drag was totally outside axes
                return
            if state.mousedown.inaxes == self.cbar.ax:
                # if we are in the colorbar
                scaling = state.mouseup.ydata/state.mousedown.ydata
                if scaling == 1:
                    # restore zoom
                    im.autoscale()
                elif scaling > 1:
                    # adjust vmax
                    vmin, vmax = im.get_clim()
                    im.set_clim(vmax = vmin + (vmax - vmin)/scaling)
                elif scaling < 1:
                    # adjust vmin
                    vmin, vmax = im.get_clim()
                    im.set_clim(vmin = vmax - (vmax - vmin)*scaling)
                self.canvas.draw()

        self.ds = DragState(relimcolor)
        self.canvas.mpl_connect('button_press_event', self.ds.recv)
        self.canvas.mpl_connect('button_release_event', self.ds.recv)

        self.subsizer = wx.BoxSizer(wx.HORIZONTAL)
        self.buttons = []
        self.buttons.append(wx.StaticText(self, -1, "VMax"))
        self.subsizer.Add(self.buttons[-1], 1, wx.EXPAND)
        self.buttons.append(wx.TextCtrl(self, -1, "Hi"))
        self.subsizer.Add(self.buttons[-1], 1, wx.EXPAND)
        for i in range(3):
            self.buttons.append(wx.Button(self, -1, "Button &%d" % i))
            self.subsizer.Add(self.buttons[-1], 1, wx.EXPAND)

        self.sizer = wx.BoxSizer(wx.VERTICAL)
        self.sizer.Add(self.canvas, 1, wx.EXPAND)
        self.sizer.Add(self.subsizer, 0, wx.EXPAND)

        self.SetSizer(self.sizer)
        self.SetAutoLayout(1)
        self.sizer.Fit(self)

        self.open('/Users/tkb/Dropbox/wanglab/data/2014-10/20 Oct rabi oscillations with stripline/',
                'image16.npz')

    def open(self, dirname, filename):
        with n.load(os.path.join(dirname, filename)) as npz:
            image = npz['image']

            self.im = show_image(image, npz['X'], npz['Y'],
                    ax=self.ax, cax=self.cbar.ax, hist=True)

            self.canvas.draw()

class DragState(object):
    """
    handles click-drag selection of an area in matplotlib

    """

    def __init__(self, callback):
        self.recording = False
        self.callback = callback

    def recv(self, event):
        if not self.recording and event.name == 'button_press_event':
            self.mousedown = event
            self.recording = True
        elif self.recording and event.name == 'button_release_event':
            self.mouseup = event
            self.recording = False
            self.callback(self)

app = wx.App(False)
frame = MainWindow(None, 'Hello World')
frame.Show(True)
app.MainLoop()