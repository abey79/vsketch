import vsketch

# asdfasdfasdf  sdafsss


class SimpleSketch(vsketch.Vsketch):
    draw_type = vsketch.Param("circle", choices=["circle", "square"])
    radius = vsketch.Param(2.0, 2.0, 7.0)
    n = vsketch.Param(100)
    drift = vsketch.Param(0.05, 1e-10, 0.1)
    k = vsketch.Param(0.02, 0.001, 0.1)

    def draw(self) -> None:
        self.size("a5")
        self.scale("1cm")

        for i in range(self.n()):
            t = self.k() * i

            if self.draw_type() == "circle":
                self.circle(0, 0, self.radius(), mode="radius")
            else:
                self.square(0, 0, self.radius(), mode="radius")

            self.translate(
                (self.noise(t, 0) - 0.3) * self.drift(),
                (self.noise(t, 1) - 0.3) * self.drift(),
            )
            self.scale(
                1 + (self.noise(t, 2) - 0.4) * self.drift(),
                1 + (self.noise(t, 3) - 0.4) * self.drift(),
            )

    def finalize(self) -> None:
        self.vpype("reloop linesimplify")
