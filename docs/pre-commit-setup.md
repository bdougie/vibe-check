# Pre-commit Hooks Setup

This project uses pre-commit hooks to ensure consistent code quality before commits.

## Quick Setup

```bash
# Install dependencies
uv pip install -r requirements.txt

# Install pre-commit hooks
make pre-commit-install
# OR
pre-commit install

# Run hooks on all files (optional, to test)
make pre-commit-run
# OR
pre-commit run --all-files
```

## What the Pre-commit Hooks Do

### 🚀 **Ruff (Primary Linter & Formatter)**
- **Lightning fast** Python linting and formatting
- Replaces flake8, isort, and several other tools
- Auto-fixes many issues automatically
- Configured in `pyproject.toml`

### 🔧 **Code Quality Checks**
- **Trailing whitespace** removal
- **End-of-file** fixing
- **YAML/JSON/TOML** validation
- **Large file** detection
- **Merge conflict** detection
- **Debug statement** detection

### 🛡️ **Security & Type Checking**
- **Bandit** security linting
- **MyPy** type checking
- **Safety** dependency vulnerability scanning

### 📝 **Code Formatting**
- **Black** code formatter (backup to ruff)
- **Markdown** linting and formatting

## Manual Usage

```bash
# Run specific hooks
pre-commit run ruff                 # Just ruff linting
pre-commit run ruff-format          # Just ruff formatting
pre-commit run black                # Just black formatting

# Skip hooks for specific commit (emergency use)
git commit --no-verify -m "emergency fix"

# Update hook versions
make pre-commit-update
# OR
pre-commit autoupdate
```

## Makefile Commands

```bash
make lint                    # Run ruff linting
make lint-fix               # Run ruff with auto-fix
make format                 # Format with ruff
make format-check           # Check formatting
make pre-commit-install     # Install hooks
make pre-commit-run         # Run all hooks
make pre-commit-update      # Update hook versions
```

## Configuration Files

- **`.pre-commit-config.yaml`** - Hook configuration
- **`pyproject.toml`** - Ruff, Black, MyPy configuration
- **`requirements.txt`** - Dependencies including ruff and pre-commit

## Ruff Configuration Highlights

```toml
[tool.ruff]
target-version = "py38"
line-length = 88
select = [
    "E", "W",   # pycodestyle
    "F",        # pyflakes  
    "I",        # isort
    "B",        # flake8-bugbear
    "UP",       # pyupgrade
    "SIM",      # flake8-simplify
    "PL",       # pylint
    # ... and more
]
```

## Why Ruff?

- **⚡ 10-100x faster** than traditional tools
- **🔧 Auto-fixes** many issues
- **📦 Replaces multiple tools** (flake8, isort, pyupgrade, etc.)
- **🎯 Zero config** needed for most projects
- **🔄 Drop-in replacement** for existing tools

## CI Integration

Pre-commit hooks also run in GitHub CI:
- **Lint job** - Runs ruff check and format
- **Pre-commit job** - Runs all hooks on all files
- **Security job** - Bandit and safety checks

## Troubleshooting

### Hook Installation Issues
```bash
# Reinstall hooks
pre-commit uninstall
pre-commit install

# Clear cache
pre-commit clean
```

### Ruff Issues
```bash
# Show what ruff would fix
ruff check . --fix --dry-run

# Fix specific files
ruff check path/to/file.py --fix

# Ignore specific rules temporarily
ruff check . --ignore E501,F401
```

### Performance
Pre-commit hooks are designed to be fast:
- **Ruff**: ~10ms for most files
- **Total runtime**: Usually <5 seconds
- **Incremental**: Only checks changed files

---

For more details, see the [pre-commit documentation](https://pre-commit.com/) and [ruff documentation](https://docs.astral.sh/ruff/).