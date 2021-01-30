import asyncio

import vpype as vp
import watchgod
from PySide2.QtCore import Qt, QThread, Signal
from PySide2.QtWidgets import QApplication
from qasync import QEventLoop
from vpype_viewer.qtviewer import QtViewer

from .utils import execute_sketch


class _WatcherThread(QThread):
    document_changed = Signal(vp.Document)

    def __init__(self, path: str, parent=None):
        QThread.__init__(self, parent)

        self._path = path

    def run(self):
        for changes in watchgod.watch(self._path):
            for change in changes:
                if change[1] == self._path and change[0] == watchgod.Change.modified:
                    print("Modified)")
                    doc = execute_sketch(self._path, finalize=False)
                    print(doc)
                    # noinspection PyUnresolvedReferences
                    self.document_changed.emit(doc)


async def watch_file(path: str):
    try:
        async for changes in watchgod.awatch(path):
            for change in changes:
                if change[1] == path and change[0] == watchgod.Change.modified:
                    print("Modified")
    except asyncio.CancelledError:
        pass


def show(path: str) -> int:
    if not QApplication.instance():
        app = QApplication()
    else:
        app = QApplication.instance()
    app.setAttribute(Qt.AA_UseHighDpiPixmaps)

    # setup asyncio loop
    loop = QEventLoop(app)
    asyncio.set_event_loop(loop)

    doc = execute_sketch(path, finalize=False)
    widget = QtViewer(doc)
    sz = app.primaryScreen().availableSize()
    widget.move(int(sz.width() * 0.05), int(sz.height() * 0.1))
    widget.resize(int(sz.width() * 0.9), int(sz.height() * 0.8))

    # show widget and monitor path
    widget.show()
    task = loop.create_task(watch_file(path))

    # run and exit gracefully
    status_code = app.exec_()
    task.cancel()
    return status_code


if __name__ == "__main__":
    show("/Users/hhip/src/vsketch/examples/simple_sketch/sketch.py")
