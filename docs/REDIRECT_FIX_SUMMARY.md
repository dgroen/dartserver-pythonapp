# WSO2 IS Redirect Fix - Summary

## Problem Identified
The login redirect was using `localhost:5000` or `letsplaydarts.eu:5000` instead of `letsplaydarts.eu` (port 443 via reverse proxy).

## Root Cause
The `.env` file had hardcoded redirect URIs with port 5000:
```
WSO2_REDIRECT_URI=https://letsplaydarts.eu:5000/callback
WSO2_POST_LOGOUT_REDIRECT_URI=https://letsplaydarts.eu:5000/
```

## Changes Applied

### 1. ✅ Fixed `.env` file
Changed redirect URIs to use standard HTTPS port (443) via reverse proxy:
```bash
WSO2_REDIRECT_URI=https://letsplaydarts.eu/callback
WSO2_POST_LOGOUT_REDIRECT_URI=https://letsplaydarts.eu/
```

### 2. ✅ Updated `nginx/nginx.conf`
Added `X-Forwarded-Host` header to ensure Flask receives the correct external hostname:
```nginx
proxy_set_header X-Forwarded-Host $host;
```

### 3. ✅ Updated `docker-compose-wso2.yml`
- Changed default redirect URIs from localhost to letsplaydarts.eu
- Enabled secure cookies: `SESSION_COOKIE_SECURE: "True"`
- Uncommented WSO2 IS deployment.toml volume mount

### 4. ✅ Verified `wso2is-config/deployment.toml`
Configuration is correct with:
```toml
hostname = "letsplaydarts.eu"
base_path = "https://letsplaydarts.eu/auth"
```

## Required Manual Steps

### Step 1: Update WSO2 IS OAuth Application Configuration

**IMPORTANT**: You must update the OAuth application in WSO2 IS to accept the new redirect URI.

1. **Access WSO2 IS Admin Console**:
   ```
   URL: https://letsplaydarts.eu/auth/carbon
   Username: admin
   Password: admin
   ```

2. **Navigate to Service Providers**:
   - Main Menu → Identity → Service Providers → List
   - Find your OAuth application (the one using client ID: `gKL8KC2FkWIz2r3553vraJ8pf8Ma`)

3. **Edit Inbound Authentication Configuration**:
   - Expand "Inbound Authentication Configuration"
   - Click "OAuth/OpenID Connect Configuration"
   - Click "Edit"

4. **Update Callback URLs**:
   Replace the old callback URL with:
   ```
   https://letsplaydarts.eu/callback
   ```
   
   Or use a regex pattern to support both (for testing):
   ```
   regexp=(https://letsplaydarts\.eu/callback|https://letsplaydarts\.eu:5000/callback)
   ```

5. **Click "Update"** to save the changes

### Step 2: Restart Services

Restart the Docker services to apply all configuration changes:

```bash
cd /data/dartserver-pythonapp
docker-compose -f docker-compose-wso2.yml down
docker-compose -f docker-compose-wso2.yml up -d
```

Wait for all services to be healthy (especially WSO2 IS takes ~2 minutes to start).

### Step 3: Verify Configuration

Run the verification script:

```bash
./scripts/verify-redirect-config.sh
```

### Step 4: Test the Login Flow

1. **Open browser** and navigate to:
   ```
   https://letsplaydarts.eu/login
   ```

2. **Open browser DevTools** (F12) → Network tab

3. **Click login** and observe the redirect to WSO2 IS

4. **Check the authorization URL** in the network tab. It should contain:
   ```
   redirect_uri=https://letsplaydarts.eu/callback
   ```
   
   **NOT**:
   - ❌ `redirect_uri=http://localhost:5000/callback`
   - ❌ `redirect_uri=https://letsplaydarts.eu:5000/callback`

5. **Complete the login** and verify you're redirected back to:
   ```
   https://letsplaydarts.eu/callback?code=...
   ```

## How It Works Now

```
User Browser
    ↓
    ↓ https://letsplaydarts.eu/login
    ↓
Nginx (Port 443)
    ↓ X-Forwarded-Proto: https
    ↓ X-Forwarded-Host: letsplaydarts.eu
    ↓
Flask App (Port 5000)
    ↓ ProxyFix processes headers
    ↓ request.scheme = "https"
    ↓ request.host = "letsplaydarts.eu"
    ↓
get_dynamic_redirect_uri()
    ↓ Returns: https://letsplaydarts.eu/callback
    ↓
Authorization URL
    ↓ https://letsplaydarts.eu/auth/oauth2/authorize?
    ↓   client_id=...&
    ↓   redirect_uri=https://letsplaydarts.eu/callback
    ↓
User redirected to WSO2 IS
    ↓ User authenticates
    ↓
WSO2 IS redirects back
    ↓ https://letsplaydarts.eu/callback?code=...
    ↓
Nginx → Flask → Token Exchange → Success!
```

## Troubleshooting

### Issue: Still seeing localhost in redirect URI

**Check 1**: Verify nginx is passing the correct headers
```bash
docker logs darts-app 2>&1 | grep "Request headers"
```

Look for:
```
X-Forwarded-Proto: https
X-Forwarded-Host: letsplaydarts.eu
```

**Check 2**: Verify ProxyFix is working
```bash
docker logs darts-app 2>&1 | grep "Dynamic redirect URI"
```

Should show:
```
Dynamic redirect URI: https://letsplaydarts.eu/callback
```

**Check 3**: Clear browser cache and cookies
```
Ctrl+Shift+Delete → Clear all cookies and cached files
```

### Issue: WSO2 IS returns "invalid_redirect_uri" error

**Solution**: The OAuth application in WSO2 IS doesn't have the new callback URL registered.
- Follow "Step 1: Update WSO2 IS OAuth Application Configuration" above
- Make sure the callback URL is exactly: `https://letsplaydarts.eu/callback`

### Issue: Session/cookie issues after login

**Check**: Verify secure cookies are enabled
```bash
docker exec darts-app printenv | grep SESSION_COOKIE_SECURE
```

Should show:
```
SESSION_COOKIE_SECURE=True
```

## Files Modified

1. ✅ `.env` - Fixed redirect URIs (removed port 5000)
2. ✅ `nginx/nginx.conf` - Added X-Forwarded-Host header
3. ✅ `docker-compose-wso2.yml` - Updated default redirect URIs and enabled secure cookies
4. ✅ `wso2is-config/deployment.toml` - Already correct (no changes needed)

## Additional Resources

- Full documentation: `docs/wso2-redirect-fix.md`
- Verification script: `scripts/verify-redirect-config.sh`