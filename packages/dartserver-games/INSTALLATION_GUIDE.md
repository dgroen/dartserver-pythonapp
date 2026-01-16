# Dartserver Games - Installation Guide

## Installation

### From PyPI (Once Published)

```bash
pip install dartserver-games
```

### Local Development Installation

For development purposes, you can install the package locally:

```bash
cd packages/dartserver-games
pip install -e ".[dev]"
```

The `-e` flag installs the package in editable mode, so changes to the source code are immediately reflected.

### Dependencies

- **Required:**
  - Python 3.10 or later
  - dartserver-core >= 1.0.0

- **Optional (Development):**
  - pytest >= 7.4.0
  - pytest-cov >= 4.1.0
  - black >= 23.0.0
  - ruff >= 0.1.0
  - mypy >= 1.7.0

## Verifying Installation

After installation, verify the package is working correctly:

```bash
python -c "from dartserver_games import Game301, GameCricket; print('✓ dartserver-games installed successfully')"
```

## Usage in Your Application

### Basic Integration

```python
from dartserver_games import Game301, GameCricket, BaseGame

# Initialize players
players = [
    {"id": 0, "name": "Alice"},
    {"id": 1, "name": "Bob"},
]

# Create a game instance
game = Game301(players, start_score=301, double_out=True)

# Process dart throws
result = game.process_score(20, "TRIPLE")

# Check game state
state = game.get_state()
```

### Importing Specific Games

```python
# Import only what you need
from dartserver_games import (
    Game301,
    GameCricket,
    GameRoundTheClock,
    GameRoundTheClockDouble,
    GameBullPractice,
    BaseGame,  # For type hints
)
```

### Type Hints

For better IDE support and type checking, use type hints:

```python
from dartserver_games import BaseGame, Game301
from typing import Dict, Any

def create_game(game_type: str, players: list[Dict[str, Any]]) -> BaseGame:
    if game_type == "301":
        return Game301(players)
    # ... other game types
```

## Development Setup

### Clone the Repository

```bash
git clone <repository-url>
cd dartserver-pythonapp
```

### Install in Development Mode

```bash
cd packages/dartserver-games
pip install -e ".[dev]"
```

### Run Tests

```bash
# Run all tests
pytest tests/

# Run with coverage report
pytest tests/ --cov=src/dartserver_games --cov-report=html

# Run specific test file
pytest tests/test_game_301.py

# Run specific test class
pytest tests/test_game_301.py::TestGame301

# Run specific test
pytest tests/test_game_301.py::TestGame301::test_initialization_default
```

### Code Quality

```bash
# Format code with black
black src/ tests/

# Lint with ruff
ruff check src/ tests/ --fix

# Type check with mypy
mypy src/

# All quality checks
black src/ tests/ && ruff check src/ tests/ && mypy src/ && pytest tests/
```

## Troubleshooting

### ImportError: No module named 'dartserver_games'

**Solution:** Make sure the package is installed correctly:
```bash
pip install -e ".[dev]"
# or
pip install dartserver-games
```

### ImportError: No module named 'dartserver_core'

**Solution:** Install the dartserver-core dependency:
```bash
pip install dartserver-core
```

### ModuleNotFoundError when importing games

**Solution:** Make sure you're in the correct directory or have installed the package in editable mode:
```bash
cd packages/dartserver-games
pip install -e .
```

### Tests fail with fixture errors

**Solution:** Make sure pytest can find the conftest.py file. Run tests from the package directory:
```bash
cd packages/dartserver-games
pytest tests/
```

## Publishing to PyPI

### Preparation

1. Update version in `pyproject.toml`
2. Update `CHANGELOG.md`
3. Create a git tag: `git tag v1.0.0`

### Build Distribution

```bash
pip install build
python -m build
```

### Upload to PyPI

```bash
pip install twine
twine upload dist/*
```

For test PyPI:
```bash
twine upload --repository-url https://test.pypi.org/legacy/ dist/*
```

## Next Steps

- Read the [README.md](README.md) for API documentation
- Check the [tests](tests/) directory for usage examples
- Review the main [dartserver-pythonapp](../../) for integration examples

## Support

For issues, questions, or contributions, refer to the main dartserver-pythonapp repository.
