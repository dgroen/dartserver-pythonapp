# Multi-Environment Configuration Guide

This guide explains how to configure the Darts Game Server for both production and development environments using only the `.env` file.

## Overview

The application supports multiple environments with different configurations:
- **Production**: `https://letsplaydarts.eu`
- **Development**: `http://dev.letsplaydarts.eu`
- **Local**: `http://localhost:5000`

## Quick Start

### For Production (default)

The production configuration is already set in `.env`. No changes needed if you're using `https://letsplaydarts.eu`:

```env
ENVIRONMENT=production
APP_DOMAIN=letsplaydarts.eu
APP_SCHEME=https
```

### For Development

To switch to development environment, update your `.env` file:

```env
ENVIRONMENT=development
APP_DOMAIN=dev.letsplaydarts.eu
APP_SCHEME=http
FLASK_DEBUG=True
```

### For Local Development

For local testing without a reverse proxy:

```env
ENVIRONMENT=development
APP_DOMAIN=localhost:5000
APP_SCHEME=http
FLASK_DEBUG=True
SESSION_COOKIE_SECURE=False
```

## Configuration Variables

### Required Environment Variables

#### `ENVIRONMENT` (required)
- **Purpose**: Defines which environment the app is running in
- **Valid values**: `production`, `development`, `staging`
- **Default**: `production`
- **Usage**: Affects logging, debug mode, and security settings

**Examples:**
```env
ENVIRONMENT=production    # Production deployment
ENVIRONMENT=development   # Development/testing
ENVIRONMENT=staging       # Staging environment
```

#### `APP_DOMAIN` (required)
- **Purpose**: The public domain/hostname where your app is accessible
- **Format**: Domain name with optional port (no scheme)
- **Default**: `localhost:5000`
- **Note**: Should NOT include `http://` or `https://` prefix

**Examples:**
```env
APP_DOMAIN=letsplaydarts.eu           # Production
APP_DOMAIN=dev.letsplaydarts.eu       # Development
APP_DOMAIN=localhost:5000             # Local testing
APP_DOMAIN=192.168.1.100:5000        # Local network
```

#### `APP_SCHEME` (required)
- **Purpose**: URL scheme used for all redirects and callbacks
- **Valid values**: `http` or `https`
- **Default**: `https`
- **Note**: Must match what users access in their browser

**Examples:**
```env
APP_SCHEME=https   # Production (required for security)
APP_SCHEME=http    # Development/Local testing only
```

### Derived Configuration

These URLs are **automatically generated** from `APP_DOMAIN` and `APP_SCHEME`. You should NOT set them manually:

| Variable | Example | Auto-generated from |
|----------|---------|-------------------|
| `APP_URL` | `https://letsplaydarts.eu` | `APP_SCHEME://APP_DOMAIN` |
| `CALLBACK_URL` | `https://letsplaydarts.eu/callback` | `APP_URL/callback` |
| `LOGOUT_REDIRECT_URL` | `https://letsplaydarts.eu/` | `APP_URL/` |
| `SWAGGER_HOST` | `letsplaydarts.eu` | `APP_DOMAIN` (if not overridden) |

These are used for:
- OAuth2 redirect URIs in WSO2 configuration
- Session cookie security settings
- API documentation

### Optional Variables

#### `SWAGGER_HOST` (optional)
- **Purpose**: Override the Swagger API documentation host
- **Default**: Same as `APP_DOMAIN`
- **Use case**: Rarely needed, only if serving docs from different domain

```env
SWAGGER_HOST=api.letsplaydarts.eu
```

#### `SESSION_COOKIE_SECURE` (optional)
- **Purpose**: Controls HTTP-only cookie security
- **Valid values**: `true` or `false`
- **Default**: Auto-detected from `APP_SCHEME` (true if https, false if http)
- **Note**: Usually you don't need to set this

```env
SESSION_COOKIE_SECURE=true   # Force secure cookies
SESSION_COOKIE_SECURE=false  # Allow non-secure cookies
```

#### `FLASK_DEBUG` (optional)
- **Purpose**: Enable Flask debug mode
- **Valid values**: `True` or `False`
- **Default**: `False`
- **Warning**: Never enable in production

```env
FLASK_DEBUG=False   # Production
FLASK_DEBUG=True    # Development only
```

#### `FLASK_USE_SSL` (optional)
- **Purpose**: Configure Flask to use SSL
- **Valid values**: `True` or `False`
- **Default**: `true`
- **Note**: Typically handled by reverse proxy (nginx), not needed if behind proxy

```env
FLASK_USE_SSL=False  # When behind nginx with reverse proxy
```

## Complete Environment Files

### Production `.env`

```env
ENVIRONMENT=production
APP_DOMAIN=letsplaydarts.eu
APP_SCHEME=https
FLASK_DEBUG=False
FLASK_USE_SSL=True

# Database (production)
DATABASE_URL=postgresql://user:password@prod-db-host:5432/dartsdb
RABBITMQ_HOST=prod-rabbitmq-host
RABBITMQ_PORT=5672
RABBITMQ_USER=<production_user>
RABBITMQ_PASSWORD=<production_password>

# WSO2 Production Configuration
WSO2_IS_URL=https://letsplaydarts.eu/auth
WSO2_CLIENT_ID=<your_production_client_id>
WSO2_CLIENT_SECRET=<your_production_client_secret>
WSO2_IS_VERIFY_SSL=True

# Security
SECRET_KEY=<your_production_secret_key>
```

### Development `.env`

```env
ENVIRONMENT=development
APP_DOMAIN=dev.letsplaydarts.eu
APP_SCHEME=http
FLASK_DEBUG=True
FLASK_USE_SSL=False
SESSION_COOKIE_SECURE=False

# Database (development)
DATABASE_URL=postgresql://postgres:postgres@localhost:5432/dartsdb_dev
RABBITMQ_HOST=localhost
RABBITMQ_PORT=5672
RABBITMQ_USER=guest
RABBITMQ_PASSWORD=guest

# WSO2 Development Configuration
WSO2_IS_URL=https://dev-wso2:9443
#WSO2_IS_INTERNAL_URL=https://wso2is:9443
WSO2_CLIENT_ID=<your_dev_client_id>
WSO2_CLIENT_SECRET=<your_dev_client_secret>
WSO2_IS_VERIFY_SSL=False

# Security
SECRET_KEY=dev-secret-key-only-for-testing
```

### Local Testing `.env`

```env
ENVIRONMENT=development
APP_DOMAIN=localhost:5000
APP_SCHEME=http
FLASK_DEBUG=True
FLASK_USE_SSL=False
SESSION_COOKIE_SECURE=False

# Local services
DATABASE_URL=postgresql://postgres:postgres@localhost:5432/dartsdb
RABBITMQ_HOST=localhost
RABBITMQ_PORT=5672
RABBITMQ_USER=guest
RABBITMQ_PASSWORD=guest

# Local WSO2 (if running)
WSO2_IS_URL=https://localhost:9443
WSO2_CLIENT_ID=local_client_id
WSO2_CLIENT_SECRET=local_client_secret
WSO2_IS_VERIFY_SSL=False

# Development
SECRET_KEY=local-dev-secret-key
AUTH_DISABLED=False  # Set to true to skip auth for testing
```

## How It Works

### Configuration Priority

The application uses this priority order when determining URLs:

1. **Request Headers** (if behind reverse proxy)
   - `X-Forwarded-Proto` header (https or http)
   - `X-Forwarded-Host` header (domain)

2. **Request Properties** (direct connection)
   - `request.scheme` (http or https)
   - `request.host` (domain and port)

3. **Configured Defaults** (fallback)
   - `APP_SCHEME://APP_DOMAIN` from `.env`

This allows the application to work correctly behind:
- Nginx reverse proxy
- Load balancers
- Direct connections

### Code Changes

The following files were updated to support multi-environment configuration:

1. **`src/config.py`** (new)
   - Centralized configuration management
   - Derives URLs from `APP_DOMAIN` and `APP_SCHEME`

2. **`auth.py`**
   - Uses `Config.CALLBACK_URL` as default redirect URI
   - Supports dynamic redirect generation from request headers

3. **`app.py`**
   - Imports `Config` class
   - Uses `Config.SESSION_COOKIE_SECURE` for security settings
   - Sets `SWAGGER_HOST` from `Config.SWAGGER_HOST`
   - Logs configuration on startup

## Testing Your Configuration

### Verify Environment Loading

```bash
# Check if your .env is being read
grep -E "^ENVIRONMENT|^APP_DOMAIN|^APP_SCHEME" .env
```

### Check Application Logs

When the app starts, it logs the configuration:

```
INFO:root:Application Configuration: Config(environment=production, domain=letsplaydarts.eu, scheme=https)
INFO:root:Environment: production
INFO:root:App URL: https://letsplaydarts.eu
INFO:root:Callback URL: https://letsplaydarts.eu/callback
INFO:root:Session Cookie Secure: True
```

### Test OAuth2 Redirect

Visit your application and check if the OAuth2 redirect URI is correct:

1. Open browser DevTools (F12)
2. Go to Network tab
3. Click login/auth button
4. Look for the redirect to WSO2
5. Verify the `redirect_uri` parameter matches your configuration

### Test with cURL

```bash
# Test callback URL generation
curl -v http://localhost:5000/callback
# Should show the correct redirect in Location header
```

## Nginx Configuration Example

When running behind Nginx, ensure these headers are forwarded:

```nginx
location / {
    proxy_pass http://localhost:5000;
    
    # Forward the original request scheme and host
    proxy_set_header X-Forwarded-Proto $scheme;
    proxy_set_header X-Forwarded-Host $server_name;
    proxy_set_header X-Forwarded-For $remote_addr;
    proxy_set_header X-Forwarded-Prefix /;
}
```

## Docker Compose Configuration

```yaml
services:
  darts-app:
    build: .
    environment:
      ENVIRONMENT: development
      APP_DOMAIN: dev.letsplaydarts.eu
      APP_SCHEME: http
      FLASK_DEBUG: "True"
      FLASK_USE_SSL: "False"
      # ... other environment variables
```

## Troubleshooting

### Issue: Redirect URI mismatch in OAuth2

**Symptom**: Error like "redirect_uri mismatch" from WSO2

**Solution**:
1. Check your `.env` file has correct `APP_DOMAIN` and `APP_SCHEME`
2. Verify the derived `CALLBACK_URL` is registered in WSO2
3. Check nginx headers are being forwarded correctly
4. Look at app logs for the actual redirect URI being used

```bash
# View logs for redirect URI
docker logs darts-app | grep -i "redirect"
```

### Issue: Session cookies not working

**Symptom**: Login doesn't persist between requests

**Solution**:
1. Check `SESSION_COOKIE_SECURE` matches your `APP_SCHEME`
2. For http: `SESSION_COOKIE_SECURE=False`
3. For https: `SESSION_COOKIE_SECURE=True`
4. Browser won't accept secure cookies over http

### Issue: Cannot reach app from different domain

**Symptom**: App accessible but login redirects fail

**Solution**:
1. Ensure `APP_DOMAIN` includes the domain you're accessing
2. Register the redirect URI in WSO2 admin console
3. If behind reverse proxy, check `X-Forwarded-*` headers are set

## Security Notes

### Production Best Practices

✅ **DO:**
- Use `ENVIRONMENT=production`
- Set `APP_SCHEME=https`
- Use strong `SECRET_KEY`
- Set `FLASK_DEBUG=False`
- Enable `WSO2_IS_VERIFY_SSL=True`
- Use environment-specific credentials

❌ **DON'T:**
- Expose `.env` file in version control
- Use `FLASK_DEBUG=True` in production
- Use `AUTH_DISABLED=True` in production
- Use `http://` in production
- Reuse development credentials

### Development Best Practices

For local development, it's acceptable to:
- Use `ENVIRONMENT=development`
- Use `APP_SCHEME=http` for localhost
- Set `FLASK_DEBUG=True`
- Set `SESSION_COOKIE_SECURE=False`
- Use `AUTH_DISABLED=False` (real auth testing)

## Related Documentation

- [WSO2 Configuration Guide](./AUTHENTICATION_SETUP.md)
- [Deployment Checklist](./DEPLOYMENT_CHECKLIST.md)
- [SSL Configuration](./SSL_CONFIGURATION.md)
- [Authentication Flow](./AUTHENTICATION_FLOW.md)

## Support

For issues or questions about multi-environment configuration:

1. Check the logs: `docker logs darts-app`
2. Review this guide's troubleshooting section
3. Check `.env` file syntax and values
4. Ensure all required variables are set