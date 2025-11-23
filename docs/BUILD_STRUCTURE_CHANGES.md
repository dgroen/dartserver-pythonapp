# Build Structure Changes

This document summarizes the changes made to reorganize the build output structure.

## New Directory Structure

```
dartserver-pythonapp/
├── docs/                          # All documentation (NEW)
│   ├── source/                    # Documentation source files
│   ├── build/                     # Generated documentation (gitignored)
│   └── README.md                  # Documentation guide
│
├── build/                         # All build artifacts
│   ├── coverage/                  # All coverage files (NEW)
│   │   ├── html/                  # HTML coverage reports
│   │   ├── html-py310/            # Python 3.10 coverage HTML
│   │   ├── html-py311/            # Python 3.11 coverage HTML
│   │   ├── html-py312/            # Python 3.12 coverage HTML
│   │   ├── coverage.xml           # Combined coverage XML
│   │   ├── coverage.json          # Combined coverage JSON
│   │   ├── coverage-py310.xml     # Python 3.10 coverage XML
│   │   ├── coverage-py311.xml     # Python 3.11 coverage XML
│   │   ├── coverage-py312.xml     # Python 3.12 coverage XML
│   │   ├── .coverage              # Coverage data file
│   │   └── .coverage.{envname}    # Per-environment coverage data
│   │
│   ├── reports/                   # Test and build reports (NEW)
│   │   ├── junit.xml              # Combined JUnit test report
│   │   ├── junit-py310.xml        # Python 3.10 JUnit report
│   │   ├── junit-py311.xml        # Python 3.11 JUnit report
│   │   └── junit-py312.xml        # Python 3.12 JUnit report
│   │
│   ├── lib/                       # Built packages (existing)
│   └── bdist.*/                   # Binary distributions (existing)
```

## Changes Made

### 1. Configuration Files Updated

#### `pyproject.toml`

- Updated `[tool.coverage.html]` directory to `build/coverage/html`
- Updated `[tool.coverage.xml]` output to `build/coverage/coverage.xml`
- Added `[tool.coverage.json]` output to `build/coverage/coverage.json`
- Updated `[tool.coverage.run]` data_file to `build/coverage/.coverage`
- Added `build/` and `docs/` to coverage omit patterns
- Added `docs/` to mypy exclude patterns
- Updated pytest addopts to use new paths for coverage and junit reports

#### `tox.ini`

- Updated `COVERAGE_FILE` environment variable to `build/coverage/.coverage.{envname}`
- Updated all coverage report paths to `build/coverage/`
- Updated junit-xml paths to `build/reports/junit-{envname}.xml`
- Updated `[testenv:coverage-report]` to use new paths
- Updated `[testenv:docs]` to build from `docs/source` to `docs/build/html`
- Updated `[testenv:clean]` to clean new directory structure

#### `Makefile`

- Updated `test-cov` target to use new coverage and report paths
- Updated `coverage` target to generate reports in `build/coverage/`
- Updated `clean` target to clean new directory structure
- Added `docs` target to build documentation

#### `.gitignore`

- Updated to ignore `build/coverage/*` and `build/reports/*` contents
- Added `.gitkeep` exceptions to preserve directory structure
- Added `docs/build/` and `docs/source/*` to ignore list
- Removed old patterns for `htmlcov/`, `.coverage`, `coverage*.xml`, `junit*.xml`

### 2. New Files Created

- `docs/README.md` - Documentation guide
- `docs/source/.gitkeep` - Preserve source directory
- `build/README.md` - Build directory guide
- `build/coverage/.gitkeep` - Preserve coverage directory
- `build/reports/.gitkeep` - Preserve reports directory

## Migration Notes

### Old Locations → New Locations

| Old Location                    | New Location                        |
| ------------------------------- | ----------------------------------- |
| `htmlcov/`                      | `build/coverage/html/`              |
| `htmlcov-py310/`                | `build/coverage/html-py310/`        |
| `htmlcov-py311/`                | `build/coverage/html-py311/`        |
| `htmlcov-py312/`                | `build/coverage/html-py312/`        |
| `coverage.xml`                  | `build/coverage/coverage.xml`       |
| `coverage.json`                 | `build/coverage/coverage.json`      |
| `coverage-py310.xml`            | `build/coverage/coverage-py310.xml` |
| `coverage-py311.xml`            | `build/coverage/coverage-py311.xml` |
| `coverage-py312.xml`            | `build/coverage/coverage-py312.xml` |
| `.coverage`                     | `build/coverage/.coverage`          |
| `.coverage.py310`               | `build/coverage/.coverage.py310`    |
| `.coverage.py311`               | `build/coverage/.coverage.py311`    |
| `.coverage.py312`               | `build/coverage/.coverage.py312`    |
| `junit-py310.xml`               | `build/reports/junit-py310.xml`     |
| `junit-py311.xml`               | `build/reports/junit-py311.xml`     |
| `junit-py312.xml`               | `build/reports/junit-py312.xml`     |
| Documentation files (scattered) | `docs/`                             |

## Usage

All existing commands continue to work as before:

```bash
# Run tests with coverage
make test-cov

# Generate coverage report
make coverage

# Run tox tests
make tox

# Build documentation
make docs

# Clean build artifacts
make clean
```

The only difference is that all output files are now organized in the new directory structure.

## Benefits

1. **Better Organization**: All related files are grouped together
2. **Cleaner Root Directory**: No more scattered coverage and report files
3. **Easier CI/CD Integration**: Standard paths for artifacts
4. **Consistent Structure**: Follows common Python project conventions
5. **Documentation Centralization**: All docs in one place
6. **Easier Cleanup**: Single `build/` directory to clean

## Backward Compatibility

All existing make targets and tox commands work exactly as before. The only change is where the output files are stored.
