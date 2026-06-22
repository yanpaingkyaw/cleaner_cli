import json

from cleaner.config import load_config


def test_load_config_missing(monkeypatch, tmp_path):
    monkeypatch.setattr("cleaner.config.CONFIG_DIRS", ())
    config = load_config(cwd=tmp_path / "missing")
    assert config.exclude_paths == ()
    assert config.custom_rules == ()


def test_load_config_from_file(tmp_path):
    config_data = {
        "exclude_paths": ["~/secret"],
        "default_flags": ["caches"],
        "custom_rules": [
            {
                "name": "mine",
                "label": "Mine",
                "path": str(tmp_path / "custom-cache"),
                "description": "Custom cache dir",
            }
        ],
    }
    config_path = tmp_path / ".cleanerrc"
    config_path.write_text(json.dumps(config_data), encoding="utf-8")

    config = load_config(cwd=tmp_path)
    assert len(config.exclude_paths) == 1
    assert config.default_flags == ("caches",)
    assert len(config.custom_rules) == 1
    assert config.custom_rules[0].name == "mine"
