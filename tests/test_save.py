def test_save_hpgl(vsk, tmp_path):
    dest = tmp_path / "output.hpgl"
    vsk.size("a4", center=False)
    vsk.rect(10, 10, 100, 200)
    vsk.save(str(dest), "hp7475a")

    assert dest.read_text().startswith("IN;DF;")


def test_save_svg(vsk, tmp_path):
    dest = tmp_path / "output.svg"
    vsk.size("a4", center=False)
    vsk.rect(10, 10, 100, 200)
    vsk.save(str(dest))

    assert dest.read_text().startswith("<?xml")
