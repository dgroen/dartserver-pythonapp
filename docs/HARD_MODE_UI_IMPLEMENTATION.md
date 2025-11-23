# Hard Mode UI Implementation

## Overview

This document describes the UI implementation for the "hard mode" feature in Round the Clock games. The hard mode resets the player to target 20 after missing all 3 darts in a turn (3 consecutive misses).

## Implementation Date

November 15, 2025

## Changes Made

### 1. Database Schema Updates

#### File: `src/core/database_models.py`
- Added `reset_on_miss` column to `GameResult` model
- Type: Boolean, default=False
- Purpose: Store whether hard mode was enabled for a game

#### File: `alembic/versions/f1a2b3c4d5e7_add_reset_on_miss_to_gameresult.py`
- Created database migration to add `reset_on_miss` column
- Migration handles both upgrade and downgrade scenarios
- Uses `server_default="0"` for backward compatibility

### 2. Backend Updates

#### File: `src/core/database_service.py`
**Modified Methods:**
- `start_new_game()`: Added `reset_on_miss` parameter
- `get_recent_games()`: Returns `reset_on_miss` and `double_out_enabled` in results
- `get_game_replay_data()`: Includes `reset_on_miss` in replay data
- `get_player_game_history()`: Returns `reset_on_miss` for each game

#### File: `src/app/game_manager.py`
- Updated `new_game()` to pass `reset_on_miss` to database service
- Maintains backward compatibility with default value `False`

#### File: `src/app/app.py`
- `/api/game/new` endpoint: Already accepts `reset_on_miss` parameter
- `/api/game/start` endpoint: Already accepts `reset_on_miss` parameter
- Both endpoints properly documented in API spec

### 3. Control Panel UI

#### File: `templates/control.html`
- Added hard mode checkbox in game setup section
- Checkbox ID: `reset-on-miss`
- Container ID: `hard-mode-container` (hidden by default)
- Label: "Hard Mode (reset to 20 after 3 consecutive misses)"

#### File: `static/js/control.js`
**Changes:**
- Added `resetOnMissCheckbox` and `hardModeContainer` DOM element references
- Updated `new_game` event to include `reset_on_miss` parameter
- Added event listener on `game-type` select to show/hide hard mode option
- Hard mode option only visible when "Round the Clock" game type is selected

### 4. History Page Display

#### File: `templates/history.html`
**JavaScript Updates:**
- Modified `displayHistory()` function to show game options
- Displays "💀 Hard Mode" badge when `reset_on_miss` is true
- Displays "🎯 Double Out" badge when `double_out_enabled` is true
- Styled with red color scheme for hard mode: `rgba(255, 71, 87, 0.8)`

### 5. Dashboard Page Display

#### File: `static/js/dashboard.js`
**Modified Functions:**
- Updated `createGameCard()` to display game options badges
- Shows "💀 Hard Mode" badge for games with hard mode enabled
- Shows "🎯 Double Out" badge for games with double out enabled

#### File: `static/css/dashboard.css`
**New CSS Classes:**
```css
.game-options {
    display: flex;
    gap: 10px;
    flex-wrap: wrap;
    margin-top: 8px;
}

.option-badge {
    display: inline-block;
    padding: 4px 12px;
    border-radius: 12px;
    font-size: 0.85em;
    background: rgba(160, 196, 255, 0.2);
    color: #a0c4ff;
    border: 1px solid rgba(160, 196, 255, 0.4);
}

.option-badge.hard-mode {
    background: rgba(255, 71, 87, 0.2);
    color: #ff4757;
    border-color: rgba(255, 71, 87, 0.4);
}
```

## User Experience Flow

### Enabling Hard Mode

1. User navigates to Control Panel (`/control`)
2. User selects "Round the Clock" from game type dropdown
3. Hard mode checkbox appears below the double-out checkbox
4. User checks "Hard Mode" checkbox
5. User clicks "Start New Game"
6. Game starts with hard mode enabled

### Viewing Hard Mode in History

1. User navigates to History page (`/history`)
2. Completed games show game details including:
   - Game type badge
   - Win/loss status
   - Player scores
   - **Game options badges** (💀 Hard Mode, 🎯 Double Out)
3. Hard mode badge displayed in red to indicate increased difficulty

### Viewing Hard Mode in Dashboard

1. User navigates to Dashboard (`/dashboard`)
2. Recent games displayed as cards
3. Each game card shows:
   - Game type and status
   - Player count and winner
   - Duration (if completed)
   - **Game options badges** below game details
4. Hard mode badge stands out with red styling

## API Changes

### Request Format

**POST /api/game/new**
```json
{
  "game_type": "round_the_clock",
  "players": ["Player 1", "Player 2"],
  "double_out": false,
  "reset_on_miss": true
}
```

**POST /api/game/start** (Mobile)
```json
{
  "game_type": "round_the_clock",
  "players": ["Player 1", "Player 2"],
  "reset_on_miss": true
}
```

### Response Format

**GET /api/game/history**
```json
{
  "status": "success",
  "games": [
    {
      "game_session_id": "uuid",
      "game_type": "round_the_clock",
      "player_count": 2,
      "winner": "Player 1",
      "started_at": "2025-11-15T12:00:00",
      "finished_at": "2025-11-15T12:15:00",
      "double_out_enabled": false,
      "reset_on_miss": true
    }
  ]
}
```

## Backward Compatibility

- ✅ Feature is **disabled by default** (`reset_on_miss=False`)
- ✅ Existing games and API calls continue to work unchanged
- ✅ Database migration handles existing records (adds column with default False)
- ✅ UI gracefully handles games without the field (won't display badge if false)
- ✅ No breaking changes to any existing endpoints

## Testing Checklist

- [x] Database model updated with new field
- [x] Database migration created
- [x] Backend service methods updated
- [x] Control panel UI includes checkbox
- [x] JavaScript sends parameter correctly
- [x] History page displays hard mode badge
- [x] Dashboard page displays hard mode badge
- [x] API endpoints accept and return the parameter
- [ ] Manual testing: Start game with hard mode enabled
- [ ] Manual testing: Verify hard mode appears in history
- [ ] Manual testing: Verify hard mode appears in dashboard
- [ ] Manual testing: Verify database contains correct values

## Related Files

### Modified Files
1. `src/core/database_models.py` - Added reset_on_miss field
2. `src/core/database_service.py` - Updated service methods
3. `src/app/game_manager.py` - Pass reset_on_miss to DB
4. `templates/control.html` - Added checkbox
5. `static/js/control.js` - Handle checkbox and send parameter
6. `templates/history.html` - Display hard mode badge
7. `static/js/dashboard.js` - Display hard mode badge
8. `static/css/dashboard.css` - Style for badges

### New Files
1. `alembic/versions/f1a2b3c4d5e7_add_reset_on_miss_to_gameresult.py` - Database migration

### Related Documentation
- `docs/ROUND_THE_CLOCK_HARD_MODE.md` - Feature specification
- `docs/IMPLEMENTATION_CHECKLIST.md` - Original implementation checklist

## Next Steps

1. **Run Database Migration**
   ```bash
   python -m alembic upgrade head
   ```

2. **Restart Application**
   ```bash
   python run.py
   ```

3. **Manual Testing**
   - Start a Round the Clock game with hard mode enabled
   - Play a few turns and verify behavior
   - Check that game appears in history with hard mode badge
   - Check that game appears in dashboard with hard mode badge

4. **Verify Database**
   ```sql
   SELECT game_session_id, game_type_id, reset_on_miss 
   FROM gameresults 
   WHERE game_session_id = '<session_id_from_test>';
   ```

## Visual Design

### Control Panel
```
Game Setup
├── Game Type: [Round the Clock ▼]
├── ☐ Double Out (must finish with a double)
├── ☐ Hard Mode (reset to 20 after 3 consecutive misses)  ← NEW
└── [Start New Game]
```

### History Page
```
╔════════════════════════════════════════╗
║ Round the Clock     ✓ Won    12:00 PM ║
║────────────────────────────────────────║
║ 🏆 Player 1          15                ║
║    Player 2          18                ║
║────────────────────────────────────────║
║ 🎯 Double Out  💀 Hard Mode  ← NEW    ║
╚════════════════════════════════════════╝
```

### Dashboard Page
```
╔═══════════════════════════════════════════╗
║ 🎯 Round the Clock    12:00 PM  Completed ║
║───────────────────────────────────────────║
║ 👥 2 players  🏆 Player 1  ⏱️ 12m 34s    ║
║ 🎯 Double Out  💀 Hard Mode  ← NEW        ║
║                              [View Details]║
╚═══════════════════════════════════════════╝
```

## Color Scheme

- **Hard Mode Badge**: Red theme `#ff4757` / `rgba(255, 71, 87, 0.8)`
- **Double Out Badge**: Blue theme `#a0c4ff` / `rgba(160, 196, 255, 0.6)`
- Provides visual distinction between difficulty modifier and rule modifier

## Notes

- Hard mode only applies to Round the Clock game type
- UI automatically hides the option for other game types
- Backend validates and stores the setting regardless of game type for future flexibility
- Visual indicator helps players remember which games had hard mode enabled
- Consistent styling across history and dashboard pages
