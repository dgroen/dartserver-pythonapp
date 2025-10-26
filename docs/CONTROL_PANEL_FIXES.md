# Control Panel Fixes - Issue Resolution

## Summary

This document describes the fixes for two issues in the control panel:

1. **Player Addition Bug**: Players were being added twice when using the search functionality
2. **History Page Redirect**: After login, users were redirected to the game page instead of the history page

## Issue 1: Player Added Twice

### Problem

When adding a player via the control panel, especially with search results, the player would appear twice in the game. This was caused by redundant API and socket calls both attempting to add the player.

### Root Cause

In `static/js/control.js`, after the API endpoint (`/api/players`) successfully added a player, the code also emitted a socket event (`add_player`). This caused the player to be added twice:

1. First by the API endpoint calling `game_manager.add_player_with_id()`
2. Second by the socket event handler calling `game_manager.add_player()`

### Solution

**File**: `static/js/control.js` (lines 141-149)

Removed the redundant socket emit after the API call. Since `add_player_with_id()` already broadcasts the game state via `_emit_game_state()`, the additional socket emit is unnecessary and causes duplication.

**Before**:

```javascript
if (response.ok) {
  const data = await response.json();
  console.log("Player added:", data);
  playerNameInput.value = "";
  selectedUser = null;
  playerSearchResults.style.display = "none";
  socket.emit("add_player", { name: name }); // ← REDUNDANT
}
```

**After**:

```javascript
if (response.ok) {
  const data = await response.json();
  console.log("Player added:", data);
  playerNameInput.value = "";
  selectedUser = null;
  playerSearchResults.style.display = "none";
  // Note: The API endpoint already broadcasts the game state via add_player_with_id,
  // so we don't need to emit a socket event here. Emitting would duplicate the player.
}
```

### Impact

- ✅ Players are now added only once when using the control panel
- ✅ Search results work correctly without duplication
- ✅ Manual player entry also works correctly

## Issue 2: History Page Redirect After Login

### Problem

When clicking the "Game History" button while not authenticated, users would be redirected to the login page. However, after successful authentication, they were redirected to the home page (`/`) instead of the history page (`/history`).

### Root Cause

The "next" parameter (indicating where to redirect after login) was being passed as a query parameter to the login endpoint but was not being preserved through the OAuth2 flow. Here's what was happening:

1. User accesses `/history` without authentication
2. `login_required` decorator redirects to `/login?next=/history`
3. User is redirected to WSO2 for OAuth2 authorization
4. OAuth2 provider calls the callback endpoint with authorization code
5. The callback endpoint tried to retrieve the "next" parameter from `request.args`, but it was never passed through the OAuth2 flow
6. Therefore, callback redirected to default home page (`/`)

### Solution

**Files Modified**:

#### 1. `src/app/app.py` - Login Route (lines 205-209)

Store the "next" parameter in the Flask session:

```python
@app.route("/login")
def login():
    """Login page"""
    # Generate state for CSRF protection
    state = secrets.token_urlsafe(32)
    session["oauth_state"] = state
    session.permanent = True  # Make session persistent across requests

    # Store the "next" parameter to redirect after login
    next_url = request.args.get("next")
    if next_url:
        session["login_next_url"] = next_url
        app.logger.info(f"Storing redirect URL in session: {next_url}")

    # ... rest of the function
```

#### 2. `src/app/app.py` - Callback Route (lines 280-286)

Retrieve the "next" parameter from the session and use it for redirection:

```python
# Clear OAuth state
session.pop("oauth_state", None)

# Redirect to original destination or home
# First, try to get the redirect URL from session (set during login)
# Otherwise fall back to home page using relative URL (preserves scheme/host from proxy)
next_url = session.pop("login_next_url", None) or "/"

app.logger.info(f"Callback redirecting to: {next_url}")
return redirect(next_url)
```

### How It Works

1. When unauthenticated user tries to access `/history`, `login_required` redirects to `/login?next=/history`
2. The login route now stores `next=/history` in `session["login_next_url"]`
3. User is redirected to WSO2 for authentication
4. After successful authentication, callback retrieves `next_url` from session
5. User is redirected to `/history` as originally intended
6. Session key is removed using `session.pop()` to clean up

### Impact

- ✅ Users are now correctly redirected to the page they originally requested after login
- ✅ Works for all protected pages (history, control panel, etc.)
- ✅ Session-based approach is secure and works with OAuth2 flow

## Testing

### Unit Tests Created

New test file: `tests/unit/test_control_panel_fixes.py`

**Test Classes**:

1. **TestPlayerAdditionFix**: Verifies player addition endpoints work correctly
   - `test_player_addition_endpoint_succeeds`: Basic player addition
   - `test_player_addition_with_username`: WSO2 user addition

2. **TestHistoryRedirectFix**: Verifies redirect behavior after login
   - `test_login_stores_next_parameter`: Confirms next URL is stored in session
   - `test_callback_uses_session_next_url`: Confirms redirect uses stored URL
   - `test_history_requires_login_unauthenticated`: Confirms login redirect preserves history URL

3. **TestControlPanelPlayerSearch**: Verifies search functionality
   - `test_player_search_endpoint`: Search returns results correctly
   - `test_player_search_empty_query`: Empty queries are rejected
   - `test_player_search_short_query`: Short queries handled appropriately

### Test Results

All 8 new tests pass:

```
tests/unit/test_control_panel_fixes.py::TestPlayerAdditionFix::test_player_addition_endpoint_succeeds PASSED
tests/unit/test_control_panel_fixes.py::TestPlayerAdditionFix::test_player_addition_with_username PASSED
tests/unit/test_control_panel_fixes.py::TestHistoryRedirectFix::test_login_stores_next_parameter PASSED
tests/unit/test_control_panel_fixes.py::TestHistoryRedirectFix::test_callback_uses_session_next_url PASSED
tests/unit/test_control_panel_fixes.py::TestHistoryRedirectFix::test_history_requires_login_unauthenticated PASSED
tests/unit/test_control_panel_fixes.py::TestControlPanelPlayerSearch::test_player_search_endpoint PASSED
tests/unit/test_control_panel_fixes.py::TestControlPanelPlayerSearch::test_player_search_empty_query PASSED
tests/unit/test_control_panel_fixes.py::TestControlPanelPlayerSearch::test_player_search_short_query PASSED
```

## Files Modified

1. **`static/js/control.js`** - Removed redundant socket emit
2. **`src/app/app.py`** - Modified login route to store next URL in session and callback route to use it
3. **`tests/unit/test_control_panel_fixes.py`** - New test file with comprehensive test coverage

## Verification

To verify the fixes work:

1. **Test Player Addition**:

   ```bash
   pytest tests/unit/test_control_panel_fixes.py::TestPlayerAdditionFix -v
   ```

2. **Test History Redirect**:

   ```bash
   pytest tests/unit/test_control_panel_fixes.py::TestHistoryRedirectFix -v
   ```

3. **Run All Tests**:

   ```bash
   pytest tests/ -v
   ```

## Future Improvements

1. Consider implementing client-side caching of search results to improve performance
2. Add analytics to track where users are coming from when they navigate between pages
3. Implement breadcrumb navigation to make the page flow clearer

## Conclusion

Both issues have been resolved with minimal code changes:

- Player duplication eliminated by removing redundant socket call
- History page redirect preserved through OAuth2 flow using session storage
- Comprehensive test coverage added to prevent regression
