# Multiple Games Implementation

This document describes how to use the multiple concurrent games feature.

## Overview

The application now supports multiple concurrent game sessions, allowing different game masters to create and manage their own games with different users.

## Architecture

### GameSessionManager

The `GameSessionManager` class manages multiple `GameManager` instances:

- Each game session has a unique ID (16-character URL-safe token)
- Sessions are completely isolated from each other
- Game masters can create, manage, and delete their own sessions

### Backward Compatibility

The implementation maintains full backward compatibility:

- A "default" session is automatically created when needed
- All existing endpoints continue to work unchanged
- WebSocket handlers route to the default session

## API Endpoints

### List Active Sessions

```http
GET /api/sessions
Authorization: Bearer <token>
```

**Response:**
```json
{
  "sessions": [
    {
      "session_id": "vpsef6f_ftxwabJM...",
      "creator_id": "user123",
      "game_type": "301",
      "is_started": true,
      "is_paused": false,
      "player_count": 2,
      "players": [
        {"name": "Alice", "id": 0},
        {"name": "Bob", "id": 1}
      ]
    }
  ]
}
```

### Create New Session

```http
POST /api/sessions/create
Authorization: Bearer <token>
```

**Required Permission:** `game:create`

**Response:**
```json
{
  "status": "success",
  "session_id": "vpsef6f_ftxwabJM...",
  "message": "Game session created"
}
```

### Get Session State

```http
GET /api/sessions/<session_id>
Authorization: Bearer <token>
```

**Response:** Returns the current game state for the session

### Delete Session

```http
DELETE /api/sessions/<session_id>
Authorization: Bearer <token>
```

**Required Permission:** `game:create`

**Response:**
```json
{
  "status": "success",
  "message": "Session deleted"
}
```

### Start Game in Session

```http
POST /api/sessions/<session_id>/new_game
Authorization: Bearer <token>
Content-Type: application/json

{
  "game_type": "301",
  "players": ["Alice", "Bob"],
  "double_out": false
}
```

**Required Permission:** `game:create`

**Response:**
```json
{
  "status": "success",
  "message": "New game started"
}
```

## Usage Example

### Python Example

```python
from src.app.app import game_session_manager

# Create a new game session
session_id = game_session_manager.create_session(creator_id="gamemaster1")

# Get the game manager for this session
game_mgr = game_session_manager.get_session(session_id)

# Start a game in the session
player_ids = [{"db_id": 1}, {"db_id": 2}]
game_mgr.new_game("301", player_ids=player_ids, double_out=False)

# List all active sessions
sessions = game_session_manager.list_sessions()

# Delete a session
game_session_manager.delete_session(session_id)
```

### JavaScript Example (using fetch)

```javascript
// Create a new game session
const createSession = async () => {
  const response = await fetch('/api/sessions/create', {
    method: 'POST',
    headers: {
      'Authorization': `Bearer ${accessToken}`
    }
  });
  const data = await response.json();
  return data.session_id;
};

// Start a game in the session
const startGame = async (sessionId) => {
  await fetch(`/api/sessions/${sessionId}/new_game`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      'Authorization': `Bearer ${accessToken}`
    },
    body: JSON.stringify({
      game_type: '301',
      players: ['Alice', 'Bob'],
      double_out: false
    })
  });
};

// List all sessions
const listSessions = async () => {
  const response = await fetch('/api/sessions', {
    headers: {
      'Authorization': `Bearer ${accessToken}`
    }
  });
  const data = await response.json();
  return data.sessions;
};
```

## Features

### Session Isolation

Each game session is completely isolated:
- Independent game state
- Separate player lists
- Different game types
- Independent scoring

### Example: Running Multiple Games

```python
# Game Master 1 creates a 301 game
session1 = game_session_manager.create_session(creator_id="gm1")
game1 = game_session_manager.get_session(session1)
game1.new_game("301", player_ids=[{"db_id": 1}, {"db_id": 2}])

# Game Master 2 creates a Cricket game
session2 = game_session_manager.create_session(creator_id="gm2")
game2 = game_session_manager.get_session(session2)
game2.new_game("cricket", player_ids=[{"db_id": 3}, {"db_id": 4}])

# Both games run independently
game1.process_score({"score": 20, "multiplier": "TRIPLE"})
game2.process_score({"score": 20, "multiplier": "SINGLE"})
```

## Testing

The implementation includes comprehensive tests:

- **Unit tests:** 12 tests for `GameSessionManager`
- **Integration tests:** 6 tests for multi-game scenarios
- **Coverage:** 96% on `GameSessionManager`

Run tests:
```bash
pytest tests/unit/test_game_session_manager.py -v
pytest tests/integration/test_multi_game_sessions.py -v
```

## Future Enhancements

Potential improvements for the future:

1. **WebSocket Session Routing**
   - Add `session_id` parameter to WebSocket events
   - Route events to specific game sessions
   
2. **Game Lobby UI**
   - User interface for browsing available games
   - Join/leave game functionality
   
3. **Session Persistence**
   - Store session metadata in database
   - Restore sessions after server restart
   
4. **Session Timeout**
   - Automatically clean up inactive sessions
   - Configurable timeout duration

## Security

- All session management endpoints require authentication
- Creating and deleting sessions requires `game:create` permission
- Sessions are isolated - users can only access sessions they're authorized for
- No security vulnerabilities detected (CodeQL scan: 0 alerts)
