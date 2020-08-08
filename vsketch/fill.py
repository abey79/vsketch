import math

import numpy as np
import vpype as vp
from shapely.geometry import MultiLineString, Polygon


def complex_to_2d(line: np.ndarray) -> np.ndarray:
    return np.vstack([line.real, line.imag]).T


def generate_fill(line: np.ndarray, pen_width: float) -> vp.LineCollection:
    poly = Polygon(complex_to_2d(line))

    # we draw the boundary, accounting for pen width
    p = poly.buffer(-pen_width / 2, join_style=2, mitre_limit=10.0)

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
