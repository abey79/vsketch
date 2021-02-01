import asyncio

import vpype as vp
import watchgod
from PySide2.QtCore import QObject, Qt, Signal
from PySide2.QtWidgets import QApplication
from qasync import QEventLoop
from vpype_viewer.qtviewer import QtViewer

from .utils import execute_sketch


class _FileWatcher(QObject):
    document_changed = Signal(vp.Document)

    # noinspection PyUnresolvedReferences
    async def watch_file(self, path: str):
        try:
            async for changes in watchgod.awatch(path):
                for change in changes:
                    if change[1] == path and change[0] == watchgod.Change.modified:
                        self.document_changed.emit(execute_sketch(path, finalize=False))
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
    watcher = _FileWatcher()
    task = loop.create_task(watcher.watch_file(path))
    # noinspection PyUnresolvedReferences
    watcher.document_changed.connect(widget.set_document)

    # run and exit gracefully
    status_code = app.exec_()
    task.cancel()
    return status_code


if __name__ == "__main__":
    show("/Users/hhip/src/vsketch/examples/simple_sketch/sketch.py")
