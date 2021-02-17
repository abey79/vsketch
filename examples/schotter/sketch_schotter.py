import vsketch


class SchotterSketch(vsketch.Vsketch):
    columns = vsketch.Param(12)
    rows = vsketch.Param(22)
    fuzziness = vsketch.Param(1.0)

    def draw(self) -> None:
        self.size("a4", landscape=False)
        self.scale("cm")

        for j in range(self.rows):
            with self.pushMatrix():
                for i in range(self.columns):
                    with self.pushMatrix():
                        self.rotate(self.fuzziness * 0.03 * self.random(-j, j))
                        self.translate(
                            self.fuzziness * 0.01 * self.randomGaussian() * j,
                            self.fuzziness * 0.01 * self.randomGaussian() * j,
                        )
                        self.rect(0, 0, 1, 1)
                    self.translate(1, 0)
            self.translate(0, 1)

    def finalize(self) -> None:
        self.vpype("linemerge linesimplify reloop linesort")


if __name__ == "__main__":
    vsk = SchotterSketch()
    vsk.draw()
    vsk.finalize()
    vsk.display()
