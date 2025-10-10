# 🎯 Darts Mobile App - Quick Reference

## What Is This?

A Progressive Web App (PWA) that allows users to connect dartboards via mobile hotspot, manage gameplay, and track game results from their mobile devices.

## Quick Links

- **🚀 Quick Start**: [MOBILE_APP_QUICKSTART.md](MOBILE_APP_QUICKSTART.md) - Get started in 5 minutes!
- **📚 User Guide**: [docs/MOBILE_APP_GUIDE.md](docs/MOBILE_APP_GUIDE.md) - Complete user documentation
- **🏗️ Architecture**: [docs/MOBILE_APP_ARCHITECTURE.md](docs/MOBILE_APP_ARCHITECTURE.md) - System design & diagrams
- **🔧 Implementation**: [docs/MOBILE_APP_IMPLEMENTATION.md](docs/MOBILE_APP_IMPLEMENTATION.md) - Technical details
- **🚢 Deployment**: [MOBILE_APP_DEPLOYMENT.md](MOBILE_APP_DEPLOYMENT.md) - Production deployment guide
- **✅ Checklist**: [MOBILE_APP_CHECKLIST.md](MOBILE_APP_CHECKLIST.md) - Task checklist
- **📝 Summary**: [MOBILE_APP_COMPLETE.md](MOBILE_APP_COMPLETE.md) - Implementation summary

## Access the App

**URL**: `http://your-server:5000/mobile`

## Main Features

1. **🎮 Gameplay** - Real-time game monitoring
2. **👑 Game Master** - Control games and players
3. **🎯 Dartboard Setup** - Register dartboards
4. **📊 Results** - View game history
5. **⚙️ Account** - Manage API keys and dartboards
6. **📡 Hotspot** - Configure dartboard connectivity

## How Dartboard Connectivity Works

```
1. Register dartboard with unique ID (e.g., DART-ABC123)
2. Configure hotspot with dartboard ID as SSID
3. Create mobile hotspot on your phone
4. Dartboard connects to hotspot
5. Dartboard sends scores via API
6. App displays scores in real-time
```

## Quick Start

### 1. Register a Dartboard

```
Mobile App → Dartboard Setup
→ Generate ID (e.g., DART-ABC123)
→ Generate WPA Key
→ Register
```

### 2. Configure Hotspot

```
Mobile App → Hotspot Control
→ Enter Dartboard ID
→ Enter WPA Key
→ Save & Activate
```

### 3. Create Mobile Hotspot

**Android:**
```
Settings → Network & Internet → Hotspot
→ Name: DART-ABC123
→ Password: [WPA Key]
→ Turn On
```

**iOS:**
```
Settings → Personal Hotspot
→ Turn On
→ Password: [WPA Key]
(Note: iOS doesn't allow custom SSID)
```

### 4. Generate API Key

```
Mobile App → Account
→ Create New API Key
→ Copy the key (shown only once!)
→ Configure dartboard with this key
```

## API Endpoints

### For Web Users (Session Auth)
- `GET /mobile` - Main app
- `GET /mobile/gameplay` - Gameplay interface
- `GET /mobile/gamemaster` - Game control
- `GET /mobile/dartboard-setup` - Setup page
- `GET /mobile/results` - Results page
- `GET /mobile/account` - Account page
- `GET /mobile/hotspot` - Hotspot page

### For Dartboards (API Key Auth)
- `POST /api/dartboard/connect` - Register connection
- `POST /api/dartboard/score` - Submit score

**Example:**
```bash
curl -X POST http://your-server:5000/api/dartboard/score \
  -H "X-API-Key: your-api-key-here" \
  -H "Content-Type: application/json" \
  -d '{
    "dartboard_id": "DART-ABC123",
    "score": 180,
    "multiplier": 1,
    "segment": 20
  }'
```

## File Structure

```
/templates/          # Mobile HTML pages (7 files)
/static/css/         # Mobile styles (mobile.css)
/static/js/          # Mobile JavaScript (7 files)
/static/             # PWA files (manifest.json, service-worker.js)
/src/                # Mobile service layer (mobile_service.py)
/docs/               # Documentation
```

## Database Tables

- `dartboard` - Registered dartboards
- `api_key` - API keys for authentication
- `hotspot_config` - Hotspot configurations
- `player` - Extended with username and email

## Installation as PWA

### Android (Chrome)
1. Open app in Chrome
2. Tap menu → "Add to Home screen"
3. Confirm installation
4. Launch from home screen

### iOS (Safari)
1. Open app in Safari
2. Tap Share button
3. Tap "Add to Home Screen"
4. Confirm installation
5. Launch from home screen

## Testing

```bash
# 1. Check database migration
cd /data/dartserver-pythonapp
source .venv/bin/activate
alembic current  # Should show: d55f29e75045

# 2. Test imports
python3 -c "from src.mobile_service import MobileService; print('✅ OK')"

# 3. Start server
python app.py

# 4. Access app
# Open http://localhost:5000/mobile in browser
```

## Troubleshooting

### App won't load
- Check server is running: `python app.py`
- Check database is accessible
- Check browser console for errors

### PWA won't install
- Ensure HTTPS is enabled (required for PWA)
- Check manifest.json is accessible
- Check service worker is registered

### Dartboard won't connect
- Verify hotspot is active
- Check dartboard ID matches exactly
- Verify WPA key is correct
- Check API key is active

### API returns 401
- Ensure user is logged in (web endpoints)
- Verify API key is correct (dartboard endpoints)
- Check API key is active in Account page

## Documentation

| Document | Description |
|----------|-------------|
| [MOBILE_APP_QUICKSTART.md](MOBILE_APP_QUICKSTART.md) | 🚀 Quick start guide (5 minutes) |
| [MOBILE_APP_GUIDE.md](docs/MOBILE_APP_GUIDE.md) | 📚 Complete user guide |
| [MOBILE_APP_ARCHITECTURE.md](docs/MOBILE_APP_ARCHITECTURE.md) | 🏗️ Architecture & diagrams |
| [MOBILE_APP_IMPLEMENTATION.md](docs/MOBILE_APP_IMPLEMENTATION.md) | 🔧 Technical implementation |
| [MOBILE_APP_DEPLOYMENT.md](MOBILE_APP_DEPLOYMENT.md) | 🚢 Production deployment |
| [MOBILE_APP_COMPLETE.md](MOBILE_APP_COMPLETE.md) | 📝 Implementation summary |
| [MOBILE_APP_CHECKLIST.md](MOBILE_APP_CHECKLIST.md) | ✅ Task checklist |

## Status

✅ **Implementation**: COMPLETE
✅ **Database Migration**: APPLIED
✅ **Code Quality**: VERIFIED
⚠️ **Testing**: PENDING
⚠️ **Production**: PENDING (needs HTTPS, icons, testing)

## Next Steps

1. Create PWA icon assets (72x72 to 512x512)
2. Set up HTTPS for PWA installation
3. Test on real mobile devices
4. Test with dartboard hardware
5. Deploy to production

## Support

- Check documentation in `/docs/`
- Review API docs at `/api/docs`
- Check server logs in `/logs/`
- Review this README and linked documents

---

**Ready to test!** 🚀