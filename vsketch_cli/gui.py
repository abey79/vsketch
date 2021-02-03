import asyncio

from PySide2.QtCore import Qt
from PySide2.QtWidgets import QApplication
from qasync import QEventLoop

from .sketch_viewer import SketchViewer


def show(path: str, second_screen: bool = False) -> int:
    if not QApplication.instance():
        app = QApplication()
    else:
        app = QApplication.instance()
    app.setAttribute(Qt.AA_UseHighDpiPixmaps)

    # setup asyncio loop
    loop = QEventLoop(app)
    asyncio.set_event_loop(loop)

    # create widget
    widget = SketchViewer(path)

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
    return app.exec_()


if __name__ == "__main__":
    show("/Users/hhip/src/vsketch/examples/simple_sketch/sketch.py", second_screen=True)
