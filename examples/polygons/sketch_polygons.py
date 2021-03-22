import numpy as np

import vsketch


class PolygonsSketch(vsketch.SketchClass):
    def draw(self, vsk: vsketch.Vsketch) -> None:
        vsk.size("a4", landscape=True)
        vsk.scale("4mm")

        phase = -np.pi / 2
        for i in range(20):
            angles = np.linspace(0, 2 * np.pi, i + 4)
            vsk.polygon((i + 1) * np.cos(angles + phase), (i + 1) * np.sin(angles + phase))

    def finalize(self, vsk: vsketch.Vsketch) -> None:
        vsk.vpype("linemerge linesimplify reloop linesort")


if __name__ == "__main__":
    PolygonsSketch.display()
