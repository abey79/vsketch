import random

from PySide6.QtWidgets import QFormLayout, QGroupBox, QPushButton, QSpinBox

_MAX_SEED = 2**31 - 1


class SeedWidget(QGroupBox):
    def __init__(self, *args, **kwargs):
        super().__init__("Seed", *args, **kwargs)

        self.seed_spin = QSpinBox()
        self.seed_spin.setRange(0, _MAX_SEED)
        randomize_btn = QPushButton("Randomize")
        randomize_btn.clicked.connect(self.randomize_seed)  # type: ignore

        layout = QFormLayout()
        layout.addRow("Seed:", self.seed_spin)
        layout.addRow("", randomize_btn)
        self.setLayout(layout)

    def randomize_seed(self):
        self.seed_spin.setValue(random.randint(0, _MAX_SEED))
