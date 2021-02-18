========
Overview
========


.. highlight:: bash


Simplify your workflow with ``vsk``
===================================

*vsketch* includes a CLI tool called ``vsk`` that aims to automate every part of your workflow, from initial creation to
final export, with the overarching objective of minimising the friction in the creative process. The following
paragraphs demonstrate how ``vsk`` is typically used for various phases in a sketch project life-cycle.


Creating a sketch with ``vsk init``
-----------------------------------

Basic use::

    $ vsk init my_project

The page size and orientation can be directly provided::

    $ vsk init -p a4 -l my_project

A custom template can be provided::

    $ vsk init --template path/to/template my_project

The template path may point to a file or a git repository. Templating is based on the `cookiecutter`_ project. The
`default template`_ can be forked to serve as a basis. If the environment variable ``VSK_TEMPLATE`` is defined, it will
be used as template by default.


.. _cookiecutter: https://cookiecutter.readthedocs.io
.. _default template: https://github.com/abey79/cookiecutter-vsketch-sketch


Running a sketch with ``vsk run``
---------------------------------

This commands execute the sketch script and displays the interactive viewer::

    $ vsk run my_project

The viewer refreshes the display every time the sketch script is saved or parameters are modified in the interface.

If a second screen is available, it can be automatically used for the viewer::

    $ vsk run --fullscreen my_project

This can ben permanently enabled by setting the ``VSK_FULLSCREEN`` environment variable.

If the ``--editor`` option is passed, it will be used to open the sketch script in the corresponding editor::

    $ vsk run --editor charm my_project

Most popular IDE and editors have such a command (e.g. ``charm`` for PyCharm, ``code`` for VSCode, ``mate`` for
TextMate, etc.). Again, setting the ``VSK_EDITOR`` environment variable enables this feature permanently.


Exporting SVG with ``vsk save``
-------------------------------

Basic use (uses a random seed)::

    $ vsk save my_project

The random number generator seed can be specified::

    $ vsk save --seed 10 my_project

Alternatively, a range of seeds can be specified::

    $ vsk save --seed 0..99 my_project

In this case, all CPU cores are used to export SVG for every seed value within the provided range. This can be
controlled with the ``--multiprocessing / --no-multiprocessing`` options and the ``VSK_MULTIPROCESSING`` environment
variable.

If configurations have been saved using ``vsk run``, they can be used for exporting as well::

    $ vsk save --config my_config my_project


Beyond the basics?
------------------

Every single feature of ``vsk`` is documented in the integrated help. You can access the global help as follows::

    $ vsk --help

This will list the available commands as well as the global options.

Each command has its dedicated help section as well. For example, you can access the ``vsk run`` command as follows::

    $ vsk run --help


Write sketches with the *vsketch* API
=====================================

.. currentmodule:: vsketch
.. highlight:: python

Sketches are made of code and *vsketch* API makes this code familiar, concise and easy-to-learn. The following
paragraphs provides an overview of how a sketch is made.


Sketch structure
----------------

Sketch scripts always have the same structure::

    import vsketch

    class MySketch(vsketch.Vsketch):
        def draw(self) -> None:
            self.size("a4", landscape=False)

        def finalize(self) -> None:
            self.vpype("linemerge linesimplify reloop linesort")


    if __name__ == "__main__":
        vsk = MySketch()
        self.draw()
        self.finalize()
        self.display(mode="matplotlib")

This structure is typically created using the ``vsk init`` command.

Your sketch is encapsulated in a subclass of :class:`Vsketch` which must implement two functions:

    * :meth:`Vsketch.draw` implements the bulk of the sketch's content.
    * :meth:`Vsketch.finalize` implements the potentially CPU-heavy optimisations that are not required for
      display purposes.

For display purposes, ``vsk`` only calls :meth:`Vsketch.draw()`. However, when it exports a sketch to a SVG file, it
also calls :meth:`Vsketch.finalize`. This enables a fast refresh of the display when the sketch or its parameters change
while ensuring that any SVG output is ready to plot.


Primitives
----------

The usual primitives are available::

    self.line(0, 0, 10, 20)
    self.rect(10, 10, 5, 8)
    self.circle(2, 2, radius=3)
    self.triangle(0, 0, 1, 1, 0, 1)

So are the less usual primitives::

    self.bezier(1, 1, 3, 1, 3, 3, 1, 3)


Units
-----

By default, vsketch uses CSS pixels as unit, just like SVG. If you'd rather work in some other unit,
just start your sketch with a scale factor::

    self.scale("1cm")
    self.line(0, 0, 21, 29.7)  # this line will span an entire A4 page


Strokes, fills and layers
-------------------------

Colors do not really make sense when preparing files for plotters. *vsketch* instead uses layers which are
intended to be plotted with different pens each::

    # by default, layer 1 is current
    self.line(0, 0, 5, 5)

    # the current layer can be changed
    self.stroke(2)
    self.circle(14, 8, 3)

No reason plotters should miss on the "fill" party! This works just as you didn't dare to expect::

    # let's use a pen width of 0.5mm for layer 2
    self.penWidth("0.5mm", 2)

    # this circle will be stroked in layer 1 and and filled in layer 2
    self.stroke(1)
    self.fill(2)
    self.circle(0, 0, 5)


Using Shapely
-------------

`Shapely <https://shapely.readthedocs.io/en/latest/>`_ is a computational geometry library that is often
very useful for generative plotter art. *vsketch* directly accepts Shapely objects::

    from shapely.geometry import Point

    self.geometry(Point(0, 0).buffer(2).union(Point(1.5, 0).buffer(1.5)))


Transforms
----------

Transformation matrices are fully supported::

    for i in range(5):
        with pushMatrix():
            self.rotate(i * 5, degrees=True)
            self.rect(-2, -2, 2, 2)

        self.translate(5, 0)

Internally, vsketch approximates all curves with segments. The level of detail (i.e. the maximum length of individual
segment) can be adjusted. *vsketch* tries to be smart about this::

    self.detail("0.1mm")

    # this circle is made of segment 0.1mm-long or less
    self.circle(0, 0, radius=1)

    self.scale(100)

    # because it is bigger, this circle will be made of many more segments than the previous one
    self.circle(0, 0, radius=1)


Perlin noise
------------

The :meth:`noise` is a vectorized implementation of Perlin noise that can sample a random space of up to 3 dimensions.
This example illustrate the case of a vectorised sampling of a 2D noise space::

    num_lines = 250
    x_coords = np.linspace(0., 250., 1000)
    perlin = self.noise(x_coords * 0.1, np.linspace(0, 5., num_lines))
    for j in range(num_lines):
        self.polygon(x_coords, j + perlin[:, j] * 6)


Using sub-sketches
------------------

Multiple sketches can be created and used as reusable sub-sketches::

    # create a sub-sketch
    sub_sketch = vsketch.Vsketch()
    sub_sketch.square(0, 0, 1)
    sub_sketch.square(0.5, 0.5, 1)

    # add the sub-sketch
    self.sketch(sub_sketch)
    self.translate(10, 10)
    self.rotate(45, degrees=True)
    self.sketch(sub_sketch)  # the transformation matrix is applied on the sub-sketch

Using *vpype*
-------------

The power of `vpype`_ can be unleashed with a single call::

    self.vpype("linesimplify linemerge reloop linesort")

Displaying and saving
---------------------

Usually, ``vsk`` takes care of running, displaying and exporting your sketch as SVG. This is also easy to do from a
regular script. Displaying is done as follows::

    self.display()

Finally, you can save a ready-to-plot SVG::

    self.save("my_file.svg")

As a matter of fact, examples always includes the following code::

    if __name__ == "__main__":
        vsk = MySketch()
        vsk.draw()
        vsk.finalize()
        vsk.display()

This way, the sketch can be executed by Python without having to use the ``vsk`` command.


Beyond the basics?
------------------

.. highlight:: bash

The entire API is documented :class:`here <Vsketch>`.

Exploring the `examples <https://github.com/abey79/vsketch/tree/master/examples>`_ included with *vsketch* is a good
way to learn about its API. If you have a local copy of *vsketch*'s repository, you can run any example with the
following command::

    $ vsk run examples/quick_draw

You may also check the author's `personal collection of sketches <https://github.com/abey79/sketches>`_.

.. _vpype: https://github.com/abey79/vpype/
