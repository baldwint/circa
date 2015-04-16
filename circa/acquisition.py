from __future__ import print_function

import os
from datetime import timedelta
import numpy as n

from monitor import WorkerThread, EVT_RESULT, EVT_FINISHED

from viewer import ImagePanel, DragState, Marker
from scan import ScanPanel
from galvo import DoubleGalvoPanel
from util import get_next_filename
import wx

class AcquisitionWindow(wx.Frame):

    def __init__(self, parent, xgalvo, ygalvo,
                 make_data_generator, nvals=4096, repeat=None):
        wx.Frame.__init__(self, parent, title='Acquisition', size=(500,400))

        self.xgalvo = xgalvo
        self.ygalvo = ygalvo
        self.ghost = None

        self.make_data_generator = make_data_generator

        # statusbar
        self.statusbar = self.CreateStatusBar()

        #panels
        self.panel = ImagePanel(self, size=(nvals,nvals))
        self.galvo = DoubleGalvoPanel(self, xcall=self.set_xgalvo_value,
                                            ycall=self.set_ygalvo_value,
                                            nvals=nvals)
        self.control = ScanPanel(self, self.scangen,
                                 abortable=True, nvals=nvals,
                                 repeat=repeat)

        self.control.Bind(EVT_RESULT, self.on_result)
        self.control.Bind(EVT_FINISHED, self.on_scan_finished)

        # rect dragging
        def resetbounds(state):
            if not state.mousedown.inaxes == state.mouseup.inaxes:
                # drag was not contained in one axes
                return
            elif state.mousedown.inaxes is None:
                # drag was totally outside axes
                return
            if state.mousedown.inaxes == self.panel.ax:
                xmin, xmax = sorted((state.mousedown.xdata, state.mouseup.xdata))
                ymin, ymax = sorted((state.mousedown.ydata, state.mouseup.ydata))
                rect = [xmin, xmax, ymin, ymax]
                rect = [int(num) for num in rect]
                if xmin == xmax or ymin == ymax:
                    xloc = (xmin + xmax) // 2
                    yloc = (ymin + ymax) // 2
                    self.set_galvo_values(xloc, yloc)
                else:
                    self.control.set_values(*rect)

        self.ds = DragState(resetbounds)
        self.panel.canvas.mpl_connect('button_press_event', self.ds.recv)
        self.panel.canvas.mpl_connect('button_release_event', self.ds.recv)

        # default directories
        self.open_from_dir = ''
        self.save_to_dir = os.path.expanduser('~')

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

        # shortcuts
        shortcuts = wx.AcceleratorTable([
            (wx.ACCEL_CTRL, ord('S'), wx.ID_SAVE),
            (wx.ACCEL_CTRL, ord('O'), wx.ID_OPEN)])
        self.SetAcceleratorTable(shortcuts)

        # sizers
        self.subsizer = wx.BoxSizer(wx.VERTICAL)
        self.subsizer.Add(self.galvo, 0, wx.EXPAND)
        self.subsizer.Add(self.control, 0, wx.EXPAND)
        self.sizer = wx.BoxSizer(wx.HORIZONTAL)
        self.sizer.Add(self.panel, 1, wx.EXPAND)
        self.sizer.Add(self.subsizer, 0, wx.EXPAND)

        self.SetSizer(self.sizer)
        self.SetAutoLayout(1)
        self.sizer.Fit(self)

    def OnExit(self, e):
        self.Close(True)

    def OnOpen(self, e):
        dlg = wx.FileDialog(self,
                message="Choose a file",
                defaultDir=self.open_from_dir,
                defaultFile='',
                wildcard="NPZ files (*.npz)|*.npz",
                style=wx.FD_OPEN)
        if dlg.ShowModal() == wx.ID_OK:
            # load file
            self.open_from_dir = dlg.GetDirectory()
            path = dlg.GetPath()
            with n.load(path) as npz:
                self.vector = npz['image']
                self.X = npz['X']
                self.Y = npz['Y']
                self.t = dict(npz).get('t')
            # update image, and parameters on scan control
            self.panel.update_image(self.vector, self.X, self.Y)
            self.control.set_values(t=self.t)  # does nothing if None
            self.control.set_values_from_image(self.panel.im)
            self.statusbar.SetStatusText('Loaded %s' % path)

    def OnSave(self, e):
        dlg = wx.FileDialog(self,
                message="Save NPZ file",
                defaultDir=self.save_to_dir,
                defaultFile=get_next_filename(self.save_to_dir,
                                              fmt="image%03d.npz"),
                wildcard="NPZ files (*.npz)|*.npz",
                style=wx.FD_SAVE | wx.FD_OVERWRITE_PROMPT)
        if dlg.ShowModal() == wx.ID_OK:
            self.save_to_dir = dlg.GetDirectory()
            path = dlg.GetPath()
            n.savez(path,
                    image=self.vector,
                    X=self.X,
                    Y=self.Y,
                    t=self.t)
            self.statusbar.SetStatusText('Saved %s' % path)

    def scangen(self, X, Y, t, **kwargs):

        vector = n.ndarray(Y.shape + X.shape)
        vector[:] = n.nan

        self.panel.update_image(vector, X, Y)

        # keep references to these (in case we save them)
        self.vector = vector
        self.X = X
        self.Y = Y
        self.t = t

        gen = self.make_data_generator(X, Y, t, vector, **kwargs)

        return gen

    def on_result(self, event):
        self.panel.update_data(self.vector)

    def on_scan_finished(self, event):
        elapsed = timedelta(seconds=int(event.elapsed))
        self.statusbar.SetStatusText('Scan completed in %s' % str(elapsed))
        self.galvo.update_both_galvos() # return galvos to orig pos
        event.Skip() # let the panel also handle

    def set_galvo_values(self, xloc, yloc):
        """ gets called when we want to move both galvos"""
        # draw or update the ghost
        if self.ghost is None:
            self.ghost = Marker(self.panel.ax, xloc, yloc,
                                mec='w', mfc='none',
                                ms=10, mew=4)
        else:
            self.ghost.set_pos(xloc, yloc)
        # update the galvo panel. This actually moves the galvos
        self.galvo.set_values(xloc, yloc)

    def set_xgalvo_value(self, value):
        self.xgalvo.set_value(value)
        if self.ghost is not None:
            self.ghost.set_x(value)
            self.ghost.draw()

    def set_ygalvo_value(self, value):
        self.ygalvo.set_value(value)
        if self.ghost is not None:
            self.ghost.set_y(value)
            self.ghost.draw()


class FakeGalvoPixel(object):
    """ encapsulates a Galvonometer at a given DAC channel"""
    def __init__(self, name="Dev2/ao0", bits=12, reverse=False):
        self.name = name
        self._value = None
        self.max_value = 2**bits
        self.factor = -1 if reverse else 1

    def get_value(self):
        return self._value

    def set_value(self, val):
        realval = (self.factor * int(val)) % self.max_value
        #set_DAC_bits(realval, self.name)
        self._value = int(val) % self.max_value

    value = property(get_value, set_value)


def main():
    from .config import load_config
    cfg = load_config()

    # galvos
    try:
        from expt import GalvoPixel
    except NotImplementedError:
        GalvoPixel = FakeGalvoPixel

    xgalvo = GalvoPixel(cfg.get('galvos', 'xgalvo'))
    ygalvo = GalvoPixel(cfg.get('galvos', 'ygalvo'))
    pulsechan = cfg.get('counting', 'pulsechan')
    countchan = cfg.get('counting', 'countchan')

    from slow import make_generator_factory
    make_data_generator = make_generator_factory(xgalvo, ygalvo,
                                                 pulsechan, countchan)

    # gui app
    app = wx.App(False)
    frame = AcquisitionWindow(None, xgalvo, ygalvo, make_data_generator,
                                repeat=False,
                              )
    frame.Show(True)
    app.MainLoop()

if __name__ == "__main__":
    main()
