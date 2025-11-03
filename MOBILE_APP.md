# 🎯 Darts Mobile Progressive Web App

## Overview

The Darts Mobile App is a **Progressive Web App (PWA)** that provides a complete mobile experience for dartboard connectivity, game management, and real-time score tracking. Install it on your mobile device's home screen for a native app-like experience!

## ✨ Key Features

### 🎮 For Players
- **Real-time Gameplay** - Watch live games with instant score updates
- **Dartboard Connectivity** - Connect physical dartboards via mobile hotspot
- **Game History** - View complete game history and statistics
- **Offline Support** - Core features work without internet connection
- **Install as App** - Add to home screen for native app experience

### 👑 For Game Masters
- **Full Game Control** - Start, pause, and manage games
- **Player Management** - Add and remove players during gameplay
- **Manual Score Entry** - Enter scores manually when needed
- **Live Scoreboard** - Real-time score tracking for all players
- **Game State Management** - Complete visibility into game state

### 🔧 Technical Features
- **Progressive Web App (PWA)** - Installable on iOS and Android
- **Offline-First Design** - Service worker caching for offline use
- **Real-time Updates** - WebSocket-based live updates
- **OAuth2 Authentication** - Secure login with WSO2
- **API Key Management** - Secure dartboard authentication
- **Responsive Design** - Optimized for all screen sizes

## 🚀 Quick Start

### 1. Access the Mobile App

Open in your mobile browser:
```
https://your-server.com/mobile
```

Or for local development:
```
http://localhost:5000/mobile
```

### 2. Login

- Use your WSO2 credentials
- Or use test accounts (if configured):
  - `testplayer` / `Player@123` (Player role)
  - `testgamemaster` / `GameMaster@123` (Game Master role)

### 3. Install as PWA (Optional)

**On Android:**
1. Tap the menu (⋮) in your browser
2. Select "Add to Home Screen"
3. Tap "Install"

**On iOS:**
1. Tap the Share button
2. Select "Add to Home Screen"
3. Tap "Add"

## 📱 App Sections

### 🏠 Home (`/mobile`)
- Quick access to all features
- Connection status indicator
- Navigation menu

### 🎮 Gameplay (`/mobile/gameplay`)
- View current active game
- Watch live scores and player turns
- See all active games
- Get finishing suggestions (throw-out advice)

### 👑 Game Master (`/mobile/gamemaster`)
- Start new games (301, 501, Cricket, etc.)
- Add/remove players
- Control game flow
- Submit manual scores
- View game state

### 🎯 Dartboard Setup (`/mobile/dartboard-setup`)
- Register new dartboards
- Configure dartboard settings
- Manage dartboard IDs
- Setup instructions

### 📊 Results (`/mobile/results`)
- View game history
- See leaderboards
- Filter by game type
- View player statistics

### ⚙️ Account (`/mobile/account`)
- Manage API keys for dartboards
- View registered dartboards
- Account settings

### 📡 Hotspot Control (`/mobile/hotspot`)
- Configure mobile hotspot for dartboards
- Setup instructions for Android/iOS
- Manage hotspot configurations

## 🔌 Dartboard Connectivity

### How It Works

```
1. Register Dartboard
   └─ Get unique ID (e.g., DART-ABC123)
   └─ Get WPA key for security

2. Create Mobile Hotspot
   └─ SSID: Your dartboard ID
   └─ Password: Your WPA key
   └─ Turn on hotspot

3. Dartboard Connects
   └─ Automatically finds and connects
   └─ Uses API key for authentication
   └─ Sends scores in real-time

4. Play Darts!
   └─ Scores appear instantly
   └─ All players see updates
   └─ Game automatically managed
```

### Setup Guide

1. **Register Dartboard**
   - Go to **Dartboard Setup**
   - Enter a unique dartboard ID
   - Generate or enter a WPA key
   - Save the configuration

2. **Create API Key**
   - Go to **Account**
   - Click "Create New API Key"
   - Copy the key (shown only once!)
   - Configure your dartboard with this key

3. **Setup Mobile Hotspot**
   - Go to **Hotspot Control**
   - Follow platform-specific instructions
   - Use dartboard ID as SSID
   - Use WPA key as password

4. **Connect Dartboard**
   - Turn on your dartboard
   - It will auto-connect to hotspot
   - Verify connection in app

## 🛠️ For Developers

### Architecture

```
┌─────────────────┐
│   Mobile PWA    │  (Frontend: HTML/CSS/JS)
│  /mobile/*      │
└────────┬────────┘
         │
         │ HTTP/WebSocket
         │
┌────────▼────────┐
│   Flask App     │  (Backend: Python/Flask)
│  src/app/app.py │
└────────┬────────┘
         │
         ├─────────────┬──────────────┐
         │             │              │
┌────────▼────────┐ ┌─▼─────────┐ ┌──▼──────────┐
│   Database      │ │ RabbitMQ  │ │   WSO2 IS   │
│  PostgreSQL     │ │ (Scores)  │ │   (Auth)    │
└─────────────────┘ └───────────┘ └─────────────┘
```

### Key Technologies

- **Frontend**: Vanilla JavaScript, Socket.IO client
- **Backend**: Flask, Flask-SocketIO, SQLAlchemy
- **Database**: PostgreSQL with Alembic migrations
- **Messaging**: RabbitMQ for dart score events
- **Authentication**: WSO2 Identity Server (OAuth2)
- **PWA**: Service Worker, Web App Manifest

### API Endpoints

#### Mobile Pages (Session Auth Required)
- `GET /mobile` - Main app
- `GET /mobile/gameplay` - Gameplay interface
- `GET /mobile/gamemaster` - Game control panel
- `GET /mobile/dartboard-setup` - Dartboard registration
- `GET /mobile/results` - Game history
- `GET /mobile/account` - Account management
- `GET /mobile/hotspot` - Hotspot configuration

#### API Endpoints (Session or API Key Auth)
- `GET /api/mobile/apikeys` - List user's API keys
- `POST /api/mobile/apikeys` - Create new API key
- `DELETE /api/mobile/apikeys/<id>` - Delete API key
- `GET /api/mobile/dartboards` - List user's dartboards
- `POST /api/mobile/dartboards` - Register dartboard
- `DELETE /api/mobile/dartboards/<id>` - Delete dartboard
- `GET /api/mobile/hotspots` - List hotspot configs
- `POST /api/mobile/hotspots` - Create hotspot config
- `PUT /api/mobile/hotspots/<id>` - Update hotspot
- `DELETE /api/mobile/hotspots/<id>` - Delete hotspot

#### Game API (Used by Mobile App)
- `GET /api/game/current` - Get current game state
- `POST /api/game/start` - Start new game
- `POST /api/score` - Submit score
- `GET /api/game/history` - Get game history
- `GET /api/players` - Get all players

### WebSocket Events

**Client → Server:**
- `new_game` - Start new game
- `manual_score` - Submit manual score
- `add_player` - Add player to game
- `remove_player` - Remove player from game
- `next_player` - Move to next player

**Server → Client:**
- `game_update` - Game state updated
- `game_started` - New game started
- `game_end` - Game ended
- `score_update` - Score submitted
- `player_added` - Player added
- `player_removed` - Player removed
- `error` - Error occurred

### File Structure

```
dartserver-pythonapp/
├── templates/
│   ├── mobile.html                 # Main mobile app
│   ├── mobile_gameplay.html        # Gameplay view
│   ├── mobile_gamemaster.html      # Game control
│   ├── mobile_dartboard_setup.html # Dartboard registration
│   ├── mobile_results.html         # Game history
│   ├── mobile_account.html         # Account management
│   └── mobile_hotspot.html         # Hotspot configuration
├── static/
│   ├── css/
│   │   ├── mobile.css              # Main mobile styles
│   │   └── mobile_gamemaster.css   # Game master styles
│   ├── js/
│   │   ├── mobile.js               # Main mobile app JS
│   │   ├── mobile_gameplay.js      # Gameplay functionality
│   │   ├── mobile_gamemaster.js    # Game control logic
│   │   ├── mobile_dartboard_setup.js # Dartboard registration
│   │   ├── mobile_results.js       # Results and history
│   │   ├── mobile_account.js       # Account management
│   │   └── mobile_hotspot.js       # Hotspot configuration
│   ├── icons/                      # PWA icons (72x72 to 512x512)
│   ├── manifest.json               # PWA manifest
│   └── service-worker.js           # Service worker for offline
├── src/
│   └── app/
│       ├── app.py                  # Main Flask app with routes
│       └── mobile_service.py       # Mobile business logic
└── docs/
    ├── MOBILE_APP_START_HERE.md    # Quick start guide
    ├── MOBILE_APP_GUIDE.md         # Complete user guide
    ├── MOBILE_APP_DEPLOYMENT.md    # Deployment instructions
    └── [20+ more mobile docs]      # Extensive documentation
```

## 📚 Documentation

### Getting Started
- **[MOBILE_APP_START_HERE.md](docs/MOBILE_APP_START_HERE.md)** - Start here for quick overview
- **[MOBILE_APP_QUICKSTART.md](docs/MOBILE_APP_QUICKSTART.md)** - 5-minute quick start guide
- **[MOBILE_APP_GUIDE.md](docs/MOBILE_APP_GUIDE.md)** - Complete user manual

### Installation & Setup
- **[MOBILE_APP_ANDROID_INSTALLATION.md](docs/MOBILE_APP_ANDROID_INSTALLATION.md)** - Android install guide
- **[MOBILE_APP_INSTALL_QUICK_GUIDE.md](docs/MOBILE_APP_INSTALL_QUICK_GUIDE.md)** - Quick install reference
- **[MOBILE_APP_DEPLOYMENT.md](docs/MOBILE_APP_DEPLOYMENT.md)** - Production deployment

### Technical Documentation
- **[MOBILE_APP_IMPLEMENTATION.md](docs/MOBILE_APP_IMPLEMENTATION.md)** - Implementation details
- **[MOBILE_GAMEMASTER_IMPLEMENTATION.md](docs/MOBILE_GAMEMASTER_IMPLEMENTATION.md)** - Game Master features
- **[PWA_MENU_FIXES.md](docs/PWA_MENU_FIXES.md)** - PWA menu implementation

### Reference
- **[MOBILE_APP_QUICK_REFERENCE.md](docs/MOBILE_APP_QUICK_REFERENCE.md)** - Quick reference card
- **[MOBILE_GAMEMASTER_UI_REFERENCE.md](docs/MOBILE_GAMEMASTER_UI_REFERENCE.md)** - Game Master UI reference
- **[MOBILE_APP_CHECKLIST.md](docs/MOBILE_APP_CHECKLIST.md)** - Implementation checklist

### Status & Summary
- **[MOBILE_APP_COMPLETE.md](docs/MOBILE_APP_COMPLETE.md)** - Completion status
- **[MOBILE_APP_FINAL_SUMMARY.md](docs/MOBILE_APP_FINAL_SUMMARY.md)** - Final summary
- **[MOBILE_APP_IMPROVEMENTS_SUMMARY.md](docs/MOBILE_APP_IMPROVEMENTS_SUMMARY.md)** - Improvements log

## 🧪 Testing

### Manual Testing

1. **Access mobile app**
   ```bash
   # Start the server
   python run.py
   
   # Open in browser
   http://localhost:5000/mobile
   ```

2. **Test PWA installation**
   - Open on mobile device
   - Look for "Add to Home Screen" prompt
   - Install and verify offline functionality

3. **Test features**
   - Login with test credentials
   - Navigate between sections
   - Start a game as Game Master
   - View game on Gameplay page
   - Submit manual scores
   - View results

### Automated Testing

```bash
# Run mobile app tests
python helpers/test_mobile_app.py

# Run full test suite
python -m pytest tests/ -v -m "mobile"
```

### Test Dartboard Connection

```bash
# Create API key via web interface
# Then test dartboard score submission

curl -X POST http://localhost:5000/api/score \
  -H "Content-Type: application/json" \
  -H "X-API-Key: your-api-key-here" \
  -d '{
    "score": 20,
    "multiplier": "TRIPLE"
  }'
```

## 🔒 Security

### Authentication

- **User Authentication**: OAuth2 via WSO2 Identity Server
- **Dartboard Authentication**: API keys with SHA-256 hashing
- **Session Management**: Secure HTTP-only cookies
- **HTTPS Required**: For production PWA installation

### Authorization

- **Player Role**: Can view games and submit scores
- **Game Master Role**: Can control games and manage players
- **Admin Role**: Full system access

### Best Practices

- API keys are hashed before storage
- Sessions expire after inactivity
- HTTPS enforced in production
- CORS configured for specific origins
- Rate limiting on API endpoints (recommended)

## 🚢 Deployment

### Prerequisites

- Python 3.10+
- PostgreSQL database
- HTTPS certificate (required for PWA)
- WSO2 Identity Server (for authentication)
- RabbitMQ (for dart score events)

### Quick Deploy

```bash
# 1. Clone repository
git clone https://github.com/yourusername/dartserver-pythonapp.git
cd dartserver-pythonapp

# 2. Install dependencies
python -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate
pip install -r requirements.txt

# 3. Configure environment
cp .env.example .env
# Edit .env with your settings

# 4. Run database migrations
alembic upgrade head

# 5. Start server
python run.py
```

### Production Deployment

See **[MOBILE_APP_DEPLOYMENT.md](docs/MOBILE_APP_DEPLOYMENT.md)** for complete production deployment guide including:

- HTTPS setup with Let's Encrypt
- Nginx reverse proxy configuration
- Systemd service configuration
- Database backup strategy
- Performance optimization
- Security hardening

## 📱 PWA Features

### Offline Support

The app uses a service worker to cache essential resources:

- HTML templates for all mobile pages
- CSS stylesheets
- JavaScript files
- PWA icons and manifest
- API responses (cached with network-first strategy)

### Installation

When installed as a PWA, the app provides:

- **Standalone Display**: Runs in its own window without browser UI
- **App Icon**: Appears on home screen with custom icon
- **Splash Screen**: Custom splash screen on launch
- **Offline Access**: Core features work without network
- **Push Notifications**: (Future enhancement)

### Manifest Configuration

The `manifest.json` includes:

- App name and short name
- Start URL (`/mobile`)
- Display mode (standalone)
- Theme color (#1e3c72)
- Multiple icon sizes (72x72 to 512x512)
- App shortcuts (Start Game, View Results)

## 🐛 Troubleshooting

### PWA Won't Install

- **Verify HTTPS**: PWA requires HTTPS (except localhost)
- **Check manifest.json**: Should be accessible at `/static/manifest.json`
- **Verify service worker**: Should register at `/static/service-worker.js`
- **Check browser console**: Look for errors

### Connection Issues

- **WebSocket fails**: Check firewall allows WebSocket connections
- **API calls fail**: Verify CORS settings in `.env`
- **Login redirects**: Ensure WSO2 callback URL matches

### Dartboard Not Connecting

- **Check hotspot**: Verify mobile hotspot is active
- **Verify SSID**: Must match dartboard ID exactly
- **Check WPA key**: Must match configured key
- **Test API key**: Use curl to test API key authentication

### Offline Mode Issues

- **Clear cache**: Unregister service worker and re-register
- **Check cache list**: Verify all URLs in `urlsToCache` are valid
- **Test network**: Disable network to test offline functionality

## 🆘 Support

### Documentation

- Complete documentation in `docs/` directory
- 20+ markdown files covering all aspects
- Start with `docs/MOBILE_APP_START_HERE.md`

### Logs

```bash
# View application logs
tail -f /var/log/dartserver/app.log

# View error logs
tail -f /var/log/dartserver/error.log

# View access logs
tail -f /var/log/dartserver/access.log
```

### Common Commands

```bash
# Check database migration status
alembic current

# View API documentation
open http://localhost:5000/api/docs/

# Test server health
curl http://localhost:5000/health

# View current game state
curl http://localhost:5000/api/game/current
```

## 🎯 What's Next?

### Current Status: ✅ COMPLETE

The mobile app is fully functional with:
- ✅ 6 mobile pages (Home, Gameplay, Game Master, Dartboard Setup, Results, Account, Hotspot)
- ✅ PWA support (installable on iOS and Android)
- ✅ Offline functionality with service worker
- ✅ Real-time updates via WebSocket
- ✅ OAuth2 authentication
- ✅ API key management for dartboards
- ✅ Comprehensive documentation
- ✅ Test suite

### Future Enhancements (Optional)

- 🔮 Push notifications for game events
- 🔮 Pause/resume game API implementation
- 🔮 Background sync for offline scores
- 🔮 Advanced statistics and analytics
- 🔮 Multiplayer matchmaking
- 🔮 Tournament management
- 🔮 Voice commands
- 🔮 AR dartboard overlay

## 📄 License

See LICENSE file in the root directory.

## 🤝 Contributing

Contributions are welcome! Please read the contributing guidelines before submitting pull requests.

---

**Happy Darting! 🎯**

For questions or issues, please refer to the extensive documentation in the `docs/` directory or contact the development team.
