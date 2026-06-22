# Cleaner CLI — AI Development Spec

> **Goal:** Build a macOS system cache & temp file cleaner CLI in Python.
> **Safety:** Dry-run by default. Deletion requires `--force`. Confirmation requires `--yes`.
> **Tech:** Python 3.10+, Click, Rich, pytest.

---

## 1. Project Structure (Final)

```
cleaner-cli/
├── pyproject.toml
├── src/
│   └── cleaner/
│       ├── __init__.py
│       ├── __main__.py        # Entry point: python -m cleaner
│       ├── cli.py             # Click commands & all flags
│       ├── scanner.py         # Directory walking, size calc, permission check
│       ├── cleaner.py         # Dry-run / deletion logic with confirmation
│       └── rules.py           # Cleaning category definitions (paths, descriptions)
└── tests/
    ├── conftest.py            # Shared fixtures
    ├── test_scanner.py
    ├── test_cleaner.py
    ├── test_rules.py
    └── test_cli.py
```

---

## 2. pyproject.toml

Create this *exact* file:

```toml
[build-system]
requires = ["hatchling"]
build-backend = "hatchling.build"

[project]
name = "cleaner"
version = "0.1.0"
description = "macOS system cache & temp file cleaner CLI"
requires-python = ">=3.10"
dependencies = [
    "click>=8.0",
    "rich>=13.0",
]

[project.scripts]
cleaner = "cleaner.cli:main"

[tool.pytest.ini_options]
testpaths = ["tests"]
pythonpath = ["src"]
```

---

## 3. src/cleaner/__init__.py

```python
"""Cleaner CLI — macOS system cache & temp file cleaner."""
__version__ = "0.1.0"
```

---

## 4. src/cleaner/rules.py

### Purpose
Defines cleaning categories: target path, description. Exposed as `CleaningRule` dataclasses.

### Types

```python
from dataclasses import dataclass
from pathlib import Path
import tempfile

@dataclass(frozen=True)
class CleaningRule:
    name: str          # machine-readable id, e.g. "caches"
    label: str         # human-readable, e.g. "User Caches"
    path: Path         # filesystem path
    description: str   # shown in help
```

### Functions — **exact signatures**

```python
def get_all_rules() -> list[CleaningRule]:
    """Return all defined rules in fixed order."""

def resolve_rules(flag_names: set[str]) -> list[CleaningRule]:
    """Resolve selected flags to CleaningRule list.
    
    - If `flag_names` contains "all", return all rules.
    - Otherwise, return rules matching the flag names in definition order.
    - Raise ValueError for unknown flag names.
    - Raise ValueError if flag_names is empty.
    """
```

### Implementation Details

```python
def get_all_rules() -> list[CleaningRule]:
    home = Path.home()
    tmpdir = Path(tempfile.gettempdir())
    return [
        CleaningRule(
            "caches",
            "User Caches",
            home / "Library/Caches",
            "Application and system user caches",
        ),
        CleaningRule(
            "logs",
            "User Logs",
            home / "Library/Logs",
            "Application and user log files",
        ),
        CleaningRule(
            "tmp",
            "Temp Files",
            tmpdir,
            "User temporary files",
        ),
        CleaningRule(
            "trash",
            "Trash",
            home / ".Trash",
            "Items in the Trash",
        ),
        CleaningRule(
            "xcode",
            "Xcode DerivedData",
            home / "Library/Developer/Xcode/DerivedData",
            "Xcode build artifacts and indexes",
        ),
    ]
```

### Acceptance Criteria
- `get_all_rules()` returns exactly 5 rules.
- `resolve_rules({"all"})` returns all 5 in definition order.
- `resolve_rules({"caches", "logs"})` returns 2 in definition order.
- `resolve_rules({"bogus"})` raises `ValueError("Unknown cleaning flags: bogus")`.
- `resolve_rules(set())` raises `ValueError`.
- `rules.py` has `__all__ = ["CleaningRule", "get_all_rules", "resolve_rules"]`.

---

## 5. src/cleaner/scanner.py

### Purpose
Recursively walk directories, calculate total byte size, count files & directories. Skip symlinks. Skip unreadable items. Handle non-existent paths gracefully.

### Types

```python
from dataclasses import dataclass
from pathlib import Path

@dataclass(frozen=True)
class ScanResult:
    rule_name: str
    path: Path
    total_bytes: int
    file_count: int
    dir_count: int
```

### Functions — **exact signatures**

```python
def humanize_size(size_bytes: int) -> str:
    """Convert bytes to human-readable string (base 1024, 1 decimal place above KB)."""

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
```

### `humanize_size` Logic

| Range | Format |
|-------|--------|
| 0 bytes | `"0 B"` |
| < 1024 | `"N B"` (integer) |
| < 1024² | `"N.N KB"` (1 decimal) |
| < 1024³ | `"N.N MB"` (1 decimal) |
| ≥ 1024³ | `"N.N GB"` (1 decimal) |

Example: `512 → "512 B"`, `1500 → "1.5 KB"`, `1500000 → "1.4 MB"`.

### `scan_directory` Walk Logic

Use `os.walk` (or `pathlib.rglob`) with `followlinks=False`. Top-down is fine.

For directories, count the directory itself as a `dir_count` (excluding the root path). For files, add size to `total_bytes` and increment `file_count`.

### Acceptance Criteria
- `humanize_size(0) == "0 B"`
- `humanize_size(1024) == "1.0 KB"`
- `humanize_size(1_073_741_824) == "1.0 GB"`
- Scanning a dir with 2 files and 1 subdir → `file_count=2, dir_count=1`.
- Symlinked files/symlinked dirs inside scanned path are skipped.
- Non-existent path returns all zeros silently.
- Permission errors on files/subdirs are caught silently with a stderr warning.

---

## 6. src/cleaner/cleaner.py

### Purpose
Orchestrates scanning + dry-run/delete execution.

### Types

```python
from dataclasses import dataclass
from pathlib import Path

@dataclass(frozen=True)
class CleanItem:
    rule_name: str
    label: str
    path: Path
    human_size: str
    total_bytes: int
    file_count: int
    dir_count: int
```

### Functions — **exact signatures**

```python
from cleaner.rules import CleaningRule
from cleaner.scanner import scan_directory, humanize_size
from rich.console import Console
from rich.table import Table

def scan_rules(rules: list[CleaningRule]) -> list[CleanItem]:
    """Scan all rules and return CleanItem summaries."""

def total_summary(items: list[CleanItem]) -> tuple[str, int, int, int]:
    """Return (human_total, total_bytes, total_files, total_dirs)."""

def delete_path(path: Path) -> None:
    """Delete a path. Skip symlinks. Use `shutil.rmtree` for dirs, `os.unlink` for files.
    Re-raise OSError so caller handles it."""

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
```

### Dry-Run Table Format

Use `rich.table.Table(title="Cleaner — Dry Run Preview")`.

Columns:
| Column | Style | Justify |
|---|---|---|
| Category | cyan | left |
| Path | dim | left |
| Size | green | right |
| Items | default | right |

A row for each `CleanItem` where `Items = file_count + dir_count`.
Add a separator, then a `Total` row with bold style.

After the table:
```
Dry run — nothing deleted. Use --force to clean.
```

### Force + Confirmation Prompt

Print:
```
Delete <human_total> across <N> files and <M> dirs? This cannot be undone. (yes/no):
```

Accept `y`, `yes`, `Y`, `YES` (case-insensitive). Reject everything else.

### Force + Yes

Print per-item progress like:
```
✓ Deleted User Caches (2.3 GB)
```

If error:
```
✗ Failed to delete Xcode DerivedData: Permission denied
```

### `total_summary` Formula

```python
total_bytes = sum(item.total_bytes for item in items)  # Add total_bytes to CleanItem in implementation
# Or: map CleanItem to include raw bytes; for now derive from path or add raw_bytes field.
```

Actually, add `total_bytes: int` to `CleanItem` so summary works:

```python
@dataclass(frozen=True)
class CleanItem:
    rule_name: str
    label: str
    path: Path
    human_size: str
    total_bytes: int   # raw bytes
    file_count: int
    dir_count: int
```

### Acceptance Criteria
- `execute_clean(items, force=False, ...)` prints table, returns `False`.
- `execute_clean(items, force=True, yes=False)` asks confirmation; returns `False` if user says no.
- `execute_clean(items, force=True, yes=True)` deletes immediately, returns `True`.
- If one `delete_path` fails, remaining items still processed.
- `total_summary` returns correct totals.
- Symlinks inside paths are never deleted (enforced by `delete_path` skipping symlinks).

---

## 7. src/cleaner/cli.py

### Purpose
Click CLI definition. **This is the only file with Click code.**

```python
import click
from rich.console import Console

from cleaner import __version__
from cleaner.rules import resolve_rules, get_all_rules
from cleaner.cleaner import execute_clean, scan_rules

@click.command(name="cleaner")
@click.version_option(version=__version__, prog_name="cleaner")
@click.option("--caches", is_flag=True, help="Clean ~/Library/Caches")
@click.option("--logs", is_flag=True, help="Clean ~/Library/Logs")
@click.option("--tmp", is_flag=True, help="Clean temp files ($TMPDIR)")
@click.option("--trash", is_flag=True, help="Empty the Trash")
@click.option("--xcode", is_flag=True, help="Clean Xcode DerivedData")
@click.option("--all", is_flag=True, help="Clean all categories")
@click.option("--force", is_flag=True, help="Enable deletion (dry-run by default)")
@click.option(
    "--yes",
    "-y",
    is_flag=True,
    help="Skip confirmation prompt (requires --force)",
)
def cli(caches, logs, tmp, trash, xcode, all, force, yes):
    """macOS system cache & temp file cleaner.
    
    By default, runs in dry-run mode and shows what would be deleted.
    Use --force to clean. Use --yes with --force to skip confirmation.
    """

def main():
    cli()
```

### cli() Logic — exact flow

```python
def cli(caches, logs, tmp, trash, xcode, all, force, yes):
    # 1. Collect selected cleaning flags
    selected = set()
    if caches:
        selected.add("caches")
    if logs:
        selected.add("logs")
    if tmp:
        selected.add("tmp")
    if trash:
        selected.add("trash")
    if xcode:
        selected.add("xcode")
    if all:
        selected.add("all")
    
    # 2. If no cleaning category selected:
    if not selected:
        click.echo("No cleaning category selected. Use --help for available options.", err=True)
        ctx = click.get_current_context()
        click.echo(ctx.get_help())
        ctx.exit(0)
    
    # 3. Resolve rules
    rules = resolve_rules(selected)
    
    # 4. Scan
    items = scan_rules(rules)
    
    # 5. Execute (dry-run or delete)
    console = Console()
    execute_clean(items, force=force, yes=yes, console=console)
```

### Edge Cases
- `--yes` without `--force`: ignore `--yes` (still dry-run). Or Click validation:
  ```python
  if yes and not force:
      raise click.UsageError("--yes requires --force")
  ```
Use the `raise click.UsageError` approach.

### Examples

```bash
$ cleaner --all
# → dry-run table

$ cleaner --caches --logs
# → dry-run table for 2 categories

$ cleaner --all --force
# → asks "Delete 2.4 GB...? (yes/no):"

$ cleaner --all --force --yes
# → deletes immediately

$ cleaner --help
# → shows all flags and descriptions
```

---

## 8. src/cleaner/__main__.py

```python
from cleaner.cli import main

if __name__ == "__main__":
    main()
```

---

## 9. tests/conftest.py

```python
import pytest
import tempfile
import shutil
from pathlib import Path

@pytest.fixture
def temp_dir():
    """Provide a temporary directory that auto-deletes after the test."""
    td = Path(tempfile.mkdtemp())
    yield td
    shutil.rmtree(td, ignore_errors=True)

@pytest.fixture
def make_tree(temp_dir):
    """Helper to create a directory tree inside temp_dir."""
    def _make(subpath: str, file_count: int = 0, file_size: int = 100) -> Path:
        target = temp_dir / subpath
        target.mkdir(parents=True, exist_ok=True)
        for i in range(file_count):
            (target / f"file_{i}.txt").write_bytes(b"x" * file_size)
        return target
    return _make
```

---

## 10. tests/test_rules.py

```python
import pytest
from cleaner.rules import CleaningRule, get_all_rules, resolve_rules

def test_all_rules_count():
    assert len(get_all_rules()) == 5

def test_all_rules_have_paths():
    for rule in get_all_rules():
        assert isinstance(rule.path, type(rule.path))  # just assert isinstance Path

def test_resolve_specific():
    rules = resolve_rules({"caches", "logs"})
    names = [r.name for r in rules]
    assert names == ["caches", "logs"]

def test_resolve_all():
    assert len(resolve_rules({"all"})) == 5

def test_resolve_unknown():
    with pytest.raises(ValueError, match="Unknown"):
        resolve_rules({"caches", "nope"})

def test_resolve_empty():
    with pytest.raises(ValueError):
        resolve_rules(set())
```

---

## 11. tests/test_scanner.py

```python
import pytest
import os
from pathlib import Path
from cleaner.scanner import humanize_size, scan_directory

def test_humanize_size():
    assert humanize_size(0) == "0 B"
    assert humanize_size(512) == "512 B"
    assert humanize_size(1024) == "1.0 KB"
    assert humanize_size(1_500_000) == "1.4 MB"
    assert humanize_size(1_073_741_824) == "1.0 GB"

def test_scan_empty(make_tree):
    path = make_tree("empty")
    result = scan_directory("test", path)
    assert result.total_bytes == 0
    assert result.file_count == 0
    assert result.dir_count == 0

def test_scan_with_files(make_tree):
    path = make_tree("docs", file_count=3, file_size=100)
    result = scan_directory("docs", path)
    assert result.file_count == 3
    assert result.total_bytes == 300
    assert result.dir_count == 0

def test_scan_with_subdir(make_tree):
    base = make_tree("base", file_count=1)
    sub = base / "sub"
    sub.mkdir()
    (sub / "inner.txt").write_text("hello")
    result = scan_directory("base", base)
    assert result.file_count == 2
    assert result.dir_count == 1

def test_scan_nonexistent():
    result = scan_directory("ghost", Path("/this/does/not/exist/123456"))
    assert result.total_bytes == 0
    assert result.file_count == 0

def test_scan_skips_symlinks(make_tree):
    base = make_tree("symlink_test", file_count=1)
    target = base / "real.txt"
    link = base / "link.txt"
    os.symlink(target, link)
    result = scan_directory("symlink", base)
    assert result.file_count == 1  # only counts the real file
```

---

## 12. tests/test_cleaner.py

```python
import pytest
from pathlib import Path
from unittest.mock import MagicMock, patch
from rich.console import Console

from cleaner.cleaner import scan_rules, total_summary, execute_clean, delete_path, CleanItem
from cleaner.rules import CleaningRule

@pytest.fixture
def dummy_items():
    return [
        CleanItem("caches", "Caches", Path("/tmp/cache"), "100 B", 100, 1, 0),
        CleanItem("logs", "Logs", Path("/tmp/log"), "200 B", 200, 2, 1),
    ]

def test_total_summary(dummy_items):
    h, b, f, d = total_summary(dummy_items)
    assert b == 300
    assert f == 3
    assert d == 1
    assert h == "300 B"

def test_delete_path_file(make_tree):
    base = make_tree("del")
    f = base / "a.txt"
    f.write_text("hi")
    delete_path(f)
    assert not f.exists()

def test_delete_path_dir(make_tree):
    base = make_tree("del_dir", file_count=2)
    delete_path(base)
    assert not base.exists()

def test_delete_path_skips_symlink(make_tree):
    import os
    base = make_tree("del_link", file_count=1)
    real = base / "real.txt"
    link = base / "link.txt"
    os.symlink(real, link)
    assert link.exists()
    delete_path(link)  # should be a no-op / skip
    assert link.exists()  # symlink remains

def test_execute_clean_dry_run():
    console = Console(file=open(os.devnull, "w"))
    items = [CleanItem("caches", "Caches", Path("/x"), "1 B", 1, 0, 0)]
    result = execute_clean(items, force=False, yes=False, console=console)
    assert result is False

@patch("cleaner.cleaner.delete_path")
def test_execute_clean_force_yes(mock_delete):
    console = Console(file=open(os.devnull, "w"))
    item = CleanItem("caches", "Caches", Path("/fake"), "1 B", 1, 0, 0)
    result = execute_clean([item], force=True, yes=True, console=console)
    assert result is True
    mock_delete.assert_called_once_with(Path("/fake"))

@patch("cleaner.cleaner.delete_path")
def test_execute_clean_force_no(mock_delete):
    console = Console(file=open(os.devnull, "w"))
    item = CleanItem("caches", "Caches", Path("/fake"), "1 B", 1, 0, 0)
    with patch.object(console, "input", return_value="no"):
        result = execute_clean([item], force=True, yes=False, console=console)
    assert result is False
    mock_delete.assert_not_called()
```

---

## 13. tests/test_cli.py

```python
import pytest
from click.testing import CliRunner
from cleaner.cli import cli

runner = CliRunner()

def test_cli_no_args():
    result = runner.invoke(cli)
    assert result.exit_code == 0
    assert "No cleaning category selected" in result.output

def test_cli_help():
    result = runner.invoke(cli, ["--help"])
    assert result.exit_code == 0
    assert "--caches" in result.output
    assert "--force" in result.output
    assert "--yes" in result.output

def test_cli_version():
    result = runner.invoke(cli, ["--version"])
    assert result.exit_code == 0
    assert "cleaner" in result.output

def test_cli_dry_run_all():
    result = runner.invoke(cli, ["--all"])
    assert result.exit_code == 0
    assert "Dry run" in result.output or "Preview" in result.output or "Total" in result.output

def test_cli_yes_without_force():
    result = runner.invoke(cli, ["--all", "--yes"])
    assert result.exit_code != 0
    assert "--yes requires --force" in result.output
```

---

## 14. Non-Goals (Original v0.1 — some addressed in v0.2)

- System-level directories requiring `sudo`.
- Scheduled/cron automation.
- Undo/restore from trash (partially addressed via `--move-to-trash`).
- GUI / TUI.
- Cross-platform support (macOS only).

### Implemented in v0.2

- Browser cache cleaning (Safari, Chrome, Firefox)
- Config files (`.cleanerrc`, `~/.config/cleaner/config.json`)
- Additional dev-tool caches (npm, Yarn, pip, Docker, CoreSimulator)

---

## 15. Acceptance Criteria Summary

1. `python -m cleaner --help` shows all flags.
2. `python -m cleaner --all` shows a dry-run preview table **without** deleting anything.
3. `python -m cleaner --caches --logs` scans only those categories.
4. `--force` alone prompts for confirmation.
5. `--force --yes` deletes without prompting.
6. Missing paths appear as `0 B` / `0 items`.
7. Symlinks are skipped in scan and delete.
8. Permission errors are caught + warned, not crashed.
9. All tests pass: `pytest tests/ -v`.
10. Installable: `pip install -e .` makes `cleaner` command available.
11. All public functions have type hints.
