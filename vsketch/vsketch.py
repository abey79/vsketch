import shlex
from typing import Any, Iterable, List, Optional, Sequence, TextIO, Tuple, Union, cast

import matplotlib
import matplotlib.pyplot as plt
import numpy as np
import vpype as vp
import vpype_cli

__all__ = ["Vsketch"]

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
    """Vsketch doc"""

    def __init__(self):
        self._vector_data = vp.VectorData()
        self._cur_stroke: Optional[int] = 1
        self._cur_fill: Optional[int] = None
        self._quantization = 0.1
        self._pipeline = ""
        self._figure = None
        self._transform = np.empty(shape=(3, 3), dtype=float)
        self.resetMatrix()

        # we cache the processed vector data to make sequence of plot() and write() faster
        # the cache must be invalidated (ie. _processed_vector_data set to None) each time
        # _vector_data or _pipeline changes
        self._processed_vector_data: Optional[vp.VectorData] = None

    @property
    def vector_data(self):
        return self._vector_data

    @property
    def processed_vector_data(self):
        if self._processed_vector_data is None:
            self._apply_pipeline()
        return self._processed_vector_data

    @property
    def transform(self) -> np.ndarray:
        """Get the current transform matrix.

        Returns:
            the current 3x3 homogenous planar transform matrix
        """
        return self._transform

    @transform.setter
    def transform(self, t: np.ndarray) -> None:
        """Set the current transform matrix.
        Args:
            t: a 3x3 homogenous planar transform matrix
        """
        self._transform = t

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

    def resetMatrix(self) -> None:
        """Reset the current transformation matrix."""
        self.transform = np.identity(3)

    def scale(self, sx: Union[float, str], sy: Optional[Union[float, str]] = None) -> None:
        """Apply a scale factor to the current transformation matrix.

        TODO: add examples

        Args:
            sx: scale factor along x axis (can be a string with units)
            sy: scale factor along y axis (can be a string with units) or None, in which case
                the same value as sx is used
        """

        if isinstance(sx, str):
            sx = vp.convert_length(sx)

        if sy is None:
            sy = sx
        elif isinstance(sy, str):
            sy = vp.convert_length(sy)

        self.transform = np.diag([float(sx), float(sy), 1]) @ self.transform

    def rotate(self, angle: float, degrees=True) -> None:
        """Apply a rotation to the current transformation matrix.

        The coordinates are always rotated around their relative position to the origin.
        Positive numbers rotate objects in a clockwise direction and negative numbers rotate in
        the couter-clockwise direction.

        Args:
            angle: the angle of the rotation in radian (or degrees if ``degrees=True``)
            degrees: if True, the input is interpreted as degree instead of radians
        """

        if degrees:
            angle = angle * np.pi / 180.0

        self.transform = (
            np.array(
                [
                    (np.cos(angle), np.sin(angle), 0),
                    (np.sin(angle), -np.cos(angle), 0),
                    (0, 0, 1),
                ],
                dtype=float,
            )
            @ self.transform
        )

    def translate(self, dx: float, dy: float) -> None:
        """Apply a translation to the current transformation matrix.

        Args:
            dx: translation along X axis
            dy: translation along Y axis
        """

        self.transform[0, 2] += float(dx)
        self.transform[1, 2] += float(dy)

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

    def triangle(
        self, x1: float, y1: float, x2: float, y2: float, x3: float, y3: float
    ) -> None:
        """Draw a triangle.

        Example:

            >>> import vsketch
            >>> vsk = vsketch.Vsketch()
            >>> vsk.triangle(2, 2, 2, 3, 3, 2.5)

        Args:
            x1: X coordinate of the first corner
            y1: Y coordinate of the first corner
            x2: X coordinate of the second corner
            y2: Y coordinate of the second corner
            x3: X coordinate of the third corner
            y3: Y coordinate of the third corner
        """
        line = np.array([x1 + y1 * 1j, x2 + y2 * 1j, x3 + y3 * 1j], dtype=complex)
        self._add_line(line)

    def polygon(
        self,
        x: Union[Iterable[float], Iterable[Sequence[float]]],
        y: Optional[Iterable[float]] = None,
        close: bool = False,
    ):
        """Draw a polygon.

        Examples:

            A single iterable of size-2 sequence can be used::

                >>> import vsketch
                >>> vsk = vsketch.Vsketch()
                >>> vsk.polygon([(0, 0), (2, 3), (3, 2)])

            Alternatively, two iterables of float can be passed::

                >>> vsk.polygon([0, 2, 3], [0, 3, 2])

            The polygon can be automatically closed if needed::

                >>> vsk.polygon([0, 2, 3], [0, 3, 2], close=True)

        Args:
            x: X coordinates or iterable of size-2 points (if ``y`` is omitted)
            y: Y coordinates
            close: the polygon is closed if True
        """
        if y is None:
            try:
                # noinspection PyTypeChecker
                line = np.array(
                    [complex(c[0], c[1]) for c in cast(Iterable[Sequence[float]], x)]
                )
            except:
                raise ValueError(
                    "when Y is not provided, X must contain an iterable of size 2+ sequences"
                )
        else:
            try:
                line = np.array([complex(c[0], c[1]) for c in zip(x, y)])  # type: ignore
            except:
                raise ValueError(
                    "when both X and Y are provided, they must be sequences o float"
                )

        if close:
            line = np.hstack([line, line[0]])

        self._add_line(line)

    def geometry(self, shape: Any) -> None:
        """Draw a Shapely geometry.

        This function should accept any of LineString, LinearRing, MultiPolygon,
        MultiLineString, or Polygon.

        Args:
            shape (Shapely geometry): a supported shapely geometry object
        """

        try:
            if shape.geom_type in ["LineString", "LinearRing"]:
                self.polygon(shape.coords)
            elif shape.geom_type == "MultiLineString":
                for ls in shape:
                    self.polygon(ls.coords)
            elif shape.geom_type in ["Polygon", "MultiPolygon"]:
                if shape.geom_type == "Polygon":
                    shape = [shape]
                for p in shape:
                    self.polygon(p.exterior.coords)
                    for hole in p.interiors:
                        self.polygon(hole.coords)
            else:
                raise ValueError("unsupported Shapely geometry")
        except AttributeError:
            raise ValueError("the input must be a supported Shapely geometry")

    def _add_line(self, line: np.ndarray) -> None:
        # invalidate the cache
        self._processed_vector_data = None

        # apply transformation
        transformed_line = self.transform @ np.vstack(
            [line.real, line.imag, np.ones(len(line))]
        ).T.reshape(len(line), 3, 1)
        line.real = transformed_line[:, 0, 0]
        line.imag = transformed_line[:, 1, 0]

        if self._cur_stroke:
            self._vector_data.add(vp.LineCollection([line]), self._cur_stroke)

        # TODO: handle fill

    def pipeline(self, s: str) -> None:
        # invalidate the cache
        if s != self._pipeline:
            self._processed_vector_data = None

        self._pipeline = s

    def plot(
        self,
        axes: bool = False,
        grid: bool = False,
        pen_up: bool = False,
        colorful: bool = False,
        unit: str = "px",
    ) -> None:
        """Plot the vsketch.

        TODO: explain arguments

        TODO: page boundaries should be displayed, probably requires a separate pageFormat()
            API.

        Args:
            axes: controls axis display
            grid: controls grid display
            pen_up: controls display of pen-up trajectories
            colorful: use a different color for each separate line
            unit: use a specific unit (``axes=True`` only)
        """
        _plot_vector_data(
            self.processed_vector_data,
            show_axes=axes,
            show_grid=grid,
            show_pen_up=pen_up,
            colorful=colorful,
            unit=unit,
        )

    def write(
        self,
        file: Union[str, TextIO],
        page_format: Union[str, Tuple[str, str]] = "a4",
        landscape: bool = False,
        center: bool = True,
        layer_label: str = "%d",
    ) -> None:
        """Write the current pipeline to a SVG file.

        TODO: probably should be renamed to save()

        Args:
            file: destination SVG file (can be a file path or text-based IO stream)
            page_format: file format (can be a string with standard format or a tuple of string
                with sizes, eg. ("15in", "10in").
            landscape: if True, rotate the page format by 90 degrees
            center: centers the geometries on the page (default True)
            layer_label: define a template for layer naming (use %d for layer ID)
        """
        if isinstance(file, str):
            file = open(file, "w")

        w, h = vp.convert_page_format(page_format)
        if landscape:
            w, h = h, w

        vp.write_svg(
            file,
            self.processed_vector_data,
            (w, h),
            center,
            layer_label_format=layer_label,
            source_string="Generated with vsketch",
        )

    def _apply_pipeline(self):
        """Apply the current pipeline on the current vector data."""

        @vpype_cli.cli.command(group="vsketch")
        @vp.global_processor
        def vsketchinput(vector_data):
            vector_data.extend(self._vector_data)
            return vector_data

        @vpype_cli.cli.command(group="vsketch")
        @vp.global_processor
        def vsketchoutput(vector_data):
            self._processed_vector_data = vector_data
            return vector_data

        args = "vsketchinput " + self._pipeline + " vsketchoutput"
        vpype_cli.cli.main(prog_name="vpype", args=shlex.split(args), standalone_mode=False)
