# Mobile App Guide

## Overview

The Darts Mobile App is a Progressive Web App (PWA) that allows users to connect dartboards, manage gameplay, and track game results from their mobile devices.

## Features

### 1. **Gameplay** (`/mobile/gameplay`)

- Real-time game monitoring
- Live scoreboard updates
- Current player display
- Last throw information
- WebSocket-based live updates

### 2. **Game Master** (`/mobile/gamemaster`)

- Start new games (301, 501, Cricket)
- Configure game settings (double out, etc.)
- Manage players
- Control game flow (next player, end game)
- Real-time game control

### 3. **Dartboard Setup** (`/mobile/dartboard-setup`)

- Register new dartboards
- Generate unique dartboard IDs
- Create WPA keys for secure connection
- Name dartboards for easy identification

### 4. **Game Results** (`/mobile/results`)

- View all completed games
- Filter by game type
- See player rankings and scores
- View game duration and statistics

### 5. **Account Management** (`/mobile/account`)

- Manage API keys for dartboard authentication
- View registered dartboards
- Monitor dartboard connection status
- Revoke/delete API keys and dartboards

### 6. **Hotspot Control** (`/mobile/hotspot`)

- Configure mobile hotspot for dartboard connectivity
- Platform-specific instructions (Android/iOS)
- Activate/deactivate hotspot configurations
- Manage dartboard connection credentials

## Installation

### As a PWA (Recommended)

1. Open the app in your mobile browser: `https://your-server.com/mobile`
2. Look for the "Install App" prompt or "Add to Home Screen" option
3. Follow the browser-specific installation steps:
   - **Chrome (Android)**: Tap the menu → "Add to Home screen"
   - **Safari (iOS)**: Tap Share → "Add to Home Screen"
4. The app will be installed and can be launched like a native app

### Web Browser Access

Simply navigate to `https://your-server.com/mobile` in any modern mobile browser.

## Dartboard Connectivity

### How It Works

1. Each dartboard has a unique ID (e.g., `DART-ABC123`)
2. The dartboard searches for a WiFi hotspot with its ID as the SSID
3. Users create a mobile hotspot with the dartboard ID and WPA key
4. The dartboard connects through this hotspot
5. Scores are sent to the app via API with API key authentication

### Setup Process

1. **Register Dartboard**:
   - Go to "Dartboard Setup"
   - Enter or generate a unique dartboard ID
   - Create or generate a WPA key
   - Save the dartboard

2. **Configure Hotspot**:
   - Go to "Hotspot Control"
   - Enter the dartboard ID as SSID
   - Enter the WPA key
   - Activate the configuration

3. **Create Mobile Hotspot**:
   - Follow platform-specific instructions
   - Use the dartboard ID as the hotspot name
   - Use the WPA key as the password

4. **Connect Dartboard**:
   - Power on the dartboard
   - It will automatically search for and connect to the hotspot
   - Connection status will update in the Account page

## API Authentication

### For Dartboards

Dartboards use API key authentication:

```bash
curl -X POST https://your-server.com/api/dartboard/score \
  -H "X-API-Key: your-api-key-here" \
  -H "Content-Type: application/json" \
  -d '{"dartboard_id": "DART-ABC123", "score": 180}'
```

### API Endpoints

- `POST /api/dartboard/connect` - Register dartboard connection
- `POST /api/dartboard/score` - Submit score from dartboard
- `GET /api/mobile/dartboards` - List user's dartboards
- `POST /api/mobile/dartboards` - Register new dartboard
- `GET /api/mobile/apikeys` - List API keys
- `POST /api/mobile/apikeys` - Generate new API key
- `GET /api/mobile/hotspot` - Get hotspot configuration
- `POST /api/mobile/hotspot` - Save hotspot configuration

## Offline Support

The mobile app includes offline capabilities:

- **Service Worker**: Caches app resources for offline access
- **Offline Queue**: Stores requests when offline and syncs when connection is restored
- **Offline Indicator**: Shows when the device is offline
- **Auto-sync**: Automatically syncs data when connection is restored

## Database Schema

### New Tables

1. **Dartboard**
   - `id`: Primary key
   - `player_id`: Foreign key to Player
   - `dartboard_id`: Unique dartboard identifier
   - `wpa_key`: WiFi password
   - `name`: Optional friendly name
   - `is_connected`: Connection status
   - `last_connected_at`: Last connection timestamp

2. **ApiKey**
   - `id`: Primary key
   - `player_id`: Foreign key to Player
   - `key_hash`: Hashed API key
   - `key_prefix`: First 8 characters for display
   - `name`: Optional key name
   - `is_active`: Active status
   - `last_used_at`: Last usage timestamp

3. **HotspotConfig**
   - `id`: Primary key
   - `player_id`: Foreign key to Player
   - `dartboard_id`: SSID for hotspot
   - `wpa_key`: Hotspot password
   - `is_active`: Active status

### Player Table Extensions

- `username`: Unique username
- `email`: Email address

## Database Migration

Run the migration to create the new tables:

```bash
# Upgrade to latest
alembic upgrade head

# Rollback if needed
alembic downgrade -1
```

## Security

- **API Keys**: Securely hashed using SHA-256
- **HTTPS**: All communication should use HTTPS
- **Session Management**: Integrated with WSO2 Identity Server OAuth2
- **WPA Keys**: Stored encrypted in database
- **CORS**: Configured for mobile app domain

## Development

### File Structure

```
/templates/
  mobile.html                    # Main mobile app page
  mobile_gameplay.html           # Gameplay interface
  mobile_gamemaster.html         # Game control page
  mobile_dartboard_setup.html    # Dartboard registration
  mobile_results.html            # Game results
  mobile_account.html            # Account management
  mobile_hotspot.html            # Hotspot control

/static/css/
  mobile.css                     # Mobile app styles

/static/js/
  mobile.js                      # Main app JavaScript
  mobile_gameplay.js             # Gameplay logic
  mobile_gamemaster.js           # Game control logic
  mobile_dartboard_setup.js      # Dartboard setup logic
  mobile_results.js              # Results display logic
  mobile_account.js              # Account management logic
  mobile_hotspot.js              # Hotspot control logic

/static/
  manifest.json                  # PWA manifest
  service-worker.js              # Service worker for offline support

/src/
  mobile_service.py              # Mobile service business logic

/alembic/versions/
  d55f29e75045_add_mobile_app_tables.py  # Database migration
```

### Adding New Features

1. Update `src/mobile_service.py` for business logic
2. Add API endpoints in `app.py`
3. Create/update templates in `/templates/`
4. Add JavaScript logic in `/static/js/`
5. Update styles in `/static/css/mobile.css`

## Troubleshooting

### Dartboard Won't Connect

1. Verify hotspot is active with correct SSID and password
2. Check dartboard is powered on and searching for WiFi
3. Ensure dartboard ID matches exactly (case-sensitive)
4. Check API key is active in Account page

### App Won't Install as PWA

1. Ensure HTTPS is enabled
2. Check manifest.json is accessible
3. Verify service worker is registered
4. Try clearing browser cache

### Offline Sync Not Working

1. Check browser console for errors
2. Verify service worker is active
3. Check IndexedDB for queued requests
4. Try re-registering service worker

## Browser Support

- **Chrome/Edge**: Full support (Android/Desktop)
- **Safari**: Full support (iOS/macOS)
- **Firefox**: Full support (Android/Desktop)
- **Opera**: Full support

## Future Enhancements

- [ ] Push notifications for game events
- [ ] Native mobile app wrapper (React Native/Flutter)
- [ ] Automatic hotspot creation (requires native app)
- [ ] Bluetooth dartboard connectivity
- [ ] Multi-dartboard support
- [ ] Tournament mode
- [ ] Social features (friends, challenges)
- [ ] Statistics and analytics dashboard

## Support

For issues or questions:

1. Check the troubleshooting section above
2. Review API documentation at `/api/docs`
3. Check server logs for errors
4. Contact system administrator
