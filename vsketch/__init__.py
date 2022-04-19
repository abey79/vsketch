"""This module implements the vsketch API."""

from .easing import EASING_FUNCTIONS
from .shape import Shape
from .sketch_class import Param, ParamType, SketchClass
from .utils import working_directory
from .vsketch import Vsketch

__all__ = [
    "Vsketch",
    "Param",
    "ParamType",
    "SketchClass",
    "Shape",
    "working_directory",
    "EASING_FUNCTIONS",
]


def _init():
    from .environment import setup

    setup()


_init()
