import vsketch


class SchotterSketch(vsketch.SketchClass):
    columns = vsketch.Param(12)
    rows = vsketch.Param(22)
    fuzziness = vsketch.Param(1.0)

    def draw(self, vsk: vsketch.Vsketch) -> None:
        vsk.size("a4", landscape=False)
        vsk.scale("cm")

        for j in range(self.rows):
            with vsk.pushMatrix():
                for i in range(self.columns):
                    with vsk.pushMatrix():
                        vsk.rotate(self.fuzziness * 0.03 * vsk.random(-j, j))
                        vsk.translate(
                            self.fuzziness * 0.01 * vsk.randomGaussian() * j,
                            self.fuzziness * 0.01 * vsk.randomGaussian() * j,
                        )
                        vsk.rect(0, 0, 1, 1)
                    vsk.translate(1, 0)
            vsk.translate(0, 1)

    def finalize(self, vsk: vsketch.Vsketch) -> None:
        vsk.vpype("linemerge linesimplify reloop linesort")


if __name__ == "__main__":
    SchotterSketch.display()
