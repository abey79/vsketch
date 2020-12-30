import vsketch


def setup(vsk: vsketch.Vsketch) -> None:
    vsk.size("a6")
    vsk.scale("1cm")
    for _ in range(5):
        vsk.rect(1, 1, 3, 4)
        vsk.scale(0.7)


def draw(vsk: vsketch.Vsketch) -> None:
    pass


def finalize(vsk: vsketch.Vsketch) -> None:
    vsk.vpype("linemerge linesort")
