# Testing Multi-Game Implementation

## Quick Start Testing

### 1. Verify Role-Based Visibility

#### Login as Regular Player
1. Go to `/` (main game page)
2. Active games box should **NOT** be visible in left sidebar
3. You should not see "Active Games" section

#### Login as Gamemaster
1. Go to `/`
2. Active games box **SHOULD** be visible in left sidebar
3. You should see "Active Games" section with "🎮 Active Games" header

#### Login as Admin
1. Go to `/`
2. Active games box **SHOULD** be visible in left sidebar
3. You should see "Active Games" section

---

### 2. Test Game Creation from `/api/game/start`

```bash
curl -X POST http://localhost:5000/api/game/start \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -d '{
    "game_type": "301",
    "players": ["Player1", "Player2"],
    "double_out": false,
    "show_throwout_advice": true
  }'
```

**Expected Response:**
```json
{
  "success": true,
  "message": "Game started successfully",
  "game_id": "game-a1b2c3d4",
  "game": { /* game state */ }
}
```

**Verification:**
- Response includes `game_id`
- Game appears immediately in active games box (if logged in as gamemaster/admin)

---

### 3. Test Game Creation from Control Panel (`/api/game/new`)

```bash
curl -X POST http://localhost:5000/api/game/new \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -d '{
    "game_type": "501",
    "players": ["Alice", "Bob"],
    "double_out": true
  }'
```

**Expected Response:**
```json
{
  "status": "success",
  "message": "New game started",
  "game_id": "game-e5f6g7h8"
}
```

**Verification:**
- Response includes `game_id`
- Game appears in active games list
- Game marked as active (visible in GET /api/games response)

---

### 4. Test Game Resumption (`/api/game/resume`)

```bash
# First, get an incomplete game session ID from /api/game/history
curl http://localhost:5000/api/game/history \
  -H "Authorization: Bearer YOUR_TOKEN"

# Then resume it
curl -X POST http://localhost:5000/api/game/resume/GAME_SESSION_ID \
  -H "Authorization: Bearer YOUR_TOKEN"
```

**Expected Response:**
```json
{
  "status": "success",
  "message": "Game resumed with X throws replayed",
  "game_id": "game-resumed-123",
  "redirect_url": "/"
}
```

**Verification:**
- Response includes `game_id` for the resumed session
- Original game session tracked in `resumed_from` field
- Resumed game appears in active games list
- Active games box shows the resumed game

---

### 5. Check Active Games API

```bash
curl http://localhost:5000/api/games \
  -H "Authorization: Bearer YOUR_TOKEN" | jq '.'
```

**Expected Response:**
```json
{
  "status": "success",
  "games": [
    {
      "game_id": "game-a1b2c3d4",
      "game_type": "301",
      "created_at": "2024-12-19T16:12:10.123456",
      "players": [{"db_id": 1, "name": "Alice"}, {"db_id": 2, "name": "Bob"}],
      "double_out": false,
      "is_active": true
    },
    {
      "game_id": "game-e5f6g7h8",
      "game_type": "501",
      "created_at": "2024-12-19T16:12:15.654321",
      "players": [...],
      "double_out": true,
      "is_active": false
    }
  ],
  "active_game_id": "game-a1b2c3d4"
}
```

---

### 6. Switch Active Game

```bash
curl -X POST http://localhost:5000/api/games/game-e5f6g7h8/activate \
  -H "Authorization: Bearer YOUR_TOKEN"
```

**Expected Response:**
```json
{
  "status": "success",
  "message": "Game activated",
  "active_game_id": "game-e5f6g7h8"
}
```

**Verification:**
- Active game switches
- GET /api/games now shows different game as active (is_active: true)

---

## Browser Testing Workflow

### Step 1: Login as Gamemaster
1. Navigate to `/` (main page)
2. Login with gamemaster credentials

### Step 2: Verify Active Games Box Visible
1. Look for "Active Games" section in left sidebar
2. Should show "Loading games..." initially
3. Should show "➕" button to create new game

### Step 3: Create Game from Mobile
1. Click "➕" button
2. Fill in game details
3. Click "Start Game"
4. New game should appear in active games list

### Step 4: Create Game from Control Panel
1. Navigate to `/control`
2. Fill in game details in control panel
3. Click "Start Game"
4. Game should appear in active games list

### Step 5: Switch Active Game
1. In active games list, click different game
2. Active game should change
3. Game board should update to show new active game

### Step 6: Resume Game
1. Navigate to `/dashboard`
2. Find incomplete game
3. Click "Resume"
4. New game created for resumption
5. Resumed game appears in active games list

### Step 7: Verify Non-Gamemaster Can't See Active Games
1. Logout
2. Login as regular player
3. Go to `/`
4. Active games box should NOT be visible

---

## Verification Checklist

- [ ] Active games box visible to gamemaster
- [ ] Active games box visible to admin
- [ ] Active games box NOT visible to regular player
- [ ] Games created from /api/game/start appear in active games
- [ ] Games created from /api/game/new appear in active games
- [ ] Games resumed via /api/game/resume appear in active games
- [ ] GET /api/games returns all tracked games
- [ ] Active game marked with is_active: true
- [ ] Can switch active game with POST /api/games/<id>/activate
- [ ] Game metadata includes all required fields (game_id, game_type, players, etc.)
- [ ] No errors in browser console
- [ ] No errors in server logs

---

## Debugging Tips

### Check Server Logs for games_store Updates
Look for log entries showing:
- "games_store updated with game-..."
- "active_game_id set to game-..."

### Inspect Active Games List in Browser
Open browser developer tools and check:
```javascript
// In browser console
console.log('Current active games:');
fetch('/api/games').then(r => r.json()).then(d => console.log(d.games));
```

### Verify Role in Request Context
Check Flask request context:
```python
from flask import request
print(f"User roles: {request.user_roles}")  # Should show: ['gamemaster'] or ['admin']
```

### Test Template Rendering
Check if active games section is rendered:
```html
<!-- View page source and search for "Active Games" -->
<!-- Should only appear if user has gamemaster or admin role -->
```
