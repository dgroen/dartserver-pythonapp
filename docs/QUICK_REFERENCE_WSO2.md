# WSO2 Integration Quick Reference

## Quick Start Commands

```bash
# Start all services
./start-wso2-stack.sh

# Check service status
docker-compose -f docker-compose-wso2.yml ps

# View logs
docker-compose -f docker-compose-wso2.yml logs -f [service_name]

# Stop all services
docker-compose -f docker-compose-wso2.yml down

# Restart a service
docker-compose -f docker-compose-wso2.yml restart [service_name]
```

## Service URLs

| Service             | URL                                | Credentials |
| ------------------- | ---------------------------------- | ----------- |
| RabbitMQ Management | <http://localhost:15672>           | guest/guest |
| WSO2 IS Console     | <https://localhost:9443/carbon>    | admin/admin |
| WSO2 APIM Publisher | <https://localhost:9444/publisher> | admin/admin |
| WSO2 APIM DevPortal | <https://localhost:9444/devportal> | admin/admin |
| API Gateway         | <http://localhost:8080>            | -           |
| Darts App           | <http://localhost:5000>            | -           |

## API Endpoints

### Health Check

```bash
curl http://localhost:8080/health
```

### Get Access Token

```bash
curl -k -X POST https://localhost:9443/oauth2/token \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "grant_type=client_credentials" \
  -d "client_id=YOUR_CLIENT_ID" \
  -d "client_secret=YOUR_CLIENT_SECRET" \
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
    "name": "Player 3"
  }'
```

## OAuth2 Scopes

| Scope          | Description         | Required Role                        |
| -------------- | ------------------- | ------------------------------------ |
| `score:write`  | Submit scores       | dartboard_device, game_admin, player |
| `score:read`   | Read scores         | game_admin                           |
| `game:write`   | Create/manage games | game_admin                           |
| `game:read`    | Read game info      | game_admin, player, spectator        |
| `player:write` | Add/manage players  | game_admin                           |
| `player:read`  | Read player info    | game_admin, player                   |

## User Roles

| Role               | Scopes                              |
| ------------------ | ----------------------------------- |
| `dartboard_device` | score:write                         |
| `game_admin`       | All scopes                          |
| `player`           | score:write, game:read, player:read |
| `spectator`        | game:read                           |

## Environment Variables

```bash
# WSO2 Identity Server
WSO2_IS_URL=https://wso2is:9443
WSO2_IS_CLIENT_ID=your_client_id
WSO2_IS_CLIENT_SECRET=your_client_secret

# JWT Validation Mode
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
```

## Common Issues & Solutions

### Token Validation Fails

```bash
# Check JWKS endpoint
curl -k https://localhost:9443/oauth2/jwks

# Try introspection mode
export JWT_VALIDATION_MODE=introspection
docker-compose -f docker-compose-wso2.yml restart api-gateway
```

### RabbitMQ Connection Failed

```bash
# Check RabbitMQ status
docker exec darts-rabbitmq rabbitmq-diagnostics ping

# Check exchange
docker exec darts-rabbitmq rabbitmqctl list_exchanges
```

### WSO2 Not Starting

```bash
# Check logs
docker logs darts-wso2is
docker logs darts-wso2apim

# Increase memory and restart
docker-compose -f docker-compose-wso2.yml down
docker-compose -f docker-compose-wso2.yml up -d
```

## Python Client Example

```python
from examples.dartboard_client import DartboardClient

# Initialize client
client = DartboardClient(
    api_gateway_url="http://localhost:8080",
    wso2_token_url="https://localhost:9443/oauth2/token",
    client_id="YOUR_CLIENT_ID",
    client_secret="YOUR_CLIENT_SECRET"
)

# Check health
if client.check_health():
    # Submit score
    result = client.submit_score(
        score=20,
        multiplier="TRIPLE",
        player_id="player-123",
        game_id="game-456"
    )
    print(result)
```

## RabbitMQ Routing Keys

| Action           | Routing Key          |
| ---------------- | -------------------- |
| Score submission | `darts.scores.api`   |
| Game creation    | `darts.games.create` |
| Player addition  | `darts.players.add`  |

## Rate Limits

| Endpoint             | Limit       |
| -------------------- | ----------- |
| POST /api/v1/scores  | 100 req/min |
| POST /api/v1/games   | 10 req/min  |
| POST /api/v1/players | 20 req/min  |

## Validation Rules

### Score Submission

- `score`: Integer, 0-60
- `multiplier`: "SINGLE", "DOUBLE", or "TRIPLE"
- `player_id`: Optional string
- `game_id`: Optional string

### Game Creation

- `game_type`: "301", "401", "501", or "cricket"
- `players`: Array, minimum 1 player
- `double_out`: Boolean, optional

### Player Addition

- `name`: Non-empty string

## HTTP Status Codes

| Code | Meaning               |
| ---- | --------------------- |
| 200  | Success               |
| 201  | Created               |
| 400  | Bad Request           |
| 401  | Unauthorized          |
| 403  | Forbidden             |
| 404  | Not Found             |
| 500  | Internal Server Error |

## Useful Docker Commands

```bash
# View all containers
docker ps -a

# View container logs
docker logs -f darts-api-gateway

# Execute command in container
docker exec -it darts-api-gateway bash

# Check container resource usage
docker stats

# Remove all stopped containers
docker container prune

# Remove all unused volumes
docker volume prune
```

## Testing Checklist

- [ ] All services started successfully
- [ ] Health check returns 200
- [ ] Can obtain access token
- [ ] Can submit score with valid token
- [ ] Score appears in RabbitMQ
- [ ] Score appears on game board
- [ ] Invalid token returns 401
- [ ] Missing scope returns 403
- [ ] Invalid data returns 400

## Documentation Links

- [WSO2 Setup Guide](./WSO2_SETUP_GUIDE.md)
- [WSO2 Integration](./WSO2_INTEGRATION.md)
- [API Gateway README](./API_GATEWAY_README.md)
- [OpenAPI Spec](./api-spec.yaml)
- [Architecture](./ARCHITECTURE.md)
- [Implementation Summary](./WSO2_IMPLEMENTATION_SUMMARY.md)

## Support

1. Check troubleshooting sections in documentation
2. Review service logs
3. Verify configuration
4. Test with curl commands
5. Check network connectivity
6. Open issue if problem persists

---

**Quick Reference Version:** 1.0.0
