import pathlib
from traceback import format_exc
from typing import Any, Optional, Type

import vpype as vp
import watchfiles
from PySide6.QtCore import QThread, Signal

import vsketch


class SketchRunnerThread(QThread):
    completed = Signal(vsketch.SketchClass)

    def __init__(
        self,
        sketch_class: Type[vsketch.SketchClass],
        seed: Optional[int],
        *args: Any,
        **kwargs: Any,
    ):
        super().__init__(*args, **kwargs)
        self._sketch_class = sketch_class
        self._seed = seed

    def run(self) -> None:
        sketch = None
        try:
            sketch = self._sketch_class.execute(seed=self._seed, finalize=False)
        except Exception as err:
            print(f"Unexpected error when running sketch: {err}\n{format_exc()}")
        if not self.isInterruptionRequested():
            # noinspection PyUnresolvedReferences
            self.completed.emit(sketch)  # type: ignore


class DocumentSaverThread(QThread):
    completed = Signal()

    def __init__(
        self,
        path: pathlib.Path,
        document: vp.Document,
        *args: Any,
        source: str = "",
        **kwargs: Any,
    ):
        super().__init__(*args, **kwargs)
        self._path = path
        self._document = document
        self._source = source

    def run(self) -> None:
        with open(self._path, "w") as fp:
            vp.write_svg(
                fp,
                self._document,
                source_string=self._source,
                use_svg_metadata=True,
            )
        # noinspection PyUnresolvedReferences
        self.completed.emit()  # type: ignore
        self.deleteLater()


class FileWatcherThread(QThread):
    sketchFileChanged = Signal()

    def __init__(self, path: pathlib.Path, *args: Any, **kwargs: Any):
        super().__init__(*args, **kwargs)
        self._path = path
        self._stop = False

    def is_set(self) -> bool:
        return self.isInterruptionRequested()

    def run(self):
        for changes in watchfiles.watch(self._path, stop_event=self):
            # noinspection PyTypeChecker
            for change in changes:
                if (
                    pathlib.Path(change[1]) == self._path
                    and change[0] == watchfiles.Change.modified
                ):
                    # noinspection PyUnresolvedReferences
                    self.sketchFileChanged.emit()
