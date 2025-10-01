# Development Guide

Complete guide for setting up and developing the dartserver-pythonapp with UV, tox, comprehensive testing, and linting.

## Table of Contents

- [Prerequisites](#prerequisites)
- [Quick Setup](#quick-setup)
- [Package Management with UV](#package-management-with-uv)
- [Testing with Tox](#testing-with-tox)
- [Linting and Code Quality](#linting-and-code-quality)
- [Pre-commit Hooks](#pre-commit-hooks)
- [Development Workflow](#development-workflow)
- [CI/CD](#cicd)

## Prerequisites

### Required

- Python 3.10, 3.11, or 3.12
- UV package manager
- Git

### Installing UV

```bash
# macOS/Linux
curl -LsSf https://astral.sh/uv/install.sh | sh

# Or with pip
pip install uv

# Verify installation
uv --version
```

## Quick Setup

### One-Command Setup

```bash
# Complete development setup
make dev-setup
```

This will:
1. Install all development dependencies with UV
2. Install pre-commit hooks
3. Setup custom git hooks

### Manual Setup

```bash
# 1. Install UV (if not already installed)
curl -LsSf https://astral.sh/uv/install.sh | sh

# 2. Install dependencies
make install-dev

# 3. Setup pre-commit hooks
make pre-commit-install
make setup-hooks

# 4. Verify installation
make test
```

## Package Management with UV

### Why UV?

UV is a fast Python package installer and resolver:
- **10-100x faster** than pip
- **Reliable** dependency resolution
- **Compatible** with pip and requirements.txt
- **Modern** and actively maintained

### Installing Dependencies

```bash
# Production dependencies only
make install

# Development dependencies
make install-dev

# All dependencies (dev + lint + test)
make install-all

# Or directly with UV
uv pip install -e .
uv pip install -e ".[dev,lint,test]"
```

### Managing Dependencies

```bash
# Add a new dependency
uv pip install package-name

# Add to pyproject.toml
# Edit pyproject.toml and add to dependencies list

# Update dependencies
uv pip install --upgrade package-name

# List installed packages
uv pip list

# Show package info
uv pip show package-name
```

### Virtual Environments with UV

```bash
# Create virtual environment
uv venv

# Activate virtual environment
source .venv/bin/activate  # Linux/macOS
.venv\Scripts\activate     # Windows

# Install in virtual environment
uv pip install -e ".[all]"
```

## Testing with Tox

### What is Tox?

Tox automates testing across multiple Python versions and environments.

### Running Tests with Tox

```bash
# Run all environments (Python 3.10, 3.11, 3.12, lint, type, security)
make tox

# Run specific Python version
make tox-py310
make tox-py311
make tox-py312

# Run linting
make tox-lint

# Run type checking
make tox-type

# Run security checks
make tox-security
```

### Tox Environments

| Environment | Description |
|------------|-------------|
| `py310` | Tests with Python 3.10 |
| `py311` | Tests with Python 3.11 |
| `py312` | Tests with Python 3.12 |
| `lint` | Linting checks (ruff, black, isort, flake8) |
| `lint-fix` | Auto-fix linting issues |
| `type` | Type checking with mypy |
| `security` | Security checks (bandit, safety) |
| `pylint` | Pylint code analysis |
| `coverage-report` | Combined coverage report |

### Tox Configuration

Configuration is in `tox.ini`:

```ini
[tox]
env_list = py{310,311,312}, lint, type, security, coverage-report

[testenv]
description = Run unit and integration tests
commands =
    pytest {posargs:tests/} --cov=. --cov-report=html --cov-report=xml
```

## Linting and Code Quality

### Available Linters

1. **Ruff** - Fast Python linter (replaces flake8, isort, and more)
2. **Black** - Code formatter
3. **isort** - Import sorter
4. **Flake8** - Style guide enforcement
5. **MyPy** - Static type checker
6. **Pylint** - Code analysis
7. **Bandit** - Security linter

### Running Linters

```bash
# Run all linting checks
make lint

# Auto-fix linting issues
make lint-fix

# Run specific linters
ruff check .
black --check .
isort --check-only .
flake8 .

# Type checking
make type

# Security checks
make security

# Pylint
make pylint
```

### Linting Configuration

All linting configuration is in `pyproject.toml`:

```toml
[tool.ruff]
line-length = 100
select = ["E", "W", "F", "I", "C", "B", "UP", "N", "S", ...]

[tool.black]
line-length = 100
target-version = ['py310', 'py311', 'py312']

[tool.isort]
profile = "black"
line_length = 100
```

### Code Quality Standards

- **Line length**: 100 characters
- **Import sorting**: isort with black profile
- **Type hints**: Encouraged but not required
- **Docstrings**: Google style
- **Security**: No hardcoded secrets, SQL injection prevention

## Pre-commit Hooks

### Two-Stage Pre-commit System

The project implements a unique two-stage pre-commit system:

1. **First Attempt**: Checks code quality and **fails** if issues found
2. **Second Attempt**: **Auto-fixes** issues and commits

### Installing Pre-commit Hooks

```bash
# Install pre-commit framework hooks
make pre-commit-install

# Install custom git hooks
make setup-hooks

# Or both at once
make dev-setup
```

### How It Works

#### First Commit Attempt

```bash
git add .
git commit -m "Add feature"

# Output:
# ✗ Ruff found issues
# ✗ Black found formatting issues
# ✗ isort found import sorting issues
# COMMIT BLOCKED: Code quality issues found!
# Try committing again to auto-fix these issues
```

#### Second Commit Attempt

```bash
git commit -m "Add feature"

# Output:
# Running Ruff with auto-fix...
# Running Black formatter...
# Running isort...
# ✓ All issues fixed! Commit proceeding...
```

### Pre-commit Configuration

Configuration is in `.pre-commit-config.yaml`:

```yaml
repos:
  - repo: https://github.com/astral-sh/ruff-pre-commit
    hooks:
      - id: ruff
        name: ruff-check-first-attempt
        args: [--exit-non-zero-on-fix]
      - id: ruff
        name: ruff-fix-second-attempt
        args: [--fix, --exit-zero]
```

### Running Pre-commit Manually

```bash
# Run on all files
make pre-commit

# Run on staged files only
pre-commit run

# Run specific hook
pre-commit run ruff

# Update hooks
pre-commit autoupdate
```

## Development Workflow

### Daily Development

```bash
# 1. Start development
git checkout -b feature/my-feature

# 2. Make changes
# Edit files...

# 3. Run tests
make test

# 4. Check code quality
make lint

# 5. Commit (pre-commit hooks will run)
git add .
git commit -m "Add feature"

# 6. Push
git push origin feature/my-feature
```

### Before Committing

```bash
# Run all checks
make check-all

# Or individually
make lint
make type
make security
make test
```

### Testing Workflow

```bash
# Run tests during development
make test

# Run with coverage
make test-cov

# Run specific test file
pytest tests/unit/test_game_301.py -v

# Run tests in watch mode (requires pytest-watch)
make test-watch
```

### Code Quality Workflow

```bash
# Check code quality
make lint

# Auto-fix issues
make lint-fix

# Type check
make type

# Security check
make security
```

## CI/CD

### Simulating CI Locally

```bash
# Run full CI pipeline
make ci

# This runs:
# 1. clean
# 2. install-dev
# 3. lint
# 4. type
# 5. security
# 6. test
# 7. coverage
```

### CI Pipeline

The CI pipeline should run:

```yaml
# Example GitHub Actions workflow
name: CI

on: [push, pull_request]

jobs:
  test:
    runs-on: ubuntu-latest
    strategy:
      matrix:
        python-version: ["3.10", "3.11", "3.12"]
    steps:
      - uses: actions/checkout@v3
      - name: Install UV
        run: curl -LsSf https://astral.sh/uv/install.sh | sh
      - name: Install dependencies
        run: make install-dev
      - name: Lint
        run: make lint
      - name: Type check
        run: make type
      - name: Security
        run: make security
      - name: Test
        run: make test-cov
      - name: Upload coverage
        uses: codecov/codecov-action@v3
```

## Makefile Commands

### Quick Reference

```bash
make help              # Show all available commands
make info              # Show project information

# Installation
make install           # Install production dependencies
make install-dev       # Install development dependencies
make install-all       # Install all dependencies

# Testing
make test              # Run all tests
make test-unit         # Run unit tests
make test-integration  # Run integration tests
make test-cov          # Run tests with coverage

# Linting
make lint              # Run all linting checks
make lint-fix          # Auto-fix linting issues
make type              # Run type checking
make security          # Run security checks
make pylint            # Run pylint

# Tox
make tox               # Run all tox environments
make tox-py310         # Run Python 3.10 tests
make tox-lint          # Run linting environment
make tox-type          # Run type checking environment

# Pre-commit
make pre-commit        # Run pre-commit on all files
make pre-commit-install # Install pre-commit hooks
make setup-hooks       # Setup custom git hooks

# Cleanup
make clean             # Clean build artifacts
make clean-all         # Clean everything including venv

# Application
make run               # Run the application
make run-dev           # Run in development mode

# Docker
make docker-build      # Build Docker image
make docker-up         # Start containers
make docker-down       # Stop containers

# Quality
make check-all         # Run all quality checks
make ci                # Simulate CI pipeline
make dev-setup         # Complete development setup
```

## Troubleshooting

### UV Installation Issues

```bash
# If UV is not found
export PATH="$HOME/.cargo/bin:$PATH"

# Or reinstall
curl -LsSf https://astral.sh/uv/install.sh | sh
```

### Tox Issues

```bash
# Recreate tox environments
tox -r

# Clean tox cache
make clean
```

### Pre-commit Issues

```bash
# Reinstall hooks
pre-commit uninstall
pre-commit install

# Clear cache
pre-commit clean
```

### Test Failures

```bash
# Run with verbose output
pytest -vv

# Run with print statements
pytest -s

# Debug specific test
pytest tests/unit/test_game_301.py::TestGame301::test_initialization_default -vv
```

## Best Practices

### 1. Always Use UV

```bash
# Good
uv pip install package-name

# Avoid
pip install package-name
```

### 2. Run Tests Before Committing

```bash
make test
```

### 3. Let Pre-commit Fix Issues

Don't manually fix linting issues - let the pre-commit hooks do it on the second attempt.

### 4. Use Tox for Final Validation

```bash
make tox
```

### 5. Keep Dependencies Updated

```bash
uv pip list --outdated
uv pip install --upgrade package-name
```

## Additional Resources

- [UV Documentation](https://github.com/astral-sh/uv)
- [Tox Documentation](https://tox.wiki/)
- [Pre-commit Documentation](https://pre-commit.com/)
- [Ruff Documentation](https://docs.astral.sh/ruff/)
- [pytest Documentation](https://docs.pytest.org/)

---

**Happy Coding! 🚀**