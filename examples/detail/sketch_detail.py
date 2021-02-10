import vsketch


class DetailSketch(vsketch.Vsketch):
    detail_mm = vsketch.Param(1, 1, 50)

    def draw(self) -> None:
        self.size("a5", landscape=True)
        self.scale("1.5cm")

        self.detail(f"{self.detail_mm()}mm")

        self.circle(0, 0, 1)
        self.circle(0, 0, 2)
        with self.pushMatrix():
            self.scale(4)
            # the scale is taken into account to compute details
            self.circle(0, 0, 1)

        self.translate(4, 0)

        for i in range(-4, 5):
            with self.pushMatrix():
                self.translate(0, i * 0.4)
                self.bezier(0, 0, 1, -2, 2, 2, 3, 0)

    def finalize(self) -> None:
        self.vpype("linemerge linesimplify reloop linesort")


if __name__ == "__main__":
    vsk = DetailSketch()
    vsk.draw()
    vsk.finalize()
    vsk.display()
