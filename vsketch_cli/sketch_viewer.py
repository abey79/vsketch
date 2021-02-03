import asyncio
import inspect
import pathlib
from runpy import run_path
from typing import Any, Dict, Optional, Type, Union

import vpype_viewer
import watchgod
from PySide2.QtCore import Signal

import vsketch

from .param_widget import ParamsWidget


class SketchViewer(vpype_viewer.QtViewer):
    sketchFileChanged = Signal()

    def __init__(self, path: Union[str, pathlib.Path], *args, **kwargs):
        super().__init__(*args, **kwargs)

        self._sketch_class: Optional[Type[vsketch.Vsketch]] = None
        self._path = str(path)
        self._vsk: Optional[vsketch.Vsketch] = None
        self._vsk_master: Optional[vsketch.Vsketch] = None
        self._param_set: Dict[str, Any] = {}
        self._seed: Optional[int] = None

        self._task = asyncio.get_event_loop().create_task(self.watch())

        # noinspection PyUnresolvedReferences
        self.sketchFileChanged.connect(self.reload_sketch_class)

        self._params_widget = ParamsWidget()
        self._params_widget.paramUpdated.connect(self.redraw_sketch)
        self.add_side_widget(self._params_widget)

        self.reload_sketch_class()

    def __del__(self):
        self._task.cancel()

    def reload_sketch_class(self) -> None:
        # extract sketch class from script file
        self._sketch_class = None
        sketch_scripts = run_path(self._path)
        for cls in sketch_scripts.values():
            if inspect.isclass(cls) and issubclass(cls, vsketch.Vsketch):
                self._sketch_class = cls

        # update UI to reflect declared parameter while attempting to save their previous
        # values
        if self._sketch_class is not None:
            # attempt to restore previous set of parameters
            if self._vsk is not None:
                self._sketch_class.set_param_set(self._vsk.param_set)

            params = self._sketch_class.get_params()
        else:
            params = {}
        self._params_widget.set_params(params)

        # trigger redraw
        self.redraw_sketch()

    def redraw_sketch(self) -> None:
        if self._sketch_class is not None:
            self._vsk = self._sketch_class()
            if self._seed is not None:
                self._vsk.randomSeed(self._seed)
                self._vsk.noiseSeed(self._seed)
            self._vsk.draw()
            self.set_document(self._vsk.document)
        else:
            self.set_document(None)

    def create_sketch(self) -> Optional[vsketch.Vsketch]:
        sketch_scripts = run_path(self._path)
        for cls in sketch_scripts.values():
            if inspect.isclass(cls) and issubclass(cls, vsketch.Vsketch):
                return cls()
        return None

    async def watch(self):
        try:
            async for changes in watchgod.awatch(self._path):
                for change in changes:
                    if change[1] == self._path and change[0] == watchgod.Change.modified:
                        # noinspection PyUnresolvedReferences
                        self.sketchFileChanged.emit()
        except asyncio.CancelledError:
            pass
