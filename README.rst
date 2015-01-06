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

Using pip_:

.. code-block:: console

    $ pip install -e git+https://github.com/baldwint/circa.git#egg=circa

.. _pip: http://www.pip-installer.org/
