import asyncio
import functools
import pathlib
import sys

import qasync
from PySide2.QtCore import Qt
from qasync import QApplication, QEventLoop

from .sketch_viewer import SketchViewer


async def _show(path: str, second_screen: bool = False) -> int:
    def close_future(future, loop):
        loop.call_later(10, future.cancel)
        future.cancel()

    loop = asyncio.get_event_loop()
    future: asyncio.Future = asyncio.Future()

    if not QApplication.instance():
        app = QApplication()
    else:
        app = QApplication.instance()
    app.setAttribute(Qt.AA_UseHighDpiPixmaps)

    if hasattr(app, "aboutToQuit"):
        getattr(app, "aboutToQuit").connect(functools.partial(close_future, future, loop))

    # create widget
    widget = SketchViewer(pathlib.Path(path))

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
    await future
    return app.exec_()


def show(path: str, second_screen: bool = False) -> int:
    try:
        return qasync.run(_show(path, second_screen))
    except asyncio.exceptions.CancelledError:
        sys.exit(0)


if __name__ == "__main__":
    show("/Users/hhip/src/vsketch/examples/simple_sketch/sketch.py", second_screen=True)
