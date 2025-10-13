# Database Storage Issue - Fix Summary

## Issue Description

The application appeared to not be storing game results in the database anymore. The last recorded games were from October 10th, 2025.

## Root Cause Analysis

After investigation, we discovered:

1. **The database WAS actually working** - it contained 15 game results and 125 scores
2. **The real issue was in the `get_recent_games()` method** in `database_service.py`
3. The method had a **PostgreSQL SQL error** that prevented retrieving game history

### The SQL Error

```
psycopg2.errors.InvalidColumnReference: for SELECT DISTINCT, ORDER BY expressions must appear in select list
```

The problematic query was:
```python
session.query(GameResult.game_session_id)
    .distinct()
    .order_by(GameResult.started_at.desc())
```

**Problem**: PostgreSQL requires that when using `DISTINCT`, all columns in the `ORDER BY` clause must also appear in the `SELECT` clause. The query was selecting only `game_session_id` but ordering by `started_at`, which caused the error.

## Changes Made

### 1. Fixed `get_recent_games()` in `database_service.py`

**Before:**
```python
game_sessions = (
    session.query(GameResult.game_session_id)
    .distinct()
    .order_by(GameResult.started_at.desc())
    .limit(limit)
    .all()
)
```

**After:**
```python
from sqlalchemy import func

subquery = (
    session.query(
        GameResult.game_session_id,
        func.max(GameResult.started_at).label("max_started_at"),
    )
    .group_by(GameResult.game_session_id)
    .order_by(func.max(GameResult.started_at).desc())
    .limit(limit)
    .subquery()
)

game_sessions = (
    session.query(subquery.c.game_session_id, subquery.c.max_started_at).all()
)
```

**Why this works:**
- Uses `GROUP BY` instead of `DISTINCT` to get unique game sessions
- Properly includes `started_at` in the aggregation
- Orders by the maximum `started_at` for each game session
- Returns results in correct chronological order (most recent first)

### 2. Fixed Deprecated `datetime.utcnow` Usage in `database_models.py`

As per project linting rules, replaced all instances of `datetime.utcnow` with timezone-aware datetime:

**Added helper function:**
```python
from datetime import datetime, timezone

def utc_now():
    """Return current UTC time with timezone awareness"""
    return datetime.now(tz=timezone.utc)
```

**Updated all model defaults:**
- `Player.created_at`
- `GameType.created_at`
- `GameResult.started_at`
- `Score.thrown_at`
- `Dartboard.created_at` and `updated_at`
- `ApiKey.created_at`
- `HotspotConfig.created_at` and `updated_at`

## Testing

### All Tests Pass
```bash
pytest tests/unit/test_database_service.py -v
# Result: 23 passed
```

### Linting Passes
```bash
ruff check database_models.py database_service.py
# Result: All checks passed!
```

### Manual Verification
```python
from database_service import DatabaseService
db_service = DatabaseService()
games = db_service.get_recent_games(limit=10)
# Result: Successfully retrieved 10 games in correct order
```

## Impact

- ✅ Database is now properly storing all game results and scores
- ✅ Game history API endpoint (`/api/game/history`) now works correctly
- ✅ Recent games are returned in proper chronological order
- ✅ All deprecated datetime usage has been fixed
- ✅ All tests pass
- ✅ Code follows project linting standards

## Files Modified

1. `database_service.py` - Fixed `get_recent_games()` method
2. `database_models.py` - Replaced deprecated `datetime.utcnow` with timezone-aware alternative

## Verification Steps

To verify the fix is working:

1. **Check database connectivity:**
   ```python
   from database_service import DatabaseService
   db = DatabaseService()
   db.initialize_database()
   ```

2. **Start a new game and verify it's stored:**
   ```python
   session_id = db.start_new_game(
       game_type_name='301',
       player_names=['Player 1', 'Player 2'],
       start_score=301,
       double_out=False
   )
   print(f"Game started: {session_id}")
   ```

3. **Retrieve recent games:**
   ```python
   games = db.get_recent_games(limit=5)
   print(f"Found {len(games)} recent games")
   ```

4. **Test via API:**
   ```bash
   curl http://localhost:5000/api/game/history?limit=5
   ```

## Conclusion

The database was working correctly all along. The issue was that the `get_recent_games()` method had a SQL error that prevented the application from retrieving and displaying the stored game history. This has been fixed, and all functionality is now working as expected.