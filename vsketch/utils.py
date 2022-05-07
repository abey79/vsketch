from __future__ import annotations

import os
import pathlib
from contextlib import contextmanager
from typing import TYPE_CHECKING, Iterator

import numpy as np

if TYPE_CHECKING:
    from . import Vsketch


class MatrixPopper:
    def __init__(self, vsk: Vsketch):
        self._vsk = vsk

    def __enter__(self):
        pass

    def __exit__(self, exc_type, exc_val, exc_tb):
        self._vsk.popMatrix()


class ResetMatrixContextManager:
    """The constructor will be called in both scenarii. __enter__() and
    __exit__() will only be called if used as a context manager (`with` statement)
    """

    def __init__(self, vsk: Vsketch):
        self._vsk = vsk
        self._old_transform = vsk.transform
        self._vsk.transform = np.identity(3)

    def __enter__(self):
        # undo what we did in the contstructor and redo it after pushing the matrix
        self._vsk.transform = self._old_transform
        self._vsk.pushMatrix()
        self._vsk.transform = np.identity(3)

    def __exit__(self, exc_type, exc_val, exc_tb):
        self._vsk.popMatrix()


def complex_to_2d(line: np.ndarray) -> np.ndarray:
    return np.vstack([line.real, line.imag]).T


def compute_ellipse_mode(
    mode: str, x: float, y: float, w: float, h: float
) -> tuple[float, float, float, float]:
    """Interpret parameters based on :meth:`ellipseMode` and compute the ellipse center and
    radii.

    Args:
        mode: :meth:`ellipseMode` mode
        x: first parameter
        y: second parameter
        w: third parameter
        h: fourth parameter

    Returns:
        tuple of center X, Y coordinates and w, h radii
    """
    if mode == "center":
        return x, y, w / 2, h / 2
    elif mode == "radius":
        return x, y, w, h
    elif mode == "corner":
        return x + w / 2, y + h / 2, w / 2, h / 2
    elif mode == "corners":
        # Find center
        xmin, xmax = min(x, w), max(x, w)
        ymin, ymax = min(y, h), max(y, h)
        c_x = xmax - 0.5 * (xmax - xmin)
        c_y = ymax - 0.5 * (ymax - ymin)
        width, height = xmax - xmin, ymax - ymin
        return c_x, c_y, width / 2, height / 2
    else:
        raise ValueError("mode must be one of 'corner', 'corners', 'center', 'radius'")


@contextmanager
def working_directory(path: pathlib.Path) -> Iterator:
    prev_cwd = os.getcwd()
    os.chdir(str(path))
    try:
        yield
    finally:
        os.chdir(prev_cwd)
