# Mobile Results Page - Debugging Guide

The mobile results page at `/mobile/results` should display game history and active games. If you're not seeing any data, follow this guide to diagnose the issue.

## Quick Verification Steps

### 1. Verify Sample Data Was Created

```bash
# First, make sure you have created sample game data
python helpers/generate_sample_game_data.py

# Output should show:
# ✅ Created 5 sample games!
```

### 2. Enable Debug Mode

Navigate to: **`http://localhost:5000/mobile/results?debug`**

This will show a debug panel at the top of the page with real-time debug information.

### 3. Check Browser Console

Open your browser's developer tools (F12) and go to the **Console** tab. Look for messages that start with timestamps showing:
- `loadPlayerHistory called`
- `API Request: /api/player/history`
- `API Response from /api/player/history: ...`

## Debug Endpoints

### Check Session State

Open: **`http://localhost:5000/api/debug/session`**

This should return:
```json
{
    "player_id": 18,
    "username": "bypass_user",
    "session_keys": ["player_id", "username", ...],
    "auth_disabled": true
}
```

**If `player_id` is `null`:**
- The auth bypass isn't working
- Check that `AUTH_DISABLED=true` is set in your environment
- Check the application logs for errors

### Check History API Directly

Open: **`http://localhost:5000/api/player/history`**

This should return:
```json
{
    "success": true,
    "games": [
        {
            "game_session_id": "sample_...",
            "game_type": "301",
            "started_at": "2024-01-15T10:30:00+00:00",
            "finished_at": "2024-01-15T10:45:00+00:00",
            "is_winner": true,
            "final_score": 0,
            "start_score": 301,
            "player_count": 2,
            "players": [
                {"name": "Bypass User", "final_score": 0, "is_winner": true},
                {"name": "Opponent 1", "final_score": 50, "is_winner": false}
            ],
            "double_out_enabled": false
        }
    ]
}
```

**If you get an error:**
- Check the `error` field in the response
- Common errors:
  - `"error": "Player ID not available"` → player_id isn't in session
  - `"error": "Player not found"` → bypass_user player doesn't exist in database

### Check Statistics API

Open: **`http://localhost:5000/api/player/statistics`**

Should return:
```json
{
    "success": true,
    "statistics": {
        "total_games": 5,
        "wins": 3,
        "losses": 2,
        "win_rate": 60.0,
        "average_score": 25,
        "by_game_type": {
            "301": {"games": 2, "wins": 2, "win_rate": 100.0},
            "501": {"games": 2, "wins": 1, "win_rate": 50.0},
            "Cricket": {"games": 1, "wins": 0, "win_rate": 0.0}
        }
    }
}
```

## Common Issues & Solutions

### Issue: "No game results found" displayed

**Possible Causes:**
1. Sample data wasn't generated
   - **Solution:** Run `python helpers/generate_sample_game_data.py`

2. Database connection issue
   - **Solution:** Check that PostgreSQL is running and DATABASE_URL is set correctly

3. Player ID not in session
   - **Solution:** Check `/api/debug/session` - if player_id is null, restart the app

**Debugging:**
- Check `/api/player/history` endpoint directly
- Look at console logs in debug mode (`?debug` parameter)
- Check application server logs for any errors

### Issue: "Unauthorized" or redirected to login

**Possible Causes:**
1. AUTH_DISABLED not set
   - **Solution:** Set `export AUTH_DISABLED=true` before starting the app

2. Session expired
   - **Solution:** Clear browser cookies for localhost and refresh

**Debugging:**
- Check `/api/debug/session` - auth_disabled should be true
- Check browser cookies - session should exist
- Check application logs

### Issue: API returns 500 error

**Debugging Steps:**
1. Check the application server logs for the full error message
2. Verify database connection: `DATABASE_URL` environment variable is set
3. Verify database has the games table: Check PostgreSQL directly
4. Restart the application

## Manual Testing

### Test 1: Verify Database Has Data

```bash
# Connect to PostgreSQL
psql $DATABASE_URL

# Check for game results
SELECT COUNT(*) FROM gameresults;
# Should return 5 if sample data was generated

# Check for bypass_user player
SELECT * FROM player WHERE username = 'bypass_user';
# Should show a player with id=18 or similar
```

### Test 2: Test API Endpoints with cURL

```bash
# Get game history
curl -X GET http://localhost:5000/api/player/history

# Get statistics
curl -X GET http://localhost:5000/api/player/statistics

# Get active games
curl -X GET http://localhost:5000/api/active-games
```

### Test 3: Clear and Regenerate Data

```bash
# Stop the application
# Kill the running Flask app

# Clear cache and restart
rm -rf .pytest_cache htmlcov

# Regenerate sample data
python helpers/generate_sample_game_data.py

# Start the application
python run.py

# Visit http://localhost:5000/mobile/results?debug
```

## Troubleshooting Flowchart

```
Are you seeing "No game results found"?
├─ YES → Go to /api/player/history
│        ├─ Returns 5 games? → CSS issue, check browser console
│        ├─ Returns empty array? → Generate sample data with:
│        │                         python helpers/generate_sample_game_data.py
│        └─ Returns error? → Check player_id at /api/debug/session
│
└─ NO → Check browser console (F12)
        ├─ Any red errors? → Post the error message
        └─ No errors? → Data should be showing
                        Try refreshing the page
                        Or check CSS display issues
```

## Getting Help

When reporting issues, please include:

1. Output from `/api/debug/session`
2. Output from `/api/player/history`
3. Browser console messages (F12 → Console tab)
4. Application server log messages
5. Steps to reproduce the issue

## Next Steps if Still Not Working

1. **Enable full debug mode:**
   ```
   export LOG_LEVEL=DEBUG
   python run.py
   ```

2. **Check mobile.css:**
   - Browser DevTools → Elements → Check if results-list div is visible
   - Check if content is hidden by CSS (display: none, etc.)

3. **Test the web results page:**
   - Go to `/history` (web version, not mobile)
   - If that works but `/mobile/results` doesn't, the issue is in mobile-specific code
   - If both don't work, the issue is in the API

4. **Clear everything and restart:**
   ```bash
   # Stop the app
   # Clear session/cookies in browser
   # Restart app with:
   python run.py
   # Visit a different page first, then go to /mobile/results
   ```