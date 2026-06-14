from dataclasses import dataclass
from pathlib import Path
import tempfile

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
    ]


def resolve_rules(flag_names: set[str]) -> list[CleaningRule]:
    """Resolve selected flags to CleaningRule list.

    - If `flag_names` contains "all", return all rules.
    - Otherwise, return rules matching the flag names in definition order.
    - Raise ValueError for unknown flag names.
    - Raise ValueError if flag_names is empty.
    """
    if not flag_names:
        raise ValueError()

    if "all" in flag_names:
        return get_all_rules()

    all_rules = get_all_rules()
    rule_map = {rule.name: rule for rule in all_rules}
    unknown = flag_names - set(rule_map.keys())
    if unknown:
        unknown_str = ", ".join(sorted(unknown))
        raise ValueError(f"Unknown cleaning flags: {unknown_str}")

    return [rule for rule in all_rules if rule.name in flag_names]
