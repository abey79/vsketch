import pathlib

import click
from PySide6.QtCore import Signal
from PySide6.QtWidgets import (
    QGroupBox,
    QHBoxLayout,
    QInputDialog,
    QLineEdit,
    QListWidget,
    QPushButton,
    QSizePolicy,
    QVBoxLayout,
)

from .utils import find_unique_path


class DeselectListWidget(QListWidget):
    def mousePressEvent(self, event):
        self.clearSelection()
        super().mousePressEvent(event)


class ConfigWidget(QGroupBox):
    saveConfig = Signal(str)
    loadConfig = Signal(str)

    def __init__(self, config_path: pathlib.Path):
        super().__init__("Configs")

        self._config_path = config_path

        self._config_list = DeselectListWidget()
        size_policy = self._config_list.sizePolicy()
        size_policy.setHorizontalPolicy(QSizePolicy.Policy.Minimum)
        self._config_list.setSizePolicy(size_policy)
        self._config_list.itemSelectionChanged.connect(  # type: ignore
            self.on_selection_changed
        )
        self.update_config_list()

        self._load_btn = QPushButton("Load")
        self._load_btn.setEnabled(False)
        self._load_btn.clicked.connect(self.on_load_btn)  # type: ignore
        save_btn = QPushButton("Save")
        save_btn.clicked.connect(self.on_save_btn)  # type: ignore
        self._delete_btn = QPushButton("Delete")
        self._delete_btn.setEnabled(False)
        self._delete_btn.clicked.connect(self.on_delete_btn)  # type: ignore

        btn_layout = QHBoxLayout()
        btn_layout.addWidget(self._delete_btn)
        btn_layout.addWidget(save_btn)
        btn_layout.addWidget(self._load_btn)

        layout = QVBoxLayout()
        layout.addWidget(self._config_list)
        layout.addLayout(btn_layout)
        self.setLayout(layout)

    def update_config_list(self) -> None:
        self._config_list.clear()
        self._config_list.addItems(
            [file.stem for file in sorted(self._config_path.glob("*.json"))]
        )

    def on_selection_changed(self) -> None:
        enabled = len(self._config_list.selectedItems()) == 1
        self._load_btn.setEnabled(enabled)
        self._delete_btn.setEnabled(enabled)

    def on_load_btn(self) -> None:
        if len(self._config_list.selectedItems()) != 1:
            return

        path = self._config_path / (self._config_list.selectedItems()[0].text() + ".json")
        if path.exists():
            # noinspection PyUnresolvedReferences
            self.loadConfig.emit(str(path))  # type: ignore
        else:
            click.echo(f"Config file {path} not found.", err=True)

    def on_save_btn(self) -> None:
        base_name, ok = QInputDialog.getText(
            self, "Config Name", "Enter the configuration name:", QLineEdit.EchoMode.Normal
        )

        if not ok:
            return

        path = find_unique_path(base_name + ".json", self._config_path)

        # noinspection PyUnresolvedReferences
        self.saveConfig.emit(str(path))  # type: ignore
        self.update_config_list()

    def on_delete_btn(self) -> None:
        for item in self._config_list.selectedItems():
            path = self._config_path / (item.text() + ".json")
            if path.exists():
                path.unlink()
        self.update_config_list()
