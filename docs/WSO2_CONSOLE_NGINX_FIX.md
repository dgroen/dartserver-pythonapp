# WSO2 IS Console Nginx Reverse Proxy Fix

## Problem

The WSO2 Identity Server console (accessible at `https://test.letsplaydarts.eu/t/carbon.super/console`) was experiencing redirect loops or failures when accessed through the Nginx reverse proxy.

### Root Causes

1. **Blanket /t/ redirect**: The original configuration redirected ALL `/t/` paths to `/auth/t/`, including the console path `/t/carbon.super/console`, causing an endless redirect loop.

2. **OAuth callback mismatch**: After authentication, the console was redirecting to `/console` instead of `/t/carbon.super/console`, causing the console to not load after login.

3. **Console static resources not loading**: The console loads JavaScript files like `startup-config.js` and `auth-spa-3.1.2.min.js` from `/console/*` paths. These were being redirected instead of proxied, causing a `startupConfig is not defined` error.

4. **Missing console-specific endpoints**: The console requires several API endpoints that weren't properly proxied:
   - `/api/identity/` - Identity management APIs
   - `/api/users/` - User management APIs
   - `/o/` - Organization management APIs
   - Tenant-specific paths like `/t/{tenant}/api/`

5. **Missing proxy redirect handling**: Console requests were being redirected by WSO2 IS internally, which needed to be disabled with `proxy_redirect off`.

6. **Incorrect proxy_context_path**: The `deployment.toml` had `proxy_context_path = "/console"` which was telling WSO2 that the console was at `/console` when it's actually at the tenant-specific path.

## Solution

The fix involves five key changes:

### 1. Fixed OAuth Callback Redirect AND Static Resource Proxying (Critical Fix)

The console's OAuth flow was redirecting to `/console` after authentication, but the actual console is at `/t/carbon.super/console`. We added a redirect for the exact path and proxying for console resources:

```nginx
# Redirect /console to tenant-specific console path (OAuth callback)
location = /console {
    return 302 https://$host/t/carbon.super/console;
}

# Proxy console static resources (JS, CSS, etc) to WSO2 IS
location /console/ {
    proxy_pass https://wso2_is/console/;
    proxy_set_header Host $host;
    proxy_set_header X-Real-IP $remote_addr;
    proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
    proxy_set_header X-Forwarded-Proto https;
    proxy_set_header X-Forwarded-Host $host;
    proxy_ssl_verify off;

    # Cache static resources
    proxy_cache_valid 200 1h;
    add_header X-Cache-Status $upstream_cache_status;
}
```

**Why this works:**

- `location = /console` (exact match) handles the OAuth callback redirect
- `location /console/` (prefix match) proxies all console static resources (startup-config.js, auth-spa-3.1.2.min.js, CSS, etc.) to WSO2 IS
- Without the proxying, resources would get 302 redirects creating broken paths like `/t/carbon.super/console/console/startup-config.js`

### 2. Added Console-Specific Location Blocks

Created regex location blocks that handle console paths BEFORE the general `/t/` redirect:

```nginx
# WSO2 Console - handle /t/carbon.super/console and tenant console paths
location ~ ^/t/[^/]+/console {
    proxy_pass https://wso2_is;
    proxy_set_header Host $host;
    proxy_set_header X-Real-IP $remote_addr;
    proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
    proxy_set_header X-Forwarded-Proto https;
    proxy_set_header X-Forwarded-Host $host;
    proxy_ssl_verify off;
    proxy_redirect off;

    # Handle console static resources
    proxy_http_version 1.1;
    proxy_set_header Upgrade $http_upgrade;
    proxy_set_header Connection "upgrade";
}

# WSO2 Console API endpoints - for tenant-specific API calls
location ~ ^/t/[^/]+/api/ {
    proxy_pass https://wso2_is;
    proxy_set_header Host $host;
    proxy_set_header X-Real-IP $remote_addr;
    proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
    proxy_set_header X-Forwarded-Proto https;
    proxy_set_header X-Forwarded-Host $host;
    proxy_ssl_verify off;
}
```

**Key points:**

- Uses regex `^/t/[^/]+/console` to match any tenant's console path
- Placed BEFORE the general `/t/` redirect location
- `proxy_redirect off` prevents WSO2's internal redirects from breaking
- WebSocket support for live updates in the console

### 3. Added Required API Endpoints

Added proxying for console-related APIs:

```nginx
# API identity endpoints for console
location /api/identity/ {
    proxy_pass https://wso2_is/api/identity/;
    # ... headers ...
}

# API users endpoints for console user management
location /api/users/ {
    proxy_pass https://wso2_is/api/users/;
    # ... headers ...
}

# Organization management endpoints
location /o/ {
    proxy_pass https://wso2_is/o/;
    # ... headers ...
}
```

### 4. Fixed WSO2 IS deployment.toml

Removed the incorrect `proxy_context_path` setting and added proper console configuration:

```toml
# Before (WRONG):
[tomcat.management_console]
proxy_context_path = "/console"

# After (CORRECT):
[console]
idle_session_timeout = "15"
remember_me_timeout = "20160"
disable_new_console = false
```

**Why this matters:** The `proxy_context_path = "/console"` was telling WSO2 IS that the console was accessible at `/console`, which conflicted with the actual tenant-specific path `/t/carbon.super/console`. Removing this allows WSO2 to use its default tenant-based console paths.

### 5. Maintained General /t/ Redirect for Non-Console Paths

The general `/t/` redirect remains at the end for other tenant paths:

```nginx
# Redirect other /t/ paths to /auth/t/ (but not console or api paths)
location /t/ {
    return 301 https://$host/auth$request_uri;
}
```

**Why this works:** Nginx processes location blocks in order of specificity. Regex locations (`~`) are processed before prefix locations, so the console paths are matched first, and only non-console `/t/` paths fall through to the redirect.

## Nginx Location Matching Order

Understanding Nginx's location matching priority is crucial:

1. **Exact match** (`= /path`)
2. **Regex match** (`~ ^/pattern` or `~* ^/pattern`)
3. **Longest prefix match** (`/path/`)

In our fix:

- `location ~ ^/t/[^/]+/console` (regex) is evaluated BEFORE
- `location /t/` (prefix)

This ensures console paths are proxied directly to WSO2 IS while other `/t/` paths are redirected to `/auth/t/`.

## Testing the Fix

### 1. Restart Services

Both Nginx and WSO2 IS need to be restarted:

```bash
# Restart Nginx:
docker-compose -f docker-compose-wso2.yml restart nginx

# Restart WSO2 IS (required for deployment.toml changes):
docker-compose -f docker-compose-wso2.yml restart wso2is

# Wait for WSO2 IS to fully start (takes 1-2 minutes)
docker logs darts-wso2is -f
```

### 2. Access the Console

Navigate to: `https://test.letsplaydarts.eu/t/carbon.super/console`

**Expected Flow:**

1. You'll be redirected to the login page at `/authenticationendpoint/login.do`
2. Enter credentials (username: `admin`, password: `admin`)
3. After authentication, you'll be redirected to `/console`
4. Nginx will automatically redirect you to `/t/carbon.super/console`
5. The console should now load successfully with all features working

### 3. Verify Login Flow

1. Log in with admin credentials (username: `admin`, password: `admin`)
2. The console should load with all UI elements properly
3. Check browser dev tools Network tab - all requests to `/api/identity/`, `/api/users/`, etc. should return 200 OK
4. No redirect loops (watch for excessive 301/302 responses)

### 4. Debug if Issues Persist

Check Nginx logs:

```bash
docker logs darts-nginx -f
```

Check WSO2 IS logs:

```bash
docker logs darts-wso2is -f | grep -i console
```

## Related Configuration

### WSO2 IS deployment.toml

The WSO2 IS configuration no longer includes the problematic `proxy_context_path`:

```toml
[server]
hostname = "test.letsplaydarts.eu"
base_path = "https://test.letsplaydarts.eu/auth"

[console]
idle_session_timeout = "15"
remember_me_timeout = "20160"
disable_new_console = false
```

**Important:** The `base_path` is set to `/auth` for the main WSO2 IS endpoints, but the console uses its own tenant-specific path structure `/t/carbon.super/console`. The console configuration is separate and doesn't need a proxy_context_path since it uses the standard tenant paths.

## Maintenance Notes

### When Adding New WSO2 Features

If you add new WSO2 IS features that use tenant-specific paths (`/t/{tenant}/...`), remember to:

1. Check if they need direct proxying (like the console)
2. If yes, add a regex location block BEFORE the general `/t/` redirect
3. Test both the super tenant (`carbon.super`) and any custom tenants

### Console Static Resources

The console serves static assets (JS, CSS, images) from paths like:

- `/console/libs/`
- `/console/themes/`
- `/t/{tenant}/console/resources/`

The current configuration handles these via the main console location block with trailing slash handling.

## Security Considerations

1. **SSL Verification**: `proxy_ssl_verify off` is used because WSO2 IS uses self-signed certificates in the Docker network. In production with proper certificates, consider enabling this.

2. **Headers**: All console proxies include proper `X-Forwarded-*` headers to ensure WSO2 IS can:
   - Generate correct redirect URLs
   - Validate request origins
   - Apply security policies

3. **Rate Limiting**: Consider adding rate limiting to console endpoints if public access is enabled:

   ```nginx
   limit_req_zone $binary_remote_addr zone=console_limit:10m rate=10r/m;

   location ~ ^/t/[^/]+/console {
       limit_req zone=console_limit burst=5 nodelay;
       # ... rest of config ...
   }
   ```

## Troubleshooting

### Console Redirects to /console and Stops

**Symptom:** After login, you're redirected to `https://test.letsplaydarts.eu/console` and nothing happens.

**Solution:** This was the main issue we fixed. Ensure:

1. The Nginx `/console` location redirects to `/t/carbon.super/console`
2. Both Nginx AND WSO2 IS have been restarted
3. Clear your browser cache and cookies for the domain

### Still Getting Redirect Loops

1. Clear browser cache and cookies for `test.letsplaydarts.eu`
2. Check WSO2 IS `deployment.toml` - ensure `hostname` and `base_path` are correct
3. Verify the console location blocks are BEFORE the general `/t/` redirect in nginx.conf
4. Check for any custom WSO2 IS configuration that might override proxy behavior

### Console Loads But Features Don't Work

1. Check browser console for CORS errors
2. Verify all API endpoints (`/api/identity/`, `/api/users/`, `/o/`, etc.) are proxied
3. Check WSO2 IS CORS configuration in `deployment.toml`
4. Ensure `X-Forwarded-Proto` is set to `https` for all console-related proxies

### Static Resources (CSS/JS) Not Loading

1. Check if paths start with `/console/` or `/t/{tenant}/console/`
2. Verify the console location block handles trailing slashes properly
3. Check Content-Type headers in responses - ensure they're not being stripped

## References

- WSO2 IS 7.x Console Documentation: <https://is.docs.wso2.com/en/latest/guides/console/>
- Nginx Proxy Module: <http://nginx.org/en/docs/http/ngx_http_proxy_module.html>
- Nginx Location Directive: <http://nginx.org/en/docs/http/ngx_http_core_module.html#location>
