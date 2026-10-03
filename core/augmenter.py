import random
from PIL import Image


AUGMENTATION_KEYS = [
    "horizontal_flip",
    "vertical_flip",
    "rotate_90",
    "rotate_180",
    "rotate_270",
    "random_rotation",
]

LABEL_MAP = {
    "horizontal_flip": "horizontal",
    "vertical_flip": "vertical",
    "rotate_90": "rotate90",
    "rotate_180": "rotate180",
    "rotate_270": "rotate270",
    "random_rotation": "rotate",
}


def apply(img: Image.Image, key: str, rotation_min: int = -30, rotation_max: int = 30) -> Image.Image:
    if key == "horizontal_flip":
        return img.transpose(Image.FLIP_LEFT_RIGHT)
    if key == "vertical_flip":
        return img.transpose(Image.FLIP_TOP_BOTTOM)
    if key == "rotate_90":
        return img.rotate(90, expand=True)
    if key == "rotate_180":
        return img.rotate(180, expand=True)
    if key == "rotate_270":
        return img.rotate(270, expand=True)
    if key == "random_rotation":
        angle = random.uniform(rotation_min, rotation_max)
        return img.rotate(angle, expand=True, resample=Image.BICUBIC)
    return img


def label(key: str) -> str:
    return LABEL_MAP.get(key, key)


def enabled_keys(augmentations: dict) -> list[str]:
    return [k for k in AUGMENTATION_KEYS if augmentations.get(k, False)]


def generate_combo(enabled: list[str]) -> tuple[list[str], str]:
    """Pick a random non-empty subset of enabled augmentations."""
    if not enabled:
        return [], ""
    count = random.randint(1, min(3, len(enabled)))
    chosen = random.sample(enabled, count)
    tag = "_".join(label(k) for k in chosen)
    return chosen, tag


def build_augmented(
    img: Image.Image,
    enabled: list[str],
    random_mode: bool,
    rotation_min: int,
    rotation_max: int,
    count: int,
) -> list[tuple[Image.Image, str]]:
    """Return list of (augmented_image, label_tag) tuples."""
    results = []
    seen_tags: set[str] = set()

    if not enabled:
        return results

    if random_mode:
        attempts = 0
        while len(results) < count and attempts < count * 10:
            attempts += 1
            keys, tag = generate_combo(enabled)
            if tag in seen_tags:
                continue
            seen_tags.add(tag)
            out = img.copy()
            for k in keys:
                out = apply(out, k, rotation_min, rotation_max)
            results.append((out, tag))
        # fill remaining if not enough unique combos
        while len(results) < count:
            keys, tag = generate_combo(enabled)
            out = img.copy()
            for k in keys:
                out = apply(out, k, rotation_min, rotation_max)
            results.append((out, f"{tag}_{len(results)}"))
    else:
        # cycle through enabled augmentations
        for i in range(count):
            key = enabled[i % len(enabled)]
            out = apply(img.copy(), key, rotation_min, rotation_max)
            results.append((out, label(key)))

    return results
