import asyncio
import pathlib
from typing import Union

import vpype as vp
from PySide2.QtCore import QObject, Qt, Signal
from PySide2.QtWidgets import QApplication
from qasync import QEventLoop
from vpype_viewer.qtviewer import QtViewer

from .sketch_runner import SketchRunner


class QtSketchRunner(QObject):
    document_changed = Signal(vp.Document)

    def __init__(self, path: Union[str, pathlib.Path], **kwargs):
        super().__init__(**kwargs)
        self.runner = SketchRunner(path, post_load_callback=self._post_load)

    def _post_load(self, runner: SketchRunner) -> None:
        # noinspection PyUnresolvedReferences
        self.document_changed.emit(runner.run())


def show(path: str, second_screen: bool = False) -> int:
    if not QApplication.instance():
        app = QApplication()
    else:
        app = QApplication.instance()
    app.setAttribute(Qt.AA_UseHighDpiPixmaps)

    # setup asyncio loop
    loop = QEventLoop(app)
    asyncio.set_event_loop(loop)

    sketch_runner = QtSketchRunner(path)
    widget = QtViewer(sketch_runner.runner.run())

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

    widget.show()

    task = loop.create_task(sketch_runner.runner.watch())
    # noinspection PyUnresolvedReferences
    sketch_runner.document_changed.connect(widget.set_document)

    # run and exit gracefully
    status_code = app.exec_()
    task.cancel()
    return status_code


if __name__ == "__main__":
    show("/Users/hhip/src/vsketch/examples/simple_sketch/sketch.py", second_screen=True)
