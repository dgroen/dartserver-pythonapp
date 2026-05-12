# dartserver-app

Flask web application for the Darts Game Server with real-time game management via WebSocket.

## Features

- **Flask App Factory** - Modular application creation with CORS and Swagger
- **Game Manager** - Orchestrates game state, player management, and scoring
- **SocketIO Events** - Real-time game updates (11 event handlers)
- **REST API** - 66 routes organized by domain (auth, game, player, etc)
- **Role-Based Access** - Admin and gamemaster endpoints

## Installation

```bash
pip install dartserver-app
```

## Quick Start

### Create Application

```python
from dartserver_app import create_app

app, socketio = create_app()

if __name__ == '__main__':
    socketio.run(app, host='0.0.0.0', port=5000)
```

### Use GameManager

```python
from dartserver_app import GameManager
from flask_socketio import SocketIO

socketio = SocketIO(app)
game_manager = GameManager(socketio)

# Create game
game_manager.new_game('301', player_ids=[1, 2])

# Add player
game_manager.add_player('Alice')

# Process score
game_manager.process_score({'zone': 20, 'modifier': 1})

# Get current state
state = game_manager.get_game_state()
```

## REST API Endpoints

### Authentication
- `GET /login` - OAuth2 login
- `GET /callback` - OAuth2 callback
- `GET /logout` - Logout
- `GET /profile` - User profile

### Game Management
- `POST /api/game/new` - Create new game
- `POST /api/game/start` - Start game
- `POST /api/game/end` - End game
- `GET /api/game/state` - Get game state
- `GET /api/game/types` - List game types

### Player Management
- `GET /api/players` - List players
- `POST /api/players` - Create player
- `DELETE /api/players/<id>` - Delete player
- `GET /api/player/history` - Player game history
- `GET /api/player/statistics` - Player statistics

### Score Management
- `POST /api/Throw/zone` - Submit score by zone

### Dartboard Management
- `GET /api/dartboard/types` - List dartboard types
- `POST /api/dartboard/connect` - Connect dartboard
- `POST /api/dartboard/score` - Submit dartboard score

### Text-to-Speech
- `GET /api/tts/config` - Get TTS config
- `POST /api/tts/config` - Update TTS config
- `POST /api/tts/test` - Test TTS

### Training Mode
- `POST /api/training/start` - Start training session
- `POST /api/training/end` - End training session
- `GET /api/training/history` - Training history

## SocketIO Events

### Server Events
- `connect` - Client connection
- `disconnect` - Client disconnection
- `game_state` - Game state broadcast
- `error` - Error notification

### Client Events
- `new_game` - Start new game
- `add_player` - Add player to game
- `remove_player` - Remove player
- `next_player` - Move to next player
- `skip_to_player` - Jump to specific player
- `end_turn_early` - End current turn
- `manual_score` - Submit score manually
- `set_throwout_advice` - Toggle advice

## Route Organization

Routes are organized into logical domains:

| Domain | Routes | Purpose |
|--------|--------|---------|
| `auth` | 6 | Authentication |
| `ui` | 15 | User interface pages |
| `game` | 13 | Game management API |
| `player` | 6 | Player management |
| `score` | 1 | Score submission |
| `dartboard` | 7 | Dartboard config |
| `tts` | 6 | Text-to-speech |
| `mobile` | 7 | Mobile API |
| `training` | 4 | Training mode |
| `debug` | 1 | Debug utilities |

## Configuration

```python
from dartserver_app import create_app

app, socketio = create_app(config={
    'SESSION_COOKIE_SECURE': True,
    'SESSION_COOKIE_SAMESITE': 'Lax',
    'PERMANENT_SESSION_LIFETIME': 3600,
})
```

## Testing

```bash
pytest tests/
```

## License

MIT - See LICENSE file

## Contributing

Pull requests welcome. Please ensure tests pass.
