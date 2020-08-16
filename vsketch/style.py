import numpy as np
import vpype as vp
from shapely.geometry import LineString


def _add_to_line_collection(geom, lc: vp.LineCollection) -> None:
    if hasattr(geom, "exterior"):
        lc.append(geom.exterior)
        lc.extend(geom.interiors)
    else:
        lc.append(geom)


def stylize_path(
    line: np.ndarray, weight: int, pen_width: float, detail: float
) -> vp.LineCollection:

    if weight == 1:
        return vp.LineCollection([line])

    lc = vp.LineCollection()

    # path to be used as starting point for buffering
    geom = LineString(vp.as_vector(line))
    if weight % 2 == 0:
        geom = geom.buffer(pen_width / 2)

    _add_to_line_collection(geom, lc)

    for _ in range((weight - 1) // 2):
        geom = geom.buffer(pen_width)
        _add_to_line_collection(geom, lc)

    return lc
