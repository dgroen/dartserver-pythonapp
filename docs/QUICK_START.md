# Quick Start Guide

## One-Command Setup

```bash
./setup-dev.sh
```

That's it! The script will:
- ✅ Check Python version (3.10+)
- ✅ Install python3-venv if needed
- ✅ Install UV package manager
- ✅ Create virtual environment with Python venv
- ✅ Install all dependencies (109 packages)
- ✅ Set up pre-commit hooks
- ✅ Run initial tests (98 tests)

---

## Daily Workflow

### 1. Activate Virtual Environment
```bash
source .venv/bin/activate
```

### 2. Run Tests
```bash
# All tests with coverage
make test

# Unit tests only
make test-unit

# Integration tests only
make test-integration

# Specific test file
pytest tests/unit/test_game_301.py -v
```

### 3. Check Code Quality
```bash
# Run all linters
make lint

# Auto-fix formatting
make format

# Type checking
make type-check

# Security scan
make security
```

### 4. Before Committing
```bash
# Stage your changes
git add .

# Commit (pre-commit hooks will run automatically)
git commit -m "Your message"

# If hooks fail, commit again (will auto-fix)
git commit -m "Your message"
```

---

## Common Commands

### Testing
```bash
make test              # Run all tests with coverage
make test-cov          # Generate HTML coverage report
make coverage-report   # Open coverage report in browser
```

### Linting
```bash
make lint              # Run all linters
make lint-fix          # Auto-fix issues
make format            # Format code (Black + isort)
```

### Tox (Multi-version Testing)
```bash
make tox               # Test on all Python versions
make tox-py310         # Test on Python 3.10
make tox-py311         # Test on Python 3.11
make tox-py312         # Test on Python 3.12
make tox-lint          # Run linting environment
```

### Package Management
```bash
# Install new package
uv pip install <package>

# Install from requirements
uv pip install -r requirements.txt

# List installed packages
uv pip list

# Show package info
uv pip show <package>
```

### Cleanup
```bash
make clean             # Remove generated files
make clean-all         # Remove venv and all generated files
```

---

## Project Structure

```
dartserver-pythonapp/
├── app.py                 # Flask application
├── game_manager.py        # Core game logic
├── games/
│   ├── game_301.py       # 301 game
│   └── game_cricket.py   # Cricket game
├── tests/
│   ├── unit/             # Unit tests (75 tests)
│   └── integration/      # Integration tests (23 tests)
├── .venv/                # Virtual environment (python venv)
├── pyproject.toml        # Main configuration
├── tox.ini               # Tox configuration
├── Makefile              # Convenient commands
└── setup-dev.sh          # Setup script
```

---

## Key Features

### 🚀 Fast Package Management
- **UV** is 10-100x faster than pip
- Installs 109 packages in seconds

### 🧪 Comprehensive Testing
- 98 tests (75 unit + 23 integration)
- 80.17% code coverage
- Fast execution (~5 seconds)

### 🔍 7 Linting Tools
- Ruff, Black, isort, Flake8, MyPy, Pylint, Bandit
- Consistent 100-char line length
- Auto-fix on second commit

### 🐍 Multi-Version Support
- Python 3.10, 3.11, 3.12
- Tested with Tox

### 🪝 Smart Pre-commit Hooks
- First commit: Check and report
- Second commit: Auto-fix
- Prevents bad code from being committed

---

## Troubleshooting

### Virtual Environment Issues
```bash
# Recreate venv
rm -rf .venv
./setup-dev.sh
```

### UV Not Found
```bash
# Add to PATH
export PATH="$HOME/.local/bin:$PATH"

# Make permanent
echo 'export PATH="$HOME/.local/bin:$PATH"' >> ~/.bashrc
```

### Pre-commit Issues
```bash
# Reinstall hooks
pre-commit uninstall
pre-commit install

# Run manually
pre-commit run --all-files
```

### Test Failures
```bash
# Run with verbose output
pytest tests/ -vv

# Run with debugging
pytest tests/ --pdb

# Run specific test
pytest tests/unit/test_game_301.py::TestGame301::test_specific -vv
```

---

## Documentation

- **SETUP_COMPLETE.md** - Complete setup documentation
- **SETUP_FIXES.md** - Details of fixes made
- **DEVELOPMENT.md** - Development guidelines
- **TESTING.md** - Testing guidelines
- **README.md** - Project overview

---

## Getting Help

```bash
# Show all make commands
make help

# Show pytest options
pytest --help

# Show tox environments
tox -l

# Show pre-commit hooks
pre-commit run --help
```

---

## Quick Reference

| Task | Command |
|------|---------|
| Setup environment | `./setup-dev.sh` |
| Activate venv | `source .venv/bin/activate` |
| Run tests | `make test` |
| Run linters | `make lint` |
| Format code | `make format` |
| Test all Python versions | `make tox` |
| Install package | `uv pip install <pkg>` |
| Clean up | `make clean` |
| Show help | `make help` |

---

**Happy coding! 🎯**