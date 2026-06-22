from __future__ import annotations

import os
import sys
from dataclasses import dataclass
from pathlib import Path

__all__ = [
    "ScanResult",
    "humanize_size",
    "parse_size",
    "scan_directory",
    "is_excluded",
]


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


def parse_size(value: str) -> int:
    """Parse a human-readable size string (e.g. '10MB', '1.5 GB') into bytes."""
    text = value.strip().upper().replace(" ", "")
    if not text:
        raise ValueError("Size cannot be empty")

    units = {
        "B": 1,
        "KB": 1024,
        "MB": 1024**2,
        "GB": 1024**3,
        "TB": 1024**4,
    }

    for suffix, multiplier in sorted(units.items(), key=lambda item: -len(item[0])):
        if text.endswith(suffix):
            number = text[: -len(suffix)]
            try:
                return int(float(number) * multiplier)
            except ValueError as exc:
                raise ValueError(f"Invalid size value: {value}") from exc

    try:
        return int(text)
    except ValueError as exc:
        raise ValueError(f"Invalid size value: {value}") from exc


def is_excluded(path: Path, exclude_paths: set[Path]) -> bool:
    """Return True if path is under any excluded path."""
    resolved = path.resolve()
    for excluded in exclude_paths:
        try:
            resolved.relative_to(excluded.resolve())
            return True
        except ValueError:
            continue
    return False


def _entry_size(entry: os.DirEntry[str]) -> int:
    try:
        if entry.is_symlink():
            return 0
        stat = entry.stat(follow_symlinks=False)
        if stat.st_mode & 0o170000 == 0o040000:
            return 0
        return stat.st_size
    except OSError:
        return 0


def _scan_tree(
    path: Path,
    exclude_paths: set[Path],
) -> tuple[int, int, int]:
    """Recursively scan using os.scandir with cached stat."""
    total_bytes = 0
    file_count = 0
    dir_count = 0

    try:
        with os.scandir(path) as entries:
            for entry in entries:
                entry_path = Path(entry.path)
                if is_excluded(entry_path, exclude_paths):
                    continue

                try:
                    if entry.is_symlink(follow_symlinks=False):
                        continue

                    if entry.is_dir(follow_symlinks=False):
                        dir_count += 1
                        sub_bytes, sub_files, sub_dirs = _scan_tree(entry_path, exclude_paths)
                        total_bytes += sub_bytes
                        file_count += sub_files
                        dir_count += sub_dirs
                    elif entry.is_file(follow_symlinks=False):
                        size = _entry_size(entry)
                        total_bytes += size
                        file_count += 1
                except OSError as exc:
                    print(
                        f"Warning: cannot access {entry_path}: {exc}",
                        file=sys.stderr,
                    )
    except OSError as exc:
        print(f"Warning: cannot access {path}: {exc}", file=sys.stderr)

    return total_bytes, file_count, dir_count


def scan_directory(
    rule_name: str,
    path: Path,
    exclude_paths: set[Path] | None = None,
) -> ScanResult:
    """Recursively scan a directory.

    Rules:
      - Skip symlinks entirely (don't follow, don't count).
      - Catch OSError on individual items; continue, log warning to stderr.
      - Count files, count subdirectories (exclude top-level path in dir_count).
      - Sum file sizes.
      - If path does not exist, return zeros.
      - If path is a file, return its size with file_count=1.
    """
    excludes = exclude_paths or set()

    if is_excluded(path, excludes):
        return ScanResult(rule_name, path, 0, 0, 0)

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

    total_bytes, file_count, dir_count = _scan_tree(path, excludes)
    return ScanResult(rule_name, path, total_bytes, file_count, dir_count)
