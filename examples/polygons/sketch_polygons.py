import numpy as np

import vsketch


class PolygonsSketch(vsketch.Vsketch):
    def draw(self) -> None:
        self.size("a4", landscape=True)
        self.scale("4mm")

        phase = -np.pi / 2
        for i in range(20):
            angles = np.linspace(0, 2 * np.pi, i + 4)
            self.polygon((i + 1) * np.cos(angles + phase), (i + 1) * np.sin(angles + phase))

    def finalize(self) -> None:
        self.vpype("linemerge linesimplify reloop linesort")
