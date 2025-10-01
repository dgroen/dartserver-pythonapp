# 🎯 Get Started with Darts Game Application

## Welcome!

You now have a complete Python web application for managing darts games with RabbitMQ integration. This guide will get you up and running in minutes.

## 🚀 Three Ways to Start

### Option 1: Docker (Easiest - Recommended)

**Prerequisites:** Docker and Docker Compose installed

```bash
docker-compose up
```

That's it! The application will start with RabbitMQ included.

**Access:**
- Game Board: http://localhost:5000
- Control Panel: http://localhost:5000/control
- RabbitMQ Management: http://localhost:15672 (guest/guest)

---

### Option 2: Quick Start Script

**Prerequisites:** Python 3.8+, RabbitMQ installed

```bash
cd python_app
./run.sh
```

The script will:
1. Create a virtual environment
2. Install dependencies
3. Start the application

---

### Option 3: Manual Setup

**Prerequisites:** Python 3.8+, RabbitMQ installed

```bash
cd python_app

# Create virtual environment
python3 -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Configure (optional)
cp .env.example .env
# Edit .env if needed

# Start application
python app.py
```

---

## ✅ Verify Installation

```bash
cd python_app
python verify_installation.py
```

This will check:
- ✓ Python version
- ✓ Required packages
- ✓ File structure
- ✓ RabbitMQ connection

---

## 🎮 Your First Game

### Step 1: Open the Control Panel

Navigate to: http://localhost:5000/control

### Step 2: Start a Game

1. Select game type: **301**
2. Click **"Start New Game"**

### Step 3: Send a Score

**Option A: Use the test script**
```bash
# In a new terminal
cd python_app
python test_rabbitmq.py
# Choose option 2 (send single random score)
```

**Option B: Use the control panel**
1. Go to "Manual Score Entry"
2. Enter score: **20**
3. Select multiplier: **TRIPLE**
4. Click **"Submit Score"**

### Step 4: Watch the Game Board

Open: http://localhost:5000

You'll see:
- Player scores update in real-time
- Current player highlighted
- Score messages displayed

### Step 5: Continue Playing

1. Send 3 scores (one turn)
2. Click **"Next Player"** in control panel
3. Repeat until someone wins!

---

## 📚 What's Next?

### Learn the Basics

1. **Read the Quick Start Guide**
   ```bash
   cat QUICKSTART.md
   ```

2. **Explore the Examples**
   ```bash
   # REST API examples
   python examples/api_examples.py
   
   # WebSocket examples
   python examples/websocket_client.py
   ```

3. **Understand the Architecture**
   ```bash
   cat ARCHITECTURE.md
   ```

### Try Different Game Modes

**301 Game:**
- Start with 301 points
- Subtract each dart
- First to exactly 0 wins

**Cricket Game:**
- Hit 15, 16, 17, 18, 19, 20, Bull
- 3 hits to "open" each number
- Score points on opened numbers
- First to open all + highest score wins

### Test RabbitMQ Integration

```bash
cd python_app
python test_rabbitmq.py
```

Choose from:
1. Send all test scores
2. Send single random score
3. Send custom score
4. Send continuous random scores

### Integrate with Your Hardware

If you have an electronic dartboard:

1. Configure Arduino/ESP32 to publish to RabbitMQ
2. Use message format:
   ```json
   {
     "score": 20,
     "multiplier": "TRIPLE",
     "user": "Player 1"
   }
   ```
3. Publish to exchange: `darts_exchange`
4. Routing key: `darts.scores.*`

---

## 🔧 Common Tasks

### Add More Players

**Via Control Panel:**
1. Enter player name
2. Click "Add Player"

**Via API:**
```bash
curl -X POST http://localhost:5000/api/players \
  -H "Content-Type: application/json" \
  -d '{"name": "Alice"}'
```

### Change Game Type

**Via Control Panel:**
1. Select game type (301, 401, 501, Cricket)
2. Click "Start New Game"

**Via API:**
```bash
curl -X POST http://localhost:5000/api/game/new \
  -H "Content-Type: application/json" \
  -d '{"game_type": "cricket", "players": ["Alice", "Bob"]}'
```

### Get Game State

**Via Browser:**
http://localhost:5000/api/game/state

**Via Command Line:**
```bash
curl http://localhost:5000/api/game/state
```

### Stop the Application

**Docker:**
```bash
docker-compose down
```

**Manual:**
Press `Ctrl+C` in the terminal

---

## 🐛 Troubleshooting

### Application Won't Start

**Check Python version:**
```bash
python --version  # Should be 3.8 or higher
```

**Reinstall dependencies:**
```bash
pip install -r requirements.txt --force-reinstall
```

### RabbitMQ Connection Failed

**Check if RabbitMQ is running:**
```bash
sudo systemctl status rabbitmq-server
```

**Start RabbitMQ:**
```bash
sudo systemctl start rabbitmq-server
```

**Check credentials in .env:**
```bash
RABBITMQ_USER=guest
RABBITMQ_PASSWORD=guest
```

### Port Already in Use

**Change Flask port:**
Edit `.env`:
```bash
FLASK_PORT=5001
```

**Or specify when running:**
```bash
FLASK_PORT=5001 python app.py
```

### Scores Not Appearing

1. **Check RabbitMQ Management UI:**
   http://localhost:15672
   - Verify exchange `darts_exchange` exists
   - Check if messages are being received

2. **Check application logs:**
   Look for error messages in the terminal

3. **Verify message format:**
   ```json
   {
     "score": 20,
     "multiplier": "TRIPLE"
   }
   ```

---

## 📖 Documentation

- **README.md** - Complete documentation
- **QUICKSTART.md** - Quick start guide
- **SUMMARY.md** - Feature summary
- **ARCHITECTURE.md** - System architecture
- **examples/** - Code examples

---

## 🎯 Quick Reference

### URLs
- Game Board: http://localhost:5000
- Control Panel: http://localhost:5000/control
- API Docs: http://localhost:5000/api/game/state
- RabbitMQ UI: http://localhost:15672

### Commands
```bash
# Start application
python app.py

# Test RabbitMQ
python test_rabbitmq.py

# Verify installation
python verify_installation.py

# Run examples
python examples/api_examples.py
python examples/websocket_client.py
```

### Message Format
```json
{
  "score": 20,
  "multiplier": "SINGLE|DOUBLE|TRIPLE|BULL|DBLBULL",
  "user": "Player Name"
}
```

### API Endpoints
```
GET  /api/game/state      - Get game state
POST /api/game/new        - Start new game
GET  /api/players         - Get players
POST /api/players         - Add player
DELETE /api/players/<id>  - Remove player
```

---

## 🎉 You're Ready!

You now have everything you need to:
- ✅ Run the darts game application
- ✅ Start games and manage players
- ✅ Send scores via RabbitMQ
- ✅ Integrate with your hardware
- ✅ Customize and extend

**Have fun playing darts! 🎯**

---

## 💡 Tips

1. **Keep the control panel open** in one browser tab and the game board in another
2. **Use the test script** to simulate games before connecting real hardware
3. **Check the examples** folder for integration ideas
4. **Read the architecture doc** to understand how everything works
5. **Join the community** and share your setup!

---

## 🆘 Need Help?

1. Check the documentation files
2. Run `python verify_installation.py`
3. Look at the examples in `examples/`
4. Check application logs for errors
5. Review the troubleshooting section above

---

**Happy Darting! 🎯🎉**