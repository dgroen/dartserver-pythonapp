# Single Player Support

## Overview

The Darts Game application now supports single-player games. You can remove players down to a single player and play solo.

## Changes Made

### 1. Updated `game_manager.py`

**Modified `remove_player()` method** (line 112-117):

- **Before**: Required minimum of 2 players
- **After**: Requires minimum of 1 player

```python
def remove_player(self, player_id):
    """Remove a player"""
    # Allow single player games - no minimum restriction
    if len(self.players) <= 1:
        print("Cannot remove player: at least 1 player required")
        return
```

## How to Use Single Player Mode

### Method 1: Start with Single Player

```python
# Via WebSocket
socket.emit('new_game', {
    'game_type': '301',  # or '401', '501', 'cricket'
    'players': ['Solo Player'],
    'double_out': False
});
```

```bash
# Via REST API
curl -X POST http://localhost:5000/api/game/new \
  -H "Content-Type: application/json" \
  -d '{
    "game_type": "301",
    "players": ["Solo Player"],
    "double_out": false
  }'
```

### Method 2: Remove Players to Get to Single Player

1. Start a game with multiple players
2. Use the control panel to remove players
3. Remove all but one player
4. Continue playing with single player

## Features in Single Player Mode

All game features work in single-player mode:

- ✅ **301/401/501 Games**: Track your score and try to reach exactly 0
- ✅ **Cricket Games**: Close all numbers and bulls
- ✅ **Double Out**: Practice finishing with doubles
- ✅ **Score Tracking**: All scores are tracked normally
- ✅ **Automatic UI Refresh**: UI updates in real-time
- ✅ **Sound Effects**: All sounds play normally
- ✅ **Statistics**: Track your performance

## Use Cases

### Practice Mode

Perfect for practicing your dart skills:

- Work on specific finishes
- Practice doubles
- Improve consistency

### Solo Challenges

Set personal goals:

- Finish a 501 game in minimum darts
- Close all Cricket numbers quickly
- Practice specific checkout combinations

### Training

Use single-player mode for:

- Warm-up before multiplayer games
- Testing new throwing techniques
- Building muscle memory

## Control Panel Usage

### Removing Players

1. Open the control panel: `http://localhost:5000/control`
2. View the list of current players
3. Click "Remove" next to any player
4. Confirm the removal
5. Continue until only one player remains

**Note**: You cannot remove the last remaining player - at least one player must remain in the game.

### Adding Players Back

You can add players back at any time:

1. Enter a player name in the "Player Name" field
2. Click "Add Player"
3. The new player joins with the starting score

## API Reference

### Remove Player via WebSocket

```javascript
socket.emit("remove_player", {
  player_id: 0, // Index of player to remove
});
```

### Remove Player via REST API

```bash
curl -X DELETE http://localhost:5000/api/players/0
```

**Response**:

```json
{
  "status": "success",
  "message": "Player removed"
}
```

**Error Cases**:

- Trying to remove the last player returns without error but doesn't remove
- Invalid player_id is ignored

## Testing Single Player Mode

### Interactive Test

```bash
# Terminal 1: Start the application
python app.py

# Terminal 2: Run the single-player test
python test_single_player.py
```

### Manual Test

1. Open browser: `http://localhost:5000/control`
2. Start a new game with 3 players
3. Remove players one by one
4. Verify you can get down to 1 player
5. Submit scores and verify they work correctly

## Technical Details

### Minimum Player Check

The `remove_player()` method now checks:

```python
if len(self.players) <= 1:
    print("Cannot remove player: at least 1 player required")
    return
```

This ensures:

- At least 1 player always remains
- Game state stays valid
- No crashes from empty player lists

### Game Logic

All game types support single player:

**301/401/501 Games** (`games/game_301.py`):

- Works with any number of players (1+)
- Turn management handles single player correctly
- Scoring and bust detection work normally

**Cricket Games** (`games/game_cricket.py`):

- Supports 1-4 players
- Target tracking works for single player
- Scoring logic unchanged

### Current Player Management

When removing players, the `current_player` index is adjusted:

```python
# Adjust current player if necessary
if self.current_player >= len(self.players):
    self.current_player = 0
```

This ensures the game continues smoothly even after player removal.

## Limitations

### Cannot Remove Last Player

You cannot remove the last remaining player. This is by design to:

- Prevent empty game states
- Ensure game logic always has a valid player
- Avoid crashes and undefined behavior

### Turn Management

In single-player mode:

- The single player always has the turn
- "Next Player" button has no effect (stays on same player)
- Turn counter still increments normally

## Future Enhancements

Potential improvements for single-player mode:

1. **Practice Mode Features**:
   - Timer to track game duration
   - Statistics dashboard
   - Personal best tracking
   - Checkout suggestions

2. **Challenge Mode**:
   - Predefined challenges
   - Score targets
   - Time limits
   - Achievement system

3. **AI Opponent**:
   - Computer player option
   - Difficulty levels
   - Learning AI

4. **Training Tools**:
   - Specific finish practice
   - Weak area identification
   - Progress tracking over time

## Troubleshooting

### Player Won't Remove

**Problem**: Clicking "Remove" doesn't remove the player

**Solutions**:

1. Check if it's the last player (cannot be removed)
2. Check browser console for errors
3. Verify WebSocket connection is active
4. Refresh the page and try again

### Game Behaves Oddly with One Player

**Problem**: Game seems stuck or doesn't progress

**Solutions**:

1. Submit a score to advance the turn
2. Check if game is paused
3. Start a new game if needed
4. Check server logs for errors

### UI Doesn't Update

**Problem**: Player list doesn't update after removal

**Solutions**:

1. Check WebSocket connection status
2. Open `/test-refresh` page to verify connectivity
3. Check browser console for Socket.IO errors
4. Refresh the page

## Summary

Single-player support is now fully functional in the Darts Game application. You can:

- ✅ Start games with a single player
- ✅ Remove players down to one
- ✅ Play all game types solo
- ✅ Track scores and progress
- ✅ Use all features normally

This makes the application perfect for practice, training, and solo play!
