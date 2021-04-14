from typing import TYPE_CHECKING, Any, Iterable, List, Optional, Sequence, Tuple, Union, cast

import numpy as np
import vpype as vp
from shapely.geometry import LineString, MultiLineString, Point, Polygon

from .curves import quadratic_bezier_path
from .utils import compute_ellipse_mode

if TYPE_CHECKING:
    from .vsketch import Vsketch

# TODO
# - clean up code duplicates
# - add points
# - examples


class Shape:
    def __init__(self, vsk: "Vsketch"):
        self._vsk = vsk
        self._polygon = Polygon()
        self._lines: List[LineString] = []
        self._points: List[Point] = []

    def _add_polygon(
        self, exterior: np.ndarray, holes: Sequence[np.ndarray] = (), op: str = "union"
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
            elif op == "xor":
                self._polygon = self._polygon.symmetric_difference(p)
            else:
                raise ValueError(f"operation {op} invalid")

    def _compile(self) -> Tuple[Polygon, MultiLineString]:
        lines = []
        for line in self._lines:
            new_line = line.difference(self._polygon)
            if not new_line.is_empty:
                lines.append(new_line)
        return self._polygon, MultiLineString(lines)

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
        diameter: Optional[float] = None,
        radius: Optional[float] = None,
        mode: Optional[str] = None,
        op: str = "union",
    ) -> None:
        """Draw a circle.

        The level of detail used to approximate the circle is controlled by :func:`detail`.
        As for the :meth:`ellipse` function, the way arguments are interpreted is influenced by
        the mode set with :meth:`ellipseMode` or the ``mode`` argument.

        .. seealso::

            * :meth:`ellipse`
            * :meth:`ellipseMode`

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
        mode: Optional[str] = None,
        op: str = "union",
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
        degrees: Optional[bool] = False,
        close: Optional[str] = "no",
        mode: Optional[str] = None,
        op: str = "union",
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
        tl: Optional[float] = None,
        tr: Optional[float] = None,
        br: Optional[float] = None,
        bl: Optional[float] = None,
        mode: Optional[str] = None,
        op: str = "union",
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
            mode: "corner", "corners", "redius", or "center" (see :meth:`rectMode`)
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
        self, x: float, y: float, extent: float, mode: Optional[str] = None, op: str = "union"
    ) -> None:
        """Draw a square.

        As for the :meth:`rect` function, the way arguments are interpreted is influenced by
        the mode set with :meth:`rectMode` or the ``mode`` argument.

        .. seealso::

            * :meth:`rect`
            * :meth:`rectMode`

        Example:

            >>> import vsketch
            >>> vsk = vsketch.Vsketch()
            >>> vsk.square(2, 2, 2.5)

        Args:
            x: X coordinate of top-left corner
            y: Y coordinate of top-left corner
            extent: width and height of the square
            mode: "corner", "redius", or "center" (see :meth:`rectMode`) — note that the
                "corners" mode is meaningless for this function, and is interpreted as the
                "corner" mode
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
        op: str = "union",
    ) -> None:
        """Draw a quadrilateral.

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
        op: str = "union",
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

        line = np.array(
            [x1 + y1 * 1j, x2 + y2 * 1j, x3 + y3 * 1j, x1 + y1 * 1j], dtype=complex
        )
        self._add_polygon(line, op=op)

    def polygon(
        self,
        x: Union[Iterable[float], Iterable[Sequence[float]], Iterable[complex]],
        y: Optional[Iterable[float]] = None,
        holes: Iterable[Iterable[Sequence[float]]] = (),
        close: bool = False,
        op: str = "union",
    ) -> None:
        """Draw a polygon.

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

    def geometry(self, shape: Any, op: str = "union") -> None:
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
                self.polygon(shape.coords, op=op)
            elif shape.geom_type == "MultiLineString":
                for ls in shape:
                    self.polygon(ls.coords, op=op)
            elif shape.geom_type in ["Polygon", "MultiPolygon"]:
                if shape.geom_type == "Polygon":
                    shape = [shape]
                for p in shape:
                    self.polygon(
                        p.exterior.coords, holes=[hole.coords for hole in p.interiors], op=op
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

        path = quadratic_bezier_path(x1, y1, x2, y2, x3, y3, x4, y4, self._vsk.epsilon)
        self._add_polygon(path, op="union")
