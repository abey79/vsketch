from __future__ import annotations

import math

import numpy as np


def _circ_inout(v):
    v = np.array(v)
    out = np.empty_like(v)
    mask = v < 0.5
    out[mask] = -0.5 * (np.sqrt(1 - 4 * v[mask] ** 2) - 1)
    mask = ~mask
    out[mask] = np.sqrt(-(v[mask] - 1.5) * (v[mask] - 0.5)) + 0.5
    return out


EASING_FUNCTIONS = {
    "linear": lambda v, a: v,
    "quad_in": lambda v, a: v * v,
    "quad_out": lambda v, a: -v * (v - 2),
    "quad_inout": lambda v, a: np.where(v < 0.5, 2 * v * v, -2 * v * (v - 2) - 1),
    "cubic_in": lambda v, a: v * v * v,
    "cubic_out": lambda v, a: (v - 1) ** 3 + 1,
    "cubic_inout": lambda v, a: np.where(v < 0.5, 4 * v * v * v, 4 * (v - 1) ** 3 + 1),
    "power_in": lambda v, a: v**a,
    "power_out": lambda v, a: 1 - (1 - v) ** a,
    "power_inout": lambda v, a: np.where(
        v < 0.5, (2 * v) ** a / 2, 1.0 - 0.5 * (2 - 2 * v) ** a
    ),
    "sin_in": lambda v, a: 1.0 - np.cos(v * math.pi / 2),
    "sin_out": lambda v, a: np.sin(v * math.pi / 2),
    "sin_inout": lambda v, a: 0.5 * (1 - np.cos(v * math.pi)),
    "exp_in": lambda v, a: 2 ** (a * (v - 1)),
    "exp_out": lambda v, a: 1 - 2 ** (-a * v),
    "exp_inout": lambda v, a: np.where(
        v < 0.5,
        (2 ** (a * (2 * v - 1))) / 2,
        1 - 2 ** (a * (1 - 2 * v) - 1),
    ),
    "circ_in": lambda v, a: -(np.sqrt(1 - v * v) - 1),
    "circ_out": lambda v, a: np.sqrt(-v * (v - 2)),
    "circ_inout": lambda v, a: _circ_inout(v),
}
