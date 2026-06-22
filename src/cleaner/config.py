from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path

from cleaner.rules import CleaningRule

__all__ = ["CleanerConfig", "load_config"]

CONFIG_FILENAMES = (".cleanerrc", "config.json")
CONFIG_DIRS = (Path.home() / ".config" / "cleaner" / "config.json",)


@dataclass(frozen=True)
class CleanerConfig:
    exclude_paths: tuple[Path, ...] = ()
    custom_rules: tuple[CleaningRule, ...] = ()
    default_flags: tuple[str, ...] = ()


def _expand_path(raw: str) -> Path:
    return Path(raw).expanduser().resolve()


def _parse_rule(entry: dict) -> CleaningRule:
    required = ("name", "label", "path", "description")
    missing = [key for key in required if key not in entry]
    if missing:
        raise ValueError(f"Custom rule missing fields: {', '.join(missing)}")
    return CleaningRule(
        name=str(entry["name"]),
        label=str(entry["label"]),
        path=_expand_path(str(entry["path"])),
        description=str(entry["description"]),
    )


def _load_json_config(path: Path) -> CleanerConfig:
    data = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        raise ValueError(f"Config file must contain a JSON object: {path}")

    exclude_paths = tuple(_expand_path(str(item)) for item in data.get("exclude_paths", []))
    custom_rules = tuple(_parse_rule(item) for item in data.get("custom_rules", []))
    default_flags = tuple(str(item) for item in data.get("default_flags", []))
    return CleanerConfig(
        exclude_paths=exclude_paths,
        custom_rules=custom_rules,
        default_flags=default_flags,
    )


def load_config(cwd: Path | None = None) -> CleanerConfig:
    """Load config from the first existing file in search order."""
    search_paths: list[Path] = []
    base = cwd or Path.cwd()
    for name in CONFIG_FILENAMES:
        search_paths.append(base / name)
    search_paths.extend(CONFIG_DIRS)

    merged = CleanerConfig()
    for path in search_paths:
        if not path.is_file():
            continue
        loaded = _load_json_config(path)
        merged = CleanerConfig(
            exclude_paths=merged.exclude_paths + loaded.exclude_paths,
            custom_rules=merged.custom_rules + loaded.custom_rules,
            default_flags=loaded.default_flags or merged.default_flags,
        )
    return merged
