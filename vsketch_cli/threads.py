import pathlib
from traceback import format_exc
from typing import Any, Optional, Type

import vpype as vp
from PySide2.QtCore import QThread, Signal

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
        **kwargs: Any,
    ):
        super().__init__(*args, **kwargs)
        self._path = path
        self._document = document

    def run(self) -> None:
        with open(self._path, "w") as fp:
            vp.write_svg(fp, self._document, color_mode="layer")
        # noinspection PyUnresolvedReferences
        self.completed.emit()  # type: ignore
        self.deleteLater()
