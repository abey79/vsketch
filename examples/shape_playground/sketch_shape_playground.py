from typing import Optional

import vsketch


class ShapePlaygroundSketch(vsketch.SketchClass):
    # Sketch parameters:
    circle_op = vsketch.Param(
        "union", choices=["union", "difference", "intersection", "symmetric_difference"]
    )
    stroke = vsketch.Param("layer 1", choices=["off", "layer 1"])
    fill = vsketch.Param("off", choices=["off", "layer 1", "layer 2"])
    pen_width = vsketch.Param(0.3, 0, unit="mm", step=0.1)
    mask_lines = vsketch.Param("default", choices=["default", "on", "off"])
    mask_points = vsketch.Param("default", choices=["default", "on", "off"])

    def draw(self, vsk: vsketch.Vsketch) -> None:
        vsk.size("15x15cm", center=False)
        vsk.scale("cm")

        shp = vsk.createShape()

        shp.square(0, 0, 3, mode="radius")
        shp.circle(5, 0, 3, mode="radius", op=self.circle_op)  # type: ignore

        for i in range(13):
            x = -3.5 + i
            shp.line(x, -3.5, x, 3.5)

            for j in range(8):
                y = -3.5 + j
                shp.point(x + 0.25, y + 0.25)

        vsk.penWidth(self.pen_width)

        if self.stroke == "off":
            vsk.noStroke()
        elif self.stroke == "layer 1":
            vsk.stroke(1)

        if self.fill == "off":
            vsk.noFill()
        elif self.fill == "layer 1":
            vsk.fill(1)
        elif self.fill == "layer 2":
            vsk.fill(2)

        def mask_opt(value: str) -> Optional[bool]:
            if value == "on":
                return True
            elif value == "off":
                return False
            else:
                return None

        vsk.translate(5, 7.5)
        vsk.shape(
            shp, mask_lines=mask_opt(self.mask_lines), mask_points=mask_opt(self.mask_points)
        )

    def finalize(self, vsk: vsketch.Vsketch) -> None:
        pass


if __name__ == "__main__":
    ShapePlaygroundSketch.display()
