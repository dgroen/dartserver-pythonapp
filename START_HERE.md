# 🎯 Start Here - Dartserver Python Application

Welcome to the **Dartserver Python Application** - a complete, standalone darts game management system!

## 🚀 Quick Start (30 seconds)

```bash
docker-compose up
```

Then open: **http://localhost:5000**

That's it! 🎉

## 📚 What is This?

This is a **production-ready Python web application** for managing darts games with:

- ✅ Multiple game modes (301, 401, 501, Cricket)
- ✅ Multi-player support (2-6 players)
- ✅ RabbitMQ integration for receiving scores
- ✅ Real-time WebSocket updates
- ✅ REST API for programmatic access
- ✅ Web-based control panel
- ✅ Docker support for easy deployment

## 🎮 How to Use

### 1. Start the Application

**Option A: Docker (Recommended)**
```bash
docker-compose up
```

**Option B: Quick Script**
```bash
./run.sh
```

**Option C: Manual**
```bash
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
python app.py
```

### 2. Access the Web Interface

- **Game Board:** http://localhost:5000
- **Control Panel:** http://localhost:5000/control
- **RabbitMQ UI:** http://localhost:15672 (guest/guest)

### 3. Start Playing

From the Control Panel:
1. Select game type (301, 401, 501, or Cricket)
2. Add players
3. Click "Start New Game"
4. Send scores via RabbitMQ, API, or manual entry

## 📖 Documentation

| Document | When to Read |
|----------|--------------|
| **[GET_STARTED.md](GET_STARTED.md)** | First time setup |
| **[QUICKSTART.md](QUICKSTART.md)** | Quick reference |
| **[README_REPO.md](README_REPO.md)** | Complete overview |
| **[ARCHITECTURE.md](ARCHITECTURE.md)** | System design |
| **[INDEX.md](INDEX.md)** | Documentation index |

**Recommended:** Start with [GET_STARTED.md](GET_STARTED.md)

## 🧪 Testing

### Verify Installation
```bash
python verify_installation.py
```

### Test RabbitMQ
```bash
python test_rabbitmq.py
```

### API Examples
```bash
python examples/api_examples.py
```

## 📡 Sending Scores

### Via RabbitMQ (Primary Method)

```json
{
  "score": 20,
  "multiplier": "TRIPLE",
  "user": "Player 1"
}
```

Publish to:
- **Exchange:** `darts_exchange`
- **Routing Key:** `darts.scores.*`

### Via REST API

```bash
curl -X POST http://localhost:5000/api/game/new \
  -H "Content-Type: application/json" \
  -d '{"game_type": "301", "players": ["Alice", "Bob"]}'
```

### Via Web Control Panel

Just use the manual score entry form!

## 🎯 Game Modes

### 301/401/501
- Start with 301/401/501 points
- Subtract each dart score
- Win by reaching exactly 0
- Bust if score goes below 0

### Cricket
- Hit targets: 15, 16, 17, 18, 19, 20, Bull
- Need 3 hits to "open" each target
- Score points on opened targets
- Win by opening all with highest score

## 🔧 Configuration

Copy and edit `.env`:
```bash
cp .env.example .env
```

Key settings:
- `RABBITMQ_HOST` - RabbitMQ server
- `FLASK_PORT` - Web server port
- `FLASK_DEBUG` - Debug mode

## 🐛 Troubleshooting

### Application won't start
```bash
python verify_installation.py
```

### RabbitMQ not connecting
```bash
sudo systemctl status rabbitmq-server
sudo systemctl start rabbitmq-server
```

### Port already in use
Edit `.env` and change `FLASK_PORT=5001`

## 📂 Project Structure

```
dartserver-pythonapp/
├── app.py                  # Main application
├── game_manager.py         # Game logic
├── rabbitmq_consumer.py    # RabbitMQ integration
├── games/                  # Game modes
├── templates/              # Web interface
├── static/                 # CSS/JS
├── examples/               # Usage examples
└── docs/                   # Documentation
```

## 🎨 Customization

### Add New Game Mode
1. Create `games/game_newmode.py`
2. Implement game logic
3. Register in `game_manager.py`

### Modify Styling
- Edit `static/css/style.css`
- Edit `static/css/control.css`

### Add Audio/Video
- Place files in `static/audio/` and `static/video/`
- Update `static/js/main.js`

## 🔗 Integration

### Arduino/ESP32
```cpp
void sendScore(int score, String multiplier) {
  String payload = "{\"score\":" + String(score) + 
                   ",\"multiplier\":\"" + multiplier + "\"}";
  mqttClient.publish("darts.scores.board1", payload);
}
```

### Node.js Bridge
```bash
node bridge_nodejs_to_rabbitmq.js
```

## 🆘 Need Help?

1. **Read the docs:** [GET_STARTED.md](GET_STARTED.md)
2. **Verify setup:** `python verify_installation.py`
3. **Check examples:** `examples/` directory
4. **Review logs:** Check console output

## ✨ Features

- ✅ Multiple game modes
- ✅ Multi-player support
- ✅ Real-time updates
- ✅ RabbitMQ integration
- ✅ REST API
- ✅ WebSocket support
- ✅ Docker deployment
- ✅ Auto-reconnection
- ✅ Bust detection
- ✅ Winner detection
- ✅ Turn management

## 🎉 You're Ready!

Everything you need is here. Start with:

```bash
docker-compose up
```

Then open **http://localhost:5000** and start playing! 🎯

---

**Questions?** Read [GET_STARTED.md](GET_STARTED.md) for detailed instructions.

**Happy Darting!** 🎯🎉