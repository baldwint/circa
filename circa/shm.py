from time import sleep
NAPTIME = .1

def shm(omega, dt):
    x = 0.
    y = 1.
    t = 0.
    while True:
        yield t,x
        sleep(NAPTIME)
        t += dt
        x += omega * y * dt
        y -= omega * x * dt
        # the above is right by mistake.
        # the following makes sense but is wrong
        #x,y = x + omega * y * dt, y - omega * x * dt

class Shm(object):

    def __init__(self, omega, dt):
        self.omega = omega
        self.dt = dt

        self.x = 0.
        self.y = 1.
        self.t = 0.

    def __iter__(self):
        return self

    def __next__(self):
        sleep(NAPTIME)
        t,x = self.t, self.x
        self.t += self.dt
        self.x += self.omega * self.y * self.dt
        self.y -= self.omega * self.x * self.dt
        return t,x

    def next(self):  #python 2
        return self.__next__()


if __name__ == "__main__":
    from math import pi
    gen = Shm(2*pi, .01)

    #from wanglib.pylab_extensions import plotgen
    #import pylab as p
    #p.ion()
    #plotgen(gen)

    import wx
    app = wx.App(False)

    import monitor
    frame = monitor.MonitorWindow(None, 'SHM', datagen=gen)
    frame.Show(True)

    def cf(val):
        gen.omega = 2*pi*(val/2048.)

    import galvo
    frame = galvo.GalvoWindow(None, 'freq control', xcall=cf)
    frame.Show(True)
    app.MainLoop()



