from typing import TYPE_CHECKING, Tuple

import numpy as np

if TYPE_CHECKING:
    import vsketch


class MatrixPopper:
    def __init__(self, vsk: "vsketch.Vsketch"):
        self._vsk = vsk

    def __enter__(self):
        pass

    def __exit__(self, exc_type, exc_val, exc_tb):
        self._vsk.popMatrix()


def complex_to_2d(line: np.ndarray) -> np.ndarray:
    return np.vstack([line.real, line.imag]).T


def compute_ellipse_mode(
    mode: str, x: float, y: float, w: float, h: float
) -> Tuple[float, float, float, float]:
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
