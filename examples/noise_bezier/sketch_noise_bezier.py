import numpy as np

import vsketch


class NoiseBezierSketch(vsketch.Vsketch):
    N = vsketch.Param(200, 0)
    freq = vsketch.Param(0.003, decimals=3)
    drift = vsketch.Param(0.06, decimals=2)

    def draw(self) -> None:
        self.size("a4", landscape=False)
        self.scale("cm")

        t = np.arange(self.N) * self.freq
        perlin = self.noise(t, np.arange(8) * 1000)

        for i in range(self.N):
            v = i * self.drift
            self.bezier(
                perlin[i, 0] * 10 + v,
                perlin[i, 1] * 10 + v,
                perlin[i, 2] * 10 + v,
                perlin[i, 3] * 10 + v,
                perlin[i, 4] * 10 + v,
                perlin[i, 5] * 10 + v,
                perlin[i, 6] * 10 + v,
                perlin[i, 7] * 10 + v,
            )

    def finalize(self) -> None:
        self.vpype("linemerge linesimplify reloop linesort")


if __name__ == "__main__":
    vsk = NoiseBezierSketch()
    vsk.draw()
    vsk.finalize()
    vsk.display()
