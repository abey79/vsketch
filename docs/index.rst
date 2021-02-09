==================
What is *vsketch*?
==================

*vsketch* is a Python generative art toolkit for plotter with focuses on the following:

* **Accessibility**: vsketch is easy to learn and feels familiar thanks to its API strongly inspired from
  `Processing`_.
* **Minimized friction**: vsketch automates every part of the creation process
  (project initialisation, friction-less iteration, export to plotter-ready files) through a CLI tool called ``vsk``
  and a tight integration with `vpype`_.
* **Plotter-centric**: vsketch is made for plotter users, by plotter users. It's feature set is focused on the
  peculiarities of this medium and doesn't aim to solve other problems.
* **Interoperability**: vsketch plays nice with popular packages such as `Numpy`_ and `Shapely`_, which are true
  enabler for plotter generative art.

*vsketch* is the sum of two things:

* A CLI tool named ``vsk`` with the following capabilities:

    - Project ("sketch") creation based on a template.
    - Interactive render of your sketch with live-reload and custom parameters.
    - Batch export to SVG with random seed and configuration management as well as multiprocessing support.

* An API similar to `Processing`_ to build your sketch.

.. _Numpy: https://numpy.org
.. _Shapely: https://shapely.readthedocs.io/en/latest/
.. _vpype: https://github.com/abey79/vpype/
.. _Processing: https://processing.org

*This project is at an early the stage and needs contributions.*


Contents
________

.. toctree::
   :maxdepth: 3

   self
   install
   overview
   contributing
   reference
   license
