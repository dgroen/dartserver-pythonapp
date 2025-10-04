# Darts Game Web Application

A Python web application for managing darts games (301 and Cricket) with RabbitMQ integration, real-time updates, and enterprise-grade authentication.

## Features

### Game Features
- **Multiple Game Modes**: 301, 401, 501, and Cricket
- **Single & Multi-Player Support**: Support for 1-6 players (Cricket max 4)
- **RabbitMQ Integration**: Receives dart scores through RabbitMQ topic subscription
- **Real-time Updates**: WebSocket-based real-time game state updates
- **Automatic UI Refresh**: All connected clients automatically refresh when scores are sent/received
- **Web Interface**: Clean, responsive web interface for game display and control
- **Manual Score Entry**: Control panel for manual score entry and game management
- **REST API**: Full REST API for game control and score submission

### 🔐 Security & Authentication (NEW!)
- **🆕 OAuth2 Authentication**: Secure login with WSO2 Identity Server
- **🆕 Role-Based Access Control**: Three-tier role model (Player, Game Master, Admin)
- **🆕 Protected Routes**: All endpoints secured with authentication
- **🆕 Permission System**: Granular permission-based access control
- **🆕 Session Management**: Secure session handling with HttpOnly cookies
- **🆕 Token Validation**: JWT signature verification and introspection

### Enterprise Integration
- **🆕 API Gateway**: Secure REST API layer with OAuth2 authentication
- **🆕 WSO2 Integration**: Enterprise-grade identity and API management
- **🆕 Developer Portal**: Self-service API access with documentation and analytics

## Quick Start with Authentication 🚀

**The fastest way to get started with full authentication:**

```bash
# 1. Run the quick start script
./start-with-auth.sh

# 2. Configure WSO2 (follow the interactive guide)
./configure-wso2-roles.sh

# 3. Update .env with your WSO2 credentials

# 4. Start services again
./start-with-auth.sh

# 5. Access the application
# Open http://localhost:5000 and login!
```

**See [QUICK_START.md](QUICK_START.md) for detailed instructions.**

---

## Manual Installation

### 1. Install Python Dependencies
```bash
pip install -r requirements.txt
```

### 2. Set up RabbitMQ (if not already installed)
```bash
# On Ubuntu/Debian
sudo apt-get install rabbitmq-server

# On macOS
brew install rabbitmq

# Start RabbitMQ
sudo systemctl start rabbitmq-server  # Linux
brew services start rabbitmq          # macOS
```

### 3. Configure Environment Variables
```bash
cp .env.example .env
# Edit .env with your settings:
# - RabbitMQ connection
# - Flask configuration
# - WSO2 authentication (for secure mode)
```

### 4. Docker Deployment (Recommended)
```bash
# With authentication (recommended)
docker-compose -f docker-compose-wso2.yml up -d

# Without authentication (development only)
docker-compose up -d
```

## Configuration

Edit the `.env` file to configure:

### RabbitMQ Settings
- `RABBITMQ_HOST`: RabbitMQ server host (default: localhost)
- `RABBITMQ_PORT`: RabbitMQ server port (default: 5672)
- `RABBITMQ_USER`: RabbitMQ username (default: guest)
- `RABBITMQ_PASSWORD`: RabbitMQ password (default: guest)
- `RABBITMQ_EXCHANGE`: Exchange name (default: darts_exchange)
- `RABBITMQ_TOPIC`: Topic pattern (default: darts.scores.#)

### Flask Settings
- `FLASK_HOST`: Flask server host (default: 0.0.0.0)
- `FLASK_PORT`: Flask server port (default: 5000)
- `FLASK_DEBUG`: Debug mode (default: True)
- `SECRET_KEY`: Session encryption key (change in production!)

### 🔐 WSO2 Authentication Settings (NEW!)
- `WSO2_IS_URL`: WSO2 Identity Server URL (default: https://localhost:9443)
- `WSO2_CLIENT_ID`: OAuth2 client ID (get from WSO2 Console)
- `WSO2_CLIENT_SECRET`: OAuth2 client secret (get from WSO2 Console)
- `WSO2_REDIRECT_URI`: OAuth2 callback URL (default: http://localhost:5000/callback)
- `JWT_VALIDATION_MODE`: Token validation method (`introspection` or `jwks`)
- `WSO2_IS_INTROSPECT_USER`: Introspection username (default: admin)
- `WSO2_IS_INTROSPECT_PASSWORD`: Introspection password (default: admin)
- `SESSION_COOKIE_SECURE`: Enable secure cookies (set to `True` in production with HTTPS)

**See [docs/AUTHENTICATION_SETUP.md](docs/AUTHENTICATION_SETUP.md) for detailed configuration guide.**

## 🔐 Authentication & Roles

The system implements a three-tier role-based access control model:

### 🟢 Player Role
**Purpose**: Basic game participation

**Permissions**:
- View game board
- Submit dart scores
- View game state

**Access**: Game board, score submission

---

### 🟡 Game Master Role
**Purpose**: Game management and coordination

**Permissions**:
- All Player permissions
- Access control panel
- Create new games
- Add/remove players
- Manage game flow

**Access**: All Player features + Control panel

---

### 🔴 Admin Role
**Purpose**: Full system administration

**Permissions**:
- All permissions (wildcard `*`)
- Full system access
- User management (via WSO2)

**Access**: Complete system access

---

**Test Users** (create these in WSO2 Console):
- `testplayer` / `Player@123` (Player role)
- `testgamemaster` / `GameMaster@123` (Game Master role)
- `testadmin` / `Admin@123` (Admin role)

**See [AUTHENTICATION_SUMMARY.md](AUTHENTICATION_SUMMARY.md) for detailed role information.**

---

## Usage

### With Authentication (Recommended)

1. **Start services**:
```bash
./start-with-auth.sh
```

2. **Access the web interface**:
   - Login page: http://localhost:5000/login
   - Main game board: http://localhost:5000/ (requires login)
   - Control panel: http://localhost:5000/control (requires Game Master or Admin role)
   - User profile: http://localhost:5000/profile (requires login)

3. **Login with test user**:
   - Use one of the test users created in WSO2
   - You'll be redirected to WSO2 login page
   - After successful login, you'll be redirected back to the game

### Without Authentication (Development Only)

1. **Start the application**:
```bash
python app.py
```

2. **Access the web interface**:
   - Main game board: http://localhost:5000/
   - Control panel: http://localhost:5000/control
   - Auto-refresh test page: http://localhost:5000/test-refresh

3. **Send scores via RabbitMQ**:

The application listens for messages on the configured RabbitMQ exchange and topic.

**Message Format** (JSON):
```json
{
  "score": 20,
  "multiplier": "TRIPLE",
  "user": "Player 1"
}
```

**Multiplier Options**:
- `SINGLE`: Single score
- `DOUBLE`: Double score
- `TRIPLE`: Triple score
- `BULL`: Bullseye (25 points)
- `DBLBULL`: Double Bullseye (50 points)

## Game Rules

### 301/401/501
- Players start with 301/401/501 points
- Each dart score is subtracted from the player's total
- First player to reach exactly 0 wins
- Going below 0 results in a "bust" - score returns to start of turn

### Cricket
- Players must hit 15, 16, 17, 18, 19, 20, and Bull (25)
- Each number must be hit 3 times to "open" it
- Once opened, additional hits score points
- When all players have hit a number 3 times, it's "closed"
- First player to open all numbers with the highest score wins

## API Endpoints

### REST API

- `GET /api/game/state` - Get current game state
- `POST /api/game/new` - Start a new game
  ```json
  {
    "game_type": "301",
    "players": ["Player 1", "Player 2"],
    "double_out": false
  }
  ```
- `POST /api/score` - Submit a score (triggers automatic UI refresh)
  ```json
  {
    "score": 20,
    "multiplier": "TRIPLE"
  }
  ```
- `GET /api/players` - Get all players
- `POST /api/players` - Add a player
  ```json
  {
    "name": "Player 3"
  }
  ```
- `DELETE /api/players/<player_id>` - Remove a player

**Note**: All API endpoints that modify game state automatically trigger UI refresh for all connected clients via WebSocket.

### WebSocket Events

**Client → Server**:
- `new_game` - Start a new game
- `add_player` - Add a player
- `remove_player` - Remove a player
- `next_player` - Move to next player
- `skip_to_player` - Skip to specific player
- `manual_score` - Submit a manual score

**Server → Client**:
- `game_state` - Game state update
- `play_sound` - Play a sound effect
- `play_video` - Play a video effect
- `message` - Display a message
- `big_message` - Display a big message

## Testing

### Test Automatic UI Refresh

**Method 1: Interactive Test Page**
```bash
# Start the application
python app.py

# Open in browser: http://localhost:5000/test-refresh
# Click the test buttons and watch the UI update automatically!
```

**Method 2: Automated Test Script**
```bash
# Start the application in one terminal
python app.py

# Open the game UI in a browser: http://localhost:5000

# Run the test script in another terminal
python examples/test_auto_refresh.py

# Watch the UI update automatically as the script makes API calls!
```

### Test RabbitMQ Integration

Use the included test script to send test scores:

```bash
python test_rabbitmq.py
```

Or manually publish messages using RabbitMQ tools:

```bash
# Install rabbitmq management tools
sudo rabbitmq-plugins enable rabbitmq_management

# Publish a test message
rabbitmqadmin publish exchange=darts_exchange routing_key=darts.scores.test \
  payload='{"score": 20, "multiplier": "TRIPLE", "user": "Test Player"}'
```

## Project Structure

```
dartserver-pythonapp/
├── app.py                  # Main Flask application
├── game_manager.py         # Game logic manager
├── rabbitmq_consumer.py    # RabbitMQ consumer
├── requirements.txt        # Python dependencies
├── .env.example           # Environment variables template
├── games/
│   ├── __init__.py
│   ├── game_301.py        # 301/401/501 game logic
│   └── game_cricket.py    # Cricket game logic
├── templates/
│   ├── index.html         # Main game board
│   ├── control.html       # Control panel
│   └── test_refresh.html  # Auto-refresh test page
├── examples/
│   ├── api_examples.py    # API usage examples
│   ├── test_auto_refresh.py # Auto-refresh test script
│   └── websocket_client.py # WebSocket client example
└── static/
    ├── css/
    │   ├── style.css      # Main styles
    │   └── control.css    # Control panel styles
    └── js/
        ├── main.js        # Main game board JavaScript
        └── control.js     # Control panel JavaScript
```

## Integration with Existing System

This Python application can work alongside your existing Node.js darts application. You can:

1. Use the Python app as a standalone system with RabbitMQ
2. Bridge the Node.js app to send scores to RabbitMQ
3. Use the Python app's REST API to integrate with other systems

## Automatic UI Refresh

The application features **automatic UI refresh** - all connected clients automatically update when:
- Scores are submitted (via API, RabbitMQ, or WebSocket)
- New games are started
- Players are added or removed
- Game state changes

This is implemented using WebSocket (Socket.IO) technology. See [docs/AUTO_REFRESH.md](docs/AUTO_REFRESH.md) for detailed documentation.

## Troubleshooting

### Authentication Issues

**Cannot login / "Invalid credentials"**:
- Verify user exists in WSO2 Console
- Check username and password
- Ensure user has a role assigned
- See [QUICK_START.md](QUICK_START.md#troubleshooting)

**"WSO2 Client ID not configured"**:
- Run `./configure-wso2-roles.sh`
- Update `.env` with Client ID and Secret
- Restart services

**"403 Forbidden" on control panel**:
- Verify user has Game Master or Admin role
- Check role assignment in WSO2 Console
- See [docs/AUTHENTICATION_SETUP.md](docs/AUTHENTICATION_SETUP.md#troubleshooting)

**"Invalid redirect URI"**:
- Verify callback URL in WSO2 OAuth2 app: `http://localhost:5000/callback`
- Check `WSO2_REDIRECT_URI` in `.env`

### Application Issues

**UI Not Automatically Refreshing?**:
- Check browser console for WebSocket connection errors
- Verify Socket.IO client library is loaded
- Visit http://localhost:5000/test-refresh to test the connection
- See [docs/AUTO_REFRESH.md](docs/AUTO_REFRESH.md) for detailed troubleshooting

**RabbitMQ Connection Issues**:
- Ensure RabbitMQ is running: `sudo systemctl status rabbitmq-server`
- Check firewall settings
- Verify credentials in `.env` file

**WebSocket Connection Issues**:
- Check browser console for errors
- Ensure Flask server is running
- Try disabling browser extensions

**Game Logic Issues**:
- Check server console for error messages
- Verify score message format
- Use the control panel to manually test game logic

**Services won't start**:
- Check Docker is running
- Verify ports are available (5000, 8080, 9443, 5672, 15672)
- Check Docker resources (4GB+ RAM recommended)
- View logs: `docker-compose -f docker-compose-wso2.yml logs -f`

---

## 📚 Documentation

### Quick Start & Setup
- **[QUICK_START.md](QUICK_START.md)** - Get started in 5 steps
- **[BANNER.txt](BANNER.txt)** - System overview and quick reference

### Authentication & Security
- **[AUTHENTICATION_SETUP.md](docs/AUTHENTICATION_SETUP.md)** - Complete authentication guide (500+ lines)
- **[AUTHENTICATION_FLOW.md](docs/AUTHENTICATION_FLOW.md)** - Visual flow diagrams
- **[AUTHENTICATION_SUMMARY.md](AUTHENTICATION_SUMMARY.md)** - Implementation overview

### Documentation Index
- **[docs/README.md](docs/README.md)** - Complete documentation index

### Helper Scripts
- **`./start-with-auth.sh`** - Quick start with health checks
- **`./configure-wso2-roles.sh`** - Interactive WSO2 configuration
- **`./test-authentication.sh`** - Authentication testing

---

## 🚀 Service URLs

| Service | URL | Credentials | Purpose |
|---------|-----|-------------|---------|
| **Darts Game** | http://localhost:5000 | WSO2 users | Main application |
| **WSO2 Console** | https://localhost:9443/carbon | admin / admin | Identity management |
| **RabbitMQ** | http://localhost:15672 | guest / guest | Message broker |
| **API Gateway** | http://localhost:8080 | Token required | REST API |

---

## 🧪 Testing

### Automated Tests
```bash
# Test authentication
./test-authentication.sh

# Test auto-refresh
python examples/test_auto_refresh.py

# Test RabbitMQ
python test_rabbitmq.py
```

### Manual Testing
1. Login with each role (player, gamemaster, admin)
2. Verify access control works correctly
3. Test game functionality
4. Test logout

**See [docs/AUTHENTICATION_SETUP.md](docs/AUTHENTICATION_SETUP.md#testing-the-setup) for detailed test procedures.**

---

## 📦 Project Structure

```
dartserver-pythonapp/
├── app.py                          # Main Flask application
├── auth.py                         # Authentication module (NEW!)
├── game_manager.py                 # Game logic manager
├── rabbitmq_consumer.py            # RabbitMQ consumer
├── requirements.txt                # Python dependencies
├── .env.example                    # Environment variables template
├── docker-compose-wso2.yml         # Docker Compose with WSO2 (NEW!)
├── QUICK_START.md                  # Quick start guide (NEW!)
├── AUTHENTICATION_SUMMARY.md       # Auth implementation summary (NEW!)
├── BANNER.txt                      # System banner (NEW!)
├── start-with-auth.sh              # Quick start script (NEW!)
├── configure-wso2-roles.sh         # WSO2 configuration helper (NEW!)
├── test-authentication.sh          # Authentication testing (NEW!)
├── docs/
│   ├── README.md                   # Documentation index (NEW!)
│   ├── AUTHENTICATION_SETUP.md     # Complete auth guide (NEW!)
│   ├── AUTHENTICATION_FLOW.md      # Flow diagrams (NEW!)
│   └── AUTO_REFRESH.md             # Auto-refresh documentation
├── games/
│   ├── __init__.py
│   ├── game_301.py                 # 301/401/501 game logic
│   └── game_cricket.py             # Cricket game logic
├── templates/
│   ├── index.html                  # Main game board (updated)
│   ├── control.html                # Control panel (updated)
│   ├── login.html                  # Login page (NEW!)
│   └── test_refresh.html           # Auto-refresh test page
├── examples/
│   ├── api_examples.py             # API usage examples
│   ├── test_auto_refresh.py        # Auto-refresh test script
│   └── websocket_client.py         # WebSocket client example
└── static/
    ├── css/
    │   ├── style.css               # Main styles (updated)
    │   └── control.css             # Control panel styles (updated)
    └── js/
        ├── main.js                 # Main game board JavaScript
        └── control.js              # Control panel JavaScript
```

---

## 🔒 Security Notes

### Development Mode (Current)
⚠️ The current configuration is for **development only**:
- Self-signed SSL certificates (verification disabled)
- HTTP instead of HTTPS for the app
- Default admin credentials for introspection
- `SESSION_COOKIE_SECURE=False`

### Production Deployment
🔒 For production, you **must**:
- Enable HTTPS with valid SSL certificates
- Set `SESSION_COOKIE_SECURE=True`
- Generate strong `SECRET_KEY`
- Create dedicated service account for introspection
- Enable SSL verification
- Configure firewall rules
- Set up monitoring and logging

**See [docs/AUTHENTICATION_SETUP.md](docs/AUTHENTICATION_SETUP.md#production-deployment) for complete production guide.**

---

## License

See LICENSE file in the root directory.
