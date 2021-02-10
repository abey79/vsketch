"""This module implements the vsketch API."""

from .param import Param, ParamType
from .vsketch import Vsketch

__all__ = ["Vsketch", "Param", "ParamType"]


def _init():
    from .environment import setup

    setup()


_init()
