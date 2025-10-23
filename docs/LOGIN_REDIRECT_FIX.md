# Login Redirect Fix - History Page Issue

## Problem
Users accessing the `/history` page were being redirected to the login page as expected. However, after completing the OAuth2 authentication with WSO2, they were being redirected to the home page (`/`) instead of being redirected back to the history page they originally requested.

## Root Cause
The issue was with how the session data was being preserved across the OAuth2 flow:

1. When a user accessed `/history` without authentication, the `@login_required` decorator would redirect them to `/login?next=<full_url_to_history>`
2. The login route would store this `next` URL in the session with `session["login_next_url"] = next_url`
3. However, the session changes weren't being explicitly marked as modified, which could cause them to not be properly persisted
4. When the OAuth2 callback returned from WSO2, the session might not contain the stored `login_next_url` value, causing the fallback to "/" to be used

## Solution
Enhanced session persistence by explicitly marking sessions as modified after storing critical data:

### Changes Made

#### 1. **src/app/app.py** - Login Route (lines 197-227)
- Added `session.modified = True` after storing the next URL to ensure the session is persisted
- Enhanced logging to debug session storage issues
- Added warning log when no 'next' parameter is found

```python
# Store the "next" parameter to redirect after login
next_url = request.args.get("next")
if next_url:
    session["login_next_url"] = next_url
    app.logger.info(f"Storing redirect URL in session: {next_url}")
else:
    app.logger.warning("No 'next' parameter found in login request")

# Ensure session changes are persisted
session.modified = True
```

#### 2. **src/app/app.py** - Callback Route (lines 286-305)
- Split the redirect URL retrieval logic for clarity
- Added comprehensive logging to track session state
- Explicitly mark session as modified after removing the `login_next_url`
- Clear fallback to "/" with informative logging

```python
next_url = session.pop("login_next_url", None)

app.logger.info(f"Callback - Retrieved login_next_url from session: {next_url}")
app.logger.info(f"Callback - Session contents: {dict(session)}")

# Use "/" as fallback if no next_url was stored
if not next_url:
    app.logger.warning("No login_next_url found in session, redirecting to home page")
    next_url = "/"

# Mark session as modified to ensure changes are persisted
session.modified = True
```

#### 3. **src/core/auth.py** - Login Required Decorator (lines 498-518)
- Added enhanced logging to track URL retrieval during the redirect
- This helps identify if the `get_current_request_url()` function is working correctly

```python
if "access_token" not in session:
    current_url = get_current_request_url()
    logger.info(
        f"login_required: No access token, "
        f"redirecting to login. Current URL: {current_url}",
    )
    return redirect(url_for("login", next=current_url))
```

#### 4. **tests/unit/test_login_redirect.py** - New Test File
Created comprehensive tests for the login redirect flow:
- `test_history_page_redirect_to_login`: Verifies redirect to login when accessing protected page
- `test_login_stores_next_url_in_session`: Confirms next URL is stored in session
- `test_login_stores_oauth_state`: Verifies OAuth state is generated
- `test_callback_redirect_to_next_url`: Tests successful redirect to history page after login
- `test_callback_redirects_to_home_without_next_url`: Tests fallback to home page
- `test_callback_clears_login_next_url_from_session`: Verifies cleanup after redirect
- `test_login_session_marked_as_permanent`: Confirms session persistence
- `test_login_route_renders_template`: UI rendering verification
- `test_login_displays_error_message`: Error message display verification

## Testing
All 9 new tests pass successfully:
```
tests/unit/test_login_redirect.py::TestLoginRedirectFlow::test_history_page_redirect_to_login PASSED
tests/unit/test_login_redirect.py::TestLoginRedirectFlow::test_login_stores_next_url_in_session PASSED
tests/unit/test_login_redirect.py::TestLoginRedirectFlow::test_login_stores_oauth_state PASSED
tests/unit/test_login_redirect.py::TestLoginRedirectFlow::test_callback_redirect_to_next_url PASSED
tests/unit/test_login_redirect.py::TestLoginRedirectFlow::test_callback_redirects_to_home_without_next_url PASSED
tests/unit/test_login_redirect.py::TestLoginRedirectFlow::test_callback_clears_login_next_url_from_session PASSED
tests/unit/test_login_redirect.py::TestLoginRedirectFlow::test_login_session_marked_as_permanent PASSED
tests/unit/test_login_redirect.py::TestLoginRedirectFlow::test_login_route_renders_template PASSED
tests/unit/test_login_redirect.py::TestLoginRedirectFlow::test_login_displays_error_message PASSED
```

## Verification
- ✅ All existing unit tests still pass (334 passed)
- ✅ New comprehensive tests added for login redirect flow (9 tests)
- ✅ Linting checks pass (ruff)
- ✅ Enhanced logging for debugging session issues
- ✅ Code follows project standards and conventions

## Expected Behavior After Fix
1. User accesses `/history` page
2. Gets redirected to `/login?next=https://localhost:5000/history`
3. Logs in via WSO2
4. Gets redirected back to `/history` page (not the home page)
5. Can now view their game history

## Additional Benefits
- Enhanced logging makes it easier to debug authentication issues in production
- Session modification is now explicit, improving reliability
- Comprehensive test coverage ensures future changes don't break the redirect flow
- Clear separation of concerns makes the code more maintainable

## Environment Variables
No new environment variables are required. The fix uses existing session configuration:
- `SESSION_COOKIE_SECURE`: Controls secure cookie flag (already configured)
- `SESSION_COOKIE_SAMESITE`: Controls SameSite attribute (already configured)
- `PERMANENT_SESSION_LIFETIME`: Session lifetime (already set to 3600 seconds)