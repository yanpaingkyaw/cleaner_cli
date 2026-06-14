# 🧹 Cleaner CLI

A safe, fast, and interactive macOS system cache & temp file cleaner built in Python.

> **Dry-run by default.** Preview everything before you delete. No accidental data loss.

[![Python 3.10+](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/downloads/)
[![license](https://img.shields.io/badge/license-MIT-green.svg)](LICENSE)

---

## ✨ Features

- **🔒 Dry-run by default** — see exactly what would be deleted before anything happens
- **🎯 Selective cleaning** — choose only the categories you want (caches, logs, temp, trash, Xcode)
- **📊 Beautiful terminal output** — Rich-powered tables with sizes and item counts
- **⚡ Fast scanning** — recursively walks directories, skips symlinks, handles permission errors
- **🛡️ Safe deletion** — `--force` required; `--yes` for automation
- **🧪 Fully tested** — 25 unit tests covering scanning, cleaning, rules, and CLI

---

## 🚀 Installation

### From source (recommended)

```bash
git clone https://github.com/yanpaingkyaw/cleaner_cli.git
cd cleaner_cli
pip install -e .
```

This installs the `cleaner` command globally (or in your active virtual environment).

### Requirements

- Python 3.10+
- macOS (uses macOS-specific paths like `~/Library/Caches`)

---

## 📖 Usage

### Dry Run (default) — Preview before deleting

```bash
# Preview all cleaning categories
cleaner --all

# Preview specific categories only
cleaner --caches --logs
cleaner --logs --tmp --xcode
```

Example output:

```
┌───────────────────┬──────────────────────────────────────┬─────────┬───────┐
│ Category          │ Path                                 │ Size    │ Items │
├───────────────────┼──────────────────────────────────────┼─────────┼───────┤
│ User Caches       │ /Users/you/Library/Caches            │ 2.3 GB  │ 1,247 │
│ User Logs         │ /Users/you/Library/Logs              │ 145 MB  │    89 │
│ Temp Files        │ /var/folders/.../T                   │  45 MB  │    12 │
│ Trash             │ /Users/you/.Trash                    │   0 B   │     0 │
│ Xcode DerivedData │ /Users/you/.../Xcode/DerivedData     │ 1.8 GB  │   312 │
├───────────────────┼──────────────────────────────────────┼─────────┼───────┤
│ Total             │                                      │ 4.3 GB  │ 1,660 │
└───────────────────┴──────────────────────────────────────┴─────────┴───────┘
Dry run — nothing deleted. Use --force to clean.
```

### Actually Clean

```bash
# Clean with confirmation prompt
cleaner --all --force

# Clean immediately without prompting (automation / scripts)
cleaner --all --force --yes
```

When `--force` is used without `--yes`, you'll see:

```
Delete 4.3 GB across 1,660 items? This cannot be undone. (yes/no):
```

Type `yes` or `y` to confirm.

---

## 🎛️ CLI Options

| Flag | Description |
|------|-------------|
| `--caches` | Clean `~/Library/Caches` |
| `--logs` | Clean `~/Library/Logs` |
| `--tmp` | Clean temp files (`$TMPDIR`) |
| `--trash` | Empty `~/.Trash` |
| `--xcode` | Clean `~/Library/Developer/Xcode/DerivedData` |
| `--all` | Select all categories above |
| `--force` | **Required** to enable actual deletion |
| `--yes`, `-y` | Skip the confirmation prompt (requires `--force`) |
| `--version` | Show version |
| `--help` | Show help and all options |

### Common Commands

```bash
# Quick preview of everything
cleaner --all

# Clean caches and logs only (with confirmation)
cleaner --caches --logs --force

# Clean everything, no prompts (CI/scripts)
cleaner --all --force --yes

# Clean Xcode build artifacts only
cleaner --xcode --force
```

> ⚠️ **Without `--force`, nothing is ever deleted.** Every command is safe to run.

---

## 🧪 Testing

```bash
python -m pytest tests/ -v
```

```
============================= test session starts ==============================
collected 25 items

tests/test_cleaner.py .......                                          [ 28%]
tests/test_cli.py .....                                                [ 48%]
tests/test_rules.py ......                                             [ 76%]
tests/test_scanner.py .....                                            [100%]

============================== 25 passed in 0.94s ==============================
```

---

## 🏗️ Project Structure

```
cleaner-cli/
├── pyproject.toml          # Build & dependency config
├── README.md               # This file
├── SPEC.md                 # Full AI development spec
├── src/
│   └── cleaner/
│       ├── __init__.py     # Version
│       ├── __main__.py     # Entry point
│       ├── cli.py          # Click CLI definition
│       ├── scanner.py      # Directory walking & size calculation
│       ├── cleaner.py      # Dry-run & deletion logic
│       └── rules.py        # Cleaning category definitions
└── tests/
    ├── conftest.py         # Shared pytest fixtures
    ├── test_cleaner.py
    ├── test_cli.py
    ├── test_rules.py
    └── test_scanner.py
```

---

## 🛠️ Development

### Run without installing

```bash
python -m cleaner --all
```

### Install dev dependencies

```bash
pip install -e ".[dev]"
```

### Code style

Type hints are used throughout. The project targets Python 3.10+.

---

## 🧹 What Gets Cleaned?

| Category | Path | Typical Size |
|----------|------|-------------|
| User Caches | `~/Library/Caches` | 500 MB – 5 GB |
| User Logs | `~/Library/Logs` | 50 MB – 500 MB |
| Temp Files | `$TMPDIR` | 10 MB – 200 MB |
| Trash | `~/.Trash` | Varies |
| Xcode DerivedData | `~/Library/Developer/Xcode/DerivedData` | 1 GB – 20 GB+ |

> ⚠️ Only **user-writable** directories are targeted. System directories (e.g., `/Library/Caches`) are never touched.

---

## 🔒 Safety Features

- **Dry-run by default** — every command previews; nothing deletes without `--force`
- **Confirmation prompt** — `--force` alone still asks before deleting
- **Symlink protection** — symlinks are never followed or deleted
- **Permission-safe** — unreadable files are skipped with a warning, never crashing
- **Missing-path handling** — non-existent directories show `0 B` and are silently skipped

---

## 📦 Tech Stack

- **[Click](https://click.palletsprojects.com/)** — CLI framework
- **[Rich](https://rich.readthedocs.io/)** — Terminal formatting & tables
- **[pytest](https://docs.pytest.org/)** — Testing framework

---

## 📝 License

MIT License — see [LICENSE](LICENSE)

---

> Built with the help of [Kimchi](https://kimchi.dev) 🥒
