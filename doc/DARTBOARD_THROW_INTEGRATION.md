# Dartboard Throw Integration

## Overview

The dartboard hardware integration uses OAuth2-authenticated API Gateway to securely submit throw data, which is then routed through RabbitMQ to the main Flask application for game processing.

## Architecture Flow

```
Dartboard Hardware
    ↓ (OAuth2 Client Credentials)
    ↓ POST /api/v1/dartboard/throw
API Gateway (Port 8080)
    ↓ (Validates JWT token & scopes)
    ↓ Publishes to RabbitMQ
RabbitMQ Exchange: darts_exchange
    ↓ Routing Key: darts.dartboard.throw
Flask App Consumer
    ↓ Maps GPIO pins → Score
    ↓ Processes through Game Manager
Game State Update → WebSocket Broadcast
```

## Message Flow

### 1. Dartboard Submits Throw

**Endpoint:** `POST /api/v1/dartboard/throw`

**Headers:**
```
Authorization: Bearer <access_token>
Content-Type: application/json
```

**Request Body:**
```json
{
  "masterPin": 4,
  "slavePin": 13,
  "boardType": "carromco"
}
```

**Response (201 Created):**
```json
{
  "status": "success",
  "message": "Throw submitted successfully",
  "data": {
    "masterPin": 4,
    "slavePin": 13,
    "boardType": "carromco",
    "client_id": "dartboard_001_client",
    "timestamp": "2025-12-29T10:15:30.123Z"
  }
}
```

### 2. API Gateway Publishes to RabbitMQ

**Exchange:** `darts_exchange`  
**Routing Key:** `darts.dartboard.throw`

**Message:**
```json
{
  "masterPin": 4,
  "slavePin": 13,
  "boardType": "carromco",
  "client_id": "dartboard_001_client",
  "timestamp": "2025-12-29T10:15:30.123Z"
}
```

### 3. Flask App Consumes & Processes

The RabbitMQ consumer in the Flask app:

1. **Receives the message** on topic `darts.#` (listening to all darts topics)
2. **Routes to handler** - detects `masterPin`/`slavePin` → calls `on_dartboard_throw_received()`
3. **Maps GPIO pins to score** using `DartboardService.get_zone_from_pins()`
4. **Converts to score format:**
   ```python
   {
       "score": 20,        # base_value from zone mapping
       "multiplier": "TRIPLE"  # multiplier_type from zone mapping
   }
   ```
5. **Processes through Game Manager** - updates game state, calculates points, checks for winner
6. **Broadcasts via WebSocket** - all connected clients receive updated game state

## RabbitMQ Configuration

### Environment Variables

```bash
# Listen to all darts topics (scores, dartboard throws, etc.)
RABBITMQ_TOPIC=darts.#
```

### Topic Routing

- `darts.scores.#` - Manual score submissions (legacy)
- `darts.dartboard.throw` - Hardware dartboard throws (GPIO pin data)
- `darts.#` - All darts-related messages (recommended for consumer)

## Code Components

### API Gateway Publisher
Location: `src/api_gateway/app.py`

```python
@app.route("/api/v1/dartboard/throw", methods=["POST"])
@require_auth(required_scopes=["dartboard:write"])
def dartboard_throw():
    # Validates token & publishes to RabbitMQ
    routing_key = "darts.dartboard.throw"
    rabbitmq_publisher.publish(routing_key, message)
```

### Flask App Consumer
Location: `src/app/app.py`

```python
def on_dartboard_throw_received(throw_data):
    """Maps GPIO pins to score and processes through game manager"""
    zone_info = DartboardService.get_zone_from_pins(
        session, board_type, master_pin, slave_pin
    )
    score_data = {
        "score": zone_info["base_value"],
        "multiplier": zone_info["multiplier_type"],
    }
    app.game_manager.process_score(score_data)
```

### Message Router
Location: `src/app/app.py`

```python
def message_router(message):
    """Routes messages to appropriate handlers"""
    if "masterPin" in message and "slavePin" in message:
        on_dartboard_throw_received(message)  # Dartboard throw
    else:
        on_score_received(message)  # Manual score
```

## Testing

### Using the Simulator

```bash
# Single throw test
python3 scripts/dartboard_simulator.py \
  --client-id local_client_id \
  --client-secret local_client_secret

# Simulate a complete game
python3 scripts/dartboard_simulator.py \
  --simulate-game \
  --num-rounds 10

# Multiple concurrent dartboards
python3 scripts/dartboard_simulator.py \
  --concurrent-boards 3

# Continuous testing
python3 scripts/dartboard_simulator.py --continuous
```

### Expected Console Output (Flask App)

```
RabbitMQ consumer started
Listening on topic: darts.#
Connected to RabbitMQ: localhost:5672
Listening on exchange 'darts_exchange' with topic 'darts.#'
Waiting for messages. To exit press CTRL+C

Received message: {'masterPin': 4, 'slavePin': 13, 'boardType': 'carromco', ...}
Dartboard throw received: {'masterPin': 4, 'slavePin': 13, 'boardType': 'carromco', ...}
Mapped pins (4,13) to TRIPLE 20 (zone 20)
Score processed: 20 TRIPLE
```

## Security

- **OAuth2 Authentication**: All dartboard clients must authenticate with WSO2
- **Scope Requirements**: `dartboard:write` scope required for throw submissions
- **Token Validation**: API Gateway validates tokens via introspection before accepting throws
- **Rate Limiting**: Configured in WSO2 API Manager (if deployed)

## Troubleshooting

### Throws Not Appearing in Game

1. **Check RabbitMQ connection:**
   ```bash
   # Check RabbitMQ management UI
   http://localhost:15672
   # Default: guest/guest
   ```

2. **Verify consumer is listening:**
   ```
   # Flask app console should show:
   RabbitMQ consumer started
   Listening on topic: darts.#
   ```

3. **Check zone mappings exist:**
   ```sql
   SELECT * FROM dartboard_zone_mapping
   WHERE dartboard_type_id = (
     SELECT id FROM dartboard_type WHERE name = 'carromco'
   );
   ```

### Message Not Routed Correctly

Check message structure - must contain `masterPin` and `slavePin` for dartboard routing:
```python
if "masterPin" in message and "slavePin" in message:
    # Routes to dartboard handler
else:
    # Routes to score handler
```

### Zone Mapping Not Found

Error: `Zone mapping not found for pins (X, Y)`

**Solution:** Add the missing mapping via API:
```bash
curl -X POST http://localhost:5000/api/dartboard/zone \
  -H "Content-Type: application/json" \
  -d '{
    "dartboard_type": "carromco",
    "master_pin": 4,
    "slave_pin": 13,
    "zone_number": 20,
    "multiplier_type": "TRIPLE",
    "base_value": 20
  }'
```

## Related Documentation

- [API Gateway Configuration](./DEPLOYMENT.md#api-gateway)
- [Dartboard Client Integration](./DARTBOARD_CLIENT_INTEGRATION.md)
- [WSO2 OAuth2 Setup](./WSO2_APIM_CONFIGURATION.md)
- [Architecture Overview](./ARCHITECTURE.md)
