import numpy as n
from matplotlib import pyplot as plt
from wanglib.pylab_extensions.density import density_plot

x = n.arange(-2,2,.001)
y = n.arange(-2,2,.001)

def wave(x,y):
    X,Y = n.meshgrid(x,y)
    Z = n.sin(10*(X + Y))
    return Z

def mandelbrot(x,y):
    X,Y = n.meshgrid(x,y)
    C = X + 1j*Y
    z = 0
    for g in range(30):
        z = z**2 + C
    return n.abs(z) < 2

def report(event):
    thing = event.name, event.xdata, event.ydata
    print str(thing)

def relim(xrange, yrange):
    x0, x1 = sorted(xrange)
    y0, y1 = sorted(yrange)
    plt.xlim(x0, x1)
    plt.ylim(y0, y1)
    plt.draw()

def recalc(xrange, yrange):
    x0, x1 = sorted(xrange)
    y0, y1 = sorted(yrange)
    spreads = x1-x0, y1-y0
    spacing = max(spreads) / 100
    x = n.arange(x0, x1, spacing)
    y = n.arange(y0, y1, spacing)
    density_plot(mandelbrot(x,y), x, y)
    plt.draw()

class State(object):

    def __init__(self):
        self.recording = False

    def recv(self, event):
        if not self.recording and event.name == 'button_press_event':
            self.x, self.y = event.xdata, event.ydata
            self.recording = True
        elif self.recording and event.name == 'button_release_event':
            xrange = (self.x, event.xdata)
            yrange = (self.y, event.ydata)
            self.recording = False
            #relim(xrange, yrange)
            recalc(xrange, yrange)



fig = plt.figure()
s = State()


fig.canvas.mpl_connect('button_press_event', s.recv)
#fig.canvas.mpl_connect('motion_notify_event', report)
fig.canvas.mpl_connect('button_release_event', s.recv)

density_plot(mandelbrot(x,y), x, y)
plt.show()
