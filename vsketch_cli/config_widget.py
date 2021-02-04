import pathlib

import typer
from PySide2.QtCore import Signal
from PySide2.QtWidgets import (
    QComboBox,
    QFormLayout,
    QGroupBox,
    QHBoxLayout,
    QInputDialog,
    QLineEdit,
    QPushButton,
    QVBoxLayout,
)


class ConfigWidget(QGroupBox):
    saveConfig = Signal(str)
    loadConfig = Signal(str)

    def __init__(self, config_path: pathlib.Path):
        super().__init__("Configs")

        self._config_path = config_path

        self._configs_combo = QComboBox()
        load_btn = QPushButton("Load")
        load_btn.clicked.connect(self.on_load_btn)
        save_btn = QPushButton("Save")
        save_btn.clicked.connect(self.on_save_btn)

        config_layout = QFormLayout()
        config_layout.addRow("Configs:", self._configs_combo)

        btn_layout = QHBoxLayout()
        btn_layout.addWidget(save_btn)
        btn_layout.addWidget(load_btn)

        layout = QVBoxLayout()
        layout.addLayout(config_layout)
        layout.addLayout(btn_layout)
        self.setLayout(layout)

    def update_config_list(self) -> None:
        self._configs_combo.clear()
        self._configs_combo.addItems(
            [file.stem for file in sorted(self._config_path.glob("*.json"))]
        )

    def on_load_btn(self) -> None:
        path = self._config_path / (self._configs_combo.currentText() + ".json")
        if path.exists():
            # noinspection PyUnresolvedReferences
            self.loadConfig.emit(str(path))  # type: ignore
        else:
            typer.echo(f"Config file {path} not found.", err=True)

    def on_save_btn(self) -> None:
        base_name, ok = QInputDialog.getText(
            self, "Config Name", "Enter the configuration name:", QLineEdit.Normal
        )

        if not ok:
            return

        # find unique name
        name = base_name
        index = 2
        while True:
            path = self._config_path / (name + ".json")
            if not path.exists():
                break
            name = base_name + "_" + str(index)
            index += 1

        # noinspection PyUnresolvedReferences
        self.saveConfig.emit(str(path))  # type: ignore
        self.update_config_list()
