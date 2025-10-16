# Darts Game System with WSO2 API Gateway

A complete darts game scoring system with enterprise-grade OAuth2 authentication, API gateway, and real-time messaging.

## 🎯 Features

- **OAuth2 Authentication** - Secure API access using WSO2 Identity Server
- **API Gateway** - RESTful API with token introspection and scope-based authorization
- **Real-time Messaging** - RabbitMQ integration for asynchronous processing
- **Web Interface** - Interactive game board with live score updates
- **Microservices Architecture** - Containerized services with Docker Compose

## 🚀 Quick Start

### Prerequisites

- Docker and Docker Compose
- 8GB RAM minimum
- Ports available: 80, 443, 5000, 5672, 8080, 9443, 9444, 15672

### 1. Start All Services

```bash
docker-compose -f docker-compose-wso2.yml up -d
```

Wait ~2-3 minutes for WSO2 services to fully initialize.

### 2. Verify Deployment

```bash
# Check all services are running
docker-compose -f docker-compose-wso2.yml ps

# Run integration tests
./test-wso2-integration.sh
```

### 3. Access the System

- **Darts Game UI:** <http://localhost:5000>
- **API Gateway:** <http://localhost:8080>
- **RabbitMQ Management:** <http://localhost:15672> (guest/guest)
- **WSO2 Identity Server:** <https://localhost:9443/carbon> (admin/admin)

## 📚 Documentation

### Quick References

- **[Deployment Success Report](docs/DEPLOYMENT_SUCCESS.md)** - Complete deployment details
- **[Quick Reference Guide](docs/QUICK_REFERENCE_WSO2.md)** - Common commands and examples
- **[WSO2 Setup Guide](docs/WSO2_SETUP_GUIDE.md)** - Detailed setup instructions
- **[API Gateway README](docs/API_GATEWAY_README.md)** - API documentation

### Test Scripts

- **`test-wso2-integration.sh`** - Automated integration tests
- **`configure-wso2.sh`** - OAuth2 client configuration
- **`examples/api_client_example.py`** - Python client example

## 🔐 OAuth2 Configuration

### Default Client Credentials

```bash
CLIENT_ID="L2rvop0o4DfJsqpqsh44cUgVn_ga"
CLIENT_SECRET="VhNFUK083Q2iUsu8GCWfcJTVCX8a"
```

### Available Scopes

- `score:write` - Submit dart scores
- `game:write` - Create and manage games
- `player:write` - Add and manage players
- `score:read` - Read score data
- `game:read` - Read game information
- `player:read` - Read player information

## 📡 API Usage

### Get Access Token

```bash
curl -k -X POST https://localhost:9443/oauth2/token \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "grant_type=client_credentials" \
  -d "client_id=L2rvop0o4DfJsqpqsh44cUgVn_ga" \
  -d "client_secret=VhNFUK083Q2iUsu8GCWfcJTVCX8a" \
  -d "scope=score:write"
```

### Submit Score

```bash
curl -X POST http://localhost:8080/api/v1/scores \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "score": 20,
    "multiplier": "TRIPLE",
    "player_id": "player-123",
    "game_id": "game-456"
  }'
```

### Create Game

```bash
curl -X POST http://localhost:8080/api/v1/games \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "game_type": "301",
    "players": ["Player 1", "Player 2"],
    "double_out": false
  }'
```

### Add Player

```bash
curl -X POST http://localhost:8080/api/v1/players \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "New Player"
  }'
```

## 🐍 Python Client Example

```python
from examples.api_client_example import DartsAPIClient

# Initialize client
client = DartsAPIClient()

# Check health
if client.check_health():
    # Submit a score
    result = client.submit_score(
        score=20,
        multiplier="TRIPLE",
        player_id="player-123",
        game_id="game-456"
    )
    print(result)
```

Run the full example:

```bash
python3 examples/api_client_example.py
```

## 🏗️ Architecture

```
┌─────────────────┐
│   API Clients   │
└────────┬────────┘
         │ OAuth2 Token
         ▼
┌─────────────────┐      ┌──────────────────┐
│  API Gateway    │◄────►│ WSO2 Identity    │
│  (Port 8080)    │      │ Server (9443)    │
└────────┬────────┘      └──────────────────┘
         │ Publish
         ▼
┌─────────────────┐
│   RabbitMQ      │
│  (Port 5672)    │
└────────┬────────┘
         │ Consume
         ▼
┌─────────────────┐
│  Darts App      │
│  (Port 5000)    │
└─────────────────┘
```

## 🛠️ Services

| Service                  | Port        | Description                         |
| ------------------------ | ----------- | ----------------------------------- |
| **Darts App**            | 5000        | Main web application with game UI   |
| **API Gateway**          | 8080        | REST API with OAuth2 authentication |
| **RabbitMQ**             | 5672, 15672 | Message broker for async processing |
| **WSO2 Identity Server** | 9443        | OAuth2/OpenID Connect provider      |
| **WSO2API Manager**      | 9444, 8243  | API management and analytics        |
| **Nginx**                | 80, 443     | Reverse proxy (optional)            |

## 🧪 Testing

### Run All Tests

```bash
./test-wso2-integration.sh
```

### Test Individual Endpoints

```bash
# Health check
curl http://localhost:8080/health

# Get token
TOKEN=$(curl -k -s -X POST https://localhost:9443/oauth2/token \
  -d "grant_type=client_credentials" \
  -d "client_id=L2rvop0o4DfJsqpqsh44cUgVn_ga" \
  -d "client_secret=VhNFUK083Q2iUsu8GCWfcJTVCX8a" \
  -d "scope=score:write" | jq -r .access_token)

# Submit score
curl -X POST http://localhost:8080/api/v1/scores \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"score": 20, "multiplier": "TRIPLE"}'
```

## 📊 Monitoring

### View Logs

```bash
# All services
docker-compose -f docker-compose-wso2.yml logs -f

# Specific service
docker-compose -f docker-compose-wso2.yml logs -f api-gateway
```

### Check RabbitMQ

```bash
# Via API
curl -u guest:guest http://localhost:15672/api/queues

# Via Management UI
open http://localhost:15672
```

### Check Service Health

```bash
# API Gateway
curl http://localhost:8080/health

# RabbitMQ
docker exec darts-rabbitmq rabbitmq-diagnostics ping

# WSO2 IS
curl -k https://localhost:9443/carbon
```

## 🔧 Configuration

### Environment Variables

#### API Gateway

```bash
WSO2_IS_URL=https://wso2is:9443
WSO2_IS_CLIENT_ID=your_client_id
WSO2_IS_CLIENT_SECRET=your_client_secret
JWT_VALIDATION_MODE=introspection
RABBITMQ_HOST=rabbitmq
RABBITMQ_EXCHANGE=darts_exchange
```

#### Darts Application

```bash
RABBITMQ_HOST=rabbitmq
RABBITMQ_EXCHANGE=darts_exchange
RABBITMQ_TOPIC=darts.scores.#
FLASK_HOST=0.0.0.0
FLASK_PORT=5000
```

## 🐛 Troubleshooting

### Services Not Starting

```bash
# Check Docker resources
docker stats

# Check logs
docker-compose -f docker-compose-wso2.yml logs

# Restart services
docker-compose -f docker-compose-wso2.yml restart
```

### Token Validation Fails

```bash
# Test introspection endpoint
curl -k -u admin:admin -X POST https://localhost:9443/oauth2/introspect \
  -d "token=YOUR_TOKEN"

# Check API Gateway logs
docker logs darts-api-gateway | grep introspection
```

### RabbitMQ Connection Issues

```bash
# Check RabbitMQ status
docker exec darts-rabbitmq rabbitmq-diagnostics status

# Check exchanges
docker exec darts-rabbitmq rabbitmqctl list_exchanges
```

## 🛑 Stopping Services

```bash
# Stop all services
docker-compose -f docker-compose-wso2.yml down

# Stop and remove volumes
docker-compose -f docker-compose-wso2.yml down -v

# Stop specific service
docker-compose -f docker-compose-wso2.yml stop api-gateway
```

## 📈 Performance

### Typical Response Times

- Token Generation: ~200ms
- Token Introspection: ~150ms
- Score Submission: ~50ms
- Game Creation: ~45ms

### Resource Requirements

- Memory: ~4GB total
- CPU: ~2 cores
- Disk: ~2GB

### Startup Times

- RabbitMQ: ~10 seconds
- WSO2 IS: ~76 seconds
- WSO2 APIM: ~72 seconds
- API Gateway: ~3 seconds
- Darts App: ~3 seconds

## 🔒 Security

### Current Implementation

- ✅ OAuth2 client credentials flow
- ✅ Bearer token authentication
- ✅ Token introspection validation
- ✅ Scope-based authorization
- ✅ Request validation
- ✅ CORS support

### Production Recommendations

1. Use proper SSL certificates (not self-signed)
2. Create dedicated service account for introspection
3. Enable certificate verification
4. Implement rate limiting
5. Add request logging and monitoring
6. Use secrets management (Vault, AWS Secrets Manager)
7. Enable audit logging

## 🚧 Known Limitations

1. **Introspection Credentials:** Using admin credentials. Consider creating a dedicated service account.
2. **Token Type:** Opaque tokens by default. Can be configured for JWT.
3. **SSL Certificates:** Self-signed certificates. Replace with proper certs for production.
4. **Logging:** Not persisted. Add volume mounts or centralized logging.

## 📝 License

[Your License Here]

## 🤝 Contributing

[Your Contributing Guidelines Here]

## 📞 Support

For issues or questions:

1. Check the [Troubleshooting](#-troubleshooting) section
2. Review service logs
3. Consult the [documentation](docs/)
4. Open an issue on GitHub

---

**Status:** ✅ Fully Operational  
**Last Updated:** October 4, 2025  
**Version:** 1.0.0
