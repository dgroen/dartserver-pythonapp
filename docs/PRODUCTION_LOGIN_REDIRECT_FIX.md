# Production Login Redirect Fix

## Problem

In production at **letsplaydarts.eu**, after successful OAuth2 login with WSO2 Identity Server, users were being redirected to **localhost:5000** instead of staying on **letsplaydarts.eu**. This prevented external access since localhost is not available from outside the hosting machine.

## Root Cause

The issue occurred because the `login_required` decorator was using `request.url` to store the "next" redirect URL parameter. When Flask's request object wasn't correctly reading the X-Forwarded-\* headers from the nginx reverse proxy, `request.url` would contain `http://localhost:5000/...` instead of `https://letsplaydarts.eu/...`.

Later, when the OAuth2 callback handler redirected using this "next" parameter, it would send the user to the localhost URL.

## Solution

### 1. Created `get_current_request_url()` Helper Function

Added a new function in `src/core/auth.py` that properly reconstructs the current request URL using the X-Forwarded-\* headers set by nginx:

```python
def get_current_request_url() -> str:
    """
    Reconstruct the current request URL using X-Forwarded-* headers.

    Priority:
    1. Use X-Forwarded-Proto and X-Forwarded-Host headers (from nginx proxy)
    2. Fall back to request.scheme and request.host
    """
```

This ensures the "next" URL parameter contains the external production domain.

### 2. Updated `login_required` Decorator

Changed the decorator to use `get_current_request_url()` instead of `request.url`:

```python
# Before:
return redirect(url_for("login", next=request.url))

# After:
return redirect(url_for("login", next=get_current_request_url()))
```

### 3. Improved OAuth2 Callback Handler

Updated the callback redirect logic to:

- Use relative URLs (like "/") by default, which preserve the external scheme/host
- Log the redirect URL for debugging
- Only use the "next" parameter if it's explicitly provided (now with correct proxy-aware URL)

```python
next_url = request.args.get("next")
if not next_url:
    next_url = "/"  # Relative URL preserves external scheme/host from proxy
```

### 4. Added `url_for()` Wrapper (Optional Enhancement)

Created an enhanced `url_for()` wrapper that ensures external URLs use the correct scheme and host when behind a proxy:

```python
def url_for(endpoint, **values):
    """
    Enhanced url_for wrapper that respects X-Forwarded-* headers
    to prevent localhost URLs in production.
    """
```

## Testing

- ✅ All 44 existing unit tests pass
- ✅ Code passes linting (ruff, black)
- ✅ Compilation successful

## Verification Steps

To verify the fix is working in production:

1. **Check nginx headers are being sent:**

   ```bash
   curl -I https://letsplaydarts.eu/login 2>&1 | grep X-Forwarded
   ```

2. **Monitor logs for redirect URLs:**
   The application now logs the redirect URLs:

   ```
   Built current request URL: https://letsplaydarts.eu/login (scheme=https, host=letsplaydarts.eu)
   ```

3. **Test login flow:**
   - Access <https://letsplaydarts.eu/login>
   - Click login to authenticate with WSO2
   - Verify you're redirected back to <https://letsplaydarts.eu> (NOT localhost:5000)

## Nginx Configuration

The nginx reverse proxy is already configured correctly to send the required headers:

```nginx
# In /nginx/nginx.conf for the darts app location
location / {
    proxy_set_header X-Forwarded-Proto https;   # Force HTTPS for OAuth redirects
    proxy_set_header X-Forwarded-Host $host;    # Pass the external host
    ...
}
```

## Files Modified

- `src/core/auth.py`: Added helper functions and updated login_required decorator
- `src/app/app.py`: Improved OAuth2 callback handler

## Impact

- **Security**: Fixes a critical issue that prevented production users from accessing the application
- **External Access**: Enables access from any domain to letsplaydarts.eu
- **Debugging**: Enhanced logging makes it easier to diagnose proxy configuration issues
