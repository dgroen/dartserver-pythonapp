# Multi-Game Management

This document explains how to use the multi-game management functionality to create and manage multiple concurrent dart games.

## Overview

The multi-game management feature allows game masters to:
- Create multiple game sessions simultaneously
- Switch between different games
- Each game maintains independent state (players, scores, game type)
- Delete games when they're complete

## API Endpoints

### 1. List All Games
```http
GET /api/games
```

**Response:**
```json
{
  "status": "success",
  "games": [
    {
      "game_id": "game-1",
      "game_type": "301",
      "is_started": true,
      "is_active": true,
      "player_count": 2,
      "players": ["Alice", "Bob"]
    },
    {
      "game_id": "game-2",
      "game_type": "cricket",
      "is_started": false,
      "is_active": false,
      "player_count": 0,
      "players": []
    }
  ],
  "active_game_id": "game-1"
}
```

### 2. Create New Game Session
```http
POST /api/games/create
Content-Type: application/json

{
  "game_id": "my-game",          # Optional - auto-generated if not provided
  "game_type": "301",             # Optional - game type to start
  "players": ["Alice", "Bob"],    # Optional - players to add
  "double_out": false,            # Optional - double-out rule
  "set_as_active": true           # Optional - make this the active game (default: true)
}
```

**Response:**
```json
{
  "status": "success",
  "message": "Game session created",
  "game_id": "my-game"
}
```

### 3. Activate a Game
```http
POST /api/games/<game_id>/activate
```

**Response:**
```json
{
  "status": "success",
  "message": "Game activated",
  "game_id": "my-game"
}
```

### 4. Get Specific Game State
```http
GET /api/games/<game_id>/state
```

**Response:**
```json
{
  "players": [...],
  "current_player": 0,
  "game_type": "301",
  "is_started": true,
  "is_paused": false,
  "current_throw": 1,
  "game_data": {...}
}
```

### 5. Delete a Game
```http
DELETE /api/games/<game_id>
```

**Response:**
```json
{
  "status": "success",
  "message": "Game session deleted"
}
```

**Note:** The default game cannot be deleted.

## Usage Examples

### Example 1: Create Multiple Games

```bash
# Create first game for Alice and Bob playing 301
curl -X POST http://localhost:5000/api/games/create \
  -H "Content-Type: application/json" \
  -d '{
    "game_id": "alice-bob-301",
    "game_type": "301",
    "players": ["Alice", "Bob"]
  }'

# Create second game for Charlie and Dave playing Cricket
curl -X POST http://localhost:5000/api/games/create \
  -H "Content-Type: application/json" \
  -d '{
    "game_id": "charlie-dave-cricket",
    "game_type": "cricket",
    "players": ["Charlie", "Dave", "Eve"]
  }'
```

### Example 2: Switch Between Games

```bash
# List all games
curl http://localhost:5000/api/games

# Switch to the Cricket game
curl -X POST http://localhost:5000/api/games/charlie-dave-cricket/activate

# Now any score submissions will go to the Cricket game
```

### Example 3: Monitor Multiple Games

```bash
# Get state of first game
curl http://localhost:5000/api/games/alice-bob-301/state

# Get state of second game
curl http://localhost:5000/api/games/charlie-dave-cricket/state
```

### Example 4: Clean Up Finished Games

```bash
# Delete the completed 301 game
curl -X DELETE http://localhost:5000/api/games/alice-bob-301

# List remaining games
curl http://localhost:5000/api/games
```

## Backward Compatibility

The implementation maintains full backward compatibility:

1. **Default Game**: A default game is automatically created on startup
2. **Existing Endpoints**: All existing API endpoints (`/api/game/state`, `/api/game/new`, etc.) work with the currently active game
3. **WebSocket Events**: All WebSocket events work with the active game
4. **No Breaking Changes**: Existing code and integrations continue to work without modifications

## Use Cases

### Tournament Management
Game masters can:
- Create separate games for different tournament matches
- Track multiple matches simultaneously
- Switch between matches to review scores
- Archive completed games

### Practice Sessions
- Create multiple practice games with different configurations
- Let players practice in parallel
- Each game maintains independent state

### Multi-Board Setups
- Manage multiple dartboards in the same venue
- Each board has its own game
- Centralized management and monitoring

## Permissions

All multi-game management endpoints require:
- **Authentication**: User must be logged in
- **Game Master Role**: User must have `game:create` permission (Game Master or Admin role)

The following endpoints are available to all authenticated users:
- `GET /api/games` - View all games
- `GET /api/games/<game_id>/state` - View specific game state

## Implementation Details

### Game ID Format
- Can be any string (alphanumeric and hyphens recommended)
- Auto-generated format: `game-<uuid>` (e.g., `game-a1b2c3d4`)
- The `default` game ID is reserved

### Active Game Concept
- Only one game is "active" at a time
- The active game is used by default endpoints and UI
- Switching games changes which game receives score updates
- The first created game becomes active by default

### Game Independence
- Each game has its own:
  - Players and scores
  - Current player and throw count
  - Game state (started, paused, winner)
  - Database records
- Games do not share or interfere with each other's state

## Testing

Comprehensive tests are included:
- 16 unit tests for `MultiGameManager`
- 6 integration tests for concurrent gameplay
- All tests verify game independence and state management
