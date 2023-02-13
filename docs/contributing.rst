.. _contributing:

============
Contributing
============


How can you help?
=================

Here is what you can do to help the project:

- Use vsketch and let people know about it.
- Give any type of feedback (what works well, missing features, possible API improvement, bugs, etc.) by opening an
  issue or contacting the author.
- Contribute to the improvement of this documentation.
- Contribute code via pull requests.

In case of doubt, let's get the discussion started on the
`Drawingbots Discord server <https://discordapp.com/invite/XHP3dBg>`_.


Development environment
=======================

.. highlight:: bash

If you intend to modify vsketch (either for your own purpose or contribute improvements), you will need to properly
setup a development environment. Vsketch uses `Poetry <https://python-poetry.org>`_ for project management (see
`installation instructions <https://python-poetry.org/docs/#installation>`_). Then, run the following commands::

    git clone https://github.com/abey79/vsketch
    cd vsketch
    poetry install --with docs # installs everything needed including vsketch in editable mode

Poetry will automatically create a virtual environment. You can spawn a shell with the virtual environment activated
with the following command::

    poetry shell

You can run tests with the following command::

  $ poetry run pytest


Using ``just``
--------------

*vsketch* provides a ``justfile`` for common operations. `Just <https://just.systems/man/en/>`__ must be installed to use it.

The following command list the available recipes:

    just -l

For example, you may build the documentation using this command:

    just docs-build

Available recipes include:

- ``just docs-build`` : build the documentation
- ``just docs-clean`` : clean the documentations build file
- ``just docs-live`` : run a live server for the documentation
- ``just install`` : install a complete dev environment
- ``just test`` : run all tests
- ``just test-failed`` : run previously failed tests
- ``just update-deps`` : update Poetry's lockfile


Donations
=========

You can help the project making `Ko-Fi donation <https://ko-fi.com/abey79>`_ or
`sponsoring me <https://github.com/sponsors/abey79>`_ on GitHub. The funds will be used to cover my development costs.
