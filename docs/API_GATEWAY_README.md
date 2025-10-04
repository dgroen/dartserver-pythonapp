# API Gateway for Darts Game System

## Overview

The API Gateway provides a secure, managed REST API layer on top of the RabbitMQ message broker. It enables electronic dartboards, mobile applications, and other external clients to interact with the Darts Game System through a standardized HTTP API.

## Key Features

- **OAuth2 Authentication:** Secure authentication via WSO2 Identity Server
- **JWT Validation:** Token validation using JWKS or introspection
- **Role-Based Access Control:** Scope-based authorization
- **Request Validation:** Schema validation for all incoming requests
- **RabbitMQ Integration:** Publishes validated messages to RabbitMQ
- **Audit Logging:** Comprehensive logging of all API requests
- **Error Handling:** Standardized error responses
- **Health Checks:** Service health monitoring endpoint

## Architecture

```
┌─────────────┐
│   Client    │
│ (Dartboard/ │
│  Mobile)    │
└──────┬──────┘
       │
       │ HTTPS + OAuth2
       │
       ▼
┌─────────────────────┐
│  WSO2 API Manager   │
│  - Rate Limiting    │
│  - Analytics        │
└──────┬──────────────┘
       │
       ▼
┌─────────────────────┐
│  WSO2 Identity      │
│  Server             │
│  - OAuth2/OIDC      │
│  - JWT Tokens       │
└──────┬──────────────┘
       │
       ▼
┌─────────────────────┐
│  API Gateway        │
│  - JWT Validation   │
│  - Request Valid.   │
│  - RabbitMQ Pub.    │
└──────┬──────────────┘
       │
       ▼
┌─────────────────────┐
│  RabbitMQ Broker    │
└──────┬──────────────┘
       │
       ▼
┌─────────────────────┐
│  Flask Application  │
│  - Game Logic       │
└─────────────────────┘
```

## API Endpoints

### Health Check

**Endpoint:** `GET /health`

**Authentication:** None

**Description:** Check if the API Gateway is healthy and operational.

**Response:**
```json
{
  "status": "healthy",
  "service": "darts-api-gateway",
  "timestamp": "2024-01-01T12:00:00.000000"
}
```

### Submit Score

**Endpoint:** `POST /api/v1/scores`

**Authentication:** Required (OAuth2)

**Required Scope:** `score:write`

**Rate Limit:** 100 requests/minute

**Request Body:**
```json
{
  "score": 20,
  "multiplier": "TRIPLE",
  "player_id": "player-123",
  "game_id": "game-456"
}
```

**Response (201 Created):**
```json
{
  "status": "success",
  "message": "Score submitted successfully",
  "data": {
    "score": 20,
    "multiplier": "TRIPLE",
    "player_id": "player-123",
    "game_id": "game-456",
    "user": "dartboard-001",
    "timestamp": "2024-01-01T12:00:00.000000"
  }
}
```

**Validation Rules:**
- `score`: Integer between 0 and 60
- `multiplier`: One of "SINGLE", "DOUBLE", "TRIPLE"
- `player_id`: Optional string
- `game_id`: Optional string

### Create Game

**Endpoint:** `POST /api/v1/games`

**Authentication:** Required (OAuth2)

**Required Scope:** `game:write`

**Rate Limit:** 10 requests/minute

**Request Body:**
```json
{
  "game_type": "301",
  "players": ["Player 1", "Player 2"],
  "double_out": false
}
```

**Response (201 Created):**
```json
{
  "status": "success",
  "message": "Game created successfully",
  "data": {
    "action": "new_game",
    "game_type": "301",
    "players": ["Player 1", "Player 2"],
    "double_out": false,
    "created_by": "admin_user",
    "timestamp": "2024-01-01T12:00:00.000000"
  }
}
```

**Validation Rules:**
- `game_type`: One of "301", "401", "501", "cricket"
- `players`: Array with at least 1 player name
- `double_out`: Boolean (optional, default: false)

### Add Player

**Endpoint:** `POST /api/v1/players`

**Authentication:** Required (OAuth2)

**Required Scope:** `player:write`

**Rate Limit:** 20 requests/minute

**Request Body:**
```json
{
  "name": "Player 3"
}
```

**Response (201 Created):**
```json
{
  "status": "success",
  "message": "Player added successfully",
  "data": {
    "action": "add_player",
    "name": "Player 3",
    "added_by": "admin_user",
    "timestamp": "2024-01-01T12:00:00.000000"
  }
}
```

**Validation Rules:**
- `name`: Non-empty string

## Authentication

### Obtaining Access Token

**Client Credentials Grant (for devices):**

```bash
curl -k -X POST https://localhost:9443/oauth2/token \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "grant_type=client_credentials" \
  -d "client_id=YOUR_CLIENT_ID" \
  -d "client_secret=YOUR_CLIENT_SECRET" \
  -d "scope=score:write"
```

**Password Grant (for users):**

```bash
curl -k -X POST https://localhost:9443/oauth2/token \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "grant_type=password" \
  -d "username=player1" \
  -d "password=Player@123" \
  -d "client_id=YOUR_CLIENT_ID" \
  -d "client_secret=YOUR_CLIENT_SECRET" \
  -d "scope=score:write game:read"
```

**Response:**
```json
{
  "access_token": "eyJhbGciOiJSUzI1NiIsICJ...",
  "refresh_token": "5c3c7c5f-...",
  "scope": "score:write",
  "token_type": "Bearer",
  "expires_in": 3600
}
```

### Using Access Token

Include the access token in the Authorization header:

```bash
curl -X POST http://localhost:8080/api/v1/scores \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "score": 20,
    "multiplier": "TRIPLE"
  }'
```

## Error Responses

### 400 Bad Request

**Cause:** Invalid request data

**Response:**
```json
{
  "error": "Invalid request",
  "message": "Score must be an integer between 0 and 60"
}
```

### 401 Unauthorized

**Cause:** Missing or invalid access token

**Response:**
```json
{
  "error": "Invalid or expired token",
  "message": "Please obtain a new access token"
}
```

### 403 Forbidden

**Cause:** Insufficient permissions (missing required scope)

**Response:**
```json
{
  "error": "Insufficient permissions",
  "message": "Required scopes: score:write"
}
```

### 500 Internal Server Error

**Cause:** Server-side error

**Response:**
```json
{
  "error": "Internal server error",
  "message": "Unable to publish message to queue"
}
```

## Configuration

### Environment Variables

```bash
# WSO2 Identity Server
WSO2_IS_URL=https://wso2is:9443
WSO2_IS_CLIENT_ID=your_client_id
WSO2_IS_CLIENT_SECRET=your_client_secret

# JWT Validation Mode: 'jwks' or 'introspection'
JWT_VALIDATION_MODE=jwks

# RabbitMQ
RABBITMQ_HOST=rabbitmq
RABBITMQ_PORT=5672
RABBITMQ_USER=guest
RABBITMQ_PASSWORD=guest
RABBITMQ_VHOST=/
RABBITMQ_EXCHANGE=darts_exchange

# API Gateway
API_GATEWAY_HOST=0.0.0.0
API_GATEWAY_PORT=8080

# Flask
FLASK_DEBUG=False
SECRET_KEY=your_secret_key
```

### JWT Validation Modes

**JWKS Mode (Recommended):**
- Validates JWT signature using public keys from JWKS endpoint
- Faster and more efficient
- No network call to WSO2 IS for each request
- Requires JWKS endpoint to be accessible

**Introspection Mode:**
- Validates token by calling WSO2 IS introspection endpoint
- More secure (can check revocation status)
- Requires network call for each request
- Use when JWKS is not available or token revocation is critical

## RabbitMQ Message Publishing

### Score Message

**Exchange:** `darts_exchange`

**Routing Key:** `darts.scores.api`

**Message Format:**
```json
{
  "score": 20,
  "multiplier": "TRIPLE",
  "player_id": "player-123",
  "game_id": "game-456",
  "user": "dartboard-001",
  "timestamp": "2024-01-01T12:00:00.000000"
}
```

### Game Creation Message

**Exchange:** `darts_exchange`

**Routing Key:** `darts.games.create`

**Message Format:**
```json
{
  "action": "new_game",
  "game_type": "301",
  "players": ["Player 1", "Player 2"],
  "double_out": false,
  "created_by": "admin_user",
  "timestamp": "2024-01-01T12:00:00.000000"
}
```

### Player Addition Message

**Exchange:** `darts_exchange`

**Routing Key:** `darts.players.add`

**Message Format:**
```json
{
  "action": "add_player",
  "name": "Player 3",
  "added_by": "admin_user",
  "timestamp": "2024-01-01T12:00:00.000000"
}
```

## Deployment

### Docker Deployment

**Build Image:**
```bash
docker build -f Dockerfile.gateway -t darts-api-gateway .
```

**Run Container:**
```bash
docker run -d \
  --name darts-api-gateway \
  -p 8080:8080 \
  -e WSO2_IS_URL=https://wso2is:9443 \
  -e WSO2_IS_CLIENT_ID=your_client_id \
  -e WSO2_IS_CLIENT_SECRET=your_client_secret \
  -e RABBITMQ_HOST=rabbitmq \
  darts-api-gateway
```

### Docker Compose Deployment

```bash
docker-compose -f docker-compose-wso2.yml up -d api-gateway
```

### Standalone Deployment

**Install Dependencies:**
```bash
pip install -r requirements-gateway.txt
```

**Run Application:**
```bash
python api_gateway.py
```

## Monitoring

### Health Checks

**Endpoint:** `GET /health`

**Use for:**
- Kubernetes liveness/readiness probes
- Load balancer health checks
- Monitoring systems

### Logging

The API Gateway logs:
- All incoming requests
- Authentication attempts
- Token validation results
- RabbitMQ publishing status
- Errors and exceptions

**Log Format:**
```
2024-01-01 12:00:00 - api_gateway - INFO - Token validated for user: dartboard-001
2024-01-01 12:00:01 - api_gateway - INFO - Published message to darts.scores.api: {...}
```

### Metrics

Monitor these metrics:
- Request rate (requests/second)
- Error rate (errors/total requests)
- Response time (p50, p95, p99)
- Token validation time
- RabbitMQ publish success rate

## Security Best Practices

1. **Use HTTPS in Production:**
   - Always use HTTPS for API Gateway
   - Use valid SSL certificates

2. **Secure Token Storage:**
   - Never log access tokens
   - Store tokens securely on client side
   - Clear tokens on logout

3. **Token Expiration:**
   - Implement token refresh logic
   - Handle 401 errors gracefully
   - Request new token when expired

4. **Rate Limiting:**
   - Respect rate limits
   - Implement exponential backoff
   - Cache responses when appropriate

5. **Input Validation:**
   - Validate all input on client side
   - Handle validation errors gracefully
   - Don't trust client-side validation alone

6. **Network Security:**
   - Use private networks for backend services
   - Implement firewall rules
   - Restrict access to management interfaces

## Troubleshooting

### Token Validation Fails

**Symptoms:**
- 401 Unauthorized responses
- "Invalid or expired token" errors

**Solutions:**
1. Check token expiration
2. Verify JWKS endpoint is accessible
3. Try introspection mode
4. Check client credentials
5. Verify token scopes

### RabbitMQ Connection Failed

**Symptoms:**
- 500 Internal Server Error
- "Unable to publish message to queue" errors

**Solutions:**
1. Verify RabbitMQ is running
2. Check network connectivity
3. Verify credentials
4. Check exchange exists
5. Review RabbitMQ logs

### High Latency

**Symptoms:**
- Slow API responses
- Timeouts

**Solutions:**
1. Check RabbitMQ performance
2. Monitor WSO2 IS response time
3. Use JWKS mode instead of introspection
4. Scale API Gateway horizontally
5. Optimize network configuration

## Client Examples

See the following examples:
- Python: `examples/dartboard_client.py`
- Arduino/ESP32: See `docs/WSO2_INTEGRATION.md`
- JavaScript: Coming soon
- Mobile (React Native): Coming soon

## Additional Resources

- [WSO2 Setup Guide](./WSO2_SETUP_GUIDE.md)
- [WSO2 Integration Documentation](./WSO2_INTEGRATION.md)
- [OpenAPI Specification](./api-spec.yaml)
- [Architecture Overview](./ARCHITECTURE.md)

## Support

For issues and questions:
1. Check the troubleshooting section
2. Review logs: `docker logs darts-api-gateway`
3. Consult the documentation
4. Open an issue on the project repository

---

**Version:** 1.0.0  
**Last Updated:** 2024-01-01