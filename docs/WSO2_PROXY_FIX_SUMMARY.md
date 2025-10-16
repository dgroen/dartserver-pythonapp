# WSO2 Identity Server Reverse Proxy Configuration Fix

## Issue Summary
When users clicked the login button on https://letsplaydarts.eu, they encountered two sequential issues:
1. **Initial Issue**: Redirect to port 9443 (e.g., `https://letsplaydarts.eu:9443/oauth2/authorize`)
2. **Secondary Issue**: Missing `/auth` prefix causing 404 errors (e.g., `https://letsplaydarts.eu/authenticationendpoint/login.do`)

## Root Cause Analysis

### Issue 1: Port 9443 in URLs
WSO2 Identity Server was not configured to recognize it's behind a reverse proxy. When generating OAuth2 URLs, it used its internal HTTPS port (9443) instead of the standard HTTPS port (443) exposed by nginx.

### Issue 2: Missing /auth Prefix
The authentication endpoint URLs were configured with relative paths (e.g., `/authenticationendpoint/login.do`) instead of absolute paths that include the `/auth` prefix required by the nginx reverse proxy routing.

## Configuration Changes

### File Modified: `/data/dartserver-pythonapp/wso2is-config/deployment.toml`

#### Change 1: Added Proxy Port Configuration
```toml
[transport.https.properties]
proxyPort = 443
```
**Location**: After line 5 (after `base_path` configuration)
**Purpose**: Tells WSO2 IS to use port 443 in all generated URLs instead of 9443

#### Change 2: Updated Authentication Endpoint URLs
```toml
[authentication.endpoints]
login_url = "${carbon.protocol}://letsplaydarts.eu/auth/authenticationendpoint/login.do"
retry_url = "${carbon.protocol}://letsplaydarts.eu/auth/authenticationendpoint/retry.do"
```
**Location**: Lines 65-67
**Changed From**: Relative paths (`/authenticationendpoint/login.do`)
**Changed To**: Absolute URLs with `/auth` prefix
**Purpose**: Ensures authentication endpoints include the `/auth` prefix required by nginx routing

## Architecture Overview

```
User Browser
    ↓
https://letsplaydarts.eu (port 443)
    ↓
Nginx Reverse Proxy
    ├─ / → darts-app:5000 (Flask application)
    ├─ /auth/ → wso2is:9443 (WSO2 Identity Server)
    └─ /api/v1/ → api-gateway:8080
    ↓
WSO2 IS Container (internal port 9443)
```

## How the Fix Works

### Before Fix:
1. User clicks login → Flask generates auth URL: `https://letsplaydarts.eu/auth/oauth2/authorize`
2. Nginx proxies to WSO2 IS
3. WSO2 IS redirects to: `https://letsplaydarts.eu:9443/authenticationendpoint/login.do` ❌
   - Wrong port (9443 instead of 443)
   - Missing /auth prefix

### After Fix:
1. User clicks login → Flask generates auth URL: `https://letsplaydarts.eu/auth/oauth2/authorize`
2. Nginx proxies to WSO2 IS
3. WSO2 IS redirects to: `https://letsplaydarts.eu/auth/authenticationendpoint/login.do` ✅
   - Correct port (443, not shown in URL)
   - Includes /auth prefix
4. Nginx proxies to WSO2 IS
5. Login page displays correctly

## Deployment Instructions

### Step 1: Restart WSO2 IS Container
The configuration file is already updated. You just need to restart the container:

```bash
cd /data/dartserver-pythonapp
docker-compose -f docker-compose-wso2.yml restart wso2is
```

### Step 2: Wait for Startup
WSO2 IS takes approximately 2-3 minutes to fully start. Monitor the logs:

```bash
docker logs -f darts-wso2is
```

Look for messages indicating the server has started successfully.

### Step 3: Verify the Fix
1. Open browser and navigate to: https://letsplaydarts.eu
2. Click the "Login" button
3. Verify the URL stays on `https://letsplaydarts.eu/auth/...` (no port 9443)
4. Verify the login page loads correctly (no 404 error)
5. Complete the login flow with test credentials

## Testing Checklist

- [ ] Login button redirects to correct URL (with /auth prefix, no port)
- [ ] Login page loads without 404 error
- [ ] Can enter credentials and submit
- [ ] OAuth callback works correctly
- [ ] User is redirected back to application after login
- [ ] Session is maintained
- [ ] Logout works correctly

## Rollback Procedure

If you need to rollback these changes:

1. Edit `/data/dartserver-pythonapp/wso2is-config/deployment.toml`
2. Remove the `[transport.https.properties]` section
3. Change authentication endpoints back to relative paths:
   ```toml
   [authentication.endpoints]
   login_url = "/authenticationendpoint/login.do"
   retry_url = "/authenticationendpoint/retry.do"
   ```
4. Restart WSO2 IS: `docker-compose -f docker-compose-wso2.yml restart wso2is`

## Related Files (No Changes Needed)

These files were already correctly configured:

- **nginx/nginx.conf**: Reverse proxy routing for `/auth/` → `wso2is:9443`
- **.env**: WSO2_IS_URL set to `https://letsplaydarts.eu/auth`
- **auth.py**: Dynamic redirect URI generation using Flask request context
- **docker-compose-wso2.yml**: Environment variables for WSO2 IS URL

## Additional Notes

- The `base_path` in deployment.toml was already correctly set to `https://letsplaydarts.eu/auth`
- OAuth endpoint URLs (consent, error, logout) were already correctly configured with the `/auth` prefix
- The nginx SSL configuration is working correctly
- The ProxyFix middleware in Flask is correctly configured to trust X-Forwarded headers

## References

- WSO2 IS Documentation: [Configuring the Proxy Server and the Load Balancer](https://is.docs.wso2.com/en/latest/deploy/configure-the-proxy-server-and-the-load-balancer/)
- WSO2 IS Configuration Reference: [deployment.toml](https://is.docs.wso2.com/en/latest/references/config-catalog/)