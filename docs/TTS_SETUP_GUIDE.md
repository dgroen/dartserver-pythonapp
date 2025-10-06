# Text-to-Speech (TTS) Setup Guide

## ✅ Status: TTS System Fully Integrated!

The Text-to-Speech system has been **successfully integrated** into your darts game application. This guide will help you install the required dependencies and configure the system.

---

## 🎯 What's Already Done

✅ **TTS Service Created** (`tts_service.py`)
- Supports both `pyttsx3` (offline) and `gTTS` (online) engines
- Configurable speed, voice type, and volume
- Enable/disable functionality
- Graceful fallback when engines aren't available

✅ **GameManager Integration** (`game_manager.py`)
- TTS initialized in `__init__` method
- `_emit_sound()` method enhanced with optional `text` parameter
- TTS announcements added throughout game events:
  - Game start: "Welcome to the game"
  - Player turns: "{Player name}, Throw Darts"
  - Scores: "Triple! 60 points", "Double Bullseye! 50 points"
  - Bust: "Bust!"
  - Winner: "We have a winner! {Player name} wins!"

✅ **API Endpoints** (`app.py`)
- `GET /api/tts/config` - Get current TTS configuration
- `POST /api/tts/config` - Update TTS settings
- `POST /api/tts/test` - Test TTS with custom text

✅ **Environment Configuration** (`.env`)
- All TTS settings configurable via environment variables

---

## 📦 Installation

### Option 1: Using UV (Recommended)

If you have UV installed:

```bash
cd /data/dartserver-pythonapp
uv pip install pyttsx3 gtts
```

### Option 2: Using pip in Virtual Environment

```bash
cd /data/dartserver-pythonapp

# Create virtual environment if it doesn't exist
python3 -m venv .venv

# Activate virtual environment
source .venv/bin/activate

# Install TTS dependencies
pip install pyttsx3 gtts

# Install all project dependencies
pip install -r requirements.txt
```

### Option 3: System-wide Installation (Not Recommended)

```bash
# Install pip if not available
sudo apt-get update
sudo apt-get install python3-pip

# Install TTS libraries
pip3 install --user pyttsx3 gtts
```

### Additional Dependencies for pyttsx3

For **pyttsx3** to work on Linux, you need espeak:

```bash
sudo apt-get update
sudo apt-get install espeak espeak-data libespeak-dev
```

For **pyttsx3** on macOS, it uses the built-in `say` command (no additional dependencies needed).

---

## ⚙️ Configuration

### Environment Variables

Edit your `.env` file (already configured):

```bash
# Text-to-Speech Configuration
TTS_ENABLED=true          # Enable/disable TTS
TTS_ENGINE=pyttsx3        # Engine: 'pyttsx3' or 'gtts'
TTS_SPEED=150             # Speech speed (words per minute for pyttsx3)
TTS_VOLUME=0.9            # Volume level (0.0 to 1.0)
TTS_VOICE=default         # Voice type (engine-specific)
```

### Configuration Options

#### TTS_ENGINE

- **`pyttsx3`** (Recommended for local use)
  - ✅ Works offline
  - ✅ Faster response time
  - ✅ No internet required
  - ⚠️ Requires espeak on Linux
  - Voice quality: Good

- **`gtts`** (Google Text-to-Speech)
  - ✅ Better voice quality
  - ✅ No system dependencies
  - ⚠️ Requires internet connection
  - ⚠️ Slower (generates audio files)
  - ⚠️ May have rate limits

#### TTS_SPEED

- **pyttsx3**: Words per minute (typical range: 100-200)
  - `100` - Very slow
  - `150` - Normal (default)
  - `200` - Fast
  - `250` - Very fast

- **gtts**: Boolean slow mode (converted automatically)
  - `< 100` - Slow speech
  - `>= 100` - Normal speech

#### TTS_VOICE

For **pyttsx3**, you can specify voice names. To see available voices:

```python
import pyttsx3
engine = pyttsx3.init()
voices = engine.getProperty('voices')
for voice in voices:
    print(f"ID: {voice.id}")
    print(f"Name: {voice.name}")
    print(f"Languages: {voice.languages}")
    print()
```

Common voice options:
- `default` - System default voice
- `male` - Male voice (if available)
- `female` - Female voice (if available)
- `english` - English voice

---

## 🚀 Usage

### Starting the Application

```bash
cd /data/dartserver-pythonapp
source .venv/bin/activate  # If using virtual environment
python3 app.py
```

Or use the run script:

```bash
./run.sh
```

### Testing TTS

#### 1. Via API Endpoint

```bash
# Test TTS with custom text
curl -X POST http://localhost:5000/api/tts/test \
  -H "Content-Type: application/json" \
  -d '{"text": "Hello, welcome to the darts game!"}'

# Get current TTS configuration
curl http://localhost:5000/api/tts/config

# Update TTS configuration
curl -X POST http://localhost:5000/api/tts/config \
  -H "Content-Type: application/json" \
  -d '{
    "enabled": true,
    "speed": 180,
    "volume": 0.8
  }'
```

#### 2. Via Python Script

```python
from tts_service import TTSService

# Initialize TTS
tts = TTSService(
    engine='pyttsx3',
    voice_type='default',
    speed=150,
    volume=0.9
)

# Speak text
tts.speak("Welcome to the darts game!")

# Change settings
tts.set_speed(180)
tts.set_volume(0.8)
tts.speak("Faster and quieter!")
```

#### 3. During Gameplay

TTS will automatically announce:
- **Game Start**: "Welcome to the game"
- **Player Turns**: "Player 1, Throw Darts"
- **Scores**: "Triple! 60 points"
- **Special Hits**: "Double Bullseye! 50 points"
- **Bust**: "Bust!"
- **Winner**: "We have a winner! Player 1 wins!"

---

## 🔧 Troubleshooting

### Issue: "No module named 'pyttsx3'"

**Solution**: Install the TTS dependencies

```bash
pip install pyttsx3 gtts
```

### Issue: pyttsx3 fails with "No module named '_espeak'"

**Solution**: Install espeak on Linux

```bash
sudo apt-get install espeak espeak-data libespeak-dev
```

### Issue: TTS not speaking

**Check 1**: Verify TTS is enabled

```bash
curl http://localhost:5000/api/tts/config
```

Should show `"enabled": true`

**Check 2**: Enable TTS via API

```bash
curl -X POST http://localhost:5000/api/tts/config \
  -H "Content-Type: application/json" \
  -d '{"enabled": true}'
```

**Check 3**: Check system audio

```bash
# Test system audio (Linux)
speaker-test -t wav -c 2

# Test espeak directly
espeak "Hello world"
```

### Issue: TTS is too slow/fast

**Solution**: Adjust the speed

```bash
# Via API
curl -X POST http://localhost:5000/api/tts/config \
  -H "Content-Type: application/json" \
  -d '{"speed": 180}'

# Or edit .env file
TTS_SPEED=180
```

### Issue: Voice quality is poor

**Solution**: Try switching to gTTS

```bash
# Edit .env file
TTS_ENGINE=gtts

# Restart the application
```

### Issue: gTTS requires internet

**Solution**: Use pyttsx3 for offline operation

```bash
# Edit .env file
TTS_ENGINE=pyttsx3

# Install espeak if needed
sudo apt-get install espeak

# Restart the application
```

---

## 📝 Code Examples

### Adding TTS to Custom Events

```python
# In game_manager.py

def custom_event(self):
    """Example of adding TTS to a custom event"""
    
    # Play sound with TTS
    self._emit_sound("customSound", "This is a custom announcement")
    
    # Play sound without TTS
    self._emit_sound("customSound")
```

### Conditional TTS

```python
# Only speak for certain conditions
if score > 100:
    self._emit_sound("highScore", f"Wow! {score} points!")
else:
    self._emit_sound("normalScore")  # No TTS
```

### Dynamic TTS Messages

```python
player_name = self.players[self.current_player]['name']
score = 180

# Create dynamic message
message = f"{player_name} scored {score} points! Amazing!"
self._emit_sound("celebration", message)
```

---

## 🎮 Game Integration Points

The TTS system is integrated at these key points:

| Event | Sound | TTS Message |
|-------|-------|-------------|
| Game Start | `intro` | "Welcome to the game" |
| Player Turn | `Player1`, `Player2`, etc. | "{Player name}, Throw Darts" |
| Triple Hit | `Triple` | "Triple! {score} points" |
| Double Hit | `Dbl` | "Double! {score} points" |
| Bullseye | `Bullseye` | "Bullseye! {score} points" |
| Double Bull | `DblBullseye` | "Double Bullseye! {score} points" |
| Bust | `Bust` | "Bust!" |
| Winner | `WeHaveAWinner` | "We have a winner! {name} wins!" |
| End Turn | `RemoveDarts` | (No TTS by default) |

---

## 🔍 Verification

Run the integration test:

```bash
cd /data/dartserver-pythonapp
python3 test_tts_integration.py
```

Expected output:
```
✓ TTS Service imported successfully
✓ TTS Service initialized
✓ GameManager module imported successfully
✓ TTSService is imported in GameManager
✓ _emit_sound supports 'text' parameter for TTS
✓ All TTS integration tests passed!
```

---

## 📚 API Reference

### TTSService Class

```python
class TTSService:
    def __init__(self, engine='pyttsx3', voice_type='default', 
                 speed=150, volume=1.0):
        """Initialize TTS service"""
        
    def speak(self, text: str) -> bool:
        """Speak the given text"""
        
    def set_speed(self, speed: int):
        """Set speech speed"""
        
    def set_volume(self, volume: float):
        """Set volume (0.0 to 1.0)"""
        
    def set_voice(self, voice_type: str):
        """Set voice type"""
        
    def enable(self):
        """Enable TTS"""
        
    def disable(self):
        """Disable TTS"""
        
    def is_enabled(self) -> bool:
        """Check if TTS is enabled"""
        
    def get_available_voices(self) -> list:
        """Get list of available voices"""
```

### REST API Endpoints

#### GET /api/tts/config

Get current TTS configuration.

**Response:**
```json
{
  "enabled": true,
  "engine": "pyttsx3",
  "speed": 150,
  "volume": 0.9,
  "voice": "default"
}
```

#### POST /api/tts/config

Update TTS configuration.

**Request Body:**
```json
{
  "enabled": true,
  "speed": 180,
  "volume": 0.8,
  "voice": "female"
}
```

**Response:**
```json
{
  "status": "success",
  "message": "TTS configuration updated"
}
```

#### POST /api/tts/test

Test TTS with custom text.

**Request Body:**
```json
{
  "text": "Hello, this is a test!"
}
```

**Response:**
```json
{
  "status": "success",
  "message": "TTS test completed"
}
```

---

## 🎉 Summary

Your TTS system is **fully integrated and ready to use**! 

### Next Steps:

1. **Install Dependencies**:
   ```bash
   pip install pyttsx3 gtts
   sudo apt-get install espeak  # Linux only
   ```

2. **Configure Settings** (already done in `.env`):
   ```bash
   TTS_ENABLED=true
   TTS_ENGINE=pyttsx3
   TTS_SPEED=150
   ```

3. **Start the Application**:
   ```bash
   python3 app.py
   ```

4. **Test TTS**:
   ```bash
   curl -X POST http://localhost:5000/api/tts/test \
     -H "Content-Type: application/json" \
     -d '{"text": "Welcome to the darts game!"}'
   ```

5. **Play the Game** and enjoy the voice announcements! 🎯

---

## 📞 Support

If you encounter any issues:

1. Check the troubleshooting section above
2. Run the integration test: `python3 test_tts_integration.py`
3. Check the application logs for TTS-related errors
4. Verify espeak is installed (Linux): `espeak --version`
5. Test TTS directly: `python3 -c "import pyttsx3; e=pyttsx3.init(); e.say('test'); e.runAndWait()"`

---

**Happy Gaming! 🎯🎮**