from __future__ import division

import wx
from wx.lib import intctrl, newevent

class MainWindow(wx.Frame):

    def __init__(self, parent, title):
        wx.Frame.__init__(self, parent, title=title, size=(500,400))

        self.panel = DoubleGalvoPanel(self)

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

class DoubleGalvoPanel(wx.Panel):

    def __init__(self, parent):

        wx.Panel.__init__(self, parent)

        self.Xlabel =  wx.StaticText(self, label='X',
                                     style=wx.ALIGN_RIGHT)
        self.X = wx.SpinCtrlDouble(self, value='2048',
                                   min=1, max=4095)

        self.Ylabel =  wx.StaticText(self, label='Y',
                                     style=wx.ALIGN_RIGHT)
        self.Y = wx.SpinCtrlDouble(self, value='2048',
                                   min=1, max=4095)

        self.inclabel = wx.StaticText(self, label='increment',
                                      style=wx.ALIGN_RIGHT)
        self.increment = wx.SpinCtrl(self, value='1',
                min=1, max=100, initial=1,
                style=wx.SP_ARROW_KEYS)

        self.X.Bind(wx.EVT_SPINCTRLDOUBLE, self.x_changed)
        self.Y.Bind(wx.EVT_SPINCTRLDOUBLE, self.y_changed)

        # the EVT_SPINCTRL event is issued whenever the entered value
        # changes, whether by pressing the up/down buttons, or the
        # arrow keys, or manual entry. For manual entry, it is only
        # issued when the text box loses focus (tabbing away, or
        # selecting another window) AND the value has changed.
        # HOWEVER, on Mac OS X, it seems to be issued twice on losing
        # focus, even when the value has not changed
        self.increment.Bind(wx.EVT_SPINCTRL, self.newinc)

        # flex grid sizer
        self.sizer = wx.FlexGridSizer(rows=3, cols=2)
        self.sizer.Add(self.Xlabel, 0, wx.EXPAND)
        self.sizer.Add(self.X, 0, wx.EXPAND)
        self.sizer.Add(self.Ylabel, 0, wx.EXPAND)
        self.sizer.Add(self.Y, 0, wx.EXPAND)
        self.sizer.Add(self.inclabel, 0, wx.EXPAND)
        self.sizer.Add(self.increment, 0, wx.EXPAND)

        # outer box
        self.box = wx.StaticBox(self, label='Galvos')
        self.boxsizer = wx.StaticBoxSizer(self.box)
        self.boxsizer.Add(self.sizer)

        self.SetSizer(self.boxsizer)
        self.SetAutoLayout(1)
        self.sizer.Fit(self)

    def newinc(self, event):
        newval = event.GetInt()
        print newval
        self.X.SetIncrement(newval)
        self.Y.SetIncrement(newval)

    def x_changed(self, event):
        print 'x', int(event.GetValue())

    def y_changed(self, event):
        print 'y', int(event.GetValue())

app = wx.App(False)
frame = MainWindow(None, 'Hello World')
frame.Show(True)
app.MainLoop()
