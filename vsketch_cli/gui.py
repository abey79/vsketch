import pathlib
from typing import Optional

from PySide6.QtCore import Qt
from PySide6.QtWidgets import QApplication
from vpype_viewer.qtviewer.utils import set_sigint_handler

from .sketch_viewer import SketchViewer


def show(
    path: pathlib.Path, output_dir: Optional[pathlib.Path], second_screen: bool = False
) -> int:
    if not QApplication.instance():
        app = QApplication()
    else:
        app = QApplication.instance()  # type: ignore
    app.setAttribute(Qt.ApplicationAttribute.AA_UseHighDpiPixmaps)

    # create widget
    widget = SketchViewer(path, output_dir)

    # handle window sizing
    screens = app.screens()
    if second_screen and len(screens) > 1:
        widget.windowHandle().setScreen(screens[1])
        r = screens[1].geometry()
        widget.move(r.topLeft())
        widget.resize(r.width(), r.height())
    else:
        sz = app.primaryScreen().availableSize()
        widget.move(int(sz.width() * 0.05), int(sz.height() * 0.1))
        widget.resize(int(sz.width() * 0.9), int(sz.height() * 0.8))

    # run
    widget.show()

    # noinspection PyUnusedLocal
    def sigint_handler(signum, frame):
        QApplication.quit()

    with set_sigint_handler(sigint_handler):
        res = app.exec_()

    return res


if __name__ == "__main__":
    show(
        pathlib.Path("/Users/hhip/src/vsketch/examples/simple_sketch/sketch.py"),
        output_dir=None,
        second_screen=True,
    )
