from PySide6.QtCore import QThread, Signal
from pathlib import Path
from utils.image_utils import open_corrected
from utils.logger import AugmentLogger
from core.augmenter import enabled_keys, build_augmented
from core.file_manager import resolve_output_dirs, copy_original, save_augmented
from core.dataset_scanner import scan


class AugmentationWorker(QThread):
    progress = Signal(int, int, int, str)   # percent, processed, generated, current_file
    finished = Signal(int, int, int)         # processed, generated, failed
    error_occurred = Signal(str)

    def __init__(self, settings: dict, parent=None):
        super().__init__(parent)
        self._settings = settings
        self._cancelled = False

    def cancel(self):
        self._cancelled = True

    def run(self):
        s = self._settings
        input_root = Path(s["input_folder"])
        output_root = Path(s["output_folder"])
        recursive = s["include_subfolders"]

        output_root.mkdir(parents=True, exist_ok=True)
        logger = AugmentLogger(output_root)

        images = scan(input_root, recursive)
        total = len(images)
        if total == 0:
            self.finished.emit(0, 0, 0)
            return

        enabled = enabled_keys(s["augmentations"])
        count = s["augmented_count"]
        random_mode = s["random_mode"]
        rot_min = s["rotation_min"]
        rot_max = s["rotation_max"]
        jpeg_quality = s["jpeg_quality"]
        copy_orig = s["copy_originals"]

        processed = 0
        generated = 0
        failed = 0

        for idx, img_path in enumerate(images):
            if self._cancelled:
                break

            self.progress.emit(
                int(idx / total * 100), idx, generated, img_path.name
            )

            try:
                img = open_corrected(img_path)
                orig_dir, aug_dir = resolve_output_dirs(img_path, input_root, output_root, recursive)

                if copy_orig:
                    copy_original(img_path, orig_dir)

                augmented_list = build_augmented(img, enabled, random_mode, rot_min, rot_max, count)
                for aug_idx, (aug_img, tag) in enumerate(augmented_list, start=1):
                    save_augmented(
                        aug_img,
                        img_path.stem,
                        img_path.suffix.lower(),
                        aug_idx,
                        tag,
                        aug_dir,
                        jpeg_quality,
                    )
                    generated += 1
                    aug_img.close()

                img.close()
                processed += 1

            except Exception as e:
                failed += 1
                logger.log_error(str(img_path), str(e))

        logger.finalize(processed, generated, failed)
        self.finished.emit(processed, generated, failed)
