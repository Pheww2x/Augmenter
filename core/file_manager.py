from pathlib import Path
import shutil
from utils.image_utils import unique_path, save_image
from PIL import Image


def resolve_output_dirs(
    image_path: Path,
    input_root: Path,
    output_root: Path,
    recursive: bool,
) -> tuple[Path, Path]:
    """Return (original_dir, augmented_dir) for a given image."""
    if recursive:
        relative = image_path.parent.relative_to(input_root)
        base = output_root / relative
    else:
        base = output_root

    original_dir = base / "original"
    augmented_dir = base / "augmented"
    original_dir.mkdir(parents=True, exist_ok=True)
    augmented_dir.mkdir(parents=True, exist_ok=True)
    return original_dir, augmented_dir


def copy_original(image_path: Path, original_dir: Path) -> None:
    dest = unique_path(original_dir / image_path.name)
    shutil.copy2(image_path, dest)


def save_augmented(
    img: Image.Image,
    stem: str,
    suffix: str,
    index: int,
    tag: str,
    augmented_dir: Path,
    jpeg_quality: int,
) -> Path:
    naming = f"{stem}_aug_{index:03d}_{tag}{suffix}" if tag else f"{stem}_aug_{index:03d}{suffix}"
    dest = unique_path(augmented_dir / naming)
    save_image(img, dest, jpeg_quality)
    return dest
