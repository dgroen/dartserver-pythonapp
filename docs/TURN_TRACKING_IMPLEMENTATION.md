# Turn Tracking and Bust Undo Implementation

## Overview
This document explains how the turn tracking and bust undo feature works in the dart game application. When a player busts (goes below zero or violates game rules), all throws made during that turn are automatically undone, restoring the game state to the beginning of the turn.

## Key Components

### 1. Turn Tracking Variables (lines 33-35 in game_manager.py)
```python
# Turn tracking for undo on bust
self.turn_throws = []  # List of throws in current turn
self.turn_start_state = None  # Game state at start of turn
```

- **`turn_throws`**: Records each throw made during the current turn (base_score, multiplier, throw_number)
- **`turn_start_state`**: Deep copy of the complete game state at the beginning of the turn

### 2. State Management Methods

#### `_save_turn_start_state()` (lines 441-447)
- Called at the start of each turn (new game, next player, skip to player)
- Creates a deep copy of the entire game state
- Preserves player scores and (for Cricket) target hits/status
- Uses Python's `copy.deepcopy()` to prevent reference issues

#### `_restore_turn_start_state()` (lines 449-472)
- Called when a bust occurs
- Restores the saved game state
- Handles both game types:
  - **301/401/501**: Restores player scores
  - **Cricket**: Restores scores AND target hits/status
- Uses deep copy to ensure proper restoration

### 3. Turn Lifecycle

#### Turn Start
When a turn begins (via `new_game()`, `next_player()`, or `skip_to_player()`):
1. Reset `turn_throws` to empty list
2. Call `_save_turn_start_state()` to capture current state

#### During Turn
In `process_score()` (lines 181-187):
1. Before processing each throw, record it in `turn_throws`:
   ```python
   throw_data = {
       "base_score": base_score,
       "multiplier": multiplier,
       "throw_number": self.current_throw,
   }
   self.turn_throws.append(throw_data)
   ```
2. Process the throw normally
3. Check for bust, winner, or turn completion

#### Bust Handling
In `_handle_bust()` (lines 326-340):
1. Call `_restore_turn_start_state()` to undo all throws
2. Set game to paused state
3. Emit bust message and effects
4. Print debug info showing how many throws were undone

## Example Scenario

### Normal Turn (No Bust)
```
Player starts with score: 301
Throw 1: Single 20 → Score: 281 (tracked)
Throw 2: Triple 19 → Score: 224 (tracked)
Throw 3: Double 18 → Score: 188 (tracked)
Turn ends → Reset tracking for next player
```

### Turn with Bust
```
Player starts with score: 100
Turn start state saved: {score: 100}

Throw 1: Single 20 → Score: 80 (tracked)
Throw 2: Triple 15 → Score: 35 (tracked)
Throw 3: Single 50 → BUST! (would be -15)

Bust detected → Restore state → Score: 100
All 3 throws undone!
```

## Technical Details

### Why Deep Copy?
Using `copy.deepcopy()` is critical because:
- Game state contains nested dictionaries (players, targets, etc.)
- Shallow copy would only copy references, not actual data
- Changes to current state would affect saved state
- Deep copy ensures complete isolation

### Game Type Support
The implementation handles both game types correctly:

**301/401/501 Games:**
- Only need to restore player scores
- Simple numeric restoration

**Cricket Games:**
- Must restore scores AND target hits
- Each target has hits count and status (open/closed)
- Requires deep copy of targets dictionary

### Performance Considerations
- Deep copying happens once per turn (minimal overhead)
- State size is small (player data only)
- No performance impact observed in testing
- Could be optimized if many players (>10) cause issues

## Testing

Comprehensive tests in `tests/unit/test_game_manager.py`:
- `test_turn_tracking_initialization`: Verifies initial state
- `test_turn_tracking_on_new_game`: Confirms setup on game start
- `test_turn_tracking_records_throws`: Validates throw recording
- `test_turn_tracking_resets_on_next_player`: Tests turn reset
- `test_bust_undoes_all_throws_in_turn_301`: Core functionality test
- `test_save_and_restore_turn_state_301`: State management for 301
- `test_save_and_restore_turn_state_cricket`: State management for Cricket
- `test_multiple_throws_then_bust`: Integration test

All 134 unit tests pass ✓

## Demo Script

Run the demonstration:
```bash
python examples/demo_turn_tracking.py
```

This shows:
1. Normal turn with throw tracking
2. Turn with bust (all throws undone)
3. Cricket game turn tracking

## Future Enhancements

Potential extensions of this feature:
1. **Multi-turn undo**: Store history of multiple turns
2. **Turn statistics**: Use `turn_throws` for analytics
3. **Replay functionality**: Replay throws from history
4. **Undo button**: Manual undo of last throw or turn
5. **Turn history UI**: Display throw history to players

## Code Quality

- ✓ All 134 unit tests pass
- ✓ No linting issues (ruff)
- ✓ No security issues (bandit)
- ✓ Maintains existing code style
- ✓ Backward compatible with existing functionality