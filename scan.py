from __future__ import division

import wx
from wx.lib import intctrl, newevent

import datetime

class MainWindow(wx.Frame):

    def __init__(self, parent, title):
        wx.Frame.__init__(self, parent, title=title, size=(400, 200))

        self.panel = ScanPanel(self)

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

class ScanPanel(wx.Panel):

    def __init__(self, parent):

        wx.Panel.__init__(self, parent)

        self.Xmin = wx.SpinCtrlDouble(self, value='1800',
                                   min=1, max=4095)
        self.Xmax = wx.SpinCtrlDouble(self, value='2200',
                                   min=1, max=4095)

        self.Ymin = wx.SpinCtrlDouble(self, value='1800',
                                   min=1, max=4095)
        self.Ymax = wx.SpinCtrlDouble(self, value='2300',
                                   min=1, max=4095)

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
        self.increment.Bind(wx.EVT_SPINCTRL, self.update_thing)
        self.exposure.Bind(wx.EVT_SPINCTRLDOUBLE, self.update_thing)

        # flex grid sizer
        self.sizer = wx.FlexGridSizer(rows=3, cols=4,
                                      vgap=5, hgap=5)

        self.sizer.Add(wx.StaticText(self, label='X',
                                     style=wx.ALIGN_RIGHT),
                                     0, wx.EXPAND)
        self.sizer.Add(self.Xmin, 0, wx.EXPAND)
        self.sizer.Add(wx.StaticText(self, label='to',
                                     style=wx.ALIGN_RIGHT),
                                     0, wx.EXPAND)
        self.sizer.Add(self.Xmax, 0, wx.EXPAND)

        self.sizer.Add(wx.StaticText(self, label='Y',
                                     style=wx.ALIGN_RIGHT),
                                     0, wx.EXPAND)
        self.sizer.Add(self.Ymin, 0, wx.EXPAND)
        self.sizer.Add(wx.StaticText(self, label='to',
                                     style=wx.ALIGN_RIGHT),
                                     0, wx.EXPAND)
        self.sizer.Add(self.Ymax, 0, wx.EXPAND)

        self.sizer.Add(wx.StaticText(self, label='increment',
                                     style=wx.ALIGN_RIGHT),
                                     0, wx.EXPAND)
        self.sizer.Add(self.increment, 0, wx.EXPAND)
        self.sizer.Add(wx.StaticText(self, label='t',
                                     style=wx.ALIGN_RIGHT),
                                     0, wx.EXPAND)
        self.sizer.Add(self.exposure, 0, wx.EXPAND)

        self.summary = wx.StaticText(self, label='')
        self.button = wx.Button(self, label='Start Scan')

        # outer box
        self.box = wx.StaticBox(self, label='Scan parameters')
        self.boxsizer = wx.StaticBoxSizer(self.box, orient=wx.VERTICAL)
        self.boxsizer.Add(self.sizer)
        self.boxsizer.Add(self.summary)
        self.boxsizer.Add(self.button)

        self.SetSizer(self.boxsizer)
        self.SetAutoLayout(1)
        self.sizer.Fit(self)

    def update_thing(self, event):
        xmin = int(self.Xmin.GetValue())
        xmax = int(self.Xmax.GetValue())
        ymin = int(self.Ymin.GetValue())
        ymax = int(self.Ymax.GetValue())
        inc  = int(self.increment.GetValue())
        t    = self.exposure.GetValue()
        xspan = (xmax - xmin) // inc
        yspan = (ymax - ymin) // inc
        seconds = int(t * xspan * yspan)
        td = datetime.timedelta(seconds=seconds)
        label = "%dx%d, %s" % (xspan, yspan, str(td))
        self.summary.SetLabel(label)

if __name__ == "__main__":
    app = wx.App(False)
    frame = MainWindow(None, 'Hello World')
    frame.Show(True)
    app.MainLoop()
