# Darts Game Python Application - Summary

## 🎯 What Has Been Created

A complete Python web application for managing darts games with the following features:

### ✅ Core Features

- **Game Modes**: 301, 401, 501, and Cricket
- **Multi-Player Support**: 2-6 players (Cricket max 4)
- **RabbitMQ Integration**: Receives scores via topic subscription
- **Real-time Updates**: WebSocket-based live game updates
- **Web Interface**: Responsive game board and control panel
- **REST API**: Full API for game management
- **Docker Support**: Easy deployment with Docker Compose

### 📁 Project Structure

```
dartserver-pythonapp/
├── app.py                      # Main Flask application
├── game_manager.py             # Game logic coordinator
├── rabbitmq_consumer.py        # RabbitMQ message consumer
├── requirements.txt            # Python dependencies
├── .env.example               # Configuration template
├── Dockerfile                 # Docker container definition
├── docker-compose.yml         # Docker Compose setup
├── run.sh                     # Startup script
├── test_rabbitmq.py          # RabbitMQ testing tool
├── bridge_nodejs_to_rabbitmq.js  # Node.js bridge script
│
├── games/                     # Game implementations
│   ├── __init__.py
│   ├── game_301.py           # 301/401/501 logic
│   └── game_cricket.py       # Cricket logic
│
├── templates/                 # HTML templates
│   ├── index.html            # Main game board
│   └── control.html          # Control panel
│
├── static/                    # Static assets
│   ├── css/
│   │   ├── style.css         # Main styles
│   │   └── control.css       # Control panel styles
│   └── js/
│       ├── main.js           # Game board JavaScript
│       └── control.js        # Control panel JavaScript
│
└── examples/                  # Usage examples
    ├── api_examples.py       # REST API examples
    └── websocket_client.py   # WebSocket examples
```

## 🚀 Quick Start

### Option 1: Docker (Easiest)

```bash
docker-compose up
```

### Option 2: Manual

```bash
./run.sh
```

Then open:

- Game Board: <http://localhost:5000>
- Control Panel: <http://localhost:5000/control>

## 🎮 How It Works

### 1. Game Flow

```
Start Game → Players Take Turns → Send Scores → Update State → Check Winner
     ↓              ↓                   ↓             ↓            ↓
  Select Type   Current Player    RabbitMQ/API   WebSocket    Display Winner
```

### 2. Score Input Methods

**A. RabbitMQ (Primary)**

```json
{
  "score": 20,
  "multiplier": "TRIPLE",
  "user": "Player 1"
}
```

**B. REST API**

```bash
POST /api/game/new
GET /api/game/state
POST /api/players
```

**C. WebSocket**

```javascript
socket.emit("manual_score", { score: 20, multiplier: "TRIPLE" });
socket.emit("next_player");
```

**D. Web Control Panel**

- Manual score entry form
- Player management
- Game controls

### 3. Game Rules Implementation

**301/401/501:**

- Start with N points
- Subtract each dart score
- Bust if going below 0
- Win by reaching exactly 0

**Cricket:**

- Hit 15-20 and Bull (25)
- 3 hits to "open" each number
- Score points on opened numbers
- Win by opening all + highest score

## 🔌 Integration Options

### With Existing Node.js App

```bash
# Use the bridge script
node bridge_nodejs_to_rabbitmq.js
```

### With Arduino/ESP32

```cpp
// Send scores to RabbitMQ
mqttClient.publish("darts.scores.board1",
  "{\"score\":20,\"multiplier\":\"TRIPLE\"}");
```

### With Other Systems

- Use REST API endpoints
- Connect via WebSocket
- Publish to RabbitMQ directly

## 📊 Message Format

### RabbitMQ Message

```json
{
  "score": 20, // Base score (0-60)
  "multiplier": "TRIPLE", // SINGLE, DOUBLE, TRIPLE, BULL, DBLBULL
  "user": "Player 1" // Optional player name
}
```

### Routing Keys

- Pattern: `darts.scores.#`
- Examples:
  - `darts.scores.board1`
  - `darts.scores.player1`
  - `darts.scores.test`

## 🧪 Testing

### Test RabbitMQ Integration

```bash
python test_rabbitmq.py
```

### Test REST API

```bash
python examples/api_examples.py
```

### Test WebSocket

```bash
python examples/websocket_client.py
```

## 🎨 Customization

### Add Audio Files

Place MP3 files in `static/audio/`:

- Plink.mp3, Triple.mp3, Dbl.mp3, etc.

### Add Video Effects

Place MP4 files in `static/video/`:

- triple.mp4, double.mp4, bullseye.mp4, etc.

### Modify Game Rules

Edit files in `games/` directory:

- `game_301.py` - Modify 301 logic
- `game_cricket.py` - Modify Cricket logic

### Change Styling

Edit CSS files in `static/css/`:

- `style.css` - Main board styling
- `control.css` - Control panel styling

## 🔧 Configuration

### Environment Variables (.env)

```bash
# RabbitMQ
RABBITMQ_HOST=localhost
RABBITMQ_PORT=5672
RABBITMQ_USER=guest
RABBITMQ_PASSWORD=guest
RABBITMQ_EXCHANGE=darts_exchange
RABBITMQ_TOPIC=darts.scores.#

# Flask
FLASK_HOST=0.0.0.0
FLASK_PORT=5000
FLASK_DEBUG=True
SECRET_KEY=your-secret-key
```

## 📡 API Reference

### REST Endpoints

- `GET /` - Game board
- `GET /control` - Control panel
- `GET /api/game/state` - Get game state
- `POST /api/game/new` - Start new game
- `GET /api/players` - Get players
- `POST /api/players` - Add player
- `DELETE /api/players/<id>` - Remove player

### WebSocket Events

**Emit (Client → Server):**

- `new_game` - Start game
- `add_player` - Add player
- `remove_player` - Remove player
- `next_player` - Next turn
- `skip_to_player` - Skip to player
- `manual_score` - Submit score

**Listen (Server → Client):**

- `game_state` - State update
- `play_sound` - Sound effect
- `play_video` - Video effect
- `message` - Alert message
- `big_message` - Big display message

## 🐛 Troubleshooting

### RabbitMQ Issues

```bash
# Check if running
sudo systemctl status rabbitmq-server

# View logs
sudo journalctl -u rabbitmq-server -f

# Restart
sudo systemctl restart rabbitmq-server
```

### Application Issues

```bash
# Check Python version (need 3.8+)
python --version

# Reinstall dependencies
pip install -r requirements.txt --force-reinstall

# Check logs
# Application prints to console
```

### Port Conflicts

```bash
# Change Flask port in .env
FLASK_PORT=5001

# Change RabbitMQ port in .env
RABBITMQ_PORT=5673
```

## 🎯 Next Steps

1. **Deploy to Production**
   - Use proper SECRET_KEY
   - Set FLASK_DEBUG=False
   - Use reverse proxy (nginx)
   - Enable HTTPS

2. **Add Features**
   - Player statistics
   - Game history
   - Leaderboards
   - More game modes

3. **Integrate Hardware**
   - Connect electronic dartboard
   - Add LED indicators
   - Physical buttons

4. **Enhance UI**
   - Add animations
   - Sound effects
   - Video effects
   - Mobile responsive

## 📚 Documentation

- **README.md** - Full documentation
- **QUICKSTART.md** - Quick start guide
- **examples/** - Code examples
- **Inline comments** - Code documentation

## 🤝 Support

For issues or questions:

1. Check documentation
2. Review examples
3. Check application logs
4. Test with provided scripts

## ✨ Features Highlight

✅ Multiple game modes (301, 401, 501, Cricket)
✅ RabbitMQ integration for score input
✅ Real-time WebSocket updates
✅ REST API for integration
✅ Web-based control panel
✅ Docker support
✅ Multi-player support
✅ Bust detection
✅ Winner detection
✅ Cricket scoring logic
✅ Extensible architecture
✅ Example scripts
✅ Comprehensive documentation

---

**Ready to play darts! 🎯**
