from pathlib import Path
from PIL import Image
import tempfile, sys

tmp = Path(tempfile.mkdtemp())
for i in range(3):
    img = Image.new("RGB", (100, 100), color=(i * 80, 100, 150))
    img.save(tmp / f"test_{i}.jpg")

from core.dataset_scanner import scan
from core.augmenter import enabled_keys, build_augmented
from utils.image_utils import open_corrected
from core.file_manager import resolve_output_dirs, copy_original, save_augmented

images = scan(tmp, False)
assert len(images) == 3, f"Expected 3, got {len(images)}"

aug_settings = {
    "horizontal_flip": True, "vertical_flip": True,
    "rotate_90": True, "rotate_180": False,
    "rotate_270": False, "random_rotation": True,
}
enabled = enabled_keys(aug_settings)
assert len(enabled) == 4

img = open_corrected(images[0])
results = build_augmented(img, enabled, True, -30, 30, 5)
assert len(results) == 5, f"Expected 5, got {len(results)}"

out_root = Path(tempfile.mkdtemp())
orig_dir, aug_dir = resolve_output_dirs(images[0], tmp, out_root, False)
copy_original(images[0], orig_dir)
assert (orig_dir / images[0].name).exists()

for idx, (aug_img, tag) in enumerate(results, 1):
    p = save_augmented(aug_img, images[0].stem, images[0].suffix, idx, tag, aug_dir, 95)
    assert p.exists(), f"Missing: {p}"
    aug_img.close()

img.close()
saved = list(aug_dir.iterdir())
assert len(saved) == 5, f"Expected 5 saved, got {len(saved)}"
print(f"All tests passed. Saved files: {[f.name for f in saved]}")
