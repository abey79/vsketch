.. _install:

============
Installation
============


.. note::

   *vsketch* heavily relies on `vpype <https://github.com/abey79/vpype>`__. Although *vpype* is automatically installed as a dependency when installing *vsketch*, it may be useful to review *vpype*'s `installation instructions <https://vpype.readthedocs.io/en/latest/install.html>`__ for additional details and troubleshooting.


Installing using pipx
=====================

.. highlight:: bash

The recommended way to install *vsketch* is using pipx as a stand-alone installation::

    $ pipx install "git+https://github.com/abey79/vsketch"



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

If you want to make modifications to *vsketch* itself (whether or not you intend to share them for upstream integration), you must clone the repository and install *vsketch* from source.

Like *vpype*, *vsketch* uses `Poetry <https://python-poetry.org>`__ as project manager. `Various methods <https://python-poetry.org/docs/#installation>`__ are available to install Poetry. Using pipx is one of them::

  $ pipx install poetry

Once Poetry is installed, clone the repository using git::

  $ git clone https://github.com/abey79/vsketch
  $ cd vsketch

From there, Poetry can install everything needed for development environment using a few commands. Though this can be done automatically, it is a good practice to explicitly create a virtual environment by specifying which Python interpreter to use::

  $ poetry env use /opt/local/bin/python3.10

This command will create a new virtual environment for the project using the provided Python interpreter (here Python 3.10 as installed by `MacPorts <https://www.macports.org>`__ on macOS – adjust as needed), and mark it as the default. Note that Poetry can handle any number of virtual environments for the project, for example with different versions of Python. At any time, one of the virtual environment is marked as default and used by other Poetry commands.

Then, everything needed to run *vsketch*, including what's needed for development, can be installed with this command::

  $ poetry install

By default, Poetry doesn't activate the virtual environment, but provides ``poetry run`` to execute commands it contains::

  $ poetry run vsk run examples/quick_draw

Alternatively, the project's default virtual environment can be activated using the following command::

  $ poetry shell
  $ vsk run examples/quick_draw

Poetry is a very powerful tool with many capabilities. Make sure to review `its documentation <https://python-poetry.org/docs/>`__.
