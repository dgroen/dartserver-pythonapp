# WSO2 APIM Integration - Complete Setup Guide

## Overview

This document provides comprehensive instructions for setting up WSO2 API Manager (APIM) 4.0.0 integration with WSO2 Identity Server (IS) 7.1.0 for the Dartserver application.

## Architecture

```
User/Browser
    ↓
Nginx (Reverse Proxy)
    ↓ /api/v1/*
APIM Gateway (8243/HTTPS, 8280/HTTP)
    ↓ (Token Validation)
WSO2 IS (OAuth2/OIDC Provider)
    ↓
API Gateway
    ↓
Python Flask Application
```

## Current Status

### ✅ Completed
- Docker Compose configured with all services
- APIM image pulled and container running
- APIM DartsGameAPI defined with throttling policies
- Nginx routing configured to APIM gateway
- APIM deployment.toml created with Key Manager configuration pointing to WSO2 IS

### ⏳ Pending
- OAuth2 client registration in WSO2 IS for APIM portals
- Portal authentication configuration

## Setup Steps

### Step 1: Verify Service Status

```bash
# Check all services are running
docker-compose -f docker-compose-localhost.yml ps

# Services should show:
# - wso2is: Up
# - wso2apim: Up  
# - postgres: Up
# - rabbitmq: Up
# - api-gateway: Up
```

### Step 2: Register APIM OAuth2 Application in WSO2 IS

**Manual Setup Required** (Automated setup will be available in future versions)

1. **Open WSO2 IS MyAccount Portal**
   ```
   https://localhost:9443/myaccount
   ```

2. **Login**
   - Username: `admin`
   - Password: `admin`

3. **Register OAuth2 Application**
   - Click on: **Security** → **OAuth Applications**
   - Click **Register** button
   - Fill in the following details:

   **Application Name:** 
   ```
   APIM
   ```

   **Authorized Redirect URIs:** (Add each one separately)
   ```
   https://localhost:9444/publisher/services/auth/callback
   https://localhost:9444/devportal/services/auth/callback
   https://localhost:9444/admin/services/auth/callback
   https://localhost:9444/analytics/services/auth/callback
   ```

   **Allowed Grant Types:** (Select all)
   ```
   ✓ Code
   ✓ Refresh Token
   ✓ Implicit
   ```

4. **Complete Registration**
   - Click **Register** button
   - You should see a success message with:
     - **Client ID** (copy this)
     - **Client Secret** (copy this)

### Step 3: Update APIM Configuration

1. **Edit deployment.toml**
   ```bash
   nano wso2apim-4-config/deployment.toml
   ```

2. **Add OAuth2 OIDC Configuration**
   
   Locate or add the `[oauth2.oidc]` section and update with the credentials from Step 2:
   
   ```toml
   [oauth2.oidc]
   client_id = "YOUR_CLIENT_ID_FROM_STEP_2"
   client_secret = "YOUR_CLIENT_SECRET_FROM_STEP_2"
   server_url = "https://wso2is:9443"
   authorize_endpoint = "https://wso2is:9443/oauth2/authorize"
   token_endpoint = "https://wso2is:9443/oauth2/token"
   revoke_endpoint = "https://wso2is:9443/oauth2/revoke"
   userinfo_endpoint = "https://wso2is:9443/oauth2/userinfo"
   oidc_logout_endpoint = "https://wso2is:9443/oidc/logout"
   oidc_session_iframe_endpoint = "https://wso2is:9443/oidc/checksession"
   scope = "openid profile email"
   ```

3. **Save the file**
   ```bash
   # If using nano, press Ctrl+X, then Y, then Enter
   ```

### Step 4: Restart APIM Container

```bash
# Restart APIM to pick up the new configuration
docker-compose -f docker-compose-localhost.yml restart wso2apim

# Wait for APIM to fully start (about 2-3 minutes)
# Check status with:
docker-compose -f docker-compose-localhost.yml ps wso2apim

# Should show "Up" with health check "healthy"
```

### Step 5: Verify Portal Access

Once APIM is healthy, test portal access:

**Publisher Portal:**
```
https://localhost:9444/publisher
```

**Developer Portal:**
```
https://localhost:9444/devportal
```

**Admin Portal:**
```
https://localhost:9444/admin
```

**Expected Result:**
- Should redirect to WSO2 IS login
- Login with `admin` / `admin`
- Should show APIM portal interface without OAuth errors

### Step 6: Verify API Gateway

Test that API requests are routed through APIM:

```bash
# Test API authentication flow
curl -k -X POST https://localhost:9443/api/v1/auth/token \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "grant_type=password&username=admin&password=admin&scope=darts_api"

# Should return access token
# Token will be validated by APIM gateway before reaching API
```

## Troubleshooting

### Portal Returns "Cannot find an application" Error

**Cause:** OAuth2 client not registered in WSO2 IS

**Solution:** 
1. Complete Step 2 again (OAuth2 Application Registration)
2. Verify Client ID and Client Secret are copied correctly
3. Ensure all redirect URIs are added (including https://)
4. Check that hostname matches (localhost:9444)

### Portal Displays Blank Page

**Cause:** Configuration not applied

**Solution:**
1. Verify deployment.toml has correct OAuth2 credentials
2. Restart APIM: `docker-compose restart wso2apim`
3. Wait for health check to pass (docker ps)
4. Clear browser cache and try again

### "Connection Refused" Errors

**Cause:** Services not running or networking issues

**Solution:**
```bash
# Check all services running
docker-compose -f docker-compose-localhost.yml ps

# Check APIM logs
docker logs darts-wso2apim

# Check IS logs
docker logs darts-wso2is

# Restart all services
docker-compose -f docker-compose-localhost.yml restart
```

### APIM Cannot Reach WSO2 IS

**Cause:** Network or hostname resolution issue

**Solution:**
1. Verify services are on same Docker network:
   ```bash
   docker inspect darts-wso2is | grep NetworkSettings
   docker inspect darts-wso2apim | grep NetworkSettings
   ```

2. Check deployment.toml uses correct IS hostname (`wso2is` not `localhost`)

3. Verify firewall/security allows 9443 port between containers

## Configuration Files

### Key Files Modified/Created

1. **docker-compose-localhost.yml**
   - Added volume mount for APIM deployment.toml
   - Added wso2apim service dependency on wso2is health check

2. **wso2apim-4-config/deployment.toml**
   - Contains Key Manager configuration pointing to WSO2 IS
   - Specifies OAuth2 endpoints and token validation settings
   - Configures APIM portals for OIDC authentication

3. **nginx/nginx.conf**
   - Routes `/api/v1/*` requests to APIM gateway (`wso2apim:8243`)
   - Maintains HTTPS with self-signed certificates

## Testing the Integration

### 1. Direct API Request Through APIM

```bash
# Request without authentication (should be rejected)
curl -k https://localhost:9443/api/v1/darts/board

# Get token
TOKEN=$(curl -k -s -X POST https://localhost:9443/api/v1/auth/token \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "grant_type=password&username=admin&password=admin&scope=darts_api" \
  | grep -o '"access_token":"[^"]*' | cut -d'"' -f4)

# Request with token (should succeed)
curl -k -H "Authorization: Bearer $TOKEN" \
  https://localhost:9443/api/v1/darts/board
```

### 2. Test APIM Throttling Policies

The following policies are configured:

- **DartboardThrottle:** 1000 requests per minute
- **GameControlThrottle:** 100 requests per minute  
- **UnlimitedThrottle:** No rate limiting

Make multiple rapid requests to verify throttling works:

```bash
for i in {1..110}; do
  curl -k -H "Authorization: Bearer $TOKEN" \
    https://localhost:9443/api/v1/darts/board
done

# After 110 requests, should receive 429 (Too Many Requests)
```

### 3. Test Portal Authentication

Access each portal and verify:
1. Redirects to WSO2 IS login
2. Can login with admin credentials
3. Portal displays without errors
4. Can navigate portal features

## Integration Points

### APIM → WSO2 IS Communication

- **Token Validation:** APIM validates JWT tokens against WSO2 IS
- **Token Introspection:** APIM introspects tokens for validity
- **User Information:** APIM retrieves user info from IS userinfo endpoint
- **OAuth2 Portal Auth:** APIM portals use IS for administrator authentication

### API Gateway → APIM

- **Token Forwarding:** API Gateway receives token in Authorization header
- **Token Validation:** Token was already validated by APIM gateway
- **Request Routing:** APIM routes authenticated requests to API Gateway

## Advanced Configuration

### Configuring Additional OAuth2 Scopes

Edit deployment.toml `[oauth2.oidc]` section:

```toml
scope = "openid profile email darts_api game_control"
```

### Using External WSO2 IS Instance

If using a separate WSO2 IS deployment:

1. Update `server_url` in deployment.toml:
   ```toml
   server_url = "https://wso2is.example.com:9443"
   ```

2. Update all endpoint URLs to use external hostname

3. Register APIM in external IS with correct redirect URIs

### Enabling Analytics

Uncomment analytics configuration in deployment.toml:

```toml
[apim.analytics]
enable = true
server_url = "https://analytics:9444"
```

## Support & Documentation

- [WSO2 APIM Documentation](https://apim.docs.wso2.com/)
- [WSO2 IS Documentation](https://is.docs.wso2.com/)
- [Dartserver Architecture](doc/ARCHITECTURE.md)
- [WSO2 APIM Configuration](doc/WSO2_APIM_CONFIGURATION.md)

## Next Steps

1. ✅ Complete Step 2 (Register OAuth2 Application)
2. ✅ Complete Step 3 (Update Configuration)
3. ✅ Complete Step 4 (Restart APIM)
4. ✅ Verify portal access in Step 5
5. Test API requests through APIM in Step 6
6. Configure additional policies as needed
7. Deploy to production with proper SSL certificates
