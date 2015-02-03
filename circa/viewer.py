from __future__ import division

import wx
import os

from matplotlib.backends.backend_wxagg import FigureCanvasWxAgg
from matplotlib.figure import Figure
import numpy as n

from wanglib.pylab_extensions.density import density_plot

class MainWindow(wx.Frame):

    def __init__(self, parent, title):
        wx.Frame.__init__(self, parent, title=title, size=(500,400))

        self.panel = ImagePanel(self)

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

from imaging import show_image, add_hist_to_cbar

class ImagePanel(wx.Panel):

    def __init__(self, parent, size=(4096, 4096)):
        """
        Create a new image panel with an (initially) blank image.

        Set size of the blank image with 'size'
        """

        wx.Panel.__init__(self, parent)

        vector = n.ndarray((2,2))
        vector[:] = n.nan

        fig = Figure()
        self.ax = fig.add_subplot(111)
        #self.im = self.ax.imshow(vector)
        self.im = density_plot(vector,
                               n.array((0,size[0]/2)),
                               n.array((0,size[1]/2)),
                               ax=self.ax)

        self.cbar = fig.colorbar(self.im, aspect=8)
        self.ax.invert_xaxis()

        # whether the vertical scale is locked
        self.scale_locked = False

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
                    self.scale_locked = False
                elif scaling > 1:
                    # adjust vmax
                    vmin, vmax = im.get_clim()
                    im.set_clim(vmax = vmin + (vmax - vmin)/scaling)
                    self.scale_locked = True
                elif scaling < 1:
                    # adjust vmin
                    vmin, vmax = im.get_clim()
                    im.set_clim(vmin = vmax - (vmax - vmin)*scaling)
                    self.scale_locked = True
                self.canvas.draw()

        self.ds = DragState(relimcolor)
        self.canvas.mpl_connect('button_press_event', self.ds.recv)
        self.canvas.mpl_connect('button_release_event', self.ds.recv)

        self.box = wx.StaticBox(self, label="Image")
        self.sizer = wx.StaticBoxSizer(self.box)
        self.sizer.Add(self.canvas, 1, wx.EXPAND)

        self.SetSizer(self.sizer)
        self.SetAutoLayout(1)
        self.sizer.Fit(self)

    def open(self, dirname, filename):
        with n.load(os.path.join(dirname, filename)) as npz:
            self.update_image(npz['image'], npz['X'], npz['Y'])

    def update_image(self, image, x, y):
        """ load a new image."""
        self.ax.clear()  # remove any previous images
                         # would be cool to have a control for this
        self.im = show_image(image, x, y,
                             ax=self.ax,
                             cax=self.cbar.ax,
                             mirror=True,
                             hist=True)
        self.canvas.draw()

    def update_data(self, newdata):
        """ The image contents have changed, but not the bounds. """
        self.im.set_data(newdata)
        if not self.scale_locked:
            self.im.autoscale()
        self.im.changed()
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

if __name__ == "__main__":
    app = wx.App(False)
    frame = MainWindow(None, 'Hello World')
    frame.Show(True)
    app.MainLoop()
