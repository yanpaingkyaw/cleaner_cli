from __future__ import annotations

import tempfile
from dataclasses import dataclass
from pathlib import Path

__all__ = ["CleaningRule", "get_all_rules", "resolve_rules"]


@dataclass(frozen=True)
class CleaningRule:
    name: str
    label: str
    path: Path
    description: str


def get_all_rules() -> list[CleaningRule]:
    """Return all defined rules in fixed order."""
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
        CleaningRule(
            "simulators",
            "CoreSimulator Caches",
            home / "Library/Developer/CoreSimulator/Caches",
            "iOS Simulator cache files",
        ),
        CleaningRule(
            "safari",
            "Safari Cache",
            home / "Library/Caches/com.apple.Safari",
            "Safari browser cache",
        ),
        CleaningRule(
            "chrome",
            "Chrome Cache",
            home / "Library/Caches/Google/Chrome",
            "Google Chrome browser cache",
        ),
        CleaningRule(
            "firefox",
            "Firefox Cache",
            home / "Library/Caches/Firefox",
            "Mozilla Firefox browser cache",
        ),
        CleaningRule(
            "npm",
            "npm Cache",
            home / ".npm",
            "npm package cache",
        ),
        CleaningRule(
            "yarn",
            "Yarn Cache",
            home / "Library/Caches/Yarn",
            "Yarn package cache",
        ),
        CleaningRule(
            "pip",
            "pip Cache",
            home / "Library/Caches/pip",
            "Python pip download cache",
        ),
        CleaningRule(
            "docker",
            "Docker Desktop Data",
            home / "Library/Containers/com.docker.docker/Data",
            "Docker Desktop container data (large; use with care)",
        ),
    ]


def resolve_rules(
    flag_names: set[str],
    extra_rules: list[CleaningRule] | None = None,
) -> list[CleaningRule]:
    """Resolve selected flags to CleaningRule list.

    - If `flag_names` contains "all", return all rules.
    - Otherwise, return rules matching the flag names in definition order.
    - Raise ValueError for unknown flag names.
    - Raise ValueError if flag_names is empty.
    """
    if not flag_names:
        raise ValueError()

    all_rules = get_all_rules()
    if extra_rules:
        existing = {rule.name for rule in all_rules}
        all_rules = all_rules + [rule for rule in extra_rules if rule.name not in existing]

    if "all" in flag_names:
        return all_rules

    rule_map = {rule.name: rule for rule in all_rules}
    unknown = flag_names - set(rule_map.keys())
    if unknown:
        unknown_str = ", ".join(sorted(unknown))
        raise ValueError(f"Unknown cleaning flags: {unknown_str}")

    return [rule for rule in all_rules if rule.name in flag_names]
