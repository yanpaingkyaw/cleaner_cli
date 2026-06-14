import pytest
from cleaner.rules import CleaningRule, get_all_rules, resolve_rules


def test_all_rules_count():
    assert len(get_all_rules()) == 5


def test_all_rules_have_paths():
    from pathlib import Path
    for rule in get_all_rules():
        assert isinstance(rule.path, Path)


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
