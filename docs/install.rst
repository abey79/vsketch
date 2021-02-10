.. _install:

============
Installation
============


Installing *vsketch*
====================

*vsketch* is a regular Python package that is installed with ``pip``::

    pip install git+https://github.com/abey79/vsketch#egg=vsketch

It is generally recommended to use virtual environment. Check `*vpype*'s documentation <https://vpype.readthedocs
.io/en/stable/install.html>`_ for more information on how to setup a virtual environment.



Using notebooks
===============

The primary way to use *vsketch* scripts is through the ``vsk`` CLI tool. Alternatively, *vsketch* can be used in
notebooks such as Jupyter Lab or Google Colab.

.. highlight:: bash

Google Colab
------------

Vpype can be used in browser without any installation steps thanks to the
`Google Colab <https://colab.research.google.com/notebooks/intro.ipynb>`_ free notebook environment. Add this content
to the first cell to setup the environment::

    !pip install git+https://github.com/abey79/vsketch#egg=vsketch

Check Colab notebook in the examples folder: open the notebook and press the "Open in Colab" button, or follow this
`link <https://colab.research.google.com/github/abey79/vsketch/blob/master/examples/_notebooks/google_colab.ipynb>`_.


Jupyter Lab
-----------

`Jupyter Lab <https://jupyterlab.readthedocs.io/en/stable/>`_ is a in-browser notebook environment similar
to Google Colab but running locally on your computer.

To set it up, install vsketch with the following steps::

    python3 -m venv vsketch_venv
    source vsketch_venv/bin/activate
    pip install --upgrade pip
    pip install git+https://github.com/abey79/vsketch#egg=vsketch[jupyterlab]

The install and configure Jupyter Lab with the following steps (these steps include a nice Matplotlib integration as
well as automatic code formatting)::

    jupyter labextension install @jupyter-widgets/jupyterlab-manager
    jupyter labextension install jupyter-matplotlib
    jupyter labextension install @ryantam626/jupyterlab_code_formatter
    jupyter serverextension enable --py jupyterlab_code_formatter

Finally, launch the Jupyter Lab environment with the following command::

    jupyter lab
