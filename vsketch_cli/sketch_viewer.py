import asyncio
import pathlib
from typing import Any, Dict, Optional, Type, Union

import vpype_viewer
import watchgod
from PySide2.QtCore import Signal
from PySide2.QtWidgets import QSizePolicy, QVBoxLayout, QWidget

import vsketch

from .param_widget import ParamsWidget
from .seed_widget import SeedWidget
from .utils import execute_sketch, load_sketch_class


class SideBarWidget(QWidget):
    def __init__(self):
        super().__init__()

        self.seed_widget = SeedWidget()
        self.params_widget = ParamsWidget()
        spacer = QWidget()
        spacer.setSizePolicy(QSizePolicy.Minimum, QSizePolicy.Expanding)

        layout = QVBoxLayout()
        layout.addWidget(self.seed_widget)
        layout.addWidget(self.params_widget)
        layout.addWidget(spacer)
        self.setLayout(layout)


class SketchViewer(vpype_viewer.QtViewer):
    sketchFileChanged = Signal()

    def __init__(self, path: Union[str, pathlib.Path], *args: Any, **kwargs: Any):
        super().__init__(*args, **kwargs)

        self._sketch_class: Optional[Type[vsketch.Vsketch]] = None
        self._path = str(path)
        self._vsk: Optional[vsketch.Vsketch] = None
        self._vsk_master: Optional[vsketch.Vsketch] = None
        self._param_set: Dict[str, Any] = {}
        self._seed: Optional[int] = None

        self._task = asyncio.get_event_loop().create_task(self.watch())

        # noinspection PyUnresolvedReferences
        self.sketchFileChanged.connect(self.reload_sketch_class)  # type: ignore

        self._sidebar = SideBarWidget()
        self._sidebar.params_widget.paramUpdated.connect(self.redraw_sketch)  # type: ignore
        self._sidebar.seed_widget.seed_spin.valueChanged.connect(self.set_seed)
        self.add_side_widget(self._sidebar)

        self.reload_sketch_class()

    def __del__(self):
        self._task.cancel()

    def set_seed(self, seed: int) -> None:
        self._seed = seed
        self.redraw_sketch()

    def reload_sketch_class(self) -> None:
        # extract sketch class from script file
        self._sketch_class = load_sketch_class(self._path)

        # update UI to reflect declared parameter while attempting to save their previous
        # values
        if self._sketch_class is not None:
            # attempt to restore previous set of parameters
            if self._vsk is not None:
                self._sketch_class.set_param_set(self._vsk.param_set)

            params = self._sketch_class.get_params()
        else:
            params = {}
        self._sidebar.params_widget.set_params(params)

        # trigger redraw
        self.redraw_sketch()

    def redraw_sketch(self) -> None:
        self._vsk = execute_sketch(self._sketch_class, seed=self._seed, finalize=False)
        self.set_document(self._vsk.document if self._vsk else None)

    async def watch(self):
        try:
            async for changes in watchgod.awatch(self._path):
                # noinspection PyTypeChecker
                for change in changes:
                    if change[1] == self._path and change[0] == watchgod.Change.modified:
                        # noinspection PyUnresolvedReferences
                        self.sketchFileChanged.emit()
        except asyncio.CancelledError:
            pass
