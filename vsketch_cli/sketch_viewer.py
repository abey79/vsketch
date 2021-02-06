import asyncio
import json
import pathlib
from typing import Any, Dict, Optional, Type

import vpype_viewer
import watchgod
from PySide2.QtCore import QThread, Signal
from PySide2.QtWidgets import QLabel, QPushButton, QSizePolicy, QVBoxLayout, QWidget

import vsketch

from .config_widget import ConfigWidget
from .param_widget import ParamsWidget
from .seed_widget import SeedWidget
from .threads import DocumentSaverThread, SketchRunnerThread
from .utils import canonical_name, find_unique_path, load_sketch_class


class StatusLabel(QLabel):
    def succeeded(self):
        self.setText('<span style="color:green"><b>Done</b></span>')

    def loading(self):
        self.setText("Loading...")

    def failed(self):
        self.setText('<span style="color:red"><b>ERROR (see console)</b></span>')


class SideBarWidget(QWidget):
    def __init__(self, config_path: pathlib.Path):
        super().__init__()

        self.seed_widget = SeedWidget()
        self.params_widget = ParamsWidget()
        self.config_widget = ConfigWidget(config_path)
        self.status_label = StatusLabel()
        self.like_btn = QPushButton("LIKE!")
        self.like_btn.setStyleSheet("padding: 15px; font-weight: bold;")
        self.like_btn.setEnabled(False)
        spacer = QWidget()
        spacer.setSizePolicy(QSizePolicy.Minimum, QSizePolicy.Expanding)

        layout = QVBoxLayout()
        layout.addWidget(self.seed_widget)
        layout.addWidget(self.params_widget)
        layout.addWidget(self.config_widget)
        layout.addWidget(spacer)
        layout.addWidget(self.status_label)
        layout.addWidget(self.like_btn)
        self.setLayout(layout)


class SketchViewer(vpype_viewer.QtViewer):
    sketchFileChanged = Signal()

    def __init__(self, path: pathlib.Path, *args: Any, **kwargs: Any):
        super().__init__(*args, **kwargs)

        self._sketch_class: Optional[Type[vsketch.Vsketch]] = None
        self._path = path
        self._vsk: Optional[vsketch.Vsketch] = None
        self._vsk_master: Optional[vsketch.Vsketch] = None
        self._param_set: Dict[str, Any] = {}
        self._seed: Optional[int] = None
        self._thread: Optional[QThread] = None

        self._task = asyncio.get_event_loop().create_task(self.watch())

        # noinspection PyUnresolvedReferences
        self.sketchFileChanged.connect(self.reload_sketch_class)  # type: ignore

        config_path = path.parent / "config"
        if not config_path.exists():
            config_path.mkdir()

        self._sidebar = SideBarWidget(config_path)
        self._sidebar.params_widget.paramUpdated.connect(self.redraw_sketch)  # type: ignore
        self._sidebar.seed_widget.seed_spin.valueChanged.connect(self.set_seed)
        self._seed = self._sidebar.seed_widget.seed_spin.value()
        self._sidebar.config_widget.saveConfig.connect(self.save_config)  # type: ignore
        self._sidebar.config_widget.loadConfig.connect(self.load_config)  # type: ignore
        self._sidebar.like_btn.clicked.connect(self.on_like)
        self.add_side_widget(self._sidebar)

        self._trigger_fit_to_viewport = True
        self.reload_sketch_class()

    def __del__(self):
        self._task.cancel()

    def set_seed(self, seed: int) -> None:
        self._seed = seed
        self.redraw_sketch()

    def save_config(self, path: str) -> None:
        if self._vsk is None:
            return

        param_set = self._vsk.param_set
        param_set["__seed__"] = self._seed
        with open(path, "w") as fp:
            json.dump(param_set, fp)

    def load_config(self, path: str) -> None:
        with open(path, "r") as fp:
            param_set = json.load(fp)
        seed = param_set.pop("__seed__", None)
        if seed is not None:
            self._seed = seed
        if self._sketch_class is not None:
            self._sketch_class.set_param_set(param_set)
            self.redraw_sketch()

    def on_like(self) -> None:
        if self._vsk is None:
            return

        base_name = canonical_name(self._path)
        path = find_unique_path(
            base_name + "_liked.svg", self._path.parent / "output", always_number=True
        )

        # launch saving process in a thread
        thread = DocumentSaverThread(path, self._vsk.document, self)
        self._sidebar.setEnabled(False)
        self._sidebar.like_btn.setText("saving...")
        thread.completed.connect(self.on_like_completed)
        thread.start()

    def on_like_completed(self) -> None:
        self._sidebar.setEnabled(True)
        self._sidebar.like_btn.setText("LIKE!")

    def reload_sketch_class(self) -> None:
        # extract sketch class from script file
        self._sketch_class = load_sketch_class(self._path)

        # update UI to reflect declared parameter while attempting to save their previous
        # values
        if self._sketch_class is not None:
            # attempt to restore previous set of parameters
            if self._vsk is not None:
                self._sketch_class.set_param_set(self._vsk.param_set)

            self._sidebar.params_widget.set_params(self._sketch_class.get_params())
        else:
            self._sidebar.params_widget.set_params({})

        # trigger redraw and updated status label
        self.redraw_sketch()

    def redraw_sketch(self) -> None:
        if self._sketch_class is None:
            self._sidebar.status_label.failed()
            self._sidebar.like_btn.setEnabled(False)
            return

        if self._thread is not None:
            self._thread.quit()
        self._thread = SketchRunnerThread(self._sketch_class, self._seed, parent=self)
        # noinspection PyUnresolvedReferences
        self._thread.completed.connect(self.redraw_sketch_completed)
        self._sidebar.status_label.loading()
        self._thread.start()

    def redraw_sketch_completed(self, vsk: vsketch.Vsketch) -> None:
        self._vsk = vsk
        self._thread = None

        if self._vsk is not None:
            self._sidebar.status_label.succeeded()
            self._sidebar.like_btn.setEnabled(True)
            self.set_document(self._vsk.document)

            if self._trigger_fit_to_viewport:
                self._viewer_widget.engine.fit_to_viewport()
                self._trigger_fit_to_viewport = False
        else:
            self._sidebar.status_label.failed()
            self._sidebar.like_btn.setEnabled(False)
            self.set_document(None)

    async def watch(self):
        try:
            async for changes in watchgod.awatch(self._path):
                # noinspection PyTypeChecker
                for change in changes:
                    if change[1] == str(self._path) and change[0] == watchgod.Change.modified:
                        # noinspection PyUnresolvedReferences
                        self.sketchFileChanged.emit()
        except asyncio.CancelledError:
            pass
