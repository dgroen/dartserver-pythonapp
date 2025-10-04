# WSO2 Integration for Darts Game System

## Overview

This document describes the integration of WSO2 Identity Server (IS) and WSO2 API Manager (APIM) with the Darts Game System to provide enterprise-grade security, API management, and developer portal capabilities.

## Architecture Components

### 1. WSO2 Identity Server (WSO2 IS)
- **Purpose:** Centralized identity and access management
- **Port:** 9443 (HTTPS)
- **Features:**
  - OAuth2 2.0 / OpenID Connect provider
  - User authentication and authorization
  - JWT token generation and validation
  - Role-based access control (RBAC)
  - Multi-factor authentication support

### 2. WSO2 API Manager (WSO2 APIM)
- **Purpose:** API lifecycle management and developer portal
- **Ports:** 
  - 9444 (Publisher/DevPortal)
  - 8280 (HTTP Gateway)
  - 8243 (HTTPS Gateway)
- **Features:**
  - API design and publishing
  - Developer portal with API documentation
  - Rate limiting and throttling
  - API analytics and monitoring
  - Subscription management

### 3. API Gateway Service
- **Purpose:** Secure REST API for score submission and game management
- **Port:** 8080
- **Features:**
  - JWT token validation
  - Request validation and sanitization
  - RabbitMQ message publishing
  - Audit logging
  - Error handling

## Authentication Flow

```
┌─────────────┐
│   Client    │
│ (Dartboard/ │
│  Mobile App)│
└──────┬──────┘
       │
       │ 1. Request Access Token
       │    POST /oauth2/token
       │    grant_type=client_credentials
       │    client_id=xxx
       │    client_secret=xxx
       │    scope=score:write
       │
       ▼
┌─────────────────────┐
│  WSO2 Identity      │
│  Server             │
│                     │
│  - Validate creds   │
│  - Generate JWT     │
│  - Return token     │
└──────┬──────────────┘
       │
       │ 2. Access Token Response
       │    {
       │      "access_token": "eyJhbGc...",
       │      "token_type": "Bearer",
       │      "expires_in": 3600
       │    }
       │
       ▼
┌─────────────┐
│   Client    │
│             │
│ Store token │
└──────┬──────┘
       │
       │ 3. API Request with Token
       │    POST /api/v1/scores
       │    Authorization: Bearer eyJhbGc...
       │    {
       │      "score": 20,
       │      "multiplier": "TRIPLE"
       │    }
       │
       ▼
┌─────────────────────┐
│  API Gateway        │
│                     │
│  - Extract token    │
│  - Validate JWT     │
│  - Check scopes     │
│  - Process request  │
└──────┬──────────────┘
       │
       │ 4. Publish to RabbitMQ
       │    Exchange: darts_exchange
       │    Routing: darts.scores.api
       │
       ▼
┌─────────────────────┐
│  RabbitMQ Broker    │
└─────────────────────┘
```

## Security Model

### User Roles

| Role | Description | Scopes |
|------|-------------|--------|
| `dartboard_device` | Electronic dartboard devices | `score:write` |
| `game_admin` | Game administrators | `score:write`, `score:read`, `game:write`, `game:read`, `player:write`, `player:read` |
| `player` | Regular players | `score:write`, `game:read`, `player:read` |
| `spectator` | Read-only access | `game:read` |

### OAuth2 Scopes

| Scope | Description | Required Role |
|-------|-------------|---------------|
| `score:write` | Submit scores | dartboard_device, game_admin, player |
| `score:read` | Read score information | game_admin |
| `game:write` | Create and manage games | game_admin |
| `game:read` | Read game information | game_admin, player, spectator |
| `player:write` | Add and manage players | game_admin |
| `player:read` | Read player information | game_admin, player |

### Token Types

**Client Credentials Grant:**
- Used by: Electronic dartboards, automated systems
- Lifetime: 1 hour (configurable)
- Refresh: Automatic on expiry

**Password Grant:**
- Used by: Mobile apps, web applications
- Lifetime: 1 hour (configurable)
- Refresh: Using refresh token

## API Endpoints

### Health Check
```
GET /health
```
No authentication required. Returns service health status.

### Score Submission
```
POST /api/v1/scores
Authorization: Bearer <token>
Content-Type: application/json

{
  "score": 20,
  "multiplier": "TRIPLE",
  "player_id": "player-123",
  "game_id": "game-456"
}
```

**Required Scope:** `score:write`

**Rate Limit:** 100 requests/minute

### Game Creation
```
POST /api/v1/games
Authorization: Bearer <token>
Content-Type: application/json

{
  "game_type": "301",
  "players": ["Player 1", "Player 2"],
  "double_out": false
}
```

**Required Scope:** `game:write`

**Rate Limit:** 10 requests/minute

### Player Addition
```
POST /api/v1/players
Authorization: Bearer <token>
Content-Type: application/json

{
  "name": "Player 3"
}
```

**Required Scope:** `player:write`

**Rate Limit:** 20 requests/minute

## Message Format

### Score Message (Published to RabbitMQ)
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

**Routing Key:** `darts.scores.api`

### Game Creation Message
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

**Routing Key:** `darts.games.create`

### Player Addition Message
```json
{
  "action": "add_player",
  "name": "Player 3",
  "added_by": "admin_user",
  "timestamp": "2024-01-01T12:00:00.000000"
}
```

**Routing Key:** `darts.players.add`

## Deployment

### Quick Start

1. **Start all services:**
```bash
docker-compose -f docker-compose-wso2.yml up -d
```

2. **Wait for services to start:**
```bash
# Check service status
docker-compose -f docker-compose-wso2.yml ps

# Watch logs
docker-compose -f docker-compose-wso2.yml logs -f
```

3. **Access WSO2 consoles:**
- WSO2 IS: https://localhost:9443/carbon (admin/admin)
- WSO2 APIM Publisher: https://localhost:9444/publisher (admin/admin)
- WSO2 APIM DevPortal: https://localhost:9444/devportal (admin/admin)

4. **Configure WSO2 (see WSO2_SETUP_GUIDE.md)**

5. **Test API Gateway:**
```bash
curl http://localhost:8080/health
```

### Environment Variables

**API Gateway:**
```bash
# WSO2 Identity Server
WSO2_IS_URL=https://wso2is:9443
WSO2_IS_CLIENT_ID=<your_client_id>
WSO2_IS_CLIENT_SECRET=<your_client_secret>

# JWT Validation Mode: 'jwks' or 'introspection'
JWT_VALIDATION_MODE=jwks

# RabbitMQ
RABBITMQ_HOST=rabbitmq
RABBITMQ_PORT=5672
RABBITMQ_USER=guest
RABBITMQ_PASSWORD=guest
RABBITMQ_EXCHANGE=darts_exchange

# API Gateway
API_GATEWAY_HOST=0.0.0.0
API_GATEWAY_PORT=8080

# Security
SECRET_KEY=<generate_strong_random_key>
```

## Client Integration

### Python Client Example

See `examples/dartboard_client.py` for a complete example.

```python
from dartboard_client import DartboardClient

# Initialize client
client = DartboardClient(
    api_gateway_url="http://localhost:8080",
    wso2_token_url="https://localhost:9443/oauth2/token",
    client_id="your_client_id",
    client_secret="your_client_secret"
)

# Submit score
result = client.submit_score(
    score=20,
    multiplier="TRIPLE",
    player_id="player-123",
    game_id="game-456"
)
```

### Arduino/ESP32 Example

```cpp
#include <WiFi.h>
#include <HTTPClient.h>
#include <ArduinoJson.h>

const char* ssid = "your_wifi_ssid";
const char* password = "your_wifi_password";
const char* tokenUrl = "https://your-wso2-is/oauth2/token";
const char* apiUrl = "http://your-api-gateway:8080/api/v1/scores";
const char* clientId = "your_client_id";
const char* clientSecret = "your_client_secret";

String accessToken = "";

void setup() {
  Serial.begin(115200);
  WiFi.begin(ssid, password);
  
  while (WiFi.status() != WL_CONNECTED) {
    delay(1000);
    Serial.println("Connecting to WiFi...");
  }
  
  Serial.println("Connected to WiFi");
  getAccessToken();
}

void getAccessToken() {
  HTTPClient http;
  http.begin(tokenUrl);
  http.addHeader("Content-Type", "application/x-www-form-urlencoded");
  
  String auth = String(clientId) + ":" + String(clientSecret);
  String authEncoded = base64::encode(auth);
  http.addHeader("Authorization", "Basic " + authEncoded);
  
  String payload = "grant_type=client_credentials&scope=score:write";
  int httpCode = http.POST(payload);
  
  if (httpCode == 200) {
    String response = http.getString();
    DynamicJsonDocument doc(1024);
    deserializeJson(doc, response);
    accessToken = doc["access_token"].as<String>();
    Serial.println("Access token obtained");
  }
  
  http.end();
}

void submitScore(int score, String multiplier) {
  HTTPClient http;
  http.begin(apiUrl);
  http.addHeader("Content-Type", "application/json");
  http.addHeader("Authorization", "Bearer " + accessToken);
  
  DynamicJsonDocument doc(256);
  doc["score"] = score;
  doc["multiplier"] = multiplier;
  doc["player_id"] = "dartboard-001";
  
  String payload;
  serializeJson(doc, payload);
  
  int httpCode = http.POST(payload);
  
  if (httpCode == 201) {
    Serial.println("Score submitted successfully");
  } else if (httpCode == 401) {
    // Token expired, get new one
    getAccessToken();
    submitScore(score, multiplier);
  }
  
  http.end();
}

void loop() {
  // Detect dart hit and submit score
  // This is a simplified example
  submitScore(20, "TRIPLE");
  delay(5000);
}
```

## Monitoring and Analytics

### WSO2 API Manager Analytics

Access analytics dashboard:
- URL: https://localhost:9444/analytics
- Metrics available:
  - API usage statistics
  - Response times
  - Error rates
  - Top users and applications
  - Geographic distribution

### Custom Metrics

The API Gateway logs all requests with:
- Timestamp
- User/client identifier
- Endpoint accessed
- Response status
- Processing time

Logs can be aggregated using ELK stack or similar tools.

## Troubleshooting

### Common Issues

**1. Token Validation Fails**
- Verify JWKS endpoint is accessible
- Check token expiration
- Ensure scopes match requirements
- Try introspection mode instead of JWKS

**2. RabbitMQ Connection Failed**
- Verify RabbitMQ is running
- Check network connectivity
- Verify credentials

**3. WSO2 Services Not Starting**
- Increase Docker memory limit (minimum 8GB)
- Wait longer for startup (3-5 minutes)
- Check logs for errors

**4. Certificate Errors**
- For development, SSL verification is disabled
- For production, use proper certificates
- Add WSO2 certificates to trusted store

## Best Practices

### Security
1. Use strong, unique passwords for all services
2. Enable HTTPS for all communications
3. Rotate client secrets regularly
4. Implement rate limiting
5. Monitor for suspicious activity
6. Use network segmentation

### Performance
1. Cache access tokens until expiry
2. Use connection pooling for RabbitMQ
3. Implement exponential backoff for retries
4. Monitor and optimize database queries
5. Scale services horizontally as needed

### Reliability
1. Implement health checks
2. Use circuit breakers for external calls
3. Handle token expiration gracefully
4. Implement message persistence in RabbitMQ
5. Set up monitoring and alerting

## Additional Resources

- [WSO2 Identity Server Documentation](https://is.docs.wso2.com/)
- [WSO2 API Manager Documentation](https://apim.docs.wso2.com/)
- [OAuth 2.0 RFC](https://tools.ietf.org/html/rfc6749)
- [JWT RFC](https://tools.ietf.org/html/rfc7519)
- [OpenAPI Specification](./api-spec.yaml)
- [Setup Guide](./WSO2_SETUP_GUIDE.md)

## Support

For issues and questions:
1. Check the troubleshooting section
2. Review WSO2 documentation
3. Check Docker logs: `docker-compose -f docker-compose-wso2.yml logs`
4. Consult the project's issue tracker

---

**Last Updated:** 2024-01-01