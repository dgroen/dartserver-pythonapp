# dartserver-games

Game implementations for the Darts Game Server including 301, Cricket, and training modes.

## Features

- **Multiple Game Types** - 301, 401, 501, Cricket, Round the Clock, Bull Practice
- **Base Game Class** - Abstract base for consistent game interface
- **Rule Engine** - Configurable rules (double-out, reset-on-miss, etc)
- **Score Tracking** - Per-player, per-round score management
- **Game State** - Serializable game state for display/replay

## Installation

```bash
pip install dartserver-games
```

## Quick Start

### Load a Game

```python
from dartserver_games import GameFactory

# Create a 301 game
game = GameFactory.create('301', num_players=2)

# Or manually
from dartserver_games import Game301
game = Game301(num_players=2, double_out=True)
```

### Play the Game

```python
# Add players
game.add_player('Alice', 1)
game.add_player('Bob', 2)

# Submit scores
game.process_score({'zone': 20, 'modifier': 1})  # 20 points

# Get game state
state = game.get_game_state()
print(f"Current player: {state['current_player']}")
print(f"Score: {state['score']}")

# Check if finished
if game.is_finished():
    print(f"Winner: {game.winner}")
```

## Supported Games

| Game | Description | Module |
|------|-------------|--------|
| **301** | Standard darts game, count down from 301 | `game_301` |
| **401** | Count down from 401 | `game_301` |
| **501** | Count down from 501 | `game_301` |
| **Cricket** | Cricket target game | `game_cricket` |
| **Round the Clock** | Hit numbers 1-20 in order | `game_round_the_clock` |
| **Bull Practice** | Practice hitting bulls | `game_bull_practice` |

## Game Interface

### BaseGame (Abstract)

```python
class BaseGame:
    def add_player(self, name: str, player_id: int) -> None
    def process_score(self, score_data: dict) -> None
    def get_game_state(self) -> dict
    def is_finished(self) -> bool
    @property
    def winner(self) -> Optional[dict]
```

## Public Exports

- `BaseGame` - Abstract base class
- `Game301`, `Game401`, `Game501` - 300-series games
- `GameCricket` - Cricket game
- `GameRoundTheClock` - Round the clock game
- `GameBullPractice` - Bull practice game
- `GameFactory` - Factory for creating games by type
- `SUPPORTED_GAMES` - List of supported game types

## Configuration

Games support configurable rules:

```python
game = Game301(
    num_players=2,
    double_out=True,      # Must finish with double
    reset_on_miss=False,  # Reset score on miss
)
```

## Testing

```bash
pytest tests/
```

## License

MIT - See LICENSE file

## Contributing

Pull requests welcome. Please ensure tests pass.
