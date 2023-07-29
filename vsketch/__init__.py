"""This module implements the vsketch API."""

# isort: skip_file

# Ordered for the documentation
from .vsketch import Vsketch
from .shape import Shape
from .sketch_class import SketchClass, Param, ParamType

from .easing import EASING_FUNCTIONS
from .utils import working_directory


__all__ = [
    "Vsketch",
    "Param",
    "ParamType",
    "SketchClass",
    "Shape",
    "working_directory",
    "EASING_FUNCTIONS",
    "__version__",
]


def _get_version() -> str:
    from importlib.metadata import version

    return version(__name__)


__version__ = _get_version()
