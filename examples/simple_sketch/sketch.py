import vsketch


class SimpleSketch(vsketch.Vsketch):
    def setup(self) -> None:
        self.size("a5")
        self.scale("1cm")

        self.param("type", "circle", choices=["circle", "square"])
        self.param("x", 5.0, bounds=(0, self.width))
        self.param("y", 5.0, bounds=(0, self.height))
        self.param("radius", 2.0, bounds=(0, 6))

    def draw(self) -> None:
        if self.type == "circle":
            self.circle(self.x, self.y, self.radius, mode="radius")
        else:
            self.square(self.x, self.y, self.radius, mode="radius")

    def finalize(self) -> None:
        self.vpype("reloop")
