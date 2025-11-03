# Fix for WSO2 IS Redirect Issues Behind Nginx Reverse Proxy

## Problems

1. **Port 9443 Redirect**: Users were being redirected to port 9443 instead of using the standard HTTPS port 443
2. **Missing /auth Prefix**: Authentication endpoints were missing the `/auth` prefix, causing 404 errors

## Root Causes

1. WSO2 Identity Server was not configured to recognize that it's behind a reverse proxy
2. Authentication endpoint URLs were using relative paths instead of absolute URLs with the `/auth` prefix

## Solutions Applied

### Fix 1: Proxy Port Configuration

Added proxy port configuration to `/data/dartserver-pythonapp/wso2is-config/deployment.toml`:

```toml
[transport.https.properties]
proxyPort = 443
```

This tells WSO2 IS to use port 443 in all generated URLs instead of the internal port 9443.

### Fix 2: Authentication Endpoint URLs

Updated authentication endpoint URLs to use absolute paths with the `/auth` prefix:

```toml
[authentication.endpoints]
login_url = "${carbon.protocol}://letsplaydarts.eu/auth/authenticationendpoint/login.do"
retry_url = "${carbon.protocol}://letsplaydarts.eu/auth/authenticationendpoint/retry.do"
```

This ensures all authentication endpoints include the `/auth` prefix required by the nginx reverse proxy configuration.

## Steps to Apply the Fix

### Option 1: Restart only WSO2 IS container (Recommended)

```bash
cd /data/dartserver-pythonapp
docker-compose -f docker-compose-wso2.yml restart wso2is
```

Wait for WSO2 IS to fully start (about 2-3 minutes). You can check the logs:

```bash
docker logs -f darts-wso2is
```

### Option 2: Restart all services

```bash
cd /data/dartserver-pythonapp
docker-compose -f docker-compose-wso2.yml down
docker-compose -f docker-compose-wso2.yml up -d
```

## Verification

1. Navigate to <https://letsplaydarts.eu>
2. Click the login button
3. Verify that the URL stays on `https://letsplaydarts.eu/auth/...` without showing port 9443
4. Complete the login flow

## Additional Notes

- The configuration file is mounted as a volume, so changes persist across container restarts
- No changes to the application code were needed
- The nginx reverse proxy configuration was already correct
- The `.env` file configuration was already correct

## Related Configuration Files

- `/data/dartserver-pythonapp/wso2is-config/deployment.toml` - WSO2 IS configuration (MODIFIED)
- `/data/dartserver-pythonapp/nginx/nginx.conf` - Nginx reverse proxy config (no changes needed)
- `/data/dartserver-pythonapp/.env` - Application environment variables (no changes needed)
