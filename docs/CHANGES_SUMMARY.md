# Changes Summary

## Issues Fixed

### Issue 1: Adding Users Not Working

**Problem:** Adding users through the web control page wasn't working properly.

**Root Cause:**

- The add player button was sending empty objects when no name was provided
- The new game button was parsing player names from DOM display text that included scores, making it fragile

**Solution:**

- Modified `/static/js/control.js`:
  - Add player button now only emits events when a valid name is provided
  - New game button now extracts player names directly from `currentGameState` object instead of parsing DOM text

### Issue 2: Double-Out Feature for 301/401/501 Games

**Problem:** Need to add the standard darts rule where players must finish with a double to win.

**Solution:** Implemented comprehensive double-out feature across the entire stack:

## Files Modified

### 1. Frontend - Control Panel UI

**File:** `/templates/control.html`

- Added checkbox UI element for "Double Out" option in the game setup section (line 26)

### 2. Frontend - Control Panel JavaScript

**File:** `/static/js/control.js`

- Added DOM reference to the double-out checkbox
- Modified new game event to include `double_out` parameter
- Added logic to sync checkbox state with current game state
- Fixed player addition to only send valid names
- Fixed new game to extract player names from game state instead of DOM parsing

### 3. Backend - Flask API

**File:** `/app.py`

- Updated REST API endpoint `/api/game/new` to accept `double_out` parameter
- Updated WebSocket handler `new_game` to accept and pass `double_out` parameter
- Both handlers now pass the parameter to GameManager with default value of `False`

### 4. Game Manager

**File:** `/game_manager.py`

- Updated `new_game()` method signature to accept `double_out` parameter
- Modified Game301 instantiation to pass the double_out flag
- Enhanced logging to show double-out status when games start

### 5. Game Logic - 301/401/501 Games

**File:** `/games/game_301.py`

- Added `double_out` attribute to the Game301 class constructor
- Completely rewrote `process_throw()` method to implement double-out rules:
  - Added check for score of 1 (impossible to finish, results in bust)
  - When a player reaches exactly 0, checks if double-out is enabled
  - If double-out is enabled, validates that the finishing throw was a DOUBLE or DBLBULL
  - If not a double, treats it as a bust and restores the original score
- Updated `get_state()` to include the `double_out` setting in the game state
- Changed `_multiplier_type` parameter to `multiplier_type` since it's now actively used

### 6. Documentation - API Examples

**File:** `/examples/api_examples.py`

- Updated example_1 to show the `double_out` parameter
- Created new example_9 demonstrating a 501 game with double-out enabled
- Added the new example to the main execution flow

### 7. Tests

**File:** `/tests/unit/test_game_301.py`

- Added 7 comprehensive tests for double-out functionality:
  1. `test_double_out_enabled` - Verify game initialization with double-out
  2. `test_double_out_win_with_double` - Test winning with a double
  3. `test_double_out_bust_with_single` - Test bust when finishing with single
  4. `test_double_out_bust_with_triple` - Test bust when finishing with triple
  5. `test_double_out_win_with_double_bull` - Test winning with double bullseye
  6. `test_double_out_disabled_win_with_single` - Test normal win when disabled
  7. `test_double_out_bust_on_score_one` - Test bust on impossible score of 1

## Testing Results

All 26 tests pass successfully:

- 19 existing tests (backward compatibility maintained)
- 7 new double-out tests

```
tests/unit/test_game_301.py::TestGame301::test_double_out_enabled PASSED
tests/unit/test_game_301.py::TestGame301::test_double_out_win_with_double PASSED
tests/unit/test_game_301.py::TestGame301::test_double_out_bust_with_single PASSED
tests/unit/test_game_301.py::TestGame301::test_double_out_bust_with_triple PASSED
tests/unit/test_game_301.py::TestGame301::test_double_out_win_with_double_bull PASSED
tests/unit/test_game_301.py::TestGame301::test_double_out_disabled_win_with_single PASSED
tests/unit/test_game_301.py::TestGame301::test_double_out_bust_on_score_one PASSED

======================================= 26 passed in 0.13s ========================================
```

## Technical Details

### Double-Out Rules Implemented

1. **Valid Finishing Throws:** Only DOUBLE (outer ring) or DBLBULL (double bullseye) can finish the game
2. **Score of 1 is Bust:** Since you can't finish with a double from 1, hitting to 1 is treated as a bust
3. **Bust Handling:** On any bust (including failed double-out), the original score is restored
4. **Backward Compatibility:** Default value is `False`, so existing games work without changes

### Data Flow

UI Checkbox → WebSocket/REST API → GameManager → Game301 → Game Logic

### Key Implementation Points

- Optional parameter with sensible default (`False`) maintains backward compatibility
- Follows existing architecture patterns
- Consistent with existing multiplier type checking
- Preserves existing bust detection mechanism
- Game state includes double-out setting for UI synchronization

## How to Use

### Via Web Control Panel

1. Open the control panel
2. Check the "Double Out" checkbox when setting up a 301/401/501 game
3. Start the game
4. Players must finish with a double or double bullseye to win

### Via REST API

```python
import requests

response = requests.post(
    "http://localhost:5000/api/game/new",
    json={
        "game_type": "501",
        "players": ["Alice", "Bob"],
        "double_out": True
    }
)
```

### Via WebSocket

```javascript
socket.emit("new_game", {
  game_type: "301",
  players: ["Player 1", "Player 2"],
  double_out: true,
});
```

## Notes

- Double-out only applies to 301/401/501 games, not Cricket
- The feature is optional and disabled by default
- All existing functionality remains unchanged when double-out is disabled
- The UI checkbox state syncs with the current game state
