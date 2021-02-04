import vsketch


class SimpleSketch(vsketch.Vsketch):
    draw_type = vsketch.Param("circle", choices=["circle", "square"])
    x = vsketch.Param(5.0, bounds=(5, 10))
    y = vsketch.Param(5.0, bounds=(0, 15))
    radius = vsketch.Param(2.0, bounds=(2, 7))
    n = vsketch.Param(100)
    drift = vsketch.Param(0.05, bounds=(1e-10, 0.1))
    k = vsketch.Param(0.02, bounds=(0.001, 0.1))

    def draw(self) -> None:
        self.size("a5")
        self.scale("1cm")

        for i in range(self.n()):
            t = self.k() * i

            if self.draw_type() == "circle":
                self.circle(self.x(), self.y(), self.radius(), mode="radius")
            else:
                self.square(self.x(), self.y(), self.radius(), mode="radius")

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
