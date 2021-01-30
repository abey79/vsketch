import vsketch


def setup(vsk: vsketch.Vsketch) -> None:
    vsk.size("a4")
    vsk.scale("1cm")
    vsk.translate(6, 6)
    vsk.rotate(-90, degrees=True)
    for _ in range(100):
        vsk.rect(1, 1, 3, 4)
        vsk.scale(1.014)
        vsk.rotate(0.02)


def draw(vsk: vsketch.Vsketch) -> None:
    pass


def finalize(vsk: vsketch.Vsketch) -> None:
    vsk.vpype("linemerge linesort")
