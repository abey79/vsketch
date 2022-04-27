.. _install:

============
Installation
============


.. note::

   *vsketch* heavily relies on `vpype <https://github.com/abey79/vpype>`__. Although *vpype* is automatically installed as a dependency when installing *vsketch*, it may be useful to review *vpype*'s `installation instructions <https://vpype.readthedocs.io/en/latest/install.html>`__ for additional details and troubleshooting.

.. caution::

   Like *vpype*, installing *vsketch* on **Apple-silicon-based Macs** requires special steps. Please carefully review the present instructions as well as *vpype*'s `installation instructions <https://vpype.readthedocs.io/en/latest/install.html>`__.

Installing using pipx
=====================

.. highlight:: bash

The recommended way to install *vsketch* is using pipx as a stand-alone installation::

    $ pipx install git+https://github.com/abey79/vsketch


Installing Apple Silicon/M1 Mac
===============================

On Apple-Silicon-based Mac, pipx is also the recommended installation method. However, specific steps are required.

First, follow the steps and requirements from *vpype* `Mac installation instructions <https://vpype.readthedocs.io/en/latest/install.html#macos>`__. Having *vpype* successfully installed means that all requirements for *vsketch* are met.

Then, use the following command to create a standalone installation of *vsketch*::

  $ pipx install git+https://github.com/abey79/vsketch --system-site-packages


Running the examples
====================

Installing *vsketch* with pipx does *not* install the examples and they must be downloaded separately. An archive from the latest version of the *vsketch* `repository <https://github.com/abey79/vsketch>`__ can be downloaded `here <https://github.com/abey79/vsketch/archive/refs/heads/master.zip>`__. After uncompressing the archive, you can readily execute the examples::

  $ vsk run path/to/vsketch-master/examples/shotter


Installing plug-ins
===================

*vsketch* is compatible with *vpype*'s `plug-ins <https://vpype.readthedocs.io/en/latest/plugins.html>`__. To use plug-ins with *vsketch*, you must install them inside *vsketch* virtual environment. In pipx parlance, this is referred to as "injecting".

For example, run the following command to install `vpype-perspective <https://github.com/abey79/vpype-perspective>`__::

  $ pipx inject vsketch vpype-perspective

.. note::

   Installing plug-in this way is necessary even if you already have them installed with your current *vpype* installation. This is due to pipx maintaining isolated environments for each piece of software installed with it.


Installing from the repository
==============================

If you want to make modification to *vsketch* itself (whether or not you intend to share them for upstream integration), cloning the repository and installing from the source is a better alterative to using pipx.

First, clone the repository using git::

  $ git clone https://github.com/abey79/vsketch
  $ cd vsketch

Then, create a virtual environment and activate it::

  $ python -m venv venv
  $ source venv/bin/activate

.. caution::

   The Apple-Silicon Mac limitations described above and in *vpype* documentation apply here too. On this platform, it strongly suggested to use a MacPorts install of Python, to use the MacPorts to install key dependencies such as PySide2 and Shapely, and create the virtual environment with the following command::

    $ python -m venv venv --system-site-packages

Finally, install *vsketch*::

  $ pip install -e .

The ``-e`` option creates a so-called "editable" install of *vsketch*. This means that any modification made to the source code in the ``vsketch/`` or ``vsketch_cli/`` subdirectories are immediately in effect in your install.

At the point, you are read to use *vsketch*::

  $ vsk run examples/quick_draw

Note that you will need to activate the virtual environment each time you open a new terminal window::

  $ source venv/bin/activate
