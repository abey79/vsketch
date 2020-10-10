import math
import random
import shlex
from typing import Any, Dict, Iterable, Optional, Sequence, TextIO, Tuple, Union, cast

import noise
import numpy as np
import vpype as vp
import vpype_cli
from shapely.geometry import Polygon

from .curves import quadratic_bezier_path, quadratic_bezier_point, quadratic_bezier_tangent
from .display import display
from .fill import generate_fill
from .style import stylize_path
from .utils import MatrixPopper, complex_to_2d, compute_ellipse_mode

__all__ = ["Vsketch"]


# noinspection PyPep8Naming
class Vsketch:
    def __init__(self):
        self._vector_data = vp.VectorData()
        self._cur_stroke: Optional[int] = 1
        self._stroke_weight: int = 1
        self._cur_fill: Optional[int] = None
        self._pipeline = ""
        self._figure = None
        self._transform_stack = [np.empty(shape=(3, 3), dtype=float)]
        self._page_format = vp.convert_page_format("a3")
        self._center_on_page = True
        self._detail = vp.convert_length("0.1mm")
        self._pen_width: Dict[int, float] = {}
        self._default_pen_width = vp.convert_length("0.3mm")
        self._rect_mode = "corner"
        self._ellipse_mode = "center"
        self._noise_lod = 4
        self._random = random.Random()
        self._noise_falloff = 0.5
        # we use the global rng to guarantee unique seeds for noise
        self._noise_seed = random.uniform(0, 1)
        self._random.seed(random.randint(0, 2 ** 31))
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

        Note: :func:`detail` applies to all primitives, including e.g. :func:`bezier`. As such,
        it replaces some of Processing's API, such as ``bezierDetail()`` or ``curveDetail()``.

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

    def strokeWeight(self, weight: int) -> None:
        """Set the stroke weight.

        By default, stroke are plotted with a single line. Stroke can be made thicker by
        setting weight greater than 1 using this function. With stroke weight greater than 1,
        each stroke will be drawn with multiple lines, each spaced by the pen width defined
        for the current layer. The pen width must thus be properly set for good results.

        .. seealso::

            * :func:`stroke`
            * :func:`penWidth`

        Args:
            weight (strictly positive ``int``): number of plotted lines to use for strokes

        """

        if weight < 1:
            raise ValueError("width should be a strictly positive integer")
        self._stroke_weight = weight

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
    def strokePenWidth(self) -> float:
        """Returns the pen width to be used for stroke, or 0 in :func:`noStroke` mode.

        Returns:
            the current stroke pen width
        """
        if self._cur_stroke is not None:
            if self._cur_stroke in self._pen_width:
                return self._pen_width[self._cur_stroke]
            else:
                return self._default_pen_width
        return 0.0

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

    def rotate(self, angle: float, degrees: bool = False) -> None:
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
        mode: Optional[str] = None,
    ) -> None:
        """Draw a circle.

        The level of detail used to approximate the circle is controlled by :func:`detail`.
        As for the :meth:`ellipse` function, the way arguments are interpreted is influenced by
        the mode set with :meth:`ellipseMode` or the ``mode`` argument.

        .. seealso::

            * :meth:`ellipse`
            * :meth:`ellipseMode`

        Example:

            >>> vsk = Vsketch()
            >>> vsk.circle(0, 0, 10)  # by default, diameter is used
            >>> vsk.circle(0, 0, radius=5)  # radius can be specified instead

        Args:
            x: x coordinate of the center
            y: y coordinate of the center
            diameter: circle diameter (or None if using radius)
            radius: circle radius (or None if using diameter
            mode: one of 'center', 'radius', 'corner', 'corners'
        """

        if (diameter is None) == (radius is None):
            raise ValueError("either (but not both) diameter and radius must be provided")

        if radius is None:
            radius = cast(float, diameter) / 2

        if mode is None:
            mode = self._ellipse_mode

        if mode == "corners":
            mode = "corner"

        self.ellipse(x, y, 2 * radius, 2 * radius, mode=mode)

    def ellipse(
        self, x: float, y: float, w: float, h: float, mode: Optional[str] = None,
    ) -> None:
        """Draw an ellipse.

        The way ``x``, ``y``, ``w``, and ``h`` parameters are interpreted depends on the
        current ellipse mode.

        By default, ``x`` and ``y`` set the location of the  ellipse center, ``w`` sets its
        width, and ``h`` sets its height. The way these parameters are interpreted can be
        changed with the :meth:`ellipseMode` function (which changes the default for subsequent
        calls to :func:`ellipse`) or the ``mode`` argument (which only affects this call).

        Examples:

            By default, the argument are interpreted as the center coordinates as well as the
            width and height::

                >>> vsk = Vsketch()
                >>> vsk.ellipse(2, 2, 1, 4)

            Alternative ellipse mode can be set as the default for subsequence calls with
            :meth:`ellipseMode`::

                >>> vsk.ellipseMode(mode="radius")
                >>> vsk.ellipse(3, 3, 2, 1)
                >>> vsk.ellipse(8, 8, 2, 1)  # both of these call are in "radius" mode

            Or they can be set for a single call only::

                >>> vsk.ellipse(2, 2, 10, 12, mode="corners")

        Args:
            x: by default, x coordinate of the ellipse center
            y: by default, y coordinate of the ellipse center
            w: by default, the ellipse width
            h: by default, the ellipse height
            mode: "corner", "corners", "radius", or "center" (see :meth:`ellipseMode`)
        """
        if mode is None:
            mode = self._ellipse_mode
        line = vp.ellipse(*compute_ellipse_mode(mode, x, y, w, h), self.epsilon)
        self._add_polygon(line)

    def arc(
        self,
        x: float,
        y: float,
        w: float,
        h: float,
        start: float,
        stop: float,
        degrees: Optional[bool] = False,
        close: Optional[str] = "no",
        mode: Optional[str] = None,
    ) -> None:
        """Draw an arc.

        The way ``x``, ``y``, ``w``, and ``h`` parameters are interpreted depends on the
        current ellipse mode (see :meth:`ellipse` for a detailed explanation) and refer to the
        arc's underlying ellipse.

        The ``close`` parameter controls the arc's closure: ``no`` keeps it open,
        ``chord`` closes it with a straight line, and ``pie`` connects the two endings with the
        arc center.

        .. seealso::
            * :meth:`ellipseMode`
            * :meth:`ellipse`

        Example:
            >>> vsk = Vsketch()
            >>> vsk.arc(2, 3, 5, 4, 0, np.pi / 2)
            >>> vsk.arc(6, 6, 1, 2, np.pi / 2, np.pi, mode="corner", close="pie")

        Args:
            x: by default, X coordinate of the associated ellipse center
            y: by default, Y coordinate of the associated ellipse center
            w: by default, width of the associated ellipse
            h: by default, height of the associated ellipse
            start: angle to start the arc (in radians)
            stop: angle to stop the arc (in radians)
            degrees: set to True to use degrees for start and stop angles (default: False)
            close: "no", "chord" or "pie" (default: "no")
            mode: "corner", "corners", "radius", or "center" (see :meth:`ellipseMode`)
        """
        if not degrees:
            start = start * (180 / np.pi)
            stop = stop * (180 / np.pi)

        if mode is None:
            mode = self._ellipse_mode

        cx, cy, rw, rh = compute_ellipse_mode(mode, x, y, w, h)
        line = vp.arc(cx, cy, rw, rh, start, stop, self.epsilon)
        if close == "chord":
            line = np.append(line, [line[0]])
        elif close == "pie":
            line = np.append(line, [complex(cx, cy), line[0]])
        elif close != "no":
            raise ValueError("close must be one of 'no', 'chord', 'pie'")

        self._add_polygon(line)

    def ellipseMode(self, mode: str) -> None:
        """Change the way parameters are interpreted to draw ellipses.

        The default is "center", where the first two parameters are the center coordinates,
        and the third and fourth are the width and height of the ellipse.

        "radius" interprets the first two parameters as the center coordinates, while the
        third and fourth represent half the width and height of the ellipse.

        "corner" interprets the first two parameters as the top-left corner coordinates of
        the ellipse's bounding box, while the third and fourth parameters are the ellipse width
        and height.

        "corners" interprets the first two parameters as the coordinates of a corner of the
        ellipse's bounding box, and the third and fourth parameters as the opposite corner
        coordinates.

        .. seealso::
            * :meth:`ellipse`

        Example:
            >>> vsk = Vsketch()
            >>> vsk.ellipseMode("radius")
            >>> vsk.ellipse(2, 2, 3, 5)

        Args:
            mode: one of "center", "radius", "corner", "corners".
        """
        if mode in ["center", "radius", "corner", "corners"]:
            self._ellipse_mode = mode
        else:
            raise ValueError("mode must be one of 'center', 'radius', 'corner', 'corners'")

    def point(self, x: float, y: float) -> None:
        """Draw a point.

        For best plotting results, a tiny circle is actually drawn with diameter set to the
        current layer's pen width.

        Example::

            >>> vsk = Vsketch()
            >>> vsk.point(2, 3.5)

        Args:
            x: X coordinate
            y: Y coordinate
        """
        self.circle(x, y, self.strokePenWidth)

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
        mode: Optional[str] = None,
    ) -> None:
        """Draw a rectangle.

        The way ``x``, ``y``, ``w``, and ``h`` parameters are interpreted depends on the
        current rect

        By default, ``x`` and ``y`` set the location of the upper-left corner, ``w`` sets the
        width, and ``h`` sets the height. The way these parameters are interpreted can be
        changed with the :meth:`rectMode` function (which changes the default for subsequent
        calls to :func:`rect`) or the ``mode`` argument (which only affects this call).

        Note: rounded corners are not yet implemented.

        Examples:

            By default, the argument are interpreted as the top left corner as well as the
            width and height::

                >>> vsk = Vsketch()
                >>> vsk.rect(0, 0, 2, 4)  # 2x4 rectangle with top-left corner at (0, 0)

            Alternative rect mode can be set as the default for subsequence calls with
            :meth:`rectMode`::

                >>> vsk.rectMode(mode="radius")
                >>> vsk.rect(3, 3, 2, 1)
                >>> vsk.rect(8, 8, 2, 1)  # both of these call are in "radius" mode

            Or they can be set for a single call only:

                >>> vsk.rect(2, 2, 10, 12, mode="corners")

        Args:
            x: by default, x coordinate of the top-left corner
            y: by default, y coordinate of the top-left corner
            w: by default, the rectangle width
            h: by default, the rectangle height (same as width if not provided)
            tl: top-left corner radius (0 if not provided)
            tr: top-right corner radius (same as tl if not provided)
            br: bottom-right corner radius (same as tr if not provided)
            bl: bottom-left corner radius (same as br if not provided)
            mode: "corner", "corners", "redius", or "center" (see :meth:`rectMode`)
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

        if mode is None:
            mode = self._rect_mode

        if mode == "corner":
            line = vp.rect(x, y, w, h)
        elif mode == "corners":
            #  Find top-left corner
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

    def square(self, x: float, y: float, extent: float, mode: Optional[str] = None) -> None:
        """Draw a square.

        As for the :meth:`rect` function, the way arguments are interpreted is influenced by
        the mode set with :meth:`rectMode` or the ``mode`` argument.

        .. seealso::

            * :meth:`rect`
            * :meth:`rectMode`

        Example:

            >>> vsk = Vsketch()
            >>> vsk.square(2, 2, 2.5)

        Args:
            x: X coordinate of top-left corner
            y: Y coordinate of top-left corner
            extent: width and height of the square
            mode: "corner", "redius", or "center" (see :meth:`rectMode`) — note that the
                "corners" mode is meaningless for this function, and is interpreted as the
                "corner" mode
        """
        if mode == "corners" or (mode is None and self._rect_mode == "corners"):
            mode = "corner"
        self.rect(x, y, extent, extent, mode=mode)

    def rectMode(self, mode: str) -> None:
        """Change the way parameters are interpreted to draw rectangles.

        The default is "corner", where the first two parameters are the top-left corner
        coordinates, and the third and fourth are the width, respectively the height of the
        rectangle.

        In `rect()`, "corners" interprets the first two parameters as the coordinates of a
        corner, and the third and fourth parameters as the opposite corner coordinates.
        In `square()`, "corners" is interpreted as "corner".

        "center" interprets the first two parameters as the shape's center coordinates, and the
        third and fourth parameters as the shape's width and height.

        "radius" interprets the first two parameters as the shape's center coordinates, and the
        third and fourth parameters as half of the shape's width and height.

        .. seealso::

            * :meth:`rect`
            * :meth:`square`

        Example:

            >>> vsk = Vsketch()
            >>> vsk.rectMode("center")
            >>> vsk.square(3, 3, 1.5)
            >>> vsk.rect(2, 2, 3.5, 1)

        Args:
            mode: one of "corner", "corners", "center", "radius".
        """
        if mode in ["corner", "corners", "center", "radius"]:
            self._rect_mode = mode
        else:
            raise ValueError("mode must be one of 'corner', 'corners', 'center', 'radius'")

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
    ) -> None:
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
        if getattr(shape, "is_empty", False):
            return

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

    def bezier(
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
        """Draws a Bezier curve

        Bezier curves are defined by a series of anchor and control points. The first two
        arguments specify the first anchor point and the last two arguments specify the other
        anchor point. The middle arguments specify the control points which define the shape
        of the curve.

        .. seealso::

            * :func:`bezierPoint`
            * :func:`bezierTangent`
            * :func:`detail`

        Args:
            x1: X coordinate of the first anchor point
            y1: Y coordinate of the first anchor point
            x2: X coordinate of the first control point
            y2: Y coordinate of the first control point
            x3: X coordinate of the second control point
            y3: Y coordinate of the second control point
            x4: X coordinate of the second anchor point
            y4: Y coordinate of the second anchor point
        """

        path = quadratic_bezier_path(x1, y1, x2, y2, x3, y3, x4, y4, self.epsilon)
        self._add_polygon(path)

    # noinspection PyMethodMayBeStatic
    def bezierPoint(self, a: float, b: float, c: float, d: float, t: float) -> float:
        """Evaluates the Bezier at point ``t`` for points ``a``, ``b``, ``c``, ``d``. The
        parameter ``t`` varies between 0 and 1, ``a`` and ``d`` are points on the curve, and
        ``b`` and ``c`` are the control points. This can be done once with the X coordinates
        and a second time with the Y coordinates to get the location of a bezier curve at
        ``t``.

        .. seealso::

            :func:`bezier`

        Args:
            a: coordinate of the first point of the curve
            b: coordinate of the first control point
            c: coordinate of the second control point
            d: coordinate of the second point of the curve
            t: value between 0 and 1

        Returns:
            evaluated coordinate on the bezier curve
        """
        x, y = quadratic_bezier_point(a, 0, b, 0, c, 0, d, 0, t)
        return x

    # noinspection PyMethodMayBeStatic
    def bezierTangent(self, a: float, b: float, c: float, d: float, t: float) -> float:
        """Calculates the tangent of a point on a Bezier curve.

        .. seealso::

            * :func:`bezier`
            * :func:`bezierPoint`

        Args:
            a: coordinate of the first point of the curve
            b: coordinate of the first control point
            c: coordinate of the second control point
            d: coordinate of the second point of the curve
            t: value between 0 and 1

        Returns:
            evaluated tangent on the bezier curve
        """
        x, y = quadratic_bezier_tangent(a, 0, b, 0, c, 0, d, 0, t)
        return x

    def bezierDetail(self, epsilon: float) -> None:
        raise NotImplementedError(
            "bezierDetail() is not implemented, see detail() for more information"
        )

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
            lc = vp.LineCollection()
            for line in [transformed_exterior] + transformed_holes:
                lc.extend(
                    stylize_path(
                        line,
                        weight=self._stroke_weight,
                        pen_width=self.strokePenWidth,
                        detail=self._detail,
                    )
                )
            self._vector_data.add(lc, self._cur_stroke)

        if self._cur_fill:
            p = Polygon(
                complex_to_2d(transformed_exterior),
                holes=[complex_to_2d(hole) for hole in transformed_holes],
            )
            lc = generate_fill(
                p, cast(float, self.fillPenWidth), self._stroke_weight * self.strokePenWidth,
            )
            self._vector_data.add(lc, self._cur_fill)

    def vpype(self, pipeline: str) -> None:
        """Execute a vpype pipeline on the current sketch.

        Calling this function is equivalent to the following pseudo-command::

            $ vpype [load from sketch] pipeline [save to sketch]

        See `vpype's documentation <https://vpype.readthedocs.io/en/latest/>`_ for more
        information the commands available.

        Notes:

          - vpype is unaware of transforms. This means that any coordinates and length passed
            to vpype is interpreted as if no transform was applied. vpype does understand
            units though. If you used transforms to work in a different unit than CSS pixel
            (e.g. ``vsk.scale("1cm")``, then use the same unit with :func:`vpype` (e.g.
            ``vsk.vpype("crop 1cm 1cm 10cm 10cm")``.
          - vpype is unaware of the automatic centering mechanism built in :func:`size`,
            :func:`display` and :func:`save`. The pipeline is applied on the un-centered
            geometries. In some case, it may be useful to pass ``center=False`` to
            :func:`size` to avoid confusion.
          - It is not recommended to use layer manipulation commands (e.g. ``lmove``,
            ``ldelete``, and ``lcopy``) as this can lead to discrepancies with some of the
            metadata vsketch maintains, such as the attached pen widths (see :func:`penWidth`).

        Example:

            The most common use-case for this function is plot optimization::

                >>> import vsketch
                >>> vsk = vsketch.Vsketch()
                >>> # draw stuff...
                >>> vsk.vpype("linesimplify linemerge reloop linesort")
                >>> vsk.save("output.svg")

            This pipeline does the following:

                - :ref:`cmd_linesimplify`: Reduces the number of segment within all paths to
                  the minimum needed to ensure quality. This reduces SVG file size and avoid
                  performance issues while plotting.
                - :ref:`cmd_linemerge`: Merge lines whose ends are very close to avoid
                  unnecessary pen-up/pen-down sequences. By default, this command will consider
                  swapping the path direction for merging.
                - :ref:`cmd_reloop`: Randomize the location of the seam for closed paths. When
                  many similar paths are used on a plot (say, circles), having the seam at the
                  same location can lead to disturbing artefacts on the final plot, which this
                  command avoids.
                - :ref:`cmd_linesort`: Reorder the paths to minimize the pen-up travel
                  distance. By default, this command will consider swapping the path direction
                  for further optimization.

        Args:
            pipeline: vpype pipeline to apply to the sketch
        """

        @vpype_cli.cli.command(group="vsketch")
        @vp.global_processor
        def vsketchinput(vector_data):
            vector_data.extend(self._vector_data)
            return vector_data

        @vpype_cli.cli.command(group="vsketch")
        @vp.global_processor
        def vsketchoutput(vector_data):
            self._vector_data = vector_data
            return vector_data

        args = "vsketchinput " + pipeline + " vsketchoutput"
        vpype_cli.cli.main(prog_name="vpype", args=shlex.split(args), standalone_mode=False)

    def display(
        self,
        mode: Optional[str] = None,
        paper: bool = True,
        pen_up: bool = False,
        color_mode: str = "layer",
        axes: bool = False,
        grid: bool = False,
        unit: str = "px",
        fig_size: Optional[Tuple[float, float]] = None,
    ) -> None:
        """Display the sketch on screen.

        This function displays the sketch on screen using the most appropriate mode depending
        on the environment.

        In standalone mode (vsketch used as a library), ``"matplotlib"`` mode is used by
        default. Otherwise (i.e. in Jupyter Lab or Google Colab), ``"ipython"`` mode is used
        instead.

        The default options are the following:

            * The sketch is laid out on the desired page format, the boundary of which are
              displayed.
            * The path are colored layer by layer.
            * Pen-up trajectories are not displayed.
            * Advanced plotting options (axes, grid, custom units) are disabled.

        All of the above can be controlled using the optional arguments.

        Examples:

            In most case, the default behaviour is best::

                >>> vsk = Vsketch()
                >>> # draw stuff...
                >>> vsk.display()

            Sometimes, seeing the page boundaries and a laid out sketch is not useful::

                >>> vsk.display(paper=False)

            The ``"matplotlib"`` mode has additional options that can occasionaly be useful::

                >>> vsk.display(mode="matplotlib", axes=True, grid=True, unit="cm")

        Args:
            mode (``"matplotlib"`` or ``"ipython"``): override the default display mode
            paper: if True, the sketch is laid out on the desired page format (default: True)
            pen_up: if True, the pen-up trajectories will be displayed (default: False)
            color_mode (``"none"``, ``"layer"``, or ``"path"``): controls how color is used for
                display (``"none"``: black and white, ``"layer"``: one color per layer,
                ``"path"``: one color per path — default: ``"layer"``)
            axes: (``"matplotlib"`` only) if True, labelled axes are displayed (default: False)
            grid: (``"matplotlib"`` only) if True, a grid is displayed (default: False)
            unit: (``"matplotlib"`` only) use a specific unit for the axes (default: "px")
            fig_size: (``"matplotlib"`` only) specify the figure size
        """
        display(
            self.processed_vector_data,
            page_format=self._page_format if paper else None,
            mode=mode,
            center=self._center_on_page,
            show_axes=axes,
            show_grid=grid,
            show_pen_up=pen_up,
            color_mode=color_mode,
            unit=unit,
            fig_size=fig_size,
        )

    def save(
        self, file: Union[str, TextIO], color_mode: str = "layer", layer_label: str = "%d"
    ) -> None:
        """Save the current sketch to a SVG file.

        ``file`` may  either be a file path or a IO stream handle (such as the one returned
        by Python's ``open()`` built-in).

        This function uses the page layout as defined by :func:`size`.

        Args:
            file: destination SVG file (can be a file path or text-based IO stream)
            color_mode (``"none"``, ``"layer"``, or ``"path"``): controls how color is used for
                display (``"none"``: black and white, ``"layer"``: one color per layer,
                ``"path"``: one color per path — default: ``"layer"``)
            layer_label: define a template for layer naming (use %d for layer ID)
        """
        if isinstance(file, str):
            file = open(file, "w")

        vp.write_svg(
            file,
            self.processed_vector_data,
            self._page_format,
            self._center_on_page,
            color_mode=color_mode,
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

    ####################
    # RANDOM FUNCTIONS #
    ####################

    def random(self, a: float, b: Optional[float] = None) -> float:
        """Return a random number with an uniform distribution between specified bounds.

        .. seealso::

            * :func:`randomSeed`
            * :func:`noise`

        Examples:

            When using a single argument, it is used as higher bound and 0 is the lower
            bound::

                >>> vsk = Vsketch()
                >>> vsk.random(10)
                5.887767258845811

            When using both arguments, they are used as lower and higher bounds::

                >>> vsk.random(30, 40)
                37.12222388435382

        Args:
            a: if b is provided: low bound, otherwise: high bound
            b: high bound

        Returns:
            the random value
        """
        return self._random.uniform(0 if b is None else a, a if b is None else b)

    def randomGaussian(self) -> float:
        """Return a random number according to  a gaussian distribution with a mean of 0 and a
        standard deviation of 1.0.

        .. seealso::

            * :func:`random`
            * :func:`randomSeed`

        Returns:
            the random value
        """
        return self._random.gauss(0.0, 1.0)

    def randomSeed(self, seed: int) -> None:
        """Set the seed for :func:`random` and :func:`randomGaussian`.

        By default, :class:`Vsketch` instance are initialized with a random seed. By explicitly
        setting the seed, the sequence of number returned by :func:`random` and
        :func:`randomGaussian` will be reproduced predictably.

        Note that each :class:`Vsketch` instance has it's own random state and will not affect
        other instances.

        Args:
            seed: the seed to use
        """
        self._random.seed(seed)

    def noise(self, x: float, y: float = 0, z: float = 0) -> float:
        """Returns the Perlin noise value at specified coordinates.

        This function can compute 1D, 2D or 3D noise, depending on the number of coordinates
        given. See `Processing's description <https://processing.org/reference/noise_.html>`_
        of Perlin noise for background information.

        For a given :class:`Vsketch` instance, a coordinate tuple will always lead to the same
        pseudo-random value, unless another seed is set (:func:`noiseSeed`).

        .. seealso::

            * :func:`noiseSeed`
            * :func:`noiseDetail`

        Args:
            x: X coordinate in the noise space
            y: Y coordinate in the noise space (if provided)
            z: Z coordinate in the noise space (if provided)

        Returns:
            noise value between 0.0 and 1.0
        """

        # We use simplex noise instead of perlin noise because it can be computed for all
        # inputs (as opposed to [0, 1]) so it behaves in a way that is closer to Processing
        return (
            noise.snoise4(
                x,
                y,
                z,
                self._noise_seed,
                octaves=self._noise_lod,
                persistence=self._noise_falloff,
            )
            + 0.5
        )

    def noiseDetail(self, lod: int, falloff: Optional[float] = None) -> None:
        """Adjusts parameters of the Perlin noise function.

        By default, noise is computed over 4 octaves with each octave contributing exactly half
        of it s predecessors. This falloff as well as the number of octaves can be adjusted
        with this function

        .. seealso::

            * :func:`noise`
            * Processing
              `noiseDetail() doc <https://processing.org/reference/noiseDetail_.html>`_

        Args:
            lod: number of octaves to use
            falloff: ratio of amplitude of one octave with respect to the previous one
        """
        self._noise_lod = lod
        if falloff is not None:
            self._noise_falloff = falloff

    def noiseSeed(self, seed: int) -> None:
        """Set the random seed for :func:`noise`.

        .. seealso::

            :func:`noise`

        Args:
            seed: the seed
        """
        rng = random.Random()
        rng.seed(seed)
        self._noise_seed = rng.uniform(0, 100000)

    #######################
    # STATELESS UTILITIES #
    #######################

    @staticmethod
    def map(
        value: Union[float, np.ndarray],
        start1: float,
        stop1: float,
        start2: float,
        stop2: float,
    ) -> Union[float, np.ndarray]:
        """Re-map a value from one range to the other.

        Input values are not clamped. This function accept float or NumPy array, in which case
        it also returns a Numpy array.

        Examples::

            >>> vsk = Vsketch()
            >>> vsk.map(5, 0, 10, 40, 60)
            50
            >>> vsk.map(-1, 0, 1, 0, 30)
            -30
            >>> vsk.map(np.arange(5), 0, 5, 10, 30)
            array([10., 14., 18., 22., 26.])

        Args:
            value: value or array of value to re-map
            start1: low bound of the value's current range
            stop1: high bound of the value's current range
            start2: low bound of the target range
            stop2: high bound of the target range

        Returns:
            the re-maped value or array
        """

        return ((value - start1) * (stop2 - start2)) / (stop1 - start1) + start2
