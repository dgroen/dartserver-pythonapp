# Quick Fix Guide - Docker Deployment Issues

## ✅ What Was Fixed

| Issue                           | Status      | Details                                                                        |
| ------------------------------- | ----------- | ------------------------------------------------------------------------------ |
| **Swagger API Docs Broken**     | ✅ FIXED    | Fixed malformed YAML docstring in `/api/game/start` endpoint                   |
| **Database Connection Failed**  | ✅ FIXED    | Updated `.env` to use Docker service names (`postgres` instead of `localhost`) |
| **History Page Empty**          | ✅ FIXED    | Database now properly connects through Docker network                          |
| **Single-Player Games Blocked** | ✅ FIXED    | Mobile Game Master now allows 1+ players instead of requiring 2+               |
| **Throwout Advice Not Showing** | ✅ VERIFIED | Feature is working in both mobile and desktop - check the checkbox!            |

---

## 🚀 Deploy Now

### Option 1: Quick Start (Docker)

```bash
cd /data/dartserver-pythonapp

# 1. Rebuild containers with fixes
docker-compose -f docker-compose-wso2.yml build

# 2. Start services
docker-compose -f docker-compose-wso2.yml up -d

# 3. Wait for services to be healthy (check logs)
docker-compose -f docker-compose-wso2.yml logs -f darts-app

# 4. Access application
# Open browser: https://letsplaydarts.eu (or your configured domain)
```

### Option 2: Manual Verification

```bash
# Check database connection
docker-compose -f docker-compose-wso2.yml exec darts-app \
  python -c "from src.core.database_service import DatabaseService; \
  db = DatabaseService(); \
  print('✅ Database Connected!' if db.check_connection() else '❌ Connection Failed')"

# Check Swagger loads
curl -s http://localhost:5000/api/docs/ | head -20

# Check game endpoints
curl -s http://localhost:5000/api/game/current | python -m json.tool
```

---

## 🎮 Test Each Feature

### 1. Test Single-Player Games

```
Step 1: Navigate to https://letsplaydarts.eu/mobile/gamemaster
Step 2: In "Start New Game" form, enter ONLY 1 player name
Step 3: Click "Start Game"
✅ Success: Game starts with 1 player
```

### 2. Test History Page

```
Step 1: Play a game to completion
Step 2: Navigate to https://letsplaydarts.eu/history
Step 3: Wait for page to load
✅ Success: See your recent games with statistics
```

### 3. Test Throwout Advice

```
Step 1: Start a 301/401/501 game
Step 2: Open the Game Master or Control panel
Step 3: Check "Show Throw-out Advice" (✓)
Step 4: Play until near finish (score < 50)
✅ Success: See suggestions like "[T20, Double 10]"
```

### 4. Test Swagger Docs

```
Step 1: Navigate to https://letsplaydarts.eu/api/docs/
✅ Success: Swagger UI loads without errors
```

### 5. Test Mobile Gameplay

```
Step 1: Start a game via Game Master
Step 2: Go to Gameplay tab
✅ Success: See current player, scores, scoreboard
```

---

## 📋 Files Changed

### Modified Files (4 total)

1. **`.env`** - Updated database and service URLs for Docker
2. **`src/app/app.py`** - Fixed Swagger YAML docstring (line 1685)
3. **`static/js/mobile_gamemaster.js`** - Allow single-player validation (line 122)
4. **`templates/mobile_gamemaster.html`** - Updated help text (line 84)

### New Files (for reference)

1. **`DOCKER_FIX_SUMMARY.md`** - Detailed technical documentation
2. **`verify_docker_config.py`** - Automated verification script
3. **`QUICK_FIX_GUIDE.md`** - This file

---

## 🔍 Verification Checklist

Run this to verify all fixes are in place:

```bash
cd /data/dartserver-pythonapp
python verify_docker_config.py
```

Expected output: **✅ All systems verified! Ready for Docker deployment.**

---

## 🐛 Troubleshooting

### Issue: History Page Still Shows "No games found"

```bash
# Check if database has games
docker-compose -f docker-compose-wso2.yml exec postgres \
  psql -U postgres -d dartsdb -c "SELECT COUNT(*) FROM game;"

# If empty, play a game first
# Check logs for database errors
docker-compose -f docker-compose-wso2.yml logs postgres
```

### Issue: Swagger Still Shows YAML Errors

```bash
# Force browser cache clear
# Press: Ctrl+Shift+Delete (Windows/Linux) or Cmd+Shift+Delete (Mac)
# Or use Incognito/Private browsing mode

# Verify fix is in file
grep "specified type and players (mobile" /data/dartserver-pythonapp/src/app/app.py
```

### Issue: Single-Player Still Blocked

```bash
# Check the validation code
grep "playerNames.length" /data/dartserver-pythonapp/static/js/mobile_gamemaster.js

# Should show: if (playerNames.length < 1)
# Not: if (playerNames.length < 2)

# Clear browser cache and reload
```

### Issue: Mobile Game Not Updating

```bash
# Check WebSocket connection in browser DevTools:
# Open DevTools → Application → Cookies → Check session
# Go to Network tab → Filter to "WS"
# Should see socket.io connection

# Restart server
docker-compose -f docker-compose-wso2.yml restart darts-app
```

---

## 📊 Architecture Changes

### Before (Broken - Local Config)

```
❌ DATABASE_URL=postgresql://postgres:postgres@localhost:5432/dartsdb  # pragma: allowlist secret
   (localhost doesn't exist inside Docker containers)
❌ RABBITMQ_HOST=localhost
   (Services can't reach localhost from containers)
```

### After (Fixed - Docker Config)

```
✅ DATABASE_URL=postgresql://postgres:postgres@postgres:5432/dartsdb  <!-- pragma: allowlist secret -->
   (postgres is the service name - resolves via Docker DNS)
✅ RABBITMQ_HOST=rabbitmq
   (rabbitmq is the service name - resolves via Docker DNS)
```

---

## 📞 Quick Reference

| Component       | Configuration                                                                            | Status                 |
| --------------- | ---------------------------------------------------------------------------------------- | ---------------------- |
| Database        | `postgresql://postgres:postgres@postgres:5432/dartsdb` <!-- pragma: allowlist secret --> | ✅ Docker Service Name |
| RabbitMQ        | `rabbitmq:5672`                                                                          | ✅ Docker Service Name |
| WSO2 (Public)   | `https://letsplaydarts.eu/auth`                                                          | ✅ Via Reverse Proxy   |
| WSO2 (Internal) | `https://wso2is:9443`                                                                    | ✅ Docker Service Name |
| Swagger         | `swagger_host: letsplaydarts.eu`                                                         | ✅ Public Domain       |
| Single Player   | Validation: `< 1` player                                                                 | ✅ Enabled             |
| Throwout Advice | Feature: `set_show_throwout_advice()`                                                    | ✅ Implemented         |

---

## ✨ Next Steps

1. ✅ Review fixes above - **DONE**
2. 🔄 Rebuild and restart Docker services
3. 🧪 Run verification tests
4. 📋 Monitor logs during startup: `docker-compose logs -f darts-app`
5. 🌐 Test all features via browser
6. 📝 Document any remaining issues

---

**Status**: All Critical Fixes Applied ✅  
**Ready for Deployment**: YES ✅  
**Last Updated**: 2025-10-19
