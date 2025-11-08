# Redirect Issue - Complete Summary

## Issue Report

**Date**: Current  
**Status**: ✅ Solution Identified  
**Severity**: High (Blocks logout functionality)

### Symptoms

1. ❌ After successful login, redirect may fail
2. ❌ After logout, error: "Post logout URI does not match with registered callback URI"
3. ❌ Users cannot properly log out of the application

### Error Message

```
Post logout URI does not match with registered callback URI.
```

## Root Cause Analysis

### The Problem

WSO2 Identity Server validates **all redirect URIs** for security:

- ✅ **Login redirect**: `https://letsplaydarts.eu/callback` - **Registered** ✅
- ❌ **Logout redirect**: `https://letsplaydarts.eu/` - **NOT Registered** ❌

### Why This Happens

OAuth2/OIDC security requires that all redirect URIs be explicitly registered in the authorization server (WSO2 IS). This prevents:

- Open redirect attacks
- Authorization code theft
- Phishing attacks

### Current Configuration

**WSO2 IS Service Provider:**

```
Callback URLs: https://letsplaydarts.eu/callback
```

**Flask Application (auth.py):**

```python
# Login - redirects to /callback
redirect_uri = "https://letsplaydarts.eu/callback"  ✅ Registered

# Logout - redirects to /
post_logout_redirect_uri = "https://letsplaydarts.eu/"  ❌ NOT Registered
```

## Solution

### Quick Fix (5 Minutes)

Update WSO2 IS Service Provider to register **both** URIs:

**Option 1: Regex Pattern (Recommended)**

```
regexp=https://letsplaydarts\.eu(/callback|/)
```

**Option 2: Comma-Separated List**

```
https://letsplaydarts.eu/callback,https://letsplaydarts.eu/
```

### Implementation Steps

1. **Access WSO2 IS Management Console**

   ```
   URL: https://letsplaydarts.eu/auth/carbon
   Username: admin
   Password: admin
   ```

2. **Navigate to Service Providers**

   ```
   Main → Identity → Service Providers → List
   ```

3. **Edit OAuth Configuration**
   - Find your application
   - Click "Edit"
   - Expand "Inbound Authentication Configuration"
   - Click "Configure" under "OAuth/OpenID Connect Configuration"

4. **Update Callback URL Field**
   - Change from: `https://letsplaydarts.eu/callback`
   - Change to: `regexp=https://letsplaydarts\.eu(/callback|/)`

5. **Save Configuration**
   - Click "Update" (OAuth dialog)
   - Click "Update" (Service Provider page)

### Verification

**Test Login:**

```bash
1. Navigate to: https://letsplaydarts.eu
2. Click "Login"
3. Authenticate on WSO2 IS
4. Should redirect back to application ✅
```

**Test Logout:**

```bash
1. While logged in, click "Logout"
2. Should redirect to WSO2 IS logout
3. Should redirect back to home page ✅
4. No error message should appear ✅
```

## Technical Details

### Architecture Overview

```
┌─────────────┐         ┌─────────────┐         ┌─────────────┐
│   Browser   │ ◄─────► │    Nginx    │ ◄─────► │  Flask App  │
│             │         │   (Proxy)   │         │  (Port 5000)│
└─────────────┘         └─────────────┘         └─────────────┘
                               │
                               │ /auth/*
                               ▼
                        ┌─────────────┐
                        │  WSO2 IS    │
                        │ (Port 9443) │
                        └─────────────┘
```

### OAuth2 Flow

**Login Flow:**

```
1. User clicks "Login"
2. Flask → WSO2 IS: /oauth2/authorize?redirect_uri=.../callback
3. User authenticates
4. WSO2 IS validates redirect_uri ✅
5. WSO2 IS → Browser: Redirect to .../callback?code=xxx
6. Browser → Flask: GET /callback?code=xxx
7. Flask exchanges code for token
8. User is logged in ✅
```

**Logout Flow:**

```
1. User clicks "Logout"
2. Flask → WSO2 IS: /oidc/logout?post_logout_redirect_uri=.../
3. WSO2 IS validates post_logout_redirect_uri ❌ (FAILS HERE)
4. Error: "Post logout URI does not match"
```

**After Fix:**

```
1. User clicks "Logout"
2. Flask → WSO2 IS: /oidc/logout?post_logout_redirect_uri=.../
3. WSO2 IS validates post_logout_redirect_uri ✅
4. WSO2 IS → Browser: Redirect to .../
5. User is logged out ✅
```

### Code References

**Flask Application** (`auth.py`):

```python
def get_dynamic_redirect_uri() -> str:
    """Build callback URI dynamically"""
    scheme = request.scheme  # https
    host = request.host      # letsplaydarts.eu
    return f"{scheme}://{host}/callback"

def get_dynamic_post_logout_redirect_uri() -> str:
    """Build post-logout URI dynamically"""
    scheme = request.scheme  # https
    host = request.host      # letsplaydarts.eu
    return f"{scheme}://{host}/"

def logout_user(id_token: str | None = None) -> str:
    """Generate logout URL"""
    post_logout_uri = get_dynamic_post_logout_redirect_uri()
    params = {
        "post_logout_redirect_uri": post_logout_uri,  # ← Validated by WSO2 IS
    }
    if id_token:
        params["id_token_hint"] = id_token
    return f"{WSO2_IS_LOGOUT_URL}?{urlencode(params)}"
```

**Environment Variables** (`.env`):

```bash
WSO2_IS_URL=https://letsplaydarts.eu/auth
WSO2_CLIENT_ID=gKL8KC2FkWIz2r3553vraJ8pf8Ma
WSO2_CLIENT_SECRET=c1nJheSbpiBxsQPKvdm_FLU3rssa
WSO2_REDIRECT_URI=https://letsplaydarts.eu/callback
WSO2_POST_LOGOUT_REDIRECT_URI=https://letsplaydarts.eu/
```

**WSO2 IS Configuration** (`deployment.toml`):

```toml
[server]
hostname = "letsplaydarts.eu"
base_path = "https://letsplaydarts.eu/auth"

[transport.https.properties]
proxyPort = 443

[authentication.endpoints]
login_url = "${carbon.protocol}://letsplaydarts.eu/auth/authenticationendpoint/login.do"
retry_url = "${carbon.protocol}://letsplaydarts.eu/auth/authenticationendpoint/retry.do"
```

## Files Modified

### No Code Changes Required! ✅

This is purely a **configuration issue** in WSO2 IS. No application code needs to be changed.

### Configuration Changes

**WSO2 IS Service Provider** (via Management Console):

- **Before**: `Callback URLs: https://letsplaydarts.eu/callback`
- **After**: `Callback URLs: regexp=https://letsplaydarts\.eu(/callback|/)`

## Documentation Created

| File                           | Purpose                            |
| ------------------------------ | ---------------------------------- |
| `QUICK_FIX_REDIRECTS.md`       | 5-minute quick fix guide           |
| `FIX_REDIRECT_URIS.md`         | Detailed step-by-step instructions |
| `REDIRECT_FLOW_EXPLAINED.md`   | Visual explanation of the issue    |
| `REDIRECT_ISSUE_SUMMARY.md`    | This file - complete summary       |
| `update_wso2_callback_urls.sh` | Helper script with instructions    |
| `configure_wso2_redirects.py`  | Python script (for reference)      |

## Testing Checklist

After applying the fix:

- [ ] Can access application: `https://letsplaydarts.eu`
- [ ] Can click "Login" button
- [ ] Redirected to WSO2 IS login page
- [ ] Can authenticate with credentials
- [ ] Redirected back to application
- [ ] User is logged in (can see profile)
- [ ] Can click "Logout" button
- [ ] Redirected to WSO2 IS logout page
- [ ] Redirected back to home page
- [ ] No error messages appear
- [ ] User is logged out (session cleared)

## Rollback Procedure

If you need to revert the changes:

1. Access WSO2 IS Management Console
2. Navigate to Service Providers → List
3. Edit your application
4. In OAuth/OpenID Connect Configuration
5. Change Callback URL back to: `https://letsplaydarts.eu/callback`
6. Click Update twice

**Note**: This will break logout functionality again.

## Security Considerations

### Why Regex Pattern is Safe

The pattern `regexp=https://letsplaydarts\.eu(/callback|/)` is secure because:

- ✅ Exact domain match (escaped dots prevent subdomain wildcards)
- ✅ Limited to specific paths (`/callback` or `/`)
- ✅ No wildcards that could match unintended URLs
- ✅ Follows OAuth2 security best practices

### What NOT to Do

❌ **Don't use overly broad patterns:**

```
regexp=https://letsplaydarts\.eu/.*  # Too broad!
regexp=.*                             # NEVER do this!
```

✅ **Do use specific patterns:**

```
regexp=https://letsplaydarts\.eu(/callback|/)  # Good!
```

## Common Issues

### Issue 1: Still Getting Error After Update

**Symptoms**: Error persists after updating callback URLs

**Causes**:

- Changes not saved properly
- Browser cache
- Session still has old state

**Solutions**:

1. Verify you clicked "Update" **twice**
2. Clear browser cache and cookies
3. Try in incognito/private window
4. Check WSO2 IS logs: `docker logs wso2is`

### Issue 2: Can't Access Management Console

**Symptoms**: Can't access `https://letsplaydarts.eu/auth/carbon`

**Causes**:

- WSO2 IS not running
- Nginx not routing correctly
- Network issues

**Solutions**:

```bash
# Check if WSO2 IS is running
docker ps | grep wso2is

# Check WSO2 IS logs
docker logs wso2is 2>&1 | tail -50

# Restart WSO2 IS
docker-compose -f docker-compose-wso2.yml restart wso2is

# Wait 2-3 minutes for startup
```

### Issue 3: Regex Pattern Not Working

**Symptoms**: Still getting validation error with regex pattern

**Causes**:

- Some WSO2 IS versions have regex issues
- Syntax error in pattern

**Solutions**:

1. Use comma-separated list instead:

   ```
   https://letsplaydarts.eu/callback,https://letsplaydarts.eu/
   ```

2. Verify regex syntax (no typos)
3. Check WSO2 IS version compatibility

## Performance Impact

✅ **No performance impact**

- Configuration change only
- No additional processing
- No latency added
- No resource usage increase

## Monitoring

After applying the fix, monitor:

```bash
# Flask app logs
docker logs -f darts-app

# WSO2 IS logs
docker logs -f wso2is

# Nginx logs
docker logs -f nginx
```

Look for:

- ✅ Successful redirects
- ✅ No error messages
- ✅ Proper OAuth2 flow completion

## Summary

| Aspect               | Details                                 |
| -------------------- | --------------------------------------- |
| **Issue**            | Post-logout redirect URI not registered |
| **Impact**           | Logout functionality broken             |
| **Severity**         | High                                    |
| **Fix Time**         | 5 minutes                               |
| **Code Changes**     | None required                           |
| **Restart Required** | No                                      |
| **Testing Required** | Yes (login + logout)                    |
| **Rollback Risk**    | Low (easy to revert)                    |

## Next Steps

1. ✅ Apply the fix using `QUICK_FIX_REDIRECTS.md`
2. ✅ Test login and logout flows
3. ✅ Verify no error messages
4. ✅ Monitor logs for any issues
5. ✅ Document the change in your deployment notes

## Support Resources

- **Quick Fix**: `QUICK_FIX_REDIRECTS.md`
- **Detailed Guide**: `FIX_REDIRECT_URIS.md`
- **Flow Explanation**: `REDIRECT_FLOW_EXPLAINED.md`
- **Helper Script**: `./update_wso2_callback_urls.sh`

## Contact

If you need further assistance:

1. Check the documentation files listed above
2. Review application logs
3. Check WSO2 IS documentation
4. Test in isolation (curl commands)

---

**Last Updated**: Current  
**Status**: Ready to Apply  
**Confidence**: High (Standard OAuth2 configuration issue)
