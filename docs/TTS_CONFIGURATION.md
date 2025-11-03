# Text-to-Speech (TTS) Configuration Guide

## Overview

The darts game application has a fully integrated Text-to-Speech system that announces game events, scores, and player turns. The TTS system is configurable via environment variables and supports two engines: **pyttsx3** (offline) and **gTTS** (online).

## Features

✅ **Dual Engine Support**: Choose between pyttsx3 (offline, faster) or gTTS (online, better quality)
✅ **Configurable Speed**: Adjust speech rate to your preference
✅ **Voice Selection**: Choose different voice types (engine-dependent)
✅ **Volume Control**: Set the volume level
✅ **Enable/Disable**: Turn TTS on or off without code changes

## Configuration

### Environment Variables

Configure TTS by setting these environment variables:

```bash
# TTS Engine Selection
TTS_ENGINE=pyttsx3          # Options: 'pyttsx3' (default) or 'gtts'

# Voice Configuration
TTS_VOICE=default           # Voice type (engine-specific)
                            # For pyttsx3: 'default', 'male', 'female', or specific voice name
                            # For gTTS: language code like 'en', 'en-us', 'en-uk'

# Speed Configuration
TTS_SPEED=150               # Speech rate
                            # For pyttsx3: words per minute (default: 150, range: 50-300)
                            # For gTTS: not directly supported (uses default speed)

# Volume Configuration
TTS_VOLUME=1.0              # Volume level (0.0 to 1.0, default: 1.0)
                            # Only applies to pyttsx3

# Enable/Disable TTS
TTS_ENABLED=true            # Options: 'true' or 'false' (default: true)
```

### Example Configurations

#### Fast Speech (pyttsx3)

```bash
export TTS_ENGINE=pyttsx3
export TTS_SPEED=200
export TTS_VOLUME=0.9
export TTS_ENABLED=true
```

#### Slow Speech (pyttsx3)

```bash
export TTS_ENGINE=pyttsx3
export TTS_SPEED=100
export TTS_VOLUME=1.0
export TTS_ENABLED=true
```

#### Google TTS (Online)

```bash
export TTS_ENGINE=gtts
export TTS_VOICE=en-us
export TTS_ENABLED=true
```

#### Disable TTS

```bash
export TTS_ENABLED=false
```

## Engine Comparison

### pyttsx3 (Offline Engine)

**Pros:**

- Works offline (no internet required)
- Faster response time
- Configurable speed and volume
- Multiple voice options

**Cons:**

- Voice quality may be lower
- Requires system TTS libraries

**Best for:** Production environments, offline use, low latency

### gTTS (Google Text-to-Speech)

**Pros:**

- High-quality voices
- Natural-sounding speech
- Multiple language support

**Cons:**

- Requires internet connection
- Slightly slower (API calls)
- Limited configuration options

**Best for:** Development, demos, when quality is priority

## Installation

### pyttsx3 Requirements

```bash
# Install pyttsx3
pip install pyttsx3

# Linux: Install espeak
sudo apt-get install espeak

# macOS: Uses built-in TTS (no additional install needed)

# Windows: Uses SAPI5 (no additional install needed)
```

### gTTS Requirements

```bash
# Install gTTS
pip install gtts

# Requires internet connection to work
```

## TTS Integration Points

The TTS system is integrated at these game events:

1. **Game Start**: Announces the first player's turn
2. **Player Turns**: Announces when it's a player's turn
3. **Scores**: Announces special scores (doubles, triples, bullseyes)
4. **Bust**: Announces when a player busts
5. **Winner**: Announces the winner
6. **Turn End**: Reminds players to remove darts

## API Endpoints

### Test TTS

```http
POST /api/tts/test
Content-Type: application/json

{
  "text": "This is a test"
}
```

### Get TTS Configuration

```http
GET /api/tts/config
```

Response:

```json
{
  "enabled": true,
  "engine": "pyttsx3",
  "voice_type": "default",
  "speed": 150,
  "volume": 1.0
}
```

### Update TTS Configuration

```http
POST /api/tts/config
Content-Type: application/json

{
  "enabled": true,
  "engine": "pyttsx3",
  "voice_type": "default",
  "speed": 180,
  "volume": 0.8
}
```

## Troubleshooting

### TTS Not Working

1. **Check if TTS is enabled:**

   ```bash
   curl http://localhost:5000/api/tts/config
   ```

2. **Verify engine is installed:**

   ```bash
   pip list | grep -E "pyttsx3|gtts"
   ```

3. **Check logs for errors:**
   Look for TTS initialization messages in the application logs

4. **Test TTS directly:**

   ```bash
   curl -X POST http://localhost:5000/api/tts/test \
     -H "Content-Type: application/json" \
     -d '{"text": "Test message"}'
   ```

### Common Issues

**Issue:** "pyttsx3 not available"
**Solution:** Install pyttsx3 and system dependencies (espeak on Linux)

**Issue:** "gTTS not available"
**Solution:** Install gtts: `pip install gtts`

**Issue:** No sound output
**Solution:** Check system volume, verify audio device is working

**Issue:** Speech is too fast/slow
**Solution:** Adjust TTS_SPEED environment variable

## Code Examples

### Programmatic TTS Usage

```python
from tts_service import TTSService

# Initialize TTS
tts = TTSService(
    engine="pyttsx3",
    voice_type="default",
    speed=150,
    volume=1.0
)

# Speak text
tts.speak("Hello, welcome to the darts game!")

# Check if enabled
if tts.is_enabled():
    tts.speak("TTS is working")

# Disable TTS
tts.disable()

# Enable TTS
tts.enable()

# Update configuration
tts.update_config(speed=200, volume=0.8)
```

### Integration in Game Manager

The `_emit_sound()` method automatically uses TTS when text is provided:

```python
# Emit sound with TTS
self._emit_sound("intro", "Welcome to the game")

# Emit sound without TTS
self._emit_sound("Plink")  # Just plays sound, no speech
```

## Performance Considerations

- **pyttsx3**: ~50-100ms latency (offline)
- **gTTS**: ~200-500ms latency (depends on network)
- TTS runs asynchronously and doesn't block game logic
- Multiple TTS calls are queued automatically

## Future Enhancements

Potential improvements for the TTS system:

- [ ] Add more voice options
- [ ] Support for multiple languages
- [ ] Custom pronunciation dictionary
- [ ] Audio effects (echo, reverb)
- [ ] Voice gender selection
- [ ] Pitch control
- [ ] SSML support for advanced speech control

## Summary

The TTS system is **fully functional and ready to use**. Simply configure the environment variables to match your preferences, and the system will automatically announce game events. The default configuration (pyttsx3, speed 150) works well for most use cases.

For the best experience:

- **Development/Testing**: Use pyttsx3 with speed 150-180
- **Production**: Use pyttsx3 for reliability
- **Demos**: Use gTTS for better voice quality (requires internet)
