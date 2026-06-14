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
    assert humanize_size(1_099_511_627_776) == "1.0 TB"


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
    assert result.file_count == 1
