# Test Server - Data Access Guide

## Current Status

The test server is **fully functional**, but the history page and dashboard appear empty because:

1. **Authentication Required**: The `/api/game/history` endpoint requires login (`@login_required`)
2. **User Filtering**: Users only see games where the player's username matches their WSO2 username
3. **Test Data**: There is game data in the database, but it belongs to specific test users

## Current Database Data

### Test Database: `dartsdbtest`

**Players in database:**
```
ID | Name/Username              | Email
---+---------------------------+--------------------------------
1  | ac13bbd5-9b05-4fb7...     | (none)
2  | b3afe2ac-455f-4a5b...     | (none)  
3  | testuser001               | test.user.001@letsplaydarts.eu
```

**Games:**
- 1 game exists
- Created by: `testuser001`
- Session ID: `318959e7-3023-4338-b263-d9d3646c4382`
- Started: 2025-11-01 19:34:26

## How to See Data

### Option 1: Create Matching WSO2 User

Create a WSO2 user with username `testuser001`:

1. Access WSO2 Console: https://test.letsplaydarts.eu/console/
2. Log in as admin/admin
3. Go to User Management → Users → Add User
4. Create user:
   - Username: `testuser001`
   - Password: (set your password)
   - Email: `test.user.001@letsplaydarts.eu`
5. Log out of WSO2
6. Log in to test.letsplaydarts.eu with `testuser001`
7. Navigate to History page - you should see the test game

### Option 2: Create New Game as Admin

1. Log in to test.letsplaydarts.eu as `admin`
2. Start a new game
3. Complete the game
4. Navigate to History page - you'll see your game

### Option 3: Test with API (For Verification)

You can verify data exists without authentication using the database:

```bash
# Connect to test database
docker exec -it darts-postgres psql -U postgres -d dartsdbtest

# Query games
SELECT
    gr.game_session_id,
    gr.started_at,
    p.username as player
FROM gameresults gr
JOIN player p ON gr.player_id = p.id
ORDER BY gr.started_at DESC
LIMIT 10;
```

## Dashboard Access

The dashboard also requires authentication and shows:
- Your recent games
- Your statistics
- Your game history

**To access dashboard:**
1. Log in with a WSO2 user
2. Navigate to /dashboard
3. You'll see your personal statistics

## Admin Access

Users with the **admin** role can:
- See all users' games (with `?user=username` parameter)
- Access admin-only features
- View system-wide statistics

**To test as admin:**
1. Log in to test.letsplaydarts.eu with `admin/admin`
2. Your games will appear in history
3. You can filter by user: `/api/game/history?user=testuser001`

## Creating Test Data

### Quick Test Game Creation

```bash
# 1. Log in to test.letsplaydarts.eu
# 2. Navigate to the game start page
# 3. Select game type (e.g., X01)
# 4. Start the game
# 5. Play or complete the game
# 6. Check history page - your game will appear
```

### Programmatic Test Data (Optional)

If you need to create test data programmatically:

```python
# Connect to test database
from src.core.database_service import DatabaseService

db = DatabaseService()
# Use db.create_game(...) methods to insert test data
```

## Troubleshooting

### "History page is empty"

**Cause**: No games exist for your logged-in username

**Solution**:
1. Verify you're logged in (check top-right corner)
2. Create a new game
3. Or log in with a user that has existing games

### "Dashboard shows no data"

**Cause**: Same as history - no games for your user

**Solution**:
1. Play at least one game
2. Dashboard will populate with your statistics

### "API returns empty array"

**Cause**: The user filter is working correctly - you have no games

**Test**:
```bash
# Check if any games exist in database
docker exec darts-postgres psql -U postgres -d dartsdbtest \
  -c "SELECT COUNT(*) FROM gameresults;"
```

## Data Isolation

The test environment uses **isolated data**:

- **Database**: `dartsdbtest` (separate from development/production)
- **RabbitMQ Exchange**: `darts_exchange_test`
- **Users**: Test-specific WSO2 users

This ensures test activities don't affect other environments.

## Next Steps

To populate the test server with meaningful data:

1. **Create test users in WSO2**
   - testuser001, testuser002, etc.

2. **Play test games**
   - Log in as different users
   - Complete various game types

3. **Verify history displays**
   - Each user sees their own games
   - Admin sees all games

## Summary

✅ **The application is working correctly**
- History API works and returns data
- Dashboard functions properly
- Data filtering by user is correct

❓ **What you see depends on**:
- Your logged-in username
- Which games exist for that user

🎯 **To see data immediately**:
- Create WSO2 user `testuser001` and log in
- Or log in as `admin` and create new games
