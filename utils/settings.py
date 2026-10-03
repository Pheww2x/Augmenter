import json
from pathlib import Path

SETTINGS_FILE = Path.home() / ".augmenter_settings.json"

DEFAULTS = {
    "input_folder": "",
    "output_folder": "",
    "include_subfolders": True,
    "augmentations": {
        "horizontal_flip": True,
        "vertical_flip": True,
        "rotate_90": True,
        "rotate_180": True,
        "rotate_270": True,
        "random_rotation": True,
    },
    "rotation_min": -30,
    "rotation_max": 30,
    "augmented_count": 5,
    "random_mode": True,
    "jpeg_quality": 95,
    "copy_originals": True,
    "naming_format": "aug",
}


def load() -> dict:
    if SETTINGS_FILE.exists():
        try:
            with open(SETTINGS_FILE, "r") as f:
                data = json.load(f)
            merged = DEFAULTS.copy()
            merged.update(data)
            merged["augmentations"] = {**DEFAULTS["augmentations"], **data.get("augmentations", {})}
            return merged
        except Exception:
            pass
    return DEFAULTS.copy()


def save(settings: dict) -> None:
    try:
        with open(SETTINGS_FILE, "w") as f:
            json.dump(settings, f, indent=2)
    except Exception:
        pass
