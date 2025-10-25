# Authentication Bypass Fix for Local Testing

## Problem

When testing locally with `AUTH_DISABLED=True`, the bypass user "admin" was being authenticated but the application was asking for login and not showing results. This was because:

1. The `login_required` decorator was correctly bypassing authentication
2. However, the `player_id` was never being stored in the session
3. API endpoints (like `/api/player/history`, `/api/player/statistics`, `/api/active-games`) require `player_id` to fetch data
4. Without `player_id` in the session, these endpoints returned 401 Unauthorized errors

## Root Cause

In normal OAuth2 flow:

- User logs in → Redirected to WSO2 IS → Callback route is called
- In `/callback` route, `get_or_create_player()` is called and `player_id` is stored in session
- API endpoints then work because `player_id` is available in session

In bypass mode (`AUTH_DISABLED=True`):

- The callback route is never executed
- `player_id` is never stored in session
- API endpoints fail because they can't find `player_id` in session

## Solution

Modified the `login_required` decorator in `/src/core/auth.py` to:

1. **Check if player_id already exists in session** - Prevents redundant database calls
2. **Create/get bypass player** - Calls `get_or_create_player()` for the bypass_user
3. **Store player_id in session** - Same as the normal OAuth2 callback flow
4. **Handle errors gracefully** - Logs warnings but continues to avoid breaking the app

### Code Changes

#### File: `/src/core/auth.py`

- Added `current_app` import from Flask
- Enhanced `login_required` decorator to handle bypass mode player initialization

#### File: `/src/app/app.py`

- Attached `game_manager` to Flask app object with `app.game_manager = game_manager`
- This allows the decorator to access game_manager via `current_app.game_manager`

## How It Works

```
User accesses protected route (e.g., /history or /api/player/history)
    ↓
login_required decorator is invoked
    ↓
AUTH_DISABLED=True? Yes
    ↓
Set user_claims and user_roles for bypass_user
    ↓
player_id in session? No
    ↓
Create/get bypass_user player in database
    ↓
Store player_id in session
    ↓
Route handler executes successfully
    ↓
API endpoints can now access player_id from session
```

## Testing

### Step 1: Verify AUTH_DISABLED is True

```bash
grep AUTH_DISABLED /data/dartserver-pythonapp/.env
# Should output: AUTH_DISABLED=True
```

### Step 2: Start the application

```bash
cd /data/dartserver-pythonapp
python app.py
```

### Step 3: Test bypass mode

1. Open browser to `http://localhost:5000`
2. You should see the main game board page (no login required)
3. Try opening `http://localhost:5000/history`
4. You should see game history page (not asking for login)

### Step 4: Test API endpoints

```bash
curl -X GET http://localhost:5000/api/player/history
# Should return: {"success": true, "games": [...]}

curl -X GET http://localhost:5000/api/player/statistics
# Should return: {"success": true, "statistics": {...}}

curl -X GET http://localhost:5000/api/active-games
# Should return: {"success": true, "games": [...]}
```

### Step 5: Test mobile pages

- `http://localhost:5000/mobile` - Should load
- `http://localhost:5000/mobile/gameplay` - Should load
- `http://localhost:5000/mobile/results` - Should load and show stats

## What Changed

### Database

- Bypass user "bypass_user" is created in the Player table automatically on first access
- Player ID is stored in session for subsequent requests

### Session

- Before: `session` only contained OAuth2 tokens
- After: `session` also contains `player_id` for API access

### User Experience

- Local testing now works seamlessly without login
- All protected routes and API endpoints work in bypass mode
- No "login required" redirects when `AUTH_DISABLED=True`

## Environment Variables

The fix respects your `.env` configuration:

- `AUTH_DISABLED=True` - Enable bypass mode (for local testing)
- `AUTH_DISABLED=False` - Require normal OAuth2 authentication (production)

## Production Note

This fix is safe for production because:

- The bypass code only executes when `AUTH_DISABLED=True`
- In production, `AUTH_DISABLED` should be `False`
- The decorator will follow the normal OAuth2 flow instead
- No database records are created for "bypass_user" in production

## Troubleshooting

### Still asking for login after fix?

1. Clear browser cache and cookies
2. Delete any existing sessions in database
3. Restart the Flask application
4. Verify `AUTH_DISABLED=True` is in `.env`

### Player ID not showing in results?

1. Check Flask logs for "Bypass player created/retrieved"
2. Verify PostgreSQL is running
3. Check that database user has permission to create tables

### 500 errors on API endpoints?

1. Check Flask logs for the specific error
2. Verify database connection is working
3. Ensure `get_or_create_player` doesn't have permissions issues

## Files Modified

- `/data/dartserver-pythonapp/src/core/auth.py` - Enhanced login_required decorator
- `/data/dartserver-pythonapp/src/app/app.py` - Attached game_manager to app
