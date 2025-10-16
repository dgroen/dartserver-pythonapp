# OAuth2 Redirect Flow - Problem and Solution

## The Problem

### Current State: ❌ Post-Logout Redirect Fails

```
┌─────────────────────────────────────────────────────────────────┐
│                         Login Flow (✅ Works)                    │
└─────────────────────────────────────────────────────────────────┘

User clicks "Login"
    │
    ├─→ Flask redirects to WSO2 IS with:
    │   redirect_uri=https://letsplaydarts.eu/callback
    │
    ├─→ User authenticates on WSO2 IS
    │
    ├─→ WSO2 IS validates redirect_uri ✅
    │   (matches registered: https://letsplaydarts.eu/callback)
    │
    └─→ WSO2 IS redirects back to:
        https://letsplaydarts.eu/callback?code=xxx
        
        ✅ SUCCESS - User is logged in


┌─────────────────────────────────────────────────────────────────┐
│                      Logout Flow (❌ Fails)                      │
└─────────────────────────────────────────────────────────────────┘

User clicks "Logout"
    │
    ├─→ Flask redirects to WSO2 IS with:
    │   post_logout_redirect_uri=https://letsplaydarts.eu/
    │
    ├─→ WSO2 IS validates post_logout_redirect_uri ❌
    │   (NOT in registered callbacks!)
    │
    └─→ ERROR: "Post logout URI does not match with 
               registered callback URI"
        
        ❌ FAILED - User sees error page
```

## Why This Happens

WSO2 Identity Server **validates ALL redirect URIs** for security:

1. **Login Flow**: Validates `redirect_uri` parameter
2. **Logout Flow**: Validates `post_logout_redirect_uri` parameter

**Current WSO2 IS Configuration:**
```
Registered Callback URLs:
  ✅ https://letsplaydarts.eu/callback
  ❌ https://letsplaydarts.eu/         <-- MISSING!
```

## The Solution

### Register BOTH URIs in WSO2 IS

```
┌─────────────────────────────────────────────────────────────────┐
│                    Updated Configuration                         │
└─────────────────────────────────────────────────────────────────┘

Option 1: Regex Pattern (Recommended)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
regexp=https://letsplaydarts\.eu(/callback|/)

This allows:
  ✅ https://letsplaydarts.eu/callback  (login)
  ✅ https://letsplaydarts.eu/          (logout)


Option 2: Comma-Separated List
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
https://letsplaydarts.eu/callback,https://letsplaydarts.eu/

This explicitly lists both URIs.
```

### After Fix: ✅ Both Flows Work

```
┌─────────────────────────────────────────────────────────────────┐
│                         Login Flow (✅ Works)                    │
└─────────────────────────────────────────────────────────────────┘

User clicks "Login"
    │
    ├─→ Flask redirects to WSO2 IS with:
    │   redirect_uri=https://letsplaydarts.eu/callback
    │
    ├─→ User authenticates on WSO2 IS
    │
    ├─→ WSO2 IS validates redirect_uri ✅
    │   (matches pattern: /callback)
    │
    └─→ WSO2 IS redirects back to:
        https://letsplaydarts.eu/callback?code=xxx
        
        ✅ SUCCESS - User is logged in


┌─────────────────────────────────────────────────────────────────┐
│                      Logout Flow (✅ Works)                      │
└─────────────────────────────────────────────────────────────────┘

User clicks "Logout"
    │
    ├─→ Flask redirects to WSO2 IS with:
    │   post_logout_redirect_uri=https://letsplaydarts.eu/
    │
    ├─→ WSO2 IS validates post_logout_redirect_uri ✅
    │   (matches pattern: /)
    │
    └─→ WSO2 IS redirects back to:
        https://letsplaydarts.eu/
        
        ✅ SUCCESS - User is logged out and back at home page
```

## Configuration Steps

### Step-by-Step Guide

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

3. **Edit Your Application**
   - Find your OAuth2 application
   - Click "Edit"

4. **Update OAuth Configuration**
   - Expand "Inbound Authentication Configuration"
   - Click "Configure" under "OAuth/OpenID Connect Configuration"
   - Find the "Callback Url" field

5. **Update Callback URL**
   
   **Current value:**
   ```
   https://letsplaydarts.eu/callback
   ```
   
   **New value (regex pattern):**
   ```
   regexp=https://letsplaydarts\.eu(/callback|/)
   ```
   
   **OR (comma-separated):**
   ```
   https://letsplaydarts.eu/callback,https://letsplaydarts.eu/
   ```

6. **Save Configuration**
   - Click "Update" in the OAuth dialog
   - Click "Update" again in the Service Provider page

## Verification

### Test Login Flow
```bash
1. Navigate to: https://letsplaydarts.eu
2. Click "Login" button
3. Authenticate on WSO2 IS
4. Should redirect back to: https://letsplaydarts.eu
5. ✅ You should be logged in
```

### Test Logout Flow
```bash
1. While logged in, click "Logout" button
2. Should redirect to WSO2 IS logout page
3. Should redirect back to: https://letsplaydarts.eu/
4. ✅ You should be logged out, no error message
```

## Technical Details

### Flask Application Code

**Login Redirect** (`auth.py`):
```python
def get_authorization_url(state: str | None = None) -> str:
    redirect_uri = get_dynamic_redirect_uri()  # → https://letsplaydarts.eu/callback
    params = {
        "response_type": "code",
        "client_id": WSO2_CLIENT_ID,
        "redirect_uri": redirect_uri,  # ← This is validated
        "scope": "openid profile email groups",
    }
    return f"{WSO2_IS_AUTHORIZE_URL}?{urlencode(params)}"
```

**Logout Redirect** (`auth.py`):
```python
def logout_user(id_token: str | None = None) -> str:
    post_logout_uri = get_dynamic_post_logout_redirect_uri()  # → https://letsplaydarts.eu/
    params = {
        "post_logout_redirect_uri": post_logout_uri,  # ← This is validated
    }
    if id_token:
        params["id_token_hint"] = id_token
    return f"{WSO2_IS_LOGOUT_URL}?{urlencode(params)}"
```

### Environment Variables (`.env`)

```bash
# These are used as fallbacks, but the app uses dynamic URIs
WSO2_REDIRECT_URI=https://letsplaydarts.eu/callback
WSO2_POST_LOGOUT_REDIRECT_URI=https://letsplaydarts.eu/
```

### WSO2 IS Configuration (`deployment.toml`)

```toml
[server]
hostname = "letsplaydarts.eu"
base_path = "https://letsplaydarts.eu/auth"

[transport.https.properties]
proxyPort = 443  # Use standard HTTPS port in URLs

[authentication.endpoints]
login_url = "${carbon.protocol}://letsplaydarts.eu/auth/authenticationendpoint/login.do"
retry_url = "${carbon.protocol}://letsplaydarts.eu/auth/authenticationendpoint/retry.do"
```

## Common Issues

### Issue 1: Still Getting Error After Update

**Cause**: Changes not saved properly

**Solution**:
1. Make sure you clicked "Update" **twice**:
   - Once in the OAuth/OpenID Connect Configuration dialog
   - Once in the Service Provider edit page
2. Clear browser cache and cookies
3. Try in an incognito/private window

### Issue 2: Regex Pattern Not Working

**Cause**: Some WSO2 IS versions have issues with regex

**Solution**: Use comma-separated list instead:
```
https://letsplaydarts.eu/callback,https://letsplaydarts.eu/
```

### Issue 3: Can't Access Management Console

**Cause**: WSO2 IS not running or not accessible

**Solution**:
```bash
# Check if WSO2 IS is running
docker ps | grep wso2is

# Check WSO2 IS logs
docker logs wso2is

# Restart if needed
docker-compose -f docker-compose-wso2.yml restart wso2is
```

## Security Considerations

### Why WSO2 IS Validates Redirect URIs

1. **Prevent Open Redirects**: Attackers can't redirect users to malicious sites
2. **Authorization Code Theft**: Prevents stealing authorization codes
3. **OAuth2 Security Best Practice**: Required by OAuth2 specification

### Regex Pattern Security

The regex pattern `regexp=https://letsplaydarts\.eu(/callback|/)` is secure because:
- ✅ Exact domain match (escaped dots)
- ✅ Limited to specific paths
- ✅ No wildcards that could match unintended URLs

### Alternative: Wildcard Pattern (NOT RECOMMENDED)

```
regexp=https://letsplaydarts\.eu/.*
```

⚠️ **Don't use this!** It allows ANY path under your domain, which is less secure.

## Summary

| Aspect | Before Fix | After Fix |
|--------|-----------|-----------|
| **Login Flow** | ✅ Works | ✅ Works |
| **Logout Flow** | ❌ Fails | ✅ Works |
| **Registered URIs** | Only `/callback` | Both `/callback` and `/` |
| **Error Message** | "Post logout URI does not match" | None |
| **User Experience** | Broken logout | Seamless login/logout |

## Quick Reference

### Files to Check
- `/data/dartserver-pythonapp/.env` - Environment variables
- `/data/dartserver-pythonapp/auth.py` - Authentication logic
- `/data/dartserver-pythonapp/wso2is-config/deployment.toml` - WSO2 IS config

### Commands to Run
```bash
# Show configuration instructions
./update_wso2_callback_urls.sh

# Check Flask app logs
docker logs darts-app 2>&1 | tail -50

# Check WSO2 IS logs
docker logs wso2is 2>&1 | tail -50

# Restart WSO2 IS (if needed)
docker-compose -f docker-compose-wso2.yml restart wso2is
```

### URLs to Access
- **Application**: https://letsplaydarts.eu
- **WSO2 IS Console**: https://letsplaydarts.eu/auth/carbon
- **OAuth2 Authorize**: https://letsplaydarts.eu/auth/oauth2/authorize
- **OIDC Logout**: https://letsplaydarts.eu/auth/oidc/logout

## Need Help?

If you're still experiencing issues after following this guide:

1. Check browser console for JavaScript errors
2. Check Flask app logs: `docker logs darts-app`
3. Check WSO2 IS logs: `docker logs wso2is`
4. Verify nginx is routing correctly: `docker logs nginx`
5. Test with curl to isolate the issue

For detailed troubleshooting, see `FIX_REDIRECT_URIS.md`.