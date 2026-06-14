import os
import pytest
from pathlib import Path
from unittest.mock import patch
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
    # delete_path clears directory contents but preserves the directory itself
    assert base.exists()
    assert len(list(base.iterdir())) == 0


def test_delete_path_skips_symlink(make_tree):
    base = make_tree("del_link", file_count=1)
    real = base / "real.txt"
    real.write_text("content")
    link = base / "link.txt"
    os.symlink(real, link)
    assert link.exists()
    delete_path(link)
    assert link.exists()


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


def test_scan_rules(make_tree):
    base = make_tree("scan_test", file_count=2, file_size=100)
    rules = [CleaningRule("test", "Test Rule", base, "test description")]
    items = scan_rules(rules)
    assert len(items) == 1
    assert items[0].rule_name == "test"
    assert items[0].label == "Test Rule"
    assert items[0].path == base
    assert items[0].total_bytes == 200
    assert items[0].file_count == 2
    assert items[0].dir_count == 0
    assert items[0].human_size == "200 B"
