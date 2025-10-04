# WSO2 Integration Implementation Summary

## Overview

This document summarizes the implementation of WSO2 Identity Server and API Manager integration for the Darts Game System, providing an enterprise-grade API layer on top of the RabbitMQ message broker.

## What Has Been Implemented

### 1. API Gateway Service (`api_gateway.py`)

A new Flask-based API Gateway service that:
- Validates OAuth2/JWT tokens from WSO2 Identity Server
- Provides REST API endpoints for score submission, game management, and player management
- Publishes validated messages to RabbitMQ
- Implements role-based access control (RBAC)
- Provides comprehensive error handling and logging

**Key Features:**
- JWT validation using JWKS or introspection
- Request validation and sanitization
- RabbitMQ message publishing with automatic reconnection
- Health check endpoint
- Audit logging

### 2. Docker Infrastructure

**New Files:**
- `docker-compose-wso2.yml`: Complete stack with WSO2 IS, WSO2 APIM, API Gateway, RabbitMQ, and Darts App
- `Dockerfile.gateway`: Docker image for API Gateway service
- `requirements-gateway.txt`: Python dependencies for API Gateway
- `nginx/nginx.conf`: Reverse proxy configuration with SSL and rate limiting

**Services Included:**
- WSO2 Identity Server (Port 9443)
- WSO2 API Manager (Ports 9444, 8280, 8243)
- API Gateway (Port 8080)
- RabbitMQ (Ports 5672, 15672)
- Darts Application (Port 5000)
- Nginx Reverse Proxy (Ports 80, 443)

### 3. Documentation

**Comprehensive Guides:**
- `docs/WSO2_SETUP_GUIDE.md`: Step-by-step setup instructions
- `docs/WSO2_INTEGRATION.md`: Integration architecture and details
- `docs/API_GATEWAY_README.md`: API Gateway documentation
- `docs/api-spec.yaml`: OpenAPI 3.0 specification
- `docs/ARCHITECTURE.md`: Updated architecture with WSO2 components

### 4. Client Examples

**Python Client (`examples/dartboard_client.py`):**
- OAuth2 authentication
- Token management with automatic renewal
- Score submission
- Error handling
- Health checks

**Arduino/ESP32 Example:**
- Included in WSO2_INTEGRATION.md
- WiFi connectivity
- OAuth2 token acquisition
- Score submission via HTTP

### 5. Automation Scripts

**Startup Script (`start-wso2-stack.sh`):**
- Automated service startup
- Health checks
- SSL certificate generation
- Resource validation
- Service status display

## Architecture Changes

### Before (Original Architecture)

```
Electronic Dartboard → RabbitMQ → Flask App → WebSocket → Web Clients
Manual Input → REST API → Flask App → WebSocket → Web Clients
```

### After (Enhanced Architecture)

```
Electronic Dartboard → WSO2 APIM → WSO2 IS → API Gateway → RabbitMQ → Flask App → WebSocket → Web Clients
Manual Input → WSO2 APIM → WSO2 IS → API Gateway → RabbitMQ → Flask App → WebSocket → Web Clients
External Apps → WSO2 APIM → WSO2 IS → API Gateway → RabbitMQ → Flask App → WebSocket → Web Clients
```

## Security Enhancements

### Authentication & Authorization

1. **OAuth2 2.0 / OpenID Connect:**
   - Client credentials grant for devices
   - Password grant for users
   - JWT tokens with configurable expiration

2. **Role-Based Access Control:**
   - `dartboard_device`: score:write
   - `game_admin`: Full access
   - `player`: Limited access
   - `spectator`: Read-only access

3. **Scope-Based Authorization:**
   - `score:write`, `score:read`
   - `game:write`, `game:read`
   - `player:write`, `player:read`

### Transport Security

1. **TLS/SSL:**
   - HTTPS for all external communications
   - Certificate-based authentication
   - Nginx SSL termination

2. **Network Segmentation:**
   - Private Docker network
   - Exposed ports only where necessary
   - Backend services isolated

### API Security

1. **Rate Limiting:**
   - Score submission: 100 req/min
   - Game management: 10 req/min
   - Player management: 20 req/min

2. **Input Validation:**
   - Schema validation
   - Type checking
   - Range validation

3. **Audit Logging:**
   - All API requests logged
   - User identification
   - Timestamp tracking

## API Endpoints

### Public Endpoints

| Endpoint | Method | Auth | Description |
|----------|--------|------|-------------|
| `/health` | GET | No | Health check |

### Protected Endpoints

| Endpoint | Method | Scope | Description |
|----------|--------|-------|-------------|
| `/api/v1/scores` | POST | score:write | Submit score |
| `/api/v1/games` | POST | game:write | Create game |
| `/api/v1/players` | POST | player:write | Add player |

## Message Flow

### Score Submission Flow

1. **Client authenticates with WSO2 IS:**
   ```
   POST /oauth2/token
   grant_type=client_credentials
   client_id=xxx
   client_secret=xxx
   ```

2. **WSO2 IS returns JWT token:**
   ```json
   {
     "access_token": "eyJhbGc...",
     "expires_in": 3600
   }
   ```

3. **Client submits score to API Gateway:**
   ```
   POST /api/v1/scores
   Authorization: Bearer eyJhbGc...
   {
     "score": 20,
     "multiplier": "TRIPLE"
   }
   ```

4. **API Gateway validates token and publishes to RabbitMQ:**
   ```
   Exchange: darts_exchange
   Routing Key: darts.scores.api
   Message: {score, multiplier, user, timestamp}
   ```

5. **Flask App consumes message and processes:**
   ```
   RabbitMQ Consumer → Game Manager → Game Logic → WebSocket
   ```

6. **Web clients receive update via WebSocket:**
   ```
   Event: game_state
   Data: {updated game state}
   ```

## Deployment Options

### Development (Local)

```bash
# Start all services
./start-wso2-stack.sh

# Or manually
docker-compose -f docker-compose-wso2.yml up -d
```

### Production

1. **Use external databases:**
   - PostgreSQL for WSO2 IS
   - PostgreSQL for WSO2 APIM
   - Separate RabbitMQ cluster

2. **Scale services:**
   - Multiple API Gateway instances
   - Load balancer (nginx/HAProxy)
   - RabbitMQ clustering

3. **Security hardening:**
   - Valid SSL certificates
   - Strong passwords
   - Network policies
   - Firewall rules

4. **Monitoring:**
   - Prometheus + Grafana
   - ELK stack for logs
   - WSO2 Analytics

## Configuration

### Required Environment Variables

```bash
# WSO2 Identity Server
WSO2_IS_URL=https://wso2is:9443
WSO2_IS_CLIENT_ID=<from_wso2_setup>
WSO2_IS_CLIENT_SECRET=<from_wso2_setup>

# JWT Validation
JWT_VALIDATION_MODE=jwks  # or 'introspection'

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

## Getting Started

### Quick Start (5 Steps)

1. **Start the stack:**
   ```bash
   ./start-wso2-stack.sh
   ```

2. **Wait for services to start (5-10 minutes):**
   ```bash
   docker-compose -f docker-compose-wso2.yml ps
   ```

3. **Configure WSO2 IS:**
   - Follow `docs/WSO2_SETUP_GUIDE.md`
   - Create service provider
   - Configure OAuth2
   - Create users and roles

4. **Configure WSO2 APIM:**
   - Connect to WSO2 IS
   - Publish API
   - Subscribe to API
   - Generate keys

5. **Test the API:**
   ```bash
   # Get token
   curl -k -X POST https://localhost:9443/oauth2/token \
     -d "grant_type=client_credentials" \
     -d "client_id=YOUR_ID" \
     -d "client_secret=YOUR_SECRET"
   
   # Submit score
   curl -X POST http://localhost:8080/api/v1/scores \
     -H "Authorization: Bearer YOUR_TOKEN" \
     -H "Content-Type: application/json" \
     -d '{"score": 20, "multiplier": "TRIPLE"}'
   ```

## Testing

### Manual Testing

1. **Health Check:**
   ```bash
   curl http://localhost:8080/health
   ```

2. **Score Submission:**
   ```bash
   # Get token first
   TOKEN=$(curl -k -X POST https://localhost:9443/oauth2/token \
     -d "grant_type=client_credentials" \
     -d "client_id=YOUR_ID" \
     -d "client_secret=YOUR_SECRET" \
     | jq -r .access_token)
   
   # Submit score
   curl -X POST http://localhost:8080/api/v1/scores \
     -H "Authorization: Bearer $TOKEN" \
     -H "Content-Type: application/json" \
     -d '{"score": 20, "multiplier": "TRIPLE"}'
   ```

3. **Check RabbitMQ:**
   - Open http://localhost:15672
   - Login: guest/guest
   - Check exchanges and queues
   - Verify messages are being published

4. **Check Darts App:**
   - Open http://localhost:5000
   - Verify score appears on game board

### Automated Testing

Create test scripts using the Python client:

```python
from examples.dartboard_client import DartboardClient

client = DartboardClient(
    api_gateway_url="http://localhost:8080",
    wso2_token_url="https://localhost:9443/oauth2/token",
    client_id="YOUR_ID",
    client_secret="YOUR_SECRET"
)

# Test score submission
result = client.submit_score(20, "TRIPLE")
assert result["status"] == "success"
```

## Monitoring & Analytics

### WSO2 API Manager Analytics

Access at: https://localhost:9444/analytics

**Metrics Available:**
- API usage statistics
- Response times
- Error rates
- Top users and applications
- Geographic distribution

### Custom Monitoring

**Recommended Tools:**
- Prometheus for metrics
- Grafana for dashboards
- ELK stack for logs
- Alertmanager for alerts

**Key Metrics to Monitor:**
- API request rate
- Error rate
- Response time (p50, p95, p99)
- Token validation time
- RabbitMQ queue depth
- Service health status

## Troubleshooting

### Common Issues

1. **WSO2 Services Not Starting:**
   - Increase Docker memory (8GB minimum)
   - Wait longer (5-10 minutes)
   - Check logs: `docker logs darts-wso2is`

2. **Token Validation Fails:**
   - Verify JWKS endpoint accessible
   - Check token expiration
   - Try introspection mode
   - Verify client credentials

3. **RabbitMQ Connection Failed:**
   - Check RabbitMQ is running
   - Verify network connectivity
   - Check credentials
   - Review exchange configuration

4. **Certificate Errors:**
   - Accept self-signed certificates in browser
   - Use proper certificates in production
   - Configure certificate trust store

### Debug Commands

```bash
# Check service status
docker-compose -f docker-compose-wso2.yml ps

# View logs
docker-compose -f docker-compose-wso2.yml logs -f api-gateway
docker-compose -f docker-compose-wso2.yml logs -f wso2is
docker-compose -f docker-compose-wso2.yml logs -f rabbitmq

# Restart service
docker-compose -f docker-compose-wso2.yml restart api-gateway

# Check network
docker network inspect darts-network

# Test RabbitMQ
docker exec darts-rabbitmq rabbitmq-diagnostics ping
```

## Migration Path

### Phase 1: API Gateway (Week 1)
- Deploy API Gateway service
- Configure RabbitMQ publisher
- Test score submission flow
- No client changes required yet

### Phase 2: WSO2 IS Setup (Week 2)
- Deploy WSO2 Identity Server
- Configure OAuth2 provider
- Create service accounts
- Implement JWT validation
- Test authentication flow

### Phase 3: WSO2 APIM Integration (Week 3)
- Deploy WSO2 API Manager
- Publish APIs to developer portal
- Configure rate limiting
- Enable analytics
- Create documentation

### Phase 4: Client Migration (Week 4)
- Update electronic dartboard firmware
- Implement OAuth2 flow in clients
- Update web clients (optional)
- Migrate existing integrations
- Decommission old endpoints

## Benefits

### Security
- ✅ Centralized authentication
- ✅ Token-based authorization
- ✅ Role-based access control
- ✅ Audit logging
- ✅ Rate limiting

### Scalability
- ✅ Horizontal scaling of API Gateway
- ✅ Load balancing support
- ✅ Caching capabilities
- ✅ Message queue decoupling

### Manageability
- ✅ Developer portal
- ✅ API documentation
- ✅ Usage analytics
- ✅ Subscription management
- ✅ Version management

### Developer Experience
- ✅ Self-service API access
- ✅ Interactive API console
- ✅ Code examples
- ✅ Comprehensive documentation
- ✅ Standardized REST API

## Next Steps

1. **Review Documentation:**
   - Read `docs/WSO2_SETUP_GUIDE.md`
   - Review `docs/API_GATEWAY_README.md`
   - Check `docs/api-spec.yaml`

2. **Deploy Services:**
   - Run `./start-wso2-stack.sh`
   - Wait for services to start
   - Verify all services are healthy

3. **Configure WSO2:**
   - Follow setup guide
   - Create service provider
   - Configure OAuth2
   - Create test users

4. **Test Integration:**
   - Use Python client example
   - Test all API endpoints
   - Verify RabbitMQ messages
   - Check game board updates

5. **Update Clients:**
   - Implement OAuth2 in dartboard firmware
   - Update mobile apps
   - Migrate existing integrations

## Support & Resources

### Documentation
- [WSO2 Setup Guide](./WSO2_SETUP_GUIDE.md)
- [WSO2 Integration](./WSO2_INTEGRATION.md)
- [API Gateway README](./API_GATEWAY_README.md)
- [OpenAPI Specification](./api-spec.yaml)
- [Architecture Overview](./ARCHITECTURE.md)

### External Resources
- [WSO2 IS Documentation](https://is.docs.wso2.com/)
- [WSO2 APIM Documentation](https://apim.docs.wso2.com/)
- [OAuth 2.0 Specification](https://oauth.net/2/)
- [JWT.io](https://jwt.io/)

### Getting Help
1. Check troubleshooting sections
2. Review service logs
3. Consult documentation
4. Open issue on project repository

---

**Implementation Date:** 2024-01-01  
**Version:** 1.0.0  
**Status:** Complete and Ready for Testing