from __future__ import division

import wx
from wx.lib import intctrl, newevent

import datetime
import numpy as n

class MainWindow(wx.Frame):

    def __init__(self, parent, title, *args, **kwargs):
        wx.Frame.__init__(self, parent, title=title, size=(400, 200))

        self.panel = ScanPanel(self, *args, **kwargs)

        #self.CreateStatusBar()

        filemenu = wx.Menu()

        menuAbout = filemenu.Append(wx.ID_ABOUT, "&About", " Info plz")
        #filemenu.AppendSeparator()
        menuExit = filemenu.Append(wx.ID_EXIT, "E&xit", " Stop program")

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

from monitor import WorkerThread, EVT_FINISHED

class ScanPanel(wx.Panel):

    def __init__(self, parent, scanfunc, abortable=False, nvals=4096):
        """
        scanfunc is an un-instantiated generator; it takes X, Y, t as
        the arguments and then does whatever. This panel will
        instantiate it when the button is pressed and run it to
        completion in its own WorkerThread.

        if 'abortable' is True, the button will allow the scan to be
        terminated prematurely

        'nvals' is the number of values taken on by X and Y, e.g. 4096
        for a 12-bit DAC. Meaningful values will be labeled 0 through
        nvals-1. Note that since upper bounds are not included in the
        scan, the range of this control will be labeled 1 through
        nvals.

        """

        wx.Panel.__init__(self, parent)

        self.scanfunc = scanfunc
        self.abortable = abortable
        self.Bind(EVT_FINISHED, self.on_scan_finished)

        self.Xmin = wx.SpinCtrlDouble(self, value='0',
                                   min=0, max=nvals-1)
        self.Xmax = wx.SpinCtrlDouble(self, value=str(nvals),
                                   min=1, max=nvals)

        self.Ymin = wx.SpinCtrlDouble(self, value='0',
                                   min=0, max=nvals-1)
        self.Ymax = wx.SpinCtrlDouble(self, value=str(nvals),
                                   min=1, max=nvals)

        self.increment = wx.SpinCtrl(self, value='10',
                min=1, max=100, style=wx.SP_ARROW_KEYS)
        self.exposure = wx.SpinCtrlDouble(self, value='.01',
                min=0., max=10, inc=.001, style=wx.SP_ARROW_KEYS)

        self.Xmin.Bind(wx.EVT_SPINCTRLDOUBLE, self.update_thing)
        self.Xmax.Bind(wx.EVT_SPINCTRLDOUBLE, self.update_thing)
        self.Ymin.Bind(wx.EVT_SPINCTRLDOUBLE, self.update_thing)
        self.Ymax.Bind(wx.EVT_SPINCTRLDOUBLE, self.update_thing)

        # the EVT_SPINCTRL event is issued whenever the entered value
        # changes, whether by pressing the up/down buttons, or the
        # arrow keys, or manual entry. For manual entry, it is only
        # issued when the text box loses focus (tabbing away, or
        # selecting another window) AND the value has changed.
        # HOWEVER, on Mac OS X, it seems to be issued twice on losing
        # focus, even when the value has not changed
        self.increment.Bind(wx.EVT_SPINCTRL, self.newinc)
        self.exposure.Bind(wx.EVT_SPINCTRLDOUBLE, self.update_thing)

        self.summary = wx.StaticText(self, label='',
                style=wx.ALIGN_CENTER)
        self.button = wx.Button(self, label='Start Scan')

        self.button.Bind(wx.EVT_BUTTON, self.on_button)

        # flex grid sizer
        self.sizer = wx.GridBagSizer(vgap=5, hgap=5)

        self.sizer.Add(wx.StaticText(self, label='X',
                                     style=wx.ALIGN_RIGHT),
                       flag=wx.EXPAND, pos=(0,0))
        self.sizer.Add(self.Xmin, flag=wx.EXPAND, pos=(0,1))
        self.sizer.Add(wx.StaticText(self, label='to',
                       style=wx.ALIGN_RIGHT),
                       flag=wx.EXPAND, pos=(0,2))
        self.sizer.Add(self.Xmax, flag=wx.EXPAND, pos=(0,3))

        self.sizer.Add(wx.StaticText(self, label='Y',
                                     style=wx.ALIGN_RIGHT),
                       flag=wx.EXPAND, pos=(1,0))
        self.sizer.Add(self.Ymin, flag=wx.EXPAND, pos=(1,1))
        self.sizer.Add(wx.StaticText(self, label='to',
                                     style=wx.ALIGN_RIGHT),
                       flag=wx.EXPAND, pos=(1,2))
        self.sizer.Add(self.Ymax, flag=wx.EXPAND, pos=(1,3))

        self.sizer.Add(wx.StaticText(self, label='increment',
                                     style=wx.ALIGN_RIGHT),
                       flag=wx.EXPAND, pos=(2,0))
        self.sizer.Add(self.increment, flag=wx.EXPAND, pos=(2,1))
        self.sizer.Add(wx.StaticText(self, label='t',
                                     style=wx.ALIGN_RIGHT),
                       flag=wx.EXPAND, pos=(2,2))
        self.sizer.Add(self.exposure, flag=wx.EXPAND, pos=(2,3))

        self.sizer.Add(self.summary, flag=wx.EXPAND,
                pos=(3,0), span=(1,4))
        self.sizer.Add(self.button, flag=wx.EXPAND,
                pos=(4,0), span=(1,4))

        # outer box
        self.box = wx.StaticBox(self, label='Scan parameters')
        self.boxsizer = wx.StaticBoxSizer(self.box, orient=wx.VERTICAL)
        self.boxsizer.Add(self.sizer)

        self.SetSizer(self.boxsizer)
        self.SetAutoLayout(1)
        self.sizer.Fit(self)

        # finally, update the label to initial value
        self.scanning = False
        self.update_thing(None)

    def get_values(self):
        xmin = int(self.Xmin.GetValue())
        xmax = int(self.Xmax.GetValue())
        ymin = int(self.Ymin.GetValue())
        ymax = int(self.Ymax.GetValue())
        inc  = int(self.increment.GetValue())
        t    = self.exposure.GetValue()
        return xmin, xmax, ymin, ymax, inc, t

    def set_values(self,
                   xmin=None, xmax=None,
                   ymin=None, ymax=None,
                   inc=None, t=None):
        if xmin is not None:
            self.Xmin.SetValue(xmin)
        if xmax is not None:
            self.Xmax.SetValue(xmax)
        if ymin is not None:
            self.Ymin.SetValue(ymin)
        if ymax is not None:
            self.Ymax.SetValue(ymax)
        if inc is not None:
            self.increment.SetValue(inc)
        if t is not None:
            self.exposure.SetValue(t)
        self.update_thing(None)

    def set_values_from_image(self, im):
        # get dimension info
        ysz, xsz = im.get_size()
        ext = im.get_extent()
        xmin, xmax, ymin, ymax = [int(num) for num in ext]
        # compute spacing
        xspacing = (xmax - xmin) / xsz
        yspacing = (ymax - ymin) / ysz
        assert xspacing == yspacing
        self.set_values(xmin, xmax, ymin, ymax, xspacing)

    def get_arrays(self):
        xmin, xmax, ymin, ymax, inc, t = self.get_values()
        X = n.arange(xmin, xmax, inc)
        Y = n.arange(ymin, ymax, inc)
        return X, Y, t

    def update_thing(self, event):
        X, Y, t = self.get_arrays()
        xspan = len(X)
        yspan = len(Y)
        seconds = int(t * xspan * yspan)
        td = datetime.timedelta(seconds=seconds)
        label = "%dx%d, %s" % (xspan, yspan, str(td))
        # http://stackoverflow.com/questions/15965254/what-is-the-correct-way-to-change-statictext-label
        self.summary.SetLabel(label)
        self.sizer.Layout()

    def newinc(self, event):
        newval = event.GetInt()
        self.update_thing(None)
        self.Xmin.SetIncrement(newval)
        self.Ymin.SetIncrement(newval)
        self.Xmax.SetIncrement(newval)
        self.Ymax.SetIncrement(newval)

    def on_button(self, event):
        """ respond to button press"""
        if not self.scanning:
            X, Y, t = self.get_arrays()
            self.start_scan(X, Y, t)
            self.scanning = True
            if not self.abortable:
                self.button.Disable()
            self.button.SetLabel('Abort Scan')
        elif self.abortable:
            self.abort_scan()
            # on_scan_finished should get triggered by the event

    def on_scan_finished(self, event):
        self.scanning = False
        self.button.SetLabel('Start Scan')
        self.button.Enable()

    def start_scan(self, X, Y, t):
        scangen = self.scanfunc(X, Y, t)
        self.worker = WorkerThread(self, scangen)
        self.worker.start()

    def abort_scan(self):
        self.worker.abort()
        self.worker.join()

    def __del__(self):
        self.abort_scan()


if __name__ == "__main__":

    from time import sleep
    def mytask(*args):
        print 'starting'
        yield
        sleep(0.8)
        print 'done'

    app = wx.App(False)
    frame = MainWindow(None, 'Hello World', mytask)
    frame.Show(True)
    app.MainLoop()
