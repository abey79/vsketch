import vsketch


class SimpleSketch(vsketch.Vsketch):
    draw_type = vsketch.Param("circle", choices=["circle", "square"])
    x = vsketch.Param(5.0, bounds=(5, 10))
    y = vsketch.Param(5.0, bounds=(0, 15))
    radius = vsketch.Param(2.0, bounds=(2, 7))

    def draw(self) -> None:
        self.size("a5")
        self.scale("1cm")

        if self.draw_type() == "circle":
            self.circle(self.x(), self.y(), self.radius(), mode="radius")
        else:
            self.square(self.x(), self.y(), self.radius(), mode="radius")

    def finalize(self) -> None:
        self.vpype("reloop linesimplify")
