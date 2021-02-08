import vsketch


class PointTransformSketch(vsketch.Vsketch):
    def draw(self) -> None:
        self.size("a4", landscape=False)
        self.scale("1mm")

        with self.pushMatrix():
            for _ in range(40):
                self.rotate(2, degrees=True)
                self.scale(0.95)
                self.point(-75, 75)
                self.point(0, 75)
                self.point(75, 75)
                self.point(75, 0)
                self.point(75, -75)
                self.point(0, -75)
                self.point(-75, -75)
                self.point(-75, 0)

        with self.pushMatrix():
            self.rotate(80, degrees=True)
            self.scale(0.95 ** 40)
            self.square(0, 0, 150, mode="center")

    def finalize(self) -> None:
        self.vpype("linemerge linesimplify reloop linesort")
