import json
import pathlib
from traceback import format_exc
from typing import Any, Optional, Type

import vpype as vp
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
        sketch: vsketch.SketchClass,
        *args: Any,
        **kwargs: Any,
    ):
        super().__init__(*args, **kwargs)
        self._path = path
        self._sketch = sketch

    def run(self) -> None:
        document = self._sketch.vsk.document
        params = self._sketch.param_set
        params["__seed__"] = self._sketch.vsk.random_seed
        with open(self._path, "w") as fp:
            vp.write_svg(fp, document, source_string=json.dumps(params))
        # noinspection PyUnresolvedReferences
        self.completed.emit()  # type: ignore
        self.deleteLater()
