from runpy import run_path

import vpype as vp
import watchgod
from PySide2.QtCore import Qt, QThread, Signal
from PySide2.QtWidgets import QApplication
from vpype_viewer.qtviewer import QtViewer

import vsketch


def execute_sketch(path: str) -> vp.Document:
    sketch = run_path(path)
    vsk = vsketch.Vsketch()
    sketch["setup"](vsk)
    sketch["draw"](vsk)
    sketch["finalize"](vsk)
    return vsk.document


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
                    doc = execute_sketch(self._path)
                    print(doc)
                    # noinspection PyUnresolvedReferences
                    self.document_changed.emit(doc)


def show(path: str) -> int:
    if not QApplication.instance():
        app = QApplication()
    else:
        app = QApplication.instance()
    app.setAttribute(Qt.AA_UseHighDpiPixmaps)

    doc = execute_sketch(path)
    widget = QtViewer(doc)
    sz = app.primaryScreen().availableSize()
    widget.move(int(sz.width() * 0.05), int(sz.height() * 0.1))
    widget.resize(int(sz.width() * 0.9), int(sz.height() * 0.8))

    # watch source file
    watcher = _WatcherThread(path)
    # noinspection PyUnresolvedReferences
    watcher.document_changed.connect(widget.set_document)

    watcher.start()
    widget.show()

    return app.exec_()


if __name__ == "__main__":
    show("/Users/hhip/src/vsketch/examples/simple_sketch/sketch.py")
