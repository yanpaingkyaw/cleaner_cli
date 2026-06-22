# 🧹 Cleaner CLI

A safe, fast, and interactive macOS system cache & temp file cleaner built in Python.

> **Dry-run by default.** Preview everything before you delete. No accidental data loss.

[![Python 3.10+](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/downloads/)
[![license](https://img.shields.io/badge/license-MIT-green.svg)](LICENSE)

---

## ✨ Features

- **🔒 Dry-run by default** — see exactly what would be deleted before anything happens
- **🎯 Selective cleaning** — choose categories (caches, logs, temp, trash, Xcode, browsers, dev tools)
- **📊 Beautiful terminal output** — Rich-powered tables with sizes and item counts
- **⚡ Fast scanning** — `os.scandir`-based recursive walks with cached stat
- **🛡️ Safe deletion** — dry-run by default; `--force` required; `--move-to-trash` for reversible cleanup
- **🤖 Scriptable** — `--json`, `--quiet`, `--threshold`, and `--exclude` for automation
- **⚙️ Configurable** — `.cleanerrc` / `~/.config/cleaner/config.json` for custom rules and excludes
- **🧪 Fully tested** — unit tests covering scanning, cleaning, rules, config, and CLI

---

## 🚀 Installation

Choose one of the following methods.

### 1. Binary Download (simplest — no Python required)

1. Download the correct binary for your Mac from the [Releases page](https://github.com/yanpaingkyaw/cleaner_cli/releases):
   - `cleaner-darwin-x86_64` — Intel Macs
   - `cleaner-darwin-arm64` — Apple Silicon (M1/M2/M3)
2. Make it executable and move it into your `PATH`:
   ```bash
   chmod +x cleaner-darwin-arm64       # use x86_64 for Intel
   mv cleaner-darwin-arm64 /usr/local/bin/cleaner
   ```
3. Run:
   ```bash
   cleaner --all
   ```

### 2. Homebrew (one-liner)

```bash
brew tap yanpaingkyaw/tap
brew install cleaner-cli
```

Then run `cleaner` normally.

### 3. From source (for developers)

Requires Python 3.10+ and macOS.

```bash
git clone https://github.com/yanpaingkyaw/cleaner_cli.git
cd cleaner_cli
pip install -e ".[dev]"
```

This installs the `cleaner` command globally (or in your active virtual environment) and includes development dependencies.

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
| `--simulators` | Clean CoreSimulator caches |
| `--safari` | Clean Safari browser cache |
| `--chrome` | Clean Chrome browser cache |
| `--firefox` | Clean Firefox browser cache |
| `--npm` | Clean npm cache |
| `--yarn` | Clean Yarn cache |
| `--pip` | Clean pip cache |
| `--docker` | Clean Docker Desktop data |
| `--all` | Select all categories above |
| `--force` | **Required** to enable actual deletion |
| `--yes`, `-y` | Skip the confirmation prompt (requires `--force`) |
| `--move-to-trash` | Move items to Trash instead of permanent delete (requires `--force`) |
| `--json` | Output scan/clean results as JSON |
| `--quiet`, `-q` | Suppress non-essential output |
| `--exclude PATH` | Exclude a path from scan/delete (repeatable) |
| `--threshold SIZE` | Only include categories at or above size (e.g. `10MB`, `1GB`) |
| `--sort-size` | Sort categories by size (largest first) |
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

# JSON output for scripting
cleaner --all --json

# Only show categories >= 100 MB, sorted by size
cleaner --all --threshold 100MB --sort-size

# Reversible cleanup via Trash
cleaner --caches --force --move-to-trash

# Exclude a path from cleaning
cleaner --caches --exclude ~/Library/Caches/com.apple.Safari
```

> ⚠️ **Without `--force`, nothing is ever deleted.** Every command is safe to run.

---

## ⚙️ Configuration

Copy [`.cleanerrc.example`](.cleanerrc.example) to `.cleanerrc` in your project directory, or create `~/.config/cleaner/config.json`:

```json
{
  "exclude_paths": ["~/Library/Caches/com.apple.Safari/WebKitCache"],
  "default_flags": ["caches", "logs"],
  "custom_rules": [
    {
      "name": "my-app-cache",
      "label": "My App Cache",
      "path": "~/Library/Caches/com.example.myapp",
      "description": "Cache for a custom application"
    }
  ]
}
```

When no CLI flags are provided, `default_flags` from config are used automatically.

---

## 🧪 Testing

```bash
python -m pytest tests/ -v
ruff check src tests
```

---

## 🏗️ Project Structure

```
cleaner-cli/
├── pyproject.toml
├── README.md
├── SPEC.md
├── .cleanerrc.example
├── scripts/
│   └── update_homebrew_formula.py
├── .github/workflows/
│   ├── ci.yml
│   └── release.yml
├── src/cleaner/
│   ├── cli.py
│   ├── cleaner.py
│   ├── config.py
│   ├── rules.py
│   └── scanner.py
└── tests/
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

Use pre-commit for local linting:

```bash
pre-commit install
pre-commit run --all-files
```

---

## 🧹 What Gets Cleaned?

| Category | Path | Typical Size |
|----------|------|-------------|
| User Caches | `~/Library/Caches` | 500 MB – 5 GB |
| User Logs | `~/Library/Logs` | 50 MB – 500 MB |
| Temp Files | `$TMPDIR` | 10 MB – 200 MB |
| Trash | `~/.Trash` | Varies |
| Xcode DerivedData | `~/Library/Developer/Xcode/DerivedData` | 1 GB – 20 GB+ |
| CoreSimulator | `~/Library/Developer/CoreSimulator/Caches` | 100 MB – 5 GB |
| Safari / Chrome / Firefox | Browser cache dirs | Varies |
| npm / Yarn / pip | Dev tool caches | Varies |
| Docker Desktop | Container data | Can be very large |

> ⚠️ Only **user-writable** directories are targeted. System directories (e.g., `/Library/Caches`) are never touched.

---

## 🔒 Safety Features

- **Dry-run by default** — every command previews; nothing deletes without `--force`
- **Confirmation prompt** — `--force` alone still asks before deleting
- **Symlink protection** — symlinks are never followed or deleted
- **Permission-safe** — unreadable files are skipped with a warning, never crashing
- **Reversible cleanup** — `--move-to-trash` moves items to `~/.Trash` instead of permanent delete
- **Accurate reporting** — deletion reports bytes actually freed, and surfaces partial failures

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
