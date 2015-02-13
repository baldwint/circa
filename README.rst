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

Next, install wanglib_ as directed on that Github page.

Finally, using pip_:

.. code-block:: console

    $ pip install --user -e git+https://github.com/baldwint/circa.git#egg=circa

The ``--user`` flag is a good idea to prevent version conflicts with
other users on the same machine. It's unnecessary if you have some
other means of doing that (e.g., in a virtualenv_).

.. _wxPython: http://wxpython.org/
.. _conda: https://store.continuum.io/cshop/anaconda/
.. _wanglib: https://github.com/baldwint/wanglib
.. _pip: http://www.pip-installer.org/
.. _virtualenv: http://www.virtualenv.org/

Programs
--------

Circa contains a several programs targeting a couple of different tasks.

The main confocal-imaging program is launched by typing

.. code-block:: console

    $ circa

If this doesn't work, try ``python -m circa`` or ``pythonw -m circa``.
This program scans galvonometers using a 12-bit DAC (NI-USB-6008 or
NI-USB-6009) and counts photons with a pair of counters on some other
NI-DAQ device.

To monitor a graph of counts per second, use

.. code-block:: console

    $ python -m circa.monitor

This is useful for optimizing the counts when doing fine focusing.

During coarse focusing and alignment, it is sometimes useful to have a
quickly-refreshing image. This isn't possible with our usual DACs
since there is no timing support, but we can get very fast scanning by
pre-loading the scan pattern on a pair of Tektronix AFGs. To do this,
use an alternate version of the confocal imaging program:

.. code-block:: console

    $ python -m circa.fast

Both of the imaging programs save data in a raw ``.npz`` format. These
can be loaded back into the imaging program to re-use the scan
settings, or into a separate viewer program just to see the image:

.. code-block:: console

    $ python -m circa.viewer

Configuration
-------------

Parameters for the data aquisition - that is, the DAQ channels, GPIB
addresses, and so on - can be configured in a file called
``circa.cfg`` in your home directory. An example configuration (for
Andrew's cryogenic setup) can be found in ``circa_example.cfg``.
