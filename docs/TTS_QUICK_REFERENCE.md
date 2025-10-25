# TTS Quick Reference Card

## 🎯 Status: ✅ FULLY IMPLEMENTED

---

## 📦 Installation (Required)

```bash
# Install TTS libraries
pip install pyttsx3 gtts

# Linux only: Install espeak
sudo apt-get install espeak
```

---

## ⚙️ Configuration (.env)

```bash
TTS_ENABLED=true        # Enable/disable TTS
TTS_ENGINE=pyttsx3      # Engine: pyttsx3 or gtts
TTS_SPEED=150           # Speed: 100-250 (words/min)
TTS_VOLUME=0.9          # Volume: 0.0-1.0
TTS_VOICE=default       # Voice: default, male, female
```

---

## 🚀 Quick Start

```bash
# 1. Install dependencies
pip install pyttsx3 gtts

# 2. Start application
python3 app.py

# 3. Test TTS
curl -X POST http://localhost:5000/api/tts/test \
  -H "Content-Type: application/json" \
  -d '{"text": "Hello!"}'
```

---

## 🎮 Game Announcements

| Event       | Announcement                      |
| ----------- | --------------------------------- |
| Game Start  | "Welcome to the game"             |
| Player Turn | "{Player}, Throw Darts"           |
| Triple      | "Triple! {score} points"          |
| Double      | "Double! {score} points"          |
| Bullseye    | "Bullseye! {score} points"        |
| Double Bull | "Double Bullseye! {score} points" |
| Bust        | "Bust!"                           |
| Winner      | "We have a winner! {name} wins!"  |

---

## 🔧 Runtime Configuration

### Get Config

```bash
curl http://localhost:5000/api/tts/config
```

### Change Speed

```bash
curl -X POST http://localhost:5000/api/tts/config \
  -H "Content-Type: application/json" \
  -d '{"speed": 180}'
```

### Change Voice

```bash
curl -X POST http://localhost:5000/api/tts/config \
  -H "Content-Type: application/json" \
  -d '{"voice": "female"}'
```

### Disable TTS

```bash
curl -X POST http://localhost:5000/api/tts/config \
  -H "Content-Type: application/json" \
  -d '{"enabled": false}'
```

---

## 🎚️ Speed Guide

| Speed | Description      |
| ----- | ---------------- |
| 100   | Very slow, clear |
| 125   | Slow             |
| 150   | Normal (default) |
| 175   | Slightly faster  |
| 200   | Fast             |
| 250   | Very fast        |

---

## 🔍 Troubleshooting

### TTS not working?

```bash
# Check if enabled
curl http://localhost:5000/api/tts/config

# Enable it
curl -X POST http://localhost:5000/api/tts/config \
  -d '{"enabled": true}'

# Test espeak (Linux)
espeak "test"
```

### Poor voice quality?

```bash
# Switch to gTTS in .env
TTS_ENGINE=gtts
```

### Need offline mode?

```bash
# Use pyttsx3 in .env
TTS_ENGINE=pyttsx3
```

---

## 📚 Documentation

- **Full Setup Guide**: `TTS_SETUP_GUIDE.md`
- **Implementation Details**: `TTS_IMPLEMENTATION_SUMMARY.md`
- **Integration Test**: `python3 test_tts_integration.py`

---

## 💡 Code Example

```python
# In game_manager.py
self._emit_sound("intro", "Welcome to the game")
self._emit_sound("Bust", "Bust!")
self._emit_sound("WeHaveAWinner", f"{player_name} wins!")
```

---

## ✅ Verification

```bash
python3 test_tts_integration.py
```

Expected: All tests pass ✓

---

**That's it! Your TTS system is ready to use! 🎯🔊**
