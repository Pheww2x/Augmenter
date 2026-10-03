from PySide6.QtWidgets import QWidget, QLabel, QVBoxLayout, QHBoxLayout, QSizePolicy
from PySide6.QtGui import QPixmap, QImage
from PySide6.QtCore import Qt
from PIL import Image
from utils.image_utils import open_corrected, resize_for_preview
from core.augmenter import enabled_keys, apply
from pathlib import Path
import random


def pil_to_pixmap(img: Image.Image) -> QPixmap:
    img = img.convert("RGBA")
    data = img.tobytes("raw", "RGBA")
    qimg = QImage(data, img.width, img.height, QImage.Format.Format_RGBA8888)
    return QPixmap.fromImage(qimg)


class ImagePanel(QWidget):
    def __init__(self, title: str, parent=None):
        super().__init__(parent)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(4)

        self.title_label = QLabel(title)
        self.title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.title_label.setStyleSheet("color: #aaa; font-size: 11px;")

        self.image_label = QLabel()
        self.image_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.image_label.setMinimumSize(200, 200)
        self.image_label.setStyleSheet("background: #1a1a2e; border: 1px solid #333; border-radius: 4px;")
        self.image_label.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)

        layout.addWidget(self.title_label)
        layout.addWidget(self.image_label)

    def set_pixmap(self, pixmap: QPixmap):
        scaled = pixmap.scaled(
            self.image_label.size(),
            Qt.AspectRatioMode.KeepAspectRatio,
            Qt.TransformationMode.SmoothTransformation,
        )
        self.image_label.setPixmap(scaled)

    def clear(self):
        self.image_label.clear()
        self.image_label.setText("No image")
        self.image_label.setStyleSheet(
            "background: #1a1a2e; border: 1px solid #333; border-radius: 4px; color: #555;"
        )


class PreviewWidget(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self._current_path: Path | None = None
        self._original_img: Image.Image | None = None

        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(8)

        self.original_panel = ImagePanel("Original")
        self.augmented_panel = ImagePanel("Augmented Preview")

        layout.addWidget(self.original_panel)
        layout.addWidget(self.augmented_panel)

    def load_image(self, path: Path, settings: dict):
        try:
            self._current_path = path
            if self._original_img:
                self._original_img.close()
            self._original_img = open_corrected(path)
            preview = self._original_img.copy()
            resize_for_preview(preview, 380)
            self.original_panel.set_pixmap(pil_to_pixmap(preview))
            preview.close()
            self.update_augmented_preview(settings)
        except Exception:
            self.original_panel.clear()
            self.augmented_panel.clear()

    def update_augmented_preview(self, settings: dict):
        if self._original_img is None:
            return
        try:
            enabled = enabled_keys(settings.get("augmentations", {}))
            if not enabled:
                self.augmented_panel.clear()
                return
            key = random.choice(enabled)
            aug = apply(
                self._original_img.copy(),
                key,
                settings.get("rotation_min", -30),
                settings.get("rotation_max", 30),
            )
            resize_for_preview(aug, 380)
            self.augmented_panel.set_pixmap(pil_to_pixmap(aug))
            aug.close()
        except Exception:
            self.augmented_panel.clear()

    def clear(self):
        if self._original_img:
            self._original_img.close()
            self._original_img = None
        self._current_path = None
        self.original_panel.clear()
        self.augmented_panel.clear()
