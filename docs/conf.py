# Configuration file for the Sphinx documentation builder.
#
# This file only contains a selection of the most common options. For a full
# list see the documentation:
# https://www.sphinx-doc.org/en/master/usage/configuration.html


# -- Project information -----------------------------------------------------

project = "vsketch"
copyright = "2020-2022, Antoine Beyeler"
author = "Antoine Beyeler"

# -- General configuration ---------------------------------------------------

# Add any Sphinx extension module names here, as strings. They can be
# extensions coming with Sphinx (named 'sphinx.ext.*') or your custom
# ones.
extensions = [
    "sphinx.ext.intersphinx",
    "sphinx.ext.napoleon",
    "myst_parser",
    "sphinx_copybutton",
    "autoapi.extension",
]


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
    "numpy": ("https://numpy.org/doc/stable/", None),
}

# -- Napoleon options
napoleon_include_init_with_doc = False

# -- autoapi configuration ---------------------------------------------------

autodoc_typehints = "signature"  # autoapi respects this

autoapi_type = "python"
autoapi_dirs = ["../vsketch"]
autoapi_template_dir = "_templates/autoapi"
autoapi_options = [
    "members",
    "undoc-members",
    "show-inheritance",
    "show-module-summary",
    "imported-members",
]
# autoapi_python_use_implicit_namespaces = True
autoapi_keep_files = True
# autoapi_generate_api_docs = False


# -- custom auto_summary() macro ---------------------------------------------


def contains(seq, item):
    """Jinja2 custom test to check existence in a container.

    Example of use:
    {% set class_methods = methods|selectattr("properties", "contains", "classmethod") %}

    Related doc: https://jinja.palletsprojects.com/en/3.1.x/api/#custom-tests
    """
    return item in seq


def prepare_jinja_env(jinja_env) -> None:
    """Add `contains` custom test to Jinja environment."""
    jinja_env.tests["contains"] = contains


autoapi_prepare_jinja_env = prepare_jinja_env

# Custom role for labels used in auto_summary() tables.
rst_prolog = """
.. role:: summarylabel
"""

# Related custom CSS
html_css_files = [
    "css/label.css",
]


# noinspection PyUnusedLocal
def autoapi_skip_members(app, what, name, obj, skip, options):
    # skip submodules
    if what == "module":
        skip = True
    elif what == "data":
        if obj.name in ["EASING_FUNCTIONS", "ParamType"]:
            skip = True
    elif what == "function":
        if obj.name in ["working_directory"]:
            skip = True
    elif "vsketch.SketchClass" in name:
        if obj.name in [
            "vsk",
            "param_set",
            "execute_draw",
            "ensure_finalized",
            "execute",
            "get_params",
            "set_param_set",
        ]:
            skip = True
    elif "vsketch.Param" in name:
        if obj.name in ["set_value", "set_value_with_validation"]:
            skip = True
    return skip


def setup(app):
    app.connect("autoapi-skip-member", autoapi_skip_members)
