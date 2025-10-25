# WSO2 IS Management Console Access Fix

## Problem

The WSO2 IS Management Console at `https://letsplaydarts.eu/auth/carbon` is not accessible because:

1. WSO2 IS redirects to `/carbon/admin/index.jsp` (missing `/auth` prefix)
2. The Management Console (`/carbon`) **does not respect** the `base_path` configuration in WSO2 IS 5.11.0
3. This is a known limitation of WSO2 Identity Server when deployed behind a reverse proxy with a context path

## Solutions

### Option 1: Access Console via Direct Port (RECOMMENDED)

Access the Management Console directly on port 9443, bypassing nginx:

```
https://letsplaydarts.eu:9443/carbon
```

**Credentials:**

- Username: `admin` <!-- pragma: allowlist secret -->
- Password: `admin` <!-- pragma: allowlist secret -->

**Pros:**

- ✅ Works immediately
- ✅ No configuration changes needed
- ✅ Bypasses reverse proxy complexity

**Cons:**

- ⚠️ Requires port 9443 to be accessible (currently exposed in docker-compose)
- ⚠️ Different URL than other services

---

### Option 2: Add Nginx Rewrite Rule for /carbon

Add a special nginx rewrite rule to handle the `/carbon` redirect:

**Edit:** `/data/dartserver-pythonapp/nginx/nginx.conf`

Add this **before** the existing `location /auth/` block:

```nginx
# Special handling for WSO2 IS Management Console
location = /carbon/admin/index.jsp {
    return 301 https://$host/auth/carbon/admin/index.jsp;
}

location /carbon/ {
    return 301 https://$host/auth$request_uri;
}

# WSO2 Identity Server Routes
location /auth/ {
    # ... existing configuration ...
}
```

Then restart nginx:

```bash
docker-compose restart nginx
```

**Pros:**

- ✅ Allows access via `https://letsplaydarts.eu/auth/carbon`
- ✅ Consistent URL structure

**Cons:**

- ⚠️ Requires nginx configuration change
- ⚠️ May need additional rewrites for other console paths

---

### Option 3: Use WSO2 IS 6.x or Later

WSO2 Identity Server 6.0+ has better support for reverse proxy deployments with context paths.

**Upgrade to WSO2 IS 6.1.0:**

Edit `docker-compose-wso2.yml`:

```yaml
services:
  wso2is:
    image: wso2/wso2is:6.1.0 # Changed from 5.11.0
```

**Pros:**

- ✅ Better reverse proxy support
- ✅ Modern features and security updates

**Cons:**

- ⚠️ Requires migration and testing
- ⚠️ Configuration file format may differ
- ⚠️ Service Provider configurations may need updates

---

## Current Status

✅ **WSO2 IS is running** and healthy  
✅ **OAuth2 endpoints work** (login/logout via application)  
⚠️ **Management Console** requires one of the solutions above

## Quick Fix (5 seconds)

Access the console directly:

```
https://letsplaydarts.eu:9443/carbon
```

Login with `admin` / `admin`

---

## Why This Happens

### Technical Explanation

1. **WSO2 IS Internal Routing**: The Management Console (`/carbon`) is a separate web application that doesn't use the same routing as OAuth2 endpoints

2. **base_path Limitation**: The `base_path` configuration in `deployment.toml` affects:
   - ✅ OAuth2 endpoints (`/oauth2/*`)
   - ✅ OIDC endpoints (`/oidc/*`)
   - ✅ Authentication endpoints (`/authenticationendpoint/*`)
   - ❌ Management Console (`/carbon/*`) - **NOT AFFECTED**

3. **Redirect Behavior**: When you access `/auth/carbon`, WSO2 IS:
   - Receives the request at `/carbon` (nginx strips `/auth`)
   - Generates a redirect to `/carbon/admin/index.jsp`
   - Doesn't prepend `/auth` because the console doesn't use `base_path`

### Architecture

```
Browser Request:
https://letsplaydarts.eu/auth/carbon
    │
    ├─→ Nginx receives: /auth/carbon
    │
    ├─→ Nginx proxies to: wso2is:9443/carbon
    │   (strips /auth prefix)
    │
    ├─→ WSO2 IS receives: /carbon
    │
    ├─→ WSO2 IS redirects to: /carbon/admin/index.jsp
    │   (doesn't add /auth because console ignores base_path)
    │
    └─→ Browser receives: https://letsplaydarts.eu/carbon/admin/index.jsp
        ❌ 404 Not Found (nginx doesn't route /carbon)
```

---

## Recommended Approach

**For now:** Use **Option 1** (direct port access) to configure the Service Provider

**Long term:** Consider **Option 3** (upgrade to WSO2 IS 6.x) for better reverse proxy support

---

## Service Provider Configuration Steps

Since you need to update the Service Provider callback URLs, use the direct port access:

1. **Access Console:**

   ```
   https://letsplaydarts.eu:9443/carbon
   ```

2. **Login:**
   - Username: `admin` <!-- pragma: allowlist secret -->
   - Password: `admin` <!-- pragma: allowlist secret -->

3. **Navigate to Service Providers:**

   ```
   Main → Identity → Service Providers → List
   ```

4. **Edit your application** and update callback URLs to:

   ```
   regexp=https://letsplaydarts\.eu(/callback|/)
   ```

5. **Save** and test login/logout flows

---

## Verification

After updating the Service Provider:

### Test Login

```bash
1. Go to: https://letsplaydarts.eu
2. Click "Login"
3. Should redirect to: https://letsplaydarts.eu/auth/oauth2/authorize
4. Authenticate
5. Should redirect back successfully
```

### Test Logout

```bash
1. While logged in, click "Logout"
2. Should redirect to: https://letsplaydarts.eu/auth/oidc/logout
3. Should redirect back to: https://letsplaydarts.eu/
4. ✅ No error message
```

---

## Files Reference

- **WSO2 IS Config:** `/data/dartserver-pythonapp/wso2is-config/deployment.toml`
- **Nginx Config:** `/data/dartserver-pythonapp/nginx/nginx.conf`
- **Docker Compose:** `/data/dartserver-pythonapp/docker-compose-wso2.yml`

---

## Summary

| Access Method                      | URL                                      | Status     |
| ---------------------------------- | ---------------------------------------- | ---------- |
| **OAuth2 Endpoints**               | `https://letsplaydarts.eu/auth/oauth2/*` | ✅ Working |
| **OIDC Endpoints**                 | `https://letsplaydarts.eu/auth/oidc/*`   | ✅ Working |
| **Management Console (via nginx)** | `https://letsplaydarts.eu/auth/carbon`   | ❌ Broken  |
| **Management Console (direct)**    | `https://letsplaydarts.eu:9443/carbon`   | ✅ Working |

**Bottom Line:** Use port 9443 to access the Management Console, or implement Option 2 (nginx rewrite rules).
