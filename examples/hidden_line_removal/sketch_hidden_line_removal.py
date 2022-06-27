"""Hidden line removal example

This examples illustrates various techniques to emulate hidden line removal.
"""

import importlib.util
import sys

from shapely.geometry import Point

import vsketch

# check if vpype-occult is installed
OCCULT_INSTALLED = importlib.util.find_spec("occult", package="vpype-occult") is not None


def two_circles_shapely(vsk: vsketch.Vsketch) -> None:
    """Use shapely's boolean operations to emulate hidden line removal."""
    circle1 = Point(0, 0).buffer(4)
    circle2 = Point(3, 0).buffer(4)

    vsk.geometry(circle1.exterior.difference(circle2))
    vsk.geometry(circle2.exterior)


def two_circles_occult(vsk: vsketch.Vsketch, layer_id: int) -> None:
    """Use the `occult` vpype plug-in."""
    if OCCULT_INSTALLED:
        vsk.circle(0, 0, radius=4)
        vsk.circle(3, 0, radius=4)
        vsk.vpype(f"occult -l{layer_id}")
    else:
        vsk.text(
            "occult must be installed for this method", x=1.5, mode="label", align="center"
        )


def two_circles_shapes(vsk: vsketch.Vsketch) -> None:
    """Use shapes.

    Note that this technique is suboptimal because overdraw happens on the common boundary.
    This is highlighted by slightly offsetting the second circle to the right.
    """
    shp = vsk.createShape()
    shp.circle(0, 0, radius=4)
    shp.circle(3, 0, radius=4, op="difference")

    vsk.shape(shp)
    vsk.circle(3.2, 0, radius=4)


class HiddenLineRemovalSketch(vsketch.SketchClass):
    def draw(self, vsk: vsketch.Vsketch) -> None:
        vsk.size("a4", landscape=False)
        vsk.scale("cm")

        vsk.stroke(1)
        two_circles_shapely(vsk)

        vsk.translate(0, 9)
        vsk.stroke(2)
        two_circles_occult(vsk, 2)

        vsk.translate(0, 9)
        vsk.stroke(3)
        two_circles_shapes(vsk)

    def finalize(self, vsk: vsketch.Vsketch) -> None:
        pass


if __name__ == "__main__":
    HiddenLineRemovalSketch.display()
