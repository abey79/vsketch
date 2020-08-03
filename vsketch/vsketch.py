import shlex
from typing import List, Optional, Tuple, Union, cast

import matplotlib
import matplotlib.pyplot as plt
import numpy as np
import vpype as vp
import vpype_cli

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


# noinspection PyUnresolvedReferences
def _plot_vector_data(
    vector_data: Union[vp.LineCollection, vp.VectorData],
    show_axes: bool = True,
    show_grid: bool = False,
    show_pen_up: bool = False,
    colorful: bool = False,
    unit: str = "px",
):
    if isinstance(vector_data, vp.LineCollection):
        vector_data = vp.VectorData(vector_data)

    scale = 1 / vp.convert(unit)

    plt.cla()

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

        layer_lines = matplotlib.collections.LineCollection(
            (vp.as_vector(line) * scale for line in lc),
            color=color,
            lw=1,
            alpha=0.5,
            label=str(layer_id),
        )
        collections[layer_id] = [layer_lines]
        plt.gca().add_collection(layer_lines)

        if show_pen_up:
            pen_up_lines = matplotlib.collections.LineCollection(
                (
                    (vp.as_vector(lc[i])[-1] * scale, vp.as_vector(lc[i + 1])[0] * scale,)
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

    return vector_data


# noinspection PyPep8Naming
class Vsketch:
    def __init__(self):
        self._vector_data = vp.VectorData()
        self._cur_stroke: Optional[int] = 1
        self._cur_fill: Optional[int] = None
        self._quantization = 0.1
        self._pipeline = ""
        self._figure = None

    @property
    def vector_data(self):
        return self._vector_data

    def stroke(self, c: int) -> None:
        """Set the current stroke color.

        Args:
            c (strictly positive int): the color (e.g. layer) to use for path
        """
        if c < 1:
            raise ValueError("color layer must be strictly positive")

        self._cur_stroke = c

    def noStroke(self) -> None:
        """Disable stroke."""
        self._cur_stroke = None

    def fill(self, c: int) -> None:
        """Set the current fill color.
        Args:
            c (strictly positive int): the color (e.g. layer) to use for fill
        """
        if c < 1:
            raise ValueError("color layer must be strictly positive")

        self._cur_fill = c

    def noFill(self) -> None:
        """Disable fill."""
        self._cur_fill = None

    def line(self, x1: float, y1: float, x2: float, y2: float) -> None:
        """Draw a line.

        Args:
            x1: X coordinate of starting point
            y1: Y coordinate of starting point
            x2: X coordinate of ending point
            y2: Y coordinate of ending point
        """

        # TODO: handle transformation
        self._add_line(np.array([x1 + y1 * 1j, x2 + y2 * 1j], dtype=complex))

    def circle(
        self,
        x: float,
        y: float,
        diameter: Optional[float] = None,
        radius: Optional[float] = None,
    ) -> None:
        """Draw a circle.

        Example:

            >>> import vsketch
            >>> vsk = vsketch.Vsketch()
            >>> vsk.circle(0, 0, 10)  # by default, diameter is used
            >>> vsk.circle(0, 0, radius=5)  # radius can be specified instead

        Args:
            x: x coordinate of the center
            y: y coordinate of the center
            diameter: circle diameter (or None if using radius)
            radius: circle radius (or None if using diameter
        """

        if (diameter is None) == (radius is None):
            raise ValueError("either (but not both) diameter and radius must be provided")

        if radius is None:
            radius = cast(float, diameter) / 2

        line = vp.circle(x, y, radius, self._quantization)
        # TODO: handle transformation
        self._add_line(line)

    def rect(
        self,
        x: float,
        y: float,
        w: float,
        h: Optional[float] = None,
        tl: Optional[float] = 0,
        tr: Optional[float] = None,
        br: Optional[float] = None,
        bl: Optional[float] = None,
    ) -> None:
        """Draw a rectangle.

        TODO: implement rectMode()

        Args:
            x: x coordinate of the top-left corner
            y: y coordinate of the top-left corner
            w: width
            h: height (same as width if not provided)
            tl: top-left corner radius (0 if not provided)
            tr: top-right corner radius (same as tl if not provided)
            br: bottom-right corner radius (same as tr if not provided)
            bl: bottom-left corner radius (same as br if not provided)
        """
        if not h:
            h = w
        if not tl:
            tl = 0
        if not tr:
            tr = tl
        if not br:
            br = tr
        if not bl:
            bl = br

        if (tr + tl) > w or (br + bl) > w:
            raise ValueError("sum of corner radius cannot exceed width")
        if (tl + bl) > h or (tr + br) > h:
            raise ValueError("sum of corner radius cannot exceed height")

        line = vp.rect(x, y, w, h)
        # TODO: handle round corners

        self._add_line(line)

    def _add_line(self, line: np.ndarray) -> None:
        if self._cur_stroke:
            self._vector_data.add(vp.LineCollection([line]), self._cur_stroke)

        # TODO: handle fill

    def pipeline(self, s: str) -> None:
        self._pipeline = s

    def plot(self) -> None:
        @vpype_cli.cli.command(group="vsketch")
        @vp.global_processor
        def vsketchinput(vector_data):
            vector_data.extend(self._vector_data)
            return vector_data

        @vpype_cli.cli.command(group="vsketch")
        @vp.global_processor
        def vsketchplot(vector_data):
            _plot_vector_data(vector_data)
            return vector_data

        args = "vsketchinput " + self._pipeline + " vsketchplot"
        vpype_cli.cli.main(prog_name="vpype", args=shlex.split(args), standalone_mode=False)
