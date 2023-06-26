from __future__ import annotations

from typing import TYPE_CHECKING, Iterable, Literal, Sequence, cast

import numpy as np
import vpype as vp
from shapely.geometry import (
    LinearRing,
    LineString,
    MultiLineString,
    MultiPoint,
    MultiPolygon,
    Point,
    Polygon,
)
from shapely.ops import unary_union

from .curves import cubic_bezier_path
from .utils import compute_ellipse_mode

if TYPE_CHECKING:
    from . import Vsketch


BooleanOperation = Literal["union", "difference", "intersection", "symmetric_difference"]
""" Specify how to combine two shapes.

Options: one of 'union', 'difference', 'intersection', or 'symmetric_difference'
"""


class Shape:
    """Reusable and drawable shape with support for boolean operations.

    A shape is a reusable graphical element made of polygons, lines and points. Shapes are
    built using primitives in a very similar way to how :class:`Vsketch` works with the added
    capability of using boolean drawing operation (union, difference, intersection, or
    exclusive union).

    Shapes must be created using a :class:`Vsketch` instance::

        shape = vsk.createShape()

    Shapes consist of an area (which may be disjoint and have holes), a set of lines, and a set
    of points (both of which may be empty). Lines and points are added to the shape using the
    :meth:`line`, :meth:`bezier`, and :meth:`point` methods.

    The shape's area can be built with primitives similar to that of :class:`Vsketch`::

        shape.square(0, 0, 1, mode="radius")
        shape.square(0.5, 0.5, 1, mode="radius")

    By default, an union operation applied when new primitives are added. Other boolean
    operations are available. For example, a hole can be punched in the shape as follows::

        shape.circle(0, 0, 0.5, mode="radius", op="difference")

    Finally, a shape can be drawn to a sketch with the :meth:`Vsketch.shape` method::

        vsk.stroke(1)
        vsk.fill(2)
        vsk.shape(shape)

    :meth:`Vsketch.shape` can control whether the lines and points which intersects with the
    shape's area are masked. For example, it's best to enable masking when the shape's area is
    to be hatched. See :meth:`Vsketch.shape`'s documentation for details.

    .. note::

        It is helpful to understand the fundamental difference between a :class:`Vsketch` and
        :class:`Shape` instance.

        At any point in time, :class:`Vsketch` instances contains a set of paths which
        correspond exactly to what the plotter will draw and is considered read-only (One of
        the reason for that is that scaling existing geometries would invalidate any hatching).

        On the other hand, a :class:`Shape` instance is an abstract geometrical representation
        which can, at any point in time, be further modified, for example using the
        ``difference`` mode (which subtracts a primitive from the existing shape). This
        abstract representation is turned into actual plotter line work (including hatching if
        enabled with :meth:`Vsketch.fill`) `only` when it is drawn in a sketch using
        :meth:`Vsketch.shape`. At this point, the final scaling is applied (based on the
        current transformation matrix), the hatching (if any) is computed, points are
        transformed into small circles (see :meth:`Vsketch.point`), and the resulting,
        ready-to-be-plotted paths are added to the sketch.
    """

    def __init__(self, vsk: Vsketch):
        self._vsk = vsk
        self._polygon = Polygon()
        self._lines: list[LineString] = []
        self._points: list[Point] = []

    def _add_polygon(
        self,
        exterior: np.ndarray,
        holes: Sequence[np.ndarray] = (),
        op: BooleanOperation = "union",
    ) -> None:
        if exterior[0] != exterior[-1]:
            if len(holes) > 0:
                raise ValueError("holes are not supported for open lines")
            if op != "union":
                raise ValueError(
                    f"operation {op} unsupported for open lines (must be 'union')"
                )
            self._lines.append(LineString(vp.as_vector(exterior)))
        else:
            p = Polygon(vp.as_vector(exterior), [vp.as_vector(hole) for hole in holes])
            if op == "union":
                self._polygon = self._polygon.union(p)
            elif op == "difference":
                self._polygon = self._polygon.difference(p)
            elif op == "intersection":
                self._polygon = self._polygon.intersection(p)
            elif op == "symmetric_difference":
                self._polygon = self._polygon.symmetric_difference(p)
            else:
                raise ValueError(f"operation {op} invalid")

    def _compile(
        self, mask_lines: bool, mask_points: bool
    ) -> tuple[MultiPolygon, MultiLineString, MultiPoint]:
        """Returns the shape's content.

        This function returns three Shapely geometries:

        * a :class:`Polygon` or :class:`MultiPolygon` for the area
        * a :class:`MultiLineString` for the individual lines
        * a : class:`MultiPoint` for the individual points

        Args:
            mask_lines: controls if points are masked by the shape's area or not
            mask_points: controls if lines are masked by the shape's area or not

        Returns:
            tuple of MultiPolygon, MultiLineString, and MultiPoint, each of which may have a 0
            length
        """

        # normalize area
        if self._polygon.is_empty:
            area = MultiPolygon()
        elif isinstance(self._polygon, Polygon):
            area = MultiPolygon([self._polygon])
        elif isinstance(self._polygon, MultiPolygon):
            area = self._polygon
        else:
            raise RuntimeError(f"incorrect type for Shape._polygon: {type(self._polygon)}")

        # normalize/mask lines
        if mask_lines:
            lines = unary_union(
                [line.difference(area) for line in self._lines if not line.is_empty]
            )

            if lines.is_empty:
                lines = MultiLineString()
            elif isinstance(lines, (LineString, LinearRing)):
                lines = MultiLineString([lines])
            elif not isinstance(lines, MultiLineString):
                raise RuntimeError(f"incorrect type for masked lines: {type(lines)}")
        else:
            lines = MultiLineString(self._lines)

        # normalize/mask points
        points = MultiPoint(
            [point for point in self._points if not mask_points or not point.intersects(area)]
        )

        return area, lines, points

    def point(self, x: float, y: float) -> None:
        """Add a point to the shape.
        Args:
            x: X coordinate of the point
            y: Y coordinate of the point
        """

        self._points.append(Point(x, y))

    def line(self, x1: float, y1: float, x2: float, y2: float) -> None:
        """Add a line to the shape.

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
        op: BooleanOperation = "union",
    ) -> None:
        """Add a circle to the shape.

        The level of detail used to approximate the circle is controlled by
        :func:`Vsketch.detail`. As for the :meth:`ellipse` function, the way arguments are
        interpreted is influenced by  the ``mode`` argument or the mode set with
        :meth:`Vsketch.ellipseMode` of the :class:`Vsketch` instance used to create the shape.

        This function support multiple boolean mode with the ``op`` argument: ``union``
        (default, the circle is added to the shape), ``difference`` (the circle is cut off the
        shape), ``intersection`` (only the overlapping part of the circle is kept in the
        shape), or ``symmetric_difference`` (only the none overlapping parts of the shape and
        circle are kept).

        .. seealso::

            * :meth:`Vsketch.circle`
            * :meth:`ellipse`
            * :meth:`Vsketch.ellipseMode`

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
            mode: one of 'center', 'radius', 'corner', 'corners'
            op: one of 'union', 'difference', 'intersection', or 'symmetric_difference'
        """

        if (diameter is None) == (radius is None):
            raise ValueError("either (but not both) diameter and radius must be provided")

        if radius is None:
            radius = cast(float, diameter) / 2

        if mode is None:
            # noinspection PyProtectedMember
            mode = self._vsk._ellipse_mode

        if mode == "corners":
            mode = "corner"

        self.ellipse(x, y, 2 * radius, 2 * radius, mode=mode, op=op)

    def ellipse(
        self,
        x: float,
        y: float,
        w: float,
        h: float,
        mode: str | None = None,
        op: BooleanOperation = "union",
    ) -> None:
        """Add an ellipse to the shape.

        The way ``x``, ``y``, ``w``, and ``h`` parameters are interpreted depends on the
        current ellipse mode of the :class:`Vsketch` instance used to create the shape.

        By default, ``x`` and ``y`` set the location of the  ellipse center, ``w`` sets its
        width, and ``h`` sets its height. The way these parameters are interpreted can be
        changed with the ``mode`` argument or the :meth:`Vsketch.ellipseMode` function of the
        :class:`Vsketch` instance used to create the shape.

        This function support multiple boolean mode with the ``op`` argument: ``union``
        (default, the ellipse is added to the shape), ``difference`` (the ellipse is cut off
        the shape), ``intersection`` (only the overlapping part of the ellipse is kept in the
        shape), or ``symmetric_difference`` (only the none overlapping parts of the shape and
        ellipse are kept).

        .. seealso::

            * :meth:`Vsketch.ellipse`
            * :meth:`Vsketch.ellipseMode`

        Examples:

            By default, the argument are interpreted as the center coordinates as well as the
            width and height::

                >>> import vsketch
                >>> vsk = vsketch.Vsketch()
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
            op: one of 'union', 'difference', 'intersection', or 'symmetric_difference'
        """
        if mode is None:
            # noinspection PyProtectedMember
            mode = self._vsk._ellipse_mode
        line = vp.ellipse(*compute_ellipse_mode(mode, x, y, w, h), self._vsk.epsilon)
        self._add_polygon(line, op=op)

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
        op: BooleanOperation = "union",
    ) -> None:
        """Add an arc to the shape.

        The way ``x``, ``y``, ``w``, and ``h`` parameters are interpreted depends on the
        current ellipse mode (see :meth:`ellipse` for a detailed explanation) and refer to the
        arc's underlying ellipse.

        The ``close`` parameter controls the arc's closure: ``no`` keeps it open,
        ``chord`` closes it with a straight line, and ``pie`` connects the two endings with the
        arc center.

        This function support multiple boolean mode with the ``op`` argument: ``union``
        (default, the arc is added to the shape), ``difference`` (the arc is cut off the
        shape), ``intersection`` (only the overlapping part of the arc is kept in the
        shape), or ``symmetric_difference`` (only the none overlapping parts of the shape and
        arc are kept).

        .. seealso::
            * :meth:`Vsketch.arc`
            * :meth:`Vsketch.ellipseMode`
            * :meth:`ellipse`

        Example:
            >>> import vsketch
            >>> vsk = vsketch.Vsketch()
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
            op: one of 'union', 'difference', 'intersection', or 'symmetric_difference'
        """
        if not degrees:
            start = start * (180 / np.pi)
            stop = stop * (180 / np.pi)

        if mode is None:
            # noinspection PyProtectedMember
            mode = self._vsk._ellipse_mode

        cx, cy, rw, rh = compute_ellipse_mode(mode, x, y, w, h)
        line = vp.arc(cx, cy, rw, rh, start, stop, self._vsk.epsilon)
        if close == "chord":
            line = np.append(line, [line[0]])
        elif close == "pie":
            line = np.append(line, [complex(cx, cy), line[0]])
        elif close != "no":
            raise ValueError("close must be one of 'no', 'chord', 'pie'")

        self._add_polygon(line, op=op)

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
        op: BooleanOperation = "union",
    ) -> None:
        """Add a rectangle to the shape.

        The way ``x``, ``y``, ``w``, and ``h`` parameters are interpreted depends on the
        current rect mode of the :class:`Vsketch` instance used to create the shape.

        By default, ``x`` and ``y`` set the location of the upper-left corner, ``w`` sets the
        width, and ``h`` sets the height. The way these parameters are interpreted can be
        changed with the ``mode`` argument or the :meth:`rectMode` function of the
        :class:`Vsketch` instance used to create this shape.

        The optional parameters ``tl``, ``tr``, ``br`` and ``bl`` define the radius used for
        each corner (default: 0). If some corner radius is not specified, it will be set equal
        to the previous corner radius. If the sum of two consecutive corner radii are greater
        than their associated edge lenght, their values will be rescaled to fit the rectangle.

        This function support multiple boolean mode with the ``op`` argument: ``union``
        (default, the rectangle is added to the shape), ``difference`` (the rectangle is cut
        off the shape), ``intersection`` (only the overlapping part of the rectangle is kept in
        the shape), or ``symmetric_difference`` (only the none overlapping parts of the shape
        and rectangle are kept).

        .. seealso::

            * :meth:`Vsketch.rect`
            * :meth:`Vsketch.rectMode`

        Examples:

            By default, the argument are interpreted as the top left corner as well as the
            width and height::

                >>> import vsketch
                >>> vsk = vsketch.Vsketch()
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
            op: one of 'union', 'difference', 'intersection', or 'symmetric_difference'
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
            # noinspection PyProtectedMember
            mode = self._vsk._rect_mode

        if mode == "corner":
            line = vp.rect(x, y, w, h, tl, tr, br, bl, self._vsk.epsilon)
        elif mode == "corners":
            #  Find top-left corner
            tl_x, tl_y = min(x, w), min(y, h)
            width, height = max(x, w) - tl_x, max(y, h) - tl_y
            line = vp.rect(tl_x, tl_y, width, height, tl, tr, br, bl, self._vsk.epsilon)
        elif mode == "center":
            line = vp.rect(x - w / 2, y - h / 2, w, h, tl, tr, br, bl, self._vsk.epsilon)
        elif mode == "radius":
            line = vp.rect(x - w, y - h, 2 * w, 2 * h, tl, tr, br, bl, self._vsk.epsilon)
        else:
            raise ValueError("mode must be one of 'corner', 'corners', 'center', 'radius'")

        self._add_polygon(line, op=op)

    def square(
        self,
        x: float,
        y: float,
        extent: float,
        mode: str | None = None,
        op: BooleanOperation = "union",
    ) -> None:
        """Add a square to the shape.

        As for the :meth:`rect` function, the way arguments are interpreted is influenced by
        the mode set with the ``mode`` argument or the :meth:`Vsketch.rectMode` of the
        :class:`Vsketch` instance used to create the shape.

        This function support multiple boolean mode with the ``op`` argument: ``union``
        (default, the square is added to the shape), ``difference`` (the square is cut off the
        shape), ``intersection`` (only the overlapping part of the square is kept in the
        shape), or ``symmetric_difference`` (only the none overlapping parts of the shape and
        square are kept).

        .. seealso::

            * :meth:`Vsketch.square`
            * :meth:`rect`
            * :meth:`Vsketch.rectMode`

        Example:

            >>> import vsketch
            >>> vsk = vsketch.Vsketch()
            >>> vsk.square(2, 2, 2.5)

        Args:
            x: X coordinate of top-left corner
            y: Y coordinate of top-left corner
            extent: width and height of the square
            mode: "corner", "radius", or "center" (see :meth:`rectMode`) — note that the
                "corners" mode is meaningless for this function, and is interpreted as the
                "corner" mode
            op: one of 'union', 'difference', 'intersection', or 'symmetric_difference'
        """
        # noinspection PyProtectedMember
        if mode == "corners" or (mode is None and self._vsk._rect_mode == "corners"):
            mode = "corner"
        self.rect(x, y, extent, extent, mode=mode, op=op)

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
        op: BooleanOperation = "union",
    ) -> None:
        """Add a quadrilateral to the shape.

        This function support multiple boolean mode with the ``op`` argument: ``union``
        (default, the quad is added to the shape), ``difference`` (the quad is cut off the
        shape), ``intersection`` (only the overlapping part of the quad is kept in the
        shape), or ``symmetric_difference`` (only the none overlapping parts of the shape and
        quad are kept).

        .. seealso::

            * :meth:`Vsketch.quad`

        Example:

            >>> import vsketch
            >>> vsk = vsketch.Vsketch()
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
            op: one of 'union', 'difference', 'intersection', or 'symmetric_difference'
        """
        line = np.array(
            [x1 + y1 * 1j, x2 + y2 * 1j, x3 + y3 * 1j, x4 + y4 * 1j, x1 + y1 * 1j],
            dtype=complex,
        )
        self._add_polygon(line, op=op)

    def triangle(
        self,
        x1: float,
        y1: float,
        x2: float,
        y2: float,
        x3: float,
        y3: float,
        op: BooleanOperation = "union",
    ) -> None:
        """Add a triangle to the shape.

        This function support multiple boolean mode with the ``op`` argument: ``union``
        (default, the triangle is added to the shape), ``difference`` (the triangle is cut off
        the shape), ``intersection`` (only the overlapping part of the triangle is kept in the
        shape), or ``symmetric_difference`` (only the none overlapping parts of the shape and
        triangle are kept).

        .. seealso::

            * :meth:`Vsketch.triangle`

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
            op: one of 'union', 'difference', 'intersection', or 'symmetric_difference'
        """

        line = np.array(
            [x1 + y1 * 1j, x2 + y2 * 1j, x3 + y3 * 1j, x1 + y1 * 1j], dtype=complex
        )
        self._add_polygon(line, op=op)

    def polygon(
        self,
        x: Iterable[float] | Iterable[Sequence[float]] | Iterable[complex],
        y: Iterable[float] | None = None,
        holes: Iterable[Iterable[Sequence[float]]] = (),
        close: bool = False,
        op: BooleanOperation = "union",
    ) -> None:
        """Add a polygon to the shape.

        This function support multiple boolean mode with the ``op`` argument: ``union``
        (default, the polygon is added to the shape), ``difference`` (the polygon is cut off
        the shape), ``intersection`` (only the overlapping part of the polygon is kept in the
        shape), or ``symmetric_difference`` (only the none overlapping parts of the shape and
        polygon are kept).

        .. seealso::

            * :meth:`Vsketch.polygon`

        Examples:

            A single iterable of size-2 sequence can be used::

                >>> import vsketch
                >>> vsk = vsketch.Vsketch()
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
            op: one of 'union', 'difference', 'intersection', or 'symmetric_difference'
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

        self._add_polygon(line, holes=hole_lines, op=op)

    def geometry(
        self,
        shape: LineString
        | LinearRing
        | MultiPoint
        | MultiPolygon
        | MultiLineString
        | Point
        | Polygon,
        op: BooleanOperation = "union",
    ) -> None:
        """Add a Shapely geometry to the shape.

        This function should accept any of LineString, LinearRing, MultiPoint,
        MultiPolygon, MultiLineString, Point, or Polygon.

        This function support multiple boolean modes with the ``op`` argument: ``union``
        (default, the geometry is added to the shape), ``difference`` (the geometry is cut off
        the shape), ``intersection`` (only the overlapping part of the geometry is kept in the
        shape), or ``symmetric_difference`` (only the none overlapping parts of the shape and
        geometry are kept).  The ``op`` argument is ignored if ``shape`` is a MultiPoint
        or Point object.

        .. seealso::

            * :meth:`Vsketch.geometry`

        Args:
            shape (Shapely geometry): a supported shapely geometry object
            op: one of 'union', 'difference', 'intersection', or 'symmetric_difference'
        """
        if getattr(shape, "is_empty", False):
            return

        try:
            if shape.geom_type in ["LineString", "LinearRing"]:
                self.polygon(shape.coords, op=op)
            elif shape.geom_type == "MultiLineString":
                for ls in shape.geoms:
                    self.polygon(ls.coords, op=op)
            elif shape.geom_type in ["Polygon", "MultiPolygon"]:
                if shape.geom_type == "Polygon":
                    poly_list = [shape]
                else:
                    poly_list = shape.geoms
                for p in poly_list:
                    self.polygon(
                        p.exterior.coords, holes=[hole.coords for hole in p.interiors], op=op
                    )
            elif shape.geom_type in ["Point", "MultiPoint"]:
                if shape.geom_type == "Point":
                    point_list = [shape]
                else:
                    point_list = shape.geoms
                for p in point_list:
                    self.point(p.x, p.y)
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
        """Add a Bezier curve to the shape.

        Bezier curves are defined by a series of anchor and control points. The first two
        arguments specify the first anchor point and the last two arguments specify the other
        anchor point. The middle arguments specify the control points which define the shape
        of the curve.

        The level of detail of the bezier curve is controlled using the :meth:`Vsketch.detail`
        method on the :class:`Vsketch` instance used to create the shape.

        .. seealso::

            * :func:`Vsketch.bezierPoint`
            * :func:`Vsketch.bezierTangent`
            * :func:`Vsketch.detail`
            * :func:`Vsketch.bezier`

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

        path = cubic_bezier_path(x1, y1, x2, y2, x3, y3, x4, y4, self._vsk.epsilon)
        self._add_polygon(path, op="union")

    def shape(self, shape: Shape, op: BooleanOperation = "union") -> None:
        """Combine the shape with another shape.

        This function can combine another shape with this shape, using various boolean mode.
        When ``op`` is set to ``"union"``, the ``shape``'s polygons, lines and points are
        merged into this instance. When using other operations (``"difference"``,
        ``"intersection"``, or ``"symmetric_difference"``), the corresponding operation is
        applied with ``shape``'s polygon, but its lines and points are ignored.

        Args:
            shape: the shape to combine
            op: one of 'union', 'difference', 'intersection', or 'symmetric_difference'
        """
        self.geometry(shape._polygon, op=op)

        if op == "union":
            self._lines.extend(shape._lines)
            self._points.extend(shape._points)
