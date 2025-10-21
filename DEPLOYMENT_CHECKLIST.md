# Docker Deployment Checklist

## Pre-Deployment Verification

### Code Quality Checks

- [ ] Run verification script: `python verify_docker_config.py`
  - Expected: All 5/5 checks pass ✅
- [ ] Review `.env` file for production credentials
- [ ] Ensure no sensitive data is committed to git

### Configuration Verification

- [ ] `.env` database uses `postgres` service name (not localhost)
- [ ] `.env` RabbitMQ uses `rabbitmq` service name (not localhost)
- [ ] `.env` WSO2 internal URL uses `wso2is` service name
- [ ] `.env` ENVIRONMENT set to `production`
- [ ] All required env vars are present in `.env`

### Code Review

- [ ] `src/app/app.py` line 1685: Multi-line YAML fixed ✅
- [ ] `static/js/mobile_gamemaster.js` line 122: Single-player validation `< 1` ✅
- [ ] `templates/mobile_gamemaster.html` line 84: Help text updated ✅

---

## Files Modified (4 files)

```
✅ .env
   └─ Updated database and service URLs for Docker network

✅ src/app/app.py
   └─ Line 1685: Fixed Swagger YAML docstring

✅ static/js/mobile_gamemaster.js
   └─ Line 122: Changed validation from (< 2) to (< 1) for single-player support

✅ templates/mobile_gamemaster.html
   └─ Line 84: Updated help text from "at least 2" to "at least 1"
```

---

## Deployment Steps

### Step 1: Pre-Flight Checks

```bash
cd /data/dartserver-pythonapp

# Verify fixes
python verify_docker_config.py

# Check git status
git status
# (Should show the 4 modified files above)

# Review critical file changes
git diff .env | head -50
git diff src/app/app.py | grep -A 3 -B 3 "1685"
```

### Step 2: Build Docker Images

```bash
# Rebuild containers with all fixes
docker-compose -f docker-compose-wso2.yml build --no-cache

# Verify build completed successfully
# Look for "Successfully tagged" or "Successfully built"
```

### Step 3: Start Services

```bash
# Start all services in background
docker-compose -f docker-compose-wso2.yml up -d

# Wait for services to be healthy (30-60 seconds)
sleep 30

# Check service status
docker-compose -f docker-compose-wso2.yml ps
# Expected: All services showing "Up" status
```

### Step 4: Monitor Startup

```bash
# Watch logs in real-time
docker-compose -f docker-compose-wso2.yml logs -f darts-app

# Look for these success messages:
# ✅ "Database connection OK!"
# ✅ "Running on" (Flask started)
# ✅ "* Debugger PIN:" (if FLASK_DEBUG=True)

# Press Ctrl+C to exit logs
```

### Step 5: Verify Connectivity

```bash
# Test database connection
docker-compose -f docker-compose-wso2.yml exec darts-app \
  python -c "from src.core.database_service import DatabaseService; \
  db = DatabaseService(); \
  print('✅ Database OK' if db.check_connection() else '❌ DB Failed')"

# Test API endpoints are accessible
curl -s http://localhost:5000/api/game/current -H "Cookie: session=test"

# Test Swagger loads
curl -s http://localhost:5000/api/docs/ | grep -q "swagger" && echo "✅ Swagger OK" || echo "❌ Swagger Failed"
```

---

## Feature Testing

### Test 1: Single-Player Games

```
Location: https://letsplaydarts.eu/mobile/gamemaster
Steps:
  1. Scroll to "Start New Game"
  2. In "Players" textarea, enter only ONE name (e.g., "Alice")
  3. Click "Start Game"
  4. Go to Gameplay tab
  5. Verify game displays with 1 player

✅ PASS if: Game starts and displays correctly
❌ FAIL if: Error message "at least 2 players" appears
```

### Test 2: History Page

```
Location: https://letsplaydarts.eu/history
Steps:
  1. Play a complete game (start → finish)
  2. Navigate to History page
  3. Wait for page to load (check browser console for errors)
  4. Look for recently played game
  5. Test filter by game type

✅ PASS if: Recent games appear with statistics
❌ FAIL if: Page stays empty or shows "No games found"
```

### Test 3: Swagger Documentation

```
Location: https://letsplaydarts.eu/api/docs/
Steps:
  1. Navigate to URL
  2. Verify page loads without errors
  3. Scroll through endpoints
  4. Click "Try it out" on an endpoint
  5. Verify request/response work

✅ PASS if: All endpoints documented and "Try it out" works
❌ FAIL if: YAML errors appear or page doesn't load
```

### Test 4: Throwout Advice

```
Location: Start a game → Control Panel or Mobile Gameplay
Steps:
  1. Start a 301/401/501 game with 2+ players
  2. In Game Master panel, check "Show Throw-out Advice"
  3. Play until one player's score is < 50
  4. Note the displayed finishing tip

✅ PASS if: Tips like "[T20, Double 10]" appear when close to finish
❌ FAIL if: No tips display or checkbox doesn't work
```

### Test 5: Mobile Gameplay

```
Location: https://letsplaydarts.eu/mobile/gameplay
Steps:
  1. Start an active game
  2. Go to Gameplay page
  3. View "Current Player" card
  4. Check Scoreboard displays all players
  5. Switch to "Active Games" tab

✅ PASS if: Current game displays with all details
❌ FAIL if: Page stays blank or shows "No Active Game"
```

---

## Monitoring & Logs

### View Application Logs

```bash
# Real-time logs
docker-compose -f docker-compose-wso2.yml logs -f darts-app

# Last 100 lines
docker-compose -f docker-compose-wso2.yml logs --tail=100 darts-app

# Logs for specific time period
docker-compose -f docker-compose-wso2.yml logs --since 5m darts-app
```

### View Database Logs

```bash
docker-compose -f docker-compose-wso2.yml logs postgres
```

### View RabbitMQ Logs

```bash
docker-compose -f docker-compose-wso2.yml logs rabbitmq
```

### Check Container Health

```bash
# Detailed status
docker-compose -f docker-compose-wso2.yml ps -a

# Health check status
docker ps --format "table {{.Names}}\t{{.Status}}" | grep darts
```

---

## Rollback Plan

If something goes wrong:

### Quick Rollback

```bash
# Stop current deployment
docker-compose -f docker-compose-wso2.yml down

# Revert file changes if needed
git checkout .env
git checkout src/app/app.py
git checkout static/js/mobile_gamemaster.js
git checkout templates/mobile_gamemaster.html

# Restart with previous configuration
docker-compose -f docker-compose-wso2.yml up -d
```

### Data Preservation

```bash
# Database volumes are persistent by default
# Even after stopping containers, data remains:
docker volume ls | grep darts

# If needed, backup database before deployment:
docker-compose -f docker-compose-wso2.yml exec postgres \
  pg_dump -U postgres dartsdb > backup_$(date +%Y%m%d_%H%M%S).sql
```

---

## Performance Optimization

### CPU/Memory Monitoring

```bash
# Monitor container resource usage
docker stats darts-app --no-stream

# Monitor over time
docker stats darts-app
```

### Database Performance

```bash
# Check database connections
docker-compose -f docker-compose-wso2.yml exec postgres \
  psql -U postgres -c "SELECT datname, count(*) FROM pg_stat_activity GROUP BY datname;"

# Check slow queries (if logging enabled)
docker-compose -f docker-compose-wso2.yml exec postgres \
  tail -f /var/log/postgresql/postgresql.log
```

---

## Post-Deployment Verification

### 24-Hour Stability Check

- [ ] Application running without restarts
- [ ] No error spikes in logs
- [ ] Database queries responding normally
- [ ] All API endpoints accessible
- [ ] WebSocket connections stable

### Week-Long Monitoring

- [ ] Error logs reviewed and addressed
- [ ] Performance metrics collected
- [ ] User reports collected (if applicable)
- [ ] Security logs reviewed

---

## Troubleshooting Matrix

| Issue                           | Check          | Solution                                                                                                     |
| ------------------------------- | -------------- | ------------------------------------------------------------------------------------------------------------ |
| **Swagger won't load**          | Browser cache  | Hard refresh (Ctrl+Shift+R) or incognito mode                                                                |
| **History page empty**          | Database query | Play a game first, then reload page                                                                          |
| **Single-player still blocked** | Cache          | Clear `localStorage` and reload                                                                              |
| **Mobile not updating**         | WebSocket      | Check browser DevTools → Network                                                                             |
| **Database connection failed**  | .env file      | Verify `DATABASE_URL=postgresql://postgres:postgres@postgres:5432/dartsdb` <!-- pragma: allowlist secret --> |
| **RabbitMQ not connecting**     | .env file      | Verify `RABBITMQ_HOST=rabbitmq`                                                                              |
| **Services won't start**        | Build cache    | Rebuild: `docker-compose build --no-cache`                                                                   |

---

## Success Criteria

✅ **Deployment is successful when:**

1. All 5 verification checks pass: `python verify_docker_config.py`
2. Docker services start without errors: `docker-compose ps` shows all "Up"
3. Swagger/API Docs loads: `/api/docs/` accessible and no YAML errors
4. Single-player games work: Can create game with 1 player
5. History page shows data: Recent games displayed after playing
6. Throwout advice displays: Tips show when toggled on near finish
7. Mobile gameplay updates: Current player and scores display real-time
8. No critical errors in logs: `docker-compose logs darts-app` shows no errors

---

## Post-Deployment Tasks

- [ ] Update documentation with deployment date
- [ ] Notify users of new features (single-player games)
- [ ] Monitor logs for first 24 hours
- [ ] Document any issues encountered
- [ ] Update backup schedule if database size changed

---

## Quick Commands Reference

```bash
# Start services
docker-compose -f docker-compose-wso2.yml up -d

# Stop services
docker-compose -f docker-compose-wso2.yml down

# Restart single service
docker-compose -f docker-compose-wso2.yml restart darts-app

# View logs
docker-compose -f docker-compose-wso2.yml logs -f darts-app

# Run one-off command
docker-compose -f docker-compose-wso2.yml exec darts-app bash

# Rebuild images
docker-compose -f docker-compose-wso2.yml build --no-cache

# Verify fixes
python verify_docker_config.py
```

---

**Status**: Ready for Production Deployment ✅  
**Last Updated**: 2025-10-19  
**Critical Issues Fixed**: 5/5 ✅
