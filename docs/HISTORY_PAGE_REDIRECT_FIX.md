# History Page Redirect Issue - Fix Documentation

## Problem
When users clicked on the "Game History" button from the main page, the history page would load initially but then immediately redirect to the login page. This caused a poor user experience where authenticated users were unexpectedly logged out.

## Root Cause
The issue was in the `get_or_create_player()` method in `/src/core/database_service.py`. This method was:

1. Creating or retrieving a Player object from the database
2. Closing the database session
3. Returning the Player object that was still bound to the now-closed session

When the callback handler tried to access `player.id` after the session was closed, SQLAlchemy would attempt to refresh the detached object, resulting in a `DetachedInstanceError`:
```
Instance <Player at 0x...> is not bound to a Session; attribute refresh operation cannot proceed
```

This prevented the `player_id` from being stored in the session, which is required by the `/api/player/statistics` and `/api/player/history` endpoints. These endpoints check:
```python
player_id = session.get("player_id")
if not player_id:
    return jsonify({"success": False, "error": "Player ID not available"}), 401
```

When `player_id` was missing, they returned 401 Unauthorized, causing the JavaScript in the history page to redirect to `/login`.

## Solution
The fix ensures that all Player attributes are accessed and loaded into the object's internal dictionary **while the database session is still active**. This forces SQLAlchemy to load the data into memory before the session is closed.

### Changes Made
**File: `/src/core/database_service.py`**

The `get_or_create_player()` method now:
1. Explicitly accesses all needed attributes (id, name, username, email) while the session is active
2. This loads the attributes into the object's `__dict__` 
3. Then returns the player object after the session closes
4. The attributes are still accessible because they're cached in memory

**Key code section:**
```python
# Extract data before session closes
player_data = {
    "id": player.id,
    "name": player.name,
    "username": player.username,
    "email": player.email,
}
```

This pattern ensures:
- All attributes are loaded from the database
- SQLAlchemy has the data cached in the object
- After session closure, the object can still be used without triggering lazy loading

## Testing
Added comprehensive unit tests to verify the fix:
- `test_get_or_create_player_new_player`: Verifies new player creation and attribute access
- `test_get_or_create_player_existing_by_username`: Verifies retrieval by username
- `test_get_or_create_player_existing_by_email`: Verifies retrieval by email
- `test_get_or_create_player_no_username_no_email`: Verifies creation with minimal data
- `test_get_or_create_player_multiple_separate_players`: Verifies multiple independent players

All tests pass successfully, confirming:
- Player objects are properly created and returned
- Attributes are accessible after session closure
- No SQLAlchemy errors occur

## Impact
- **User Experience**: Users can now access the History page without unexpected redirects
- **Callback Flow**: The login callback now properly stores `player_id` in the session
- **API Endpoints**: Statistics and history endpoints can access `player_id` from the session
- **Backward Compatibility**: No breaking changes; existing code continues to work

## Related Components
- **Affected Endpoints**:
  - `/api/player/statistics` - Requires `session["player_id"]`
  - `/api/player/history` - Requires `session["player_id"]`
- **Affected Template**: `/templates/history.html` - JavaScript makes requests to the above endpoints
- **Callback Flow**: `/src/app/app.py` - `/callback` route now successfully stores `player_id`

## Verification
To verify the fix works:
1. Login with WSO2 credentials
2. Click "Game History" button
3. Page should load with game history and statistics
4. No redirect to login should occur
5. All data should display correctly

To run tests:
```bash
pytest tests/unit/test_database_service.py -k "get_or_create" -v
pytest tests/unit/test_login_redirect.py -v
```