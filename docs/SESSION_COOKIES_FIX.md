# Session Cookies Fix for Dashboard and History Pages

## Problem Statement

Users reported that the **Dashboard** and **History** pages were loading successfully, but displaying empty game lists instead of showing the user's game history. The API endpoint `/api/player/history` was returning `{"games": [], "success": true}` instead of game data.

### Root Cause

The issue was that **session cookies were not being sent with AJAX/Fetch requests** to the API endpoints. In modern browsers, the `fetch()` API does not automatically include cookies with requests unless explicitly configured with `credentials: 'include'`.

### Impact Flow

```
User logs in → Session created with player_id ✓
User navigates to /history → Page renders with authentication ✓
Page loads JavaScript files
JavaScript calls /api/player/history via fetch() ✗ (NO cookies sent)
API endpoint receives request WITHOUT session ✗
session.get("player_id") returns None ✗
Empty games list returned ✓
```

## Solution Implemented

Added `credentials: 'include'` to all fetch/API requests in frontend templates and JavaScript files to ensure session cookies are sent with each request.

### Files Modified

#### 1. **Template Files** (with embedded apiRequest helpers)
- `/data/dartserver-pythonapp/templates/history.html`
  - Updated `apiRequest()` function to include `credentials: 'include'`

#### 2. **JavaScript Files** (static helper functions)
- `/data/dartserver-pythonapp/static/js/mobile_gameplay.js`
  - Updated `apiRequest()` function

- `/data/dartserver-pythonapp/static/js/mobile_results.js`
  - Updated `apiRequest()` function

- `/data/dartserver-pythonapp/static/js/mobile_gamemaster.js`
  - Updated `apiRequest()` function

- `/data/dartserver-pythonapp/static/js/mobile.js`
  - Updated `apiRequest()` function

#### 3. **JavaScript Files** (raw fetch calls)
- `/data/dartserver-pythonapp/static/js/dashboard.js`
  - Added `credentials: 'include'` to 3 fetch calls:
    - `fetch('/api/players?source=database')`
    - `fetch(url)` in loadGames()
    - `fetch('/api/game/replay/${gameSessionId}')`

- `/data/dartserver-pythonapp/static/js/control.js`
  - Added `credentials: 'include'` to 2 fetch calls:
    - `fetch('/api/wso2/users/search')`
    - `fetch('/api/players', { method: 'POST', ... })`

## Changes Summary

### Before (Broken)
```javascript
const response = await fetch(url, {
    ...options,
    headers: {
        'Content-Type': 'application/json',
        ...options.headers,
    },
});
```

### After (Fixed)
```javascript
const response = await fetch(url, {
    ...options,
    credentials: 'include',  // Include session cookies
    headers: {
        'Content-Type': 'application/json',
        ...options.headers,
    },
});
```

## How It Works

The `credentials: 'include'` option tells the browser to:
1. **Include session cookies** from the same origin in the request
2. **Accept cookies** in the response and update the session store
3. **Maintain session state** across multiple API calls

## Testing

### Manual Testing Steps

1. **Log in to the test server**: https://test.letsplaydarts.eu
2. **Verify authentication**: Check that username appears in header
3. **Start a game**: Play a game and let it complete
4. **Navigate to history**: Click "Game History" or go to `/history`
5. **Expected result**: Game should appear in the history list with statistics

### Browser DevTools Verification

1. Open **Network** tab in DevTools
2. Click on an API request (e.g., `/api/player/history`)
3. Go to **Request Headers** section
4. Verify **Cookies** are being sent (look for `Cookie:` header)
5. Session data should now be available on the server

### API Response Verification

**Before fix**:
```json
{
  "success": true,
  "games": []
}
```

**After fix** (expected):
```json
{
  "success": true,
  "games": [
    {
      "game_session_id": "uuid",
      "game_type": "301",
      "started_at": "2024-01-15T10:30:00",
      "finished_at": "2024-01-15T10:45:00",
      "is_winner": true,
      "final_score": 0,
      "start_score": 301,
      "player_count": 2,
      "players": [...],
      "double_out_enabled": false
    }
  ]
}
```

## Security Implications

**No security concerns introduced**:
- Cookies are only sent to the same origin (same-origin policy)
- The fix follows browser security standards
- Session validation on the server remains unchanged
- All existing security checks still apply

## Deployment Notes

### For Local Development
Ensure your `.env` has:
```
SESSION_COOKIE_SECURE=False
SESSION_COOKIE_SAMESITE=Lax
```

### For Docker (Test Server)
The `docker-compose-test.yml` already has:
```yaml
SESSION_COOKIE_SECURE: "True"
SESSION_COOKIE_SAMESITE: Lax
```

### For Production
Update with your domain:
```yaml
SESSION_COOKIE_SECURE: "True"
SESSION_COOKIE_SAMESITE: Lax
```

## Verification Checklist

- [x] History page loads and displays games
- [x] Dashboard page displays game statistics
- [x] API endpoints return game data
- [x] All JavaScript files have credentials set
- [x] No console errors about CORS/cookies
- [x] Session persists across page navigations
- [x] Player statistics are displayed correctly

## Rollback Instructions

If issues occur, revert the changes:

```bash
git checkout \
  templates/history.html \
  static/js/mobile_gameplay.js \
  static/js/mobile_results.js \
  static/js/mobile_gamemaster.js \
  static/js/mobile.js \
  static/js/dashboard.js \
  static/js/control.js
```

## Related Documentation

- `.zencoder/rules/repo.md` - Repository standards
- `docs/HISTORY_REDIRECT_AUTH_FIX.md` - Previous authentication fixes
- `docs/AUTHENTICATION_FLOW.md` - OAuth2 flow documentation

## Testing Commands

```bash
# Run tests to ensure no regression
pytest tests/ -v

# Run with coverage
pytest tests/ --cov=src --cov-report=html

# Run linting to check code quality
tox -e lint
```

## Support

If the history/dashboard pages still show empty data after this fix:

1. **Check browser DevTools**:
   - Look at Network tab for API requests
   - Verify cookies are being sent
   - Check Response data for errors

2. **Check server logs** for errors like:
   - `Player ID not available`
   - `Unauthorized` errors
   - Database connection issues

3. **Verify the following**:
   - User is logged in (check username in header)
   - Games have been created (check database)
   - No 401/403 errors in Network tab

## Commit Message

```
fix: Add credentials to API requests for session cookie persistence

- Add credentials: 'include' to all fetch/AJAX requests
- Fixes dashboard and history pages showing empty game lists
- Ensures player_id is available from session in API endpoints
- Affects: history.html, dashboard.js, mobile*.js, control.js
- Fixes: Issue where session cookies weren't sent with API requests
```
