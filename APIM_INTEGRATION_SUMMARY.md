# WSO2 API Manager Integration - Implementation Summary

## Overview

Successfully integrated WSO2 API Manager into the Darts Game System request flow. All dartboard and API requests now flow through APIM for centralized management, rate limiting, and security.

## What Changed

### 1. Request Flow (BEFORE → AFTER)

**BEFORE:**
```
Dartboard → Nginx → API Gateway → RabbitMQ
```

**AFTER:**
```
Dartboard → Nginx → APIM (validates, rate limits) → API Gateway → RabbitMQ
```

### 2. Files Created

#### Scripts
- **helpers/setup_wso2_apim.py**: Automated APIM configuration
  - Creates throttling policies (DartboardThrottle: 1000/min, GameControlThrottle: 100/min)
  - Defines DartsGameAPI with all endpoints
  - Configures scopes and security
  - Publishes API to Developer Portal

- **helpers/configure_wso2_apim.sh**: Shell wrapper for Docker integration
  - Waits for APIM to be healthy
  - Runs Python setup script
  - Provides status feedback

- **helpers/test_wso2_apim_integration.py**: Comprehensive integration tests
  - OAuth2 token acquisition
  - Health endpoint testing
  - Authenticated requests through APIM
  - Rate limiting validation
  - Unauthorized access blocking

#### Documentation
- **helpers/README_APIM.md**: Quick start guide for APIM integration
- **doc/WSO2_APIM_CONFIGURATION.md**: Updated with automated setup instructions
- **doc/ARCHITECTURE.md**: Updated diagrams and flow descriptions

### 3. Files Modified

#### nginx/nginx.conf
- **Changed**: Route `/api/v1/*` through APIM gateway (port 8243) instead of direct to API Gateway
- **Added**: `/api-direct/v1/*` for direct API Gateway access (debugging/testing)
- **Removed**: Nginx rate limiting (now handled by APIM)

#### docker-compose-localhost.yml
- **Changed**: api-gateway now depends on wso2apim being healthy
- Ensures APIM is ready before API Gateway starts

### 4. API Endpoints (via APIM)

All requests to `https://domain/api/v1/*` now go through APIM:

| Endpoint | Scope | Throttle Policy |
|----------|-------|-----------------|
| POST /v1/dartboard/throw | dartboard:write | 1000 req/min |
| POST /v1/scores | score:write | 100 req/min |
| POST /v1/games | game:create | 100 req/min |
| POST /v1/players | player:create | 100 req/min |
| POST /v1/game/actions/* | game:control | 100 req/min |
| GET /health | (none) | Unlimited |

## How to Use

### Quick Start

```bash
# 1. Start the stack
docker-compose -f docker-compose-localhost.yml up -d

# 2. Configure APIM (runs automatically, or manually):
./helpers/configure_wso2_apim.sh

# 3. Test integration
python helpers/test_wso2_apim_integration.py --verbose
```

### Access APIM Portals

- Publisher Portal: https://localhost:9444/publisher
- Developer Portal: https://localhost:9444/devportal
- Admin Portal: https://localhost:9444/admin
- Credentials: admin / admin

### Client Configuration

Dartboards and clients should now use:

```env
# Token endpoint (WSO2 IS)
WSO2_TOKEN_URL=https://your-domain/auth/oauth2/token

# API endpoint (through APIM)
API_GATEWAY_URL=https://your-domain/api/v1

# OAuth2 credentials
WSO2_CLIENT_ID=<from-apim-devportal>
WSO2_CLIENT_SECRET=<from-apim-devportal>
```

## Benefits

1. **Centralized Management**: All APIs managed through APIM console
2. **Rate Limiting**: Protect backend from abuse with throttling policies
3. **Analytics**: Request monitoring and reporting (when enabled)
4. **Security**: Token validation at gateway layer
5. **Versioning**: Easy API version management
6. **Documentation**: Auto-generated API documentation

## Testing

### Automated Tests

```bash
python helpers/test_wso2_apim_integration.py --verbose
```

Tests include:
- ✓ OAuth2 token acquisition
- ✓ Health endpoint (no auth)
- ✓ Unauthorized access blocking
- ✓ Dartboard throw submission
- ✓ Score submission
- ✓ Rate limiting validation

### Manual Testing

```bash
# Get token
TOKEN=$(curl -k -X POST https://localhost:9443/oauth2/token \
  -u "CLIENT_ID:CLIENT_SECRET" \
  -d "grant_type=client_credentials&scope=dartboard:write" \
  | jq -r '.access_token')

# Submit throw through APIM
curl -k -X POST https://localhost:8243/api/v1/dartboard/throw \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"pins": [20, 1], "game_id": "test-123", "player_id": "player-1"}'
```

## Migration Notes

### Existing Dartboards

Update dartboard configuration to:
1. Use new API Gateway URL (through APIM)
2. Obtain client credentials from APIM DevPortal
3. Test connectivity with integration script

### Direct API Gateway Access

For debugging, direct access is still available:
- Via nginx: `https://localhost/api-direct/v1/`
- Direct: `http://localhost:8080/`

**Production**: Block direct access with firewall rules.

## Rollback Plan

If issues arise:

1. Update nginx to route directly to API Gateway:
   ```nginx
   location /api/v1/ {
       proxy_pass http://api_gateway;
   }
   ```

2. Restart nginx:
   ```bash
   docker-compose restart nginx
   ```

3. Clients continue to work (same endpoint, no APIM in between)

## Next Steps

1. **Production Deployment**:
   - Configure SSL certificates
   - Set up proper DNS
   - Configure APIM analytics
   - Enable monitoring

2. **Client Migration**:
   - Update dartboard firmware with new credentials
   - Test each dartboard individually
   - Monitor APIM analytics for errors

3. **Advanced Features**:
   - Enable APIM analytics for request tracking
   - Set up custom throttling policies per client
   - Configure API versioning for future updates
   - Add API documentation portal

## Troubleshooting

See:
- **helpers/README_APIM.md**: Quick troubleshooting guide
- **doc/WSO2_APIM_CONFIGURATION.md**: Detailed configuration
- **doc/ARCHITECTURE.md**: System architecture

Common issues:
- APIM not starting → Check memory (needs 2GB)
- Setup script fails → Run with `--verbose` flag
- Rate limiting not working → Verify throttling policies in Admin Portal
- Token validation fails → Check WSO2 IS integration

## Files Summary

**Created:**
- helpers/setup_wso2_apim.py (658 lines)
- helpers/configure_wso2_apim.sh (67 lines)
- helpers/test_wso2_apim_integration.py (460 lines)
- helpers/README_APIM.md (194 lines)

**Modified:**
- nginx/nginx.conf (routing changes)
- docker-compose-localhost.yml (dependency updates)
- doc/WSO2_APIM_CONFIGURATION.md (updated with automation)
- doc/ARCHITECTURE.md (updated diagrams and flows)

**Total Lines Added**: ~1,400 lines of code and documentation
