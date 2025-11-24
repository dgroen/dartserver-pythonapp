# CORS Credentials Configuration Fix

## Problem

Dashboard and History pages were displaying empty game lists despite:

- User authentication working correctly
- Pages rendering properly
- API endpoints being called via JavaScript fetch requests
- Session cookies being created during login

## Root Cause

The **backend CORS configuration did not support credentials**, which prevented session cookies from being transmitted with API requests.

### Technical Details

When JavaScript makes a fetch request with `credentials: 'include'`:

```javascript
fetch("/api/game/history", {
  credentials: "include", // Include session cookies
});
```

The browser requires the server to respond with **both**:

1. `Access-Control-Allow-Credentials: true`
2. `Access-Control-Allow-Origin: [specific-origin]` (NOT `*`)

Without these headers, the browser **silently blocks the response** and doesn't send/receive cookies.

### What Was Happening

**Before the fix:**

```
Backend: CORS(app)  → Sends Access-Control-Allow-Origin: *
Browser: credentials: 'include' → Requests include cookies
Result: ❌ Browser rejects response - cookies not sent
Effect: API sees no session → Returns empty games list
```

**After the fix:**

```
Backend: CORS(app, supports_credentials=True)  → Sends Access-Control-Allow-Credentials: true
Browser: credentials: 'include' → Requests include cookies
Result: ✅ Browser accepts response - cookies included
Effect: API gets session context → Returns user's actual game history
```

## Solution

Changed CORS initialization to support credentials in two files:

### 1. Main Application (`src/app/app.py`)

```python
# Before
CORS(app)

# After
CORS(app, supports_credentials=True)
```

### 2. API Gateway (`src/api_gateway/app.py`)

```python
# Before
CORS(app)

# After
CORS(app, supports_credentials=True)
```

## How It Works

With `supports_credentials=True`, Flask-CORS:

1. **Automatically sends** `Access-Control-Allow-Credentials: true` header
2. **Uses the request's origin** instead of `*` (required for credential requests)
3. **Allows cookies** to be sent and received with cross-origin requests
4. **Maintains security** by only allowing credentials from same-origin policy

## Files Modified

- `src/app/app.py` - Line 75
- `src/api_gateway/app.py` - Line 39

## Testing the Fix

After deployment, verify the fix works:

### 1. Browser DevTools Method

1. Open browser DevTools (F12)
2. Go to Network tab
3. Refresh the page and log in
4. Navigate to Dashboard or History
5. Click on the API call (e.g., `/api/game/history`)
6. Check Response Headers:
   - ✅ Should see: `Access-Control-Allow-Credentials: true`
   - ✅ Should see: `Access-Control-Allow-Origin: https://test.letsplaydarts.eu`
7. Check Request Headers:
   - ✅ Should see: `Cookie: [session_cookie_data]`

### 2. Expected Behavior After Fix

- ✅ Dashboard shows game statistics
- ✅ History page displays game list
- ✅ Mobile results page shows player stats
- ✅ All API endpoints return data instead of empty lists

## Security Implications

✅ **This fix is secure because:**

- Credentials are only sent to **same-origin** (defined by specific domain in CORS headers)
- Cookies cannot be leaked to cross-origin sites
- Session tokens are still HttpOnly and Secure (cannot be accessed via JavaScript)
- Complies with browser CORS security policy

## Deployment Notes

1. **Docker:** Rebuild and redeploy the containers

   ```bash
   docker-compose -f docker-compose-wso2.yml -f docker-compose-test.yml build
   docker-compose -f docker-compose-wso2.yml -f docker-compose-test.yml up -d
   ```

2. **Browser Cache:** Force refresh after deployment
   - Chrome/Firefox: `Ctrl+Shift+R` or `Cmd+Shift+R` on Mac
   - Or: Clear browser cache entirely

3. **Verification:** Check DevTools Network tab as described in Testing section

## Rollback Instructions

If issues arise, revert to original configuration:

```python
# In both files, change:
CORS(app, supports_credentials=True)

# Back to:
CORS(app)
```

Then rebuild and redeploy.

## Related Documentation

- `SESSION_COOKIES_FIX.md` - Frontend changes to include credentials in fetch requests
- `AUTHENTICATION_FLOW.md` - Overall authentication flow with WSO2
- `AUTHENTICATION_SETUP.md` - Configuration details
