# WSO2 API Manager Configuration Guide

This guide explains how to configure WSO2 API Manager (APIM) to manage and expose the Darts API Gateway service.

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
                 │  WSO2 APIM       │
                 │  (API Gateway)   │
                 └──────────────────┘
                          │
                          │ Forwards to
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

## Step 1: Configure WSO2 Identity Server Integration

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

## Step 2: Create API in WSO2 APIM

### 2.1 Import OpenAPI Specification

1. Log in to WSO2 APIM Publisher Portal: `https://wso2-apim:9443/publisher`
2. Click "Create API" → "Import Open API"
3. Upload the OpenAPI spec from `src/api_gateway/openapi.yaml`
4. Configure API details:
   - **Name**: Darts API Gateway
   - **Version**: 1.0.0
   - **Context**: `/darts/v1`
   - **Endpoint**: `http://api-gateway:8080`

### 2.2 Configure API Manually (Alternative)

If importing doesn't work, create the API manually:

```bash
# API Details
Name: Darts API Gateway
Version: 1.0.0
Context: /darts/v1
Business Plans: Unlimited

# Endpoints
Production Endpoint: http://api-gateway:8080
Sandbox Endpoint: http://api-gateway:8080

# Resources
POST /api/v1/dartboard/throw     - dartboard:write
POST /api/v1/scores               - score:write
POST /api/v1/games                - game:write
POST /api/v1/players              - player:write
POST /api/v1/game/actions/*       - game:control
GET  /health                      - (no scope required)
GET  /docs                        - (no scope required)
```

## Step 3: Configure Security

### 3.1 OAuth2 Scopes

Define the following scopes in the API:

| Scope | Description |
|-------|-------------|
| `dartboard:write` | Submit dartboard throws |
| `score:write` | Submit scores |
| `game:write` | Create and manage games |
| `game:control` | Control game flow (pause, resume, end turn) |
| `player:write` | Add players to games |

### 3.2 Configure Grant Types

Enable the following grant types:

- **Client Credentials**: For dartboard hardware devices
- **Authorization Code**: For web applications
- **Refresh Token**: For maintaining sessions

## Step 4: Register Dartboard Clients

### 4.1 Create Application for Dartboards

1. Go to WSO2 APIM Developer Portal: `https://wso2-apim:9443/devportal`
2. Create a new application:
   - **Name**: Dartboard Devices
   - **Throttling Tier**: Unlimited
   - **Description**: Hardware dartboard clients

3. Subscribe to "Darts API Gateway"

4. Generate Keys:
   - **Grant Types**: Client Credentials
   - **Scopes**: `dartboard:write`, `game:control`

### 4.2 Distribute Credentials to Dartboards

Each dartboard device needs:
- **Client ID**: Unique identifier (e.g., `dartboard_001_client`)
- **Client Secret**: Secure secret key

Example `.env` configuration for dartboard:

```env
WSO2_TOKEN_URL=https://wso2-apim:9443/oauth2/token
WSO2_CLIENT_ID=dartboard_001_client
WSO2_CLIENT_SECRET=xxxxxxxxxxxxxxxxxxxxxxx
API_GATEWAY_URL=https://wso2-apim:9443/darts/v1
```

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
