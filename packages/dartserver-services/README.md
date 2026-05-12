# dartserver-services

Backend services including message queue, text-to-speech, dartboard mapping, and mobile API management.

## Features

- **RabbitMQ Consumer** - Asynchronous score ingestion from dartboard hardware
- **Text-to-Speech (TTS)** - Dual engines (pyttsx3 offline, gTTS cloud)
- **Dartboard Service** - GPIO pin mapping and score calculation
- **Mobile Service** - API key and dartboard registration management

## Installation

```bash
pip install dartserver-services
```

## Quick Start

### RabbitMQ Consumer

```python
from dartserver_services import RabbitMQConsumer

def on_score(score_data):
    print(f"Score received: {score_data}")

config = {
    'host': 'localhost',
    'port': 5672,
    'exchange': 'darts_exchange',
    'topic': 'darts.scores.#',
}

consumer = RabbitMQConsumer(config, on_score)
consumer.start()  # Blocks until stopped
```

### Text-to-Speech

```python
from dartserver_services import TTSService

tts = TTSService(engine='offline')

# Generate speech
tts.speak("Double twenty")

# List voices
voices = tts.get_voices()

# List languages
languages = tts.get_supported_languages()
```

### Dartboard Service

```python
from dartserver_services import DartboardService

dartboard = DartboardService()

# Map GPIO pin to zone
dartboard.add_zone_mapping(0, 20)  # Pin 0 -> Zone 20
dartboard.add_zone_mapping(1, 5)   # Pin 1 -> Zone 5

# Calculate score
score = dartboard.calculate_score(0)  # Returns 20

# Export mappings
mappings = dartboard.export_mappings()
```

### Mobile Service

```python
from dartserver_services import MobileService

mobile = MobileService(db_service)

# Register dartboard
dartboard_id = mobile.register_dartboard('Board-01', 'Dartboard A')

# Create API key
api_key = mobile.create_api_key(dartboard_id, 'mobile-app')

# Setup hotspot config
mobile.configure_hotspot(dartboard_id, 'MyDartsWiFi', '192.168.1.100')

# Toggle hotspot
mobile.toggle_hotspot(config_id)
```

## Public Exports

- `RabbitMQConsumer` - Message queue consumer
- `TTSService` - Text-to-speech service
- `DartboardService` - Dartboard mapping and scoring
- `MobileService` - Mobile API management
- `DartboardMappingError` - Dartboard exception

## Services Overview

### RabbitMQConsumer
- Connects to RabbitMQ with auto-reconnection
- Handles heartbeats and connection failures
- Deserializes JSON score messages
- Calls registered callback on score receipt

### TTSService
- Supports 12+ languages
- Configurable voice selection
- Automatic audio streaming
- Falls back gracefully between engines

### DartboardService
- Maps GPIO pins to dartboard zones
- Calculates scores from pin inputs
- Supports zone validation
- Bulk import from matrix format

### MobileService
- Manages API keys with rotation
- Registers dartboards and hotspots
- Tracks device lifecycle
- Maintains device configurations

## Testing

```bash
pytest tests/
```

## License

MIT - See LICENSE file

## Contributing

Pull requests welcome. Please ensure tests pass.
