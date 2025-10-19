# Fix: Missing /auth Prefix in OAuth2 Redirects

## Problem

When clicking login, the redirect goes to:

```
❌ https://letsplaydarts.eu/oauth2/authorize?sessionDataKey=...
```

But it should go to:

```
✅ https://letsplaydarts.eu/auth/oauth2/authorize?sessionDataKey=...
```

The `/auth` prefix is missing, causing a 404 error or incorrect routing.

## Root Cause

WSO2 Identity Server is not aware of the **proxy context path** (`/auth`). While we set the `base_path`, we also need to set `proxy_context_path` to tell WSO2 IS to include `/auth` in all generated URLs.

## Solution Applied ✅

### Configuration Change

**File**: `/data/dartserver-pythonapp/wso2is-config/deployment.toml`

**Added**:

```toml
[server]
hostname = "letsplaydarts.eu"
node_ip = "127.0.0.1"
base_path = "https://letsplaydarts.eu/auth"
proxy_context_path = "/auth"  # ← NEW: Tells WSO2 to include /auth in URLs
```

This configuration tells WSO2 IS:

- `base_path`: The full public URL including the context path
- `proxy_context_path`: The context path to prepend to all generated URLs

## How to Apply

### Step 1: Restart WSO2 IS Container

The configuration file has been updated. Now restart WSO2 IS to apply the changes:

```bash
cd /data/dartserver-pythonapp
docker-compose -f docker-compose-wso2.yml restart wso2is
```

### Step 2: Wait for Startup

WSO2 IS takes 2-3 minutes to fully start. Monitor the logs:

```bash
docker logs -f wso2is
```

Wait until you see:

```
WSO2 Carbon started in X sec
```

### Step 3: Test the Login Flow

1. Navigate to: `https://letsplaydarts.eu`
2. Click "Login" button
3. Should redirect to: `https://letsplaydarts.eu/auth/oauth2/authorize?...` ✅
4. Authenticate with your credentials
5. Should redirect back to the application ✅

## What This Fixes

### Before Fix

```
User clicks "Login"
    ↓
Flask redirects to: https://letsplaydarts.eu/auth/oauth2/authorize
    ↓
WSO2 IS processes request
    ↓
WSO2 IS redirects to: https://letsplaydarts.eu/oauth2/authorize?sessionDataKey=...
    ↓
❌ 404 Error - nginx doesn't know how to route /oauth2/authorize
```

### After Fix

```
User clicks "Login"
    ↓
Flask redirects to: https://letsplaydarts.eu/auth/oauth2/authorize
    ↓
WSO2 IS processes request
    ↓
WSO2 IS redirects to: https://letsplaydarts.eu/auth/oauth2/authorize?sessionDataKey=...
    ↓
✅ SUCCESS - nginx routes to WSO2 IS, user sees login page
```

## Technical Details

### Nginx Configuration

Nginx is configured to route `/auth/*` to WSO2 IS:

```nginx
location /auth/ {
    proxy_pass https://wso2is:9443/;
    # ... proxy headers ...
}
```

### WSO2 IS URL Generation

With `proxy_context_path = "/auth"`, WSO2 IS will:

- ✅ Generate URLs like: `/auth/oauth2/authorize`
- ✅ Generate URLs like: `/auth/authenticationendpoint/login.do`
- ✅ Include `/auth` in all redirects and links

Without `proxy_context_path`, WSO2 IS generates:

- ❌ URLs like: `/oauth2/authorize` (missing /auth)
- ❌ URLs like: `/authenticationendpoint/login.do` (missing /auth)

### Configuration Hierarchy

```toml
[server]
hostname = "letsplaydarts.eu"           # Domain name
base_path = "https://letsplaydarts.eu/auth"  # Full public URL
proxy_context_path = "/auth"            # Context path for URL generation

[transport.https.properties]
proxyPort = 443                         # Use standard HTTPS port
```

## Verification

### Check Generated URLs

After restart, check the logs to verify URLs are generated correctly:

```bash
# Check Flask app logs
docker logs darts-app 2>&1 | grep -i "authorization URL"

# Should show:
# Generated authorization URL: https://letsplaydarts.eu/auth/oauth2/authorize?...
```

### Test All Flows

1. **Login Flow**:
   - Click "Login"
   - Should redirect to: `https://letsplaydarts.eu/auth/oauth2/authorize`
   - Should show WSO2 IS login page
   - After login, should redirect back to app

2. **Logout Flow**:
   - Click "Logout"
   - Should redirect to: `https://letsplaydarts.eu/auth/oidc/logout`
   - Should redirect back to home page

3. **Authentication Endpoints**:
   - Login page: `https://letsplaydarts.eu/auth/authenticationendpoint/login.do`
   - Should load correctly with `/auth` prefix

## Common Issues

### Issue 1: Still Getting 404 After Restart

**Cause**: WSO2 IS not fully started or configuration not loaded

**Solution**:

```bash
# Check if WSO2 IS is running
docker ps | grep wso2is

# Check logs for errors
docker logs wso2is 2>&1 | tail -100

# Verify configuration was loaded
docker exec wso2is cat /home/wso2carbon/wso2is-6.1.0/repository/conf/deployment.toml | grep proxy_context_path
```

### Issue 2: URLs Still Missing /auth

**Cause**: Configuration file not mounted correctly

**Solution**:

```bash
# Verify the volume mount in docker-compose-wso2.yml
docker-compose -f docker-compose-wso2.yml config | grep -A 5 "wso2is-config"

# Should show:
# volumes:
#   - ./wso2is-config/deployment.toml:/home/wso2carbon/wso2is-6.1.0/repository/conf/deployment.toml
```

### Issue 3: Redirect Loop

**Cause**: Conflicting proxy configurations

**Solution**: Check nginx configuration and ensure it's not modifying the URLs incorrectly.

## Related Issues

This fix addresses the **missing /auth prefix** issue. You may also need to fix:

1. **Post-Logout Redirect URI**: See `FIX_REDIRECT_URIS.md`
   - Register both `/callback` and `/` in WSO2 IS Service Provider

2. **Callback URI Registration**: See `QUICK_FIX_REDIRECTS.md`
   - Ensure callback URLs are registered in WSO2 IS

## Summary

| Aspect                   | Before                                | After                                      |
| ------------------------ | ------------------------------------- | ------------------------------------------ |
| **OAuth2 Authorize URL** | `/oauth2/authorize` ❌                | `/auth/oauth2/authorize` ✅                |
| **Login Endpoint**       | `/authenticationendpoint/login.do` ❌ | `/auth/authenticationendpoint/login.do` ✅ |
| **Logout Endpoint**      | `/oidc/logout` ❌                     | `/auth/oidc/logout` ✅                     |
| **Configuration**        | Only `base_path`                      | `base_path` + `proxy_context_path` ✅      |
| **Restart Required**     | N/A                                   | Yes (WSO2 IS only)                         |

## Quick Reference

### Files Modified

- ✅ `/data/dartserver-pythonapp/wso2is-config/deployment.toml`

### Commands to Run

```bash
# Restart WSO2 IS
docker-compose -f docker-compose-wso2.yml restart wso2is

# Monitor startup
docker logs -f wso2is

# Test login
# Navigate to https://letsplaydarts.eu and click "Login"
```

### Expected Behavior

- ✅ Login redirects to: `https://letsplaydarts.eu/auth/oauth2/authorize`
- ✅ Login page loads at: `https://letsplaydarts.eu/auth/authenticationendpoint/login.do`
- ✅ Logout redirects to: `https://letsplaydarts.eu/auth/oidc/logout`
- ✅ All URLs include the `/auth` prefix

## Next Steps

After applying this fix:

1. ✅ Restart WSO2 IS container
2. ✅ Test login flow
3. ✅ Test logout flow
4. ⚠️ Fix post-logout redirect URI (see `FIX_REDIRECT_URIS.md`)

The post-logout redirect URI issue is separate and requires updating the WSO2 IS Service Provider configuration via the Management Console.
