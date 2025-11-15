# Round the Clock Hard Mode Feature

## Overview

The Round the Clock hard mode adds an optional difficulty increase where players are reset to target 20 after missing all 3 darts in a turn. This feature applies only to numbered targets (20-1) and does NOT apply to the bull/double-bull stage.

## Specification

### When Reset Occurs

A reset to target 20 happens when **all** of the following conditions are met:

1. Hard mode is enabled (`reset_on_miss=True`)
2. Player misses their current target with all 3 darts in a turn
3. Player's current target is between 1-20 (not at bull stage, target > 0)

### When Reset Does NOT Occur

- Hard mode is disabled (default behavior)
- Player hits their target at least once during the turn
- Player is at bull/double-bull stage (target = 0)
- Player misses fewer than 3 darts (turn ended early)

## API Usage

### REST API Endpoints

#### Start a new game with hard mode

**POST** `/api/game/new`

```json
{
  "game_type": "round_the_clock",
  "players": ["Player 1", "Player 2"],
  "reset_on_miss": true
}
```

**POST** `/api/game/start` (Mobile endpoint)

```json
{
  "game_type": "round_the_clock",
  "players": ["Player 1", "Player 2"],
  "reset_on_miss": true
}
```

### SocketIO Events

```javascript
socket.emit('new_game', {
  game_type: 'round_the_clock',
  players: ['Player 1', 'Player 2'],
  reset_on_miss: true
});
```

### Python API

```python
from src.games.game_round_the_clock import GameRoundTheClock

# Create game with hard mode enabled
game = GameRoundTheClock(
    players=[{"id": 0, "name": "Player 1"}],
    reset_on_miss=True
)

# Process throws
game.process_throw(0, 20, "SINGLE")  # Miss
game.process_throw(0, 19, "SINGLE")  # Miss
game.process_throw(0, 18, "SINGLE")  # Miss

# End turn - check for reset
result = game.end_turn(0)
if result["reset"]:
    print(result["message"])  # "Missed target! Reset to 20"
```

## Examples

### Example 1: Reset after 3 misses

```python
game = GameRoundTheClock([{"id": 0, "name": "Alice"}], reset_on_miss=True)
game.players[0]["current_target"] = 15

# Alice misses all 3 darts
game.process_throw(0, 20, "SINGLE")
game.process_throw(0, 19, "SINGLE")
game.process_throw(0, 18, "SINGLE")

result = game.end_turn(0)
# result["reset"] == True
# game.players[0]["current_target"] == 20
```

### Example 2: No reset with at least 1 hit

```python
game = GameRoundTheClock([{"id": 0, "name": "Bob"}], reset_on_miss=True)
game.players[0]["current_target"] = 15

# Bob hits target once, then misses twice
game.process_throw(0, 15, "SINGLE")  # Hit!
game.process_throw(0, 20, "SINGLE")  # Miss
game.process_throw(0, 19, "SINGLE")  # Miss

result = game.end_turn(0)
# result["reset"] == False
# game.players[0]["current_target"] == 14 (advanced due to hit)
```

### Example 3: No reset at bull stage

```python
game = GameRoundTheClock([{"id": 0, "name": "Charlie"}], reset_on_miss=True)
game.players[0]["current_target"] = 0  # Bull stage

# Charlie misses all 3 darts at bull
game.process_throw(0, 20, "SINGLE")
game.process_throw(0, 19, "SINGLE")
game.process_throw(0, 18, "SINGLE")

result = game.end_turn(0)
# result["reset"] == False (bull stage is exempt)
# game.players[0]["current_target"] == 0 (still at bull)
```

## Implementation Details

### Data Structure

Each player object includes:

```python
{
    "id": 0,
    "name": "Player 1",
    "current_target": 20,
    "is_turn": False,
    "bull_hits": 0,
    "turn_misses": 0  # New field for hard mode
}
```

### Turn Tracking

- `turn_misses` counter increments on each miss (when `current_target > 0`)
- Counter resets to 0 when:
  - Player hits their target
  - Turn ends (via `end_turn()` method)
  - Game is reset

### Game Flow Integration

The `GameManager` class automatically calls `game.end_turn(player_id)` at the end of each turn in `_end_turn()` method, which:

1. Checks if reset should occur
2. Applies reset if conditions are met
3. Emits appropriate messages to clients
4. Resets the turn_misses counter for next turn

## Testing

The feature includes comprehensive unit tests covering:

- Basic initialization with/without hard mode
- Miss counter increment/reset behavior
- Reset trigger after 3 misses
- No reset when hard mode disabled
- Bull stage exemption
- Partial miss scenarios
- Multi-player independence
- Edge cases and error handling

Run tests with:

```bash
pytest tests/unit/test_game_round_the_clock_hard_mode.py -v
```

## Backward Compatibility

- Feature is **disabled by default** (`reset_on_miss=False`)
- Existing games and API calls continue to work unchanged
- No database schema changes required
- Optional parameter in all API endpoints

## Security Summary

CodeQL analysis shows no security vulnerabilities introduced by this feature.
