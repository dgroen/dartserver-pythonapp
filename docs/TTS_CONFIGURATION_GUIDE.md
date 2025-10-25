# Text-to-Speech (TTS) Configuration Guide

## Overview

The Dart Game application includes a fully integrated Text-to-Speech (TTS) system that announces game events, scores, and player turns. The TTS system supports two engines and is highly configurable.

## Features

- **Dual Engine Support**: Choose between `pyttsx3` (offline) or `gTTS` (online)
- **Configurable Speed**: Adjust speech rate from slow to very fast
- **Voice Selection**: Choose from 75+ available voices (pyttsx3)
- **Volume Control**: Adjust volume from 0.0 to 1.0
- **Real-time Configuration**: Change settings via REST API without restarting
- **Game Integration**: Automatic announcements for all game events

## Quick Start

### 1. Environment Variables

Create or edit `.env` file in the project root:

```bash
# Enable/disable TTS
TTS_ENABLED=true

# Choose engine: pyttsx3 (offline) or gtts (online)
TTS_ENGINE=pyttsx3

# Speech speed (words per minute)
# 100 = slow, 150 = normal, 200 = fast, 250 = very fast
TTS_SPEED=150

# Volume level (0.0 to 1.0)
TTS_VOLUME=1.0

# Voice type (engine-specific)
TTS_VOICE=default
```

### 2. Using the REST API

#### Get Current Configuration

```bash
curl http://localhost:5000/api/tts/config
```

Response:

```json
{
  "enabled": true,
  "engine": "pyttsx3",
  "speed": 150,
  "volume": 1.0,
  "voice": "default"
}
```

#### Update Configuration

```bash
curl -X POST http://localhost:5000/api/tts/config \
  -H "Content-Type: application/json" \
  -d '{
    "enabled": true,
    "speed": 180,
    "volume": 0.8,
    "voice": "english"
  }'
```

#### Get Available Voices

```bash
curl http://localhost:5000/api/tts/voices
```

Response:

```json
[
  {
    "id": "english",
    "name": "english",
    "languages": ["en"],
    "gender": "unknown"
  },
  {
    "id": "english-us",
    "name": "english-us",
    "languages": ["en-US"],
    "gender": "unknown"
  }
  // ... more voices
]
```

#### Test TTS

```bash
curl -X POST http://localhost:5000/api/tts/test \
  -H "Content-Type: application/json" \
  -d '{"text": "Hello, this is a test"}'
```

## Configuration Options

### Speed Settings

| Speed | Description | Use Case                       |
| ----- | ----------- | ------------------------------ |
| 100   | Very Slow   | Maximum clarity, accessibility |
| 125   | Slow        | Clear pronunciation            |
| 150   | Normal      | Default, balanced speed        |
| 175   | Fast        | Quick announcements            |
| 200   | Very Fast   | Rapid gameplay                 |
| 250+  | Ultra Fast  | Expert players                 |

### Engine Comparison

| Feature             | pyttsx3           | gTTS                       |
| ------------------- | ----------------- | -------------------------- |
| **Connection**      | Offline           | Online (requires internet) |
| **Speed**           | Fast              | Slower (API calls)         |
| **Voices**          | 75+ system voices | Google voices              |
| **Quality**         | Good              | Excellent                  |
| **Latency**         | Low               | Higher                     |
| **Recommended For** | Local games       | High-quality audio         |

## Game Event Announcements

The TTS system automatically announces:

### Game Start

- "Welcome to the game"
- "[Player Name], Throw Darts"

### Score Announcements

- **Single**: "[Score] points"
- **Double**: "Double [base score]! [total] points"
- **Triple**: "Triple [base score]! [total] points"
- **Bullseye**: "Bullseye! [score] points"
- **Double Bullseye**: "Double Bullseye! [score] points"

### Turn Changes

- "[Player Name], Throw Darts"

### Game Events

- **Bust**: "Bust!"
- **Winner**: "We have a winner! [Player Name] wins!"
- **End Turn**: "Remove darts"

### Player Management

- **Add Player**: "Player [name] added"
- **Remove Player**: "Player [name] removed"

## Advanced Configuration

### Selecting a Specific Voice

1. Get list of available voices:

```bash
curl http://localhost:5000/api/tts/voices
```

2. Choose a voice from the list and update configuration:

```bash
curl -X POST http://localhost:5000/api/tts/config \
  -H "Content-Type: application/json" \
  -d '{"voice": "english-us"}'
```

### Dynamic Speed Adjustment

You can change speed during gameplay:

```bash
# Slow down for important announcements
curl -X POST http://localhost:5000/api/tts/config \
  -H "Content-Type: application/json" \
  -d '{"speed": 120}'

# Speed up for rapid gameplay
curl -X POST http://localhost:5000/api/tts/config \
  -H "Content-Type: application/json" \
  -d '{"speed": 200}'
```

### Temporarily Disable TTS

```bash
# Disable
curl -X POST http://localhost:5000/api/tts/config \
  -H "Content-Type: application/json" \
  -d '{"enabled": false}'

# Re-enable
curl -X POST http://localhost:5000/api/tts/config \
  -H "Content-Type: application/json" \
  -d '{"enabled": true}'
```

## Testing

### Test Script

Run the included test script:

```bash
# Using virtual environment
.venv/bin/python3 test_game_tts.py

# Or activate venv first
source .venv/bin/activate
python3 test_game_tts.py
```

### Manual Testing

```python
from tts_service import TTSService

# Create TTS instance
tts = TTSService(engine="pyttsx3", speed=150, volume=1.0)

# Test speech
tts.speak("Hello, this is a test")

# Change speed
tts.set_speed(200)
tts.speak("This is faster")

# Change voice
tts.set_voice("english-us")
tts.speak("This is a different voice")
```

## Troubleshooting

### No Audio Output

**Symptom**: "aplay: not found" messages

**Cause**: Server environment without audio hardware

**Solution**: This is normal for server deployments. TTS is generating audio correctly, but there's no audio output device. The TTS will work fine when the application is accessed from a client with audio capabilities.

### TTS Not Working

1. Check if TTS is enabled:

```bash
curl http://localhost:5000/api/tts/config
```

2. Verify dependencies are installed:

```bash
.venv/bin/pip list | grep -E "(pyttsx3|gtts)"
```

3. Test TTS directly:

```bash
curl -X POST http://localhost:5000/api/tts/test \
  -H "Content-Type: application/json" \
  -d '{"text": "Test"}'
```

### Slow Performance

If using gTTS and experiencing delays:

1. Switch to pyttsx3 for lower latency:

```bash
curl -X POST http://localhost:5000/api/tts/config \
  -H "Content-Type: application/json" \
  -d '{"engine": "pyttsx3"}'
```

Note: Changing engines requires restarting the application.

### Voice Not Found

If a specific voice isn't working:

1. List available voices:

```bash
curl http://localhost:5000/api/tts/voices
```

2. Use the exact voice ID from the list

## Integration Examples

### Python Client

```python
import requests

# Configure TTS
response = requests.post(
    "http://localhost:5000/api/tts/config",
    json={
        "enabled": True,
        "speed": 150,
        "volume": 0.9,
        "voice": "english"
    }
)

# Test announcement
response = requests.post(
    "http://localhost:5000/api/tts/test",
    json={"text": "Player One, throw darts"}
)
```

### JavaScript Client

```javascript
// Configure TTS
fetch("http://localhost:5000/api/tts/config", {
  method: "POST",
  headers: { "Content-Type": "application/json" },
  body: JSON.stringify({
    enabled: true,
    speed: 150,
    volume: 0.9,
    voice: "english",
  }),
});

// Test announcement
fetch("http://localhost:5000/api/tts/test", {
  method: "POST",
  headers: { "Content-Type": "application/json" },
  body: JSON.stringify({
    text: "Player One, throw darts",
  }),
});
```

## Best Practices

1. **Speed Selection**: Start with 150 (normal) and adjust based on player preference
2. **Volume**: Keep at 1.0 unless audio is too loud for your environment
3. **Engine Choice**: Use pyttsx3 for local games, gTTS for better quality when internet is available
4. **Voice Selection**: Test different voices to find the most clear and pleasant one
5. **Disable When Not Needed**: Turn off TTS during practice sessions to reduce audio fatigue

## Performance Considerations

- **pyttsx3**: ~50ms latency, suitable for real-time announcements
- **gTTS**: ~200-500ms latency due to API calls, better for non-critical announcements
- **Memory**: TTS service uses minimal memory (~10MB)
- **CPU**: pyttsx3 uses more CPU but is still lightweight

## API Reference

### GET /api/tts/config

Get current TTS configuration

**Response**: `{enabled, engine, speed, volume, voice}`

### POST /api/tts/config

Update TTS configuration

**Body**: `{enabled?, speed?, volume?, voice?}`

**Response**: `{status, message}`

### GET /api/tts/voices

Get available voices

**Response**: Array of voice objects

### POST /api/tts/test

Test TTS with custom text

**Body**: `{text}`

**Response**: `{status, message}`

## Support

For issues or questions:

1. Check the logs for error messages
2. Verify dependencies are installed
3. Test with the included test scripts
4. Review the TTS_USAGE.md file for additional details
