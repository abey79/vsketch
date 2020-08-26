import math
from typing import Tuple

import bezier
import numpy as np


def _interp_bezier(curve: bezier.Curve, detail: float) -> np.ndarray:
    """Strategy: interpolate at 1/5th target resolution and generate s param based
    on resulting segment length.


    """
    s = np.linspace(0, 1, max(3, math.ceil(curve.length / detail / 5)))
    x, y = curve.evaluate_multi(s)

    curv_absc = np.cumsum(np.hstack([0, np.hypot(np.diff(x), np.diff(y))]))

    new_s = np.interp(
        np.linspace(0, curv_absc[-1], max(3, math.ceil(1.15 * curve.length / detail))),
        curv_absc,
        s,
    )

    x, y = curve.evaluate_multi(new_s)
    return x + 1j * y


def quadratic_bezier_path(
    x1: float,
    y1: float,
    x2: float,
    y2: float,
    x3: float,
    y3: float,
    x4: float,
    y4: float,
    detail: float,
) -> np.ndarray:
    """Compute a piece-wise linear path approximating a quadratic bezier. Length of individual
    segments is close to but never greater than ``detail``."""

    curve = bezier.Curve(np.array([[x1, x2, x3, x4], [y1, y2, y3, y4]]), degree=3, copy=False)
    return _interp_bezier(curve, detail)


def quadratic_bezier_point(
    x1: float,
    y1: float,
    x2: float,
    y2: float,
    x3: float,
    y3: float,
    x4: float,
    y4: float,
    t: float,
) -> Tuple[float, float]:
    """Evaluate a bezier curve at a given point, based on t in [0, 1].
    """

    curve = bezier.Curve(np.array([[x1, x2, x3, x4], [y1, y2, y3, y4]]), degree=3, copy=False)
    [x], [y] = curve.evaluate(t)
    return x, y


def quadratic_bezier_tangent(
    x1: float,
    y1: float,
    x2: float,
    y2: float,
    x3: float,
    y3: float,
    x4: float,
    y4: float,
    t: float,
) -> Tuple[float, float]:
    """Evaluate a bezier curve at a given point, based on t in [0, 1].
    """

    curve = bezier.Curve(np.array([[x1, x2, x3, x4], [y1, y2, y3, y4]]), degree=3, copy=False)
    [x], [y] = curve.evaluate_hodograph(t)
    return x, y
