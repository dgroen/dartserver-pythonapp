# 🎯 TTS Demo & Quick Reference

## ✅ Status: FULLY WORKING & INTEGRATED

Your darts game now has **Text-to-Speech** with configurable speed and voice!

---

## 🚀 Quick Start

```bash
# Start the app
source .venv/bin/activate
python3 app.py
```

**That's it!** TTS will automatically announce game events.

---

## 🎮 What You'll Hear

When you play the game, TTS will announce:

1. **Game Start**: "Welcome to the game"
2. **Player Turns**: "Player 1, Throw Darts"
3. **Scores**: "Triple! 60 points", "Double! 40 points"
4. **Special Hits**: "Bullseye! 50 points"
5. **Bust**: "Bust!"
6. **Winner**: "We have a winner! Player 1 wins!"

---

## ⚙️ Configuration Options

### Option 1: Edit `.env` File (Permanent)

```bash
# Speed: 100 (slow) to 250 (fast)
TTS_SPEED=150

# Voice: default, english, male, female
TTS_VOICE=default

# Volume: 0.0 (silent) to 1.0 (max)
TTS_VOLUME=0.9

# Enable/Disable
TTS_ENABLED=true
```

### Option 2: Use API (Runtime Changes)

```bash
# Change speed to fast (200 WPM)
curl -X POST http://localhost:5000/api/tts/config \
  -H "Content-Type: application/json" \
  -d '{"speed": 200}'

# Change volume to 80%
curl -X POST http://localhost:5000/api/tts/config \
  -H "Content-Type: application/json" \
  -d '{"volume": 0.8}'

# Disable TTS
curl -X POST http://localhost:5000/api/tts/config \
  -H "Content-Type: application/json" \
  -d '{"enabled": false}'

# Test TTS
curl -X POST http://localhost:5000/api/tts/test \
  -H "Content-Type: application/json" \
  -d '{"text": "Hello from the darts game!"}'
```

---

## 📊 Speed Guide

| Speed      | WPM     | Description    |
| ---------- | ------- | -------------- |
| Very Slow  | 100     | For beginners  |
| Slow       | 125     | Clear and easy |
| **Normal** | **150** | **Default**    |
| Fast       | 175     | Quick games    |
| Very Fast  | 200     | Tournaments    |
| Maximum    | 250     | Speed mode     |

---

## 🔧 Testing

Run the verification script:

```bash
source .venv/bin/activate
python3 verify_tts_integration.py
```

Expected output:

```
✅ ALL TESTS PASSED!

📋 Summary:
   • TTS Service: ✓ Working
   • Speech Output: ✓ Working
   • Speed Control: ✓ Working (100-250 WPM)
   • GameManager Integration: ✓ Complete
   • API Endpoints: ✓ Available
```

---

## 📝 Examples

### Example 1: Slow Speed for Learning

```bash
# Edit .env
TTS_SPEED=100

# Restart app
python3 app.py
```

### Example 2: Fast Speed for Experienced Players

```bash
# Via API (no restart needed)
curl -X POST http://localhost:5000/api/tts/config \
  -H "Content-Type: application/json" \
  -d '{"speed": 200}'
```

### Example 3: Quiet Volume for Late Night

```bash
curl -X POST http://localhost:5000/api/tts/config \
  -H "Content-Type: application/json" \
  -d '{"volume": 0.3}'
```

---

## 🎤 Available Voices

List all voices on your system:

```bash
source .venv/bin/activate
python3 -c "from tts_service import TTSService; tts = TTSService(); [print(v['name']) for v in tts.get_available_voices()]"
```

Then set your favorite in `.env`:

```bash
TTS_VOICE=english
```

---

## ✅ What's Integrated

- ✅ **TTS Service** - Fully functional with pyttsx3 engine
- ✅ **Speed Control** - 100-250 WPM configurable
- ✅ **Voice Selection** - Multiple voices available
- ✅ **Volume Control** - 0.0-1.0 range
- ✅ **GameManager** - TTS integrated into all game events
- ✅ **API Endpoints** - Runtime configuration available
- ✅ **Environment Config** - .env file support
- ✅ **Enable/Disable** - Can be toggled on/off

---

## 🎯 Summary

**Your TTS system is 100% complete and working!**

Just start your app and enjoy voice announcements with configurable speed and voice type! 🎉

For more details, see:

- `TTS_USAGE.md` - Complete usage guide
- `TTS_SETUP_GUIDE.md` - Detailed setup information
- `TTS_QUICK_REFERENCE.md` - Quick reference card
