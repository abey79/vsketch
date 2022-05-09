from __future__ import annotations

import math
from typing import overload

import numpy as np


@overload
def _cubic_bezier(
    x1: float,
    y1: float,
    x2: float,
    y2: float,
    x3: float,
    y3: float,
    x4: float,
    y4: float,
    positions: float,
) -> tuple[float, float]:
    ...


@overload
def _cubic_bezier(
    x1: float,
    y1: float,
    x2: float,
    y2: float,
    x3: float,
    y3: float,
    x4: float,
    y4: float,
    positions: np.ndarray,
) -> tuple[np.ndarray, np.ndarray]:
    ...


def _cubic_bezier(
    x1: float,
    y1: float,
    x2: float,
    y2: float,
    x3: float,
    y3: float,
    x4: float,
    y4: float,
    positions: float | np.ndarray,
) -> tuple[float | np.ndarray, float | np.ndarray]:
    """Compute cubic bezier at positions."""

    pos_3 = positions * positions * positions
    n_pos = 1 - positions
    n_pos_3 = n_pos * n_pos * n_pos
    pos_2_n_pos = positions * positions * n_pos
    n_pos_2_pos = n_pos * n_pos * positions
    return (
        n_pos_3 * x1 + 3 * (n_pos_2_pos * x2 + pos_2_n_pos * x3) + pos_3 * x4,
        n_pos_3 * y1 + 3 * (n_pos_2_pos * y2 + pos_2_n_pos * y3) + pos_3 * y4,
    )


def _cubic_bezier_interpolate(
    x1: float,
    y1: float,
    x2: float,
    y2: float,
    x3: float,
    y3: float,
    x4: float,
    y4: float,
    detail: float,
) -> tuple[np.ndarray, np.ndarray]:
    """Strategy:

    1) estimate length:
        - rough estimate according to https://stackoverflow.com/a/37862545/229511
        - linspace at 10x details

    2) produce final curve
        - linspace at 5x details with correct length
    """

    # produce a length estimate based on the average between the chord and the path going
    # through all control points
    chord = math.hypot(x4 - x1, y4 - y1)
    cont_net = (
        math.hypot(x2 - x1, y2 - y1)
        + math.hypot(x3 - x2, y3 - y2)
        + math.hypot(x4 - x3, y4 - y3)
    )
    length_estimate = (chord + cont_net) / 2

    # produce a sampling at 10x details, based on estimated length
    s = np.linspace(0, 1, max(3, math.ceil(length_estimate / detail / 10)))
    x, y = _cubic_bezier(x1, y1, x2, y2, x3, y3, x4, y4, s)
    length = np.sum(np.hypot(np.diff(x), np.diff(y)))

    # based on the properly estimated length, produce a sampling at 5x details
    s = np.linspace(0, 1, max(3, math.ceil(length / detail / 5)))
    x, y = _cubic_bezier(x1, y1, x2, y2, x3, y3, x4, y4, s)

    # compute curvilinear abscissa and produce final sampling, at detail + 15%
    curv_absc = np.cumsum(np.hstack([0, np.hypot(np.diff(x), np.diff(y))]))
    new_s: np.ndarray = np.interp(
        np.linspace(0, curv_absc[-1], max(3, math.ceil(1.15 * length / detail))),
        curv_absc,
        s,
    )

    return _cubic_bezier(x1, y1, x2, y2, x3, y3, x4, y4, new_s)


@overload
def _cubic_bezier_tangent(
    x1: float,
    y1: float,
    x2: float,
    y2: float,
    x3: float,
    y3: float,
    x4: float,
    y4: float,
    positions: float,
) -> tuple[float, float]:
    ...


@overload
def _cubic_bezier_tangent(
    x1: float,
    y1: float,
    x2: float,
    y2: float,
    x3: float,
    y3: float,
    x4: float,
    y4: float,
    positions: np.ndarray,
) -> tuple[np.ndarray, np.ndarray]:
    ...


def _cubic_bezier_tangent(
    x1: float,
    y1: float,
    x2: float,
    y2: float,
    x3: float,
    y3: float,
    x4: float,
    y4: float,
    positions: float | np.ndarray,
) -> tuple[float | np.ndarray, float | np.ndarray]:
    """
    Compute cubic bezier tangent according to https://stackoverflow.com/a/48255154/229511
    """

    pos_2 = positions * positions
    n_pos = 1 - positions
    pos_n_pos = positions * n_pos
    n_pos_2 = n_pos * n_pos

    return (
        3 * n_pos_2 * (x2 - x1) + 6 * pos_n_pos * (x3 - x2) + 3 * pos_2 * (x4 - x3),
        3 * n_pos_2 * (y2 - y1) + 6 * pos_n_pos * (y3 - y2) + 3 * pos_2 * (y4 - y3),
    )


def cubic_bezier_path(
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

    x, y = _cubic_bezier_interpolate(x1, y1, x2, y2, x3, y3, x4, y4, detail)
    return x + 1j * y


def cubic_bezier_point(
    x1: float,
    y1: float,
    x2: float,
    y2: float,
    x3: float,
    y3: float,
    x4: float,
    y4: float,
    t: float,
) -> tuple[float, float]:
    """Evaluate a bezier curve at a given point, based on t in [0, 1]."""

    return _cubic_bezier(x1, y1, x2, y2, x3, y3, x4, y4, t)


def cubic_bezier_tangent(
    x1: float,
    y1: float,
    x2: float,
    y2: float,
    x3: float,
    y3: float,
    x4: float,
    y4: float,
    t: float,
) -> tuple[float, float]:
    """Evaluate a bezier curve at a given point, based on t in [0, 1]."""

    return _cubic_bezier_tangent(x1, y1, x2, y2, x3, y3, x4, y4, t)
