.. _install:

============
Installation
============


Installing *vsketch*
====================

*vsketch* is a regular Python package that is installed with pip or pipx.

The recommended way to install *vpype* via pipx (see the `installation instructions <https://vpype.readthedocs
.io/en/latest/install.html>`__) and then inject *vsketch* in *vpype*'s install::

    $ pipx inject vpype git+https://github.com/abey79/vsketch --include-apps

Note the use of ``--include-apps``. This is necessary so the ``vsk`` command-line tool is made available by pipx.


Apple Silicon/M1 Mac note
-------------------------

The following command must be used instead on this platform::

    $ BEZIER_NO_EXTENSION=true pipx inject vpype git+https://github.com/abey79/vsketch --include-apps
