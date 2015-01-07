Confocal Image Raster-Counting Acquisition (``circa``)
======================================================

Circa is a graphical user interface (GUI) for use with homebuilt
confocal imaging microscopes in the Wang lab. Our setups are based on
National Instruments DACs and pulse counters, in combination with
ThorLabs galvonometers and photon counting modules.

This program is built on PyDAQmx for instrument control, the wxPython
widget toolkit, and matplotlib.

Installation
------------

First, install wxPython_. I've always had trouble installing this
using pip, but have had success using conda_, or the official
wxPython binaries.

Then, using pip_:

.. code-block:: console

    $ pip install -e git+https://github.com/baldwint/circa.git#egg=circa

.. _wxPython: http://wxpython.org/
.. _conda: https://store.continuum.io/cshop/anaconda/
.. _pip: http://www.pip-installer.org/
