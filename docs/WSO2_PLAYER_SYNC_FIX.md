# WSO2 Player Synchronization Fix

## Problem Resolved

The system was creating **phantom players** (players without a WSO2 connection) whenever:
- A game was played with a player name only (no WSO2 user)
- A player was added manually without WSO2 authentication

This caused **game results to be stored under wrong player IDs**, breaking the connection between:
- **Logged-in user** (Dennis with player_id=11)
- **Games in database** (stored under phantom player with UUID name, player_id=21)

## Root Cause

In `database_service.py`, the `start_new_game()` method was creating players by name only:

```python
# OLD (WRONG) - Created phantom players
player = session.query(Player).filter_by(name=player_name).first()
if not player:
    player = Player(name=player_name)  # ← Creates phantom!
    session.add(player)
```

This violated the architecture principle:
> **Only WSO2-authenticated users should have game results recorded**

## Solution Implemented

### 1. Database Relationship Enforcement
**File**: `src/core/database_service.py`

- **Modified `start_new_game()`**: Now requires `player_ids` (database IDs) instead of `player_names`
- **Modified `get_or_create_player()`**: Requires `username` (WSO2 user) to create a player
  - Validates that only WSO2-authenticated users are added
  - Exception: `bypass_user` for local development

```python
# NEW (CORRECT) - Only WSO2 users allowed
def get_or_create_player(self, name, username=None, email=None):
    """
    IMPORTANT: Only players with username (WSO2 users) can be created
    Exception: Special users like "bypass_user"
    """
    if not username:
        print("Cannot create player without username")
        return None
```

### 2. Game Manager Updates
**File**: `src/app/game_manager.py`

- **Modified `new_game()`**: Accepts `player_ids` parameter (WSO2 player IDs)
- **Modified game recording**: Validates all players have `db_id` before saving
  - Raises clear error if players missing database IDs
  - Ensures game results only created for WSO2 users

```python
# Validate that all players have database IDs
missing_ids = [i for i, pid in enumerate(player_ids) if not pid]
if missing_ids:
    raise ValueError(
        f"Cannot save game: Players missing database IDs "
        f"(only WSO2 users allowed)"
    )
```

### 3. API Endpoint Enforcement
**File**: `src/app/app.py`

- **Modified `/api/players` (POST)**: Now requires `username` (WSO2 lookup)
  - Rejects manual player entry
  - Only allows adding existing WSO2 users to games
  - Clear error messages explain the requirement

```python
# NEW - WSO2-only enforcement
if not username:
    return jsonify({
        "success": False,
        "error": "Username is required. Only WSO2-authenticated users can be added."
    }), 400
```

## Data Model

```
WSO2 User (e.g., "dennis")
    ↓
Player (id=11, username="dennis", name="Dennis")
    ↓
GameResult (player_id=11) ← One-to-many relationship
    ↓
Score (player_id=11)     ← Per-throw tracking
```

## Database Cleanup

### Step 1: Identify Phantom Players

```bash
python helpers/cleanup_phantom_players.py
```

Output shows:
- Phantom players (no username)
- Games affected by each phantom player
- Database summary

### Step 2: Delete Phantom Players

```bash
python helpers/cleanup_phantom_players.py --commit
```

**Example Output**:
```
🔍 Found 1 phantom player (no username):

  ID: 21
  Name: 049198fa-75dc-492e-a830-c755c3883e3b
  Games: 0

⚠️  SUMMARY:
   Total phantom players: 1
   Total games affected: 0

🗑️  Deleting phantom players...
✅ Cleanup complete!
```

### Step 3: Verify Dennis Has Correct Player ID

```bash
psql -U your_user -d your_db -c "SELECT id, name, username FROM player WHERE name='Dennis';"
```

Should return:
```
id | name  | username
----+-------+----------
11 | Dennis| dennis   (or empty if no WSO2 user yet)
```

## Usage After Fix

### Starting a Game with WSO2 Users

```python
# ALL players MUST have database IDs (must be WSO2 users)

# Example: Start game with logged-in user + opponent
logged_in_player_id = 11  # Dennis
opponent_player_id = 12   # Charlie

game_manager.new_game(
    game_type="301",
    player_ids=[logged_in_player_id, opponent_player_id],
    start_score=501,
    double_out=True
)
```

### Adding Players to Game

```bash
# API call to add a player
POST /api/players
{
    "username": "charlie"  # ← REQUIRED (WSO2 username)
}

# Response:
{
    "status": "success",
    "player": {
        "name": "Charlie",
        "email": "charlie@example.com",
        "player_id": 12
    }
}
```

## Architecture Benefits

✅ **Single Source of Truth**: Players only exist in WSO2 + database
✅ **Referential Integrity**: All game results link to real WSO2 users
✅ **Clear Relationships**: Username → Player ID → Game Results → Scores
✅ **No Orphaned Data**: Can't create phantom player without username
✅ **Easy Auditing**: Can trace any game to its WSO2 user

## Backward Compatibility

⚠️ **BREAKING CHANGE**: 
- Manual player creation (no WSO2 username) is NO LONGER ALLOWED
- Old game results with phantom players should be deleted (cleanup script provided)
- New games MUST have all players registered in WSO2

## Exception: bypass_user

For local development/testing:

```python
# In auth.py - bypass_user is special exception
player = game_manager.db_service.get_or_create_player(
    username="bypass_user",  # ← Special development user
    email="bypass@local.dev",
    name="Bypass User",
)
```

## Migration Path

For existing production systems:

1. **Identify all phantom players**: 
   ```bash
   psql -c "SELECT id, name FROM player WHERE username IS NULL AND name != 'Bypass User';"
   ```

2. **Contact players to register in WSO2** if their games need to be preserved

3. **Delete phantom players and old game results**:
   ```bash
   python helpers/cleanup_phantom_players.py --commit
   ```

4. **Players login via WSO2** to auto-create their player record

5. **Players are automatically linked** on future logins

## Testing

### Test 1: Only WSO2 Users Can Play

```bash
# Try to start game without player IDs
curl -X POST http://localhost:5000/api/game/start \
  -H "Content-Type: application/json" \
  -d '{"game_type": "301", "players": ["Manual Player"]}'

# Should fail with: "Players missing database IDs (only WSO2 users allowed)"
```

### Test 2: Adding Non-WSO2 User Fails

```bash
# Try to add player without username
curl -X POST http://localhost:5000/api/players \
  -H "Content-Type: application/json" \
  -d '{"name": "John"}'

# Should fail with: "Username is required. Only WSO2-authenticated users..."
```

### Test 3: WSO2 User Can Play

```bash
# Add WSO2 user
curl -X POST http://localhost:5000/api/players \
  -H "Content-Type: application/json" \
  -d '{"username": "charlie"}'

# Should succeed with: "Player charlie added to game"
```

## Troubleshooting

### Issue: "Player ID not available" when viewing history

**Cause**: Player logged in, but never created in database (no WSO2 link)

**Solution**: 
1. Check `/api/debug/session` - verify `player_id` exists
2. Check player table - verify player has `username` (WSO2 link)
3. If missing, re-login to trigger auto-creation

### Issue: Games from old phantom players missing

**Cause**: Phantom players deleted in cleanup

**Solution**: 
- Backup database before cleanup
- Check backup if games need to be recovered
- Contact user to replay game as WSO2 user

### Issue: Database constraint error on game save

**Cause**: Player ID in game data doesn't exist in player table

**Solution**: 
1. Run cleanup: `python helpers/cleanup_phantom_players.py`
2. Verify all players have WSO2 usernames
3. Only add players with valid player_ids

## Files Modified

| File | Change |
|------|--------|
| `src/core/database_service.py` | `start_new_game()` now requires player IDs; `get_or_create_player()` enforces username |
| `src/app/game_manager.py` | `new_game()` accepts player_ids; validates db_id before saving |
| `src/app/app.py` | `/api/players` POST now requires username; rejects manual entries |
| `helpers/cleanup_phantom_players.py` | **NEW** - Cleanup utility for phantom players |

## References

- **Database Models**: `src/core/database_models.py` - Player/GameResult/Score relationships
- **Authentication**: `src/core/auth.py` - WSO2 integration
- **API**: `src/app/app.py` - REST endpoints
- **Game Logic**: `src/app/game_manager.py` - Game state management