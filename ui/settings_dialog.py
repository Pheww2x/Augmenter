from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QSpinBox,
    QCheckBox, QDialogButtonBox, QGroupBox, QFormLayout,
)
from PySide6.QtCore import Qt


class SettingsDialog(QDialog):
    def __init__(self, settings: dict, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Settings")
        self.setMinimumWidth(340)
        self.setModal(True)
        self._build_ui(settings)

    def _build_ui(self, s: dict):
        layout = QVBoxLayout(self)
        layout.setSpacing(12)

        # Output group
        out_group = QGroupBox("Output")
        out_form = QFormLayout(out_group)

        self.jpeg_quality = QSpinBox()
        self.jpeg_quality.setRange(1, 100)
        self.jpeg_quality.setValue(s.get("jpeg_quality", 95))
        out_form.addRow("JPEG Quality (1–100):", self.jpeg_quality)

        self.copy_originals = QCheckBox("Copy originals to output folder")
        self.copy_originals.setChecked(s.get("copy_originals", True))
        out_form.addRow(self.copy_originals)

        layout.addWidget(out_group)

        # Buttons
        buttons = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel
        )
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)

    def get_values(self) -> dict:
        return {
            "jpeg_quality": self.jpeg_quality.value(),
            "copy_originals": self.copy_originals.isChecked(),
        }
