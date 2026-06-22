import os
from pathlib import Path
from unittest.mock import patch

import pytest
from rich.console import Console

from cleaner.cleaner import (
    CleanItem,
    DeleteResult,
    delete_path,
    execute_clean,
    move_to_trash,
    scan_rules,
    total_summary,
)
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
    result = delete_path(f)
    assert not f.exists()
    assert result.success
    assert result.bytes_freed == 2


def test_delete_path_dir(make_tree):
    base = make_tree("del_dir", file_count=2, file_size=50)
    result = delete_path(base)
    assert base.exists()
    assert len(list(base.iterdir())) == 0
    assert result.success
    assert result.bytes_freed == 100


def test_delete_path_skips_symlink(make_tree):
    base = make_tree("del_link", file_count=1)
    real = base / "real.txt"
    real.write_text("content")
    link = base / "link.txt"
    os.symlink(real, link)
    result = delete_path(link)
    assert link.exists()
    assert result.success
    assert result.bytes_freed == 0


def test_delete_path_reports_failure(make_tree, monkeypatch):
    base = make_tree("fail_dir", file_count=1)
    original_unlink = os.unlink

    def failing_unlink(path):
        if str(path).endswith("file_0.txt"):
            raise OSError("Permission denied")
        return original_unlink(path)

    monkeypatch.setattr(os, "unlink", failing_unlink)
    result = delete_path(base)
    assert not result.success
    assert result.error is not None


def test_move_to_trash(make_tree, monkeypatch, tmp_path):
    trash_dir = tmp_path / "Trash"
    trash_dir.mkdir()
    monkeypatch.setattr("cleaner.cleaner.Path.home", lambda: tmp_path)

    base = make_tree("trash_test", file_count=1)
    file_path = base / "file_0.txt"
    move_to_trash(file_path)
    assert not file_path.exists()
    assert any(item.name.startswith("cleaner-") for item in trash_dir.iterdir())


def test_execute_clean_dry_run():
    console = Console(file=open(os.devnull, "w"))
    items = [CleanItem("caches", "Caches", Path("/x"), "1 B", 1, 0, 0)]
    result = execute_clean(items, force=False, yes=False, console=console)
    assert result is False


def test_execute_clean_dry_run_json(capsys):
    console = Console(file=open(os.devnull, "w"))
    items = [CleanItem("caches", "Caches", Path("/x"), "1 B", 1, 0, 0)]
    result = execute_clean(
        items,
        force=False,
        yes=False,
        console=console,
        json_output=True,
    )
    captured = capsys.readouterr()
    assert result is False
    assert '"mode": "dry-run"' in captured.out


@patch("cleaner.cleaner.delete_path")
def test_execute_clean_force_yes(mock_delete):
    mock_delete.return_value = DeleteResult(bytes_freed=1, success=True)
    console = Console(file=open(os.devnull, "w"))
    item = CleanItem("caches", "Caches", Path("/fake"), "1 B", 1, 0, 0)
    result = execute_clean([item], force=True, yes=True, console=console)
    assert result is True
    mock_delete.assert_called_once()


@patch("cleaner.cleaner.delete_path")
def test_execute_clean_force_no(mock_delete):
    console = Console(file=open(os.devnull, "w"))
    item = CleanItem("caches", "Caches", Path("/fake"), "1 B", 1, 0, 0)
    with patch.object(console, "input", return_value="no"):
        result = execute_clean([item], force=True, yes=False, console=console)
    assert result is False
    mock_delete.assert_not_called()


def test_execute_clean_sort_by_size():
    console = Console(file=open(os.devnull, "w"))
    items = [
        CleanItem("a", "A", Path("/a"), "1 B", 1, 0, 0),
        CleanItem("b", "B", Path("/b"), "100 B", 100, 0, 0),
    ]
    execute_clean(items, force=False, yes=False, console=console, sort_by_size=True)


def test_scan_rules(make_tree):
    base = make_tree("scan_test", file_count=2, file_size=100)
    rules = [CleaningRule("test", "Test Rule", base, "test description")]
    items = scan_rules(rules)
    assert len(items) == 1
    assert items[0].rule_name == "test"
    assert items[0].total_bytes == 200
