# Docker Deployment Instructions - Post-Fix

## Summary of Changes

Three critical issues have been addressed:

1. ✅ **Swagger YAML Parsing Error** - FIXED
   - 3 mobile API endpoint descriptions were unquoted (causing parsing failures)
   - All descriptions are now properly quoted

2. ✅ **Throwout Advice Missing on Desktop** - FIXED
   - Desktop control panel now displays "💡 Finishing Tip" section
   - Shows finishing advice when game is active and feature is enabled

3. ⚠️ **Game History Not Displaying** - IDENTIFIED (Infrastructure Issue)
   - Root cause: PostgreSQL Docker service not accessible
   - Requires Docker service verification

---

## Deployment Steps

### Step 1: Verify Files Changed

```bash
# Files that were modified:
ls -la /data/dartserver-pythonapp/src/app/app.py
ls -la /data/dartserver-pythonapp/templates/control.html
ls -la /data/dartserver-pythonapp/static/js/control.js
```

### Step 2: Stop Current Containers

```bash
docker-compose down
```

### Step 3: Rebuild & Start Services

```bash
docker-compose build
docker-compose up -d
```

### Step 4: Verify Services Are Running

```bash
# Check all services
docker-compose ps

# Should show:
# - darts-app: running
# - postgres: running
# - rabbitmq: running
# - (other services based on your docker-compose.yml)
```

### Step 5: Check Application Logs

```bash
# Main application logs
docker-compose logs -f darts-app | head -50

# PostgreSQL logs (should show connection ready)
docker-compose logs postgres | head -20

# Look for errors related to YAML parsing or database connection
```

### Step 6: Test Swagger/API Documentation

```bash
# Once the app is running, test API docs endpoint:
# Open in browser: http://localhost:5000/apidocs

# Or via curl:
curl -s http://localhost:5000/apispec.json | python -m json.tool | head -20

# Should NOT show yaml.scanner.ScannerError
```

---

## Testing Checklist

After deployment, verify these features work:

### Desktop Control Panel

- [ ] Navigate to `/control`
- [ ] Check "Display Settings" has "Show Throw-out Advice" checkbox
- [ ] Check "💡 Finishing Tip" section displays (should show "No active game" initially)
- [ ] Start a game and verify finishing tips display when a player is near victory
- [ ] Enable/disable "Show Throw-out Advice" checkbox and verify section updates

### Mobile Gameplay

- [ ] Navigate to `/mobile/gameplay`
- [ ] Start a game via `/mobile/gamemaster`
- [ ] Verify "💡 Finishing Tip" section appears when player is near victory
- [ ] Verify all game details display (current player, scoreboard, last throw)

### Game History (Once Database Connected)

- [ ] Navigate to `/history`
- [ ] Verify recent games load and display
- [ ] Verify statistics section shows total games, wins, win rate, avg score

### Swagger/API Documentation

- [ ] Navigate to `/apidocs` or `/api/docs`
- [ ] Verify page loads without YAML errors
- [ ] Verify mobile endpoints are documented (lines 1659, 1685, 1790)

---

## If Issues Persist

### Swagger Still Shows Errors

```bash
# Check for Python syntax errors
python3 -m py_compile src/app/app.py

# Check YAML validity in docstrings
python3 -c "
import yaml
import re
with open('src/app/app.py') as f:
    content = f.read()
    for match in re.finditer(r'\"\"\"(.*?)\"\"\"', content, re.DOTALL):
        if '---' in match.group(1):
            yaml_part = match.group(1)[match.group(1).find('---')+3:]
            try:
                yaml.safe_load(yaml_part)
            except Exception as e:
                print(f'YAML Error: {e}')
"
```

### Database Connection Fails

```bash
# Check PostgreSQL container
docker-compose logs postgres

# Test database connection from app container
docker-compose exec darts-app psql -h postgres -U postgres -d dartsdb -c "SELECT 1;"

# Expected output: (1 row with "1")
```

### History Page Still Empty

```bash
# Check database has data
docker-compose exec postgres psql -U postgres -d dartsdb -c "SELECT COUNT(*) FROM game_session;"

# Check if player_id is set in session
# Test API endpoint directly:
curl -s http://localhost:5000/api/player/history \
  -H "Cookie: session=<your_session_id>" | python -m json.tool
```

---

## Architecture Notes

### Modified Files

1. **src/app/app.py** (Lines 1659, 1685, 1790)
   - Mobile API endpoint docstrings now have quoted descriptions
   - Prevents YAML parsing errors in Flasgger/Swagger

2. **templates/control.html** (Lines 85-91)
   - Added "💡 Finishing Tip" display section
   - Shows throwout advice when game is active

3. **static/js/control.js** (Lines 138-151)
   - Added logic to populate throwout advice display
   - Handles enabled/disabled state and game status

### No Breaking Changes

- All changes are additive or fix existing issues
- No API modifications
- No database schema changes
- All existing features should continue working

---

## Troubleshooting Docker Issues

### Services Not Starting

```bash
# Clear Docker volumes and start fresh
docker-compose down -v
docker-compose up -d
```

### Database Connection Timeout

```bash
# Verify Docker network connectivity
docker network ls
docker network inspect <network_name>

# Should show all containers connected to same network
```

### Port Conflicts

```bash
# Check if ports are already in use
lsof -i :5000  # Flask app
lsof -i :5432  # PostgreSQL
lsof -i :5672  # RabbitMQ

# If ports occupied, either:
# 1. Stop the conflicting service
# 2. Modify docker-compose.yml port mappings
```

---

## Performance Notes

The throwout advice feature now available on desktop requires:

- Minor HTML rendering (single div section)
- Minimal JavaScript execution (array join operation)
- No database queries (data already in game state)
- Expected impact: **Negligible**

---

## Questions or Issues?

Check the detailed report: `ISSUE_FIX_REPORT.md`
