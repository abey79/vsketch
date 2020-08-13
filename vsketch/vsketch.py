import math
import shlex
from typing import Any, Dict, Iterable, Optional, Sequence, TextIO, Union, cast

import numpy as np
import vpype as vp
import vpype_cli
from shapely.geometry import Polygon

from .fill import generate_fill
from .plot import plot_vector_data
from .utils import MatrixPopper, complex_to_2d

__all__ = ["Vsketch"]


# noinspection PyPep8Naming
class Vsketch:
    def __init__(self):
        self._vector_data = vp.VectorData()
        self._cur_stroke: Optional[int] = 1
        self._cur_fill: Optional[int] = None
        self._pipeline = ""
        self._figure = None
        self._transform_stack = [np.empty(shape=(3, 3), dtype=float)]
        self._page_format = vp.convert_page_format("a3")
        self._center_on_page = True
        self._detail = vp.convert_length("0.1mm")
        self._pen_width: Dict[int, float] = {}
        self._default_pen_width = vp.convert_length("0.3mm")
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
    def width(self) -> float:
        """Get the page width in CSS pixels.

        Returns:
            page width
        """
        return self._page_format[0]

    @property
    def height(self) -> float:
        """Get the page height in CSS pixels.

        Returns:
            page height
        """
        return self._page_format[1]

    @property
    def transform(self) -> np.ndarray:
        """Get the current transform matrix.

        Returns:
            the current 3x3 homogenous planar transform matrix
        """
        return self._transform_stack[-1]

    @transform.setter
    def transform(self, t: np.ndarray) -> None:
        """Set the current transform matrix.

        Args:
            t: a 3x3 homogenous planar transform matrix
        """
        self._transform_stack[-1] = t

    @property
    def epsilon(self) -> float:
        """Returns the segment maximum length for curve approximation.

        The returned value takes into account the desired level of detail (see :func:`detail``
        as well as the scaling to be applied by the current transformation matrix.

        Returns:
            the maximum segment length to use
        """

        # The top 2x2 sub-matrix of the current transform corresponds to how the base vectors
        # would be transformed. We thus take their (transformed) length and use their maximum
        # value as scaling factor.
        scaling = max(math.hypot(*self.transform[0:2, 0]), math.hypot(*self.transform[0:2, 1]))

        return self._detail / scaling

    def detail(self, epsilon: Union[float, str]) -> None:
        """Define the level of detail for curved paths.

        Vsketch internally stores exclusively so called line strings, i.e. paths made of
        straight segments. Curved geometries (e.g. :func:`circle`) are approximated by many
        small segments. The level of detail controls the maximum size these segments may have.
        The default value is set to 0.1mm, with is good enough for most plotting needs.

        Examples::

            :func:`detail` accepts string values with unit::

                >>> vsk = Vsketch()
                >>> vsk.detail("1mm")

            A float input is interpretted as CSS pixels::

                >>> vsk.detail(1.)

        Args:
            epsilon: maximum length of segments approximating curved elements (may be a string
                value with units -- float value are interpreted as CSS pixels
        """
        self._detail = vp.convert_length(epsilon)

    def size(
        self,
        width: Union[float, str],
        height: Optional[Union[float, str]] = None,
        landscape: bool = False,
        center: bool = True,
    ) -> None:
        """Define the page layout.

        If floats are for width and height, they are interpreted as CSS pixel (same as SVG).
        Alternatively, strings can be passed and may contain units. The string form accepts
        both two parameters, or a single, vpype-like page format specifier.

        Page format specifier can either be a known page format (see ``vpype write --help`` for
        a list) or a string in the form of `WxH`, where both W and H may have units (e.g.
        `15inx10in`.

        By default, the sketch is always centered on the page. This can be disabled with
        ``center=False``. In this case, the sketch's absolute coordinates are used, with (0, 0)
        corresponding to the page's top-left corener and Y coordinates increasing downwards.

        The current page format (in CSS pixels) can be obtained with :py:attr:`width` and
        :py:attr:`height` properties.

        Examples:

            Known page format can be used directly::

                >>> vsk = Vsketch()
                >>> vsk.size("a4")

            Alternatively, the page size can be explicitely provided. All of the following
            calls are strictly equivalent::

                >>> vsk.size("15in", "10in")
                >>> vsk.size("10in", "15in", landscape=True)
                >>> vsk.size("15inx10in")
                >>> vsk.size("15in", 960.)  # 1in = 96 CSS pixels

        Args:
            width: page width or page forwat specifier if ``h`` is omitted
            height: page height
            landscape: rotate page format by 90 degrees if True
            center: if False, automatic centering is disabled
        """

        if height is None:
            width, height = vp.convert_page_format(width)
        else:
            width, height = vp.convert_length(width), vp.convert_length(height)

        if landscape:
            self._page_format = (height, width)
        else:
            self._page_format = (width, height)
        self._center_on_page = center

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

    def penWidth(self, width: Union[float, str], layer: Optional[int] = None) -> None:
        """Configure the pen width.

        For some feature, vsketch needs to know the width of your pen to for an optimal output.
        For example, the hatching pattern generated by :func:`fill` must be spaced by the right
        amount. The default pen width is set to 0.3mm.

        The default pen width can be set this way, and will be used for all layers unless a
        layer-specific pen width is provided::

            >>> vsk = Vsketch()
            >>> vsk.penWidth("0.5mm")

        A layer-specific pen width can be defined this way::

            >>> vsk.penWidth("1mm", 2)  # set pen width of layer 2 to 1mm

        If float is used as input, it is interpreted as CSS pixels.

        Args:
            width: pen width
            layer: if provided, ID of the layer for which the pen width must be set (otherwise
                the default pen width is changed)
        """
        w = vp.convert_length(width)
        if layer is not None:
            if layer < 1:
                raise ValueError("layer ID must be a strictly positive integer")
            self._pen_width[layer] = w
        else:
            self._default_pen_width = w

    @property
    def strokePenWidth(self) -> Optional[float]:
        """Returns the pen width to be used for stroke, or None in :func:`noStroke` mode.

        Returns:
            the current stroke pen width
        """
        if self._cur_stroke is not None:
            if self._cur_stroke in self._pen_width:
                return self._pen_width[self._cur_stroke]
            else:
                return self._default_pen_width
        return None

    @property
    def fillPenWidth(self) -> Optional[float]:
        """Returns the pen width to be used for fill, or None in :func:`noFill` mode.

        Returns:
            the current fill pen width
        """
        if self._cur_fill is not None:
            if self._cur_fill in self._pen_width:
                return self._pen_width[self._cur_fill]
            else:
                return self._default_pen_width
        return None

    def resetMatrix(self) -> None:
        """Reset the current transformation matrix."""
        self.transform = np.identity(3)

    def pushMatrix(self) -> MatrixPopper:
        """Push the current transformation matrix onto the matrix stack.

        Each call to :func:`pushMatrix` should be matched by exactly one call to
        :func:`popMatrix` to maintain consistency. Alternatively, the context manager
        returned by :func:`pushMatrix` can be used to automatically call :func:`popMatrix`

        Examples:

            Using matching :func:`popMatrix`::

                >>> vsk = Vsketch()
                >>> for _ in range(5):
                ...    vsk.pushMatrix()
                ...    vsk.rotate(_*5, degrees=True)
                ...    vsk.rect(-2, -2, 2, 2)
                ...    vsk.popMatrix()
                ...    vsk.translate(5, 0)
                ...

            Using context manager::

                >>> for _ in range(5):
                ...    with vsk.pushMatrix():
                ...        vsk.rotate(_*5, degrees=True)
                ...        vsk.rect(-2, -2, 2, 2)
                ...    vsk.translate(5, 0)
                ...

        Returns:
            context manager object: a context manager object for use with a ``with`` statement
        """
        self._transform_stack.append(self.transform.copy())

        return MatrixPopper(self)

    def popMatrix(self) -> None:
        """Pop the current transformation matrix from the matrix stack."""
        if len(self._transform_stack) == 1:
            raise RuntimeError("popMatrix() was called more times than pushMatrix()")

        self._transform_stack.pop()

    def printMatrix(self) -> None:
        """Print the current transformation matrix."""
        print(self.transform)

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

        self.transform = self.transform @ np.diag([sx, sy, 1])

    def rotate(self, angle: float, degrees=False) -> None:
        """Apply a rotation to the current transformation matrix.

        The coordinates are always rotated around their relative position to the origin.
        Positive numbers rotate objects in a clockwise direction and negative numbers rotate in
        the counter-clockwise direction.

        Args:
            angle: the angle of the rotation in radian (or degrees if ``degrees=True``)
            degrees: if True, the input is interpreted as degree instead of radians
        """

        if degrees:
            angle = angle * np.pi / 180.0

        self.transform = self.transform @ np.array(
            [
                (np.cos(angle), -np.sin(angle), 0),
                (np.sin(angle), np.cos(angle), 0),
                (0, 0, 1),
            ],
            dtype=float,
        )

    def translate(self, dx: float, dy: float) -> None:
        """Apply a translation to the current transformation matrix.

        Args:
            dx: translation along X axis
            dy: translation along Y axis
        """

        self.transform = self.transform @ np.array(
            [(1, 0, dx), (0, 1, dy), (0, 0, 1)], dtype=float
        )

    def line(self, x1: float, y1: float, x2: float, y2: float) -> None:
        """Draw a line.

        Args:
            x1: X coordinate of starting point
            y1: Y coordinate of starting point
            x2: X coordinate of ending point
            y2: Y coordinate of ending point
        """

        # TODO: handle transformation
        self._add_polygon(np.array([x1 + y1 * 1j, x2 + y2 * 1j], dtype=complex))

    def circle(
        self,
        x: float,
        y: float,
        diameter: Optional[float] = None,
        radius: Optional[float] = None,
    ) -> None:
        """Draw a circle.

        The level of detail used to approximate the circle is controlled by :func:`detail`.

        Example:

            >>> vsk = Vsketch()
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

        line = vp.circle(x, y, radius, self.epsilon)
        self._add_polygon(line)

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
        mode: Optional[str] = "corner",
    ) -> None:
        """Draw a rectangle.

        Examples:
            >>> vsk = Vsketch()
            >>> vsk.rect(0, 0, 2, 4)  # Default mode is 'corner'
            >>> vsk.rect(3, 3, 2.5, 1, mode="radius")

        Args:
            x: x coordinate of the top-left corner
            y: y coordinate of the top-left corner
            w: width
            h: height (same as width if not provided)
            tl: top-left corner radius (0 if not provided)
            tr: top-right corner radius (same as tl if not provided)
            br: bottom-right corner radius (same as tr if not provided)
            bl: bottom-left corner radius (same as br if not provided)
            mode: One of "corner", "corners", "center", "radius" (default: "corner")
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

        if mode == "corner":
            line = vp.rect(x, y, w, h)
        elif mode == "corners":
            #  Find top-left corner
            tl_x, tl_y = min(x, w), min(y, h)
            width, height = max(x, w) - tl_x, max(y, h) - tl_y
            line = vp.rect(tl_x, tl_y, width, height)
        elif mode == "center":
            line = vp.rect(x - w / 2, y - h / 2, w, h)
        elif mode == "radius":
            line = vp.rect(x - w, y - h, 2 * w, 2 * h)
        else:
            raise ValueError("mode must be one of 'corner', 'corners', 'center', 'radius'")

        # TODO: handle round corners

        self._add_polygon(line)

    def square(self, x: float, y: float, extent: float) -> None:
        """Draw a square.

        Example:

            >>> vsk = Vsketch()
            >>> vsk.square(2, 2, 2.5)
        
        Args:
            x: X coordinate of top-left corner
            y: Y coordinate of top-left corner
            extent: width and height of the square
        """

        line = vp.rect(x, y, extent, extent)

        self._add_polygon(line)

    def quad(
        self,
        x1: float,
        y1: float,
        x2: float,
        y2: float,
        x3: float,
        y3: float,
        x4: float,
        y4: float,
    ) -> None:
        """Draw a quadrilateral.

        Example:

            >>> vsk = Vsketch()
            >>> vsk.quad(0, 0, 1, 3.5, 4.5, 4.5, 3.5, 1)
        
        Args:
            x1: X coordinate of the first vertex
            y1: Y coordinate of the first vertex
            x2: X coordinate of the second vertex
            y2: Y coordinate of the second vertex
            x3: X coordinate of the third vertex
            y3: Y coordinate of the third vertex
            x4: X coordinate of the last vertex
            y4: Y coordinate of the last vertex
        """
        line = np.array(
            [x1 + y1 * 1j, x2 + y2 * 1j, x3 + y3 * 1j, x4 + y4 * 1j, x1 + y1 * 1j],
            dtype=complex,
        )
        self._add_polygon(line)

    def triangle(
        self, x1: float, y1: float, x2: float, y2: float, x3: float, y3: float
    ) -> None:
        """Draw a triangle.

        Example:

            >>> vsk = Vsketch()
            >>> vsk.triangle(2, 2, 2, 3, 3, 2.5)

        Args:
            x1: X coordinate of the first corner
            y1: Y coordinate of the first corner
            x2: X coordinate of the second corner
            y2: Y coordinate of the second corner
            x3: X coordinate of the third corner
            y3: Y coordinate of the third corner
        """

        line = np.array(
            [x1 + y1 * 1j, x2 + y2 * 1j, x3 + y3 * 1j, x1 + y1 * 1j], dtype=complex
        )
        self._add_polygon(line)

    def polygon(
        self,
        x: Union[Iterable[float], Iterable[Sequence[float]]],
        y: Optional[Iterable[float]] = None,
        holes: Iterable[Iterable[Sequence[float]]] = (),
        close: bool = False,
    ):
        """Draw a polygon.

        Examples:

            A single iterable of size-2 sequence can be used::

                >>> vsk = Vsketch()
                >>> vsk.polygon([(0, 0), (2, 3), (3, 2)])

            Alternatively, two iterables of float can be passed::

                >>> vsk.polygon([0, 2, 3], [0, 3, 2])

            The polygon can be automatically closed if needed::

                >>> vsk.polygon([0, 2, 3], [0, 3, 2], close=True)

            Finally, polygons can have holes, which is useful when using :func:`fill`::

                >>> vsk.polygon([0, 1, 1, 0], [0, 0, 1, 1],
                ...             holes=[[(0.3, 0.3), (0.3, 0.6), (0.6, 0.6)]])

        Args:
            x: X coordinates or iterable of size-2 points (if ``y`` is omitted)
            y: Y coordinates
            holes: list of holes inside the polygon
            close: the polygon is closed if True
        """
        if y is None:
            try:
                # noinspection PyTypeChecker
                line = np.array(
                    [complex(c[0], c[1]) for c in cast(Iterable[Sequence[float]], x)],
                    dtype=complex,
                )
            except:
                raise ValueError(
                    "when Y is not provided, X must contain an iterable of size 2+ sequences"
                )
        else:
            try:
                line = np.array(
                    [complex(c[0], c[1]) for c in zip(x, y)], dtype=complex  # type: ignore
                )
            except:
                raise ValueError(
                    "when both X and Y are provided, they must be sequences o float"
                )

        hole_lines = []
        try:
            for hole in holes:
                hole_lines.append(np.array([complex(c[0], c[1]) for c in hole], dtype=complex))
        except:
            raise ValueError("holes must be a sequence of sequence of 2D coordinates")

        if close and line[-1] != line[0]:
            line = np.hstack([line, line[0]])

        self._add_polygon(line, holes=hole_lines)

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
                    self.polygon(
                        p.exterior.coords, holes=[hole.coords for hole in p.interiors]
                    )
            else:
                raise ValueError("unsupported Shapely geometry")
        except AttributeError:
            raise ValueError("the input must be a supported Shapely geometry")

    def sketch(self, sub_sketch: "Vsketch") -> None:
        """Draw the content of another Vsketch.

        Vsketch objects being self-contained, multiple instances can be created by a single
        program, for example to create complex shapes in a sub-sketch to be used multiple times
        in the main sketch. This function can be used to draw in a sketch the content of
        another sketch.

        The styling options (stroke layer, fill layer, pen width, etc.) must be defined in the
        sub-sketch and are preserved by :func:`sketch`. Layers IDs are preserved and will be
        created if needed.

        The current transformation matrix is applied on the sub-sketch before inclusion in the
        main sketch.

        Args:
            sub_sketch: sketch to draw in the current sketch
        """

        # invalidate the cache
        self._processed_vector_data = None

        for layer_id, layer in sub_sketch._vector_data.layers.items():
            lc = vp.LineCollection([self._transform_line(line) for line in layer])
            self._vector_data.add(lc, layer_id)

    def _transform_line(self, line: np.ndarray) -> np.ndarray:
        """Apply the current transformation matrix to a line."""

        transformed_line = self.transform @ np.vstack(
            [line.real, line.imag, np.ones(len(line))]
        ).T.reshape(len(line), 3, 1)
        return transformed_line[:, 0, 0] + 1j * transformed_line[:, 1, 0]

    def _add_polygon(self, exterior: np.ndarray, holes: Iterable[np.ndarray] = ()) -> None:
        """Add a polygon with optional holes to the sketch.

        If the exterior is nos closed, this will be reflected by its stroke. Its fill will
        behave as if the polygon was closed.

        Args:
            exterior (numpy array of complex): polygon external boundary
            holes (iterable of numpy array of complex): interior holes
        """
        # invalidate the cache
        self._processed_vector_data = None

        transformed_exterior = self._transform_line(exterior)
        transformed_holes = [self._transform_line(hole) for hole in holes]

        if self._cur_stroke:
            self._vector_data.add(
                vp.LineCollection(
                    [line for line in [transformed_exterior] + transformed_holes]
                ),
                self._cur_stroke,
            )

        if self._cur_fill:
            p = Polygon(
                complex_to_2d(transformed_exterior),
                holes=[complex_to_2d(hole) for hole in transformed_holes],
            )
            lc = generate_fill(p, cast(float, self.fillPenWidth))
            self._vector_data.add(lc, self._cur_fill)

    def pipeline(self, s: str) -> None:
        # invalidate the cache
        if s != self._pipeline:
            self._processed_vector_data = None

        self._pipeline = s

    def plot(
        self,
        page: bool = True,
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
            page: controls the page display
            axes: controls axis display
            grid: controls grid display
            pen_up: controls display of pen-up trajectories
            colorful: use a different color for each separate line
            unit: use a specific unit (``axes=True`` only)
        """
        plot_vector_data(
            self.processed_vector_data,
            page_format=self._page_format if page else None,
            center=self._center_on_page,
            show_axes=axes,
            show_grid=grid,
            show_pen_up=pen_up,
            colorful=colorful,
            unit=unit,
        )

    def save(self, file: Union[str, TextIO], layer_label: str = "%d",) -> None:
        """Save the current sketch to a SVG file.

        ``file`` may  either be a file path or a IO stream handle (such as the one returned
        by Python's ``open()`` built-in).

        This function uses the page layout as defined by :func:`size`.

        Args:
            file: destination SVG file (can be a file path or text-based IO stream)
            layer_label: define a template for layer naming (use %d for layer ID)
        """
        if isinstance(file, str):
            file = open(file, "w")

        vp.write_svg(
            file,
            self.processed_vector_data,
            self._page_format,
            self._center_on_page,
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
