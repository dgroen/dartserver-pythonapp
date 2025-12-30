# API Gateway

Secure REST API Gateway for the Darts Game System with OAuth2 authentication.

## Overview

The API Gateway provides a secure, authenticated interface for:
- **Dartboard Hardware**: Submit throws using client credentials OAuth2 flow
- **Game Management**: Create and control games
- **Score Submission**: Manual or automated score entry
- **Multi-Game Support**: Handle multiple concurrent games

This service is designed to be managed and exposed through WSO2 API Manager.

## Features

- ✅ **OAuth2 Authentication**: Secure client credentials and authorization code flows
- ✅ **Scope-Based Authorization**: Fine-grained permission control
- ✅ **OpenAPI 3.0 Specification**: Complete API documentation
- ✅ **Swagger UI**: Interactive API documentation at `/docs`
- ✅ **RabbitMQ Integration**: Publish events to message queue
- ✅ **Token Validation**: JWT signature verification via JWKS or introspection
- ✅ **Health Monitoring**: Health check endpoint at `/health`
- ✅ **CORS Support**: Cross-origin requests enabled

## Quick Start

### 1. Prerequisites

- Python 3.10+
- RabbitMQ server running
- WSO2 Identity Server configured
- Client credentials (client_id and client_secret)

### 2. Installation

```bash
# Install dependencies
pip install -r requirements-gateway.txt

# Configure environment
cp .env.example .env
# Edit .env with your WSO2 and RabbitMQ settings
```

### 3. Configuration

Edit `.env` file:

```env
# WSO2 Identity Server
WSO2_IS_URL=https://wso2-is:9443
WSO2_IS_CLIENT_ID=your_client_id
WSO2_IS_CLIENT_SECRET=your_client_secret
WSO2_IS_VERIFY_SSL=false

# JWT Validation
JWT_VALIDATION_MODE=introspection  # or 'jwks'
WSO2_IS_INTROSPECT_USER=admin
WSO2_IS_INTROSPECT_PASSWORD=admin

# RabbitMQ
RABBITMQ_HOST=localhost
RABBITMQ_PORT=5672
RABBITMQ_USER=guest
RABBITMQ_PASSWORD=guest
RABBITMQ_EXCHANGE=darts_exchange

# API Gateway
API_GATEWAY_HOST=0.0.0.0
API_GATEWAY_PORT=8080
FLASK_DEBUG=false
```

### 4. Run the Gateway

```bash
# Development
python api_gateway.py

# With Docker
docker build -f Dockerfile.gateway -t darts-api-gateway .
docker run -p 8080:8080 --env-file .env darts-api-gateway
```

### 5. Access Documentation

- **Swagger UI**: http://localhost:8080/docs
- **OpenAPI Spec (YAML)**: http://localhost:8080/api/v1/openapi.yaml
- **OpenAPI Spec (JSON)**: http://localhost:8080/api/v1/openapi.json
- **Health Check**: http://localhost:8080/health

## API Endpoints

### Public Endpoints (No Authentication)

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/health` | Health check |
| GET | `/docs` | Swagger UI documentation |
| GET | `/api/v1/openapi.yaml` | OpenAPI specification (YAML) |
| GET | `/api/v1/openapi.json` | OpenAPI specification (JSON) |

### Authenticated Endpoints

#### Dartboard (Requires `dartboard:write` scope)

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/v1/dartboard/throw` | Submit dartboard throw (pins) |

**Example:**
```bash
curl -X POST http://localhost:8080/api/v1/dartboard/throw \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "masterPin": 4,
    "slavePin": 13,
    "boardType": "carromco"
  }'
```

#### Scores (Requires `score:write` scope)

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/v1/scores` | Submit manual score |

**Example:**
```bash
curl -X POST http://localhost:8080/api/v1/scores \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "score": 20,
    "multiplier": "TRIPLE"
  }'
```

#### Games (Requires `game:write` scope)

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/v1/games` | Create new game |

**Example:**
```bash
curl -X POST http://localhost:8080/api/v1/games \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "game_type": "301",
    "players": ["Alice", "Bob"],
    "double_out": false
  }'
```

#### Players (Requires `player:write` scope)

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/v1/players` | Add player to game |

#### Game Actions (Requires `game:control` scope)

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/v1/game/actions/end-turn` | End current turn |
| POST | `/api/v1/game/actions/continue` | Continue game |
| POST | `/api/v1/game/actions/pause` | Pause game |

## Authentication

### Client Credentials Flow (for Dartboards)

1. **Obtain Access Token**
```bash
curl -X POST https://wso2-is:9443/oauth2/token \
  -u "CLIENT_ID:CLIENT_SECRET" \
  -d "grant_type=client_credentials&scope=dartboard:write"
```

2. **Use Access Token**
```bash
curl -X POST http://localhost:8080/api/v1/dartboard/throw \
  -H "Authorization: Bearer ACCESS_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"masterPin":4,"slavePin":13,"boardType":"carromco"}'
```

### Token Management

- Tokens expire after the time specified in `expires_in` (typically 3600 seconds)
- Refresh tokens before expiration (recommended: 60 seconds before)
- Handle 401 responses by obtaining a new token

## OAuth2 Scopes

| Scope | Description | Used By |
|-------|-------------|---------|
| `dartboard:write` | Submit dartboard throws | Dartboard hardware |
| `score:write` | Submit scores | Manual entry, testing |
| `game:write` | Create and manage games | Game management |
| `game:control` | Control game flow | UI, automation |
| `player:write` | Add players | Game setup |

## Testing

### Unit Tests

```bash
# Run all API Gateway tests
pytest tests/unit/test_api_gateway.py -v

# Run specific test class
pytest tests/unit/test_api_gateway.py::TestDartboardEndpoint -v
```

### Integration Tests

```bash
# Run integration tests
pytest tests/integration/test_api_gateway_integration.py -v

# Test multi-game scenarios
pytest tests/integration/test_api_gateway_integration.py::TestMultiGameScenarios -v
```

### Dartboard Simulator

Use the included simulator for testing:

```bash
# Single throw
python scripts/dartboard_simulator.py \
  --client-id dartboard_001 \
  --client-secret YOUR_SECRET \
  --gateway-url http://localhost:8080

# Simulate complete game
python scripts/dartboard_simulator.py \
  --simulate-game \
  --num-rounds 10

# Multiple concurrent dartboards
python scripts/dartboard_simulator.py \
  --concurrent-boards 5

# Continuous testing
python scripts/dartboard_simulator.py --continuous
```

## Deployment

### Docker

```bash
# Build
docker build -f Dockerfile.gateway -t darts-api-gateway:latest .

# Run
docker run -d \
  --name darts-api-gateway \
  -p 8080:8080 \
  --env-file .env \
  darts-api-gateway:latest
```

### Docker Compose

```yaml
services:
  api-gateway:
    build:
      context: .
      dockerfile: Dockerfile.gateway
    ports:
      - "8080:8080"
    environment:
      - WSO2_IS_URL=${WSO2_IS_URL}
      - RABBITMQ_HOST=rabbitmq
      - JWT_VALIDATION_MODE=introspection
    depends_on:
      - rabbitmq
```

### Production Deployment

For production:
1. Configure HTTPS
2. Set `WSO2_IS_VERIFY_SSL=true`
3. Use production credentials
4. Configure proper logging
5. Set up monitoring and alerts
6. Use WSO2 APIM as reverse proxy

See [WSO2 APIM Configuration Guide](../doc/WSO2_APIM_CONFIGURATION.md) for details.

## Monitoring

### Health Check

```bash
curl http://localhost:8080/health
```

Response:
```json
{
  "status": "healthy",
  "service": "darts-api-gateway",
  "timestamp": "2024-01-15T10:30:00Z"
}
```

### Logs

The gateway logs all requests and errors. Configure logging in your environment:

```env
FLASK_DEBUG=true  # Enable debug logging
```

## Troubleshooting

### Common Issues

**Problem**: Token validation fails
- **Solution**: Check WSO2 IS URL and credentials
- Verify JWKS endpoint is accessible
- Check token hasn't expired

**Problem**: RabbitMQ connection failed
- **Solution**: Verify RabbitMQ is running
- Check RABBITMQ_HOST and credentials
- Ensure exchange exists

**Problem**: CORS errors
- **Solution**: CORS is enabled by default
- Check allowed origins in CORS configuration

**Problem**: 401 Unauthorized
- **Solution**: Ensure valid Bearer token in Authorization header
- Check token has required scopes
- Verify token hasn't expired

## Development

### Project Structure

```
src/api_gateway/
├── __init__.py
├── app.py              # Main application
└── openapi.yaml        # API specification

tests/
├── unit/
│   └── test_api_gateway.py
└── integration/
    └── test_api_gateway_integration.py

scripts/
└── dartboard_simulator.py
```

### Adding New Endpoints

1. Define endpoint in `app.py`
2. Add `@require_auth` decorator with required scopes
3. Update `openapi.yaml` with endpoint documentation
4. Add tests in `tests/unit/test_api_gateway.py`
5. Update this README

## Documentation

- [WSO2 APIM Configuration](../doc/WSO2_APIM_CONFIGURATION.md)
- [Dartboard Client Integration](../doc/DARTBOARD_CLIENT_INTEGRATION.md)
- [OpenAPI Specification](openapi.yaml)
- [Architecture Overview](../doc/ARCHITECTURE.md)

## Security

- All endpoints except `/health` and `/docs` require OAuth2 authentication
- Tokens are validated via JWKS or introspection
- Scope-based authorization enforced
- HTTPS required in production
- Rate limiting managed by WSO2 APIM

## Contributing

1. Follow existing code structure
2. Add tests for new features
3. Update OpenAPI specification
4. Update documentation
5. Run linters before committing

## Support

- Issues: GitHub Issues
- Documentation: `/docs` endpoint
- API Reference: OpenAPI specification

## License

See main project LICENSE file.
