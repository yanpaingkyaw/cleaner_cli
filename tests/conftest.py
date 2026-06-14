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
