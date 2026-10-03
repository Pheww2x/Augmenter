from pathlib import Path
from datetime import datetime


class AugmentLogger:
    def __init__(self, output_dir: Path):
        self.log_path = output_dir / "augmentation_log.txt"
        self.errors: list[str] = []
        output_dir.mkdir(parents=True, exist_ok=True)
        with open(self.log_path, "w") as f:
            f.write(f"Augmenter Log - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
            f.write("=" * 60 + "\n\n")

    def log_error(self, filepath: str, error: str) -> None:
        entry = f"[ERROR] {filepath}: {error}"
        self.errors.append(entry)
        with open(self.log_path, "a") as f:
            f.write(entry + "\n")

    def log_info(self, message: str) -> None:
        with open(self.log_path, "a") as f:
            f.write(f"[INFO] {message}\n")

    def finalize(self, processed: int, generated: int, failed: int) -> None:
        with open(self.log_path, "a") as f:
            f.write(f"\n{'=' * 60}\n")
            f.write(f"Processed: {processed}\nGenerated: {generated}\nFailed: {failed}\n")
