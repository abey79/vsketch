=======
vsketch
=======

.. start-doc-inclusion-marker

Vsketch is plotter generative art toolkit based based on `vpype <https://github.com/abey79/vpype/>`_ and suited
for use within Jupyter notebooks. Its API is loosely based on that of `Processing <https://processing.org>`_ and
it plays nicely with `Shapely <https://shapely.readthedocs.io/en/latest/>`_.

*This project is at the stage of the very early concept/prototype and welcomes contributions.*

Installation
============

.. highlight:: bash

Follow these steps to install vsketch::

    git clone https://github.com/abey79/vsketch
    cd vsketch
    python3 -m venv venv
    source venv/bin/activate
    pip install --upgrade pip
    pip install -r requirements.txt
    pip install -e .
    
Follow these steps to setup a nice Jupyter Lab environment with interactive matplotlib widget and automatic code
formatting with `black <https://github.com/psf/black>`_::

    jupyter labextension install @jupyter-widgets/jupyterlab-manager jupyter-matplotlib @ryantam626/jupyterlab_code_formatter
    jupyter serverextension enable --py jupyterlab_code_formatter

    # start jupyter lab
    jupyter lab


Overview
========

.. highlight:: python

To get started with vsketch only takes two lines::

    import vsketch

    vsk = vsketch.Vsketch()
    vsk.size("a3", landscape=True)
    
The usual primitives are available::

    vsk.line(0, 0, 10, 20)
    vsk.rect(10, 10, 5, 8)
    vsk.circle(2, 2, radius=3)
    vsk.triangle(0, 0, 1, 1, 0, 1)
    
By default, vsketch uses CSS pixels as unit, just like SVG. If you'd rather work in some other unit,
just start your sketch with a scale factor::

    vsk.scale("1cm")
    vsk.line(0, 0, 21, 29.7)  # this line will span an entire A4 page
    
Colors do not really make sense when preparing files for plotters. Vsketch instead uses layers which are
intended to be plotted with different pens each::

    # by default, layer 1 is current
    vsk.line(0, 0, 5, 5)
    
    # the current layer can be changed
    vsk.stroke(2)
    vsk.circle(14, 8, 3)

No reason plotters should miss on the "fill" party! This works just as you didn't dare to expect::

    # let's use a pen width of 0.5mm for layer 2
    vsk.penWidth("0.5mm", 2)

    # this circle will be stroked in layer 1 and and filled in layer 2
    vsk.stroke(1)
    vsk.fill(2)
    vsk.circle(0, 0, 5)
    
`Shapely <https://shapely.readthedocs.io/en/latest/>`_ is a computational geometry library that is often
very useful for generative plotter art. Vsketch directly accepts Shapely objects::

    from shapely.geometry import Point
    
    vsk.geometry(Point(0, 0).buffer(2).union(Point(1.5, 0).buffer(1.5)))
    
Transformation matrices are fully supported::

    for i in range(5):
        with pushMatrix():
            vsk.rotate(i * 5, degrees=True)
            vsk.rect(-2, -2, 2, 2)
        
        vsk.translate(5, 0)

Internally, vsketch approximates all curves with segments. The level of detail (i.e. the maximum length of individual
segment) can be adjusted. Vsketch tries to be smart about this::

    vsk.detail("0.1mm")

    # this circle is made of segment 0.1mm-long or less
    vsk.circle(0, 0, radius=1)

    vsk.scale(100)

    # because it is bigger, this circle will be made of many more segments than the previous one
    vsk.circle(0, 0, radius=1)

Multiple sketches can be created and used as reusable sub-sketches::

    # create a sub-sketch
    sub_sketch = vsketch.Vsketch()
    sub_sketch.square(0, 0, 1)
    sub_sketch.square(0.5, 0.5, 1)

    # add the sub-sketch
    vsk.sketch(sub_sketch)
    vsk.translate(10, 10)
    vsk.rotate(45, degrees=True)
    vsk.sketch(sub_sketch)  # the transformation matrix is applied on the sub-sketch

The power of `vpype`_ can be unleashed with a single call::

    vsk.pipeline("linemerge reloop linesort")
    
Displaying your sketch is as easy as::

    vsk.plot()
    
Finally, you can save a ready-to-plot SVG::

    vsk.save("my_file.svg")
    
See also included the multiple examples included in the repository.


Contributing
============

Issues and pull-request are most welcome contributions. Let's get the discussion started on the
`Drawingbots Discord server <https://discordapp.com/invite/XHP3dBg>`_.


.. stop-doc-inclusion-marker

License
=======

This project is licensed under the MIT License - see the `LICENSE <LICENSE>`_ file for details.
