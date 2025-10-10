# Testing Guide

This document describes the testing setup and how to run tests for the dartserver-pythonapp.

## Table of Contents

- [Overview](#overview)
- [Test Structure](#test-structure)
- [Running Tests](#running-tests)
- [Test Coverage](#test-coverage)
- [Writing Tests](#writing-tests)
- [Continuous Integration](#continuous-integration)

## Overview

The project uses a comprehensive testing setup with:

- **pytest** - Testing framework
- **pytest-cov** - Coverage reporting
- **pytest-mock** - Mocking support
- **tox** - Testing across multiple Python versions
- **UV** - Fast package management

## Test Structure

```
tests/
├── __init__.py
├── conftest.py              # Shared fixtures
├── unit/                    # Unit tests
│   ├── __init__.py
│   ├── test_game_301.py
│   ├── test_game_cricket.py
│   └── test_game_manager.py
└── integration/             # Integration tests
    ├── __init__.py
    ├── test_app_endpoints.py
    └── test_game_scenarios.py
```

### Unit Tests

Unit tests focus on testing individual components in isolation:

- `test_game_301.py` - Tests for 301/401/501 game logic
- `test_game_cricket.py` - Tests for Cricket game logic
- `test_game_manager.py` - Tests for game manager

### Integration Tests

Integration tests verify that components work together:

- `test_app_endpoints.py` - Tests for Flask API endpoints
- `test_game_scenarios.py` - Tests for complete game scenarios

## Running Tests

### Quick Start

```bash
# Run all tests
make test

# Run with coverage
make test-cov

# Run only unit tests
make test-unit

# Run only integration tests
make test-integration
```

### Using pytest directly

```bash
# Run all tests
pytest

# Run with verbose output
pytest -v

# Run specific test file
pytest tests/unit/test_game_301.py

# Run specific test
pytest tests/unit/test_game_301.py::TestGame301::test_initialization_default

# Run tests matching pattern
pytest -k "test_301"

# Run with coverage
pytest --cov=. --cov-report=html
```

### Using tox

Tox runs tests across multiple Python versions and environments:

```bash
# Run all tox environments
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

## Test Coverage

### Viewing Coverage

```bash
# Generate coverage report
make coverage

# View HTML coverage report
open htmlcov/index.html  # macOS
xdg-open htmlcov/index.html  # Linux
```

### Coverage Requirements

- Minimum coverage: **80%**
- Coverage is enforced in CI/CD
- Uncovered lines are reported in terminal

### Coverage Configuration

Coverage settings are in `pyproject.toml`:

```toml
[tool.coverage.run]
source = ["."]
omit = ["*/tests/*", "*/examples/*"]
branch = true

[tool.coverage.report]
precision = 2
show_missing = true
fail_under = 80
```

## Writing Tests

### Test Fixtures

Common fixtures are defined in `tests/conftest.py`:

```python
@pytest.fixture
def mock_socketio():
    """Mock SocketIO instance."""
    mock = MagicMock()
    mock.emit = MagicMock()
    return mock

@pytest.fixture
def sample_players():
    """Sample player data for testing."""
    return [
        {"id": 0, "name": "Player 1"},
        {"id": 1, "name": "Player 2"},
    ]
```

### Writing Unit Tests

```python
"""Unit tests for Game301 class."""
import pytest
from games.game_301 import Game301

class TestGame301:
    """Test cases for Game301 class."""

    def test_initialization_default(self, sample_players):
        """Test game initialization with default score."""
        game = Game301(sample_players)
        assert game.start_score == 301
        assert len(game.players) == 2
```

### Writing Integration Tests

```python
"""Integration tests for Flask endpoints."""
import json

class TestAppEndpoints:
    """Test Flask application endpoints."""

    def test_new_game_301(self, client):
        """Test starting new 301 game."""
        response = client.post(
            "/api/game/new",
            data=json.dumps({"game_type": "301", "players": ["Alice", "Bob"]}),
            content_type="application/json",
        )
        assert response.status_code == 200
```

### Test Markers

Use markers to categorize tests:

```python
@pytest.mark.unit
def test_something():
    """Unit test."""
    pass

@pytest.mark.integration
def test_integration():
    """Integration test."""
    pass

@pytest.mark.slow
def test_slow_operation():
    """Slow test."""
    pass

@pytest.mark.rabbitmq
def test_rabbitmq_connection():
    """Test requiring RabbitMQ."""
    pass
```

Run specific markers:

```bash
pytest -m unit
pytest -m integration
pytest -m "not slow"
```

## Continuous Integration

### CI Pipeline

The CI pipeline runs:

1. **Linting** - Code quality checks
2. **Type Checking** - Static type analysis
3. **Security** - Security vulnerability scanning
4. **Tests** - All tests with coverage
5. **Coverage Report** - Generate and upload coverage

### Simulating CI Locally

```bash
# Run full CI pipeline
make ci

# Or step by step
make clean
make install-dev
make lint
make type
make security
make test
make coverage
```

## Test Best Practices

### 1. Test Naming

- Use descriptive names: `test_process_throw_triple`
- Follow pattern: `test_<what>_<condition>_<expected>`

### 2. Test Organization

- One test class per class being tested
- Group related tests together
- Use fixtures for common setup

### 3. Test Independence

- Tests should not depend on each other
- Each test should set up its own state
- Clean up after tests if needed

### 4. Assertions

- Use specific assertions: `assert x == 5` not `assert x`
- One logical assertion per test
- Use pytest's assertion introspection

### 5. Mocking

- Mock external dependencies (RabbitMQ, SocketIO)
- Don't mock the code under test
- Use `pytest-mock` for cleaner mocks

### 6. Coverage

- Aim for high coverage but focus on meaningful tests
- Test edge cases and error conditions
- Don't write tests just for coverage

## Troubleshooting

### Tests Failing

```bash
# Run with verbose output
pytest -vv

# Show print statements
pytest -s

# Stop on first failure
pytest -x

# Run last failed tests
pytest --lf
```

### Coverage Issues

```bash
# Show missing lines
pytest --cov=. --cov-report=term-missing

# Generate detailed HTML report
pytest --cov=. --cov-report=html
open htmlcov/index.html
```

### Import Errors

```bash
# Ensure package is installed in editable mode
uv pip install -e .

# Check Python path
python -c "import sys; print(sys.path)"
```

## Additional Resources

- [pytest documentation](https://docs.pytest.org/)
- [pytest-cov documentation](https://pytest-cov.readthedocs.io/)
- [tox documentation](https://tox.wiki/)
- [Coverage.py documentation](https://coverage.readthedocs.io/)

Coverage settings are in `pyproject.toml`:

```toml
[tool.coverage.run]
source = ["."]
omit = ["*/tests/*", "*/examples/*"]
branch = true

[tool.coverage.report]
precision = 2
show_missing = true
fail_under = 80
```

## Writing Tests

### Test Fixtures

Common fixtures are defined in `tests/conftest.py`:

```python
@pytest.fixture
def mock_socketio():
    """Mock SocketIO instance."""
    mock = MagicMock()
    mock.emit = MagicMock()
    return mock

@pytest.fixture
def sample_players():
    """Sample player data for testing."""
    return [
        {"id": 0, "name": "Player 1"},
        {"id": 1, "name": "Player 2"},
    ]
```

### Writing Unit Tests

```python
"""Unit tests for Game301 class."""
import pytest
from games.game_301 import Game301

class TestGame301:
    """Test cases for Game301 class."""

    def test_initialization_default(self, sample_players):
        """Test game initialization with default score."""
        game = Game301(sample_players)
        assert game.start_score == 301
        assert len(game.players) == 2
```

### Writing Integration Tests

```python
"""Integration tests for Flask endpoints."""
import json

class TestAppEndpoints:
    """Test Flask application endpoints."""

    def test_new_game_301(self, client):
        """Test starting new 301 game."""
        response = client.post(
            "/api/game/new",
            data=json.dumps({"game_type": "301", "players": ["Alice", "Bob"]}),
            content_type="application/json",
        )
        assert response.status_code == 200
```

### Test Markers

Use markers to categorize tests:

```python
@pytest.mark.unit
def test_something():
    """Unit test."""
    pass

@pytest.mark.integration
def test_integration():
    """Integration test."""
    pass

@pytest.mark.slow
def test_slow_operation():
    """Slow test."""
    pass

@pytest.mark.rabbitmq
def test_rabbitmq_connection():
    """Test requiring RabbitMQ."""
    pass
```

Run specific markers:

```bash
pytest -m unit
pytest -m integration
pytest -m "not slow"
```

## Continuous Integration

### CI Pipeline

The CI pipeline runs:

1. **Linting** - Code quality checks
2. **Type Checking** - Static type analysis
3. **Security** - Security vulnerability scanning
4. **Tests** - All tests with coverage
5. **Coverage Report** - Generate and upload coverage

### Simulating CI Locally

```bash
# Run full CI pipeline
make ci

# Or step by step
make clean
make install-dev
make lint
make type
make security
make test
make coverage
```

## Test Best Practices

### 1. Test Naming

- Use descriptive names: `test_process_throw_triple`
- Follow pattern: `test_<what>_<condition>_<expected>`

### 2. Test Organization

- One test class per class being tested
- Group related tests together
- Use fixtures for common setup

### 3. Test Independence

- Tests should not depend on each other
- Each test should set up its own state
- Clean up after tests if needed

### 4. Assertions

- Use specific assertions: `assert x == 5` not `assert x`
- One logical assertion per test
- Use pytest's assertion introspection

### 5. Mocking

- Mock external dependencies (RabbitMQ, SocketIO)
- Don't mock the code under test
- Use `pytest-mock` for cleaner mocks

### 6. Coverage

- Aim for high coverage but focus on meaningful tests
- Test edge cases and error conditions
- Don't write tests just for coverage

## Troubleshooting

### Tests Failing

```bash
# Run with verbose output
pytest -vv

# Show print statements
pytest -s

# Stop on first failure
pytest -x

# Run last failed tests
pytest --lf
```

### Coverage Issues

```bash
# Show missing lines
pytest --cov=. --cov-report=term-missing

# Generate detailed HTML report
pytest --cov=. --cov-report=html
open htmlcov/index.html
```

### Import Errors

```bash
# Ensure package is installed in editable mode
uv pip install -e .

# Check Python path
python -c "import sys; print(sys.path)"
```

## Additional Resources

- [pytest documentation](https://docs.pytest.org/)
- [pytest-cov documentation](https://pytest-cov.readthedocs.io/)
- [tox documentation](https://tox.wiki/)
- [Coverage.py documentation](https://coverage.readthedocs.io/)
