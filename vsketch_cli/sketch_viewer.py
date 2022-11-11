import asyncio
import json
import pathlib
from typing import Any, Dict, Optional, Type

import vpype_viewer
import watchfiles
from PySide6.QtCore import QThread, Signal
from PySide6.QtGui import QKeySequence, QShortcut
from PySide6.QtWidgets import (
    QLabel,
    QPushButton,
    QScrollArea,
    QSizePolicy,
    QVBoxLayout,
    QWidget,
)

import vsketch

from .config_widget import ConfigWidget
from .param_widget import ParamsWidget
from .seed_widget import SeedWidget
from .threads import DocumentSaverThread, SketchRunnerThread
from .utils import canonical_name, find_unique_path, get_config_path, load_sketch_class


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
        spacer.setSizePolicy(QSizePolicy.Minimum, QSizePolicy.MinimumExpanding)

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

        self._sketch_class: Optional[Type[vsketch.SketchClass]] = None
        self._sketch: Optional[vsketch.SketchClass] = None
        self._path = path.resolve(strict=True)  # make sure the path has no symlink
        self._param_set: Dict[str, Any] = {}
        self._seed: Optional[int] = None
        self._thread: Optional[QThread] = None
        self._stop_event = asyncio.Event()

        self._task = asyncio.get_event_loop().create_task(self.watch())

        # noinspection PyUnresolvedReferences
        self.sketchFileChanged.connect(self.reload_sketch_class)  # type: ignore

        self._sidebar = SideBarWidget(get_config_path(self._path))
        self._sidebar.params_widget.paramUpdated.connect(self.redraw_sketch)  # type: ignore
        self._sidebar.seed_widget.seed_spin.valueChanged.connect(self.set_seed)  # type: ignore
        self._seed = self._sidebar.seed_widget.seed_spin.value()
        self._sidebar.config_widget.saveConfig.connect(self.save_config)  # type: ignore
        self._sidebar.config_widget.loadConfig.connect(self.load_config)  # type: ignore
        self._sidebar.like_btn.clicked.connect(self.on_like)  # type: ignore

        scroller = QScrollArea()
        scroller.setWidget(self._sidebar)
        scroller.setWidgetResizable(True)
        sp = scroller.sizePolicy()
        sp.setHorizontalPolicy(QSizePolicy.Minimum)
        scroller.setSizePolicy(sp)
        self.add_side_widget(scroller)

        likeShortcut = QShortcut(QKeySequence("S"), self)
        likeShortcut.activated.connect(self.on_like)  # type: ignore

        randomizeShortcut = QShortcut(QKeySequence("R"), self)
        randomizeShortcut.activated.connect(  # type: ignore
            self._sidebar.seed_widget.randomize_seed
        )

        self._trigger_fit_to_viewport = True
        self.reload_sketch_class()

    def __del__(self):
        self._stop_event.set()
        self._task.cancel()

    def set_seed(self, seed: int) -> None:
        self._seed = seed
        self.redraw_sketch()

    def closeEvent(self, event):
        self._stop_event.set()
        self._task.cancel()

    def save_config(self, path: str) -> None:
        if self._sketch is None:
            return

        param_set = self._sketch.param_set
        param_set["__seed__"] = self._seed
        with open(path, "w") as fp:
            json.dump(param_set, fp)

    def load_config(self, path: str) -> None:
        with open(path, "r") as fp:
            param_set = json.load(fp)
        seed = param_set.pop("__seed__", None)
        if seed is not None:
            self._seed = seed

        if self._sketch is not None:
            self._sketch.set_param_set(param_set)
            self._sidebar.params_widget.update_from_param()
        self.redraw_sketch()

    def on_like(self) -> None:
        if self._sketch is None:
            return

        base_name = canonical_name(self._path)
        path = find_unique_path(
            base_name + "_liked.svg", self._path.parent / "output", always_number=True
        )

        self._sketch.ensure_finalized()

        # launch saving process in a thread
        thread = DocumentSaverThread(path, self._sketch.vsk.document, self)
        self._sidebar.setEnabled(False)
        self._sidebar.like_btn.setText("saving...")
        thread.completed.connect(self.on_like_completed)  # type: ignore
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
            if self._sketch is not None:
                self._sketch_class.set_param_set(self._sketch.param_set)

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
            self._thread.requestInterruption()
        self._thread = SketchRunnerThread(self._sketch_class, self._seed, parent=self)
        # noinspection PyUnresolvedReferences
        self._thread.completed.connect(self.redraw_sketch_completed)  # type: ignore
        self._sidebar.status_label.loading()
        self._thread.start()

    def redraw_sketch_completed(self, sketch: vsketch.SketchClass) -> None:
        self._sketch = sketch
        self._thread = None

        if self._sketch is not None:
            self._sidebar.status_label.succeeded()
            self._sidebar.like_btn.setEnabled(True)
            self.set_document(self._sketch.vsk.document)

            if self._trigger_fit_to_viewport:
                self._viewer_widget.engine.fit_to_viewport()
                self._trigger_fit_to_viewport = False
        else:
            self._sidebar.status_label.failed()
            self._sidebar.like_btn.setEnabled(False)
            self.set_document(None)

    async def watch(self):
        try:
            async for changes in watchfiles.awatch(self._path, stop_event=self._stop_event):
                # noinspection PyTypeChecker
                for change in changes:
                    if (
                        pathlib.Path(change[1]) == self._path
                        and change[0] == watchfiles.Change.modified
                    ):
                        # noinspection PyUnresolvedReferences
                        self.sketchFileChanged.emit()
        except asyncio.CancelledError:
            pass
