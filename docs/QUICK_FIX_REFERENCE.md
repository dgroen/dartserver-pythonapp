# Quick Fix Reference - Game History & Mobile App Issues

## TL;DR - What Was Fixed Today

### 🎮 Game History Page (Web & Mobile)

**Problem**: Game history was empty even though games were logged  
**Root Cause**: NULL values in database causing SQL sort issues  
**Status**: ✅ FIXED (database_service.py uses COALESCE)

### 📱 Mobile App Wrong Player

**Problem**: Mobile app always showed player_id=1 instead of logged-in user  
**Root Cause**: 9 endpoints using wrong session key  
**Status**: ✅ FIXED (all endpoints now use `session.get('player_id')`)

### 🎯 Throwout Advice

**Problem**: Not appearing during gameplay  
**Status**: ✅ NO CHANGES NEEDED - Feature working correctly

---

## What Changed

### File 1: `src/app/app.py` - 9 Endpoints Fixed

```
Line 1227  ✅ get_mobile_api_keys()
Line 1264  ✅ create_api_key()
Line 1296  ✅ revoke_api_key()
Line 1330  ✅ get_user_dartboards()
Line 1377  ✅ register_dartboard()
Line 1412  ✅ delete_dartboard()
Line 1446  ✅ get_hotspot_configs()
Line 1495  ✅ create_hotspot_config()
Line 1539  ✅ toggle_hotspot()
```

All now use:

```python
player_id = session.get("player_id")
if not player_id:
    return jsonify({"error": "Player ID not available"}), 401
```

### File 2: `src/core/database_service.py` - Query Fix (Previously Applied)

```python
# Line 435-437: get_recent_games()
desc(func.coalesce(GameResult.finished_at, GameResult.started_at))

# Line 557-559: get_player_game_history()
desc(func.coalesce(GameResult.finished_at, GameResult.started_at))
```

---

## How to Test

### Web App

```
1. Login as Dennis → https://letsplaydarts.eu/
2. Go to /history
3. See all games displayed ✅
4. See correct statistics ✅
```

### Mobile App

```
1. Login as Dennis
2. Go to Results tab
3. See Dennis's games (not player 1) ✅
4. See correct statistics ✅
```

### Throwout Advice

```
1. Start new 301 game
2. Control page → Check "Show Throw-out Advice"
3. During gameplay → See advice for scores ✅
```

---

## Deployment

### Production (Docker)

```bash
docker-compose -f docker-compose-wso2.yml down
docker-compose -f docker-compose-wso2.yml up -d
```

### Local Testing

```bash
python run.py
# Then test at http://localhost:5000/
```

### Verify

```bash
python test_history_fixes.py
```

---

## Key Points

✅ **No database migration needed**  
✅ **No schema changes required**  
✅ **Fully backward compatible**  
✅ **No breaking changes**  
✅ **Ready for production**

---

## Debug Commands

If issues occur:

```python
# Check session data
curl http://localhost:5000/api/debug/session

# Check available players
sqlite3 games.db "SELECT id, name, username FROM player LIMIT 10;"

# Check games for player
sqlite3 games.db "SELECT * FROM game_result WHERE player_id=11 LIMIT 5;"
```

---

## Support

**Issue**: History page still empty  
**Fix**: Check if logged in, check database has games

**Issue**: Mobile shows wrong player  
**Fix**: Clear cache, re-login, restart app

**Issue**: No throwout advice  
**Fix**: Start game first, enable checkbox, check WebSocket connection

---

**Status**: ✅ Ready for deployment
