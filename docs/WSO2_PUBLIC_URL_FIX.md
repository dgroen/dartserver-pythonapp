# WSO2 Public URL Fix - Multi-Domain Authentication

## Problem

When accessing the application from `https://letsplaydarts.eu` and clicking login, users were redirected to `https://localhost:9443`, which doesn't work from remote computers or mobile devices.

## Root Cause

The `WSO2_IS_URL` environment variable was set to `https://localhost:9443`, which is only accessible from the local machine. This caused:

1. **Browser redirects** (login/logout) to point to localhost
2. **Remote users** unable to authenticate
3. **Mobile devices** unable to access the authentication server

## Solution Architecture

We implemented a **dual-URL system** that separates:

1. **Public URL** (`WSO2_IS_URL`): For browser redirects that users see
2. **Internal URL** (`WSO2_IS_INTERNAL_URL`): For backend server-to-server API calls

### URL Usage Matrix

| Endpoint             | Type             | URL Used | Reason                                      |
| -------------------- | ---------------- | -------- | ------------------------------------------- |
| `/oauth2/authorize`  | Browser redirect | Public   | User's browser needs to access it           |
| `/oidc/logout`       | Browser redirect | Public   | User's browser needs to access it           |
| `/oauth2/token`      | Backend API      | Internal | Server-to-server call (faster, more secure) |
| `/oauth2/userinfo`   | Backend API      | Internal | Server-to-server call                       |
| `/oauth2/introspect` | Backend API      | Internal | Server-to-server call                       |
| `/oauth2/jwks`       | Backend API      | Internal | Server-to-server call                       |

## Implementation

### 1. Code Changes (`auth.py`)

```python
# WSO2 Identity Server Configuration
# WSO2_IS_URL: Public URL for browser redirects (authorize, logout)
# WSO2_IS_INTERNAL_URL: Internal URL for backend API calls (token, userinfo, introspect)
WSO2_IS_URL = os.getenv("WSO2_IS_URL", "https://localhost:9443")
WSO2_IS_INTERNAL_URL = os.getenv("WSO2_IS_INTERNAL_URL", WSO2_IS_URL)

# Browser-facing URLs (use public URL)
WSO2_IS_AUTHORIZE_URL = f"{WSO2_IS_URL}/oauth2/authorize"
WSO2_IS_LOGOUT_URL = f"{WSO2_IS_URL}/oidc/logout"

# Backend API URLs (use internal URL for server-to-server communication)
WSO2_IS_TOKEN_URL = f"{WSO2_IS_INTERNAL_URL}/oauth2/token"
WSO2_IS_USERINFO_URL = f"{WSO2_IS_INTERNAL_URL}/oauth2/userinfo"
WSO2_IS_JWKS_URL = f"{WSO2_IS_INTERNAL_URL}/oauth2/jwks"
WSO2_IS_INTROSPECT_URL = f"{WSO2_IS_INTERNAL_URL}/oauth2/introspect"
```

### 2. Environment Configuration

#### For Local Development (`.env`)

```bash
# Public URL (what users see in browser)
WSO2_IS_URL=https://letsplaydarts.eu/auth

# Internal URL (optional - if not set, uses WSO2_IS_URL)
# Leave commented out for local development
#WSO2_IS_INTERNAL_URL=https://wso2is:9443
```

#### For Docker Deployment (`docker-compose-wso2.yml`)

```yaml
environment:
  # Public URL for browser redirects
  WSO2_IS_URL: https://letsplaydarts.eu/auth
  # Internal Docker network URL for backend API calls
  WSO2_IS_INTERNAL_URL: https://wso2is:9443
```

### 3. Nginx Configuration

The nginx reverse proxy routes `/auth/` to the WSO2 IS container:

```nginx
location /auth/ {
    limit_req zone=auth_limit burst=5 nodelay;

    proxy_pass https://wso2_is/;
    proxy_set_header Host $host;
    proxy_set_header X-Real-IP $remote_addr;
    proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
    proxy_set_header X-Forwarded-Proto $scheme;
    proxy_ssl_verify off;
}
```

## Benefits

### 1. **Remote Access Works**

- Users can now login from any device
- Mobile devices can authenticate
- No localhost references in browser

### 2. **Performance Optimization**

- Backend API calls use internal Docker network (faster)
- No unnecessary routing through nginx for server-to-server calls
- Reduced latency for token validation

### 3. **Security Improvement**

- Internal API calls don't go through public internet
- Reduced attack surface
- Better network isolation

### 4. **Flexibility**

- Works with or without Docker
- Supports multiple deployment scenarios
- Backward compatible (if `WSO2_IS_INTERNAL_URL` not set, uses `WSO2_IS_URL`)

## Deployment Scenarios

### Scenario 1: Docker with Nginx (Production)

```bash
# .env or docker-compose.yml
WSO2_IS_URL=https://letsplaydarts.eu/auth
WSO2_IS_INTERNAL_URL=https://wso2is:9443
```

**Flow:**

1. User browser → `https://letsplaydarts.eu/auth/oauth2/authorize` (via nginx)
2. Backend API → `https://wso2is:9443/oauth2/token` (direct Docker network)

### Scenario 2: Local Development (No Docker)

```bash
# .env
WSO2_IS_URL=https://localhost:9443
# WSO2_IS_INTERNAL_URL not set (uses WSO2_IS_URL)
```

**Flow:**

1. User browser → `https://localhost:9443/oauth2/authorize`
2. Backend API → `https://localhost:9443/oauth2/token`

### Scenario 3: Docker without Nginx

```bash
# docker-compose.yml
WSO2_IS_URL=https://letsplaydarts.eu:9443
WSO2_IS_INTERNAL_URL=https://wso2is:9443
```

**Flow:**

1. User browser → `https://letsplaydarts.eu:9443/oauth2/authorize` (direct to WSO2)
2. Backend API → `https://wso2is:9443/oauth2/token` (Docker network)

## Testing

All 38 authentication tests pass:

```bash
pytest tests/unit/test_auth.py -v
# ✅ 38 passed in 3.72s
```

## WSO2 Configuration Required

In WSO2 Identity Server, register all redirect URIs:

```
Callback URL (Regex):
regexp=(https://localhost:5000/callback|https://letsplaydarts\.eu:5000/callback|https://letsplaydarts\.eu/callback)
```

## Troubleshooting

### Issue: Still redirecting to localhost

**Check:**

1. Restart the application after changing `.env`
2. Verify `WSO2_IS_URL` in environment variables
3. Check browser console for redirect URL
4. Clear browser cache and cookies

### Issue: Backend API calls failing

**Check:**

1. Verify `WSO2_IS_INTERNAL_URL` is accessible from darts-app container
2. Check Docker network connectivity: `docker exec darts-app curl -k https://wso2is:9443`
3. Verify SSL verification is disabled: `WSO2_IS_VERIFY_SSL=False`

### Issue: CORS errors

**Check:**

1. Nginx CORS headers are configured
2. WSO2 IS CORS settings allow your domain
3. Check browser console for specific CORS error

## Verification Steps

### 1. Check Environment Variables

```bash
# Inside darts-app container
docker exec darts-app env | grep WSO2
```

Expected output:

```
WSO2_IS_URL=https://letsplaydarts.eu/auth
WSO2_IS_INTERNAL_URL=https://wso2is:9443
```

### 2. Test Login Flow

1. Open `https://letsplaydarts.eu` in browser
2. Click "Login"
3. Should redirect to `https://letsplaydarts.eu/auth/oauth2/authorize`
4. After login, should redirect back to `https://letsplaydarts.eu/callback`

### 3. Check Logs

```bash
# Check darts-app logs
docker logs darts-app | grep -i wso2

# Should see:
# Dynamic redirect URI: https://letsplaydarts.eu/callback
```

## Summary

This fix enables remote authentication by:

- ✅ Using public URL for browser redirects
- ✅ Using internal URL for backend API calls
- ✅ Supporting multiple deployment scenarios
- ✅ Maintaining backward compatibility
- ✅ Improving performance and security

Users can now successfully login from any device, anywhere! 🎉
