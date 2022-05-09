from __future__ import annotations

import math
from typing import Any

import numpy as np
import vpype as vp
from shapely.geometry import JOIN_STYLE, LineString


def _add_to_line_collection(geom: Any, lc: vp.LineCollection) -> None:
    if hasattr(geom, "exterior"):
        lc.append(geom.exterior)
        lc.extend(geom.interiors)
    else:
        lc.append(geom)


def _calc_buffer_resolution(radius: float, detail: float) -> int:
    """Compute the ``resolution`` parameter of Shapely's ``buffer()`` based on the radius
    and desired detail.
    """
    return max(math.ceil(0.5 * math.pi * radius / detail) + 1, 3)


def stylize_path(
    line: np.ndarray, weight: int, pen_width: float, detail: float, join_style: str
) -> vp.LineCollection:
    """Implement a heavy stroke weight by buffering multiple times the base path.

    Note: recursive buffering is to be avoided to properly control detail!
    """

    if weight == 1:
        return vp.LineCollection([line])

    lc = vp.LineCollection()

    # convert vsketch str-based join style to the corresponding shapely value
    shapely_join_style = getattr(JOIN_STYLE, join_style)

    # path to be used as starting point for buffering
    geom = LineString(vp.as_vector(line))
    if weight % 2 == 0:
        radius = pen_width / 2
        _add_to_line_collection(
            geom.buffer(
                radius,
                resolution=_calc_buffer_resolution(radius, detail),
                join_style=shapely_join_style,
            ),
            lc,
        )
    else:
        radius = 0.0
        _add_to_line_collection(geom, lc)

    for i in range((weight - 1) // 2):
        radius += pen_width
        p = geom.buffer(
            radius,
            resolution=_calc_buffer_resolution(radius, detail),
            join_style=shapely_join_style,
        )
        _add_to_line_collection(p, lc)

    return lc
