"""Example kindly contributed by Pedro Alcocer.

Website: http://art.pedroalcocer.com
Twitter: https://twitter.com/thepedroalcocer
Instagram: https://www.instagram.com/thepedroalcocer/
"""

import numpy as np

import vsketch


def bug(vsk, x, y):
    ts = [682, 268, 624, 98]
    xy_max = 143.25

    for _ in range(0, 150, 12):
        random = vsk.random(1)
        ts = [t * random + 0.24 for t in ts]

        x1 = np.interp(vsk.noise(ts[0]), [-1, 1], [0, xy_max])
        y1 = np.interp(vsk.noise(ts[1]), [-1, 1], [0, xy_max])
        x2 = np.interp(vsk.noise(ts[2]), [-1, 1], [0, xy_max])
        y2 = np.interp(vsk.noise(ts[3]), [-1, 1], [0, xy_max])
        x3 = np.interp(vsk.noise(ts[3]), [-1, 1], [0, xy_max])
        y3 = np.interp(vsk.noise(ts[2]), [-1, 1], [0, xy_max])
        x4 = np.interp(vsk.noise(ts[1]), [-1, 1], [0, xy_max])
        y4 = np.interp(vsk.noise(ts[0]), [-1, 1], [0, xy_max])

        with vsk.pushMatrix():
            vsk.translate(x, y)
            vsk.rotate(45, degrees=True)
            vsk.bezier(x1, y1, x2, y2, x3, y3, x4, y4)


class BezierBugSketch(vsketch.Vsketch):
    row_count = vsketch.Param(7, 1)
    column_count = vsketch.Param(7, 1)
    row_offset = vsketch.Param(100.0)
    column_offset = vsketch.Param(100.0)

    def draw(self) -> None:
        self.size("10in", "10in")

        for row in range(self.row_count):
            for col in range(self.column_count):
                x = col * self.column_offset
                y = row * self.row_offset
                bug(self, x, y)

    def finalize(self) -> None:
        self.vpype("linesimplify linesort")


if __name__ == "__main__":
    vsk = BezierBugSketch()
    vsk.draw()
    vsk.finalize()
    vsk.display()
