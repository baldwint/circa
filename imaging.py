import numpy as n
from pylab import gca
import matplotlib as mpl
mpl.rc('image', interpolation='nearest', origin='lower', cmap='jet')
mpl.rc('figure', figsize=(8,6))

from wanglib.pylab_extensions.density import density_plot

from mpl_toolkits.axes_grid1.anchored_artists import AnchoredSizeBar

def add_sizebar(ax, size, **kwargs):
    kwargs.setdefault('label', str(size))
    kwargs.setdefault('loc', 4)
    asb = AnchoredSizeBar(ax.transData, size, **kwargs)
    ax.add_artist(asb)
    return asb

def show_image(vector, X, Y,
               cal = None, bar = 1.,
               ax = None, cax=None, hist=True, **kwargs):
    """
    show a density plot with a sizebar,

    cal: calibration (um per pixel)
    bar: length of bar (in um)

    """
    if ax is None:
        ax = gca()
    im = density_plot(vector, X, Y, ax=ax, **kwargs)
    cbar = ax.figure.colorbar(im, cax=cax)
    if hist:
        add_hist_to_cbar(im)
        im.callbacksSM.connect('changed', add_hist_to_cbar)
    if cal is not None:
        sb = add_sizebar(ax,
                          size=bar/cal,
                          label='%dum' % bar,
                          pad=.3, borderpad=.2,
                          frameon=True)
        sb.patch.set_alpha(0.5)
    return im

from matplotlib.patches import Polygon

def add_hist_to_cbar(im, cbar=None):
    """ Add histogram to colorbar """
    if cbar is None:
        cbar = im.colorbar

    # need this or it doesn't work
    cbar.on_mappable_changed(im)

    # compute normalized histogram
    image_data = im.get_array()
    N,edges = n.histogram(image_data, bins=32, range=im.get_clim(),
                          density=True)
    N = N / max(N)

    def gen_patch_edge(N, edges):
        last_N = 0
        for val,edge in zip(N, edges[:-1]):
            yield last_N, edge
            last_N = val
            yield last_N, edge
        yield last_N, edges[-1]
        yield 0, edges[-1]

    # remove any other histogram patches
    for patch in cbar.ax.patches:
        patch.remove()

    # draw histogram over colorbar
    zigzag = list(gen_patch_edge(N, [cbar.norm(edge) for edge in edges]))
    histpatch = Polygon(zigzag, color='w', alpha=.5, ec='k')
    cbar.ax.add_patch(histpatch)

    return histpatch


#from matplotlib.colorbar import Colorbar
#
#class HistColorbar(Colorbar):
#
#    def __init__(self, ax, mappable, **kw):
#        Colorbar.__init__(self, ax, mappable, **kw)
#        self.on_mappable_changed(mappable)
#
#    def on_mappable_changed(self, mappable):
#        Colorbar.on_mappable_changed(self, ax, mappable, **kw)
#        add_hist_to_cbar(mappable, self)


