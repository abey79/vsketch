from __future__ import annotations

import math

import numpy as np
import vpype as vp
from shapely.geometry import MultiLineString, Polygon

from .utils import complex_to_2d


def generate_fill(poly: Polygon, pen_width: float, stroke_width: float) -> vp.LineCollection:
    """Draw a fill pattern for the input polygon.

    The fill pattern should take into account the stroke width.

    Args:
        poly: polygon to fill
        pen_width: pen width on paper
        stroke_width: width of the stroke (accounting for stroke pen width and weight)

    Returns:
        fill paths
    """

    # we draw the boundary, accounting for pen width
    if stroke_width > 0:
        p = poly.buffer(-stroke_width / 2, join_style=2, mitre_limit=10.0)
    else:
        p = poly

    if p.is_empty:
        # too small, nothing to fill
        return vp.LineCollection()

    min_x, min_y, max_x, max_y = p.bounds
    height = max_y - min_y
    line_count = math.ceil(height / pen_width) + 1
    base_seg = np.array([min_x, max_x])
    y_start = min_y + (height - (line_count - 1) * pen_width) / 2

    segs = []
    for n in range(line_count):
        seg = base_seg + (y_start + pen_width * n) * 1j
        segs.append(seg if n % 2 == 0 else np.flip(seg))

    # mls = MultiLineString([[(pt.real, pt.imag) for pt in seg] for seg in segs]).intersection(
    mls = MultiLineString([complex_to_2d(seg) for seg in segs]).intersection(
        p.buffer(-pen_width / 2, join_style=2, mitre_limit=10.0)
    )

    lc = vp.LineCollection(mls)
    lc.merge(tolerance=pen_width * 5, flip=True)

    boundary = p.boundary
    if boundary.geom_type == "MultiLineString":
        lc.extend(boundary)
    else:
        lc.append(boundary)
    return lc
