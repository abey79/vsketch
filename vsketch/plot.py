from typing import List, Optional, Tuple, Union

import matplotlib
import matplotlib.pyplot as plt
import numpy as np
import vpype as vp

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


def plot_vector_data(
    vector_data: Union[vp.LineCollection, vp.VectorData],
    page_format: Optional[Tuple[float, float]] = None,
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

    try:
        # noinspection PyUnresolvedReferences
        import mpld3

        mpld3.display()
    except ModuleNotFoundError:
        plt.show()
