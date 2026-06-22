from __future__ import annotations

import json
import os
import shutil
import time
from dataclasses import dataclass
from pathlib import Path

from rich.console import Console
from rich.progress import Progress, SpinnerColumn, TextColumn
from rich.table import Table

from cleaner.rules import CleaningRule
from cleaner.scanner import humanize_size, scan_directory

__all__ = [
    "CleanItem",
    "DeleteResult",
    "scan_rules",
    "total_summary",
    "execute_clean",
    "delete_path",
    "move_to_trash",
]


@dataclass(frozen=True)
class CleanItem:
    rule_name: str
    label: str
    path: Path
    human_size: str
    total_bytes: int
    file_count: int
    dir_count: int


@dataclass(frozen=True)
class DeleteResult:
    bytes_freed: int
    success: bool
    error: str | None = None
    partial: bool = False


def scan_rules(
    rules: list[CleaningRule],
    exclude_paths: set[Path] | None = None,
    *,
    console: Console | None = None,
    show_progress: bool = False,
) -> list[CleanItem]:
    """Scan all rules and return CleanItem summaries."""
    items: list[CleanItem] = []
    excludes = exclude_paths or set()

    progress_ctx = (
        Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=console,
            transient=True,
        )
        if show_progress and console is not None
        else None
    )

    if progress_ctx is not None:
        progress_ctx.start()

    try:
        for rule in rules:
            if progress_ctx is not None:
                progress_ctx.add_task(f"Scanning {rule.label}...", total=None)
            result = scan_directory(rule.name, rule.path, excludes)
            items.append(
                CleanItem(
                    rule_name=rule.name,
                    label=rule.label,
                    path=rule.path,
                    human_size=humanize_size(result.total_bytes),
                    total_bytes=result.total_bytes,
                    file_count=result.file_count,
                    dir_count=result.dir_count,
                )
            )
    finally:
        if progress_ctx is not None:
            progress_ctx.stop()

    return items


def total_summary(items: list[CleanItem]) -> tuple[str, int, int, int]:
    """Return (human_total, total_bytes, total_files, total_dirs)."""
    total_bytes = sum(item.total_bytes for item in items)
    total_files = sum(item.file_count for item in items)
    total_dirs = sum(item.dir_count for item in items)
    return humanize_size(total_bytes), total_bytes, total_files, total_dirs


def _file_size(path: Path) -> int:
    try:
        if path.is_symlink() or not path.is_file():
            return 0
        return path.stat().st_size
    except OSError:
        return 0


def _dir_contents_size(path: Path, exclude_paths: set[Path]) -> int:
    from cleaner.scanner import is_excluded

    total = 0
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
                        total += _dir_contents_size(entry_path, exclude_paths)
                    elif entry.is_file(follow_symlinks=False):
                        total += entry.stat(follow_symlinks=False).st_size
                except OSError:
                    continue
    except OSError:
        pass
    return total


def move_to_trash(path: Path) -> None:
    """Move a file or directory into ~/.Trash with a unique name."""
    trash_dir = Path.home() / ".Trash"
    trash_dir.mkdir(parents=True, exist_ok=True)
    timestamp = int(time.time())
    destination = trash_dir / f"cleaner-{timestamp}-{path.name}"
    counter = 1
    while destination.exists():
        destination = trash_dir / f"cleaner-{timestamp}-{counter}-{path.name}"
        counter += 1
    shutil.move(str(path), str(destination))


def delete_path(
    path: Path,
    exclude_paths: set[Path] | None = None,
    use_trash: bool = False,
) -> DeleteResult:
    """Delete a path. Skip symlinks.

    For directories: clears contents recursively, but preserves the directory
    itself unless use_trash is True (then the whole directory is moved).
    """
    from cleaner.scanner import is_excluded

    excludes = exclude_paths or set()

    if not path.exists() or path.is_symlink():
        return DeleteResult(bytes_freed=0, success=True)

    if is_excluded(path, excludes):
        return DeleteResult(bytes_freed=0, success=True)

    if use_trash:
        if path.is_dir():
            bytes_freed = 0
            failures = 0
            try:
                entries = list(os.scandir(path))
            except OSError as exc:
                return DeleteResult(bytes_freed=0, success=False, error=str(exc))

            for entry in entries:
                entry_path = Path(entry.path)
                if is_excluded(entry_path, excludes) or entry.is_symlink(follow_symlinks=False):
                    continue
                try:
                    if entry.is_dir(follow_symlinks=False):
                        size = _dir_contents_size(entry_path, excludes)
                    else:
                        size = entry.stat(follow_symlinks=False).st_size
                    move_to_trash(entry_path)
                    bytes_freed += size
                except OSError:
                    failures += 1

            if failures:
                return DeleteResult(
                    bytes_freed=bytes_freed,
                    success=False,
                    partial=bytes_freed > 0,
                    error=f"{failures} item(s) could not be moved to Trash",
                )
            return DeleteResult(bytes_freed=bytes_freed, success=True)

        size = _file_size(path)
        try:
            move_to_trash(path)
            return DeleteResult(bytes_freed=size, success=True)
        except OSError as exc:
            return DeleteResult(bytes_freed=0, success=False, error=str(exc))

    if path.is_dir():
        bytes_freed = 0
        failures = 0
        try:
            entries = list(os.scandir(path))
        except OSError as exc:
            return DeleteResult(bytes_freed=0, success=False, error=str(exc))

        for entry in entries:
            entry_path = Path(entry.path)
            if is_excluded(entry_path, excludes):
                continue
            if entry.is_symlink(follow_symlinks=False):
                continue
            try:
                if entry.is_dir(follow_symlinks=False):
                    sub_size = _dir_contents_size(entry_path, excludes)
                    shutil.rmtree(entry_path)
                    bytes_freed += sub_size
                else:
                    size = entry.stat(follow_symlinks=False).st_size
                    os.unlink(entry_path)
                    bytes_freed += size
            except OSError:
                failures += 1

        if failures:
            return DeleteResult(
                bytes_freed=bytes_freed,
                success=False,
                partial=bytes_freed > 0,
                error=f"{failures} item(s) could not be deleted",
            )
        return DeleteResult(bytes_freed=bytes_freed, success=True)

    size = _file_size(path)
    try:
        os.unlink(path)
        return DeleteResult(bytes_freed=size, success=True)
    except OSError as exc:
        return DeleteResult(bytes_freed=0, success=False, error=str(exc))


def _items_to_json(items: list[CleanItem]) -> list[dict]:
    return [
        {
            "rule_name": item.rule_name,
            "label": item.label,
            "path": str(item.path),
            "human_size": item.human_size,
            "total_bytes": item.total_bytes,
            "file_count": item.file_count,
            "dir_count": item.dir_count,
            "item_count": item.file_count + item.dir_count,
        }
        for item in items
    ]


def _print_json(payload: dict) -> None:
    print(json.dumps(payload, indent=2))


def execute_clean(
    items: list[CleanItem],
    force: bool,
    yes: bool,
    console: Console,
    *,
    quiet: bool = False,
    json_output: bool = False,
    use_trash: bool = False,
    sort_by_size: bool = False,
    exclude_paths: set[Path] | None = None,
) -> bool:
    """Execute cleaning.

    Returns True if any deletion was attempted (even with errors), False otherwise.
    """
    if sort_by_size:
        items = sorted(items, key=lambda item: item.total_bytes, reverse=True)

    human_total, total_bytes, total_files, total_dirs = total_summary(items)
    excludes = exclude_paths or set()

    if not force:
        if json_output:
            _print_json(
                {
                    "mode": "dry-run",
                    "items": _items_to_json(items),
                    "total_bytes": total_bytes,
                    "total_human": human_total,
                    "total_files": total_files,
                    "total_dirs": total_dirs,
                    "total_items": total_files + total_dirs,
                }
            )
            return False

        if not quiet:
            table = Table(title="Cleaner — Dry Run Preview")
            table.add_column("Category", style="cyan", justify="left")
            table.add_column("Path", style="dim", justify="left")
            table.add_column("Size", style="green", justify="right")
            table.add_column("Items", justify="right")

            for item in items:
                table.add_row(
                    item.label,
                    str(item.path),
                    item.human_size,
                    str(item.file_count + item.dir_count),
                )

            table.add_section()
            table.add_row(
                "Total",
                "",
                human_total,
                str(total_files + total_dirs),
                style="bold",
            )
            console.print(table)
            console.print("Dry run — nothing deleted. Use --force to clean.")
        return False

    if not yes:
        prompt = (
            f"Delete {human_total} across {total_files + total_dirs} items? "
            "This cannot be undone. (yes/no): "
        )
        if use_trash:
            prompt = (
                f"Move {human_total} across {total_files + total_dirs} items to Trash? (yes/no): "
            )
        response = console.input(prompt)
        if response.strip().lower() not in {"y", "yes"}:
            return False

    attempted = False
    results: list[dict] = []
    total_freed = 0

    for item in items:
        attempted = True
        delete_result = delete_path(item.path, excludes, use_trash=use_trash)
        total_freed += delete_result.bytes_freed

        if json_output:
            results.append(
                {
                    "rule_name": item.rule_name,
                    "label": item.label,
                    "path": str(item.path),
                    "scanned_bytes": item.total_bytes,
                    "bytes_freed": delete_result.bytes_freed,
                    "success": delete_result.success,
                    "partial": delete_result.partial,
                    "error": delete_result.error,
                }
            )
            continue

        if quiet:
            if not delete_result.success:
                console.print(
                    f"[red]✗ Failed to delete {item.label}: {delete_result.error}[/red]",
                )
            continue

        if delete_result.success:
            freed = humanize_size(delete_result.bytes_freed)
            action = "Moved to Trash" if use_trash else "Deleted"
            console.print(f"✓ {action} {item.label} ({freed})")
            if delete_result.partial:
                console.print(
                    f"[yellow]  Partial: {delete_result.error}[/yellow]",
                )
        else:
            console.print(
                f"[red]✗ Failed to delete {item.label}: {delete_result.error}[/red]",
            )

    if json_output:
        _print_json(
            {
                "mode": "trash" if use_trash else "delete",
                "results": results,
                "total_freed_bytes": total_freed,
                "total_freed_human": humanize_size(total_freed),
            }
        )

    return attempted
