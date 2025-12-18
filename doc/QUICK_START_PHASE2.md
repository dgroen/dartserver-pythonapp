# Phase 2 Quick Start - Dartserver Games Package

Get up and running with the dartserver-games package in 5 minutes.

## What Was Done

The dartserver-games package extracts all game logic (301, Cricket, Round the Clock, etc.) from the monolith into a standalone, reusable Python package.

## Installation

### Option 1: Install in Development Mode (Recommended)

```bash
cd packages/dartserver-games
pip install -e .
```

### Option 2: Install with Development Tools

```bash
cd packages/dartserver-games
pip install -e ".[dev]"
```

## Quick Test

Verify the package works:

```python
from dartserver_games import Game301, GameCricket

# Create a game
players = [
    {"id": 0, "name": "Alice"},
    {"id": 1, "name": "Bob"},
]

game = Game301(players, start_score=301)

# Process a dart throw (20 triple)
result = game.process_score(20, "TRIPLE")
print(result)
# Output: {'player_id': 0, 'score': 60, 'new_total': 241, 'bust': False, 'winner': False}
```

## What Changed

### Main Application

**Before:**
```python
from src.games.game_301 import Game301
from src.games.game_cricket import GameCricket
# ...
```

**After:**
```python
from dartserver_games import Game301, GameCricket
# ...
```

### Import Location

Old: `from src.games.game_xxx import GameXxx`
New: `from dartserver_games import GameXxx`

## Available Games

Import any or all game types:

```python
from dartserver_games import (
    BaseGame,                    # Abstract base class
    Game301,                     # 301/401/501
    GameCricket,                 # Cricket
    GameRoundTheClock,           # Round the Clock
    GameRoundTheClockDouble,     # Round the Clock (double bull)
    GameBullPractice,            # Bull practice
)
```

## Key Features

- **5 Game Types**: 301, Cricket, Round the Clock, Round the Clock Double, Bull Practice
- **Clean API**: Consistent interface across all games
- **Type Hints**: Full Python type annotations
- **Well Tested**: Comprehensive test coverage
- **Production Ready**: Ready for PyPI publishing

## Development

### Run Tests

```bash
cd packages/dartserver-games
pytest tests/
```

### Code Quality

```bash
# Format
black src/ tests/

# Lint
ruff check src/ tests/

# Type check
mypy src/

# All together
black src/ tests/ && ruff check src/ tests/ && mypy src/
```

## Project Layout

```
packages/dartserver-games/
├── src/dartserver_games/       # Source code
│   ├── __init__.py             # Public API
│   ├── base.py                 # Abstract base class
│   ├── game_301.py             # 301/401/501 logic
│   ├── game_cricket.py         # Cricket logic
│   ├── game_round_the_clock.py # Round the Clock logic
│   ├── game_round_the_clock_double.py
│   └── game_bull_practice.py   # Bull practice logic
│
├── tests/                       # Test suite
│   ├── conftest.py             # Fixtures
│   ├── test_core.py            # Package tests
│   ├── test_game_301.py
│   ├── test_game_cricket.py
│   └── ...
│
├── pyproject.toml              # Package config
├── README.md                   # Full documentation
└── INSTALLATION_GUIDE.md       # Detailed setup
```

## Using in Your Code

### Basic Usage

```python
from dartserver_games import Game301

# Initialize
players = [{"id": 0, "name": "Player 1"}, {"id": 1, "name": "Player 2"}]
game = Game301(players)

# Process throw
result = game.process_score(20, "TRIPLE")

# Check state
state = game.get_state()
print(state["players"][0]["score"])  # Current score
```

### Type Hints

```python
from dartserver_games import BaseGame
from typing import Dict, Any, List

def run_game(game: BaseGame) -> Dict[str, Any]:
    """Play a game and return final state."""
    # Use game through abstract interface
    return game.get_state()
```

## Next Steps

- Read the [README.md](README.md) for full API documentation
- Check [INSTALLATION_GUIDE.md](INSTALLATION_GUIDE.md) for advanced setup
- Review [tests/](tests/) for usage examples

## Files Modified

- `src/app/game_manager.py` - Updated imports to use dartserver_games package

## Files Created

- `packages/dartserver-games/` - Complete new package (17 files)
- `doc/PHASE2_COMPLETE.md` - Phase 2 completion summary

## Support

For questions or issues, refer to:
- Package README: [README.md](README.md)
- Installation Guide: [INSTALLATION_GUIDE.md](INSTALLATION_GUIDE.md)
- Main refactoring docs: [../doc/REFACTORING_PLAN.md](../doc/REFACTORING_PLAN.md)
