# WSO2 API Manager Configuration Guide

This guide explains how to configure WSO2 API Manager (APIM) to manage and expose the Darts API Gateway service.

**Status**: ✅ **IMPLEMENTED** - This integration is now active in the system.

## Quick Start

For quick setup in development:

```bash
# 1. Start the stack
docker-compose -f docker-compose-localhost.yml up -d

# 2. Wait for services to be healthy (2-3 minutes)
docker-compose -f docker-compose-localhost.yml ps

# 3. Run automated APIM configuration
./helpers/configure_wso2_apim.sh

# 4. Test the integration
python helpers/test_wso2_apim_integration.py --verbose
```

## Prerequisites

- WSO2 API Manager 4.x installed and running
- WSO2 Identity Server (IS) configured and integrated with APIM
- API Gateway service deployed and accessible
- Admin access to WSO2 APIM Management Console

## Architecture Overview

```
┌─────────────────┐
│   Dartboard     │ ──┐
│   Hardware      │   │
└─────────────────┘   │
                      │ Client Credentials
┌─────────────────┐   │ OAuth2 Flow
│   Web Clients   │ ──┤
│   (Browser)     │   │
└─────────────────┘   │
                      ▼
                 ┌──────────────────┐
                 │  Nginx Proxy     │
                 │  (Port 443)      │
                 └──────────────────┘
                          │
                          │ Routes /api/v1/*
                          ▼
                 ┌──────────────────┐
                 │  WSO2 APIM       │
                 │  Gateway         │
                 │  (Port 8243)     │
                 └──────────────────┘
                          │
                          │ Validates & Forwards
                          ▼
                 ┌──────────────────┐
                 │  Darts API       │
                 │  Gateway         │
                 │  (Port 8080)     │
                 └──────────────────┘
                          │
                          │ Publishes to
                          ▼
                 ┌──────────────────┐
                 │  RabbitMQ        │
                 └──────────────────┘
```

**Request Flow:**
1. Client sends request to `https://your-domain/api/v1/dartboard/throw`
2. Nginx routes to APIM gateway at port 8243
3. APIM validates OAuth2 token with WSO2 IS
4. APIM applies rate limiting policies
5. APIM forwards to API Gateway at port 8080
6. API Gateway publishes event to RabbitMQ
7. Response flows back through the chain

## Automated Setup

### Using the Setup Script (Recommended)

The automated setup script handles all APIM configuration:

```bash
# Run with defaults (uses environment variables)
python helpers/setup_wso2_apim.py

# Run with custom settings
python helpers/setup_wso2_apim.py \
  --apim-url https://localhost:9444 \
  --api-gateway-url http://api-gateway:8080 \
  --username admin \
  --password admin \
  --verbose
```

**What it does:**
1. Waits for APIM to be ready
2. Authenticates with admin credentials
3. Creates throttling policies:
   - `DartboardThrottle`: 1000 requests/minute (for dartboards)
   - `GameControlThrottle`: 100 requests/minute (for game control)
   - `UnlimitedThrottle`: No limits (for testing)
4. Creates the Darts API with all endpoints
5. Publishes the API to the Developer Portal

### Docker Integration

The APIM setup runs automatically during container startup. To trigger manually:

```bash
docker exec -it darts-wso2apim /app/helpers/configure_wso2_apim.sh
```

## Manual Configuration

### Step 1: Configure WSO2 Identity Server Integration

Ensure WSO2 IS is properly integrated with APIM for authentication:

1. **Configure Token Validation**
   - In APIM, configure the Key Manager to use WSO2 IS
   - Set the introspection endpoint: `https://wso2-is:9443/oauth2/introspect`
   - Set the token endpoint: `https://wso2-is:9443/oauth2/token`
   - Set the JWKS endpoint: `https://wso2-is:9443/oauth2/jwks`

2. **Verify Connection**
   ```bash
   curl -k https://wso2-apim:9443/api/am/admin/v4/key-managers
   ```

### Step 2: Create API in WSO2 APIM

The automated script creates an API named **DartsGameAPI** with the following configuration:

**API Details:**
- **Name**: DartsGameAPI
- **Version**: v1
- **Context**: `/api`
- **Backend**: `http://api-gateway:8080`

**Endpoints:**
```
POST /v1/dartboard/throw     - Submit dartboard throw (scope: dartboard:write)
POST /v1/scores               - Submit score (scope: score:write)
POST /v1/games                - Create game (scope: game:create)
POST /v1/players              - Add player (scope: player:create)
POST /v1/game/actions/end-turn     - End turn (scope: game:control)
POST /v1/game/actions/continue     - Continue game (scope: game:control)
POST /v1/game/actions/pause        - Pause game (scope: game:control)
GET  /health                  - Health check (no auth required)
```

### Step 3: Configure Security

### 3.1 OAuth2 Scopes

The following scopes are defined in the API:

| Scope | Description |
|-------|-------------|
| `dartboard:write` | Submit dartboard throws |
| `score:write` | Submit scores |
| `game:create` | Create new games |
| `game:control` | Control game flow (pause, resume, end turn) |
| `player:create` | Add players to games |

### 3.2 Throttling Policies

| Policy | Rate Limit | Usage |
|--------|------------|-------|
| DartboardThrottle | 1000 req/min | Dartboard hardware throws |
| GameControlThrottle | 100 req/min | Game control operations |
| Unlimited | No limit | Health checks and development |

## Client Configuration

### For Dartboard Hardware

Configure dartboards to use APIM gateway:

```env
# Token endpoint (WSO2 IS)
WSO2_TOKEN_URL=https://your-domain/auth/oauth2/token

# APIM Gateway endpoint
API_GATEWAY_URL=https://your-domain/api/v1

# OAuth2 credentials (obtain from APIM Dev Portal)
WSO2_CLIENT_ID=<your-client-id>
WSO2_CLIENT_SECRET=<your-client-secret>

# Scopes
OAUTH_SCOPES=dartboard:write game:control
```

**Example cURL request:**

```bash
# 1. Get access token
TOKEN=$(curl -k -X POST https://localhost:9443/oauth2/token \
  -u "CLIENT_ID:CLIENT_SECRET" \
  -d "grant_type=client_credentials" \
  -d "scope=dartboard:write" \
  | jq -r '.access_token')

# 2. Submit dartboard throw through APIM
curl -k -X POST https://localhost:8243/api/v1/dartboard/throw \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "pins": [20, 1],
    "game_id": "test-game",
    "player_id": "player-1"
  }'
```

### For Web Applications

Web apps should use the authorization code flow:

```javascript
// 1. Redirect to authorization endpoint
const authUrl = `https://your-domain/auth/oauth2/authorize?` +
  `client_id=${CLIENT_ID}&` +
  `redirect_uri=${REDIRECT_URI}&` +
  `response_type=code&` +
  `scope=score:write game:create`;

window.location.href = authUrl;

// 2. Exchange code for token (on callback)
const tokenResponse = await fetch('https://your-domain/auth/oauth2/token', {
  method: 'POST',
  headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
  body: new URLSearchParams({
    grant_type: 'authorization_code',
    code: authCode,
    redirect_uri: REDIRECT_URI,
    client_id: CLIENT_ID,
    client_secret: CLIENT_SECRET
  })
});

const { access_token } = await tokenResponse.json();

// 3. Use token to call API through APIM
const response = await fetch('https://your-domain/api/v1/scores', {
  method: 'POST',
  headers: {
    'Authorization': `Bearer ${access_token}`,
    'Content-Type': 'application/json'
  },
  body: JSON.stringify({
    score: 60,
    multiplier: 'TRIPLE',
    game_id: 'game-123',
    player_id: 'player-1'
  })
});
```

## Testing the Integration

### Automated Testing

Run the comprehensive test suite:

```bash
# Basic test
python helpers/test_wso2_apim_integration.py

# Verbose output
python helpers/test_wso2_apim_integration.py --verbose

# Custom endpoints
python helpers/test_wso2_apim_integration.py \
  --apim-gateway-url https://localhost:8243 \
  --wso2-is-url https://localhost:9443 \
  --client-id YOUR_CLIENT_ID \
  --client-secret YOUR_CLIENT_SECRET
```

**Tests performed:**
1. ✓ OAuth2 token acquisition
2. ✓ Health endpoint (no auth)

### 4.3 Test Dartboard Authentication

```bash
# Get access token
curl -k -X POST https://wso2-apim:9443/oauth2/token \
  -u "dartboard_001_client:CLIENT_SECRET" \
  -d "grant_type=client_credentials&scope=dartboard:write"

# Response
{
  "access_token": "eyJhbGciOiJSUzI1NiIsICJ0eXAiOiJKV1QiLCAia2lkIjoi...",
  "scope": "dartboard:write",
  "token_type": "Bearer",
  "expires_in": 3600
}

# Use token to submit throw
curl -k -X POST https://wso2-apim:9443/darts/v1/api/v1/dartboard/throw \
  -H "Authorization: Bearer ACCESS_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "masterPin": 4,
    "slavePin": 13,
    "boardType": "carromco"
  }'
```

## Step 5: Configure Rate Limiting and Throttling

### 5.1 Application-Level Throttling

Configure throttling policies for different client types:

1. **Unlimited** (for trusted internal clients)
2. **Gold** (100 requests/minute for production dartboards)
3. **Silver** (50 requests/minute for test dartboards)
4. **Bronze** (10 requests/minute for development)

### 5.2 Resource-Level Throttling

Apply specific limits to endpoints:

- `/api/v1/dartboard/throw`: 10 requests/second per client
- `/api/v1/scores`: 10 requests/second per client
- `/api/v1/games`: 1 request/second per client

## Step 6: Enable HTTPS

### 6.1 Configure SSL Certificates

For production deployment:

1. Obtain SSL certificates from a trusted CA
2. Configure APIM to use certificates:

```bash
# Import certificate to keystore
keytool -import -alias apim_cert \
  -file certificate.crt \
  -keystore client-truststore.jks \
  -storepass wso2carbon
```

3. Update `deployment.toml`:

```toml
[transport.https.properties]
proxyPort = 443

[[apim.gateway.environment]]
name = "Production"
type = "hybrid"
provider = "wso2"
display_in_api_console = true
description = "Production Gateway"
show_as_token_endpoint_url = true
service_url = "https://api.dartsapp.example.com"
ws_endpoint = "wss://api.dartsapp.example.com"
```

### 6.2 Development Environment (HTTP)

For development, allow HTTP:

```toml
[transport.http]
listener.enable = true
listener.port = 8280
```

## Step 7: Configure Monitoring and Analytics

### 7.1 Enable API Analytics

1. Go to APIM Admin Portal
2. Navigate to Settings → Analytics
3. Enable analytics for the Darts API Gateway
4. Configure:
   - Request/response logging
   - Performance metrics
   - Error tracking

### 7.2 Set Up Alerts

Configure alerts for:
- High error rates (>5% errors)
- Slow responses (>1 second)
- Rate limit breaches
- Unauthorized access attempts

## Step 8: Configure CORS

Enable CORS for web applications:

```xml
<!-- In deployment.toml -->
[apim.cors]
enable = true
allow_origins = ["https://app.dartsapp.example.com", "http://localhost:5000"]
allow_methods = ["GET", "POST", "PUT", "DELETE", "OPTIONS"]
allow_headers = ["Authorization", "Content-Type", "X-API-Key"]
allow_credentials = true
```

## Testing the Configuration

### Test Suite Checklist

- [ ] Health check endpoint accessible without auth
- [ ] Swagger UI accessible at `/docs`
- [ ] Dartboard client can obtain access token
- [ ] Dartboard client can submit throws with token
- [ ] Web client can use authorization code flow
- [ ] Rate limiting works as expected
- [ ] HTTPS redirects HTTP traffic (production)
- [ ] Analytics data is being collected
- [ ] Multiple concurrent dartboards work

### Automated Testing Script

```bash
#!/bin/bash
# test_apim_config.sh

APIM_URL="https://wso2-apim:9443/darts/v1"
CLIENT_ID="dartboard_001_client"
CLIENT_SECRET="your_secret_here"

# Test 1: Get access token
echo "Test 1: Obtaining access token..."
TOKEN_RESPONSE=$(curl -sk -X POST https://wso2-apim:9443/oauth2/token \
  -u "$CLIENT_ID:$CLIENT_SECRET" \
  -d "grant_type=client_credentials&scope=dartboard:write")

ACCESS_TOKEN=$(echo $TOKEN_RESPONSE | jq -r '.access_token')

if [ "$ACCESS_TOKEN" != "null" ]; then
  echo "✓ Token obtained successfully"
else
  echo "✗ Failed to obtain token"
  exit 1
fi

# Test 2: Submit dartboard throw
echo "Test 2: Submitting dartboard throw..."
THROW_RESPONSE=$(curl -sk -X POST $APIM_URL/api/v1/dartboard/throw \
  -H "Authorization: Bearer $ACCESS_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"masterPin":4,"slavePin":13,"boardType":"carromco"}')

STATUS=$(echo $THROW_RESPONSE | jq -r '.status')

if [ "$STATUS" == "success" ]; then
  echo "✓ Dartboard throw submitted successfully"
else
  echo "✗ Failed to submit throw"
  exit 1
fi

# Test 3: Health check
echo "Test 3: Checking health endpoint..."
HEALTH_RESPONSE=$(curl -sk $APIM_URL/health)
HEALTH_STATUS=$(echo $HEALTH_RESPONSE | jq -r '.status')

if [ "$HEALTH_STATUS" == "healthy" ]; then
  echo "✓ Health check passed"
else
  echo "✗ Health check failed"
  exit 1
fi

echo "All tests passed!"
```

## Troubleshooting

### Common Issues

1. **Token validation fails**
   - Check WSO2 IS integration configuration
   - Verify JWKS endpoint is accessible
   - Check client ID and secret are correct

2. **CORS errors**
   - Enable CORS in APIM configuration
   - Add your domain to allowed origins

3. **Rate limiting too aggressive**
   - Adjust throttling policies
   - Create custom policies for specific clients

4. **SSL certificate errors**
   - Import CA certificate to truststore
   - For development, use `-k` flag with curl

## Production Deployment Checklist

- [ ] SSL certificates installed and verified
- [ ] All endpoints use HTTPS
- [ ] Rate limiting configured appropriately
- [ ] Analytics and monitoring enabled
- [ ] Backup of APIM configuration
- [ ] Dartboard clients configured with production credentials
- [ ] CORS configured for production domains
- [ ] Load balancer configured (if using multiple APIM instances)
- [ ] Disaster recovery plan documented
- [ ] Security audit completed

## References

- [WSO2 APIM Documentation](https://apim.docs.wso2.com/)
- [OAuth2 Client Credentials Flow](https://oauth.net/2/grant-types/client-credentials/)
- [OpenAPI Specification](https://swagger.io/specification/)
- Darts API Gateway OpenAPI Spec: `src/api_gateway/openapi.yaml`
