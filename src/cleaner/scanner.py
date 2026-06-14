import os
import sys
from dataclasses import dataclass
from pathlib import Path

__all__ = ["ScanResult", "humanize_size", "scan_directory"]


@dataclass(frozen=True)
class ScanResult:
    rule_name: str
    path: Path
    total_bytes: int
    file_count: int
    dir_count: int


def humanize_size(size_bytes: int) -> str:
    """Convert bytes to human-readable string (base 1024, 1 decimal place above KB)."""
    if size_bytes == 0:
        return "0 B"
    if size_bytes < 1024:
        return f"{size_bytes} B"

    units = ["KB", "MB", "GB", "TB"]
    size = float(size_bytes)
    for unit in units:
        size /= 1024
        if size < 1024 or unit == "TB":
            return f"{size:.1f} {unit}"
    return f"{size:.1f} TB"


def scan_directory(rule_name: str, path: Path) -> ScanResult:
    """Recursively scan a directory.

    Rules:
      - Skip symlinks entirely (don't follow, don't count).
      - Catch OSError on individual items; continue, log warning to stderr.
      - Count files, count subdirectories (exclude top-level path in dir_count).
      - Sum file sizes.
      - If path does not exist, return ScanResult with total_bytes=0, file_count=0, dir_count=0.
      - If path is not a directory, return ScanResult with total_bytes=file_size, file_count=1, dir_count=0.
    """
    if not path.exists():
        return ScanResult(rule_name, path, 0, 0, 0)

    if not path.is_dir():
        try:
            if path.is_symlink():
                return ScanResult(rule_name, path, 0, 0, 0)
            size = path.stat().st_size
            return ScanResult(rule_name, path, size, 1, 0)
        except OSError as exc:
            print(f"Warning: cannot access {path}: {exc}", file=sys.stderr)
            return ScanResult(rule_name, path, 0, 0, 0)

    total_bytes = 0
    file_count = 0
    dir_count = 0

    for root, dirs, files in os.walk(path, followlinks=False):
        root_path = Path(root)

        filtered_dirs: list[str] = []
        for dirname in dirs:
            dir_path = root_path / dirname
            if dir_path.is_symlink():
                continue
            try:
                if dir_path.is_dir():
                    dir_count += 1
                    filtered_dirs.append(dirname)
            except OSError as exc:
                print(f"Warning: cannot access {dir_path}: {exc}", file=sys.stderr)
        dirs[:] = filtered_dirs

        for filename in files:
            file_path = root_path / filename
            if file_path.is_symlink():
                continue
            try:
                total_bytes += file_path.stat().st_size
                file_count += 1
            except OSError as exc:
                print(f"Warning: cannot access {file_path}: {exc}", file=sys.stderr)

    return ScanResult(rule_name, path, total_bytes, file_count, dir_count)
