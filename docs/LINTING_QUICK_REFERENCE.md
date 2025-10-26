# 🎯 Linting Quick Reference Guide

## ✅ Current Status

**ALL PRIMARY LINTERS PASSING** ✨

---

## 🚀 Quick Commands

### Check All Linters (Recommended)

```bash
./check_linting.sh
```

### Auto-Fix Everything

```bash
ruff check --fix . && black . && isort . --skip .venv
```

### Individual Checks

```bash
# Ruff (primary linter)
ruff check .

# Flake8 (style checker)
flake8 .

# Black (formatter)
black --check .

# isort (import sorter)
isort --check-only . --skip .venv
```

### Individual Auto-Fixes

```bash
# Fix ruff issues
ruff check --fix .

# Format code
black .

# Sort imports
isort . --skip .venv
```

---

## 📋 Common Issues & Solutions

### Issue: "Undefined name 'X'"

**Error Code**: F821
**Solution**: Import the missing module or define the variable

### Issue: "Line too long"

**Error Code**: E501
**Solution**: Run `black .` to auto-format

### Issue: "Import not sorted"

**Error Code**: I001
**Solution**: Run `isort . --skip .venv`

### Issue: "Missing docstring"

**Error Code**: D103, D107
**Solution**: Add a docstring to the function/class/method

```python
def my_function():
    """Brief description of what this function does."""
    pass
```

### Issue: "Redundant exception in logging.exception"

**Error Code**: TRY401
**Solution**: Remove exception variable from logger.exception()

```python
# ❌ Wrong
except Exception as e:
    logger.exception(f"Error: {e}")

# ✅ Correct
except Exception:
    logger.exception("Error occurred")
```

### Issue: "Loop variable overwritten"

**Error Code**: PLW2901
**Solution**: Use a different variable name

```python
# ❌ Wrong
for item in items:
    item = transform(item)

# ✅ Correct
for item in items:
    transformed_item = transform(item)
```

### Issue: "Implicit Optional"

**Error Code**: RUF013
**Solution**: Use explicit union type

```python
# ❌ Wrong
def func(param: str = None):

# ✅ Correct
def func(param: str | None = None):
```

---

## 🎯 Pre-Commit Checklist

Before committing code:

1. ✅ Run `./check_linting.sh`
2. ✅ Fix any reported issues
3. ✅ Run auto-fixes if needed: `ruff check --fix . && black . && isort . --skip .venv`
4. ✅ Verify all tests pass
5. ✅ Commit your changes

---

## 🔧 Configuration Files

- **pyproject.toml**: Main configuration for all linters
- **check_linting.sh**: Automated linting check script
- **LINTING_STATUS.md**: Detailed linting status report

---

## 📚 Linting Rules Summary

### Enabled Rule Sets

- ✅ pycodestyle (E, W) - Style guide enforcement
- ✅ pyflakes (F) - Logical errors
- ✅ flake8-bugbear (B) - Bug detection
- ✅ flake8-simplify (SIM) - Code simplification
- ✅ isort (I) - Import sorting
- ✅ pep8-naming (N) - Naming conventions
- ✅ pyupgrade (UP) - Modern Python syntax
- ✅ flake8-bandit (S) - Security issues
- ✅ flake8-comprehensions (C4) - List/dict comprehensions
- ✅ tryceratops (TRY) - Exception handling
- ✅ pylint (PL) - Code quality
- ✅ ruff-specific (RUF) - Ruff-specific rules

### Ignored Rules

- E501: Line too long (handled by Black)
- S101: Use of assert (allowed in tests)
- PLR0913: Too many arguments (acceptable in some cases)

---

## 🎓 Best Practices

### Type Hints

```python
# Use modern Python 3.10+ syntax
def process(data: str | None = None) -> dict[str, Any]:
    """Process data and return results."""
    return {}
```

### Logging

```python
# Use lazy formatting
logger.info("Processing %s items", count)

# Use exception() without passing exception
try:
    risky_operation()
except Exception:
    logger.exception("Operation failed")
```

### Docstrings

```python
def calculate_score(points: int, multiplier: int) -> int:
    """
    Calculate the final score.

    Args:
        points: Base points scored
        multiplier: Score multiplier (1, 2, or 3)

    Returns:
        Final calculated score
    """
    return points * multiplier
```

### Exception Handling

```python
# Catch specific exceptions when possible
try:
    result = risky_operation()
except ValueError as e:
    logger.error("Invalid value: %s", e)
except KeyError as e:
    logger.error("Missing key: %s", e)
```

---

## 🆘 Need Help?

### View Detailed Report

```bash
cat LINTING_STATUS.md
```

### Check Specific File

```bash
ruff check path/to/file.py
flake8 path/to/file.py
```

### Get Rule Documentation

```bash
# Ruff rule documentation
ruff rule <RULE_CODE>

# Example
ruff rule F821
```

---

## 📊 Statistics

- **Total Python Files**: 31
- **Primary Linters**: 4 (Ruff, Flake8, Black, isort)
- **Rule Sets Enabled**: 15+
- **Errors Fixed**: 22
- **Current Status**: ✅ ALL PASSING

---

**Last Updated**: 2025-01-XX
**Status**: ✅ ALL PRIMARY LINTERS PASSING
