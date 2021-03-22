"""This module implements the vsketch API."""

from .sketch_class import Param, ParamType, SketchClass
from .utils import working_directory
from .vsketch import Vsketch

__all__ = ["Vsketch", "Param", "ParamType", "SketchClass", "working_directory"]


def _init():
    from .environment import setup

    setup()


_init()
