# WSO2 IS Redirect URI Configuration Fix

## Problem

The login redirect from WSO2 IS was redirecting to `localhost` instead of `letsplaydarts.eu` with the proper SSL port handled by the reverse proxy.

## Root Causes

1. **Missing X-Forwarded-Host header in nginx**: Flask's ProxyFix middleware needs this header to understand the external domain
2. **Hardcoded localhost redirect URIs**: Docker-compose had fallback redirect URIs pointing to localhost
3. **WSO2 IS configuration not mounted**: The deployment.toml file was not being mounted into the container
4. **WSO2 IS OAuth application configuration**: The OAuth application in WSO2 IS needs to have the correct redirect URIs registered

## Changes Made

### 1. Nginx Configuration (`nginx/nginx.conf`)

Added `X-Forwarded-Host` header to both the main application and WSO2 IS proxy locations:

```nginx
# Darts Application Routes
location / {
    proxy_pass http://darts_app;
    proxy_set_header Host $host;
    proxy_set_header X-Real-IP $remote_addr;
    proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
    proxy_set_header X-Forwarded-Proto https;  # Force HTTPS for OAuth redirects
    proxy_set_header X-Forwarded-Host $host;   # Pass the external host for dynamic redirects
    ...
}

# WSO2 Identity Server Routes
location /auth/ {
    ...
    proxy_set_header X-Forwarded-Proto https;  # Force HTTPS for OAuth redirects
    proxy_set_header X-Forwarded-Host $host;   # Pass the external host
    ...
}
```

### 2. Docker Compose Configuration (`docker-compose-wso2.yml`)

- Changed default redirect URIs from `http://localhost:5000/callback` to `https://letsplaydarts.eu/callback`
- Changed post-logout redirect URI from `http://localhost:5000/` to `https://letsplaydarts.eu/`
- Enabled secure cookies: `SESSION_COOKIE_SECURE: "True"`
- Uncommented the deployment.toml volume mount for WSO2 IS

### 3. WSO2 IS Configuration (`wso2is-config/deployment.toml`)

The configuration file is already correct with:

- `hostname = "letsplaydarts.eu"`
- `base_path = "https://letsplaydarts.eu/auth"`
- OAuth endpoints configured with `letsplaydarts.eu/auth` paths

## Additional Steps Required

### Configure OAuth Application in WSO2 IS

You need to configure the OAuth application in WSO2 IS to accept redirect URIs from `letsplaydarts.eu`:

1. **Access WSO2 IS Admin Console**:
   - URL: `https://letsplaydarts.eu/auth/carbon`
   - Username: `admin`
   - Password: `admin` <!-- pragma: allowlist secret -->

2. **Navigate to Service Providers**:
   - Main Menu → Identity → Service Providers → List
   - Find your application (or create a new one)

3. **Configure Inbound Authentication**:
   - Expand "Inbound Authentication Configuration"
   - Click "OAuth/OpenID Connect Configuration"
   - Click "Edit" or "Configure"

4. **Update Callback URLs**:
   Add the following callback URLs (use regex pattern for flexibility):

   ```
   regexp=https://letsplaydarts\.eu/callback
   ```

   Or add specific URLs:

   ```
   https://letsplaydarts.eu/callback
   ```

5. **Configure Allowed Grant Types**:
   - Authorization Code
   - Refresh Token

6. **Save the Configuration**

7. **Note the Client ID and Secret**:
   - Copy the OAuth Client Key (Client ID)
   - Copy the OAuth Client Secret
   - Update your `.env` file or docker-compose environment variables:

     ```
     WSO2_CLIENT_ID=<your_client_id>
     WSO2_CLIENT_SECRET=<your_client_secret>
     ```

## How It Works

1. **User accesses**: `https://letsplaydarts.eu/login`
2. **Nginx receives request** and forwards to Flask app with headers:
   - `X-Forwarded-Proto: https`
   - `X-Forwarded-Host: letsplaydarts.eu`
3. **Flask ProxyFix middleware** processes these headers and updates `request.scheme` and `request.host`
4. **Dynamic redirect URI function** (`get_dynamic_redirect_uri()`) builds: `https://letsplaydarts.eu/callback`
5. **Authorization URL** is generated with the correct redirect URI
6. **User is redirected to WSO2 IS**: `https://letsplaydarts.eu/auth/oauth2/authorize?...&redirect_uri=https://letsplaydarts.eu/callback`
7. **After authentication**, WSO2 IS redirects back to: `https://letsplaydarts.eu/callback?code=...`
8. **Flask receives callback** and exchanges code for token using the same dynamic redirect URI

## Testing

1. **Restart the services**:

   ```bash
   docker-compose -f docker-compose-wso2.yml down
   docker-compose -f docker-compose-wso2.yml up -d
   ```

2. **Check logs** for the dynamic redirect URI:

   ```bash
   docker logs darts-app | grep "Dynamic redirect URI"
   ```

3. **Test the login flow**:
   - Navigate to `https://letsplaydarts.eu/login`
   - Check the browser's network tab to see the redirect URI in the authorization request
   - Complete the login
   - Verify you're redirected back to `https://letsplaydarts.eu/callback`

## Troubleshooting

### Still redirecting to localhost?

1. **Check nginx is running and configured correctly**:

   ```bash
   docker exec darts-nginx nginx -t
   docker logs darts-nginx
   ```

2. **Check Flask is receiving the correct headers**:

   ```bash
   docker logs darts-app | grep "Request headers"
   ```

3. **Verify ProxyFix is enabled** in `app.py`:

   ```python
   app.wsgi_app = ProxyFix(
       app.wsgi_app,
       x_for=1,
       x_proto=1,
       x_host=1,
       x_prefix=1
   )
   ```

### WSO2 IS returns "invalid redirect_uri" error?

1. **Check the OAuth application configuration** in WSO2 IS
2. **Verify the callback URL** is registered exactly as: `https://letsplaydarts.eu/callback`
3. **Check WSO2 IS logs**:

   ```bash
   docker logs darts-wso2is | grep -i redirect
   ```

### Session issues after login?

1. **Verify secure cookies are enabled** when using HTTPS
2. **Check cookie domain settings** in Flask configuration
3. **Ensure session secret key** is set and consistent across restarts

## Environment Variables Reference

```bash
# Public URL for browser redirects
WSO2_IS_URL=https://letsplaydarts.eu/auth

# Internal URL for backend API calls
WSO2_IS_INTERNAL_URL=https://wso2is:9443

# OAuth credentials
WSO2_CLIENT_ID=your_client_id_here
WSO2_CLIENT_SECRET=your_client_secret_here

# Fallback redirect URIs (app will use dynamic URIs based on X-Forwarded headers)
WSO2_REDIRECT_URI=https://letsplaydarts.eu/callback
WSO2_POST_LOGOUT_REDIRECT_URI=https://letsplaydarts.eu/

# Security settings
WSO2_IS_VERIFY_SSL=False  # Set to True in production with valid certificates
SESSION_COOKIE_SECURE=True  # Required for HTTPS
```
