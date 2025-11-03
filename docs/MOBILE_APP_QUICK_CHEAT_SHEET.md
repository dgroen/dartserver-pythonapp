# 🎯 Mobile App Quick Reference Card

## Access Points

| Feature | URL | Description |
|---------|-----|-------------|
| Mobile Home | `/mobile` | Main mobile app dashboard |
| Gameplay | `/mobile/gameplay` | View active games and scores |
| Game Master | `/mobile/gamemaster` | Control games and players |
| Dartboard Setup | `/mobile/dartboard-setup` | Register dartboards |
| Results | `/mobile/results` | View game history |
| Account | `/mobile/account` | Manage API keys |
| Hotspot | `/mobile/hotspot` | Configure hotspot |

## Quick Commands

### Start Server
```bash
python run.py
```

### Test Mobile App
```bash
python examples/mobile_app_examples.py
```

### Check PWA Resources
```bash
curl http://localhost:5000/static/manifest.json
curl http://localhost:5000/static/service-worker.js
```

## API Key Authentication

### Create API Key (Web UI)
1. Login at `/mobile`
2. Go to `/mobile/account`
3. Click "Create New API Key"
4. Copy the key (shown once!)

### Use API Key
```bash
curl -X POST http://localhost:5000/api/score \
  -H "Content-Type: application/json" \
  -H "X-API-Key: YOUR_API_KEY" \
  -d '{"score": 20, "multiplier": "TRIPLE"}'
```

## Dartboard Registration

### Via Web UI
1. Go to `/mobile/dartboard-setup`
2. Enter dartboard ID (e.g., DART-ABC123)
3. Enter friendly name
4. Enter WPA key
5. Submit

### Via API
```bash
curl -X POST http://localhost:5000/api/mobile/dartboards \
  -H "Content-Type: application/json" \
  -H "Cookie: session=YOUR_SESSION" \
  -d '{
    "dartboard_id": "DART-ABC123",
    "name": "Living Room Board",
    "wpa_key": "secure-key-123"
  }'
```

## Mobile Hotspot Setup

### Android
```
Settings → Network & Internet → Hotspot
- Name: DART-ABC123 (your dartboard ID)
- Password: Your WPA key
- Turn On
```

### iOS
```
Settings → Personal Hotspot
- Turn On
- Password: Your WPA key
(Note: iOS doesn't allow custom SSID)
```

## PWA Installation

### Android Chrome
1. Open `/mobile` in Chrome
2. Tap menu (⋮)
3. Select "Add to Home Screen"
4. Tap "Install"

### iOS Safari
1. Open `/mobile` in Safari
2. Tap Share button
3. Select "Add to Home Screen"
4. Tap "Add"

## Common API Endpoints

| Method | Endpoint | Auth | Description |
|--------|----------|------|-------------|
| GET | `/api/game/current` | Session | Get current game |
| POST | `/api/game/start` | Session | Start new game |
| POST | `/api/score` | API Key | Submit score |
| GET | `/api/mobile/apikeys` | Session | List API keys |
| POST | `/api/mobile/apikeys` | Session | Create API key |
| GET | `/api/mobile/dartboards` | Session | List dartboards |
| POST | `/api/mobile/dartboards` | Session | Register dartboard |

## WebSocket Events

### Listen For (Server → Client)
- `game_update` - Game state changed
- `game_started` - New game started
- `game_end` - Game finished
- `score_update` - Score submitted
- `player_added` - Player joined
- `player_removed` - Player left

### Emit (Client → Server)
- `new_game` - Start game
- `manual_score` - Submit score
- `add_player` - Add player
- `remove_player` - Remove player
- `next_player` - Next turn

## Troubleshooting

### PWA Won't Install
- ✓ Check HTTPS (required except localhost)
- ✓ Verify manifest.json accessible
- ✓ Check service worker registers
- ✓ Look at browser console

### Connection Issues
- ✓ Check server is running
- ✓ Verify firewall allows port 5000
- ✓ Test with curl
- ✓ Check browser console

### Dartboard Not Connecting
- ✓ Hotspot active?
- ✓ SSID matches dartboard ID?
- ✓ WPA key correct?
- ✓ API key valid?

## File Locations

| Type | Path |
|------|------|
| Templates | `templates/mobile*.html` |
| JavaScript | `static/js/mobile*.js` |
| CSS | `static/css/mobile*.css` |
| Icons | `static/icons/icon-*.png` |
| Manifest | `static/manifest.json` |
| Service Worker | `static/service-worker.js` |
| Backend | `src/app/mobile_service.py` |
| Routes | `src/app/app.py` (search "mobile") |

## Documentation

| Document | Description |
|----------|-------------|
| `MOBILE_APP.md` | **START HERE** - Complete guide |
| `docs/MOBILE_APP_QUICKSTART.md` | 5-minute quick start |
| `docs/MOBILE_APP_GUIDE.md` | Full user manual |
| `docs/MOBILE_APP_DEPLOYMENT.md` | Production deployment |
| `examples/mobile_app_examples.py` | API examples & tests |

## Support

- **Test Suite**: `python examples/mobile_app_examples.py`
- **Logs**: Check browser console and server logs
- **Health Check**: `curl http://localhost:5000/health`
- **API Docs**: `http://localhost:5000/api/docs/`

---

**Need Help?** See [MOBILE_APP.md](../MOBILE_APP.md) for comprehensive documentation.
