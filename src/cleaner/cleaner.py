from __future__ import annotations

import os
import shutil
from dataclasses import dataclass
from pathlib import Path

from rich.console import Console
from rich.table import Table

from cleaner.rules import CleaningRule
from cleaner.scanner import humanize_size, scan_directory

__all__ = ["CleanItem", "scan_rules", "total_summary", "execute_clean", "delete_path"]


@dataclass(frozen=True)
class CleanItem:
    rule_name: str
    label: str
    path: Path
    human_size: str
    total_bytes: int
    file_count: int
    dir_count: int


def scan_rules(rules: list[CleaningRule]) -> list[CleanItem]:
    """Scan all rules and return CleanItem summaries."""
    items: list[CleanItem] = []
    for rule in rules:
        result = scan_directory(rule.name, rule.path)
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
    return items


def total_summary(items: list[CleanItem]) -> tuple[str, int, int, int]:
    """Return (human_total, total_bytes, total_files, total_dirs)."""
    total_bytes = sum(item.total_bytes for item in items)
    total_files = sum(item.file_count for item in items)
    total_dirs = sum(item.dir_count for item in items)
    return humanize_size(total_bytes), total_bytes, total_files, total_dirs


def delete_path(path: Path) -> None:
    """Delete a path. Skip symlinks. Use `shutil.rmtree` for dirs, `os.unlink` for files.

    Re-raise OSError so caller handles it.
    """
    if not path.exists():
        return
    if path.is_symlink():
        return
    if path.is_dir():
        shutil.rmtree(path)
    else:
        os.unlink(path)


def execute_clean(
    items: list[CleanItem],
    force: bool,
    yes: bool,
    console: Console,
) -> bool:
    """Execute cleaning.

    flow:
      - If not force → print dry-run table, return False.
      - If force and not yes → print summary, prompt "(yes/no): ", delete if confirmed.
      - If force and yes → delete immediately.
      - On deletion: iterate items, try delete_path each. On OSError, print red error, continue.

    Returns True if any deletion was attempted (even with errors), False otherwise.
    """
    human_total, total_bytes, total_files, total_dirs = total_summary(items)

    if not force:
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
        response = console.input(
            f"Delete {human_total} across {total_files} files and {total_dirs} dirs? "
            "This cannot be undone. (yes/no): "
        )
        if response.strip().lower() not in {"y", "yes"}:
            return False

    attempted = False
    for item in items:
        attempted = True
        try:
            delete_path(item.path)
            console.print(f"✓ Deleted {item.label} ({item.human_size})")
        except OSError as exc:
            console.print(
                f"[red]✗ Failed to delete {item.label}: {exc}[/red]",
            )

    return attempted
