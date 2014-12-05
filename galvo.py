from __future__ import division

import wx
from wx.lib import intctrl, newevent
import os


from matplotlib.backends.backend_wxagg import FigureCanvasWxAgg
from matplotlib.figure import Figure
import numpy as n

class MainWindow(wx.Frame):

    def __init__(self, parent, title):
        wx.Frame.__init__(self, parent, title=title, size=(500,400))

        #self.panel = GalvoPanel(self)
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

IntChangeEvent, EVT_INT_CHANGE = newevent.NewEvent()

class IntPanel(wx.Panel):

    def __init__(self, parent, label='X', value=0,
            min=None, max=None, increment=1):

        wx.Panel.__init__(self, parent)

        self.increment = increment

        self.label = wx.StaticText(self, label=label,
                style=wx.ALIGN_RIGHT)

        # make an integer control and have it send when enter key is
        # pressed (we don't want to bind when EVT_INT is sent, or
        # partial typings will get sent)
        self.control = intctrl.IntCtrl(self, value=value,
                min=min, max=max, limited=True,
                style=wx.ALIGN_RIGHT | wx.TE_PROCESS_ENTER)
        self.control.Bind(wx.EVT_TEXT_ENTER, self.on_enter)
        #self.control.Bind(intctrl.EVT_INT, self.on_enter)

        #increment buttons
        self.plus  = wx.Button(self, -1, '+')
        self.plus.Bind(wx.EVT_BUTTON, self.on_plus)
        self.minus = wx.Button(self, -1, '-')
        self.minus.Bind(wx.EVT_BUTTON, self.on_minus)

        #horizontal sizer
        self.sizer = wx.BoxSizer(wx.HORIZONTAL)
        self.sizer.Add(self.label, 1, wx.EXPAND)
        self.sizer.Add(self.control, 1, wx.EXPAND)
        self.sizer.Add(self.plus, 1, wx.EXPAND)
        self.sizer.Add(self.minus, 1, wx.EXPAND)

        self.SetSizer(self.sizer)
        self.SetAutoLayout(1)
        self.sizer.Fit(self)

    def on_plus(self, event):
        prev = self.control.GetValue()
        self.control.SetValue(prev + self.increment)
        self.send()

    def on_minus(self, event):
        prev = self.control.GetValue()
        self.control.SetValue(prev - self.increment)
        self.send()

    def on_enter(self, event):
        self.send()

    def send(self):
        evt = IntChangeEvent(value = self.control.GetValue())
        wx.PostEvent(self, evt)

class DoubleGalvoPanel(wx.Panel):

    def __init__(self, parent):

        wx.Panel.__init__(self, parent)

        self.X = IntPanel(self, 'X', 2048, 1,4096)
        self.Y = IntPanel(self, 'Y', 2048, 1, 4096)

        self.inclabel = wx.StaticText(self, label='increment',
                                      style=wx.ALIGN_RIGHT)
        self.increment = wx.SpinCtrl(self, value='1',
                min=1, max=100, initial=1,
                style=wx.SP_ARROW_KEYS)

        self.X.Bind(EVT_INT_CHANGE, self.x_changed)
        self.Y.Bind(EVT_INT_CHANGE, self.y_changed)

        # the EVT_SPINCTRL event is issued whenever the entered value
        # changes, whether by pressing the up/down buttons, or the
        # arrow keys, or manual entry. For manual entry, it is only
        # issued when the text box loses focus (tabbing away, or
        # selecting another window) AND the value has changed.
        # HOWEVER, on Mac OS X, it seems to be issued twice on losing
        # focus, even when the value has not changed
        self.increment.Bind(wx.EVT_SPINCTRL, self.newinc)

        # horizontal sizer
        self.subsizer = wx.BoxSizer(wx.HORIZONTAL)
        self.subsizer.Add(self.inclabel, 0, wx.EXPAND)
        self.subsizer.Add(self.increment, 0, wx.EXPAND)

        # vertical sizer
        self.sizer = wx.BoxSizer(wx.VERTICAL)
        self.sizer.Add(self.X, 0, wx.EXPAND)
        self.sizer.Add(self.Y, 0, wx.EXPAND)
        self.sizer.Add(self.subsizer, 0, wx.EXPAND)

        self.SetSizer(self.sizer)
        self.SetAutoLayout(1)
        self.sizer.Fit(self)

    def newinc(self, event):
        newval = event.GetInt()
        print newval
        self.X.increment = newval
        self.Y.increment = newval

    def x_changed(self, event):
        print 'x', event.value

    def y_changed(self, event):
        print 'y', event.value

app = wx.App(False)
frame = MainWindow(None, 'Hello World')
frame.Show(True)
app.MainLoop()
