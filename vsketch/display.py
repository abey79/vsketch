import io
import logging
import sys
from typing import List, Optional, Tuple, Union

import matplotlib
import matplotlib.pyplot as plt
import numpy as np
import vpype as vp

from .environment import COLAB, get_svg_pan_zoom_url

try:
    # noinspection PyPackageRequirements
    import IPython
except ModuleNotFoundError:
    pass

COLORS = [
    (0, 0, 1),
    (0, 0.5, 0),
    (1, 0, 0),
    (0, 0.75, 0.75),
    (0, 1, 0),
    (0.75, 0, 0.75),
    (0.75, 0.75, 0),
    (0, 0, 0),
]


def display_matplotlib(
    vector_data: Union[vp.LineCollection, vp.VectorData],
    page_format: Tuple[float, float] = None,
    center: bool = False,
    show_axes: bool = True,
    show_grid: bool = False,
    show_pen_up: bool = False,
    colorful: bool = False,
    unit: str = "px",
) -> None:
    if isinstance(vector_data, vp.LineCollection):
        vector_data = vp.VectorData(vector_data)

    scale = 1 / vp.convert(unit)

    plt.cla()

    # draw page
    if page_format is not None:
        w = page_format[0] * scale
        h = page_format[1] * scale
        dw = 10 * scale
        plt.fill(
            np.array([w, w + dw, w + dw, dw, dw, w]),
            np.array([dw, dw, h + dw, h + dw, h, h]),
            "k",
            alpha=0.3,
        )
        plt.plot(
            np.array([0, 1, 1, 0, 0]) * w, np.array([0, 0, 1, 1, 0]) * h, "-k", lw=0.25,
        )

    # compute offset
    offset = complex(0, 0)
    if center and page_format:
        bounds = vector_data.bounds()
        if bounds is not None:
            offset = complex(
                (page_format[0] - (bounds[2] - bounds[0])) / 2.0 - bounds[0],
                (page_format[1] - (bounds[3] - bounds[1])) / 2.0 - bounds[1],
            )
    offset_ndarr = np.array([offset.real, offset.imag])

    # plot all layers
    color_idx = 0
    collections = {}
    for layer_id, lc in vector_data.layers.items():
        if colorful:
            color: Union[
                Tuple[float, float, float], List[Tuple[float, float, float]]
            ] = COLORS[color_idx:] + COLORS[:color_idx]
            color_idx += len(lc)
        else:
            color = COLORS[color_idx]
            color_idx += 1
        if color_idx >= len(COLORS):
            color_idx = color_idx % len(COLORS)

        # noinspection PyUnresolvedReferences
        layer_lines = matplotlib.collections.LineCollection(
            (vp.as_vector(line + offset) * scale for line in lc),
            color=color,
            lw=1,
            alpha=0.5,
            label=str(layer_id),
        )
        collections[layer_id] = [layer_lines]
        plt.gca().add_collection(layer_lines)

        if show_pen_up:
            # noinspection PyUnresolvedReferences
            pen_up_lines = matplotlib.collections.LineCollection(
                (
                    (
                        (vp.as_vector(lc[i])[-1] + offset_ndarr) * scale,
                        (vp.as_vector(lc[i + 1])[0] + offset_ndarr) * scale,
                    )
                    for i in range(len(lc) - 1)
                ),
                color=(0, 0, 0),
                lw=0.5,
                alpha=0.5,
            )
            collections[layer_id].append(pen_up_lines)
            plt.gca().add_collection(pen_up_lines)

    plt.gca().invert_yaxis()
    plt.axis("equal")
    plt.margins(0, 0)

    if show_axes or show_grid:
        plt.axis("on")
        plt.xlabel(f"[{unit}]")
        plt.ylabel(f"[{unit}]")
    else:
        plt.axis("off")
    if show_grid:
        plt.grid("on")

    plt.show()


def display_ipython(
    vector_data: Union[vp.LineCollection, vp.VectorData],
    page_format: Optional[Tuple[float, float]],
    center: bool = False,
    show_pen_up: bool = False,
    color_mode: str = "layer",
):
    """Implements a SVG previsualisation with pan/zoom support for IPython.

    If page_format is provided, a page is displayed and the sketch is laid out on it. Otherwise
    the sketch is displayed using its intrinsic boundaries.
    """
    if "IPython" not in sys.modules:
        raise RuntimeError("IPython display cannot be used outside of IPython")

    svg_io = io.StringIO()
    vp.write_svg(
        svg_io,
        vector_data,
        page_format if page_format is not None else (0, 0),
        center,
        show_pen_up=show_pen_up,
        color_mode=color_mode,
    )

    MARGIN = 10

    if page_format is None:
        bounds = vector_data.bounds()
        if bounds:
            svg_width = bounds[2] - bounds[0]
            svg_height = bounds[3] - bounds[1]
        else:
            svg_width = 0
            svg_height = 0
    else:
        svg_width = page_format[0]
        svg_height = page_format[1]

    page_boundaries = f"""
        <polygon points="{svg_width},{MARGIN}
            {svg_width + MARGIN},{MARGIN}
            {svg_width + MARGIN},{svg_height + MARGIN}
            {MARGIN},{svg_height + MARGIN}
            {MARGIN},{svg_height}
            {svg_width},{svg_height}"
            style="fill:black;stroke:none;opacity:0.3;" />
        <rect width="{svg_width}" height="{svg_height}"
            style="fill:none;stroke-width:1;stroke:rgb(0,0,0)" />
    """

    svg_margin = MARGIN if page_format is not None else 0

    IPython.display.display_html(
        f"""<div id="container" style="width: 80%; height: {svg_height}px;">
            <svg id="vsketch_svg" width="{svg_width + svg_margin}px"
                    height={svg_height + svg_margin}
                    viewBox="0 0 {svg_width + svg_margin} {svg_height + svg_margin}">
                {page_boundaries if page_format is not None else ""}
                {svg_io.getvalue()}
            </svg>
        </div>
        <script src="{get_svg_pan_zoom_url()}"></script>
        <script>
            svgPanZoom('#vsketch_svg', {{
                zoomEnabled: true,
                controlIconsEnabled: true,
                center: true,
                zoomScaleSensitivity: 0.3,
                contain: true,
            }});
          </script>
        """,
        raw=True,
    )


def display(
    vector_data: Union[vp.LineCollection, vp.VectorData],
    page_format: Optional[Tuple[float, float]],
    center: bool = False,
    show_axes: bool = True,
    show_grid: bool = False,
    show_pen_up: bool = False,
    color_mode: str = "layer",
    unit: str = "px",
    mode: Optional[str] = None,
) -> None:
    """Display a layout with vector data using the best method given the environment.

    Supported modes:

        "matplotlib": use matplotlib to render the preview
        "ipython": use SVG with zoom/pan capability (requires IPython)

    Note: all options are not necessarily implemented by all display modes.

    Args:
        vector_data: the vector data to display
        page_format: size of the page in pixels
        center: if True, the geometries are centered on the page
        show_axes: if True, display axes
        show_grid: if True, display a grid
        show_pen_up: if True, display pen-up trajectories
        color_mode: "none" (everything is black and white), "layer" (one color per layer), or
            "path" (one color per path)
        unit: display unit
        mode: if provided, force a specific display mode
    """

    if mode is None:
        if COLAB:
            mode = "ipython"
        else:
            mode = "matplotlib"

    if mode == "ipython":
        if show_axes:
            logging.warning("show_axis is not supported by IPython display mode")

        if show_grid:
            logging.warning("show_grid is not supported by IPython display mode")

        if unit != "px":
            logging.warning("custom units are not supported by IPython display mode")

        display_ipython(
            vector_data, page_format, center, show_pen_up=show_pen_up, color_mode=color_mode
        )
    elif mode == "matplotlib":
        display_matplotlib(
            vector_data,
            page_format,
            center=center,
            show_axes=show_axes,
            show_grid=show_grid,
            show_pen_up=show_pen_up,
            colorful=(color_mode == "path"),
            unit=unit,
        )
    else:
        raise ValueError(f"unsupported display mode: {mode}")
