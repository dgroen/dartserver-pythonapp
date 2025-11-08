# Multi-Environment Quick Start

This document provides a quick reference for setting up and switching between production, development, and local environments.

## Files Added

### 1. New Configuration Module

- **File**: `src/config.py`
- **Purpose**: Centralized environment-aware configuration
- **Features**:
  - Auto-generates URLs from `APP_DOMAIN` and `APP_SCHEME`
  - Handles environment detection (production/development/staging)
  - Derives security settings from configuration
  - Provides helper methods

### 2. Documentation

- **File**: `docs/MULTI_ENVIRONMENT_SETUP.md`
  - Comprehensive guide with all configuration options
  - Troubleshooting section
  - Security best practices
  - Nginx configuration example

### 3. Example Environment Files

- **`.env.production.example`**: Production deployment template
- **`.env.development.example`**: Development deployment template
- **`.env.local.example`**: Local testing template

## Quick Setup

### For Production (<https://letsplaydarts.eu>)

1. Copy production template:

```bash
cp .env.production.example .env
```

2. Edit `.env` with your production values:

```env
ENVIRONMENT=production
APP_DOMAIN=letsplaydarts.eu
APP_SCHEME=https
WSO2_IS_URL=https://letsplaydarts.eu/auth
WSO2_CLIENT_ID=your_client_id
WSO2_CLIENT_SECRET=your_client_secret
DATABASE_URL=postgresql://user:pass@host/db  # pragma: allowlist secret
RABBITMQ_HOST=rabbitmq.host
SECRET_KEY=your_secure_key
```

3. Deploy and start the application

### For Development (<http://dev.letsplaydarts.eu>)

1. Copy development template:

```bash
cp .env.development.example .env
```

2. Edit `.env` with your development values:

```env
ENVIRONMENT=development
APP_DOMAIN=dev.letsplaydarts.eu
APP_SCHEME=http
FLASK_DEBUG=True
WSO2_IS_URL=https://dev-wso2:9443
WSO2_CLIENT_ID=dev_client_id
WSO2_CLIENT_SECRET=dev_client_secret
DATABASE_URL=postgresql://postgres:postgres@localhost:5432/dartsdb_dev  # pragma: allowlist secret
```

3. Run the application

### For Local Testing (<http://localhost:5000>)

1. Copy local template:

```bash
cp .env.local.example .env
```

2. Start services (if using Docker):

```bash
docker-compose up -d postgres rabbitmq
```

3. Run the application:

```bash
python app.py
```

or with Flask:

```bash
flask run
```

## Configuration Variables Summary

| Variable                | Production         | Development            | Local            | Purpose          |
| ----------------------- | ------------------ | ---------------------- | ---------------- | ---------------- |
| `ENVIRONMENT`           | `production`       | `development`          | `development`    | Environment name |
| `APP_DOMAIN`            | `letsplaydarts.eu` | `dev.letsplaydarts.eu` | `localhost:5000` | Public domain    |
| `APP_SCHEME`            | `https`            | `http`                 | `http`           | URL scheme       |
| `FLASK_DEBUG`           | `False`            | `True`                 | `True`           | Debug mode       |
| `FLASK_USE_SSL`         | `True`             | `False`                | `False`          | SSL in Flask     |
| `SESSION_COOKIE_SECURE` | `True`             | `False`                | `False`          | Secure cookies   |

## What Changed

### Files Modified

1. **auth.py**
   - Now imports `Config` class from `src.config`
   - Uses `Config.CALLBACK_URL` for default redirect URI
   - Enhanced redirect URI logging for debugging
   - Improved X-Forwarded-Proto/Host header handling

2. **app.py**
   - Now imports `Config` class from `src.config`
   - Uses `Config.SESSION_COOKIE_SECURE` for security settings
   - Sets `SWAGGER_HOST` from `Config.SWAGGER_HOST`
   - Logs configuration on startup for visibility

3. **.env**
   - Added `ENVIRONMENT`, `APP_DOMAIN`, `APP_SCHEME` variables
   - These auto-generate `CALLBACK_URL` and other URLs
   - Removed hardcoded redirect URIs (now auto-generated)

4. **.env.example**
   - Updated with new configuration structure
   - Added clear comments explaining each section
   - Shows all available options

### How It Works

```
User accesses app (browser request)
         ↓
App receives request with headers:
  - X-Forwarded-Proto (from nginx/proxy)
  - X-Forwarded-Host (from nginx/proxy)
  - Host (if direct connection)
         ↓
get_dynamic_redirect_uri() function:
  1. Try X-Forwarded-Proto header
  2. Fall back to request.scheme
  3. Try X-Forwarded-Host header
  4. Fall back to request.host
  5. Build: scheme://host/callback
         ↓
OAuth2 redirect to WSO2 with correct redirect_uri
         ↓
WSO2 returns to callback URL → Auth successful
```

## Docker Compose Example

```yaml
services:
  darts-app:
    build: .
    container_name: darts-app
    ports:
      - "5000:5000"
    environment:
      ENVIRONMENT: development
      APP_DOMAIN: dev.letsplaydarts.eu
      APP_SCHEME: http
      FLASK_DEBUG: "True"
      DATABASE_URL: postgresql://postgres:postgres@postgres:5432/dartsdb # pragma: allowlist secret
      RABBITMQ_HOST: rabbitmq
      # ... other variables
    depends_on:
      - postgres
      - rabbitmq
```

## Nginx Configuration

```nginx
server {
    listen 443 ssl http2;
    server_name dev.letsplaydarts.eu;

    ssl_certificate /path/to/cert.pem;
    ssl_certificate_key /path/to/key.pem;

    location / {
        proxy_pass http://localhost:5000;

        # Forward scheme and host for correct redirect URIs
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_set_header X-Forwarded-Host $server_name;
        proxy_set_header X-Forwarded-For $remote_addr;

        # WebSocket support
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
    }
}
```

## Testing Your Configuration

### Check Environment Loading

```bash
# View current configuration
grep "ENVIRONMENT\|APP_DOMAIN\|APP_SCHEME" .env

# Output should show your environment settings
ENVIRONMENT=production
APP_DOMAIN=letsplaydarts.eu
APP_SCHEME=https
```

### Check Application Logs

When the app starts, it logs:

```
INFO:root:Application Configuration: Config(environment=production, domain=letsplaydarts.eu, scheme=https)
INFO:root:Environment: production
INFO:root:App URL: https://letsplaydarts.eu
INFO:root:Callback URL: https://letsplaydarts.eu/callback
INFO:root:Session Cookie Secure: True
```

### Test OAuth2 Callback

```bash
# Check if auth endpoint returns correct redirect_uri
curl -X GET "http://localhost:5000/api/auth/authorize" -v

# Look for redirect_uri parameter in the WSO2 redirect URL
# Should match your APP_DOMAIN and APP_SCHEME
```

## Security Checklist

- [ ] Production uses HTTPS (`APP_SCHEME=https`)
- [ ] Production has `SESSION_COOKIE_SECURE=True`
- [ ] Development uses different credentials than production
- [ ] All `SECRET_KEY` values are strong and unique
- [ ] Never commit `.env` file to version control
- [ ] Register redirect URIs in WSO2 for each environment
- [ ] Database passwords are strong and different per environment

## Troubleshooting

### "redirect_uri mismatch" error from WSO2

**Solution:**

1. Verify `APP_DOMAIN` matches your actual domain
2. Check `APP_SCHEME` matches what users access (http/https)
3. Ensure redirect URI is registered in WSO2:
   - `{APP_SCHEME}://{APP_DOMAIN}/callback`
4. Check nginx is forwarding `X-Forwarded-*` headers

### Cookies not persisting

**Solution:**

1. Check `SESSION_COOKIE_SECURE` setting
2. For http: must be `false`
3. For https: should be `true`
4. Browser won't accept secure cookies over http

### Different behavior between environments

**Solution:**

1. Check `.env` file is correct
2. Restart the application after changing `.env`
3. Look at logs for actual config being used
4. Verify environment-specific services (WSO2, DB) are accessible

## Related Documentation

- [Multi-Environment Setup (Detailed)](./MULTI_ENVIRONMENT_SETUP.md)
- [Authentication Flow](./AUTHENTICATION_FLOW.md)
- [WSO2 Configuration](./WSO2_SETUP_GUIDE.md)
- [SSL Configuration](./SSL_CONFIGURATION.md)
