# Phase 3 Quick Start Guide: Services Module

Get started with the `dartserver-services` package in 5 minutes.

## Installation

### From Local Development

```bash
# Install the package in development mode
cd packages/dartserver-services
pip install -e ".[dev]"
```

### Dependencies

The package automatically installs:
- `dartserver-core>=1.0.0` - Core authentication and database
- `pika>=1.3.2` - RabbitMQ client
- `gtts>=2.5.0` - Google Text-to-Speech
- `pyttsx3>=2.90` - Offline TTS engine
- `SQLAlchemy>=2.0.23` - Database ORM

## Quick Usage

### 1. Import Services

```python
from dartserver_services import (
    RabbitMQConsumer,
    TTSService,
    DartboardService,
    MobileService,
)
```

### 2. RabbitMQ Consumer

```python
from dartserver_services import RabbitMQConsumer

# Configuration
config = {
    "host": "localhost",
    "port": 5672,
    "user": "guest",
    "password": "guest",
    "vhost": "/",
    "exchange": "darts",
    "topic": "darts.scores.#",
}

# Callback function
def on_score_received(message):
    print(f"Score received: {message}")

# Create consumer
consumer = RabbitMQConsumer(config, on_score_received)

# Start consuming (blocking)
consumer.start()
```

### 3. TTS Service

```python
from dartserver_services import TTSService

# Initialize with pyttsx3 (offline)
tts = TTSService(
    engine="pyttsx3",
    speed=150,
    volume=0.8,
    language="en"
)

# Speak text
tts.speak("Score: 180!")

# Or generate audio data for streaming
audio_bytes = tts.speak("Your score", generate_audio=True)

# Configure
tts.set_language("nl")
tts.set_speed(200)
tts.set_volume(1.0)

# Get available voices
voices = tts.get_available_voices()
supported = TTSService.get_supported_languages()
```

### 4. Dartboard Service

```python
from dartserver_core import get_session
from dartserver_services import DartboardService

session = get_session()

# Register dartboard type
dartboard_type = DartboardService.register_dartboard_type(
    session,
    name="carromco",
    brand="Carromco",
    model="NG2500",
)

# Add zone mapping (GPIO pins to dartboard zones)
mapping = DartboardService.add_zone_mapping(
    session,
    dartboard_type_id=dartboard_type.id,
    master_pin=1,
    slave_pin=2,
    zone_number=20,
    multiplier_type="SINGLE",
    base_value=20,
)

# Get zone from pins
zone_info = DartboardService.get_zone_from_pins(
    session,
    dartboard_type_name="carromco",
    master_pin=1,
    slave_pin=2,
)
print(f"Zone: {zone_info['zone_number']}, Score: {zone_info['score']}")

# Calculate score
score = DartboardService.calculate_score(20, "TRIPLE")  # Returns 60

# Validate zone mapping
is_valid = DartboardService.validate_zone_mapping(20, "DOUBLE", 20)

# Legacy conversion
zone = DartboardService.convert_legacy_to_zone(
    session, "carromco", score=20, multiplier="DOUBLE"
)
```

### 5. Mobile Service

```python
from dartserver_core import get_session
from dartserver_services import MobileService

session = get_session()
mobile_service = MobileService(session)

# Register dartboard
result = mobile_service.register_dartboard(
    owner_id=1,
    dartboard_id="BOARD-001",
    name="Home Dartboard",
    wpa_key="secure_key_123",
)

# Get user's dartboards
dartboards = mobile_service.get_user_dartboards(owner_id=1)

# Create API key
api_key = mobile_service.create_api_key(
    player_id=1,
    key_name="Mobile App Key",
)

# Validate API key
player_info = mobile_service.validate_api_key(api_key["api_key"]["api_key"])

# Manage hotspot config
config = mobile_service.create_hotspot_config(
    player_id=1,
    dartboard_id=1,
    ssid="Dartboard-WiFi",
    password="hotspot_pwd",
)

mobile_service.toggle_hotspot(config["config"]["id"], 1, enabled=True)
```

## Testing

```bash
# Run all tests
pytest tests/ -v

# Run with coverage
pytest tests/ --cov=src/dartserver_services --cov-report=html

# Run specific test file
pytest tests/test_core.py -v

# Run specific test
pytest tests/test_core.py::test_rabbitmq_consumer_initialization -v
```

## Common Error Solutions

### Error: ModuleNotFoundError: No module named 'dartserver_services'

**Solution**: Install the package in development mode:
```bash
cd packages/dartserver-services
pip install -e .
```

### Error: ImportError: cannot import name 'RabbitMQConsumer'

**Solution**: Make sure you're importing from the package, not internal modules:
```python
# ✓ Correct
from dartserver_services import RabbitMQConsumer

# ✗ Wrong
from dartserver_services.rabbitmq.consumer import RabbitMQConsumer
```

### Error: sqlite3.OperationalError (Database not initialized)

**Solution**: Initialize the database first:
```python
from dartserver_core import init_db, Config

# Initialize database
init_db(Config.SQLALCHEMY_DATABASE_URI)
```

## Files Modified

- `src/app/app.py` - Imports from dartserver_services
- `src/app/game_manager.py` - Imports TTSService from dartserver_services
- `src/mobile_service.py` - Wrapper imports from dartserver_services
- `packages/dartserver-core/src/dartserver_core/__init__.py` - Added model exports

## Architecture

```
┌─────────────────────┐
│   Main Application  │
│   (src/app/app.py)  │
└──────────┬──────────┘
           │ imports
           ↓
┌──────────────────────────────────┐
│  dartserver-services Package     │
│  ├── RabbitMQConsumer           │
│  ├── TTSService                 │
│  ├── DartboardService           │
│  └── MobileService              │
└──────────┬───────────────────────┘
           │ depends on
           ↓
┌──────────────────────────────────┐
│  dartserver-core Package         │
│  ├── Authentication             │
│  ├── Configuration              │
│  └── Database Models & Service  │
└──────────────────────────────────┘
```

---

For detailed API documentation, see [README.md](../packages/dartserver-services/README.md)
