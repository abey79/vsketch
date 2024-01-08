from __future__ import annotations

import math
import os
import random
import shlex
from numbers import Real
from typing import Any, Iterable, Sequence, TextIO, TypeVar, cast, overload

import numpy as np
import vpype as vp
import vpype_cli
from pnoise import Noise
from shapely.geometry import Polygon

from .curves import cubic_bezier_path, cubic_bezier_point, cubic_bezier_tangent
from .display import display
from .easing import EASING_FUNCTIONS
from .fill import generate_fill
from .shape import Shape
from .style import stylize_path
from .utils import MatrixPopper, ResetMatrixContextManager, complex_to_2d, compute_ellipse_mode

__all__ = ["Vsketch"]


T = TypeVar("T")


# noinspection PyPep8Naming
class Vsketch:
    """Core drawing API.

    All drawing are created through an instance of :class:`Vsketch`.

    Typically, a :class:`Vsketch` instance is provided to your :class:`SketchClass` subclass by
    *vsketch*.

    Alternatively, :class:`Vsketch` instance may be manually created and used in a standalone
    script::

        >>> import vsketch
        >>> vsk = vsketch.Vsketch()
        >>> vsk.rect(10, 10, 50, 50)
        >>> vsk.display()
        >>> vsk.save("output.svg")
    """

    def __init__(self) -> None:
        self._document = vp.Document(page_size=vp.convert_page_size("a3"))
        self._cur_stroke: int | None = 1
        self._stroke_weight: int = 1
        self._join_style: str = "round"
        self._cur_fill: int | None = None
        self._figure = None
        self._transform_stack = [np.empty(shape=(3, 3), dtype=float)]
        self._center_on_page = True
        self._detail = vp.convert_length("0.1mm")
        self._pen_width: dict[int, float] = {}
        self._default_pen_width = vp.convert_length("0.3mm")
        self._rect_mode = "corner"
        self._ellipse_mode = "center"
        self._random = random.Random()
        self.random_seed = random.randint(0, 2**31)
        self._random.seed(self.random_seed)
        self._noise = Noise()
        self._text_mode = "transform"
        self.resetMatrix()

    @property
    def document(self):
        """Return the :class:`vpype.Document` instance containing the sketch's geometries."""
        return self._document

    @property
    def width(self) -> float:
        """Get the page width in CSS pixels.

        Returns:
            page width
        """
        return cast(float, self.document.page_size[0])

    @property
    def height(self) -> float:
        """Get the page height in CSS pixels.

        Returns:
            page height
        """
        return cast(float, self.document.page_size[1])

    @property
    def centered(self) -> bool:
        """Controls whether the sketch should be centered on page."""
        return self._center_on_page

    @centered.setter
    def centered(self, centered: bool) -> None:
        self._center_on_page = centered

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

    def detail(self, epsilon: float | str) -> None:
        """Define the level of detail for curved paths.

        Vsketch internally stores exclusively so called line strings, i.e. paths made of
        straight segments. Curved geometries (e.g. :func:`circle`) are approximated by many
        small segments. The level of detail controls the maximum size these segments may have.
        The default value is set to 0.1mm, with is good enough for most plotting needs.

        Note: :func:`detail` applies to all primitives, including e.g. :func:`bezier`. As such,
        it replaces some of Processing's API, such as ``bezierDetail()`` or ``curveDetail()``.

        Examples:

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
        width: float | str,
        height: float | str | None = None,
        landscape: bool = False,
        center: bool = True,
    ) -> None:
        """Define the page layout.

        If floats are for width and height, they are interpreted as CSS pixel (same as SVG).
        Alternatively, strings can be passed and may contain units. The string form accepts
        both two parameters, or a single, vpype-like page size specifier.

        Page size specifier can either be a known page size (see ``vpype write --help`` for
        a list) or a string in the form of `WxH`, where both W and H may have units (e.g.
        `15inx10in`.

        By default, the sketch is always centered on the page. This can be disabled with
        ``center=False``. In this case, the sketch's absolute coordinates are used, with (0, 0)
        corresponding to the page's top-left corner and Y coordinates increasing downwards.

        The current page size (in CSS pixels) can be obtained with :py:attr:`width` and
        :py:attr:`height` properties.

        Examples:

            Known page size can be used directly::

                >>> vsk = Vsketch()
                >>> vsk.size("a4")

            Alternatively, the page size can be explicitly provided. All of the following
            calls are strictly equivalent::

                >>> vsk.size("15in", "10in")
                >>> vsk.size("10in", "15in", landscape=True)
                >>> vsk.size("15inx10in")
                >>> vsk.size("15in", 960.)  # 1in = 96 CSS pixels

        Args:
            width: page width or page format specifier if ``h`` is omitted
            height: page height
            landscape: rotate page size by 90 degrees if True
            center: if False, automatic centering is disabled
        """

        if height is None:
            width, height = vp.convert_page_size(width)
        else:
            width, height = vp.convert_length(width), vp.convert_length(height)

        if landscape:
            self.document.page_size = (height, width)
        else:
            self.document.page_size = (width, height)
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

    def strokeJoin(self, join_style: str) -> None:
        """Set the style of the joints that connects line segments.

        Defines how joints between line segments are drawn when stroke weight is greater than
        1. The available styles are ``"round"`` (default), ``"mitre"``, and ``"bevel"``.

        .. seealso::

            * :func:`stroke`
            * :func:`strokeWeight`

        Args:
            join_style (``"round"``, ``"mitre"``, or ``"bevel"``): join style to use
        """

        if join_style not in ("round", "mitre", "bevel"):
            raise ValueError(
                f'incorrect join style "{join_style}", must be one of "round", "mitre", or '
                '"bevel"'
            )

        self._join_style = join_style

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

    def penWidth(self, width: float | str, layer: int | None = None) -> None:
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

    def getPenWidth(self, layer: int | None) -> float | None:
        """Get the pen width for a given layer.

        Args:
            layer: layer ID (or None for default pen width)

        Returns:
            the pen width (or `None` if not defined)
        """

        if layer is None:
            return self._default_pen_width

        return self._pen_width.get(layer, self._default_pen_width)

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
    def fillPenWidth(self) -> float | None:
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

    def resetMatrix(self) -> ResetMatrixContextManager:
        """Reset the current transformation matrix.

        It can also be used as a context manager. In this case, :func:`pushMatrix`
        and its associated :func:`popMatrix` will be called automatically.

        Examples:

            Using :func:`resetMatrix` as is::

                >>> vsk = Vsketch()
                >>> vsk.rotate(45)
                >>> vsk.scale(20, 3)
                >>> vsk.rect(0, 0, 4, 5)  # will be rotated and scaled
                >>> vsk.resetMatrix()
                >>> vsk.rect(0, 0, 2, 3)  # won't be rotated and scaled

            Using context manager::

                >>> vsk = Vsketch()
                >>> vsk.rotate(42)
                >>> with vsk.resetMatrix():
                ...     vsk.rect(5, 4, 20, 15)  # won't be rotated by 42° rotation
                >>> vsk.rect(2, 2, 10, 10)  # will be rotated by 42°

        .. seealso::

            * :func:`pushMatrix`

        Returns:
            context manager object: a context manager object for use with a ``with`` statement
        """
        return ResetMatrixContextManager(self)

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

    def scale(self, sx: float | str, sy: float | str | None = None) -> None:
        """Apply a scale factor to the current transformation matrix.

        Examples:

            Set sketch units to centimeters::

                >>> vsk = Vsketch()
                >>> vsk.scale("1cm")
                >>> vsk.square(5, 5, 2)  # square with 2cm-long sides

            Apply a non-homogeneous scale transformation::

                >>> vsk.scale(2, 3)

        Args:
            sx: scale factor along x axis (can be a string with units)
            sy: scale factor along y axis (can be a string with units) or None, in which case
                the same value as sx is used
        """

        if isinstance(sx, str):
            scale_x = vp.convert_length(sx)
        else:
            scale_x = float(sx)

        if sy is None:
            scale_y = scale_x
        elif isinstance(sy, str):
            scale_y = vp.convert_length(sy)
        else:
            scale_y = float(sy)

        self.transform = self.transform @ np.diag([scale_x, scale_y, 1])

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

        self._add_polygon(np.array([x1 + y1 * 1j, x2 + y2 * 1j], dtype=complex))

    def circle(
        self,
        x: float,
        y: float,
        diameter: float | None = None,
        radius: float | None = None,
        mode: str | None = None,
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

    def ellipse(self, x: float, y: float, w: float, h: float, mode: str | None = None) -> None:
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
        degrees: bool | None = False,
        close: str | None = "no",
        mode: str | None = None,
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
        if self._cur_stroke:
            center = self._transform_line(np.array([complex(x, y)]))
            circle = vp.circle(
                center[0].real, center[0].imag, self.strokePenWidth / 2, self.epsilon
            )
            lc = vp.LineCollection(
                stylize_path(
                    circle,
                    weight=self._stroke_weight,
                    pen_width=self.strokePenWidth,
                    detail=self._detail,
                    join_style="round",
                )
            )
            self._document.add(lc, self._cur_stroke)

    def rect(
        self,
        x: float,
        y: float,
        w: float,
        h: float,
        *radii: float,
        tl: float | None = None,
        tr: float | None = None,
        br: float | None = None,
        bl: float | None = None,
        mode: str | None = None,
    ) -> None:
        """Draw a rectangle.

        The way ``x``, ``y``, ``w``, and ``h`` parameters are interpreted depends on the
        current rect

        By default, ``x`` and ``y`` set the location of the upper-left corner, ``w`` sets the
        width, and ``h`` sets the height. The way these parameters are interpreted can be
        changed with the :meth:`rectMode` function (which changes the default for subsequent
        calls to :func:`rect`) or the ``mode`` argument (which only affects this call).

        The optional parameters ``tl``, ``tr``, ``br`` and ``bl`` define the radius used for
        each corner (default: 0). If some corner radius is not specified, it will be set equal
        to the previous corner radius. If the sum of two consecutive corner radii are greater
        than their associated edge lenght, their values will be rescaled to fit the rectangle.

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

            Drawing rectangles with rounded corners:

                >>> vsk.rect(0, 0, 5, 5, 5)  # all corners are rounded with a radius of 5
                >>> vsk.rect(0, 0, 4, 4, 1.5, 0.5, 1.5, 1)  # all corner radii specified
                >>> vsk.rect(5, 5, 20, 20, tr=3, bl=5)  # specified corners rounded, others
                                                        # default to 0

        Args:
            x: by default, x coordinate of the top-left corner
            y: by default, y coordinate of the top-left corner
            w: by default, the rectangle width
            h: by default, the rectangle height (same as width if not provided)
            tl: top-left corner radius (0 if not provided)
            tr: top-right corner radius (same as tl if not provided)
            br: bottom-right corner radius (same as tr if not provided)
            bl: bottom-left corner radius (same as br if not provided)
            mode: "corner", "corners", "radius", or "center" (see :meth:`rectMode`)
        """
        if len(radii) == 0:
            radii = (0, 0, 0, 0)
        elif len(radii) == 1:
            radii *= 4
        elif len(radii) != 4:
            raise ValueError(
                "only 1 or 4 corner radii may be implicitly specified, use keyword "
                "arguments instead"
            )
        if tl is None:
            tl = radii[0]
        if tr is None:
            tr = radii[1]
        if br is None:
            br = radii[2]
        if bl is None:
            bl = radii[3]

        if mode is None:
            mode = self._rect_mode

        if mode == "corner":
            line = vp.rect(x, y, w, h, tl, tr, br, bl, self.epsilon)
        elif mode == "corners":
            #  Find top-left corner
            tl_x, tl_y = min(x, w), min(y, h)
            width, height = max(x, w) - tl_x, max(y, h) - tl_y
            line = vp.rect(tl_x, tl_y, width, height, tl, tr, br, bl, self.epsilon)
        elif mode == "center":
            line = vp.rect(x - w / 2, y - h / 2, w, h, tl, tr, br, bl, self.epsilon)
        elif mode == "radius":
            line = vp.rect(x - w, y - h, 2 * w, 2 * h, tl, tr, br, bl, self.epsilon)
        else:
            raise ValueError("mode must be one of 'corner', 'corners', 'center', 'radius'")

        self._add_polygon(line)

    def square(self, x: float, y: float, extent: float, mode: str | None = None) -> None:
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
            mode: "corner", "radius", or "center" (see :meth:`rectMode`) — note that the
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
        x: Iterable[float] | Iterable[complex] | Iterable[Sequence[float]],
        y: Iterable[float] | None = None,
        holes: Iterable[Iterable[Sequence[float]]] = (),
        close: bool = False,
    ) -> None:
        """Draw a polygon.

        Examples:

            A single iterable of size-2 sequence can be used::

                >>> vsk = Vsketch()
                >>> vsk.polygon([(0, 0), (2, 3), (3, 2)])

            A 1-dimension iterable of complex can also be used::

                >>> vsk.polygon([3 + 3j, 2 + 5j, 4 + 7j])

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
                if hasattr(x, "__len__"):
                    data = np.array(x)
                else:
                    data = np.array(list(x))

                if len(data.shape) == 1 and data.dtype == complex:
                    line = data
                elif len(data.shape) == 2 and data.shape[1] == 2:
                    line = data[:, 0] + 1j * data[:, 1]
                else:
                    raise ValueError()
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

        This function should accept any of LineString, LinearRing, MultiPoint,
        MultiPolygon, MultiLineString, Point, or Polygon.

        Args:
            shape (Shapely geometry): a supported shapely geometry object
        """
        if getattr(shape, "is_empty", False):
            return

        try:
            if shape.geom_type == "GeometryCollection":
                for geom in shape.geoms:
                    self.geometry(geom)
            elif shape.geom_type in ["LineString", "LinearRing"]:
                self.polygon(shape.coords)
            elif shape.geom_type == "MultiLineString":
                for ls in shape.geoms:
                    self.polygon(ls.coords)
            elif shape.geom_type in ["Polygon", "MultiPolygon"]:
                if shape.geom_type == "Polygon":
                    geoms = [shape]
                else:
                    geoms = shape.geoms
                for p in geoms:
                    self.polygon(
                        p.exterior.coords, holes=[hole.coords for hole in p.interiors]
                    )
            elif shape.geom_type in ["Point", "MultiPoint"]:
                if shape.geom_type == "Point":
                    geoms = [shape]
                else:
                    geoms = shape.geoms
                for p in geoms:
                    self.point(p.x, p.y)
            else:
                raise ValueError(f"unsupported Shapely geometry: {shape.geom_type}")
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

        path = cubic_bezier_path(x1, y1, x2, y2, x3, y3, x4, y4, self.epsilon)
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
        x, y = cubic_bezier_point(a, 0, b, 0, c, 0, d, 0, t)
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
        x, y = cubic_bezier_tangent(a, 0, b, 0, c, 0, d, 0, t)
        return x

    def createShape(self) -> Shape:
        return Shape(self)

    def shape(
        self, shp: Shape, mask_lines: bool | None = None, mask_points: bool | None = None
    ) -> None:
        """Draw a shape.

        Draw a shape, including its area, lines, and points. If a :meth:`fill` layer is active,
        it is used for the area. Likewise, the current :meth:`penWidth` is used for points
        (see :meth:`points`).

        By default, the shape's lines and points are masked by the its area if a fill layer is
        active (such as to avoid unwanted interaction with the hatch fill), and left unmasked
        if not. This behaviour can be overridden using the ``mask_lines`` and ``mask_points``
        parameters.

        Args:
            shp: the shape to draw
            mask_lines: controls whether the shape's line are masked by its area (default:
                True if fill active, otherwise False)
            mask_points: controls whether the shape's points are masked by its area (default:
                True if fill active, otherwise False)
        """

        if mask_lines is None:
            mask_lines = self._cur_fill is not None
        if mask_points is None:
            mask_points = self._cur_fill is not None

        # noinspection PyProtectedMember
        area, lines, points = shp._compile(mask_lines, mask_points)

        self.geometry(area)
        self.geometry(lines)
        for point in points.geoms:
            self.point(point.x, point.y)

    def sketch(self, sub_sketch: Vsketch) -> None:
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

        for layer_id, layer in sub_sketch._document.layers.items():
            lc = vp.LineCollection([self._transform_line(line) for line in layer])
            self._document.add(lc, layer_id)

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
                        join_style=self._join_style,
                    )
                )
            self._document.add(lc, self._cur_stroke)

        if self._cur_fill and len(transformed_exterior) > 2:
            p = Polygon(
                complex_to_2d(transformed_exterior),
                holes=[complex_to_2d(hole) for hole in transformed_holes],
            )
            lc = generate_fill(
                p, cast(float, self.fillPenWidth), self._stroke_weight * self.strokePenWidth
            )
            self._document.add(lc, self._cur_fill)

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
          - It is not recommended to use layer manipulation commands (e.g. :ref:`cmd_lmove`,
            :ref:`cmd_ldelete`, and :ref:`cmd_lcopy`) as this can lead to discrepancies with
            some of the metadata vsketch maintains, such as the attached pen widths (see
            :func:`penWidth`).

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
        @vpype_cli.global_processor
        def vsketchinput(document):
            document.extend(self._document)
            return document

        @vpype_cli.cli.command(group="vsketch")
        @vpype_cli.global_processor
        def vsketchoutput(document):
            self._document = document
            return document

        args = "vsketchinput " + pipeline + " vsketchoutput"
        vpype_cli.cli.main(prog_name="vpype", args=shlex.split(args), standalone_mode=False)

    def display(
        self,
        paper: bool = True,
        pen_up: bool = False,
        colorful: bool = False,
        axes: bool = False,
        grid: bool = False,
        unit: str = "px",
        fig_size: tuple[float, float] | None = None,
    ) -> None:
        """Display the sketch on screen using matplotlib.

        The default options are the following:

            * The sketch is laid out on the desired page size, the boundary of which are
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

            Additional options may occasionaly be useful::

                >>> vsk.display(axes=True, grid=True, unit="cm")

        Args:
            paper: if True, the sketch is laid out on the desired page size (default: True)
            pen_up: if True, the pen-up trajectories will be displayed (default: False)
            colorful: if True, use one color per path instead of per layer (default: False)
            axes: if True, labelled axes are displayed (default: False)
            grid: if True, a grid is displayed (default: False)
            unit: use a specific unit for the axes (default: "px")
            fig_size: specify the figure size
        """
        display(
            self.document,
            page_size=self.document.page_size if paper else None,
            center=self._center_on_page,
            show_axes=axes,
            show_grid=grid,
            show_pen_up=pen_up,
            colorful=colorful,
            unit=unit,
            fig_size=fig_size,
        )

    # noinspection PyShadowingBuiltins
    def save(
        self,
        file: str | TextIO,
        device: str | None = None,
        *,
        format: str | None = None,
        color_mode: str = "layer",
        layer_label: str = "%d",
        paper_size: str | None = None,
        velocity: float | None = None,
        quiet: bool = False,
    ) -> None:
        """Save the current sketch to a SVG or HPGL file.

        ``file`` may  either be a file path or a IO stream handle (such as the one returned
        by Python's :func:`open` built-in).

        This function uses the page layout as defined by :func:`size`.

        Due to the nature of HPGL (which much be generated for a specific plotter device/paper
        size combination), the device name must always be specified. If ``paper_size`` is
        not provided, :meth:`save` attempts to infer which paper configuration to use based
        on the page size provided to :meth:`size`. If multiple configurations match the page
        size, the first one is used. In case of ambiguity, it is recommendande to specify
        ``paper_size``. See `vpype's documentation
        <https://vpype.readthedocs.io/en/latest/>`_ for more information on HPGL generation.

        Examples:

            Save the sketch to a SVG file::

                >>> vsk = Vsketch()
                >>> vsk.size("a4", landscape=True)
                >>> # draw stuff...
                >>> vsk.save("output.svg")

            Save to a SVG file with customization::

                >>> vsk.save("output.svg", color_mode="path", layer_label="layer %d")

            Save to a HPGL file::

                >>> vsk.save("output.hpgl", "hp7475a")

            Save to a HPGL file with customization::

                >>> vsk.save("output.hpgl", "hp7475a", paper_size="a4", veolocty=30)

        Args:
            file: destination SVG file (can be a file path or text-based IO stream)
            device: (HPGL only) target device for the HPGL output
            format (``"svg"``, ``"hpgl"``): specify the format of the output file (default is
                inferred from the file extension)
            color_mode (``"none"``, ``"layer"``, or ``"path"``): (SVG only) controls how color
                is used for display (``"none"``: black and white, ``"layer"``: one color per
                layer, ``"path"``: one color per path — default: ``"layer"``)
            layer_label: (SVG only) define a template for layer naming (use %d for layer ID)
            paper_size: (HPGL only) name of the paper size to use, as configured for the
                specified ``device`` (if omitted, the paper size will be inferred based on
                the page size specified with :meth:`size`)
            velocity: (HPGL only) if provided, a VS command will be emitted with the provided
                velocity
            quiet: (HPGL only) if set to True, silence plotter configuration and paper loading
                instructions
        """
        if format is None:
            _, ext = os.path.splitext(file.name if isinstance(file, TextIO) else file)
            format = ext.lstrip(".").lower()

        # inner function to accept only file-like object
        def write_to_file(file_object):
            nonlocal paper_size

            if format == "svg":
                vp.write_svg(
                    file_object,
                    self.document,
                    center=self._center_on_page,
                    color_mode=color_mode,
                    layer_label_format=layer_label,
                    source_string="Generated with vsketch",
                    use_svg_metadata=True,
                )
            elif format == "hpgl":
                if device is None:
                    raise ValueError(f"'device' must be provided")
                if paper_size is None:
                    config = vp.config_manager.get_plotter_config(device)
                    paper_config = config.paper_config_from_size(self.document.page_size)
                    if paper_config:
                        paper_size = paper_config.name
                    else:
                        raise ValueError(f"page size is not available for device {device}")

                vp.write_hpgl(
                    file_object,
                    self.document,
                    page_size=paper_size,
                    landscape=self.document.page_size[0] > self.document.page_size[1],
                    center=self._center_on_page,
                    device=device,
                    velocity=velocity,
                    quiet=quiet,
                )
            else:
                raise ValueError(
                    f"unknown format '{format}', specify format with 'format' argument "
                )

        try:
            with open(file, "w") as fo:  # type: ignore
                write_to_file(fo)
        except TypeError:
            write_to_file(file)

    ####################
    # RANDOM FUNCTIONS #
    ####################

    def random(self, a: float, b: float | None = None) -> float:
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
        self.random_seed = seed

    @property
    def random_seed(self) -> int:
        """Get the current random seed.

        Returns:
            the current random seed as an integer
        """
        return self._random_seed

    @random_seed.setter
    def random_seed(self, seed: int) -> None:
        self._random_seed = seed
        self._random.seed(self._random_seed)

    @overload
    def noise(
        self,
        x: float,
        y: float | None = None,
        z: float | None = None,
        grid_mode: bool = True,
    ) -> float:
        ...

    @overload
    def noise(
        self,
        x: Sequence[float] | np.ndarray,
        y: None | float | Sequence[float] | np.ndarray = None,
        z: None | float | Sequence[float] | np.ndarray = None,
        grid_mode: bool = True,
    ) -> np.ndarray:
        ...

    def noise(self, x, y=None, z=None, grid_mode=True):
        """Returns the Perlin noise value at specified coordinates.

        This function sample 1D, 2D or 3D noise space, depending on the number of
        coordinates provided. The coordinates may be either scalar values or vectors. In the
        later case, :meth:`noise` can operate in grid mode (default) or not.

        When ``x``, ``y``, and ``z`` are scalar values, this function returns a float value::

            >>> vsk = Vsketch()
            >>> vsk.noise(1.0, 1.0, 1.0)
            0.5713948646260701

        With grid mode enabled, either or all of ``x``, ``y``, and ``z`` can also be 1D vectors
        (any sequence type, such as Numpy array), each with possibly different length.
        :meth:`noise` computes values for *every combination* of the input parameters::

            >>> vsk.noise([0, 0.1, 0.2, 0.3, 0.4])
            array([0.73779253, 0.7397108 , 0.73590816, 0.72425246, 0.69773313])
            >>> vsk.noise([0., 1.], np.linspace(0., 1., 5))
            array([[0.73779253, 0.61588815, 0.52075717, 0.48219902, 0.50484146],
                   [0.59085755, 0.67609827, 0.73308901, 0.74057962, 0.75528381]])
            >>> vsk.noise(np.linspace(0., 1., 100), np.linspace(0., 1., 50), [0, 100]).shape
            (100, 50, 2)

        With grid mode disabled, the provided input coordinates must all have the same shape
        and the returned array will also have this shape. In this example, the Perlin 2D noise
        field is sample along the diagonal::

            >>> vsk.noise(np.linspace(0, 1, 10), np.linspace(0, 1, 10), grid_mode=False)
            array([0.57731468, 0.58830833, 0.61182686, 0.59998289, 0.64938922,
            0.68599367, 0.62879284, 0.6615939 , 0.73334911, 0.76806402])

        The vectorised version of :meth:`noise` is several orders of magnitude faster than the
        corresponding scalar calls. It is thus strongly recommended to use few, out-of-loop,
        vectorized calls instead of many in-loop scalar calls.

        For a given :class:`Vsketch` instance, a given coordinate will always yield the same
        pseudo-random value, unless another seed is set (:func:`noiseSeed`).

        See `Processing's description <https://processing.org/reference/noise_.html>`_
        of Perlin noise for background information.

        .. seealso::

            * :func:`noiseSeed`
            * :func:`noiseDetail`

        Args:
            x: X coordinate in the noise space
            y: Y coordinate in the noise space (if provided)
            z: Z coordinate in the noise space (if provided)
            grid_mode: enable grid mode (default: True)

        Returns:
            noise value between 0.0 and 1.0
        """

        # force grid mode to True in scalar mode
        if (
            isinstance(x, Real)
            and (isinstance(y, Real) or y is None)
            and (isinstance(z, Real) or z is None)
        ):
            grid_mode = True

        zeros = np.zeros_like(x) if not grid_mode else 0
        return self._noise.perlin(
            x,
            y if y is not None else zeros,
            z if z is not None else zeros,
            grid_mode=grid_mode,
        )

    def noiseDetail(self, lod: int, falloff: float | None = None) -> None:
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
        if lod > 0:
            self._noise.octaves = lod
        if falloff is not None and falloff > 0.0:
            self._noise.amp_falloff = falloff

    def noiseSeed(self, seed: int) -> None:
        """Set the random seed for :func:`noise`.

        .. seealso::

            :func:`noise`

        Args:
            seed: the seed
        """
        self._noise.seed(seed)

    #######################
    # STATELESS UTILITIES #
    #######################

    @staticmethod
    def lerp(
        start: float | complex | np.ndarray,
        stop: float | complex | np.ndarray,
        amt: float,
    ) -> float | complex | np.ndarray:
        """Interpolate between two numbers or arrays.

        The ``amt`` parameter is the amount to interpolate between the two values where 0.0
        equal to the first point, 0.1 is very near the first point, 0.5 is half-way in between,
        etc.

        Examples::

            >>> vsk = Vsketch()
            >>> vsk.lerp(0., 10, 0.3)
            3.
            >>> vsk.lerp(np.array([0, 1, 2]), np.array(10, 11, 12), 0.5)
            array([5., 6., 7.])

        Args:
            start: start value or array
            stop: end value or array
            amt: value between 0. and 1.

        Return:
            interpolated value or array
        """
        return (1.0 - amt) * start + amt * stop

    @staticmethod
    def map(
        value: float | np.ndarray,
        start1: float,
        stop1: float,
        start2: float,
        stop2: float,
    ) -> float | np.ndarray:
        """Map a value from one range to the other.

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

    # noinspection PyNestedDecorators
    @overload
    @staticmethod
    def easing(
        value: float,
        mode: str = "linear",
        start1: float = 0.0,
        stop1: float = 1.0,
        start2: float = 0.0,
        stop2: float = 1.0,
        low_dead: float = 0.0,
        high_dead: float = 0.0,
        param: float = 10,
    ) -> float:
        ...

    # noinspection PyNestedDecorators
    @overload
    @staticmethod
    def easing(
        value: np.ndarray,
        mode: str = "linear",
        start1: float = 0.0,
        stop1: float = 1.0,
        start2: float = 0.0,
        stop2: float = 1.0,
        low_dead: float = 0.0,
        high_dead: float = 0.0,
        param: float = 10,
    ) -> np.ndarray:
        ...

    @staticmethod
    def easing(
        value: float | np.ndarray,
        mode: str = "linear",
        start1: float = 0.0,
        stop1: float = 1.0,
        start2: float = 0.0,
        stop2: float = 1.0,
        low_dead: float = 0.0,
        high_dead: float = 0.0,
        param: float = 10,
    ) -> float | np.ndarray:
        """Map a value from one range to another, using an easing function.

        Easing functions specify the rate of change of a parameter over time (or any other
        input). This function provides a way to apply an easing function on a value.

        The ``mode`` parameter specify the easing function to use. Check the ``easing`` example
        for a list and a demo of all easing functions.

        The input value may be a single float or a Numpy array of float.

        Input values are clamped to ``[start1, stop1]`` and mapped to ``[start2, stop2]``.
        Further, a lower and/or high dead zone can be specified as a fraction of the range
        using ``low_dead`` and ``high_dead``. If ``delta = stop1 - start1``, the actual input
        range is ``[start1 + low_dead * delta, stop1 - high_dead * delta]``.

        The ``param`` argument is used by some easing functions.

        Args:
            value: input value(s)
            mode: easing function to use
            start1: start of the input range
            stop1: end of the input range
            start2: start of the output range
            stop2: end of the output range
            low_dead: lower dead zone (fraction of input range)
            high_dead: higher dead zone (fraction of input range)
            param: parameter use

        Returns:
            converted value(s)
        """

        input_low = start1 + low_dead * (stop1 - start1)
        input_high = stop1 - high_dead * (stop1 - start1)
        if input_low == input_high:
            raise ValueError(f"invalid input span")
        norm_value = np.clip((value - input_low) / (input_high - input_low), 0.0, 1.0)

        if mode in EASING_FUNCTIONS:
            out = EASING_FUNCTIONS[mode](norm_value, param)
        else:
            raise NotImplementedError(f"unknown easing function {mode}")

        res = start2 + out * (stop2 - start2)
        if getattr(res, "shape", None) == ():
            res = float(res)
        return res

    ########
    # TEXT #
    ########

    def textMode(self, mode: str) -> None:
        """Controls how text is laid out.

        There are two options for the text mode:
          - "transform", where the font itself is subject to the current transform
            matrix, including translation, scaling, rotation, skewing and flipping.
          - "label", where the text is only scaled and translated using the current
            transform matrix, but is not rotated, skewed or flipped.

        .. seealso::

            * :func:`text`

        Args:
            mode (``"transform"``, or ``"label"``): text layout mode to use.
        """

        if mode in ["label", "transform"]:
            self._text_mode = mode
        else:
            raise ValueError("mode must be one of 'label', 'transform'")

    def text(
        self,
        text: str,
        x: float = 0.0,
        y: float = 0.0,
        *,
        width: float | None = None,
        font: str = "futural",
        size: float | str = "12pt",
        mode: str | None = None,
        align: str = "left",
        line_spacing: float = 1.0,
        justify: bool = False,
    ) -> None:
        """Add text to your sketch!

        This can add either lines or blocks of text to your sketch. The default is
        to add a line of text, but if `width` is specified, then a block of text
        will be created that width.

        The fonts available are the same as those
        `available from vpype <https://github.com/abey79/vpype/tree/master/vpype/fonts>`_.

        A ``size`` of 1.0 means the maximum font height will be as long as a line 1.0
        long (given current transform).

        The ``mode`` here is special. There are two options for the mode:
          - "transform", where the font itself is subject to the current transform
            matrix, including translation, scaling, rotation, skewing and flipping.
          - "label", where the text is only moved and scaled using the current
            transform matrix, but is not rotated, skewed or flipped.

        The text mode can also be set using :func:`textMode`.

        ``align`` controls the text alignment, and can be "left", "right" or "center".

        ``line_spacing`` and ``justify`` are only used when ``width`` is specified, and they
        allow you to control the line spacing and justification of your block of text.

        .. seealso::

          - :func:`textMode`

        Args:
            text: text to add to the sketch
            x: the x coordinate of the anchor point for the text. This sets either
                the leftmost, rightmost, or centre point of the first line of
                text, depending on the value of ``align``.
            y: the y coordinate of the anchor point for the text. This sets the
                centre line of the first line of text.
            width: if given, wraps the text to this width and creates a text
                block, not a text line. A text block may be multi-line.
            size: the font size. It is highly recommended to give this as a float
                (in document units) in "transform" mode, and an absolute size
                such as "12pt" in "label" mode.
            font: a vpype font
            mode: "transform" or "label", see description for details.
            align: "left", "right", or "center". See also `x` and `y` args.
            line_spacing: Gives the line spacing for a text block, in multiples
                of `size`. No effect without `width`.
            justify: whether to justify the text block. No effect without `width`.

        """

        if mode is None:
            mode = self._text_mode

        size = vp.convert_length(size)

        if width is None:
            text_lc = vp.text_line(text, font, size, align=align)
        else:
            text_lc = vp.text_block(text, width, font, size, align, line_spacing, justify)

        if mode == "transform":
            # Move the text to the right place, and then apply the current
            # transform.
            text_lc.translate(x, y)
            text_lc = vp.LineCollection([self._transform_line(line) for line in text_lc])
        elif mode == "label":
            # Then use a point to find out where to move the text to, given the
            # current transformation.
            location = self._transform_line(np.array([complex(x, y)]))
            text_lc.translate(location.real, location.imag)

        if self._cur_stroke is not None:
            self._document.add(text_lc, self._cur_stroke)
