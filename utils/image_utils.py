from PIL import Image, ExifTags
from pathlib import Path

SUPPORTED_EXTENSIONS = {".jpg", ".jpeg", ".png", ".webp", ".bmp"}

EXIF_ORIENTATION_TAG = next(
    (k for k, v in ExifTags.TAGS.items() if v == "Orientation"), None
)

EXIF_ROTATION_MAP = {
    3: Image.ROTATE_180,
    6: Image.ROTATE_270,
    8: Image.ROTATE_90,
}


def is_supported(path: Path) -> bool:
    return path.suffix.lower() in SUPPORTED_EXTENSIONS


def open_corrected(path: Path) -> Image.Image:
    """Open image and apply EXIF orientation correction."""
    img = Image.open(path)
    img.load()
    try:
        exif = img._getexif()
        if exif and EXIF_ORIENTATION_TAG in exif:
            orientation = exif[EXIF_ORIENTATION_TAG]
            if orientation in EXIF_ROTATION_MAP:
                img = img.transpose(EXIF_ROTATION_MAP[orientation])
    except Exception:
        pass
    return img


def resize_for_preview(img: Image.Image, max_size: int = 400) -> Image.Image:
    img.thumbnail((max_size, max_size), Image.LANCZOS)
    return img


def save_image(img: Image.Image, path: Path, jpeg_quality: int = 95) -> None:
    ext = path.suffix.lower()
    if ext in (".jpg", ".jpeg"):
        rgb = img.convert("RGB") if img.mode in ("RGBA", "P") else img
        rgb.save(path, "JPEG", quality=jpeg_quality, subsampling=0)
    elif ext == ".png":
        img.save(path, "PNG")
    elif ext == ".webp":
        img.save(path, "WEBP", quality=jpeg_quality)
    elif ext == ".bmp":
        img.save(path, "BMP")
    else:
        img.save(path)


def unique_path(path: Path) -> Path:
    if not path.exists():
        return path
    stem, suffix, parent = path.stem, path.suffix, path.parent
    counter = 1
    while True:
        candidate = parent / f"{stem}_{counter}{suffix}"
        if not candidate.exists():
            return candidate
        counter += 1
