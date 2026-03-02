# Configuration Repository Requirements

This document outlines the required environment variables that must be configured in the `dartserver-config` repository for each deployment environment.

## Overview

The deployment pipeline pulls environment-specific configuration from the private `dartserver-config` repository. Configuration files are stored in:
- `environments/test/.env` - Test environment
- `environments/production/.env` - Production environment

## Required Environment Variables

### WSO2 Identity Server Configuration

#### WSO2_IS_CLIENT_ID
- **Description**: OAuth2 client ID for the API Gateway service
- **Default**: `darts_api_gateway`
- **Required**: Yes
- **Example**: `darts_api_gateway`

#### WSO2_IS_CLIENT_SECRET
- **Description**: OAuth2 client secret for the API Gateway service
- **Required**: Yes
- **Security**: Store securely in encrypted config repository
- **Example**: `darts_api_gateway_secret`

#### WSO2_IS_INTROSPECT_USER
- **Description**: Admin username for token introspection API calls
- **Default**: `admin`
- **Required**: Yes
- **Example**: `admin`

#### WSO2_IS_INTROSPECT_PASSWORD
- **Description**: Admin password for token introspection API calls
- **Required**: Yes
- **Security**: Store securely in encrypted config repository
- **Example**: `admin`

#### WSO2_IS_DEFAULT_SCOPES
- **Description**: Default OAuth2 scopes to apply when WSO2 token introspection omits the scope field
- **Required**: Yes (as of PR #182)
- **Format**: Space-separated or comma-separated list of scopes
- **Default**: `"dartboard:write dartboard:read game:write game:control score:write player:write"`
- **Purpose**: 
  - Fallback when WSO2 introspection returns tokens without scope field
  - Only applied when `client_id` matches `WSO2_IS_CLIENT_ID`
  - Enables scope-based authorization even when introspection omits scopes
- **Example**: 
  ```dotenv
  WSO2_IS_DEFAULT_SCOPES="dartboard:write dartboard:read game:write game:control score:write player:write"
  ```

### Application Configuration

#### SECRET_KEY
- **Description**: Flask session encryption secret key
- **Required**: Yes
- **Security**: Generate unique cryptographically random value per environment
- **Example**: Use `python -c "import secrets; print(secrets.token_hex(32))"`

#### TTS_ENABLED
- **Description**: Enable/disable text-to-speech announcements
- **Default**: `true`
- **Values**: `true` or `false`

#### TTS_ENGINE
- **Description**: Text-to-speech engine to use
- **Default**: `gtts`
- **Options**: `gtts`, `espeak`, `festival`

### Database Configuration

#### DATABASE_URL
- **Description**: PostgreSQL connection string
- **Required**: Yes
- **Format**: `postgresql://user:password@host:port/database`
- **Example**: `postgresql://postgres:postgres@postgres:5432/dartsdb`

### RabbitMQ Configuration

#### RABBITMQ_EXCHANGE
- **Description**: RabbitMQ exchange name for message routing
- **Required**: Yes
- **Example**: `darts_exchange`

## Configuration Template

### Test Environment (.env)

```dotenv
# Environment
ENVIRONMENT=test
APP_DOMAIN=test.letsplaydarts.eu
APP_SCHEME=https
FLASK_USE_SSL=True
FLASK_DEBUG=False

# WSO2 Identity Server
WSO2_CLIENT_ID=darts_api_gateway
WSO2_CLIENT_SECRET=<ENCRYPTED_SECRET>
WSO2_IS_INTROSPECT_USER=admin
WSO2_IS_INTROSPECT_PASSWORD=<ENCRYPTED_PASSWORD>
WSO2_IS_DEFAULT_SCOPES="dartboard:write dartboard:read game:write game:control score:write player:write"
WSO2_IS_URL=https://test.letsplaydarts.eu/auth
WSO2_IS_VERIFY_SSL=False

# Application
SECRET_KEY=<GENERATED_SECRET_KEY>
SESSION_COOKIE_SECURE=True
AUTH_DISABLED=false

# Database
DATABASE_URL=postgresql://postgres:<PASSWORD>@postgres:5432/dartsdb

# RabbitMQ
RABBITMQ_EXCHANGE=darts_exchange
RABBITMQ_TOPIC=darts.#

# TTS
TTS_ENABLED=true
TTS_ENGINE=gtts
TTS_LANGUAGE=nl
```

### Production Environment (.env)

```dotenv
# Environment
ENVIRONMENT=production
APP_DOMAIN=letsplaydarts.eu
APP_SCHEME=https
FLASK_USE_SSL=True
FLASK_DEBUG=False

# WSO2 Identity Server
WSO2_CLIENT_ID=darts_api_gateway
WSO2_CLIENT_SECRET=<ENCRYPTED_SECRET>
WSO2_IS_INTROSPECT_USER=admin
WSO2_IS_INTROSPECT_PASSWORD=<ENCRYPTED_PASSWORD>
WSO2_IS_DEFAULT_SCOPES="dartboard:write dartboard:read game:write game:control score:write player:write"
WSO2_IS_URL=https://letsplaydarts.eu/auth
WSO2_IS_VERIFY_SSL=True

# Application
SECRET_KEY=<GENERATED_SECRET_KEY>
SESSION_COOKIE_SECURE=True
AUTH_DISABLED=false

# Database
DATABASE_URL=postgresql://postgres:<PASSWORD>@postgres:5432/dartsdb

# RabbitMQ
RABBITMQ_EXCHANGE=darts_exchange
RABBITMQ_TOPIC=darts.#

# TTS
TTS_ENABLED=true
TTS_ENGINE=gtts
TTS_LANGUAGE=nl
```

## Migration Guide for PR #182

### What Changed

PR #182 introduces robust OAuth2 scope handling to fix "Insufficient permissions" errors when WSO2 Identity Server introspection omits the `scope` field in token responses.

### Required Actions

**Before deploying to test or production**, add the following to your environment `.env` files in the `dartserver-config` repository:

```dotenv
WSO2_IS_DEFAULT_SCOPES="dartboard:write dartboard:read game:write game:control score:write player:write"
```

### Why This Is Needed

1. **WSO2 Behavior**: WSO2 Identity Server 7.x sometimes omits the `scope` field in introspection responses, particularly for client credentials grants
2. **Fallback Mechanism**: The code now falls back to `WSO2_IS_DEFAULT_SCOPES` when:
   - Token introspection succeeds (`active: true`)
   - Client ID matches `WSO2_IS_CLIENT_ID`
   - No scope field is present in the introspection response
3. **Environment Flexibility**: Each environment can define its own default scope set based on security requirements

### Deployment Impact

| Configuration Status | Deployment Behavior |
|---------------------|---------------------|
| Variable not set | Uses hardcoded default (works but not customizable) |
| Variable set in .env | Uses environment-specific scopes (recommended) |
| WSO2 returns scopes | Uses actual scopes from introspection (preferred) |

### Testing the Configuration

After deployment, verify scope handling:

```bash
# 1. Request token with specific scope
TOKEN=$(curl -ks -X POST https://<domain>/oauth2/token \
  -H 'Content-Type: application/x-www-form-urlencoded' \
  -d 'grant_type=client_credentials' \
  -d 'client_id=darts_api_gateway' \
  -d 'client_secret=<secret>' \
  -d 'scope=score:write' | jq -r '.access_token')

# 2. Test authorized endpoint
curl -X POST https://<domain>/api/v1/scores \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"player_id":"test","score":180,"multiplier":3,"segment":20}'

# Expected: 200 OK with {"status":"success",...}
```

## Related Documentation

- [WSO2 API Manager Configuration](WSO2_APIM_CONFIGURATION.md)
- [Deployment Guide](DEPLOYMENT.md)
- [Security Guide](SECURITY.md)

## Support

For questions or issues with configuration:
1. Check deployment logs: `docker-compose logs api-gateway`
2. Verify introspection response format in logs
3. Review PR #182 for technical details on scope handling
