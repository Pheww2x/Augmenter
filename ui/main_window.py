import os
import subprocess
from pathlib import Path

from PySide6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QLabel,
    QPushButton, QLineEdit, QCheckBox, QSpinBox, QProgressBar,
    QFileDialog, QMessageBox, QGroupBox, QScrollArea, QListWidget,
    QListWidgetItem, QSplitter, QFrame, QSizePolicy, QToolButton,
    QDialog, QDialogButtonBox,
)
from PySide6.QtCore import Qt, QSize, QThread
from PySide6.QtGui import QFont, QIcon, QPixmap, QColor

from ui.preview_widget import PreviewWidget
from ui.settings_dialog import SettingsDialog
from core.dataset_scanner import scan
from workers.augmentation_worker import AugmentationWorker
import utils.settings as app_settings

STYLE = """
QMainWindow, QWidget {
    background-color: #0f0f1a;
    color: #e0e0e0;
    font-family: 'Segoe UI', sans-serif;
    font-size: 13px;
}
QGroupBox {
    border: 1px solid #2a2a4a;
    border-radius: 6px;
    margin-top: 8px;
    padding: 8px;
    font-weight: bold;
    color: #7b8cde;
}
QGroupBox::title {
    subcontrol-origin: margin;
    left: 10px;
    padding: 0 4px;
}
QPushButton {
    background-color: #1e1e3a;
    color: #c0c8ff;
    border: 1px solid #3a3a6a;
    border-radius: 5px;
    padding: 6px 14px;
    font-size: 12px;
}
QPushButton:hover { background-color: #2a2a5a; border-color: #5a5aaa; }
QPushButton:pressed { background-color: #151530; }
QPushButton:disabled { color: #555; border-color: #222; }
QPushButton#start_btn {
    background-color: #2d5a27;
    color: #90ee90;
    border-color: #4a8a44;
    font-weight: bold;
    font-size: 13px;
    padding: 8px 20px;
}
QPushButton#start_btn:hover { background-color: #3a7a33; }
QPushButton#cancel_btn {
    background-color: #5a2020;
    color: #ffaaaa;
    border-color: #8a3333;
}
QPushButton#cancel_btn:hover { background-color: #7a2a2a; }
QLineEdit {
    background-color: #141428;
    border: 1px solid #2a2a4a;
    border-radius: 4px;
    padding: 5px 8px;
    color: #ddd;
}
QLineEdit:focus { border-color: #5a5aaa; }
QSpinBox {
    background-color: #141428;
    border: 1px solid #2a2a4a;
    border-radius: 4px;
    padding: 4px 6px;
    color: #ddd;
    min-width: 60px;
}
QSpinBox::up-button, QSpinBox::down-button { width: 16px; }
QCheckBox { spacing: 6px; color: #ccc; }
QCheckBox::indicator {
    width: 15px; height: 15px;
    border: 1px solid #4a4a7a;
    border-radius: 3px;
    background: #141428;
}
QCheckBox::indicator:checked {
    background-color: #4a4aaa;
    border-color: #7a7aee;
}
QProgressBar {
    border: 1px solid #2a2a4a;
    border-radius: 4px;
    background: #141428;
    text-align: center;
    color: #aaa;
    height: 18px;
}
QProgressBar::chunk { background-color: #4a4aaa; border-radius: 3px; }
QListWidget {
    background-color: #0d0d1f;
    border: 1px solid #2a2a4a;
    border-radius: 4px;
    color: #ccc;
    font-size: 12px;
}
QListWidget::item:selected { background-color: #2a2a5a; }
QListWidget::item:hover { background-color: #1a1a3a; }
QScrollBar:vertical {
    background: #0d0d1f; width: 8px; border-radius: 4px;
}
QScrollBar::handle:vertical { background: #3a3a6a; border-radius: 4px; min-height: 20px; }
QLabel#status_label { color: #aaa; font-size: 12px; }
QLabel#title_label {
    color: #7b8cde;
    font-size: 22px;
    font-weight: bold;
    letter-spacing: 2px;
}
QLabel#subtitle_label { color: #555; font-size: 11px; }
QFrame#separator { background-color: #2a2a4a; max-height: 1px; }
"""


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Augmenter — Automatic Image Augmentation")
        self.setMinimumSize(960, 700)
        self._settings = app_settings.load()
        self._images: list[Path] = []
        self._worker: AugmentationWorker | None = None
        self._setup_ui()
        self._load_settings_to_ui()
        self.setStyleSheet(STYLE)

    # ------------------------------------------------------------------ UI BUILD

    def _setup_ui(self):
        central = QWidget()
        self.setCentralWidget(central)
        root = QHBoxLayout(central)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(0)

        # Left panel (controls)
        left_scroll = QScrollArea()
        left_scroll.setWidgetResizable(True)
        left_scroll.setFixedWidth(380)
        left_scroll.setFrameShape(QFrame.Shape.NoFrame)
        left_scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)

        left_widget = QWidget()
        left_layout = QVBoxLayout(left_widget)
        left_layout.setContentsMargins(16, 16, 16, 16)
        left_layout.setSpacing(12)
        left_scroll.setWidget(left_widget)

        # Header
        title = QLabel("AUGMENTER")
        title.setObjectName("title_label")
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        subtitle = QLabel("Automatic Image Augmentation Tool")
        subtitle.setObjectName("subtitle_label")
        subtitle.setAlignment(Qt.AlignmentFlag.AlignCenter)
        left_layout.addWidget(title)
        left_layout.addWidget(subtitle)
        left_layout.addWidget(self._separator())

        # Input folder
        left_layout.addWidget(self._build_input_group())
        # Augmentation settings
        left_layout.addWidget(self._build_augmentation_group())
        # Output folder
        left_layout.addWidget(self._build_output_group())
        left_layout.addWidget(self._separator())

        # Action buttons
        btn_row = QHBoxLayout()
        self.preview_btn = QPushButton("Preview")
        self.preview_btn.clicked.connect(self._on_preview)
        self.settings_btn = QPushButton("⚙ Settings")
        self.settings_btn.clicked.connect(self._on_settings)
        self.start_btn = QPushButton("▶  START AUGMENTATION")
        self.start_btn.setObjectName("start_btn")
        self.start_btn.clicked.connect(self._on_start)
        btn_row.addWidget(self.preview_btn)
        btn_row.addWidget(self.settings_btn)
        btn_row.addStretch()
        btn_row.addWidget(self.start_btn)
        left_layout.addLayout(btn_row)

        # Progress
        left_layout.addWidget(self._build_progress_group())
        left_layout.addStretch()

        # Right panel (image list + preview)
        right_widget = QWidget()
        right_layout = QVBoxLayout(right_widget)
        right_layout.setContentsMargins(12, 16, 16, 16)
        right_layout.setSpacing(8)

        img_list_label = QLabel("Images in Folder")
        img_list_label.setStyleSheet("color: #7b8cde; font-weight: bold;")
        self.image_list = QListWidget()
        self.image_list.setMaximumHeight(160)
        self.image_list.currentItemChanged.connect(self._on_image_selected)

        self.preview_widget = PreviewWidget()
        self.preview_widget.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)

        right_layout.addWidget(img_list_label)
        right_layout.addWidget(self.image_list)
        right_layout.addWidget(self.preview_widget, stretch=1)

        root.addWidget(left_scroll)
        root.addWidget(self._vseparator())
        root.addWidget(right_widget, stretch=1)

    def _build_input_group(self) -> QGroupBox:
        group = QGroupBox("Input Dataset")
        layout = QVBoxLayout(group)
        layout.setSpacing(6)

        row = QHBoxLayout()
        self.input_edit = QLineEdit()
        self.input_edit.setPlaceholderText("Select input folder...")
        self.input_edit.setReadOnly(True)
        browse_btn = QPushButton("Browse")
        browse_btn.setFixedWidth(70)
        browse_btn.clicked.connect(self._browse_input)
        row.addWidget(self.input_edit)
        row.addWidget(browse_btn)
        layout.addLayout(row)

        self.images_found_label = QLabel("Images Found: 0")
        self.images_found_label.setStyleSheet("color: #7b8cde; font-size: 12px;")
        layout.addWidget(self.images_found_label)

        self.include_subfolders = QCheckBox("Include subfolders")
        self.include_subfolders.stateChanged.connect(self._rescan)
        layout.addWidget(self.include_subfolders)
        return group

    def _build_augmentation_group(self) -> QGroupBox:
        group = QGroupBox("Augmentation Settings")
        layout = QVBoxLayout(group)
        layout.setSpacing(6)

        self.aug_checks = {}
        aug_labels = [
            ("horizontal_flip", "Horizontal Flip"),
            ("vertical_flip", "Vertical Flip"),
            ("rotate_90", "Rotate 90°"),
            ("rotate_180", "Rotate 180°"),
            ("rotate_270", "Rotate 270°"),
            ("random_rotation", "Random Rotation"),
        ]
        for key, label in aug_labels:
            cb = QCheckBox(label)
            self.aug_checks[key] = cb
            layout.addWidget(cb)

        # Rotation range
        rot_row = QHBoxLayout()
        rot_row.setContentsMargins(20, 0, 0, 0)
        rot_row.addWidget(QLabel("Min:"))
        self.rot_min = QSpinBox()
        self.rot_min.setRange(-180, 0)
        self.rot_min.setValue(-30)
        self.rot_min.setSuffix("°")
        rot_row.addWidget(self.rot_min)
        rot_row.addWidget(QLabel("Max:"))
        self.rot_max = QSpinBox()
        self.rot_max.setRange(0, 180)
        self.rot_max.setValue(30)
        self.rot_max.setSuffix("°")
        rot_row.addWidget(self.rot_max)
        rot_row.addStretch()
        layout.addLayout(rot_row)

        layout.addWidget(self._separator())

        count_row = QHBoxLayout()
        count_row.addWidget(QLabel("Augmented images per original:"))
        self.aug_count = QSpinBox()
        self.aug_count.setRange(1, 100)
        self.aug_count.setValue(5)
        count_row.addWidget(self.aug_count)
        count_row.addStretch()
        layout.addLayout(count_row)

        self.random_mode = QCheckBox("Random Augmentation Mode")
        layout.addWidget(self.random_mode)
        return group

    def _build_output_group(self) -> QGroupBox:
        group = QGroupBox("Output Folder")
        layout = QVBoxLayout(group)
        row = QHBoxLayout()
        self.output_edit = QLineEdit()
        self.output_edit.setPlaceholderText("Select output folder...")
        self.output_edit.setReadOnly(True)
        browse_btn = QPushButton("Browse")
        browse_btn.setFixedWidth(70)
        browse_btn.clicked.connect(self._browse_output)
        row.addWidget(self.output_edit)
        row.addWidget(browse_btn)
        layout.addLayout(row)
        return group

    def _build_progress_group(self) -> QGroupBox:
        group = QGroupBox("Progress")
        layout = QVBoxLayout(group)
        layout.setSpacing(6)

        self.current_file_label = QLabel("Ready")
        self.current_file_label.setObjectName("status_label")
        layout.addWidget(self.current_file_label)

        self.progress_bar = QProgressBar()
        self.progress_bar.setValue(0)
        layout.addWidget(self.progress_bar)

        stats_row = QHBoxLayout()
        self.processed_label = QLabel("Processed: 0 / 0")
        self.generated_label = QLabel("Generated: 0")
        self.processed_label.setObjectName("status_label")
        self.generated_label.setObjectName("status_label")
        stats_row.addWidget(self.processed_label)
        stats_row.addStretch()
        stats_row.addWidget(self.generated_label)
        layout.addLayout(stats_row)

        btn_row = QHBoxLayout()
        self.cancel_btn = QPushButton("Cancel")
        self.cancel_btn.setObjectName("cancel_btn")
        self.cancel_btn.setEnabled(False)
        self.cancel_btn.clicked.connect(self._on_cancel)
        self.open_output_btn = QPushButton("Open Output Folder")
        self.open_output_btn.setEnabled(False)
        self.open_output_btn.clicked.connect(self._open_output)
        btn_row.addWidget(self.cancel_btn)
        btn_row.addStretch()
        btn_row.addWidget(self.open_output_btn)
        layout.addLayout(btn_row)
        return group

    def _separator(self) -> QFrame:
        f = QFrame()
        f.setObjectName("separator")
        f.setFrameShape(QFrame.Shape.HLine)
        return f

    def _vseparator(self) -> QFrame:
        f = QFrame()
        f.setFrameShape(QFrame.Shape.VLine)
        f.setStyleSheet("background-color: #2a2a4a; max-width: 1px;")
        return f

    # ------------------------------------------------------------------ SETTINGS LOAD/SAVE

    def _load_settings_to_ui(self):
        s = self._settings
        self.input_edit.setText(s.get("input_folder", ""))
        self.output_edit.setText(s.get("output_folder", ""))
        self.include_subfolders.setChecked(s.get("include_subfolders", True))
        self.aug_count.setValue(s.get("augmented_count", 5))
        self.random_mode.setChecked(s.get("random_mode", True))
        self.rot_min.setValue(s.get("rotation_min", -30))
        self.rot_max.setValue(s.get("rotation_max", 30))
        for key, cb in self.aug_checks.items():
            cb.setChecked(s.get("augmentations", {}).get(key, True))
        if s.get("input_folder"):
            self._rescan()

    def _collect_settings(self) -> dict:
        s = self._settings.copy()
        s["input_folder"] = self.input_edit.text()
        s["output_folder"] = self.output_edit.text()
        s["include_subfolders"] = self.include_subfolders.isChecked()
        s["augmented_count"] = self.aug_count.value()
        s["random_mode"] = self.random_mode.isChecked()
        s["rotation_min"] = self.rot_min.value()
        s["rotation_max"] = self.rot_max.value()
        s["augmentations"] = {k: cb.isChecked() for k, cb in self.aug_checks.items()}
        return s

    # ------------------------------------------------------------------ ACTIONS

    def _browse_input(self):
        folder = QFileDialog.getExistingDirectory(self, "Select Input Folder")
        if folder:
            self.input_edit.setText(folder)
            self._rescan()

    def _browse_output(self):
        folder = QFileDialog.getExistingDirectory(self, "Select Output Folder")
        if folder:
            self.output_edit.setText(folder)

    def _rescan(self):
        folder = self.input_edit.text()
        if not folder:
            return
        recursive = self.include_subfolders.isChecked()
        self._images = scan(Path(folder), recursive)
        self.images_found_label.setText(f"Images Found: {len(self._images)}")
        self._populate_image_list()

    def _populate_image_list(self):
        self.image_list.clear()
        for p in self._images[:500]:  # cap list at 500 for performance
            item = QListWidgetItem(p.name)
            item.setData(Qt.ItemDataRole.UserRole, str(p))
            self.image_list.addItem(item)

    def _on_image_selected(self, current, _previous):
        if current is None:
            return
        path = Path(current.data(Qt.ItemDataRole.UserRole))
        self.preview_widget.load_image(path, self._collect_settings())

    def _on_preview(self):
        item = self.image_list.currentItem()
        if item:
            path = Path(item.data(Qt.ItemDataRole.UserRole))
            self.preview_widget.load_image(path, self._collect_settings())
        elif self._images:
            self.preview_widget.load_image(self._images[0], self._collect_settings())

    def _on_settings(self):
        dlg = SettingsDialog(self._settings, self)
        if dlg.exec() == QDialog.DialogCode.Accepted:
            self._settings.update(dlg.get_values())
            app_settings.save(self._settings)

    def _on_start(self):
        s = self._collect_settings()

        # Validate
        input_path = Path(s["input_folder"]) if s["input_folder"] else None
        output_path = Path(s["output_folder"]) if s["output_folder"] else None

        if not input_path or not input_path.is_dir():
            QMessageBox.warning(self, "Validation Error", "Please select a valid input folder.")
            return
        if not output_path:
            QMessageBox.warning(self, "Validation Error", "Please select an output folder.")
            return
        if not self._images:
            QMessageBox.warning(self, "Validation Error", "No supported images found in the input folder.")
            return
        if not any(cb.isChecked() for cb in self.aug_checks.values()):
            QMessageBox.warning(self, "Validation Error", "Please enable at least one augmentation.")
            return
        try:
            output_path.mkdir(parents=True, exist_ok=True)
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Cannot create output folder:\n{e}")
            return

        app_settings.save(s)
        self._settings = s
        self._start_worker(s)

    def _start_worker(self, settings: dict):
        self._worker = AugmentationWorker(settings, self)
        self._worker.progress.connect(self._on_progress)
        self._worker.finished.connect(self._on_finished)

        self.start_btn.setEnabled(False)
        self.cancel_btn.setEnabled(True)
        self.open_output_btn.setEnabled(False)
        self.progress_bar.setValue(0)
        self.current_file_label.setText("Starting...")
        total = len(self._images)
        self.processed_label.setText(f"Processed: 0 / {total}")
        self.generated_label.setText("Generated: 0")

        self._worker.start()

    def _on_cancel(self):
        if self._worker:
            self._worker.cancel()
            self.cancel_btn.setEnabled(False)
            self.current_file_label.setText("Cancelling...")

    def _on_progress(self, percent: int, processed: int, generated: int, filename: str):
        self.progress_bar.setValue(percent)
        self.current_file_label.setText(f"Processing: {filename}")
        total = len(self._images)
        self.processed_label.setText(f"Processed: {processed} / {total}")
        self.generated_label.setText(f"Generated: {generated}")

    def _on_finished(self, processed: int, generated: int, failed: int):
        self.start_btn.setEnabled(True)
        self.cancel_btn.setEnabled(False)
        self.open_output_btn.setEnabled(True)
        self.progress_bar.setValue(100)

        total = processed + generated
        msg = (
            f"<b>Augmentation Complete!</b><br><br>"
            f"Original Images: {processed}<br>"
            f"Augmented Images: {generated}<br>"
            f"Total Images: {processed + generated}<br>"
        )
        if failed:
            msg += f"<br>Failed: {failed} (see augmentation_log.txt)"

        cancelled = self._worker and self._worker._cancelled
        if cancelled:
            self.current_file_label.setText(f"Cancelled — Processed: {processed}, Generated: {generated}")
        else:
            self.current_file_label.setText(f"Done — {processed} processed, {generated} generated")

        dlg = QMessageBox(self)
        dlg.setWindowTitle("Augmentation Complete" if not cancelled else "Augmentation Cancelled")
        dlg.setTextFormat(Qt.TextFormat.RichText)
        dlg.setText(msg)
        dlg.setIcon(QMessageBox.Icon.Information)
        open_btn = dlg.addButton("Open Output Folder", QMessageBox.ButtonRole.ActionRole)
        dlg.addButton(QMessageBox.StandardButton.Close)
        dlg.exec()
        if dlg.clickedButton() == open_btn:
            self._open_output()

        self._worker = None

    def _open_output(self):
        folder = self.output_edit.text()
        if folder and Path(folder).exists():
            os.startfile(folder)

    def closeEvent(self, event):
        app_settings.save(self._collect_settings())
        if self._worker and self._worker.isRunning():
            self._worker.cancel()
            self._worker.wait(3000)
        super().closeEvent(event)
