from pathlib import Path
from utils.image_utils import is_supported


def scan(folder: Path, recursive: bool = True) -> list[Path]:
    """Return list of supported image paths in folder."""
    if not folder.is_dir():
        return []
    pattern = "**/*" if recursive else "*"
    return [p for p in folder.glob(pattern) if p.is_file() and is_supported(p)]
