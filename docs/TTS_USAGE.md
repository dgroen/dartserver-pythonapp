# TTS Usage Guide

## ✅ Status: FULLY WORKING

Your darts game now has **Text-to-Speech (TTS)** fully integrated and working!

---

## 🎯 Quick Start

The TTS system is **already configured and ready to use**. Just start your app:

```bash
source .venv/bin/activate
python3 app.py
```

---

## ⚙️ Configuration

Edit the `.env` file to customize TTS settings:

```bash
# Enable/Disable TTS
TTS_ENABLED=true          # Set to 'false' to disable

# Engine Selection
TTS_ENGINE=pyttsx3        # Options: 'pyttsx3' (offline) or 'gtts' (online)

# Speech Speed (Words Per Minute)
TTS_SPEED=150             # Range: 100-250
                          # 100 = Very slow
                          # 150 = Normal (default)
                          # 200 = Fast
                          # 250 = Very fast

# Volume Level
TTS_VOLUME=0.9            # Range: 0.0-1.0 (0.9 = 90%)

# Voice Type
TTS_VOICE=default         # Options: default, english, male, female
                          # Or use specific voice names from available voices
```

---

## 🎮 Game Announcements

TTS will automatically announce these game events:

| Event              | Announcement                      |
| ------------------ | --------------------------------- |
| 🎯 **Game Start**  | "Welcome to the game"             |
| 👤 **Player Turn** | "[Player Name], Throw Darts"      |
| 🎪 **Triple Hit**  | "Triple! [score] points"          |
| 🎯 **Double Hit**  | "Double! [score] points"          |
| 🎯 **Bullseye**    | "Bullseye! [score] points"        |
| 🎯 **Double Bull** | "Double Bullseye! [score] points" |
| ❌ **Bust**        | "Bust!"                           |
| 🏆 **Winner**      | "We have a winner! [name] wins!"  |

---

## 🔧 Runtime Configuration (API)

You can change TTS settings while the app is running using the REST API:

### Get Current Configuration

```bash
curl http://localhost:5000/api/tts/config
```

### Change Speed

```bash
curl -X POST http://localhost:5000/api/tts/config \
  -H "Content-Type: application/json" \
  -d '{"speed": 200}'
```

### Change Volume

```bash
curl -X POST http://localhost:5000/api/tts/config \
  -H "Content-Type: application/json" \
  -d '{"volume": 0.8}'
```

### Enable/Disable TTS

```bash
# Disable
curl -X POST http://localhost:5000/api/tts/config \
  -H "Content-Type: application/json" \
  -d '{"enabled": false}'

# Enable
curl -X POST http://localhost:5000/api/tts/config \
  -H "Content-Type: application/json" \
  -d '{"enabled": true}'
```

### Test TTS

```bash
curl -X POST http://localhost:5000/api/tts/test \
  -H "Content-Type: application/json" \
  -d '{"text": "Testing text to speech!"}'
```

---

## 🎤 Available Voices

To see all available voices on your system:

```bash
source .venv/bin/activate
python3 -c "from tts_service import TTSService; tts = TTSService(); voices = tts.get_available_voices(); [print(f'{v[\"name\"]}') for v in voices]"
```

Then set your preferred voice in `.env`:

```bash
TTS_VOICE=english
```

---

## 📊 Speed Guide

| Speed (WPM) | Description | Use Case                 |
| ----------- | ----------- | ------------------------ |
| 100         | Very Slow   | Beginners, learning      |
| 125         | Slow        | Clear announcements      |
| 150         | Normal      | **Default, recommended** |
| 175         | Fast        | Experienced players      |
| 200         | Very Fast   | Quick games              |
| 250         | Maximum     | Speed tournaments        |

---

## 🔍 Testing

Test the TTS system:

```bash
source .venv/bin/activate
python3 test_tts_simple.py
```

This will:

- ✓ Verify TTS is initialized
- ✓ Test speech output
- ✓ Test speed changes
- ✓ Show available voices

---

## 🐛 Troubleshooting

### TTS Not Speaking

1. **Check if enabled:**

   ```bash
   curl http://localhost:5000/api/tts/config
   ```

   Make sure `"enabled": true`

2. **Check .env file:**

   ```bash
   cat .env | grep TTS
   ```

   Verify `TTS_ENABLED=true`

3. **Test TTS directly:**

   ```bash
   python3 test_tts_simple.py
   ```

### Audio Output Issues

If you see "aplay: not found" warnings:

- This is normal in headless environments
- TTS is still working, just no audio device available
- On systems with audio, install: `sudo apt-get install alsa-utils`

### Speed Not Changing

- Speed changes require pyttsx3 engine
- If using gtts, speed control is limited
- Restart the app after changing `.env` settings

---

## 📝 Examples

### Example 1: Slow Speed for Beginners

```bash
# Edit .env
TTS_SPEED=100

# Or via API
curl -X POST http://localhost:5000/api/tts/config \
  -H "Content-Type: application/json" \
  -d '{"speed": 100}'
```

### Example 2: Fast Speed for Tournaments

```bash
# Edit .env
TTS_SPEED=200

# Or via API
curl -X POST http://localhost:5000/api/tts/config \
  -H "Content-Type: application/json" \
  -d '{"speed": 200}'
```

### Example 3: Disable TTS Temporarily

```bash
curl -X POST http://localhost:5000/api/tts/config \
  -H "Content-Type: application/json" \
  -d '{"enabled": false}'
```

### Example 4: Custom Voice

```bash
# First, find available voices
python3 -c "from tts_service import TTSService; tts = TTSService(); [print(v['name']) for v in tts.get_available_voices()]"

# Then set in .env
TTS_VOICE=english
```

---

## ✅ Summary

**Your TTS system is fully operational!**

- ✅ TTS Service installed and configured
- ✅ Integrated into GameManager
- ✅ Configurable speed (100-250 WPM)
- ✅ Configurable voice type
- ✅ Configurable volume (0.0-1.0)
- ✅ Runtime enable/disable via API
- ✅ Automatic game event announcements
- ✅ REST API for configuration

**Just start your app and enjoy voice announcements!** 🎉
