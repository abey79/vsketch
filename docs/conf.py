# Configuration file for the Sphinx documentation builder.
#
# This file only contains a selection of the most common options. For a full
# list see the documentation:
# https://www.sphinx-doc.org/en/master/usage/configuration.html

# -- Path setup --------------------------------------------------------------

# If extensions (or modules to document with autodoc) are in another directory,
# add these directories to sys.path here. If the directory is relative to the
# documentation root, use os.path.abspath to make it absolute, like shown here.
#
# import os
# import sys
# sys.path.insert(0, os.path.abspath('.'))

# -- Project information -----------------------------------------------------

project = "vsketch"
copyright = "2020-2022, Antoine Beyeler"
author = "Antoine Beyeler"

# -- General configuration ---------------------------------------------------

# Add any Sphinx extension module names here, as strings. They can be
# extensions coming with Sphinx (named 'sphinx.ext.*') or your custom
# ones.
extensions = [
    "sphinx.ext.autodoc",
    "sphinx.ext.intersphinx",
    "sphinx.ext.autosummary",
    "sphinx.ext.napoleon",
    "myst_parser",
    "sphinx_copybutton",
]


# -- Autodoc

autodoc_default_flags = ["members"]
autosummary_generate = True
add_module_names = False
autosummary_imported_members = True


# Add any paths that contain templates here, relative to this directory.
templates_path = ["_templates"]

# List of patterns, relative to source directory, that match files and
# directories to ignore when looking for source files.
# This pattern also affects html_static_path and html_extra_path.
exclude_patterns = ["_build", "Thumbs.db", ".DS_Store", "venv", ".*"]

# -- Global options ----------------------------------------------------------

# Don't mess with double-dash used in CLI options
smartquotes_action = "qe"

# -- Options for HTML output -------------------------------------------------

# The theme to use for HTML and HTML Help pages.  See the documentation for
# a list of builtin themes.
#
html_theme = "furo"

# Add any paths that contain custom static files (such as style sheets) here,
# relative to this directory. They are copied after the builtin static files,
# so a file named "default.css" will overwrite the builtin "default.css".
html_static_path = ["_static"]

# -- Intersphinx options
intersphinx_mapping = {
    "shapely": ("https://shapely.readthedocs.io/en/latest/", None),
    "vpype": ("https://vpype.readthedocs.io/en/latest/", None),
    "python": ("https://docs.python.org/3/", None),
}


# -- Napoleon options

napoleon_include_init_with_doc = False


# noinspection PyUnusedLocal
def autodoc_skip_member(app, what, name, obj, skip, options):

    exclusions = (
        # vsketch/param.py
        "get_params",
        "set_param_set",
        "params",
        "param_set",
        # misc from vsk
        "working_directory",
        "execute",
        "execute_draw",
        "ensure_finalized",
    )
    is_private = name.startswith("_")  # and name != "__init__"
    exclude = name in exclusions or is_private
    return skip or exclude


def setup(app):
    app.connect("autodoc-skip-member", autodoc_skip_member)
