import vsketch


class NoiseBezierSketch(vsketch.Vsketch):
    N = vsketch.Param(200, 0)
    freq = vsketch.Param(0.003, decimals=3)
    drift = vsketch.Param(0.06, decimals=2)

    def draw(self) -> None:
        self.size("a4", landscape=False)
        self.scale("cm")

        for i in range(self.N()):
            t = i * self.freq()
            v = i * self.drift()
            self.bezier(
                self.noise(t, 0) * 10 + v,
                self.noise(t, 1000) * 10 + v,
                self.noise(t, 2000) * 10 + v,
                self.noise(t, 3000) * 10 + v,
                self.noise(t, 4000) * 10 + v,
                self.noise(t, 5000) * 10 + v,
                self.noise(t, 6000) * 10 + v,
                self.noise(t, 7000) * 10 + v,
            )

    def finalize(self) -> None:
        self.vpype("linemerge linesimplify reloop linesort")
